"""Push / in-app channel adapter."""

from src.channels.base import AbstractChannelAdapter
from src.domain.enums import Channel, DeliveryResult
from src.infrastructure.email_provider import PushProvider


class PushAdapter(AbstractChannelAdapter):
    channel_name = Channel.PUSH
    timeout_seconds = 5.0

    def __init__(self, provider: PushProvider | None = None) -> None:
        self.provider = provider or PushProvider()

    def validate_recipient(self, recipient: str) -> bool:
        return bool(recipient) and len(recipient) >= 8

    def send(self, recipient: str, subject: str | None, body: str) -> tuple[DeliveryResult, str]:
        if not self.validate_recipient(recipient):
            return DeliveryResult.PERMANENT_FAILURE, "invalid_device_token"
        result = self.provider.send(recipient, subject, body)
        if result.success:
            return DeliveryResult.SUCCESS, result.reference_id
        if result.error_code in {"invalid_device_token"}:
            return DeliveryResult.PERMANENT_FAILURE, result.error_code or "permanent_failure"
        return DeliveryResult.RETRY, result.error_code or "transient_failure"
