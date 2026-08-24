# Architecture

See root [DESIGN.md](../DESIGN.md) for the primary design write-up.

## Layers

- `src/api` — HTTP surface, middleware, dependencies
- `src/services` — orchestration and policies
- `src/domain` — pure business types
- `src/repositories` — persistence
- `src/channels` — adapter pattern for providers
- `src/queue` — Celery tasks and producer
- `src/infrastructure` — Redis, circuit breaker, mocks
- `src/observability` — logs, metrics, health
