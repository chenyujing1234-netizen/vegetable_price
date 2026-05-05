from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_user
from app.database import get_db
from app.models import PriceAlert, User
from app.services.alert_service import evaluate_all

router = APIRouter()


class AlertIn(BaseModel):
    market_id: int | None = None
    product_id: int
    rule: str = "below"
    threshold: float
    channel: str = "email"
    webhook_url: str | None = None


class AlertOut(BaseModel):
    id: int
    market_id: int | None
    product_id: int
    rule: str
    threshold: float
    channel: str
    webhook_url: str | None
    is_active: bool
    last_triggered_at: datetime | None
    created_at: datetime


@router.get("", response_model=list[AlertOut])
async def list_my_alerts(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(PriceAlert).where(PriceAlert.user_id == user.id).order_by(PriceAlert.id.desc())
    )).scalars().all()
    return [AlertOut(
        id=r.id,
        market_id=r.market_id,
        product_id=r.product_id,
        rule=r.rule,
        threshold=float(r.threshold),
        channel=r.channel,
        webhook_url=r.webhook_url,
        is_active=r.is_active,
        last_triggered_at=r.last_triggered_at,
        created_at=r.created_at,
    ) for r in rows]


@router.post("", response_model=AlertOut)
async def create_alert(
    body: AlertIn,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    a = PriceAlert(
        user_id=user.id,
        market_id=body.market_id,
        product_id=body.product_id,
        rule=body.rule,
        threshold=body.threshold,
        channel=body.channel,
        webhook_url=body.webhook_url,
    )
    db.add(a)
    await db.commit()
    return AlertOut(
        id=a.id,
        market_id=a.market_id,
        product_id=a.product_id,
        rule=a.rule,
        threshold=float(a.threshold),
        channel=a.channel,
        webhook_url=a.webhook_url,
        is_active=a.is_active,
        last_triggered_at=a.last_triggered_at,
        created_at=a.created_at,
    )


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    a = (await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id, PriceAlert.user_id == user.id)
    )).scalar_one_or_none()
    if a is None:
        raise HTTPException(404, "not found")
    await db.delete(a)
    await db.commit()
    return {"deleted": alert_id}


@router.post("/evaluate")
async def evaluate(db: AsyncSession = Depends(get_db)):
    """触发一次告警评估（生产环境用 Celery Beat 调度）"""
    triggered = await evaluate_all(db)
    return {"triggered": triggered, "count": len(triggered)}
