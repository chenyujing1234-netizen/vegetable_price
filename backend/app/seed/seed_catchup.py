"""把所有市场 × 产品的价格、所有区域的天气补齐到今天。

种子数据是按 `date.today()` 一次性合成的，时间长了之后老市场的"最新一天"
会落后，导致首页"主要市场最新价格"和价格热力图（都按全局 max(date) 取数）
只能看到最近一次入数据的那些市场。本脚本幂等地补齐所有缺失日期。

执行：``python -m app.seed.seed_catchup``
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from loguru import logger
from sqlalchemy import and_, func, select

from app.database import AsyncSessionLocal
from app.models import Market, PriceDaily, Product, Region, WeatherDaily
from app.seed.seed_data import (
    MARKET_BASE_PRICE,
    synth_other_veg_price,
    synth_tomato_price,
    synth_weather,
)


async def catchup_prices(session) -> int:
    today = date.today()
    markets = (await session.execute(select(Market))).scalars().all()
    products = (await session.execute(select(Product))).scalars().all()

    inserted = 0
    batch: list[dict] = []
    for m in markets:
        base = MARKET_BASE_PRICE.get(m.code, 4.5)
        for p in products:
            last = (
                await session.execute(
                    select(func.max(PriceDaily.date)).where(
                        and_(
                            PriceDaily.market_id == m.id,
                            PriceDaily.product_id == p.id,
                        )
                    )
                )
            ).scalar_one_or_none()
            if last is None or last >= today:
                continue
            d = last + timedelta(days=1)
            while d <= today:
                if p.code == "tomato":
                    low, avg, high = synth_tomato_price(m.code, d, base)
                else:
                    low, avg, high = synth_other_veg_price(p.code, m.code, d, base)
                batch.append(
                    {
                        "market_id": m.id,
                        "product_id": p.id,
                        "date": d,
                        "low": low,
                        "avg": avg,
                        "high": high,
                        "volume": None,
                        "source": "seed_catchup",
                    }
                )
                d += timedelta(days=1)
                if len(batch) >= 5000:
                    await session.execute(PriceDaily.__table__.insert(), batch)
                    inserted += len(batch)
                    batch.clear()
    if batch:
        await session.execute(PriceDaily.__table__.insert(), batch)
        inserted += len(batch)
    logger.info(f"价格补齐：新增 {inserted} 条")
    return inserted


async def catchup_weather(session) -> int:
    today = date.today()
    regions = (await session.execute(select(Region))).scalars().all()
    inserted = 0
    batch: list[dict] = []
    for r in regions:
        last = (
            await session.execute(
                select(func.max(WeatherDaily.date)).where(WeatherDaily.region_code == r.code)
            )
        ).scalar_one_or_none()
        if last is None or last >= today:
            continue
        d = last + timedelta(days=1)
        while d <= today:
            w = synth_weather(r.code, d)
            batch.append({"region_code": r.code, "date": d, **w, "source": "seed_catchup"})
            d += timedelta(days=1)
            if len(batch) >= 5000:
                await session.execute(WeatherDaily.__table__.insert(), batch)
                inserted += len(batch)
                batch.clear()
    if batch:
        await session.execute(WeatherDaily.__table__.insert(), batch)
        inserted += len(batch)
    logger.info(f"天气补齐：新增 {inserted} 条")
    return inserted


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            logger.info(f"=== 数据补齐到 {date.today()} ===")
            await catchup_prices(session)
            await catchup_weather(session)
        logger.info("=== 补齐完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
