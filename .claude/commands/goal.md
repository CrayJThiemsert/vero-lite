---
description: Declare (or clear) the session goal for the Axis-B verification loop — writes .claude/state/goal.json, which the Stop-hook goal gate then checks every turn (ADR-0018 / PLAN-0021)
argument-hint: <goal statement, optionally with source: PLAN pointer> | clear
---

# /goal — declare or clear the session verification goal

You (the main Code agent) maintain the Axis-B goal artifact at
`.claude/state/goal.json` (gitignored; schema = `.claude/hooks/_goal_state.py`,
ADR-0018 §spec 1). The Stop-hook goal gate (`_goal_gate.py`) reads it at every
Stop: runs `check` criteria deterministically, dispatches the `goal-evaluator`
subagent for `judge` residue, and warns/releases per the ratified fail-open,
warn-only-v1 semantics. The argument is: `$ARGUMENTS`

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
   the total deterministic budget at Stop is 600 s
   (`CLAUDE_GOAL_CHECK_BUDGET_S`); a timeout/skip is unresolved, never a pass
   (VX-2). Commands run **argv-without-shell** from the repo root: no `&&`,
   no pipes — one command per criterion.

3. **Write the file** (`Write` to `.claude/state/goal.json`, honoring a
   `CLAUDE_GOAL_PATH` override if set):

   ```json
   {
     "schema_version": 1,
     "goal": "<the one-sentence goal>",
     "source": "<PLAN pointer, if any>",
     "session": <current session number>,
     "created": "<now, ISO-8601 with offset>",
     "status": "active",
     "criteria": [
       {"id": "C1", "kind": "check", "cmd": "<scoped command>",
        "desc": "<what it proves>", "timeout_s": <seconds>},
       {"id": "J1", "kind": "judge", "desc": "<judgment residue>"}
     ],
     "evaluations": []
   }
   ```

4. **Confirm back** to the user: the goal, the criteria table (id / kind /
   cmd-or-desc / timeout), and the reminder that the gate is **warn-only v1,
   fail-open** (ADR-0018 D4/D5): a FAIL never blocks a stop; Telegram + the
   `evaluations[]` trail are the channel of record.

## Hard rules

- This command performs **no git operation** and embeds **no secrets**.
- Never mark criteria yourself — the gate records `check` results and the
  `goal-evaluator` (its `Write` is hook-narrowed to `goal.json`) records
  `judge` verdicts. You do not edit `evaluations[]` or `status` by hand;
  declare/clear is your whole write surface.
- Known v1 limitation: `/goal` discipline is manual (ADR-0018 Consequences;
  auto-declared goals for unattended runs are OQ-8 backlog).

## References

- `docs/adr/0018-axis-b-verification-loop.md` (design of record; Accepted)
- `docs/plans/0021-axis-b-verification-loop-build.md` (build plan)
- `.claude/hooks/_goal_state.py` (schema), `.claude/hooks/_goal_gate.py` (gate)
