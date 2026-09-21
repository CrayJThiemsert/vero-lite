# The seven goal-gate rounds that judged PR #1545

**Date:** 2026-09-21 · **Session:** 316 · **Event type:** rehome (preservation of a gitignored verdict trail)
**Author:** Claude Code (Tier 2)
**Commit:** the commit this file lands in
**Source, gitignored:** `.claude/state/goal.json`, entries `evaluations[0]`–`[14]` — per-machine working state, which is why this file exists

---

## Why this file exists

PR [#1545](https://github.com/CrayJThiemsert/vero-lite/pull/1545) (squash `1a3894a9`) added
a `tag --reflow` block to `tools/probe_battery/README.md` and a new lesson,
`docs/lessons/0066-place-the-record-where-the-breaker-must-look.md`. Both were written under
an Axis-B session goal (ADR-0018) whose `judge` criteria were fixed before either change
existed, and the `goal-evaluator` judged the work seven times before the PR merged.

Those verdicts were appended to the session goal file, which lives under the gitignored
`.claude/state/`. Lesson 0066 first pointed its readers there — at a file that exists on one
machine and is rotated when a goal closes, which is an expiring home by that lesson's own
test. This file is the tracked copy.

**Its scope is closed on purpose:** it records the seven rounds that judged PR #1545, each
named by fingerprint. A closed round does not change, so nothing here goes stale when later
rounds are appended to the same goal.

## Key metrics — the seven rounds

Each fingerprint below was bound to its commit by **recomputing it** with the gate's own
function, `work_fingerprint()` in `.claude/hooks/_goal_gate.py`:
`sha256(git rev-parse HEAD + "\n" + git status --porcelain)`, first 16 hex characters. All
seven recompute exactly with an empty porcelain, so the working tree was clean at every
evaluation.

| Round | `evaluations[]` | Fingerprint | Commit judged | J1 | J2 | J3 |
|:-:|:-:|---|---|:-:|:-:|:-:|
| 1 | 1 | `d1df13c8c594d198` | `90d88987` | FAIL | FAIL | PASS |
| 2 | 3 | `18840572eb41744f` | `fb5d7358` | FAIL | PASS | PASS |
| 3 | 5 | `590227f6868470bb` | `00aabc90` | PASS | FAIL | PASS |
| 4 | 7 | `e6463c2015f92b83` | `60bcf334` | PASS | FAIL | PASS |
| 5 | 9 | `866f74213fb77c8b` | `88aecddd` | PASS | FAIL | PASS |
| 6 | 11 | `8234ea5352af83b1` | `370fa245` | PASS | FAIL | PASS |
| 7 | 13 | `aaad9fbc6d5580f6` | `f8c4dc43` | PASS | FAIL | PASS |

- Deterministic checks C1–C5 read `pass` in every one of the seven rounds.
- PR #1545 carried **eight** commits. The eighth, `ecd271ff`, was never evaluated on its own:
  no recorded fingerprint recomputes from it, because `60bcf334` superseded it before the
  gate next fired.
- **Round 7 is the state that merged.** `git diff f8c4dc43 1a3894a9` over the two changed
  files is empty (0 lines; the same diff against the pre-PR base `bf919c01` is 220 lines).
  So `main` carried round 7's J2 FAIL, and the follow-up change that lands with this file
  repairs it.
- The criteria: J1 — the README text invents no guarantee its two named sources lack.
  J2 — the lesson cites only facts re-derived on disk that session, each with a pointer.
  J3 — neither document records PLAN-0128 closeout item ① as decided.

## What each round's verdict led to

The commit that followed each round, by its own subject line (`git log` on the PR branch).
These are the author's descriptions of the repair, not the evaluator's findings; the findings
themselves are in `evaluations[]`.

| After round | Next commit | Subject |
|:-:|---|---|
| 1 | `fb5d7358` | repair the two defects the goal-evaluator refuted |
| 2 | `00aabc90` | drop an over-broad restore claim the second evaluation caught |
| 3 | `ecd271ff`, `60bcf334` | a uniqueness claim the battery refuted, and cite by name not by offset · the last live positional locator, which falsified the page's own rule |
| 4 | `88aecddd` | stop the page narrating its own revision history |
| 5 | `370fa245` | stop describing the trail at all, and bound an over-broad claim |
| 6 | `f8c4dc43` | drop three unforced claims; the stated hypothesis was wrong |
| 7 | — | PR merged at round 7's state |

## Two findings about the mechanism itself

**1. The gate runs `check` commands from the Windows side.** Recorded in lesson 0066 under
*The same rule, applied to a consumer that is not a human*. The first declaration of this
goal used POSIX paths in its check commands and scored `error` on four of five; it was
archived rather than deleted, per PLAN-0123 R8.

**2. A surfaced decision survives only if the evaluator embeds it in a verdict's reason.**
`_goal_state.Evaluation` has no field for surfaced decisions — the union of keys across all
fifteen entries is `amendments_seen`, `deterministic`, `detail`, `divergence`, `evaluator`,
`fingerprint`, `judged`, `ts` — and its docstring records that an unknown field on disk is
silently stripped by the next `save_goal`. Measured across the trail:

- **SD-1** (whether J1's line references are bounds or pointers) is written into the
  `judged` reasons of `evaluations[3]`, `[5]`, `[7]`, `[9]`, `[11]` and `[13]`, so each round
  could see the previous rounds' reading of it.
- **SD-2** (whether J2's "both documents" means two files or two changed bodies of text) was
  raised by round 6 in its returned message, but `evaluations[11]` does not contain it.
  Round 7 therefore could not see it, and said so in `evaluations[13]`.

A decision the evaluator surfaces for the human is therefore durable by accident, not by
design. Neither SD-1 nor SD-2 was ruled before the PR merged; `amendments[]` held no entry
through round 7.

## Reference

- PR [#1545](https://github.com/CrayJThiemsert/vero-lite/pull/1545) — the eight commits
  named above
- `docs/lessons/0066-place-the-record-where-the-breaker-must-look.md`
- `.claude/hooks/_goal_gate.py` (`work_fingerprint`), `.claude/hooks/_goal_state.py`
  (`Evaluation`)
- `docs/adr/0018-axis-b-verification-loop.md`
- `docs/plans/done/0123-goal-declaration-trigger-and-templates.md` (R8)
