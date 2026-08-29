from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Incident, RiskAssessment, HumanReview
from app.schemas.incident import IncidentListItem, IncidentDetail, ReviewRequest, DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Aggregate KPIs for the main dashboard."""
    try:
        # Total requests from risk assessments
        total_stmt = select(func.count(RiskAssessment.id))
        total = (await db.execute(total_stmt)).scalar() or 0

        # Action breakdown
        action_stmt = select(
            RiskAssessment.action,
            func.count(RiskAssessment.id)
        ).group_by(RiskAssessment.action)
        action_rows = (await db.execute(action_stmt)).all()
        action_counts = {row[0]: row[1] for row in action_rows if row[0]}

        allowed = action_counts.get("ALLOW", 0)
        repaired = action_counts.get("REPAIR", 0)
        escalated = action_counts.get("ESCALATE", 0)
        blocked = action_counts.get("BLOCK", 0)

        # Cost saved estimate
        # Simple estimate: ₹1.22 saved per high-cost incident
        high_cost_stmt = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.cost_risk.in_(["HIGH", "CRITICAL"])
        )
        high_cost_count = (await db.execute(high_cost_stmt)).scalar() or 0
        cost_saved = round(high_cost_count * 1.22, 2)

        # Average evaluation latency
        latency_stmt = select(func.avg(RiskAssessment.total_evaluation_ms))
        avg_latency = (await db.execute(latency_stmt)).scalar() or 0

        # Risk rates
        perf_risk_stmt = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.performance_risk.in_(["HIGH", "CRITICAL"])
        )
        perf_risk_count = (await db.execute(perf_risk_stmt)).scalar() or 0

        cost_risk_stmt = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.cost_risk.in_(["HIGH", "CRITICAL"])
        )
        cost_risk_count = (await db.execute(cost_risk_stmt)).scalar() or 0

        resp_risk_stmt = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.responsibility_risk.in_(["HIGH", "CRITICAL"])
        )
        resp_risk_count = (await db.execute(resp_risk_stmt)).scalar() or 0

        def rate(n): return round(n / total, 3) if total > 0 else 0.0

        # Recent incidents
        recent_stmt = (
            select(Incident)
            .order_by(Incident.created_at.desc())
            .limit(10)
        )
        recent_rows = (await db.execute(recent_stmt)).scalars().all()
        recent_incidents = [_incident_to_list_item(i) for i in recent_rows]

        # Risk trend (last 24 hours, hourly)
        risk_trend = await _get_risk_trend(db)

        return DashboardSummary(
            total_requests=total,
            allowed=allowed,
            repaired=repaired,
            escalated=escalated,
            blocked=blocked,
            estimated_cost_saved_inr=cost_saved,
            average_evaluation_ms=round(float(avg_latency), 1),
            performance_risk_rate=rate(perf_risk_count),
            cost_risk_rate=rate(cost_risk_count),
            responsibility_risk_rate=rate(resp_risk_count),
            intervention_rate=rate(repaired + escalated + blocked),
            recent_incidents=recent_incidents,
            risk_trend=risk_trend,
            action_breakdown={
                "ALLOW": allowed,
                "REPAIR": repaired,
                "ESCALATE": escalated,
                "BLOCK": blocked,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _get_risk_trend(db: AsyncSession) -> list[dict]:
    """Get hourly risk data for the last 24 hours."""
    try:
        from sqlalchemy import text
        # strftime works on both SQLite and can be adapted for Postgres
        result = await db.execute(text("""
            SELECT
                strftime('%Y-%m-%dT%H:00:00', created_at) as hour,
                COUNT(*) as total,
                SUM(CASE WHEN action = 'BLOCK' THEN 1 ELSE 0 END) as blocked,
                SUM(CASE WHEN action = 'REPAIR' THEN 1 ELSE 0 END) as repaired,
                SUM(CASE WHEN action = 'ESCALATE' THEN 1 ELSE 0 END) as escalated
            FROM risk_assessments
            WHERE created_at >= datetime('now', '-24 hours')
            GROUP BY strftime('%Y-%m-%dT%H:00:00', created_at)
            ORDER BY hour
        """))
        rows = result.all()
        return [
            {
                "hour": row[0] or "",
                "total": row[1] or 0,
                "blocked": row[2] or 0,
                "repaired": row[3] or 0,
                "escalated": row[4] or 0,
            }
            for row in rows
        ]
    except Exception:
        return []



router_incidents = APIRouter()


@router_incidents.get("", response_model=list[IncidentListItem])
async def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List incidents with optional filters."""
    stmt = select(Incident).order_by(Incident.created_at.desc())
    if status:
        stmt = stmt.where(Incident.status == status)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if incident_type:
        stmt = stmt.where(Incident.incident_type == incident_type)
    stmt = stmt.offset(skip).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [_incident_to_list_item(i) for i in rows]


@router_incidents.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get full forensic detail for an incident."""
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = (await db.execute(stmt)).scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Load risk assessment
    ra_stmt = select(RiskAssessment).where(RiskAssessment.id == incident.risk_assessment_id)
    ra = (await db.execute(ra_stmt)).scalar_one_or_none()

    # Load reviews
    rev_stmt = select(HumanReview).where(HumanReview.incident_id == incident_id)
    reviews = (await db.execute(rev_stmt)).scalars().all()

    detail = _incident_to_list_item(incident)
    return IncidentDetail(
        **detail.model_dump(),
        evidence=incident.evidence or {},
        repaired_response_text=incident.repaired_response_text,
        human_reviews=[
            {
                "id": r.id,
                "reviewer_name": r.reviewer_name,
                "action": r.review_action,
                "comment": r.comment,
                "was_correct": r.was_correct,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in reviews
        ],
        risk_assessment={
            "performance_score": float(ra.performance_score or 0) if ra else 0,
            "cost_score": float(ra.cost_score or 0) if ra else 0,
            "responsibility_score": float(ra.responsibility_score or 0) if ra else 0,
            "overall_risk_score": float(ra.overall_risk_score or 0) if ra else 0,
            "fast_screen_ms": ra.fast_screen_ms if ra else 0,
            "total_evaluation_ms": ra.total_evaluation_ms if ra else 0,
        } if ra else None,
    )


@router_incidents.post("/{incident_id}/review")
async def review_incident(
    incident_id: str,
    review: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a human review decision on an incident."""
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = (await db.execute(stmt)).scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    hr = HumanReview(
        incident_id=incident_id,
        reviewer_name=review.reviewer_name,
        review_action=review.action,
        comment=review.comment,
        original_action=incident.action,
        final_action=review.action.upper() if review.action in ("approve", "reject") else incident.action,
        was_correct=review.was_correct,
    )
    db.add(hr)

    # Update incident status
    incident.status = "resolved"
    if review.action == "approve":
        incident.action = "ALLOW"
    elif review.action == "reject":
        incident.action = "BLOCK"

    await db.flush()
    return {"message": "Review recorded", "incident_id": incident_id, "action": review.action}


def _incident_to_list_item(i: Incident) -> IncidentListItem:
    return IncidentListItem(
        id=i.id,
        incident_type=i.incident_type or "unknown",
        severity=i.severity or "LOW",
        action=i.action or "ALLOW",
        status=i.status or "open",
        reason=i.reason or "",
        application_name=i.application_name or "",
        request_text=i.request_text or "",
        response_text=(i.response_text or "")[:200],
        created_at=i.created_at or datetime.now(timezone.utc),
    )
