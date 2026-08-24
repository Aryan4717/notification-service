"""Notification REST endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from src.api.v1.dependencies import get_notification_service
from src.domain.enums import Channel, NotificationStatus, Priority
from src.domain.schemas import NotificationCreateRequest, NotificationResponse, PaginatedResponse
from src.services.notification_service import NotificationService

router = APIRouter()


@router.post(
    "/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a notification",
    tags=["notifications"],
)
def create_notification(
    payload: NotificationCreateRequest,
    response: Response,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    result = service.create_notification(payload)
    response.headers["X-RateLimit-Limit"] = "100"
    return result


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
    summary="Get notification status",
    tags=["notifications"],
)
def get_notification(
    notification_id: UUID,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    return service.get_notification(notification_id)


@router.get(
    "/users/{user_id}/notifications",
    response_model=PaginatedResponse[NotificationResponse],
    summary="List notifications for a user",
    tags=["notifications"],
)
def list_user_notifications(
    user_id: UUID,
    status_filter: NotificationStatus | None = Query(None, alias="status"),
    priority: Priority | None = None,
    channel: Channel | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: NotificationService = Depends(get_notification_service),
) -> PaginatedResponse[NotificationResponse]:
    items, total = service.list_user_notifications(
        user_id,
        status=status_filter,
        priority=priority,
        channel=channel,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
