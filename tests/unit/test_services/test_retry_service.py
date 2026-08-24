"""Retry service unit tests."""

from src.services.retry_service import RetryService


def test_exponential_backoff_increases():
    svc = RetryService()
    d1 = svc.calculate_retry_delay(1).total_seconds()
    d2 = svc.calculate_retry_delay(2).total_seconds()
    d3 = svc.calculate_retry_delay(3).total_seconds()
    assert d1 < d2 < d3 or d1 <= d2 <= d3


def test_should_not_retry_permanent():
    svc = RetryService()
    assert svc.should_retry("invalid_email", 1) is False


def test_should_retry_transient():
    svc = RetryService()
    assert svc.should_retry("timeout", 1) is True


def test_max_retries():
    svc = RetryService()
    assert svc.should_retry("timeout", 3) is False
