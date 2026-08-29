from __future__ import annotations

from app.controlplane.types import CostResult
from app.config import get_settings

settings = get_settings()

# INR pricing per 1K tokens (approximate for demo)
MODEL_PRICING_INR: dict[str, dict] = {
    "gpt-4o": {"input": 4.17, "output": 12.50},
    "gpt-4o-mini": {"input": 0.13, "output": 0.42},
    "gpt-4": {"input": 25.0, "output": 75.0},
    "gpt-3.5-turbo": {"input": 0.42, "output": 1.25},
    "gemini-1.5-pro": {"input": 5.83, "output": 17.5},
    "gemini-1.5-flash": {"input": 0.058, "output": 0.23},
    "demo-model": {"input": 0.10, "output": 0.30},
    "example-model": {"input": 0.10, "output": 0.30},
}


def calculate_cost_inr(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    pricing = MODEL_PRICING_INR.get(model.lower(), MODEL_PRICING_INR["demo-model"])
    cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
    return round(cost, 4)


def run_cost_engine(
    telemetry: dict,
    policy: dict,
    context: dict,
) -> CostResult:
    """
    Evaluate AI execution cost against use-case baseline.
    """
    reasons: list[str] = []

    model = telemetry.get("model", "demo-model")
    input_tokens = telemetry.get("input_tokens", 0)
    output_tokens = telemetry.get("output_tokens", 0)
    llm_calls = telemetry.get("llm_calls", 1)
    tool_calls = telemetry.get("tool_calls", 0)
    retrieval_calls = telemetry.get("retrieval_calls", 0)
    retries = telemetry.get("retries", 0)
    latency_ms = telemetry.get("latency_ms", 0)
    reported_cost = telemetry.get("estimated_cost", 0.0)

    # Calculate actual cost
    calculated_cost = calculate_cost_inr(model, input_tokens, output_tokens)
    # Use reported cost if provided and > 0, otherwise use calculated
    estimated_cost_inr = reported_cost if reported_cost > 0 else calculated_cost

    # Baseline from policy
    expected_cost_inr = float(policy.get("expected_cost_inr", settings.default_expected_cost_inr))
    max_tool_calls = int(policy.get("max_tool_calls", settings.max_tool_calls_default))
    max_retries = int(policy.get("max_retries", settings.max_retries_default))
    latency_budget_ms = int(policy.get("latency_budget_ms", settings.default_latency_budget_ms))

    # Cost multiplier
    if expected_cost_inr > 0:
        cost_multiplier = estimated_cost_inr / expected_cost_inr
    else:
        cost_multiplier = 1.0

    # ── Anomaly checks ────────────────────────────────────────────────────
    if cost_multiplier > settings.cost_multiplier_high:
        reasons.append(
            f"Cost ₹{estimated_cost_inr:.2f} is {cost_multiplier:.1f}x the expected ₹{expected_cost_inr:.2f}"
        )

    if tool_calls > max_tool_calls:
        reasons.append(f"Tool calls ({tool_calls}) exceeded limit ({max_tool_calls})")

    if retries > max_retries:
        reasons.append(f"Retry count ({retries}) exceeded limit ({max_retries})")

    if llm_calls > 5:
        reasons.append(f"Excessive LLM calls: {llm_calls} (potential agent loop)")

    if latency_ms > latency_budget_ms * 3:
        reasons.append(f"Latency {latency_ms}ms is {latency_ms // latency_budget_ms}x the budget {latency_budget_ms}ms")

    if input_tokens + output_tokens > 8000:
        reasons.append(f"High token usage: {input_tokens + output_tokens} total tokens")

    # ── Risk level ────────────────────────────────────────────────────────
    if cost_multiplier > settings.cost_multiplier_high or (tool_calls > max_tool_calls and retries > max_retries):
        risk_level = "HIGH"
    elif cost_multiplier > settings.cost_multiplier_medium or tool_calls > max_tool_calls:
        risk_level = "MEDIUM"
    elif cost_multiplier > 1.5:
        risk_level = "LOW"
    else:
        risk_level = "LOW"
        if not reasons:
            reasons = ["Cost within expected baseline"]

    if not reasons:
        reasons = ["Cost within expected baseline"]

    return CostResult(
        risk_level=risk_level,
        estimated_cost_inr=estimated_cost_inr,
        expected_cost_inr=expected_cost_inr,
        cost_multiplier=cost_multiplier,
        tool_calls=tool_calls,
        model_calls=llm_calls,
        retries=retries,
        latency_ms=latency_ms,
        reasons=reasons,
    )
