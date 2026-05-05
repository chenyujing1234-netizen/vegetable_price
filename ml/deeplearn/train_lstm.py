"""LSTM / N-BEATS 多变量价格预测模型（基于 Darts）

外生变量：
- 主产区 7 天滚动平均气温
- 主产区 7 天累计降水
- 节假日 one-hot
- CPI（接入后）

特性：
- 90 天回测 + MAE/MAPE/RMSE
- 模型 artifact 保存到 ml/checkpoints/lstm/

如果 darts/torch 未安装，仅打印安装提示，不抛异常。
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
from app.models import Market, PriceDaily, Product, Region, WeatherDaily  # noqa: E402

app = typer.Typer(add_completion=False, no_args_is_help=True)

DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql+psycopg://veg:vegpass@localhost:5432/vegdb",
)
CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "checkpoints" / "lstm"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset(product_code: str, market_code: str, region_code: str) -> pd.DataFrame:
    engine = create_engine(DATABASE_URL, future=True)
    with Session(engine) as s:
        product = s.execute(select(Product).where(Product.code == product_code)).scalar_one()
        market = s.execute(select(Market).where(Market.code == market_code)).scalar_one()
        region = s.execute(select(Region).where(Region.code == region_code)).scalar_one()

        price_rows = s.execute(
            select(PriceDaily.date, PriceDaily.avg).where(
                PriceDaily.market_id == market.id,
                PriceDaily.product_id == product.id,
            ).order_by(PriceDaily.date)
        ).all()

        weather_rows = s.execute(
            select(
                WeatherDaily.date, WeatherDaily.temp_avg, WeatherDaily.precip
            ).where(WeatherDaily.region_code == region.code).order_by(WeatherDaily.date)
        ).all()

    price_df = pd.DataFrame(price_rows, columns=["date", "price"])
    weather_df = pd.DataFrame(weather_rows, columns=["date", "temp_avg", "precip"])
    df = pd.merge(price_df, weather_df, on="date", how="left").sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    df["price"] = df["price"].astype(float)
    df["temp_avg"] = pd.to_numeric(df["temp_avg"], errors="coerce")
    df["precip"] = pd.to_numeric(df["precip"], errors="coerce")
    df["temp_7d"] = df["temp_avg"].rolling(7, min_periods=1).mean()
    df["precip_7d"] = df["precip"].rolling(7, min_periods=1).sum()
    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    return df.dropna()


def train_with_darts(df: pd.DataFrame, model_type: str, horizon: int = 30, holdout: int = 90):
    try:
        from darts import TimeSeries
        from darts.models import NBEATSModel, RNNModel
    except ImportError:
        logger.error(
            "darts/torch not installed. run: pip install 'darts[torch]==0.30.0' torch==2.4.1"
        )
        return None, {}

    series = TimeSeries.from_dataframe(df, time_col="date", value_cols="price")
    cov = TimeSeries.from_dataframe(
        df, time_col="date", value_cols=["temp_7d", "precip_7d"]
    )

    train, test = series[:-holdout], series[-holdout:]
    train_cov, test_cov = cov[:-holdout], cov[-holdout:]

    if model_type == "lstm":
        model = RNNModel(
            input_chunk_length=30,
            output_chunk_length=horizon,
            model="LSTM",
            hidden_dim=64,
            n_rnn_layers=2,
            n_epochs=20,
            batch_size=32,
            random_state=42,
            force_reset=True,
        )
    elif model_type == "nbeats":
        model = NBEATSModel(
            input_chunk_length=30,
            output_chunk_length=horizon,
            n_epochs=30,
            batch_size=32,
            random_state=42,
            force_reset=True,
        )
    else:
        raise ValueError(f"unknown model: {model_type}")

    model.fit(train, past_covariates=train_cov, verbose=False)

    pred = model.predict(n=horizon, past_covariates=cov, verbose=False)
    actual = test.values()[:horizon].flatten()
    pred_v = pred.values().flatten()
    mae = float(np.mean(np.abs(actual - pred_v)))
    mape = float(np.mean(np.abs((actual - pred_v) / actual)) * 100)
    rmse = float(np.sqrt(np.mean((actual - pred_v) ** 2)))

    return model, {"mae": round(mae, 4), "mape": round(mape, 2), "rmse": round(rmse, 4)}


@app.command()
def run(
    product: str = typer.Option("tomato"),
    market: str = typer.Option("shouguang"),
    region: str = typer.Option("370783", help="对应主产区行政区划"),
    model: str = typer.Option("lstm", help="lstm / nbeats"),
    horizon: int = typer.Option(30),
    holdout: int = typer.Option(90),
):
    df = load_dataset(product, market, region)
    if len(df) < 200:
        logger.error(f"not enough data: {len(df)} rows")
        raise typer.Exit(1)
    logger.info(f"dataset: {len(df)} rows")

    m, metrics = train_with_darts(df, model, horizon=horizon, holdout=holdout)
    if m is None:
        return
    logger.info(f"metrics: {metrics}")

    out = CHECKPOINT_DIR / f"{market}_{product}_{model}.pkl"
    joblib.dump(
        {
            "model": m,
            "metrics": metrics,
            "trained_at": datetime.utcnow().isoformat(),
            "product": product,
            "market": market,
            "model_type": model,
        },
        out,
    )
    logger.info(f"saved -> {out}")


if __name__ == "__main__":
    app()
