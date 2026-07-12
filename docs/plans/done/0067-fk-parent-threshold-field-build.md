# PLAN-0067: FK-parent `threshold_field` — supply_chain cold-chain build (ADR-016 Amendment 2026-07-12)

**Status:** Done (built + merged 2026-07-12, session 121)
**Owner:** Claude Code
**Created:** 2026-07-12
**Related ADRs:** ADR-016 **Amendment (2026-07-12): FK-parent-column
`threshold_field` — the join extension (per-entity bands, v2)** — **Accepted**,
merged to `main` = `1c296a4` via PR #707
(`docs/adr/0016-governed-procedure-engine.md:1675-2109`; FKP-1..FKP-4, SD-1..SD-5
ratified, SD-4 = supply_chain-only build scope); the Q4 join amendment
(2026-07-09, same file `:1010-1377`); ADR-0019 / ADR-010 IN-3 (determinism);
ADR-006 (Rule-of-Three); ADR-008 (ontology grammar untouched by a plain property)

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authoring) from a Code-originated
> dispatch; every cited `file:line` was re-verified on disk 2026-07-12 against
> the post-#707 tree. Independent reviewers = Code R2 (re-verify citations,
> commit per ADR-009 D2) + Cray at SD ratification. Drafter ≠ committer ≠
> ratifier — separation intact. **Drafter finding:** one engine coupling the
> amendment's change surface did NOT list is added below (the
> `env_band_step.py:74` delegate guard — Step 3) — surfaced, not silently
> absorbed.

## Goal

Build the Accepted FK-parent `threshold_field` amendment for its ratified
scope — **supply_chain only**: widen the load gate so a `threshold_field` may
name a column on a JOINED FK-parent of the traced query step (FKP-2 g1–g4,
`orchestrator.py`), add the `Shipment.temp_ceiling: float` band property +
per-cargo-type seeds (FKP-4 / ratified SD-2), migrate `read_temps` to the
declared multi-read join (**the first shipped `join:` consumer**, Q4
SD-C-parity-guarded) and the `judge` from `env_band` to
`threshold_field: temp_ceiling` (ratified SD-5) — with the demo-visible
per-cargo verdict delta **RED-verified against the unedited YAML first**
(PLAN-0066 AC-6 discipline). Zero new grammar fields (FKP-1); zero
`evaluate_step.py` change (FKP-3 — the merged row already carries the band);
the stale Phase-C docstring is corrected. One draft-discovered engine
coupling rides along: the `EnvBandEvaluateExecutor` delegate guard must
recognize `threshold_field` as an authored band (Step 3), else the migrated
judge's authored `direction` is silently clobbered by the env direction and
the audit falsely records `band_source: "env"`.

**Grammar-change authority.** This PLAN legitimately touches
`orchestrator.py` / `spec.py` / `env_band_step.py` because the ADR-016
FK-parent amendment is **Accepted** (2026-07-12, PR #707) — the L-4 tripwire
("no spec/grammar change without an ADR-016 amendment") is satisfied; no step
below reopens FKP-1..FKP-4 or the amendment's SD-1..SD-5.

## Acceptance Criteria

- [x] **AC-1 (load gate, FKP-2 g1–g4).** `_validate_threshold_field_bindings`
  (`orchestrator.py:350-386`) validates a `threshold_field` against
  **`declared_properties(reads[0]) ∪ ⋃ declared_properties(join[].with_read)`**
  of the traced query step (today: `reads[0]` only, `:374-375`). **g1**: a
  band column in NO traced read's declared properties refuses with a typed
  `ProcedureError`; the c1 fail-closed refusals (meta-required, no-reads,
  untraceable provenance) carry unmodified. **g2**: composes with the
  collision gate by ordering (`:311-312` — `_validate_join_project` +
  `_validate_join_collisions` `:461-487` run first); no new ambiguity rule.
  **g3**: the c3 rename-away refusal carries (a `threshold_field` named in
  the traced step's `project.fields` keys refuses). **g4**: runtime-only
  collisions keep Q4's counted-not-refused posture (`_merge`,
  `query_step.py:583-603`) — no stricter fork for band columns. **All seven
  PLAN-0066 gate tests + the join-grammar gate tests pass unmodified**
  (same-row behaviour byte-identical). C901: extract a helper if the widened
  function trips complexity.
- [x] **AC-2 (env-band delegate guard — the draft-discovered coupling).**
  `EnvBandEvaluateExecutor.execute` delegates UNTOUCHED when the step authors
  **either** band: the guard at `env_band_step.py:74` becomes
  `threshold is not None or threshold_field is not None`. Proof tests: a
  `threshold_field` step passes through with its authored `direction` intact
  (no `model_copy` clobber via `:76-81`) and NO `band_source: "env"` audit
  stamp; the band-less env path is byte-identical (all pre-existing
  `test_env_band_evaluate.py` cases pass unmodified). This aligns the code
  with the module's own contract ("a step that authors one is an `in_file`
  band and delegates through unchanged", `:17-19`) — a docstring-vs-code gap
  that predates this PLAN.
- [x] **AC-3 (ontology property + generated artifacts + DB migration).**
  `Shipment.temp_ceiling` (`type: float`, described as the cargo-type
  cold-chain ceiling) added to `supply_chain_v0.yaml` (Shipment properties,
  `:32-63`); artifacts regenerated via the **console script `uv run
  vero-lite …`** (NOT `python -m` — a silent no-op), verified by the "OK:"
  output + `generated/models.py` / `orm.py` mtime; a new Alembic revision
  (next = `0012_…`; precedent `alembic/versions/0009_asset_rated_current_a.py`)
  adds the column; schema-parity + supply_chain adapter/ontology-meta tests
  green.
- [x] **AC-4 (YAML migration — the first shipped `join:` consumer).**
  `read_temps` → `reads: [OperationalEvent, Shipment]` +
  `join: [{with: Shipment, link: event_concerns_shipment}]`
  (`supply_chain_v0.yaml:236-240` — parseable FK, equal-named key pair
  exempt) + kept `latest_per`/`order_by` + `project.fields:
  {facility_id: shipment_facility_id}` (the ONE declared collision:
  `Shipment.facility_id` `:53-56` vs `OperationalEvent.facility_id`
  `:116-118`); `judge` → `threshold_field: temp_ceiling` +
  `direction: above`, facet `decision_condition` → `{gate_kind: in_file_band,
  band_source: in_file}` (ratified SD-5), facet prose re-synced (D2-A2).
  Both procedures load through the full gate
  (`validate_read_bindings_for_vertical`).
- [x] **AC-5 (Q4 SD-C parity).** On the same synthetic fixtures, the migrated
  join run of `read_temps` reproduces the prior projection run: the SAME
  latest event per shipment (`event_id`, `measured_value`, `occurred_at`
  equal per `shipment_id`), the SAME row count, every base
  `OperationalEvent` column preserved under its own name; joined `Shipment`
  columns are a strict ADDITION (superset assertion, `facility_id` base-wins
  + `shipment_facility_id` carries the joined side).
- [x] **AC-6 (per-cargo flip, RED-verified).** A fixture asserts the
  demo-visible delta — the shipment whose reading the blanket env-band 8 °C
  judges `ok` but its OWN `temp_ceiling` judges `breach` (shape per SD-2/3)
  — and is run **against the UNEDITED YAML first**: it must FAIL there
  (proving the assertion bites), then flip GREEN after Step 6. A green
  against the unedited YAML = the fixture is wrong; stop and fix.
- [x] **AC-7 (in-memory `run_procedure`, not spec-load-only).** An in-memory
  end-to-end run of the migrated procedure (synthetic adapter + real
  ontology meta + the registered factory executors) passes
  `validate_governance_complete` (proving `derive_governance_todo`'s
  band-awareness `draft.py:285-288` holds for this consumer — PLAN-0066's
  build-discovered coupling, proven not assumed), executes the join read +
  per-row judge, and suspends `waiting_human` at gated `hold_breaches` with
  the expected breach set.
- [x] **AC-8 (regression pins).** Procurement's shipped same-row consumer
  byte-for-byte (its YAML, fixtures, and the PLAN-0066 flip tests pass
  unmodified); energy's band-less `env_band` judge
  (`verticals/energy/procedures.yaml:64-75`) still loads + runs; the scalar
  `threshold` path unchanged; determinism invariant
  (`evaluate_step.py:14-19`) untouched — **zero `evaluate_step.py` /
  `draft.py` / `spec.py`-schema edits** (FKP-3; `spec.py` gets ONLY the
  `:796-801` description-string reword); the stale Phase-C docstring
  (`orchestrator.py:281-283`) corrected to the honest post-#666 frame.
- [x] **AC-9 (hygiene).** Full suite green WITH Postgres up (one pytest per
  checkout); `ruff check` + `ruff format --check` clean; `mypy --strict
  services/` clean; CI `gate` green on the PR.

## Out of Scope

- ❌ **energy migration** (`threshold_field: rated_current_a`) — a labelled
  follow-on per ratified amendment SD-4: NOT free (partially-populated band
  column + FKP-3 fail-loud needs a narrowing `where` or seed completion;
  `site_id` declared-collision rename).
- ❌ **aquaculture per-species floors** — labelled follow-on (needs a new
  numeric `Pond` property + `direction: below` floor semantics).
- ❌ Any derived arithmetic — the Q4 select/rename/equi-join-only wall
  stands; the band is a STORED column.
- ❌ The per-class `cargo_type → ceiling` LOOKUP grammar — amendment SD-2 (b)
  = OUT.
- ❌ `watch_margin_field` / `direction_field` — still OQ-2 = no.
- ❌ The reactive recommender's env threshold — `OCT_RECOMMEND_THRESHOLD`
  stays for the recommender path and energy's judge; only the supply_chain
  procedure judge migrates.
- ❌ Re-deciding FKP-1..FKP-4 or the amendment's SD-1..SD-5 — the Accepted
  amendment is the contract.
- ❌ NL-query aggregate convergence (Q4 SD-B's named future question).

## Steps

### Step 1: Plan-first read of the result-producing code

Re-read on the executing branch: `orchestrator.py:281-320,350-386,403-530`
(the stale docstring, gate ordering, threshold gate, join/collision/project
validators), `env_band_step.py` (full — the guard + rebind),
`query_step.py:405-520` (`_execute_join` pipeline),
`spec.py:778-846` (band fields + `_validate_band_family`),
`verticals/supply_chain/{ontology/supply_chain_v0.yaml,procedures.yaml,
data_adapter/synthetic.py,procedures_factory.py}`, and
`alembic/versions/0009_asset_rated_current_a.py` (the property-addition
precedent). **Pass/fail read (pre-committed):** the change-surface citations
in this PLAN still match on-disk code (drift = stop, reconcile line numbers
here before editing).

### Step 2: Load gate — widen the threshold_field domain to joined parents (`orchestrator.py`)

Extend `_validate_threshold_field_bindings` (`:350-386`): after resolving
`base = source.input.reads[0]` (`:374`), when the traced step declares
`join`, the valid domain becomes base ∪ each `join[].with_read`'s
`_declared_properties` (g1); keep every c1 refusal and the c3
`project.fields` rename-away refusal (g3) byte-equivalent for the
non-joined path; add NOTHING for g2/g4 (they hold by ordering `:311-312`
and by Q4's `_merge` posture — assert them in tests, not code). Fix the
stale docstring (`:281-283`): execution-bound is ✔ since PLAN-0061 #666
(`docs/plans/done/0061-join-projection-grammar-build.md:3`); the honest
residual ✖ belongs to unmigrated seed-backed procedures (`0061:450-452`).
Extract a helper if C901 trips (PLAN-0066 `_validate_band_family`
precedent). Tests (placement = SD-5): joined-parent column accepts;
non-declared column refuses; a parent column named while NO join is
declared refuses (same-row rule unchanged); c1/c3 cases pass unmodified;
a collision-gate refusal still fires BEFORE the threshold gate on an
un-renamed declared collision. **Pass/fail read:** new cases green; the
seven PLAN-0066 gate tests + `test_join_grammar.py` pass unmodified.

### Step 3: env-band delegate guard + `spec.py` description reword

`env_band_step.py:74`: `if step.threshold is not None or
step.threshold_field is not None: return await self.base.execute(...)` —
plus a docstring line citing the FK-parent amendment. Without this, the
`:76-81` rebind would stamp env `threshold` + `direction` onto the migrated
judge: the per-row band still wins in the executor
(`evaluate_step.py:103-109` checks `threshold_field` first) but the authored
`direction: above` is silently REPLACED by `settings.oct_recommend_direction`
and the audit falsely records `band_source: "env"` — a governance-honesty
defect, not just hygiene. Reword the `spec.py:796-801` `threshold_field`
description ("a same-row ontology column" → the extended same-row ∪
joined-parent scope, citing the 2026-07-12 amendment) — a docstring edit,
no schema change. Tests in `test_env_band_evaluate.py`: a `threshold_field`
step delegates untouched (authored direction preserved; no env audit keys);
band-less env path unchanged. **Pass/fail read:** new cases green; ALL
pre-existing `test_env_band_evaluate.py` + energy factory tests pass
unmodified.

### Step 4: `Shipment.temp_ceiling` — ontology + regen + Alembic + seed ceilings

Add `temp_ceiling: {type: float, description: cargo-type cold-chain ceiling
(°C) …}` to Shipment (`supply_chain_v0.yaml:32-63`). Run the generator via
the console script (`uv run vero-lite …`) and verify "OK:" + fresh mtimes on
`verticals/supply_chain/generated/{models.py,orm.py}`. Add Alembic revision
`0012_shipment_temp_ceiling` (nullable float on the shipment table —
`0009_asset_rated_current_a.py` shape). Seed ALL FOUR shipments
(`synthetic.py:50-89`) with SD-3 ceilings — every shipment that reaches the
judge must carry a numeric value (FKP-3 fail-loud): pharma-01 `8.0`,
produce-01 `12.0`, frozen-01 `-15.0`, biologic-01 `6.0` (SD-3; produce/
biologic are demo-inert today — no readings — but the substrate is uniform).
**Pass/fail read:** generator "OK:" + mtimes; schema-parity, adapter, and
ontology-meta tests green; a grep confirms 4/4 shipment records carry
`temp_ceiling`.

### Step 5: Flip seed event (SD-2) + RED-verify vs the UNEDITED YAML

Per SD-2 (recommended (b)): add ONE warming reading to `frozen-01` —
`event-reading-04`, `measured_value: -11.8`, `occurred_at` 08:12 (2 min
after the `event-alarm-01` door-open at 08:08, `synthetic.py:121-129` — the
alarm finally pays off narratively: door open → cargo warming), making it
frozen-01's latest reading and the timeline's new final beat (real-time
anchoring note `synthetic.py:8-16` updated). The flip: `-11.8` is `ok`
under the blanket env 8 °C (a thawing frozen shipment MISSED) but `breach`
under its own `-15.0` ceiling (CAUGHT — the demo's point). Write the
per-cargo verdict fixture (pharma-01 `breach` at 14.6 vs 8.0 — continuity;
frozen-01 `breach` at −11.8 vs −15.0 — the flip) and run it against the
**unedited** `procedures.yaml`. **Pass/fail read (pre-committed):** the
fixture FAILS against the env-band YAML (frozen-01 judged `ok`) — RED
proven; a green here = a wrong fixture, stop and fix it.

### Step 6: Migrate `verticals/supply_chain/procedures.yaml` + the parity test

`read_temps` (`:43-64`): `reads: [OperationalEvent, Shipment]`; `join:
[{with: Shipment, link: event_concerns_shipment}]`; keep `where:
{event_type: reading}` + `latest_per`/`order_by`; add `project.fields:
{facility_id: shipment_facility_id}` (the declared collision — the join-key
`shipment_id` pair is exempt, `orchestrator.py:471-476`); re-sync the facet
prose. `judge` (`:65-76`): add `threshold_field: temp_ceiling` +
`direction: above`; facet → `{gate_kind: in_file_band, band_source:
in_file}`; description/prose drop the `OCT_RECOMMEND_*` references. Add the
AC-5 parity test (suggested home: `test_seed_migration_parity.py`, the Q4
SD-C module): pre-migration projection output captured as the fixture
baseline; the join run must match per AC-5's criterion. **Pass/fail read:**
Step-5 fixture flips GREEN; parity test green; both supply_chain procedures
load through `validate_read_bindings_for_vertical`; `grep -c 'env_band'
verticals/supply_chain/procedures.yaml` returns 0.

### Step 7: In-memory `run_procedure` + coupled-test audit

Add/extend the in-memory end-to-end run per AC-7 (governance-complete →
join read → per-row judge → `waiting_human` at `hold_breaches`, breach set =
{pharma-01, frozen-01} under SD-2 (b)). Then audit the coupled modules —
updates are **deliberate and disclosed in the PR body**, never silent
(PLAN-0066 Step-7 discipline): `tests/verticals/supply_chain/
test_supply_chain_procedure_factory.py` (`:73` asserts the judge executor is
`EnvBandEvaluateExecutor` — outcome depends on SD-4),
`test_seed_migration_parity.py`, `test_example_procedures.py`,
`test_prose_lint.py` (facet prose sync), `tests/api/
test_supply_chain_vertical.py`, `tests/api/test_procedures_endpoint.py`,
`tests/benchmark/test_procedure_comparison_verticals.py` +
`tests/benchmark/test_loader.py`, `test_env_band_evaluate.py`, and any
timeline-anchor assertions touched by the Step-5 final-beat change.
**Pass/fail read:** every audited module green; each modified assertion
listed in the PR body with its reason.

### Step 8: Two-PR build boundary + full-suite hygiene (ratified SD-1 = b)

Per ratified SD-1 (b) — a deliberate Cray divergence isolating the rollback
of the DB migration + the FIRST production `join:` consumer — the build
lands as TWO PRs:

- **PR1 — engine** (Steps 2–3), branch `feat/plan0067-fkp-engine`: the
  FKP-2 g1–g4 gate widening + the stale-docstring fix (`orchestrator.py`),
  the env_band delegate guard (`env_band_step.py`), the `spec.py`
  description reword, plus their new/frozen engine tests. Satisfies **AC-1,
  AC-2**, and the engine half of AC-8. Self-contained: the gate only WIDENS
  what it accepts (a joined-parent column) — zero shipped procedure declares
  such a `threshold_field` until PR2, so existing procedures/tests are
  byte-unaffected.
- **PR2 — vertical** (Steps 4–7), branch `feat/plan0067-fkp-supplychain`,
  **gated on PR1 merged** (the gate must accept the joined-parent column
  before the migrated YAML loads): `Shipment.temp_ceiling` + regen + Alembic
  `0012_…` + per-cargo seeds + the frozen-01 flip event + the `read_temps`
  join migration + judge migration + the Q4 SD-C parity test + the
  RED-verify flip + the in-memory `run_procedure` + the coupled-test audit.
  Satisfies **AC-3..AC-7** + the vertical half of AC-8, AC-9. The RED-verify
  (Step 5) lands within PR2 before Step 6's migration commit.

For EACH PR: start `vero-postgres` (Docker Desktop, Windows engine); run the
FULL suite via WSL (one pytest per checkout), `ruff check .`, `ruff format
--check .`, `mypy --strict services/`; PR body via `--body-file`, citing the
ADR-016 2026-07-12 amendment + this PLAN; CI `gate` green. After BOTH merge
+ Cray closeout: `git mv docs/plans/0067-*.md docs/plans/done/`.
**Pass/fail read (per PR):** suite green with DB up (~123 skips = DB down —
restart and rerun); linters clean; CI `gate` green on the merge candidate.

## Surfaced decisions (RATIFIED — Cray, typed 2026-07-12)

All five SDs were adjudicated by Cray on 2026-07-12 (typed, via
AskUserQuestion): SD-2 = (b), SD-4 = (a), SD-5 = (a) as recommended;
SD-3 = the rendered ceilings; SD-1 = (b), a deliberate Cray divergence from
the drafter's recommendation (typed pick — recorded per attribution
honesty).

- **SD-1 — PR granularity. RATIFIED = (b) TWO PRs — Cray DIVERGED from the
  drafter's recommended (a).** The drafter had recommended (a) ONE PR
  (splitting would merge a gate extension with zero in-repo consumers, the
  PLAN-0066 SD-2 = (a) precedent). Cray's typed call = (b): engine first
  (`feat/plan0067-fkp-engine`, Steps 2–3), vertical second
  (`feat/plan0067-fkp-supplychain`, Steps 4–7, gated on PR1 merged) —
  rationale: this build carries a DB migration + generated artifacts + the
  FIRST production `join:` consumer, so (b) isolates the rollback of the DB
  migration + that first `join:` consumer. Woven into Step 8.
- **SD-2 — flip design + demo visibility. RATIFIED = (b), as recommended.**
  The seed warming reading on frozen-01 (Step 5, mirroring Cray's PLAN-0066
  SD-4 typed divergence toward demo-visible): the LIVE demo shows the
  blanket ceiling missing a thawing frozen shipment that per-cargo banding
  catches, and the door-open alarm gets its narrative payoff. ⚠️ A ratified
  demo-output change: the timeline's final beat moves (08:10 pharma → 08:12
  frozen) and the `hold_breaches` set grows 1 → 2. (Alternative (a) —
  test-local fixture only, seed untouched — declined.)
- **SD-3 — concrete ceiling values. RATIFIED = the rendered ceilings.**
  pharma `8.0` (equals today's env band — pharma verdict continuity),
  produce `12.0`, frozen `-15.0`, biologic `6.0` (tighter than pharma —
  plausible cold-chain conventions).
- **SD-4 — factory EVALUATE wiring. RATIFIED = (a), as recommended.** Keep
  `EnvBandEvaluateExecutor(base=…)` (`procedures_factory.py:72`) — with the
  Step-3 guard it delegates through for the migrated judge; symmetric with
  energy, minimal churn. (Alternative (b) — register the bare
  `EvaluateStepExecutor` — declined: touches the factory + its `:73`
  isinstance test, and desyncs the two factories' shapes.)
- **SD-5 — gate-test placement. RATIFIED = (a), as recommended.** Extend
  `test_orchestrator.py` — the seven PLAN-0066 threshold_field gate tests
  live there; PLAN-0066 SD-3 = (a) precedent. ((b) — `test_join_grammar.py`
  or a new module — remains available if the joined-domain matrix grows
  large.)

## Verification

AC-1/AC-2 by the new + frozen engine tests (Steps 2–3); AC-3 by the
generator "OK:" + mtime + schema-parity/adapter tests (Step 4); AC-5/AC-6 by
the parity test + the RED-then-GREEN fixture sequence (Steps 5–6 — the flip
is proven against the unedited YAML first); AC-7 by the in-memory
`run_procedure` (Step 7); AC-8 by the unmodified procurement/energy/scalar
test pins across Steps 2–7; AC-9 by the Step-8 full-suite + linter + CI
`gate` run. Evidence = fresh pytest/linter output on the branch; pass/fail
reads pre-committed per step (Lesson #0026 discipline). No live host-state
run is required — the offline oracle is the gate (CLAUDE.md §8).

## Close-out (built + merged 2026-07-12, session 121)

Built as TWO PRs per ratified SD-1 (b): **PR1 engine**
`feat/plan0067-fkp-engine` → PR #709 (merge `a24971c`) — the FKP-2 g1–g4
gate widening + the env_band delegate guard + the stale-docstring fix +
the `spec.py` description reword; **PR2 vertical**
`feat/plan0067-fkp-supplychain` → PR #710 (merge `0b6be2a`) —
`Shipment.temp_ceiling` + per-cargo seeds + the frozen-01 flip event + the
`read_temps` join migration + the judge migration. Governance lineage:
amendment PR #707 (Accepted) → PLAN-0067 Ready PR #708 → PR1 #709 → PR2
#710; final `main` = `670117c`. All nine ACs met, AC-3 as corrected (see
honest record #1):

- **AC-1** `_validate_threshold_field_bindings` widened its domain from
  `reads[0]` to base ∪ each declared joined FK-parent; 5 FKP-2 gate tests
  green in `test_orchestrator.py` (accept joined-parent, accept base under
  join, refuse parent-without-join, refuse undeclared,
  collision-refused-before-threshold); same-row path byte-identical.
- **AC-2** the `env_band_step.py:74` guard now delegates on `threshold` OR
  `threshold_field` — a `threshold_field` judge passes through untouched
  (authored `direction` preserved, no false `band_source: "env"` audit);
  proof test in `test_env_band_evaluate.py`.
- **AC-3** met **AS CORRECTED** — `Shipment.temp_ceiling: float` added +
  artifacts regenerated (the gitignored `generated/`); **NO Alembic
  migration** — build-discovered: supply_chain has no committed ORM / DB
  table, so there is no `shipment` table to migrate (honest record #1;
  Cray ratified in-memory Option A). The AC-3 "Alembic `0012_…`" clause is
  **superseded by new info**, not an error in intent.
- **AC-4** `read_temps` → `reads: [OperationalEvent, Shipment]` +
  `join: event_concerns_shipment` + kept `latest_per` + the `facility_id`
  collision rename; `judge` → `threshold_field: temp_ceiling` +
  `direction: above`, facet `in_file_band` (SD-5); both procedures load
  through the gate — the first shipped `join:` consumer.
- **AC-5** the run test asserts the join preserves the base
  `measured_value` AND adds `temp_ceiling` (superset); the
  projection-parity test in `test_seed_migration_parity.py` still
  validates the latest-per-group half the join preserves.
- **AC-6** the frozen shipment warms to −11.8 °C: `ok` under the blanket
  8 °C ceiling, `breach` under its own −15 °C ceiling — RED-verified
  against the unedited env_band YAML FIRST (it FAILED: frozen judged
  `ok`), GREEN after migration; hold set deliberately 1 → 2 (SD-2 b).
- **AC-7** in-memory end-to-end run
  (`tests/verticals/supply_chain/test_cold_chain_per_cargo_band.py`):
  governance-complete → join read → per-row judge → suspends
  `waiting_human` at gated `hold_breaches`, breach set
  {pharma-01, frozen-01}.
- **AC-8** procurement same-row consumer byte-identical; energy band-less
  env_band judge still loads + runs; scalar path unchanged; zero
  `evaluate_step.py` / `draft.py` change (FKP-3).
- **AC-9** full suite **2544 passed / 7 skipped** WITH Postgres up;
  `ruff check` + `ruff format --check` + `mypy --strict services/` clean;
  CI `gate` green on #709 + #710.

### Honest completion record

1. **Build-discovered AC-3 correction (the standout):** the PLAN assumed
   an Alembic migration (`0012_shipment_temp_ceiling`), modeled on
   energy's `rated_current_a` (`0009`). Fresh on-disk evidence corrected
   it: `services/db/models.py` + `test_schema_parity.py` are energy-only,
   `_ORM_COMMITTED_DEST = {"energy": ...}`, and supply_chain's Shipment is
   served in-memory by the synthetic adapter (its `generated/orm.py` is
   gitignored) — there is no `shipment` table, so `temp_ceiling`'s ripple
   is the ontology YAML + the gitignored regen only. Cray ratified
   skipping the migration (in-memory Option A) after an ELI-30 review; a
   committed supply_chain ORM is the deferred per-vertical ORM-layout
   decision, out of scope. **Classified: superseded by new info** — the
   intent (parity with energy) was right; the substrate assumption was
   wrong.
2. **Three draft≠review≠verify catches, one per role:** (i) Code R2
   caught the amendment dispatch's premise that the join executor was
   "deferred Phase C" (a stale docstring — it had actually shipped:
   PLAN-0061 #666, `_execute_join`); (ii) the plan-drafter caught the
   `env_band_step.py:74` delegate-guard coupling the amendment's change
   surface missed (a migrated judge would clobber `direction` + falsely
   audit `band_source: "env"`); (iii) the build caught AC-3's no-table
   reality (#1).
3. **Coupled tests updated deliberately, disclosed in the #710 body:**
   the factory full-run breach set 1 → 2 + the judge audit
   `env → in_file` (`test_supply_chain_procedure_factory.py`);
   frozen-01's latest reading `event-reading-02 → event-reading-04`
   (`test_seed_migration_parity.py`); the supply_chain judge moved from
   the env_band list to `_IN_FILE_BAND_JUDGES` (`test_spec.py`).
4. **Deferred to future ADR-016 amendments (TF-2 residue):** aquaculture
   per-species floors (needs a new `Pond` numeric property +
   `direction: below` floor semantics); energy `rated_current_a`
   migration (partially-populated band column → FKP-3 fail-loud needs a
   narrowing `where` or seed completion, plus a `site_id`
   declared-collision rename).

## References

- `docs/adr/0016-governed-procedure-engine.md:1675-2109` — the Amendment
  (2026-07-12), Accepted (PR #707, `main`=`1c296a4`): FKP-1..FKP-4,
  SD-1..SD-5 ratified (SD-4 = supply_chain only); `:1010-1377` — the Q4 join
  amendment (SD-A/B/C/D, the parity discipline).
- `docs/plans/done/0066-threshold-field-per-entity-band-build.md` — the
  same-row build this mirrors: AC-6 RED-verify discipline, Step-7 coupled-test
  audit, the `derive_governance_todo` build-discovered coupling (honest
  completion #1), SD-4 = (b) demo-visible precedent.
- `docs/plans/done/0061-join-projection-grammar-build.md:3,450-452` — Phase C
  shipped (#666); the honest residual ✖ (unmigrated seeds).
- `services/engine/procedures/orchestrator.py:281-283` (stale docstring),
  `:311-312` (gate ordering), `:350-386` (`_validate_threshold_field_bindings`;
  `:374-375` the base-only domain), `:461-487` (`_validate_join_collisions` +
  the `:471-476` join-key exemption), `:490-530` (`_validate_project`).
- `services/engine/procedures/query_step.py:458-520` (`_execute_join`),
  `:522-581` (`_apply_join`), `:583-603` (`_merge`), `:605-646`
  (`_latest_per_group`).
- `services/engine/procedures/env_band_step.py:17-19,66-89` — the delegate
  contract vs the `:74` threshold-only guard; the `:76-81` rebind (the
  direction-clobber / false-audit hazard).
- `services/engine/procedures/evaluate_step.py:14-19,49-68,87-93,103-109,131-139`
  — determinism; fail-loud band; per-row resolution (why zero change).
- `services/engine/procedures/spec.py:796-801` (the description reword —
  the only spec.py touch), `:821-846` (band invariants, unchanged).
- `services/engine/procedures/draft.py:42-59,285-288` — governance pin +
  band-aware todo (zero change; proven by AC-7).
- `verticals/supply_chain/ontology/supply_chain_v0.yaml:32-63` (Shipment;
  `:39-41` cargo_type, `:53-56` facility_id), `:113-118`
  (OperationalEvent refs), `:123` (declared join_path), `:236-240`
  (`event_concerns_shipment`).
- `verticals/supply_chain/procedures.yaml:43-64` (read_temps), `:65-76`
  (judge); `verticals/supply_chain/data_adapter/synthetic.py:24-27,50-89,
  92-141` (seed shipments + events; the 08:08 alarm `:121-129`; the final
  beat note `:8-16`); `verticals/supply_chain/procedures_factory.py:64-76`
  (`:72` EVALUATE wiring).
- `verticals/energy/procedures.yaml:64-75` — the band-less env_band judge
  (the AC-8 regression pin).
- `tests/verticals/supply_chain/test_supply_chain_procedure_factory.py:73` —
  the SD-4-coupled isinstance assert;
  `tests/services/engine/procedures/{test_orchestrator.py,
  test_join_grammar.py,test_env_band_evaluate.py,test_seed_migration_parity.py}`
  — the test homes named in Steps 2–7.
- `alembic/versions/0009_asset_rated_current_a.py` — the ontology-property
  Alembic precedent for `0012_shipment_temp_ceiling`.
