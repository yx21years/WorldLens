"""
Database repository helpers for Article, Source models.

Uses asynchronous SQLAlchemy session for non-blocking database access.
Dependencies: sqlalchemy[asyncio] (already in requirements.txt)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app_logging.setup import get_logger
from database.models import Article, Source, Analysis

logger = get_logger("repo")


async def get_session(session: AsyncSession | None) -> AsyncSession:
    """Return the provided session or create a new one."""
    if session is None:
        from database.connection import get_async_session
        async for new_session in get_async_session():
            return new_session
    return session


async def get_article_by_url(url: str, session: AsyncSession) -> Optional[Article]:
    """Lookup an article by its URL in the database (async)."""
    stmt = select(Article).where(sa.func.lower(Article.url) == url.lower())
    result = await session.execute(stmt)
    return result.scalars().first()


async def insert_source(session: AsyncSession, source_data: Dict[str, Any]) -> Source:
    """Insert or fetch a Source record. Returns the Source ORM object."""
    stmt = select(Source).where(Source.url == source_data["url"])
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    new_source = Source(
        name=source_data.get("name", "Unknown Source"),
        type=source_data.get("type", "rss"),
        url=source_data["url"],
        country=source_data.get("country", "US"),
        active=source_data.get("active", True),
    )
    session.add(new_source)
    await session.commit()
    await session.refresh(new_source)
    return new_source


async def batch_insert_articles(
    articles: List[Dict[str, Any]],
    session: AsyncSession,
) -> List[Article]:
    """Batch-insert new Article records into the database."""
    valid_columns = {column.name for column in Article.__table__.columns}

    inserted = []
    for art in articles:
        if "raw_content" not in art or not art["raw_content"]:
            art["raw_content"] = art.get("summary") or art.get("description") or ""

        filtered_art = {k: v for k, v in art.items() if k in valid_columns}

        try:
            db_art = Article(**filtered_art)
            session.add(db_art)
            await session.flush()
            inserted.append(db_art)
        except IntegrityError:
            await session.rollback()
            logger.warning(f"Skip duplicate article: {filtered_art.get('url')}")
            continue

    return inserted


async def batch_insert_analyses(
    analysis_list: list[dict],
    session: AsyncSession,
) -> list[Analysis]:
    """Batch-insert Analysis records."""
    valid_columns = {column.name for column in Analysis.__table__.columns}
    inserted = []
    for data in analysis_list:
        try:
            filtered_data = {k: v for k, v in data.items() if k in valid_columns}
            analysis = Analysis(**filtered_data)
            session.add(analysis)
            await session.flush()
            inserted.append(analysis)
        except Exception as e:
            logger.warning(f"Failed to insert analysis: {e}")
            continue
    return inserted


async def count_existing_urls(session: AsyncSession, urls: set[str]) -> set[str]:
    if not urls:
        return set()
    lower_urls = {u.lower() for u in urls}
    stmt = select(Article.url).where(
        sa.func.lower(Article.url).in_(lower_urls)
    )
    result = await session.execute(stmt)
    existing = {row[0] for row in result.all()}
    return existing


async def list_all_article_urls(session: AsyncSession) -> set[str]:
    stmt = select(Article.url)
    result = await session.execute(stmt)
    return {row[0].lower() for row in result.all()}


async def get_article_by_id(article_id: int, session: AsyncSession) -> Optional[Article]:
    """Lookup an article by its ID with preloaded relationships."""
    stmt = select(Article).where(Article.id == article_id).options(
        selectinload(Article.source),
        selectinload(Article.analysis)
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()


async def update_article_status(
    article_id: int,
    status: str,
    session: AsyncSession,
) -> bool:
    """Update the status of an article."""
    stmt = update(Article).where(Article.id == article_id).values(status=status)
    await session.execute(stmt)
    return True


async def create_analysis_record(
    article_id: int,
    data: Dict[str, Any],
    session: AsyncSession,
) -> Analysis:
    """Create or update an Analysis record."""
    stmt = select(Analysis).where(Analysis.article_id == article_id)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    valid_columns = {column.name for column in Analysis.__table__.columns}
    filtered_data = {k: v for k, v in data.items() if k in valid_columns}
    filtered_data['article_id'] = article_id

    if existing:
        for key, value in filtered_data.items():
            if key not in ('article_id', 'created_at'):
                setattr(existing, key, value)
        await session.flush()
        return existing
    else:
        analysis = Analysis(**filtered_data)
        session.add(analysis)
        await session.flush()
        return analysis