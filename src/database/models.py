"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.database.connection import Base
from src.domain.enums import Channel, NotificationStatus, Priority


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Use JSON for SQLite tests; PostgreSQL prefers JSONB via dialect
JSONType = JSON().with_variant(JSONB(), "postgresql")


def _enum_values(enum_cls: type) -> list[str]:
    """Persist Enum.value (email) instead of Enum.name (EMAIL) for Postgres."""
    return [member.value for member in enum_cls]


def channel_enum(*, create_constraint: bool = True) -> Enum:
    return Enum(
        Channel,
        name="channel_enum",
        native_enum=False,
        create_constraint=create_constraint,
        values_callable=_enum_values,
    )


def status_enum() -> Enum:
    return Enum(
        NotificationStatus,
        name="notification_status_enum",
        native_enum=False,
        values_callable=_enum_values,
    )


def priority_enum() -> Enum:
    return Enum(
        Priority,
        name="priority_enum",
        native_enum=False,
        values_callable=_enum_values,
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    preferences = relationship("UserPreferenceModel", back_populates="user", cascade="all, delete")
    notifications = relationship("NotificationModel", back_populates="user", cascade="all, delete")


class UserPreferenceModel(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "channel", name="uq_user_channel"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[Channel] = mapped_column(channel_enum(), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("UserModel", back_populates="preferences")


class NotificationTemplateModel(Base):
    __tablename__ = "notification_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NotificationModel(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_status_priority_created", "user_id", "status", "priority", "created_at"),
        Index("ix_notifications_idempotency_key", "idempotency_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[Channel] = mapped_column(channel_enum(create_constraint=False), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        status_enum(),
        default=NotificationStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[Priority] = mapped_column(
        priority_enum(),
        default=Priority.NORMAL,
        nullable=False,
    )
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recipient: Mapped[str] = mapped_column(String(512), nullable=False)
    variables: Mapped[dict] = mapped_column(JSONType, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user = relationship("UserModel", back_populates="notifications")
    delivery_logs = relationship(
        "NotificationDeliveryLogModel", back_populates="notification", cascade="all, delete"
    )


class NotificationDeliveryLogModel(Base):
    __tablename__ = "notification_delivery_logs"
    __table_args__ = (Index("ix_delivery_logs_notification_ts", "notification_id", "timestamp"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[Channel] = mapped_column(channel_enum(create_constraint=False), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    notification = relationship("NotificationModel", back_populates="delivery_logs")


class RateLimitTrackerModel(Base):
    __tablename__ = "rate_limit_tracker"
    __table_args__ = (UniqueConstraint("user_id", "channel", name="uq_rate_user_channel"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    channel: Mapped[Channel] = mapped_column(channel_enum(create_constraint=False), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)
    window_reset_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
