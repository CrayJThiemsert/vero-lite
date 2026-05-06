# CLAUDE.md — vero-lite Project Constitution

> This file is read by Claude Code at the start of **every** session.
> It defines project context, working patterns, and constraints.
> If anything here conflicts with a more recent ADR, the ADR wins — update this file accordingly.

---

## Project Identity

- **Codename:** vero-lite (Vertical Ontology, Lite Edition)
- **Vision:** Palantir-like data platform (AIP + Foundry + Apollo style) for Thai SMB market (10–100 employees)
- **First vertical:** Veterinary clinics (digitize handwritten medical records → AI-assisted workflows)
- **Founder:** Jirachai Thiemsert (solo developer, GitHub: `CrayJThiemsert`)
- **License:** Apache 2.0
- **Repository:** https://github.com/CrayJThiemsert/vero-lite (Public)
- **Strategy:** Build the moat first (YAML ontology + code generator) → 2–3 design partners → revenue. Technical excellence as defensibility before competitors enter the Thai SMB market.

## Current Phase

**Phase 1, Month 1, Session 3+** (post starter-pack scaffold)

Active priorities:
1. Find 2–3 vet clinic design partners by month 3
2. Build YAML ontology + code generator (the moat)
3. Demo 5: 30-second onboarding (drop CSV → schema detected → answers in <30s)

## Architecture

Three-layer ontology engine:

1. **Mapping layer** — dbt/SQLMesh translates raw sources → canonical records
2. **Semantic layer** (the moat) — YAML ontology = single source of truth
   - Generates: Pydantic models, SQL DDL, JSON Schema, MCP tools, TypeScript types
3. **Action layer** — FastAPI functions tied to objects with permissions + audit trail

## Tech Stack (Locked)

| Layer | Choice | ADR |
|---|---|---|
| Language | Python 3.12+ | — |
| Web framework | FastAPI | — |
| Validation | Pydantic v2 | — |
| ORM | SQLAlchemy 2.0 (async) | — |
| Migrations | Alembic | — |
| Background jobs | Celery + Redis | — |
| Database | PostgreSQL 16 + pgvector + Apache AGE + pg_trgm | TBD |
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

## Hardware

- **Cray-Legion5Pro** — Dev machine. Windows 11 + WSL2 Ubuntu 24.04. Path: `~/work/vero-lite`.
- **MS-S1 MAX** — LLM server. AMD Ryzen AI Max+ 395, 128GB unified memory (~64GB as VRAM), 2TB SSD. LAN IP: `192.168.1.133`. Hostname: `ms-s1-max` (via `/etc/hosts`). See ADR-002.

---

## Working Patterns

### Conversation Hygiene (CRITICAL)

Three roles, each with one job:

| Role | Purpose | Output |
|---|---|---|
| **Claude Chat** (claude.ai) | Thinking partner, architecture decisions, ADR drafts | Markdown drafts pasted into repo |
| **Claude Code** (in repo) | Execution agent, implementation, refactoring | Code commits |
| **Repository** | Shared memory between sessions | ADRs, plans, code |

**Rule:** Never copy-paste long context between Claude Chat and Claude Code. Use the repository.

### Decision Flow

1. New decision needed → discuss in Claude Chat
2. Draft ADR in `docs/adr/NNNN-name.md` (use `0000-template.md`)
3. Status: `Proposed` → `Accepted` after acceptance
4. Implementation PRs reference the ADR number in commits

### Plan Flow

1. New work needed → write a PLAN in `docs/plans/NNNN-name.md` (use `0000-template.md`)
2. Plan must include: Goal, Acceptance Criteria, Out of Scope, Steps
3. Claude Code executes plan in feature branch
4. After completion, `git mv docs/plans/NNNN-*.md docs/plans/done/`

### Token Economy

- **Detailed plans BEFORE implementation = 3–10x token savings.**
- Each Claude Code session needs: clear plan + ADR refs + acceptance criteria + out-of-scope explicit.
- Long context dumps in Claude Chat → ALWAYS persist to repo as ADR or plan.

### Multi-Project Coexistence (per ADR-003)

- All host ports in `docker-compose.yml` use `${VAR:-default}` fallback pattern
- `.env.example` uses vendor defaults (5432, 6379, 8000)
- Local `.env` overrides per-machine ports to avoid conflicts
- `DATABASE_URL` / `REDIS_URL` must always match `*_HOST_PORT`
- vero-lite never demands exclusive ownership of vendor-default ports

---

## Code Style

### Python

- **Line length:** 100
- **Type hints:** Mandatory on all functions, methods, class attributes
- **Imports:** Sorted via ruff (isort)
- **Docstrings:** Required on public modules, classes, and functions
- **Async:** Default for I/O-bound code (DB, HTTP, LLM calls)

### Tooling

- `ruff check .` and `ruff format .` — must pass
- `mypy services/` — must pass (strict mode in pyproject.toml)
- `pytest` — all tests must pass; coverage threshold 70%
- `pre-commit run --all-files` — must pass before push

### Pydantic

- All API request/response models extend `BaseModel`
- Use `Field(...)` with `description` for all fields
- Use `model_config = ConfigDict(...)` for v2 settings

---

## Git Conventions

### Commits (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`

Examples:
```
feat(api): add /clinic/patients endpoint
fix(ontology): correct ISO 8601 datetime parsing
docs(adr): add ADR-003 for pgvector
chore(deps): bump fastapi to 0.115.5
```

### Branches

- `main` — protected, deploy-ready
- `feat/<short-name>` — features
- `fix/<short-name>` — bug fixes
- `docs/<short-name>` — documentation only
- `chore/<short-name>` — tooling, deps

### Pull Requests

- Reference plan + ADRs in description
- Acceptance criteria checked off
- All CI green before merge

---

## Constraints (DO NOT VIOLATE)

### Public Repository

- **NEVER** commit `.env`, `.env.local`, `.env.production`, or any file with secrets.
- **NEVER** commit API keys, tokens, passwords, connection strings with credentials.
- `.env.example` is the only `.env*` file allowed in git.
- `pre-commit` runs `detect-secrets` against `.secrets.baseline` — do not bypass with `--no-verify`.

### Code Quality

- All new code: type hints + tests + ruff clean + mypy clean.
- All endpoints: Pydantic request + response models.
- All schemas: documented (Field descriptions).
- All ADRs: must be merged before related implementation PR.

### Compliance Forward-Looking

- **PDPA (Thailand Personal Data Protection Act)** compliance: assume all clinical data is PII. Build audit trails from day 1.
- **Data residency:** Local LLM on MS-S1 MAX is the default. Cloud LLM (Claude API) only with explicit user consent and only for non-PII workflows in Phase 1.
- **Medical liability:** All AI outputs are "assistive" — never auto-diagnostic. UI must show this disclaimer.

---

## File Reading Priority for Claude Code

When starting a new session, read in this order:

1. **`CLAUDE.md`** (this file) — always first
2. **`docs/adr/`** — read all, most recent first (highest number = most recent)
3. **`docs/plans/`** — active plans, then `done/` for context
4. **`pyproject.toml`** — current dependencies + tool config
5. **`docker-compose.yml`** — current services
6. **`services/api/main.py`** + related code — current API surface
7. **`tests/`** — current test coverage and patterns

---

## Active TODOs (replaced periodically)

- [ ] Decide canonical author email for `pyproject.toml` (currently the GitHub `users.noreply.github.com` alias — works but is a placeholder; ADR-004 TBD)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX (separate plan)
- [ ] Add pgvector + Apache AGE + pg_trgm extensions to Postgres image (ADR-004 + PLAN-002 TBD)
- [x] ADR-003: Service port strategy (env-overridable ports for multi-project coexistence)
- [ ] First ontology YAML: `vet_clinic_v0.yaml` covering Patient, Visit, Diagnosis (PLAN-002 TBD)
- [ ] Decide canonical project email + author identity (ADR-004 TBD)

---

## Glossary

| Term | Meaning |
|---|---|
| **Ontology** | YAML files defining canonical objects, properties, relationships, and actions for a vertical |
| **Vertical** | A specific domain (vet clinic, pharmacy, dental clinic) |
| **Generator** | Code that reads ontology YAML and emits Pydantic models, SQL DDL, MCP tools, TS types |
| **MCP** | Model Context Protocol — standard for exposing tools/resources to LLM agents |
| **HITL** | Human-In-The-Loop — required before destructive AI actions |
| **Lineage** | Track-back from any data point to its sources, transformations, and decisions |
| **Object Explorer** | Foundry-style UI for browsing/querying canonical objects |
| **Time travel** | Query the state of objects at a past point in time (audit trail core feature) |

---

## Contact / Escalation

- **GitHub:** https://github.com/CrayJThiemsert/vero-lite
- **Issues:** Use GitHub Issues with templates
- **Sensitive matters:** Direct to founder (private channel — not in repo)

---

*Last updated: 2026-05-05 (Session 2)*
