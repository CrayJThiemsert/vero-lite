# Runbook: Memory Architecture

**Status:** Active
**Last updated:** 2026-05-07 (Session 5)
**Related:** `CLAUDE.md` §4

---

## Purpose

Define how vero-lite maintains durable context across Claude Chat, Claude Code, and Cowork sessions, while keeping a clear separation between private working memory and shared project knowledge.

## Approach: Hybrid (Auto Memory + Repository)

Auto Memory is **complementary**, never authoritative. The repository is the single source of truth.

```
┌─────────────────────────────────────────────────────────┐
│  Tier 0: Private working memory (NOT in repo)           │
│  ~/.claude/projects/.../memory/                         │
│  - Auto Memory CLI v2.1.132 (enabled)                   │
│  - Per-machine, per-user, ephemeral context             │
│  - Notes, half-formed thoughts, scratch                 │
└─────────────────────────────────────────────────────────┘
                         │
                         │ promote durable insights
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 1: Hot context (in repo, read every session)      │
│  - CLAUDE.md          → stable constitution             │
│  - docs/STATUS.md     → volatile project state          │
└─────────────────────────────────────────────────────────┘
                         │
                         │ details / references
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 2: Reference (in repo, lookup as needed)          │
│  - docs/adr/          → architecture decisions          │
│  - docs/lessons/      → session learnings (timeless)    │
│  - docs/runbooks/     → operational guides              │
│  - docs/conventions/  → tech stack, code style, etc.    │
└─────────────────────────────────────────────────────────┘
                         │
                         │ derive curated snippets
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 2.5: Derived curated context (in repo)            │
│  - docs/for_llm/      → cold-start session primers      │
│  - Authority: derived; canonicals win on conflict       │
│  - Lifecycle: regenerate when source changes            │
└─────────────────────────────────────────────────────────┘
                         │
                         │ historical record
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 3: Archeology (in repo, rare lookup)              │
│  - docs/plans/done/   → completed PLANs                 │
│  - git log            → commit history                  │
└─────────────────────────────────────────────────────────┘
```

## Tier Details

### Tier 0 — Private Working Memory

- **Location:** `~/.claude/projects/<project-uuid>/memory/`
- **Tool:** Claude CLI Auto Memory feature (v2.1.132+)
- **Scope:** Single user, single machine
- **Lifetime:** Ephemeral, may be cleared/migrated by CLI updates
- **Use:** In-session scratchpad, recent context, working hypotheses
- **Anti-pattern:** Storing decisions or workflow rules here (use Tier 1-2 instead)

### Tier 1 — Hot Context

| File | Role | Update frequency |
|------|------|------------------|
| `CLAUDE.md` | Stable constitution: identity, architecture, workflow, constraints | Rare (only when rules change) |
| `docs/STATUS.md` | Volatile state: current focus, recent decisions, in-flight, TODOs | Every commit / session |

**Rule of thumb:** If content is stable for >1 month, it belongs in CLAUDE.md. If it changes per session, it belongs in STATUS.md.

### Tier 2 — Reference

| Path | Content | Examples |
|------|---------|----------|
| `docs/adr/` | Architecture Decision Records (numbered, immutable once Accepted) | ADR-001 LLM baseline, ADR-003 ports |
| `docs/lessons/` | Timeless learnings extracted from sessions | Pre-commit env setup, file ownership traps |
| `docs/runbooks/` | Operational how-to guides | Memory architecture (this file) |
| `docs/conventions/` | Coding/process conventions | Tech stack, code style, glossary |

### Tier 2.5 — Derived Curated Context

- **Location:** `docs/for_llm/`
- **Purpose:** Curated snippets optimized for paste-into-new-session
- **Authority:** **Derived**, not canonical. If conflict with Tier 1-2, canonical wins.
- **Lifecycle:** Regenerate when source changes; stale snippets are worse than none.
- **Use:** Cold-start LLM sessions where pasting all canonicals would exceed context budget.

### Tier 3 — Archeology

- `docs/plans/done/` — completed PLANs, kept for historical context
- `git log` — full commit history with messages

Rarely read directly. Used when investigating "why did we do X" months later.

## Promotion Workflow

Insights flow upward (Tier 0 → 1/2):

```
Auto Memory note (Tier 0)
        │
        │ Weekly review: "Is this durable knowledge?"
        ▼
   ┌────┴────┐
   │ YES?    │ NO?
   ▼         ▼
Tier 1/2   Stays Tier 0 or discarded
```

**Examples:**

| Insight | Tier | Why |
|---------|------|-----|
| "Used `uv sync --extra dev` to fix missing pre-commit deps" | Tier 2 (`docs/lessons/`) | Timeless trap, others will hit it |
| "Currently debugging port conflict with smb-flow" | Tier 0 only | Transient, machine-specific |
| "Decided pgvector over Qdrant for vector search" | Tier 2 (`docs/adr/`) | Architectural decision, needs immutable record |
| "TODO: write ADR-004 by next session" | Tier 1 (`docs/STATUS.md`) | Active project state |
| "Architecture summary for new sessions" | Tier 2.5 (`docs/for_llm/`) | Curated snippet derived from CLAUDE.md §3 |

## Cross-Tool Sharing

Three tools, one source of truth:

| Tool | Reads | Writes |
|------|-------|--------|
| **Claude Chat** (claude.ai) | Project Knowledge (uploaded files from repo) | Drafts → human pastes into repo |
| **Claude Code** (CLI) | All repo files directly | Commits to repo |
| **Cowork** (Desktop) | Linked folder = repo path | Direct file writes when permitted |

**Rule:** All three converge on the repository. Never let one tool develop authoritative state outside the repo.

## Anti-Patterns

❌ **Don't:** Use Auto Memory to store decisions or workflow rules
✅ **Do:** Promote them to `CLAUDE.md`, `docs/adr/`, or `docs/lessons/`

❌ **Don't:** Copy-paste long context between Claude Chat and Claude Code
✅ **Do:** Persist to repo, then reference from both tools

❌ **Don't:** Edit `CLAUDE.md` for transient state ("currently working on X")
✅ **Do:** Update `docs/STATUS.md` instead

❌ **Don't:** Let Cowork or Claude Code accumulate state in non-repo paths
✅ **Do:** All durable state lives in repo

❌ **Don't:** Treat `docs/for_llm/` snippets as canonical when they conflict with CLAUDE.md or docs/
✅ **Do:** Update the canonical first, then regenerate the snippet

## Maintenance Schedule

| Cadence | Action |
|---------|--------|
| Per session | Update `docs/STATUS.md` front-matter + sections |
| Per commit | Update `docs/STATUS.md` "Recent Decisions" if applicable |
| Weekly | Review Auto Memory for promotion candidates |
| Per major decision | Mint ADR in `docs/adr/` |
| Per session learning | Add to `docs/lessons/` if timeless |
| When canonicals change | Regenerate affected `docs/for_llm/` snippets |

## References

- `CLAUDE.md` §4 — Memory Architecture summary
- ADR-003 — Service port strategy (example of Tier 2 ADR)
- `docs/for_llm/README.md` — Tier 2.5 conventions
- Session 4 research — Original investigation (Tier 0 Auto Memory archive)
