"""价格预测结果归档"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    model: Mapped[str] = mapped_column(String(32), comment="prophet/lstm/ensemble")
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, comment="预测产出时间"
    )
    target_date: Mapped[date] = mapped_column(Date, index=True, comment="预测目标日期")
    forecast: Mapped[float] = mapped_column(Numeric(8, 3), comment="预测均价 元/公斤")
    lower_80: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    upper_80: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    lower_95: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    upper_95: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint(
            "market_id", "product_id", "model", "run_at", "target_date", name="pk_predictions"
        ),
    )
