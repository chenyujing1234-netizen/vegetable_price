from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Region, WeatherDaily
from app.schemas.weather import WeatherPoint, WeatherSeries

router = APIRouter()


@router.get("/series", response_model=WeatherSeries)
async def weather_series(
    region_code: str,
    days: int = Query(365, ge=1, le=3650),
    db: AsyncSession = Depends(get_db),
):
    end = date.today()
    start = end - timedelta(days=days)
    region = (
        await db.execute(select(Region).where(Region.code == region_code))
    ).scalar_one_or_none()
    rows = (
        await db.execute(
            select(WeatherDaily)
            .where(
                WeatherDaily.region_code == region_code,
                WeatherDaily.date >= start,
                WeatherDaily.date <= end,
            )
            .order_by(WeatherDaily.date.asc())
        )
    ).scalars().all()

    points = [
        WeatherPoint(
            date=r.date,
            temp_min=float(r.temp_min) if r.temp_min is not None else None,
            temp_max=float(r.temp_max) if r.temp_max is not None else None,
            temp_avg=float(r.temp_avg) if r.temp_avg is not None else None,
            precip=float(r.precip) if r.precip is not None else None,
            humidity=float(r.humidity) if r.humidity is not None else None,
            wind_speed=float(r.wind_speed) if r.wind_speed is not None else None,
            weather=r.weather,
        )
        for r in rows
    ]
    return WeatherSeries(
        region_code=region_code,
        region_name=region.name if region else region_code,
        points=points,
    )
