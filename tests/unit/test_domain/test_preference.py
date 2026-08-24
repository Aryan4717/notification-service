"""Preference value object tests."""

from uuid import uuid4

from src.domain.entities import UserPreference
from src.domain.enums import Channel


def test_preference_equality() -> None:
    uid = uuid4()
    a = UserPreference(user_id=uid, channel=Channel.EMAIL, enabled=True)
    b = UserPreference(user_id=uid, channel=Channel.EMAIL, enabled=False)
    assert a == b
    assert hash(a) == hash(b)
