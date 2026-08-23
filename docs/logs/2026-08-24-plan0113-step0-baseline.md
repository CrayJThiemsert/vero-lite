# PLAN-0113 Step 0 — the pre-change baseline

**Date:** 2026-08-24 (session 250)
**Event type:** measurement only — no code changed, no host touched
**Baseline commit:** `17defa0` (`main`, tree clean, 0 open PRs)
**Why this file exists:** Step 4's regression gate (AC-4) compares against these
numbers. A baseline held only in a session transcript is not a baseline — the
session that needs it is a later one.

## The four gates, at CI scope

Run exactly as PLAN-0113 Step 0 specifies — **no path-scoped shortcuts**, because
the offline oracle is the gate (`CLAUDE.md` §8).

| Gate | Command | Result | rc |
|---|---|---|---|
| Lint | `ruff check .` (bare) | All checks passed | 0 |
| Format | `ruff format --check .` | 654 files already formatted | 0 |
| Types | `mypy --strict services/ verticals/` | no issues in **201 source files** | 0 |
| Tests | `pytest tests/` | **4267 passed, 8 skipped**, 2 warnings (695 s) | 0 |

**Matches the s246 reference exactly** (4267 passed / 8 skipped), so the tree
entering PLAN-0113 is the tree PLAN-0113 was scoped against.

⚠️ **`mypy` must name `verticals/` as well as `services/`.** Scoped to
`services/` alone it reports **137** files and still exits 0 — a green that omits
a third of the surface the PLAN changes. The 201 figure is the one to compare
against; a later run reporting 137 has narrowed its scope, not fixed anything.

## Procurement's hero-run observable (the AC-4 comparison target)

`emergency_sourcing_round`'s hero moment, captured offline — stub `ChatClient`,
no DB, no MS-S1, deterministic:

```python
from tests.verticals.procurement.test_hero_run import _stub_factory
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.hero_demo.run import (
    build_live_hero_governance_audit, run_hero_governance_moment,
)

hero  = await run_hero_governance_moment(
    FastenalCsvAdapter(), client_factory=_stub_factory, run_id="plan0113-step0-baseline")
audit = await build_live_hero_governance_audit(
    FastenalCsvAdapter(), client_factory=_stub_factory)
```

The stub is **imported from the test module, never re-implemented** — a private
copy drifts silently from the thing AC-4 compares against, and a drifted baseline
is worse than none.

### Pinned values — the primary baseline

These are **instrument-independent**: they survive any change to how the snapshot
is serialised, so a Step-4 assertion can name a field rather than a digest.

| Observable | Baseline value |
|---|---|
| `supplier_id` | `SUP-RAPIDMRO` (the off-AVL override) |
| `po_id` | `PO-2026-0412` |
| `amount` | `288000` THB (derived, 96,000 × 3) |
| `doa_tier[0].resolved_tier_id` | `CONTROLLER` |
| `doa_tier[0].resolved_approver_id` | `appr-controller` |
| `doa_tier[0].amount` | `288000` THB |
| `sod.governed` | `True` |
| `sod.requester.person_id` | `req-maint-planner` |
| `sod.approver.person_id` | `appr-controller` |
| `audit.provisional` | `True` |
| `audit.source` | `live-run` |
| hero top-level keys | `amount`, `asset_id`, `declared_tier_id`, `doa_tier`, `governed_decision`, `governed_kind`, `is_off_avl_override`, `order_type`, `part_id`, `po_id`, `scored_rule`, `sod`, `supplier_id` |
| audit top-level keys | `contrast`, `hero`, `provisional`, `source` |

Every one of these independently matches an assertion already standing in
`tests/verticals/procurement/test_hero_run.py` — in
`test_live_run_derives_the_hero_governance_moment` and
`test_build_live_contract_hero_live_contrast_offline`. (Cited by test name, not
line number: Step 4 edits this area, so a line anchor would rot by
construction.) That agreement was not arranged — it is the check that the
capture read the object AC-4 means.

### Digests — secondary, and only comparable through the same instrument

Canonical JSON (`sort_keys`, `indent=2`), with identity/clock fields
(`run_id`, `created_at`, `detected_at`, `now`, `timestamp`) stripped:

| Snapshot | sha256 |
|---|---|
| hero | `b66d7ae7e17835c4ca2c84c756603083358a452e3d47c90996803b0d7ecd41f9` |
| audit | `a8f2e33100e422c8a3095f6def9fc8575e36ffe3d9acd6994f545517ed9a6cc3` |

🔴 **A digest is only evidence against a re-run of the same serialisation.** A
Step-4 comparison that rebuilds the capture from scratch may key or order the
JSON differently and produce a different digest for identical behaviour — that is
an instrument difference, not a regression. **Prefer the pinned values above; use
the digests only to confirm a byte-identical re-run.**

**Reproducibility checked, not assumed:** the capture was run twice and both
digests compared equal. A baseline that does not reproduce is not a baseline.

## Two PLAN claims verified independently while capturing

Both were re-measured rather than carried from the fact pack — an inherited
premise is a claim, not context (`CLAUDE.md` §6).

- **`trigger: event` = exactly 2** across `verticals/` — fleet's `intake` and
  procurement's `emergency_sourcing_round`. This is the grounded negative
  PLAN-0113's blast radius rests on.
- **manual + schedule = exactly 11** procedures, matching AC-4's "all 11
  manual/schedule procedures" wording.

## What is NOT yet true

Nothing of the feature exists. Re-measured on this tree:

- `scope_by` in `services/engine/procedures/spec.py` — **0 hits**
- `trigger_context` in `services/engine/procedures/query_step.py` — **0 hits**

Positive control for those two zeros: the same search finds `trigger: event`
twice, so the search is live and the zeros are real absences rather than a broken
grep.

## Next

Step 1 — the `scope_by` / `when_absent` grammar in `spec.py`, consuming nothing
yet. Step 0b (the ADR-016 amendment) is already merged and Accepted (#1269), so
`CLAUDE.md` §8's "all ADRs must be merged before related implementation PR" is
satisfied. 🔴 The field must be **only-when-supplied** (AC-1) or every vertical's
governance config hash moves and in-flight runs fail closed.
