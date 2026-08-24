"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from src.api.middleware.error_handlers import register_error_handlers
from src.api.middleware.idempotency import IdempotencyMiddleware
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.v1.routers import notifications as notifications_router
from src.api.v1.routers import preferences as preferences_router
from src.api.v1.routers import templates as templates_router
from src.config import get_settings
from src.observability.health_checks import readiness
from src.observability.logger import setup_logging
from src.observability.metrics import metrics_output


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Notification Service",
        version="1.0.0",
        description="Multi-channel notification service (Email, SMS, Push) with priority queues, retries, and delivery tracking.",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(IdempotencyMiddleware)
    register_error_handlers(app)

    prefix = settings.api_v1_prefix
    app.include_router(notifications_router.router, prefix=prefix)
    app.include_router(preferences_router.router, prefix=prefix)
    app.include_router(templates_router.router, prefix=prefix)

    # Assignment-compatible aliases without /api/v1
    app.include_router(notifications_router.router)
    app.include_router(preferences_router.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, bool]:
        return {"alive": True}

    @app.get("/health/ready", tags=["health"])
    async def ready() -> JSONResponse:
        payload = readiness()
        code = 200 if payload["ready"] else 503
        return JSONResponse(status_code=code, content=payload)

    @app.get("/metrics", tags=["observability"])
    async def metrics() -> Response:
        return Response(content=metrics_output(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()
