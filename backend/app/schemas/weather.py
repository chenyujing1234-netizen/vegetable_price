from datetime import date

from pydantic import BaseModel, ConfigDict


class WeatherPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    temp_min: float | None = None
    temp_max: float | None = None
    temp_avg: float | None = None
    precip: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    weather: str | None = None


class WeatherSeries(BaseModel):
    region_code: str
    region_name: str
    points: list[WeatherPoint]
