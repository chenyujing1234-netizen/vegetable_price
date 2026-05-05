from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Policy
from app.schemas.policy import PolicyOut

router = APIRouter()


@router.get("", response_model=list[PolicyOut])
async def list_policies(
    days: int = Query(720, ge=1, le=3650),
    product: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days)
    q = (
        select(Policy)
        .where(Policy.publish_date >= since)
        .order_by(Policy.publish_date.desc())
    )
    if product:
        q = q.where(Policy.related_products.any(product))
    rows = (await db.execute(q)).scalars().all()
    return rows
