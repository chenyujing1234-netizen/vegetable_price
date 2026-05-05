"""预测 Schema"""

from datetime import date, datetime

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: date
    forecast: float
    lower_80: float | None = None
    upper_80: float | None = None
    lower_95: float | None = None
    upper_95: float | None = None


class ForecastSeries(BaseModel):
    market_id: int
    market_name: str
    product_id: int
    product_name: str
    model: str
    run_at: datetime
    horizon_days: int
    points: list[ForecastPoint]
    metrics: dict | None = None


class ModelMetric(BaseModel):
    model: str
    mae: float
    mape: float
    rmse: float
    last_evaluated_at: datetime
