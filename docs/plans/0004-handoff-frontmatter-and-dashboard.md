# PLAN-004: Handoff Frontmatter and Dashboard

**Status:** Proposed (v2 — amended pre-dispatch)
**Date:** 2026-05-19
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-006 (vertical plugin), Lesson #5 (tier-system audit) §1 + §2 + §3 + §4, Lesson #6 (Code surface → Chat re-dispatch pattern), `docs/runbooks/claude-code-chat-handoff.md`, `docs/runbooks/transcript-handoff.md`, `docs/conventions/chat_tab_instructions.md`, `docs/conventions/cowork_tab_instructions.md`, `tools/handoffs/render_transcript.py` (precedent, commit `98e5591`)

## Context

The vero-lite handoff workflow (Chat ↔ Code ↔ Cowork) has produced
50+ handoff files across sessions 9–12 under `.claude/handoffs/session-NN/`.
Each handoff carries a YAML frontmatter block declaring `from`, `to`,
`session`, `batch`, `phase`, `status`, `created`, `title`, plus
optional `references_*` lists. The handoff mechanism itself is canonical
(CLAUDE.md §11), but reading session state currently requires opening
files individually — there is no aggregated view of what batches ran,
what paused, what is still in-queue.

**Critical pre-amendment constraint (Lesson #5 §4):** Handoff files
themselves are **gitignored by design** — they are session-scoped
working notes between tiers, not part of canonical repo history.
`.claude/handoffs/.gitignore` uses `*` to ignore all handoff files.
This means handoff frontmatter migration **operates on the working tree
only**; it is not a git-tracked change set. The schema, validator,
reader, and runbook (which live under `docs/` and `tools/`) ARE
committed; the frontmatter edits to handoff files themselves are not.
This is a feature, not a bug — and it reshapes Batch 2 acceptance
criteria away from "commit clean retro-migration" toward "validator
exit 0 on the working tree" plus a thin git-tracked summary recording
that the migration event occurred.

Four forces motivate the dashboard:

1. **Volume growth** — session 10 alone produced 30+ handoffs across a
   three-dispatch lesson-cleanup cycle plus governance + STATUS + §11
   ratification batches. Sessions 11+ will produce more, not fewer.
2. **Schema drift risk** — frontmatter has been hand-authored without a
   validator. Field names, value formats, and field presence vary
   across files. Sessions 9 files lack the `actor:` field that this
   plan introduces.
3. **Lifecycle visibility gap** — session 10 produced two PAUSED
   midflights (v1 + v2 of lesson cleanup) plus several NEEDS_INPUT
   states (Cray OQ pending). Current `status:` field is informal and
   does not distinguish these from `IN_PROGRESS`.
4. **Audit-cycle archeology** — handoff files are the canonical record
   for "what was the project state at time T", even when gitignored.
   Without a dashboard, each audit must re-derive state from scratch by
   reading files.

This plan codifies the dashboard as a Python tool (precedent:
`tools/handoffs/render_transcript.py`, commit `98e5591`) plus a YAML
frontmatter schema plus retro-migration of older session files (working
tree only, with thin git-tracked summary).

## Decision

Build a Handoff Dashboard as a three-piece system:

1. **Frontmatter schema** — closed YAML schema with documented required
   and optional fields; lives at `docs/conventions/handoff-frontmatter-schema.md`
2. **Validator** — Python script `tools/handoffs/validate_handoff.py`
   that parses one or more handoff files and reports schema violations.
   Designed to be invoked manually or wired into pre-commit later (Phase B).
3. **Reader** — Python script `tools/handoffs/handoff_status.py` that
   walks `.claude/handoffs/session-NN/` and emits a session snapshot
   (counts by phase + status, pause-and-redispatch chains, open
   NEEDS_INPUT items, references graph).

Both scripts share a single `tools/handoffs/_schema.py` module for
frontmatter parsing + schema enforcement, with pytest coverage matching
the `render_transcript.py` precedent (≥14 tests minimum). Stdlib-only,
no third-party deps, mypy-strict clean (consistent with §8 quality
gate for `tools/`).

### D1: Frontmatter schema (canonical, closed)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `from` | string | yes | originating actor identifier (e.g. `claude-chat-session-10-current-thread`) |
| `to` | string | yes | target actor identifier |
| `actor` | enum | yes | `chat` \| `code` \| `cowork` \| `cray` (D2) |
| `session` | int | yes | session number |
| `batch` | string | yes | free-form batch identifier |
| `phase` | enum | yes | `kickoff` \| `dispatch` \| `midflight` \| `closeout` \| `handoff` \| `discussion` (D3) |
| `suffix` | enum | no | content-type suffix (D4) — present when filename uses a non-core suffix token |
| `status` | enum | yes | `READY` \| `IN_PROGRESS` \| `PAUSED` \| `DONE` \| `NEEDS_INPUT` (D5) |
| `created` | ISO8601 datetime with TZ | yes | e.g. `2026-05-19T10:30:00+07:00` |
| `title` | string | yes | human-readable title |
| `references_predecessor_handoffs` | list[string] | no | filenames of prior handoffs this one continues |
| `references_session_batches_completed` | list[string] | no | batch descriptors completed by this handoff |
| `references_commits` | list[string] | no | short SHA references |

Unknown fields = validator warning, not error (forward-compat).

### D2: `actor:` enum + filename prefix discipline

| Value | Filename prefix | Authored by |
|-------|-----------------|-------------|
| `chat` | `chat-` | Tier 1 (Claude Chat) |
| `code` | `code-` | Tier 2 (Claude Code) |
| `cowork` | `cowork-` | Tier 0 (Claude Cowork) |
| `cray` | `cray-` | Tier 3 (Cray, human, direct codification path) |

Validator enforces filename prefix matches `actor:` field. Cray-direct
codification path is per Lesson #5 §2 sub-rule (e.g. CLAUDE.md §11
"Transcript Handoff" subsection authored by Cray in commit `dd65d9b`).

### D3: `phase:` enum (lifecycle role, canonical)

| Phase | Meaning |
|-------|---------|
| `kickoff` | session/batch initialization handoff |
| `dispatch` | Chat → Code (or Chat → Cowork) execute-this batch |
| `midflight` | recipient surfaces issue mid-execution (pause + ask) |
| `closeout` | recipient reports completion + acceptance criteria self-check |
| `handoff` | thread-to-thread state transfer (Chat → new Chat thread, etc.) |
| `discussion` | exploratory conversation file (no execute boundary) |

### D4: `suffix:` enum (content-type token, canonical)

Filename suffixes encode WHAT the handoff carries, distinct from D3
(lifecycle role). Core suffix enum is **locked**, extensible suffixes
are **registered here**:

| Suffix | Meaning | Locked / Extensible | Source |
|--------|---------|---------------------|--------|
| `closeout` | batch closeout report | locked (core) | implicit since session 9 |
| `midflight` | mid-batch pause + surface | locked (core) | implicit since session 10 |
| `kickoff` | session/batch initialization | locked (core) | implicit since session 9 |
| `errata` | correction notice | locked (core) | reserved |
| `amendment` | retroactive edit notice | locked (core) | reserved |
| `addendum` | post-closeout supplement | locked (core) | `2026-05-12-1430-...-batch2-closeout-addendum.md` precedent |
| `transcript` | full raw session transcript (per `transcript-handoff.md`) | extensible | Session 11, `dd65d9b` |
| `sync` | curated cross-tier sync handoff | extensible | Session 11, `2026-05-16-2210-code-chat-sync-transcript-tooling.md` |
| `restart-bridge` | constitutional-edit restart handoff (Lesson #5 §1) | extensible | Session 11, `2026-05-16-1337-code-session11-restart-bridge.md` |
| `dispatch` | Tier-1 execute / kickoff dispatch to Code (ADR-009 D1) | extensible | Session 10, C-2 resolution α (`2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md`) |
| `completion` | Tier-1 governance-artifact completion report | extensible | Session 10, C-2 resolution α (`2026-05-21-1130-cowork-plan0005-runtime-layer-completion.md`) |
| `consultation` | pre-draft consultation Q&A round | extensible | Session 10, C-2 resolution α (`2026-05-20-0215-chat-plan003-pre-draft-consultation.md`) |

**Field semantics:** `suffix:` field is OPTIONAL. Files using only core
lifecycle patterns (kickoff/closeout/midflight folded into `phase:`)
may omit `suffix:`. Files using extensible suffixes (the extensible
rows above) MUST declare `suffix:` so validator + reader can
classify them. Validator enforces filename-token / `suffix:` field
consistency when both are present. New extensible suffixes added to
this table require a PLAN-004 amendment (lightweight, single-row edit).

**Amendment (2026-05-22 — C-2 resolution α):** `dispatch`, `completion`,
and `consultation` registered as extensible suffixes (rows above),
closing the `tools/handoffs/_schema.py:Suffix` enum ↔
`docs/conventions/cowork_tab_instructions.md` suffix-list divergence.
Cray adjudicated option α (expand the enum) on 2026-05-22. `discussion`
is deliberately **not** added — per ADR-012, discussion handoffs carry
their role via `phase: discussion` and omit `suffix:`.

The `phase:` ↔ `suffix:` distinction:
- `phase:` always present, answers "what stage of the batch?"
- `suffix:` present when content type is non-core, answers "what KIND of artifact?"

Example: a Code → Chat sync handoff has `phase: handoff` + `suffix: sync`.
A transcript export has `phase: handoff` + `suffix: transcript`.

### D5: `status:` enum semantics (canonical)

| Status | Meaning | Example |
|--------|---------|---------|
| `READY` | dispatch authored, awaiting recipient action | Chat dispatch to Code |
| `IN_PROGRESS` | recipient actively working | Code midflight ack |
| `PAUSED` | work halted pending re-dispatch (anchor mismatch, scope question, etc.) | v1/v2 lesson cleanup midflights |
| `DONE` | work complete, closeout filed | typical closeout |
| `NEEDS_INPUT` | blocked on Cray decision (open question) | gated dispatches awaiting OQ resolution |

Validator does NOT verify status transitions (e.g. allow `READY → DONE`
without intermediate); the reader infers chains from file timestamps +
`references_predecessor_handoffs`.

### D6: Two-batch execution split

This plan is implemented in two atomic batches:

**Batch 1 — Tooling (committed):**
- Land PLAN-004 v2 doc itself at `docs/plans/0004-handoff-frontmatter-and-dashboard.md`
- Land `docs/conventions/handoff-frontmatter-schema.md`
- Land `tools/handoffs/_schema.py` (schema module)
- Land `tools/handoffs/validate_handoff.py` (CLI)
- Land `tools/handoffs/handoff_status.py` (CLI)
- Land `tests/handoffs/test_validate_handoff.py` + `tests/handoffs/test_handoff_status.py` + `tests/handoffs/test_schema.py` (≥14 tests total)
- Update `docs/runbooks/transcript-handoff.md` cross-reference (replace
  "see restart-bridge §4 / PLAN-004 Phase A" with concrete pointer to
  schema doc + suffix enum table)
- Update CLAUDE.md §10 index to reference new docs/scripts
- Update STATUS.md (catch-up + bump `head_commit` per Q4 spec) — once,
  at last commit of Batch 1
- All files NEW or amended in safe additive ways
- **Acceptance:** validator runs against zero files (idempotent), reader
  runs against zero files, all tests pass (ruff-clean, ruff-formatted,
  mypy-strict clean for `tools/handoffs/`), pre-commit clean

**Batch 2 — Retro-migration (working tree + thin git summary):**
- Run validator against all existing `.claude/handoffs/session-*/`
  files, capture violations as a manifest
- Amend each violating file in-place to match schema (primarily adding
  `actor:`, normalizing `status:` values, adding missing `phase:`,
  declaring `suffix:` where applicable)
- Verify validator passes on 100% of files
- Produce **two evidence artifacts**:
  - **Gitignored closeout** (operator-grade) at
    `.claude/handoffs/session-NN/<YYYY-MM-DD>-<HHMM>-code-plan004-batch2-closeout.md` —
    full migration manifest (every file changed, validator output,
    deviations). Session-scoped working note per Lesson #5 §4.
  - **Git-tracked summary** (audit-grade) at
    `docs/logs/2026-05-XX-plan004-batch2-migration.md` — thin record
    (~15-30 lines): completion date, total file count migrated,
    validator exit code, breakdown by session, pointer to gitignored
    closeout. Single commit `docs(logs): record PLAN-004 Batch 2
    migration completion`.
  - The tracked summary respects Lesson #5 §4 boundary (no handoff
    content reproduced in repo history) while preserving a git-visible
    audit trail that the migration event happened.
- **Acceptance:** `validate_handoff.py --all` returns exit 0 across all
  session directories. Both evidence artifacts produced. Single commit
  lands the tracked summary.

Batch 2 depends on Batch 1 (dog-fooding: validator from Batch 1 drives
the migration in Batch 2). If Batch 1 surfaces a schema flaw during
retro-migration (Batch 2), Batch 2 may emit a midflight requesting
Batch 1.5 (schema amendment via PLAN-004 v3) before resuming.

## Consequences

### Positive

- **Single-source-of-truth schema** for all handoff frontmatter going
  forward — closes the drift loophole that produced session 9 files
  without `actor:`
- **Dashboard reader** gives session-level visibility (counts, chains,
  open items) without manual file-by-file reading
- **PAUSED + NEEDS_INPUT explicit states** make pause-and-redispatch
  chains (per Lesson #6) first-class data instead of inferred from
  file body content
- **Retro-migration eats own dog food** — Batch 2 is the largest
  real-world test the validator will receive at design time
- **Cray-direct codification path** gets first-class schema support
  (`actor: cray`) reflecting Lesson #5 §2 sub-rule
- **`suffix:` enum codifies what `transcript-handoff.md` §2 forward-
  declared** ("extensible suffix beyond the core enum — see
  restart-bridge §4 / PLAN-004 Phase A") — this PLAN delivers that
  promise
- **Tooling cohabitation** with `render_transcript.py` under
  `tools/handoffs/` keeps related tools discoverable
- **Two-artifact evidence model** (gitignored detail + tracked summary)
  preserves both operator-grade visibility AND audit-trail visibility
  without violating Lesson #5 §4
- **Future-proof** — Phase B (automation) and Phase C (polish) can
  build on this foundation without re-deciding the schema

### Negative

- **Retro-migration touches ~50 working-tree files** in Batch 2 — even
  though gitignored, anchor verification (Tier 1 self-check #7) applies
  per file. Expect Code-surface midflights if inferring frontmatter
  content rather than reading from disk
- **`tools/handoffs/` module proliferation** — adds schema module +
  two CLIs alongside `render_transcript.py`. Acceptable cost; module
  layout already established
- **Schema becomes constitutional** — once landed, amendments require
  PLAN-004 supersession. Trade-off accepted: discipline is the value
- **Pre-commit integration deferred** — Phase A does NOT wire validator
  into pre-commit hook (left for Phase B). Operators must invoke
  manually until then
- **Batch 2 commit footprint is minimal** — retro-migration itself is
  a working-tree transformation (gitignored files). The only commit
  is a thin summary at `docs/logs/` recording completion. Full
  operator-grade manifest lives in the gitignored closeout. This
  two-artifact pattern preserves audit trail while respecting
  Lesson #5 §4.
- **Creates new `docs/logs/` directory** if it doesn't exist —
  introduces a new top-level docs sub-directory whose purpose
  (thin tracked summaries of working-tree events) needs its own
  README to avoid confusion with `docs/lessons/`, `docs/runbooks/`,
  etc.

### Neutral

- `tools/handoffs/render_transcript.py` (commit `98e5591`) is orthogonal
  in scope — covers Chat-thread transcript export, not handoff
  aggregation. Both tools live under `tools/handoffs/` and may share
  small helpers later; no Phase A coupling required
- CLAUDE.md §11 "Transcript Handoff" subsection (commit `dd65d9b`)
  describes a different artifact (Chat-thread transcripts). No conflict
  with handoff frontmatter schema; `suffix: transcript` integrates them
- ADR-007/008 (OCT contracts, YAML ontology) are unaffected — this
  plan governs `.claude/handoffs/` only, not `verticals/*/ontology/`
- Quality-gate hook scope (`mypy` on `^services/` only per CLAUDE.md §8)
  means Batch 1 tools must be mypy-checked manually before commit
  (same pattern as `render_transcript.py`)

## Alternatives Considered

### Alternative 1: Free-form frontmatter (no schema)

- **Pros:** Zero migration cost; no enforcement overhead
- **Cons:** Drift already evident (session 9 missing `actor:`, status
  values inconsistent); audit-cycle cost compounds session by session;
  dashboard reader cannot be reliably built on free-form input
- **Why rejected:** The drift problem is observable today, not
  speculative. Schema cost is paid once; free-form cost is paid every
  audit cycle.

### Alternative 2: Schema codified, but no validator + no reader

- **Pros:** Cheaper to land (docs only)
- **Cons:** Schema without validator drifts identically to free-form —
  human discipline alone has not held across sessions 9–12; dashboard
  reader is the consumer the schema exists to serve
- **Why rejected:** Schema must be machine-checked or it is decoration.
  Lesson #5 §3 schema-fidelity discipline applies recursively here.

### Alternative 3: Shell-based tooling (bash + yq)

- **Pros:** Lighter dependency; pre-commit hook integration trivial
- **Cons:** YAML parsing in shell is fragile; test coverage hard to
  build; reader logic (chain detection, group-by, references graph)
  exceeds shell's comfort zone; `render_transcript.py` precedent
  already sets Python (stdlib-only) as the in-repo scripting language
  for `tools/handoffs/`
- **Why rejected:** Reader complexity dominates the decision. Validator
  alone could plausibly be shell; reader cannot.

### Alternative 4: Place scripts under `scripts/` (not `tools/handoffs/`)

- **Pros:** Shorter import paths
- **Cons:** `tools/handoffs/render_transcript.py` is the established
  precedent for handoff-domain tooling; splitting handoff tools across
  two directories fragments discoverability and risks duplicating
  helpers
- **Why rejected:** Co-location with `render_transcript.py` wins.
  `tools/handoffs/` is the canonical home for handoff-domain tools.

### Alternative 5: Commit-track handoff files (un-gitignore)

- **Pros:** Retro-migration becomes a normal git change set; full audit
  history of frontmatter evolution
- **Cons:** Reverses Lesson #5 §4 explicit design decision; pollutes
  repo history with session-scoped working notes; conflicts with
  current Cowork + Code workflows that assume gitignored handoffs;
  forces every transcript export (already large) into git
- **Why rejected:** Lesson #5 §4 is a deliberate boundary, not an
  oversight. Treating handoffs as working tree only is the system
  design, and this plan must respect it. Note: PLAN-004 v2 Batch 2
  produces a thin git-tracked summary at `docs/logs/` recording that
  the migration completed (~15-30 lines). This does NOT track the
  handoff files themselves — only that the migration event happened.
  The summary respects the gitignored-by-design boundary while
  preserving audit-trail visibility.

### Alternative 6: Defer until session 12+

- **Pros:** Avoid mid-cycle work
- **Cons:** Session 10 has already produced enough volume (30+ files)
  that retro-migration is non-trivial now and grows monotonically;
  Lesson #6 pause-and-redispatch chains are first-observable in
  session 10 and benefit from dashboard codification while pattern
  is fresh
- **Why rejected:** Compound interest argument. Cheaper now than later.

### Alternative 7: Single-batch monolithic execution

- **Pros:** Atomic landing
- **Cons:** Dispatch covers ~7 new tracked files + ~50 working-tree
  amendments in one batch — high Code-judgment surface risk per
  Lesson #5 §3 schema-fidelity rule; if any anchor mismatches surface
  mid-execution, batch boundary blur makes rollback messy
- **Why rejected:** Session 10 three-dispatch cycle established that
  large dispatches are high-risk. Two-batch split isolates failure
  domains.

## Phase Structure

PLAN-004 is decomposed into three phases. Phase A is in-scope of this
plan; Phases B and C are forward-declared.

### Phase A — Schema + tooling + retro-migration (this plan, two batches)

Scope: D1–D6 above. Acceptance:
- Batch 1: pytest green, ruff clean, mypy clean on `tools/handoffs/`,
  PLAN-004 v2 + schema doc landed, STATUS bumped per Q4 spec
- Batch 2: `validate_handoff.py --all` returns exit 0 on full
  `.claude/handoffs/` tree; gitignored closeout + git-tracked summary
  both produced; single commit for the tracked summary

### Phase B — Automation (forward-declared)

- Wire validator into `.pre-commit-config.yaml` so new handoffs are
  checked at commit time (this requires either un-gitignoring at least
  the validator's check, or running validator in a way that doesn't
  depend on staging — open design question for Phase B)
- Add `tools/handoffs/handoff_status.py --watch` for live session
  monitoring during long sessions
- Generate `.claude/handoffs/session-NN/INDEX.md` auto-table per
  session (gitignored output, idempotent regeneration)

Out of scope for Phase A. Drafted as a future PLAN-004 amendment or
separate plan when Phase A has soaked for ≥1 session.

### Phase C — Optional polish (forward-declared)

- HTML or markdown dashboard rendered to `docs/` (web-readable; this
  WOULD be tracked, since it lives under `docs/`)
- References graph visualization (mermaid diagram of dispatch chains)
- Integration with `render_transcript.py` for unified session export

Explicitly optional. May never land if Phase A + B prove sufficient.

## Implementation Notes (Batch 1)

Code tab will be instructed via dispatch handoff. Expected commits:

1. `docs(plan): add PLAN-004 v2 — handoff frontmatter and dashboard`
   (this doc at `docs/plans/0004-handoff-frontmatter-and-dashboard.md`)
2. `docs: add handoff frontmatter schema`
   (`docs/conventions/handoff-frontmatter-schema.md`)
3. `feat(tools): add handoff validator + reader + schema module`
   (`tools/handoffs/{_schema,validate_handoff,handoff_status}.py`,
   `tests/handoffs/test_*.py`)
4. `docs(runbooks): cross-link transcript-handoff to PLAN-004 schema`
   (`docs/runbooks/transcript-handoff.md` §2 pointer update)
5. `docs: update CLAUDE.md §10 index + STATUS.md`
   (catch-up + head_commit bump per Q4 spec)

Batch 1 dispatch will spell out each file's exact content. Batch 2
dispatch is authored AFTER Batch 1 lands and validator is available
to drive migration.

**Note on `docs/logs/`:** If `docs/logs/` does not exist at Batch 2
time, Code creates it together with a `docs/logs/README.md` describing
purpose (thin git-tracked summaries of working-tree events that
require audit-trail visibility but whose detail lives outside repo
history; distinct from `docs/lessons/` which captures durable
patterns). The README + first log file lands in the single Batch 2
commit.

## References

- ADR-005 (strategic pivot to OCT)
- ADR-006 (vertical plugin architecture)
- Lesson #5 (tier-system audit 2026-05-15) — §1 (restart), §2 (Cray-
  direct + Code-judgment), §3 (schema-fidelity), §4 (handoffs
  gitignored by design)
- Lesson #6 (Code surface → Chat re-dispatch pattern)
- `docs/runbooks/claude-code-chat-handoff.md` (handoff file mechanism)
- `docs/runbooks/transcript-handoff.md` (transcript export tooling)
- `docs/conventions/chat_tab_instructions.md` (Tier 1 — anchor
  verification protocol)
- `docs/conventions/cowork_tab_instructions.md` (Tier 0)
- CLAUDE.md §11 (Tier 2 operations + Transcript Handoff subsection)
- `tools/handoffs/render_transcript.py` + tests (commit `98e5591`) —
  Python tooling precedent
- `docs/STATUS.md` Q4 subsection (`head_commit` semantics — substantive
  vs housekeeping)
- `.claude/handoffs/session-10/2026-05-18-1645-chat-session-handoff-to-new-thread.md`
  (PLAN-004 gating decisions captured)
- `.claude/handoffs/session-10/2026-05-16-2210-code-chat-sync-transcript-tooling.md`
  §2.4 (PLAN-004 Phase A new input — `suffix` extensibility flagged)
