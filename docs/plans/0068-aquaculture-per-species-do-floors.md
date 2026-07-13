# PLAN-0068: aquaculture per-species DO floors — per-entity `threshold_field` on the FK-parent Pond

**Status:** Ready
**Owner:** Claude Code
**Created:** 2026-07-13
**Related ADRs:** ADR-016 **Amendment (2026-07-12): FK-parent-column
`threshold_field` — the join extension (per-entity bands, v2)** — **Accepted**
(PR #707, `main`=`1c296a4`; `docs/adr/0016-governed-procedure-engine.md:1675-2109`,
FKP-1..FKP-4 + SD-1..SD-5 ratified; SD-4 named aquaculture a **labelled
follow-on**, `:2048-2050` — this PLAN is that follow-on); the `threshold_field`
amendment (2026-07-11, TF-1..TF-4); the Q4 join amendment (2026-07-09, SD-A..SD-D);
ADR-0019 / ADR-010 IN-3 (determinism); ADR-006 (Rule-of-Three — **MET at N=3**
for the FK-parent shape by this build); ADR-008 (ontology grammar untouched by a
plain property)

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authoring) from a Code-originated
> dispatch; every cited `file:line` was re-verified on disk 2026-07-13 against
> the post-#711 tree. Independent reviewers = Code R2 (re-verify citations,
> commit per ADR-009 D2) + Cray at SD ratification. Drafter ≠ committer ≠
> ratifier — separation intact. **Drafter findings** the dispatch did not list:
> (i) aquaculture's factory binds the **bare** `EvaluateStepExecutor`
> (`procedures_factory.py:75`) — the s121 env-band delegate-guard coupling does
> NOT exist here, so there is no SD-4-analog factory decision; (ii) the factory
> test's `_FixtureAdapter` serves ONLY OperationalEvent
> (`tests/verticals/aquaculture/test_aquaculture_procedure_factory.py:48-58`) —
> the migrated inner join will empty its rows, a coupled-test break Step 5
> handles deliberately; (iii) seeding the SD-3 flip reading at 01:55 (BEFORE
> the 02:00 crash) keeps the crash as the timeline's final beat — no
> real-time-anchor ripple, an improvement over s121's ratified final-beat move.

## Goal

Migrate aquaculture's `morning_pond_health_round` from ONE blanket 4.0 mg/L
dissolved-oxygen floor for every pond (`verticals/aquaculture/procedures.yaml:97-99`
— scalar `threshold: 4.0` + `direction: below` + `watch_margin: 1.0`) to
**per-species floors banded per pond**: add `Pond.do_floor: float` (SD-1) seeded
per `species` (SD-2), migrate `read_do` to the declared FK-parent `join:`
(bringing each pond's floor onto its latest reading, with the `site_id`
declared-collision renamed away) and the `judge` to
`threshold_field: do_floor` — keeping the authored `direction: below` +
`watch_margin: 1.0`, making this the **first shipped `threshold_field` ×
`watch_margin` (3-band) consumer**. The demo-visible flip (SD-3) is a MISSED
breach: a tiger-prawn pond at 4.2 mg/L is a mere `watch` under the blanket 4.0
but a `breach` under its own 4.5 floor — RED-verified against the unedited YAML
first (PLAN-0066 AC-6 / PLAN-0067 discipline). This is the third OCT vertical
on the per-entity band substrate (procurement same-row s120, supply_chain
FK-parent s121) — Rule-of-Three MET for the FK-parent shape (ADR-006).

**Zero engine change (the SD-0 crux).** The engine is already complete for this
consumer: the executor resolves the band per-row from `threshold_field`
(`evaluate_step.py:103-109`) or scalar (`:110-111`) and applies the authored
`direction` + `watch_margin` (`:116` — `classify_verdict(reading, band,
direction, step.watch_margin)`); the FKP-2 load-gate union domain (base ∪
joined FK-parent) shipped GENERALLY in PR #709
(`orchestrator.py:376-382`); `threshold_field` is already H-governed
(`draft.py:47`) and `derive_governance_todo` is already band-aware
(`draft.py:285-288`). No `orchestrator.py` / `evaluate_step.py` / `spec.py` /
`draft.py` / `env_band_step.py` edit is expected — AC-8 pins that as a
verified outcome, not an assumption. The L-4 tripwire is satisfied by riding
the Accepted 2026-07-12 amendment; no step below reopens FKP-1..FKP-4.

**NO Alembic migration — in-memory vertical (state it, don't let a reviewer
assume otherwise).** `_ORM_COMMITTED_DEST = {"energy": ...}`
(`services/engine/code_generator.py:742`) — only energy has a committed
ORM/DB table. aquaculture's ORM emits to the gitignored
`verticals/aquaculture/generated/orm.py` (`:745-762` fallback); its objects
are served in-memory by the synthetic adapter. So `do_floor`'s ripple is the
ontology YAML + the gitignored regen + the in-memory seeds ONLY — no Alembic
revision, no schema-parity test (energy-only). This is s121's Cray-ratified
in-memory Option A (PLAN-0067 honest record #1), applied here BY DESIGN rather
than build-discovered.

## Acceptance Criteria

- [ ] **AC-1 (ontology property + regen; NO Alembic).** `Pond.do_floor`
  (`type: float`, described as the per-species dissolved-oxygen floor, mg/L)
  added to `aquaculture_v0.yaml` Pond properties (`:16-43`); artifacts
  regenerated via the **console script `uv run vero-lite generate aquaculture`**
  (NOT `python -m` — a silent no-op), verified by the "OK:" output + fresh
  mtimes on `verticals/aquaculture/generated/{models.py,orm.py}`. **Zero
  Alembic revision, zero schema-parity change** — asserted explicitly in the
  PR body (in-memory vertical, `code_generator.py:742`).
- [ ] **AC-2 (per-species seeds — FKP-3 fail-loud sidestepped by
  construction).** ALL FOUR seed ponds (`synthetic.py:54-97`) carry a numeric
  `do_floor` per SD-2 — including the fallow tilapia `pond-05` (demo-inert, no
  readings, but the substrate is uniform — s121's produce/biologic precedent).
  A grep confirms 4/4 pond records carry `do_floor`.
- [ ] **AC-3 (`read_do` join migration + collision rename).** `read_do`
  (`procedures.yaml:64-76`) → `reads: [OperationalEvent, Pond]` +
  `join: [{with: Pond, link: event_emitted_by_pond}]` (declared FK,
  `aquaculture_v0.yaml:170-174`; the equal-named `pond_id` join-key pair is
  exempt, `orchestrator.py:479-487`) + kept `where: {event_type: reading}` +
  kept `latest_per`/`order_by` + `project.fields: {site_id: pond_site_id}` —
  the ONE declared collision (`Pond.site_id` `:40-43` vs
  `OperationalEvent.site_id` `:89-91`, both → Farm; refused at load without
  the rename, `orchestrator.py:490-496`); facet prose re-synced (D2-A2). Both
  the migrated procedure and every other shipped YAML load through the full
  gate (`validate_read_bindings_for_vertical`).
- [ ] **AC-4 (judge migration — the first 3-band `threshold_field`
  consumer).** `judge` (`:87-107`): `threshold: 4.0` →
  `threshold_field: do_floor`; **KEEP** `direction: below` +
  `watch_margin: 1.0` as authored scalars (SD-5 — each species' watch band =
  `(floor, floor + 1.0]`); facet stays
  `{gate_kind: in_file_band, band_source: in_file}` (TF OQ-4 taxonomy — the
  band's NAME is authored in-file); description/goal prose re-synced off the
  hardcoded "4 mg/L" framing.
- [ ] **AC-5 (Q4 SD-C parity).** On the same synthetic fixtures, the migrated
  join run of `read_do` reproduces the prior projection run: the SAME latest
  event per pond (`event_id`, `measured_value`, `occurred_at` equal per
  `pond_id`), the SAME row count, every base OperationalEvent column preserved
  under its own name (base-wins `site_id`); joined Pond columns
  (`do_floor`, `species`, `pond_site_id`, …) are a strict ADDITION (superset
  assertion). Home: `test_seed_migration_parity.py` (the existing aquaculture
  parity tests at `:427-524` extend, not fork).
- [ ] **AC-6 (per-species flip, RED-verified).** A fixture asserts the
  demo-visible MISSED breach — the tiger-prawn pond whose 4.2 mg/L reading
  the blanket 4.0 judges `watch` but its OWN 4.5 floor judges `breach`
  (SD-3) — and is run **against the UNEDITED (blanket-4.0) YAML first**: it
  must FAIL there (pond-11 judged `watch`, aerate fan-out = {pond-07} only),
  then flip GREEN after Step 4 (pond-11 `breach`, aerate fan-out =
  {pond-07, pond-11}). A green against the unedited YAML = the fixture is
  wrong; stop and fix.
- [ ] **AC-7 (in-memory `run_procedure`, not spec-load-only).** An in-memory
  end-to-end run of the migrated procedure (synthetic adapter + real ontology
  meta + the registered factory executors) passes
  `validate_governance_complete` (proving `draft.py:285-288` band-awareness
  holds for this consumer — proven, not assumed; memory:
  a-new-band-field-needs-`derive_governance_todo`, here the SAME field already
  handled), executes the join read + per-row 3-band judge, and suspends
  `waiting_human` at the gated `aerate` with breach set {pond-07, pond-11}.
  Plus a 3-band per-species pin: one fixture pond per species lands breach /
  watch / ok against ITS OWN floor (the first shipped `threshold_field` ×
  `watch_margin` coverage — SD-5).
- [ ] **AC-8 (regression pins + zero-engine-change proof).** supply_chain's
  FK-parent consumer and procurement's same-row consumer byte-identical (their
  YAMLs, seeds, and PLAN-0066/0067 flip tests pass unmodified); energy's
  band-less `env_band` judge (`verticals/energy/procedures.yaml:64-75`) still
  loads + runs; the scalar `threshold` path unchanged; determinism invariant
  (`evaluate_step.py:14-19`) untouched — **zero `orchestrator.py` /
  `evaluate_step.py` / `spec.py` / `draft.py` / `env_band_step.py` /
  `procedures_factory.py` edits** (the diff proves SD-0's "engine already
  complete"). The aquaculture factory keeps the bare `EvaluateStepExecutor`
  (`procedures_factory.py:75` — no env wrapper exists on this path; module
  docstring band prose updated only if stale).
- [ ] **AC-9 (hygiene).** Full suite green WITH Postgres up (one pytest per
  checkout); `ruff check` + `ruff format --check` clean; `mypy --strict
  services/` clean; CI `gate` green on the PR; coupled-test updates disclosed
  in the PR body (Step 5), never silent.

## Out of Scope

- ❌ **energy `rated_current_a` FK-parent adoption** — the OTHER TF-2 residue,
  its own future item (ADR-016 SD-4 labelled follow-on). Verified this
  session: `rated_current_a` exists ONLY in the ontology
  (`energy_v0.yaml:40`) — **0/4 seed assets populate it** (zero occurrences
  outside the YAML), so FKP-3 fail-loud makes migration a step-failing config
  without **mandatory seed completion** (not "partial" backfill) or a
  narrowing `where`, plus energy's own `site_id` collision rename.
- ❌ Any derived arithmetic — the Q4 wall stands: select / rename / equi-join
  ONLY; `do_floor` is a STORED column, never computed.
- ❌ The per-class `species → floor` LOOKUP grammar — ADR-016 SD-2 (b) = OUT
  (over-abstraction at this N).
- ❌ `watch_margin_field` / `direction_field` — still TF OQ-2 = no. The
  authored scalars stay shared across ponds (SD-5).
- ❌ The reactive recommender's env threshold — `OCT_RECOMMEND_THRESHOLD=4` /
  `direction=below` stays for the rule-based recommender path
  (`synthetic.py:28-31` DO_CRASH escalation); only the procedure judge
  migrates. The SD-3 flip reading (4.2 > 4.0) deliberately does NOT trip the
  recommender — that path is byte-unaffected.
- ❌ Re-deciding FKP-1..FKP-4 or the 2026-07-12 amendment's SD-1..SD-5 — the
  Accepted amendment is the contract.
- ❌ Pond `status` filtering in `read_do` (PLAN-0062 SD-4 dropped it; the
  fallow pond has no readings and never reaches the judge — unchanged).
- ❌ NL-query aggregate convergence (Q4 SD-B's named future question).

## Steps

### Step 1: Plan-first read of the result-producing code

Re-read on the executing branch: `orchestrator.py:306-314` (gate ordering:
join/collision checks before the `:314` threshold gate), `:352-395`
(`_validate_threshold_field_bindings` — the `:376-382` FKP-2 union domain,
`:389-395` c3 rename-away refusal), `:470-496` (`_validate_join_collisions` +
the `:479-487` join-key exemption); `evaluate_step.py:87-116` (band-less
guard, per-row resolution, `classify_verdict` with `watch_margin`),
`:131-139` (audit records `threshold_field`); `draft.py:42-59,285-288`;
`verticals/aquaculture/{ontology/aquaculture_v0.yaml,procedures.yaml,
data_adapter/synthetic.py,data_adapter/__init__.py,procedures_factory.py}`;
`verticals/supply_chain/procedures.yaml:43-82` (the shipped join + judge
mirror); `tests/verticals/aquaculture/test_aquaculture_procedure_factory.py`
(the coupled fixture adapter + audit asserts). **Pass/fail read
(pre-committed):** the change-surface citations in this PLAN still match
on-disk code (drift = stop, reconcile line numbers here before editing).

### Step 2: `Pond.do_floor` — ontology + regen + per-species seeds (NO Alembic)

Add `do_floor: {type: float, description: per-species dissolved-oxygen floor
(mg/L) — the pond breaches BELOW it}` to Pond
(`aquaculture_v0.yaml:16-43`; house style mirrors `Shipment.temp_ceiling`).
Regenerate via `uv run vero-lite generate aquaculture`; verify "OK:" + fresh
mtimes on the gitignored `verticals/aquaculture/generated/` artifacts.
**Explicitly NO Alembic revision** (`code_generator.py:742` — energy-only
committed ORM; aquaculture is in-memory synthetic). Seed ALL FOUR ponds
(`synthetic.py:54-97`) per SD-2: `pond-07` (whiteleg) `4.0`, `pond-03`
(whiteleg) `4.0`, `pond-11` (tiger_prawn) `4.5`, `pond-05` (tilapia, fallow)
`3.0`. Whiteleg at 4.0 = verdict continuity for the existing crash narrative
(the s121 pharma-8.0 move). Update the module docstring's band prose (the
"4 mg/L safe threshold" framing gains the per-species note; the recommender
sentence stays — that path is untouched). **Pass/fail read:** generator "OK:"
+ mtimes; adapter/ontology-meta tests green; a grep confirms 4/4 ponds carry
`do_floor`; `git status` shows NO `alembic/versions/` change.

### Step 3: Flip seed event (SD-3) + RED-verify vs the UNEDITED YAML

Add ONE reading to `pond-11` (tiger_prawn, farm-inland-01):
`event-reading-12`, `measured_value: 4.2`, `unit: mg/L`, `severity: warn`,
`occurred_at` 2026-06-02 **01:55** UTC — inserted between the 01:45 aerator
alarm and the 02:00 crash (`synthetic.py:170-189`), so pond-11's latest
reading becomes 4.2 **while the pond-07 crash stays the timeline's final
beat** (real-time anchoring PLAN-0015 D1 undisturbed — the deliberate
improvement over s121's final-beat move; surface to Cray in SD-3). The flip:
`4.2` is `watch` under the blanket 4.0 (a "keep an eye on it" water-exchange
proposal) but `breach` under tiger_prawn's own 4.5 floor (the emergency
aerator) — a genuinely breaching pond DEMOTED by the blanket floor, the
missed-breach class. 4.2 > 4.0 so the reactive recommender does NOT trip
(the docstring invariant "every non-breach reading is kept strictly above
it" holds — with the note that "it" is the recommender's env threshold).
Write the flip fixture (pond-07 `breach` at 3.2 vs 4.0 — continuity;
pond-11 `breach` at 4.2 vs 4.5 — the flip; aerate fan-out =
{pond-07, pond-11}) and run it against the **unedited** `procedures.yaml`.
**Pass/fail read (pre-committed):** the fixture FAILS against the blanket
YAML (pond-11 judged `watch`; aerate = {pond-07} only) — RED proven; a green
here = a wrong fixture, stop and fix it.

### Step 4: Migrate `verticals/aquaculture/procedures.yaml` + the parity test

`read_do` (`:64-76`): `reads: [OperationalEvent, Pond]`; `join: [{with: Pond,
link: event_emitted_by_pond}]`; keep `where: {event_type: reading}` +
`latest_per: event_emitted_by_pond` / `order_by: occurred_at`; add
`project.fields: {site_id: pond_site_id}` (the declared collision — base
OperationalEvent keeps `site_id`, joined Pond's lands as `pond_site_id`;
the `pond_id` join-key pair is exempt); re-sync the facet prose. `judge`
(`:87-107`): `threshold: 4.0` → `threshold_field: do_floor`; keep
`direction: below` + `watch_margin: 1.0`; facet stays `in_file_band`;
re-sync description + the procedure `goal` prose off "the 4 mg/L breach
threshold". Note the c3 guard is satisfied trivially (`do_floor` is not a
`project.fields` key). Add the AC-5 parity test in
`test_seed_migration_parity.py` (extend the `:427-524` aquaculture cases).
**Pass/fail read:** Step-3 fixture flips GREEN; parity test green; every
shipped YAML loads through the gate; `grep -c 'threshold: 4.0'
verticals/aquaculture/procedures.yaml` returns 0.

### Step 5: In-memory `run_procedure` + 3-band per-species pins + coupled-test audit

Add/extend the in-memory end-to-end run per AC-7 (suggested home:
`tests/verticals/aquaculture/test_pond_per_species_floor.py`, mirroring
s121's `test_cold_chain_per_cargo_band.py`): governance-complete → join read
→ per-row judge → `waiting_human` at gated `aerate`, breach set =
{pond-07, pond-11}. Add the SD-5 3-band-per-species pin: fixture ponds with
DISTINCT floors each landing breach / watch / ok against their OWN floor
(e.g. tilapia 3.4 → `watch` vs 3.0 while whiteleg 3.4 → `breach` vs 4.0 —
the same reading, two verdicts: the per-entity point in one assert). Then
audit the coupled modules — updates **deliberate and disclosed in the PR
body**, never silent (PLAN-0066/0067 Step-7 discipline):

- `tests/verticals/aquaculture/test_aquaculture_procedure_factory.py` — the
  `_FixtureAdapter` (`:48-58`) serves ONLY OperationalEvent → the migrated
  inner join would empty its rows: it must also serve Pond rows carrying
  `do_floor` (drafter finding ii); the judge-audit asserts
  (`:155-158` `threshold == 4.0` → `threshold is None` +
  `threshold_field == "do_floor"`); the aerate fan-out (`:160-163`
  `len == 1` → `2`); the three-band fixture (`:166-215`) gains per-pond
  floors.
- `test_seed_migration_parity.py:427-524` — pond-11's latest reading moves
  `event-reading-11` → `event-reading-12`.
- `test_spec.py:455` (the worked-example load assert on the typed band) +
  `:626-627` (aquaculture stays IN `_IN_FILE_BAND_JUDGES` — no list move,
  unlike s121's env→in_file migration).
- `test_example_procedures.py`, `test_prose_lint.py` (facet prose sync),
  `tests/api/test_procedures_endpoint.py`,
  `tests/services/engine/test_aquaculture_vertical.py` +
  `test_demo_events.py` + `test_discovery.py` (event count 7 → 8 /
  health-check `object_counts` / anchor offsets),
  `tests/benchmark/test_procedure_comparison_verticals.py` +
  `test_loader.py`, `test_watch_gated_routing.py` (the watch set's
  membership shifts).

**Pass/fail read:** every audited module green; each modified assertion
listed in the PR body with its reason; zero engine-file diffs (AC-8).

### Step 6: TWO-PR build boundary + full-suite hygiene (SD-4 = (b), RATIFIED — Cray divergence)

Per the ratified SD-4 (b) TWO PRs (the Cray divergence):

- **PR1 (substrate + RED) — Steps 2–3.** Branch
  `feat/plan0068-aqua-do-floor-substrate`: add `Pond.do_floor` + regen (NO
  Alembic) + per-species seeds (Step 2) + the SD-3 flip seed reading +
  the RED-verify run recorded against the UNEDITED `procedures.yaml` (Step 3
  — pond-11 judged `watch`, aerate = {pond-07} only, proving RED before the
  migration). The judge is NOT yet migrated in PR1, so the suite stays green
  on the blanket-4.0 behaviour; the flip fixture is committed here in its
  RED-proven form (xfail/skip-guarded or asserting the blanket verdict), then
  flipped GREEN in PR2 — disclose the mechanism in the PR body.
- **PR2 (migration + tests) — Steps 4–5.** Branch
  `feat/plan0068-aqua-per-species-judge`: the `read_do` join + `site_id`
  rename + the `judge` `threshold: 4.0` → `threshold_field: do_floor` (Step 4)
  + the parity test, the flip fixture flipped GREEN, the in-memory
  `run_procedure` + 3-band per-species pin, and every coupled-test update
  (Step 5). Rebase on `main` after PR1 merges.

For each PR: start `vero-postgres` (Docker Desktop, Windows engine); run the
FULL suite via WSL (one pytest per checkout), `ruff check .`,
`ruff format --check .`, `mypy --strict services/`; PR body via `--body-file`
(built with the Write tool), citing the ADR-016 2026-07-12 amendment (FKP-1)
+ this PLAN; CI `gate` green; each merge needs a fresh Cray sign-off
(auto-mode blocks agent-authored merges). After PR2 merges + Cray closeout:
`git mv docs/plans/0068-*.md docs/plans/done/`. **Pass/fail read:** suite
green with DB up (~123 skips = DB down — restart and rerun); linters clean;
CI `gate` green on both PRs.

## Surfaced decisions (SD-0 … SD-5 — RATIFIED by Cray 2026-07-13)

> **Ratification record.** All six SDs were RATIFIED by Cray on 2026-07-13
> (typed, via AskUserQuestion), after Code R2 re-verified every load-bearing
> citation on disk. **As-recommended: SD-0, SD-1, SD-2, SD-3, SD-5.**
> **SD-4 = (b) TWO PRs — a CRAY DIVERGENCE** from the drafter's recommended
> (a) ONE PR (mirrors s121/PLAN-0067's SD-1(b) two-PR Cray divergence). Each
> recommendation below now reads as the ratified disposition.

The **direction is LOCKED** upstream: per-entity bands via a denormalized
numeric FK-parent column + the declared `join:` (ADR-016 FKP-1/FKP-4,
Accepted; the per-class lookup is OUT per its SD-2 (b); the same-row
denormalize-onto-readings shape was REJECTED by Cray 2026-07-12). Ratified:

- **SD-0 — fresh ADR-016 amendment, or a pure new-consumer build PLAN riding
  the Accepted FKP-1 (THE lead decision)?** *Recommend: pure build PLAN, NO
  fresh amendment.* Evidence for: **zero engine/grammar change** — the gate
  union-domain shipped generally in #709 (`orchestrator.py:376-382`), the
  executor already composes `threshold_field` × `direction` × `watch_margin`
  (`evaluate_step.py:103-116`), `Pond.do_floor` is a plain authored property
  (ADR-008 grammar untouched), and PLAN-0062 migrated consumers onto shipped
  grammar without an amendment; the L-4 tripwire covers spec/grammar
  *changes*, and this PLAN makes none. Evidence against: ADR-016 SD-4 said
  aquaculture "lands under this same amendment discipline when scheduled"
  (`0016:2048-2050` — readable as requiring an amendment), and s120/s121 each
  minted one (but each CHANGED grammar/gate semantics; this build changes
  neither). *Why Cray's call:* it fixes what "amendment discipline" means for
  a zero-grammar-delta consumer — a governance-record precedent future
  verticals will cite. If Cray picks "thin amendment," this PLAN stands
  unchanged and gains the citation.
- **SD-1 — the band property: name + shape.** *Recommend:*
  `Pond.do_floor: float`, seeded per `species` so every pond that reaches the
  judge carries a numeric value (FKP-3 fail-loud sidestepped by construction
  — supply_chain's per-cargo_type precedent, ADR-016 SD-2 (a)). `do_floor`
  mirrors `temp_ceiling`'s house style (direction-bearing name). Alternatives:
  `do_floor_mg_l` (unit-suffixed — rejected: no shipped band column carries a
  unit suffix); the per-class lookup map (OUT upstream). *Why Cray's call:*
  new governed ontology surface on a demo vertical.
- **SD-2 — the per-species floor VALUES (synthetic, plausible — no external
  source cited; penaeid shrimp need higher DO, tilapia is hypoxia-tolerant).**
  *Recommend:* whiteleg_shrimp **4.0** (equals today's blanket — verdict
  continuity for the pond-07 crash narrative), tiger_prawn **4.5**, tilapia
  **3.0**. The values make the SD-3 flip real (4.0 < 4.2 < 4.5) and keep
  every healthy reading (≥ 5.4) `ok` under all floors + margins. *Why Cray's
  call:* demo-visible domain numbers, permanent-record bar.
- **SD-3 — the demo-visible flip.** *Recommend:* ONE seeded reading —
  `event-reading-12`, pond-11 (tiger_prawn), **4.2 mg/L at 01:55** — the
  MISSED-breach class (blanket demotes a real breach to `watch`;
  safety-relevant, s121's frozen-cargo analog), timed BEFORE the 02:00 crash
  so the final beat + real-time anchor are undisturbed (drafter finding iii
  — deliberately cleaner than s121's ratified final-beat move; the aerate
  breach set still grows 1 → 2, a ratified demo-output change). Alternatives:
  (b) also seed a tilapia false-alarm flip (blanket over-alarms a hardy
  species, `breach`→`watch`) — richer, but pond-05 is fallow with no
  readings, so it needs a new pond or a status change: more demo churn,
  recommend NOT at this N; (c) test-local fixture only, seeds untouched —
  declined in s120 AND s121 (Cray consistently picked demo-visible). *Why
  Cray's call:* it changes the live demo's visible behavior (breach set,
  watch set, event count).
- **SD-4 — one PR or two? RATIFIED (b) TWO PRs — a CRAY DIVERGENCE** from the
  drafter's recommended (a) ONE PR (Cray typed, via AskUserQuestion). The
  drafter's (a) rationale was: s121's two-PR rationale (isolating a
  DB-migration + first-`join:`-consumer rollback) does not transfer here — NO
  migration (in-memory), NO engine diff, the join-consumer shape already
  shipped in supply_chain. **Cray chose (b) anyway** — the same PR-granularity
  divergence Cray made in s121/PLAN-0067's SD-1(b); the PR-granularity call is
  Cray's own precedent line. **The ratified boundary (plan of record):**
  **PR1 = Steps 2–3** (`Pond.do_floor` substrate + per-species seeds + the
  SD-3 flip seed + RED-verify against the unedited YAML); **PR2 = Steps 4–5**
  (`read_do` join + `judge` migration + parity/flip/in-memory/coupled-test
  updates). Step 6 carries this boundary.
- **SD-5 — `watch_margin` & `direction`.** *Recommend: KEEP* `direction:
  below` + `watch_margin: 1.0` as authored scalars — per-species floor +
  shared relative watch offset (each species' watch = `(floor, floor+1.0]`;
  coherent: the escalate zone tracks the floor). This makes aquaculture the
  **first shipped `threshold_field` + `watch_margin` (3-band) combination** —
  the executor supports it (`evaluate_step.py:116`) but it is NEW test
  surface: AC-7's per-species 3-band pin covers it. Alternatives: drop
  `watch_margin` (rejected — it would delete the shipped ADR-0019
  watch→gated escalation path); `watch_margin_field` per species (OUT — TF
  OQ-2, over-abstraction at this N). *Why Cray's call:* it fixes the
  watch-band semantics every future floor-vertical will copy.

## Verification

AC-1/AC-2 by the generator "OK:" + mtimes + the 4/4 seed grep + the
no-Alembic `git status` check (Step 2); AC-3/AC-4 by the load-gate pass +
the `grep -c 'threshold: 4.0'` = 0 (Step 4); AC-5 by the parity test
(Step 4); AC-6 by the RED-then-GREEN fixture sequence (Steps 3–4 — the flip
is proven against the unedited YAML first); AC-7 by the in-memory
`run_procedure` + the per-species 3-band pin (Step 5 — an in-memory run, NOT
spec-load-only: a load-only test masks governance-gate + executor-wiring
gaps, the PLAN-0066 build-discovered lesson); AC-8 by the unmodified
supply_chain/procurement/energy/scalar pins + the zero-engine-diff check
(Step 5); AC-9 by the Step-6 full-suite + linter + CI `gate` run. Evidence =
fresh pytest/linter output on the branch; pass/fail reads pre-committed per
step (Lesson #0026). No live host-state run is required — the offline oracle
is the gate (CLAUDE.md §8).

## References

- `docs/adr/0016-governed-procedure-engine.md:1675-2109` — the Accepted
  FK-parent amendment (FKP-1..FKP-4; `:1877-1891` FKP-4 substrate shape;
  `:1964-1970` aquaculture named OUT-deferred; `:2041-2050` SD-4 "labelled
  follow-on"; `:2104-2106` the aquaculture citations it pre-recorded).
- `docs/plans/done/0067-fk-parent-threshold-field-build.md` — the s121 build
  this mirrors: RED-verify (AC-6), coupled-test audit (Step 7), the
  no-Alembic honest record #1, the two-PR ratified SD-1 (b) this PLAN's SD-4
  distinguishes.
- `docs/plans/done/0066-threshold-field-per-entity-band-build.md` — the
  same-row migration precedent + the `derive_governance_todo` coupling.
- `services/engine/procedures/orchestrator.py:306-314` (gate ordering),
  `:352-395` (`_validate_threshold_field_bindings`; `:376-382` FKP-2 union
  domain; `:389-395` c3), `:470-496` (`_validate_join_collisions`;
  `:479-487` join-key exemption; `:488` renamed set).
- `services/engine/procedures/evaluate_step.py:87-93` (band-less guard),
  `:103-111` (per-row band resolution), `:116` (`classify_verdict` — why
  `threshold_field` composes with `watch_margin`), `:131-139` (audit).
- `services/engine/procedures/draft.py:42-59` (`STEP_GOVERNANCE_FIELDS`,
  `threshold_field` at `:47`), `:285-288` (band-aware
  `derive_governance_todo`) — zero change, proven by AC-7.
- `services/engine/code_generator.py:742` (`_ORM_COMMITTED_DEST` —
  energy-only), `:745-762` (gitignored ORM fallback — the no-Alembic ground).
- `verticals/aquaculture/ontology/aquaculture_v0.yaml:16-43` (Pond; `:34-36`
  species; `:40-43` site_id), `:89-91` (OperationalEvent.site_id — the
  collision), `:170-174` (`event_emitted_by_pond`).
- `verticals/aquaculture/procedures.yaml:64-76` (`read_do`), `:87-107` (the
  blanket judge; `:97-99` the scalar band).
- `verticals/aquaculture/data_adapter/synthetic.py:28-31` (`DO_CRASH_MG_L` +
  the recommender invariant), `:54-97` (ponds), `:100-194` (events; `:125-135`
  pond-11's 6.5 reading; `:170-189` the 01:45 alarm → 02:00 crash window the
  flip reading slots into); `data_adapter/__init__.py:26-39` (demo_events
  routing + `_OBJECT_SOURCES`).
- `verticals/aquaculture/procedures_factory.py:75` — the bare
  `EvaluateStepExecutor` (no env wrapper → no s121 delegate-guard coupling).
- `verticals/supply_chain/procedures.yaml:43-82` — the shipped join + judge
  mirror (`:53-59` join + rename syntax; `:75-76` threshold_field + direction).
- `verticals/energy/ontology/energy_v0.yaml:40` — `rated_current_a`
  (ontology-only, 0 seed occurrences — the Out-of-Scope ground).
- `tests/verticals/aquaculture/test_aquaculture_procedure_factory.py:48-58`
  (the OperationalEvent-only `_FixtureAdapter`), `:155-158` (audit asserts),
  `:160-163` (aerate fan-out), `:166-215` (three-band fixture);
  `tests/services/engine/procedures/test_seed_migration_parity.py:427-524`;
  `test_spec.py:455,626-627` — the Step-5 audit homes.
