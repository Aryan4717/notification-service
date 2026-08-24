"""Prometheus metrics."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Notifications sent",
    ["channel", "status"],
)
notifications_failed_total = Counter(
    "notifications_failed_total",
    "Notifications failed",
    ["channel", "error_type"],
)
retry_attempts_total = Counter(
    "retry_attempts_total",
    "Retry attempts",
    ["attempt_number"],
)
rate_limit_exceeded_total = Counter(
    "rate_limit_exceeded_total",
    "Rate limit exceeded events",
    ["channel"],
)
queue_size = Gauge("queue_size", "Pending notifications by priority", ["priority"])
channel_health = Gauge("channel_health", "Channel health (1=healthy)", ["channel"])
notification_delivery_duration_seconds = Histogram(
    "notification_delivery_duration_seconds",
    "Delivery duration",
    ["channel"],
)
api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    ["endpoint"],
)


def metrics_output() -> bytes:
    return generate_latest()
