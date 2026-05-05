# 爬虫工程

## 设计原则

1. **优先官方 / 公开数据源**，严格遵循 robots.txt 与 ToS
2. **多源交叉验证**：同一品类至少 2 个数据源，发现偏差时人工 review
3. **幂等写库**：以 (market_id, product_id, date) 为主键，可重复执行
4. **指数退避重试**：tenacity，避免触发反爬
5. **采集 = 提取 + 标准化 + 入库** 三段式

## 已实现的爬虫

| 模块 | 数据源 | 频率 | 状态 |
|---|---|---|---|
| `price.moa_crawler` | 农业农村部 zdscxx.moa.gov.cn | 每日 | scaffold |
| `price.food21_crawler` | 食价搜 21food.cn | 每日 | scaffold |
| `price.askci_crawler` | 中商情报网 s.askci.com | 每日 | scaffold |
| `price.cnopendata_loader` | CnOpenData 学术数据集 (CSV/Excel 离线导入) | 一次性 | scaffold |
| `weather.htqx_client` | 海天气象 htqx.cn | 每日 | scaffold |
| `policy.moa_policy` | 农业农村部 政策栏目 | 每周 | scaffold |
| `policy.gov_cn_policy` | 国务院政策文件库 | 每周 | scaffold |
| `news.aggregator` | 百度新闻 / 新浪 / 财经网 | 每小时 | scaffold |

## 运行

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium  # 部分爬虫用到

# 跑西红柿价格（需要 DATABASE_URL 环境变量指向数据库）
export SYNC_DATABASE_URL="postgresql+psycopg://veg:vegpass@localhost:5432/vegdb"
python -m price.moa_crawler --product tomato --days 7 --dry-run     # 仅打印
python -m price.moa_crawler --product tomato --days 7               # 入库

# 跑天气
python -m weather.htqx_client --region 370783 --days 30
```

## 调度

生产环境通过 backend 内的 Celery + Celery Beat 调度，本目录下的脚本都是
**单次执行的命令行入口**（typer），便于本地手测和 CI 跑数据回填。
