from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FastScreenResult:
    risk_level: str  # LOW / MEDIUM / HIGH / CRITICAL
    triggers: list[str] = field(default_factory=list)
    hard_block: bool = False
    needs_deep_check: bool = False
    latency_ms: int = 0
    pii_quick_hits: list[str] = field(default_factory=list)
    cost_signal: Optional[str] = None


@dataclass
class PerformanceResult:
    risk_level: str  # LOW / MEDIUM / HIGH / CRITICAL / UNVERIFIED
    grounding_score: float = 0.0
    evidence_coverage: float = 0.0
    contradiction_detected: bool = False
    unsupported_claim_count: int = 0
    confidence: float = 0.5
    reasons: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)


@dataclass
class CostResult:
    risk_level: str  # LOW / MEDIUM / HIGH / CRITICAL
    estimated_cost_inr: float = 0.0
    expected_cost_inr: float = 0.20
    cost_multiplier: float = 1.0
    tool_calls: int = 0
    model_calls: int = 1
    retries: int = 0
    latency_ms: int = 0
    reasons: list[str] = field(default_factory=list)


@dataclass
class PiiEntity:
    entity_type: str
    text: str
    start: int
    end: int
    confidence: float
    policy_action: str = "redact"  # redact / block / allow


@dataclass
class PolicyViolation:
    rule_id: str
    description: str
    severity: str
    action: str


@dataclass
class ResponsibilityResult:
    risk_level: str  # LOW / MEDIUM / HIGH / CRITICAL
    pii_detected: bool = False
    pii_entities: list[PiiEntity] = field(default_factory=list)
    policy_violations: list[PolicyViolation] = field(default_factory=list)
    safety_signal: Optional[str] = None
    bias_signal: Optional[str] = None
    confidence: float = 0.5
    reasons: list[str] = field(default_factory=list)


@dataclass
class RiskDecision:
    overall_score: float
    overall_level: str  # LOW / MEDIUM / HIGH / CRITICAL
    action: str  # ALLOW / REPAIR / ESCALATE / BLOCK
    reasons: list[str] = field(default_factory=list)
    requires_human: bool = False
    can_repair: bool = False
    hard_rule_triggered: bool = False
    performance_score: float = 0.0
    cost_score: float = 0.0
    responsibility_score: float = 0.0
