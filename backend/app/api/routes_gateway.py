from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.gateway import EvaluateRequest, EvaluateResponse
from app.controlplane.orchestrator import evaluate

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_response(
    req: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluateResponse:
    """
    Primary ControlPlane gateway endpoint.
    Submit an AI response + telemetry for evaluation.
    Returns ALLOW / REPAIR / ESCALATE / BLOCK decision with full risk breakdown.
    """
    return await evaluate(req, db)
