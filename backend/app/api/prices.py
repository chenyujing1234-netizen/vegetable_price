from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.price import PriceHeatPoint, PriceLatest, PriceSeries
from app.services import price_service

router = APIRouter()


@router.get("/series", response_model=PriceSeries)
async def price_series(
    market_id: int,
    product_id: int,
    start: date | None = Query(None),
    end: date | None = Query(None),
    days: int = Query(365, ge=1, le=3650),
    db: AsyncSession = Depends(get_db),
):
    end = end or date.today()
    start = start or (end - timedelta(days=days))
    try:
        return await price_service.get_price_series(db, market_id, product_id, start, end)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/latest", response_model=list[PriceLatest])
async def latest_prices(
    product_id: int,
    market_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return list(await price_service.get_latest_with_changes(db, product_id, market_id))


@router.get("/heatmap", response_model=list[PriceHeatPoint])
async def heatmap(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    return list(await price_service.get_heatmap(db, product_id))
