"""Idempotency-Key header support for POST /notifications."""

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config import get_settings
from src.infrastructure.redis_client import get_redis

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or "/notifications" not in request.url.path:
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)

        try:
            redis = get_redis()
            cache_key = f"idem:{key}"
            cached = redis.get(cache_key)
            if cached:
                return JSONResponse(status_code=201, content=json.loads(cached))

            response = await call_next(request)
            return response
        except Exception:
            logger.warning("idempotency_middleware_skipped", extra={"reason": "redis_unavailable"})
            return await call_next(request)
