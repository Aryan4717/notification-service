"""Abstract channel adapter base class."""

from abc import ABC, abstractmethod

from src.domain.enums import Channel, DeliveryResult


class AbstractChannelAdapter(ABC):
    channel_name: Channel
    timeout_seconds: float = 5.0
    max_retries: int = 3

    @abstractmethod
    def send(self, recipient: str, subject: str | None, body: str) -> tuple[DeliveryResult, str]:
        raise NotImplementedError

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        raise NotImplementedError

    def is_healthy(self) -> bool:
        return True
