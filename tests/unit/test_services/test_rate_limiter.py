"""Rate limiter unit tests."""

from uuid import uuid4

from src.domain.enums import Channel, Priority
from src.services.rate_limiter import RateLimiter
from tests.conftest import FakeRedis


def test_rate_limit_allows_within_quota():
    redis = FakeRedis()
    limiter = RateLimiter(redis_client=redis, limit_per_hour=100)
    user = uuid4()
    allowed, remaining = limiter.check_rate_limit(user, channel=Channel.EMAIL)
    assert allowed is True
    assert remaining >= 0


def test_rate_limit_exceeded():
    redis = FakeRedis()
    limiter = RateLimiter(redis_client=redis, limit_per_hour=2)
    user = uuid4()
    assert limiter.check_rate_limit(user, channel=Channel.SMS)[0] is True
    assert limiter.check_rate_limit(user, channel=Channel.SMS)[0] is True
    assert limiter.check_rate_limit(user, channel=Channel.SMS)[0] is False


def test_critical_burst_higher_limit():
    redis = FakeRedis()
    limiter = RateLimiter(redis_client=redis, limit_per_hour=4)
    limiter.settings.rate_limit_critical_burst_factor = 1.25
    user = uuid4()
    # critical limit = 5
    for _ in range(5):
        assert limiter.check_rate_limit(user, priority=Priority.CRITICAL)[0] is True
    assert limiter.check_rate_limit(user, priority=Priority.CRITICAL)[0] is False
