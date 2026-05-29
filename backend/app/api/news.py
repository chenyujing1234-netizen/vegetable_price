from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import News
from app.schemas.news import NewsAnalyzeOut, NewsDailySentiment, NewsDetailOut, NewsOut
from app.services.news_analysis_service import analyze_news_item

router = APIRouter()


def _to_out(row: News) -> NewsOut:
    return NewsOut(
        id=row.id,
        title=row.title,
        source=row.source,
        url=row.url,
        publish_at=row.publish_at,
        sentiment_score=float(row.sentiment_score) if row.sentiment_score is not None else None,
        sentiment_label=row.sentiment_label,
        keywords=row.keywords or [],
        analysis_status=row.analysis_status or "none",
        analysis_summary=row.analysis_summary,
        has_analysis=row.analysis_status == "done" and bool(row.analysis_summary),
    )


@router.get("/sentiment-daily", response_model=list[NewsDailySentiment])
async def sentiment_daily(
    days: int = Query(30, ge=1, le=1095),
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


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)):
    """已入库新闻的来源站点统计"""
    q = (
        select(News.source, func.count(News.id))
        .group_by(News.source)
        .order_by(func.count(News.id).desc())
    )
    rows = (await db.execute(q)).all()
    return [{"source": s, "count": int(n)} for s, n in rows]


@router.get("", response_model=list[NewsOut])
async def list_news(
    days: int = Query(30, ge=1, le=1095),
    limit: int = Query(50, ge=1, le=500),
    product: str | None = None,
    source: str | None = Query(None, description="按来源名过滤，如 农民日报"),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    q = select(News).where(News.publish_at >= since).order_by(News.publish_at.desc()).limit(limit)
    if product:
        q = q.where(News.related_products.any(product))
    if source:
        q = q.where(News.source.ilike(f"%{source}%"))
    rows = (await db.execute(q)).scalars().all()
    return [_to_out(r) for r in rows]


@router.get("/{news_id}", response_model=NewsDetailOut)
async def get_news(news_id: int, db: AsyncSession = Depends(get_db)):
    row = await db.get(News, news_id)
    if not row:
        raise HTTPException(404, "新闻不存在")
    base = _to_out(row)
    return NewsDetailOut(
        **base.model_dump(),
        content=row.content,
        analysis_detail=row.analysis_detail,
        analyzed_at=row.analyzed_at,
        related_products=row.related_products or [],
    )


@router.post("/{news_id}/analyze", response_model=NewsAnalyzeOut)
async def analyze_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """用户点击「解读」时按需分析：抓取正文 → 情感 + 平台观点"""
    try:
        row = await analyze_news_item(db, news_id)
        await db.commit()
    except ValueError:
        raise HTTPException(404, "新闻不存在")
    except Exception as e:
        await db.rollback()
        raise HTTPException(502, f"解读失败: {e}") from e

    return NewsAnalyzeOut(
        id=row.id,
        title=row.title,
        analysis_status=row.analysis_status,
        analysis_summary=row.analysis_summary,
        analysis_detail=row.analysis_detail,
        sentiment_label=row.sentiment_label,
        sentiment_score=float(row.sentiment_score) if row.sentiment_score is not None else None,
        analyzed_at=row.analyzed_at,
    )
