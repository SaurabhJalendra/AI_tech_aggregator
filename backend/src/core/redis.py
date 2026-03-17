"""Redis client for caching and rate limiting."""

import json
from typing import Any

from src.core.config import settings

_redis_client = None


async def get_redis():
    """Get or create the Redis client (lazy init)."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
            await _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


async def cache_get(key: str) -> Any | None:
    """Get a cached value by key."""
    client = await get_redis()
    if not client:
        return None
    try:
        val = await client.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set a cached value with TTL in seconds."""
    client = await get_redis()
    if not client:
        return False
    try:
        await client.set(key, json.dumps(value), ex=ttl)
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    """Delete a cached key."""
    client = await get_redis()
    if not client:
        return False
    try:
        await client.delete(key)
        return True
    except Exception:
        return False
