from __future__ import annotations

from app.controlplane.types import (
    RiskDecision, PerformanceResult, CostResult, ResponsibilityResult, FastScreenResult
)

# Risk level to numeric score mapping
_RISK_SCORES = {
    "LOW": 0.15,
    "MEDIUM": 0.37,
    "HIGH": 0.62,
    "CRITICAL": 0.88,
    "UNVERIFIED": 0.55,
}

# Overall score to level mapping
_SCORE_BANDS = [
    (0.75, "CRITICAL"),
    (0.50, "HIGH"),
    (0.25, "MEDIUM"),
    (0.00, "LOW"),
]


def _score(level: str) -> float:
    return _RISK_SCORES.get(level, 0.15)


def _level(score: float) -> str:
    for threshold, label in _SCORE_BANDS:
        if score >= threshold:
            return label
    return "LOW"


def run_risk_engine(
    fast_screen: FastScreenResult,
    performance: PerformanceResult,
    cost: CostResult,
    responsibility: ResponsibilityResult,
    context: dict,
    policy: dict,
) -> RiskDecision:
    """
    Combine multi-dimensional risk signals into a contextual risk decision.

    Design principles:
    - No naive average — use max with context weights
    - Hard rules override soft signals
    - Business impact and use-case risk amplify scores
    - Uncertainty + high impact → escalate
    """
    reasons: list[str] = []
    hard_rule_triggered = False

    # ── 1. Check hard block rules ──────────────────────────────────────────
    policy_rules = policy.get("rules", {})

    # Critical PII → immediate block
    from app.controlplane.types import PolicyViolation
    critical_violations = [
        v for v in responsibility.policy_violations
        if v.severity == "critical" and v.action == "block"
    ]
    safety_block = responsibility.safety_signal is not None

    if critical_violations or safety_block or fast_screen.hard_block:
        hard_rule_triggered = True
        reasons.extend([v.description for v in critical_violations])
        if safety_block:
            reasons.append(f"Safety violation: {responsibility.safety_signal}")

    # ── 2. Compute dimension scores ────────────────────────────────────────
    perf_score = _score(performance.risk_level)
    cost_score = _score(cost.risk_level)
    resp_score = _score(responsibility.risk_level)

    # Responsibility gets a slight weight boost (privacy/safety > cost)
    # Cost gets 0.7 weight (cost anomaly alone rarely warrants same severity as privacy breach)
    weighted_cost = cost_score * 0.7

    # Base risk: take max of dominant dimensions
    base_risk = max(perf_score, resp_score, weighted_cost)

    # ── 3. Context adjustments ─────────────────────────────────────────────
    business_impact = context.get("business_impact", "medium")
    use_case_risk = policy.get("risk_level", "medium")

    impact_multiplier = {
        "low": 0.8,
        "medium": 1.0,
        "high": 1.25,
        "critical": 1.5,
    }.get(business_impact, 1.0)

    use_case_multiplier = {
        "low": 0.85,
        "medium": 1.0,
        "high": 1.20,
    }.get(use_case_risk, 1.0)

    context_score = base_risk * impact_multiplier * use_case_multiplier

    # ── 4. Uncertainty amplification ──────────────────────────────────────
    if performance.risk_level == "UNVERIFIED" and business_impact in ("high", "critical"):
        context_score = max(context_score, 0.65)
        reasons.append("High-impact context with unverified response")

    # ── 5. Evidence confidence adjustment ─────────────────────────────────
    # Low detector confidence reduces certainty of soft signals
    avg_confidence = (performance.confidence + responsibility.confidence) / 2
    if avg_confidence < 0.4 and not hard_rule_triggered:
        context_score *= 0.85  # dampen low-confidence signals

    # Final overall score (clamped 0–1)
    overall_score = round(min(1.0, context_score), 4)

    if hard_rule_triggered:
        overall_score = max(overall_score, 0.85)

    overall_level = _level(overall_score)
    if hard_rule_triggered:
        overall_level = "CRITICAL"

    # ── 6. Collect all reasons ─────────────────────────────────────────────
    reasons.extend(performance.reasons[:2])
    reasons.extend(cost.reasons[:2])
    reasons.extend(responsibility.reasons[:2])
    reasons = list(dict.fromkeys(reasons))  # deduplicate preserving order

    # ── 7. Determine can_repair and requires_human ─────────────────────────
    can_repair = (
        responsibility.pii_detected and not critical_violations
        or performance.contradiction_detected and not hard_rule_triggered
        or cost.risk_level in ("MEDIUM", "HIGH") and not performance.contradiction_detected
    )

    requires_human = (
        performance.risk_level == "UNVERIFIED" and business_impact in ("high", "critical")
        or responsibility.bias_signal is not None
        or any(v.action == "escalate" for v in responsibility.policy_violations)
        or (overall_level == "HIGH" and avg_confidence < 0.6)
    )

    # ── 8. Determine action ────────────────────────────────────────────────
    if hard_rule_triggered:
        action = "BLOCK"
    elif requires_human:
        # Human review takes priority over automated block when the signal is
        # policy-driven escalation (e.g. financial recommendation, bias) rather
        # than a hard safety violation.
        action = "ESCALATE"
    elif overall_level == "CRITICAL":
        action = "BLOCK"
    elif can_repair or overall_level in ("MEDIUM", "HIGH"):
        action = "REPAIR"
    else:
        action = "ALLOW"

    # Policy override
    policy_overrides = policy.get("action_overrides", {})
    if performance.contradiction_detected and policy_rules.get("contradicted_transaction_claim") == "repair":
        if action == "BLOCK" and not hard_rule_triggered:
            action = "REPAIR"

    if not reasons:
        reasons = ["No significant risk detected"]

    return RiskDecision(
        overall_score=overall_score,
        overall_level=overall_level,
        action=action,
        reasons=reasons[:6],
        requires_human=requires_human,
        can_repair=can_repair,
        hard_rule_triggered=hard_rule_triggered,
        performance_score=perf_score,
        cost_score=cost_score,
        responsibility_score=resp_score,
    )
