"""增量入库：把 seed_data.PRODUCTS 里新增的品类写入数据库，并补齐缺失的价格序列。

不会删除已有数据，可重复执行。新增品类后运行：

    python -m app.seed.seed_products

如需把新品类价格补到今天，再运行：

    python -m app.seed.seed_catchup
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from loguru import logger
from sqlalchemy import and_, func, select

from app.database import AsyncSessionLocal
from app.models import Market, PriceDaily, Product
from app.seed.seed_data import (
    MARKET_BASE_PRICE,
    PRODUCTS,
    synth_other_veg_price,
    synth_tomato_price,
)


async def upsert_products(session) -> list[Product]:
    added: list[Product] = []
    for p in PRODUCTS:
        exists = (
            await session.execute(select(Product).where(Product.code == p["code"]))
        ).scalar_one_or_none()
        if exists:
            continue
        row = Product(**p)
        session.add(row)
        added.append(row)
    if added:
        await session.flush()
        logger.info(f"新增 {len(added)} 个品类: {[p.name for p in added]}")
    else:
        logger.info("无新增品类，PRODUCTS 与数据库已一致")
    return added


async def fill_missing_prices(session, years: int = 3) -> int:
    today = date.today()
    start = today - timedelta(days=365 * years)
    markets = (await session.execute(select(Market))).scalars().all()
    products = (await session.execute(select(Product))).scalars().all()

    inserted = 0
    batch: list[dict] = []
    for m in markets:
        base = MARKET_BASE_PRICE.get(m.code, 4.5)
        for p in products:
            count = (
                await session.execute(
                    select(func.count())
                    .select_from(PriceDaily)
                    .where(
                        and_(
                            PriceDaily.market_id == m.id,
                            PriceDaily.product_id == p.id,
                        )
                    )
                )
            ).scalar_one()
            if count > 0:
                continue

            d = start
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
                        "source": "seed_products",
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
    logger.info(f"补齐价格序列：新增 {inserted} 条")
    return inserted


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await upsert_products(session)
            await fill_missing_prices(session, years=3)
    logger.info("seed_products 完成")


if __name__ == "__main__":
    asyncio.run(main())
