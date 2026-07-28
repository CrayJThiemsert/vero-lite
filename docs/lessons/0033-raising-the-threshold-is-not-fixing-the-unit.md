# Lesson #0033 — Raising a threshold is not fixing a wrong unit of measurement

**Date:** 2026-07-25 (session 173; the recurrence spans sessions 168–172)
**Class:** advisory (guardrail design / false-positive diagnosis)
**Trigger:** L1 loop-detect false-fired on doc authoring on 2026-06-08 and was
"fixed" by raising the prose threshold 6 → 15 (Lesson #0021 fix #1). Between
2026-07-23 and 2026-07-25 the *same class* of false fire returned on **code**
paths four times in five sessions — s168 (`cli.py`), s169 (`run_analytics.py`),
s170 (`tests/support/run_corpus_factory.py`), s172 (PLAN-0093 Step 1) — of which
three deadlocked and **two ended in a Cray-authorised shell escape**. The
structural fix is PLAN-0094; the state-lifetime bug fix is PR
[#912](https://github.com/CrayJThiemsert/vero-lite/pull/912).

## The lesson

**When a guard false-fires, ask what it is counting before you ask how high the
bar should be.** Raising the bar is attractive because it is one line, it is
obviously "less strict", and it makes today's false positive go away. But it only
helps if the metric is right and the bar is wrong. If the *metric* is wrong,
raising the bar buys silence on the path class you raised and leaves the defect
live everywhere else — while weakening the true positive in the same motion.

L1's stated intent is to catch **directionless repetition** ("an agent loops > 6
rounds on the same problem", ADR-0013 row E.4). What it actually counted was
`PostToolUse` Write/Edit calls per file per turn — i.e. **touches**. Touches and
thrash are not the same quantity:

- six distinct successful edits implementing one ratified plan step → 6
- six retries of the same broken `old_string` → **0**, because `PostToolUse`
  fires only on success, so a failed Edit never reaches the counter at all

The second line is the damning one. The guard was not merely mis-calibrated
against productive work; it was **blind to the exact failure mode it exists to
catch**, and 100% of what it did count was forward progress. No threshold value
fixes that. 6 was not too low and 15 is not too high — the unit was wrong.

## Why the 2026-06-08 raise looked like a fix and wasn't

It was a real improvement in outcomes for one path class, and it was reasoned, not
careless: prose authoring genuinely has no `edit → test → fail → edit` feedback
loop to drive a directionless cycle, so a higher bar for `*.md` is defensible on
its own terms. Lesson #0021 §2 argued exactly that, and it was right.

What it did not do was change the quantity. So:

- **doc paths** got quiet, because 15 is above where legitimate authoring lands;
- **code paths** kept the old bar and kept false-firing — and code is where the
  deadlock is worst, because the documented escape (`git commit`) is itself
  blocked when `ruff`/`mypy` is red on the very file the guard has gated, and
  `--no-verify` is forbidden by CLAUDE.md §8.

Lesson #0021 §6 recorded the honest version at the time: distinctness-based
counting was "the most intent-true fix", explicitly deferred as "**A now, B
later**" (Cray, 2026-06-08). The deferral was a reasonable call under time
pressure. The failure was leaving it deferred for seven weeks while the symptom
was suppressed on one path class — which removed the pressure that would have
surfaced it sooner. **A suppressed symptom stops generating the evidence that
would justify the real fix.**

## The tell that you are raising a bar instead of fixing a unit

Ask: *can I state a threshold value that separates the good case from the bad
case?* If two behaviours you need to distinguish produce **the same number**, no
value exists and tuning is a dead end. For L1: "6 good edits" and "6 retries of
one broken anchor" both produced 6 (in fact the retries produced 0) — so the
answer was no, and that was knowable in 2026-06-08 without waiting for s172.

Two corollaries:

- **A threshold raise trades sensitivity for silence in one motion.** Going 6 → 15
  on docs also means a genuinely stuck doc loop now burns 15 attempts before
  anyone hears about it. You rarely want that trade; you usually want a different
  measurement.
- **"Finite, so a real loop still trips" is not a defence of the metric.** It was
  the stated safeguard on the 2026-06-08 raise, and it is true, but it only bounds
  the damage of a wrong unit — it does not make the unit right.

## How to apply

- Before changing a guard's threshold, write down the two behaviours it must
  distinguish and the number each produces. Same number → fix the metric.
- Prefer a metric where correct behaviour scores **zero**, not "less". L1's
  replacement counts non-progress (failed/rejected edit, repeated anchor,
  content-hash oscillation), so distinct forward edits score 0 and the bar stops
  being load-bearing for the common case.
- When you *do* defer the real fix, make the deferral generate pressure: leave a
  failing or skipped test, a tracking PLAN, or a dated tripwire. Lesson #0021 §6
  left prose only, and prose does not fail a build.
- If a guard is being routinely bypassed to get work done — two of the four L1
  fires ended in an authorised shell escape — treat the bypass rate as the
  primary signal about the guard, not as an operator problem to be disciplined.
- Check whether the guard's own **message** is telling the truth. L1's deny text
  advertised a reset path (`"for a subagent's edits — when the Agent tool
  returns"`, `pretooluse_loop_detect.py:142-143`) that was never wired, so agents
  following its advice waited for an event that could not fire.

## Related

- [[lesson-0021-l1-loop-detect-subagent-and-doc-threshold]] — the 2026-06-08 raise
  and its §6 deferral of the real fix ("A now, B later")
- [[lesson-0012-loop-detect-l1-vs-governance-doc-fillup-passes]] — the earlier
  recovery-over-retuning decision, and the "verbal ack ≠ unblock" meta-lesson
- `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` — the structural
  fix (non-progress counting, warn-before-deny, the reset paths)
- `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — the
  same shape resolved the same way: 14 misfires / 0 valid fires demoted an order
  to a suggestion rather than retuning it
- ADR-0013 row E.4 (`docs/adr/0013-autonomy-axis-relocation.md:90`) — the
  originating trigger, which specified "pause + Telegram alert", not a hard deny
