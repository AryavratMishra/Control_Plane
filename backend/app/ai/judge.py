from __future__ import annotations

import re
import logging
from typing import Optional

from app.ai.model_client import get_model_client
from app.ai.prompts import EVALUATOR_SYSTEM_PROMPT, EVALUATOR_USER_PROMPT
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Deterministic contradiction checks (no LLM required)
# ---------------------------------------------------------------------------

def _deterministic_check(
    response_text: str,
    trusted_data: dict,
) -> tuple[bool, list[str], float]:
    """
    Check response against structured trusted data deterministically.
    Returns (contradiction_detected, reasons, grounding_score).
    """
    contradictions: list[str] = []
    supported_claims = 0
    total_claims = 0

    text_lower = response_text.lower()

    # ── Refund status check ────────────────────────────────────────────────
    refund_status = trusted_data.get("refund_status", "")
    if refund_status:
        total_claims += 1
        if refund_status.upper() == "PENDING":
            if any(phrase in text_lower for phrase in [
                "processed", "completed", "transferred", "credited", "done", "successful"
            ]):
                if any(word in text_lower for word in ["refund", "amount", "money", "₹", "rs"]):
                    contradictions.append(
                        f"AI claims refund was processed/completed, but trusted data shows refund_status=PENDING"
                    )
                else:
                    supported_claims += 1
            else:
                supported_claims += 1
        elif refund_status.upper() in ("COMPLETED", "PROCESSED"):
            if "pending" in text_lower and "refund" in text_lower:
                contradictions.append(
                    f"AI says refund is pending but trusted data shows refund_status={refund_status}"
                )
            else:
                supported_claims += 1

    # ── Order status check ─────────────────────────────────────────────────
    order_status = trusted_data.get("order_status", trusted_data.get("status", ""))
    if order_status:
        total_claims += 1
        status_lower = order_status.lower()
        if status_lower == "shipped" and "delivered" in text_lower:
            contradictions.append(
                f"AI says order is delivered but trusted data shows order_status=SHIPPED"
            )
        elif status_lower == "cancelled" and any(w in text_lower for w in ["shipped", "delivered", "on the way"]):
            contradictions.append(
                f"AI claims delivery but trusted data shows order is CANCELLED"
            )
        else:
            supported_claims += 1

    # ── Amount check ───────────────────────────────────────────────────────
    trusted_amount = trusted_data.get("refund_amount", trusted_data.get("amount", 0))
    if trusted_amount and trusted_amount > 0:
        total_claims += 1
        # Find any amount mentioned in response
        amount_matches = re.findall(r"₹[\d,]+|rs\.?\s*[\d,]+|\d{3,7}\s*(?:rupees|inr)", text_lower)
        if amount_matches:
            for match in amount_matches:
                digits = re.sub(r"[^\d]", "", match)
                if digits:
                    response_amount = int(digits)
                    if abs(response_amount - int(trusted_amount)) > 10:
                        contradictions.append(
                            f"Amount mismatch: response mentions ₹{response_amount}, trusted data shows ₹{trusted_amount}"
                        )
                        break
            else:
                supported_claims += 1
        else:
            supported_claims += 1

    # Grounding score: ratio of supported to total checked
    if total_claims > 0:
        grounding_score = supported_claims / total_claims
    else:
        grounding_score = 0.5  # neutral when no data to check

    return len(contradictions) > 0, contradictions, grounding_score


async def run_llm_judge(
    response_text: str,
    request_text: str,
    evidence_chunks: list[dict],
    context: dict,
) -> Optional[dict]:
    """
    Run LLM-as-Judge evaluation. Returns structured result or None if unavailable.
    """
    if not settings.enable_llm_judge:
        return None

    client = get_model_client()
    evidence_text = "\n\n".join([
        f"[Source: {c.get('source', 'unknown')}]\n{c.get('content', '')}"
        for c in evidence_chunks[:5]
    ]) or "No trusted evidence available."

    user_prompt = EVALUATOR_USER_PROMPT.format(
        response=response_text[:2000],
        request=request_text[:500],
        evidence=evidence_text[:3000],
        use_case=context.get("use_case", "general"),
        business_impact=context.get("business_impact", "medium"),
    )

    result = await client.complete(
        system_prompt=EVALUATOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.1,
        max_tokens=800,
    )

    return result
