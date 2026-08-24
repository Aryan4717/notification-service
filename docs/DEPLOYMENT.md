# Deployment

## Prerequisites

- Docker and Docker Compose

## Run

```bash
cp .env.example .env
docker compose up --build -d
```

## Services

| Service | Port |
|---------|------|
| web (API) | 8000 |
| postgres | 5432 |
| redis | 6379 |
| flower | 5555 |

Entrypoint waits for Postgres and runs `alembic upgrade head` (falls back to `init_db()`).

## Scaling workers

```bash
docker compose up --scale celery_worker=3
```

## Health

- Liveness: `GET /health/live`
- Readiness: `GET /health/ready`
