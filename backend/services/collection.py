"""Collection Service - Phase 2 implementation.

Coordinates RSS fetching, deduplication against the database, and batch storage.
Dependencies: feedparser (pip install feedparser)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_maker
from database.repo import (
    batch_insert_articles,
    list_all_article_urls,
    insert_source,
)
from database.models import Source
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
        # ============================================================
        # 1. 获取所有需要采集的 RSS 源
        # ============================================================
        if source_urls is None:
            # ✅ 从数据库读取所有活跃的 RSS 源
            stmt = select(Source).where(
                Source.active == True,
                Source.type == "rss"
            )
            result = await session.execute(stmt)
            sources = result.scalars().all()
            
            if not sources:
                logger.warning("没有找到活跃的 RSS 源，请先导入 OPML 文件")
                return {
                    "success": False,
                    "count_new": 0,
                    "count_skipped": 0,
                    "count_failed": 0,
                    "errors": ["没有活跃的 RSS 源"],
                    "timestamp": datetime.now().isoformat(),
                }
            
            # 构建 URL -> Source 对象的映射
            source_map: Dict[str, Source] = {s.url: s for s in sources}
            source_urls = [s.url for s in sources]
            source_id_map: Dict[str, int] = {s.url: s.id for s in sources}
            default_source_id = source_id_map.get(source_urls[0]) if source_urls else None
            
            logger.info(f"从数据库加载了 {len(source_urls)} 个 RSS 源")
            logger.info(f"分类分布: {_get_category_stats(sources)}")
        else:
            # 用户手动传入 URL 列表时，逐个查询/创建来源
            source_id_map = {}
            source_map = {}
            for url in source_urls:
                stmt = select(Source).where(Source.url == url)
                result = await session.execute(stmt)
                source = result.scalar_one_or_none()
                if source:
                    source_map[url] = source
                    source_id_map[url] = source.id
                else:
                    # 如果源不存在，自动创建（但不会设置 category）
                    new_source = await insert_source(session, {"url": url})
                    source_map[url] = new_source
                    source_id_map[url] = new_source.id
            default_source_id = next(iter(source_id_map.values())) if source_id_map else None

        if not source_urls:
            logger.warning("没有可用的 RSS 源")
            return {
                "success": False,
                "count_new": 0,
                "count_skipped": 0,
                "count_failed": 0,
                "errors": ["没有可用的 RSS 源"],
                "timestamp": datetime.now().isoformat(),
            }

        logger.info(f"Starting collection from {len(source_urls)} RSS feed(s)")

        # ============================================================
        # 2. 抓取所有 RSS 文章
        # ============================================================
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

        # ============================================================
        # 3. 清洗文章 + 同批次内部 URL 去重
        # ============================================================
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

        # ============================================================
        # 4. 数据库去重
        # ============================================================
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

        # ============================================================
        # 5. 字段归一化
        # ============================================================
        normalized = normalize_artifacts(to_add)

        # ============================================================
        # 6. 绑定 source_id（关键修复：优先使用 _feed_url）
        # ============================================================
        for art in normalized:
            # ✅ 优先从 _feed_url 字段获取源 URL
            feed_url = art.get("_feed_url")
            if feed_url and feed_url in source_id_map:
                art["source_id"] = source_id_map[feed_url]
            else:
                # 回退到原有的逻辑，兼容旧数据
                feed_url = art.get("feed_url") or art.get("source_url") or art.get("feed")
                if feed_url and feed_url in source_id_map:
                    art["source_id"] = source_id_map[feed_url]
                else:
                    # 如果找不到对应的 source_id，用默认值
                    art["source_id"] = default_source_id

            # 兜底：确保 url 字段存在
            if "url" not in art and "link" in art:
                art["url"] = art["link"]

        # ============================================================
        # 7. 批量入库
        # ============================================================
        inserted = await batch_insert_articles(normalized, session=session)
        new_ids = [article.id for article in inserted]
        logger.info(f"Inserted {len(inserted)} articles into database")

        await session.commit()

        # ============================================================
        # 8. 按分类统计新增文章
        # ============================================================
        category_counts = {}
        if inserted:
            source_ids = list(set([a.source_id for a in inserted]))
            stmt = select(Source).where(Source.id.in_(source_ids))
            result = await session.execute(stmt)
            sources_info = {s.id: s.category for s in result.scalars().all()}
            
            for article in inserted:
                cat = sources_info.get(article.source_id, "未分类")
                category_counts[cat] = category_counts.get(cat, 0) + 1
            logger.info(f"新增文章分类分布: {category_counts}")

        # ============================================================
        # 9. 自动分析
        # ============================================================
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
            "category_stats": category_counts,
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


def _get_category_stats(sources: List[Source]) -> Dict[str, int]:
    """统计各分类的源数量"""
    stats = {}
    for s in sources:
        cat = s.category or "未分类"
        stats[cat] = stats.get(cat, 0) + 1
    return stats