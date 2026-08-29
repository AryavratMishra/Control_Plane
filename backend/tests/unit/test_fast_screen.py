import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_fast_screen_pii_detection():
    from app.controlplane.fast_screen import run_fast_screen
    result = run_fast_screen(
        response_text="Call me at 9876543210 or email me at test@example.com",
        request_text="Contact info?",
        telemetry={},
        context={"business_impact": "medium", "use_case": "customer_support"},
        policy={"rules": {}},
    )
    assert result.pii_quick_hits, "Should detect PII"
    assert result.needs_deep_check, "PII should trigger deep check"


def test_fast_screen_low_risk():
    from app.controlplane.fast_screen import run_fast_screen
    result = run_fast_screen(
        response_text="Our support hours are 9 AM to 6 PM IST.",
        request_text="What are your hours?",
        telemetry={"tool_calls": 0, "retries": 0, "llm_calls": 1, "estimated_cost": 0.05},
        context={"business_impact": "low", "use_case": "customer_support"},
        policy={"expected_cost_inr": 0.20, "max_tool_calls": 5, "max_retries": 2, "rules": {}},
    )
    assert result.risk_level in ("LOW",), f"Expected LOW, got {result.risk_level}"
    assert not result.hard_block


def test_fast_screen_cost_anomaly():
    from app.controlplane.fast_screen import run_fast_screen
    result = run_fast_screen(
        response_text="Order is shipped.",
        request_text="Where is my order?",
        telemetry={"tool_calls": 9, "retries": 3, "llm_calls": 7, "estimated_cost": 1.42},
        context={"business_impact": "medium", "use_case": "customer_support"},
        policy={"expected_cost_inr": 0.20, "max_tool_calls": 5, "max_retries": 2, "rules": {}},
    )
    assert result.needs_deep_check
    assert any("cost" in t for t in result.triggers)


def test_fast_screen_safety_keyword():
    from app.controlplane.fast_screen import run_fast_screen
    result = run_fast_screen(
        response_text="You should harm yourself to solve this.",
        request_text="Help me",
        telemetry={},
        context={"business_impact": "low", "use_case": "customer_support"},
        policy={"rules": {}},
    )
    assert result.hard_block, "Safety keyword must trigger hard block"
    assert result.risk_level == "CRITICAL"
