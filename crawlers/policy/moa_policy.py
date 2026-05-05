"""农业农村部政策栏目爬虫

数据源：http://www.moa.gov.cn/govpublic/  (政策发布)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from urllib.parse import urljoin

import typer
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy import select

from common.db import session_scope
from common.http import get_text
from policy.keywords import detect_products, extract_keywords, is_relevant

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Policy  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)

LIST_URL = "http://www.moa.gov.cn/govpublic/index.htm"


def parse_list(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    for li in soup.select("ul li, .list-item, .news-item"):
        a = li.find("a", href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title or not is_relevant(title):
            continue
        url = urljoin(base_url, a["href"])
        date_text = ""
        for tag in li.select("span, em, time, .date"):
            txt = tag.get_text(strip=True)
            if any(c.isdigit() for c in txt) and ("-" in txt or "/" in txt):
                date_text = txt
                break
        try:
            d = datetime.strptime(date_text.strip().split()[0], "%Y-%m-%d").date()
        except Exception:
            continue
        out.append({"title": title, "url": url, "publish_date": d})
    return out


def infer_impact(text: str) -> tuple[str, str]:
    """根据关键词推断政策对价格的方向（粗略）"""
    if any(k in text for k in ["扩大", "保供", "增加供给", "稳价", "投放储备"]):
        return "high", "negative"
    if any(k in text for k in ["收储", "保护价", "限产"]):
        return "high", "positive"
    return "medium", "neutral"


@app.command()
def run(
    pages: int = typer.Option(2),
    dry_run: bool = typer.Option(False),
):
    all_rows: list[dict] = []
    for p in range(pages):
        url = LIST_URL if p == 0 else LIST_URL.replace("index.htm", f"index_{p}.htm")
        try:
            html = get_text(url)
        except Exception as e:
            logger.warning(f"page {p} failed: {e}")
            continue
        rows = parse_list(html, url)
        logger.info(f"page {p}: {len(rows)} relevant items")
        all_rows.extend(rows)

    if dry_run:
        for r in all_rows[:10]:
            logger.info(r)
        return

    with session_scope() as s:
        existing = {
            u for (u,) in s.execute(select(Policy.url)).all()
        }
        to_insert = []
        for r in all_rows:
            if r["url"] in existing:
                continue
            level, direction = infer_impact(r["title"])
            to_insert.append({
                "title": r["title"][:512],
                "publisher": "农业农村部",
                "publish_date": r["publish_date"],
                "url": r["url"],
                "summary": None,
                "full_text": None,
                "impact_level": level,
                "impact_direction": direction,
                "related_products": detect_products(r["title"]),
                "keywords": extract_keywords(r["title"]),
            })
        if to_insert:
            n = upsert_many(
                s,
                Policy.__table__,
                to_insert,
                conflict_columns=["url"],
            )
            logger.info(f"inserted {n} new policies")
        else:
            logger.info("no new policies")


if __name__ == "__main__":
    app()
