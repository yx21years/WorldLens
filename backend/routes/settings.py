from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/")
async def get_settings():
    """Get current user settings. Full implementation in Phase 3."""
    return {"data": {"interests": [], "sources": [], "llm_provider": "claude"}, "errors": []}


@router.put("/")
async def update_settings():
    """Update user settings. Full implementation in Phase 3."""
    return {"data": {"status": "updated"}, "errors": []}


@router.get("/sources")
async def list_sources():
    """List configured news sources. Full implementation in Phase 3."""
    return {"data": [], "errors": []}


@router.post("/sources")
async def add_source():
    """Add a news source. Full implementation in Phase 3."""
    return {"data": {"status": "added"}, "errors": []}


@router.delete("/sources/{source_id}")
async def remove_source(source_id: int):
    """Remove a news source. Full implementation in Phase 3."""
    return {"data": {"status": "removed"}, "errors": []}
