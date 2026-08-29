import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.controlplane.types import (
    FastScreenResult, PerformanceResult, CostResult, ResponsibilityResult
)


def _make_low():
    return (
        FastScreenResult(risk_level="LOW", needs_deep_check=False),
        PerformanceResult(risk_level="LOW", grounding_score=0.85, confidence=0.9, reasons=["Well grounded"]),
        CostResult(risk_level="LOW", estimated_cost_inr=0.18, expected_cost_inr=0.20, cost_multiplier=0.9, reasons=["Within baseline"]),
        ResponsibilityResult(risk_level="LOW", confidence=0.9, reasons=["No issues"]),
    )


def _make_contradiction():
    return (
        FastScreenResult(risk_level="HIGH", needs_deep_check=True, triggers=["claim_requires_verification"]),
        PerformanceResult(risk_level="HIGH", grounding_score=0.18, contradiction_detected=True, confidence=0.92, reasons=["Contradiction detected"]),
        CostResult(risk_level="LOW", estimated_cost_inr=0.18, expected_cost_inr=0.20, cost_multiplier=0.9, reasons=["Within baseline"]),
        ResponsibilityResult(risk_level="LOW", confidence=0.9, reasons=["No issues"]),
    )


def _make_pii_critical():
    from app.controlplane.types import PolicyViolation
    return (
        FastScreenResult(risk_level="CRITICAL", hard_block=True, needs_deep_check=True, pii_quick_hits=["PAN"]),
        PerformanceResult(risk_level="LOW", grounding_score=0.7, confidence=0.8, reasons=["OK"]),
        CostResult(risk_level="LOW", estimated_cost_inr=0.18, expected_cost_inr=0.20, cost_multiplier=0.9, reasons=["Within baseline"]),
        ResponsibilityResult(
            risk_level="CRITICAL",
            pii_detected=True,
            policy_violations=[
                PolicyViolation(rule_id="CRITICAL_PII", description="PAN detected", severity="critical", action="block"),
            ],
            confidence=0.98,
            reasons=["Critical PII: PAN"],
        ),
    )


def test_risk_engine_low_risk_allows():
    from app.controlplane.risk_engine import run_risk_engine
    fs, perf, cost, resp = _make_low()
    decision = run_risk_engine(
        fast_screen=fs, performance=perf, cost=cost, responsibility=resp,
        context={"business_impact": "low", "use_case": "customer_support"},
        policy={"risk_level": "medium", "rules": {}},
    )
    assert decision.action == "ALLOW"
    assert decision.overall_level in ("LOW", "MEDIUM")


def test_risk_engine_contradiction_triggers_action():
    from app.controlplane.risk_engine import run_risk_engine
    fs, perf, cost, resp = _make_contradiction()
    decision = run_risk_engine(
        fast_screen=fs, performance=perf, cost=cost, responsibility=resp,
        context={"business_impact": "high", "use_case": "customer_support"},
        policy={"risk_level": "medium", "rules": {"contradicted_transaction_claim": "repair"}},
    )
    assert decision.action in ("REPAIR", "ESCALATE", "BLOCK")
    assert decision.overall_level not in ("LOW",)


def test_risk_engine_pii_hard_block():
    from app.controlplane.risk_engine import run_risk_engine
    fs, perf, cost, resp = _make_pii_critical()
    decision = run_risk_engine(
        fast_screen=fs, performance=perf, cost=cost, responsibility=resp,
        context={"business_impact": "high", "use_case": "customer_support"},
        policy={"risk_level": "medium", "rules": {"critical_pii_exposure": "block"}},
    )
    assert decision.action == "BLOCK"
    assert decision.hard_rule_triggered


def test_risk_engine_unverified_high_impact_escalates():
    from app.controlplane.risk_engine import run_risk_engine
    fs = FastScreenResult(risk_level="HIGH", needs_deep_check=True)
    perf = PerformanceResult(risk_level="UNVERIFIED", grounding_score=0.0, confidence=0.5, reasons=["No evidence"])
    cost = CostResult(risk_level="LOW", estimated_cost_inr=0.35, expected_cost_inr=0.50, cost_multiplier=0.7, reasons=["OK"])
    resp = ResponsibilityResult(risk_level="LOW", confidence=0.7, reasons=["No issues"])

    decision = run_risk_engine(
        fast_screen=fs, performance=perf, cost=cost, responsibility=resp,
        context={"business_impact": "critical", "use_case": "financial_decision_support"},
        policy={"risk_level": "high", "rules": {"investment_recommendation": "escalate"}},
    )
    assert decision.action in ("ESCALATE", "BLOCK")
