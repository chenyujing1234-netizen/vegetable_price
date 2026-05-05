"""中商情报网西红柿价格走势爬虫

数据源：https://s.askci.com/data/price/170120
该页面渲染需要 JavaScript（Highcharts），用 Playwright 抓取
图表的底层 JSON 数据，再写入数据库。
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime

import typer
from loguru import logger

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

app = typer.Typer(no_args_is_help=True, add_completion=False)


async def _fetch(url: str) -> list[dict]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error(
            "playwright not installed; run: pip install playwright && playwright install chromium"
        )
        return []

    captured: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; VegBot/0.1; +https://example.com/bot)"
        )
        page = await ctx.new_page()

        async def handle_response(resp):
            if "highchart" in resp.url.lower() or "/data/" in resp.url:
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    try:
                        data = await resp.json()
                        captured.append({"url": resp.url, "data": data})
                    except Exception:
                        pass

        page.on("response", handle_response)
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(3000)
        await browser.close()
    return captured


@app.command()
def run(
    url: str = typer.Option("https://s.askci.com/data/price/170120"),
    out: str = typer.Option("askci_tomato.json", help="输出 JSON 文件"),
):
    """抓取并保存原始 JSON，后续用专门的 ETL 解析入库

    第一阶段我们仅做 dump，避免在网站结构变化时反复修改入库逻辑。
    """
    captured = asyncio.run(_fetch(url))
    logger.info(f"captured {len(captured)} JSON responses")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fetched_at": datetime.utcnow().isoformat(),
                "source_url": url,
                "responses": captured,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info(f"saved to {out}")


if __name__ == "__main__":
    app()
