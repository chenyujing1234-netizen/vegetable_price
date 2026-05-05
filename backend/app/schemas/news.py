from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class NewsDailySentiment(BaseModel):
    date: str
    avg_sentiment: float
    count: int
