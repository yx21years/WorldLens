#!/usr/bin/env python
"""
导入 OPML 文件中的 RSS 订阅源到数据库。
用法：python import_opml.py --opml my_feeds.opml
"""
import asyncio
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import List, Dict, Optional

from database.connection import async_session_maker
from database.models import Source


# OPML 分类 → 前端四分类映射
CATEGORY_MAP = {
    "科技": "tech",
    "战争/冲突": "war",
    "生活": "life",
    "休闲": "leisure",
}


def parse_opml(file_path: str) -> List[Dict[str, str]]:
    tree = ET.parse(file_path)
    root = tree.getroot()
    feeds = []

    def traverse(outline, current_category: Optional[str] = None):
        if outline.get('xmlUrl'):
            name = outline.get('title') or outline.get('text') or '未命名源'
            url = outline.get('xmlUrl')
            if url:
                mapped_category = CATEGORY_MAP.get(current_category or '', 'life')
                feeds.append({
                    'name': name,
                    'url': url,
                    'category': mapped_category
                })
        else:
            cat = outline.get('text') or outline.get('title') or '未分类'
            new_cat = cat if current_category is None else f"{current_category} > {cat}"
            for child in outline:
                traverse(child, new_cat if new_cat else None)

    body = root.find('body')
    if body is None:
        print("错误：找不到 <body> 节点")
        return []
    for child in body:
        traverse(child, None)
    return feeds


async def insert_feeds(feeds: List[Dict[str, str]]) -> int:
    from sqlalchemy import select
    inserted = 0
    async with async_session_maker() as session:
        for feed in feeds:
            stmt = select(Source).where(Source.url == feed['url'])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                print(f"跳过已存在: {feed['name']}")
                continue
            new_source = Source(
                name=feed['name'],
                url=feed['url'],
                type='rss',
                active=True,
                country='US',
                category=feed['category']
            )
            session.add(new_source)
            inserted += 1
            if inserted % 10 == 0:
                print(f"已插入 {inserted} 条")
        await session.commit()
    return inserted


async def main(opml_path: str):
    print(f"正在解析 OPML 文件: {opml_path}")
    feeds = parse_opml(opml_path)
    if not feeds:
        print("没有找到任何订阅源。")
        return

    print(f"共解析到 {len(feeds)} 个订阅源")
    categories = {}
    for f in feeds:
        categories[f['category']] = categories.get(f['category'], 0) + 1
    print("分类统计（映射后）:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")

    print("正在插入数据库...")
    inserted = await insert_feeds(feeds)
    print(f"成功插入 {inserted} 个新源，跳过 {len(feeds) - inserted} 个已存在。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--opml', required=True, help='OPML 文件路径')
    args = parser.parse_args()
    if not Path(args.opml).exists():
        print(f"文件不存在: {args.opml}")
        exit(1)
    asyncio.run(main(args.opml))