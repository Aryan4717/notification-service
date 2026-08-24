"""Circuit breaker unit tests."""

from src.domain.enums import Channel
from src.infrastructure.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitState


def test_opens_after_threshold():
    CircuitBreakerRegistry.reset()
    breaker = CircuitBreaker(Channel.EMAIL, failure_threshold=3, recovery_seconds=60)
    assert breaker.allow_request() is True
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request() is False


def test_success_resets():
    breaker = CircuitBreaker(Channel.SMS, failure_threshold=2, recovery_seconds=60)
    breaker.record_failure()
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
