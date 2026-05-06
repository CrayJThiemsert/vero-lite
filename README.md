# vero-lite

> Palantir-lite for Thai SMB, starting with vet clinics.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![Status: Pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange)

**Status:** Pre-alpha (Session 2 / Phase 1, Month 1)

vero-lite is a vertical ontology engine — a small "Palantir-lite" platform aimed at the Thai SMB market (10–100 employees). The first vertical is veterinary clinics: digitize handwritten medical records and provide AI-assisted workflows. Future verticals: pharmacy, dental, agro-trade.

---

## Architecture (3-layer ontology engine)

1. **Mapping layer** — dbt / SQLMesh translates raw sources → canonical records
2. **Semantic layer (the moat)** — YAML ontology = single source of truth.
   Generates: Pydantic models, SQL DDL, JSON Schema, MCP tools, TypeScript types
3. **Action layer** — FastAPI functions tied to objects with permissions + audit trail

See [`CLAUDE.md`](CLAUDE.md) for the full project constitution and [`docs/adr/`](docs/adr/) for architecture decisions.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| Validation | Pydantic v2 |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic |
| Database | PostgreSQL 16 (+ pgvector + Apache AGE + pg_trgm — PLAN-002) |
| Background jobs | Celery + Redis |
| LLM (local) | Ollama on MS-S1 MAX (see ADR-001, ADR-002) |
| LLM (fallback) | Anthropic Claude API |
| Agent orchestration | LangGraph |
| Code-agent integration | MCP server |
| Package manager | uv |
| Quality | ruff, mypy, pytest, pre-commit, detect-secrets |
| Container | Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker + Docker Compose
- `gh` CLI (optional, for repo workflow)

### Quick start

```bash
git clone https://github.com/CrayJThiemsert/vero-lite.git
cd vero-lite
cp .env.example .env
docker compose up -d
uv sync --extra dev
uv run uvicorn services.api.main:app --reload
# open http://localhost:8000/health
```

Or run the bootstrap script:

```bash
bash scripts/bootstrap.sh
```

### Smoke test

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
# {"status": "ok", "timestamp": "2026-...", "version": "0.1.0"}

uv run pytest -v
```

---

## Project Structure

```
vero-lite/
├── docs/
│   ├── adr/             # Architecture Decision Records
│   ├── plans/           # Execution plans (active + done/)
│   └── for_llm/         # Curated context for LLM sessions
├── ontology/            # YAML ontology — the moat (PLAN-002+)
├── services/
│   └── api/             # FastAPI app (Pydantic v2)
├── tests/               # pytest
└── scripts/             # bootstrap.sh, ops helpers
```

See [`docs/`](docs/) for the full picture.

---

## Contributing

Read [`CLAUDE.md`](CLAUDE.md) first — it is the project constitution. In short:

- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, ...)
- Branch from `main`, PR back to `main`
- All ADRs are merged **before** related implementation PRs
- All endpoints get Pydantic request + response models
- `ruff check . && mypy services/ && pytest` must pass before push
- Pre-commit hooks (ruff, mypy, detect-secrets) must pass — do **not** bypass with `--no-verify`

---

## License

Apache 2.0 — see [`LICENSE`](LICENSE).

Copyright (c) 2026 Jirachai Thiemsert.
