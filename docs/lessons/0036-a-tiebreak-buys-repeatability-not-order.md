# Lesson #0036 — A tiebreak buys repeatability, not order; which one you need is decided by the consumer, not the query

**Date:** 2026-08-05 (session 206; both incidents landed 2026-08-04)
**Class:** advisory (ordering correctness / review heuristics)
**Trigger:** two PRs from two different sessions hit the same reflex on the same
day, in the same file — and reached **two different correct answers**.
[#1034](https://github.com/CrayJThiemsert/vero-lite/pull/1034) added a `uuid4`
tiebreak and was right; [#1035](https://github.com/CrayJThiemsert/vero-lite/pull/1035)
refused one and re-keyed on a monotonic `seq`, and was also right.

## The lesson

**A tiebreak makes a tied ordering *repeatable*. It does not make it *correct*.**
Those are different properties, and a random-keyed tiebreak buys only the first.

So the question a tied `ORDER BY` raises is never "which tiebreak column?" It is:

> **Does anything downstream act on this order?**

- **No consumer reads the order** — it is a list a human scans. Repeatability is
  the whole requirement, and a `uuid4` tiebreak delivers it at zero migration
  cost. Ship it, and *say in the code* that the order is arbitrary.
- **Something downstream acts on it** — a sweep, a state machine, a "latest wins"
  reduction. Repeatability is worthless here; the reduction needs the *true*
  order, which a random key cannot supply at any price. It needs a monotonic
  sequence, and that is a migration.

The trap is that both cases present identically at the call site: a wall-clock
`ORDER BY` that ties. The distinguishing fact is outside the query entirely.

## The two incidents, measured

Same file, same day, opposite prescriptions.

**#1034 — `GET /api/cases`, the display list.** `services/api/routers/cases.py:272`
now reads:

```python
.order_by(RepairCase.opened_at.desc(), RepairCase.case_id)
```

Two cases opened in the same millisecond tied, so the page was not repeatable
across refreshes, and with the endpoint's truncating `limit` a boundary case
could flicker on and off page 1. The `case_id` tiebreak ends the flicker.

**The PR's own framing is the useful part: it says the obvious reading is wrong.**
`case_id` is a `uuid4`, so the tiebreak buys repeatability, **not** newest-first
correctness — **measured 50.5 % over 20,000 reps**, which is a coin flip wearing
the costume of a fix. Recovering true insertion order needs a monotonic `seq`,
and PLAN-0099 §Coverage had already weighed exactly that for this endpoint and
left it (ledger row 7, `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md:261`).
**Cray ratified keeping it left.** The docstring at `cases.py:263-268` records
why, so the next reader does not re-derive it.

**#1035 — the task chain, a correctness path.** The same file's `_task_events()`
(now `cases.py:305`) moved the other way:

```diff
-                .order_by(RepairCaseTaskEvent.at)
+                .order_by(RepairCaseTaskEvent.seq)
```

Here the order feeds `stale_items` → the LINE nudge sweep, so a wrong order is a
wrong *action*: on a backward clock step the superseded flip won, and **both
directions were live failures** — a finished step nudged forever, a reopened one
silently un-chased. The pre-existing `event_id` tiebreak protected neither,
because `at` **led** the sort and so the tiebreak was never consulted on an
inversion — and `event_id` is a `uuid4` anyway. The fix is migration `0025`: a
DB-assigned `seq`, unique per `(tenant_id, seq)`.

The comment left at `cases.py:301-304` is the pairing stated in one line: an `at`
ordering here *"would read as though the clock were still the key, which is the
belief migration 0025 exists to end."*

## Why this is worth a lesson and not a code comment

Because the reflex is **right half the time**, which is the worst possible hit
rate for a habit. A reviewer who learned "tiebreaks fix flaky ordering" from
#1034 would have approved a `uuid4` tiebreak on #1035's path and shipped a bug
that fires only on a clock step, in a sweep nobody watches.

Two further traps this pair exposed:

- **A tiebreak on a leading wall-clock key never fires on an inversion.** It only
  breaks *exact* ties. The failure mode people actually have — a stamp that moved
  backwards — steps straight past it. `#1035`'s `event_id` tiebreak had been
  there the whole time and had never once been consulted.
- **A `uuid4` tiebreak looks deterministic in a test.** Seed two rows, assert an
  order, watch it pass — it passes because the two UUIDs happened to sort that
  way. #1034's test seeds **eight** tied cases for this reason: removing the
  tiebreak then fails at 1/8! rather than 1/2.

## How to apply

When you see a tied or wall-clock `ORDER BY`, before choosing a tiebreak:

1. **Name the consumer of the order.** If you cannot name one, it is a display
   list — a tiebreak is enough, and the code must say the order is arbitrary.
2. **If you can name one, a random tiebreak is not a candidate.** Reach for a
   monotonic sequence and accept the migration, or record the gap explicitly as
   PLAN-0099 did rather than papering it.
3. **Check whether the tiebreak can fire at all.** A tiebreak behind a leading
   wall-clock key is inert against backward steps, which is the failure this box
   actually produces ([`0007`](0007-harness-exit-code-artifact.md)'s sibling
   hazard; the clock measurement is in PLAN-0099).
4. **Make the test fail without the tiebreak.** More tied rows, not two — and
   drive `tests/clock_support.py`'s `Clock` rather than the host clock.

Related: [`#0037`](0037-a-scans-blind-spot-is-the-intersection-of-its-axes.md) —
the ordering guard that could not see #1035's site at all.
