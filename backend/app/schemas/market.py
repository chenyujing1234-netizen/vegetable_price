"""市场 Schema"""

from pydantic import BaseModel, ConfigDict


class MarketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    region_code: str
    level: str
    is_origin: bool
    is_destination: bool
    lng: float | None = None
    lat: float | None = None
