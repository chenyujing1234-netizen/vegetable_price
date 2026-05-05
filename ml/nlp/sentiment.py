"""新闻情感分析 + 关键词提取（bge-base-zh + 词典 hybrid）

策略：
1. 词典法（PRICE_UP / PRICE_DOWN / NEUTRAL）给基础分
2. 用 bge-base-zh-v1.5 计算与 [价格上涨, 价格下跌, 中性] 三个 anchor 的余弦相似度
   作为补充信号
3. 二者加权融合输出最终情感得分

如果未安装 sentence-transformers，会自动降级为纯词典模式。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import typer
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import News  # noqa: E402

app = typer.Typer(add_completion=False, no_args_is_help=True)

DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql+psycopg://veg:vegpass@localhost:5432/vegdb",
)


PRICE_UP_WORDS = [
    "上涨", "走高", "看涨", "回暖", "上扬", "飙升", "暴涨", "突破", "站上",
    "供给紧张", "减产", "灾害", "冻害", "暴雨", "受灾", "短缺",
]
PRICE_DOWN_WORDS = [
    "下跌", "跌势", "看跌", "回落", "下行", "暴跌", "走低", "下滑",
    "供过于求", "丰产", "增产", "扩种", "扩大产能", "滞销", "菜贱",
    "稳价", "保供", "投放储备", "降本",
]


def lex_score(text: str) -> tuple[str, float]:
    pos = sum(text.count(w) for w in PRICE_UP_WORDS)
    neg = sum(text.count(w) for w in PRICE_DOWN_WORDS)
    total = pos + neg
    if total == 0:
        return "neutral", 0.0
    score = (pos - neg) / total
    label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
    return label, round(score, 3)


@dataclass
class EmbedAnalyzer:
    model_name: str = "BAAI/bge-base-zh-v1.5"

    def __post_init__(self):
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
            self.anchors = self.model.encode(
                ["蔬菜价格上涨", "蔬菜价格下跌", "蔬菜价格平稳"],
                normalize_embeddings=True,
            )
            self.available = True
        except Exception as e:
            logger.warning(f"sentence-transformers not available, fallback to lexicon: {e}")
            self.available = False

    def score(self, text: str) -> tuple[str, float] | None:
        if not self.available:
            return None
        import numpy as np

        emb = self.model.encode([text], normalize_embeddings=True)[0]
        sims = self.anchors @ emb
        up, down, _ = sims[0], sims[1], sims[2]
        score = float(up - down)
        label = "positive" if score > 0.05 else ("negative" if score < -0.05 else "neutral")
        return label, round(score, 3)


def hybrid_score(text: str, embed: EmbedAnalyzer | None) -> tuple[str, float]:
    lex_label, lex = lex_score(text)
    if embed is None or not embed.available:
        return lex_label, lex
    emb_res = embed.score(text)
    if emb_res is None:
        return lex_label, lex
    _, emb = emb_res
    final = round(0.5 * lex + 0.5 * emb, 3)
    label = "positive" if final > 0.15 else ("negative" if final < -0.15 else "neutral")
    return label, final


@app.command()
def reanalyze(
    limit: int = typer.Option(500, help="回填最近 N 条新闻"),
    use_embed: bool = typer.Option(True, help="是否使用 bge-base-zh"),
):
    embed = EmbedAnalyzer() if use_embed else None
    engine = create_engine(DATABASE_URL, future=True)
    with Session(engine) as s:
        rows = s.execute(
            select(News).order_by(News.publish_at.desc()).limit(limit)
        ).scalars().all()
        n = 0
        for r in rows:
            text = (r.title or "") + " " + (r.content or "")
            label, score = hybrid_score(text, embed)
            r.sentiment_label = label
            r.sentiment_score = score
            n += 1
        s.commit()
    logger.info(f"updated sentiment for {n} news items")


if __name__ == "__main__":
    app()
