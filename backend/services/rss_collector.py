"""
RSS Feed Collector Service - Phase 2.

Required dependency: feedparser (install via: pip install feedparser)

This module provides functions to fetch articles from RSS feeds, clean them,
deduplicate against existing database entries, and batch-insert new records.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import re
import urllib.request

import feedparser

from errors.base import FetchTimeoutError, FilterRejectionError
from app_logging.setup import get_logger

logger = get_logger("rss_collector")

# ============================================================
# 全局代理配置（所有请求统一走代理）
# ============================================================
PROXY = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}


def _parse_with_proxy(url: str):
    """使用全局代理解析 RSS 源"""
    proxy_handler = urllib.request.ProxyHandler(PROXY)
    opener = urllib.request.build_opener(proxy_handler)
    # 可选：添加 User-Agent 头，防止某些源拦截
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    return feedparser.parse(url)


async def fetch_rss_feed(source_url: str, timeout: int = 15, source_url_param: str = None) -> List[Dict[str, Any]]:
    """Fetch an RSS feed and parse it into article dictionaries.

    Args:
        source_url: The RSS feed URL to fetch.
        timeout: Maximum seconds to wait for the HTTP request (per feed).

    Returns:
        List of article dicts with fields matching Article schema:
        {title, url, published_at, content, summary, author, image_url, _feed_url}

    Raises:
        FetchTimeoutError: If the request exceeds the timeout threshold.
        Exception: For other parsing/network failures (logged but not re-raised).
    """
    start_time = time.time()

    try:
        loop = asyncio.get_event_loop()
        # ✅ 全部走代理
        feed = await loop.run_in_executor(
            None,
            lambda: _parse_with_proxy(source_url),
        )

        elapsed = time.time() - start_time
        if elapsed > timeout * 0.8:
            logger.warning(f"Slow RSS fetch for {source_url}: {elapsed:.1f}s (timeout={timeout})")

        if getattr(feed, "bozo", True) and not feed.entries:
            logger.warning(f"Parse error or empty feed at {source_url}")
            return []

        articles = []
        for entry in feed.entries:
            article = _extract_entry_data(entry, source_url_param or source_url)
            if article:
                articles.append(article)

        logger.debug(f"Fetched {len(articles)} articles from {source_url} ({elapsed:.1f}s)")
        return articles

    except asyncio.TimeoutError as e:
        raise FetchTimeoutError(source_url) from e
    except Exception as e:
        logger.error(f"Failed to fetch RSS feed {source_url}: {type(e).__name__} - {e}", exc_info=True)
        return []


def _extract_entry_data(entry: Any, source_url: str) -> Dict[str, Any] | None:
    """Extract structured article data from a feedparser entry dict."""
    title = entry.get("title", "").strip()
    if len(title) < 2:
        return None

    link = entry.get("link", "").split("?")[0]
    if not link:
        return None

    published = _parse_published(entry.get("published"))
    summary = entry.get("summary", "") or entry.get("description", "")[:500]
    content = ""
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")[:5000]
    elif hasattr(entry, "description"):
        content = entry.description[:5000] if entry.description else ""

    author = entry.get("author", "").strip()[:200]

    # 提取图片 URL（自动升级为高清）
    image_url = _extract_image_url(entry)
    if image_url:
        image_url = _upscale_image_url(image_url)

    return {
        "title": title[:500],
        "url": link[:2000],
        "published_at": published,
        "summary": summary[:500],
        "content": content,
        "author": author,
        "image_url": image_url,
        "raw_entry": entry,
        "_feed_url": source_url,  # ✅ 源头标记
    }


def _extract_image_url(entry: Any) -> Optional[str]:
    """从 feedparser 条目中提取第一张图片 URL。

    优先级：
    1. media_thumbnail
    2. enclosures (image/*)
    3. 从 description / content 中提取 <img src="...">
    """
    # 1. media_thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        thumb = entry.media_thumbnail[0]
        if isinstance(thumb, dict):
            return thumb.get("url")
        elif isinstance(thumb, str):
            return thumb

    # 2. enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href")

    # 3. 从 description / content 中提取 <img src="...">
    desc = entry.get("summary", "") or entry.get("description", "")
    if desc:
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc, re.IGNORECASE)
        if match:
            return match.group(1)

    # 4. 从 content 中提取（如果有）
    if hasattr(entry, "content") and entry.content:
        content_text = entry.content[0].get("value", "")
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def _upscale_image_url(url: str) -> str:
    """将图片 URL 中的尺寸参数替换为高清版本（1024px）。"""
    # BBC 图片：将 /240/ 或 /320/ 等替换为 /1024/
    if "ichef.bbci.co.uk" in url:
        url = re.sub(r'/(\d{3,4})/cpsprodpb', '/1024/cpsprodpb', url)
    # 可继续添加其他来源的规则
    return url


def _parse_published(value: Any) -> datetime | None:
    """Convert various date formats to Python datetime object."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            parsed = feedparser.parse_rfc822(value)
            return parsed if parsed else None
        except (ValueError, AttributeError):
            pass
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    logger.debug(f"Unrecognized publish date: type={type(value).__name__} value={value}")
    return None


async def fetch_all_rss_feeds(feeds: List[str], batch_timeout: int = 60) -> List[dict]:
    """Fetch multiple RSS feeds concurrently with optional total timeout.

    Args:
        feeds: List of RSS feed URLs.
        batch_timeout: Maximum seconds allowed for all requests combined.

    Returns:
        Combined list of all successfully fetched articles.
    """
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_semaphore(url):
        async with semaphore:
            return await fetch_rss_feed(url, timeout=batch_timeout // max(1, len(feeds)), source_url_param=url)

    tasks = [fetch_with_semaphore(url) for url in feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Feed {feeds[idx]} raised exception: {result}")
            continue
        articles.extend(result)

    logger.info(f"Total articles collected from all RSS feeds: {len(articles)}")
    return articles


def clean_article(raw: dict) -> dict | None:
    """Clean raw article data: strip HTML-like artifacts, filter insufficient content.

    Returns cleaned dict or None if the article fails quality checks.
    """
    title = raw.get("title", "").strip()
    if not title or len(title) < 3:
        return None

    content = raw.get("content", "") or raw.get("summary", "")
    if len(content.strip()) < 10:
        return None

    cleaned = raw.copy()
    cleaned["title"] = title[:500]
    cleaned["content"] = content[:5000] if len(content) > 5000 else content
    cleaned["summary"] = raw.get("summary", "")[:500]
    cleaned["author"] = raw.get("author", "")[:200]
    # 保留 image_url 和 _feed_url
    return cleaned


def deduplicate_existing(existing_urls: set[str], new_articles: List[dict]) -> tuple[List[dict], List[dict]]:
    """Split new articles into 'to_add' (new) and 'skipped' (duplicates).

    Args:
        existing_urls: Set of URLs already in the database.
        new_articles: List of candidate article dicts.

    Returns:
        (to_add_list, skipped_list)
    """
    to_add = []
    skipped = []
    for art in new_articles:
        url = art.get("url", "")
        if url and url in existing_urls:
            skipped.append(art)
        else:
            to_add.append(art)
    return to_add, skipped


def normalize_artifacts(articles: List[dict], source_id: int | None = None) -> List[Dict[str, Any]]:
    """Normalize article dicts to match Article ORM model schema for DB insertion.

    Adds source_id foreign key if provided, converts types where needed.
    ✅ 关键修复：保留 _feed_url 字段，用于后续 source_id 绑定
    """
    normalized = []
    now = datetime.now()
    for art in articles:
        rec = {
            "source_id": source_id,
            "url": str(art.get("url", ""))[:2000],
            "title": str(art.get("title", ""))[:500],
            "raw_content": json.dumps(art.get("raw_entry", {})) if art.get("raw_entry") else None,
            "published_at": art.get("published_at"),
            "country": "US",
            "status": "raw",
            "created_at": now,
            "summary": str(art.get("summary", ""))[:500],
            "content": str(art.get("content", ""))[:5000],
            "author": str(art.get("author", ""))[:200],
            "image_url": str(art.get("image_url", ""))[:2000] if art.get("image_url") else None,
            "_feed_url": art.get("_feed_url"),  # ✅ 关键：保留来源标记
        }
        normalized.append(rec)
    return normalized