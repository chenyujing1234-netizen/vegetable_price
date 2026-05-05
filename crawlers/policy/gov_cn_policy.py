"""国务院政策文件库爬虫

数据源：https://sousuo.www.gov.cn/sousuo/search.shtml
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from urllib.parse import urlencode

import typer
from loguru import logger
from sqlalchemy import select

from common.db import session_scope
from common.http import get_json
from policy.keywords import detect_products, extract_keywords

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Policy  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)

# 国务院搜索 JSON 接口
SEARCH_API = "https://sousuo.www.gov.cn/search-gov/data"


def search(keyword: str, n: int = 30) -> list[dict]:
    params = {
        "t": "zhengcelibrary",
        "q": keyword,
        "n": n,
        "p": 1,
        "timetype": "timeqb",
        "mintime": "",
        "maxtime": "",
    }
    url = f"{SEARCH_API}?{urlencode(params)}"
    raw = get_json(url)
    items = raw.get("searchVO", {}).get("listVO", []) if isinstance(raw, dict) else []
    out = []
    for it in items:
        title = it.get("title") or it.get("titleDetail") or ""
        url_ = it.get("url") or it.get("urlPub") or ""
        date_str = it.get("pubtimeStr") or it.get("publishTime") or ""
        try:
            d = datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
        except Exception:
            continue
        out.append({
            "title": title.replace("<em>", "").replace("</em>", ""),
            "url": url_,
            "publish_date": d,
            "publisher": it.get("puborg") or "国务院",
        })
    return out


@app.command()
def run(
    keywords: list[str] = typer.Option(["蔬菜价格", "菜篮子", "鲜活农产品"]),
    dry_run: bool = typer.Option(False),
):
    all_rows: list[dict] = []
    for k in keywords:
        rows = search(k)
        logger.info(f"keyword '{k}': {len(rows)} hits")
        all_rows.extend(rows)
    seen = set()
    dedup = []
    for r in all_rows:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        dedup.append(r)
    if dry_run:
        for r in dedup[:10]:
            logger.info(r)
        return

    with session_scope() as s:
        existing = {u for (u,) in s.execute(select(Policy.url)).all()}
        to_insert = []
        for r in dedup:
            if r["url"] in existing:
                continue
            to_insert.append({
                "title": r["title"][:512],
                "publisher": r["publisher"][:128],
                "publish_date": r["publish_date"],
                "url": r["url"],
                "summary": None,
                "full_text": None,
                "impact_level": "medium",
                "impact_direction": "neutral",
                "related_products": detect_products(r["title"]),
                "keywords": extract_keywords(r["title"]),
            })
        if to_insert:
            upsert_many(s, Policy.__table__, to_insert, conflict_columns=["url"])
        logger.info(f"inserted {len(to_insert)} new policies")


if __name__ == "__main__":
    app()
