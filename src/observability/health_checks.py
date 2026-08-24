"""Health check helpers."""

from src.domain.enums import Channel
from src.infrastructure.circuit_breaker import CircuitBreakerRegistry
from src.infrastructure.redis_client import get_redis


def database_healthy() -> bool:
    try:
        from src.database.connection import engine

        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


def redis_healthy() -> bool:
    try:
        return bool(get_redis().ping())
    except Exception:
        return False


def channels_healthy() -> dict[str, bool]:
    return {c.value: CircuitBreakerRegistry.get(c).is_healthy() for c in Channel}


def readiness() -> dict:
    db = database_healthy()
    redis = redis_healthy()
    channels = channels_healthy()
    ready = db and redis and all(channels.values())
    return {
        "ready": ready,
        "database": db,
        "redis": redis,
        "channels": channels,
    }
