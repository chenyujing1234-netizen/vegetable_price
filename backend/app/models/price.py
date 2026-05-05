"""价格日表（TimescaleDB hypertable）"""

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceDaily(Base):
    __tablename__ = "price_daily"

    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    low: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True, comment="最低价 元/公斤")
    avg: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, comment="均价 元/公斤")
    high: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True, comment="最高价 元/公斤")
    volume: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True, comment="成交量 吨")
    source: Mapped[str] = mapped_column(String(32), default="moa", comment="数据来源标识")

    __table_args__ = (
        PrimaryKeyConstraint("market_id", "product_id", "date", name="pk_price_daily"),
    )
