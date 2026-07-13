# PLAN-0069: Axis-B v2 gate/schema build — warn→enforce graduation of the Stop-hook goal gate

**Status:** Ready (SD-A…SD-D ratified by Cray via AskUserQuestion 2026-07-13 — all four as-recommended: SD-A = 2 PRs, SD-B = same-PR/PR2, SD-C = no migration, SD-D = positional `amendments_seen`)
**Owner:** Claude Code
**Created:** 2026-07-13
**Related ADRs:** ADR-0018 (V2 Amendment, Accepted 2026-07-13 — the design of record; this PLAN implements, does not redesign), ADR-013 D1 (harness primitives are Code-built), ADR-009 D2 (only Code commits)

## Author≠reviewer disclosure (ADR-012 D4.3)

Drafted by the in-harness `plan-drafter` subagent under ADR-013 D1 phased
authority (outline originator: Code, session 2026-07-13 dispatch). Independent
review: **Code R2-reviews** against ADR-0018 §V2 + the cited code lines,
**Cray ratifies** the SURFACED decisions, **Code commits via PR** (ADR-009
D2). Separation: INTACT — drafter authored; reviewer/committer distinct.

## Goal

Graduate the Axis-B Stop-hook goal gate from v1 (warn-only, ADR-0018 D5) to
v2 (per-goal opt-in enforcement) by implementing the Accepted ADR-0018 V2
Amendment contracts (`docs/adr/0018-axis-b-verification-loop.md:853-879`):
`goal.json` schema_version → 2 with first-class `enforce: bool` (default
`false`) and append-only `amendments[]`; new status `blocked-pending-human`;
the deterministic drift/redirect/enforce ladder (V2-D2/V2-D3) at the gate;
V2-D4 evidence-missing-pauses semantics; trail instrumentation for the
promotion-evidence loop (V2-OQ-1); and `/goal` + `goal-evaluator` doc updates
— all deterministic-offline, stdlib-only, pytest-covered, with `enforce:
false` behavior byte-for-byte identical to v1.

## Ratified contract (LOCKED — ADR-0018 V2, SD-0…SD-4 Cray-ratified 2026-07-13; not re-decidable here)

- **L-1 (SD-1, V2-D1):** per-goal `enforce: bool`, default `false` = exact v1
  warn behavior; `schema_version` → 2.
- **L-2 (SD-2, V2-D2):** append-only `amendments[]` ratification log; entry
  shape fixed at `0018:761-770` (`ts`, `event` = `"typed" |
  "ask_user_question:<label>"`, `summary`, `prev_goal`, `new_goal`,
  `fingerprint`). Ratification = **typed Cray sign-off only** (a Stop-hook
  "proceed", a Code inference, or a subagent suggestion never qualifies).
  Divergence detection is **evaluator-detected, deterministically-
  consequenced**: the LLM writes the divergence verdict to the trail; the
  gate's drift/redirect/enforce rule is a **pure function of the on-disk
  verdict trail + `amendments[]` + `enforce`** — no LLM in the decision path
  (`0018:819-820`).
- **L-3 (V2-D3):** enforcing consequence = **one bounded block** (existing
  dispatch-block shape, chain-cap-8-counted; reason states failing criteria
  verbatim + remediate-or-ratify instruction), then on re-Stop still failing
  (or cap pressure) the Stop **fires** and the goal transitions to
  **`blocked-pending-human`** + loud Telegram. Never an unbounded loop (D4
  asymmetry stands).
- **L-4 (SD-4, V2-D4):** evidence-missing under `enforce: true` (evaluator
  unavailable, spawn failure, malformed verdict, INSUFFICIENT-EVIDENCE) →
  `blocked-pending-human`, **never a silent pass** and never
  `released-unevaluated`. Under `enforce: false` the v1 fail-open path is
  unchanged.
- **L-5 (SD-3, V2-D5):** scope = the goal-gate graduation ONLY. Sibling
  hooks are out (see Out of Scope).
- **L-6 (V2 build note 4):** `/goal` accepts the `enforce` flag and documents
  the amendment-recording step.
- **L-7 (`0018:712-714`):** gate/evaluator stay reasoning-blind +
  injection-resistant; the evaluator's **refute-not-bless mandate is
  unchanged** — v2 changes the *consequence* of its FAIL, not its mandate.

## Acceptance Criteria

- [ ] **AC-1 (build hazard i — silent-strip):** `enforce` and `amendments[]`
  are first-class fields on the `Goal` dataclass
  (`.claude/hooks/_goal_state.py:189-200`), emitted by `to_json`
  (`:202-214`) and parsed by `from_json` (`:216-241`) — because the module
  **ignores unknown fields on parse and drops them on rewrite** (`:36-37`)
  and `save_goal` atomic-replaces the whole document (`:276-297`). A
  round-trip test proves: a v2 goal with `enforce: true` + a non-empty
  `amendments[]`, loaded via `load_goal` and rewritten via `save_goal`
  (i.e., the gate's own rewrite path), preserves both fields exactly.
- [ ] **AC-2 (build hazard ii — status rejection):** `blocked-pending-human`
  is added to `VALID_STATUSES` (`_goal_state.py:59-62`); `Goal.from_json`
  parses it (v1 rejects any unknown status at `:225-227` → `None` →
  `load_goal` reports *no active goal*). A test proves a
  `blocked-pending-human` file loads as a real goal under v2 and that the
  gate stands down on it (`_goal_gate.py:316` — not `active`) **without**
  the goal ever transitioning to `passed`.
- [ ] **AC-3 (warn tier frozen):** `enforce: false` (and enforce-absent v1
  files) behavior is **byte-for-byte warn-only v1**: every pre-existing
  behavioral test in `tests/handoffs/test_goal_gate.py` /
  `test_goal_state.py` passes **unmodified** (new tests may be added;
  existing assertions may not be weakened), and a differential test asserts
  the gate's return value, status transitions, trail markers, and Telegram
  events are identical to v1 across all five flow outcomes (pass / check-
  FAIL warn / dispatch / fail-open release / judge-residue warn) for an
  `enforce: false` goal.
- [ ] **AC-4 (v1↔v2 reader skew):** test-matrix rows prove (a) the v2 parser
  reads a v1 file (no `enforce`, no `amendments`, `schema_version: 1`) with
  defaults `enforce=false`, `amendments=[]`, full v1 semantics; (b) the
  skew direction is pinned **fail-safe**: a v2 `blocked-pending-human` file
  under v1 parse rules (frozen as a fixture replicating `:225-227`
  semantics) degrades to stand-down — the gate stands down, it never
  blocks and never marks `passed` (ADR-0018 Reversibility, `0018:905-909`);
  and (c) a status unknown to v2 still yields `None` (the stand-down
  contract survives the next skew).
- [ ] **AC-5 (enforce ladder):** for an `enforce: true` goal with an
  evidence-backed FAIL (deterministic check FAIL, judge FAIL, or
  drift-without-ratification verdict): first Stop → exactly one block
  directive (dispatch-block shape, failing criteria verbatim,
  remediate-or-ratify instruction, marker trail entry); second consecutive
  failing Stop → no block, Stop fires, status → `blocked-pending-human` +
  loud Telegram. Tests prove the ladder never blocks twice for the same
  failing state.
- [ ] **AC-6 (never a silent pass):** under `enforce: true`, the unanswered-
  dispatch path (`_goal_gate.py:366-388`) and a recorded
  INSUFFICIENT-EVIDENCE verdict transition to `blocked-pending-human`
  (with an `UNAVAILABLE`/`INSUFFICIENT-EVIDENCE` trail entry + loud
  Telegram) — a test asserts `released-unevaluated` and `passed` are both
  unreachable from these states while `enforce: true`.
- [ ] **AC-7 (drift vs redirect, deterministic):** with a divergence verdict
  on the trail: a fresher amendment (per the SD-D freshness rule) → pass
  freely (redirect); no fresher amendment → warn (`enforce: false`) or
  ladder (`enforce: true`). Implemented as a pure function over the parsed
  artifact (no subprocess, no LLM, no clock ordering); tested with
  synthetic trails covering amendment-before-verdict,
  amendment-after-verdict, and no-amendment cases.
- [ ] **AC-8 (append-only + concurrency, V2-VX):** `amendments[]` writes go
  through the existing `save_goal` atomic-replace; a test row exercises the
  gate-rewrite-vs-appended-amendment interleaving and proves no amendment
  entry is ever dropped by a gate rewrite (composes with AC-1).
- [ ] **AC-9 (docs surface):** `.claude/commands/goal.md` documents the
  `enforce` flag, the v2 schema example, the amendment-recording procedure
  (typed sign-off → append), and `blocked-pending-human` handling;
  `.claude/agents/goal-evaluator.md` adds the V2-D2 divergence question
  ("does this turn's disk evidence serve the anchor?" — anchor = goal +
  latest ratified amendment) and its verdict field, with the
  refute-not-bless posture text unchanged.
- [ ] **AC-10 (suite + hygiene):** full `pytest tests/handoffs -q` green;
  hooks remain stdlib-only (no new imports beyond stdlib); ruff + mypy
  clean on touched files.

## Out of Scope

- ❌ **Sibling hooks (LOCKED, SD-3 / V2-D5):** the anti-duplicate pre-create
  `PreToolUse` check, the `SubagentStop` verification gate, per-turn
  re-injection — each is its own future PLAN/ADR (V2-OQ-3).
- ❌ Any default-flip of `enforce` (V2-OQ-1 promotion review comes first) and
  auto-`enforce: true` for PLAN-0010 unattended runs (V2-OQ-2).
- ❌ Axis-A surfaces: no `pretooluse_*_deny` hook changes, no classifier
  behavior, no commit-boundary mechanics (`0018:849-851` re-affirmed).
- ❌ Changes to the evaluator's tools, Write-narrowing hook, or mandate; the
  `pretooluse_goal_evaluator_write_deny.py` deny surface is regression-
  tested only, not modified.
- ❌ Migration tooling for on-disk `goal.json` (see SD-C — recommendation is
  no migration; forward-compat by tolerant defaults).
- ❌ Pydantic or any non-stdlib dependency in hooks.

## Surfaced decisions (RATIFIED 2026-07-13 — Cray, AskUserQuestion, all four as-recommended: SD-A = 2 PRs · SD-B = same-PR/PR2 · SD-C = no migration · SD-D = positional `amendments_seen`; the recommendations below are now LOCKED and load-bearing in the Steps)

- **SD-A — PR staging.** *Recommendation: two PRs.* PR1 = Step 1
  (`_goal_state.py` schema v2 + state tests — proves both build hazards
  closed in isolation); PR2 = Steps 2–5 (gate ladder + `/goal` + evaluator
  prompt + gate/skew/concurrency tests). Reason: bounded review; the schema
  contract is provable before consequence logic lands. Alternative: one PR
  (smaller total overhead; harder R2). Cray call because it sets the review
  workload and merge sequencing.
- **SD-B — evaluator prompt change ships in PR2 (same PR as the gate).**
  *Recommendation: same-PR.* The divergence-verdict field and the gate rule
  consuming it are one contract — split-landing leaves either dead gate code
  or an unread verdict field. Alternative: separate doc-only PR. Cray call
  because it touches a second trusted-surface file in a behavior PR.
- **SD-C — no migration of existing on-disk `goal.json`.** *Recommendation:
  none.* `goal.json` is gitignored, per-session, ephemeral; the v2 parser
  reads v1 files via tolerant defaults (AC-4a). Any goal active at merge
  time: `/goal clear` + re-declare. Alternative: a one-shot migration
  helper. Cray call because it defines what happens to a live goal on
  upgrade day.
- **SD-D — the freshness rule refinement.** The ADR pins the comparison
  operands (`amendments[-1].fingerprint` vs the last evaluation fingerprint,
  `0018:869-872`) but raw fingerprints are unordered hashes and equality
  misclassifies the common ratify-immediately-no-new-work case; wall-clock
  ordering is barred (WSL clock non-monotonic). *Recommendation:* positional
  freshness — each trail entry records `amendments_seen: int`
  (len(`amendments`) at write time; also serves build-note-3
  instrumentation); an amendment is *fresher* than a divergence verdict iff
  `len(amendments) > verdict_entry.amendments_seen`. Deterministic,
  clock-free, append-order-correct; refines (does not contradict) the ADR's
  stated comparison. Alternative: literal fingerprint equality/inequality.
  Cray call because it refines a mechanism stated in an Accepted ADR.

## Steps

### Step 1: schema v2 in `_goal_state.py` + state tests (PR1 under SD-A)

Modify `.claude/hooks/_goal_state.py`:

- `SCHEMA_VERSION = 2`; add `STATUS_BLOCKED_PENDING_HUMAN =
  "blocked-pending-human"` to `VALID_STATUSES` (hazard ii).
- New `Amendment` dataclass with exactly the L-2 fields
  (`ts`/`event`/`summary`/`prev_goal`/`new_goal`/`fingerprint`), tolerant
  `from_json` (junk entries skipped, like `_parse_criteria`), full `to_json`.
- `Goal` gains first-class `enforce: bool = False` and `amendments:
  list[Amendment] = []` (hazard i); `to_json` always emits both; `from_json`
  defaults them when absent (v1 files); keep `schema_version` passthrough.
- `Evaluation` gains optional instrumentation fields per SD-D + build note 3:
  `amendments_seen: int` and an optional `divergence` dict (`verdict`
  `ALIGNED|DIVERGENT`, `reason`, optional `introduced_fingerprint` for
  catch-latency where recoverable). Exact field names are Code-shape
  (`0018:855-856` delegates exact code shape to this PLAN; R2 may rename
  without re-ratification, semantics fixed).

Tests (`tests/handoffs/test_goal_state.py`): AC-1 round-trip, AC-2 status
parse, AC-4 skew rows (a)(c) + the frozen v1-rules fixture for (b), AC-8
append-only interleaving.

**Pre-committed pass/fail:** `pytest tests/handoffs/test_goal_state.py -q`
exits 0 with the new tests present and every pre-existing test unmodified;
grep confirms `blocked-pending-human` in `VALID_STATUSES` and
`enforce`/`amendments` in the `Goal` dataclass body.

### Step 2: the gate ladder in `_goal_gate.py` + gate tests (PR2)

The three currently-non-blocking `return None` sites are the graduation
surface — under `enforce: true` **only**:

1. **Deterministic-check FAIL (`:343-349`):** ladder step 1 — append a new
   `GATE_ENFORCE_BLOCK_MARKER` trail entry + return a block directive
   (dispatch-block shape; reason = failing criteria verbatim +
   remediate-or-obtain-typed-ratification instruction, template constant
   in-module per the `_EVALUATOR_DISPATCH_TEMPLATE` precedent). If the last
   gate marker is already `GATE_ENFORCE_BLOCK_MARKER` and the state still
   fails → ladder step 2: status → `blocked-pending-human`, trail entry,
   loud Telegram, `return None` (Stop fires).
2. **Judge FAIL / IE / drift-without-ratification with no new work
   (`:389-396`):** same two-step ladder. Drift/redirect is decided first via
   the SD-D pure function over
   (latest divergence verdict, `amendments`, `enforce`): fresher amendment →
   redirect, pass freely (the anchor is already updated); else drift.
3. **Unanswered dispatch / fail-open release (`:366-388`):** under
   `enforce: true`, go **directly** to `blocked-pending-human` +
   `UNAVAILABLE` trail entry + loud Telegram (V2-D4 — no block step,
   no `released-unevaluated`). `enforce: false` keeps the v1 path verbatim.

Guards: `enforce: false` takes the exact v1 code paths (AC-3 differential
test); gate entry keeps standing down on non-`active` statuses (`:316`), so
`blocked-pending-human` self-quiesces; chain-cap interplay (the gate runs
after the cap check) is a verify-at-execution row — if cap pressure
suppresses the step-1 block, the next Stop's step-2 pause still fires.

**Pre-committed pass/fail:** `pytest tests/handoffs/test_goal_gate.py -q`
exits 0; AC-3/5/6/7 test names present; zero pre-existing assertions
weakened (diff review at R2).

### Step 3: `/goal` command update (`.claude/commands/goal.md`, PR2)

Document: the `enforce` flag at declaration (`argument-hint` + schema example
→ v2 with `enforce`/`amendments`); the amendment-recording procedure (on a
typed Cray sign-off changing the goal, the **main agent** appends the L-2
entry with the current `work_fingerprint()` — the one addition to its write
surface; `evaluations[]`/`status` stay off-limits, except status→`active`
reactivation which itself requires a typed Cray sign-off recorded as an
amendment); `blocked-pending-human` handling (clear, re-declare, or
ratify-to-reactivate); update the warn-only-v1 confirmation text to state
the per-goal tier.

**Pre-committed pass/fail:** grep `goal.md` for `enforce`, `amendments`,
`blocked-pending-human` — all present; no git-op/secret rule changes.

### Step 4: `goal-evaluator` prompt update (`.claude/agents/goal-evaluator.md`, PR2 per SD-B)

Add the V2-D2 divergence assessment: "does this turn's disk evidence serve
the **anchor** (goal statement + latest ratified amendment)?" — verdict
written into the appended trail entry's `divergence` field (its only power;
it still cannot block, release, or ratify). Update the "Warn-only v1" line
to state that consequences are the deterministic gate's, per-goal. The
refute-not-bless posture section is **unchanged** (L-7); tools,
Write-narrowing, `maxTurns` untouched.

**Pre-committed pass/fail:** grep confirms `anchor` + `divergence` present
AND the literal "refute" posture heading unchanged;
`tests/handoffs/test_pretooluse_goal_evaluator_write_deny.py` passes
unmodified (deny surface untouched).

### Step 5: closeout sweep (PR2)

Full `pytest tests/handoffs -q` + ruff/mypy on touched files; R2 review
against ADR-0018 §V2 line-by-line (contracts L-1…L-7); confirm AC checklist;
after merge, `git mv docs/plans/0069-*.md docs/plans/done/` + STATUS
reconcile per Plan Flow.

**Pre-committed pass/fail:** suite exit 0; every AC box checkable with a
named test or grep.

## Verification

The offline oracle is the gate (CLAUDE.md §8): all ACs are answerable by
pytest exit codes + greps — no live model, no MS-S1, no host-state change.
The two verified build hazards each have a dedicated failing-first test
(AC-1, AC-2); warn-tier freezing is proven differentially (AC-3);
enforcement teeth are proven as *bounded* (AC-5) and *never silently
passing* (AC-6). V2-VX residues (amendments concurrency, reader skew) are
explicit matrix rows (AC-4, AC-8). Trail instrumentation (Step 1) makes
V2-OQ-1's promotion-evidence review measurable from our own `evaluations[]`
trail — this PLAN builds the sensor-with-a-brake; flipping any default stays
out of scope.
