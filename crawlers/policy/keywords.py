"""政策/新闻关键词词典 + 关联产品识别"""

POLICY_KEYWORDS = [
    "蔬菜", "菜篮子", "保供", "稳价", "收储", "储备", "补贴",
    "鲜活农产品", "绿色通道", "设施大棚", "设施蔬菜", "种植面积",
    "农产品价格", "农资", "种子", "化肥", "化肥价格",
]

PRODUCT_KEYWORDS = {
    "tomato": ["番茄", "西红柿", "圣女果", "樱桃番茄"],
    "cucumber": ["黄瓜", "青瓜"],
    "chili": ["辣椒", "尖椒", "灯笼椒", "螺丝椒"],
    "potato": ["土豆", "马铃薯", "薯类"],
}


def is_relevant(text: str) -> bool:
    return any(k in text for k in POLICY_KEYWORDS)


def detect_products(text: str) -> list[str]:
    out = []
    for code, kws in PRODUCT_KEYWORDS.items():
        if any(k in text for k in kws):
            out.append(code)
    return out


def extract_keywords(text: str, top_k: int = 6) -> list[str]:
    """简易关键词提取：按词典命中频次排序

    生产环境替换为 jieba.analyse.extract_tags 或 HanLP 的 keyphrase。
    """
    counts = {}
    for k in POLICY_KEYWORDS:
        c = text.count(k)
        if c > 0:
            counts[k] = c
    for kws in PRODUCT_KEYWORDS.values():
        for k in kws:
            c = text.count(k)
            if c > 0:
                counts[k] = c
    sorted_kw = sorted(counts.items(), key=lambda x: -x[1])
    return [k for k, _ in sorted_kw[:top_k]]
