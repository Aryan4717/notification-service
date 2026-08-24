"""Pydantic request/response schemas for the API."""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.enums import Channel, NotificationStatus, Priority

T = TypeVar("T")


class NotificationCreateRequest(BaseModel):
    user_id: UUID
    channel: Channel
    recipient: str = Field(..., min_length=1, description="Email, phone, or device token")
    priority: Priority = Priority.NORMAL
    subject: str | None = None
    body: str | None = None
    template_id: UUID | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("body")
    @classmethod
    def body_or_template(cls, v: str | None, info: Any) -> str | None:
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "11111111-1111-1111-1111-111111111111",
                    "channel": "email",
                    "recipient": "user@example.com",
                    "priority": "high",
                    "subject": "Order shipped",
                    "body": "Hello, your order has shipped.",
                    "idempotency_key": "order-123-shipped",
                }
            ]
        }
    )


class DeliveryLogResponse(BaseModel):
    id: UUID
    channel: Channel
    status: str
    provider_response: str | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    channel: Channel
    priority: Priority
    status: NotificationStatus
    subject: str | None = None
    body: str
    recipient: str
    template_id: UUID | None = None
    delivery_attempts: int
    last_error: str | None = None
    task_id: str | None = None
    idempotency_key: str | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    delivery_logs: list[DeliveryLogResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceRequest(BaseModel):
    channel: Channel
    enabled: bool = True

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"channel": "sms", "enabled": False}]}
    )


class UserPreferenceResponse(BaseModel):
    user_id: UUID
    channel: Channel
    enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreferencesMapResponse(BaseModel):
    user_id: UUID
    preferences: dict[str, bool]


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    subject: str
    body: str
    variables: list[str] = Field(default_factory=list)


class TemplateUpdateRequest(BaseModel):
    subject: str | None = None
    body: str | None = None
    variables: list[str] | None = None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    subject: str
    body: str
    variables: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    timestamp: datetime
