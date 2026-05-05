"""集成模型评估：将 Prophet + LSTM 结果加权融合并与 baseline 对比

权重：基于回测 MAPE 的反比例（越准权重越大）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import typer
from loguru import logger

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

app = typer.Typer(add_completion=False, no_args_is_help=True)

ROOT = Path(__file__).resolve().parent.parent / "checkpoints"


def load_artifact(model_dir: str, market: str, product: str, suffix: str = "") -> dict | None:
    fn = ROOT / model_dir / f"{market}_{product}{('_' + suffix) if suffix else ''}.pkl"
    if not fn.exists():
        logger.warning(f"missing artifact: {fn}")
        return None
    return joblib.load(fn)


@app.command()
def run(
    product: str = typer.Option("tomato"),
    market: str = typer.Option("shouguang"),
):
    prophet_a = load_artifact("prophet", market, product)
    lstm_a = load_artifact("lstm", market, product, suffix="lstm")
    nbeats_a = load_artifact("lstm", market, product, suffix="nbeats")

    found = [(k, a) for k, a in [("prophet", prophet_a), ("lstm", lstm_a), ("nbeats", nbeats_a)] if a]
    if not found:
        logger.error("no model artifacts found; train them first")
        raise typer.Exit(1)

    rows = []
    for name, a in found:
        m = a.get("metrics", {})
        rows.append({"model": name, **m})

    df = pd.DataFrame(rows)
    logger.info("\n" + df.to_string(index=False))

    valid_mape = df[df["mape"].notna()]
    if not valid_mape.empty:
        weights = 1.0 / np.maximum(valid_mape["mape"].values, 0.01)
        weights = weights / weights.sum()
        valid_mape = valid_mape.assign(weight=weights.round(3))
        logger.info("\n=== ensemble weights (based on MAPE) ===")
        logger.info("\n" + valid_mape[["model", "mape", "weight"]].to_string(index=False))


if __name__ == "__main__":
    app()
