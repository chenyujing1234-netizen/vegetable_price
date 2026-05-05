"""CnOpenData 农产品批发价格数据集 - 离线 CSV 导入器

CnOpenData 提供 2011-2025 全国 31 省 45 种主要农产品的批发价格数据
（学术免费、商用收费）。下载后将文件放到 data/raw/cnopendata/ 下，
本脚本将其标准化并 upsert 到 price_daily 表。

CSV 预期字段：
    province, market, category, product, date, price (元/公斤)

使用：
    python -m price.cnopendata_loader \
        --csv data/raw/cnopendata/tomato_2011_2025.csv \
        --product tomato
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import typer
from loguru import logger
from sqlalchemy import select

from common.db import session_scope

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Market, PriceDaily, Product  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)

MARKET_KEYWORDS = {
    "shouguang": ["寿光"],
    "shijiazhuang_qiaoxi": ["石家庄", "桥西"],
    "dandong": ["丹东"],
    "urumqi_jiufeng": ["乌鲁木齐", "九鼎"],
    "laibin": ["来宾", "正菱"],
    "beijing_xinfadi": ["新发地"],
    "shanghai_jiangqiao": ["江桥"],
    "guangzhou_jiangnan": ["江南果菜", "广州"],
    "shenzhen_haijixing": ["海吉星", "深圳"],
    "chengdu_julong": ["聚合", "成都"],
    "wuhan_baishazhou": ["白沙洲", "武汉"],
}


def map_market(name: str) -> str | None:
    for code, keys in MARKET_KEYWORDS.items():
        for k in keys:
            if k in name:
                return code
    return None


@app.command()
def run(
    csv: Path = typer.Option(..., exists=True, readable=True),
    product: str = typer.Option("tomato"),
    start: str = typer.Option(None, help="起始日期 YYYY-MM-DD"),
    end: str = typer.Option(None, help="结束日期 YYYY-MM-DD"),
    dry_run: bool = typer.Option(False),
):
    df = pd.read_csv(csv)
    logger.info(f"loaded {len(df)} rows from {csv}")

    cols = {c.lower(): c for c in df.columns}
    market_col = cols.get("market") or cols.get("市场名称") or cols.get("市场")
    date_col = cols.get("date") or cols.get("日期")
    price_col = cols.get("price") or cols.get("avg") or cols.get("价格(元/公斤)") or cols.get("价格")
    if not all([market_col, date_col, price_col]):
        logger.error(f"missing required columns; got {list(df.columns)}")
        raise typer.Exit(1)

    df = df.rename(columns={market_col: "market", date_col: "date", price_col: "avg"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["avg"] = pd.to_numeric(df["avg"], errors="coerce")
    df = df.dropna(subset=["avg"])

    if start:
        df = df[df["date"] >= datetime.strptime(start, "%Y-%m-%d").date()]
    if end:
        df = df[df["date"] <= datetime.strptime(end, "%Y-%m-%d").date()]

    df["market_code"] = df["market"].astype(str).map(map_market)
    skipped_markets = sorted(set(df.loc[df["market_code"].isna(), "market"].unique()))
    df = df.dropna(subset=["market_code"])
    logger.info(f"mapped {len(df)} rows; skipped markets: {skipped_markets[:10]}{'...' if len(skipped_markets) > 10 else ''}")

    if dry_run:
        logger.info(df.head().to_string())
        logger.info(f"DRY-RUN total {len(df)} rows")
        return

    with session_scope() as s:
        product_obj = s.execute(select(Product).where(Product.code == product)).scalar_one()
        markets = {m.code: m for m in s.execute(select(Market)).scalars().all()}
        rows = []
        for _, r in df.iterrows():
            mid = markets.get(r["market_code"])
            if mid is None:
                continue
            rows.append({
                "market_id": mid.id,
                "product_id": product_obj.id,
                "date": r["date"],
                "low": None,
                "avg": float(r["avg"]),
                "high": None,
                "volume": None,
                "source": "cnopendata",
            })
        n = upsert_many(
            s,
            PriceDaily.__table__,
            rows,
            conflict_columns=["market_id", "product_id", "date"],
            update_columns=["avg", "source"],
        )
    logger.info(f"upserted {n} rows")


if __name__ == "__main__":
    app()
