from __future__ import annotations

import re
import time
from typing import Optional

from app.controlplane.types import FastScreenResult
from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# PII quick-detect regex patterns (fast path only – full detection in responsibility engine)
# ---------------------------------------------------------------------------

PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "PHONE_IN": re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ \-]?){13,16}\b"),
    "ACCOUNT_NUMBER": re.compile(r"\b\d{9,18}\b"),
    "PAN": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "AADHAAR": re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
}

# High-impact use-case keywords that raise scrutiny
HIGH_IMPACT_KEYWORDS = [
    "refund", "credit", "debit", "payment", "account", "balance",
    "investment", "retirement", "savings", "loan", "insurance",
    "medical", "diagnosis", "legal", "terminate", "fire", "hire",
    "financial", "withdraw", "transfer",
]

# Safety keyword list (very basic – responsibility engine does deeper check)
UNSAFE_KEYWORDS = [
    "kill", "bomb", "weapon", "suicide", "harm yourself", "self-harm",
    "hate", "discrimination",
]

# Claims that indicate factual assertions needing verification
CLAIM_INDICATORS = [
    "was processed", "has been", "is pending", "is approved", "is rejected",
    "will be", "has shipped", "delivered on", "refund of ₹", "refund of rs",
    "your balance", "your account",
]


def run_fast_screen(
    response_text: str,
    request_text: str,
    telemetry: dict,
    context: dict,
    policy: dict,
) -> FastScreenResult:
    """
    Fast deterministic risk screen. Runs in < 50ms.
    Returns FastScreenResult with risk level and triggers.
    """
    start = time.monotonic()
    triggers: list[str] = []
    pii_quick_hits: list[str] = []
    hard_block = False
    needs_deep_check = False
    cost_signal: Optional[str] = None

    text_lower = response_text.lower()

    # ── 1. PII Quick Scan ──────────────────────────────────────────────────
    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(response_text):
            pii_quick_hits.append(pii_type)
            triggers.append(f"pii_detected:{pii_type.lower()}")
            needs_deep_check = True
            if pii_type in ("CREDIT_CARD", "AADHAAR", "PAN"):
                hard_block = True

    # ── 2. Safety Keyword Check ────────────────────────────────────────────
    for kw in UNSAFE_KEYWORDS:
        if kw in text_lower:
            triggers.append(f"unsafe_keyword:{kw}")
            hard_block = True
            needs_deep_check = True
            break

    # ── 3. High-Impact Use Case Classification ─────────────────────────────
    business_impact = context.get("business_impact", "medium")
    use_case = context.get("use_case", "customer_support")

    is_high_impact = business_impact in ("high", "critical")
    for kw in HIGH_IMPACT_KEYWORDS:
        if kw in text_lower or kw in request_text.lower():
            triggers.append(f"high_impact_keyword:{kw}")
            needs_deep_check = True
            break

    # ── 4. Claim Indicators – needs evidence check ─────────────────────────
    for indicator in CLAIM_INDICATORS:
        if indicator in text_lower:
            triggers.append("claim_requires_verification")
            needs_deep_check = True
            break

    # ── 5. Cost / Telemetry Anomaly ────────────────────────────────────────
    tool_calls = telemetry.get("tool_calls", 0)
    retries = telemetry.get("retries", 0)
    llm_calls = telemetry.get("llm_calls", 1)
    estimated_cost = telemetry.get("estimated_cost", 0.0)
    expected_cost = float(policy.get("expected_cost_inr", settings.default_expected_cost_inr))

    if estimated_cost > 0 and expected_cost > 0:
        multiplier = estimated_cost / expected_cost
        if multiplier > settings.cost_multiplier_high:
            triggers.append(f"cost_anomaly:multiplier_{multiplier:.1f}x")
            cost_signal = f"HIGH:{multiplier:.1f}x"
            needs_deep_check = True
        elif multiplier > settings.cost_multiplier_medium:
            triggers.append(f"cost_elevated:multiplier_{multiplier:.1f}x")
            cost_signal = f"MEDIUM:{multiplier:.1f}x"

    if tool_calls > policy.get("max_tool_calls", settings.max_tool_calls_default):
        triggers.append(f"tool_calls_anomaly:{tool_calls}")
        needs_deep_check = True

    if retries > policy.get("max_retries", settings.max_retries_default):
        triggers.append(f"retry_anomaly:{retries}")
        needs_deep_check = True

    if llm_calls > 5:
        triggers.append(f"llm_calls_anomaly:{llm_calls}")
        needs_deep_check = True

    # ── 6. Policy-based hard rules ─────────────────────────────────────────
    policy_rules = policy.get("rules", {})
    critical_hits = [p for p in pii_quick_hits if p in ("CREDIT_CARD", "AADHAAR", "PAN")]
    if critical_hits and policy_rules.get("critical_pii_exposure") == "block":
        hard_block = True

    # ── 7. Presence of evidence check ─────────────────────────────────────
    trusted_data = context.get("trusted_data", {})
    if not trusted_data and needs_deep_check:
        triggers.append("no_trusted_data_available")

    # ── Determine risk level ───────────────────────────────────────────────
    if hard_block:
        risk_level = "CRITICAL"
    elif len(triggers) >= 4 or is_high_impact:
        risk_level = "HIGH"
        needs_deep_check = True
    elif len(triggers) >= 2:
        risk_level = "MEDIUM"
        needs_deep_check = True
    elif len(triggers) == 1:
        risk_level = "LOW"
    else:
        risk_level = "LOW"

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return FastScreenResult(
        risk_level=risk_level,
        triggers=triggers,
        hard_block=hard_block,
        needs_deep_check=needs_deep_check,
        latency_ms=elapsed_ms,
        pii_quick_hits=pii_quick_hits,
        cost_signal=cost_signal,
    )
