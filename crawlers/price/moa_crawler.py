"""农业农村部 - 全国农产品商务信息公共服务平台 价格爬虫

数据源：http://zdscxx.moa.gov.cn:8080/nyb/pc/index.jsp
该平台对外暴露 JSON 接口（前端请求 `/nyb/api/getMrhq.action` 等）
本脚本封装核心抓取逻辑，并以幂等 upsert 写入 price_daily 表。

合规：
- 仅采集页面公开展示的批发价格汇总数据
- User-Agent 带项目标识；请求间隔 ≥ 1 秒
- 无任何登录态、cookie 绕过

注意：实际抓取时部分接口可能会变化或加入风控，需要结合
具体页面按 F12 抓包定位最新接口；本文件提供的 URL/参数为
2026 年初观察到的版本。如失效请到 issue 里反馈。
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Iterable

import typer
from loguru import logger
from sqlalchemy import select

from common.db import session_scope
from common.http import safe_get_json

# 后端 ORM 直接复用
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Market, PriceDaily, Product  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)


# 农业农村部对常见品类有自己的编码体系，此处给出西红柿等映射
MOA_PRODUCT_CODE = {
    "tomato": "番茄",
    "cucumber": "黄瓜",
    "chili": "尖椒",
    "potato": "马铃薯",
}

# 平台 API（如失效请抓包替换）
LIST_API = "http://zdscxx.moa.gov.cn/nyb/api/getMrhq.action"


def fetch_one_day(product_zh: str, day: date) -> list[dict]:
    """抓取某一天某一品类在全国各市场的价格汇总

    返回标准化字段列表：[{market_name, region, low, avg, high, date}]
    """
    params = {
        "isStart": "true",
        "pageNo": 1,
        "pageSize": 200,
        "name": product_zh,
        "startTime": day.isoformat(),
        "endTime": day.isoformat(),
    }
    raw = safe_get_json(LIST_API, params=params)
    if not raw or not isinstance(raw, dict):
        return []
    rows = raw.get("data") or raw.get("rows") or []
    out: list[dict] = []
    for r in rows:
        market_name = r.get("marketName") or r.get("market") or r.get("scmc")
        if not market_name:
            continue
        try:
            low = float(r.get("lowPrice") or r.get("zdj") or 0) or None
            high = float(r.get("highPrice") or r.get("zgj") or 0) or None
            avg = float(r.get("avgPrice") or r.get("pjj") or 0)
        except (TypeError, ValueError):
            continue
        if not avg:
            continue
        out.append(
            {
                "market_name": market_name,
                "region": r.get("provinceName") or r.get("province") or "",
                "low": low,
                "avg": avg,
                "high": high,
                "date": day,
            }
        )
    return out


def standardize_market(name: str) -> str | None:
    """将抓取的市场名映射到我们 markets 表里的 code"""
    table = {
        "山东寿光": "shouguang",
        "寿光": "shouguang",
        "石家庄": "shijiazhuang_qiaoxi",
        "丹东": "dandong",
        "乌鲁木齐": "urumqi_jiufeng",
        "新发地": "beijing_xinfadi",
        "江桥": "shanghai_jiangqiao",
        "江南果菜": "guangzhou_jiangnan",
        "海吉星": "shenzhen_haijixing",
        "聚合": "chengdu_julong",
        "白沙洲": "wuhan_baishazhou",
        "正菱": "laibin",
    }
    for k, v in table.items():
        if k in name:
            return v
    return None


def write_to_db(records: Iterable[dict], product_code: str, dry_run: bool) -> int:
    records = list(records)
    if not records:
        logger.info("no records to write")
        return 0

    if dry_run:
        for r in records[:10]:
            logger.info(f"DRY-RUN {r}")
        logger.info(f"DRY-RUN total {len(records)} records (showing first 10)")
        return 0

    with session_scope() as s:
        product = s.execute(select(Product).where(Product.code == product_code)).scalar_one_or_none()
        if product is None:
            logger.error(f"product {product_code} not in DB; please run seed first")
            return 0
        markets = {m.code: m for m in s.execute(select(Market)).scalars().all()}
        rows = []
        skipped = 0
        for r in records:
            mcode = standardize_market(r["market_name"])
            if mcode is None or mcode not in markets:
                skipped += 1
                continue
            rows.append(
                {
                    "market_id": markets[mcode].id,
                    "product_id": product.id,
                    "date": r["date"],
                    "low": r.get("low"),
                    "avg": r["avg"],
                    "high": r.get("high"),
                    "volume": None,
                    "source": "moa",
                }
            )
        n = upsert_many(
            s,
            PriceDaily.__table__,
            rows,
            conflict_columns=["market_id", "product_id", "date"],
            update_columns=["low", "avg", "high", "source"],
        )
    logger.info(f"upserted {n} rows (skipped {skipped} unmapped markets)")
    return n


@app.command()
def run(
    product: str = typer.Option("tomato", help="产品 code（tomato/cucumber/chili/potato）"),
    days: int = typer.Option(7, help="抓取最近 N 天"),
    end: str = typer.Option(None, help="结束日期 YYYY-MM-DD，默认今天"),
    dry_run: bool = typer.Option(False, help="只打印不入库"),
    rate: float = typer.Option(1.0, help="每个请求间隔秒数（避免触发风控）"),
):
    if product not in MOA_PRODUCT_CODE:
        typer.echo(f"unsupported product: {product}; available: {list(MOA_PRODUCT_CODE)}")
        raise typer.Exit(1)
    end_dt = datetime.strptime(end, "%Y-%m-%d").date() if end else date.today()
    start_dt = end_dt - timedelta(days=days - 1)
    logger.info(f"crawl moa: {product} from {start_dt} to {end_dt}")

    all_rows: list[dict] = []
    d = start_dt
    while d <= end_dt:
        rows = fetch_one_day(MOA_PRODUCT_CODE[product], d)
        logger.info(f"  {d}: {len(rows)} rows")
        all_rows.extend(rows)
        time.sleep(rate)
        d += timedelta(days=1)

    write_to_db(all_rows, product, dry_run)


if __name__ == "__main__":
    app()
