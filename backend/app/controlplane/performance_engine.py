from __future__ import annotations

import logging
from typing import Optional

from app.controlplane.types import PerformanceResult
from app.ai.judge import _deterministic_check, run_llm_judge
from app.retrieval.retriever import retrieve_evidence
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_performance_engine(
    response_text: str,
    request_text: str,
    context: dict,
    policy: dict,
    db=None,
) -> PerformanceResult:
    """
    Evaluate whether the AI response is grounded and free from hallucination/contradiction.

    Evidence hierarchy:
    1. Trusted structured data (context.trusted_data)
    2. Retrieved document evidence (pgvector / keyword)
    3. LLM-as-Judge (if enabled)
    4. Mark as UNVERIFIED when evidence is absent
    """
    reasons: list[str] = []
    evidence_used: list[dict] = []
    contradiction_detected = False
    grounding_score = 0.5
    evidence_coverage = 0.0
    unsupported_claim_count = 0
    confidence = 0.5

    # ── 1. Deterministic check against structured trusted data ─────────────
    trusted_data = context.get("trusted_data", {})
    if trusted_data:
        contradiction, det_reasons, det_grounding = _deterministic_check(
            response_text, trusted_data
        )
        if contradiction:
            contradiction_detected = True
            grounding_score = det_grounding
            reasons.extend(det_reasons)
            confidence = 0.92  # high confidence when deterministic contradiction found
            evidence_used.append({
                "source": "trusted_transaction_data",
                "content": str(trusted_data),
                "trust_level": "high",
                "type": "structured_data",
            })
        else:
            grounding_score = max(det_grounding, 0.6)
            evidence_coverage = 0.7
            confidence = 0.85

    # ── 2. Evidence retrieval from document store ──────────────────────────
    search_query = f"{request_text} {response_text[:200]}"
    retrieved = await retrieve_evidence(search_query, db=db, top_k=5)
    if retrieved:
        evidence_used.extend(retrieved[:3])
        if not trusted_data:
            # Assess grounding from retrieved evidence
            top_score = retrieved[0].get("score", 0) if retrieved else 0
            grounding_score = min(0.8, top_score + 0.2)
            evidence_coverage = min(0.9, top_score + 0.3)

    # ── 3. LLM-as-Judge (if enabled and API key available) ────────────────
    llm_result = None
    if settings.enable_llm_judge and retrieved:
        llm_result = await run_llm_judge(
            response_text, request_text, retrieved, context
        )

    if llm_result and isinstance(llm_result, dict):
        # Parse structured LLM evaluation
        claims = llm_result.get("claims", [])
        unsupported_claim_count = sum(
            1 for c in claims if c.get("status") in ("CONTRADICTED", "UNVERIFIED")
        )
        if llm_result.get("contradiction_detected"):
            contradiction_detected = True
        grounding_score = float(llm_result.get("grounding_score", grounding_score))
        confidence = float(llm_result.get("confidence", confidence))
        llm_reason = llm_result.get("reason", "")
        if llm_reason:
            reasons.append(f"LLM Judge: {llm_reason}")

    # ── 4. Handle no-evidence case ─────────────────────────────────────────
    business_impact = context.get("business_impact", "medium")
    has_evidence = bool(trusted_data or retrieved)

    if not has_evidence:
        evidence_coverage = 0.0
        reasons.append("No trusted evidence available for verification")
        if business_impact in ("high", "critical"):
            reasons.append("High-impact context with unverified response — escalation recommended")

    # ── Determine risk level ───────────────────────────────────────────────
    if contradiction_detected:
        risk_level = "HIGH"
        if not reasons:
            reasons = ["Contradiction detected between AI response and trusted data"]
    elif not has_evidence and business_impact in ("high", "critical"):
        risk_level = "UNVERIFIED"
        reasons = reasons or ["Response unverified — no evidence available for high-impact claim"]
    elif grounding_score < 0.3:
        risk_level = "HIGH"
        reasons = reasons or ["Low grounding score — claims insufficiently supported"]
    elif grounding_score < 0.55 or unsupported_claim_count > 0:
        if not has_evidence and business_impact == "low":
            risk_level = "LOW"
            reasons = reasons or ["Low impact query without evidence — treated as safe"]
        else:
            risk_level = "MEDIUM"
            reasons = reasons or ["Some claims lack sufficient evidence"]
    else:
        risk_level = "LOW"
        if not reasons:
            reasons = ["Response is well-grounded in available evidence"]

    return PerformanceResult(
        risk_level=risk_level,
        grounding_score=round(grounding_score, 3),
        evidence_coverage=round(evidence_coverage, 3),
        contradiction_detected=contradiction_detected,
        unsupported_claim_count=unsupported_claim_count,
        confidence=round(confidence, 3),
        reasons=reasons,
        evidence=evidence_used,
    )
