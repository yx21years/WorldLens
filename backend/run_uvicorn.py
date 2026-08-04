"""Run command entry point for FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from database.connection import init_db
from app_logging.setup import setup_logging, get_logger

from routes.status import router as status_router
from routes.articles import router as articles_router
from routes.briefings import router as briefings_router
from routes.settings import router as settings_router

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = get_logger("main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal world intelligence assistant — AI-powered daily news analysis and briefing",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "app://worldlens-ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router)
app.include_router(articles_router)
app.include_router(briefings_router)
app.include_router(settings_router)


def run():
    """Entry point: `python -m run_uvicorn` or `python run_uvicorn.py`"""
    import sys
    from pathlib import Path
    import uvicorn

    # Set host/port from command-line args or default
    host = "--host" in sys.argv and sys.argv.index("--host") + 1 < len(sys.argv) and sys.argv[sys.argv.index("--host") + 1] or "127.0.0.1"
    port_str = "--port" in sys.argv and sys.argv.index("--port") + 1 < len(sys.argv) and int(sys.argv[sys.argv.index("--port") + 1]) or settings.API_PORT

    logger.info("starting_server", host=host, port=port_str)
    uvicorn.run(app, host=host, port=port_str, reload=settings.DEBUG)


if __name__ == "__main__":
    run()
