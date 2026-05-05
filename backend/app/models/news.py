"""新闻表"""

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
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
