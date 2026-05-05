"""通用 Schema"""

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    size: int = 50


class Message(BaseModel):
    message: str
    code: int = 0
