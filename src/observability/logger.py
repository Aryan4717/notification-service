"""Structured JSON logging with PII masking."""

from __future__ import annotations

import logging
import re
import sys

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # older python-json-logger
    from pythonjsonlogger import jsonlogger

    JsonFormatter = jsonlogger.JsonFormatter  # type: ignore[misc,assignment]

from src.config import get_settings


class PiiFilter(logging.Filter):
    EMAIL_RE = re.compile(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
    PHONE_RE = re.compile(r"(\+\d{2})\d+(\d{4})")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask(record.msg)
        return True

    @classmethod
    def mask(cls, text: str) -> str:
        text = cls.EMAIL_RE.sub(r"\1***\2", text)
        text = cls.PHONE_RE.sub(r"\1****\2", text)
        return text


def setup_logging() -> None:
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger_name"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(PiiFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())
