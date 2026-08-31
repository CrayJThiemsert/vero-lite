# Lesson #0054 — the clock was injected; the bucket key was not

**Session:** 266 (2026-08-31 to 09-01) · **Measured on:** two incidents in one
session at two granularities — one that took `main` red in seven hours, one still
latent and unfixed · **Status:** advisory (§1 precedence — promote to ADR if it must bind)

## The claim

Two functions in this repo take a clock as an **explicit parameter** rather than
reading an ambient one, and `load_monthly_export` says why in its own docstring:

> *"``now`` is a parameter, not an ambient clock … an export re-run for last month
> must compute the exception labels that month's report showed, not today's."*

That discipline is correct and it was applied. **It still did not hold, because the
other parameter — the one that names which BUCKET the record belongs to — is
computed by the caller from the same ambient clock the injection was meant to
avoid.**

```python
now = datetime.now(UTC)
order = await allocate_repair_order_no(session, case_id=case_id, year=now.year, now=now)
#                                                                    ^^^^^^^^
#                            the clock is injected here ------------------- and read here
```

Injecting the clock **one frame short** is indistinguishable from not injecting it,
at exactly the boundary where it matters.

## What happened — the same defect at two granularities

Both buckets are defined in **Asia/Bangkok**; both keys were chosen from a **UTC**
clock. Bangkok is UTC+7, so the two disagree for the **last seven hours of every
boundary** — 17:00 to 24:00 UTC on the final day.

| | the bucket | who chose the key | fires | found |
|---|---|---|---|---|
| **month** | the accounting month (`month_bounds(..., timezone=EXPORT_TIMEZONE)`) | 6 test call sites, from `datetime.now(UTC)` | every month | **in 7 hours** — it took `main` red on the clock alone |
| **year** | the repair-order series (`MAX(seq) WHERE year = year`) | 2 **product** call sites, from `datetime.now(UTC)` | every year | **not yet. Still unfixed.** |

### The month one, fixed (#1340)

Three DB-backed tests seeded a row into September and then asked for August's
report. `month_bounds(2026, 8)` ends `2026-08-31T17:00Z`; the seeded audit row sat
at `17:16Z`, sixteen minutes past the end. The **product was not affected** — the
export route takes `year` and `month` as path parameters, so the caller names the
month, which is the right shape for an accounting export.

Notably, **one test module already had it right.** `_this_month()` in
`tests/api/test_repair_spend_export_scenario.py` converted to Bangkok before taking
year and month — which is exactly why that module stayed green while two others went
red. The rule had been written twice; the copy is what failed. It now has one home.

### The year one, still open

`allocate_repair_order_no` partitions the series by `year` — `MAX(seq)` is scoped to
it — and `format_repair_order_no(year, seq)` prints it: **`RC-2026-0007`**. Both
production callers pass `year=now.year` from a UTC `now`, with no conversion
anywhere in either file:

- `services/api/routers/cases.py` — the close-out endpoint
- `verticals/fleet_maintenance/operate_seed.py` — the demo seed, deliberately using
  the same path so it cannot drift from production

So for the seven hours between 17:00 UTC on 31 December and midnight UTC, a repair
closed on **1 January in Bangkok** is allocated a number in the **previous** year's
series, consuming a sequence number in a year that has ended, and the wrong year is
printed on the number that reaches the month-end CSV and the operator's screen.

🔴 **The invariant survives while its meaning does not.** The docstring promises
*"gap-free within a year, by construction"* — and that stays **true**. The series has
no holes. What breaks is the thing nobody wrote down: *the numbers in the 2026 series
are the repairs that closed in 2026.* An invariant that still passes is the worst
possible cover for a defect, because every check keyed on it is green.

🔴 **Nothing tests it.** The order-number tests pass a fixed `_YEAR` constant
(`tests/services/db/test_concurrent_writer_races.py`), which exercises the function
and never the callers' derivation. The two lines that hold the defect are covered by
no test at all.

## The test

1. **When a function takes both a clock and a bucket key, ask who computes the key
   and from which clock.** "We pass `now` explicitly" is not the answer; it is the
   thing that makes the leak look handled.
2. **Detection frequency is inverse to severity here, and that is not a coincidence.**
   The monthly one fires twelve times a year, so it surfaced within hours of being
   reachable. The annual one fires once, for seven hours, onto a number a human reads
   off paper and keys into an accounting system. **The rarer boundary is the more
   dangerous one AND the less likely to be found by running the suite** — so it is
   the one that needs a deliberately-pinned test rather than a hope that CI runs at
   the wrong moment.
3. **A guard for a rare boundary must pin the instant explicitly.** A test that runs
   "now" is green 99.9% of the time and proves nothing about the 0.1%.
   `tests/services/db/test_accounting_month.py` does this for the month: it names
   `2026-08-31T17:16Z` and asserts against `month_bounds` itself, plus a non-vacuity
   case that the UTC month really would have excluded the row.
4. **Store in UTC; bucket in the business timezone.** These are different decisions
   and only the second one was ever ambiguous here.

## What this does NOT say

- It does not say "avoid UTC". Storing and comparing instants in UTC is right, and
  `occurred_at >= start` against UTC bounds is exactly how the export should work.
- It does not say either function is wrong. Both signatures are good — `now` and the
  bucket key are separate parameters, which is what made the fix a caller-side change
  and not a redesign.
- It does not claim the year defect has ever fired. As far as anyone knows it has
  not. It is latent, and it is recorded here because a defect that fires once a year
  is one nobody will rediscover by accident.

## Where this fires

- 🔴 **UNFIXED at the time of writing:** the two `year=now.year` call sites above.
  Fixing them is a caller-side change of the same shape as #1340, but it is
  **product** behaviour and wants its own decision — in particular whether the
  demo seed should follow production here (it currently does, on purpose).
- The month half is closed: `tests/support/accounting_month.py` holds the rule,
  `tests/services/db/test_accounting_month.py` guards it, and
  `grep -rn "now.year|now.month" tests/` returns nothing.

## References

- PR #1340 — the month fix, with the paired A/B evidence (`main` 3 failed at
  17:37:12Z, the branch 15 passed at 17:38:25Z, one clock).
- `services/db/repair_spend_export.py` — `month_bounds`, `EXPORT_TIMEZONE`, and the
  `now`-as-a-parameter docstring that states the discipline this lesson extends.
- `services/db/repair_case_closeout.py` — `allocate_repair_order_no` and
  `format_repair_order_no`.
- Lesson #0053 (same session) — the other shape of "the measurement was right and the
  conclusion was not": there, two observers sharing one instrument; here, one
  discipline applied one frame short.
- Lesson #0026 — fix the pass/fail read before the run. Both incidents were read
  correctly only because the criterion was fixed first.
