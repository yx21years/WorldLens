from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # rss | api
    url: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(10), default="US")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="分类（如：国际时事、科技AI等）")

    articles: Mapped[list["Article"]] = relationship(back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"))
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="raw")  # raw | analyzed | error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # ✅ 新增图片 URL 字段
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文章配图链接")

    source: Mapped["Source"] = relationship(back_populates="articles")
    analysis: Mapped["Analysis | None"] = relationship(back_populates="article", uselist=False)


class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"), unique=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-10
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)  # positive | negative | neutral
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    key_entities: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as text
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    background_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    potential_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    trend_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    article: Mapped["Article"] = relationship(back_populates="analysis")


class Briefing(Base):
    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # YYYY-MM-DD
    content: Mapped[str] = mapped_column(Text, nullable=False)
    article_ids: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as text
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserAction(Base):
    __tablename__ = "user_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"))
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # viewed | saved | skipped
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interest_weights: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    preferred_regions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )