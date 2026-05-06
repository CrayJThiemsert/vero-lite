# PLAN-001: Starter Pack Scaffold for vero-lite

**Status:** Ready for execution (Amended Phase E — see note below)
**Owner:** Claude Code (after human approval)
**Created:** 2026-05-05 (Session 2)
**Amended:** 2026-05-06 (Session 3 mid-execution + Session 4 finalization)
**Related ADRs:** ADR-001 (LLM models), ADR-002 (Network topology), ADR-003 (Service port strategy)

> **📝 Amendment Note (Phase E):** ADR-003 was originally reserved for "custom Postgres image" but Phase E execution discovered a port conflict with the co-existing smb-flow project (which uses 5432-5435 + 8000 + 5050 + 5678 + 5679 + 8501). ADR-003 was emergency-minted for **Service port strategy** (env-overridable host ports for multi-project coexistence on Cray-Legion5Pro). The original "custom Postgres image" plan is renumbered to **ADR-005** (ADR-004 reserved for canonical email decision). See `docs/adr/0003-*.md` and the forward references later in this document.

---

## Goal

Create the initial repository scaffold for **vero-lite** — a "Palantir-lite" data platform for Thai SMB market, starting with vet clinic vertical. The first commit must produce a **verified-working baseline**: clone → `uv sync` → `docker compose up` → `curl localhost:8000/health` returns 200.

## Acceptance Criteria

- [ ] Repository exists at `~/work/vero-lite` (WSL native path: `/home/crayj/work/vero-lite`)
- [ ] Git repository initialized with `main` branch
- [ ] All files committed with conventional commit messages
- [ ] Pushed to `https://github.com/CrayJThiemsert/vero-lite` (Public)
- [ ] `uv sync` completes without errors
- [ ] `docker compose up -d` starts Postgres + Redis successfully
- [ ] `uv run uvicorn services.api.main:app --reload` starts FastAPI on port 8000
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok","timestamp":"..."}`
- [ ] `uv run pytest` runs test_health.py and passes
- [ ] `pre-commit run --all-files` passes (or only fails on intentional placeholders)
- [ ] `detect-secrets scan` completes with no real secrets found

## Out of Scope (Explicitly NOT in this plan)

- ❌ Real ontology files (only `ontology/.gitkeep` + `ontology/README.md` placeholder)
- ❌ Real Pydantic models (only stub for health check)
- ❌ Database migrations (Alembic config exists but no migrations yet)
- ❌ Frontend templates (HTMX/Jinja2 — defer to PLAN-002)
- ❌ MCP server implementation (defer to PLAN-003)
- ❌ CI/CD workflow files (defer — need self-hosted runner ready first)
- ❌ Code generation pipeline (the "moat" — defer to PLAN-004)

## Decision Context

| Decision | Choice | Rationale |
|---|---|---|
| Repo path | `~/work/vero-lite` | WSL native = 5-20x faster than `/mnt/d/...` |
| Visibility | Public | Per handoff doc; secret scanning enforced via pre-commit |
| Scaffold level | Full + Hello World | Verified-working baseline; reduces token waste in future sessions |
| Package manager | `uv` | Per handoff doc; faster than pip, lock file native |
| Python version | 3.12+ | Per handoff doc |
| License | Apache 2.0 | Per handoff doc |

---

## Directory Structure (Final)

```
vero-lite/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── .vscode/
│   └── settings.json                    # Python interpreter, ruff, formatter
├── docs/
│   ├── adr/                             # Architecture Decision Records
│   │   ├── 0000-template.md
│   │   ├── 0001-llm-model-baseline.md
│   │   └── 0002-network-topology.md
│   ├── plans/                           # Execution plans
│   │   ├── 0000-template.md
│   │   ├── done/
│   │   │   └── PLAN-001-starter-pack-scaffold.md  # this file, moved here
│   │   └── README.md
│   └── for_llm/                         # Curated context for LLM sessions
│       └── README.md
├── ontology/                            # YAML ontology (the moat) — empty for now
│   ├── .gitkeep
│   └── README.md                        # explains future structure
├── services/
│   └── api/
│       ├── __init__.py
│       ├── main.py                      # FastAPI app, /health endpoint
│       ├── config.py                    # Pydantic Settings (env vars)
│       └── models/
│           ├── __init__.py
│           └── health.py                # HealthResponse model
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # pytest fixtures
│   └── test_health.py                   # smoke test for /health
├── scripts/
│   └── bootstrap.sh                     # one-time setup helper
├── .env.example                         # template for .env (no secrets)
├── .gitignore
├── .pre-commit-config.yaml
├── .secrets.baseline                    # detect-secrets baseline
├── .python-version                      # 3.12
├── CLAUDE.md                            # constitution / project rules
├── docker-compose.yml                   # Postgres 16 + Redis 7
├── Dockerfile                           # Python 3.12 + uv + app
├── LICENSE                              # Apache 2.0
├── pyproject.toml                       # uv-managed, dependencies + tool config
├── README.md                            # project overview, getting started
└── uv.lock                              # generated by uv
```

---

## File Specifications

### 1. `README.md`

Sections required:
- Project name + tagline ("Palantir-lite for Thai SMB, starting with vet clinics")
- License badge (Apache 2.0)
- Status: "Pre-alpha (Session 2)"
- Architecture overview (3-layer ontology engine — copy from handoff)
- Tech stack table
- Getting started (prerequisites + quick start)
- Project structure (link to docs/)
- Contributing (link to CLAUDE.md)
- License notice

Quick start commands (must work as-is):
```bash
git clone https://github.com/CrayJThiemsert/vero-lite.git
cd vero-lite
cp .env.example .env
docker compose up -d
uv sync
uv run uvicorn services.api.main:app --reload
# open http://localhost:8000/health
```

### 2. `CLAUDE.md` (Constitution)

This file is read by Claude Code at the start of every session. Must contain:

**Project context:**
- Codename, vision, founder, strategy (from handoff)
- Current phase: "Phase 1, Month 1, Session 2"

**Working patterns:**
- Conversation hygiene: Claude Chat (thinking) vs Claude Code (execution) vs Repository (shared memory)
- Decision flow: All decisions → ADR in `docs/adr/`
- Plan flow: All plans → `docs/plans/`, completed plans → `docs/plans/done/`
- Token economy rules

**Code style:**
- Python: ruff (line length 100), mypy strict, type hints mandatory
- Imports: isort via ruff
- Tests: pytest, marker `slow` for >1s tests
- Commits: conventional commits (feat:, fix:, docs:, refactor:, test:, chore:)
- Branch naming: `feat/`, `fix/`, `docs/`, `chore/`

**Constraints:**
- Public repo: NEVER commit `.env`, secrets, API keys
- Pre-commit hooks must pass before push
- All code must have type hints
- All endpoints must have Pydantic request/response models
- All ADRs must be merged before related implementation PR

**File reading priority for Claude Code:**
1. This file (CLAUDE.md)
2. `docs/adr/` (most recent first)
3. `docs/plans/` (active plans, then `done/`)
4. `pyproject.toml` (dependencies + tool config)
5. Existing code in `services/`

### 3. `LICENSE`

Standard Apache 2.0 license text.
Copyright holder: `Jirachai Thiemsert`
Year: `2026`

### 4. `pyproject.toml`

```toml
[project]
name = "vero-lite"
version = "0.1.0"
description = "Palantir-lite data platform for Thai SMB — vertical ontology engine"
authors = [{ name = "Jirachai Thiemsert", email = "<replace-with-real>" }]
license = { text = "Apache-2.0" }
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.9.0",
  "pydantic-settings>=2.5.0",
  "sqlalchemy>=2.0.35",
  "alembic>=1.13.0",
  "asyncpg>=0.29.0",
  "redis>=5.0.0",
  "celery>=5.4.0",
  "httpx>=0.27.0",
  "python-dotenv>=1.0.0",
  "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "pytest-asyncio>=0.24.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.6.0",
  "mypy>=1.11.0",
  "pre-commit>=3.8.0",
  "detect-secrets>=1.5.0",
  "ipython>=8.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = []  # use [project.optional-dependencies].dev instead

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
  "E", "F", "W",      # pycodestyle + pyflakes
  "I",                # isort
  "B",                # bugbear
  "UP",               # pyupgrade
  "RUF",              # ruff-specific
  "C90",              # mccabe complexity
  "N",                # pep8-naming
  "S",                # bandit (security)
]
ignore = [
  "S101",             # asserts ok in tests
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105", "S106"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
  "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]

[tool.coverage.run]
source = ["services"]
omit = ["tests/*", "**/__init__.py"]

[tool.coverage.report]
show_missing = true
fail_under = 70
```

### 5. `services/api/main.py`

```python
"""FastAPI entry point for vero-lite."""
from datetime import datetime, timezone
from fastapi import FastAPI
from services.api.models.health import HealthResponse

app = FastAPI(
    title="vero-lite",
    description="Palantir-lite data platform — vertical ontology engine",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse, tags=["infrastructure"])
async def health() -> HealthResponse:
    """Liveness probe endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
    )
```

### 6. `services/api/models/health.py`

```python
"""Health check response model."""
from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="Service status (ok / degraded / down)")
    timestamp: datetime = Field(..., description="Server time at response (UTC)")
    version: str = Field(..., description="Application version")
```

### 7. `services/api/config.py`

```python
"""Application configuration via environment variables."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://vero:vero@localhost:5432/vero_lite",
        description="PostgreSQL connection string (asyncpg driver)",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for Celery broker + cache",
    )

    # LLM
    ollama_host: str = Field(
        default="http://ms-s1-max:11434",
        description="Ollama API endpoint (use http://localhost:11434 for local dev)",
    )
    ollama_default_model: str = Field(
        default="gemma4:26b",
        description="Default LLM model (see ADR-001)",
    )

    # App
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")


settings = Settings()
```

### 8. `tests/test_health.py`

```python
"""Smoke test for /health endpoint."""
import pytest
from httpx import ASGITransport, AsyncClient
from services.api.main import app


@pytest.mark.asyncio
async def test_health_returns_200() -> None:
    """GET /health must return 200 with valid HealthResponse."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"
```

### 9. `tests/conftest.py`

```python
"""Shared pytest fixtures."""
# Empty for now — fixtures added as needed
```

### 10. `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: vero-postgres
    environment:
      POSTGRES_USER: vero
      POSTGRES_PASSWORD: vero
      POSTGRES_DB: vero_lite
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vero -d vero_lite"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: vero-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

> **NOTE:** pgvector + Apache AGE + pg_trgm extensions will be added in PLAN-002 (database setup).
> The base `postgres:16-alpine` image is used for now to keep scaffold simple.
> An **ADR-005** will document the eventual switch to a custom Postgres image
> (originally planned as ADR-003 — see Amendment Note in the header above).

### 11. `Dockerfile`

```dockerfile
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY services/ ./services/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 12. `.env.example`

```dotenv
# Database
DATABASE_URL=postgresql+asyncpg://vero:vero@localhost:5432/vero_lite

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM (Ollama on MS-S1 MAX)
OLLAMA_HOST=http://ms-s1-max:11434
OLLAMA_DEFAULT_MODEL=gemma4:26b

# App
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 13. `.gitignore`

Standard Python + Node + IDE + OS gitignore. Must include:
```
# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/

# uv
.uv-cache/

# Environment
.env
.env.*
!.env.example

# IDE
.vscode/*
!.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Project-specific
*.log
local/
scratch/

# Docker
.docker/
```

### 14. `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.9.0
          - pydantic-settings>=2.5.0
        args: [--config-file=pyproject.toml]
        files: ^services/

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json
```

### 15. `scripts/bootstrap.sh`

```bash
#!/usr/bin/env bash
# bootstrap.sh — one-time setup for vero-lite dev environment
set -euo pipefail

echo "=== vero-lite bootstrap ==="

# 1. Verify prerequisites
command -v uv >/dev/null || { echo "❌ uv not installed. See https://docs.astral.sh/uv/"; exit 1; }
command -v docker >/dev/null || { echo "❌ docker not installed"; exit 1; }
command -v git >/dev/null || { echo "❌ git not installed"; exit 1; }

# 2. Copy .env if missing
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "✅ Created .env from .env.example"
fi

# 3. Sync Python dependencies
echo "→ Running uv sync..."
uv sync

# 4. Install pre-commit hooks
echo "→ Installing pre-commit hooks..."
uv run pre-commit install

# 5. Initialize detect-secrets baseline
if [[ ! -f .secrets.baseline ]]; then
  echo "→ Creating detect-secrets baseline..."
  uv run detect-secrets scan > .secrets.baseline
fi

# 6. Start Docker services
echo "→ Starting Docker services..."
docker compose up -d

# 7. Wait for Postgres
echo "→ Waiting for Postgres to be ready..."
until docker compose exec -T postgres pg_isready -U vero >/dev/null 2>&1; do
  sleep 1
done
echo "✅ Postgres ready"

# 8. Smoke test
echo "→ Running smoke test..."
uv run pytest tests/test_health.py -v

echo ""
echo "=== Bootstrap complete ==="
echo "Start the API with: uv run uvicorn services.api.main:app --reload"
echo "Then visit:         http://localhost:8000/health"
```

### 16. ADR template (`docs/adr/0000-template.md`)

```markdown
# ADR-NNNN: <Decision Title>

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
**Date:** YYYY-MM-DD
**Deciders:** <names>
**Related:** <links to other ADRs, plans, issues>

## Context

What is the situation? What forces are at play?

## Decision

What did we decide?

## Consequences

### Positive
-

### Negative
-

### Neutral
-

## Alternatives Considered

### Alternative 1: <Name>
- Pros: ...
- Cons: ...
- Why rejected: ...

## References
-
```

### 17. Plan template (`docs/plans/0000-template.md`)

```markdown
# PLAN-NNNN: <Plan Title>

**Status:** Draft | Ready for execution | In progress | Complete
**Owner:** <Claude Code | human | both>
**Created:** YYYY-MM-DD
**Related ADRs:** ADR-XXXX

## Goal

One-paragraph statement of what this plan accomplishes.

## Acceptance Criteria

- [ ] ...

## Out of Scope

- ❌ ...

## Steps

### Step 1: <name>
...

## Verification

How do we know it worked?
```

### 18. ADR-001, ADR-002, and ADR-003

**See separate files** — copied verbatim into `docs/adr/`.

- ADR-001: LLM model baseline (gemma4:26b general, qwen2.5-coder:32b code)
- ADR-002: Network topology (Cray ↔ MS-S1 MAX, Tailscale)
- ADR-003: Service port strategy (env-overridable for multi-project coexistence)

---

## Execution Steps for Claude Code

### Phase A: Initialize repository structure

```bash
# Create directory and cd
mkdir -p ~/work/vero-lite
cd ~/work/vero-lite

# Initialize git
git init -b main
git config user.name "Jirachai Thiemsert"
git config user.email "<replace-with-real>"

# Create directory structure
mkdir -p .github/ISSUE_TEMPLATE .vscode \
         docs/adr docs/plans/done docs/for_llm \
         ontology services/api/models tests scripts
```

### Phase B: Create all files

Create each file from the specifications above. Use `cat > path <<'EOF'` heredocs for clarity, or individual write tool calls.

### Phase C: Initialize Python environment

```bash
echo "3.12" > .python-version

# Create pyproject.toml first (see spec above)
# Then:
uv sync
```

### Phase D: Install pre-commit + detect-secrets baseline

```bash
uv run pre-commit install
uv run detect-secrets scan > .secrets.baseline
```

### Phase E: Smoke test

```bash
# Start services
docker compose up -d
sleep 5  # let Postgres warm up

# Run tests
uv run pytest tests/ -v

# Manual verify
uv run uvicorn services.api.main:app --reload &
SERVER_PID=$!
sleep 3
curl -s http://localhost:8000/health | python3 -m json.tool
kill $SERVER_PID

# Stop services (optional)
docker compose down
```

### Phase F: Commit and push

```bash
# Stage and commit
git add .
git status  # human review checkpoint

# First commit: structure only
git commit -m "chore: initial scaffold for vero-lite

- Repository structure (services/, ontology/, docs/, tests/)
- Python 3.12 + uv + FastAPI + Pydantic v2
- Docker Compose: Postgres 16 + Redis 7
- Pre-commit: ruff + mypy + detect-secrets
- /health endpoint with smoke test
- ADR-001 (LLM model baseline)
- ADR-002 (Network topology)
- ADR-003 (Service port strategy — env-overridable host ports for
  multi-project coexistence; resolves Phase E port conflicts
  with smb-dev-postgres / smb-dev-whisper)
- CLAUDE.md constitution

Refs: PLAN-001"

# Move PLAN-001 to done/ (it's executed now)
git mv docs/plans/PLAN-001-starter-pack-scaffold.md docs/plans/done/
git commit -m "docs: move PLAN-001 to done/ after execution"

# Create GitHub repo
gh auth status  # verify logged in
gh repo create CrayJThiemsert/vero-lite \
  --public \
  --description "Palantir-lite data platform for Thai SMB — vertical ontology engine" \
  --source=. \
  --remote=origin \
  --push
```

### Phase G: Verify on GitHub

- [ ] Repo is public at `https://github.com/CrayJThiemsert/vero-lite`
- [ ] README renders correctly
- [ ] LICENSE detected by GitHub (shows "Apache-2.0" badge)
- [ ] Initial commit shows all files

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `uv` not installed on Cray WSL | Step bootstrap.sh fails fast with clear message + link |
| Postgres port 5432 conflict (with smb-flow) | RESOLVED Phase E — env-overridable host ports per ADR-003; vero-lite uses 5436 by default to avoid conflict with smb-dev-postgres |
| `gh` CLI not authenticated | Step E checks `gh auth status` first |
| Pre-commit hooks fail on first commit | Use `--no-verify` for initial commit only, fix issues in next commit |
| Email used in pyproject.toml | RESOLVED — GitHub no-reply alias `16893502+CrayJThiemsert@users.noreply.github.com` used as interim canonical for public repo; ADR-004 will formally adopt this convention |

## Verification After Execution

Run these commands from `~/work/vero-lite` and confirm all succeed:

```bash
# 1. Repo state
git log --oneline                     # should show 2 commits
git remote -v                         # should show origin -> github.com/CrayJThiemsert/vero-lite

# 2. Python env
uv run python --version               # 3.12.x
uv run python -c "import fastapi; print(fastapi.__version__)"

# 3. Docker services
docker compose ps                     # postgres + redis both "healthy"

# 4. API smoke test
uv run uvicorn services.api.main:app &
sleep 2
curl -s http://localhost:8000/health
kill %1

# 5. Tests
uv run pytest tests/ -v

# 6. Lint + types
uv run ruff check .
uv run mypy services/

# 7. Pre-commit
uv run pre-commit run --all-files
```

If any step fails, open a NEW plan (PLAN-002) to address — do not modify PLAN-001 retroactively.

---

## Handoff Note for Next Session

After PLAN-001 executes successfully:
1. Update CLAUDE.md current phase: "Phase 1, Month 1, Session 3"
2. Open PLAN-002 for next priority (likely: pgvector + AGE + first ontology YAML)
3. Decide: self-hosted GitHub Actions runner setup (separate plan) or feature work first
