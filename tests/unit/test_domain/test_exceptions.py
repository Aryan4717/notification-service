"""Domain exception tests."""

from src.domain.exceptions import RateLimitExceededException, UserPreferenceNotMetException


def test_exceptions_have_codes() -> None:
    assert RateLimitExceededException().code == "rate_limit_exceeded"
    assert UserPreferenceNotMetException().code == "preference_not_met"
