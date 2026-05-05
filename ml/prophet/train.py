"""Prophet 模型独立训练脚本

特性：
- 中国节假日（春节/国庆/中秋/清明/五一/端午）作为外生变量
- 周/年季节性
- 留出 90 天回测，输出 MAE / MAPE / RMSE
- 模型 artifact 保存为 joblib pickle
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import typer
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import Market, PriceDaily, Product  # noqa: E402

app = typer.Typer(add_completion=False, no_args_is_help=True)

DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql+psycopg://veg:vegpass@localhost:5432/vegdb",
)
CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "checkpoints" / "prophet"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


# 同 backend forecast_service 中的简化节假日表
HOLIDAYS = pd.DataFrame({
    "holiday": [
        "spring_festival", "spring_festival", "spring_festival", "spring_festival",
        "spring_festival", "spring_festival",
        "national_day", "national_day", "national_day", "national_day",
        "national_day", "national_day",
        "mid_autumn", "mid_autumn", "mid_autumn", "mid_autumn", "mid_autumn",
        "qingming", "qingming", "qingming", "qingming", "qingming",
        "labor_day", "labor_day", "labor_day", "labor_day", "labor_day",
        "dragon_boat", "dragon_boat", "dragon_boat", "dragon_boat", "dragon_boat",
    ],
    "ds": pd.to_datetime([
        "2022-02-01", "2023-01-22", "2024-02-10", "2025-01-29", "2026-02-17", "2027-02-06",
        "2022-10-01", "2023-10-01", "2024-10-01", "2025-10-01", "2026-10-01", "2027-10-01",
        "2022-09-10", "2023-09-29", "2024-09-17", "2025-10-06", "2026-09-25",
        "2022-04-05", "2023-04-05", "2024-04-04", "2025-04-04", "2026-04-05",
        "2022-05-01", "2023-05-01", "2024-05-01", "2025-05-01", "2026-05-01",
        "2022-06-03", "2023-06-22", "2024-06-10", "2025-05-31", "2026-06-19",
    ]),
    "lower_window": 0,
    "upper_window": 3,
})


def load_series(product_code: str, market_code: str) -> pd.DataFrame:
    engine = create_engine(DATABASE_URL, future=True)
    with Session(engine) as s:
        product = s.execute(select(Product).where(Product.code == product_code)).scalar_one()
        market = s.execute(select(Market).where(Market.code == market_code)).scalar_one()
        rows = s.execute(
            select(PriceDaily.date, PriceDaily.avg).where(
                PriceDaily.market_id == market.id,
                PriceDaily.product_id == product.id,
            ).order_by(PriceDaily.date)
        ).all()
    df = pd.DataFrame(rows, columns=["ds", "y"])
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = df["y"].astype(float)
    return df


def train_one(df: pd.DataFrame, holdout: int = 90):
    from prophet import Prophet

    train = df.iloc[:-holdout].copy() if holdout > 0 and len(df) > holdout + 30 else df.copy()
    test = df.iloc[-holdout:].copy() if holdout > 0 and len(df) > holdout + 30 else None

    m = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        holidays=HOLIDAYS,
        interval_width=0.95,
        changepoint_prior_scale=0.05,
    )
    m.fit(train)

    metrics = {}
    if test is not None and len(test) > 0:
        future = m.make_future_dataframe(periods=len(test), freq="D")
        forecast = m.predict(future)
        pred = forecast.iloc[-len(test):]["yhat"].values
        actual = test["y"].values
        mae = float(np.mean(np.abs(actual - pred)))
        mape = float(np.mean(np.abs((actual - pred) / actual)) * 100)
        rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))
        metrics = {"mae": round(mae, 4), "mape": round(mape, 2), "rmse": round(rmse, 4)}

    return m, metrics


@app.command()
def run(
    product: str = typer.Option("tomato"),
    market: str = typer.Option("shouguang"),
    holdout: int = typer.Option(90),
    horizon: int = typer.Option(30),
):
    df = load_series(product, market)
    if len(df) < 60:
        logger.error(f"not enough data: {len(df)} rows")
        raise typer.Exit(1)
    logger.info(f"loaded {len(df)} rows from {df.iloc[0].ds} to {df.iloc[-1].ds}")

    model, metrics = train_one(df, holdout=holdout)
    logger.info(f"backtest metrics: {metrics}")

    out = CHECKPOINT_DIR / f"{market}_{product}.pkl"
    joblib.dump(
        {
            "model": model,
            "metrics": metrics,
            "trained_at": datetime.utcnow().isoformat(),
            "n_train": len(df) - holdout,
            "horizon": horizon,
            "product": product,
            "market": market,
        },
        out,
    )
    logger.info(f"saved -> {out}")


if __name__ == "__main__":
    app()
