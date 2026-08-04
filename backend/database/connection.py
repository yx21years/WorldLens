# backend/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from pathlib import Path

from config.settings import get_settings

_engine = None
_SessionLocal = None
_async_factory = None
_async_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        db_path = Path(settings.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}?check_same_thread=False", echo=settings.DEBUG)
    return _engine


def get_async_engine():
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        db_path = Path(settings.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _async_engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}?check_same_thread=False",
            echo=settings.DEBUG
        )
    return _async_engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_async_session_factory():
    """Return (or create) the async session factory."""
    global _async_factory
    if _async_factory is None:
        async_engine = get_async_engine()
        _async_factory = async_sessionmaker(async_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    return _async_factory


async def get_async_session() -> AsyncSession:
    """Create and return a new AsyncSession. Caller must close it manually."""
    factory = get_async_session_factory()
    return factory()


def get_db():
    Session = get_session_factory()
    session = Session()
    try:
        yield session
    finally:
        session.close()


async def init_db():
    """异步创建所有表（内部使用同步引擎，避免循环导入）"""
    engine = get_engine()
    # 在函数内部导入 Base，避免循环依赖
    from database.models import Base
    Base.metadata.create_all(engine)
# ========== 全局异步会话工厂 ==========
async_session_maker = async_sessionmaker(
    	get_async_engine(),
    	autocommit=False,
    	autoflush=False,
    	expire_on_commit=False
)