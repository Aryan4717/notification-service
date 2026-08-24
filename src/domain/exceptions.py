"""Domain-specific exceptions."""

from src.core.exceptions import AppException


class NotificationServiceException(AppException):
    """Base domain exception for notification service."""

    def __init__(self, message: str, code: str = "notification_error") -> None:
        super().__init__(message=message, code=code)


class InvalidNotificationException(NotificationServiceException):
    def __init__(self, message: str = "Invalid notification request") -> None:
        super().__init__(message=message, code="invalid_notification")


class UserPreferenceNotMetException(NotificationServiceException):
    def __init__(self, message: str = "User has opted out of this channel") -> None:
        super().__init__(message=message, code="preference_not_met")


class TemplateNotFoundException(NotificationServiceException):
    def __init__(self, message: str = "Template not found") -> None:
        super().__init__(message=message, code="template_not_found")


class RateLimitExceededException(NotificationServiceException):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message=message, code="rate_limit_exceeded")


class IdempotencyConflictException(NotificationServiceException):
    def __init__(self, message: str = "Idempotency key conflict") -> None:
        super().__init__(message=message, code="idempotency_conflict")


class ChannelNotAvailableException(NotificationServiceException):
    def __init__(self, message: str = "Channel temporarily unavailable") -> None:
        super().__init__(message=message, code="channel_unavailable")


class NotificationNotFoundException(NotificationServiceException):
    def __init__(self, message: str = "Notification not found") -> None:
        super().__init__(message=message, code="notification_not_found")


class CircuitOpenException(NotificationServiceException):
    def __init__(self, message: str = "Circuit breaker is open") -> None:
        super().__init__(message=message, code="circuit_open")
