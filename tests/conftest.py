"""Shared pytest fixtures."""

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.config import Settings, get_settings
from src.database import models  # noqa: F401
from src.database.connection import Base, SessionLocal, configure_engine, get_db
from src.domain.enums import Priority
from src.main import create_app
from src.queue.producer import NotificationProducer
from src.queue.tasks import send_notification_task


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.zsets: dict[str, dict[str, float]] = {}

    def get(self, key: str):
        return self.store.get(key)

    def setex(self, key: str, _ttl: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)

    def ping(self) -> bool:
        return True

    def zremrangebyscore(self, key: str, min_s: float, max_s: float) -> int:
        z = self.zsets.setdefault(key, {})
        to_del = [m for m, s in z.items() if min_s <= s <= max_s]
        for m in to_del:
            del z[m]
        return len(to_del)

    def zcard(self, key: str) -> int:
        return len(self.zsets.get(key, {}))

    def zadd(self, key: str, mapping: dict) -> int:
        z = self.zsets.setdefault(key, {})
        z.update(mapping)
        return 1

    def expire(self, key: str, _ttl: int) -> None:
        return None

    def zrem(self, key: str, member: str) -> None:
        self.zsets.get(key, {}).pop(member, None)

    def pipeline(self):
        return FakePipeline(self)


class FakePipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self.redis = redis
        self.ops: list = []

    def zremrangebyscore(self, *a, **k):
        self.ops.append(("zremrangebyscore", a, k))
        return self

    def zcard(self, *a, **k):
        self.ops.append(("zcard", a, k))
        return self

    def zadd(self, *a, **k):
        self.ops.append(("zadd", a, k))
        return self

    def expire(self, *a, **k):
        self.ops.append(("expire", a, k))
        return self

    def execute(self):
        results = []
        for name, a, k in self.ops:
            results.append(getattr(self.redis, name)(*a, **k))
        self.ops = []
        return results


class EagerProducer(NotificationProducer):
    def enqueue(self, notification_id: UUID, priority: Priority, countdown: int = 0) -> str:
        if countdown == 0:
            send_notification_task(str(notification_id))
        return "eager-task"


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    test_engine = configure_engine("sqlite:///:memory:")
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session, fake_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("src.infrastructure.redis_client.get_redis", lambda: fake_redis)
    monkeypatch.setattr("src.services.rate_limiter.get_redis", lambda: fake_redis)
    monkeypatch.setattr("src.services.preference_service.get_redis", lambda: fake_redis)
    monkeypatch.setattr("src.api.v1.dependencies.NotificationProducer", EagerProducer)
    monkeypatch.setattr(
        "src.infrastructure.email_provider.get_settings",
        lambda: Settings(mock_provider_failure_rate=0.0),
    )

    app = create_app()

    def _override_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


@pytest.fixture
def user_id():
    return uuid4()
