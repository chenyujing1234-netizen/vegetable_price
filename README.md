# 蔬菜价格预测 SaaS（Vegetable Price Intelligence）

> 🌱 **欢迎试用！在线体验地址：<http://124.221.115.174:3000/>**
>
> 无需注册，免费、开源、助农。打开即看西红柿全国价格走势、30 天预测、12 个主流批发市场行情、天气与政策影响因子分析。

面向农户、采购商和政策研究者的蔬菜价格预测平台。第一期聚焦**西红柿**，整合价格、天气、政策、新闻、种植面积五大维度数据，提供可视化仪表盘和价格预测能力。

| | |
|---|---|
| 🌐 在线试用 | <http://124.221.115.174:3000/> |
| 📖 我们的故事 | <http://124.221.115.174:3000/story> · [让一年的辛苦，不再烂在田里 →](http://124.221.115.174:3000/story) |
| 💻 源代码 | <https://github.com/chenyujing1234-netizen/vegetable_price> |
| 📦 镜像源 | <https://gitee.com/chenyujing/vegetable> |
| 🪪 协议 | MIT，可自由商用 |

## 核心能力

- 全国主流批发市场西红柿价格实时与历史走势
- 7 / 30 / 180 / 365 天价格预测（Prophet + LSTM 集成）
- 天气、政策、新闻、种植面积多因子影响分析
- 全国价格热力地图与区域价差分析
- 价格阈值告警订阅

## 仓库结构

```
vegetable/
├── backend/        FastAPI + SQLAlchemy 主服务
├── frontend/       Next.js 14 + TailwindCSS + shadcn/ui
├── crawlers/       Scrapy / Playwright 爬虫工程
├── ml/             Prophet / LSTM / NLP 模型
├── infra/          Docker Compose、TimescaleDB 初始化脚本
└── docs/           设计文档、数据源说明
```

## 快速开始

### 1. 启动基础设施（Postgres+TimescaleDB+Redis）

```bash
cd infra
docker compose up -d postgres redis
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head        # 建表
python -m app.seed.seed_all # 灌入示例数据
uvicorn app.main:app --reload --port 8000
```

打开 <http://localhost:8000/docs> 查看 OpenAPI 文档。

### 3. 启动前端

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

打开 <http://localhost:3000>。

### 4. 跑爬虫（可选）

```bash
cd crawlers
pip install -r requirements.txt
python -m price.moa_crawler --product tomato --days 30
```

### 5. 训练预测模型

```bash
cd ml
pip install -r requirements.txt
python -m prophet.train --product tomato --market shouguang
```

## 数据源

详见 [`docs/data-sources.md`](docs/data-sources.md)。

## 一键启动

```bash
make up    # 启动全部服务
make seed  # 灌入示例数据
make dev   # 同时启动后端和前端
```

## 扩展蔬菜品类

后端以 `Product` 表统一管理品类，前端各页面通过右上角**品类下拉框**切换（选择会保存在浏览器 localStorage）。

### 当前已内置品类

西红柿、黄瓜、辣椒、土豆、大白菜、茄子、小白菜、西兰花（共 8 种）。

### 新增一个品类（3 步）

**1. 在 `backend/app/seed/seed_data.py` 的 `PRODUCTS` 列表追加一行：**

```python
{"code": "garlic", "name": "大蒜", "category": "vegetable", "spec": "普通", "unit": "kg"},
```

并在 `PRODUCT_PRICE_FACTORS` 里设置相对西红柿的合成价格系数（仅 seed 演示数据用）：

```python
"garlic": 1.8,
```

**2. 增量入库（不会清空已有数据）：**

```bash
cd backend
python -m app.seed.seed_products   # 写入新品类 + 补齐 3 年历史价格
python -m app.seed.seed_catchup    # 可选：把所有市场/品类价格补到今天
```

**3. 刷新前端** —— 下拉框会自动出现新品类，无需改前端代码。

### 接入真实数据

- 价格：在 `crawlers/price/` 增加对应爬虫，或对接农业农村部 / 21food 等数据源
- 新闻：在 `crawlers/news/` 的关键词列表里加入新品类名称
- 种植面积：在 `SEED_CROPLAND` 或 GEE 模块里按 `region_code + product_id` 扩展

## License

MIT
