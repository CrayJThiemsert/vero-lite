# PLAN-0097: A durable trail entry on the goal gate's warn path

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-07-30
**Related ADRs:** ADR-0018 (Axis-B verification loop — D1, D5, §Minimal-prototype spec, §V2 Amendment)

> **Drafting provenance + author≠reviewer disclosure (ADR-012 D4.3).** Drafted
> (uncommitted) by the in-harness `plan-drafter` subagent (ADR-013 D1 phased
> authority) from a Code-authored dispatch (session 194; fact-pack verified by
> Code on `main` = `ad1eca1` immediately pre-dispatch, every line cite
> re-confirmed on disk by the drafter). Outline originator: Code. Independent
> reviewer: Cray at PR merge (Code performs the R2 fact-check + commits per
> ADR-009 D2). Separation: **INTACT** — author (plan-drafter), reviewer/committer
> (Code), ratifier (Cray) are three distinct actors. All `file:line` cites below
> are at `main` = `ad1eca1`; line numbers drift — re-verify at execution.

---

## The ADR-0018 determination (made first, per dispatch)

**Question:** does adding a trail entry to the warn path change behaviour that
ADR-0018 ratified?

**Determination: NO** — a gate-written trail entry on the warn path changes no
ratified *consequence*, and the ratified descriptions of the warn tier
affirmatively include annotation. The change is licensed by ADR-0018's own
Decision text. Because the ADR's two normative sections genuinely diverge on
this point (shown honestly below), the determination was surfaced as **SD-1**
for Cray's ruling — **ruled 2026-07-30, session 194: Cray typed (ก) = option
(a), the no-amendment reading (see Step 0 / SD-1)** — with a contingency
amendment drafted in **Appendix A** (NOT applied; superseded by that ruling —
`docs/adr/0018-*.md` is untouched by this PLAN).

### What is ratified as the warn-tier consequence (untouched by this PLAN)

- **D5:** *"It never hard-blocks a stop in v1."* and *"…**lets the Stop
  fire**."*
- The code docstring carries the same ratified consequence:
  `_goal_gate.py:438-439` — *"else warn-only (v1 — the stop fires)"* — and
  `stop_continuation.py:600` documents the composition: *"None = no active
  goal / warn-only outcome -> classifier flow unchanged."*

Every AC below preserves this: the warn path returns `None`, the Stop fires,
status stays `active`.

### What the ratified text says about recording on that tier

- **D5 (§"How hard"), verbatim:** *"v1 is **warn + annotate**: on a FAIL or
  `released-unevaluated` verdict the gate fires Telegram, **records the
  verdict trail in the goal file**, and **lets the Stop fire**."* — the
  ratified warn consequence is a three-part bundle, and the middle part is
  recording.
- **§V2 Amendment, V2-D1, verbatim:** *"**`enforce: false` (default):**
  exactly v1 behavior — **warn + annotate + Telegram**, the Stop fires."* —
  the 2026-07-13 amendment, ratified with the warn path already built,
  *re-describes* the default tier as warn **+ annotate** + Telegram. The
  shipped warn branch (`_goal_gate.py:445-446`) implements Telegram only.
- **D1, verbatim:** *"The gate runs these as subprocesses and **records
  per-criterion pass/fail**. Cheap, fast, un-arguable."* — unconditional; the
  current warn branch computes the per-criterion results and discards them
  (only a Telegram detail string leaves the machine).
- **§Minimal-prototype spec step 2, verbatim:** *"**Run `check` criteria**
  (subprocess, per-criterion `timeout_s`, total budget capped — VX-2);
  **record results**."*
- **Purpose texts:** Consequences/Positive — *"**The verdict trail is durable
  evidence** — closeouts cite it; drift between claimed and verified
  completion becomes visible"* — and D7 — closeouts *"may cite the gate's
  verdict trail as evidence."* A trail that omits exactly the red mid-work
  entries cannot serve either sentence: the red check **is** the
  drift-visibility case.

### The counter-reading, stated honestly

- **§Minimal-prototype spec step 5, verbatim:** *"**FAIL verdict recorded
  (either layer), or fingerprint unchanged** → **do not block** (D5): Telegram
  warn with per-criterion summary, leave `status: "active"`, fall through
  (stop fires)."* — the step-5 action list does **not** include writing a
  trail entry, and the implementation follows this list faithfully.
- The V2 Amendment's R2 review read the warn path as-is (*"Live code read for
  this amendment: `.claude/hooks/_goal_gate.py` (warn path, …)"*) and amended
  around it without flagging the missing annotation — evidence the silence
  was at least *tolerated* by the V2 process.
- V2 §Consequences/Neutral: *"warn-tier behavior is byte-for-byte v1."*

### Why NO wins

1. The step-5 sketch is the *projection* of the decisions; it cannot repeal
   the D5 decision text it projects. What Cray ratified twice — at v1
   (2026-06-10) and again in V2-D1 (2026-07-13) — is the phrase **"warn +
   annotate."** The omission lives only in the sketch's action list.
2. *"Byte-for-byte v1"* is a **historical neutrality claim about what the V2
   amendment changed** (nothing, at warn tier), not a freeze on the warn
   tier; and the v1 it points back to is D5's, whose own words include
   annotation.
3. The ratified *consequence* — never hard-block, the Stop fires — is
   untouched. This PLAN's design (below) makes "untouched" a **provable
   invariant**, not a hope: warn entries are structurally invisible to the
   gate's decision function (AC-3).

### The "ADR-0018 question, not a Code patch" claim, tested (not inherited)

The standing warn-path TODO in `docs/STATUS.md` §'Active TODOs' asserts
*"changing it is an ADR-0018 question routed through Cowork, not a Code
patch."* (Cited by section, not line: the R7 citation guard caught this
draft's own line-number cite — the same rot class a sibling PR was
concurrently repairing in ADR-0025.) **Upheld in routing** — a new PLAN is
mechanically drafter-routed regardless (CLAUDE.md §6) — but the **premise is
corrected**: what `:438-439` ratifies is the *consequence* ("the stop
fires"), not the absence of a record. The absence of a record is a
spec-step-5 implementation artifact that D5's and V2-D1's own "annotate"
wording speaks against. STATUS's recommended shape (*"a trail entry on the
warn path (no consequence change)"*) is independently re-derived here and
confirmed.

---

## Goal

Give the goal gate's most frequently travelled branch — a red `check` or
unresolved judge residue under the default `enforce: false` posture — a
durable, on-disk trail entry, so the Axis-B loop is auditable after the fact.
Today that branch's only signal is a best-effort Telegram ping that leaves
the machine and **no-ops silently** when the script is absent
(`_goal_gate.py:152-153`); the gate file contains **zero logging statements**
(verified: a case-insensitive grep for `log` across all 566 lines returns
nothing), so the trail entry is not "one more log line" — it is the branch's
*only* durable record. Both `_failing_consequence` call sites are covered
(`:491-494` deterministic check failure; `:565` judge FAIL /
INSUFFICIENT-EVIDENCE / unredirected drift with no new work). The ratified
consequence — the Stop fires, never a block on the warn tier — is preserved
and *proven* preserved. The mechanism reused is already safe:
`record_evaluation` is append-only (`_goal_state.py:438-442`) and `save_goal`
writes atomically (`:396-417`); nothing new is invented.

**Elimination was considered and rejected** (the dispatch explicitly
permitted a "leave it silent, record why" outcome): leaving the branch silent
is defensible only if byte-parity with the shipped v1 outranks auditability —
but ADR-0018's purpose texts (D7, Consequences) make the trail the durable
evidence closeouts cite, the s182 incident cost a forensic reconstruction
(`sort_keys` key-order analysis proved the file had never been written —
archived at `.claude/handoffs/session-186/evidence/goal-s182-openq2-evidence.json`,
verified present), and unattended PLAN-0010 runs are exactly where a red
check must not evaporate with a lost ping. SD-1 = (c) was the elimination
exit; it was **not taken** — Cray ratified (a) (see Step 0).

## Acceptance Criteria

Execution was gated on **SD-1 = (a)**; that gate is **discharged** — Cray
typed (a), session 194 (Step 0). SD-2/SD-3 remain open and their contingent
ACs say so. Every AC names the mutation
that reddens it (CLAUDE.md §8 non-vacuity discipline — the red must be SEEN,
restore-from-`/tmp`-copy, never `git checkout`). **No AC may be satisfied by
mocking `record_evaluation` or `save_goal`** — those are the things under
test; every trail assertion reloads the goal file **from disk** via
`load_goal(goal_file)`, the same read path the next Stop's gate uses.

- [ ] **AC-1 — check-fail site (`:491-494`) records.** Scenario-shaped: real
  `run_goal_gate({})` against a real on-disk goal file (tmp
  `CLAUDE_GOAL_PATH` via the existing `gate_env` fixture,
  `tests/handoffs/test_goal_gate.py:90-103`), a real subprocess check that
  exits 1 (`_check_fail` helper). Asserts: return `None` (the Stop fires);
  reloaded-from-disk status still `active`; `evaluations[-1].evaluator ==
  GATE_WARN_MARKER`; `deterministic` carries the per-criterion result
  (`{"C1": "fail"}`); `fingerprint` recorded; ping events exactly `["warn"]`.
  **Mutation M1:** delete the `_record_warn(...)` call in the warn arm → the
  on-disk `evaluations` stays `[]` → red. *Vacuity counterexample check:* an
  assertion on the seeded in-memory `Goal` object would survive M1 — which is
  why the AC mandates the disk reload; a mocked `save_goal` cannot fake it.
- [ ] **AC-2 — judge-residue/drift site (`:565`) records.** Parametrized:
  (a) checks green + a seeded evaluator FAIL verdict at the pinned
  fingerprint (no new work); (b) `enforce: false` DIVERGENT drift (the
  `test_drift_under_enforce_false_warns` seed shape). Both: return `None` +
  an on-disk warn entry. **Mutation M2 (site-independence):** revert site 1
  only — replace the `:491-494` call with the old inline two-liner
  (ping + `return None`) → AC-1 reds while AC-2 stays green; **M2b:** the
  symmetric revert at `:565` → AC-2 reds while AC-1 stays green. This proves
  each call site is *independently* oracled (a single-site fix cannot pass).
- [ ] **AC-3 — decision invariance (the "purely additive" proof).** The
  gate's decision function is invariant under warn-entry insertion. Two named
  corners, both currently untested (their "today" baseline is derived by code
  reading — see Residual gaps): **(i) the flake corner** — a warn entry at
  fp-A, checks now green (flake), judge unresolved, fingerprint still fp-A →
  the gate must still **DISPATCH** (as today, where the trail would be
  empty → `work_changed` true at `:498`); **(ii) the enforce-flip corner** —
  trail `[enforce_block, warn]` (a warn-tier interlude), goal re-amended
  `enforce: true`, still failing → the gate must still **PARK**, not issue a
  second block (`_last_was_enforce_block`, `:372-380`, must see through the
  warn entry). **Mutation M3:** drop the warn-marker exclusion from the
  `last` read feeding `:498`/`:515` → corner (i) warns instead of
  dispatching → red. **Mutation M3b:** drop it from `_last_was_enforce_block`
  → corner (ii) double-blocks → red. *NB:* AC-3 alone would pass with
  recording deleted wholesale (no warn entries → trivially invariant) — it is
  non-vacuous only jointly with AC-1/AC-2; M3/M3b are its own reddeners.
- [ ] **AC-4 — bounded growth (dedup, contingent on SD-3 = dedup).** Two
  consecutive gate runs in the same failing state at the same pinned
  fingerprint append **exactly one** warn entry (exact-count assert, not
  `>= 1`); re-pin the fingerprint to fp-B (a new failing state) → a second
  entry; an empty fingerprint (`""` — git failure) always records (fail
  toward recording, mirroring `work_fingerprint()`'s fail-toward-evaluating
  contract). **Mutation M4:** delete the dedup guard → count 2 → red. (M1
  reds it at count 0.)
- [ ] **AC-5 — durable when the off-machine channel is dead.** With
  `CLAUDE_TELEGRAM_SCRIPT` pointed at a nonexistent path and `_ping_telegram`
  **not** monkeypatched (the real function silently no-ops,
  `_goal_gate.py:152-153` — dispatch fact 8), the on-disk warn entry still
  lands. This is the branch's defect in miniature: the record must not ride
  on the ping. **Mutation M5 = M1 under this fixture** — proves the disk
  record exists independently of the ping path.
- [ ] **AC-6 — regression inventory: zero silent edits to existing tests.**
  The entire existing `tests/handoffs/test_goal_gate.py` suite passes
  **unmodified**. Pre-verified inventory (this draft): the warn-branch tests
  assert pings/status/detail but never trail-emptiness —
  `test_check_fail_warns_never_blocks` (`:162`),
  `test_missing_timeout_is_invalid_and_warns` (`:170`),
  `test_drift_under_enforce_false_warns` (`:492`),
  `test_enforce_is_the_only_pivot_for_check_fail` (`:502-514`) — all stay
  green. If any existing assertion needs editing, that is STOP-and-surface
  to Cray, not a silent edit. `test_goal_state.py` gains only the SD-2
  round-trip tests; `test_stop_continuation.py` / `test_phase2_integration.py`
  untouched. **Mutation M6:** restructure so the warn recording also fires
  under `enforce: true` (collapse the else) → the existing ladder tests
  (`test_check_fail_blocks_once_then_parks`,
  `test_never_blocks_twice_for_same_state`) redden because the ladder's
  last-entry bookkeeping breaks → red, proving the enforce tier is fenced.
- [ ] **AC-7 — offline gate + isolation constraint.** Full offline gate green
  at CI scope (full `pytest tests/`, `ruff`, `mypy services/` — not the
  changed subset). Every new test uses the `gate_env` fixture, which pins
  `CLAUDE_GOAL_PATH` to `tmp_path` — **no test may read or write the real
  `.claude/state/goal.json`** (dispatch fact 13: a live `ACTIVE` goal file
  leaks into gate tests and makes them pass or fail for the wrong reason).
  Mutation: n/a — this AC is the oracle-of-oracles; its teeth are AC-1…AC-6's
  mutations run under it.

**Scenario-test statement (CLAUDE.md §8, binding):** AC-1/AC-2/AC-5 drive the
**real producer into the real consumer on realistic simulated data** — real
`run_goal_gate` → real subprocess checks → real `record_evaluation` +
`save_goal` atomic write → reload via real `load_goal` from the real file (the
next Stop's own read path), seeded with a goal shaped like the archived s182
evidence artifact (`enforce: false`, real `check` criteria). The only pinned
seams are `work_fingerprint` (a test-controlled *input*, established fixture
precedent at `:102`) and the Telegram capture — and AC-5 unpins even that.
Nothing on either side of the seam under test is stubbed. The implementation
therefore sits behind a **strong offline oracle**; a wrong implementation move
is caught by the suite, and the ACs lean on that. (The *governance
determination* above enjoys no such oracle — which is why it is SD-1, not a
Code judgment call.)

## Out of Scope

- ❌ **Any change to the warn consequence.** The Stop still fires; the warn
  tier never blocks. (D5 ratified; also the dispatch's hard boundary.)
- ❌ **The enforce ladder** — rungs, markers, park semantics, templates:
  byte-untouched (`_issue_enforce_block`, `_park_blocked_pending_human`).
- ❌ **Logging infrastructure.** No `logging` import, no log files. The trail
  entry *is* the record; the file's zero-logging posture is preserved.
- ❌ **Telegram changes.** The ping's event name, content, and best-effort
  no-op contract are unchanged; the only delta is that the record is written
  before it.
- ❌ **Editing `docs/adr/0018-axis-b-verification-loop.md`.** Appendix A is
  proposal text living in this PLAN; applying it (only if SD-1 = (b)) is a
  separate Cray-ratified amendment route.
- ❌ **`schema_version` bump.** No new status value, no consequence-bearing
  field; SD-2's optional `detail` follows the `divergence` optional-emission
  precedent within version 2. Skew direction if declined: none; if adopted: a
  stale reader drops `detail` on rewrite — an annotation loss, never a
  consequence change (named residual, SD-2).
- ❌ PR-merge gating, the V2-D5 sibling hooks, `/goal` command changes,
  chain-cap semantics.

## Design (the build surface)

All in `.claude/hooks/`; ~25 lines of production delta.

1. **Marker (the sixth constant, `_goal_gate.py:101-106` family):**
   `GATE_WARN_MARKER = "_goal_gate:warn"`. Rationale: matches the Telegram
   event label `warn` (one grep finds both signals of the same event) and the
   `_goal_gate:` family prefix keeps it disjoint from evaluator verdicts
   (`_latest_verdicts` filters on `EVALUATOR_NAME`, so a warn entry can never
   read as a verdict — verified at `:250-260`).
2. **`_record_warn(goal, fingerprint, deterministic, detail)` helper:** dedup
   guard (SD-3) → `record_evaluation(...)` with
   `ts/fingerprint/deterministic/amendments_seen/evaluator=GATE_WARN_MARKER`
   (+ `detail` per SD-2) → `save_goal(goal)`. Called from
   **`_failing_consequence`'s warn arm only** — which covers **both** call
   sites (`:491-494`, `:565`) by construction, since `_failing_consequence`
   is the sole warn route (verified: exactly two references in the file).
   AC-2's M2/M2b still oracle each site independently.
3. **Ordering: record → save → ping.** The durable record must not depend on
   the best-effort off-machine channel; mirrors
   `_park_blocked_pending_human`'s record-then-ping shape (`:406-430`).
   Enforced by AC-5's dead-channel fixture + review.
4. **Warn entries are annotations — structurally invisible to control flow.**
   A helper (e.g. `_last_decision_evaluation(goal)`) returns the last
   non-warn-marker entry and replaces the raw `goal.last_evaluation()` read
   at `:468` (feeding both the `work_changed` comparison at `:498` and the
   unanswered-dispatch check at `:515`) **and** inside
   `_last_was_enforce_block` (`:372-380`). Only the dedup guard reads warn
   entries. **Why this is load-bearing:** without the exclusion, a warn
   entry's fingerprint would suppress an evaluator dispatch in the
   flaky-check/same-fingerprint corner and hide the dispatch/enforce-block
   markers from the step-6/ladder reads — i.e., it would change *whether a
   Stop fires* in corner cases, which is precisely the consequence change
   this PLAN must not make. The exclusion converts "purely additive" from a
   claim into an invariant the suite proves (AC-3).
5. **Self-trigger impossibility (no new hazard):** `goal.json` is gitignored,
   so the warn-path `save_goal` cannot perturb `work_fingerprint()` —
   documented in the fingerprint docstring (`:172-178`); the recording cannot
   cause a re-dispatch by itself.
6. **Docstring updates (in-scope, same file):** module docstring step 5 gains
   the trail entry; the "enforce parity (PLAN-0069 AC-3)" paragraph
   (`:41-44`) is updated — its "trail markers … identical to v1" sentence
   becomes stale the moment this lands, and leaving it would be a
   doc-vs-code forward-reference defect.
7. **SD-2 (if adopted), `_goal_state.py`:** `detail: str = ""` as a
   **first-class** `Evaluation` field (the V2 build hazard is explicit:
   unknown fields are dropped on rewrite — `_goal_state.py:43-50` — so a
   non-first-class field would be silently stripped), emitted in `to_json`
   only when non-empty (the `divergence` precedent, `:220-221`), tolerant on
   parse. Carries the same string the Telegram ping carries: the on-disk
   record must not be poorer than the signal that leaves the machine.

## Steps

### Step 0: Cray adjudication (gated everything — SD-1 DISCHARGED)

> **DISCHARGED 2026-07-30 (session 194): Cray typed (ก) = option (a).**
> D5 controls — the trail entry is licensed by ADR-0018 as-is (D5 + V2-D1's
> "warn + annotate" wording; the spec-step-5 sketch does not repeal the
> Decision text it projects); no amendment needed. This is Cray's typed
> ratification (relayed via the session-194 correction dispatch), not a Code
> inference. Execution proceeds down exit (a). **SD-2 and SD-3 were NOT
> ruled on and remain OPEN** — this ruling covers SD-1 only; present SD-2
> before Step 1 and SD-3 before the Step 2 dedup wiring.

The three exits as surfaced — (a) taken; (b)/(c) considered and not taken:
- **(a) no-amendment reading ratified** → execute Steps 1–5. **← TAKEN.**
- **(b) spec-step-5 controlling; amend first** → route Appendix A through the
  amendment process (drafter-authored, Code-committed, Cray-ratified — the
  ADR-0016/0018 dated-amendment shape); Steps 1–5 execute only after it
  merges. *Not taken.*
- **(c) eliminate — the silence is the design** → no build. Record the ruling:
  close the warn-path row in `docs/STATUS.md` §'Active TODOs' citing this
  PLAN §Determination, set this PLAN `Status: Complete` (closure-without-build
  noted in-file), archive to `done/`. The dispatch pre-authorized this
  outcome. *Not taken.*

### Step 1: Schema (contingent on SD-2)

`_goal_state.py`: optional first-class `Evaluation.detail` per Design 7.
Tests in `test_goal_state.py`: round-trip (non-empty emitted, empty omitted),
tolerant parse of a legacy entry without the key. **Mutation:** drop `detail`
from `to_json` → round-trip test red.

### Step 2: The gate

`_goal_gate.py`: `GATE_WARN_MARKER`; `_record_warn` (Design 2–3, dedup per
SD-3); warn-arm wiring in `_failing_consequence`; `_last_decision_evaluation`
exclusion (Design 4) at `:468` and in `_last_was_enforce_block`; docstring
updates (Design 6). No other function touched.

### Step 3: Tests

New `TestWarnPathTrail` class in `tests/handoffs/test_goal_gate.py`
implementing AC-1…AC-5 on the `gate_env` fixture (AC-7 isolation is inherited
from the fixture). AC-6 inventory run: full existing suite, zero edits.

### Step 4: Non-vacuity mutation sweep

Run M1, M2, M2b, M3, M3b, M4, M6 (and Step 1's) **fresh**: apply mutation →
SEE the named test red → restore from a `/tmp` copy (never `git checkout` —
it wipes the edit under test and manufactures a false PASS). Record the
red/green pairs in the PR body.

### Step 5: Gate, PR, closeout

Full offline gate at CI scope (AC-7). Branch `feat/plan0097-goal-gate-warn-trail`
→ PR → merge (Code commits; ADR-009 D2). Closeout: rewrite the
warn-path row in `docs/STATUS.md` §'Active TODOs' (diagnosed s183 → fixed,
cite PR + this PLAN), tick ACs, `Status: Complete`
(kept `Draft` until this moment — an `Accepted`-status PLAN G1-gates its own
closeout), `git mv` to `docs/plans/done/`.

## Verification

- **The offline oracle is the gate** (CLAUDE.md §8): the suite runs the real
  gate against real on-disk goal files end-to-end; AC-1…AC-6 with their named
  mutations are the pass/fail read, fixed here before the run. No live run,
  no host-state surface (nothing touches MS-S1; no §8 host-state approval
  needed).
- **Post-merge observable (bonus, not the gate):** the next genuine red-check
  Stop leaves a `_goal_gate:warn` entry in `.claude/state/goal.json` — the
  s182 forensic ("was the file ever written?") becomes a one-line grep.
- **What "done" looks like:** a red check mid-work under default posture
  leaves the same class of durable, append-only, atomically-written evidence
  as every other gate outcome — and the gate's decisions are provably
  identical to before, warn entries stripped or not.

## Surfaced decisions (SD-1 RULED; SD-2/SD-3 remain open for Cray)

- **SD-1 — the ADR-0018 ruling. RATIFIED 2026-07-30 (session 194): Cray
  typed (ก) = option (a).** D5 controls; the trail entry is licensed by
  ADR-0018 as-is (D5 + V2-D1's "warn + annotate" wording); the spec-step-5
  sketch does not repeal the Decision text it projects; no amendment needed.
  Recorded as Cray's typed ratification (relayed via the session-194
  correction dispatch) — not a Code inference. The surfacing as drafted,
  kept for the record: *Question:* is the warn-path trail entry
  licensed by ADR-0018 as-is? *Recommendation:* **(a)** yes — D5's and
  V2-D1's ratified "warn + annotate" wording licenses it; no amendment
  (reasoning + full quotes in §Determination). *Alternatives:* **(b)** rule
  spec step 5's action list controlling → apply Appendix A first;
  **(c)** rule the silence the design → eliminate (no build, record why).
  *Why Cray:* two normative sections of an Accepted ADR diverge; deciding
  which controls is ratification authority, and no test suite catches a
  wrong governance reading (the dispatch's no-accelerator clause).
- **SD-2 — the `detail` field.** *Question:* should the warn entry carry the
  human-readable detail string (what Telegram gets)? *Recommendation:* yes —
  optional first-class `Evaluation.detail`, emitted when non-empty; without
  it a `:565` entry cannot distinguish drift from judge-residue, and the
  on-disk record would be poorer than the off-machine ping this PLAN exists
  to back up. *Alternative:* marker + `deterministic` only (smaller diff,
  `_goal_state.py` untouched). *Why Cray:* it changes the shared schema
  module all three writers (gate, evaluator, `/goal`) use, and accepts a
  named skew residual.
- **SD-3 — dedup vs always-append.** *Question:* one warn entry per distinct
  failing state, or one per Stop? *Recommendation:* dedup on (warn-marker,
  same non-empty fingerprint) — bounds trail noise in a Stop-looping session,
  mirrors the ladder's at-most-once-per-state bound (`_last_was_enforce_block`);
  empty fingerprint always records. Cost: a check flake at an identical
  fingerprint collapses into one entry. *Alternative:* always-append (a
  complete per-Stop observation log, unbounded within a session). *Why Cray:*
  this decides what the audit record *means* — and the record's semantics are
  the deliverable of this PLAN.

## Residual gaps

- The AC-3 corner baselines ("today the flake corner dispatches"; "today the
  enforce-flip corner parks") are derived by code reading — no existing test
  covers either corner. AC-3 *creates* those tests; if execution finds the
  analytic baseline wrong, STOP-and-surface before wiring the exclusion.
- PLAN-0069's AC-3 parity property ("trail markers identical to v1") is
  intentionally moved by this PLAN; Design 6 updates the docstring that
  states it, and AC-6/M6 re-fence what the property actually protected (the
  enforce tier). If a committed test elsewhere asserts the literal parity
  sentence, Step 3's inventory will catch it → STOP-and-surface.

## Appendix A — contingency amendment text (NOT applied — SUPERSEDED by SD-1 = (a))

> **Superseded 2026-07-30 (session 194):** Cray ratified SD-1 = (a) — no
> amendment is needed and `docs/adr/0018-axis-b-verification-loop.md` stays
> untouched. Retained unapplied so a later reader sees the fork that existed
> and why it closed; it would have applied only under SD-1 = (b).

> To be appended to `docs/adr/0018-axis-b-verification-loop.md` as a dated
> section, per the ADR-0016/0018 in-place dated-amendment precedent
> ("extends, does not reverse or renumber"). Draft text:

```markdown
## V2.1 Amendment (2026-MM-DD): the warn path's "annotate" made concrete

> **Extends, does not reverse.** D5 and V2-D1 describe the default tier as
> "warn + annotate"; §Minimal-prototype spec step 5's action list omitted the
> annotation. This amendment resolves that internal divergence in favor of
> the Decision text: on every warn outcome (both `_failing_consequence`
> routes — deterministic check failure, and judge FAIL / INSUFFICIENT-
> EVIDENCE / unredirected drift with no new work) the gate appends a
> gate-marked trail entry (marker `_goal_gate:warn`) carrying the
> per-criterion deterministic results and the work fingerprint, then saves
> atomically, then pings Telegram. Spec step 5 is amended to read:
> "…Telegram warn with per-criterion summary, **append a warn-marker trail
> entry**, leave `status: "active"`, fall through (stop fires)." Warn entries
> are annotations: excluded from the gate's control-flow reads (the
> work-since-last-evaluation comparison, the unanswered-dispatch check, the
> enforce ladder's last-entry bound), so the gate's decision function is
> invariant under their insertion. The ratified consequence is unchanged: the
> warn tier never blocks; the Stop fires. Build + tests: PLAN-0097.
```

## References

- **ADR-0018** — D1, D5, D7, §Minimal-prototype spec steps 2/5, §V2 Amendment
  (V2-D1, §Consequences/Neutral, §Amendment references) — all quotes verbatim
  from the file at `ad1eca1`.
- **Code (all at `ad1eca1`):** `.claude/hooks/_goal_gate.py` (`:101-106`
  markers; `:152-153` Telegram no-op; `:172-178` fingerprint/gitignore;
  `:372-380` `_last_was_enforce_block`; `:383-403` + `:406-430` the two
  recording templates; `:433-446` `_failing_consequence`, warn arm
  `:445-446`, docstring `:438-439`; call sites `:491-494` + `:565`; control
  reads `:468`/`:498`/`:515`); `.claude/hooks/_goal_state.py` (`:43-50`
  unknown-field drop hazard; `:192-232` `Evaluation`; `:396-417` `save_goal`;
  `:438-442` `record_evaluation`); `.claude/hooks/stop_continuation.py:600`
  (fall-through contract); `tests/handoffs/test_goal_gate.py` (`:90-103`
  `gate_env`; `:162`/`:170`/`:492`/`:502-514` warn-branch inventory).
- **STATUS:** the warn-path row in `docs/STATUS.md` §'Active TODOs' (the
  diagnosing TODO — tested, not inherited, in §Determination).
- **Evidence:** `.claude/handoffs/session-186/evidence/goal-s182-openq2-evidence.json`
  (the s182 never-written `goal.json`, archived s186; verified present).
- **Dispatch:** session-194 Code dispatch (fact-pack verified at `ad1eca1`).
