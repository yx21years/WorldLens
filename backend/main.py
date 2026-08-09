# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from database.connection import init_db,get_async_engine
from app_logging.setup import setup_logging, get_logger
from services.collection import collect_from_sources

from routes.status import router as status_router
from routes.articles import router as articles_router
from routes.briefings import router as briefings_router
from routes.settings import router as settings_router

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    logger.info("database_initialized")

    # ✅ 定时任务：每天早上 7:00 采集
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        collect_from_sources,
        trigger=CronTrigger(hour=7, minute=0),
        id="daily_collection",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler_started, daily collection scheduled at 07:00")

    yield

    # 关闭时清理
    scheduler.shutdown()
    await get_async_engine().dispose()
    logger.info("shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal world intelligence assistant — AI-powered daily news analysis and briefing",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "app://worldlens-ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(articles_router)
app.include_router(briefings_router)
app.include_router(settings_router)


@app.get("/health")
async def health_root():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}

# 放在所有路由和 app 定义之后
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # 生产环境不要开 reload
    )