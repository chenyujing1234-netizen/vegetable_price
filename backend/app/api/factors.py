from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product
from app.schemas.factor import CorrelationReport, FactorOverview
from app.services import factor_service

router = APIRouter()


@router.get("/overview", response_model=FactorOverview)
async def factor_overview(product_id: int, db: AsyncSession = Depends(get_db)):
    product = (
        await db.execute(select(Product).where(Product.id == product_id))
    ).scalar_one()
    return await factor_service.get_factor_overview(product.id, product.name)


@router.get("/correlation/weather", response_model=CorrelationReport)
async def correlation_weather(
    market_id: int,
    product_id: int,
    region_code: str,
    days: int = Query(365, ge=30, le=3650),
    db: AsyncSession = Depends(get_db),
):
    end = date.today()
    start = end - timedelta(days=days)
    return await factor_service.correlate_price_weather(
        db, market_id, product_id, region_code, start, end
    )


@router.get("/event-study/policy")
async def event_study_policy(
    market_id: int,
    product_id: int,
    product_code: str = Query("tomato"),
    window: int = Query(30, ge=7, le=120),
    db: AsyncSession = Depends(get_db),
):
    return await factor_service.event_study_policy(
        db, market_id, product_id, product_code, window
    )


@router.get("/granger/weather")
async def granger_weather(
    market_id: int,
    product_id: int,
    region_code: str,
    feature: str = Query("temp_avg", pattern="^(temp_avg|temp_max|temp_min|precip|humidity)$"),
    days: int = Query(720, ge=120, le=3650),
    max_lag: int = Query(7, ge=1, le=21),
    db: AsyncSession = Depends(get_db),
):
    return await factor_service.granger_weather_to_price(
        db, market_id, product_id, region_code, feature, days, max_lag
    )
