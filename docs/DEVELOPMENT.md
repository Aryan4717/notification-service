# Development

## Setup

```bash
python -m venv .venv
pip install -r requirements.txt
pre-commit install
```

## Quality

```bash
black src/ tests/
flake8 src/ tests/ --max-line-length=100
mypy src/ --ignore-missing-imports
pytest tests/ -v --cov=src
```

## Adding a channel

1. Implement `AbstractChannelAdapter` in `src/channels/`
2. Add a mock provider under `src/infrastructure/`
3. Register in `ChannelAdapterFactory`
4. Extend `Channel` enum and migration if needed
5. Add unit tests

## Migrations

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```
