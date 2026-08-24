"""Email channel adapter."""

import re

from src.channels.base import AbstractChannelAdapter
from src.domain.enums import Channel, DeliveryResult
from src.infrastructure.email_provider import EmailProvider


class EmailAdapter(AbstractChannelAdapter):
    channel_name = Channel.EMAIL
    timeout_seconds = 5.0

    def __init__(self, provider: EmailProvider | None = None) -> None:
        self.provider = provider or EmailProvider()

    def validate_recipient(self, recipient: str) -> bool:
        return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", recipient))

    def send(self, recipient: str, subject: str | None, body: str) -> tuple[DeliveryResult, str]:
        if not self.validate_recipient(recipient):
            return DeliveryResult.PERMANENT_FAILURE, "invalid_email"
        result = self.provider.send(recipient, subject or "", body)
        if result.success:
            return DeliveryResult.SUCCESS, result.reference_id
        if result.error_code in {"invalid_email"}:
            return DeliveryResult.PERMANENT_FAILURE, result.error_code or "permanent_failure"
        return DeliveryResult.RETRY, result.error_code or "transient_failure"
