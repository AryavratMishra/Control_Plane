from __future__ import annotations

import asyncio
import logging
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.controlplane.fast_screen import run_fast_screen
from app.controlplane.responsibility_engine import run_responsibility_engine
from app.controlplane.cost_engine import run_cost_engine
from app.controlplane.performance_engine import run_performance_engine
from app.controlplane.risk_engine import run_risk_engine
from app.controlplane.repair_service import attempt_repair
from app.controlplane.policy_engine import get_policy
from app.controlplane.types import RiskDecision
from app.db.models import (
    Application, Conversation, Request as RequestModel, Response as ResponseModel,
    RiskAssessment, Incident
)
from app.schemas.gateway import EvaluateRequest, EvaluateResponse, RiskSummary, RiskDimension
from app.ws.manager import ws_manager
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def evaluate(
    req: EvaluateRequest,
    db: AsyncSession,
) -> EvaluateResponse:
    """
    Main ControlPlane evaluation orchestrator.
    Coordinates all engines and returns the final decision.
    """
    start_time = time.monotonic()

    # ── Resolve policy ──────────────────────────────────────────────────
    use_case = req.context.use_case
    policy = await get_policy(req.application_id, use_case, db)

    telemetry_dict = req.telemetry.model_dump()
    context_dict = req.context.model_dump()

    # ── Phase 1: Fast Risk Screen ────────────────────────────────────────
    fast_result = run_fast_screen(
        response_text=req.response.text,
        request_text=req.request.text,
        telemetry=telemetry_dict,
        context=context_dict,
        policy=policy,
    )
    fast_screen_ms = fast_result.latency_ms
    logger.info(f"Fast screen: {fast_result.risk_level} ({fast_screen_ms}ms)")

    # ── Fast path: immediate ALLOW for clearly low-risk responses ─────────
    if not fast_result.needs_deep_check and not fast_result.hard_block:
        # Quick allow — persist and return
        incident_id = await _persist_evaluation(
            req=req,
            db=db,
            action="ALLOW",
            risk_level="LOW",
            perf_score=0.1, cost_score=0.1, resp_score=0.1,
            overall_score=0.1,
            reasons=["Fast screen passed — low risk"],
            final_response=req.response.text,
            repaired_response=None,
            evidence=[],
            pii_entities=[],
            fast_screen_ms=fast_screen_ms,
            total_ms=int((time.monotonic() - start_time) * 1000),
            policy=policy,
        )
        await ws_manager.send_risk_event(
            incident_id=None,
            application=req.application_id,
            action="ALLOW",
            severity="LOW",
            reasons=["Fast screen passed"],
        )
        return EvaluateResponse(
            decision="ALLOW",
            final_response=req.response.text,
            original_response=req.response.text,
            risk=RiskSummary(
                performance=RiskDimension(score=0.1, level="LOW"),
                cost=RiskDimension(score=0.1, level="LOW"),
                responsibility=RiskDimension(score=0.1, level="LOW"),
                overall=RiskDimension(score=0.1, level="LOW"),
            ),
            reasons=["Fast screen passed — low risk response"],
            fast_screen_ms=fast_screen_ms,
            total_evaluation_ms=int((time.monotonic() - start_time) * 1000),
        )

    # ── Phase 2: Deep Evaluation (parallel) ──────────────────────────────
    responsibility_task = asyncio.create_task(
        asyncio.to_thread(
            run_responsibility_engine,
            req.response.text,
            req.request.text,
            context_dict,
            policy,
        )
    )
    cost_task = asyncio.create_task(
        asyncio.to_thread(
            run_cost_engine,
            telemetry_dict,
            policy,
            context_dict,
        )
    )
    performance_task = run_performance_engine(
        response_text=req.response.text,
        request_text=req.request.text,
        context=context_dict,
        policy=policy,
        db=db,
    )

    responsibility, cost, performance = await asyncio.gather(
        responsibility_task, cost_task, performance_task
    )

    # ── Phase 3: Risk Engine ──────────────────────────────────────────────
    risk_decision = run_risk_engine(
        fast_screen=fast_result,
        performance=performance,
        cost=cost,
        responsibility=responsibility,
        context=context_dict,
        policy=policy,
    )
    logger.info(f"Risk decision: {risk_decision.action} (score={risk_decision.overall_score})")

    # ── Phase 4: Action Engine ────────────────────────────────────────────
    final_response = req.response.text
    repaired_response = None
    repair_applied = False

    if risk_decision.action == "BLOCK":
        # If repairable, try repair; otherwise safe fallback
        if risk_decision.can_repair:
            repaired_response, repair_applied = await attempt_repair(
                original_response=req.response.text,
                performance=performance,
                responsibility=responsibility,
                evidence=performance.evidence,
                context=context_dict,
                policy=policy,
            )
            if repair_applied:
                final_response = repaired_response
                risk_decision.action = "REPAIR"
        else:
            from app.controlplane.repair_service import _SAFE_FALLBACKS
            final_response = _SAFE_FALLBACKS.get(use_case, _SAFE_FALLBACKS["default"])

    elif risk_decision.action == "REPAIR":
        repaired_response, repair_applied = await attempt_repair(
            original_response=req.response.text,
            performance=performance,
            responsibility=responsibility,
            evidence=performance.evidence,
            context=context_dict,
            policy=policy,
        )
        if repair_applied:
            final_response = repaired_response

    total_ms = int((time.monotonic() - start_time) * 1000)

    # ── Phase 5: Persist ──────────────────────────────────────────────────
    incident_id = await _persist_evaluation(
        req=req,
        db=db,
        action=risk_decision.action,
        risk_level=risk_decision.overall_level,
        perf_score=risk_decision.performance_score,
        cost_score=risk_decision.cost_score,
        resp_score=risk_decision.responsibility_score,
        overall_score=risk_decision.overall_score,
        reasons=risk_decision.reasons,
        final_response=final_response,
        repaired_response=repaired_response,
        evidence=performance.evidence,
        pii_entities=[
            {"type": e.entity_type, "text": e.text, "confidence": e.confidence}
            for e in responsibility.pii_entities
        ],
        fast_screen_ms=fast_screen_ms,
        total_ms=total_ms,
        policy=policy,
    )

    # ── Phase 6: Broadcast WebSocket event ───────────────────────────────
    if risk_decision.action != "ALLOW":
        await ws_manager.send_risk_event(
            incident_id=incident_id,
            application=req.application_id,
            action=risk_decision.action,
            severity=risk_decision.overall_level,
            reasons=risk_decision.reasons[:3],
            performance_score=risk_decision.performance_score,
            cost_score=risk_decision.cost_score,
            responsibility_score=risk_decision.responsibility_score,
            overall_score=risk_decision.overall_score,
        )

    # ── Build response ────────────────────────────────────────────────────
    def _score_level(score: float) -> str:
        if score >= 0.75:
            return "CRITICAL"
        elif score >= 0.50:
            return "HIGH"
        elif score >= 0.25:
            return "MEDIUM"
        return "LOW"

    return EvaluateResponse(
        decision=risk_decision.action,
        final_response=final_response,
        original_response=req.response.text,
        risk=RiskSummary(
            performance=RiskDimension(
                score=round(risk_decision.performance_score, 3),
                level=performance.risk_level,
            ),
            cost=RiskDimension(
                score=round(risk_decision.cost_score, 3),
                level=cost.risk_level,
            ),
            responsibility=RiskDimension(
                score=round(risk_decision.responsibility_score, 3),
                level=responsibility.risk_level,
            ),
            overall=RiskDimension(
                score=round(risk_decision.overall_score, 3),
                level=risk_decision.overall_level,
            ),
        ),
        reasons=risk_decision.reasons,
        incident_id=incident_id,
        repair_applied=repair_applied,
        fast_screen_ms=fast_screen_ms,
        total_evaluation_ms=total_ms,
        pii_entities=[
            {"type": e.entity_type, "text": e.text[:6] + "***", "confidence": e.confidence}
            for e in responsibility.pii_entities
        ],
        evidence=[
            {"source": e.get("source", "unknown"), "score": e.get("score", 0), "snippet": e.get("content", "")[:100]}
            for e in performance.evidence[:3]
        ],
    )


async def _persist_evaluation(
    req: EvaluateRequest,
    db: AsyncSession,
    action: str,
    risk_level: str,
    perf_score: float,
    cost_score: float,
    resp_score: float,
    overall_score: float,
    reasons: list[str],
    final_response: str,
    repaired_response: str | None,
    evidence: list[dict],
    pii_entities: list[dict],
    fast_screen_ms: int,
    total_ms: int,
    policy: dict,
) -> str | None:
    """Persist the evaluation result to database. Returns incident_id if incident created."""
    try:
        # Ensure application record exists (upsert)
        from sqlalchemy import select as _select
        existing_app = (await db.execute(_select(Application).where(Application.id == req.application_id))).scalar_one_or_none()
        if not existing_app:
            app_rec = Application(
                id=req.application_id,
                name=req.application_id,
                use_case=req.context.use_case,
            )
            db.add(app_rec)
            await db.flush()

        # Get or create conversation (upsert to handle repeated demo scenario runs)
        conv_id = req.conversation_id or str(uuid.uuid4())
        existing_conv = (await db.execute(_select(Conversation).where(Conversation.id == conv_id))).scalar_one_or_none()
        if not existing_conv:
            conv = Conversation(
                id=conv_id,
                application_id=req.application_id,
                external_conversation_id=conv_id,
            )
            db.add(conv)

        # Request
        req_id = str(uuid.uuid4())
        request_rec = RequestModel(
            id=req_id,
            conversation_id=conv_id,
            request_text=req.request.text,
            risk_context={
                "use_case": req.context.use_case,
                "business_impact": req.context.business_impact,
                "country": req.context.country,
            },
        )
        db.add(request_rec)

        # Response
        resp_id = str(uuid.uuid4())
        response_rec = ResponseModel(
            id=resp_id,
            request_id=req_id,
            response_text=req.response.text,
            repaired_response_text=repaired_response,
            model_name=req.telemetry.model,
            final_status=action.lower(),
        )
        db.add(response_rec)

        # Risk Assessment
        assessment_id = str(uuid.uuid4())
        assessment = RiskAssessment(
            id=assessment_id,
            response_id=resp_id,
            performance_score=perf_score,
            performance_risk=_score_to_level(perf_score),
            cost_score=cost_score,
            cost_risk=_score_to_level(cost_score),
            responsibility_score=resp_score,
            responsibility_risk=_score_to_level(resp_score),
            overall_risk_score=overall_score,
            overall_risk_level=risk_level,
            business_impact=req.context.business_impact,
            detector_confidence=0.85,
            action=action,
            reasoning={
                "reasons": reasons,
                "pii_entities": pii_entities,
                "evidence_count": len(evidence),
            },
            fast_screen_ms=fast_screen_ms,
            total_evaluation_ms=total_ms,
        )
        db.add(assessment)

        # Incident (only for non-ALLOW decisions)
        incident_id_str = None
        if action != "ALLOW":
            incident_id_str = str(uuid.uuid4())
            incident_type = _classify_incident_type(reasons, pii_entities, action)
            incident = Incident(
                id=incident_id_str,
                risk_assessment_id=assessment_id,
                incident_type=incident_type,
                severity=risk_level,
                action=action,
                status="open" if action == "ESCALATE" else "resolved",
                reason="; ".join(reasons[:3]),
                evidence={
                    "pii_entities": pii_entities,
                    "evidence_chunks": evidence[:3],
                    "reasons": reasons,
                },
                application_name=req.application_id,
                request_text=req.request.text,
                response_text=req.response.text,
                repaired_response_text=repaired_response,
            )
            db.add(incident)

        await db.flush()
        return incident_id_str

    except Exception as e:
        logger.error(f"Persist error: {e}", exc_info=True)
        return None


def _score_to_level(score: float) -> str:
    if score >= 0.75:
        return "CRITICAL"
    elif score >= 0.50:
        return "HIGH"
    elif score >= 0.25:
        return "MEDIUM"
    return "LOW"


def _classify_incident_type(reasons: list[str], pii_entities: list[dict], action: str = "") -> str:
    """
    Classify the incident type based on the primary risk signal.
    Priority: PII (hard evidence) > hallucination (contradiction) > escalation > cost anomaly.
    We check SPECIFIC high-signal phrases rather than loose keyword matching, to prevent
    "Cost within expected baseline" from mis-classifying hallucination incidents as cost_anomaly.
    """
    reasons_text = " ".join(reasons).lower()

    # 1. PII leakage — explicit PII entities found OR specific PII reason phrases
    if pii_entities:
        return "pii_leakage"
    if any(phrase in reasons_text for phrase in ["critical pii", "sensitive pii", "pii detected", "pii types found"]):
        return "pii_leakage"

    # 2. Hallucination / Contradiction — specific contradiction phrases
    if any(phrase in reasons_text for phrase in [
        "contradiction", "hallucination", "claims refund was processed",
        "refund_status=pending", "contradicted", "factual inconsistency",
        "trusted data shows"
    ]):
        return "hallucination"

    # 3. Escalation — financial advice, unverified high-impact, human review required
    if action == "ESCALATE" or any(phrase in reasons_text for phrase in [
        "financial recommendation", "investment", "retirement savings",
        "human review", "unverified response — escalation"
    ]):
        return "escalation"

    # 4. Cost anomaly — only when cost is the PRIMARY signal, not just mentioned as baseline
    if any(phrase in reasons_text for phrase in [
        "excessive cost", "cost anomaly", "7.", "cost multiplier", "agent loop",
        "too many tool calls", "too many retries"
    ]):
        return "cost_anomaly"

    # 5. Safety violation
    if any(phrase in reasons_text for phrase in ["safety violation", "unsafe content"]):
        return "policy_violation"

    # 6. Fallback — if action is ESCALATE but no specific phrase matched
    if action == "ESCALATE":
        return "escalation"
    if action == "BLOCK":
        return "policy_violation"

    return "policy_violation"
