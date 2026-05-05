"""价格 Schema"""

from datetime import date

from pydantic import BaseModel, ConfigDict


class PricePoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    avg: float
    low: float | None = None
    high: float | None = None
    volume: float | None = None


class PriceSeries(BaseModel):
    market_id: int
    market_name: str
    product_id: int
    product_name: str
    points: list[PricePoint]


class PriceLatest(BaseModel):
    market_id: int
    market_name: str
    product_id: int
    product_name: str
    date: date
    avg: float
    yoy: float | None = None
    mom: float | None = None
    wow: float | None = None


class PriceHeatPoint(BaseModel):
    market_id: int
    market_name: str
    region_code: str
    lng: float | None
    lat: float | None
    avg: float
    yoy: float | None = None
