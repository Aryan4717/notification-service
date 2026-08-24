"""Main notification business logic."""

from __future__ import annotations

from uuid import UUID

from src.channels.factory import ChannelAdapterFactory
from src.domain.entities import Notification
from src.domain.enums import Channel, NotificationStatus, Priority
from src.domain.exceptions import (
    IdempotencyConflictException,
    InvalidNotificationException,
    NotificationNotFoundException,
    RateLimitExceededException,
    TemplateNotFoundException,
    UserPreferenceNotMetException,
)
from src.domain.schemas import (
    DeliveryLogResponse,
    NotificationCreateRequest,
    NotificationResponse,
)
from src.queue.producer import NotificationProducer
from src.repositories.notification_repository import (
    SQLAlchemyDeliveryLogRepository,
    SQLAlchemyNotificationRepository,
    SQLAlchemyTemplateRepository,
)
from src.services.preference_service import PreferenceService
from src.services.rate_limiter import RateLimiter


class NotificationService:
    def __init__(
        self,
        notification_repo: SQLAlchemyNotificationRepository,
        template_repo: SQLAlchemyTemplateRepository,
        delivery_log_repo: SQLAlchemyDeliveryLogRepository,
        preference_service: PreferenceService,
        rate_limiter: RateLimiter,
        producer: NotificationProducer | None = None,
    ) -> None:
        self.notification_repo = notification_repo
        self.template_repo = template_repo
        self.delivery_log_repo = delivery_log_repo
        self.preference_service = preference_service
        self.rate_limiter = rate_limiter
        self.producer = producer or NotificationProducer()

    def create_notification(self, request: NotificationCreateRequest) -> NotificationResponse:
        if not request.body and not request.template_id:
            raise InvalidNotificationException("Either body or template_id is required")

        if request.idempotency_key:
            existing = self.notification_repo.get_by_idempotency_key(request.idempotency_key)
            if existing:
                return self._to_response(existing)

        if not self.preference_service.validate_channel_enabled(request.user_id, request.channel):
            raise UserPreferenceNotMetException(
                f"User opted out of channel {request.channel.value}"
            )

        allowed, remaining = self.rate_limiter.check_rate_limit(
            request.user_id, channel=request.channel, priority=request.priority
        )
        if not allowed:
            raise RateLimitExceededException(
                f"Rate limit exceeded for user (remaining={remaining})"
            )

        adapter = ChannelAdapterFactory.get_adapter(request.channel)
        if not adapter.validate_recipient(request.recipient):
            raise InvalidNotificationException(f"Invalid recipient for {request.channel.value}")

        subject = request.subject
        body = request.body or ""
        template_id = request.template_id
        if template_id:
            template = self.template_repo.get(template_id)
            if template is None:
                raise TemplateNotFoundException()
            subject, body = template.render(request.variables)

        notification = Notification(
            user_id=request.user_id,
            channel=request.channel,
            priority=request.priority,
            status=NotificationStatus.PENDING,
            subject=subject,
            body=body,
            recipient=request.recipient,
            template_id=template_id,
            variables=request.variables,
            idempotency_key=request.idempotency_key,
        )
        saved = self.notification_repo.save(notification)
        self.notification_repo.session.commit()
        task_id = self.producer.enqueue(saved.id, saved.priority)
        saved.task_id = task_id
        saved = self.notification_repo.update(saved)
        self.notification_repo.session.commit()
        return self._to_response(saved)

    def get_notification(self, notification_id: UUID) -> NotificationResponse:
        notification = self.notification_repo.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundException()
        logs = self.delivery_log_repo.list_for_notification(notification_id)
        return self._to_response(notification, logs)

    def list_user_notifications(
        self,
        user_id: UUID,
        *,
        status: NotificationStatus | None = None,
        priority: Priority | None = None,
        channel: Channel | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[NotificationResponse], int]:
        items, total = self.notification_repo.get_by_user(
            user_id,
            status=status,
            priority=priority,
            channel=channel,
            limit=min(limit, 100),
            offset=offset,
        )
        return [self._to_response(n) for n in items], total

    def _to_response(
        self, notification: Notification, logs: list[dict] | None = None
    ) -> NotificationResponse:
        delivery_logs = []
        if logs:
            delivery_logs = [
                DeliveryLogResponse(
                    id=log["id"],
                    channel=log["channel"],
                    status=log["status"],
                    provider_response=log.get("provider_response"),
                    timestamp=log["timestamp"],
                )
                for log in logs
            ]
        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            channel=notification.channel,
            priority=notification.priority,
            status=notification.status,
            subject=notification.subject,
            body=notification.body,
            recipient=notification.recipient,
            template_id=notification.template_id,
            delivery_attempts=notification.delivery_attempts,
            last_error=notification.last_error,
            task_id=notification.task_id,
            idempotency_key=notification.idempotency_key,
            scheduled_at=notification.scheduled_at,
            sent_at=notification.sent_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
            delivery_logs=delivery_logs,
        )
