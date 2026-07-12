# PLAN-0066: `threshold_field` per-entity band — build (ADR-016 Amendment 2026-07-11)

**Status:** Done (built + merged 2026-07-12, session 120)
**Owner:** Claude Code
**Created:** 2026-07-12
**Related ADRs:** ADR-016 **Amendment (2026-07-11): per-entity `threshold_field` on evaluate steps (same-row v1)** — Accepted (`docs/adr/0016-governed-procedure-engine.md:1379-1673`); ADR-0019 / ADR-010 IN-3 (determinism invariant); ADR-006 (Rule-of-Three scoping)

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authoring) from a Code-originated
> dispatch; every cited `file:line` was re-verified on disk 2026-07-12.
> Independent reviewers = Code R2 (re-verify citations, commit per ADR-009 D2)
> + Cray at SD ratification. Drafter ≠ committer ≠ ratifier — separation intact.

## Goal

Build the just-Accepted ADR-016 `threshold_field` amendment: an evaluate step
may name a **same-row ontology column** as its per-entity band
(`threshold_field: reorder_point`) instead of one scalar `threshold`. The ADR
**decided** TF-1..TF-4 and ratified OQ-1..OQ-4; this PLAN **builds** — grammar
field + at-most-one validator (`spec.py`), per-row resolution in the
deterministic executor (`evaluate_step.py`), the TF-3 seam-(a) trace-to-reads
load gate with corollaries c1–c4 (`orchestrator.py`), the governance pin
(`draft.py`), and the migration of BOTH procurement `judge_stock` scalar
stand-ins (`verticals/procurement/procedures.yaml:348`, `:641`) — with the
per-part verdict delta proven by RED-verified fixtures, not assumed. No design
choice below reopens the amendment; the build-level choices SD-1..SD-4 were
ratified by Cray 2026-07-12 (SD-1/2/3 = (a) as recommended; SD-4 = (b) — a
deliberate Cray divergence that pulls a third demo seed part IN scope).

**Grammar-change authority.** This PLAN legitimately touches
`spec.py`/`evaluate_step.py`/`orchestrator.py` because the ADR-016 amendment is
**Accepted** (2026-07-11) — the PLAN-0065 L-4 tripwire ("no spec/grammar change
without an ADR-016 amendment", `docs/plans/done/0065-calm-path-reorder-runnability.md:101-105`)
is satisfied, and this build discharges PLAN-0065 SD-3.

## Acceptance Criteria

- [x] **AC-1 (grammar).** `Step.threshold_field: str | None` exists;
  BOTH `threshold` + `threshold_field` set → raises at load (at-most-one /
  NOT-BOTH `@model_validator(mode="after")`); NEITHER set → loads (env-band +
  NL-only judges); `threshold_field` on a non-evaluate kind → raises (band
  family stays evaluate-only, extending the `spec.py:825-831` loop);
  `direction`/`watch_margin` now satisfiable by `threshold` OR
  `threshold_field` (extend `spec.py:832-838`); `ConfigDict(extra="forbid")`
  kept. ⚠️ Explicitly NOT the `JoinSpec._validate_exactly_one_form`
  mandatory-exactly-one shape (`spec.py:265-278`).
- [x] **AC-2 (band-less regression — the R2-catch's point).** Energy `judge`
  (`verticals/energy/procedures.yaml:64-71`) and supply_chain `judge`
  (`verticals/supply_chain/procedures.yaml:65-72`) — band-less env-band
  judges, `threshold` absent today — still load unchanged (explicit factory
  regression tests pass unmodified).
- [x] **AC-3 (executor).** With `threshold_field`, each entity bands vs ITS
  OWN column value; a row whose band column is missing / non-numeric / bool
  fails the step loudly (typed error, `_entity_value` discipline,
  `evaluate_step.py:49-65`); band-less guard fires only when BOTH are absent
  (`:82-87`); summary + audit record `threshold_field` (`:100-114`); no LLM —
  determinism invariant (`:14-19`) intact. **Scalar path byte-for-byte
  unchanged when `threshold_field` is absent** — every pre-existing
  `test_evaluate_step.py` case passes unmodified.
- [x] **AC-4 (load gate, TF-3 seam (a) + c1–c4).** A valid same-row
  `threshold_field` passes `validate_read_bindings`; a non-ontology column
  fails at LOAD (`_declared_properties`, `orchestrator.py:315-317`, precedent
  `:435-439`); **c1** untraceable provenance (traced query step without
  `reads`, or non-query origin) fails CLOSED with typed `ProcedureError`
  (posture of `:301-308`); **c2** multi-read traced step validates vs
  `reads[0]`; **c3** a `project.fields` rename-SOURCE
  (`fields[threshold_field] != threshold_field`) is refused at load; **c4**
  `has_read_bindings` (`:213-224`) fires for a field-only procedure.
- [x] **AC-5 (governance pin).** `"threshold_field"` ∈
  `STEP_GOVERNANCE_FIELDS` (`draft.py:42-59`; plain membership — sits directly
  on `Step` like `threshold`, no lift-strip); the draft-disjointness CI test
  covers it and is green.
- [x] **AC-6 (procurement migration + LIVE demo flip, RED-verified).** BOTH
  `judge_stock` sites (`procedures.yaml:348` event-flavoured + `:641`
  scheduled) migrated to `threshold_field: reorder_point`; facet keeps
  `gate_kind: in_file_band` (OQ-4); the demo seed gains a third "flip" Part
  (ratified SD-4 = b) with `100 < stock_qty ≤ its own reorder_point`, so the
  LIVE run demonstrates the delta — `ok` under the old scalar-100, `breach`
  under per-part banding — and the reorder set DELIBERATELY grows from 2 to
  3 parts (a ratified demo-output change, not drift). Per-part verdict
  fixtures assert the flip and are **RED-verified against the UNEDITED YAML
  first** (PLAN-0065 AC-2 discipline: proven, not assumed).
- [x] **AC-7 (hygiene).** Full suite green WITH Postgres up (one pytest per
  checkout); `ruff check` + `ruff format --check` clean;
  `mypy --strict services/` clean; CI `gate` green on the PR.

## Out of Scope

- ❌ FK-parent-column join case (energy `Asset.rated_current_a`) — future
  amendment (TF-2 (i)).
- ❌ New-column per-class bands (supply_chain `cargo_type` / aquaculture
  `species`) — future amendment (TF-2 (ii)).
- ❌ `watch_margin_field` / `direction_field` — ratified NO in v1 (OQ-2); do
  not "complete the family".
- ❌ Any `stock_qty − reorder_point` derived arithmetic — the Q4
  projection-is-select/rename-only wall stands.
- ❌ New `gate_kind` facet taxonomy — `in_file_band` kept (OQ-4).
- ❌ Re-deciding TF-1..TF-4 / OQ-1..OQ-4 — the amendment is the contract.

## Steps

### Step 1: Plan-first read of the result-producing code

Re-read on the executing branch: `evaluate_step.py` (full),
`spec.py:760-870` (Step fields + `_validate_step`), `orchestrator.py:213-330`
+ `:412-453` (`has_read_bindings`, `validate_read_bindings`,
`_declared_properties`, `_validate_project` precedent), `draft.py:40-74`,
`query_step.py:280-330` (`from_step` threading + reads-vs-from exclusivity),
both YAML sites. **Pass/fail read (pre-committed):** the six ADR change-surface
citations still match on-disk code (drift = stop, reconcile line numbers in
this PLAN before editing).

### Step 2: Grammar — `Step.threshold_field` + NOT-BOTH validator (`spec.py`)

Add `threshold_field: str | None = Field(default=None, ...)` beside
`threshold` (`:778-782`). Extend `_validate_step` (`:813-838`): (a) add
`"threshold_field"` to the evaluate-only field loop (`:826`); (b) NOT-BOTH —
both set → raise (cite the ADR amendment in the message); (c) band invariant —
`direction`/`watch_margin` satisfied by `threshold` OR `threshold_field`.
Neither-set stays valid. Tests in
`tests/services/engine/procedures/test_spec.py`: both-set raises; neither-set
loads; field-only + `direction`/`watch_margin` loads; non-evaluate kind
raises. **Pass/fail read:** new spec tests green AND all four vertical factory
test modules green unmodified (AC-2's energy/supply_chain band-less loads).

### Step 3: Executor — per-row threshold resolution (`evaluate_step.py`)

Guard (`:82-87`) → fire only when `threshold is None and threshold_field is
None` (update message to name both). In the loop (`:88-99`) resolve per row:
scalar `step.threshold`, else the row's `step.threshold_field` column via the
`_entity_value` numeric / bool-reject / fail-loud discipline (`:49-65`; helper
shape = SD-1). Summary (`:100-105`) names the band source; audit (`:107-114`)
adds `"threshold_field": step.threshold_field`. No LLM. Tests in
`test_evaluate_step.py`: two rows with different band columns get different
verdicts from the same reading; missing / non-numeric / `True` band column →
loud typed failure; band-less error mentions both fields. **Pass/fail read:**
new tests green; ALL pre-existing `test_evaluate_step.py` tests pass
byte-unmodified (AC-3 scalar-path freeze).

### Step 4: Load gate — TF-3 seam (a) trace-to-reads + c1–c4 (`orchestrator.py`)

Extend `validate_read_bindings` (`:252-308`), which today `continue`s on
non-QUERY steps (`:284`): for each evaluate step with `threshold_field`, walk
the `from_step` chain (`input.from_step`, default = the immediately preceding
step) back through steps until the QUERY step that declared `reads`; assert
`threshold_field ∈ _declared_properties(meta, reads[0])` (c2; precedent
`:435-439`); require `meta` (fail-loud like `:301-308`). **c1:** traced query
step without `reads`, or chain terminates without a query step → typed
`ProcedureError`, fail CLOSED. **c3:** if the traced step's `project.fields`
maps `threshold_field` to a different name, refuse at load (rename SOURCE
passes declared-props but is absent from rows at run; `query_step.py:649-663`
`_rename` keeps only unmapped columns intact). **c4:** extend
`has_read_bindings` (`:213-224`) to also return True when any evaluate step
declares `threshold_field`. Tests in `test_orchestrator.py` (placement =
SD-3): pass / non-declared column / c1 / c3 / c4 cases per AC-4. **Pass/fail
read:** the five AC-4 cases green; pre-existing `validate_read_bindings` +
`has_read_bindings` tests pass unmodified.

### Step 5: Add the flip seed part (ratified SD-4 = b) + RED-verify the delta vs the UNEDITED YAML

**Fact (verified 2026-07-12):** the shipped synthetic seed has exactly two
parts — `part-spindle-01` (stock 0, reorder_point 1) and `part-filter-02`
(stock 40, reorder_point 100) (`verticals/procurement/data_adapter/synthetic.py:47-48,173-197`)
— and BOTH judge `breach` under scalar-100 AND per-part banding, so the
2-part seed alone cannot show the flip. Per ratified SD-4 (b), add a THIRD
Part to `part_records()` (`synthetic.py:173-197`): a "flip part" with
`100 < stock_qty ≤ its own reorder_point` (e.g. stock 150, reorder_point
200) — `ok` under the old scalar-100, `breach` under per-part banding. Give
it a realistic identity in the existing seed style: a high-turnover
consumable whose HIGH reorder_point a blanket-100 threshold wrongly clears
(the demo's point — a blanket threshold MISSES a genuinely-low high-reorder
part that per-part banding catches). Keep it `on_contract: True` with a
`preferred_supplier` consistent with the calm-path so it flows through
`reorder`. Then write one fixture per migrated site (event-flavoured +
scheduled) asserting per-part verdicts including the flip part, and run
against the **unedited** YAML.
**Pass/fail read (pre-committed):** both fixtures FAIL (flip part judged
`ok`) against `threshold: 100.0` — proving the assertion bites; a green here
= the fixture is wrong, stop and fix it.

### Step 6: Migrate BOTH `judge_stock` sites (`procedures.yaml:348`, `:641`)

Replace `threshold: 100.0` with `threshold_field: reorder_point` at both sites
(keep `direction: below`); keep facet `gate_kind: in_file_band` (OQ-4; the
D2-A3 point-at now covers `threshold_field`); update the step `description` +
facet notes that currently label the scalar a deferred stand-in
(`:342-346`, `:636-639` — cite the ADR-016 2026-07-11 amendment + this PLAN).
`reorder_point` is a declared `Part` property
(`verticals/procurement/ontology/procurement_v0.yaml:191-193`) already carried
to the judge (the `:649-663` rename keeps unmapped columns). **Pass/fail
read:** Step-5 fixtures flip to GREEN; the load gate accepts both procedures;
`grep -c 'threshold: 100.0' verticals/procurement/procedures.yaml` returns 0.

### Step 7: Audit + deliberately update coupled parity tests

PLAN-0064/0065 shipped tests assert on `read_stock`/`judge_stock` output
(PLAN-0065 hit exactly this with
`test_read_stock_routes_to_the_shipped_executor_not_the_seed`). ⚠️ Ratified
SD-4 (b) makes this surface LARGER than the fixture-only (a) path would have
been: the third seed part changes the reorder-set cardinality (2 → 3)
post-migration, so any test asserting "2 parts", reorder-set membership,
headline counts, or demo-run part counts (notably
`test_scheduled_procurement_demo.py`, `test_procedure_headline.py`, the
`test_calm_path_*` modules) must be audited + updated deliberately —
disclosed in the PR body. Audit list (files matching
`judge_stock|EvaluateStepExecutor|validate_read_bindings|STEP_GOVERNANCE_FIELDS`,
grep 2026-07-12, 23 files / 88 hits — the procurement-coupled subset):
`tests/verticals/procurement/test_calm_path_production_runnability.py`,
`tests/verticals/procurement/test_intake_shadow_parity.py`,
`tests/services/engine/test_procurement_vertical.py`,
`tests/services/db/test_scheduled_procurement_demo.py`,
`tests/services/db/test_procedure_headline.py`,
`tests/services/db/test_procurement_sod_gate.py`,
`tests/api/test_calm_path_run_endpoint.py`,
`tests/services/engine/procedures/test_seed_migration_parity.py`. Any test
asserting the literal scalar band (e.g. audit `"threshold": 100.0`) is updated
**deliberately and disclosed in the PR body** — never silently loosened.
**Pass/fail read:** every audited module green; each modified assertion is
listed in the PR body with its reason.

### Step 8: Full-suite hygiene + PR

Start `vero-postgres` (Docker Desktop, Windows engine); run the FULL suite via
WSL (one pytest per checkout), `ruff check .`, `ruff format --check .`,
`mypy --strict services/`. Branch `feat/plan0066-threshold-field` → PR (body
via `--body-file`) citing ADR-016 Amendment 2026-07-11 + this PLAN; CI `gate`
green; PR granularity = SD-2. After merge + Cray closeout:
`git mv docs/plans/0066-*.md docs/plans/done/`. **Pass/fail read:** suite
green with DB up (~123 skips = DB down, restart and rerun); all three linters
clean; CI `gate` green on the PR merge candidate.

## Surfaced decisions (RATIFIED — Cray, typed 2026-07-12)

All four SDs were adjudicated by Cray on 2026-07-12: SD-1/2/3 = (a) as
recommended; SD-4 = (b), a deliberate Cray divergence from the drafter's
recommendation (typed pick — recorded per attribution honesty).

- **SD-1 — per-row band helper shape. RATIFIED = (a).** (a) Generalize `_entity_value` to
  `_entity_number(step_id, entity, field, purpose)` used by both reading and
  band reads (one discipline, zero drift — **recommended**); (b) a separate
  sibling `_entity_threshold` duplicating the checks. Cray's call: (a) touches
  the shipped reading path's error-message text (cosmetic but user-visible in
  D4 divert traces).
- **SD-2 — PR granularity. RATIFIED = (a).** (a) ONE PR (engine + migration + fixtures;
  RED-verify ordering is within-branch commits — **recommended**: splitting
  would merge a grammar with zero in-repo consumers); (b) two PRs (engine
  first, YAML migration second, PLAN-0062-style). Cray's call: merge-boundary
  / review-load preference.
- **SD-3 — load-gate test placement. RATIFIED = (a).** (a) Extend
  `test_orchestrator.py` (**recommended** — `validate_read_bindings` tests
  live there); (b) a new `test_threshold_field_gate.py` (the
  `test_join_grammar.py` precedent) if the c1–c4 matrix grows large. Cray's
  call: test-suite topology convention.
- **SD-4 — delta-fixture data shape + demo visibility. RATIFIED = (b) —
  Cray DIVERGED from the drafter's recommended (a).** Add a third synthetic
  seed part so the LIVE demo shows the per-part flip (drafter had recommended
  test-local fixtures only, demo seed untouched). A deliberate, typed Cray
  call and a ratified demo-output change — the reorder set grows 2 → 3
  parts — woven into AC-6, Step 5, and Step 7; the former "demo seed
  redesign" Out-of-Scope item is removed accordingly.

## Verification

AC-1..AC-5 by the new + frozen engine tests (Steps 2–4); AC-6 by the
RED-then-GREEN fixture sequence (Steps 5–6 — the flip is proven against the
unedited YAML first); AC-7 by the Step-8 full-suite + linter + CI `gate` run
on the PR. Evidence = fresh pytest/linter output on the branch, pass/fail
reads pre-committed per step above (Lesson #0026 discipline).

## Close-out (built + merged 2026-07-12, session 120)

Built on `feat/plan0066-threshold-field` in three commits — engine grammar +
executor `40ce172` → load gate `57e5e08` → procurement migration + flip seed
`3047386` — merged via PR #705 (merge commit `3682d79`, now `main`).
Governance lineage: PR #703 (ADR-016 amendment Accepted) → PR #704 (this PLAN
Ready) → PR #705 (build). All seven ACs met, verified on-disk this session:

- **AC-1** `Step.threshold_field` + at-most-one (NOT-BOTH) validator +
  evaluate-only, with the band-family checks extracted to
  `_validate_band_family` (C901 complexity); `test_spec.py` grammar tests
  green.
- **AC-2** energy + supply_chain band-less env-band `judge`s load unchanged
  (the R2-catch's whole point); full suite + env_band tests green.
- **AC-3** per-entity band vs each row's OWN column; scalar path
  byte-for-byte unchanged; loud non-numeric band; determinism intact
  (`test_evaluate_step.py` green).
- **AC-4** TF-3 seam (a) + c1–c4: 7 gate tests green in
  `test_orchestrator.py` (accept, non-ontology column, c1 no-reads, c1
  entry-point, c3 rename-source, c4 `has_read_bindings`, meta-required).
- **AC-5** `threshold_field` ∈ `STEP_GOVERNANCE_FIELDS`; draft-disjointness
  CI green.
- **AC-6** BOTH `judge_stock` sites migrated to
  `threshold_field: reorder_point`; SD-4 (b) flip seed part `part-vbelt-03`
  (stock 150 / reorder_point 200) RED-verified `ok` against the unedited
  YAML, then GREEN `breach` post-migration; reorder set deliberately 2 → 3.
- **AC-7** full suite **2536 passed / 7 skipped** WITH Postgres up; `ruff
  check` + `ruff format --check` + `mypy --strict services/` clean; CI
  `gate` green on #705.

### Honest completion record

1. **Build-discovered coupling NOT in the ADR change surface** (the standout
   note): `draft.py::derive_governance_todo` derived the `in_file_band` band
   obligation as a hardcoded `threshold`, so `validate_governance_complete`
   flagged `threshold` as an unfilled governance stub on a `threshold_field`
   judge and REFUSED to run the migrated procedure. Fixed to derive the band
   obligation as `threshold_field` (when authored) or `threshold`. Caught by
   the AC-2 in-memory runnability test — not assumed. (Analogous to
   PLAN-0065's shadow-parity build-discovered coupling.)
2. **Three draft≠review≠verify findings, one per role:** (i) Code R2 caught
   the ADR's TF-1 "exactly-one" → "at-most-one" defect (strict exactly-one
   would have broken the energy/supply_chain env-band judges at load);
   (ii) the plan-drafter caught the seed-parity fact (the shipped 2 parts
   BOTH breach under either banding, so the flip needed a third seed part);
   (iii) the build caught the `draft.py` governance coupling above.
3. **Coupled tests updated deliberately, disclosed in the #705 body:**
   scheduled-demo verdict count 2 → 3; the event-based calm-path test feeds
   `reorder_point` and its `_Evaluate` mock routes `threshold_field` to the
   band executor; env_band + facet-points-at tests accept the widened band.
4. **Deferred to future ADR-016 amendments (TF-2):** FK-parent-column join
   case (energy `Asset.rated_current_a`); not-yet-present-column cases
   (supply_chain `cargo_type` / aquaculture `species`);
   `watch_margin_field` / `direction_field` (OQ-2 = no).

## References

- `docs/adr/0016-governed-procedure-engine.md:1379-1673` — the Amendment
  (2026-07-11), Accepted: TF-1..TF-4, OQ-1..OQ-4 ratified, change surface.
- `docs/plans/done/0065-calm-path-reorder-runnability.md` — L-4 tripwire
  (`:101-105`), SD-3 deferral, AC-2 RED-verify discipline.
- `services/engine/procedures/spec.py:265-278,760-838` ·
  `evaluate_step.py:14-19,49-65,82-115` ·
  `orchestrator.py:213-224,252-317,435-439` · `draft.py:42-59` ·
  `query_step.py:293-317,649-663`.
- `verticals/procurement/procedures.yaml:330-356,610-648` ·
  `ontology/procurement_v0.yaml:191-193` ·
  `data_adapter/synthetic.py:47-50,173-197`.
