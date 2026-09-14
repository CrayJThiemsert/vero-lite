# Lesson #0063 — sixteen instruments lied, and the fix that followed was built but not reached

**Session:** 298 (2026-09-14), carrying the s288–s289 census · **PRs:** #1459, #1461, #1463
(the build), #1466 (AC-9), #1472 (a renderer defect), #1478 (AC-12), and the PLAN-0123 closeout
· **Status:** advisory (§1 precedence — promote to ADR if it must bind). The binding halves
already live in `CLAUDE.md` §8 and in the renderer's clause-named refusals.

_[Owed since PLAN-0123 Step 0 — "a lesson under `docs/lessons/` carrying §1.2 and §1.3 … in
the same PR or the next" — and never written. Found at Step 5, when the closeout went to
cross-link it: `was an error`, an unexecuted deliverable. Written at that closeout.]_

---

## The measurement

Two sessions, **sixteen instrument errors**: ten from s288's census, six from s289's first
field test of the goal gate. The table is the record and is not copied here —
[`PLAN-0123` §1.2](../plans/done/0123-goal-declaration-trigger-and-templates.md). Every row is
an instrument returning a **confident** wrong answer: a `grep -c` counting a word inside a
different field; a background wrapper's `0` masking `command not found`; a `$?` expanded one
shell layer early; a checker printing `PASS` while exiting `1`; a HEAD-pinned check reading
`fail` at four consecutive Stops after its PR merged, with the work correct and shipped.

## What the sixteen had in common

- **Not one was caught by reading more carefully.** Every catch was two numbers disagreeing —
  `139 ≠ 140`, `had_model=True` against a prior reading, `PASS` beside `exit 1`.
- **A control certifies only what it is exposed to.** It must be able to fail the same way the
  claim can, and be about the same subject; a control on a different model certified nothing.
- **A bare PASS/FAIL withholds the evidence the instrument collected.** Three of s289's six
  were one-step diagnoses only because the report printed its values.
- **The exit code and the printed verdict can disagree** — and the gate reads one while the
  human reads the other.
- **A check has an evidence basis, and a merge can move it.**
- **`CLAUDE.md` §8 already stated the rules that would have prevented several.** They were
  skipped. More prose was measured not to be the fix. Two catches were luck.

## What was built, and what the field then measured

PLAN-0123 answered structurally, every AC witnessed by a battery: a renderer whose goals
satisfy R1–R8 or are refused by clause name; `tools/absent.py`, whose control can fail;
one value for exit code and printed verdict across every instrument; a `basis-moved` check
state; a driver that writes its own provenance-stamped report.

Then it measured whether any of it would be **used**, and both readings failed:

- **The moment (AC-9).** An advisory at the instant of taking a reading, replayed offline
  first: it matched **27.1 %** of all Bash calls against a 5 % ceiling. Taking a reading is
  not a rare event. About half its fires were well aimed; it was far too talkative, and it
  never shipped.
- **The templates (AC-12).** One template goal in five sessions, none passed. After the
  renderer's quoting defect was fixed (#1472), the templates were reached for **zero** times
  in three sessions. The one surface an agent reads at declaration time,
  `.claude/commands/goal.md`, had never gained the pointer PLAN-0123 OQ-3 ruled it would.

Cray read that NOT MET as a failure of **reach**, not of the templates (s298, typed).

## The lesson

1. **An instrument's confidence is not evidence; a contradiction between printed numbers is.**
   Print the values. Control on the same subject, exposed to the same failure. Make the exit
   code and the verdict one value.
2. **A structural fix is structural only at the surface its consumer reads at the moment of
   need.** `CLAUDE.md` §4 says it for rules — *name the consumer, check the home is in that
   consumer's input* — and it holds for tools. Eight ACs witnessed that what was built was
   **correct**. None asked whether anyone would be **pointed at it**, so the build passed
   every check it had and still measured as unused.

## How to apply

- Shipping a tool meant to replace a manual habit: put the invocation in the surface read at
  that moment (the command prose, the skill, the catalogue) **in the same PR**, and pin it
  with a test that runs the documented command against the real tool — the closeout's
  `tests/handoffs/test_goal_command_points_at_the_renderer.py` is the shape.
- An adoption count comes back low: check the entry points **before** judging the tool.
- Writing an AC for a tool's value: measure reach and correctness as separate claims. A green
  on one says nothing about the other.

Related: [`0056`](0056-suspect-the-instrument-before-the-artifact.md) (the instrument is the
first suspect), [`0060`](0060-an-archive-move-is-three-acts-not-one.md) (archiving is the last
inspection a PLAN gets — the moment this lesson was found missing).
