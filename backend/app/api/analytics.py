"""综合统计接口：用于首页 dashboard summary"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CroplandYearly, Market, PriceDaily, Product

router = APIRouter()


@router.get("/dashboard")
async def dashboard_summary(
    product_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    today = (
        await db.execute(
            select(func.max(PriceDaily.date)).where(PriceDaily.product_id == product_id)
        )
    ).scalar_one_or_none()
    if today is None:
        return {"product_id": product_id, "message": "no data"}

    yoy_date = today - timedelta(days=365)
    mom_date = today - timedelta(days=30)

    today_avg = (
        await db.execute(
            select(func.avg(PriceDaily.avg)).where(
                PriceDaily.product_id == product_id, PriceDaily.date == today
            )
        )
    ).scalar_one()
    yoy_avg = (
        await db.execute(
            select(func.avg(PriceDaily.avg)).where(
                PriceDaily.product_id == product_id, PriceDaily.date == yoy_date
            )
        )
    ).scalar_one()
    mom_avg = (
        await db.execute(
            select(func.avg(PriceDaily.avg)).where(
                PriceDaily.product_id == product_id, PriceDaily.date == mom_date
            )
        )
    ).scalar_one()

    market_count = (
        await db.execute(select(func.count(Market.id)))
    ).scalar_one()

    cropland_latest_year = (
        await db.execute(
            select(func.max(CroplandYearly.year)).where(
                CroplandYearly.product_id == product_id
            )
        )
    ).scalar_one_or_none()
    cropland_total = None
    cropland_yoy = None
    if cropland_latest_year:
        cropland_total = (
            await db.execute(
                select(func.sum(CroplandYearly.area_mu)).where(
                    CroplandYearly.product_id == product_id,
                    CroplandYearly.year == cropland_latest_year,
                )
            )
        ).scalar_one_or_none()
        prev_total = (
            await db.execute(
                select(func.sum(CroplandYearly.area_mu)).where(
                    CroplandYearly.product_id == product_id,
                    CroplandYearly.year == cropland_latest_year - 1,
                )
            )
        ).scalar_one_or_none()
        if cropland_total and prev_total:
            cropland_yoy = round(
                (float(cropland_total) - float(prev_total)) / float(prev_total) * 100, 2
            )

    product = (
        await db.execute(select(Product).where(Product.id == product_id))
    ).scalar_one()

    def _f(v):
        return float(v) if v is not None else None

    today_avg_f = _f(today_avg)
    yoy_avg_f = _f(yoy_avg)
    mom_avg_f = _f(mom_avg)

    return {
        "product_id": product.id,
        "product_name": product.name,
        "as_of": today,
        "national_avg_price": today_avg_f,
        "yoy_pct": _pct(today_avg_f, yoy_avg_f),
        "mom_pct": _pct(today_avg_f, mom_avg_f),
        "market_coverage": int(market_count),
        "cropland_latest_year": cropland_latest_year,
        "cropland_total_mu": _f(cropland_total),
        "cropland_yoy_pct": cropland_yoy,
    }


def _pct(curr, base):
    if curr is None or base is None or base == 0:
        return None
    return round((curr - base) / base * 100, 2)
