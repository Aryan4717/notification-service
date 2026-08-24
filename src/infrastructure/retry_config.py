"""Retry classification configuration."""

PERMANENT_FAILURES = {
    "invalid_email",
    "invalid_number",
    "invalid_device_token",
    "account_suspended",
    "permanent_failure",
}

TRANSIENT_FAILURES = {
    "timeout",
    "connection_error",
    "service_down",
    "rate_limited",
    "temporary_unavailable",
    "transient_failure",
    "circuit_open",
}
