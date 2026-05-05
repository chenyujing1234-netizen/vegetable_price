from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Market, Product
from app.schemas.market import MarketOut
from app.schemas.product import ProductOut

router = APIRouter()


@router.get("", response_model=list[MarketOut])
async def list_markets(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Market).order_by(Market.id))).scalars().all()
    return rows


@router.get("/products", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Product).order_by(Product.id))).scalars().all()
    return rows
