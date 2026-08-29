import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_cost_engine_baseline():
    from app.controlplane.cost_engine import run_cost_engine
    result = run_cost_engine(
        telemetry={"model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50, "llm_calls": 1, "tool_calls": 1, "retries": 0, "latency_ms": 300, "estimated_cost": 0.18},
        policy={"expected_cost_inr": 0.20, "max_tool_calls": 5, "max_retries": 2, "latency_budget_ms": 700},
        context={},
    )
    assert result.risk_level == "LOW"
    assert result.cost_multiplier < 2.0


def test_cost_engine_anomaly():
    from app.controlplane.cost_engine import run_cost_engine
    result = run_cost_engine(
        telemetry={"model": "gpt-4o-mini", "input_tokens": 3421, "output_tokens": 1280, "llm_calls": 7, "tool_calls": 9, "retries": 3, "latency_ms": 8200, "estimated_cost": 1.42},
        policy={"expected_cost_inr": 0.20, "max_tool_calls": 5, "max_retries": 2, "latency_budget_ms": 700},
        context={},
    )
    assert result.risk_level in ("HIGH", "CRITICAL"), f"Expected HIGH/CRITICAL, got {result.risk_level}"
    assert result.cost_multiplier > 4.0
    assert len(result.reasons) > 0


def test_cost_engine_tool_call_anomaly():
    from app.controlplane.cost_engine import run_cost_engine
    result = run_cost_engine(
        telemetry={"model": "demo-model", "input_tokens": 500, "output_tokens": 200, "llm_calls": 2, "tool_calls": 8, "retries": 0, "latency_ms": 1200, "estimated_cost": 0.30},
        policy={"expected_cost_inr": 0.20, "max_tool_calls": 5, "max_retries": 2, "latency_budget_ms": 700},
        context={},
    )
    assert "Tool calls" in " ".join(result.reasons)
