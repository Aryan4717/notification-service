"""Celery tasks for notification delivery."""

from __future__ import annotations

import logging
from uuid import UUID

from src.channels.factory import ChannelAdapterFactory
from src.database.connection import session_scope
from src.domain.enums import DeliveryResult, NotificationStatus
from src.infrastructure.circuit_breaker import CircuitBreakerRegistry
from src.queue.producer import NotificationProducer
from src.queue.worker_config import celery_app
from src.repositories.notification_repository import (
    SQLAlchemyDeliveryLogRepository,
    SQLAlchemyNotificationRepository,
)
from src.services.retry_service import RetryService

logger = logging.getLogger(__name__)


@celery_app.task(name="src.queue.tasks.send_notification_task", bind=True, max_retries=3)
def send_notification_task(self, notification_id: str) -> dict:
    """Process a single notification delivery attempt."""
    nid = UUID(notification_id)
    retry_service = RetryService()
    producer = NotificationProducer()

    with session_scope() as session:
        repo = SQLAlchemyNotificationRepository(session)
        logs = SQLAlchemyDeliveryLogRepository(session)
        notification = repo.get_by_id(nid)
        if notification is None:
            logger.error("notification_not_found", extra={"notification_id": notification_id})
            return {"status": "missing"}

        breaker = CircuitBreakerRegistry.get(notification.channel)
        if not breaker.allow_request():
            error = "circuit_open"
            notification.record_attempt(error)
            logs.add(nid, notification.channel, "retry", error)
            if retry_service.should_retry(error, notification.delivery_attempts):
                delay = retry_service.calculate_retry_delay(notification.delivery_attempts)
                notification.next_retry_at = notification.updated_at + delay  # type: ignore[operator]
                repo.update(notification)
                producer.enqueue_retry(nid, notification.priority, int(delay.total_seconds()))
                return {"status": "circuit_open_retry"}
            notification.mark_failed(error)
            repo.update(notification)
            return {"status": "failed", "error": error}

        adapter = ChannelAdapterFactory.get_adapter(notification.channel)
        try:
            result, provider_response = adapter.send(
                notification.recipient, notification.subject, notification.body
            )
        except Exception as exc:  # noqa: BLE001
            result, provider_response = DeliveryResult.RETRY, f"exception:{exc}"

        error_code = retry_service.classify_result(result, provider_response)
        notification.record_attempt(None if result == DeliveryResult.SUCCESS else error_code)
        logs.add(
            nid,
            notification.channel,
            result.value,
            provider_response,
        )

        if result == DeliveryResult.SUCCESS:
            breaker.record_success()
            notification.mark_sent()
            notification.mark_delivered()
            repo.update(notification)
            logger.info(
                "notification_delivered",
                extra={"notification_id": notification_id, "channel": notification.channel.value},
            )
            return {"status": "delivered", "provider": provider_response}

        breaker.record_failure()
        if result == DeliveryResult.PERMANENT_FAILURE or not retry_service.should_retry(
            error_code, notification.delivery_attempts
        ):
            notification.mark_failed(error_code)
            repo.update(notification)
            return {"status": "failed", "error": error_code}

        delay = retry_service.calculate_retry_delay(notification.delivery_attempts)
        from datetime import datetime, timezone

        notification.next_retry_at = datetime.now(timezone.utc) + delay
        notification.status = NotificationStatus.PENDING
        repo.update(notification)
        producer.enqueue_retry(nid, notification.priority, int(delay.total_seconds()))
        return {"status": "retry_scheduled", "delay_seconds": int(delay.total_seconds())}


@celery_app.task(name="src.queue.tasks.retry_failed_notification")
def retry_failed_notification(notification_id: str) -> dict:
    return send_notification_task(notification_id)
