"""User preference service with Redis caching."""

from __future__ import annotations

from uuid import UUID

from src.config import get_settings
from src.domain.entities import UserPreference
from src.domain.enums import Channel
from src.infrastructure.redis_client import get_redis
from src.repositories.preference_repository import SQLAlchemyPreferenceRepository


class PreferenceService:
    def __init__(self, repository: SQLAlchemyPreferenceRepository, redis_client=None) -> None:
        self.repository = repository
        self.redis = redis_client
        self.settings = get_settings()

    def _cache_key(self, user_id: UUID, channel: Channel) -> str:
        return f"pref:{user_id}:{channel.value}"

    def get_user_preferences(self, user_id: UUID) -> dict[str, bool]:
        prefs = {c.value: True for c in Channel}  # default opt-in
        stored = self.repository.get_all_for_user(user_id)
        for p in stored:
            prefs[p.channel.value] = p.enabled
        return prefs

    def set_user_preference(self, user_id: UUID, channel: Channel, enabled: bool) -> UserPreference:
        preference = UserPreference(user_id=user_id, channel=channel, enabled=enabled)
        saved = self.repository.save(preference)
        self._invalidate_cache(user_id, channel)
        return saved

    def validate_channel_enabled(self, user_id: UUID, channel: Channel) -> bool:
        cached = self._get_cached(user_id, channel)
        if cached is not None:
            return cached
        pref = self.repository.get(user_id, channel)
        enabled = True if pref is None else pref.enabled
        self._set_cached(user_id, channel, enabled)
        return enabled

    def delete_preference(self, user_id: UUID, channel: Channel) -> None:
        self.repository.delete(user_id, channel)
        self._invalidate_cache(user_id, channel)

    def _get_cached(self, user_id: UUID, channel: Channel) -> bool | None:
        if self.redis is None:
            try:
                self.redis = get_redis()
            except Exception:
                return None
        try:
            value = self.redis.get(self._cache_key(user_id, channel))
            if value is None:
                return None
            return value == "1"
        except Exception:
            return None

    def _set_cached(self, user_id: UUID, channel: Channel, enabled: bool) -> None:
        if self.redis is None:
            try:
                self.redis = get_redis()
            except Exception:
                return
        try:
            self.redis.setex(
                self._cache_key(user_id, channel),
                self.settings.preference_cache_ttl_seconds,
                "1" if enabled else "0",
            )
        except Exception:
            return

    def _invalidate_cache(self, user_id: UUID, channel: Channel) -> None:
        if self.redis is None:
            try:
                self.redis = get_redis()
            except Exception:
                return
        try:
            self.redis.delete(self._cache_key(user_id, channel))
        except Exception:
            return
