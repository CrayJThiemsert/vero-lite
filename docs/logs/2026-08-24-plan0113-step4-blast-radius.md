# PLAN-0113 Step 4 — the blast radius, measured against the Step-0 baseline

**Date:** 2026-08-24 (session 252)
**Branch:** `feat/plan0113-step4-blast-radius`, cut from `main` = `ca6133e`
**Baseline compared against:** `docs/logs/2026-08-24-plan0113-step0-baseline.md` (`17defa0`)
**Event type:** measurement + a scratch positive control (restored byte-identical). No host
touched, no production change.

## Verdict

**AC-4 PASS.** Procurement's hero observable is byte-identical to the Step-0 capture, the
two structural counts still hold, and the positive control reddens — so the comparison can
detect a scoping change in procurement rather than being green by construction.

## 1. Procurement's hero-run observable — unchanged

Captured with the Step-0 recipe verbatim (the stub `ChatClient` **imported** from
`tests/verticals/procurement/test_hero_run.py`, never re-implemented).

| Check | Result |
|---|---|
| 11 pinned values | **0 differ** from baseline |
| hero top-level keys | match (13 keys) |
| audit top-level keys | match (4 keys) |
| hero sha256 | `b66d7ae7e17835c4…` — **matches** |
| audit sha256 | `a8f2e33100e422c8…` — **matches** |

Both digests matching is the strong result: the Step-0 log warned a digest is only evidence
against the same serialisation, and this run reproduced that serialisation exactly.

## 2. 🔴 An AC-4 assumption that is FALSE — registered as inexpressible

AC-4 reads: *"apply a `scope_by` to procurement in a scratch copy → its comparison
reddens"*. **`scope_by` cannot be authored on procurement's event path at all.**

`ScopeBySpec` requires a declared `reads` list (`services/engine/procedures/spec.py`,
`StepInput._validate_scope_shape` — "scope_by requires a declared reads list"), and
**no step of `emergency_sourcing_round` declares `input.reads`**. Measured by loading the
spec, not by grep:

```
scope_by expressible on emergency_sourcing_round? False
  — no step of emergency_sourcing_round declares input.reads
```

Its `intake` is served by `_SeedQuery`, the co-existing seed executor
(`verticals/procurement/hero_demo/run.py::_executors`, PLAN-0062 SD-C / PLAN-0064 SD-1);
only the two **calm-path** procedures declare a read (`read_stock`, `reads: [Part]`).

**This is a STRONGER result than the AC asked for** — procurement's event path is not
merely unchanged, it is structurally incapable of carrying the clause today — but it is
recorded rather than silently upgraded, per `CLAUDE.md` §8: *"A case the system cannot
express is registered as inexpressible, in writing, with its reason."*

**Consequence for the control:** it targets the manual calm path's `read_stock`, the one
procurement step that CAN carry the clause. That still proves what the AC wants proven —
that a `scope_by` added to procurement is DETECTED — on the only surface where the
premise holds.

## 3. Positive control — it reddens

Scratch mutation: `scope_by: { field: part_id, from: trigger.entity_ids }` +
`when_absent: refuse` appended to the manual calm path's `read_stock`.

| | |
|---|---|
| mutation reached the file | `procedures.yaml` `20f148e4230b` → `8257dad48cdc`, Δ **+95 bytes** |
| observable | `test_calm_path_run_endpoint.py` + `test_calm_path_production_runnability.py` + `test_intake_shadow_parity.py` |
| under the mutation | **4 failed, 6 passed** |
| restore | **byte-identical** (`20f148e4230b`) |

## 4. Structural counts — still what the baseline pinned

Counted from the **parsed** spec across all six verticals:

```
{'manual': 8, 'event': 2, 'schedule': 3}   →  event=2, manual+schedule=11
```

Matches the Step-0 baseline exactly.

## 5. The three re-greps PLAN-0113's blast-radius section requires

The s202 instruction — *"Step 2's implementer re-greps `trigger_context`, `entity_ids`, and
`fleet-wide` before closing AC-4"* — run on this tree:

- **`trigger_context`** — 67 hits across 13 files under `services/` + `verticals/`.
  `query_step.py` now appears, which is Step 2's wire; nothing else is new.
- **`entity_ids`** — 10 files, including `verticals/fleet_maintenance/procedures.yaml`
  (Step 3's clause) and `services/api/static/assets/view-hero.js` (UI read-side).
- **`fleet-wide`** — 🔴 **`docs/STATUS.md` still carries the stale narrative in two places**
  (the Current Focus paragraph and a 2026-08-22 row). That is **blast radius #10 / Step 7**,
  not Step 4, and it is confirmed still outstanding rather than assumed. Every `fleet-wide`
  hit under `tests/` is now HISTORICAL framing ("used to be", "the bound PLAN-0113 replaced")
  and correct as written.

## 6. Instrument repairs — three, all on the check, none on the criterion

The first run reported `AC-4: FAIL` on all three legs. Every one was the instrument.

1. **Counts read 12 manual / 4 schedule against a baseline of 11.** The check counted
   `git grep -c 'trigger: manual'` LINES — which also match prose in comments (`# L-8: only
   manual runs in Phase 1`; fleet's SD-5 block explaining that manual firing survives).
   Repaired to count loaded `Procedure.trigger` values. The parsed spec is the oracle; a
   grep over commented YAML is not.
2. **`amount` appeared to have changed** to `{'value': '288000', 'currency': 'THB'}` — while
   **both digests matched**, which is impossible if the object had moved. The Step-0 log
   renders the figure as "288000 THB" for a human reader; the object holds a money mapping.
   The transcription was wrong, the artifact was not. (The instrument-vs-subject test:
   when a check and a stronger check disagree, suspect the weaker one.)
3. **The control did not redden** — it ran the scheduled demo and the hero suite, neither of
   which exercises `read_stock`, while the mutation lands on the MANUAL calm path. A control
   aimed at an observable the mutation cannot reach proves nothing.

None of the three was repaired by relaxing what the check demanded.

## Next

Step 6 (demo integrity offline, AC-6) and Step 7 (governance records, AC-7 — including the
`docs/STATUS.md` fleet-wide narrative found still live in §5 above). Step 8 stays gated on a
typed Cray go per occasion and per phase.
