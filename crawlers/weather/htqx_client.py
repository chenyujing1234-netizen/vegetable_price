"""海天气象 (htqx.cn) 历史天气数据采集

支持：
- 通过 HTTP API 拉取指定地区的逐日历史气象数据（温度/降水/湿度/风速）
- 也支持回退到极速数据 / 聚合数据 接口

合规：
- 海天气象需要在控制台获取 HTQX_API_KEY 后写入 .env
- 免费 / 试用账户每日有调用次数限制
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, datetime, timedelta

import typer
from loguru import logger
from sqlalchemy import select

from common.db import session_scope
from common.http import safe_get_json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Region, WeatherDaily  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)

HTQX_BASE = "https://htqx.cn/openapi/v1"


def fetch_htqx_daily(region_code: str, start: date, end: date, api_key: str) -> list[dict]:
    """拉取海天气象的指定地区逐日数据

    示例 URL: GET /openapi/v1/history/daily?region={code}&start=YYYYMMDD&end=YYYYMMDD
    """
    params = {
        "region": region_code,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "key": api_key,
    }
    raw = safe_get_json(f"{HTQX_BASE}/history/daily", params=params)
    if not raw or raw.get("code") != 0:
        logger.warning(f"htqx returned: {raw}")
        return []
    out: list[dict] = []
    for r in raw.get("data") or []:
        out.append({
            "region_code": region_code,
            "date": datetime.strptime(str(r["date"]), "%Y%m%d").date(),
            "temp_min": _f(r.get("tmin")),
            "temp_max": _f(r.get("tmax")),
            "temp_avg": _f(r.get("tavg")),
            "precip": _f(r.get("rain")),
            "humidity": _f(r.get("rh")),
            "wind_speed": _f(r.get("ws")),
            "weather": r.get("wx"),
            "source": "htqx",
        })
    return out


def fetch_jisu_daily(region_name: str, day: date, app_key: str) -> dict | None:
    """极速数据接口（备用，免费 100 次/月）

    GET https://api.jisuapi.com/weather2/query?city=寿光&date=YYYY-MM-DD&appkey=xxx
    """
    raw = safe_get_json(
        "https://api.jisuapi.com/weather2/query",
        params={"city": region_name, "date": day.isoformat(), "appkey": app_key},
    )
    if not raw or raw.get("status") != 0:
        return None
    r = raw["result"]
    return {
        "date": day,
        "temp_min": _f(r.get("templow")),
        "temp_max": _f(r.get("temphigh")),
        "temp_avg": (_f(r.get("templow")) + _f(r.get("temphigh"))) / 2 if r.get("templow") else None,
        "precip": None,
        "humidity": _f(r.get("humidity")),
        "wind_speed": None,
        "weather": r.get("weather"),
        "source": "jisu",
    }


def _f(v):
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None


@app.command()
def run(
    region: str = typer.Option(..., help="行政区划代码，如 370783 (寿光)"),
    days: int = typer.Option(30),
    end: str = typer.Option(None, help="结束日期 YYYY-MM-DD"),
    provider: str = typer.Option("htqx", help="htqx / jisu"),
    dry_run: bool = typer.Option(False),
):
    end_dt = datetime.strptime(end, "%Y-%m-%d").date() if end else date.today()
    start_dt = end_dt - timedelta(days=days - 1)

    if provider == "htqx":
        api_key = os.getenv("HTQX_API_KEY")
        if not api_key:
            logger.error("HTQX_API_KEY not set; switch provider or set env var")
            raise typer.Exit(1)
        rows = fetch_htqx_daily(region, start_dt, end_dt, api_key)
    elif provider == "jisu":
        api_key = os.getenv("JISU_APP_KEY")
        if not api_key:
            logger.error("JISU_APP_KEY not set")
            raise typer.Exit(1)
        # jisu 按城市名查询，需要先解析 region_name
        with session_scope() as s:
            region_obj = s.execute(select(Region).where(Region.code == region)).scalar_one_or_none()
        if region_obj is None:
            logger.error(f"region {region} not found in DB")
            raise typer.Exit(1)
        rows = []
        d = start_dt
        while d <= end_dt:
            r = fetch_jisu_daily(region_obj.name, d, api_key)
            if r:
                rows.append({**r, "region_code": region})
            time.sleep(1.0)
            d += timedelta(days=1)
    else:
        typer.echo(f"unknown provider: {provider}")
        raise typer.Exit(1)

    logger.info(f"fetched {len(rows)} records from {provider}")
    if dry_run:
        for r in rows[:5]:
            logger.info(r)
        return

    if not rows:
        logger.warning("nothing to write")
        return

    with session_scope() as s:
        n = upsert_many(
            s,
            WeatherDaily.__table__,
            rows,
            conflict_columns=["region_code", "date"],
            update_columns=[
                "temp_min", "temp_max", "temp_avg",
                "precip", "humidity", "wind_speed", "weather", "source",
            ],
        )
    logger.info(f"upserted {n} rows")


if __name__ == "__main__":
    app()
