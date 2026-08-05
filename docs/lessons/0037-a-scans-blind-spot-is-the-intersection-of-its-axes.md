# Lesson #0037 — A scan's blind spot is the intersection of its axes; naming one axis reads as having named the gap

**Date:** 2026-08-05 (session 206; the escaping site was found 2026-08-04)
**Class:** advisory (guard design / coverage claims)
**Trigger:** PLAN-0099's ordering guard recorded its own limit in Out of Scope
and was praised for it. Then
[#1035](https://github.com/CrayJThiemsert/vero-lite/pull/1035) found a real
wall-clock ordering bug that the guard could not see — and it escaped on **three
axes at once**, only one of which that Out-of-Scope note had named.

## The lesson

**A scan's coverage is the *intersection* of its axes, so its blind spot is the
union of their complements — and a note that names one axis reads, to a later
reader, as having characterised the whole gap.**

PLAN-0099 did the disciplined thing: it wrote its limitation down. The note is
accurate. It is also **one third of the exposure**, and that is what made it
misleading rather than merely incomplete — a reader who had internalised
"the guard is vocabulary-scoped" would go looking for a *stamp column with an
unusual name* and would still not find this site, because the site is not in the
scanned directory and is not an `order_by` call.

The corollary for review: **widening the axis you documented would not have
caught it.** Adding `at` to the vocabulary changes nothing here. Coverage
arguments have to be made per-axis, and the axes multiply.

## The guard's three axes, each verified in source

`tests/services/db/test_run_analytics_ordering_guard.py`:

1. **Directory scope** — `_SERVICES = _REPO_ROOT / "services"` (`:200`), walked by
   `_scan_services()`. Nothing outside `services/` is ever parsed.
2. **Call shape** — `offending_sites()` matches only `order_by(...)` call
   arguments. A Python `sorted()` is structurally invisible.
3. **Column vocabulary** — nine hand-picked names, pinned by
   `assert len(_WALL_CLOCK_WIDE) == 9` (`:338`): `started_at`, `created_at`,
   `updated_at`, `entered_at`, `accepted_at`, `opened_at`, `linked_at`,
   `occurred_at`, `fired_at`.

The guard states axis 3 about itself, honestly, at `:30-33`:

> These are nine hand-picked names. A timestamp column named anything else is
> invisible here, so the completeness this guard backs is scoped to the
> vocabulary — a future stamp column either joins this set or joins the blind
> spot.

## The site that escaped all three

`verticals/fleet_maintenance/task_chain.py`, in the form it had before #1035
(recover it from git at `c99132c^` — it is **not** at HEAD, so cite the commit or
the migration, never a current line number):

```python
for event in sorted(events, key=lambda e: (e.at, e.event_id)):
```

- **outside `services/`** — it is in `verticals/`;
- **a Python `sorted()`** — there is no `order_by` to match;
- **on a column named `at`** — outside the nine.

Any one of the three would have hidden it. All three held at once.

And it was not cosmetic: that reduction feeds `stale_items` → the LINE nudge
sweep, so a backward clock step let the superseded flip win in **both**
directions — a finished step nudged forever, a reopened one silently un-chased.

## What PLAN-0099 actually predicted

Its Out of Scope
(`docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md:401-404`)
reads:

> ❌ Wall-clock `order_by` sites invisible to the widened scan because their
> column names fall outside the chosen nine-name `_WALL_CLOCK` vocabulary — the
> ledger's completeness is vocabulary-scoped (see §Coverage); a future timestamp
> column joins the vocabulary, or it joins the blind spot.

**Axis 3 only** — and note it even says *"`order_by` sites"*, which quietly
assumes axis 2 away inside the sentence meant to disclose a limit.

The first place all three are enumerated together is **after the fact**, in the
migration that fixes the escaped site — `alembic/versions/0025_task_event_seq.py:33-38`:

> It was not weighed and excluded — it was **invisible**. PLAN-0099's guard scans
> `services/` only, matches only `order_by` calls, and only against a nine-name
> `_WALL_CLOCK` vocabulary… PLAN-0099's Out of Scope records that blind spot in
> as many words; this revision is the first instance found inside it.

That last clause is generous to the earlier note, and this lesson exists to say
so precisely: the Out-of-Scope recorded **one** axis of a three-axis gap.

## A second, quieter finding: the ledger's own vocabulary drifted

PLAN-0099's §Coverage ledger row **7** is labelled **`ALLOWLISTED`**
(`0099:261`), while the phrase **`KNOWINGLY LEFT`** appears at `:235-236` on
*sibling* rows. Both mean "seen and left", and `cases.py:263-268` cites the row
using the sibling phrase. Harmless in isolation; worth knowing before quoting,
because a lesson or an ADR that quotes "KNOWINGLY LEFT (ledger #7)" is quoting a
label that row does not carry.

## How to apply

- **When a guard records its limits, enumerate every axis it filters on** —
  scope, match shape, and value set are three separate claims, and a reader takes
  a stated limit as *the* limit.
- **State coverage as an intersection.** "Every `order_by` in `services/` on one
  of nine columns" is honest. "Every wall-clock ordering site" is what the same
  guard gets read as.
- **Before widening a guard, ask which axis the escape used.** Widening the
  documented axis is the reflex, and here it would have changed nothing.
- **A guard's ledger arithmetic proves internal consistency, not coverage.**
  PLAN-0099's `12 = 7 + 5` reconciles perfectly and says nothing about the site
  that was never scanned.

Related: [`#0034`](0034-deliberate-gate-outside-the-scanned-surface.md) — the same
shape one level up (a decision recorded outside the surface it would be looked
for on); [`#0036`](0036-a-tiebreak-buys-repeatability-not-order.md) — the defect
this site actually was.
