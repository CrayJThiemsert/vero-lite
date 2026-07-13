# PLAN-0070: energy over-current re-theme — per-feeder `rated_current_a` band on the FK-parent Asset

**Status:** Complete — built + merged 2026-07-13 (session 125), one PR (SD-1). All 9 ACs
met; the RED→GREEN per-feeder flip verified end-to-end (Feeder Meter A at 84 A is `ok`
under the blanket env 90 band but `breach` at 105% of its own 80 A rating → gated restart);
full suite **2572 passed / 7 skipped** WITH Postgres; ruff + `ruff format` + `mypy --strict`
clean; **zero functional `services/` change** (the only `services/` diff is the SD-5
env_band_step.py docstring hunk — the last shipped env_band judge retired). **Build-discovered
coupling (correction to AC-8's "benchmark UNMODIFIED" pin):** the two current readings grew the
energy synthetic OperationalEvent set 11 → 13 and added a second `warn` reading, which rippled
into the NL-query feasibility benchmark gold set — `gold.yaml` nl-02 (total 11→13), nl-03
(measured_value>80, 2→3: the 84 A reading is unit-agnostically >80), nl-05 (warn 1→2) updated to
match the data (the corpus header requires hand-verified-against-data), plus the two
`test_nl_query_text_to_sql.py` SQL cross-checks. No production code touched.

**Prior status:** Ready — Code R2 PASS (all 7 load-bearing citations verified vs code,
2026-07-13); SD-1…SD-6 RATIFIED by Cray (AskUserQuestion, 2026-07-13).
**Owner:** Claude Code
**Created:** 2026-07-13
**Related ADRs:** ADR-016 **Amendment (2026-07-12): FK-parent-column
`threshold_field` — the join extension (per-entity bands, v2)** — **Accepted**
(PR #707, `main`=`1c296a4`; `docs/adr/0016-governed-procedure-engine.md:1675-2109`).
This PLAN is the **energy labelled follow-on that amendment pre-recorded**: the
change surface at `:1920-1926` names `judge → threshold_field: rated_current_a`
+ the `event_emitted_by_asset` join + the `site_id` collision rename + the FKP-3
partial-population narrowing, and SD-4 (`:2041-2050`) deferred it as "cheap on
paper but NOT free". **NO new ADR** — this rides the Accepted amendment (zero
grammar/gate change expected; AC-8 pins it as a verified outcome). Also: ADR-0019
/ ADR-010 IN-3 (determinism); ADR-006 (Rule-of-Three — already MET at N=3 by
PLAN-0068; see the honesty note in Goal); ADR-008 (ontology grammar untouched —
here not even a property is added).

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authoring) from a Code-originated
> dispatch carrying Cray's LOCKED Option-A decision (2026-07-13, typed via
> AskUserQuestion); every cited `file:line` was re-verified on disk 2026-07-13
> against the post-#723 tree. Independent reviewers = Code R2 (re-verify
> citations, commit per ADR-009 D2) + Cray at SD ratification. Drafter ≠
> committer ≠ ratifier — separation intact. **Drafter findings** the dispatch
> did not list: (i) the reactive recommender + PLAN-0015 demo anchor are
> **unit-blind at 90.0** (`config.py:186-193`; `demo_events.py:44-67` anchors on
> the latest reading crossing 90 *regardless of unit*) — every seeded ampere
> reading must stay **< 90 A** and **before 08:10** or the demo anchor moves and
> the recommender double-escalates; (ii) the ontology's own `rated_current_a`
> description ("for current-rated assets … distinct from capacity_kw, which
> misfits assets rated in A", `energy_v0.yaml:42-44`) makes 4/4 uniform seed
> completion **ontology-incoherent** for energy — the narrowing `where` is the
> coherent FKP-3 option (SD-2/SD-6); (iii) `env_band_step.py:6-7` is **already
> stale** (still names `supply_chain.judge` as an env consumer post-#710), and
> after this migration the env half has **zero** shipped YAML consumers (SD-5);
> (iv) `tests/services/engine/test_nl_query.py:655-656,667` pin the energy
> OperationalEvent count at **11** — seed additions break NL-query tests, not
> just procedure tests; (v) a `restart`→`shed_load`/`trip` handler rename would
> require an **ontology enum edit** (`RecommendedAction.action_type`
> `energy_v0.yaml:160-163` = {restart, isolate, dispatch_technician, escalate})
> — hard grounds for SD-3's keep-restart.

## Goal

Re-theme energy's single procedure `substation_health_sweep`
(`verticals/energy/procedures.yaml:34-95`) from over-TEMPERATURE to
over-CURRENT (feeder overload), making energy the **4th OCT vertical on the
per-entity FK-parent `threshold_field` band substrate** (procurement same-row
s120, supply_chain `temp_ceiling` s121, aquaculture `do_floor` s123):
`read_readings` gains the declared FK-parent `join:` via `event_emitted_by_asset`
(`energy_v0.yaml:205-209`) plus a narrowing
`where: {event_type: reading, measured_kind: current}`, and the `judge`
migrates `env_band` (blanket `OCT_RECOMMEND_THRESHOLD`, `procedures.yaml:71`)
→ `threshold_field: rated_current_a` + `direction: above` — each feeder's
latest current reading (ampere) banded against its OWN `Asset.rated_current_a`
(`energy_v0.yaml:40-44`). The demo-visible flip (SD-2) is a MISSED overload: a
feeder at 84 A is `ok` under the blanket 90 band but `breach` under its own
80 A rating — RED-verified against the unedited YAML first (PLAN-0066 AC-6 /
0067 / 0068 discipline).

**LOCKED upstream (Cray, 2026-07-13, typed via AskUserQuestion — do NOT
re-open):** Option A = **re-theme the existing single procedure**, not add a
second one. The over-temperature *procedure* demo is intentionally replaced by
an over-current demo; over-current/feeder-overload → human-gated restart is a
grid narrative as strong as over-temp. The reactive recommender / timeline
demo path stays over-temp (Out of Scope).

**Honesty note — demo-breadth, not moat-critical.** Rule-of-Three for the
FK-parent band shape was already MET at N=3 by PLAN-0068 (ADR-006). This build
adds demo breadth (all four verticals on the per-entity substrate) at the
lowest-effort coherent path — one procedure migrated, mirroring the exemplars
exactly. That framing is Cray's ratified rationale for Option A, recorded here
so the permanent record does not over-claim.

**Zero engine change expected; zero substrate build.** The FKP-2 union domain
shipped generally in #709 (`orchestrator.py:376-382`); the env-band delegate
guard already recognizes `threshold_field` (`env_band_step.py:76-77` — the
PLAN-0067 AC-2 coupling, shipped); the executor resolves the band per-row
(`evaluate_step.py:103-116`); `derive_governance_todo` is already
`threshold_field`-aware (`draft.py:282-289`). And uniquely among the four
verticals, energy's substrate **pre-exists end-to-end**: `rated_current_a` is
in the ontology (`energy_v0.yaml:40-44`), the committed ORM
(`services/db/models.py:21`), and Alembic (`0009_asset_rated_current_a.py`;
head = `0011_schedule_states.py`), and the ontology already models
`measured_kind: current` (`:99-101`), `unit` sample `ampere` (`:93-98`), and
the current/ampere quantity_binding whose `join_path` literally pre-declares
this join (`OperationalEvent.asset_id -> Asset.asset_id`, `:120-123`). So:
**NO ontology edit, NO `generated/**` regen, NO Alembic migration** — the whole
change is `synthetic.py` seeds + `procedures.yaml` + tests. The L-4 tripwire is
satisfied by riding the Accepted amendment; no step reopens FKP-1..FKP-4.

## Acceptance Criteria

- [ ] **AC-1 (substrate seeds — ontology/DB untouched).** Per ratified SD-2:
  `rated_current_a` values on the current-rated seed assets and TWO new
  current (ampere) readings in
  `verticals/energy/data_adapter/synthetic.py:54-92,95-240` (today 0/4 assets
  carry `rated_current_a` and zero `measured_kind: current` readings exist).
  **Recommender/anchor invariants (drafter finding i):** every added reading's
  `measured_value` < 90.0 AND `occurred_at` before the 08:10 breach
  (`event-reading-03`) — the reactive recommender (`recommender.py:113-121`),
  the fail-safe rule, and the PLAN-0015 demo anchor
  (`demo_events.py:44-67`) are byte-unaffected; the thermal final beat stays
  the timeline's latest event (module docstring `synthetic.py:8-16` updated,
  invariant preserved). `git status` shows NO change under
  `verticals/energy/ontology/`, `alembic/versions/`, or `services/db/`.
- [ ] **AC-2 (per-feeder flip, RED-verified).** A fixture asserts the
  demo-visible MISSED overload — the feeder-metering asset whose 84 A reading
  the blanket env 90 band judges `ok` but its OWN 80 A rating judges `breach`
  (SD-2) — and is run **against the UNEDITED YAML first**: it must FAIL there
  (84 < 90 → `ok`; restart fan-out = {asset-battery-01} only), then flip GREEN
  after Step 4 (breach set = {asset-meter-01}). A green against the unedited
  YAML = the fixture is wrong; stop and fix.
- [ ] **AC-3 (`read_readings` join migration + collision rename + narrowing
  where).** `read_readings` (`procedures.yaml:43-63`) →
  `reads: [OperationalEvent, Asset]` +
  `join: [{with: Asset, link: event_emitted_by_asset}]` (declared FK
  `energy_v0.yaml:205-209`; the equal-named `asset_id` join-key pair is exempt,
  `orchestrator.py:479-487`) + `where: {event_type: reading,
  measured_kind: current}` (the ADR-016 `:1926` FKP-3 narrowing — `where` is
  all-pairs field equality, `spec.py:356-358`, applied BEFORE `latest_per`,
  `query_step.py:150-151,464`) + kept `latest_per: event_emitted_by_asset` /
  `order_by: occurred_at` + `project.fields: {site_id: asset_site_id}` — the
  ONE declared collision (`Asset.site_id` `energy_v0.yaml:54-57` vs
  `OperationalEvent.site_id` `:110-112`, both → Site; refused at load without
  the rename, `orchestrator.py:490-496`); facet prose re-synced (D2-A2). Every
  shipped YAML loads through `validate_read_bindings_for_vertical`.
- [ ] **AC-4 (judge migration — the LAST shipped env_band consumer retires).**
  `judge` (`procedures.yaml:64-75`): drop the env facet binding →
  `threshold_field: rated_current_a` + `direction: above` (band shape per
  ratified SD-4), facet `decision_condition` →
  `{gate_kind: in_file_band, band_source: in_file}`; procedure `goal`
  (`:36-39`), step names/descriptions, and agent comment prose (`:26-31`)
  re-themed to feeder overload; `grep -c 'env_band'
  verticals/energy/procedures.yaml` returns 0.
- [ ] **AC-5 (parity-ADAPTED — per ratified SD-6, NOT strict Q4 SD-C).** The
  strict same-rows parity of 0067/0068 cannot hold: the narrowing `where`
  intentionally shrinks the sweep (latest-any-reading per 4 assets → latest
  CURRENT reading per current-rated asset). Instead: (a) each surviving row
  preserves every base OperationalEvent column under its own name and gains
  the joined Asset columns (`rated_current_a`, `asset_site_id`, …) as a strict
  ADDITION; (b) the row-set delta is asserted EXPLICITLY (exactly the
  current-reading assets remain; the battery temperature rows and Hz-only
  histories leave the sweep — the re-theme's intended, disclosed delta).
- [ ] **AC-6 (in-memory `run_procedure`, not spec-load-only).** An in-memory
  end-to-end run (synthetic adapter + real ontology meta + the registered
  factory executors) passes `validate_governance_complete` — the migrated
  judge's derived obligations become `[threshold_field, direction]`, both
  authored (`draft.py:282-289` — the PLAN-0066 coupling, proven not assumed) —
  executes the narrowed join read + per-row judge, and suspends
  `waiting_human` at gated `restart_breaches` with breach set
  {asset-meter-01} and the judge audit recording
  `threshold_field: rated_current_a` with NO `band_source: "env"` stamp
  (`evaluate_step.py:131-139`; the delegate guard `env_band_step.py:76-77`).
- [ ] **AC-7 (coupled-test audit — the bulk of the risk).** Every module the
  Step-5 audit enumerates is updated deliberately and disclosed in the PR
  body, never silently (0066/0067/0068 discipline). Known from this draft's
  sweep: `test_energy_procedure_factory.py:101-117` (readings set, breach set
  battery→meter, the `:111` `band_source == "env"` assert, fan-out asset),
  `test_spec.py:634-639,678-692` (energy joins `_IN_FILE_BAND_JUDGES`;
  `test_env_band_judge_migrated` retires — no shipped env_band judge remains),
  `test_procedures_endpoint.py:134-141` (env_band → in_file_band asserts),
  `test_nl_query.py:655-656,667` (event count 11 → 13), plus the Step-5 grep
  sweep.
- [ ] **AC-8 (regression pins + zero-functional-engine-change proof).**
  supply_chain / aquaculture / procurement YAMLs, seeds, and flip tests
  byte-identical; the scalar `threshold` path and determinism invariant
  (`evaluate_step.py:14-19`) untouched; the reactive recommender path
  UNMODIFIED — `oct_recommend_threshold` 90.0 / `direction` above / label
  "over-temperature" (`config.py:186-226`) all stay, and
  `test_recommender*.py`, `test_demo_events.py`, the golden traces, and the
  LLM/benchmark modules pass UNMODIFIED (the benchmark corpus does not read
  `procedures.yaml` — verified `tests/benchmark/test_loader.py` has no
  `load_procedures` reference). **Zero functional `services/` change**; the
  only permitted `services/` diff is the SD-5 docstring sync
  (`env_band_step.py:6-7`) if ratified, disclosed as such.
- [ ] **AC-9 (hygiene).** Full suite green WITH Postgres up (one pytest per
  checkout); `ruff check` + `ruff format --check` clean; `mypy --strict
  services/` clean; CI `gate` green on the PR(s); the FULL suite re-run on the
  merge commit (CI is PR-only — the merge commit is never tested otherwise).

## Out of Scope

- ❌ **Any ontology edit / `generated/**` regen / Alembic migration** — all
  unnecessary: `rated_current_a`, `measured_kind: current`, `ampere`, and the
  current quantity_binding pre-exist (`energy_v0.yaml:40-44,93-101,120-123`;
  `services/db/models.py:21`; `alembic/versions/0009_asset_rated_current_a.py`).
- ❌ **A second energy procedure** — that was Option B, REJECTED by Cray's
  LOCKED 2026-07-13 decision. One procedure, re-themed.
- ❌ **The reactive recommender / timeline demo path** — `OCT_RECOMMEND_*`
  (90 °C, above, "over-temperature"), the thermal incident seeds
  (`event-reading-01..-03,-05,-06`), the PLAN-0015 anchor, golden traces,
  NL-query semantics, and the fail-safe rule all stay over-temp. Only the
  procedure judge migrates (the 0067/0068 recommender-path precedent).
- ❌ Renaming the `restart` handler or the `substation_health_sweep`
  procedure_id (per SD-3 recommendation — a handler rename is an ontology
  enum edit, `energy_v0.yaml:160-163`; an id rename ripples through
  `test_runs_endpoints.py:33-34`, `test_procedures_endpoint.py:29`,
  `test_spec.py:684,737` and any demo wiring for zero narrative gain).
- ❌ Deleting `EnvBandEvaluateExecutor` or the `env_band` gate_kind even
  though this retires the last shipped YAML consumer — the executor stays
  engine-general and test-covered (`test_env_band_evaluate.py`); removal
  would be an engine change needing its own ADR-016 conversation.
- ❌ Any derived arithmetic — the Q4 select/rename/equi-join wall stands;
  `rated_current_a` is a STORED column.
- ❌ `watch_margin_field` / `direction_field` (TF OQ-2 = no); the per-class
  lookup grammar (ADR-016 SD-2 (b) = OUT).
- ❌ Re-deciding FKP-1..FKP-4 or the amendment's SD-1..SD-5 — the Accepted
  amendment is the contract.
- ❌ The Box-4 economic facet.

## Steps

### Step 1: Plan-first read of the result-producing code

Re-read on the executing branch: `orchestrator.py:352-395` (threshold gate;
`:376-382` FKP-2 union domain; `:389-395` c3), `:470-496`
(`_validate_join_collisions`; `:479-487` join-key exemption);
`evaluate_step.py:87-140` (band-less guard, per-row resolution `:103-116`,
audit `:131-139`); `env_band_step.py` (full — the `:76-77` guard + the stale
`:6-7` docstring); `draft.py:282-289`; `demo_events.py:44-67` +
`config.py:186-226` (the unit-blind 90.0 couplings);
`verticals/energy/{procedures.yaml,ontology/energy_v0.yaml,
data_adapter/synthetic.py,data_adapter/__init__.py,procedures_factory.py}`;
`verticals/supply_chain/procedures.yaml:43-82` +
`verticals/aquaculture/procedures.yaml:64-108` (the shipped join + judge
mirrors); `tests/verticals/energy/test_energy_procedure_factory.py`.
**Pass/fail read (pre-committed):** the change-surface citations in this PLAN
still match on-disk code (drift = stop, reconcile line numbers here before
editing).

### Step 2: Seeds — `rated_current_a` values + two current readings (SD-2)

In `verticals/energy/data_adapter/synthetic.py`, per ratified SD-2:

- `asset-meter-01` ("Feeder Meter A", the feeder measurement point,
  `:84-91`): `rated_current_a: 80.0` (an LV distribution-feeder rating).
- `asset-inverter-01` (`:66-74`): `rated_current_a: 722.0` (derived: 500 kW
  at 400 V 3φ ≈ 722 A — provenance from its own `capacity_kw`).
- The batteries stay UNRATED — per the ontology's own SD-6/F9 description
  (`energy_v0.yaml:42-44`: `rated_current_a` is for current-rated assets,
  *distinct from* `capacity_kw` which "misfits assets rated in A"). Partial
  population is energy's DESIGNED shape (ADR-016 `:1871-1875`); the Step-4
  narrowing `where` makes it FKP-3-safe (unrated assets never reach the
  judge).

Add TWO current readings (energy's `event-reading-07`/`-08` ids are free —
the seed set uses `-01..-06,-09..-11`):

- `event-reading-07`: asset-inverter-01, `measured_value: 61.0`,
  `unit: ampere`, `measured_kind: current`, severity `info`, 08:02 UTC —
  light morning load, ~8% of its 722 A rating (`ok` under any band).
- `event-reading-08`: asset-meter-01, `measured_value: 84.0`,
  `unit: ampere`, `measured_kind: current`, severity `warn`, 08:04 UTC —
  **105% of its own 80 A rating**, the overload the blanket band misses.

Both < 90.0 (recommender + fail-safe + demo anchor byte-unaffected — drafter
finding i) and both BEFORE the 08:08 alarm / 08:10 breach (the thermal climax
stays the final beat — the PLAN-0068 finding-iii discipline; no real-time
anchor ripple). Update the module docstring (`:8-21`): the "every non-breach
reading is kept below it" invariant now explicitly means the RECOMMENDER's
env threshold, and the current readings are noted as sub-90 by design.
**Pass/fail read:** adapter/ontology-meta tests green;
`test_demo_events.py` + `test_recommender*.py` + parity `:319`
(battery-01 = event-reading-03) pass UNMODIFIED; the NL-query count pins
(`test_nl_query.py:655-656,667`) updated 11 → 13 in the same commit,
disclosed; a grep confirms exactly 2 assets carry `rated_current_a` and
exactly 2 `measured_kind: current` events exist.

### Step 3: Flip fixture + RED-verify vs the UNEDITED YAML

Write the per-feeder verdict fixture (breach set = {asset-meter-01}; 84.0 vs
its own 80.0 = `breach`; inverter 61.0 vs 722.0 = `ok`; the batteries ABSENT
from the sweep) and run it against the **unedited** `procedures.yaml` (env
blanket, un-narrowed): meter-01's latest reading is now the 84 A row, judged
vs env 90 → `ok`, and the breach set is still {asset-battery-01} (96.5 ≥ 90).
**Pass/fail read (pre-committed):** the fixture FAILS against the unedited
YAML — RED proven; a green here = a wrong fixture, stop and fix it. (This is
also the PLAN-0066/0067/0068 AC-6 discipline verbatim.)

### Step 4: Migrate `verticals/energy/procedures.yaml`

`read_readings` (`:43-63`): `reads: [OperationalEvent, Asset]`;
`join: [{with: Asset, link: event_emitted_by_asset}]`; `where:
{event_type: reading, measured_kind: current}`; keep
`latest_per: event_emitted_by_asset` / `order_by: occurred_at`; add
`project.fields: {site_id: asset_site_id}` (the declared collision — base
OperationalEvent keeps `site_id`, joined Asset's lands as `asset_site_id`;
the `asset_id` join-key pair is exempt); re-sync the facet prose. `judge`
(`:64-75`): `threshold_field: rated_current_a` + `direction: above` (+
`watch_margin` only if SD-4 (b) is ratified); facet `decision_condition` →
`{gate_kind: in_file_band, band_source: in_file}`; description → "each
asset's verdict vs ITS OWN rated_current_a". `restart_breaches` (`:76-94`):
keep `handler: restart` + `autonomy: gated` + the `{from: judge, where:
{verdict: breach}}` fan-out (SD-3); description reworded to the overload
narrative ("propose a restart of the overloaded feeder's breaker …").
Procedure `goal` (`:36-39`) + the header comment (`:7-12`) + the grid_agent
comment (`:26-31`) re-themed. Add the AC-5 parity-adapted assertions (home:
extend `test_seed_migration_parity.py`'s energy block — the `:50` mirror
comment updates with the YAML). **Pass/fail read:** the Step-3 fixture flips
GREEN; every shipped YAML loads through the gate; `grep -c 'env_band'
verticals/energy/procedures.yaml` = 0; `grep -c 'OCT_RECOMMEND'
verticals/energy/procedures.yaml` = 0.

### Step 5: In-memory `run_procedure` + coupled-test audit

Add the in-memory end-to-end run per AC-6 (suggested home:
`tests/verticals/energy/test_feeder_overcurrent_band.py`, mirroring s121's
`test_cold_chain_per_cargo_band.py` / s123's
`test_pond_per_species_floor.py`): governance-complete → narrowed join read →
per-row judge → `waiting_human` at gated `restart_breaches`, breach set
{asset-meter-01}, audit `threshold_field == "rated_current_a"` and NO
`band_source` key. Then audit the coupled modules — updates **deliberate and
disclosed in the PR body**, never silent:

- `tests/verticals/energy/test_energy_procedure_factory.py` — `:101-108`
  (readings = the 2 current rows; judged set mirrors it; breaches
  [asset-battery-01] → [asset-meter-01]); `:111` (`band_source == "env"` —
  REMOVE/invert: the delegated in-file path stamps none); `:114-117` (fan-out
  stays len 1, the asset changes); `:76-77` isinstance survives under SD-5
  (a).
- `tests/services/engine/procedures/test_spec.py` — `:634-639` energy joins
  `_IN_FILE_BAND_JUDGES`; `:678-692` `test_env_band_judge_migrated` retires
  (zero shipped env_band judges remain — note it in the PR body as the
  milestone it is); `:737` (read_readings `gate_kind: none`) unaffected.
- `tests/api/test_procedures_endpoint.py:134-141` — the energy judge asserts
  flip to `threshold_field`/`in_file_band`.
- `tests/api/test_runs_endpoints.py` — stub-driven (`:111` fabricates
  verdicts); step ids + handler kept per SD-3, so expected minimal; audit the
  `:79-82` stub prose (cosmetic re-theme optional, disclosed if touched).
- `tests/services/engine/procedures/test_seed_migration_parity.py` — the
  `:50` mirror comment + the AC-5 parity-adapted additions; `:302-324`
  expected to pass unmodified (its where is test-local
  `{event_type: reading}`; `:319` pins battery-01 = event-reading-03, which
  the sub-08:10 seed timing preserves) — VERIFY, don't assume.
- `tests/api/conftest.py` + `test_example_procedures.py` +
  `test_prose_lint.py` (facet prose sync) + `test_env_band_evaluate.py`
  (docstrings citing energy as the env consumer — cosmetic only, the engine
  cases stand).
- Expected UNMODIFIED pins (verify green, touch nothing): `test_recommender.py`,
  `test_recommender_config.py`, `test_demo_events.py`, the
  `eval/golden_traces/*overtemp*` fixtures, `llm/test_prompt.py`,
  `test_structured.py`, `test_intake_extraction.py`, `test_trace.py`,
  `tests/benchmark/*` (dataset-driven).
- The grep sweep (pre-committed, run via the Grep tool): `env_band`,
  `OCT_RECOMMEND_THRESHOLD`, `over-temperature`, `substation_health_sweep`,
  `band_source`, `event-reading-07|event-reading-08`, `== 11` across
  `tests/**` — every hit classified touched / pinned-unmodified in the PR
  body.

**Pass/fail read:** every audited module green; each modified assertion
listed in the PR body with its reason; `git diff main -- services/` empty
(or exactly the SD-5 docstring hunk, if ratified).

### Step 6: PR boundary (SD-1) + full-suite hygiene

Per ratified SD-1. If (a) ONE PR (drafter recommendation): branch
`feat/plan0070-energy-overcurrent`, Steps 2–5 land together with the
RED-verify evidence recorded in the PR body before the Step-4 migration
commit. If Cray diverges to (b) TWO PRs (the s121 + s123 precedent):
**PR1 = Steps 2–3** (seeds + the NL-query count updates + the RED-proven
fixture, xfail/skip-guarded exactly as PLAN-0068 PR1 did) →
**PR2 = Steps 4–5** (the YAML re-theme + every coupled-test update), rebased
on PR1's merge. For each PR: start `vero-postgres` (Docker Desktop, Windows
engine); run the FULL suite via WSL (one pytest per checkout), `ruff check .`,
`ruff format --check .`, `mypy --strict services/`; PR body via `--body-file`
(built with the Write tool), citing the ADR-016 2026-07-12 amendment
(`:1920-1926` — the pre-recorded energy follow-on) + this PLAN; CI `gate`
green; fresh Cray sign-off per merge; re-run the full suite on the merge
commit (CI is PR-only). After merge + Cray closeout: `git mv
docs/plans/0070-*.md docs/plans/done/`. **Pass/fail read:** suite green with
DB up (~123 skips = DB down — restart and rerun); linters clean; CI `gate`
green.

## Surfaced decisions (SD-1 … SD-6 — RATIFIED 2026-07-13, Cray via AskUserQuestion)

**RATIFIED (Cray, 2026-07-13, AskUserQuestion):** **SD-1 = (a) ONE PR** (a Cray
divergence from his own 2-PR precedent on 0067/0068 — accepted the drafter+R2
recommendation given the zero-engine/zero-migration surface); **SD-2 =
as-recommended** (meter-01 rated 80.0 A + inverter-01 rated 722.0 A, batteries
unrated; readings meter-01 84.0 A/warn [the flip] + inverter-01 61.0 A/info; all
< 90 A and < 08:10); **SD-3 = keep** (`restart` handler + `substation_health_sweep`
id kept, goal/descriptions re-themed); **SD-4 = (a) 2-band** (no `watch_margin`);
**SD-5 = (a) keep** the `EnvBandEvaluateExecutor` wrapper + sync the two stale
docstrings (docstring-only `services/` hunk, disclosed); **SD-6 = parity-adapted**
(per-row superset + explicit row-set delta). The recommendations below are now
LOCKED and load-bearing in the Steps + ACs.

The **direction is LOCKED** upstream (Option A re-theme, Cray 2026-07-13) and
the substrate shape is the Accepted ADR-016 FKP amendment — none of that is
re-opened here. These six are the open build-shape calls:

- **SD-1 — one PR or two?** *Recommend: (a) ONE PR.* No engine diff, no
  migration, no regen, no new property — the two-PR rationales of s121 (DB
  migration + first `join:` consumer rollback isolation) and s123 (Cray's
  precedent line) have their thinnest-ever footing here; a single PR carries
  the RED evidence in its own body. **Honest precedent note:** Cray typed (b)
  TWO PRs on BOTH prior occasions (0067 SD-1, 0068 SD-4), each a divergence
  from the drafter's (a) — if Cray holds the line, the Step-6 (b) boundary is
  pre-cut (PR1 seeds+RED / PR2 re-theme). *Why Cray's call:* PR granularity
  is Cray's own established precedent line.
- **SD-2 — seed design: WHICH assets are current-rated, values, and the
  flip.** *Recommend:* rate ONLY `asset-meter-01` ("Feeder Meter A") **80.0**
  and `asset-inverter-01` **722.0** (from its 500 kW nameplate); batteries
  stay unrated (the ontology's own `rated_current_a` description says
  current-rated assets are a subset — `energy_v0.yaml:42-44`); two readings —
  inverter **61.0 A** (08:02, info, ok everywhere) + feeder meter **84.0 A**
  (08:04, warn) = the flip: `ok` under blanket 90, **breach at 105% of its
  own 80 A rating** — the missed-overload class, s121's frozen-cargo /
  s123's tiger-prawn analog. Both values < 90 and both timestamps < 08:10 by
  CONSTRUCTION (drafter finding i — recommender, fail-safe, and demo anchor
  untouched; the thermal climax keeps the final beat). Alternative: 4/4 seed
  completion (the 0067/0068 uniform-substrate precedent) — REJECTED by the
  drafter: it contradicts the ontology's own SD-6/F9 property semantics and
  (without the narrowing where) would band °C readings against ampere
  ratings. *Why Cray's call:* demo-visible domain numbers on the flagship
  vertical — permanent-record bar (the 0067 SD-3 / 0068 SD-2 precedent).
- **SD-3 — the action + naming surface.** *Recommend: KEEP everything named:*
  handler `restart` (a rename to `shed_load`/`trip_breaker` is an **ontology
  enum edit** — `RecommendedAction.action_type`, `energy_v0.yaml:160-163` —
  Out of Scope), procedure_id `substation_health_sweep` (an id rename ripples
  through `test_runs_endpoints.py:33`, `test_procedures_endpoint.py:29`,
  `test_spec.py:684,737` + demo wiring for zero narrative gain), and the
  theme-neutral title "Substation Health Sweep". Re-word ONLY goal/step
  descriptions ("restart the overloaded feeder's breaker after a human
  go/no-go" — restart-after-overload is coherent grid practice). Alternative:
  rename the id to `feeder_overcurrent_sweep` — cleaner grep story, real
  ripple cost; surface only. *Why Cray's call:* demo-facing naming.
- **SD-4 — band shape: 2-band or 3-band?** *Recommend: 2-band* —
  `direction: above`, NO `watch_margin` (mirrors supply_chain; the LOCKED
  lowest-effort-coherent rationale; energy's judge facet is two-verdict
  today). Alternative (b): `watch_margin: 8.0` — watch = [72, 80) on the
  80 A feeder, i.e. ≥90% loading, genuinely good grid semantics
  (`verdict.py:52-57` above-direction watch band) and it would give the
  3-band × threshold_field combination a second consumer after s123 — at the
  cost of new watch-routing test surface. *Why Cray's call:* it fixes the
  verdict vocabulary the energy demo shows.
- **SD-5 — executor wiring + the stale env docstrings.** *Recommend: (a)
  KEEP* `EnvBandEvaluateExecutor(base=…)` (`procedures_factory.py:68`) — the
  shipped `:76-77` guard delegates a `threshold_field` judge through
  untouched (0067 SD-4 (a) precedent; zero factory churn; the
  `test_energy_procedure_factory.py:76-77` isinstance pin survives) — AND
  sync the two now-false prose surfaces: the factory module docstring
  (`procedures_factory.py:17-20` — energy's own file, states the judge is
  env_band) and the **pre-existing** stale `env_band_step.py:6-7` (still
  names `supply_chain.judge` post-#710; after this build the env half has
  zero shipped YAML consumers). The latter is a docstring-only `services/`
  edit — the AC-8 pin is therefore "zero FUNCTIONAL services/ change", with
  this one hunk disclosed (the 0067 spec.py-reword precedent). Alternative:
  (b) swap to the bare `EvaluateStepExecutor` (desyncs the factory shape +
  breaks the isinstance pin — declined in 0067); or leave both docstrings
  stale (rejected: governance-honesty). *Why Cray's call:* it touches
  `services/` prose under a zero-engine-change PLAN.
- **SD-6 — parity posture (first deliberate Q4 SD-C departure).** The strict
  "migrated run reproduces the prior run" parity of 0067/0068 CANNOT hold —
  the narrowing `where` shrinks the sweep by design (that IS the re-theme).
  *Recommend:* the AC-5 parity-adapted pair — per-row superset preservation
  on surviving rows + an EXPLICIT before/after row-set delta assertion — and
  the existing energy parity tests (`test_seed_migration_parity.py:216-324`)
  kept as latest-per-group grammar tests with only their mirror comment
  updated. Alternative: skip parity entirely (rejected — the superset check
  is what caught the s121 collision class). *Why Cray's call:* it sets the
  precedent for what "parity" means when a migration is INTENDED to change
  the row set — future re-themes will cite it.

## Verification

AC-1 by the seed greps + the unmodified recommender/demo/anchor pins +
`git status` (Step 2); AC-2 by the RED-then-GREEN fixture sequence (Steps
3–4 — the flip proven against the unedited YAML first); AC-3/AC-4 by the
load-gate pass + the two `grep -c` = 0 checks (Step 4); AC-5 by the
parity-adapted assertions (Step 4, per SD-6); AC-6 by the in-memory
`run_procedure` (Step 5 — an in-memory run, NOT spec-load-only); AC-7 by the
Step-5 audit with every hit classified in the PR body; AC-8 by the
`git diff main -- services/` check + the unmodified sibling-vertical /
recommender-path pins; AC-9 by the Step-6 full-suite + linter + CI `gate` +
merge-commit re-run. Evidence = fresh pytest/linter output on the branch;
pass/fail reads pre-committed per step (Lesson #0026). **No MS-S1 / no
host-state — the offline oracle is the gate (CLAUDE.md §8).**

## References

- `docs/adr/0016-governed-procedure-engine.md:1675-2109` — the Accepted
  FK-parent amendment; `:1869-1875` FKP-3 fail-loud + "Energy is NOT the free
  second consumer it appears to be on paper"; `:1920-1926` the pre-recorded
  energy change surface this PLAN builds (judge → `rated_current_a`, the
  `event_emitted_by_asset` join, the `site_id` rename, the narrowing-where /
  seed-completion pair); `:2041-2050` SD-4 (energy = labelled follow-on).
- `docs/plans/done/0067-fk-parent-threshold-field-build.md` — the FK-parent
  build shape (RED-verify, coupled audit, SD-4 executor precedent, the
  two-PR Cray divergence); `docs/plans/done/0068-aquaculture-per-species-do-floors.md`
  — the zero-engine-change consumer PLAN this mirrors most closely (SD-0 pure
  build PLAN precedent; the before-the-climax flip-seed timing; the second
  two-PR divergence); `docs/plans/done/0066-threshold-field-per-entity-band-build.md`
  — the `derive_governance_todo` coupling + RED discipline origin.
- `verticals/energy/procedures.yaml:24-31` (grid_agent; `:28` gated ceiling,
  `:31` `action_handlers: [restart]`), `:34-95` (the procedure; goal
  `:36-39`; read_readings `:43-63`; judge `:64-75` — the env facet `:71`;
  restart_breaches `:76-94`; terminal `:95`).
- `verticals/energy/ontology/energy_v0.yaml:40-44` (`rated_current_a` + the
  SD-6/F9 subset semantics), `:54-57` / `:110-112` (the `site_id` collision
  pair), `:93-98` (`ampere`), `:99-101` (`measured_kind: current`),
  `:120-123` (the current/ampere quantity_binding pre-declaring this join),
  `:160-163` (`action_type` enum — why a handler rename is an ontology
  edit), `:205-209` (`event_emitted_by_asset`).
- `verticals/energy/data_adapter/synthetic.py:8-21` (final-beat + recommender
  invariants), `:29-31` (`OVERTEMP_READING_CELSIUS`), `:54-92` (the 4 assets
  — 0/4 rated today; inverter `:66-74`, meter `:84-91`), `:95-240` (11
  events — zero `current` readings today; ids `-07`/`-08` free; the 08:08
  alarm `:215-223`; the 08:10 breach `:224-235`);
  `data_adapter/__init__.py:25-39` (demo_events routing + `_OBJECT_SOURCES`),
  `:99-106` (health_check `object_counts`).
- `verticals/energy/procedures_factory.py:60-70` (`:68` the
  `EnvBandEvaluateExecutor(base=…)` wiring), `:17-24` (the docstring that
  goes stale — SD-5).
- `services/engine/procedures/env_band_step.py:6-7` (the ALREADY-stale env
  consumer list), `:66-77` (the delegate guard — `threshold` OR
  `threshold_field` passes through untouched, shipped #709), `:78-91` (the
  rebind + `band_source: "env"` audit the migrated judge must NOT receive).
- `services/engine/procedures/orchestrator.py:352-395`
  (`_validate_threshold_field_bindings`; `:376-382` FKP-2 union domain;
  `:389-395` c3), `:470-496` (`_validate_join_collisions`; `:479-487`
  join-key exemption; `:490-496` the refusal the `site_id` rename averts).
- `services/engine/procedures/evaluate_step.py:87-93` (band-less guard),
  `:103-116` (per-row band resolution + `classify_verdict`), `:131-139`
  (audit records `threshold_field`); `verdict.py:42-67` (the above-direction
  watch band — SD-4 (b) semantics).
- `services/engine/procedures/draft.py:282-289` (band-aware
  `derive_governance_todo` — the migrated judge owes
  `[threshold_field, direction]`, both authored); `spec.py:356-358` (`where`
  = all-pairs field equality); `query_step.py:150-151,464` (pipeline order:
  where BEFORE latest-per-group — why the narrowing composes).
- `services/api/config.py:186-226` (`oct_recommend_threshold` 90.0 /
  direction / label — the UNTOUCHED recommender knobs);
  `services/engine/demo_events.py:44-67` (the unit-blind anchor selector —
  the < 90 A seed constraint); `services/engine/recommender.py:113-121`
  (the unit-blind escalation trigger).
- `services/db/models.py:21` + `alembic/versions/0009_asset_rated_current_a.py`
  (head = `0011_schedule_states.py`) — the pre-existing DB substrate = why
  NO migration.
- Coupled tests: `tests/verticals/energy/test_energy_procedure_factory.py:39-41,
  76-77,101-117`; `tests/services/engine/procedures/test_spec.py:634-639,
  678-692,737`; `tests/api/test_procedures_endpoint.py:29,134-141`;
  `tests/api/test_runs_endpoints.py:33-34,79-82,111`;
  `tests/services/engine/procedures/test_seed_migration_parity.py:50,216-324`
  (`:319` the battery pin the seed timing preserves);
  `tests/services/engine/test_nl_query.py:655-656,667` (the count-11 pins);
  `tests/benchmark/test_loader.py` (no `load_procedures` — the benchmark
  no-coupling proof).
