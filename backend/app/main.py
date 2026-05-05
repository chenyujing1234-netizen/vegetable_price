"""FastAPI 入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import (
    alerts,
    analytics,
    auth,
    factors,
    markets,
    news,
    policies,
    predictions,
    prices,
    public,
    weather,
)
from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Booting backend in {settings.app_env} mode")
    yield
    await engine.dispose()
    logger.info("Backend shut down")


app = FastAPI(
    title="蔬菜价格预测 SaaS API",
    description="面向农户、采购商和政策研究者的蔬菜价格预测平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "Vegetable Price Intelligence API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


app.include_router(markets.router, prefix="/api/markets", tags=["markets"])
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(policies.router, prefix="/api/policies", tags=["policies"])
app.include_router(factors.router, prefix="/api/factors", tags=["factors"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(public.router_keys, prefix="/api/auth/api-keys", tags=["auth"])
app.include_router(public.router, prefix="/api/v1/public", tags=["public-api"])
