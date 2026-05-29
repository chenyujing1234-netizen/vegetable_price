from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    url: str
    publish_at: datetime
    sentiment_score: float | None = None
    sentiment_label: str | None = None
    keywords: list[str] = []
    analysis_status: str = "none"
    analysis_summary: str | None = None
    has_analysis: bool = False


class NewsDetailOut(NewsOut):
    content: str | None = None
    analysis_detail: dict[str, Any] | None = None
    analyzed_at: datetime | None = None
    related_products: list[str] = []


class NewsAnalyzeOut(BaseModel):
    id: int
    title: str
    analysis_status: str
    analysis_summary: str | None = None
    analysis_detail: dict[str, Any] | None = None
    sentiment_label: str | None = None
    sentiment_score: float | None = None
    analyzed_at: datetime | None = None
    message: str = Field(default="解读完成")


class NewsDailySentiment(BaseModel):
    date: str
    avg_sentiment: float
    count: int
