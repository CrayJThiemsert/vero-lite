# Runbook: Memory Architecture

**Status:** Active
**Last updated:** 2026-06-09 (Session 49 — Tier 2.6 skills added per ADR-0017)
**Related:** `CLAUDE.md` §4; ADR-0017 (Skills as a memory tier)

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
                         │ harness auto-loads by description match
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 2.6: On-demand procedural skills (in repo)        │
│  - .claude/skills/    → task-triggered how-to           │
│  - Authority: derived; canonicals win on conflict       │
│  - Load: auto-invoked by description match (not always) │
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

### Tier 2.6 — On-Demand Procedural Skills (ADR-0017)

- **Location:** `.claude/skills/<kebab-name>/SKILL.md` (git-tracked, sibling to `.claude/agents/`)
- **Purpose:** Task-triggered procedure / how-to, surfaced automatically at the moment of need.
- **Authority:** **Derived**, not canonical (same posture as Tier 2.5). A skill synthesizes procedure but **must cite its canonical(s)** and **must never own a binding rule**; on conflict the canonical wins (ADR-0017 D3/D6).
- **Load model:** the harness **auto-invokes by `description` match** — the one memory home that loads *by relevance* rather than always-on (Tier 1) or deliberate lookup (Tier 2/2.5). That distinct load model is why it is its own sub-tier.
- **Consumer:** runs for tiers that execute skills — **Code** and **Cowork** (via the bridge / desktop client). **Chat cannot auto-load skills** (repo-blind, not a bridge client) → Chat uses a Tier 2.5 `for_llm/` paste instead (ADR-0017 D2). This is the bright line that keeps 2.5 and 2.6 distinct.
- **Authoring owner:** **Code** authors all skills (harness primitive, ADR-013 D1); governance/domain content a skill needs lives in a Cowork-drafted, Code-committed canonical that the skill only references (ADR-0017 D4 escalation rule).

### Tier 3 — Archeology

- `docs/plans/done/` — completed PLANs, kept for historical context
- `git log` — full commit history with messages

Rarely read directly. Used when investigating "why did we do X" months later.

## Knowledge-Placement Decision Rule (ADR-0017 D5)

Where does a given piece of knowledge go? Ask, in order:

| The knowledge is… | It goes in… | Load model |
|---|---|---|
| a **binding rule** the agent must always obey (a "must / never") | **`CLAUDE.md`** (keep it short) | always-on |
| a **durable learning** ("we hit X because Y; next time do Z") — advisory, timeless | **`docs/lessons/`** | reference (advisory) |
| a **canonical reference / standard** you look up deliberately — definitions, schema, stable conventions | **`docs/conventions/`** (or **`docs/runbooks/`** for operational how-to) | deliberate lookup |
| a **procedure / how-to needed only while doing a specific task**, best surfaced automatically at that moment | a **Skill** (`.claude/skills/`) | auto-load on description match |

Two bright lines disambiguate the close cases:

- **Skill vs `docs/conventions/` (both on-demand):** a **convention is the canonical statement** of a reference/standard, **pulled deliberately** by someone who knows to look (the source of truth). A **skill is a derived, task-triggered procedure** the harness **auto-surfaces** by description match; it **references** the convention and never replaces it. *Convention = the law on the shelf (you fetch it); skill = the checklist that pops up when you start the job (it fetches you).*
- **Skill vs `CLAUDE.md`:** a **binding rule never moves into a skill** — a skill that fails to trigger would silently drop the rule. `CLAUDE.md` holds the rule (always loaded); the skill holds the how-to (loaded when relevant). (The PR #234 split: §7 kept the binding git rules; the how-to moved to the `git-workflow` skill.)

## Skill Conventions (ADR-0017 D7)

- **Location / shape:** project skills at `.claude/skills/<kebab-name>/SKILL.md`, git-tracked, sibling to `.claude/agents/`. YAML frontmatter: `name`, `description`. Body = the procedure + a `## References` section pointing to the canonical(s) it derives from (D3).
- **Description discipline (the single most important authoring rule):** the `description` is the **trigger contract** — name the trigger conditions precisely enough that the skill loads at the *right* task and stays silent otherwise. Over-broad → loads always (defeats the token saving); under-broad → never loads (dead weight). Exemplar: `git-workflow`'s *"Use whenever committing, pushing, or creating/editing a PR, issue, or release."*
- **Project vs global vs plugin skills:** project skills (`.claude/skills/`) are repo-canonical for project procedures. Global skills (`~/.claude/skills/`, e.g. the personal `eli-cray` skill) and plugin skills are personal / cross-project and **must not encode project-binding rules** (those belong in `CLAUDE.md` / ADRs). On a name collision, project-local context wins for project work. *(The exact harness resolution order for a same-named project vs global vs plugin skill is an open question — ADR-0017 OQ-B — to be confirmed empirically and recorded here; this runbook asserts only the authority rule.)*
- **Authoring owner:** **Code** (harness primitive, ADR-013 D1). If a skill would need to *originate* binding or governance content, the ADR-009 D1 path runs first (Cowork drafts the canonical, Code commits it), *then* Code packages the skill that references it — a skill is never the first home of a governance rule.
- **Forward link — harness-as-plugin:** skills + hooks + agents could later bundle as a portable vero-lite harness plugin for reuse across projects (the same engine-vs-config reuse logic as ADR-006). Forward-declared only; not decided in ADR-0017.

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
| "git/PR mechanics how-to, surfaced while committing" | Tier 2.6 (`.claude/skills/git-workflow/`) | Task-triggered procedure; auto-loads by description match |

## Cross-Tool Sharing

Three tools, one source of truth:

| Tool | Reads | Writes |
|------|-------|--------|
| **Claude Chat** (claude.ai) | Project Knowledge (uploaded files from repo) | Drafts → human pastes into repo |
| **Claude Code** (CLI) | All repo files directly | Commits to repo |
| **Cowork** (Desktop) | Linked folder = repo path | Direct file writes when permitted |

**Rule:** All three converge on the repository. Never let one tool develop authoritative state outside the repo.

**Skills (Tier 2.6) auto-load** for **Claude Code** and **Cowork** (the bridge / desktop client); **Claude Chat cannot** (repo-blind, not a bridge client) — Chat receives curated context only via a human-pasted `for_llm/` primer (Tier 2.5). This consumer split is why 2.5 and 2.6 coexist rather than one superseding the other (ADR-0017 D2).

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

❌ **Don't:** Put a binding rule in a skill (a skill that fails to trigger silently drops it), or let a skill originate governance content
✅ **Do:** Keep binding rules in `CLAUDE.md`; a skill references the canonical and holds only how-to (ADR-0017 D3/D4)

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
- ADR-0017 — Skills as a memory tier (Tier 2.6; D5 decision rule, D7 conventions sourced here)
- ADR-003 — Service port strategy (example of Tier 2 ADR)
- `docs/for_llm/README.md` — Tier 2.5 conventions
- `.claude/skills/git-workflow/SKILL.md`, `.claude/skills/code-operational-policy/SKILL.md` — Tier 2.6 skill exemplars
- Session 4 research — Original investigation (Tier 0 Auto Memory archive)
