.PHONY: help up down logs ps seed backend frontend dev crawl-price crawl-weather train clean

help:
	@echo "蔬菜价格预测 SaaS - 常用命令"
	@echo ""
	@echo "  make up            启动 docker 基础设施 (postgres+timescale+redis)"
	@echo "  make down          停止 docker 基础设施"
	@echo "  make logs          查看 docker 日志"
	@echo "  make ps            查看 docker 容器状态"
	@echo "  make seed          灌入示例数据"
	@echo "  make backend       启动 FastAPI 后端 (端口 8000)"
	@echo "  make frontend      启动 Next.js 前端 (端口 3000)"
	@echo "  make dev           同时启动后端和前端 (需要 tmux/concurrently)"
	@echo "  make crawl-price   跑西红柿价格爬虫"
	@echo "  make crawl-weather 跑天气数据采集"
	@echo "  make train         训练 Prophet 预测模型"
	@echo "  make clean         清理 __pycache__ / .next 等临时产物"

up:
	cd infra && docker compose up -d postgres redis

down:
	cd infra && docker compose down

logs:
	cd infra && docker compose logs -f

ps:
	cd infra && docker compose ps

seed:
	cd backend && python -m app.seed.seed_all

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "请在两个终端分别执行 make backend 和 make frontend"

crawl-price:
	cd crawlers && python -m price.moa_crawler --product tomato --days 30

crawl-weather:
	cd crawlers && python -m weather.htqx_client --region shouguang --days 365

train:
	cd ml && python -m prophet.train --product tomato --market shouguang

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
	rm -rf frontend/.next frontend/out
	rm -rf backend/.coverage backend/htmlcov
