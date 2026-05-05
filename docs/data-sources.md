# 数据源说明

本文档列出当前接入与计划接入的所有数据源、采集频率、字段和合规要点。

## 1. 价格数据

### 1.1 农业农村部 - 全国农产品商务信息公共服务平台

- URL：<http://zdscxx.moa.gov.cn/>
- 频率：每日（T-1）
- 字段：市场名称、省份、品类、最低价、均价、最高价
- 实现：`crawlers/price/moa_crawler.py`
- 合规：仅采集页面公开汇总数据，请求间隔 ≥ 1s

### 1.2 食价搜（食品商务网）

- URL：<https://wap.21food.cn/price/>
- 频率：每日
- 字段：市场、规格、价格、日期
- 实现：`crawlers/price/food21_crawler.py`

### 1.3 中商情报网

- URL：<https://s.askci.com/data/price/170120>
- 频率：每日（图表数据为月度）
- 实现：`crawlers/price/askci_crawler.py`（使用 Playwright 抓取 Highcharts JSON）

### 1.4 CnOpenData 农产品批发价格数据集（学术）

- 覆盖：2011 年 1 月 ~ 2025 年 9 月，全国 31 省，45 种主要农产品
- 字段：省份、市场名称、分类、日期、价格(元/公斤)
- 用途：**冷启动历史回填**
- 实现：`crawlers/price/cnopendata_loader.py`

#### 历史数据回填流程

```bash
# 1. 下载 CnOpenData 西红柿数据集（学术机构申请获取）
mkdir -p data/raw/cnopendata
cp ~/Downloads/tomato_2011_2025.csv data/raw/cnopendata/

# 2. 干跑校验数据
cd crawlers
export SYNC_DATABASE_URL="postgresql+psycopg://veg:vegpass@localhost:5432/vegdb"
python -m price.cnopendata_loader \
    --csv ../data/raw/cnopendata/tomato_2011_2025.csv \
    --product tomato \
    --start 2022-01-01 \
    --dry-run

# 3. 入库
python -m price.cnopendata_loader \
    --csv ../data/raw/cnopendata/tomato_2011_2025.csv \
    --product tomato \
    --start 2022-01-01
```

> 在没有 CnOpenData 访问权限时，可先用 `python -m app.seed.seed_all` 灌入合成
> 历史数据，整个产品端到端可用，便于演示与开发。

### 1.5 地方批发市场数据（补充）

- 南京市农业农村局 <https://nyncj.agri114.cn:8081/>
- 大连价格监测 <https://jgjc.pc.dl.gov.cn:8090/>
- 各国家级市场官网（新发地、寿光地利等）

## 2. 天气数据

### 2.1 海天气象（推荐）

- URL：<https://htqx.cn/>
- 覆盖：2000 ~ 2025，全国逐小时
- 接入：HTTP API + Python SDK，付费档支持自动更新脚本
- 实现：`crawlers/weather/htqx_client.py`
- 配置：`HTQX_API_KEY` 环境变量

### 2.2 备用免费接口

- 极速数据 <https://m.jisuapi.com/api/weather2/>：100 次/月免费
- 聚合数据 <https://www.juhe.cn/docs/api/id/277>：付费 60QPS
- 全国天气日期级 <https://api.aa1.cn/doc/api-tianqi-3.html>：完全免费但稳定性一般

## 3. 政策数据

### 3.1 农业农村部政策栏目

- URL：<http://www.moa.gov.cn/govpublic/>
- 频率：每周扫描，新发布即入库
- 实现：`crawlers/policy/moa_policy.py`

### 3.2 国务院政策文件库

- URL：<https://www.gov.cn/zhengce/zhengceku/>
- 频率：每周
- 实现：`crawlers/policy/gov_cn_policy.py`

### 3.3 关键词过滤

`蔬菜`、`保供`、`菜篮子`、`价格`、`补贴`、`收储`、`储备`、`流通`、
`鲜活农产品`、`绿色通道`

## 4. 新闻数据

### 4.1 来源

- 百度新闻搜索：<https://news.baidu.com/ns?word=蔬菜价格>
- 新浪财经：<https://finance.sina.com.cn/>
- 第一财经：<https://www.yicai.com/>
- 央视财经 / 人民网 / 新华财经

实现：`crawlers/news/aggregator.py`

### 4.2 NLP 分析

- 语义嵌入：`bge-base-zh-v1.5`（HuggingFace）
- 情感分析：基于嵌入 + 关键词词典的 hybrid 方案
- 实体识别：HanLP

实现：`ml/nlp/sentiment.py`

## 5. 种植面积 / 产量

### 5.1 国家统计局年鉴

- URL：<http://www.stats.gov.cn/sj/ndsj/>
- 频率：年度

### 5.2 卫星遥感

- **CACD（中国作物分类数据集）** v1：30 米分辨率，1990-2023 年，已上 Google Earth Engine
- **CropLayer**：2 米分辨率，2020 年单年，Mapbox + Google 卫星影像
- **Sentinel-2**：10-60 米分辨率，重访周期 5 天
- 接入方式：Google Earth Engine Python API（`ee` 包）
- 实现：`crawlers/cropland/gee_estimator.py`（Phase 4）

## 6. 宏观经济数据

- CPI / PPI：国家统计局月度数据
- 油价：发改委成品油调价历史
- 物流指数：中国物流与采购联合会

## 7. 数据合规清单

| 数据源 | 类型 | 合规要点 |
|---|---|---|
| 农业农村部 | 政府公开 | 标注来源 |
| 食价搜 | 商业平台 | 遵守 robots.txt，控制 QPS |
| 中商情报网 | 商业平台 | 仅个人研究使用，付费版用于商用 |
| CnOpenData | 学术数据集 | 仅学术使用需要授权；商用需付费 |
| 海天气象 | 商业 API | 按合同使用 |
| Google Earth Engine | 公开 | 遵守 GEE 服务条款 |
| 新闻 | 公开 | 仅采集摘要 + 链接，全文不二次发布 |
