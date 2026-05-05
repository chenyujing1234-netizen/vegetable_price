"""开放公共 API (v1)

特点：
- 通过 X-API-Key Header 鉴权
- 内存级令牌桶速率限制（生产环境改用 Redis）
- 全部走只读接口，避免误操作

申请 API Key：
  POST /api/auth/api-keys  (需要登录态)

调用示例：
  curl -H "X-API-Key: vk_live_xxxx" \
       https://api.example.com/api/v1/prices/latest?product=tomato
"""

from __future__ import annotations

import hashlib
import secrets
import time
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_user
from app.database import get_db
from app.models import ApiKey, Market, PriceDaily, Product, User

router = APIRouter()
router_keys = APIRouter()


# ===== API Key 管理 =====


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    plan: str
    rate_limit_per_min: int
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    secret: str | None = None  # 只在创建时返回


@router_keys.get("", response_model=list[ApiKeyOut])
async def list_keys(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.id.desc())
    )).scalars().all()
    return [
        ApiKeyOut(
            id=r.id, name=r.name, key_prefix=r.key_prefix, plan=r.plan,
            rate_limit_per_min=r.rate_limit_per_min, is_active=r.is_active,
            created_at=r.created_at, last_used_at=r.last_used_at,
        )
        for r in rows
    ]


@router_keys.post("", response_model=ApiKeyOut)
async def create_key(
    name: str = "default",
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    raw = "vk_live_" + secrets.token_urlsafe(24)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    rate = {"free": 60, "pro": 600, "enterprise": 6000}.get(user.plan, 60)
    k = ApiKey(
        user_id=user.id,
        key_prefix=raw[:12],
        key_hash=digest,
        name=name,
        plan=user.plan,
        rate_limit_per_min=rate,
    )
    db.add(k)
    await db.commit()
    await db.refresh(k)
    return ApiKeyOut(
        id=k.id, name=k.name, key_prefix=k.key_prefix, plan=k.plan,
        rate_limit_per_min=k.rate_limit_per_min, is_active=k.is_active,
        created_at=k.created_at, last_used_at=None, secret=raw,
    )


# ===== 鉴权依赖 + 速率限制 =====

_RATE_BUCKETS: dict[int, list[float]] = {}


async def require_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(401, "missing X-API-Key header")
    digest = hashlib.sha256(x_api_key.encode()).hexdigest()
    key = (await db.execute(
        select(ApiKey).where(ApiKey.key_hash == digest, ApiKey.is_active.is_(True))
    )).scalar_one_or_none()
    if key is None:
        raise HTTPException(403, "invalid api key")

    bucket = _RATE_BUCKETS.setdefault(key.id, [])
    now = time.time()
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= key.rate_limit_per_min:
        raise HTTPException(
            429,
            f"rate limit exceeded: {key.rate_limit_per_min}/min for plan {key.plan}",
        )
    bucket.append(now)

    key.last_used_at = datetime.utcnow()
    await db.commit()
    return key


# ===== 公共数据接口 =====


@router.get("/prices/latest")
async def public_latest_price(
    product: str = Query(..., description="产品 code: tomato/cucumber/chili/potato"),
    market: str | None = Query(None, description="市场 code"),
    api_key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    p = (await db.execute(select(Product).where(Product.code == product))).scalar_one_or_none()
    if p is None:
        raise HTTPException(404, "unknown product")
    m = None
    if market:
        m = (await db.execute(select(Market).where(Market.code == market))).scalar_one_or_none()
        if m is None:
            raise HTTPException(404, "unknown market")

    today = (await db.execute(
        select(func.max(PriceDaily.date)).where(PriceDaily.product_id == p.id)
    )).scalar_one_or_none()
    if today is None:
        return {"product": p.code, "data": []}

    q = select(
        Market.code, Market.name, PriceDaily.avg, PriceDaily.low, PriceDaily.high
    ).join(Market, Market.id == PriceDaily.market_id).where(
        PriceDaily.product_id == p.id, PriceDaily.date == today,
    )
    if m is not None:
        q = q.where(PriceDaily.market_id == m.id)
    rows = (await db.execute(q)).all()
    return {
        "product": p.code,
        "date": str(today),
        "data": [
            {
                "market": code,
                "market_name": name,
                "avg": float(avg),
                "low": float(low) if low is not None else None,
                "high": float(high) if high is not None else None,
            }
            for code, name, avg, low, high in rows
        ],
    }


@router.get("/prices/series")
async def public_price_series(
    product: str = Query(...),
    market: str = Query(...),
    days: int = Query(90, ge=1, le=1825),
    api_key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date, timedelta

    p = (await db.execute(select(Product).where(Product.code == product))).scalar_one_or_none()
    m = (await db.execute(select(Market).where(Market.code == market))).scalar_one_or_none()
    if not p or not m:
        raise HTTPException(404, "product or market not found")
    end = date.today()
    start = end - timedelta(days=days)
    rows = (await db.execute(
        select(PriceDaily.date, PriceDaily.avg, PriceDaily.low, PriceDaily.high).where(
            PriceDaily.product_id == p.id,
            PriceDaily.market_id == m.id,
            PriceDaily.date >= start,
        ).order_by(PriceDaily.date)
    )).all()
    return {
        "product": p.code,
        "market": m.code,
        "points": [
            {"date": str(d), "avg": float(a), "low": float(l) if l is not None else None,
             "high": float(h) if h is not None else None}
            for d, a, l, h in rows
        ],
    }


@router.get("/products")
async def public_products(
    api_key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(Product).order_by(Product.id))).scalars().all()
    return [{"code": p.code, "name": p.name, "spec": p.spec} for p in rows]


@router.get("/markets")
async def public_markets(
    api_key: ApiKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(Market).order_by(Market.id))).scalars().all()
    return [
        {
            "code": m.code, "name": m.name, "region_code": m.region_code, "level": m.level,
            "is_origin": m.is_origin, "is_destination": m.is_destination,
            "lng": m.lng, "lat": m.lat,
        }
        for m in rows
    ]
