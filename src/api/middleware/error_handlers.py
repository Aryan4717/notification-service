"""Global exception handlers."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.domain.exceptions import (
    ChannelNotAvailableException,
    CircuitOpenException,
    IdempotencyConflictException,
    InvalidNotificationException,
    NotificationNotFoundException,
    NotificationServiceException,
    RateLimitExceededException,
    TemplateNotFoundException,
    UserPreferenceNotMetException,
)


def _error_body(request: Request, code: str, message: str, details: dict | None = None) -> dict:
    request_id = getattr(request.state, "request_id", None) or request.headers.get(
        "X-Request-ID", str(uuid4())
    )
    return {
        "error": code,
        "message": message,
        "details": details or {},
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RateLimitExceededException)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededException) -> JSONResponse:
        return JSONResponse(status_code=429, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(IdempotencyConflictException)
    async def idempotency_handler(request: Request, exc: IdempotencyConflictException) -> JSONResponse:
        return JSONResponse(status_code=409, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(NotificationNotFoundException)
    async def not_found_handler(request: Request, exc: NotificationNotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(TemplateNotFoundException)
    async def template_not_found(request: Request, exc: TemplateNotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(UserPreferenceNotMetException)
    async def pref_handler(request: Request, exc: UserPreferenceNotMetException) -> JSONResponse:
        return JSONResponse(status_code=400, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(InvalidNotificationException)
    async def invalid_handler(request: Request, exc: InvalidNotificationException) -> JSONResponse:
        return JSONResponse(status_code=400, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(ChannelNotAvailableException)
    async def channel_handler(request: Request, exc: ChannelNotAvailableException) -> JSONResponse:
        return JSONResponse(status_code=503, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(CircuitOpenException)
    async def circuit_handler(request: Request, exc: CircuitOpenException) -> JSONResponse:
        return JSONResponse(status_code=503, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(NotificationServiceException)
    async def domain_handler(request: Request, exc: NotificationServiceException) -> JSONResponse:
        return JSONResponse(status_code=400, content=_error_body(request, exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = {"errors": exc.errors()}
        return JSONResponse(
            status_code=400,
            content=_error_body(request, "validation_error", "Request validation failed", details),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_body(request, "validation_error", str(exc)),
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_body(request, "internal_error", "An unexpected error occurred"),
        )
