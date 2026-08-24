"""Domain enumerations."""

from enum import Enum


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

    @property
    def queue_score(self) -> int:
        """Lower score = higher priority for Redis sorted sets / Celery."""
        return {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.NORMAL: 2,
            Priority.LOW: 3,
        }[self]


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class DeliveryResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    PERMANENT_FAILURE = "permanent_failure"
