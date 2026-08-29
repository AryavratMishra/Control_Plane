from __future__ import annotations

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("")
async def health():
    return {
        "status": "healthy",
        "service": "ControlPlane.ai Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
