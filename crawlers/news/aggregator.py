"""新闻聚合爬虫

支持多个新闻搜索引擎：百度新闻、Bing 新闻 (国内可用)、新浪 RSS。
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import typer
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy import select

from common.db import session_scope
from common.http import get_text
from policy.keywords import detect_products, extract_keywords

try:
    from news.sources import FIXED_NEWS_SOURCES, get_source
except ImportError:
    from sources import FIXED_NEWS_SOURCES, get_source  # type: ignore

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import News  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)


def search_baidu_news(keyword: str, pages: int = 2) -> list[dict]:
    """百度新闻搜索（HTML 解析版）

    URL: https://news.baidu.com/ns?word=KEYWORD&pn=N
    """
    out: list[dict] = []
    for p in range(pages):
        url = f"https://news.baidu.com/ns?word={quote_plus(keyword)}&pn={p * 10}&cl=2&ct=1"
        try:
            html = get_text(url)
        except Exception as e:
            logger.warning(f"baidu page {p} failed: {e}")
            continue
        soup = BeautifulSoup(html, "lxml")
        for item in soup.select(".result.title, .result, .news-item"):
            a = item.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            source_tag = item.select_one(".c-author, .source, .news-source")
            source = source_tag.get_text(strip=True) if source_tag else "百度新闻"
            time_tag = item.select_one(".c-color-gray2, time, .date")
            time_text = time_tag.get_text(strip=True) if time_tag else ""
            publish_at = parse_publish_time(time_text)
            if not title or not href:
                continue
            out.append({
                "title": title,
                "url": href,
                "source": source[:64],
                "publish_at": publish_at,
            })
    return out


def parse_publish_time(text: str) -> datetime:
    """容错解析时间字符串：'2025-05-18 09:30' / '2小时前' / '昨天 10:20' 等"""
    text = text.strip()
    now = datetime.utcnow()
    try:
        if "分钟前" in text:
            mins = int("".join(c for c in text if c.isdigit()))
            return now - timedelta(minutes=mins)
        if "小时前" in text:
            hrs = int("".join(c for c in text if c.isdigit()))
            return now - timedelta(hours=hrs)
        if text.startswith("昨天"):
            return now - timedelta(days=1)
        if text.startswith("前天"):
            return now - timedelta(days=2)
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%m-%d %H:%M", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    return now


def basic_sentiment(text: str) -> tuple[str, float]:
    """词典法情感分析（baseline）

    返回 (label, score)，score 范围 -1 ~ 1
    """
    pos_words = ["上涨", "走高", "看涨", "稳价", "保供", "增长", "回暖", "丰收"]
    neg_words = ["下跌", "跌势", "看跌", "滞销", "菜贱", "亏损", "灾害", "冻害", "暴雨"]
    pos = sum(text.count(w) for w in pos_words)
    neg = sum(text.count(w) for w in neg_words)
    total = pos + neg
    if total == 0:
        return "neutral", 0.0
    score = (pos - neg) / total
    label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
    return label, round(score, 3)


def search_site_news(source_id: str, keyword: str, pages: int = 1) -> list[dict]:
    """在固定来源域名内搜索（百度 news site: 语法）"""
    src = get_source(source_id)
    if not src:
        logger.warning(f"unknown source: {source_id}")
        return []
    query = f"site:{src.domain} {keyword}"
    rows = search_baidu_news(query, pages=pages)
    for r in rows:
        r["source"] = src.name
    return rows


@app.command()
def run(
    keywords: list[str] = typer.Option(["蔬菜价格", "西红柿 批发", "菜篮子"]),
    pages: int = typer.Option(2),
    sources: list[str] = typer.Option(
        [],
        help="固定来源 id：farmer, agri, nfncb, xinhua, sina；为空则全网百度新闻",
    ),
    dry_run: bool = typer.Option(False),
):
    all_rows: list[dict] = []
    if sources:
        for sid in sources:
            src = get_source(sid)
            if not src:
                continue
            kws = keywords or list(src.default_keywords)
            for k in kws:
                rows = search_site_news(sid, k, pages=pages)
                logger.info(f"[{src.name}] '{k}': {len(rows)} items")
                all_rows.extend(rows)
    else:
        for k in keywords:
            rows = search_baidu_news(k, pages=pages)
            logger.info(f"'{k}': {len(rows)} items")
            all_rows.extend(rows)

    seen = set()
    dedup = []
    for r in all_rows:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        dedup.append(r)

    enriched = []
    for r in dedup:
        label, score = basic_sentiment(r["title"])
        enriched.append({
            **r,
            "content": None,
            "sentiment_label": label,
            "sentiment_score": score,
            "related_products": detect_products(r["title"]),
            "keywords": extract_keywords(r["title"]),
        })

    if dry_run:
        for r in enriched[:10]:
            logger.info(r)
        return

    with session_scope() as s:
        existing = {u for (u,) in s.execute(select(News.url)).all()}
        to_insert = [r for r in enriched if r["url"] not in existing]
        if to_insert:
            upsert_many(s, News.__table__, to_insert, conflict_columns=["url"])
        logger.info(f"inserted {len(to_insert)} news")


if __name__ == "__main__":
    app()
