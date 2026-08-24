# Notification Service

Multi-channel notification backend (Email, SMS, Push) with priority queues, user preferences, retries, rate limiting, and delivery tracking.

## Features

- REST API for sending notifications and managing preferences/templates
- Channels: Email, SMS, Push (mocked providers)
- Priorities: critical, high, normal, low
- Templates with `{{variable}}` substitution
- Delivery status: pending, sent, delivered, failed
- Exponential backoff retries (max 3)
- Idempotency keys and per-user rate limiting (100/hour)
- Structured JSON logging, Prometheus `/metrics`, health probes
- Docker Compose with PostgreSQL, Redis, Celery worker, Flower

## Tech stack

| Choice | Why |
|--------|-----|
| FastAPI | Async-friendly ASGI API, automatic OpenAPI |
| PostgreSQL | Durable notification + audit persistence |
| Redis + Celery | Reliable async processing and caching |
| SQLAlchemy + Alembic | Typed ORM and migrations |
| Pydantic v2 | Request validation and settings |

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Flower: http://localhost:5555
- Health: http://localhost:8000/health

## Local development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start Postgres + Redis (Docker)
docker compose up postgres redis -d

alembic upgrade head
uvicorn src.main:app --reload
celery -A src.queue.worker_config.celery_app worker --loglevel=info
```

## Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## API overview

Assignment paths are available both under `/api/v1` and as aliases without the prefix:

| Method | Path |
|--------|------|
| POST | `/api/v1/notifications` or `/notifications` |
| GET | `/api/v1/notifications/{id}` or `/notifications/{id}` |
| GET | `/api/v1/users/{userId}/notifications` |
| POST | `/api/v1/users/{userId}/preferences` |
| GET | `/api/v1/users/{userId}/preferences` |

Extra: template CRUD under `/api/v1/templates`.

### Example

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "11111111-1111-1111-1111-111111111111",
    "channel": "email",
    "recipient": "user@example.com",
    "priority": "high",
    "subject": "Shipped",
    "body": "Your order has shipped.",
    "idempotency_key": "order-1"
  }'
```

## Assumptions

- Authentication is handled by an upstream gateway (not implemented here).
- Only `user_id` is stored; user profiles live elsewhere.
- Email/SMS/Push providers are mocked (configurable failure rate).
- Default preference is opt-in for all channels until explicitly disabled.
- Rate limit is 100 notifications/hour per user per channel (critical gets a small burst).

## Project layout

See [DESIGN.md](DESIGN.md) for architecture, schema, failure handling, and trade-offs. Additional docs live in `docs/`.

## License

MIT — see [LICENSE](LICENSE).
