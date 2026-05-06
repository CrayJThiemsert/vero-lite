#!/usr/bin/env bash
# bootstrap.sh — one-time setup for vero-lite dev environment
set -euo pipefail

echo "=== vero-lite bootstrap ==="

# 1. Verify prerequisites
command -v uv >/dev/null || { echo "X uv not installed. See https://docs.astral.sh/uv/"; exit 1; }
command -v docker >/dev/null || { echo "X docker not installed"; exit 1; }
command -v git >/dev/null || { echo "X git not installed"; exit 1; }

# 2. Copy .env if missing
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "OK Created .env from .env.example"
fi

# 3. Sync Python dependencies
echo "-> Running uv sync..."
uv sync --extra dev

# 4. Install pre-commit hooks
echo "-> Installing pre-commit hooks..."
uv run pre-commit install

# 5. Initialize detect-secrets baseline
if [[ ! -f .secrets.baseline ]]; then
  echo "-> Creating detect-secrets baseline..."
  uv run detect-secrets scan > .secrets.baseline
fi

# 6. Start Docker services
echo "-> Starting Docker services..."
docker compose up -d

# 7. Wait for Postgres
echo "-> Waiting for Postgres to be ready..."
until docker compose exec -T postgres pg_isready -U vero >/dev/null 2>&1; do
  sleep 1
done
echo "OK Postgres ready"

# 8. Smoke test
echo "-> Running smoke test..."
uv run pytest tests/test_health.py -v

echo ""
echo "=== Bootstrap complete ==="
echo "Start the API with: uv run uvicorn services.api.main:app --reload"
echo "Then visit:         http://localhost:8000/health"
