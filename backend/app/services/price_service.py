"""价格相关业务逻辑"""

from datetime import date, timedelta
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Market, PriceDaily, Product
from app.schemas.price import PriceHeatPoint, PriceLatest, PricePoint, PriceSeries


async def get_price_series(
    db: AsyncSession,
    market_id: int,
    product_id: int,
    start: date,
    end: date,
) -> PriceSeries:
    market = (await db.execute(select(Market).where(Market.id == market_id))).scalar_one()
    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one()

    rows = (
        await db.execute(
            select(PriceDaily)
            .where(
                and_(
                    PriceDaily.market_id == market_id,
                    PriceDaily.product_id == product_id,
                    PriceDaily.date >= start,
                    PriceDaily.date <= end,
                )
            )
            .order_by(PriceDaily.date.asc())
        )
    ).scalars().all()

    points = [
        PricePoint(
            date=r.date,
            avg=float(r.avg),
            low=float(r.low) if r.low is not None else None,
            high=float(r.high) if r.high is not None else None,
            volume=float(r.volume) if r.volume is not None else None,
        )
        for r in rows
    ]
    return PriceSeries(
        market_id=market.id,
        market_name=market.name,
        product_id=product.id,
        product_name=product.name,
        points=points,
    )


async def get_latest_with_changes(
    db: AsyncSession,
    product_id: int,
    market_id: int | None = None,
) -> Sequence[PriceLatest]:
    """获取最新价格 + 同比/环比/周环比"""
    today = (
        await db.execute(
            select(func.max(PriceDaily.date)).where(PriceDaily.product_id == product_id)
        )
    ).scalar_one_or_none()
    if today is None:
        return []

    yoy_date = today - timedelta(days=365)
    mom_date = today - timedelta(days=30)
    wow_date = today - timedelta(days=7)

    q = select(
        PriceDaily.market_id,
        Market.name.label("market_name"),
        PriceDaily.avg,
    ).join(Market, Market.id == PriceDaily.market_id).where(
        PriceDaily.product_id == product_id, PriceDaily.date == today
    )
    if market_id is not None:
        q = q.where(PriceDaily.market_id == market_id)
    today_rows = (await db.execute(q)).all()

    async def _avg_at(d: date) -> dict[int, float]:
        r = await db.execute(
            select(PriceDaily.market_id, PriceDaily.avg).where(
                and_(PriceDaily.product_id == product_id, PriceDaily.date == d)
            )
        )
        return {mid: float(avg) for mid, avg in r.all()}

    yoy_map = await _avg_at(yoy_date)
    mom_map = await _avg_at(mom_date)
    wow_map = await _avg_at(wow_date)

    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one()

    out: list[PriceLatest] = []
    for mid, mname, avg in today_rows:
        avg_f = float(avg)
        out.append(
            PriceLatest(
                market_id=mid,
                market_name=mname,
                product_id=product.id,
                product_name=product.name,
                date=today,
                avg=avg_f,
                yoy=_pct(avg_f, yoy_map.get(mid)),
                mom=_pct(avg_f, mom_map.get(mid)),
                wow=_pct(avg_f, wow_map.get(mid)),
            )
        )
    return out


async def get_heatmap(db: AsyncSession, product_id: int) -> Sequence[PriceHeatPoint]:
    today = (
        await db.execute(
            select(func.max(PriceDaily.date)).where(PriceDaily.product_id == product_id)
        )
    ).scalar_one_or_none()
    if today is None:
        return []
    yoy_date = today.replace(year=today.year - 1) if today.month != 2 or today.day != 29 else today - timedelta(days=365)

    rows = (
        await db.execute(
            select(
                Market.id,
                Market.name,
                Market.region_code,
                Market.lng,
                Market.lat,
                PriceDaily.avg,
            )
            .join(PriceDaily, PriceDaily.market_id == Market.id)
            .where(
                and_(
                    PriceDaily.product_id == product_id,
                    PriceDaily.date == today,
                )
            )
        )
    ).all()

    yoy_map = dict(
        (await db.execute(
            select(PriceDaily.market_id, PriceDaily.avg).where(
                and_(PriceDaily.product_id == product_id, PriceDaily.date == yoy_date)
            )
        )).all()
    )

    out = []
    for mid, name, rcode, lng, lat, avg in rows:
        avg_f = float(avg)
        prev = yoy_map.get(mid)
        out.append(
            PriceHeatPoint(
                market_id=mid,
                market_name=name,
                region_code=rcode,
                lng=lng,
                lat=lat,
                avg=avg_f,
                yoy=_pct(avg_f, float(prev)) if prev is not None else None,
            )
        )
    return out


def _pct(curr: float, base: float | None) -> float | None:
    if base is None or base == 0:
        return None
    return round((curr - base) / base * 100, 2)
