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
- **Project vs global vs plugin skills:** project skills (`.claude/skills/`) are repo-canonical for project procedures. Global skills (`C:\Users\crayj\.claude\skills\` on the Windows/host side) and plugin skills are personal / cross-project and **must not encode project-binding rules** (those belong in `CLAUDE.md` / ADRs per D3/D5). **Authority rule (intent):** project context *should* govern project work. **Loader reality (OQ-B resolved 2026-06-10, restart-confirmed — see [`Lesson #22`](../lessons/0022-skill-loader-precedence.md)):** the harness does **not** enforce that intent — on a same-bare-name collision the **global/user skill WINS over the project skill** (`C:\Users\crayj\.claude\skills\` **>** `<repo>/.claude/skills/`); the **WSL** `~/.claude/skills/` root is **not scanned at all** (harness HOME = Windows side); **plugin** skills are namespace-qualified (`plugin:skill`) and never bare-name-collide. **Authoring guard:** never rely on a project skill shadowing a same-named global one — it won't, and your project copy becomes silent dead weight; give project skills collision-free names (the repo's `git-workflow` + `code-operational-policy` already are). *(Aside: the `eli-cray` example formerly cited here is a **command** at `C:\Users\crayj\.claude\commands\eli-cray.md`, not a global skill — see Lesson #22 §3.)*
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

❌ **Don't:** Let an always-read Tier-1 file retain content "for archeology" — retention without a size budget is monotonic growth (STATUS hit 393 KB and broke the Read tool, Lesson #23)
✅ **Do:** Keep STATUS within the rotation policy (≤64 KB hard / 48 KB soft); archeology lives in `docs/status-archive/` + git history (Tier 3)

❌ **Don't:** Put a binding rule in a skill (a skill that fails to trigger silently drops it), or let a skill originate governance content
✅ **Do:** Keep binding rules in `CLAUDE.md`; a skill references the canonical and holds only how-to (ADR-0017 D3/D4)

## STATUS.md Rotation Policy (Lesson #23)

`docs/STATUS.md` is Tier-1 **volatile state** — always-read, never an archive.
After it grew to 393 KB / >25k tokens and broke the Read tool + looped the
`status-scribe` subagent (Lesson #23, PR #243), the following rules are
**binding**. The empirically binding limit is the Read tool's **25k-token
whole-file cap** (hit at ~83 KB for this file's ~3.3 bytes/token density —
measured 2026-06-10), not the 256 KB byte cap.

### R1 — Size budget (hard ceiling)

- **Hard ceiling: 64 KB** (≈19.6k tokens at measured density; ~78% of the
  25k-token cap). **Soft target: 48 KB.**
- Enforcement is split by capability:
  - **Pre-commit size guard** (deterministic, fail-closed at >64 KB) — Code
    scopes as a follow-up; the authoritative check.
  - **Main Code agent** — `stat` after each reconcile; >48 KB = prune harder
    next reconcile, >64 KB = fix before commit.
  - **`status-scribe`** — has no Bash, so it cannot byte-check; it enforces the
    *structural* rules (R2/R3) whose counts are Grep-countable.

### R2 — Rolling window

- **Current Focus:** keep blocks from the **4 most-recent sessions**, capped at
  **8 blocks** total (blocks ≠ sessions — session 49 had 3 blocks; the session
  window carries narrative continuity, the block cap bounds multi-block
  sessions). Older blocks rotate to the archive (R4).
- **Recent Decisions:** keep the **newest 10 rows**; fix the header to
  **"(last 10)"**. New rows are **pointers, not narratives: ≤ ~600 chars** —
  full detail lives in the referenced ADR/PLAN/PR, which every row already
  links. (The row-terseness rule is what bends the size curve long-term.)
- **Ratified extension (Cray, 2026-06-10):** *Active TODOs* — delete `[x]`
  items older than the session window (each is already recorded in Recent
  Decisions and/or git history; drop, no archive needed). *Next Steps* —
  delete superseded "MERGED"-history entries. Both sections carried
  session-4-era content and were the next-largest bloat source after the
  decisions table.
- **Ratified extension (Cray, 2026-07-17 — session 141):** *Active TODOs* obey
  the **same pointer rule as Recent Decisions rows** — an open TODO is a
  **pointer, not a narrative: ≤ ~600 chars**, naming the tracked artifact that
  holds the full story (an ADR, a PLAN incl. `done/`, a lesson, a runbook, a
  code/test docstring) so a reader reaches it in one hop. Rationale: the
  2026-06-10 extension covered only *deleting `[x]` items*, so **open** items were
  free to grow — by s141 Active TODOs were 17,181 B / 26% of the file with **zero**
  `[x]` items to delete, and one item (`Rock 3`) was 5,528 B of history already
  closed in `docs/plans/done/`.
  - **The carve-out is binding — it is what makes the rule safe.** An item is
    trimmed **only after verifying its substance has a tracked home**. An item whose
    facts live *nowhere else in git* — or only in **gitignored**
    `docs/research/private/` / `docs/strategy/private/`, or only in a private Tier-0
    auto-memory — is **not a duplicate**, and is **left at full length until it is
    rehomed**. Trimming it would delete the fact from the repository, which R4
    forbids. Three items hit this carve-out at s141 and were left byte-untouched:
    the s74 demo-card-UX decision (at s141 `ADR-0030` cited **STATUS itself** as
    its authority, and `PLAN-0035` still recorded the question as open), `Rock 4`'s
    evidence-asymmetry finding (survives only in gitignored research), and the
    monotonic `sequence`-column deferral.
  - **"Until it is rehomed" is a real exit — the carve-out defers a trim, it does
    not grant permanent tenure.** The correct response to a carve-out item is to
    **rehome it into a tracked artifact and then trim** — never to leave it at full
    length forever; STATUS is not a home. **The order is the rule: rehome →
    re-point the citers → verify → trim.** Trimming first would delete the fact.
    **All three s141 items were discharged at s142** — and their three homes are
    deliberately different, which is the lesson: *rehome into the artifact whose
    reader needs the fact, not into whichever doc is nearest.*
    - **`Rock 4`'s evidence-asymmetry finding** → `docs/adr/0025-at2-managerial-layer.md:23-29`
      — the ADR that already recorded the same research; a public-repo-safe
      statement, with the gitignored research cited **by path only** per the
      ADR-0032 boundary. A rehome may itself be **gated**: ADR-0025 is Accepted, so
      `plan-drafter` authored the edit and Code R2'd + committed it (G1).
    - **The s74 demo-card decision** → `docs/plans/done/0035-governed-action-verify-reshape-build.md:576`
      — a dated **post-archival amendment** at SD-3, the very question that PLAN had
      left open (precedent `414e564` / `done/0008-*.md:593-618`), plus re-pointing
      `ADR-0030`'s six `STATUS.md:262` citations at that amendment.
    - **The monotonic `sequence`-column deferral** → the module docstring of
      `tests/services/db/test_load_run_ordering_guard.py` — a reader who hits the
      guard is exactly who needs to know the root fix was deferred and why — plus a
      pointer back to it at each wall-clock code site.
  - **Corollary — an ADR citing `STATUS.md:<line>` is a defect, not a citation.**
    It inverts §1 (STATUS is state, never a rule) *and* rots on contact: R2/R6
    re-prune STATUS every reconcile, so the anchor decays by construction (the s74
    ref was written at `:262`, had drifted to `:319` by s142). When a carve-out item
    is found with an ADR citing it **through** STATUS, the ADR's citation is part of
    the rehome — not a follow-up.
  - **R4 still applies:** the full original is appended to `docs/status-archive/`
    before the trim lands — move, never drop.

### R3 — Frontmatter terseness (binding)

`current_batch` / `next_action` / `blocked_on` are **current-session-only**:
single-line YAML scalars, **≤ ~200 chars each**, **no `Prior:` chains, ever**.
Narrative lives in the Current Focus body, never in frontmatter. (A 48 KB
one-line scalar was the acute killer — one long line defeats windowed Reads
entirely; see Lesson #23 §3.)

### R4 — Archive, don't drop (move-only, never silent-delete)

- Rotated content is **moved** to `docs/status-archive/` — the provisional
  path from #243 is **ratified**. Rationale over drop-to-git-history: Current
  Focus blocks are edited across reconciles, so reconstructing "the block as it
  last stood" from git means spelunking many `docs(status):` commits; a flat,
  greppable, tracked archive costs one paste at rotation time and keeps Tier-3
  lookup cheap. (Git history remains the ultimate Tier-3 record either way —
  nothing is ever lost by rotation.)
- **File cadence:** the existing `2026-h1-current-focus.md` is ratified as-is.
  From 2026 H2: one file per half-year, `docs/status-archive/<YYYY>-h<N>-status.md`,
  carrying TWO sections — rotated Current Focus blocks AND rotated Recent
  Decisions rows (newest at top, each tagged with its rotation date).
- **Archive size escape:** archives are Tier-3 (grep + windowed reads only,
  never whole-file Read), but stay under the 256 KB byte cap for sanity: if a
  half-year file would exceed **~192 KB**, start a `-b` continuation file.
- Deleting STATUS content **without** archiving remains forbidden (the
  `status-scribe` adversarial-hardening posture is amended to "rotation per
  this policy is the sanctioned path", not abandoned).

### R5 — Surgical reads for `status-scribe` (binding agent rule)

The scribe **never whole-file Reads `docs/STATUS.md`**. Discipline:

1. Frontmatter via `Read(offset=1, limit≈30)`.
2. Structure map via `Grep -n` on anchors (`^## `, `^> \*\*Session`).
3. Edit-target windows of **≤ 60 lines** (empirical at 83 KB: a 170-line
   window Read failed, a 45-line window succeeded).
4. `Edit` with exact-match strings; never `Write` a full-file rewrite.

### R6 — When rotation runs

**Every reconcile** (recommended in the dispatch; adopted): each
`status-scribe` run = prepend the new block + prune to the R2 window + emit the
rotated content for the main agent to append to the archive file. STATUS is
thereby self-limiting; no periodic sweep, no extra process. If a single
reconcile cannot reach the soft target without pruning *below* the R2 window
(e.g. one giant new block), the scribe surfaces an SD rather than over-pruning.

### Responsibility matrix

| Rule | status-scribe | Main Code agent | Pre-commit guard |
|---|---|---|---|
| R1 ceiling | — (no Bash) | `stat` check | **fail >64 KB** |
| R2 window | **prunes every reconcile** | reviews diff | — |
| R3 frontmatter | **writes terse** | reviews diff | — |
| R4 archive | emits rotated text | **appends to archive file + commits** | — |
| R5 surgical reads | **binding contract** | — | — |
| R6 cadence | per-reconcile | serializes spawns | — |

### When to deviate

A block with live cross-session load-bearing content (e.g. an unresolved SD a
future session must see) may be retained one extra window-cycle — flag it
explicitly in the block. If STATUS repeatedly cannot fit the window under the
soft target, that is a signal the *narrative voice* has drifted archival again;
fix the voice (terser blocks), don't raise the ceiling.

## Maintenance Schedule

| Cadence | Action |
|---------|--------|
| Per session | Update `docs/STATUS.md` front-matter + sections |
| Per STATUS reconcile | `status-scribe` prunes STATUS.md to the rotation window (R2) + rotates older blocks/rows to `docs/status-archive/` (R4); pre-commit guard enforces the 64 KB ceiling (R1) |
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
- `docs/lessons/0023-status-md-rotation.md` — STATUS.md bloat incident + the size-budget principle behind the rotation policy
- Session 4 research — Original investigation (Tier 0 Auto Memory archive)
