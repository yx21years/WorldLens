import json
import re
import aiosqlite
from datetime import datetime, timezone

from llm.provider_factory import get_provider
from prompts.manager import PromptManager
from app_logging.setup import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()
DB_PATH = settings.DATABASE_PATH


def _extract_json(text: str) -> dict:
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
        raise ValueError(f"Invalid JSON: {e}")


async def analyze_all_direct_async():
    """全异步原生 SQLite 分析，完全绕过 ORM"""
    analyzed_ids = []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT id, title, raw_content FROM articles WHERE status = "raw"'
        )
        articles = await cursor.fetchall()

        logger.info(f"找到 {len(articles)} 篇待分析文章")

        for row in articles:
            article_id = row['id']
            title = row['title'] or ""
            content = row['raw_content'] or ""

            # 检查是否已有分析
            cursor2 = await db.execute(
                'SELECT id FROM analysis WHERE article_id = ?', (article_id,)
            )
            existing = await cursor2.fetchone()
            if existing:
                logger.info(f"文章 {article_id} 已有分析，跳过")
                await db.execute(
                    'UPDATE articles SET status = "analyzed" WHERE id = ?', (article_id,)
                )
                await db.commit()
                analyzed_ids.append(article_id)
                continue

            if len(content) > 1500:
                content = content[:1497] + "..."

            prompt_manager = PromptManager()
            prompt = prompt_manager.get_prompt("analyze_article", version="2")
            system_prompt = prompt["system_prompt"]
            user_prompt = prompt["user_prompt_template"].format(title=title, content=content)

            provider = get_provider()
            params = {
                "temperature": prompt.get("params", {}).get("temperature", 0.3),
                "max_tokens": 1000,
            }

            try:
                response = await provider.complete(
                    prompt=user_prompt,
                    system=system_prompt,
                    params=params,
                )
                raw_text = response.content if hasattr(response, 'content') else str(response)
                result = _extract_json(raw_text)

                required = ["summary", "importance", "category", "sentiment", "why_it_matters"]
                for field in required:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")

                await db.execute('''
                    INSERT INTO analysis (
                        article_id, summary, importance, category, sentiment,
                        why_it_matters, background_context, potential_impact,
                        key_entities, trend_level, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_id,
                    result.get("summary", ""),
                    int(result.get("importance", 5)),
                    result.get("category", ""),
                    result.get("sentiment", "neutral"),
                    result.get("why_it_matters", ""),
                    result.get("background_context", ""),
                    result.get("potential_impact", ""),
                    json.dumps(result.get("key_entities", [])),
                    result.get("trend_level", "MEDIUM"),
                    datetime.now(timezone.utc).isoformat()
                ))

                await db.execute(
                    'UPDATE articles SET status = "analyzed" WHERE id = ?', (article_id,)
                )
                await db.commit()

                logger.info(f"文章 {article_id} 分析完成")
                analyzed_ids.append(article_id)

            except Exception as e:
                logger.error(f"文章 {article_id} 分析失败: {e}")
                await db.execute(
                    'UPDATE articles SET status = "error" WHERE id = ?', (article_id,)
                )
                await db.commit()
                continue

    return analyzed_ids