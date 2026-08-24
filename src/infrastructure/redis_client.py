"""Redis client helper."""

from __future__ import annotations

import redis

from src.config import get_settings

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def reset_redis() -> None:
    global _redis_client
    _redis_client = None
