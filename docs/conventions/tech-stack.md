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
| Database | PostgreSQL 16 + pgvector + Apache AGE + pg_trgm | TBD (ADR-005) |
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
- Database: PostgreSQL 16 (extensions TBD via ADR-005)
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
- **PostgreSQL with extensions (not separate stores):** Single source of truth, simpler ops, pgvector + AGE cover vector + graph use cases without adding Qdrant/Neo4j

## References

- ADR-001 — LLM model baseline
- ADR-002 — Network topology (where MS-S1 MAX fits)
- ADR-003 — Service port strategy
- ADR-005 (TBD) — Custom Postgres image with extensions

## Related

- `CLAUDE.md` §3 — Architecture mental model
- `docs/conventions/code-style.md` — Code style for Python stack
