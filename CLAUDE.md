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

The project uses four collaboration tiers (topology amended 2026-05-21 per ADR-009; free-form venues amended 2026-05-22 per ADR-012; **autonomy axis relocated 2026-05-23 per ADR-013** — see autonomy-axis note below the table):

| Tier | Role | Purpose | Primary output |
|------|------|---------|----------------|
| **Tier 0 + Tier 1 + Tier-1b** — Cowork (merged per ADR-009 D1; free-form added per ADR-012 D1) | Research + governance authoring + repo-grounded free-form | External knowledge compilation; **dispatch, ADR, PLAN authoring**; repo-grounded free-form discussion / thinking-partner / informal code review (ADR-012) | Research files in `docs/research/private/`; `cowork-` prefixed handoffs (via outputs scratchpad under K-2 — see Lesson #8); **uncommitted drafts in `docs/adr/` and `docs/plans/`**; free-form = conversation (optional `phase: discussion` capture) |
| **Tier 1 (narrowed)** — Chat | Free-form discussion — repo-blind, shared with Cowork per ADR-012 (per ADR-009 D5 option b) | Open-ended strategy discussion, sounding-board, blue-sky / conceptual code review | **Conversation only — no repo-tracked artifacts** |
| **Tier 2** — Code | Execution agent | Repo writes, git operations, implementation, **all commits** (per ADR-009 D2 "only Code commits" fail-safe) | Code commits, file modifications, `code-` prefixed handoffs |
| **Tier 3** — Cray | Final authority | Private knowledge, business judgment, routing between tiers | Decisions, dispatch ratification |

Tier instruction files in `docs/conventions/cowork_tab_instructions.md` (Tier 0 + Tier 1 + Tier-1b scope) and `docs/conventions/chat_tab_instructions.md` (narrowed Tier 1 free-form scope) define detailed read/write scopes, behavioral rules, and handoff conventions per tier. Tier 2 (Code) operational policy lives in §11 below. The K-1/K-2 Cowork-mode operating workflow is codified durably in [`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`](docs/lessons/0008-cowork-tier1-k1-k2-workflow.md).

**Autonomy-axis note (ADR-013, 2026-05-23).** Per ADR-013 D1, the harness *execution-automation* axis (hooks, subagents, MCP transport, headless/`defer` resume) relocates into **Code + subagents (Tier 2)** — the only tier that can run those primitives. Cowork/Chat shift toward an **advisory / second-perspective** role for execution-automation authoring. The relocation is **phased**: until the subagent topology lands (PLAN-0008+, Phase 3), Cowork retains interim governance authoring under ADR-009 D1, and after Phase 3 **Cowork is retained as the advisory drafter of governance artifacts** (ADR-013 OQ-1 resolved). Free-form venues (ADR-012) are **retained**, not revoked (ADR-013 D3). ADR-009 D2 ("only Code commits") is preserved and **reinforced** by a deterministic `PreToolUse deny` hook (ADR-013 D2). Tier instruction files in `docs/conventions/` will be annotated (not deprecated) at the Phase-3 boundary (ADR-013 T4).

**Rule:** Never copy-paste long context between Claude Chat and Claude Code. Use the repository as shared memory.

### Decision Flow

1. New decision needed → discuss in Claude Chat (free-form mode per ADR-009 D5 b)
2. **Cowork drafts ADR** in `docs/adr/NNNN-name.md` (use `0000-template.md`) per ADR-009 D1
3. Status: `Proposed` → `Accepted` after Cray ratification
4. **Code commits the ADR** per ADR-009 D2; Implementation PRs reference the ADR number in commits

### Plan Flow

1. New work needed → discuss requirements (Chat free-form) then **Cowork writes the PLAN** in `docs/plans/NNNN-name.md` (use `0000-template.md`) per ADR-009 D1
2. Plan must include: Goal, Acceptance Criteria, Out of Scope, Steps
3. **Code commits the PLAN** per ADR-009 D2, then executes plan in feature branch
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
**Branches:** `main` (protected — **no direct push, no exceptions**), `feat/*`, `fix/*`, `docs/*`, `chore/*`
**Workflow to `main`:** **All commits land via feature / `chore/*` / `docs/*` branch + PR + merge — no exceptions.** This includes single-file `docs(status):`, `docs(constitution):`, `docs(plans):`, `docs(lessons):`, and `docs(adr):` updates. Even one-line edits use a small `chore/*` or `docs/*` PR. Rationale: classifier-friendly (auto-mode guards direct push to default branch unconditionally — see Lesson #10), consistent history (every change has an explicit boundary + reviewable diff), trivially-revertable, and reinforces ADR-009 D2 "only Code commits" boundary.
**Author:** `Jirachai Thiemsert <16893502+CrayJThiemsert@users.noreply.github.com>`
**AI assistance:** Note in commit body — **NEVER** as `Co-Authored-By`
**Commit messages:** Write to file → `git commit -F`. Prefer Write tool against WSL UNC path (`\\wsl.localhost\Ubuntu-24.04\tmp\commit-message.txt`) over `wsl bash -c "cat <<'EOF'"` heredoc when message contains backticks, `$var`, or code blocks (per Lesson #4 prevention).
**Commit + push hygiene:** When the push target is a non-`main` branch, `git commit -F … && git push -u origin <branch>` chained is fine. When landing on `main` via PR, never chain commit with a push to `main` — always commit on a branch first, then PR-flow. Avoids the rework hazard of a chained command being denied as a whole (per Lesson #10).

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
*Last updated: 2026-05-26 (§7 clarified: all commits to `main` land via PR — no direct-push exceptions, even for single-file `docs(status):` / `docs(constitution):` edits; Workflow + Commit-push-hygiene lines added; Lesson #10 referenced as the prevention source. Prior 2026-05-23 amendment per ADR-013 — §6 autonomy-axis note; prior 2026-05-22 per ADR-012; prior 2026-05-21 per ADR-009 D1+D5.)*
