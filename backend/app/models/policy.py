"""政策表"""

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    publisher: Mapped[str] = mapped_column(String(128), comment="发布机构")
    publish_date: Mapped[date] = mapped_column(Date, index=True)
    url: Mapped[str] = mapped_column(String(512), unique=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="摘要")
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_level: Mapped[str] = mapped_column(
        String(16), default="medium", comment="low/medium/high"
    )
    impact_direction: Mapped[str] = mapped_column(
        String(16), default="neutral", comment="positive/negative/neutral 对价格"
    )
    related_products: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, comment="影响的产品 code 列表"
    )
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(64)), default=list)
