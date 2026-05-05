"""种植面积年表"""

from sqlalchemy import ForeignKey, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CroplandYearly(Base):
    __tablename__ = "cropland_yearly"

    region_code: Mapped[str] = mapped_column(
        ForeignKey("regions.code", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    year: Mapped[int] = mapped_column(index=True)
    area_mu: Mapped[float] = mapped_column(Numeric(14, 2), comment="种植面积 亩")
    yield_kg_per_mu: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="单产 公斤/亩"
    )
    total_output_ton: Mapped[float | None] = mapped_column(
        Numeric(14, 2), nullable=True, comment="总产量 吨"
    )
    source: Mapped[str] = mapped_column(
        String(32), default="nbs", comment="nbs(国家统计局)/cacd/croplayer/gee"
    )
    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2), default=1.0, comment="置信度 0-1，遥感估算 < 1"
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "region_code", "product_id", "year", "source", name="pk_cropland_yearly"
        ),
    )
