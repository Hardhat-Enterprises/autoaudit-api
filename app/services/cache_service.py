import aioredis
import asyncio
from typing import Optional
from app.core.config import settings
from structlog import get_logger

logger = get_logger()

class CacheService:
    """Redis-based cache service for AutoAudit API."""

    def __init__(self):
        # Initialize Redis connection pool
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        # Stats
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a value from cache."""
        # Use namespaced cache keys to avoid collisions across environments/projects
        value = await self.redis.get(f"{settings.CACHE_KEY_PREFIX}:{key}")
        if value is None:
            self.misses += 1
            logger.debug("Cache miss", key=key)
        else:
            self.hits += 1
            logger.debug("Cache hit", key=key)
        return value

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set a value in cache with TTL."""
        expire = ttl or settings.CACHE_TTL_DEFAULT
        await self.redis.set(
            f"{settings.CACHE_KEY_PREFIX}:{key}",
            value,
            ex=expire,
        )
        logger.debug("Cache set", key=key, ttl=expire)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self.redis.delete(f"{settings.CACHE_KEY_PREFIX}:{key}")
        logger.debug("Cache delete", key=key)

    async def clear(self) -> None:
        """Clear the entire cache (use with caution)."""
        await self.redis.flushdb()
        logger.warning("Cache cleared")

    def stats(self) -> dict:
        """Return cache hit/miss statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }

# Instantiate a singleton service
cache_service = CacheService()
