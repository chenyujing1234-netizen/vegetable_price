"""固定农业新闻来源配置

爬虫通过 site: 限定域名，从权威农业媒体抓取标题与链接；
正文在用户点击「解读」时由后端按需抓取。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSource:
    id: str
    name: str
    domain: str
    description: str
    default_keywords: tuple[str, ...]


# 国内农业/菜价相关权威来源（可按需扩展）
FIXED_NEWS_SOURCES: list[NewsSource] = [
    NewsSource(
        id="farmer",
        name="农民日报",
        domain="farmer.com.cn",
        description="农业农村部主管，政策与产销权威",
        default_keywords=("蔬菜价格", "菜篮子", "西红柿"),
    ),
    NewsSource(
        id="agri",
        name="中国农业新闻网",
        domain="agri.cn",
        description="全国农业行业动态",
        default_keywords=("蔬菜", "批发价格", "农产品"),
    ),
    NewsSource(
        id="nfncb",
        name="南方农村报",
        domain="nfncb.cn",
        description="华南地区农业与菜价报道",
        default_keywords=("蔬菜价格", "菜价", "批发"),
    ),
    NewsSource(
        id="xinhua",
        name="新华财经",
        domain="news.cn",
        description="宏观与民生价格报道",
        default_keywords=("菜价", "蔬菜价格", "CPI"),
    ),
    NewsSource(
        id="sina",
        name="新浪财经",
        domain="finance.sina.com.cn",
        description="农产品期货与批发行情",
        default_keywords=("蔬菜", "农产品价格"),
    ),
]


def get_source(source_id: str) -> NewsSource | None:
    for s in FIXED_NEWS_SOURCES:
        if s.id == source_id:
            return s
    return None
