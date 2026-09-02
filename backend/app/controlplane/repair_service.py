from __future__ import annotations

import logging
from typing import Optional

from app.ai.model_client import get_model_client
from app.ai.prompts import REPAIR_SYSTEM_PROMPT, REPAIR_USER_PROMPT
from app.controlplane.types import PerformanceResult, ResponsibilityResult
from app.privacy.redactor import redact_pii

logger = logging.getLogger(__name__)

# Safe fallback messages by use case
_SAFE_FALLBACKS = {
    "customer_support": (
        "I'm unable to provide a fully verified answer right now. "
        "Please contact our support team for accurate information about your account."
    ),
    "finance": (
        "This financial query requires human review. "
        "Please speak with a qualified financial advisor before making any decisions."
    ),
    "financial_decision_support": (
        "This financial query requires human review. "
        "Please speak with a qualified financial advisor before making any decisions."
    ),
    "internal_knowledge": (
        "I was unable to verify this information against our internal knowledge base. "
        "Please check with the relevant team."
    ),
    "default": (
        "I'm unable to provide a verified response at this time. "
        "Please contact a support representative for assistance."
    ),
}


async def attempt_repair(
    original_response: str,
    performance: PerformanceResult,
    responsibility: ResponsibilityResult,
    evidence: list[dict],
    context: dict,
    policy: dict,
) -> tuple[str, bool]:
    """
    Attempt to repair the AI response.
    Returns (repaired_text, success).

    Repair strategies:
    1. PII redaction (deterministic — always applied)
    2. LLM constrained regeneration (if enabled)
    3. Safe fallback (if regeneration fails/unavailable)
    """
    use_case = context.get("use_case", "default")
    repaired = original_response
    repair_applied = False

    # ── Step 1: PII Redaction (always apply) ──────────────────────────────
    if responsibility.pii_detected and responsibility.pii_entities:
        repaired = redact_pii(repaired, responsibility.pii_entities)
        repair_applied = True
        logger.info(f"PII redacted: {len(responsibility.pii_entities)} entities")

    # ── Step 2: Contradiction — attempt LLM regeneration ──────────────────
    if performance.contradiction_detected or performance.risk_level in ("HIGH", "UNVERIFIED"):
        trusted_data = context.get("trusted_data", {})
        evidence_text = ""

        if trusted_data:
            evidence_text = f"Trusted transaction data: {trusted_data}"
        elif evidence:
            evidence_text = "\n".join([
                f"[{c.get('source', 'unknown')}]: {c.get('content', '')[:300]}"
                for c in evidence[:3]
            ])

        if evidence_text:
            client = get_model_client()
            instructions = []
            if performance.contradiction_detected:
                instructions.append("Correct the contradicted facts using only the trusted evidence below.")
            if responsibility.pii_detected:
                instructions.append("Remove all personal or sensitive information.")
            instructions.append("State clearly if certain information is not yet available.")

            user_prompt = REPAIR_USER_PROMPT.format(
                original_response=original_response[:1500],
                reasons="\n".join(performance.reasons[:3]),
                evidence=evidence_text[:2000],
                instructions="\n".join(f"- {i}" for i in instructions),
            )

            llm_result = await client.complete(
                system_prompt=REPAIR_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=500,
                response_format="text",
            )

            if llm_result and isinstance(llm_result, str) and len(llm_result) > 20:
                repaired_candidate = llm_result.strip()
                if repaired_candidate == original_response.strip():
                    logger.info("LLM repair generated identical response. Using fallback.")
                    repaired = _SAFE_FALLBACKS.get(use_case, _SAFE_FALLBACKS["default"])
                else:
                    repaired = repaired_candidate
                    logger.info("LLM repair applied")
                repair_applied = True
            else:
                # Fallback to safe message
                repaired = _SAFE_FALLBACKS.get(use_case, _SAFE_FALLBACKS["default"])
                repair_applied = True
        else:
            # No evidence available — use safe fallback
            repaired = _SAFE_FALLBACKS.get(use_case, _SAFE_FALLBACKS["default"])
            repair_applied = True

    return repaired, repair_applied
