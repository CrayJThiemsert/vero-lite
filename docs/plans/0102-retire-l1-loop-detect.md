# PLAN-0102: Retire the L1 loop-detect guard

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-04
**Related ADRs:** ADR-013 (E.4 context — explicitly **not** amended, see §Governance), ADR-009 (D1/D2 routing)
**Drafted by:** `plan-drafter` subagent (ADR-009 D1 / ADR-013 D1 phased authority); independent review: Code R2 + Cray at PR merge (ADR-012 D4.3)

## Goal

Execute Cray's typed ruling (2026-08-04, session 205): **retire L1** — the
same-file-edit loop guard — by surgical excision from the **four** live hooks
and the shared state layer that carry it, while preserving L2/L3/L4 intact.
L1 is not a deletable file: it is threaded through `_loop_counter.py`,
`pretooluse_loop_detect.py`, `posttooluse_progress_observer.py`, and
`stop_continuation.py`, all of which also serve surviving loop types or
unrelated Stop-hook arms. This PLAN defines the minimal verifiable boundary of
that excision, proves the retirement **behaviourally** (not by string absence),
and proves ADR-013 trigger E.4 still holds afterwards. **PLAN-0102 is the
governance record of the retirement** — no ADR amendment (grounding below).

## Context — the evidence this PLAN executes (settled; do not re-litigate)

OQ-4's pre-committed criterion (`docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md:1049-1055`,
re-homed to a `docs/STATUS.md` Active TODO, now flipped `[x]` there):
re-measure ~20 sessions after AC-7; if true positives are still 0 **and** ≥1
false positive exists → retire L1. The session-205 re-measure ran over 130
transcripts (2026-07-05 → 2026-08-04), keyed on **structural hook-emission
paths** (warns at `attachment.blockingError.blockingError`; denies at
bare-string `toolUseResult` or a `permissionDecisionReason` leaf — raw
substring search over-counts ~3x), with a **positive control that passed 3/3**
(re-found the s180 baseline's exact three warns). Method + the four traps:
`docs/lessons/0035-negative-measurement-needs-a-positive-control.md`.

| Window | Exposure | Denies | Warns |
|---|---|---|---|
| pre-AC-7, 2026-07-05 → 07-27 | 23 active days, 99 transcripts, 4,201 Write/Edit ops | **56** (a FLOOR — 30-day retention already deleted 06-27 → 07-04) | 3 |
| post-AC-7, 2026-07-28 → 08-04 | 8 active days, 31 transcripts, 1,369 Write/Edit ops | **0** | 1 (induced self-test, `l1_livecheck.py` — organic = 0) |

- **True positives = 0 in both eras.** No true positive has ever been recorded
  for L1 across its entire live history.
- The s180 baseline's "0 denies" was **wrong** (≥ 56 measured; ~1.33 % of all
  pre-AC-7 edits hard-walled). Root cause: three deny wordings existed, not
  two — `docs/lessons/0012-loop-detect-l1-vs-governance-doc-fillup-passes.md:26`
  quotes `hit 6 times in this **session**` while every live emission says
  `in this **turn**`; s180 searched for a string that never appears in a
  transcript. Classified `was an error` per CLAUDE.md §6.
- **Stated limitation (binding on how this evidence is cited):** the 56 pre-AC-7
  denies were classified as false positives **from context** — each target
  (e.g. `services/engine/procedures/spec.py`, `services/engine/nl_query.py`,
  `docs/STATUS.md`, `docs/plans/0081-*`) was under sustained legitimate
  construction that shipped — **not** by replaying each edit sequence. That is
  the same classification basis s180 used for its 3 warns. This PLAN treats the
  56 as strong evidence of a false-positive-dominant guard, not as 56
  individually adjudicated verdicts.

**Cray typed "retire L1" on 2026-08-04 (session 205). The retire/keep question
is settled and is not a surfaced decision of this PLAN.**

## Governance — why no ADR amendment

The OQ-4 criterion prescribed "dispatch Cowork to draft an ADR-013 amendment."
That premise fails on the ADR's own text, verified on disk this session:

- `docs/adr/0013-autonomy-axis-relocation.md:90` — E.4 reads: "**New trigger:**
  pause + Telegram alert when an agent loops > 6 rounds on the same
  **problem**." It never names L1, files, or edit-counting.
- `docs/adr/0013-autonomy-axis-relocation.md:333-336` — "This ADR codifies
  E.1–E.5 only; it does not pre-authorize Phase 2–4. PLAN-0008+ must carry its
  own ratification for the continuation loop, **stateful loop-detection**,
  subagent topology, and MCP bus." The L1 implementation has **zero ADR
  backing**; its ratification chain runs through PLANs (0008, 0094) and
  Cray-approved per-diff self-modification (2026-06-08).
- A bounded sweep of `docs/adr/` for loop-detection (session 205) finds **no
  later ADR** touching it — `0013:335` is the only mention, so no
  newest-ADR-wins conflict exists (CLAUDE.md §1 precedence).
- **Precedent, verbatim** (`.claude/autonomy-triggers.md:336`, PLAN-0092): "No
  ADR amendment — the arm's order-emitting behavior had zero ADR backing;
  PLAN-0092 is the governance record."

**Therefore: PLAN-0102 is the governance record. E.4 survives the retirement —
and becomes *more* faithful to its ratified wording.** L2 (same failing test),
L3 (same error signature), and L4 (same failing Bash pattern) key on the same
**problem** recurring; L1 keyed on the same **file**, which is how it walled 56
legitimate construction sequences while catching zero real loops. Retiring L1
narrows the implementation to exactly what E.4 ratified.

## Code surface (all verified on disk, session 205)

One correction to the session-205 fact-pack, found while grounding this PLAN:
L1 lives in **four** live hooks, not three — `stop_continuation.py` imports
`reset_untouched_l1` (`:74`) and calls it in its turn-boundary reset (`:237`).
Its test module was already on the list; the hook itself was not.

| Site | L1 material | Post-retirement fate |
|---|---|---|
| `.claude/hooks/_loop_counter.py` | `LoopType.FILE_EDIT = "L1"` (`:145`); `l1_threshold_for` (`:761`); L1 commit-reset keying (`:807`); `record_turn_touched` (`:814`), `record_subagent_touched` (`:827`), `take_subagent_touched` (`:841`), `reset_untouched_l1` (`:862`), `clear_turn_touched` (`:915`); `turn_touched`/`subagent_touched` state fields (`:272-273`) + their (de)serialization; the L1 warn ledger (`warned_at`, `:197-205`) and non-progress tallies (`attempted_edits`/`content_hashes`, `:207-223`) | **Excise L1 helpers + enum member.** Keep everything L2/L3/L4 touches. See the "excise behaviour, tolerate schema" rule in Step 5. **Never delete the file** — shared state layer. |
| `.claude/hooks/pretooluse_loop_detect.py` | Write/Edit branch of `_resolve_target` (`:228-235`, the only mapping to `FILE_EDIT`); the warn-grace stage of `_deny_decision` (`:193-199`); L1 imports | **Excise the Write/Edit branch + grace stage.** Keep the file and the whole Bash/L4 gate path — deleting a snapshotted hook script breaks every later Edit in a session (known hazard). |
| `.claude/hooks/posttooluse_progress_observer.py` | `_handle_write_or_edit` (`:421-515` — entirely L1: non-progress scoring, touched recording, warn stage), `_handle_subagent_stop` (`:518-547` — entirely L1), `_maybe_warn_l1` (`~:355`), `_warn_advisory` (`:365-388`), the Write/Edit + SubagentStop dispatch branches in `main()` (`:792-795`) | **Excise the L1 handlers + dispatch branches.** Keep `_handle_bash` (`:750-777`) whole — L2/L3/L4 feeding, commit-reset, shell-hygiene warning all live there. Never delete the file. |
| `.claude/hooks/stop_continuation.py` | `reset_untouched_l1` import (`:74`) + turn-boundary reset call (`:226-243` incl. `clear_turn_touched` at `:238`) | **Excise the L1 reset block only.** Chain-cap fail-safe, classifier, auto-handoff arms untouched. |
| `.claude/settings.json` | PreToolUse `Write\|Edit` → `pretooluse_loop_detect.py` (`:30-33`); PostToolUse `Write\|Edit` → `posttooluse_progress_observer.py` (`:45-48`); SubagentStop `*` → `posttooluse_progress_observer.py` (`:94-102`) | **ELIMINATE all three registrations** (see below). Retain: PreToolUse `Bash` → loop_detect (`:13-16`, the L4 gate); PostToolUse `Write\|Edit` → `posttooluse_validate_handoff.py` (`:42-44`); PostToolUse `Bash` → observer (`:51-59`); SubagentStop `plan-drafter` → `subagentstop_notify.py` (`:84-93`). |
| `tests/handoffs/` (8 files carry L1 material) | `test_pretooluse_loop_detect.py` (mixed L1/L4), `test_plan0094_warn_first_deny.py` (L1-only), `test_posttooluse_progress_observer.py` (mixed), `test_loop_counter_state.py` (mixed), `test_stop_continuation.py` (mixed), `test_phase2_integration.py` (mixed), `test_settings_hook_wiring.py:88-98` (pins the SubagentStop→observer registration **whose only purpose is the L1 reset** — must be inverted, not left green vacuously), `test_sonnet_classifier.py:59-61,201-209` (**fixture-only** — synthetic registry/verdict strings; no L1 behaviour; no change required) | Delete the L1-only module; excise L1 cases from mixed modules; invert the wiring pin; add the PLAN-0102 retirement tests (Step 7). |
| `.claude/autonomy-triggers.md` | Row L1 (`:132`), path-class-threshold note (`:119-128`), reset-paths note (`:140-148` — L1 paths a/b/c), the PLAN-0094 correction box (`:150+`), L1 mentions in the Phase-2 intro (`:111-117`) | Remove the row + rewrite the notes for L2/L3/L4-only; record the retirement in the footer per the file's own amendment convention (PLAN-0092 precedent at `:336`). |
| Historical record | `docs/lessons/0012-*`, `docs/lessons/0021-*`, `docs/lessons/0033-*`, `docs/lessons/0035-*`, `docs/plans/done/0094-*`, STATUS history rows | **Do not touch.** Lessons and archived PLANs are archeology; the string "L1" surviving there is expected and is exactly why no AC in this PLAN may key on string absence. |

**Elimination proposal (dispatch invited it, evidence supports it):** the three
settings.json registrations above are not "L1 call sites inside a shared hook"
— they are **whole harness surfaces that exist only for L1**. `_resolve_target`
maps nothing but Write/Edit → `FILE_EDIT`, so the PreToolUse `Write|Edit`
loop-detect registration spawns a Python process on **every single Write/Edit
in every session** to compute a guaranteed no-op once L1 is gone. Same for the
observer's `Write|Edit` PostToolUse registration (`_handle_write_or_edit` is
pure L1) and the SubagentStop `*` registration (`_handle_subagent_stop` is pure
L1). All three are **eliminated, not preserved or stubbed**. Likewise
`turn_touched`/`subagent_touched` bookkeeping: a hooks-wide reference sweep
(session 205) found no consumer outside the L1 reset paths — eliminated, not
kept "in case".

## Acceptance Criteria

Every AC below is behavioural and carries an explicit non-vacuity story ("RED
when"), because the sharp hazard of this PLAN is that **post-AC-7 L1 already
never fires organically** — a test that merely observes an absence of firings
passes identically before and after the excision. The design answer, used
throughout: **drive the hooks directly with synthetic stdin payloads (the
established `tests/handoffs/` pattern) and pair every absence-assertion with a
same-harness positive control that still produces output.** The pre-change RED
baseline (Step 1) proves the drivers can make L1 fire at HEAD; the L4/L2
controls prove the harness can still surface a firing after.

- [ ] **AC-1 — the deny is extinct, not dormant.** Driving
  `pretooluse_loop_detect.py` with a Write payload whose target carries ≥ 20
  recorded hits in a pre-seeded state file (20 > every historical bar: 6/15
  warn, 9/18 deny) produces **no deny** — stdout carries no
  `"permissionDecision": "deny"` and the tool is allowed. **Positive control in
  the same test module:** a Bash payload whose tokenized command carries ≥ 6
  recorded failures still produces the L4 deny JSON. **RED when:** any
  Write/Edit → loop-type mapping is reintroduced in `_resolve_target`, or the
  L4 control stops denying (harness breakage is indistinguishable from success
  without it). **Pre-change probe (Step 1):** the identical L1 driver at HEAD
  emits the deny — recorded before the excision lands.
- [ ] **AC-2 — the warn is extinct.** Driving
  `posttooluse_progress_observer.py` with a sequence of Write payloads that
  re-apply the same `old_string` past every historical warn bar emits **no
  stdout output at all** (no `decision: block` advisory, no Telegram attempt —
  asserted via the existing Telegram stub seam). **Positive control:** a Bash
  payload violating shell hygiene still emits the `decision: block` hygiene
  warning through the same stdout channel in the same test. **RED when:** any
  Write/Edit handling path is reintroduced in the observer's `main()` dispatch.
  **Pre-change probe (Step 1):** the identical driver at HEAD emits the warn.
- [ ] **AC-3 — the counter no longer tracks FILE_EDIT.** After driving N Write
  payloads through the observer, the saved state file contains **no
  `L1:`-prefixed counter key and no `turn_touched`/`subagent_touched` growth**.
  **Positive control, same run:** one failing-Bash payload creates an
  `L4:`-prefixed key in the same state file — proving the writer wrote.
  **RED when:** any L1 recording path survives, or the writer stops writing
  entirely (the L4 key catches that).
- [ ] **AC-4 — the settings excision is pinned as data, both directions.** A
  rewritten `tests/handoffs/test_settings_hook_wiring.py` asserts (a) the
  **absences**: no `pretooluse_loop_detect.py` under any PreToolUse
  `Write|Edit` matcher, no `posttooluse_progress_observer.py` under PostToolUse
  `Write|Edit` or under SubagentStop; and (b) the **retentions**: loop_detect
  still registered for PreToolUse `Bash`, observer still registered for
  PostToolUse `Bash`, `posttooluse_validate_handoff.py` still registered for
  PostToolUse `Write|Edit`, `subagentstop_notify.py` still registered for
  SubagentStop `plan-drafter`. **RED when:** someone re-registers an eliminated
  surface **or** deletes a retained one — the paired retention half is what
  keeps this AC from passing on an emptied hooks block. (This inverts the
  PLAN-0094 pin at `test_settings_hook_wiring.py:88-98`, whose stated purpose
  was keeping the L1 subagent reset reachable — left as-is it would now fail,
  or worse, be deleted without a replacement guard.)
- [ ] **AC-5 — legacy state cannot crash or resurrect the guard.** Loading a
  fixture state file containing pre-retirement content — `L1:`-prefixed
  entries, `turn_touched`, `subagent_touched`, `warned_at` stamps — neither
  raises nor produces any L1 behaviour (no deny, no warn, per the AC-1/AC-2
  drivers run against that fixture), and a subsequent save round-trips without
  error. Gitignored state files predating the excision exist in every worktree
  and on both machines; the loader's tolerant-by-contract posture
  (`_loop_counter.py:173-187`, PLAN-0094 D4) must extend to the removed
  vocabulary. **RED when:** enum removal leaves any load path doing
  `LoopType("L1")` on stale keys, which raises `ValueError` at hook start.
- [ ] **AC-6 — E.4 still holds (the continuity scenario).** One scenario test
  drives the real observer + real gate over realistic simulated "same problem"
  sequences: (a) the same pytest nodeid failing 6 consecutive times in Bash
  output → L2 fires the Telegram payload `{loop_type, target, last_6_actions}`
  (captured at the stub seam); (b) the same Bash command failing 6 times → the
  L4 gate **denies the 7th attempt**. This is the proof that retiring L1 did
  not silently sever the ratified trigger "pause + alert when an agent loops
  > 6 rounds on the same problem" (`0013:90`). **RED when:** the excision
  collaterally damages `_handle_bash`, `_apply_l2`/`_apply_l4`, the shared
  threshold, the Telegram path, or the L4 branch of `_resolve_target`. Per
  CLAUDE.md §8 this drives the real producer into the real consumer on
  realistic simulated data — no stubbing of either side of the seam under test
  (the Telegram transport stub sits beyond the asserted seam, which is the
  emitted payload).
- [ ] **AC-7 — no wholesale deletion.** All four hook files still exist and
  the full `tests/handoffs/` suite is green post-excision. Guards two known
  hazards: the shared state layer serves L2/L3/L4, and deleting a snapshotted
  hook script breaks every later Edit in a live session. **RED when:** a file
  is deleted or an L2/L3/L4 behaviour regresses.
- [ ] **AC-8 — the registry and live-claim docs are truthful.** In
  `.claude/autonomy-triggers.md`: row L1 removed from the trigger table, the
  `:119-128` path-class note and `:140-148` reset-paths note removed or
  rewritten to L2/L3/L4-only, the Phase-2 intro no longer describes an L1
  reset, and the footer carries a dated retirement entry citing PLAN-0102 (the
  PLAN-0092 amendment pattern at `:336`). A **scoped** sweep of live-claim
  surfaces (`.claude/autonomy-triggers.md`, `docs/for_llm/`,
  `.claude/skills/`, `docs/runbooks/`) finds no remaining claim that L1 is
  live. Lessons and `done/` PLANs are explicitly exempt — they are history.
  **RED when:** a Tier-1/2/2.5/2.6 doc still tells a future agent the guard
  exists. (Note this AC keys on *liveness claims* in *current-truth documents*
  — not on the string "L1", which legitimately survives in history.)
- [ ] **AC-9 — the excision left no dead code (hygiene, not the retirement
  proof).** The removed identifiers — `FILE_EDIT`, `l1_threshold_for`,
  `l1_deny_threshold_for`, `reset_untouched_l1`, `reset_l1_for_targets`,
  `record_turn_touched`, `record_subagent_touched`, `take_subagent_touched`,
  `clear_turn_touched`, `note_attempted_edit`, `note_content_hash`,
  `_handle_write_or_edit`, `_handle_subagent_stop`, `_maybe_warn_l1`,
  `_warn_advisory` — have zero remaining call sites or imports under
  `.claude/hooks/` and `tests/handoffs/`, and ruff + mypy are clean (unused
  imports/symbols would flag). This AC is explicitly **subordinate**: ACs 1–3
  and 6 prove the retirement; this one only proves the diff is finished. It
  asserts on identifiers in code, never on prose.
- [ ] **AC-10 — the offline gate matches CI scope, run from the main
  checkout.** Full `tests/` suite + ruff + mypy at CI scope, executed from the
  main checkout — **not** a worktree, where 5 known `tests/handoffs/` hook
  tests false-RED (a 6th failure is real and must be chased). The Step-1
  pre-change RED probe outputs are preserved in the PR body as the
  before/after evidence pair.

## Out of Scope

- ❌ **Re-litigating retire vs keep.** Cray typed the ruling 2026-08-04;
  OQ-4's evidence and method are banked in `docs/STATUS.md` §"Active TODOs"
  and lesson 0035.
- ❌ **Any ADR-013 amendment.** Grounded above: E.4 never named L1, `0013:333-336`
  delegated stateful loop-detection to PLANs, PLAN-0092 is the precedent. An
  amendment here would *create* the ADR backing L1 never had.
- ❌ **Touching L2/L3/L4 behaviour or thresholds.** They are the surviving —
  and more faithful — implementation of E.4. Any change to them is a different
  PLAN.
- ❌ **Deleting or rewriting history**: lessons 0012/0021/0033/0035, archived
  PLAN-0094, STATUS Recent-Decisions rows, the autonomy-triggers footer trail.
  The historical string "L1" is not a defect.
- ❌ **State-file migration tooling** beyond the AC-5 load tolerance.
  `.claude/state/loop-counter.json` is gitignored and entries age out at
  `COUNTER_MAX_AGE_HOURS = 6.0` (`_loop_counter.py:135`); stale keys self-heal.
- ❌ **`tests/handoffs/test_sonnet_classifier.py` fixture edits.** Its L1
  strings (`:59-61`, `:201-209`) are self-contained synthetic registry/verdict
  fixtures testing classifier *parsing*, not L1 behaviour; the classifier reads
  the live registry at runtime and needs no code change when a row disappears.
- ❌ **Optional schema pruning** of the generic `CounterEntry` fields the warn
  machinery used (`warned_at`, `attempted_edits`, `content_hashes`). They are
  additive-by-contract and harmless once nothing writes them; removing them
  enlarges the diff in the shared layer for zero behaviour. Excise behaviour,
  tolerate schema.

## Steps

### Step 1: Pre-change RED baseline (the non-vacuity anchor)

Before any excision, on a branch at current HEAD: run the AC-1 and AC-2 driver
payloads against the live hooks and capture the emitted deny JSON and warn
advisory (plus the seeded state files used). These outputs are the proof that
**the drivers are capable of making L1 fire** — without them, every
post-change absence-assertion is indistinguishable from a broken driver.
Preserve the captured outputs as test-fixture comments and in the PR body
(AC-10). Restore any probe artifacts from scratch copies, never `git checkout`
(non-vacuity probe convention).

### Step 2: Excise the gate side — `pretooluse_loop_detect.py`

Remove the Write/Edit branch of `_resolve_target` (`:228-235`), the
`warn_threshold` grace-stage in `_deny_decision` (`:193-199`, L1-only — L4 has
no warn stage), and the now-unused L1 imports. The Bash/L4 path must be
behaviourally byte-equivalent: same threshold, same deny payload shape, same
Telegram contract. The file stays.

### Step 3: Excise the observer — `posttooluse_progress_observer.py`

Remove `_handle_write_or_edit`, `_handle_subagent_stop`, `_maybe_warn_l1`,
`_warn_advisory`, `_content_digest`/`_sha1` if their only remaining callers
were L1 (verify before deleting — keep anything L3 signature-hashing uses),
the `Write`/`Edit` and `SubagentStop` branches of `main()` (`:792-795`), and
the L1 imports. `_handle_bash` (`:750-777`) — L2/L3/L4 feeding, commit-reset,
shell-hygiene — is untouched. The file stays.

### Step 4: Excise the Stop-hook L1 reset — `stop_continuation.py`

Remove the turn-boundary L1 reset block (`:226-243`) and the
`reset_untouched_l1` / `clear_turn_touched` imports (`:70-74`). Chain-cap,
classifier, and auto-handoff arms untouched. Update the module docstring's
numbered responsibilities (`:2-13`) so the file's contract matches its
behaviour.

### Step 5: Excise the shared state layer — `_loop_counter.py`

Remove: `LoopType.FILE_EDIT` (`:145`), `l1_threshold_for` (`:761`) +
`l1_deny_threshold_for`, `reset_untouched_l1` (`:862`), `reset_l1_for_targets`,
`record_turn_touched` (`:814`), `record_subagent_touched` (`:827`),
`take_subagent_touched` (`:841`), `clear_turn_touched` (`:915`),
`note_attempted_edit`, `note_content_hash`, `mark_warned` (verify L1-only
before removing), `L1_GRACE_BUDGET`, and the `turn_touched` /
`subagent_touched` fields + their (de)serialization (`:272-282`, `:294-320`).
**Rule for this file: excise behaviour, tolerate schema** — the loader must
skip unknown counter-key prefixes and ignore the removed top-level keys
fail-open (AC-5), consistent with its existing additive-fields contract
(`:173-187`). Everything L2/L3/L4 calls survives unmodified.

### Step 6: Eliminate the three L1-only harness registrations — `.claude/settings.json`

Remove: PreToolUse `Write|Edit` → `pretooluse_loop_detect.py` (`:30-33`);
PostToolUse `Write|Edit` → `posttooluse_progress_observer.py` (`:45-48`);
the SubagentStop `*` → observer block (`:94-102`). Retain everything listed in
the AC-4 retention set. This is deregistration, not script deletion — the
snapshotted-hook-deletion hazard does not apply, and no no-op stub is needed
because all four scripts remain live for their surviving duties.

### Step 7: Rebuild the test surface

- Delete `tests/handoffs/test_plan0094_warn_first_deny.py` (L1-only by
  charter).
- Excise L1 cases from `test_pretooluse_loop_detect.py`,
  `test_posttooluse_progress_observer.py`, `test_loop_counter_state.py`,
  `test_stop_continuation.py`, `test_phase2_integration.py` — preserving every
  L2/L3/L4 case as the AC-6 continuity base.
- Rewrite `test_settings_hook_wiring.py` per AC-4 (absences + retentions,
  both pinned as data).
- Add `tests/handoffs/test_plan0102_l1_retired.py` carrying the AC-1, AC-2,
  AC-3, AC-5 drivers with their paired positive controls and the Step-1
  fixture material.
- Extend/confirm the AC-6 scenario in `test_phase2_integration.py` (or the new
  module) so the E.4 payload contract and the L4 seventh-attempt deny are
  asserted end-to-end on realistic simulated output.

### Step 8: Docs — registry, live-claim sweep

Update `.claude/autonomy-triggers.md` per AC-8 (row, notes, intro, footer
entry citing PLAN-0102 — follow the file's own amendment protocol: this PLAN
is the drafted change record, Code commits). Run the scoped live-claim sweep
over `docs/for_llm/`, `.claude/skills/`, `docs/runbooks/` and fix any "L1 is
live" claim found. Lessons and archives untouched.

### Step 9: Verify, ship, close out

Full AC-10 gate from the main checkout; one PR per CLAUDE.md §7 referencing
this PLAN. Closeout: flip Status → Complete, `git mv` to `docs/plans/done/`,
STATUS Recent-Decisions row + `next_action` update. Non-repo courtesy note for
the executing agent: the Tier-0 auto-memory note on L1 loop-detect behaviour
(`project_status_scribe_l1_loop_detect.md`) is stale after this lands and
should be updated in the same session.

## Surfaced decisions

None. The retire/keep question is Cray-ruled (session 205, typed) and the
excision boundary above is derivable from the verified code surface: every
eliminated harness registration and state field was confirmed to serve L1
exclusively, and every retained path was confirmed to serve L2/L3/L4 or an
unrelated Stop-hook arm. Remaining choices (e.g. tombstone-vs-remove for the
enum member, schema pruning) are implementation details pinned in the Steps
with rationale, reviewable at R2/PR.

## Verification

How we know it worked, in one paragraph: the same synthetic-payload drivers
that provably made L1 deny and warn at HEAD (Step 1, captured RED) produce no
L1 output after the excision, **while in the same test runs** the L4 gate still
denies, the observer still writes `L4:` state and still emits its hygiene
warning, and the AC-6 scenario still lands the E.4 Telegram payload and blocks
the 7th same-problem attempt. Absence paired with a live positive control is
what distinguishes "L1 removed" from "L1 present but silent" — and from "the
whole loop-detect layer died." The settings pin (AC-4) holds both directions as
data; the legacy-state fixture (AC-5) proves old state files cannot crash the
surviving hooks; the full-suite gate (AC-10) runs from the main checkout to
dodge the 5 known worktree false-REDs.
