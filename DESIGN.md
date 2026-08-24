# Design Document — Notification Service

## High-level architecture

```
Client -> FastAPI (validation, preferences, rate limit, persist)
       -> Celery producer (Redis broker)
       -> Celery worker -> Channel adapter (Email/SMS/Push mock)
       -> Update status + delivery_logs in PostgreSQL
```

Layers:

1. **API** — routers, middleware, DI
2. **Services** — notification, preference, rate limit, retry
3. **Domain** — entities, enums, exceptions, protocols (no infra imports)
4. **Repositories / adapters** — SQLAlchemy + channel adapters
5. **Infrastructure** — Redis, Celery, circuit breaker, mock providers

## Database schema

- `users` — external user ids only
- `user_preferences` — per-channel opt-in/out (unique user_id+channel)
- `notification_templates` — reusable `{{var}}` templates
- `notifications` — lifecycle, priority, idempotency_key (unique), attempts, errors
- `notification_delivery_logs` — audit trail per attempt
- `rate_limit_tracker` — optional DB tracker (primary limiter is Redis)

Indexes focus on `(user_id, status, priority, created_at)` and unique idempotency keys for high read/write throughput.

## Failure handling and retries

- Classify permanent (`invalid_email`, `invalid_number`, …) vs transient (`timeout`, `service_down`, …).
- Max 3 retries with exponential backoff (~2, 4, 8 minutes) plus jitter.
- Persist attempt state before scheduling the next retry (no silent loss).
- Per-channel circuit breaker: open after consecutive failures; half-open probe after recovery window.

## Scalability (1000+/sec)

- API path is enqueue-only (persist + Redis publish) for low latency.
- Horizontal Celery workers process deliveries asynchronously.
- Redis for rate limits and preference cache; PostgreSQL connection pooling.
- Priority mapped onto Celery task priority so critical work is preferred.

## Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Sync SQLAlchemy + Celery workers | Simpler than fully async ORM; FastAPI stays responsive via async enqueue |
| Mock providers | Focuses on service design, not vendor SDKs |
| Fail-open rate limit if Redis down | Availability over strict limiting in degraded mode |
| Default opt-in preferences | Safer for transactional alerts; document for product review |

## Observability

- JSON logs with request_id and PII masking
- Prometheus metrics at `/metrics`
- `/health`, `/health/live`, `/health/ready`
- Flower UI for Celery when running Compose
