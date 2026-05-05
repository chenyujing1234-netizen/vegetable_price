from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.prediction import ForecastSeries, ModelMetric
from app.services import forecast_service

router = APIRouter()


@router.get("/forecast", response_model=ForecastSeries)
async def forecast(
    market_id: int,
    product_id: int,
    horizon_days: int = Query(30, ge=1, le=365),
    model: str = Query("prophet", pattern="^(prophet|baseline|lstm|ensemble)$"),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await forecast_service.forecast_price(
            db, market_id, product_id, horizon_days, model
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"forecast failed: {e}")


@router.get("/metrics", response_model=list[ModelMetric])
async def metrics():
    return list(await forecast_service.get_model_metrics())
