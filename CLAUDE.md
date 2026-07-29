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

**Derived artifacts** — Tier 2.5 (`docs/for_llm/`) and Tier 2.6 (`.claude/skills/`) — carry **no independent precedence** (ADR-0017 D6). On any conflict with `CLAUDE.md`, an ADR, a convention, or a lesson, the **canonical wins** and the derived artifact is corrected.

## 2. Direction & Current Focus

→ **Standing direction:** [`ADR-0032`](docs/adr/0032-strategic-frame-demo-to-pilot-wedge-and-3-shape-roadmap.md) — the demo→pilot wedge (D1), the 3-shape roadmap and its binding pilot gate (D2–D4), and the positioning / fit-filter discipline (D5–D6). Read it before planning anything strategic.

→ **Current state:** [`docs/STATUS.md`](docs/STATUS.md) — in-flight work, recent decisions, and Active TODOs.

*(State never overrides direction — §1 precedence.)*

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
| **2.6** | In repo (derived) | On-demand procedural skills — git-tracked, **auto-loaded by description match** (not read every session, not deliberately pulled) | `.claude/skills/` (`git-workflow`, `code-operational-policy`) |
| **3** | In repo (archeology) | Historical record | `docs/plans/done/`, git history |

→ Full details: [`docs/runbooks/memory-architecture.md`](docs/runbooks/memory-architecture.md)

**Rule:** Repository = single source of truth. Auto Memory complements, never replaces. `for_llm/` (2.5) and `.claude/skills/` (2.6) snippets are derived — canonicals win on conflict (ADR-0017 D3/D6). Tier instruction files in `docs/conventions/` are canonical; the Claude project UI Chat tab / Cowork tab "project instructions" field is a sync target that Cray re-pastes when canonical changes.

**Where new knowledge goes** (the ADR-0017 D5 routing rule): a **binding rule** the agent must always obey → `CLAUDE.md` (keep it short); a **durable learning** → `docs/lessons/` (advisory); a **canonical reference / standard** you look up deliberately → `docs/conventions/` (or `docs/runbooks/` for operational how-to); a **task-triggered procedure** best surfaced automatically at the moment of need → a **Skill** (`.claude/skills/`). Bright line: a binding rule never moves into a skill (a skill that fails to trigger would silently drop it) — `CLAUDE.md` holds the rule, the skill holds the how-to. Full rule + skill-authoring conventions: [`docs/runbooks/memory-architecture.md`](docs/runbooks/memory-architecture.md).

## 5. Hardware

- **Cray-Legion5Pro** — Dev. Win11 + WSL2 Ubuntu 24.04. Path: `~/work/vero-lite`.
- **MS-S1 MAX** — LLM server. AMD Ryzen AI Max+ 395, 128GB unified, 192.168.1.133. See ADR-002.

## 6. Working Patterns

### Conversation Hygiene (CRITICAL)

The project uses four collaboration tiers (topology per ADR-009; free-form venues per ADR-012; autonomy axis per ADR-013 — see note below the table):

| Tier | Role | Purpose | Primary output |
|------|------|---------|----------------|
| **Tier 0 + Tier 1 + Tier-1b** — Cowork (merged per ADR-009 D1; free-form added per ADR-012 D1) | Research + governance authoring + repo-grounded free-form | External knowledge compilation; **dispatch, ADR, PLAN authoring**; repo-grounded free-form discussion / thinking-partner / informal code review (ADR-012) | Research files in `docs/research/private/`; `cowork-` prefixed handoffs (via outputs scratchpad under K-2 — see Lesson #8); **uncommitted drafts in `docs/adr/` and `docs/plans/`**; free-form = conversation (optional `phase: discussion` capture) |
| **Tier 1 (narrowed)** — Chat | Free-form discussion — repo-blind, shared with Cowork per ADR-012 (per ADR-009 D5 option b) | Open-ended strategy discussion, sounding-board, blue-sky / conceptual code review | **Conversation only — no repo-tracked artifacts** |
| **Tier 2** — Code | Execution agent | Repo writes, git operations, implementation, **all commits** (per ADR-009 D2 "only Code commits" fail-safe) | Code commits, file modifications, `code-` prefixed handoffs |
| **Tier 3** — Cray | Final authority | Private knowledge, business judgment, routing between tiers | Decisions, dispatch ratification |

The table is the single in-file statement of ADR-009 D1/D2 — everywhere else in this file, bare `(ADR-009 D1)` / `(ADR-009 D2)` point back here. Detailed read/write scopes + handoff conventions per tier: `docs/conventions/cowork_tab_instructions.md`, `docs/conventions/chat_tab_instructions.md`. Tier 2 operational policy: §11. K-1/K-2 Cowork workflow: [`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`](docs/lessons/0008-cowork-tier1-k1-k2-workflow.md).

**Autonomy-axis note (ADR-013).** The execution-automation axis (hooks, subagents, MCP transport, headless/`defer` resume) lives in **Code + subagents (Tier 2)** — the only tier that can run those primitives (D1); Cowork/Chat are advisory on that axis. Phased: Cowork retains interim governance authoring (ADR-009 D1) until the subagent topology lands (PLAN-0008+, Phase 3), and after Phase 3 remains the **advisory drafter of governance artifacts** (OQ-1 resolved). Free-form venues retained (D3). ADR-009 D2 is preserved and **hook-reinforced** (deterministic `PreToolUse deny`, D2). Details: ADR-013.

**Rule:** Never copy-paste long context between Claude Chat and Claude Code. Use the repository as shared memory.

### Governance Artifact Flow (ADR + PLAN)

1. Need a decision or new work → discuss free-form (Chat, per ADR-009 D5 b) → **Cowork drafts** in `docs/adr/NNNN-name.md` or `docs/plans/NNNN-name.md` (use `0000-template.md`) (ADR-009 D1)
2. Cray ratifies — ADR status `Proposed` → `Accepted`. PLANs must include: Goal, Acceptance Criteria, Out of Scope, Steps
3. **Code commits** (ADR-009 D2). ADRs: implementation PRs reference the ADR number in commits. PLANs: execute in a feature branch; after completion, `git mv docs/plans/NNNN-*.md docs/plans/done/`

### Routing: proceed vs Cowork-dispatch (per ADR-009 D1/D2, ADR-013)

Decide the route from the *nature* of the task, not by default:

- **Solid, and the only thing left is a confirming second perspective → proceed.** Code approves / executes directly. Don't bounce solid work through a heavier cycle.
- **Might have gaps, OR genuinely needs creative / adversarial input → build a Cowork dispatch file.** Cowork returns the draft; Code + Cray review. Reserve the heavier cycle for where an independent creative / adversarial lens adds *real* value.

**Mechanical overlay (structural — NOT a quality judgment).** A *new* PLAN or ADR (or editing an Accepted ADR) is **PreToolUse-gated for Code** (the G1 / G2 governance gates, scoped to `docs/adr/` + `docs/plans/`); the in-harness `plan-drafter` is exempt from the G2 classifier **by design** (PLAN-0034 prong 2 — it is the one actor for whom those writes are allowed) and is instead **gated by its own fail-closed write-allowlist**, which permits `docs/adr/` + `docs/plans/` only and denies everything else; a constitutional edit to this file is not gate-blocked but is **Cowork-drafted by convention** (ADR-009 D1). Either way the work routes through Cowork **regardless of how solid it is** — **Cowork drafts (ungated) → Code commits** (ADR-009 D1/D2). This is mechanical, **not** a finding that the work has gaps. When routing to Cowork, state the solid-vs-needs-creative judgment **explicitly**; never bounce the substance silently.

| Task | Route | Why |
|------|-------|-----|
| New PLAN | Cowork dispatch | mechanical — new PLAN = G2-gated for Code |
| New ADR | Cowork dispatch | mechanical — new ADR = G2-gated for Code |
| Refresh / re-rank of existing work | judgment call | solid → proceed; needs creative re-rank → dispatch |
| Offline re-grade / harness reuse (no governance artifact) | proceed (Code solo) | solid, no gate |

Dispatch how-to: `.claude/handoffs/session-NN/<YYYY-MM-DD>-<HHMM>-cowork-<topic>-dispatch.md`, valid frontmatter, LOCKED vs SURFACED marked, write target + fallback stated (full mechanics: `docs/conventions/cowork_tab_instructions.md` K-1/K-2 workflow + the handoff-frontmatter schema). Code commits the returned draft via PR (§7). This records standing ADR-009 / ADR-013 practice — it overrides no ADR (§1 Precedence: a later ADR still wins).

### Verification is hygiene, not a verdict

*(Generalizes the Mechanical-overlay principle — structural, NOT a quality judgment — from routing to the Axis-B verify loop.)*

- Re-checking solid prior work does **not** imply the prior was wrong.
- The duty to refute the claim is **unchanged**: verify against a pass/fail read fixed **before** the run, with **fresh on-disk evidence** (Lesson #0026; §8 "the offline oracle is the gate").
- Only the **narration** of a passed, evidence-backed check is freed from blame-framing: record it `confirmed — prior intact`. A recalled artifact that no longer matches current code is **classified** `superseded by new info` (evolution — keep the reasoning lineage) **vs** `was an error` (fix + note why) — distinct handling, never flattened to "stale".
- This **never** licenses skipping, shortening, or softening a check. No fresh evidence = **INSUFFICIENT-EVIDENCE, not a pass**. The `confirmed — prior intact` label is double-gated — pre-committed pass/fail criterion **and** fresh on-disk artifact — never written from memory.
- **Scope:** governs how a prior **decision** is treated — **not** the verification of a **claim**; claim-refutation stays fully adversarial (the `goal-evaluator`'s refute-not-bless mandate, ADR-0018).
- Before reopening a settled decision, weigh its **reversal cost** (the downstream work built on it), not just the cost of editing that one artifact. **Tripwire:** if this principle is cited as a reason *not to check*, it is misapplied — it governs the **label on a finished check**, never the **decision to run one**.

Deep rationale + the claim-vs-decision worked example: [`docs/lessons/0027-verify-not-indictment-refute-claim-not-decision.md`](docs/lessons/0027-verify-not-indictment-refute-claim-not-decision.md).

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
**Commit messages:** Write to a file → `git commit -F` (never an inline backtick/`$var`/code-block heredoc).
**PR / issue / release bodies:** Use `--body-file` / `--notes-file`, **never** `--body "$(cat PATH)"` (backticks trigger command substitution + silently corrupt the body).
**Commit + push hygiene:** Never chain commit with a push to `main` — commit on a branch first, then PR-flow.

→ Mechanics + rationale + recovery (WSL UNC path, `gh api PATCH` body fix, `gh pr edit` caveat, Lessons #4/#10/#11): **`git-workflow` skill** (`.claude/skills/git-workflow/`, loads on demand) — the standing procedural home (§4 placement rule: binding rules here, task-triggered how-to in the skill). No `docs/conventions/git.md` extraction is planned.

## 8. Constraints (DO NOT VIOLATE)

### Public Repository

- **NEVER** commit `.env`, `.env.local`, `.env.production`, or any file with secrets
- **NEVER** commit API keys, tokens, passwords, connection strings with credentials
- `.env.example` is the only `.env*` file allowed in git
- `pre-commit` runs `detect-secrets` against `.secrets.baseline` — do not bypass with `--no-verify`

### Code Quality

- All new code: type hints + tests + ruff clean + mypy clean
- **Every build also ships a scenario test** — it must **drive the real producer into the real consumer on realistic simulated data**; skipping it is not allowed. A mock-fed unit suite agrees with itself by construction: it proves the contract its author imagined, never the one the system produces — a planted seam bug kept all 24 LINE unit tests green while silently severing an approval route; only scenario cases reddened (PRs #960/#961). A test that stubs either side of the seam under test, or a scenario file that drives nothing, does not satisfy this rule.
- All endpoints: Pydantic request + response models with `Field(description=...)`
- All ADRs: must be merged before related implementation PR

### Compliance Forward-Looking

- **PDPA (Thailand)** — assume all clinical data is PII, build audit trails from day 1
- **Data residency** — Local LLM on MS-S1 MAX is default; Claude API only with consent + non-PII
- **Medical liability** — All AI outputs are "assistive" — never auto-diagnostic

### Host-State Actions

- Warming or running a model on **MS-S1**, altering that machine over its
  administrative **SSH** channel, or any change to global / host configuration
  outside the worktree, is a **host-state change** — get **explicit Cray go
  before it**, and **minimize live runs**. A live verification is *evidence*,
  not a CI gate; the offline oracle is the gate. The gated surface is the
  **whole host**, not just inference.
- This binding rule lives here so it survives when no PLAN is active.
  Mechanics — addresses / ports, warm + verify-the-right-model, SSH admin
  procedure — are in the `ms-s1-ollama` and `ms-s1-admin` skills.

### Command Output Is Evidence — Do Not Corrupt It

- Running a command via `wsl bash -lc` can silently hand you a **fabricated
  success** or a **partial read**. Three measured shapes: a bare `$` inside the
  string expands one shell layer early (so `$?` reports `0` for a failed
  command); unmerged `stderr` **overwrites** `stdout` byte-for-byte (one stderr
  line can erase the entire output); and a pipe into `head`/`tail` reports the
  *truncator's* exit status while cutting the traceback.
- Therefore, whenever a command's result is **evidence for a claim**: merge
  streams with **`2>&1`**, escape **`\$`** for every `$`, chain with **`&&`**
  (newlines do not short-circuit), and **never pipe into `head`/`tail`** —
  redirect to a file, echo the real exit code, then read a bounded slice.
- This binding rule lives here because the hazard fires on ordinary Bash calls
  in **every** session, where a task-triggered skill would not load. Mechanics,
  the measured probes, and the enforcement hook: [`docs/lessons/0007-harness-exit-code-artifact.md`](docs/lessons/0007-harness-exit-code-artifact.md).

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
| `tools/handoffs/` | Handoff tooling — transcript rendering, frontmatter validation (+ `handoff-frontmatter` pre-commit hook, PLAN-004 Phase B), dashboard reader (`--watch` live view, `--index` per-session `INDEX.md`) |
| `.claude/skills/` | On-demand procedure skills for Code (`git-workflow`, `code-operational-policy`); auto-loaded by relevance so detailed how-to stays out of always-on context. **Tier 2.6** in the memory model — formalized by ADR-0017 (see §4 + the memory-architecture runbook for placement, the knowledge-placement decision rule, and authoring conventions) |

## 11. Tier 2 (Code) Operational Policy

Tactical policy specific to Tier 2 (Code) execution. Other tiers do not need to read this section.

The worktree-mode decision table (when isolation is ON vs OFF, per Lesson #3) and
the transcript-handoff procedure (`tools/handoffs/render_transcript.py` → always
state the export path in the reply) now live in the **`code-operational-policy`
skill** (`.claude/skills/code-operational-policy/`), loaded on demand when
deciding worktree isolation or rendering a handoff. Sources: Lesson #3,
[`docs/runbooks/transcript-handoff.md`](docs/runbooks/transcript-handoff.md).

The **plan-first discipline** for costly / host-state / irreversible /
multi-step execution — read the result-producing code first, stage a plan with a
pre-committed pass/fail read, run the cheapest gate first, run once, verify via
the Read tool, and declare a `/goal` for verification tasks — also lives in that
skill (Lesson #0026; host-state gate = §8 above).

The **verify-loop hygiene rule** — a re-checked, evidence-backed prior is logged `confirmed — prior intact` (never recorded as a defect), and a recalled-artifact mismatch is classified `superseded by new info` vs `was an error` — is the cross-tier §6 rule ("Verification is hygiene, not a verdict"); it fires most often here, in Code's verify habit, and never licenses skipping or softening a check.

---

*Constitution = stable. Volatile state in `docs/STATUS.md`.*
*Last updated: 2026-07-29 (session 188). Convention: a constitutional edit bumps this date only — the full record of what changed and why lives in that edit's commit message (`git log --follow -- CLAUDE.md` is the amendment history); durable learnings live in `docs/lessons/`.*
