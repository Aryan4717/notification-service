"""Priority helpers for queue routing."""

from src.domain.enums import Priority
from src.queue.worker_config import PRIORITY_MAP


def celery_priority_for(priority: Priority) -> int:
    return PRIORITY_MAP.get(priority.value, 5)


def queue_name_for(priority: Priority) -> str:
    return f"notifications.{priority.value}"
