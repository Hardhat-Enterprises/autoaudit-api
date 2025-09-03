from fastapi import APIRouter, HTTPException
from app.services.cache_service import cache_service
from app.core.config import settings

router = APIRouter()
PREFIX = settings.API_PREFIX + "/cache"

@router.get("/status")
async def cache_status():
    """
    Get cache status (enabled flag and Redis connection health).
    """
    enabled = settings.CACHE_ENABLED
    try:
        pong = await cache_service.redis.ping()
        healthy = pong is True
    except Exception as e:
        healthy = False
    return {"enabled": enabled, "healthy": healthy}

@router.post("/clear")
async def cache_clear():
    """
    Clear the entire cache.
    """
    if not settings.CACHE_ENABLED:
        raise HTTPException(status_code=400, detail="Caching is disabled")
    await cache_service.clear()
    return {"status": "cleared"}

@router.get("/stats")
async def cache_stats():
    """
    Retrieve cache hit/miss statistics.
    """
    stats = cache_service.stats()
    return stats
