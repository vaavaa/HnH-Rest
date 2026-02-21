#!/usr/bin/env bash
# Run full test suite (requires uv and DB/Redis as per docker-compose or .env)
set -e
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then
  uv run pytest tests/ -v --tb=short
else
  python3 -m pytest tests/ -v --tb=short
fi
