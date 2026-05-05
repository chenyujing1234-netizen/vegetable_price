"""增量种子：为新增的漳州（350600）补全 region/market/价格/天气/种植面积。

不会动其他市场/区域已有的数据。可幂等执行：已存在则跳过；价格/天气仅补
该区域/市场缺失的日期。

执行：``python -m app.seed.seed_zhangzhou``
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from loguru import logger
from sqlalchemy import and_, select

from app.database import AsyncSessionLocal
from app.models import (
    CroplandYearly,
    Market,
    PriceDaily,
    Product,
    Region,
    WeatherDaily,
)
from app.seed.seed_data import (
    MARKET_BASE_PRICE,
    MARKETS,
    REGIONS,
    SEED_CROPLAND,
    synth_other_veg_price,
    synth_tomato_price,
    synth_weather,
)


REGION_CODE = "350600"
MARKET_CODE = "zhangzhou_minnan"


async def upsert_region(session) -> Region:
    region_def = next(r for r in REGIONS if r["code"] == REGION_CODE)
    existing = await session.get(Region, REGION_CODE)
    if existing:
        logger.info(f"region {REGION_CODE}({region_def['name']}) 已存在，跳过")
        return existing
    region = Region(**region_def)
    session.add(region)
    await session.flush()
    logger.info(f"已新增 region: {region_def['name']} ({REGION_CODE})")
    return region


async def upsert_market(session) -> Market:
    market_def = next(m for m in MARKETS if m["code"] == MARKET_CODE)
    existing = (
        await session.execute(select(Market).where(Market.code == MARKET_CODE))
    ).scalar_one_or_none()
    if existing:
        logger.info(f"market {MARKET_CODE} 已存在，跳过")
        return existing
    region = await session.get(Region, REGION_CODE)
    market = Market(**market_def, lng=region.lng, lat=region.lat)
    session.add(market)
    await session.flush()
    logger.info(f"已新增 market: {market_def['name']}")
    return market


async def fill_prices(session, market: Market, years: int = 3) -> int:
    """为新增 market 补 N 年日度价格（覆盖所有 product）。"""
    end = date.today()
    start = end - timedelta(days=365 * years)
    base = MARKET_BASE_PRICE.get(market.code, 4.0)

    products = (await session.execute(select(Product))).scalars().all()

    existing_dates = (
        (
            await session.execute(
                select(PriceDaily.date).where(PriceDaily.market_id == market.id)
            )
        )
        .scalars()
        .all()
    )
    skip = set(existing_dates)
    if skip:
        logger.info(
            f"market {market.code} 已有 {len(skip)} 天价格数据，仅补缺失的部分"
        )

    batch: list[dict] = []
    inserted = 0
    for p in products:
        d = start
        while d <= end:
            if d not in skip:
                if p.code == "tomato":
                    low, avg, high = synth_tomato_price(market.code, d, base)
                else:
                    low, avg, high = synth_other_veg_price(p.code, market.code, d, base)
                batch.append(
                    {
                        "market_id": market.id,
                        "product_id": p.id,
                        "date": d,
                        "low": low,
                        "avg": avg,
                        "high": high,
                        "volume": None,
                        "source": "seed_zhangzhou",
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
    logger.info(
        f"已为 {market.name} × {len(products)} 个产品补 {inserted} 条价格记录"
    )
    return inserted


async def fill_weather(session, region_code: str, years: int = 3) -> int:
    end = date.today()
    start = end - timedelta(days=365 * years)
    existing = (
        (
            await session.execute(
                select(WeatherDaily.date).where(WeatherDaily.region_code == region_code)
            )
        )
        .scalars()
        .all()
    )
    skip = set(existing)
    batch: list[dict] = []
    inserted = 0
    d = start
    while d <= end:
        if d not in skip:
            w = synth_weather(region_code, d)
            batch.append(
                {"region_code": region_code, "date": d, **w, "source": "seed_zhangzhou"}
            )
        d += timedelta(days=1)
        if len(batch) >= 5000:
            await session.execute(WeatherDaily.__table__.insert(), batch)
            inserted += len(batch)
            batch.clear()
    if batch:
        await session.execute(WeatherDaily.__table__.insert(), batch)
        inserted += len(batch)
    logger.info(f"已为 region {region_code} 补 {inserted} 条天气记录")
    return inserted


async def fill_cropland(session, region_code: str) -> int:
    products = {
        p.code: p for p in (await session.execute(select(Product))).scalars().all()
    }
    tomato_id = products["tomato"].id

    existing = (
        (
            await session.execute(
                select(CroplandYearly.year).where(
                    and_(
                        CroplandYearly.region_code == region_code,
                        CroplandYearly.product_id == tomato_id,
                    )
                )
            )
        )
        .scalars()
        .all()
    )
    skip = set(existing)

    rows = [c for c in SEED_CROPLAND if c["region_code"] == region_code]
    inserted = 0
    for c in rows:
        if c["year"] in skip:
            continue
        session.add(
            CroplandYearly(
                region_code=c["region_code"],
                product_id=tomato_id,
                year=c["year"],
                area_mu=c["area_mu"],
                yield_kg_per_mu=c.get("yield_kg_per_mu"),
                total_output_ton=(
                    c["area_mu"] * c.get("yield_kg_per_mu", 0) / 1000
                    if c.get("yield_kg_per_mu")
                    else None
                ),
                source="seed_zhangzhou",
                confidence=1.0,
            )
        )
        inserted += 1
    logger.info(f"已为 region {region_code} 补 {inserted} 条种植面积年度记录")
    return inserted


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            logger.info("=== 漳州增量种子开始 ===")
            await upsert_region(session)
            market = await upsert_market(session)
            await fill_prices(session, market, years=3)
            await fill_weather(session, REGION_CODE, years=3)
            await fill_cropland(session, REGION_CODE)
        logger.info("=== 漳州增量种子完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
