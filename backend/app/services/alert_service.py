"""价格告警评估器：扫描所有启用的告警规则，命中即记录并触发通知

通知通道：
- email: 写入日志 + 可在生产接入 SES/SendGrid
- webhook: HTTP POST
- sms: 可在生产接入阿里云 / 腾讯云 SMS
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

import httpx
from loguru import logger
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Market, PriceAlert, PriceDaily, Product, User


async def evaluate_all(db: AsyncSession) -> list[dict]:
    alerts = (
        await db.execute(select(PriceAlert).where(PriceAlert.is_active.is_(True)))
    ).scalars().all()
    triggered = []
    for a in alerts:
        hit = await _eval_one(db, a)
        if hit:
            await _send(db, a, hit)
            a.last_triggered_at = datetime.utcnow()
            triggered.append(hit)
    if triggered:
        await db.commit()
    return triggered


async def _eval_one(db: AsyncSession, a: PriceAlert) -> dict | None:
    today = (await db.execute(
        select(func.max(PriceDaily.date)).where(PriceDaily.product_id == a.product_id)
    )).scalar_one_or_none()
    if today is None:
        return None

    q = select(func.avg(PriceDaily.avg)).where(
        and_(PriceDaily.product_id == a.product_id, PriceDaily.date == today)
    )
    if a.market_id is not None:
        q = q.where(PriceDaily.market_id == a.market_id)
    avg_today = (await db.execute(q)).scalar_one_or_none()
    if avg_today is None:
        return None
    avg_today = float(avg_today)
    threshold = float(a.threshold)

    fired = False
    detail: dict = {"date": str(today), "current": avg_today, "threshold": threshold}

    if a.rule == "below" and avg_today < threshold:
        fired = True
    elif a.rule == "above" and avg_today > threshold:
        fired = True
    elif a.rule in ("yoy_above", "mom_above"):
        ref_date = today - (timedelta(days=365) if a.rule == "yoy_above" else timedelta(days=30))
        ref_q = select(func.avg(PriceDaily.avg)).where(
            and_(PriceDaily.product_id == a.product_id, PriceDaily.date == ref_date)
        )
        if a.market_id is not None:
            ref_q = ref_q.where(PriceDaily.market_id == a.market_id)
        ref = (await db.execute(ref_q)).scalar_one_or_none()
        if ref:
            change = (avg_today - float(ref)) / float(ref) * 100
            detail["change_pct"] = round(change, 2)
            if change > threshold:
                fired = True

    if not fired:
        return None

    return {"alert_id": a.id, "user_id": a.user_id, **detail, "rule": a.rule}


async def _send(db: AsyncSession, a: PriceAlert, hit: dict):
    user = (await db.execute(select(User).where(User.id == a.user_id))).scalar_one_or_none()
    market = None
    if a.market_id:
        market = (await db.execute(select(Market).where(Market.id == a.market_id))).scalar_one_or_none()
    product = (await db.execute(select(Product).where(Product.id == a.product_id))).scalar_one()

    msg = (
        f"[菜价·智算] {product.name} "
        f"{market.name if market else '全国均价'} 告警触发：当前 ¥{hit['current']:.2f} "
        f"规则 {a.rule} 阈值 {hit['threshold']}"
    )

    channels = (a.channel or "").split(",")
    if "email" in channels:
        logger.info(f"[EMAIL] -> {user.email if user else 'unknown'}: {msg}")
    if "webhook" in channels and a.webhook_url:
        try:
            with httpx.Client(timeout=10) as c:
                c.post(a.webhook_url, json={"alert": hit, "message": msg})
            logger.info(f"[WEBHOOK] -> {a.webhook_url}: ok")
        except Exception as e:
            logger.warning(f"webhook failed: {e}")
    if "sms" in channels:
        logger.info(f"[SMS-stub] -> {user.email if user else 'unknown'}: {msg}")
