from fastapi import APIRouter, HTTPException
from datetime import date
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.connection import get_async_engine
from database.models import Briefing
from services.briefing_generator import generate_today_briefing as generate_briefing_service
from app_logging.setup import get_logger

logger = get_logger("routes.briefings")
router = APIRouter(prefix="/api/v1/briefings", tags=["briefings"])


@router.get("/")
async def list_briefings():
    """列出历史简报（返回最近的7天）"""
    today_str = date.today().isoformat()
    async_engine = get_async_engine()
    async_session_maker = async_sessionmaker(async_engine, autocommit=False, autoflush=False)

    async with async_session_maker() as session:
        stmt = select(Briefing).order_by(Briefing.date.desc()).limit(7)
        result = await session.execute(stmt)
        briefings = result.scalars().all()

        return {
            "data": [
                {
                    "date": b.date,
                    "article_count": len(json.loads(b.article_ids)) if b.article_ids else 0,
                    "preview": b.content[:200] + "..." if len(b.content) > 200 else b.content,
                }
                for b in briefings
            ],
            "meta": {"total": len(briefings)},
            "errors": [],
        }


@router.get("/today")
async def get_today_briefing():
    """获取今日简报（如果不存在则返回提示）"""
    today_str = date.today().isoformat()
    async_engine = get_async_engine()
    async_session_maker = async_sessionmaker(async_engine, autocommit=False, autoflush=False)

    async with async_session_maker() as session:
        stmt = select(Briefing).where(Briefing.date == today_str)
        result = await session.execute(stmt)
        brief = result.scalar_one_or_none()

        if not brief:
            return {
                "status": "not_found",
                "message": "今日简报尚未生成，请调用 POST /api/v1/briefings/generate",
                "date": today_str,
                "data": None,
                "errors": [],
            }

        return {
            "status": "success",
            "date": brief.date,
            "content": brief.content,
            "article_ids": json.loads(brief.article_ids) if brief.article_ids else [],
            "data": {
                "content": brief.content,
                "article_count": len(json.loads(brief.article_ids)) if brief.article_ids else 0,
            },
            "errors": [],
        }


@router.post("/generate")
async def generate_briefing():
    """手动生成今日简报"""
    logger.info("手动触发简报生成...")
    result = await generate_briefing_service()

    if not result.get("success"):
        logger.error(f"简报生成失败: {result.get('error')}")
        raise HTTPException(status_code=500, detail=result.get("error", "简报生成失败"))

    return {
        "status": "success",
        "message": "简报生成成功",
        "date": result.get("date"),
        "article_count": result.get("article_count", 0),
        "data": {
            "briefing": result.get("briefing"),
        },
        "errors": [],
    }