"""Channel adapter factory."""

from src.channels.base import AbstractChannelAdapter
from src.channels.email_adapter import EmailAdapter
from src.channels.push_adapter import PushAdapter
from src.channels.sms_adapter import SMSAdapter
from src.domain.enums import Channel
from src.domain.exceptions import ChannelNotAvailableException


class ChannelAdapterFactory:
    """Singleton-style factory for channel adapters."""

    _adapters: dict[Channel, AbstractChannelAdapter] | None = None

    @classmethod
    def _ensure(cls) -> dict[Channel, AbstractChannelAdapter]:
        if cls._adapters is None:
            cls._adapters = {
                Channel.EMAIL: EmailAdapter(),
                Channel.SMS: SMSAdapter(),
                Channel.PUSH: PushAdapter(),
            }
        return cls._adapters

    @classmethod
    def get_adapter(cls, channel: Channel) -> AbstractChannelAdapter:
        adapters = cls._ensure()
        adapter = adapters.get(channel)
        if adapter is None:
            raise ChannelNotAvailableException(f"No adapter for channel {channel}")
        return adapter

    @classmethod
    def reset(cls) -> None:
        """Reset adapters (for tests)."""
        cls._adapters = None
