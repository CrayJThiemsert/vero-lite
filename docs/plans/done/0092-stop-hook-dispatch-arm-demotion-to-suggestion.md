# PLAN-0092: Stop-hook dispatch arm — demotion from order to suggestion (A′)

**Status:** **COMPLETE** — 6/6 ACs met, closed out + archived session 168 (2026-07-23).
Built as PR [#871](https://github.com/CrayJThiemsert/vero-lite/pull/871) (merge commit
`7c86752`); SD-A…SD-D were all ratified by Cray (typed, AskUserQuestion, s167) and are
recorded inline below. See **Closeout** at the end.
_(Never `Accepted`: that status G1-gates a PLAN's own closeout — the PLAN-0087/0089/0090 precedent.)_
**Owner:** Claude Code
**Created:** 2026-07-23
**Related ADRs:** none amended — see §Why no ADR. Context: ADR-0018 (V1 goal-gate arm, explicitly preserved), ADR-013 (autonomy-axis relocation, unchanged)

## Goal

Demote the Stop-hook classifier's `dispatch` verdict from an **order** (a
`block` directive instructing the main agent to spawn `plan-drafter`) to a
**suggestion**: on `dispatch` the hook emits **no** stdout directive, lets the
stop fire (pause semantics, chain **reset**), and sends a Telegram ping
carrying the would-be suggestion (subagent, artifact_kind, task_summary,
matched D-rows, classifier reason) so Cray sees what the classifier wanted and
can route it deliberately. Hook-side only — the classifier, the V1 goal-gate
arm, and the PreToolUse arm are untouched.

**Ratification record.** Cray typed-ratified (AskUserQuestion, 2026-07-23,
session 167): the autonomy fork resolves as **option A′** — demote the
dispatch verdict to a suggestion. Cray also typed-ratified the execution
route: this short PLAN via `plan-drafter` (same route as the PLAN-0034
precedent); Code commits via PR.

## Origin / evidence

**The misfire ledger.** 14 Stop-hook dispatch-arm misfires across 5 sessions
(3× s71 · 3× s163 · 3× s164 · 3× s165 · 2× s166 — recorded in
`docs/STATUS.md`, In-Flight "the autonomy fork" entry), in **4 distinct
shapes**:

1. re-dispatch of already-in-flight work;
2. wrong artifact kind routed to a closed route;
3. mention-as-intent (discussion of an artifact read as a drafting order);
4. non-existent-artifact assumption.

Every one was declined by Code via the registry's Override clause
(`.claude/autonomy-triggers.md:135-140`). **Zero valid dispatch-arm fires are
recorded** in STATUS or the status archive across ~2 months live. Caveat,
honestly: an unrecorded valid fire cannot be fully ruled out — but the
recorded base rate is 0/14.

**Root-cause split.** Shapes 1 and 4 (plus part of 2) are **knowledge**
failures: the classifier cannot see disk state or in-flight work, so no model
upgrade fixes them. Shape 3 is a **judgment** failure: a
prompt-rule-per-shape race that PLAN-0034's rule already lost 4 sessions
running. A′ moots **both** families at the arm — a suggestion that misfires
costs one Telegram ping, not a spurious spawn order the agent must
adversarially decline. This also honors the registry's own design preference:
"spurious dispatches are worse than spurious pauses"
(`.claude/autonomy-triggers.md:139-140`, `:142-145`; restated in the
classifier prompt at `_sonnet_classifier.py:260-264`).

**Rejected alternatives** (recorded so they are not re-proposed):

- **(a) Another prompt rule** — refuted empirically: the exact anti-shape-3
  rule has existed since PLAN-0034 and failed in 4 consecutive sessions.
- **(b) Deterministic disconfirmers on a still-ordering arm** — would kill
  shapes 1/2/4 only; the shape-3 judgment race continues.
- **(e) Backend flip to Sonnet** — config-only, but fixes only the judgment
  family, has a known API-key/org fail-closed mode needing a live probe, and
  was **deferred** by Cray's A′ pick (not needed if the order class dies).

### Why no ADR

The dispatch arm's order-emitting behavior and the "FLOOR, not a specificity
judge" stance have **zero ADR backing** (caller grep-verified 2026-07-23: no
ADR/PLAN match) — they live in PLAN-0009 Step 5c-1 and the hook itself. No
ADR amendment is required; **this PLAN is the governance record** of the
demotion.

## Grounding table

Every row re-verified on disk 2026-07-23 (caller fact-pack + drafter Read).

| # | Fact | Evidence |
|---|------|----------|
| G1 | Dispatch arm: validates `dispatch_meta` is a dict, builds the instruction, **increments** the stop-chain, emits `_proceed_block(instruction)` | `.claude/hooks/stop_continuation.py:597-619` (dict guard `:604`, builder call `:610`, chain `:615-616`, block `:618`) |
| G2 | The dict check is the ONLY guard on the arm; the #844 contentless-reason floor (`_reason_is_contentless`, `:419-447`) is called only on the proceed arm (`:584`) — structurally unreachable from dispatch | `stop_continuation.py:584`, `:604` |
| G3 | Instruction builder formats the spawn order incl. pre-spawn NNNN enumeration + the Override clause | `stop_continuation.py:463-518`; budget-reminder constant `:454-460` |
| G4 | Provenance: arm = PLAN-0009 Step 5c-1 "auto-handoff dispatch" | module docstring `stop_continuation.py:21-29` |
| G5 | D-rows D1/D2 (new-ADR-after-ratification / new-PLAN-once-scope-agreed); Override clause; "spurious dispatches are worse than spurious pauses" | `.claude/autonomy-triggers.md:114-159` (D1 `:132`, D2 `:133`, Override `:135-140`, preference `:139-140` + `:142-145`); chain-cap-interaction paragraph `:147-150`; Stop-side contract bullet `:212-220` |
| G6 | Classifier: prompt `:235-328`; returns proceed/pause/dispatch; backend defaults to local Ollama `gpt-oss:20b` on MS-S1 (`:685-691`, `DEFAULT_OLLAMA_MODEL` `:92`); fail-closed to pause on infra failure | `.claude/hooks/_sonnet_classifier.py` — **OUT OF SCOPE**; it may keep returning `dispatch`, the hook reinterprets |
| G7 | Goal-gate arm: V1 goal-evaluator dispatch emitted deterministically by `_goal_gate.py` BEFORE the classifier — a different mechanism (ADR-0018) | `stop_continuation.py:565-571`; registry `autonomy-triggers.md:181-199` — **OUT OF SCOPE, byte-unchanged behavior** |
| G8 | PreToolUse arm maps `dispatch` → deny-with-spawn-redirect on G1/G2 Write/Edit signatures | `.claude/hooks/pretooluse_classifier_dispatch.py:346-351` (own builder `_build_dispatch_deny_reason` `:232`); registry `:221-242` — **OUT OF SCOPE** (a gate deny on an action Code initiated, not an unprompted order) |
| G9 | Telegram infra exists: `_ping_telegram(...)` used by the chain-cap alert; `CLAUDE_TELEGRAM_SCRIPT` env override for testability | `stop_continuation.py:158-185` (transport), `:557` (cap-hit call), `:90-92` (override), docstring `:40-43`; cap formatter `_format_cap_message` `:148-155` |
| G10 | `_build_dispatch_instruction` has **no callers** outside `stop_continuation.py:610`; tests exercise it only via `main()` (no direct import — caller grep of `tests/handoffs/`, 2026-07-23). One **textual** reference exists: the `_goal_gate.py:302-305` comment cites `_PLAN_DRAFTER_BUDGET_REMINDER` as its in-module-template precedent (a comment, not a caller — patched in Step 3) | drafter Grep of `.claude/hooks/*.py` + caller R2 grep, 2026-07-23 |
| G11 | Dispatch-arm test block asserts the current order-emitting contract | `tests/handoffs/test_stop_continuation.py` — inventory in Step 1 below |
| G12 | `tests/handoffs/test_phase2_integration.py` carries **no dispatch-arm assertions** — its three "dispatch" mentions (`:157`, `:312`, `:345`) are fixture comments about classifier invocation generally | drafter Grep + Read, 2026-07-23 |
| G13 | In-process test fixture `inproc_env` points `CLAUDE_TELEGRAM_SCRIPT` at a **nonexistent** script (ping no-ops); the subprocess `stub_env` fixture has a working stub + capture-file pattern to mirror for AC-2 | `test_stop_continuation.py:359-390` (inproc), `test_phase2_integration.py:151-177` + `test_stop_continuation.py:231` (stub pattern) |

## LOCKED decisions (ratified — not up for re-litigation at R2)

- **L1 — A′ semantics.** On `verdict == "dispatch"` the hook emits **no**
  stdout block directive and lets the stop fire. The dispatch verdict is a
  suggestion, never an order.
- **L2 — Suggestion channel = Telegram.** The ping carries the would-be
  suggestion: subagent, artifact_kind, task_summary, matched D-rows,
  classifier reason.
- **L3 — Hook-side only.** `_sonnet_classifier.py` is untouched: prompt,
  backend, schema, `dispatch` as an allowed decision all stay. The hook
  reinterprets the verdict.
- **L4 — Chain semantics: dispatch now behaves as a pause.** The chain is
  **RESET**, not incremented (today it increments per
  `stop_continuation.py:615-616` / `autonomy-triggers.md:147-150`).
- **L5 — V1 goal-gate arm byte-unchanged in behavior** (G7). Its tests must
  not change.
- **L6 — PreToolUse arm untouched** (G8) — named explicitly so nobody
  "helpfully" edits it.
- **L7 — D-rows annotated, never deleted.** D1/D2 still document when a
  *suggestion* fires.
- **L8 — Route.** This PLAN drafted via `plan-drafter` (PLAN-0034 precedent);
  Code reviews (R2) + commits via PR.

## Acceptance Criteria

Each AC is deterministic-offline and designed to FAIL against today's code or
against a silent revert (non-vacuity noted per AC).

- [x] **AC-1 — dispatch emits nothing and resets the chain.** In-process
  test: seed the chain file at depth ≥ 1, patch `classify` to a well-formed
  dispatch verdict, run `main()`. Assert: exit 0, **stdout empty**, chain
  file reset to `{depth: 0}`. *Non-vacuous:* today's code emits a block JSON
  and increments the seeded depth — both assertions fail against it.
- [x] **AC-2 — the suggestion ping fires exactly once with the full
  payload.** Point `CLAUDE_TELEGRAM_SCRIPT` at a capture stub (mirror the
  `stub_env` pattern, G13). Assert one invocation whose captured body
  carries all five fields: subagent, artifact_kind, task_summary, matched
  rows (or the none-cited marker), classifier reason. *Non-vacuous:* today's
  dispatch arm never calls `_ping_telegram` — capture stays empty.
- [x] **AC-3 — proceed, pause, cap, re-entry, goal-gate, and
  malformed-dispatch behavior unchanged.** The following existing tests stay
  **green unmodified** (`tests/handoffs/test_stop_continuation.py`): proceed
  arm `:583` + contentless-floor block `:740/:745/:751/:769/:786/:797/:815`
  + `:849`; pause arm `:276/:284/:600/:614`; cap `:231/:247/:254/:264/:504`;
  re-entry `:121/:653`; malformed-dispatch demotion `:529/:547/:562`;
  **goal-gate (V1)** `:961/:972/:993/:1013/:1039`. `test_phase2_integration.py`
  needs no edits (G12).
- [x] **AC-4 — non-vacuity evidenced RED-first.** The rewritten
  dispatch-contract tests are run against the **unmodified** hook before the
  Step 2 edit and the RED output is recorded in the PR body. At minimum the
  stdout-empty assertion (AC-1) and the ping-capture assertion (AC-2) fail
  against the old order-emitting code.
- [x] **AC-5 — governance surfaces annotated.** `.claude/autonomy-triggers.md`
  Auto-handoff section (intro `:116-128`, chain-cap paragraph `:147-150`,
  Stop-side bullet `:212-220`) and the `stop_continuation.py` module
  docstring (responsibilities 2–3, `:15-29`) annotated to record the
  demotion **citing PLAN-0092**; D1/D2 rows retained (L7); registry stays
  machine-readable per its own `:243-246` constraint. *Oracle:* grep
  `PLAN-0092` in both files is non-empty (impossible today), and neither
  file still describes the Stop arm as emitting a block directive on
  dispatch.
- [x] **AC-6 — offline gate green.** Full `pytest tests/` + `mypy` at CI
  scope + `ruff check`, run in the **main tree** (5 `tests/handoffs/` hook
  tests are known false-RED in a git worktree). CI is PR-only, so the
  **merge commit** gets a full-suite re-run after merge.

## Out of Scope

- ❌ `_sonnet_classifier.py` — prompt, backend, schema, allowed decisions
  (L3). It keeps returning `dispatch`; only the hook's interpretation
  changes. (SD-D parks the prompt-wording question as a follow-up note.)
- ❌ The V1 goal-gate arm — `_goal_gate.py`, `stop_continuation.py:565-571`,
  registry `:181-199`, tests `:961-1050` (L5, ADR-0018).
- ❌ `pretooluse_classifier_dispatch.py` — the PreToolUse `dispatch` →
  deny-with-spawn-redirect mapping stays exactly as is (L6, G8).
- ❌ Option B deterministic disconfirmers; ❌ option E Sonnet backend
  flip/probe (both rejected/deferred — see Origin).
- ❌ Any NEW `.claude/autonomy-triggers.md` row; ❌ deleting D1/D2 (L7).
- ❌ Chain-cap, turn-boundary-reset, proceed-arm, and contentless-floor
  behavior — all byte-unchanged.

## Steps

### Step 1: Test-first contract rewrite (RED)

*Ordering note (drafter refinement, surfaced not silent): the caller sketch
ordered hook-edit → test-rewrite; this PLAN swaps them so AC-4's non-vacuity
evidence falls out of the normal red→green flow instead of a
restore-from-backup dance.*

In `tests/handoffs/test_stop_continuation.py`, rewrite the dispatch block to
the suggestion contract. Named inventory:

**REWRITE (order-contract → suggestion-contract):**

- `:431 test_dispatch_plan_emits_block_with_instruction` → asserts stdout
  empty + exit 0 + one Telegram capture carrying the five payload fields
  (AC-1 + AC-2 happy path).
- `:466 test_dispatch_adr_routes_to_docs_adr` → asserts the captured payload
  carries `artifact_kind: adr` (routing survives into the suggestion).
- `:490 test_dispatch_increments_chain_depth` → inverted: seeded depth 3
  **resets to 0** (L4).
- `:635 test_dispatch_with_empty_matched_rows_still_dispatches` → still
  pings, payload shows the none-cited marker.
- `:678 test_dispatch_instruction_includes_step4_references` and
  `:690 test_dispatch_instruction_includes_scoped_context_discipline` →
  **DELETE** (the spawn-order template they pin is removed per SD-B —
  ratified as DELETE).

**UNCHANGED (must stay green as-is — AC-3):** `:504` (cap fires before
classifier), `:529`/`:547` (malformed meta demotes to pause), `:562`
(demotion resets chain), `:653` (re-entry guard). **Extension (flagged, not
silent):** add a *new* negative assertion test that malformed dispatch meta
produces **no ping** (the demotion path stays silent — there is no coherent
suggestion to send); the three existing malformed tests themselves stay
untouched.

Also update the `inproc_env` fixture usage only where a test needs the
capture stub (G13) — the fixture's default nonexistent-script behavior stays
for non-ping tests.

Run the rewritten tests against the unmodified hook: expect RED. Record the
output (AC-4).

### Step 2: Hook edit (GREEN)

`.claude/hooks/stop_continuation.py`, dispatch arm `:597-619` only:

1. Keep the `dispatch_meta` dict guard (`:604`) — malformed meta still
   demotes to silent pause (`_reset_chain()`, return 0, no ping).
2. Well-formed meta: build the suggestion payload (subagent, artifact_kind,
   task_summary, matched rows, reason), call `_ping_telegram(...)` once,
   `_reset_chain()` (L4), return 0 — **no stdout**.
3. Per SD-B recommendation: delete `_build_dispatch_instruction`
   (`:463-518`) + `_PLAN_DRAFTER_BUDGET_REMINDER` (`:454-460`) and add a
   small suggestion-payload builder + a formatter branch for the new event
   (SD-A). `_ping_telegram`'s transport and the cap-hit call path (`:557`)
   are untouched.

Safe to delete: G10 confirms no callers outside `:610` + tests.

### Step 3: Documentation annotation

- `stop_continuation.py` module docstring: responsibility 3 (`:21-29`)
  rewritten to suggestion semantics; responsibility 2's "proceed/dispatch
  count toward the chain" (`:15-19`) corrected to proceed-only; cite
  PLAN-0092.
- `.claude/autonomy-triggers.md`: annotate the Auto-handoff intro
  (`:116-128`), the chain-cap-interaction paragraph (`:147-150` — dispatch
  no longer counts, it resets), and the Stop-side contract bullet
  (`:212-220`) to record the demotion citing PLAN-0092. D1/D2 rows retained
  verbatim (L7). Preserve machine-readability (`:243-246`).
- `_goal_gate.py:302-305` — one-line comment amendment (added at Code R2):
  the ADR-0018 D6 note cites `_PLAN_DRAFTER_BUDGET_REMINDER` as its
  in-module-template precedent; after SD-B's deletion, re-word to cite it
  historically ("the former `_PLAN_DRAFTER_BUDGET_REMINDER`, removed per
  PLAN-0092"). **Docs-only edit to a V1-arm file, explicitly flagged:** L5
  governs behavior + tests (both stay byte-unchanged); a comment re-word
  does not violate it. *(Catch provenance: the drafter's caller-grep was correct — no
  callers exist; a textual reference is not a caller. Caught by caller R2.)*

### Step 4: Offline gate + PR

Full `pytest tests/` + `mypy` (CI scope) + `ruff check` in the **main tree**;
PR per CLAUDE.md §7 with the AC-4 RED evidence in the body; after merge,
re-run the full suite on the merge commit (CI is PR-only).

## Surfaced decisions (**ALL FOUR RATIFIED by Cray — typed AskUserQuestion, 2026-07-23, session 167 — as-recommended.** Nothing in this PLAN awaits a decision.)

- **SD-A — Telegram payload shape. RATIFIED (as-recommended).** *A new compact event
  shape* (`stop_dispatch_suggestion`) reusing the existing `_ping_telegram`
  transport, via a formatter branch keyed on the event field — NOT the
  cap-hit shape. Reason: `_format_cap_message` (`:148-155`) renders
  `depth=/cap=` lines that are meaningless noise for a suggestion and would
  bury the five routing fields Cray reads from a phone. Alternative: reuse
  the cap shape as-is (smaller diff, worse signal).
- **SD-B — fate of `_build_dispatch_instruction`. RATIFIED (as-recommended):
  DELETE** it plus `_PLAN_DRAFTER_BUDGET_REMINDER`, replacing with a much
  smaller suggestion-body builder. Reason: repurposing 55 lines of
  spawn-order text (budget reminder, pre/post-spawn discipline) into a ping
  body would smuggle order-semantics into the suggestion channel; deletion
  leaves no dead code and G10 proves no external callers. Alternative:
  repurpose (keeps template heritage, but every retained line is
  order-shaped).
- **SD-C — env-var escape hatch to restore ordering. RATIFIED
  (as-recommended): AGAINST.** `git revert` is the rollback. Reasons: a config flag re-promoting
  the order is a silent path around a typed ratification; 0/14 recorded
  valid fires shows no evidenced need; per-machine env divergence would make
  Stop-hook behavior non-deterministic across sessions. No concrete need was
  found while drafting.
- **SD-D — softening the classifier prompt's DISPATCH description. RATIFIED
  (as-recommended): PARK as an explicit follow-up note, not a Step.** The
  prompt still describes dispatch as an instruction the hook formats
  (`_sonnet_classifier.py:235-328`) — now stale-ish but harmless, since the
  hook reinterprets (L3) and the AC-5 registry annotation is the
  discoverability fix. Any prompt edit touches `_sonnet_classifier.py`
  (out of scope here, R1) and its contract tests; if drift ever confuses a
  reviewer, a later PLAN aligns the wording.

## Verification

AC-1/AC-2/AC-4 via the rewritten in-process tests (RED-first evidence
recorded); AC-3 via the named unchanged tests staying green unmodified; AC-5
via the `PLAN-0092` grep oracle on both annotated files; AC-6 via the full
offline gate in the main tree plus the post-merge full-suite re-run on the
merge commit. Live-fire verification is deliberately absent: the change is
deterministic hook logic, fully exercisable offline (the classifier is
patched in-process; the Telegram stub captures the ping).

## Follow-up notes (non-binding)

- SD-D parked: classifier-prompt DISPATCH wording alignment, only if drift
  causes real confusion.
- If a *valid* suggestion ever fires post-demotion, record it in STATUS — it
  is the first datum against the 0/14 base rate and would inform any future
  re-promotion discussion (which would need its own ratification).

## Closeout — session 168, 2026-07-23 (6/6 ACs met; ARCHIVED)

Built and merged as PR [#871](https://github.com/CrayJThiemsert/vero-lite/pull/871)
(`0870266` → re-sync `6afaf9c` → merge commit `7c86752`) during session 167. The
closeout itself is filed one session later: the build landed mid-session and the
PLAN was left `Draft` with its boxes unticked, which is what this PR corrects.

**Per-AC evidence, re-verified on disk against `main` = `64c2190` before ticking**
(CLAUDE.md §6 — the label `confirmed — prior intact` requires a fresh artifact, never
memory):

| AC | Evidence read fresh |
|----|---------------------|
| AC-1 | `.claude/hooks/stop_continuation.py:597-611` — the dispatch arm has no `print`; malformed metadata takes the silent `_reset_chain(); return 0` path at `:598-600`; the well-formed path pings then `_reset_chain(); return 0` at `:610-611`. Tests `tests/handoffs/test_stop_continuation.py:463` (`assert out == ""`) and `:504-519` (`test_dispatch_resets_chain_depth`, seeded depth 3 → 0). |
| AC-2 | `_format_dispatch_suggestion` at `stop_continuation.py:162-181` carries all five routing fields (subagent, artifact_kind, task_summary, matched_rows with a `(none cited)` fallback, reason) and closes with the advisory line *"Route it yourself if it is right; ignoring it is the default"*. Payload builder `:483-503`, call site `:603-609`. |
| AC-3 | The named arms are intact and unmodified: proceed `:562-580`, cap `:541-544`, goal-gate (V1) `:550-556`, malformed-demote `:597-600`. |
| AC-4 | RED-first block recorded in the #871 PR body: the four rewritten dispatch tests `4 failed, 8 passed, 45 deselected` against the **unmodified** hook, with the honest caveat that the malformed-no-ping guard passes both before and after and is therefore **not** counted as AC-4 evidence. |
| AC-5 | `grep -c PLAN-0092` → `.claude/autonomy-triggers.md` **8**, `.claude/hooks/stop_continuation.py` **6** — the oracle is non-empty on both files, as the AC requires, and D1/D2 rows are annotated rather than deleted (L7). |
| AC-6 | 2994 passed / 7 skipped on the merge commit `7c86752`; `ruff` + `mypy --strict services/` clean at CI scope. |

**SD-B's DELETE confirmed as a scoped deletion, not a rename.** `_build_dispatch_instruction`
and `_PLAN_DRAFTER_BUDGET_REMINDER` return **zero** hits under `.claude/hooks/stop_continuation.py`.
The single surviving mention repo-wide is the historical re-word Step 3 mandated, at
`.claude/hooks/_goal_gate.py:303-304` — a textual precedent citation, not a caller.

**SD-D stays parked but is now a real contradiction, not merely "stale-ish".** The
Follow-up note above judged the drift *"harmless"*. Re-reading the prompt at closeout
sharpens that: `_sonnet_classifier.py:262-264` still tells the model *"Spurious dispatches
are worse than spurious pauses (they consume a subagent spawn)"* — a claim that is now
**factually false** post-A′ (a dispatch consumes one Telegram ping and spawns nothing),
while `.claude/autonomy-triggers.md:118-125`, read verbatim into the *same* prompt,
correctly describes the no-directive behavior. The model therefore sees ordering framing
in the preamble and suggestion framing in the embedded registry. Classified
**`superseded by new info`**, not `was an error`: the note was written before the registry
annotation landed alongside it. Cray ratified the alignment fix (typed, s168) — it is
tracked as its own PR and stays out of this PLAN's scope (R1).

*Drafting disclosure (ADR-012 D4.3): authored by the in-harness
`plan-drafter` subagent, 2026-07-23, from a Cray-ratified (session 167)
dispatch payload; independent review by Code (R2) + Cray at PR merge.*
