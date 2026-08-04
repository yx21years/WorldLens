"""Collection Service - Phase 2 implementation.

Coordinates RSS fetching, deduplication against the database, and batch storage.
Dependencies: feedparser (pip install feedparser)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_maker
from database.repo import (
    batch_insert_articles,
    list_all_article_urls,
    insert_source,
)
from services.rss_collector import (
    fetch_all_rss_feeds,
    clean_article,
    normalize_artifacts,
)
from errors.base import FetchTimeoutError
from app_logging.setup import get_logger

logger = get_logger("collection")


async def collect_from_sources(
    source_urls: Optional[List[str]] = None,
    session: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """Main entry point: fetch articles from configured sources, deduplicate, store."""
    if session is None:
       async with async_session_maker() as session:
            return await _collect_internal(source_urls, session)
    else:
        return await _collect_internal(source_urls, session)


async def _collect_internal(
    source_urls: Optional[List[str]],
    session: AsyncSession,
) -> Dict[str, Any]:
    """Internal worker that holds the DB session across all steps."""
    cleaned = []
    try:
        if source_urls is None:
            source_urls = [
                "http://feeds.bbci.co.uk/news/world/rss.xml",
                "https://feeds.reuters.com/reuters/worldNews",
                "https://www.aljazeera.com/xml/rss/all.xml",
            ]

        logger.info(f"Starting collection from {len(source_urls)} RSS feed(s)")

        # 1. 先创建/获取所有来源，建立 URL -> source_id 映射
        source_id_map: Dict[str, int] = {}
        for url in source_urls:
            source = await insert_source(session, {"url": url})
            source_id_map[url] = source.id
        default_source_id = next(iter(source_id_map.values()))

        # 2. 抓取所有 RSS 文章
        raw_articles = await fetch_all_rss_feeds(source_urls)
        logger.info(f"Total articles collected from all RSS feeds: {len(raw_articles)}")

        if not raw_articles:
            return {
                "success": True,
                "count_new": 0,
                "count_skipped": 0,
                "count_failed": 0,
                "errors": [],
                "timestamp": datetime.now().isoformat(),
            }

        # 3. 清洗文章 + 同批次内部 URL 去重（第一层防护）
        cleaned = []
        seen_urls = set()
        for art in raw_articles:
            cleaned_art = clean_article(art)
            if cleaned_art is None:
                continue
            
            url = cleaned_art.get("url") or cleaned_art.get("link", "")
            url_lower = url.lower()
            if url_lower in seen_urls:
                continue
            seen_urls.add(url_lower)
            cleaned.append(cleaned_art)

        logger.info(f"Cleaned {len(cleaned)} articles (after internal dedup)")

        # 4. 数据库去重：统一小写比对（第二层防护）
        existing_urls = await list_all_article_urls(session)
        logger.info(f"Deduplication check: {len(cleaned)} candidates, {len(existing_urls)} existing in DB")

        to_add = []
        skipped = []
        for art in cleaned:
            url = art.get("url") or art.get("link", "")
            if url.lower() in existing_urls:
                skipped.append(art)
            else:
                to_add.append(art)

        logger.info(f"After deduplication: {len(to_add)} new, {len(skipped)} skipped")

        if not to_add:
            return {
                "success": True,
                "count_new": 0,
                "count_skipped": len(skipped),
                "count_failed": 0,
                "errors": [],
                "timestamp": datetime.now().isoformat(),
            }

        # 5. 字段归一化
        normalized = normalize_artifacts(to_add)

        # 6. 强制绑定 source_id，放在归一化之后避免被覆盖
        for art in normalized:
            feed_url = art.get("feed_url") or art.get("source_url") or art.get("feed")
            if feed_url and feed_url in source_id_map:
                art["source_id"] = source_id_map[feed_url]
            else:
                art["source_id"] = default_source_id

            # 兜底：确保 url 字段存在
            if "url" not in art and "link" in art:
                art["url"] = art["link"]

        # 7. 批量入库（repo 层已加第三层异常兜底）
        inserted = await batch_insert_articles(normalized, session=session)
        new_ids = [article.id for article in inserted]  # ✅ 提取新增 ID
        logger.info(f"Inserted {len(inserted)} articles into database")

        await session.commit()

        # ✅ 自动分析新采集的文章（只分析新插入的，不扫描全表）
        from config.settings import get_settings
        settings = get_settings()
        if settings.AUTO_ANALYZE and new_ids:
            logger.info(f"触发自动分析，共 {len(new_ids)} 篇新文章...")
            try:
                from services.ai_service import analyze_articles_by_ids
                analyzed = await analyze_articles_by_ids(new_ids)
                logger.info(f"自动分析完成，成功分析 {len(analyzed)} 篇")
            except Exception as e:
                logger.error(f"自动分析失败: {e}")
        elif not settings.AUTO_ANALYZE:
            logger.info("自动分析已禁用（AUTO_ANALYZE=false）")
        else:
            logger.info("没有新文章需要分析")

        return {
            "success": True,
            "count_new": len(inserted),
            "count_skipped": len(skipped),
            "count_failed": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

    except FetchTimeoutError as e:
        logger.error(f"Collection timeout: {e}")
        return {
            "success": False,
            "count_new": 0,
            "count_skipped": 0,
            "count_failed": len(cleaned),
            "errors": [str(e)],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Collection failed: {type(e).__name__} - {e}", exc_info=True)
        if session:
            await session.rollback()
        return {
            "success": False,
            "count_new": 0,
            "count_skipped": 0,
            "count_failed": len(cleaned),
            "errors": [str(e)],
            "timestamp": datetime.now().isoformat(),
        }