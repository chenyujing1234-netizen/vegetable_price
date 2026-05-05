"""一键灌入种子数据：建表 + 插入示例

执行：``python -m app.seed.seed_all``
"""

import asyncio
from datetime import date, timedelta

from loguru import logger
from sqlalchemy import delete, select, text

from app.database import AsyncSessionLocal, Base, engine
from app.models import (
    CroplandYearly,
    Market,
    News,
    Policy,
    PriceDaily,
    Product,
    Region,
    WeatherDaily,
)
from app.seed.seed_data import (
    MARKET_BASE_PRICE,
    MARKETS,
    PRODUCTS,
    REGIONS,
    SEED_CROPLAND,
    SEED_NEWS,
    SEED_POLICIES,
    synth_other_veg_price,
    synth_tomato_price,
    synth_weather,
)


async def init_schema():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        except Exception as e:
            logger.warning(f"timescaledb extension not available, falling back to plain Postgres: {e}")
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(
                text(
                    "SELECT create_hypertable('price_daily', 'date', if_not_exists => TRUE, "
                    "migrate_data => TRUE)"
                )
            )
            await conn.execute(
                text(
                    "SELECT create_hypertable('weather_daily', 'date', if_not_exists => TRUE, "
                    "migrate_data => TRUE)"
                )
            )
        except Exception as e:
            logger.warning(f"hypertable creation skipped: {e}")


async def seed_meta(session):
    for r in REGIONS:
        existing = await session.get(Region, r["code"])
        if existing:
            continue
        session.add(Region(**r))
    await session.flush()

    for m in MARKETS:
        exists = (
            await session.execute(select(Market).where(Market.code == m["code"]))
        ).scalar_one_or_none()
        if exists:
            continue
        session.add(Market(**m, lng=_market_lng(m), lat=_market_lat(m)))
    await session.flush()

    for p in PRODUCTS:
        exists = (
            await session.execute(select(Product).where(Product.code == p["code"]))
        ).scalar_one_or_none()
        if exists:
            continue
        session.add(Product(**p))
    await session.flush()


def _market_lng(m: dict) -> float | None:
    for r in REGIONS:
        if r["code"] == m["region_code"]:
            return r["lng"]
    return None


def _market_lat(m: dict) -> float | None:
    for r in REGIONS:
        if r["code"] == m["region_code"]:
            return r["lat"]
    return None


async def seed_prices(session, years: int = 3):
    """为每个市场 × 每个产品 灌入近 N 年的合成日度价格"""
    end = date.today()
    start = end - timedelta(days=365 * years)

    markets = (await session.execute(select(Market))).scalars().all()
    products = (await session.execute(select(Product))).scalars().all()

    await session.execute(delete(PriceDaily))

    batch: list[dict] = []
    for m in markets:
        base = MARKET_BASE_PRICE.get(m.code, 4.5)
        for p in products:
            d = start
            while d <= end:
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
                        "source": "seed",
                    }
                )
                d += timedelta(days=1)
                if len(batch) >= 5000:
                    await session.execute(PriceDaily.__table__.insert(), batch)
                    batch.clear()
    if batch:
        await session.execute(PriceDaily.__table__.insert(), batch)
    logger.info(f"seeded prices: {len(markets)} markets x {len(products)} products x {years*365} days")


async def seed_weather(session, years: int = 3):
    end = date.today()
    start = end - timedelta(days=365 * years)
    regions = (await session.execute(select(Region))).scalars().all()
    await session.execute(delete(WeatherDaily))
    batch: list[dict] = []
    for r in regions:
        d = start
        while d <= end:
            w = synth_weather(r.code, d)
            batch.append({"region_code": r.code, "date": d, **w, "source": "seed"})
            d += timedelta(days=1)
            if len(batch) >= 5000:
                await session.execute(WeatherDaily.__table__.insert(), batch)
                batch.clear()
    if batch:
        await session.execute(WeatherDaily.__table__.insert(), batch)
    logger.info(f"seeded weather: {len(regions)} regions x {years*365} days")


async def seed_policies_news(session):
    await session.execute(delete(Policy))
    for p in SEED_POLICIES:
        session.add(Policy(**p))

    await session.execute(delete(News))
    for n in SEED_NEWS:
        session.add(News(**n))
    logger.info(f"seeded {len(SEED_POLICIES)} policies and {len(SEED_NEWS)} news")


async def seed_cropland(session):
    products = {p.code: p for p in (await session.execute(select(Product))).scalars().all()}
    tomato_id = products["tomato"].id
    await session.execute(delete(CroplandYearly))
    for c in SEED_CROPLAND:
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
                source="seed",
                confidence=1.0,
            )
        )
    logger.info(f"seeded {len(SEED_CROPLAND)} cropland records")


async def main():
    logger.info("=== schema init ===")
    await init_schema()

    async with AsyncSessionLocal() as session:
        async with session.begin():
            logger.info("=== seed regions/markets/products ===")
            await seed_meta(session)
            logger.info("=== seed prices ===")
            await seed_prices(session, years=3)
            logger.info("=== seed weather ===")
            await seed_weather(session, years=3)
            logger.info("=== seed policies/news ===")
            await seed_policies_news(session)
            logger.info("=== seed cropland ===")
            await seed_cropland(session)
        logger.info("All seed data committed.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
