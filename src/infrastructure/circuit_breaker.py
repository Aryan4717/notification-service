"""Per-channel circuit breaker."""

from __future__ import annotations

import threading
import time
from enum import Enum

from src.config import get_settings
from src.domain.enums import Channel


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        channel: Channel,
        failure_threshold: int | None = None,
        recovery_seconds: int | None = None,
    ) -> None:
        settings = get_settings()
        self.channel = channel
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.recovery_seconds = recovery_seconds or settings.circuit_breaker_recovery_seconds
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    def _maybe_transition_to_half_open(self) -> None:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.recovery_seconds:
                self._state = CircuitState.HALF_OPEN

    def allow_request(self) -> bool:
        with self._lock:
            self._maybe_transition_to_half_open()
            if self._state == CircuitState.OPEN:
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()

    def is_healthy(self) -> bool:
        return self.state != CircuitState.OPEN


class CircuitBreakerRegistry:
    _breakers: dict[Channel, CircuitBreaker] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, channel: Channel) -> CircuitBreaker:
        with cls._lock:
            if channel not in cls._breakers:
                cls._breakers[channel] = CircuitBreaker(channel)
            return cls._breakers[channel]

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._breakers.clear()
