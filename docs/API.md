# API Reference

Interactive docs: `http://localhost:8000/docs` (OpenAPI 3 via FastAPI).

Base URL: `http://localhost:8000`

Versioned prefix: `/api/v1` (assignment aliases without prefix are also registered for notifications/preferences).

## Error format

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded for user",
  "details": {},
  "request_id": "uuid",
  "timestamp": "2026-01-01T00:00:00+00:00"
}
```

## Endpoints

### POST /api/v1/notifications

Create and enqueue a notification.

### GET /api/v1/notifications/{id}

Fetch status and delivery logs.

### GET /api/v1/users/{userId}/notifications

Paginated history (`limit`, `offset`, optional `status`, `priority`, `channel`).

### POST /api/v1/users/{userId}/preferences

Set `{ "channel": "email|sms|push", "enabled": true|false }`.

### GET /api/v1/users/{userId}/preferences

Returns map of channel → enabled.

### Templates

- `POST /api/v1/templates`
- `GET /api/v1/templates`
- `GET /api/v1/templates/{id}`
- `PUT /api/v1/templates/{id}`
