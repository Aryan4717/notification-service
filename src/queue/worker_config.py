"""Celery application configuration."""

from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "notification_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.queue.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_default_queue="notifications.normal",
    task_queues=None,
    task_routes={
        "src.queue.tasks.send_notification_task": {"queue": "notifications.normal"},
    },
    broker_connection_retry_on_startup=True,
)

# Priority queues via Celery task priority (Redis transport supports 0-9; lower is higher priority in some versions)
# We map critical=9 ... low=0 for Redis broker priority.
PRIORITY_MAP = {
    "critical": 9,
    "high": 7,
    "normal": 5,
    "low": 1,
}
