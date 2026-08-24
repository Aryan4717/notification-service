"""Channel adapter unit tests."""

from src.channels.email_adapter import EmailAdapter
from src.channels.push_adapter import PushAdapter
from src.channels.sms_adapter import SMSAdapter
from src.domain.enums import DeliveryResult
from src.infrastructure.email_provider import EmailProvider, PushProvider, SMSProvider


def test_email_invalid():
    adapter = EmailAdapter(EmailProvider(failure_rate=0.0))
    result, code = adapter.send("bad", "s", "b")
    assert result == DeliveryResult.PERMANENT_FAILURE
    assert code == "invalid_email"


def test_email_valid():
    adapter = EmailAdapter(EmailProvider(failure_rate=0.0))
    result, ref = adapter.send("a@b.com", "s", "hello")
    assert result == DeliveryResult.SUCCESS
    assert ref


def test_sms_invalid():
    adapter = SMSAdapter(SMSProvider(failure_rate=0.0))
    result, code = adapter.send("abc", None, "hi")
    assert result == DeliveryResult.PERMANENT_FAILURE


def test_sms_valid():
    adapter = SMSAdapter(SMSProvider(failure_rate=0.0))
    result, _ = adapter.send("+14155552671", None, "hi")
    assert result == DeliveryResult.SUCCESS


def test_push_invalid():
    adapter = PushAdapter(PushProvider(failure_rate=0.0))
    result, code = adapter.send("short", "t", "b")
    assert result == DeliveryResult.PERMANENT_FAILURE


def test_push_valid():
    adapter = PushAdapter(PushProvider(failure_rate=0.0))
    result, _ = adapter.send("device-token-12345", "Title", "Body")
    assert result == DeliveryResult.SUCCESS
