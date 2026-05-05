from datetime import date

from pydantic import BaseModel, ConfigDict


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    publisher: str
    publish_date: date
    url: str
    summary: str | None = None
    impact_level: str
    impact_direction: str
    related_products: list[str] = []
    keywords: list[str] = []
