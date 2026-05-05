"""天气日表"""

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeatherDaily(Base):
    __tablename__ = "weather_daily"

    region_code: Mapped[str] = mapped_column(
        ForeignKey("regions.code", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    temp_min: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True, comment="最低气温 ℃")
    temp_max: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True, comment="最高气温 ℃")
    temp_avg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    precip: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True, comment="降水量 mm")
    humidity: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True, comment="平均湿度 %")
    wind_speed: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True, comment="平均风速 m/s")
    weather: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="天气描述")
    source: Mapped[str] = mapped_column(String(32), default="htqx")

    __table_args__ = (
        PrimaryKeyConstraint("region_code", "date", name="pk_weather_daily"),
    )
