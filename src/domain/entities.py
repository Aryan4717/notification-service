"""Domain entities and value objects (no infrastructure imports)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.domain.enums import Channel, NotificationStatus, Priority


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email: {self.value}")


@dataclass(frozen=True)
class PhoneNumber:
    value: str

    def __post_init__(self) -> None:
        cleaned = re.sub(r"[\s\-()]", "", self.value)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            raise ValueError(f"Invalid phone number: {self.value}")


@dataclass(frozen=True)
class DeviceToken:
    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) < 8:
            raise ValueError("Invalid device token")


@dataclass
class UserPreference:
    user_id: UUID
    channel: Channel
    enabled: bool = True
    created_at: datetime = field(default_factory=utcnow)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserPreference):
            return False
        return self.user_id == other.user_id and self.channel == other.channel

    def __hash__(self) -> int:
        return hash((self.user_id, self.channel))


@dataclass
class NotificationTemplate:
    name: str
    subject: str
    body: str
    variables: list[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)

    def render(self, values: dict[str, Any]) -> tuple[str, str]:
        """Substitute {{var}} placeholders in subject and body."""
        subject = self.subject
        body = self.body
        for key, value in values.items():
            placeholder = "{{" + key + "}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        return subject, body


@dataclass
class Notification:
    user_id: UUID
    channel: Channel
    priority: Priority = Priority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    subject: str | None = None
    body: str = ""
    recipient: str = ""
    template_id: UUID | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None
    delivery_attempts: int = 0
    last_error: str | None = None
    task_id: str | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    next_retry_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def mark_sent(self) -> None:
        self.status = NotificationStatus.SENT
        self.sent_at = utcnow()
        self.updated_at = utcnow()

    def mark_delivered(self) -> None:
        self.status = NotificationStatus.DELIVERED
        self.updated_at = utcnow()

    def mark_failed(self, error: str) -> None:
        self.status = NotificationStatus.FAILED
        self.last_error = error
        self.updated_at = utcnow()

    def record_attempt(self, error: str | None = None) -> None:
        self.delivery_attempts += 1
        self.last_error = error
        self.updated_at = utcnow()
