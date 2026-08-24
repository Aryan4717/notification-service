"""ORM <-> domain mappers and repositories."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database.models import (
    NotificationDeliveryLogModel,
    NotificationModel,
    NotificationTemplateModel,
    UserModel,
    UserPreferenceModel,
)
from src.domain.entities import Notification, NotificationTemplate, UserPreference
from src.domain.enums import Channel, NotificationStatus, Priority


def ensure_user(session: Session, user_id: UUID) -> UserModel:
    user = session.get(UserModel, user_id)
    if user is None:
        user = UserModel(id=user_id)
        session.add(user)
        session.flush()
    return user


def notification_to_entity(row: NotificationModel) -> Notification:
    return Notification(
        id=row.id,
        user_id=row.user_id,
        channel=row.channel,
        priority=row.priority,
        status=row.status,
        subject=row.subject,
        body=row.body,
        recipient=row.recipient,
        template_id=row.template_id,
        variables=row.variables or {},
        idempotency_key=row.idempotency_key,
        delivery_attempts=row.delivery_attempts,
        last_error=row.last_error,
        task_id=row.task_id,
        scheduled_at=row.scheduled_at,
        sent_at=row.sent_at,
        next_retry_at=row.next_retry_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def apply_entity_to_model(row: NotificationModel, entity: Notification) -> None:
    row.status = entity.status
    row.priority = entity.priority
    row.subject = entity.subject
    row.body = entity.body
    row.recipient = entity.recipient
    row.variables = entity.variables
    row.delivery_attempts = entity.delivery_attempts
    row.last_error = entity.last_error
    row.task_id = entity.task_id
    row.scheduled_at = entity.scheduled_at
    row.sent_at = entity.sent_at
    row.next_retry_at = entity.next_retry_at
    row.updated_at = datetime.now(timezone.utc)


class SQLAlchemyNotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, notification: Notification) -> Notification:
        ensure_user(self.session, notification.user_id)
        row = NotificationModel(
            id=notification.id,
            user_id=notification.user_id,
            template_id=notification.template_id,
            channel=notification.channel,
            status=notification.status,
            priority=notification.priority,
            subject=notification.subject,
            body=notification.body,
            recipient=notification.recipient,
            variables=notification.variables,
            idempotency_key=notification.idempotency_key,
            delivery_attempts=notification.delivery_attempts,
            last_error=notification.last_error,
            task_id=notification.task_id,
            scheduled_at=notification.scheduled_at,
            sent_at=notification.sent_at,
            next_retry_at=notification.next_retry_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )
        self.session.add(row)
        self.session.flush()
        return notification_to_entity(row)

    def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        row = self.session.get(NotificationModel, notification_id)
        return notification_to_entity(row) if row else None

    def get_by_idempotency_key(self, key: str) -> Optional[Notification]:
        stmt = select(NotificationModel).where(NotificationModel.idempotency_key == key)
        row = self.session.scalar(stmt)
        return notification_to_entity(row) if row else None

    def get_by_user(
        self,
        user_id: UUID,
        *,
        status: Optional[NotificationStatus] = None,
        priority: Optional[Priority] = None,
        channel: Optional[Channel] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        filters = [NotificationModel.user_id == user_id]
        if status:
            filters.append(NotificationModel.status == status)
        if priority:
            filters.append(NotificationModel.priority == priority)
        if channel:
            filters.append(NotificationModel.channel == channel)
        count_stmt = select(func.count()).select_from(NotificationModel).where(*filters)
        total = int(self.session.scalar(count_stmt) or 0)
        stmt = (
            select(NotificationModel)
            .where(*filters)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = list(self.session.scalars(stmt))
        return [notification_to_entity(r) for r in rows], total

    def update(self, notification: Notification) -> Notification:
        row = self.session.get(NotificationModel, notification.id)
        if row is None:
            raise ValueError("Notification not found")
        apply_entity_to_model(row, notification)
        self.session.flush()
        return notification_to_entity(row)


class SQLAlchemyPreferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: UUID, channel: Channel) -> Optional[UserPreference]:
        stmt = select(UserPreferenceModel).where(
            UserPreferenceModel.user_id == user_id,
            UserPreferenceModel.channel == channel,
        )
        row = self.session.scalar(stmt)
        if not row:
            return None
        return UserPreference(
            user_id=row.user_id, channel=row.channel, enabled=row.enabled, created_at=row.created_at
        )

    def get_all_for_user(self, user_id: UUID) -> list[UserPreference]:
        stmt = select(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        rows = list(self.session.scalars(stmt))
        return [
            UserPreference(
                user_id=r.user_id, channel=r.channel, enabled=r.enabled, created_at=r.created_at
            )
            for r in rows
        ]

    def save(self, preference: UserPreference) -> UserPreference:
        ensure_user(self.session, preference.user_id)
        existing = self.get(preference.user_id, preference.channel)
        if existing:
            stmt = select(UserPreferenceModel).where(
                UserPreferenceModel.user_id == preference.user_id,
                UserPreferenceModel.channel == preference.channel,
            )
            row = self.session.scalar(stmt)
            assert row is not None
            row.enabled = preference.enabled
            self.session.flush()
            return UserPreference(
                user_id=row.user_id, channel=row.channel, enabled=row.enabled, created_at=row.created_at
            )
        row = UserPreferenceModel(
            id=uuid4(),
            user_id=preference.user_id,
            channel=preference.channel,
            enabled=preference.enabled,
            created_at=preference.created_at,
        )
        self.session.add(row)
        self.session.flush()
        return preference

    def delete(self, user_id: UUID, channel: Channel) -> None:
        stmt = select(UserPreferenceModel).where(
            UserPreferenceModel.user_id == user_id,
            UserPreferenceModel.channel == channel,
        )
        row = self.session.scalar(stmt)
        if row:
            self.session.delete(row)
            self.session.flush()


class SQLAlchemyTemplateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, template_id: UUID) -> Optional[NotificationTemplate]:
        row = self.session.get(NotificationTemplateModel, template_id)
        return self._to_entity(row) if row else None

    def get_by_name(self, name: str) -> Optional[NotificationTemplate]:
        stmt = select(NotificationTemplateModel).where(NotificationTemplateModel.name == name)
        row = self.session.scalar(stmt)
        return self._to_entity(row) if row else None

    def save(self, template: NotificationTemplate) -> NotificationTemplate:
        row = NotificationTemplateModel(
            id=template.id,
            name=template.name,
            subject=template.subject,
            body=template.body,
            variables=template.variables,
            created_at=template.created_at,
        )
        self.session.add(row)
        self.session.flush()
        return self._to_entity(row)

    def list_all(
        self, *, limit: int = 20, offset: int = 0, search: str | None = None
    ) -> tuple[list[NotificationTemplate], int]:
        filters = []
        if search:
            filters.append(NotificationTemplateModel.name.ilike(f"%{search}%"))
        count_stmt = select(func.count()).select_from(NotificationTemplateModel)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self.session.scalar(count_stmt) or 0)
        stmt = select(NotificationTemplateModel).order_by(NotificationTemplateModel.created_at.desc())
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.limit(limit).offset(offset)
        rows = list(self.session.scalars(stmt))
        return [self._to_entity(r) for r in rows], total

    def update(self, template: NotificationTemplate) -> NotificationTemplate:
        row = self.session.get(NotificationTemplateModel, template.id)
        if row is None:
            raise ValueError("Template not found")
        row.subject = template.subject
        row.body = template.body
        row.variables = template.variables
        self.session.flush()
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: NotificationTemplateModel) -> NotificationTemplate:
        return NotificationTemplate(
            id=row.id,
            name=row.name,
            subject=row.subject,
            body=row.body,
            variables=row.variables or [],
            created_at=row.created_at,
        )


class SQLAlchemyDeliveryLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        notification_id: UUID,
        channel: Channel,
        status: str,
        provider_response: str | None = None,
    ) -> None:
        row = NotificationDeliveryLogModel(
            id=uuid4(),
            notification_id=notification_id,
            channel=channel,
            status=status,
            provider_response=provider_response,
        )
        self.session.add(row)
        self.session.flush()

    def list_for_notification(self, notification_id: UUID) -> list[dict[str, Any]]:
        stmt = (
            select(NotificationDeliveryLogModel)
            .where(NotificationDeliveryLogModel.notification_id == notification_id)
            .order_by(NotificationDeliveryLogModel.timestamp.asc())
        )
        rows = list(self.session.scalars(stmt))
        return [
            {
                "id": r.id,
                "channel": r.channel,
                "status": r.status,
                "provider_response": r.provider_response,
                "timestamp": r.timestamp,
            }
            for r in rows
        ]
