"""通用 HTTP 客户端，带重试与可配置 UA"""

from __future__ import annotations

import os
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

DEFAULT_UA = os.getenv(
    "CRAWL_USER_AGENT",
    "Mozilla/5.0 (compatible; VegBot/0.1; +https://example.com/bot)",
)
TIMEOUT = float(os.getenv("CRAWL_REQUEST_TIMEOUT", "20"))
RETRIES = int(os.getenv("CRAWL_RETRY_TIMES", "3"))


def _client(headers: dict | None = None) -> httpx.Client:
    base_headers = {
        "User-Agent": DEFAULT_UA,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if headers:
        base_headers.update(headers)
    return httpx.Client(headers=base_headers, timeout=TIMEOUT, follow_redirects=True)


@retry(
    reraise=True,
    stop=stop_after_attempt(RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
)
def get_json(url: str, params: dict | None = None, headers: dict | None = None) -> Any:
    with _client(headers) as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        return r.json()


@retry(
    reraise=True,
    stop=stop_after_attempt(RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
)
def get_text(url: str, params: dict | None = None, headers: dict | None = None) -> str:
    with _client(headers) as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        return r.text


@retry(
    reraise=True,
    stop=stop_after_attempt(RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
)
def post_json(url: str, json: dict, headers: dict | None = None) -> Any:
    with _client(headers) as c:
        r = c.post(url, json=json)
        r.raise_for_status()
        return r.json()


def safe_get_json(url: str, **kwargs) -> Any | None:
    """对失败做兜底，返回 None"""
    try:
        return get_json(url, **kwargs)
    except Exception as e:
        logger.warning(f"GET {url} failed after retries: {e}")
        return None
