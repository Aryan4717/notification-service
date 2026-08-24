"""FastAPI dependency injection."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.queue.producer import NotificationProducer
from src.repositories.notification_repository import (
    SQLAlchemyDeliveryLogRepository,
    SQLAlchemyNotificationRepository,
    SQLAlchemyPreferenceRepository,
    SQLAlchemyTemplateRepository,
)
from src.services.notification_service import NotificationService
from src.services.preference_service import PreferenceService
from src.services.rate_limiter import RateLimiter


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(
        notification_repo=SQLAlchemyNotificationRepository(db),
        template_repo=SQLAlchemyTemplateRepository(db),
        delivery_log_repo=SQLAlchemyDeliveryLogRepository(db),
        preference_service=PreferenceService(SQLAlchemyPreferenceRepository(db)),
        rate_limiter=RateLimiter(),
        producer=NotificationProducer(),
    )


def get_preference_service(db: Session = Depends(get_db)) -> PreferenceService:
    return PreferenceService(SQLAlchemyPreferenceRepository(db))


def get_template_repo(db: Session = Depends(get_db)) -> SQLAlchemyTemplateRepository:
    return SQLAlchemyTemplateRepository(db)
