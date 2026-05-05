"""农产品主表"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="标准品类名 e.g. 西红柿")
    category: Mapped[str] = mapped_column(String(32), default="vegetable")
    spec: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="规格 e.g. 普通/串番茄")
    unit: Mapped[str] = mapped_column(String(8), default="kg")
