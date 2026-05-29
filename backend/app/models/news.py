"""新闻表"""

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(64), comment="来源 e.g. 新浪财经")
    url: Mapped[str] = mapped_column(String(512), unique=True)
    publish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(
        Numeric(4, 3), nullable=True, comment="-1(消极) ~ +1(积极)"
    )
    sentiment_label: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="positive/neutral/negative"
    )
    related_products: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list)
    # 用户点击「解读」后按需生成，不预跑全文分析
    analysis_status: Mapped[str] = mapped_column(
        String(16), default="none", comment="none|done|failed"
    )
    analysis_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="平台观点摘要（面向农户可读）"
    )
    analysis_detail: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="结构化解读：价格影响、因子、建议等"
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
