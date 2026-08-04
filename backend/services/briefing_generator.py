"""Briefing generation service — Phase 5.

Generates daily news briefings from analyzed articles.
"""

import json
from datetime import datetime, date, timezone
from typing import List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.connection import get_async_engine
from database.models import Article, Analysis, Briefing
from llm.provider_factory import get_provider
from prompts.manager import PromptManager
from app_logging.setup import get_logger

logger = get_logger(__name__)


async def generate_today_briefing() -> Dict[str, Any]:
    """生成今日简报（基于已分析文章，取前25篇按重要性排序）"""
    today_str = date.today().isoformat()
    logger.info(f"开始生成 {today_str} 简报...")

    async_engine = get_async_engine()
    async_session_maker = async_sessionmaker(async_engine, autocommit=False, autoflush=False)

    async with async_session_maker() as session:
        # 1. 查询今天已分析的文章（按重要性降序，取前25篇）
        stmt = (
            select(Article, Analysis)
            .join(Analysis, Article.id == Analysis.article_id)
            .where(Article.status == "analyzed")
            .order_by(desc(Analysis.importance))
            .limit(25)
        )
        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            logger.info("今日没有已分析的文章，跳过简报生成")
            return {"success": True, "message": "No articles to brief", "briefing": None}

        # 2. 组装数据
        articles_data = []
        article_ids = []
        for article, analysis in rows:
            articles_data.append({
                "title": article.title,
                "summary": analysis.summary,
                "category": analysis.category,
                "importance": analysis.importance,
                "why_it_matters": analysis.why_it_matters,
                "background_context": analysis.background_context or "",
            })
            article_ids.append(article.id)

        logger.info(f"找到 {len(articles_data)} 篇文章用于生成简报")

        # 3. 加载提示词
        prompt_manager = PromptManager()
        prompt = prompt_manager.get_prompt("generate_briefing", version="1")
        system_prompt = prompt["system_prompt"]

        # 构建用户提示
        articles_text = ""
        for i, art in enumerate(articles_data, 1):
            articles_text += f"\n--- 文章 {i} ---\n"
            articles_text += f"标题: {art['title']}\n"
            articles_text += f"分类: {art['category']}\n"
            articles_text += f"重要性: {art['importance']}/10\n"
            articles_text += f"摘要: {art['summary']}\n"
            articles_text += f"为什么重要: {art['why_it_matters']}\n"
            if art['background_context']:
                articles_text += f"背景: {art['background_context'][:200]}...\n"

        user_prompt = f"根据以下 {len(articles_data)} 篇文章，生成今日全球简报：\n\n{articles_text}"

        # 4. 调用 LLM
        provider = get_provider()
        params = {
            "temperature": prompt.get("params", {}).get("temperature", 0.5),
            "max_tokens": prompt.get("params", {}).get("max_tokens", 2500),
        }

        try:
            response = await provider.complete(
                prompt=user_prompt,
                system=system_prompt,
                params=params,
            )
            content = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"LLM 简报生成失败: {e}")
            return {"success": False, "error": str(e)}

        # 5. 检查是否已有今日简报（如有则更新）
        stmt_existing = select(Briefing).where(Briefing.date == today_str)
        existing_result = await session.execute(stmt_existing)
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.article_ids = json.dumps(article_ids)
            existing.created_at = datetime.now(timezone.utc)
            logger.info(f"更新已有简报: {today_str}")
        else:
            new_brief = Briefing(
                date=today_str,
                content=content,
                article_ids=json.dumps(article_ids),
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_brief)
            logger.info(f"创建新简报: {today_str}")

        await session.commit()
        logger.info(f"简报生成成功，包含 {len(article_ids)} 篇文章")

        return {
            "success": True,
            "date": today_str,
            "article_count": len(article_ids),
            "briefing": content,
        }