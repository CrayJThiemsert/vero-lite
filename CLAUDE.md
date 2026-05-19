# CLAUDE.md — vero-lite Project Constitution

> Read by Claude Code at the start of **every** session.
> Constitution = stable rules. Volatile state lives in `docs/STATUS.md`.
> If anything here conflicts with a more recent ADR, the ADR wins — update this file accordingly.

---

## 1. Project Identity

- **Codename:** vero-lite (Vertical Ontology, Lite Edition)
- **Vision:** Palantir-like data platform (AIP + Foundry + Apollo style) for distributed asset operations across industries
- **Phase 1 vertical:** Operational Control Tower (OCT) — three vertical-agnostic features:
  1. Ontology-driven operational map
  2. Natural language operational query
  3. Anomaly detection + suggested action with reasoning trace

  First instantiated on a regional energy operator (primary design partner type); second on an industrial supply chain operator (secondary). See ADR-005.
- **Phase 2 vertical (parked):** Veterinary clinics (digitize handwritten medical records → AI-assisted workflows). Same engine, swap ontology + data adapter. Park decision: ADR-005. Architectural decisions in ADRs 001–004 remain valid.
- **Founder:** Jirachai Thiemsert (solo developer, GitHub: `CrayJThiemsert`)
- **License:** Apache 2.0
- **Repository:** https://github.com/CrayJThiemsert/vero-lite (Public)
- **Strategy:** Build the moat first (YAML ontology + code generator + 3 OCT features = vertical plugin architecture per ADR-006) → 2 enterprise design partners → revenue. Template-first multi-vertical (Rule of Three; abstraction extracted only after 3 working verticals).

### Precedence (when sources conflict)

When two governance sources appear to disagree, resolve in this order:

1. **Most recent accepted ADR** — architectural decisions are binding
2. **This file (`CLAUDE.md`)** — constitutional rules
3. **Tier instruction files** (`docs/conventions/{chat,cowork}_tab_instructions.md`) — tier-specific scope and behavior
4. **Lessons** (`docs/lessons/`) — advisory; promote to ADR if a lesson must be behavior-binding
5. **`docs/STATUS.md`** — state, not rules (never wins a rule conflict)

If a tier instruction conflicts with an accepted ADR, the tier instruction is stale — surface to Cray for update. If a lesson is being cited as behavior-binding without ADR backing, raise the question of whether it should be promoted.

## 2. Current Focus

→ See [`docs/STATUS.md`](docs/STATUS.md) for current state, in-flight work, and recent decisions.

## 3. Architecture Mental Model

Three-layer ontology engine:

1. **Mapping layer** — dbt/SQLMesh translates raw sources → canonical records
2. **Semantic layer** (the moat) — YAML ontology = single source of truth
   - Generates: Pydantic models, SQL DDL, JSON Schema, MCP tools, TypeScript types
3. **Action layer** — FastAPI functions tied to objects with permissions + audit trail

## 4. Memory Architecture

Hybrid model: Auto Memory (private) + Repository (shared, source of truth).

| Tier | Location | Scope | Examples |
|------|----------|-------|----------|
| **0** | `~/.claude/projects/.../memory/` | Private, NOT in repo | Auto Memory CLI v2.1.132 working notes |
| **1** | In repo (hot) | Read every session | `CLAUDE.md`, `docs/STATUS.md` |
| **2** | In repo (reference) | Lookup as needed | `docs/{adr,lessons,runbooks,conventions}/` including `docs/conventions/{chat,cowork}_tab_instructions.md` (canonical for Claude project tier instructions; sync target = Claude project UI) |
| **2.5** | In repo (derived) | Curated snippets for cold-start sessions | `docs/for_llm/` |
| **3** | In repo (archeology) | Historical record | `docs/plans/done/`, git history |

→ Full details: [`docs/runbooks/memory-architecture.md`](docs/runbooks/memory-architecture.md)

**Rule:** Repository = single source of truth. Auto Memory complements, never replaces. `for_llm/` snippets are derived — canonicals win on conflict. Tier instruction files in `docs/conventions/` are canonical; the Claude project UI Chat tab / Cowork tab "project instructions" field is a sync target that Cray re-pastes when canonical changes.

## 5. Hardware

- **Cray-Legion5Pro** — Dev. Win11 + WSL2 Ubuntu 24.04. Path: `~/work/vero-lite`.
- **MS-S1 MAX** — LLM server. AMD Ryzen AI Max+ 395, 128GB unified, 192.168.1.133. See ADR-002.

## 6. Working Patterns

### Conversation Hygiene (CRITICAL)

The project uses four collaboration tiers, each with a distinct artifact-ownership scope:

| Tier | Role | Purpose | Primary output |
|------|------|---------|----------------|
| **Tier 0** — Cowork | Research agent | External knowledge compilation, prior art, library scans | Research files in `docs/research/private/` + own closeout handoffs |
| **Tier 1** — Chat | Strategy + architecture | ADR drafts, PLAN drafts, code review, handoff drafting | Markdown content (paste-ready) and `chat-` prefixed handoffs |
| **Tier 2** — Code | Execution agent | Repo writes, git operations, implementation | Code commits, file modifications, `code-` prefixed handoffs |
| **Tier 3** — Cray | Final authority | Private knowledge, business judgment, routing between tiers | Decisions, dispatch |

Tier instruction files in `docs/conventions/chat_tab_instructions.md` and `docs/conventions/cowork_tab_instructions.md` define detailed read/write scopes, behavioral rules, and handoff conventions per tier. Tier 2 (Code) operational policy lives in §11 below.

**Rule:** Never copy-paste long context between Claude Chat and Claude Code. Use the repository as shared memory.

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

- Detailed plans BEFORE implementation = 3–10x token savings
- Long context dumps in Claude Chat → ALWAYS persist to repo as ADR or plan

### Multi-Project Coexistence (per ADR-003)

- Host ports in `docker-compose.yml` use `${VAR:-default}` fallback pattern
- `.env.example` uses vendor defaults; local `.env` overrides per-machine
- `DATABASE_URL` / `REDIS_URL` must always match `*_HOST_PORT`
- vero-lite never demands exclusive ownership of vendor-default ports

## 7. Git Conventions (compact)

**Format:** Conventional Commits — `<type>(<scope>): <subject>`
**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`
**Branches:** `main` (protected), `feat/*`, `fix/*`, `docs/*`, `chore/*`
**Author:** `Jirachai Thiemsert <16893502+CrayJThiemsert@users.noreply.github.com>`
**AI assistance:** Note in commit body — **NEVER** as `Co-Authored-By`
**Commit messages:** Write to file → `git commit -F`. Prefer Write tool against WSL UNC path (`\\wsl.localhost\Ubuntu-24.04\tmp\commit-message.txt`) over `wsl bash -c "cat <<'EOF'"` heredoc when message contains backticks, `$var`, or code blocks (per Lesson #4 prevention).

→ Full details: [`docs/conventions/git.md`](docs/conventions/git.md) *(future, see STATUS TODO)*

## 8. Constraints (DO NOT VIOLATE)

### Public Repository

- **NEVER** commit `.env`, `.env.local`, `.env.production`, or any file with secrets
- **NEVER** commit API keys, tokens, passwords, connection strings with credentials
- `.env.example` is the only `.env*` file allowed in git
- `pre-commit` runs `detect-secrets` against `.secrets.baseline` — do not bypass with `--no-verify`

### Code Quality

- All new code: type hints + tests + ruff clean + mypy clean
- All endpoints: Pydantic request + response models with `Field(description=...)`
- All ADRs: must be merged before related implementation PR

### Compliance Forward-Looking

- **PDPA (Thailand)** — assume all clinical data is PII, build audit trails from day 1
- **Data residency** — Local LLM on MS-S1 MAX is default; Claude API only with consent + non-PII
- **Medical liability** — All AI outputs are "assistive" — never auto-diagnostic

## 9. File Reading Priority for Claude Code

Read in this order at session start:

1. `CLAUDE.md` (this file)
2. `docs/STATUS.md` — current focus, in-flight work
3. `docs/adr/` — most recent first (highest number)
4. `docs/plans/` — active plans, then `done/` for context
5. `pyproject.toml`, `docker-compose.yml` — current deps + services
6. `services/api/main.py` + related code
7. `tests/` — current coverage and patterns

## 10. Index → docs/ + tools/

| Path | Purpose |
|------|---------|
| `docs/STATUS.md` | Current state, TODOs, in-flight discussions |
| `docs/adr/` | Architecture Decision Records |
| `docs/plans/` | Active execution plans |
| `docs/plans/done/` | Completed plans (archeology) |
| `docs/lessons/` | Session learnings (durable knowledge) |
| `docs/logs/` | Thin tracked summaries of working-tree events (gitignored-closeout companions; PLAN-004 v2 D6 two-artifact evidence model) |
| `docs/runbooks/` | Operational guides |
| `docs/conventions/` | Tech stack, code style, glossary, tier instructions, handoff frontmatter schema (canonical) |
| `docs/for_llm/` | Curated snippets for cold-start LLM sessions (derived from canonicals — see runbook) |
| `tools/handoffs/` | Handoff tooling (transcript rendering, frontmatter validation, dashboard reader) |

## 11. Tier 2 (Code) Operational Policy

Tactical policy specific to Tier 2 (Code) execution. Other tiers do not need to read this section.

### Worktree Mode

Default policy per Lesson #3:

| Scenario | Worktree | Rationale |
|----------|----------|-----------|
| Single-task work (ADR draft, doc edit, single commit) | **OFF** | Avoid Family B traps (sandbox ownership cascade); zero isolation benefit |
| Parallel work (multiple branches in flight, risky refactor) | **ON** | Isolation worth the lifecycle cost; apply Lesson #3 prevention checklist |
| Buildable code that should fail-isolated in CI | **ON** | PR boundary clarity; explicit pre-flight required |

Apply the [Lesson #3 prevention checklist](docs/lessons/0003-code-tab-worktree-lifecycle-traps.md#prevention-checklist) before any worktree-on session.

### Transcript Handoff

When the Code tab judges that a reply or span of work should be handed
to Chat or Cowork for follow-up, render the full raw transcript via
`tools/handoffs/render_transcript.py` into `.claude/handoffs/session-NN/`
(gitignored working note) and **always state the export file path in
the reply**. Procedure + options:
[`docs/runbooks/transcript-handoff.md`](docs/runbooks/transcript-handoff.md).

---

*Constitution = stable. Volatile state in `docs/STATUS.md`.*
*Last updated: 2026-05-16 (Session 11 — §11 Transcript Handoff convention)*
