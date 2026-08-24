"""Exponential backoff retry orchestration."""

from __future__ import annotations

import random
from datetime import timedelta

from src.config import get_settings
from src.domain.enums import DeliveryResult
from src.infrastructure.retry_config import PERMANENT_FAILURES, TRANSIENT_FAILURES


class RetryService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def calculate_retry_delay(self, attempt: int) -> timedelta:
        """Exponential backoff: 2^attempt minutes with ±10% jitter. Attempt is 1-based."""
        base = self.settings.retry_base_minutes
        minutes = base ** attempt if attempt > 0 else base
        # Prefer 2^attempt * base_minutes style from assignment: 2, 4, 8
        minutes = (2**attempt) if attempt >= 1 else 2
        # Cap at 60 minutes
        minutes = min(minutes, 60)
        jitter = minutes * 0.1
        delayed = minutes + random.uniform(-jitter, jitter)
        return timedelta(minutes=max(0.1, delayed))

    def should_retry(self, error_code: str, attempt: int) -> bool:
        if attempt >= self.settings.max_retries:
            return False
        if error_code in PERMANENT_FAILURES:
            return False
        if error_code in TRANSIENT_FAILURES:
            return True
        # Default: retry unknown errors as transient
        return True

    def classify_result(self, result: DeliveryResult, provider_code: str) -> str:
        if result == DeliveryResult.PERMANENT_FAILURE:
            return provider_code if provider_code in PERMANENT_FAILURES else "permanent_failure"
        if result == DeliveryResult.RETRY:
            return provider_code if provider_code else "transient_failure"
        if result == DeliveryResult.FAILED:
            return provider_code or "transient_failure"
        return "success"
