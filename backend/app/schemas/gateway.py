from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field


class TelemetryIn(BaseModel):
    model: str = "demo-model"
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 1
    tool_calls: int = 0
    retrieval_calls: int = 0
    retries: int = 0
    latency_ms: int = 0
    estimated_cost: float = 0.0
    currency: str = "INR"


class RequestIn(BaseModel):
    text: str


class ResponseIn(BaseModel):
    text: str


class ContextIn(BaseModel):
    country: str = "IN"
    use_case: str = "customer_support"
    business_impact: str = "medium"  # low/medium/high/critical
    conversation_history: list[dict] = Field(default_factory=list)
    trusted_data: dict = Field(default_factory=dict)  # e.g., order records


class EvaluateRequest(BaseModel):
    application_id: str = "customer-support"
    conversation_id: Optional[str] = None
    request: RequestIn
    response: ResponseIn
    context: ContextIn = Field(default_factory=ContextIn)
    telemetry: TelemetryIn = Field(default_factory=TelemetryIn)


class RiskDimension(BaseModel):
    score: float
    level: str


class RiskSummary(BaseModel):
    performance: RiskDimension
    cost: RiskDimension
    responsibility: RiskDimension
    overall: RiskDimension


class EvaluateResponse(BaseModel):
    decision: str  # ALLOW / REPAIR / ESCALATE / BLOCK
    final_response: str
    original_response: str
    risk: RiskSummary
    reasons: list[str]
    incident_id: Optional[str] = None
    repair_applied: bool = False
    fast_screen_ms: int = 0
    total_evaluation_ms: int = 0
    pii_entities: list[dict] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
