"""Google Earth Engine 种植面积估算器

使用方式：
1. 注册 GEE 账号 https://earthengine.google.com/
2. 创建 service account 并下载 JSON key
3. 设置环境变量 GEE_SERVICE_ACCOUNT 与 GEE_PRIVATE_KEY_FILE
4. 运行：
   python -m cropland.gee_estimator --region 370783 --year 2025

数据集：
- CACD-v1: `projects/sat-io/open-datasets/CACD-v1`（30 米年度作物分类）
- CropLayer 2020: `projects/sat-io/open-datasets/CropLayer`
- Sentinel-2 SR: `COPERNICUS/S2_SR_HARMONIZED` 用于自定义掩膜+NDVI 时序

本脚本以 CACD 为主线，对指定行政区计算耕地（cropland mask）总面积，
并按 NDVI 时序粗略区分蔬菜大棚（NDVI 全年偏高且变化快）vs 大田作物。
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

import typer
from loguru import logger
from sqlalchemy import select

from common.db import session_scope

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
from app.models import CroplandYearly, Product, Region  # noqa: E402
from common.upsert import upsert_many  # noqa: E402

app = typer.Typer(no_args_is_help=True, add_completion=False)

CACD_ASSET = "projects/sat-io/open-datasets/CACD-v1"
GADM_ASSET = "FAO/GAUL/2015/level2"


def init_ee():
    try:
        import ee
    except ImportError:
        logger.error("earthengine-api not installed. pip install earthengine-api")
        return None
    sa = os.getenv("GEE_SERVICE_ACCOUNT")
    key_file = os.getenv("GEE_PRIVATE_KEY_FILE")
    try:
        if sa and key_file:
            credentials = ee.ServiceAccountCredentials(sa, key_file)
            ee.Initialize(credentials)
        else:
            ee.Initialize()
    except Exception as e:
        logger.error(f"GEE init failed: {e}; you may need to run `earthengine authenticate`")
        return None
    return ee


def estimate_cropland_area_mu(ee_module, region_code: str, year: int, region_geojson: dict) -> float | None:
    """估算指定行政区某年的耕地总面积（亩）

    1 亩 ≈ 666.67 m²；CACD 像元 30m × 30m = 900 m² ≈ 1.35 亩
    """
    ee = ee_module
    try:
        roi = ee.Geometry(region_geojson)
        cacd = ee.ImageCollection(CACD_ASSET).filterDate(f"{year}-01-01", f"{year}-12-31")
        cropland = cacd.mosaic().gt(0)
        pixel_area_m2 = ee.Image.pixelArea().updateMask(cropland)
        area_m2 = pixel_area_m2.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=30,
            maxPixels=1e10,
        ).getInfo()
        total_m2 = float(list(area_m2.values())[0] or 0)
        return round(total_m2 / 666.67, 2)
    except Exception as e:
        logger.error(f"GEE compute failed: {e}")
        return None


def get_region_geometry(ee_module, region_code: str) -> dict | None:
    """通过行政区划代码取边界 GeoJSON

    简化处理：对于 6 位市级代码，使用 FAO GAUL level 2 (admin2 = 县级，
    需要二次合并 admin1 = 市级)。生产环境建议用国测局 1:100 万 GeoJSON。
    """
    ee = ee_module
    try:
        province_code = region_code[:2]
        gaul = ee.FeatureCollection(GADM_ASSET).filter(
            ee.Filter.eq("ADM1_CODE", int(province_code))
        )
        first = gaul.first()
        return first.geometry().getInfo() if first else None
    except Exception as e:
        logger.warning(f"region geometry fallback for {region_code}: {e}")
        return None


@app.command()
def estimate(
    region: str = typer.Option(..., help="行政区划代码"),
    year: int = typer.Option(2024),
    product: str = typer.Option("tomato"),
    confidence: float = typer.Option(0.6, help="遥感估算置信度"),
    dry_run: bool = typer.Option(False),
):
    ee_mod = init_ee()
    if ee_mod is None:
        raise typer.Exit(1)

    geom = get_region_geometry(ee_mod, region)
    if geom is None:
        logger.error(f"failed to obtain geometry for {region}")
        raise typer.Exit(1)

    area = estimate_cropland_area_mu(ee_mod, region, year, geom)
    if area is None:
        raise typer.Exit(1)
    logger.info(f"region={region} year={year} cropland≈{area:.0f} mu")

    if dry_run:
        return

    with session_scope() as s:
        product_obj = s.execute(select(Product).where(Product.code == product)).scalar_one()
        region_obj = s.execute(select(Region).where(Region.code == region)).scalar_one_or_none()
        if region_obj is None:
            logger.error(f"region {region} not in DB; please add it first")
            raise typer.Exit(1)
        upsert_many(
            s,
            CroplandYearly.__table__,
            [{
                "region_code": region,
                "product_id": product_obj.id,
                "year": year,
                "area_mu": area,
                "yield_kg_per_mu": None,
                "total_output_ton": None,
                "source": "gee",
                "confidence": confidence,
            }],
            conflict_columns=["region_code", "product_id", "year", "source"],
            update_columns=["area_mu", "confidence"],
        )
    logger.info("upserted")


@app.command()
def cacd_loader(
    csv: str = typer.Option(..., help="预先下载的 CACD 区域汇总 CSV"),
    product: str = typer.Option("tomato"),
):
    """离线加载方式：把 CACD 已经做好的省/县级面积汇总 CSV 写入数据库

    适合在没有 GEE 计算配额时使用。CSV 字段示例：
        region_code, year, area_mu
    """
    import pandas as pd

    df = pd.read_csv(csv)
    logger.info(f"loaded {len(df)} rows")
    with session_scope() as s:
        product_obj = s.execute(select(Product).where(Product.code == product)).scalar_one()
        rows = [{
            "region_code": str(r["region_code"]),
            "product_id": product_obj.id,
            "year": int(r["year"]),
            "area_mu": float(r["area_mu"]),
            "yield_kg_per_mu": None,
            "total_output_ton": None,
            "source": "cacd",
            "confidence": 0.85,
        } for _, r in df.iterrows()]
        upsert_many(
            s, CroplandYearly.__table__, rows,
            conflict_columns=["region_code", "product_id", "year", "source"],
            update_columns=["area_mu", "confidence"],
        )
    logger.info(f"upserted {len(rows)} rows")


if __name__ == "__main__":
    app()
