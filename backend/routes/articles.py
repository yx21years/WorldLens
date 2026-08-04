"""Articles routes - Phase 2/3 implementation.

Handles article CRUD, listing, collection, and AI analysis endpoints.
"""
import json
import traceback
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from database.connection import async_session_maker
from database.models import Article, Analysis
from errors.base import CollectionError
from services.collection import collect_from_sources
from services.ai_service import analyze_article, analyze_all_articles
from app_logging.setup import get_logger

logger = get_logger("routes.articles")

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.get("/")
async def list_articles(
    status: str | None = None,
    category: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List articles with optional status and category filters."""
    try:
        async with async_session_maker() as session:
            stmt = select(Article).options(selectinload(Article.source))

            if status:
                stmt = stmt.where(Article.status == status)

            if category:
                stmt = stmt.join(Analysis, Article.id == Analysis.article_id).where(
                    Analysis.category == category
                )

            stmt = stmt.order_by(desc(Article.created_at)).offset(offset).limit(limit)
            result = await session.execute(stmt)
            articles = result.unique().scalars().all()

            data = []
            for art in articles:
                data.append({
                    "id": art.id,
                    "title": art.title,
                    "url": art.url,
                    "image_url": art.image_url,
                    "published_at": art.published_at,
                    "status": art.status,
                    "source_id": art.source_id,
                    "source_name": art.source.name if art.source else None,  # 预加载后安全访问
                })

            return {
                "data": data,
                "meta": {"total": len(data), "page": offset // limit + 1, "per_page": limit},
                "errors": []
            }
    except Exception as e:
        logger.error(f"List articles error: {e}")
        return {"data": [], "meta": {"total": 0}, "errors": [str(e)]}


@router.get("/{article_id}")
async def get_article(article_id: int):
    """Get single article by ID."""
    try:
        async with async_session_maker() as session:
            stmt = select(Article).where(Article.id == article_id).options(
                selectinload(Article.source)
            )
            result = await session.execute(stmt)
            article = result.unique().scalar_one_or_none()

            if not article:
                raise HTTPException(status_code=404, detail="Article not found")

            return {
                "data": {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "image_url": article.image_url,
                    "raw_content": article.raw_content,
                    "published_at": article.published_at,
                    "status": article.status,
                    "source_id": article.source_id,
                    "source_name": article.source.name if article.source else None,
                },
                "errors": []
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get article error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect")
async def trigger_collection():
    """Manually trigger news collection from RSS feeds."""
    try:
        result = await collect_from_sources()
        if not result["success"]:
            raise CollectionError(f"Collection failed: {result['errors'][0]}")
        return {
            "data": {
                "status": "completed",
                "new_articles": result["count_new"],
                "skipped_duplicates": result["count_skipped"],
                "failed_fetches": result["count_failed"],
                "timestamp": result["timestamp"],
                "errors": result["errors"]
            },
            "errors": []
        }
    except CollectionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Collection endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Collection service encountered an error")


@router.post("/{article_id}/analyze")
async def analyze_article_route(article_id: int):
    """Manually trigger AI analysis for a specific article."""
    try:
        result = await analyze_article(article_id)
        return {
            "status": "success",
            "article_id": article_id,
            "message": "Article analyzed successfully",
            "analysis": result
        }
    except Exception as e:
        logger.error(f"Analyze endpoint error for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze_all")
async def analyze_all_articles_route():
    """Analyze all raw articles (use with caution - may consume many LLM tokens)."""
    try:
        result = await analyze_all_articles()
        return {
            "status": "success",
            "analyzed_count": len(result),
            "message": f"{len(result)} articles analyzed"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.exception("All-analyze endpoint error")
        # ✅ 返回具体错误信息
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )

@router.get("/{article_id}/enriched")
async def get_enriched_article(article_id: int):
    """获取文章 + AI 智能卡片（纯异步，不依赖同步 Session）。"""
    async with async_session_maker() as session:
        stmt = select(Article).where(Article.id == article_id).options(
            selectinload(Article.source)
        )
        result = await session.execute(stmt)
        article = result.unique().scalar_one_or_none()

        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")

        analysis_stmt = select(Analysis).where(Analysis.article_id == article_id)
        analysis_result = await session.execute(analysis_stmt)
        analysis_obj = analysis_result.scalar_one_or_none()

        if analysis_obj:
            try:
                key_entities = json.loads(analysis_obj.key_entities) if analysis_obj.key_entities else []
            except json.JSONDecodeError:
                key_entities = [analysis_obj.key_entities] if analysis_obj.key_entities else []

            analysis_data = {
                "summary": analysis_obj.summary or "",
                "importance": analysis_obj.importance,
                "category": analysis_obj.category,
                "sentiment": analysis_obj.sentiment or "neutral",
                "why_it_matters": analysis_obj.why_it_matters or "",
                "background_context": analysis_obj.background_context or "",
                "potential_impact": analysis_obj.potential_impact or "",
                "key_entities": key_entities,
                "trend_level": analysis_obj.trend_level or "MEDIUM"
            }
        else:
            analysis_data = None

        return {
            "id": article.id,
            "title": article.title,
            "raw_content": article.raw_content or "",
            "status": article.status,
            "analysis": analysis_data
        }

@router.post("/analyze_direct_async")
async def analyze_all_direct_async_route():
    """绕过 ORM，用原生 aiosqlite 异步分析"""
    from services.analyze_direct_async import analyze_all_direct_async
    result = await analyze_all_direct_async()
    return {
        "status": "success",
        "analyzed_count": len(result),
        "article_ids": result
    }