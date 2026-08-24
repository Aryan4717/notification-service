"""Channel adapter interfaces."""

from typing import Protocol

from src.domain.enums import Channel, DeliveryResult


class IChannelAdapter(Protocol):
    """Interface for notification channel adapters."""

    channel_name: Channel

    def send(self, recipient: str, subject: str | None, body: str) -> tuple[DeliveryResult, str]:
        """Send a message; return (result, provider_response)."""
        ...

    def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format for this channel."""
        ...

    def is_healthy(self) -> bool:
        """Return provider health status."""
        ...
