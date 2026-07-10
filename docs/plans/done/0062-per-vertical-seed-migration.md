# PLAN-0062: Q4 Phase 3 — per-vertical seed migration onto the declared join/projection grammar (SD-C, parity-guarded)

**Status:** Complete — all 9 ACs met; shipped across PR1 (#672), PR1b (#673), PR2
(#675), PR3 (#676), PR4 (this PR); closed session 117, 2026-07-10. **Two errata are
recorded in the Close-out section below**: ERRATUM 1 (AC-5's "shipped executors" wording
vs the PR1b `EnvBandEvaluateExecutor`) and ERRATUM 2 (fact 7's `read_stock` deferral
reason — observation true, inference false). Ratification lineage: SD-1..SD-6 ratified
as-recommended (Cray, session 116, 2026-07-09, AskUserQuestion); Code R2-verified every
load-bearing citation on disk (facts 3/5/7 confirmed: the sole `StepKind.QUERY`
production wiring is `run.py:244`; real `purchase_order.csv` has no `quote_id` column +
`quotation.csv` carries `part_id`/`price_thb`; real `part.csv` has no
stock_qty/reorder_point — **see ERRATUM 2**). Steps executed directly (§6 "Steps execute
directly"); Code committed per ADR-009 D2.
**Owner:** Claude Code (executes); Cray ratifies the surfaced decisions
**Created:** 2026-07-09
**Related ADRs:** ADR-016 — the **"Amendment (2026-07-09): join/projection grammar for
multi-read query steps (Q4)"** (`docs/adr/0016-governed-procedure-engine.md:1010-1377`,
Accepted) is the authorizing decision; its ratified **Sequencing names this exact PLAN**:
"per-vertical production factory + seed migration (Phase 3, parity-guarded per SD-C)"
(`0016:1196-1199`). This PLAN **executes** SD-C (`0016:1161-1172`) + OQ-3
(`0016:1302-1315`) and needs **NO new ADR**; it reopens no ratified fork. Also:
ADR-0024 D3/D6 (no LLM in the read path — carried), ADR-0025 D5 (SoD — the procurement
`intake` step is SoD-constrained, a hard boundary for SD-5), ADR-006 (Rule-of-Three),
ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (authoring/commit boundaries + disclosure).
**Related PLANs:** PLAN-0061 (`docs/plans/done/0061-join-projection-grammar-build.md` —
the grammar this PLAN authors against; its Step-4 fixtures are the designated authoring
templates, `tests/services/engine/procedures/test_join_fixtures_e2e.py:1-11`); PLAN-0048
(single-read executor + the honest LOCKED-9 frame); PLAN-0046 (the load gate newly-declared
reads route through); PLAN-0047 (governance pin — the fail-closed-at-resume consequence of
editing a shipped YAML); PLAN-0054 (the executor-factory registration precedent,
`verticals/procurement/hero_demo/run.py:542-595`); PLAN-0055 (the scheduled procurement
demo fires through that same factory — a regression surface here).

> **Authorship disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent (ADR-013 D1 phased authority). Outline originator: Cray — the ADR-016 Q4
> amendment's ratified SD-C + Sequencing name this exact Phase-3 migration PLAN, and the
> Phase-3 dispatch is Cray's session-116 next-work pick. Independent review: Code R2
> (every `file:line` citation re-verified on disk against fresh evidence) + Cray at SD
> ratification and PR merge; Code commits per ADR-009 D2 — the drafter does not git.
> Separation: **INTACT**.

> **This is a build PLAN — no new ADR.** The architecture is settled (SD-A/B/C/D +
> OQ-1..4 Accepted). **Tripwire — STOP and surface for an ADR-016 amendment if execution
> finds any of:** (i) a seed shape the two-shape v1 grammar cannot honestly express
> without new spec semantics (do NOT invent grammar — SD-B walls it off), (ii) a need
> for a new StepKind (e.g. a `transform` home for the intake's derived fields — that is
> a future decision, not a Phase-3 build call), or (iii) any inherited LOCK below must
> bend. Never bake a deviation in.

## Goal

Migrate the shipped verticals' hand-written query semantics onto the **declared**
join/projection grammar PLAN-0061 built, each migration guarded by a **run-semantics
parity test** (SD-C: co-exist, no force-retire). Concretely: the three OCT
latest-per-group query steps (energy `read_readings`, supply_chain `read_temps`,
aquaculture `read_do`) gain typed `reads:` + `project:` declarations in their
`procedures.yaml` and run through the generic `QueryStepExecutor(meta=...)` on a real
per-vertical production factory; the procurement `intake` seed's **join half** is proven
grammar-expressible under parity over the REAL hero CSVs (**PARTIAL** per OQ-3 — the
derived compliance/criticality/qty→amount fields stay in the co-existing seed,
execution-bound ✖ per LOCKED-9).

**The honest cost statement (verified fact 1 below):** NO shipped `procedures.yaml`
declares `reads:` at all today — the OCT query steps carry only non-authoritative
`facet.input` prose. Migration is therefore **authoring `reads:` + `project:` from
scratch**, not appending a block to an existing list — and authoring `reads:` newly
routes those procedures through the `validate_read_bindings` load gate on every
production run (`has_read_bindings` currently short-circuits them past it,
`services/engine/procedures/orchestrator.py:213-224`; the gate fires at
`run_procedure` `orchestrator.py:751` and both persisted paths
`services/engine/procedures/persistence.py:113,294`). Everything here is **offline,
deterministic, MS-S1-independent** — no LLM anywhere in the read path (LOCKED-6 /
ADR-0024 D3/D6); the PLAN-0061 SD-6 no-live-run posture is carried verbatim.

## LOCKED (ratified — render faithfully; do NOT re-litigate)

- **L-1 (SD-C, ratified, `0016:1161-1172`).** Seeds **co-exist**; each migration is
  guarded by a run-semantics-**parity** test — the declared-grammar run must produce
  the same step output as the seed on the same fixture. A seed that cannot reach parity
  migrates **partially or stays**, honestly labelled execution-bound ✖ (LOCKED-9). **No
  force-retire.**
- **L-2 (OQ-3, resolved, `0016:1302-1315`).** Grammar = **join + projection (field
  select/rename) ONLY**. The intake's `compliance` dict, criticality amplification, and
  qty→amount (`verticals/procurement/hero_demo/run.py:199-224`) stay in a downstream
  transform step **or the co-existing seed** — and no transform StepKind exists today
  (spec StepKinds = query/evaluate/action/human_task), so the co-existing seed is the
  only home that exists. `intake` migrates **PARTIALLY**: the join half only.
- **L-3 (SD-B, ratified).** v1 = exactly the two shipped shapes. No general
  aggregation; no `nl_query` change (the PLAN-0048 wall stands).
- **L-4 (SD-A + OQ-4, ratified).** Declared-link joins are the governed default;
  explicit `on`/`fuse` overrides are typed escape hatches, **warn-first** at the gate
  when no declared relationship backs the pair (`orchestrator.py:320-322,364-374`).
- **L-5 (PLAN-0061 shipped surfaces — extend, never fork).** The grammar schema
  (`services/engine/procedures/spec.py`: `JoinOn` `:214-225`, `JoinSpec` `:228-278`,
  `ProjectSpec` `:281-320`, `StepInput.join/project` `:365-374`, shape validator
  `:376-397`); the load gate (`orchestrator.py`: `validate_read_bindings(meta=)`
  `:252-308`, `_validate_join_project` `:325-380`, collisions `:383-409`, project
  checks `:412-452`); the compile/execute seam (`services/engine/procedures/query_step.py`:
  `plan_read(meta=)` `:263-346`, `_compile_join_plan` `:167-260`, `JoinReadPlan`
  `:144-165`, `QueryStepExecutor.meta` `:379-456`, `_execute_join` `:458-520`,
  `ReadRefusalKind.JOIN_SHAPE_VIOLATION` `:78`). This PLAN **authors declarations and
  registers factories against** these surfaces; it changes none of them.
- **L-6 (inherited invariants).** `extra="forbid"` on the spec; `where` = engine-side
  post-fetch field-equality only; the single shared `read_bound_violation` predicate at
  BOTH gate and compile (`orchestrator.py:231-249`); one `fetch_objects` dispatch per
  declared read, no repair loop; `join`/`project` are H-governed + pinned (a mid-flight
  edit fails CLOSED at resume — the PLAN-0047/0048/0061 pin machinery); **no LLM in the
  read path**; explicit factory registration only (OQ-6 — no import-scan discovery of
  executor factories, `services/api/main.py:116-126`).

## Substrate facts (verified on disk, 2026-07-09; ontology line-cites for energy carried from the same-day R2-verified ADR/PLAN-0061 record)

1. **No shipped `procedures.yaml` declares `reads:`.** A grep of `reads` across
   `verticals/*/procedures.yaml` matches only prose comments
   (`verticals/{energy,supply_chain}/procedures.yaml:18`). The OCT query steps are
   facet-prose only: energy `read_readings` (`verticals/energy/procedures.yaml:43-51`,
   "latest temperature reading per active Asset"), supply_chain `read_temps`
   (`verticals/supply_chain/procedures.yaml:43-51`, "…per in-transit Shipment"),
   aquaculture `read_do` (`verticals/aquaculture/procedures.yaml:64-72`, "…per active
   Pond"), procurement `read_stock` (`verticals/procurement/procedures.yaml:309-317`,
   "part stock levels").
2. **The declared group links exist for all three OCT verticals** (the SD-A governed
   default is available): energy `event_emitted_by_asset` (FK
   `OperationalEvent.asset_id -> Asset.asset_id`, `energy_v0.yaml:205-209`),
   supply_chain `event_concerns_shipment` (FK
   `OperationalEvent.shipment_id -> Shipment.shipment_id`,
   `supply_chain_v0.yaml:236-240`), aquaculture `event_emitted_by_pond` (FK
   `OperationalEvent.pond_id -> Pond.pond_id`, `aquaculture_v0.yaml:170-174`). PLAN-0061
   AC-1 pinned that every shipped FK parses to typed form.
3. **Production-executor reality: only procurement registers a factory.** A repo grep of
   `StepKind.QUERY` finds exactly ONE production wiring —
   `verticals/procurement/hero_demo/run.py:244` (`StepKind.QUERY: _SeedQuery(seed)`),
   registered active-vertical-scoped at API startup (`main.py:121-126` →
   `register_procurement_procedure_executors`, `run.py:542-595`). Every
   energy/supply_chain/aquaculture query executor in the repo is a **test stub**
   (e.g. `tests/api/test_runs_endpoints.py:96-129`). The OCT procedures are not
   production-runnable today (factory lookup 409s). **The factory maps executors
   per-KIND, not per-step** (`run.py:227-247`) — every procurement QUERY step shares
   `_SeedQuery`.
4. **The `_SeedQuery` docstring stance this PLAN supersedes.** `run.py:129-148`:
   "DEPRECATE-IN-PLACE (PLAN-0048 SD-3) … It stays; **nothing migrates**." SD-C
   (later, Accepted) supersedes that with co-exist + parity-guarded migration — the
   docstring must be updated to cite this PLAN + its parity test.
5. **The intake join half vs the REAL data shape (heavier than the fixture showed).**
   `_intake_seed` (`run.py:183-224`) fuses the singleton failure event (`:189`) + the
   constant hero PO (`:190-191`) and joins quotes on **`part_id`** (`:192`). The REAL
   hero CSVs (`verticals/procurement/data/hero/`): `purchase_order.csv:1` has **NO
   `quote_id` column**, and `quotation.csv:1` carries `part_id`/`price_thb`/
   `lead_time_days` — not the ontology-declared `part_no`/`price`/`lead_time`. So the
   **declared `po_from_quotation` link (FK `PurchaseOrder.quote_id -> Quotation.quote_id`,
   `procurement_v0.yaml:410-414`) cannot execute over the real adapter rows** — the
   PLAN-0061 e2e fixture passed it only by inventing PO rows WITH `quote_id`
   (`test_join_fixtures_e2e.py:154-173`; the offline-fixture-masks-real-shape lesson).
   The real intake join must use the explicit override `on: {left: part_id, right:
   part_id}` — which does NOT warn, because the PO↔Quotation pair IS declared-connected
   (`_pair_is_declared` checks the pair, not the keys, `orchestrator.py:320-322`).
6. **The intake output shape does not flatten.** The grammar emits **flat merged rows**
   (one per join match — PLAN-0061 L-7/AC-5; nesting explicitly out of scope,
   `0061:242-243`), while the seed emits ONE requisition dict with a **nested
   `candidate_quotes` list** (`run.py:193-224`) that the downstream `judge`/`source`
   (scored_rule) consume. Even the join half therefore cannot reach byte-identical
   output parity — parity for intake must be an **information-parity comparator** over
   a pinned field map (SD-5), or a full migration must restructure the hero procedure.
   Additionally `intake` is a **SoD-constrained step id**
   (`verticals/procurement/procedures.yaml:293-297`, ADR-0025 D5) — splitting/renaming
   it ripples SoD + principals.
7. **`read_stock` has no data substrate and needs no grammar.** *(Heading is WRONG —
   **see ERRATUM 2**. The substrate exists on the vertical's REGISTERED adapter; the
   real blocker is the per-kind executor routing this fact's own body names below.)*
   Procurement declares NO
   OperationalEvent→Part link (`procurement_v0.yaml:329-414` — event links go to
   Equipment/Plant only), so there is no `latest_per` link to group by; the ontology
   declares `Part.stock_qty`/`Part.reorder_point` (`:188-193`) but
   `verticals/procurement/data/hero/part.csv:1` carries **neither column** (the HERO
   adapter's CSV — not `ProcurementSyntheticAdapter`, the one the registry serves). As "fetch
   Part rows" it is a PLAN-0048 **single read** (`reads: [Part]`) requiring no
   join/projection at all — and today, run through the registered per-kind factory, it
   would receive the **intake requisition seed** (fact 3), i.e. it has never had a
   faithful implementation anywhere.
8. **Agent allowlists need no edits.** No shipped agent declares
   `allowed.object_types` (e.g. `energy/procedures.yaml:29-31`) — empty =
   **unconstrained** (Q3 OQ-6, `orchestrator.py:242-248`), so authoring `reads:`
   activates the gate's ontology-existence check without requiring allowlist changes.
9. **The governance-pin ripple.** `join`/`project`/`reads` are pinned per step
   (`build_governance_snapshot`; PLAN-0061 AC-2). Editing a shipped YAML changes what
   new runs pin; a **pre-deploy parked (`waiting_human`) run of an edited procedure
   fails CLOSED at resume** (the sanctioned cancel-and-restart). Blast radius today:
   the OCT verticals have no production parked runs (fact 3 — no factories); under the
   SD-5 recommendation procurement's YAML is untouched.
10. **The authoring templates + house semantics.** The PLAN-0061 fixtures are the
    designated authoring examples (`test_join_fixtures_e2e.py`: shape 1 `:85-137`,
    declared-link join `:197-224`, on-override + fuse `:226-288`; the PO∩Quotation
    declared-collision rename map `currency`/`part_no`/`supplier_id` `:147-151`).
    `ProjectSpec.fields` is **rename-only** — unlisted fields are KEPT (`spec.py:304-308`;
    proven at `:137`), so a migrated OCT step emits full event rows. "Latest" = argmax
    `occurred_at` with the SD-5 primary-key tie-break; all four verticals have
    deterministic adapters (`EnergySyntheticAdapter`, `SupplyChainSyntheticAdapter`,
    `AquacultureSyntheticAdapter`, `FastenalCsvAdapter` — the energy adapter's
    `demo_events` real-time anchor must be OFF in parity fixtures,
    `verticals/energy/data_adapter/__init__.py:25-32`).

## Acceptance Criteria

Everything below is **offline and deterministic**, each provable under the required CI
`gate` on a fresh PR (prove main-green via the PR's CI, not a named subset). ACs are
written to the SD recommendations and re-scope mechanically if Cray picks otherwise.

- [x] **AC-1 — the shared parity harness exists.** One test-module helper (SD-3) that
      runs a declared-grammar step through the production `run_procedure` path over a
      supplied adapter + REAL shipped ontology meta and compares the step's output set
      against an **independently hand-coded reference** of the seed semantics —
      order-insensitive, key-complete, zero tolerance (identical rows). Fixtures
      exercise the SD-5 determinism edges: multiple readings per group, an order-by
      tie (primary-key tie-break), and a missing-group-key row (excluded + counted in
      provenance, asserted).
- [x] **AC-2 — energy migrated under parity.** `read_readings` declares
      `reads: [OperationalEvent]` + `project: {latest_per: event_emitted_by_asset,
      order_by: occurred_at}` (+ `where` per SD-4); the shipped YAML passes
      `validate_read_bindings_for_vertical` in a pinned spec test; the parity test is
      green; a full-procedure fixture run (real YAML, fixture adapter, stub action
      client) reaches the gated `restart_breaches` suspension — the migrated step feeds
      `judge` in situ; the `facet.input` prose is synced to the typed truth (D2-A2).
- [x] **AC-3 — supply_chain migrated under parity.** Same as AC-2 for `read_temps` over
      `event_concerns_shipment`.
- [x] **AC-4 — aquaculture migrated under parity.** Same as AC-2 for `read_do` over
      `event_emitted_by_pond` (the breach/watch/ok three-band judge downstream).
- [x] **AC-5 — per-vertical production factories registered (SD-2).** The three OCT
      verticals gain explicit, idempotent, deterministic executor-factory registrations
      (`QueryStepExecutor(adapter, object_type_names, meta=...)` + the shipped
      evaluate/action executors with the advisory-stub client — the
      `register_procurement_procedure_executors` pattern, `run.py:542-595`), wired
      active-vertical-scoped at API startup (`main.py:116-126` generalized). A migrated
      OCT procedure is then declared ✔ · gated ✔ · **execution-bound ✔ on the production
      HTTP path**, not just in tests.
- [x] **AC-6 — procurement intake: the join half proven under parity, PARTIAL per
      OQ-3.** A shadow-parity test (SD-5) runs the declared join-half —
      `reads: [OperationalEvent, PurchaseOrder, Quotation]`, `where: {event_type:
      failure}`, `fuse` the hero PO, `on: {left: part_id, right: part_id}` for quotes
      (fact 5) — over the **REAL `FastenalCsvAdapter`** and asserts information-parity
      against `_intake_seed`'s join-half fields via a pinned field map (po/part/asset
      ids, qty, and per-quote quote_id/supplier_id/price/currency/lead-time/on-contract
      — `price_thb`→`unit_price` normalization included). The derived fields
      (`compliance`, criticality amplification, qty→amount) are asserted **absent** from
      the grammar output (the OQ-3 boundary made executable). The `_SeedQuery`
      docstring's "nothing migrates" stance (`run.py:134-140`) is replaced with the
      SD-C co-exist + this parity citation. The production factory, hero YAML, hero
      audit contract, and scheduled-demo path are **byte-unchanged**.
- [x] **AC-7 — `read_stock` disposition recorded (SD-1).** Per the recommendation:
      deferred with the honest reason (fact 7 — no substrate, no grammar need) recorded
      in this PLAN's close-out + the step's facet note; zero code. (If Cray ratifies
      migrate-now instead: `reads: [Part]` single-read + a fixture parity test, and the
      factory's per-step routing joins SD-2's scope.)
- [x] **AC-8 — no regression + pin disclosure.** Full offline suite green (incl. the
      PLAN-0046/0047/0048/0054/0055/0061 suites untouched); the hero-demo contract and
      `test_scheduled_procurement_demo` byte-unchanged; each YAML-editing PR body
      discloses the governance-pin consequence (fact 9: pre-deploy parked runs of an
      edited procedure refuse at resume — cancel-and-restart).
- [x] **AC-9 — offline gate green, no live anything.** Suite + ruff + ruff-format +
      `mypy --strict services/` green under CI `gate` on fresh PRs; **no MS-S1 / live-LLM
      call anywhere** (the PLAN-0061 SD-6 posture carried; nothing non-deterministic
      exists to confirm).

## Out of Scope

- ❌ **The intake derived fields** (`compliance` / criticality amplification /
  qty→amount, `run.py:199-224`) — L-2/OQ-3; they stay in the co-existing seed,
  execution-bound ✖ per LOCKED-9. No transform StepKind is invented (tripwire ii).
- ❌ **Retiring `_SeedQuery` / restructuring the hero procedure** — SD-C co-exist; the
  intake step id is SoD-load-bearing (fact 6).
- ❌ **General aggregation / `nl_query` unification** (SD-B; the PLAN-0048 wall).
- ❌ **Any grammar/spec/gate/executor change** — L-5; a shape the grammar cannot express
  is the tripwire, not a build call.
- ❌ **Ontology YAML changes** (e.g. adding `quote_id` to the PO CSV or a
  PurchaseOrder→Quotation part-keyed link to "fix" fact 5) — data/ontology evolution is
  its own decision, not smuggled into a migration PLAN.
- ❌ **Any live / MS-S1 run** (SD-6 posture carried; CLAUDE.md §8).
- ❌ **The PLAN-0004 / PLAN-0010 / PLAN-0012 filing decisions** (out of this PLAN's
  lane entirely).
- ❌ UI / `GET /meta` consumption of the migrated declarations; vet_clinic (parked, no
  procedures.yaml in the N=4 migration set).

## Surfaced Decisions

Build-level forks only — the direction (SD-C co-exist + parity, OQ-3 partial intake) is
LOCKED. Each SD carries a recommendation; **Cray ratifies via AskUserQuestion**; none is
silently decided.

- **SD-1 — the v1 migration set.**
  *Recommendation:* the three OCT latest-per-group steps (energy, supply_chain,
  aquaculture) + the procurement intake **join half** (shadow-parity per SD-5).
  **`read_stock` is DEFERRED**: it needs no join/projection grammar (a `reads: [Part]`
  single read), its data substrate is absent (fact 7 — `part.csv` has no
  stock_qty/reorder_point — **see ERRATUM 2**), and there is no seed to parity against (it has never run
  faithfully anywhere — fact 3/7). Migrating it now would be declaration theater.
  *Alternatives:* (i) include `read_stock` as a plain single-read declaration + fixture
  parity — cheap but unfalsifiable against production data; (ii) OCT-only, defer all of
  procurement — rejected: the ADR names the intake join half as the Phase-3 centerpiece.
  *Why Cray:* the migration set is the demo-visible surface area of Phase 3.
- **SD-2 — the per-vertical production-factory shape (replace, no flag).**
  *Recommendation:* register explicit deterministic factories for the three OCT
  verticals (AC-5), mirroring `register_procurement_procedure_executors` — idempotent,
  active-vertical-scoped at startup, advisory-stub LLM client (no MS-S1), explicit
  registration per OQ-6. **Replace, not flag-gated co-exist:** the OCT verticals have
  NO existing production query executor to co-exist with (fact 3 — a factory lookup
  409s today), so there is nothing to put behind a flag; SD-C's co-existence applies to
  *seeds*, and the only production seed (`_SeedQuery`) stays untouched. The procurement
  factory is byte-unchanged under SD-5(b).
  *Alternatives:* (i) tests-only, no factories — smaller, but leaves the migrated
  declarations with no production consumer (execution-bound ✔ only in tests) and defies
  the ADR Sequencing's "per-vertical production factory" (`0016:1196-1199`); (ii) a
  feature flag per vertical — doubles the surface for zero co-existence benefit.
  *Why Cray:* this makes three more verticals live-runnable over HTTP — an operational
  surface change, not a drafter call.
- **SD-3 — the parity-harness shape.**
  *Recommendation:* one shared helper in a committed test module (house gotcha honored:
  nothing under `docs/plans/` — G2 fires on non-plan docs there): run the real shipped
  YAML step through `run_procedure` over a fixture adapter + real ontology meta; the
  reference implementation is hand-coded **in the test, independently of the executor**
  (argmax `order_by` per FK group key, max-primary-key tie-break) so grammar and
  reference can only agree by computing the same semantics. OCT fixtures =
  test-module rows (SD-5-edge coverage per AC-1) + one secondary parity run over the
  real deterministic synthetic adapter (anchor OFF — fact 10); procurement = the real
  `FastenalCsvAdapter` for BOTH paths (seed and grammar), the strongest honest fixture
  (real CSVs, deterministic, offline).
  *Alternatives:* golden-file snapshots (opaque drift, no semantics); re-using the
  executor's own `_latest_per_group` as the reference (circular — parity would prove
  nothing).
  *Why Cray:* the comparator IS the SD-C guard's meaning; its strictness is the
  migration's safety property.
- **SD-4 — the literal OCT declarations (and the "active/in-transit" prose qualifier).**
  *Recommendation:* per vertical, `reads: [OperationalEvent]` + `where: {event_type:
  reading}` (pin the exact event_type per vertical's synthetic data at build) +
  `project: {latest_per: <declared link>, order_by: occurred_at}`, **no `fields` map**
  (rename-only semantics keep all event fields — fact 10; `measured_value` flows to the
  judge unchanged). **Do NOT encode the "active Asset"/"in-transit Shipment" qualifier
  as a parent-type join in v1**: no implementation of that qualifier exists anywhere
  today (fact 3 — the prose was aspiration, not behavior), and adding a status-filter
  join would change semantics under a PLAN whose contract is parity. Sync the
  `facet.input` prose to the typed declaration (D2-A2: typed fields are the source of
  truth) and note the dropped qualifier honestly. No `allowed.object_types` opt-in in
  this PLAN (fact 8; future hardening).
  *Alternatives:* (i) join the parent type + `where: {status: active}` — expressible,
  but invents behavior with no seed to parity against and adds collision-rename burden;
  (ii) keep the prose as-is while the typed field contradicts it — dishonest surface.
  *Why Cray:* this fixes the demo-visible read semantics of all three OCT demos and
  edits their governed YAML.
- **SD-5 — intake partial-migration mechanics: shadow-parity (b), not a step split (a).**
  *Recommendation:* **(b) shadow-parity.** Production `intake` stays `_SeedQuery` (the
  OQ-3 co-existing seed — the only existing home for the derived fields, L-2); the hero
  YAML gains no join declaration; the AC-6 test proves the join half is
  grammar-expressible + information-identical over the real CSVs. Honest frame after:
  intake = declared-expressible ✔ (proven) · production execution via seed ·
  execution-bound ✖ for the derived fields (LOCKED-9 — no over-claim). The docstring
  supersede (AC-6) records the SD-C stance.
  *Alternative:* **(a) split** intake into a declared-join query step + a seed transform
  step threading `from:` — full YAML migration of the join half, BUT: the executor map
  is per-KIND so both steps would hit the same QUERY executor (needs a per-step router),
  the flat-rows→nested-`candidate_quotes` reshape still needs the seed (fact 6), the
  SoD constraint names `intake` (fact 6 — renaming ripples ADR-0025 D5 + principals),
  and the hero demo + scheduled demo + governance pin all move. High demo-visible risk
  for the same parity evidence.
  *Why Cray:* the hero demo is the flagship; whether its governed YAML changes at all is
  Cray's risk call, not a drafter default.
- **SD-6 — phasing: one PR per vertical (mirrors PLAN-0061 SD-2).**
  *Recommendation:* four PRs — **PR1** harness + energy (AC-1/2 + energy's slice of
  AC-5), **PR2** supply_chain, **PR3** aquaculture, **PR4** procurement shadow-parity +
  docstring + `read_stock` disposition + close-out (AC-6/7/8). Each green under CI
  `gate`; per-vertical parity = per-PR review boundary.
  *Alternative:* two PRs (the three mechanically-identical OCT verticals together +
  procurement) — fewer boundaries, acceptable if Cray prefers speed over per-vertical
  revertability.
  *Why Cray:* phase boundaries = review boundaries (the 0061 precedent).

## Steps

Build order = cheapest gate first; the suite stays green at every boundary. (Step
granularity follows SD-6's recommendation; re-cut mechanically if Cray picks two PRs.)

### Step 1 — PR1: parity harness + energy (AC-1, AC-2, energy factory of AC-5)
The shared harness helper + SD-5-edge fixtures; declare `reads`/`project` on
`read_readings` per SD-4; pinned all-shipped-YAMLs-pass-the-gate spec test; energy
parity green (fixture rows + the real `EnergySyntheticAdapter` with anchor off);
full-procedure fixture run to the `restart_breaches` suspension;
`register_energy_procedure_executors` + the generalized startup wiring
(`main.py:116-126`); facet prose sync; PR body discloses the pin consequence (fact 9).

### Step 2 — PR2: supply_chain (AC-3 + its AC-5 slice)
Same shape over `event_concerns_shipment`; `read_temps`; the cold-chain judge
downstream; factory + prose + disclosures as Step 1.

### Step 3 — PR3: aquaculture (AC-4 + its AC-5 slice)
Same shape over `event_emitted_by_pond`; `read_do`; the three-band breach/watch/ok
judge + watch-escalation path downstream (the richest in-situ check); factory + prose +
disclosures as Step 1.

### Step 4 — PR4: procurement shadow-parity + close-out (AC-6, AC-7, AC-8)
The AC-6 shadow-parity test over the real `FastenalCsvAdapter` (fuse + `on: part_id`,
the pinned field map, the derived-fields-absent assertion, `ProcedureWarning` handled
per the fixture precedent `test_join_fixtures_e2e.py:246-253`); the `_SeedQuery`
docstring supersede; the `read_stock` deferral note (AC-7); the byte-unchanged sweeps
(hero contract, scheduled demo); STATUS reconcile. Conventional commits
`feat(verticals): …` / `test(engine): …` referencing PLAN-0062; Code commits via PR per
CLAUDE.md §7 (ADR-009 D2).

## Verification

**Binding — and complete: the offline oracle is the entire bar** (the PLAN-0061 SD-6
posture carried; there is no LLM in the read path, so nothing non-deterministic exists
to confirm — no host-state action, no §8 gate, no live evidence note). The AC matrix
runs under the required CI `gate` on fresh PRs. The parity property is the heart:
grammar-vs-independent-reference identity on OCT fixtures; grammar-vs-seed
information-parity on the real procurement CSVs. **Honest enforcement frame after this
PLAN (LOCKED-9):** the three OCT query steps become declared ✔ · gated ✔ ·
execution-bound ✔ on the production path; procurement `intake` = join half proven
grammar-expressible under parity, production execution stays the co-existing seed,
derived fields execution-bound ✖; `read_stock` = deferred, labelled. Nothing may claim
more.

## Close-out (session 117, 2026-07-10)

Evidence at close: full offline suite 2496 passed / 7 skipped; ruff + ruff-format +
`mypy --strict services/` clean; every PR green through the required CI `gate`;
**MS-S1 never touched** (the SD-6 / PLAN-0061 no-live-run posture held end to end).
Shipped: PR1 (#672) shared parity harness
(`tests/services/engine/procedures/test_seed_migration_parity.py`) + energy
`read_readings` migrated + the 4-vertical load-gate pin; PR1b (#673)
`services/engine/procedures/env_band_step.py` (`EnvBandEvaluateExecutor`) +
`services/engine/procedures/advisory_stub.py` + `verticals/energy/procedures_factory.py`
+ the `main.py` per-vertical registrar table; PR2 (#675) supply_chain `read_temps` over
`event_concerns_shipment` + `verticals/supply_chain/procedures_factory.py` (harness
became vertical-parameterised); PR3 (#676) aquaculture `read_do` over
`event_emitted_by_pond` + `verticals/aquaculture/procedures_factory.py`, binding the
SHIPPED `EvaluateStepExecutor` unwrapped (`in_file_band`); PR4 (this PR)
`tests/verticals/procurement/test_intake_shadow_parity.py` (8 tests) + the `_SeedQuery`
docstring supersede + the `read_stock` facet note.

### Honest enforcement frame — the binding claim, no more

The three OCT query steps (energy `read_readings`, supply_chain `read_temps`,
aquaculture `read_do`) are **declared ✔ · load-gated ✔ · execution-bound ✔ on the
production HTTP path**. procurement `intake` is **declared-expressible ✔ (proven under
shadow parity)** but its production execution stays the co-existing `_SeedQuery`; it
remains **execution-bound ✖ for the derived fields** (`compliance`, the `criticality`
amplification, the nested `candidate_quotes` reshape) — LOCKED-9. `read_stock` is
**deferred**, labelled (reason corrected — ERRATUM 2). Nothing may claim more.

### ERRATUM 1 — AC-5's wording vs what PR1b shipped

- The PLAN's `## Out of Scope` says "❌ **Any grammar/spec/gate/executor change** —
  L-5", and **AC-5** says the factories bind "the **shipped** evaluate/action
  executors".
- PR1b (#673) added a **new** engine module,
  `services/engine/procedures/env_band_step.py::EnvBandEvaluateExecutor`. So AC-5's
  wording is **not literally satisfied**.
- Why it was nonetheless the right build: **AC-2 requires a full-procedure run to the
  gated suspension**, and energy's `judge` is an ADR-016 D2-A3 `env_band` (band from
  `OCT_RECOMMEND_THRESHOLD`, **no in-file `threshold`**) which the shipped
  `EvaluateStepExecutor` refuses (`evaluate_step.py` raises on a band-less step). AC-2
  is unreachable without an env-band evaluate executor. L-5's *enumerated* surfaces are
  the **grammar stack only** — `spec.py` `JoinOn`/`JoinSpec`/`ProjectSpec`/
  `StepInput.join|project`, the `orchestrator.py` load gate, and `query_step.py`'s
  compile/execute seam — none of which PR1b touched.
- **Cray ratified the engine-module home** (session 117, AskUserQuestion) after Code
  surfaced the tension; the thin-executor direction was approved in session 116.
  Disclosed in the #673 PR body, not silently reinterpreted.
- The executor is a **delegating wrapper**: it binds the env band onto a band-less step
  and hands it to the shipped base, so `verdict.classify_verdict` remains the single
  band definition (extend, never fork). It does **not** read `facet` — ADR-016
  **D2-A4** keeps `facet` schema-only; the vertical's **factory** selects the executor,
  and the executor's only trigger is the typed `Step` (`threshold is None`).

### ERRATUM 2 — fact 7 / AC-7's stated reason for the `read_stock` deferral was wrong

- The PLAN's Status header (Code R2) and the SD-1 recommendation assert the deferral is
  because "its data substrate is absent (fact 7 — `part.csv` has no
  stock_qty/reorder_point)", and AC-7 records "the honest reason (fact 7 — no
  substrate, no grammar need)".
- **The observation is true but the inference is false.** `part.csv` belongs to
  `FastenalCsvAdapter`, which is the **hero demo's** adapter, constructed explicitly.
  The vertical's **registry-registered** adapter is `ProcurementSyntheticAdapter`,
  whose `Part` rows **do** carry `stock_qty` and `reorder_point` — and the ontology
  **declares** both (`Part.stock_qty`, `Part.reorder_point`). A `reads: [Part]`
  declaration would resolve at the load gate today. **Cray ratified SD-1 on this false
  premise.**
- **The true blocker is executor routing, not data.** The procurement factory binds
  executors **per `StepKind`** (`verticals/procurement/hero_demo/run.py::_executors`),
  and its `QUERY` executor is the fixed `_SeedQuery` intake seed. The orchestrator
  resolves an executor by `executors.get(step.kind)`. So a declared `read_stock` would
  pass the gate and still be handed the intake requisition at run time: **declared ✔ /
  execution-bound ✖**, and actively misleading. Honest migration needs a **per-step
  QUERY router**, which SD-2's ratified scope excludes.
- **This was summary drift, not bad analysis.** Fact 7's *body* already said it —
  "today, run through the registered per-kind factory, it would receive the **intake
  requisition seed** (fact 3), i.e. it has never had a faithful implementation
  anywhere" — and it correctly noted that the ontology *does* declare both columns. The
  routing reason then fell out of the fact's own **heading** ("`read_stock` has no data
  substrate"), and every downstream restatement — SD-1's recommendation, AC-7, the
  Status header's R2 note — carried the heading forward and dropped the body. **A
  compression step, not the research, introduced the error.** The generalisable guard:
  when a fact is restated in a decision line, re-read the fact's **body**, not its title.
- **Disposition, Cray-ratified session 117 (AskUserQuestion): keep the deferral,
  correct the reason.** Zero code. The corrected reason is recorded in the step's facet
  note (`verticals/procurement/procedures.yaml`, `read_stock`) and pinned as an
  **executable invariant** —
  `tests/verticals/procurement/test_intake_shadow_parity.py::test_read_stock_substrate_exists_the_plan_fact_7_erratum`
  and `::test_read_stock_is_blocked_by_per_kind_executor_routing_not_by_data`. When a
  per-step router ships, that second test fails and the deferral falls due.
- **Method note worth carrying:** the R2 pass verified the *file* the fact named
  (`part.csv`) and not the *adapter the vertical actually registers*. A citation can be
  literally correct and still support a false conclusion.

### What PR4 proved about `intake` (AC-6)

The declared join half — `reads: [OperationalEvent, PurchaseOrder, Quotation]`,
`where: {event_type: failure}`, `fuse` the hero PO, quotes `on: {left: part_id, right:
part_id}` — runs through the production `run_procedure` path over the **real
`FastenalCsvAdapter`** and is **information-identical** to `_intake_seed`'s join-half
fields (`price_thb`→`unit_price` normalisation included, compared as `Decimal`). It
emits **three flat rows** (one per quote), never the nested reshape, and **none** of
the derived fields. A further drift is pinned: the ontology declares
`PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id` while the
real CSVs emit `part_id` / `price_thb` / `asset_id`; the load gate checks **declared**
properties while the executor merges **runtime** keys, so the declaration renames the
four declared `PurchaseOrder`∩`Quotation` collisions (`currency` · `part_no` ·
`quote_id` · `supplier_id`) even though only `supplier_id` collides at runtime — and
that rename is what preserves each quote's own supplier.

### AC-8 pin disclosure (fact 9)

The hero procedure block, the hero audit contract, the production factory, and the
scheduled-demo path are **byte-unchanged**; the only
`verticals/procurement/procedures.yaml` change is the AC-7 facet note on the calm-path
`read_stock` step. Governance-pin consequence: a pre-deploy parked run of an **edited**
procedure refuses at resume — cancel-and-restart.

### Follow-ups this PLAN deliberately leaves open

- (i) A per-step QUERY router for procurement, which would make `read_stock` migratable
  and reopen AC-7.
- (ii) The procurement ontology↔CSV column drift (`part_no`/`part_id`,
  `price`/`price_thb`, `equipment_id`/`asset_id`) — data/ontology evolution, explicitly
  out of this PLAN's scope.

## Open Questions (build-level; settle at step review — never silently)

- **OQ-1 —** the OCT factories' action-executor client: the advisory-stub factory (the
  procurement precedent, recommended — deterministic, MS-S1-free) vs a settings-gated
  real client passthrough. Settle at Step 1 review.
- **OQ-2 —** each vertical's exact `where` narrowing (`event_type: reading` vs no
  narrowing) — pin against the synthetic datasets at build; the parity fixture encodes
  whichever is pinned.
- **OQ-3 —** whether the pinned all-YAMLs-pass-the-gate test lives in `test_spec.py`
  (beside the existing shipped-spec sweep, `:616-669`) or the parity module. Cosmetic;
  settle at Step 1 review.

## Size estimate

**M.** Four contained PRs: one harness + three mechanically-similar YAML+factory+parity
slices, and one test+docs procurement PR. No engine changes (L-5), no ontology changes,
no live runs; blast radius bounded by the byte-unchanged sweeps (AC-8) and per-vertical
revertability (SD-6).

---

*PLAN-0062 drafted by the in-harness `plan-drafter` subagent (2026-07-09), ADR-013 D1
phased governance authoring (ADR-009 D1). It executes the Accepted ADR-016 Q4
amendment's SD-C + OQ-3 (Phase 3, `0016:1161-1172`, `:1196-1199`, `:1302-1315`) — no
ratified fork is reopened; six build-level forks are surfaced (SD-1..SD-6) with
recommendations, none silently decided. Author≠reviewer (ADR-012 D4.3): drafter =
plan-drafter; reviewers = Code R2 (every citation re-verified on disk) + Cray at SD
ratification (AskUserQuestion) and PR merge — separation INTACT. Drafted uncommitted;
Code commits via a `docs/*` PR (ADR-009 D2); the drafter does not git. AI-assisted
(plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
