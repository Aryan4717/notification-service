"""SMS channel adapter."""

import re

from src.channels.base import AbstractChannelAdapter
from src.domain.enums import Channel, DeliveryResult
from src.infrastructure.email_provider import SMSProvider


class SMSAdapter(AbstractChannelAdapter):
    channel_name = Channel.SMS
    timeout_seconds = 3.0

    def __init__(self, provider: SMSProvider | None = None) -> None:
        self.provider = provider or SMSProvider()

    def validate_recipient(self, recipient: str) -> bool:
        cleaned = re.sub(r"[\s\-()]", "", recipient)
        return bool(re.match(r"^\+?[1-9]\d{7,14}$", cleaned))

    def send(self, recipient: str, subject: str | None, body: str) -> tuple[DeliveryResult, str]:
        if not self.validate_recipient(recipient):
            return DeliveryResult.PERMANENT_FAILURE, "invalid_number"
        # Long SMS: truncate note for mock; still send full body
        result = self.provider.send(recipient, body)
        if result.success:
            return DeliveryResult.SUCCESS, result.reference_id
        if result.error_code in {"invalid_number", "account_suspended"}:
            return DeliveryResult.PERMANENT_FAILURE, result.error_code or "permanent_failure"
        return DeliveryResult.RETRY, result.error_code or "transient_failure"
