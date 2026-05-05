"""影响因子分析服务"""

from datetime import date, timedelta
from typing import Sequence

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PriceDaily, Policy, WeatherDaily
from app.schemas.factor import CorrelationItem, CorrelationReport, FactorOverview, FactorScore


# 学术研究综合得到的因子权重（论文：蔬菜价格波动的共同影响因子与宏观决定因素 等）
DEFAULT_FACTORS: list[FactorScore] = [
    FactorScore(
        factor="planting_area",
        name="种植面积",
        weight=0.25,
        direction="negative",
        description="供给端核心因素，种植面积扩大通常压低次年价格",
    ),
    FactorScore(
        factor="weather",
        name="天气（温度/降水/灾害）",
        weight=0.22,
        direction="bidirectional",
        description="主产区极端天气直接影响单产与上市节奏",
    ),
    FactorScore(
        factor="seasonality",
        name="季节性 + 节假日效应",
        weight=0.15,
        direction="bidirectional",
        description="春节/中秋等会显著加剧蔬菜价格波动（冬储期价格高）",
    ),
    FactorScore(
        factor="policy",
        name="政策调控",
        weight=0.10,
        direction="positive",
        description="生产端调控政策约 4 个月正向影响、流通端约 3 个月",
    ),
    FactorScore(
        factor="logistics_cost",
        name="流通与人工成本",
        weight=0.09,
        direction="positive",
        description="油价、运费、人工工资上升直接推高终端价格",
    ),
    FactorScore(
        factor="cpi_macro",
        name="CPI / 货币流动性",
        weight=0.07,
        direction="positive",
        description="货币 M2、CPI 与农产品价格长期正相关",
    ),
    FactorScore(
        factor="substitutes",
        name="替代品价格联动",
        weight=0.06,
        direction="positive",
        description="黄瓜、辣椒、茄子等价格互为替代会产生联动",
    ),
    FactorScore(
        factor="news_sentiment",
        name="舆情情绪",
        weight=0.06,
        direction="bidirectional",
        description="灾害/丰产/政策舆情会影响短期市场预期",
    ),
]


async def get_factor_overview(product_id: int, product_name: str) -> FactorOverview:
    return FactorOverview(
        product_id=product_id,
        product_name=product_name,
        factors=DEFAULT_FACTORS,
    )


async def correlate_price_weather(
    db: AsyncSession,
    market_id: int,
    product_id: int,
    region_code: str,
    start: date,
    end: date,
) -> CorrelationReport:
    price_rows = (
        await db.execute(
            select(PriceDaily.date, PriceDaily.avg).where(
                PriceDaily.market_id == market_id,
                PriceDaily.product_id == product_id,
                PriceDaily.date >= start,
                PriceDaily.date <= end,
            )
        )
    ).all()
    weather_rows = (
        await db.execute(
            select(
                WeatherDaily.date,
                WeatherDaily.temp_avg,
                WeatherDaily.temp_max,
                WeatherDaily.temp_min,
                WeatherDaily.precip,
                WeatherDaily.humidity,
            ).where(
                WeatherDaily.region_code == region_code,
                WeatherDaily.date >= start,
                WeatherDaily.date <= end,
            )
        )
    ).all()

    if not price_rows or not weather_rows:
        return CorrelationReport(target="price_avg", items=[])

    price_df = pd.DataFrame(price_rows, columns=["date", "price"]).astype({"price": float})
    weather_df = pd.DataFrame(
        weather_rows,
        columns=["date", "temp_avg", "temp_max", "temp_min", "precip", "humidity"],
    )
    for c in ["temp_avg", "temp_max", "temp_min", "precip", "humidity"]:
        weather_df[c] = pd.to_numeric(weather_df[c], errors="coerce")

    merged = pd.merge(price_df, weather_df, on="date", how="inner").dropna()
    items: list[CorrelationItem] = []
    for col in ["temp_avg", "temp_max", "temp_min", "precip", "humidity"]:
        if col not in merged.columns or merged[col].std() == 0:
            continue
        corr = float(np.corrcoef(merged["price"], merged[col])[0, 1])
        items.append(CorrelationItem(feature=col, correlation=round(corr, 3)))

    return CorrelationReport(target="price_avg", items=items)


async def event_study_policy(
    db: AsyncSession,
    market_id: int,
    product_id: int,
    product_code: str,
    window: int = 30,
) -> list[dict]:
    """事件研究法：对每条相关政策发布前后 window 天计算价格平均偏离

    输出形如：
        [{policy_id, title, publish_date, before_avg, after_avg, abnormal_pct}]
    """
    policies_q = await db.execute(
        select(Policy).where(Policy.related_products.any(product_code)).order_by(Policy.publish_date.desc())
    )
    policies = policies_q.scalars().all()
    if not policies:
        return []

    price_q = await db.execute(
        select(PriceDaily.date, PriceDaily.avg).where(
            PriceDaily.market_id == market_id, PriceDaily.product_id == product_id
        ).order_by(PriceDaily.date)
    )
    price_df = pd.DataFrame(price_q.all(), columns=["date", "price"]).astype({"price": float})
    if price_df.empty:
        return []
    price_df["date"] = pd.to_datetime(price_df["date"])
    price_df = price_df.set_index("date")

    out: list[dict] = []
    for p in policies:
        center = pd.Timestamp(p.publish_date)
        start = center - pd.Timedelta(days=window)
        end = center + pd.Timedelta(days=window)
        sub = price_df.loc[(price_df.index >= start) & (price_df.index <= end)]
        if len(sub) < 10:
            continue
        before = sub.loc[sub.index < center, "price"]
        after = sub.loc[sub.index >= center, "price"]
        if before.empty or after.empty:
            continue
        before_avg = float(before.mean())
        after_avg = float(after.mean())
        abnormal = round((after_avg - before_avg) / before_avg * 100, 2) if before_avg else 0.0
        out.append({
            "policy_id": p.id,
            "title": p.title,
            "publisher": p.publisher,
            "publish_date": str(p.publish_date),
            "before_avg": round(before_avg, 3),
            "after_avg": round(after_avg, 3),
            "abnormal_pct": abnormal,
            "impact_direction": p.impact_direction,
        })
    return out


def granger_causality(price_series: pd.Series, exog_series: pd.Series, max_lag: int = 7) -> dict:
    """简化版格兰杰因果：返回每个 lag 的 F 检验 p-value

    需要 statsmodels；未安装时返回空。
    """
    try:
        from statsmodels.tsa.stattools import grangercausalitytests
    except ImportError:
        return {"error": "statsmodels not installed"}

    df = pd.concat([price_series, exog_series], axis=1).dropna()
    df.columns = ["price", "exog"]
    if len(df) < max_lag * 4:
        return {"error": "insufficient data"}
    try:
        res = grangercausalitytests(df, maxlag=max_lag, verbose=False)
        return {
            f"lag_{k}": round(float(v[0]["ssr_ftest"][1]), 4) for k, v in res.items()
        }
    except Exception as e:
        return {"error": str(e)}


async def granger_weather_to_price(
    db: AsyncSession,
    market_id: int,
    product_id: int,
    region_code: str,
    feature: str = "temp_avg",
    days: int = 720,
    max_lag: int = 7,
) -> dict:
    end = date.today()
    start = end - timedelta(days=days)
    price_q = await db.execute(
        select(PriceDaily.date, PriceDaily.avg).where(
            PriceDaily.market_id == market_id,
            PriceDaily.product_id == product_id,
            PriceDaily.date >= start,
            PriceDaily.date <= end,
        ).order_by(PriceDaily.date)
    )
    weather_q = await db.execute(
        select(WeatherDaily.date, getattr(WeatherDaily, feature)).where(
            WeatherDaily.region_code == region_code,
            WeatherDaily.date >= start,
            WeatherDaily.date <= end,
        ).order_by(WeatherDaily.date)
    )
    price_df = pd.DataFrame(price_q.all(), columns=["date", "price"]).astype({"price": float})
    weather_df = pd.DataFrame(weather_q.all(), columns=["date", feature])
    weather_df[feature] = pd.to_numeric(weather_df[feature], errors="coerce")

    merged = pd.merge(price_df, weather_df, on="date", how="inner").dropna()
    if len(merged) < 60:
        return {"error": "insufficient data", "n": len(merged)}
    return {
        "feature": feature,
        "n": len(merged),
        "p_values": granger_causality(merged["price"], merged[feature], max_lag=max_lag),
    }
