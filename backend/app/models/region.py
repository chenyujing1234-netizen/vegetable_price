"""地区主表（省、市级别）"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Region(Base):
    __tablename__ = "regions"

    code: Mapped[str] = mapped_column(String(12), primary_key=True, comment="行政区划代码 (GB/T 2260)")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="地区名称")
    province: Mapped[str] = mapped_column(String(32), nullable=False, comment="所属省/直辖市")
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="city", comment="province/city/county")
    lng: Mapped[float | None] = mapped_column(nullable=True, comment="经度 WGS84")
    lat: Mapped[float | None] = mapped_column(nullable=True, comment="纬度 WGS84")
