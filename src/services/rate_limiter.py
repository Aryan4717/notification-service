"""Redis-backed sliding-window rate limiter."""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from src.config import get_settings
from src.domain.enums import Channel, Priority
from src.infrastructure.redis_client import get_redis


class RateLimiter:
    """Sliding window: max N notifications per hour per user (optionally per channel)."""

    def __init__(self, redis_client=None, limit_per_hour: int | None = None) -> None:
        self.settings = get_settings()
        self.redis = redis_client
        self._limit_override = limit_per_hour

    def _key(self, user_id: UUID, channel: Channel | None = None) -> str:
        if channel:
            return f"rate_limit:{user_id}:{channel.value}"
        return f"rate_limit:{user_id}"

    def _limit_for(self, priority: Priority) -> int:
        base = (
            self._limit_override
            if self._limit_override is not None
            else self.settings.rate_limit_per_hour
        )
        if priority == Priority.CRITICAL:
            return int(base * self.settings.rate_limit_critical_burst_factor)
        return base

    def check_rate_limit(
        self,
        user_id: UUID,
        *,
        channel: Channel | None = None,
        priority: Priority = Priority.NORMAL,
    ) -> tuple[bool, int]:
        """Return (allowed, remaining)."""
        limit = self._limit_for(priority)
        if self.redis is None:
            try:
                self.redis = get_redis()
            except Exception:
                return True, limit

        key = self._key(user_id, channel)
        now = time.time()
        window = 3600
        member = str(uuid4())
        try:
            self.redis.zremrangebyscore(key, 0, now - window)
            count = int(self.redis.zcard(key))
            if count >= limit:
                return False, 0
            self.redis.zadd(key, {member: now})
            self.redis.expire(key, window)
            remaining = max(0, limit - (count + 1))
            return True, remaining
        except Exception:
            return True, limit
