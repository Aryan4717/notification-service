"""Queue producer — enqueue notifications for async delivery."""

from __future__ import annotations

from uuid import UUID

from src.domain.enums import Priority
from src.queue.priority_queue import celery_priority_for
from src.queue.worker_config import celery_app


class NotificationProducer:
    def enqueue(self, notification_id: UUID, priority: Priority, countdown: int = 0) -> str:
        """Enqueue send task; return Celery task id."""
        result = celery_app.send_task(
            "src.queue.tasks.send_notification_task",
            args=[str(notification_id)],
            countdown=countdown,
            priority=celery_priority_for(priority),
        )
        return result.id

    def enqueue_retry(self, notification_id: UUID, priority: Priority, delay_seconds: int) -> str:
        return self.enqueue(notification_id, priority, countdown=delay_seconds)
