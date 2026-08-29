from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import Policy, PolicyVersion

router = APIRouter()


class PolicyOut(BaseModel):
    id: str
    name: str
    description: str | None
    use_case: str | None
    geography: str | None
    versions: list[dict] = []


@router.get("", response_model=list[PolicyOut])
async def list_policies(db: AsyncSession = Depends(get_db)):
    """List all policies with their versions."""
    stmt = select(Policy)
    policies = (await db.execute(stmt)).scalars().all()
    result = []
    for p in policies:
        ver_stmt = select(PolicyVersion).where(PolicyVersion.policy_id == p.id).order_by(PolicyVersion.version.desc())
        versions = (await db.execute(ver_stmt)).scalars().all()
        result.append(PolicyOut(
            id=p.id,
            name=p.name,
            description=p.description,
            use_case=p.use_case,
            geography=p.geography,
            versions=[
                {
                    "version": v.version,
                    "status": v.status,
                    "config": v.config,
                    "effective_from": v.effective_from.isoformat() if v.effective_from else "",
                }
                for v in versions
            ],
        ))
    return result
