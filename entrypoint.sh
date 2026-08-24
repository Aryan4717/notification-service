#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
retries=30
until python -c "import sqlalchemy; from src.config import get_settings; e=sqlalchemy.create_engine(get_settings().database_url); e.connect().close()" 2>/dev/null; do
  retries=$((retries-1))
  if [ "$retries" -le 0 ]; then
    echo "PostgreSQL not ready"
    exit 1
  fi
  sleep 2
done

echo "Running migrations..."
alembic upgrade head || python -c "from src.database.connection import init_db; init_db()"

echo "Starting: $@"
exec "$@"
