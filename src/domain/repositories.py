"""Repository and adapter interfaces (Protocols)."""

from typing import Any, Optional, Protocol
from uuid import UUID

from src.domain.entities import Notification, NotificationTemplate, UserPreference
from src.domain.enums import Channel, DeliveryResult, NotificationStatus, Priority


class NotificationRepository(Protocol):
    def save(self, notification: Notification) -> Notification: ...

    def get_by_id(self, notification_id: UUID) -> Optional[Notification]: ...

    def get_by_idempotency_key(self, key: str) -> Optional[Notification]: ...

    def get_by_user(
        self,
        user_id: UUID,
        *,
        status: Optional[NotificationStatus] = None,
        priority: Optional[Priority] = None,
        channel: Optional[Channel] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]: ...

    def update(self, notification: Notification) -> Notification: ...


class PreferenceRepository(Protocol):
    def get(self, user_id: UUID, channel: Channel) -> Optional[UserPreference]: ...

    def get_all_for_user(self, user_id: UUID) -> list[UserPreference]: ...

    def save(self, preference: UserPreference) -> UserPreference: ...

    def delete(self, user_id: UUID, channel: Channel) -> None: ...


class TemplateRepository(Protocol):
    def get(self, template_id: UUID) -> Optional[NotificationTemplate]: ...

    def get_by_name(self, name: str) -> Optional[NotificationTemplate]: ...

    def save(self, template: NotificationTemplate) -> NotificationTemplate: ...

    def list_all(self, *, limit: int = 20, offset: int = 0, search: str | None = None) -> tuple[list[NotificationTemplate], int]: ...

    def update(self, template: NotificationTemplate) -> NotificationTemplate: ...


class DeliveryLogRepository(Protocol):
    def add(
        self,
        notification_id: UUID,
        channel: Channel,
        status: str,
        provider_response: str | None = None,
    ) -> None: ...

    def list_for_notification(self, notification_id: UUID) -> list[dict[str, Any]]: ...


class ChannelAdapter(Protocol):
    channel_name: Channel

    def send(self, recipient: str, subject: str | None, body: str) -> tuple[DeliveryResult, str]: ...

    def validate_recipient(self, recipient: str) -> bool: ...
