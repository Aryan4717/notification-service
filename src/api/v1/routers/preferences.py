"""User preference endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.api.v1.dependencies import get_preference_service
from src.domain.enums import Channel
from src.domain.schemas import PreferencesMapResponse, UserPreferenceRequest, UserPreferenceResponse
from src.services.preference_service import PreferenceService

router = APIRouter()


@router.get(
    "/users/{user_id}/preferences",
    response_model=PreferencesMapResponse,
    summary="Get user channel preferences",
    tags=["preferences"],
)
def get_preferences(
    user_id: UUID,
    response: Response,
    service: PreferenceService = Depends(get_preference_service),
) -> PreferencesMapResponse:
    prefs = service.get_user_preferences(user_id)
    response.headers["Cache-Control"] = "max-age=3600"
    return PreferencesMapResponse(user_id=user_id, preferences=prefs)


@router.post(
    "/users/{user_id}/preferences",
    response_model=UserPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set a channel preference",
    tags=["preferences"],
)
def set_preference(
    user_id: UUID,
    payload: UserPreferenceRequest,
    service: PreferenceService = Depends(get_preference_service),
) -> UserPreferenceResponse:
    saved = service.set_user_preference(user_id, payload.channel, payload.enabled)
    return UserPreferenceResponse(
        user_id=saved.user_id,
        channel=saved.channel,
        enabled=saved.enabled,
        created_at=saved.created_at,
    )


@router.delete(
    "/users/{user_id}/preferences/{channel}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset a channel preference to default (opt-in)",
    tags=["preferences"],
)
def delete_preference(
    user_id: UUID,
    channel: Channel,
    service: PreferenceService = Depends(get_preference_service),
) -> Response:
    service.delete_preference(user_id, channel)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
