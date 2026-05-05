"""影响因子分析相关 Schema"""

from pydantic import BaseModel


class FactorScore(BaseModel):
    factor: str
    name: str
    weight: float
    direction: str
    description: str


class FactorOverview(BaseModel):
    product_id: int
    product_name: str
    factors: list[FactorScore]


class CorrelationItem(BaseModel):
    feature: str
    correlation: float
    p_value: float | None = None


class CorrelationReport(BaseModel):
    target: str
    items: list[CorrelationItem]
