"""批发市场主表"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="内部唯一编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="市场名称")
    region_code: Mapped[str] = mapped_column(
        ForeignKey("regions.code", onupdate="CASCADE"), index=True
    )
    level: Mapped[str] = mapped_column(String(16), default="city", comment="国家级 / 省级 / 地市级")
    is_origin: Mapped[bool] = mapped_column(default=False, comment="是否主产区市场")
    is_destination: Mapped[bool] = mapped_column(default=False, comment="是否主销区市场")
    lng: Mapped[float | None] = mapped_column(nullable=True)
    lat: Mapped[float | None] = mapped_column(nullable=True)
