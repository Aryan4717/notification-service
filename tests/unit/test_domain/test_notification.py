"""Domain entity tests."""

from uuid import uuid4

import pytest

from src.domain.entities import EmailAddress, NotificationTemplate, PhoneNumber
from src.domain.enums import Channel, Priority


def test_email_value_object_valid():
    assert EmailAddress("user@example.com").value == "user@example.com"


def test_email_value_object_invalid():
    with pytest.raises(ValueError):
        EmailAddress("not-an-email")


def test_phone_value_object():
    assert PhoneNumber("+14155552671").value == "+14155552671"


def test_template_render():
    tpl = NotificationTemplate(
        name="welcome",
        subject="Hello {{name}}",
        body="Order {{order_id}} ready",
        variables=["name", "order_id"],
    )
    subject, body = tpl.render({"name": "Ada", "order_id": "42"})
    assert subject == "Hello Ada"
    assert body == "Order 42 ready"


def test_priority_queue_score():
    assert Priority.CRITICAL.queue_score < Priority.LOW.queue_score
    assert Channel.EMAIL.value == "email"
