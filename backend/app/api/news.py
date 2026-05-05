from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import News
from app.schemas.news import NewsDailySentiment, NewsOut

router = APIRouter()


@router.get("", response_model=list[NewsOut])
async def list_news(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=500),
    product: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    q = select(News).where(News.publish_at >= since).order_by(News.publish_at.desc()).limit(limit)
    if product:
        q = q.where(News.related_products.any(product))
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.get("/sentiment-daily", response_model=list[NewsDailySentiment])
async def sentiment_daily(
    days: int = Query(30, ge=1, le=365),
    product: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    day = func.date(News.publish_at).label("d")
    q = (
        select(
            day,
            func.avg(News.sentiment_score).label("avg_s"),
            func.count(News.id).label("n"),
        )
        .where(News.publish_at >= since, News.sentiment_score.is_not(None))
        .group_by(day)
        .order_by(day)
    )
    if product:
        q = q.where(News.related_products.any(product))
    rows = (await db.execute(q)).all()
    return [
        NewsDailySentiment(date=str(d), avg_sentiment=float(s) if s else 0.0, count=int(n))
        for d, s, n in rows
    ]
