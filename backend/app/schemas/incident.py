from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class IncidentListItem(BaseModel):
    id: str
    incident_type: str
    severity: str
    action: str
    status: str
    reason: str
    application_name: str
    request_text: str
    response_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentDetail(IncidentListItem):
    evidence: dict
    repaired_response_text: Optional[str] = None
    human_reviews: list[dict] = []
    risk_assessment: Optional[dict] = None


class ReviewRequest(BaseModel):
    reviewer_name: str = "Reviewer"
    action: str  # approve / reject / override
    comment: str = ""
    was_correct: str = "yes"  # yes / false_positive / false_negative


class DashboardSummary(BaseModel):
    total_requests: int
    allowed: int
    repaired: int
    escalated: int
    blocked: int
    estimated_cost_saved_inr: float
    average_evaluation_ms: float
    performance_risk_rate: float
    cost_risk_rate: float
    responsibility_risk_rate: float
    intervention_rate: float
    recent_incidents: list[IncidentListItem] = []
    risk_trend: list[dict] = []
    action_breakdown: dict = {}
