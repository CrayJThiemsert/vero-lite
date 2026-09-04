# Probe-battery definitions (committed evidence)

A probe battery's **coverage report is not reviewable without its definition.** The
report says `PROBE-COVERAGE: COMPLETE`; only the definition says *which* mutations ran,
against which nodes, and which claims were exempted rather than witnessed. PLAN-0120
Step 5 already required the definition to travel with the report — *"PLAN-0117 committed
no battery file, so the definition is reviewable only if it travels with the report"* —
and it was skipped twice running. These files close that.

Convention, from session 278: **a battery whose result is cited to close an acceptance
criterion is committed here**, named `<plan-slug>-<step-or-scope>.json`. Precedent for
committing a battery beside its subject: `benchmarks/intake_extraction/probe_battery.json`.

Run one with:

```bash
python -m tools.probe_battery run --battery tests/batteries/<file>.json
```

## What is here

| file | claims | RED | exempt | closes |
|---|---|---|---|---|
| `plan-0120-step1-db-guard.json` | 21 | 7 | 14 | AC-3 / AC-4 / AC-5 |
| `plan-0120-step2-session-hooks.json` | 31 | 14 | 17 | AC-6, AC-7 parts (b)+(c) |
| `plan-0120-step3-race-report.json` | 8 | 3 | 5 | AC-11 |
| `plan-0120-step4-gate.json` | 14 | 8 | 6 | AC-8's two `_run_one_check` artifacts |
| `plan-0120-ac1-ac2-route-a.json` | 19 | 3 | 16 | AC-2, and AC-1's offline half (route (ก)) |
| `plan-0120-ac7-token-field.json` | 16 | 13 | 3 | AC-7 part (a) — the token's measured fields |
| `plan-0120-ac8-pin-module.json` | 5 | 4 | 1 | AC-8's cross-file pin, incl. **declared probe 8c** |

## Why the last two exist — the gap that committing these made visible

The first five were written per-step during s277. The union of their `claim_sources` is
**four modules**. Two artifacts that PLAN-0120's acceptance criteria name were in none of
them:

- `tests/tools/test_db_guard.py` — **AC-7's artifact (a)**, the token-fields test
- `tests/handoffs/test_goal_gate_contended_exit_pins_the_guard.py` — **AC-8's cross-file
  pin**, whose **declared probe 8c had never run**

So `PROBE-COVERAGE: COMPLETE` on those five was true *and* said nothing about those two
artifacts: a coverage report is scoped to its own `claim_sources` denominator, which is
not the same set as the obligations the AC ledger rests on. AC-7 and AC-8 were ticked on
that reading and the tick was premature. `plan-0120-ac7-token-field.json` and
`plan-0120-ac8-pin-module.json` close it — both `PROBE-BATTERY: PASS`, `GAPS: 0`.

**The join key is each probe's `node_id`**, which is what makes the mismatch computable
rather than a matter of reading prose carefully.

## Two things a reader should know before trusting these

**Step 2 re-ran Step 1's probes.** `plan-0120-step2-session-hooks.json` repeats `P1`–`P6`
from Step 1 alongside its own `6a`–`X1`. The two files are not disjoint, so probe counts
across them do not simply add.

**Three exemptions are marked INEXPRESSIBLE rather than "not probed"**, and the
distinction is deliberate (CLAUDE.md §8: *a case the system cannot express is registered
as inexpressible, in writing, with its reason*):

- the reserved code's `5 < code < 128` range — reddening it alone needs **both** literals
  moved together, which one `old`/`new` pair cannot express;
- `validated_role`'s malformed-role message — the test is parametrized over **six** bad
  roles, so any message mutation reddens all six and the driver correctly refuses to
  credit it under one-mutation-one-assertion;
- `advisory_key`'s determinism — it is the positive control for the uniqueness probe, and
  reddening it alone needs per-call entropy no substitution provides.

The parametrization limit is worth knowing before writing a probe: a single assertion
inside a `@pytest.mark.parametrize` cannot be witnessed unless the mutation is targeted
at one parameter value. `plan-0120-ac7-token-field.json`'s `T-ok` does exactly that, at
`role_2` — verified by `git grep` to be used in no other test.
