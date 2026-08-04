from fastapi import APIRouter
from database.connection import get_engine
from config.settings import get_settings

router = APIRouter(prefix="/api/v1/status", tags=["status"])


@router.get("/health")
async def health_check():
    """Health check — confirms backend is running."""
    settings = get_settings()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
    }


@router.get("/stats")
async def get_stats():
    """Application statistics. Full implementation in Phase 2."""
    engine = get_engine()
    return {
        "data": {
            "articles_total": 0,
            "articles_analyzed": 0,
            "last_collection": None,
        },
        "errors": [],
    }
