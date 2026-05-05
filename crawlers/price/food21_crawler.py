"""食价搜（食品商务网）价格爬虫

数据源：https://wap.21food.cn/price/
通过解析 HTML 列表页 + 详情页的方式抓取每日批发价格。
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, datetime, timedelta

import typer
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy import select

from common.db import session_scope
from common.http import get_text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Market, PriceDaily, Product  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)

LIST_URL = "https://wap.21food.cn/price/list-{slug}.html"

PRODUCT_SLUG = {
    "tomato": "xihongshi",
    "cucumber": "huanggua",
    "chili": "lajiao",
    "potato": "tudou",
}


def parse_list_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    items = []
    for tr in soup.select("table tr"):
        tds = [td.get_text(strip=True) for td in tr.select("td")]
        if len(tds) < 4:
            continue
        try:
            price = float(tds[2].replace("元/公斤", "").replace("元", "").strip())
        except (ValueError, IndexError):
            continue
        items.append({
            "market_name": tds[0],
            "spec": tds[1] if len(tds) > 1 else None,
            "avg": price,
            "date_str": tds[-1],
        })
    return items


def standardize_market(name: str) -> str | None:
    table = {
        "新发地": "beijing_xinfadi",
        "江桥": "shanghai_jiangqiao",
        "江南果菜": "guangzhou_jiangnan",
        "海吉星": "shenzhen_haijixing",
        "白沙洲": "wuhan_baishazhou",
        "聚合": "chengdu_julong",
        "寿光": "shouguang",
        "石家庄": "shijiazhuang_qiaoxi",
        "丹东": "dandong",
        "乌鲁木齐": "urumqi_jiufeng",
        "正菱": "laibin",
    }
    for k, v in table.items():
        if k in name:
            return v
    return None


@app.command()
def run(
    product: str = typer.Option("tomato"),
    days: int = typer.Option(7),
    dry_run: bool = typer.Option(False),
    rate: float = typer.Option(1.5),
):
    if product not in PRODUCT_SLUG:
        typer.echo(f"unsupported product: {product}")
        raise typer.Exit(1)

    today = date.today()
    earliest = today - timedelta(days=days - 1)
    url = LIST_URL.format(slug=PRODUCT_SLUG[product])
    logger.info(f"GET {url}")
    html = get_text(url)
    items = parse_list_html(html)
    logger.info(f"parsed {len(items)} items")

    rows = []
    for it in items:
        try:
            d = datetime.strptime(it["date_str"], "%Y-%m-%d").date()
        except Exception:
            d = today
        if d < earliest:
            continue
        rows.append({**it, "date": d})

    if dry_run:
        for r in rows[:10]:
            logger.info(f"DRY-RUN {r}")
        logger.info(f"DRY-RUN total {len(rows)}")
        return

    with session_scope() as s:
        product_obj = s.execute(select(Product).where(Product.code == product)).scalar_one()
        markets = {m.code: m for m in s.execute(select(Market)).scalars().all()}
        db_rows = []
        skipped = 0
        for r in rows:
            mcode = standardize_market(r["market_name"])
            if mcode not in markets:
                skipped += 1
                continue
            db_rows.append({
                "market_id": markets[mcode].id,
                "product_id": product_obj.id,
                "date": r["date"],
                "low": None,
                "avg": r["avg"],
                "high": None,
                "volume": None,
                "source": "21food",
            })
        n = upsert_many(
            s,
            PriceDaily.__table__,
            db_rows,
            conflict_columns=["market_id", "product_id", "date"],
            update_columns=["avg", "source"],
        )
    logger.info(f"upserted {n} rows, skipped {skipped} unmapped")
    time.sleep(rate)


if __name__ == "__main__":
    app()
