# 蔬菜价格预测 SaaS（Vegetable Price Intelligence）

面向农户、采购商和政策研究者的蔬菜价格预测平台。第一期聚焦**西红柿**，整合价格、天气、政策、新闻、种植面积五大维度数据，提供可视化仪表盘和价格预测能力。

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

## License

MIT
