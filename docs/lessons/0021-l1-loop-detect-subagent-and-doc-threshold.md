# Lesson #21: L1 loop-detect vs subagent-authored governance docs — the structural fix (path-class threshold + subagent-completion reset)

> **Status:** Codified 2026-06-08 (Session 45). Observed live the same session:
> a `plan-drafter` subagent made 6 edits to `docs/plans/0019-core-procedure-baseline.md`
> while formalizing ratified SDs, exhausting the flat L1 threshold (6) **inside
> the main agent's turn**, so the main agent could not add even ONE of the two
> remaining edits. Recovery cost two extra turns (sticky reset) and a Cray nudge.
> **Sequel to [[lesson-0012-loop-detect-l1-vs-governance-doc-fillup-passes]]** —
> #0012 chose recovery-actions-over-retuning; this session showed that for
> *subagent-authored* governance docs the recovery actions are not enough, so the
> structural fix #0012 kept deferring finally landed (Cray-approved per-diff).
> **Severity:** Low (no data loss; gate behaved per spec). Friction high — it
> stalled legitimate, ratified doc work across multiple turns.
> **Cross-references:** PLAN-0008 Step 2/3/4 hooks; `.claude/autonomy-triggers.md`
> row L1; [[lesson-0012-loop-detect-l1-vs-governance-doc-fillup-passes]] (§7
> commit-boundary reset + the "verbal ack ≠ unblock" meta-lesson, both re-lived
> here); ADR-013 / Cray E.4.

## 1. The finding

L1 (`pretooluse_loop_detect.py`) counted **a subagent's edits and the main
agent's edits in the same per-turn bucket**, with a **flat threshold of 6** for
every path class. Two consequences, both hit this session:

1. **Subagent bunching.** A `plan-drafter` subagent that makes ≥ 6 edits to one
   file pre-spends the *whole* turn budget — the main agent (which dispatched it)
   then cannot edit that file at all, even though it has distinct, productive
   work to add. (Empirically: drafter did 6/8 SD edits, main was denied the
   last 2.)
2. **Flat 6 is wrong for prose.** Multi-section governance authoring (PLAN / ADR
   / STATUS / lessons / handoffs) legitimately makes many small *distinct*
   edits to one file in a turn — that is the work, not a loop. The flat-6 bar
   (designed for code `edit → test → fail → edit` thrash) false-fires on it.

The reset paths that existed (Stop turn-boundary reset, commit-boundary reset
from #0012 §7) did not save the day mid-turn: the turn-boundary reset is
**sticky** (a file touched in turn N survives N's `Stop`; it only resets after a
*fully untouched* turn — so recovery cost two turns), and no commit had happened
yet (the work was uncommittable mid-formalization).

## 2. Why a structural fix this time (vs #0012's "use recovery actions")

Lesson #0012 deliberately chose **not** to retune the threshold — surgical reset
/ batch-into-one-Write / pause were the prescribed recoveries. That holds for a
*single human-driven* closeout pass. It breaks for the **subagent** case:

- The subagent cannot batch *across* the main agent — the budget is already gone
  when control returns.
- "Batch into one Write" is exactly what a careful surgical multi-section edit
  *avoids* (small reviewable diffs are good practice). Penalizing it is backwards.
- The loop signal L1 proxies — *directionless repetition* — does not exist for
  prose: there is no test/build feedback driving a doc edit→fail→edit cycle. The
  code feedback loop is covered more directly by L2 (test-fail), L3
  (error-signature), L4 (bash-pattern).

So the proxy (edits-to-a-path-per-turn ≥ 6) is simply the *wrong unit* for docs.
The fix is to make the threshold **path-class-aware** and to treat a subagent
return as a reset boundary.

## 3. The fix (Cray-approved per-diff self-modification, 2026-06-08)

Three changes in the loop-detect hooks:

1. **Path-class threshold** (`_loop_counter.l1_threshold_for`): **6 for code
   paths**, **15 for prose/doc paths** (`*.md` anywhere, or under `docs/`). The
   doc bar is raised but **finite** — a genuinely stuck doc loop (e.g. a runaway
   STATUS reconcile) still trips at 15. Code paths are unchanged.
2. **Subagent-completion reset** (`posttooluse_progress_observer._handle_agent_completion`):
   on an `Agent`/`Task` tool completing, reset the L1 counters for the files
   touched this turn — symmetric with the existing commit-boundary and Stop
   turn-boundary resets. A drafter subagent's edits no longer pre-spend the main
   agent's budget.
3. **Honest deny message + registry**: the deny reason now reports the *actual*
   path-class threshold and says "in this turn"; `.claude/autonomy-triggers.md`
   row L1 documents all three reset paths (resolving the doc-follow-up #0012 §7
   explicitly deferred).

## 4. Two meta-lessons (both re-lived from #0012, worth restating)

- **A verbal/chat ack does NOT unblock a deterministic PreToolUse gate.** When
  L1 hard-blocks and Cray says "OK / go", the gate re-fires identically on the
  retry — the hook never sees the chat. The legitimate unblock is a **state
  transition** (here: the turn-boundary reset, satisfied by ending a turn with
  the file untouched), *not* a conversational one. Do **not** hand-edit
  `loop-counter.json` or `sed` the file to dismiss a trip — that is the forbidden
  circumvention. (Re-confirmed live: a `git diff` between attempts did **not**
  reset the counter; only the `Stop` turn-boundary did.)
- **Editing your own guardrail needs per-diff approval, not direction approval.**
  The auto-mode classifier denied the first attempt to raise the L1 threshold as
  *self-modification*, even though Cray had picked the fix direction via a
  routing question. **Routing pick ≠ per-diff approval** (same rule as the
  G1/G2 ADR/PLAN gates). The correct move is to show the exact diff that touches
  the guardrail and get explicit per-diff go — then the retry passes.

## 5. Prevention / guidance going forward

- **Authoring a governance doc via a subagent is now safe** up to 15 edits/turn,
  and the subagent's edits reset when it returns. No special handling needed for
  the common case.
- **If you still hit L1 on a doc** (≥ 15 edits to one file in one turn), treat it
  as a real signal: you are probably thrashing — batch into one Write, or pause.
- **Code paths are unchanged (6).** For generated/formatter rewrites, prefer a
  single `Write` (counts as 1) over N `Edit`s.
- **When L1 blocks mid-turn and you cannot commit:** end the turn with the file
  untouched-that-turn; the `Stop` hook resets the counter; continue next turn
  with the remaining work as ONE consolidated edit.

## 6. Residual gaps (deferred)

- **Distinctness-based counting (the "B later" option).** The most intent-true
  fix is to count only *repeated-region* edits (or edits interleaved with a
  failing test on the same target) as a loop, rather than all edits. Deferred as
  a follow-up if the path-class threshold proves insufficient (Cray: "A now, B
  later", 2026-06-08).
- **Session-immortal state file** (from #0012 §7 bug 1) is still untouched —
  mostly harmless given the reset paths, but a future hardening could re-mint
  `session_id` when `$CLAUDE_SESSION_ID` changes.
