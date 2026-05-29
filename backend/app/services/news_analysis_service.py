"""新闻按需解读：抓取正文 → 情感分析 → 生成平台观点（用户点击时触发）"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import News

# 与 ml/nlp/sentiment.py 词典保持一致（backend 不依赖 ml 包）
PRICE_UP_WORDS = [
    "上涨", "走高", "看涨", "回暖", "上扬", "飙升", "暴涨", "突破", "站上",
    "供给紧张", "减产", "灾害", "冻害", "暴雨", "受灾", "短缺", "涨价",
]
PRICE_DOWN_WORDS = [
    "下跌", "跌势", "看跌", "回落", "下行", "暴跌", "走低", "下滑",
    "供过于求", "丰产", "增产", "扩种", "扩大产能", "滞销", "菜贱", "烂在",
    "稳价", "保供", "投放储备", "降本", "降价",
]

FACTOR_PATTERNS: list[tuple[str, str, list[str]]] = [
    ("weather", "天气/灾害", ["寒潮", "暴雨", "台风", "干旱", "冻害", "高温", "降雨", "天气"]),
    ("supply", "供需/产量", ["供应", "产量", "扩种", "丰收", "滞销", "上市", "集中上市", "供过于求"]),
    ("policy", "政策调控", ["政策", "储备", "收储", "保供", "调控", "补贴", "国常会", "发改委"]),
    ("logistics", "物流成本", ["运输", "物流", "运费", "绿色通道", "高速"]),
    ("substitute", "替代品类", ["替代", "换种", "其他蔬菜", "竞品"]),
]

PRODUCT_NAMES: dict[str, str] = {
    "tomato": "西红柿",
    "cucumber": "黄瓜",
    "chili": "辣椒",
    "potato": "土豆",
    "cabbage": "大白菜",
    "eggplant": "茄子",
    "pakchoi": "小白菜",
    "broccoli": "西兰花",
}

PRODUCT_KEYWORDS: dict[str, list[str]] = {
    "tomato": ["西红柿", "番茄", "圣女果"],
    "cucumber": ["黄瓜", "青瓜"],
    "chili": ["辣椒", "尖椒", "彩椒"],
    "potato": ["土豆", "马铃薯"],
    "cabbage": ["大白菜", "白菜", "甘蓝"],
    "eggplant": ["茄子"],
    "pakchoi": ["小白菜", "青菜", "油菜"],
    "broccoli": ["西兰花", "花菜", "菜花"],
}


def lex_sentiment(text: str) -> tuple[str, float]:
    pos = sum(text.count(w) for w in PRICE_UP_WORDS)
    neg = sum(text.count(w) for w in PRICE_DOWN_WORDS)
    total = pos + neg
    if total == 0:
        return "neutral", 0.0
    score = round((pos - neg) / total, 3)
    label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
    return label, score


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(re.sub(r"\s+", " ", text))
    return text.strip()


def fetch_article_content(url: str) -> str | None:
    """尝试抓取新闻正文（同步，供 asyncio.to_thread 调用）"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; VegBot/0.1; +https://example.com/bot)"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    try:
        with httpx.Client(timeout=20, follow_redirects=True, headers=headers) as client:
            r = client.get(url)
            r.raise_for_status()
            html = r.text
    except Exception as e:
        logger.warning(f"fetch content failed {url}: {e}")
        return None

    # 优先尝试 BeautifulSoup（若已安装）
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        for sel in (
            "article",
            ".article-content",
            ".content",
            "#content",
            ".TRS_Editor",
            ".Custom_UnionStyle",
            "main",
        ):
            node = soup.select_one(sel)
            if node:
                t = node.get_text(" ", strip=True)
                if len(t) > 80:
                    return t[:8000]
        paras = [p.get_text(strip=True) for p in soup.find_all("p")]
        body = " ".join(p for p in paras if len(p) > 15)
        if len(body) > 80:
            return body[:8000]
    except ImportError:
        pass

    plain = _strip_html(html)
    return plain[:8000] if len(plain) > 80 else None


def detect_products(text: str) -> list[str]:
    found: list[str] = []
    for code, kws in PRODUCT_KEYWORDS.items():
        if any(k in text for k in kws):
            found.append(code)
    return found


def detect_factors(text: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for fid, name, kws in FACTOR_PATTERNS:
        hits = [k for k in kws if k in text]
        if hits:
            out.append({"id": fid, "name": name, "evidence": "、".join(hits[:3])})
    return out


def price_impact_from_sentiment(label: str) -> tuple[str, str]:
    if label == "positive":
        return "likely_up", "偏多：文本倾向涨价或供应偏紧"
    if label == "negative":
        return "likely_down", "偏空：文本倾向跌价或供应过剩"
    return "neutral", "中性：未出现明确涨跌信号"


def build_viewpoint(
    title: str,
    content: str,
    products: list[str],
    factors: list[dict[str, str]],
    label: str,
    score: float,
) -> tuple[str, dict[str, Any]]:
    impact, impact_reason = price_impact_from_sentiment(label)

    product_cn = "、".join(PRODUCT_NAMES.get(p, p) for p in products) or "相关蔬菜"
    factor_text = "；".join(f"{f['name']}（{f['evidence']}）" for f in factors[:4])
    if not factor_text:
        factor_text = "正文未明确提及典型价格驱动因子，建议结合本站价格走势交叉验证"

    if label == "positive":
        advice = f"若您正考虑扩大 {product_cn} 种植，建议先对照本站 30 天预测与区域价差，避免集中上市踩坑。"
    elif label == "negative":
        advice = f"短期 {product_cn} 可能承压。可考虑错峰上市、对接销区批发渠道，或关注政策收储窗口。"
    else:
        advice = f"{product_cn} 短期方向不明，建议以本站多市场最新报价 + 天气因子综合判断。"

    summary = (
        f"【平台观点】本文对 {product_cn} 价格影响偏"
        f"{'强' if label == 'positive' else '弱' if label == 'negative' else '中性'}"
        f"（情感分 {score:+.2f}）。{impact_reason}。"
    )

    detail: dict[str, Any] = {
        "price_impact": impact,
        "price_impact_reason": impact_reason,
        "sentiment_label": label,
        "sentiment_score": score,
        "mentioned_products": products,
        "mentioned_products_cn": [PRODUCT_NAMES.get(p, p) for p in products],
        "key_factors": factors,
        "farmer_advice": advice,
        "method": "lexicon_v1",
        "disclaimer": "基于关键词与词典的规则解读，仅供参考，不构成投资建议。",
    }

    viewpoint = (
        f"{summary}\n\n"
        f"识别到的主要因子：{factor_text}。\n\n"
        f"给农户的建议：{advice}\n\n"
        f"（解读方法：标题+正文词典情感 + 因子关键词匹配；"
        f"后续可接入 bge 语义模型提升精度。）"
    )
    return viewpoint, detail


async def analyze_news_item(db: AsyncSession, news_id: int) -> News:
    row = await db.get(News, news_id)
    if not row:
        raise ValueError("news_not_found")

    if row.analysis_status == "done" and row.analysis_summary:
        return row

    content = row.content
    if not content or len(content) < 40:
        fetched = await asyncio.to_thread(fetch_article_content, row.url)
        if fetched:
            row.content = fetched
            content = fetched

    text = f"{row.title} {content or ''}".strip()
    label, score = lex_sentiment(text)
    products = list(dict.fromkeys((row.related_products or []) + detect_products(text)))
    factors = detect_factors(text)
    viewpoint, detail = build_viewpoint(row.title, text, products, factors, label, score)

    row.sentiment_label = label
    row.sentiment_score = score
    row.related_products = products
    row.analysis_summary = viewpoint.split("\n\n")[0]
    row.analysis_detail = detail
    row.analysis_status = "done"
    row.analyzed_at = datetime.now(timezone.utc)

    await db.flush()
    return row
