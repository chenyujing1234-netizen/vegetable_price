"""种子数据：地区、市场、产品、合成的西红柿历史价格 + 天气 + 政策 + 新闻 + 种植面积

合成的价格序列基于真实趋势 + 季节性 + 节假日效应 + 噪声，便于在没有爬取
真实数据时也能完整跑通整个产品。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import math
import random


REGIONS: list[dict] = [
    # 主产区
    {"code": "370783", "name": "寿光市", "province": "山东省", "level": "city", "lng": 118.7363, "lat": 36.8814},
    {"code": "130100", "name": "石家庄市", "province": "河北省", "level": "city", "lng": 114.5149, "lat": 38.0428},
    {"code": "210600", "name": "丹东市", "province": "辽宁省", "level": "city", "lng": 124.3833, "lat": 40.1244},
    {"code": "650100", "name": "乌鲁木齐市", "province": "新疆", "level": "city", "lng": 87.6168, "lat": 43.8256},
    {"code": "451300", "name": "来宾市", "province": "广西", "level": "city", "lng": 109.2295, "lat": 23.7333},
    {"code": "350600", "name": "漳州市", "province": "福建省", "level": "city", "lng": 117.6612, "lat": 24.5109},
    # 主销区
    {"code": "110100", "name": "北京市", "province": "北京市", "level": "city", "lng": 116.4074, "lat": 39.9042},
    {"code": "310100", "name": "上海市", "province": "上海市", "level": "city", "lng": 121.4737, "lat": 31.2304},
    {"code": "440100", "name": "广州市", "province": "广东省", "level": "city", "lng": 113.2644, "lat": 23.1291},
    {"code": "440300", "name": "深圳市", "province": "广东省", "level": "city", "lng": 114.0579, "lat": 22.5431},
    {"code": "510100", "name": "成都市", "province": "四川省", "level": "city", "lng": 104.0665, "lat": 30.5728},
    {"code": "420100", "name": "武汉市", "province": "湖北省", "level": "city", "lng": 114.3055, "lat": 30.5928},
]


MARKETS: list[dict] = [
    {"code": "shouguang", "name": "山东寿光地利农产品物流园", "region_code": "370783", "level": "国家级", "is_origin": True, "is_destination": False},
    {"code": "shijiazhuang_qiaoxi", "name": "石家庄桥西蔬菜批发市场", "region_code": "130100", "level": "国家级", "is_origin": True, "is_destination": False},
    {"code": "dandong", "name": "丹东振兴农产品批发市场", "region_code": "210600", "level": "省级", "is_origin": True, "is_destination": False},
    {"code": "urumqi_jiufeng", "name": "乌鲁木齐九鼎农产品批发市场", "region_code": "650100", "level": "国家级", "is_origin": True, "is_destination": False},
    {"code": "laibin", "name": "来宾正菱蔬菜批发市场", "region_code": "451300", "level": "省级", "is_origin": True, "is_destination": False},
    {"code": "zhangzhou_minnan", "name": "漳州闽南果蔬批发市场", "region_code": "350600", "level": "省级", "is_origin": True, "is_destination": False},
    {"code": "beijing_xinfadi", "name": "北京新发地农产品批发市场", "region_code": "110100", "level": "国家级", "is_origin": False, "is_destination": True},
    {"code": "shanghai_jiangqiao", "name": "上海江桥蔬菜批发市场", "region_code": "310100", "level": "国家级", "is_origin": False, "is_destination": True},
    {"code": "guangzhou_jiangnan", "name": "广州江南果菜批发市场", "region_code": "440100", "level": "国家级", "is_origin": False, "is_destination": True},
    {"code": "shenzhen_haijixing", "name": "深圳海吉星农产品批发市场", "region_code": "440300", "level": "国家级", "is_origin": False, "is_destination": True},
    {"code": "chengdu_julong", "name": "成都聚合农产品批发市场", "region_code": "510100", "level": "国家级", "is_origin": False, "is_destination": True},
    {"code": "wuhan_baishazhou", "name": "武汉白沙洲农副产品批发市场", "region_code": "420100", "level": "国家级", "is_origin": False, "is_destination": True},
]


PRODUCTS: list[dict] = [
    {"code": "tomato", "name": "西红柿", "category": "vegetable", "spec": "普通", "unit": "kg"},
    {"code": "cucumber", "name": "黄瓜", "category": "vegetable", "spec": "普通", "unit": "kg"},
    {"code": "chili", "name": "辣椒", "category": "vegetable", "spec": "尖椒", "unit": "kg"},
    {"code": "potato", "name": "土豆", "category": "vegetable", "spec": "普通", "unit": "kg"},
    {"code": "cabbage", "name": "大白菜", "category": "vegetable", "spec": "普通", "unit": "kg"},
    {"code": "eggplant", "name": "茄子", "category": "vegetable", "spec": "紫皮", "unit": "kg"},
    {"code": "pakchoi", "name": "小白菜", "category": "vegetable", "spec": "普通", "unit": "kg"},
    {"code": "broccoli", "name": "西兰花", "category": "vegetable", "spec": "普通", "unit": "kg"},
]

# 各品类相对西红柿基准价的合成系数（用于 seed 数据生成）
PRODUCT_PRICE_FACTORS: dict[str, float] = {
    "tomato": 1.0,
    "cucumber": 0.95,
    "chili": 1.6,
    "potato": 0.55,
    "cabbage": 0.42,
    "eggplant": 0.88,
    "pakchoi": 0.48,
    "broccoli": 1.25,
}


# 不同市场的基础价格水平（产区低、销区高）
MARKET_BASE_PRICE = {
    "shouguang": 3.5,
    "shijiazhuang_qiaoxi": 3.6,
    "dandong": 3.8,
    "urumqi_jiufeng": 4.0,
    "laibin": 3.7,
    "zhangzhou_minnan": 3.6,
    "beijing_xinfadi": 5.2,
    "shanghai_jiangqiao": 5.6,
    "guangzhou_jiangnan": 5.8,
    "shenzhen_haijixing": 6.0,
    "chengdu_julong": 4.8,
    "wuhan_baishazhou": 4.6,
}


def synth_tomato_price(market_code: str, d: date, base: float) -> tuple[float, float, float]:
    """合成西红柿价格：基础水平 + 年内季节性 + 多年趋势 + 节假日 + 随机噪声"""
    doy = d.timetuple().tm_yday
    season = 0.45 * math.sin(2 * math.pi * (doy - 30) / 365)
    long_trend = (d.year - 2022) * 0.18
    holiday_boost = 0.0
    if (d.month == 1 and d.day >= 20) or (d.month == 2 and d.day <= 15):
        holiday_boost = 0.6
    if d.month == 10 and d.day <= 7:
        holiday_boost = 0.25

    rng = random.Random(hash((market_code, d.toordinal())) & 0xFFFF)
    noise = rng.uniform(-0.25, 0.25)

    avg = max(0.8, base + season + long_trend + holiday_boost + noise)
    spread = max(0.3, 0.18 * avg + rng.uniform(0.05, 0.2))
    low = round(max(0.3, avg - spread / 2), 3)
    high = round(avg + spread / 2, 3)
    return round(low, 3), round(avg, 3), round(high, 3)


def synth_other_veg_price(product_code: str, market_code: str, d: date, base_tomato: float) -> tuple[float, float, float]:
    f = PRODUCT_PRICE_FACTORS.get(product_code, 1.0)
    low, avg, high = synth_tomato_price(market_code + product_code, d, base_tomato * f)
    return low, avg, high


def synth_weather(region_code: str, d: date) -> dict:
    rng = random.Random(hash((region_code, d.toordinal())) & 0xFFFF)
    doy = d.timetuple().tm_yday

    base_temp_by_region = {
        "370783": 14, "130100": 14, "210600": 9, "650100": 8, "451300": 22,
        "350600": 21,
        "110100": 13, "310100": 17, "440100": 22, "440300": 23,
        "510100": 16, "420100": 17,
    }
    base = base_temp_by_region.get(region_code, 15)
    season = 14 * math.sin(2 * math.pi * (doy - 110) / 365)
    temp_avg = round(base + season + rng.uniform(-3, 3), 1)
    temp_min = round(temp_avg - rng.uniform(3, 7), 1)
    temp_max = round(temp_avg + rng.uniform(3, 7), 1)
    precip = round(max(0.0, rng.gauss(2.5, 6.0) if 4 <= d.month <= 9 else rng.gauss(0.6, 2.0)), 1)
    humidity = round(min(98, max(20, rng.gauss(65, 12))), 1)
    wind = round(max(0.0, rng.gauss(2.5, 1.2)), 1)
    weather = "晴"
    if precip > 8:
        weather = "大雨"
    elif precip > 1:
        weather = "小雨"
    elif rng.random() < 0.2:
        weather = "多云"
    return {
        "temp_min": temp_min,
        "temp_max": temp_max,
        "temp_avg": temp_avg,
        "precip": precip,
        "humidity": humidity,
        "wind_speed": wind,
        "weather": weather,
    }


SEED_POLICIES: list[dict] = [
    {
        "title": "农业农村部关于做好 2025 年 \"菜篮子\" 产品稳产保供工作的通知",
        "publisher": "农业农村部",
        "publish_date": date(2025, 1, 12),
        "url": "https://www.moa.gov.cn/seed/policy/202501-tomato-supply",
        "summary": "要求各地落实菜篮子市长负责制，扩大设施蔬菜生产能力，保障春节及'两会'期间蔬菜稳定供应。",
        "impact_level": "high",
        "impact_direction": "negative",
        "related_products": ["tomato", "cucumber", "chili"],
        "keywords": ["菜篮子", "保供", "设施蔬菜", "春节"],
    },
    {
        "title": "国家发改委关于加强重要民生商品价格调控监管的指导意见",
        "publisher": "国家发改委",
        "publish_date": date(2024, 11, 8),
        "url": "https://www.ndrc.gov.cn/seed/2024-11-priceregulation",
        "summary": "完善重要民生商品价格调控机制，蔬菜列入重点监测目录，价格异常波动启动预警和投放储备。",
        "impact_level": "high",
        "impact_direction": "negative",
        "related_products": ["tomato", "cucumber", "chili", "potato"],
        "keywords": ["价格调控", "民生", "储备投放"],
    },
    {
        "title": "山东省关于支持寿光蔬菜产业高质量发展的实施意见",
        "publisher": "山东省人民政府",
        "publish_date": date(2024, 6, 3),
        "url": "https://www.shandong.gov.cn/seed/2024-06-shouguang",
        "summary": "支持寿光建设全国最大的蔬菜种植和交易集散基地，新增设施大棚 50 万亩，预计 2-3 年内增加供给。",
        "impact_level": "medium",
        "impact_direction": "negative",
        "related_products": ["tomato", "cucumber"],
        "keywords": ["寿光", "设施大棚", "产能"],
    },
    {
        "title": "农业农村部启动 2024 年蔬菜临时收储工作",
        "publisher": "农业农村部",
        "publish_date": date(2024, 3, 15),
        "url": "https://www.moa.gov.cn/seed/2024-03-storage",
        "summary": "对集中上市期供过于求的部分蔬菜品类启动临时收储，缓解菜贱伤农。",
        "impact_level": "medium",
        "impact_direction": "positive",
        "related_products": ["tomato", "potato"],
        "keywords": ["收储", "保护价", "菜贱伤农"],
    },
    {
        "title": "财政部 农业农村部关于下达 2025 年农业生产救灾资金的通知",
        "publisher": "财政部",
        "publish_date": date(2025, 7, 22),
        "url": "https://www.mof.gov.cn/seed/2025-07-disaster",
        "summary": "针对寒潮、台风等灾害下达农业生产救灾资金 28 亿元，重点支持蔬菜复产。",
        "impact_level": "medium",
        "impact_direction": "positive",
        "related_products": ["tomato", "cucumber", "chili"],
        "keywords": ["灾害", "救灾", "复产"],
    },
]


SEED_NEWS: list[dict] = [
    {
        "title": "西红柿价格连续两周下跌，产地大棚扎堆上市",
        "source": "新华财经",
        "url": "https://news.example.com/seed-1",
        "publish_at": datetime(2025, 5, 18, 9, 30),
        "content": "受寿光等主产区大棚集中上市影响，本周西红柿批发均价环比下跌 12%，预计 6 月份跌势仍将延续。",
        "sentiment_score": -0.55,
        "sentiment_label": "negative",
        "related_products": ["tomato"],
        "keywords": ["西红柿", "寿光", "下跌"],
    },
    {
        "title": "寒潮来袭：北方设施蔬菜受灾，菜价短期或反弹",
        "source": "央视财经",
        "url": "https://news.example.com/seed-2",
        "publish_at": datetime(2025, 1, 8, 18, 12),
        "content": "强冷空气南下，山东、河北等地大棚作物受冻害影响，预计未来一周蔬菜批发价格将出现明显反弹。",
        "sentiment_score": 0.4,
        "sentiment_label": "positive",
        "related_products": ["tomato", "cucumber", "chili"],
        "keywords": ["寒潮", "冻害", "菜价上涨"],
    },
    {
        "title": "今年西红柿种植面积扩张 8%，业内提示防价格战",
        "source": "第一财经",
        "url": "https://news.example.com/seed-3",
        "publish_at": datetime(2025, 3, 22, 11, 0),
        "content": "调研显示今春主产区西红柿种植面积较去年增长约 8%，业内人士提示种植户警惕集中上市价格战风险。",
        "sentiment_score": -0.3,
        "sentiment_label": "negative",
        "related_products": ["tomato"],
        "keywords": ["种植面积", "价格战", "供过于求"],
    },
    {
        "title": "国务院常务会议部署稳定菜价相关举措",
        "source": "人民网",
        "url": "https://news.example.com/seed-4",
        "publish_at": datetime(2024, 11, 6, 20, 45),
        "content": "国务院常务会议研究部署稳定 \"菜篮子\" 产品供应和价格的相关政策，要求加强主产区与主销区产销衔接。",
        "sentiment_score": 0.1,
        "sentiment_label": "neutral",
        "related_products": ["tomato", "cucumber", "chili", "potato"],
        "keywords": ["国常会", "稳菜价", "产销衔接"],
    },
    {
        "title": "春节临近，全国蔬菜批发价格连续四周走高",
        "source": "新浪财经",
        "url": "https://news.example.com/seed-5",
        "publish_at": datetime(2025, 1, 25, 8, 0),
        "content": "随着春节临近，居民囤菜需求增加，叠加部分地区低温天气，全国蔬菜批发均价已连续四周走高。",
        "sentiment_score": 0.5,
        "sentiment_label": "positive",
        "related_products": ["tomato", "cucumber", "chili"],
        "keywords": ["春节", "囤菜", "价格上涨"],
    },
    {
        "title": "高速通行成本下降，蔬菜运输费用环比降 5%",
        "source": "经济观察网",
        "url": "https://news.example.com/seed-6",
        "publish_at": datetime(2025, 4, 10, 15, 20),
        "content": "鲜活农产品绿色通道政策落地，蔬菜公路运输成本环比下降约 5%，有助于平抑终端零售价。",
        "sentiment_score": 0.2,
        "sentiment_label": "positive",
        "related_products": ["tomato", "cucumber", "chili", "potato"],
        "keywords": ["物流", "绿色通道", "运输成本"],
    },
]


# 各产区西红柿种植面积（亩）数据（合成，但相对接近真实量级）
SEED_CROPLAND: list[dict] = [
    # 寿光（主产）
    {"region_code": "370783", "year": 2022, "area_mu": 600000, "yield_kg_per_mu": 9000},
    {"region_code": "370783", "year": 2023, "area_mu": 620000, "yield_kg_per_mu": 9200},
    {"region_code": "370783", "year": 2024, "area_mu": 650000, "yield_kg_per_mu": 9400},
    {"region_code": "370783", "year": 2025, "area_mu": 700000, "yield_kg_per_mu": 9500},
    # 河北
    {"region_code": "130100", "year": 2022, "area_mu": 380000, "yield_kg_per_mu": 7500},
    {"region_code": "130100", "year": 2023, "area_mu": 400000, "yield_kg_per_mu": 7600},
    {"region_code": "130100", "year": 2024, "area_mu": 410000, "yield_kg_per_mu": 7700},
    {"region_code": "130100", "year": 2025, "area_mu": 430000, "yield_kg_per_mu": 7800},
    # 辽宁丹东
    {"region_code": "210600", "year": 2022, "area_mu": 120000, "yield_kg_per_mu": 6500},
    {"region_code": "210600", "year": 2023, "area_mu": 130000, "yield_kg_per_mu": 6600},
    {"region_code": "210600", "year": 2024, "area_mu": 145000, "yield_kg_per_mu": 6700},
    {"region_code": "210600", "year": 2025, "area_mu": 158000, "yield_kg_per_mu": 6800},
    # 新疆
    {"region_code": "650100", "year": 2022, "area_mu": 180000, "yield_kg_per_mu": 8000},
    {"region_code": "650100", "year": 2023, "area_mu": 200000, "yield_kg_per_mu": 8100},
    {"region_code": "650100", "year": 2024, "area_mu": 230000, "yield_kg_per_mu": 8200},
    {"region_code": "650100", "year": 2025, "area_mu": 260000, "yield_kg_per_mu": 8300},
    # 广西
    {"region_code": "451300", "year": 2022, "area_mu": 90000, "yield_kg_per_mu": 5500},
    {"region_code": "451300", "year": 2023, "area_mu": 95000, "yield_kg_per_mu": 5600},
    {"region_code": "451300", "year": 2024, "area_mu": 100000, "yield_kg_per_mu": 5700},
    {"region_code": "451300", "year": 2025, "area_mu": 105000, "yield_kg_per_mu": 5800},
    # 福建漳州（南方冬菜重要产区，亚热带气候适合反季节种植）
    {"region_code": "350600", "year": 2022, "area_mu": 85000, "yield_kg_per_mu": 6800},
    {"region_code": "350600", "year": 2023, "area_mu": 92000, "yield_kg_per_mu": 6900},
    {"region_code": "350600", "year": 2024, "area_mu": 98000, "yield_kg_per_mu": 7000},
    {"region_code": "350600", "year": 2025, "area_mu": 105000, "yield_kg_per_mu": 7100},
]
