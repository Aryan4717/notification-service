"""Mock email / SMS / push providers."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass

from src.config import get_settings


@dataclass
class ProviderResult:
    success: bool
    reference_id: str
    error_code: str | None = None
    message: str = ""


class BaseMockProvider:
    name: str = "mock"

    def __init__(self, failure_rate: float | None = None) -> None:
        settings = get_settings()
        self.failure_rate = (
            failure_rate if failure_rate is not None else settings.mock_provider_failure_rate
        )

    def _maybe_fail(self, permanent_codes: list[str], transient_codes: list[str]) -> ProviderResult | None:
        if random.random() < self.failure_rate:
            code = random.choice(transient_codes + permanent_codes)
            permanent = code in permanent_codes
            return ProviderResult(
                success=False,
                reference_id="",
                error_code=code,
                message=f"{self.name} failure: {code}" + (" (permanent)" if permanent else ""),
            )
        return None


class EmailProvider(BaseMockProvider):
    name = "mock-smtp"

    def send(self, to: str, subject: str, body: str) -> ProviderResult:
        fail = self._maybe_fail(
            permanent_codes=["invalid_email"],
            transient_codes=["timeout", "service_down", "connection_error"],
        )
        if fail:
            return fail
        ref = f"smtp-{uuid.uuid4().hex[:12]}"
        return ProviderResult(success=True, reference_id=ref, message=f"Email accepted for {to}")


class SMSProvider(BaseMockProvider):
    name = "mock-sms"

    def send(self, to: str, body: str) -> ProviderResult:
        fail = self._maybe_fail(
            permanent_codes=["invalid_number", "account_suspended"],
            transient_codes=["timeout", "service_down", "rate_limited"],
        )
        if fail:
            return fail
        sid = f"SM{uuid.uuid4().hex[:16]}"
        return ProviderResult(success=True, reference_id=sid, message=f"SMS queued to {to}")


class PushProvider(BaseMockProvider):
    name = "mock-fcm"

    def send(self, token: str, title: str | None, body: str) -> ProviderResult:
        fail = self._maybe_fail(
            permanent_codes=["invalid_device_token"],
            transient_codes=["timeout", "service_down", "temporary_unavailable"],
        )
        if fail:
            return fail
        ref = f"fcm-{uuid.uuid4().hex[:12]}"
        return ProviderResult(success=True, reference_id=ref, message=f"Push delivered to token")
