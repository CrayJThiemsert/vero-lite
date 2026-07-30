# Tech Stack

> Locked technology choices for vero-lite.
> Changes require ADR.

---

## Core Stack

| Layer | Choice | ADR |
|-------|--------|-----|
| Language | Python 3.12+ | — |
| Web framework | FastAPI | — |
| Validation | Pydantic v2 | — |
| ORM | SQLAlchemy 2.0 (async) | — |
| Migrations | Alembic | — |
| Background jobs | Celery + Redis | — |
| Database | PostgreSQL 16 (stock image, no extensions) | — |
| Frontend (Phase 1) | FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind | — |
| Frontend (Phase 2, m7+) | Next.js for complex pages | — |
| LLM (local) | Ollama on MS-S1 MAX | ADR-001 |
| LLM (cloud fallback) | Anthropic Claude API | ADR-001 |
| Agent orchestration | LangGraph | — |
| Code agent integration | MCP server | — |
| Package manager | uv (Python), pnpm (Node) | — |
| Quality | ruff, mypy, pytest, pre-commit, detect-secrets | — |
| Container | Docker + Docker Compose | — |
| CI/CD | GitHub Actions + self-hosted runner on MS-S1 MAX | — |

## Locked vs. Open

**Locked** (changes require ADR):
- Language: Python 3.12+
- Web framework: FastAPI
- Validation: Pydantic v2
- Database: PostgreSQL 16, stock `postgres:16-alpine` (extensions are an OPEN question — no ADR drafted)
- Local LLM: Ollama on MS-S1 MAX (per ADR-001)

**Open** (subject to revision before Phase 2):
- Frontend Phase 2 framework (Next.js tentative)
- Specific orchestration patterns within LangGraph
- CI/CD specifics beyond "GitHub Actions + self-hosted runner"

## Why These Choices

Brief rationale for non-obvious picks (full reasoning in ADRs where they exist):

- **uv over pip/poetry:** Speed, lockfile reliability, single binary
- **Pydantic v2 over v1:** Performance, stricter validation, better error messages
- **Async SQLAlchemy:** I/O-bound workload (DB + LLM calls), concurrency without threads
- **HTMX + Alpine over React (Phase 1):** Lower complexity, faster iteration with one developer, Server-Side Rendering by default
- **PostgreSQL as the single store — extensions are a CANDIDATE, not a shipped choice:** the preference, if semantic or graph features are ever needed, is to reach for pgvector + AGE inside Postgres rather than add Qdrant/Neo4j — one source of truth, simpler ops. **None of those extensions is installed today** (`docker-compose.yml` runs stock `postgres:16-alpine`, and a repo-wide grep for `pgvector` / `pg_trgm` / `CREATE EXTENSION` / `cypher` returns zero hits under `services/`, `verticals/`, `tests/`, `alembic/`). Adopting them needs a fresh ADR **and** a PLAN; neither is drafted.

## References

- ADR-001 — LLM model baseline
- ADR-002 — Network topology (where MS-S1 MAX fits)
- ADR-003 — Service port strategy
- ADR-005 — Strategic pivot to OCT *(NOT the Postgres-image decision: this file previously cited ADR-005 for a custom Postgres image, and that number was already taken by an unrelated accepted ADR. The extensions decision has **no** ADR number reserved — see `docs/STATUS.md` Active TODOs.)*

## Related

- `CLAUDE.md` §3 — Architecture mental model
- `docs/conventions/code-style.md` — Code style for Python stack
