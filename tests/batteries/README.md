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

| file | probes | exemptions | closes |
|---|---|---|---|
| `plan-0120-step1-db-guard.json` | 7 | 14 | AC-3 / AC-4 / AC-5 |
| `plan-0120-step2-session-hooks.json` | 14 | 17 | AC-6 / AC-7 |
| `plan-0120-step3-race-report.json` | 3 | 5 | AC-11 |
| `plan-0120-step4-gate.json` | 8 | 6 | AC-8, and the offline halves of AC-1 / AC-2 |
| `plan-0120-ac1-ac2-route-a.json` | 3 | 16 | AC-2, and AC-1's offline half (route (ก), s278) |

## Two things a reader should know before trusting these

**Step 2 re-ran Step 1's probes.** `plan-0120-step2-session-hooks.json` repeats `P1`–`P6`
from Step 1 alongside its own `6a`–`X1`. The two files are not disjoint, so probe counts
across them do not simply add.

🔴 **These definitions do not cover every artifact their ACs name.** The union of all
five `claim_sources` is four modules. `tests/tools/test_db_guard.py` (AC-7's artifact
(a)) and `tests/handoffs/test_goal_gate_contended_exit_pins_the_guard.py` (AC-8's
cross-file pin) appear in **no** `claim_sources` and are named by **no** probe's
`node_id`; declared probe **8c** never ran. So `PROBE-COVERAGE: COMPLETE` on these files
was computed over a denominator that excluded those artifacts entirely — which is
exactly the gap that makes committing the definitions worth doing. Measured s278; see
PLAN-0120's AC-7 and AC-8 notes.
