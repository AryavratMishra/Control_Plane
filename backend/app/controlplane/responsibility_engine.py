from __future__ import annotations

from app.controlplane.types import (
    ResponsibilityResult, PiiEntity, PolicyViolation
)
from app.privacy.pii_detector import detect_pii

# ---------------------------------------------------------------------------
# Safety keyword categories
# ---------------------------------------------------------------------------

_UNSAFE_CATEGORIES = {
    "violence": ["kill", "murder", "bomb", "weapon", "attack", "hurt someone"],
    "self_harm": ["suicide", "self-harm", "harm yourself", "end your life"],
    "hate_speech": ["hate speech", "racial slur", "discriminate"],
    "confidential": ["internal only", "do not share", "confidential", "proprietary"],
}

# Bias-sensitive decision contexts
_BIAS_CONTEXTS = [
    "hire", "fired", "promotion", "loan approved", "loan rejected",
    "credit approved", "credit denied", "insurance denied",
]


def run_responsibility_engine(
    response_text: str,
    request_text: str,
    context: dict,
    policy: dict,
) -> ResponsibilityResult:
    """
    Evaluate privacy, safety, policy, and potential bias signals.
    """
    reasons: list[str] = []
    policy_violations: list[PolicyViolation] = []
    safety_signal: str | None = None
    bias_signal: str | None = None

    policy_rules = policy.get("rules", {})

    # ── 1. PII Detection ──────────────────────────────────────────────────
    pii_entities = detect_pii(response_text, policy_rules)
    pii_detected = len(pii_entities) > 0

    if pii_detected:
        critical_types = {e.entity_type for e in pii_entities if e.policy_action == "block"}
        redact_types = {e.entity_type for e in pii_entities if e.policy_action == "redact"}

        if critical_types:
            reasons.append(f"Critical PII detected: {', '.join(critical_types)}")
            policy_violations.append(PolicyViolation(
                rule_id="CRITICAL_PII_EXPOSURE",
                description=f"Critical PII types found: {', '.join(critical_types)}",
                severity="critical",
                action="block",
            ))
        if redact_types:
            reasons.append(f"Sensitive PII detected: {', '.join(redact_types)}")
            policy_violations.append(PolicyViolation(
                rule_id="PII_EXPOSURE",
                description=f"Sensitive PII types: {', '.join(redact_types)}",
                severity="high",
                action="redact",
            ))

    # ── 2. Safety Check ────────────────────────────────────────────────────
    text_lower = response_text.lower()
    for category, keywords in _UNSAFE_CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                safety_signal = category
                reasons.append(f"Unsafe content detected: {category}")
                policy_violations.append(PolicyViolation(
                    rule_id=f"SAFETY_{category.upper()}",
                    description=f"Unsafe content category: {category}",
                    severity="critical",
                    action="block",
                ))
                break
        if safety_signal:
            break

    # ── 3. Policy-based enterprise rule checks ─────────────────────────────
    # Financial recommendation without evidence
    if policy_rules.get("investment_recommendation") == "escalate":
        finance_kws = ["invest", "recommend this fund", "put your money", "retirement savings"]
        if any(kw in text_lower for kw in finance_kws):
            reasons.append("Financial recommendation detected — requires human review per policy")
            policy_violations.append(PolicyViolation(
                rule_id="FINANCIAL_RECOMMENDATION",
                description="Financial recommendation without verified evidence",
                severity="high",
                action="escalate",
            ))

    # Confidential data
    if policy_rules.get("confidential_data_exposure") == "block":
        if any(kw in text_lower for kw in _UNSAFE_CATEGORIES["confidential"]):
            reasons.append("Confidential/internal information exposure detected")
            policy_violations.append(PolicyViolation(
                rule_id="CONFIDENTIAL_EXPOSURE",
                description="Internal confidential data detected in response",
                severity="critical",
                action="block",
            ))

    # ── 4. Bias Signal Detection (lightweight prototype) ───────────────────
    use_case = context.get("use_case", "")
    if use_case in ("hr", "finance", "financial_decision_support"):
        for kw in _BIAS_CONTEXTS:
            if kw in text_lower or kw in request_text.lower():
                bias_signal = "potential_protected_attribute_influence"
                reasons.append("High-impact decision context detected — potential bias signal")
                policy_violations.append(PolicyViolation(
                    rule_id="BIAS_SIGNAL",
                    description="Decision context with protected attribute risk",
                    severity="medium",
                    action="escalate",
                ))
                break

    # ── Compute risk level ─────────────────────────────────────────────────
    has_critical = any(v.severity == "critical" for v in policy_violations)
    has_high = any(v.severity == "high" for v in policy_violations)
    has_medium = any(v.severity == "medium" for v in policy_violations)

    if has_critical or safety_signal:
        risk_level = "CRITICAL"
    elif has_high and pii_detected:
        risk_level = "HIGH"
    elif has_high:
        risk_level = "HIGH"
    elif has_medium or pii_detected:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Confidence: higher when multiple signals agree
    confidence = min(0.95, 0.60 + len(policy_violations) * 0.10 + (0.15 if pii_detected else 0))

    if not reasons:
        reasons = ["No responsibility issues detected"]

    return ResponsibilityResult(
        risk_level=risk_level,
        pii_detected=pii_detected,
        pii_entities=pii_entities,
        policy_violations=policy_violations,
        safety_signal=safety_signal,
        bias_signal=bias_signal,
        confidence=confidence,
        reasons=reasons,
    )
