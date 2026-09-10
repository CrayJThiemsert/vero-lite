---
description: Declare (or clear) the session goal for the Axis-B verification loop — writes .claude/state/goal.json, which the Stop-hook goal gate then checks every turn (ADR-0018 / PLAN-0021)
argument-hint: <goal statement, optionally with source: PLAN pointer, optionally enforce> | clear | amend <ratification summary>
---

# /goal — declare or clear the session verification goal

You (the main Code agent) maintain the Axis-B goal artifact at
`.claude/state/goal.json` (gitignored; schema = `.claude/hooks/_goal_state.py`,
ADR-0018 §spec 1). The Stop-hook goal gate (`_goal_gate.py`) reads it at every
Stop: runs `check` criteria deterministically, dispatches the `goal-evaluator`
subagent for `judge` residue, and — per the goal's own `enforce` flag — either
**warns** (default, warn-only v1: a FAIL never blocks) or **enforces** (v2: one
bounded block, then park at `blocked-pending-human`; ADR-0018 V2 / PLAN-0069).
The argument is: `$ARGUMENTS`

## If the argument is `clear`

Delete `.claude/state/goal.json` (or, if you prefer an audit trail in-session,
load it and confirm its final `status` to the user before deleting). Confirm:
"goal cleared — the gate stands down."

## Otherwise — declare the goal

1. **Parse the goal statement.** The argument is a one-sentence goal. If it
   references a PLAN (e.g. `source: docs/plans/0021-...md#acceptance-criteria`
   or "per PLAN-0021"), resolve that pointer — the PLAN's AC block is the
   **canonical contract**; the goal file is a **derived projection** of it
   (ADR-0017 D3/D6: on divergence the PLAN wins).

2. **Derive criteria using the D1 split rule** (state this honestly — don't
   inflate): *if a criterion can be written as a command whose exit code
   answers it, it MUST be `kind: "check"`* (with `cmd` + **required**
   `timeout_s`); *only judgment residue* (template shape, "resolves every
   OQ", prose quality) *goes to `kind: "judge"`* (with `desc`). Scope each
   `check` `cmd` yourself — e.g. `pytest tests/handoffs -q`, not the world —
   the total deterministic budget at Stop is 120 s
   (`CLAUDE_GOAL_CHECK_BUDGET_S`; the constant is `DEFAULT_CHECK_BUDGET_S` in
   `_goal_gate.py`, and `tests/handoffs/test_goal_command_prose_pins_the_budget.py`
   pins this sentence to it — PLAN-0123 AC-2, after the prose sat at 600 s for
   sixteen sessions while the gate enforced 120); a timeout/skip is unresolved,
   never a pass (VX-2). Commands run **argv-without-shell** from the repo root:
   no `&&`, no pipes — one command per criterion.

   **R2 — evidence goes to a file, not to stdout.** A `check`'s stdout never
   reaches the `goal-evaluator`: only the exit code becomes a state. If a
   `judge` criterion must read a measurement, the `check` that produces it writes
   the artifact to disk (name the path in the judge's `desc`) — a number that
   only ever existed in a captured stdout is a number nobody took.

   **R5 — name the basis; HEAD-pinning is pre-merge only.** A `check` of the
   form `git show <sha>:<path>` pins a basis that a merge can move out from
   under it. Declare it only for a goal that closes before its PR merges, and
   record `declared_head` (the sha you declared against) in the goal file. After
   HEAD moves from `declared_head`, such a check reads **`basis-moved`** — not
   `fail`: no ladder rung, no defect in the trail, one Telegram naming the moved
   basis, and the goal stays `active` for you to clear or re-declare (PLAN-0123
   §4.4, SD-2 = c). A tree-basis check (`pytest …`, `python -c …`) is never
   reclassified — a real failure after a merge is still a failure.

   **R8 — one goal file, no silent replacement.** An `active` goal that has not
   passed is **appended to** (new criteria ids prefixed `T<n>-`), never
   overwritten by a fresh declaration: overwriting erases the trail that says
   what the earlier goal found. To replace it on purpose, archive the old file to
   `.claude/state/goal-history/` first, so the abandonment is a record and not a
   disappearance (PLAN-0123 R8 / AC-8; the renderer's `--replace` does this for
   you once Step 2 lands — until then, do it by hand). A `passed` goal may be
   replaced freely.

3. **Write the file** (`Write` to `.claude/state/goal.json`, honoring a
   `CLAUDE_GOAL_PATH` override if set):

   ```json
   {
     "schema_version": 2,
     "goal": "<the one-sentence goal>",
     "source": "<PLAN pointer, if any>",
     "session": <current session number>,
     "created": "<now, ISO-8601 with offset>",
     "status": "active",
     "enforce": false,
     "criteria": [
       {"id": "C1", "kind": "check", "cmd": "<scoped command>",
        "desc": "<what it proves>", "timeout_s": <seconds>},
       {"id": "J1", "kind": "judge", "desc": "<judgment residue>"}
     ],
     "evaluations": [],
     "amendments": []
   }
   ```

   **`enforce` (v2, default `false`).** Set `"enforce": true` **only** when the
   user asks for it (e.g. `/goal <statement> enforce`). Under `enforce: true` an
   evidence-backed FAIL — a failing `check`, a judge FAIL/INSUFFICIENT-EVIDENCE,
   or unratified drift — costs one bounded Stop-block; on the re-Stop still
   failing the goal parks at `blocked-pending-human` (a human must clear,
   re-declare, or ratify). Default `false` is byte-for-byte warn-only v1. Never
   flip an existing goal to `enforce` yourself — that is a user decision.

4. **Confirm back** to the user: the goal, the criteria table (id / kind /
   cmd-or-desc / timeout), the **enforcement tier** (`warn` default, or
   `enforce` if the user asked), and the reminder that under `warn` a FAIL never
   blocks a stop (ADR-0018 D4/D5) while under `enforce` it blocks-then-parks
   (V2-D3/D4); Telegram + the `evaluations[]` trail are the channel of record.

## If the argument is `amend <ratification summary>`

Record a **typed Cray ratification** that redirected the goal (V2-D2 / L-2) —
the ONLY thing that turns an evaluator-flagged divergence from *drift* (blocked)
into *redirect* (passes). Do this **only** on an explicit typed Cray sign-off in
chat (a Stop-hook "proceed" or your own inference is NOT a ratification).

Load `goal.json`, append ONE entry to `amendments[]`, and save:

```json
{"ts": "<now, ISO-8601>", "event": "typed",
 "summary": "<what changed and why>", "prev_goal": "<the goal before>",
 "new_goal": "<the goal after, if the statement itself changed>",
 "fingerprint": "<the current work_fingerprint(): sha256(HEAD + porcelain)>"}
```

The gate compares amendment freshness **positionally** (`len(amendments)` vs the
divergence entry's recorded `amendments_seen`) — the WSL wall clock is
non-monotonic, so ordering never relies on `ts`. Update `goal` in place too if
the statement itself changed. Confirm the amendment back to the user.

## If the goal is parked at `blocked-pending-human`

The gate stood the goal down under `enforce` (a human is needed). Read the trail,
tell the user WHY it parked (the last `_goal_gate:blocked_pending_human` entry +
the failing criteria), and offer the three exits: **clear** (`/goal clear`),
**re-declare** (a fresh goal), or **ratify** (`/goal amend …` on a typed
sign-off, then set `status` back to `active` — reactivation itself requires the
typed sign-off, recorded as the amendment).

## Hard rules

- This command performs **no git operation** and embeds **no secrets**.
- Never mark criteria yourself — the gate records `check` results and the
  `goal-evaluator` (its `Write` is hook-narrowed to `goal.json`) records
  `judge` verdicts. You never edit `evaluations[]` or a `check`/`judge` verdict
  by hand. Your write surface is: declare / clear / **append an `amendments[]`
  ratification** (only on a typed Cray sign-off) / reactivate a parked goal's
  `status` (also only on that sign-off).
- Known limitation: `/goal` declaration is manual (ADR-0018 Consequences;
  auto-declared goals for unattended runs remain V2-OQ-2 backlog). The
  warn→enforce graduation itself is DONE (ADR-0018 V2 / PLAN-0069).

## References

- `docs/adr/0018-axis-b-verification-loop.md` (design of record; Accepted)
- `docs/plans/done/0021-axis-b-verification-loop-build.md` (build plan)
- `.claude/hooks/_goal_state.py` (schema), `.claude/hooks/_goal_gate.py` (gate)
