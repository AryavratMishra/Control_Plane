from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Application, PolicyVersion, Policy

logger = logging.getLogger(__name__)

# Default policy configs by use case
_DEFAULT_POLICIES = {
    "customer_support": {
        "risk_level": "medium",
        "expected_cost_inr": 0.20,
        "latency_budget_ms": 700,
        "max_tool_calls": 5,
        "max_retries": 2,
        "rules": {
            "pii_exposure": "redact",
            "critical_pii_exposure": "block",
            "contradicted_transaction_claim": "repair",
            "unresolved_high_impact_claim": "escalate",
            "severe_safety_violation": "block",
            "moderate_uncertainty": "repair",
        },
        "action_overrides": {},
    },
    "financial_decision_support": {
        "risk_level": "high",
        "expected_cost_inr": 0.50,
        "latency_budget_ms": 1800,
        "max_tool_calls": 8,
        "max_retries": 2,
        "rules": {
            "pii_exposure": "block",
            "critical_pii_exposure": "block",
            "unsupported_financial_claim": "escalate",
            "investment_recommendation": "escalate",
            "severe_safety_violation": "block",
        },
        "action_overrides": {},
    },
    "internal_knowledge": {
        "risk_level": "medium",
        "expected_cost_inr": 0.15,
        "latency_budget_ms": 1200,
        "max_tool_calls": 5,
        "max_retries": 2,
        "rules": {
            "confidential_data_exposure": "block",
            "unverified_low_impact_claim": "repair",
            "critical_internal_policy_conflict": "escalate",
        },
        "action_overrides": {},
    },
    "default": {
        "risk_level": "medium",
        "expected_cost_inr": 0.20,
        "latency_budget_ms": 1000,
        "max_tool_calls": 5,
        "max_retries": 2,
        "rules": {
            "pii_exposure": "redact",
            "critical_pii_exposure": "block",
            "severe_safety_violation": "block",
        },
        "action_overrides": {},
    },
}


async def get_policy(
    application_id: str,
    use_case: str,
    db: AsyncSession | None = None,
) -> dict:
    """
    Load policy for an application/use-case.
    Tries DB first, falls back to default config.
    """
    if db is not None:
        try:
            # Try to find application-specific policy
            stmt = (
                select(PolicyVersion)
                .join(Policy)
                .where(Policy.use_case == use_case)
                .where(PolicyVersion.status == "active")
                .order_by(PolicyVersion.version.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            pv = result.scalar_one_or_none()
            if pv and pv.config:
                return pv.config
        except Exception as e:
            logger.warning(f"Policy DB lookup failed: {e}")

    return _DEFAULT_POLICIES.get(use_case, _DEFAULT_POLICIES["default"])
