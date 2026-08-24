"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "notification-service"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/notif_db"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    rate_limit_per_hour: int = 100
    rate_limit_critical_burst_factor: float = 1.25

    max_retries: int = 3
    retry_base_minutes: int = 2
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_seconds: int = 30

    mock_provider_failure_rate: float = 0.05

    idempotency_ttl_seconds: int = 86400
    preference_cache_ttl_seconds: int = 3600
    template_cache_ttl_seconds: int = 86400


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
