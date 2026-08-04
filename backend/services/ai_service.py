import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from database.connection import get_async_engine
from database.repo import (
    create_analysis_record,
    update_article_status,
)
from database.models import Article, Analysis
from errors.base import CollectionError
from llm.provider_factory import get_provider
from prompts.manager import PromptManager
from app_logging.setup import get_logger

logger = get_logger(__name__)


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"无法解析 JSON，原始内容前 500 字符: {text[:500]}")
        raise ValueError(f"Invalid JSON: {text[:200]}") from e


async def _analyze_article(article: Article, session) -> dict:
    """内部函数：在已有会话中分析单篇文章"""
    # 检查已有分析
    analysis_stmt = select(Analysis).where(Analysis.article_id == article.id)
    analysis_result = await session.execute(analysis_stmt)
    existing = analysis_result.scalar_one_or_none()
    if existing:
        logger.info(f"Article {article.id} already has analysis, skipping")
        await update_article_status(article.id, "analyzed", session)
        await session.commit()
        return {
            "already_analyzed": True,
            "summary": existing.summary,
            "importance": existing.importance,
            "category": existing.category,
            "sentiment": existing.sentiment,
            "why_it_matters": existing.why_it_matters,
            "background_context": existing.background_context,
            "potential_impact": existing.potential_impact,
            "key_entities": json.loads(existing.key_entities) if existing.key_entities else [],
            "trend_level": existing.trend_level or "MEDIUM"
        }

    # 截断内容
    content = article.raw_content or ""
    if len(content) > 1500:
        content = content[:1497] + "..."

    prompt_manager = PromptManager()
    prompt = prompt_manager.get_prompt("analyze_article", version="2")
    system_prompt = prompt["system_prompt"]
    user_prompt = prompt["user_prompt_template"].format(title=article.title, content=content)

    provider = get_provider()
    params = {
        "temperature": prompt.get("params", {}).get("temperature", 0.3),
        "max_tokens": 1000,
    }

    response = await provider.complete(
        prompt=user_prompt,
        system=system_prompt,
        params=params,
    )
    raw_text = response.content if hasattr(response, 'content') else str(response)
    result = _extract_json(raw_text)

    # 验证必要字段
    required = ["summary", "importance", "category", "sentiment", "why_it_matters"]
    for field in required:
        if field not in result:
            raise CollectionError(f"Missing required field: {field}")

    analysis_data = {
        "article_id": article.id,
        "summary": str(result.get("summary", "")),
        "importance": int(result.get("importance", 5)),
        "category": str(result.get("category", "")),
        "sentiment": str(result.get("sentiment", "neutral")),
        "why_it_matters": str(result.get("why_it_matters", "")),
        "background_context": str(result.get("background_context", "")),
        "potential_impact": str(result.get("potential_impact", "")),
        "key_entities": json.dumps(result.get("key_entities", [])),
        "trend_level": result.get("trend_level", "MEDIUM"),
        "created_at": datetime.now(timezone.utc),
    }

    await create_analysis_record(article.id, analysis_data, session)
    await update_article_status(article.id, "analyzed", session)
    await session.commit()

    logger.info(f"Article {article.id} 分析完成")

    return {
        "summary": result.get("summary", ""),
        "importance": int(result.get("importance", 5)),
        "category": result.get("category", ""),
        "sentiment": result.get("sentiment", "neutral"),
        "why_it_matters": result.get("why_it_matters", ""),
        "background_context": result.get("background_context", ""),
        "potential_impact": result.get("potential_impact", ""),
        "key_entities": result.get("key_entities", []),
        "trend_level": result.get("trend_level", "MEDIUM")
    }


async def analyze_article(article_id: int) -> dict:
    """公开 API：分析单篇文章"""
    async_engine = get_async_engine()
    async_session_maker = async_sessionmaker(async_engine, autocommit=False, autoflush=False, expire_on_commit=False)

    async with async_session_maker() as session:
        stmt = select(Article).where(Article.id == article_id).options(
            selectinload(Article.source)
        )
        result = await session.execute(stmt)
        article = result.unique().scalar_one_or_none()
        if article is None:
            raise CollectionError(f"Article {article_id} not found")
        if article.status != "raw":
            raise CollectionError(f"Article {article_id} status is {article.status}, not raw")

        return await _analyze_article(article, session)


async def analyze_all_articles() -> List[int]:
    """分析所有 raw 文章"""
    analyzed_ids = []
    async_engine = get_async_engine()
    async_session_maker = async_sessionmaker(async_engine, autocommit=False, autoflush=False, expire_on_commit=False)

    async with async_session_maker() as session:
        stmt = select(Article).where(Article.status == "raw").options(
            selectinload(Article.source)
        )
        result = await session.execute(stmt)
        articles = result.unique().scalars().all()

        for article in articles:
            try:
                await _analyze_article(article, session)
                analyzed_ids.append(article.id)
            except CollectionError as e:
                logger.warning(f"Skipped article {article.id}: {e}")
                await session.rollback()
            except Exception as e:
                logger.error(f"Error analyzing article {article.id}: {e}")
                await update_article_status(article.id, "error", session)
                await session.commit()

    return analyzed_ids


async def analyze_articles_by_ids(article_ids: List[int]) -> List[int]:
    """增量分析指定 ID 的文章"""
    analyzed = []
    if not article_ids:
        return analyzed

    async_engine = get_async_engine()
    async_session_maker = async_sessionmaker(async_engine, autocommit=False, autoflush=False)

    async with async_session_maker() as session:
        stmt = select(Article).where(Article.id.in_(article_ids)).options(
            selectinload(Article.source)
        )
        result = await session.execute(stmt)
        articles = result.unique().scalars().all()

        for article in articles:
            try:
                await _analyze_article(article, session)
                analyzed.append(article.id)
            except Exception as e:
                logger.warning(f"跳过文章 {article.id}: {e}")
                await update_article_status(article.id, "error", session)
                await session.commit()

    return analyzed