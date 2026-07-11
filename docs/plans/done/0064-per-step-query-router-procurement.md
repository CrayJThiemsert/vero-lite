# PLAN-0064: Per-step QUERY routing for procurement — migrate `read_stock` onto the shipped executor, reopen PLAN-0062 AC-7

**Status:** Complete — all 8 ACs shipped in ONE PR (#696, `75ed717` → merge `fdd6a9b`,
2026-07-11, session 118; gate-green). Close-out below. PLAN-0062 AC-7's deferral is
**discharged by reference** (AC-6) — no ratified 0062 line edited.
**Owner:** Claude Code (executes); Cray ratifies the surfaced decisions
**Created:** 2026-07-11
**Origin:** Cray picked this candidate as the #1 next-work item (session 118,
2026-07-11, via AskUserQuestion after the next-work-analyst ranking; option
"Router + hygiene"). It is the top-ranked follow-up from PLAN-0062's close-out —
**ERRATUM 2** established that `read_stock`'s true deferral reason is per-`StepKind`
executor routing, NOT missing data, and PLAN-0062's own follow-ups list names
"a per-step QUERY router for procurement, which would make `read_stock` migratable
and reopen AC-7" (`docs/plans/done/0062-per-vertical-seed-migration.md:536-539`).
**Related ADRs:** ADR-016 — the Q3 typed-reads contract + the Q4 grammar amendment
govern the declared read this PLAN activates; critically, ADR-016 itself records
that a vertical's executor supply is "an **undocumented operational expectation,
not an engine contract**" (`docs/adr/0016-governed-procedure-engine.md:511-513`),
and the Q4 amendment's scope-boundary OUT-list pins the grammar stack, not the
executor-map shape (`0016:1233-1247`) — the basis for SD-0. Also ADR-0024 D3/D6
(no LLM in the read path — carried, LOCKED), ADR-0025 D5 (SoD — `intake` untouched),
ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (authoring/commit boundaries + disclosure).
**Related PLANs:** PLAN-0062 (ERRATUM 2 — the origin; its ratified lines are NOT
reworded, see AC-6); PLAN-0048 (the shipped single-read `QueryStepExecutor` this
step migrates onto); PLAN-0061 (grammar + load gate); PLAN-0047 (executor-factory
registration + governance pins); PLAN-0054/0055 (hero + scheduled demo — the
regression surfaces this PLAN must leave byte-unchanged).

> **Authorship disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent (ADR-013 D1 phased authority). Outline originator: Cray — the session-118
> next-work pick; the dispatch fact-pack was Code-verified 2026-07-11 against
> main = 3f7b22c, and the drafter re-verified every load-bearing citation on disk
> before building on it. Independent review: Code R2 + Cray at SD ratification and
> PR merge; Code commits per ADR-009 D2 — the drafter does not git.
> Separation: **INTACT**.

> **This is a build PLAN — no new ADR (per SD-0's recommendation; Cray ratifies).**
> **Tripwire — STOP and surface for an ADR-016 amendment if execution finds any
> of:** (i) the delegating-wrapper shape (SD-1/SD-2) cannot deliver per-step routing
> without changing the orchestrator's `Mapping[StepKind, StepExecutor]` contract
> (`orchestrator.py:714-717`, `:784-786`), the registry's `ExecutorFactory` type
> (`services/engine/registry.py:30`), or any spec/grammar surface; (ii) a new
> `StepKind` or new grammar field is needed; (iii) any inherited LOCK below must
> bend. Never bake a deviation in.

## Goal

Give the procurement executor factory **per-step QUERY routing** so the calm-path
`read_stock` step can be honestly migrated onto the **shipped** generic
`QueryStepExecutor` (declared `reads: [Part]`, PLAN-0048 single-read — no new query
surface, no grammar change, no LLM), closing the gap PLAN-0062 ERRATUM 2 named:
today a declared `read_stock` would pass the load gate and still be handed the
intake requisition seed at run time — declared ✔ / execution-bound ✖, actively
misleading. After this PLAN, `read_stock` is **declared ✔ · gated ✔ ·
execution-bound ✔** through the production factory over the vertical's
registry-registered adapter, `intake` continues to run the co-existing `_SeedQuery`
byte-identically (PLAN-0062 SD-C — no force-retire), and the PLAN-0062 AC-7
deferral is reopened and discharged **by this PLAN's own ACs** (0062's ratified
text is never edited). Everything is **offline, deterministic, MS-S1-independent**;
CI `gate` is the binding bar.

## LOCKED (inherited — render faithfully; do NOT re-litigate)

- **L-1 (ADR-0024 D3/D6; dispatch LOCKED-6).** No LLM anywhere in the read path.
  `read_stock` migrates onto the SHIPPED declared-grammar executor — no new query
  surface.
- **L-2 (PLAN-0062 SD-C, ratified).** Seeds co-exist; no force-retire. `_SeedQuery`
  stays in production for `intake`; its derived fields remain execution-bound ✖
  (LOCKED-9 honest labelling). This PLAN adds routing AROUND it, never through it.
- **L-3 (OQ-6 / PLAN-0047).** Explicit factory registration only — no import-scan
  discovery of executor factories (`services/api/main.py:125-133`).
- **L-4 (PLAN-0061/0048 pin machinery).** `reads` is H-governed + pinned; editing a
  shipped `procedures.yaml` changes what new runs pin — a pre-deploy parked run of
  an EDITED procedure fails CLOSED at resume (disclose per AC-8; the sanctioned
  cancel-and-restart).
- **L-5 (PLAN-0062 ratified lines).** 0062's text — including its ERRATUM 2 and
  AC-7 — is history, not an editable surface. Reopening happens by cross-reference
  from THIS PLAN.

## Substrate facts (drafter re-verified on disk, 2026-07-11)

1. **Executor resolution is per-KIND.** `orchestrator.py:818` — `executor =
   executors.get(step.kind)`; both `run_procedure` (`:714-717`) and `execute_steps`
   (`:784-786`) take `executors: Mapping[StepKind, StepExecutor]`, and the
   persisted/resume paths thread the same mapping
   (`services/engine/procedures/persistence.py:89-93`; gate-resolve resumes via
   `registry.get_procedure_executors("procurement")`,
   `verticals/procurement/hero_demo/run.py:560-562`). One executor serves EVERY
   query step of a vertical's procedures.
2. **Procurement's QUERY slot is the fixed `_SeedQuery`.** `run.py:129-160` (frozen
   dataclass returning the pre-assembled intake requisition); the per-kind dict is
   built in `_executors()` (`run.py:239-259`, `StepKind.QUERY: _SeedQuery(seed)` at
   `:256`) and registered per-vertical at `run.py:601-607`. The registrar table:
   `services/api/main.py:97-133`.
3. **The extend-not-replace wrapper precedent is documented engine style.** The
   procurement EVALUATE/ACTION slots already do per-step dispatch INSIDE one kind
   slot via delegating wrappers: `GovernanceActionExecutor`
   (`services/engine/procedures/governance_step.py:118-138`) and
   `GovernanceEvaluateExecutor` (`:262-282` — "The orchestrator's
   ``StepKind``-keyed contract is untouched (extend not replace, LOCKED #5)",
   `:270-271`). The engine-module home for a vertical-triggered delegating executor
   was Cray-ratified at PLAN-0062 ERRATUM 1 (`env_band_step.py`).
4. **The other three verticals bind the shipped `QueryStepExecutor` — still
   per-KIND.** e.g. energy `verticals/energy/procedures_factory.py:60-70` (QUERY at
   `:65-67`, bound to `registry.get_adapter(_VERTICAL)` + `load_ontology_meta`).
5. **`read_stock` + its corrected deferral note.**
   `verticals/procurement/procedures.yaml:309-324` (the 16-line note already states
   the routing reason and names the tripwire test); the step itself `:325-335`
   (kind: query, facet note "the procurement factory lacks per-step QUERY
   routing"). Downstream: `judge_stock` `:336-352` (in_file_band, threshold 100.0,
   direction below), `reorder` `:353+`.
6. **The data substrate EXISTS (ERRATUM 2).** Ontology declares `Part.stock_qty` +
   `Part.reorder_point` (`verticals/procurement/ontology/procurement_v0.yaml:188-193`);
   the registry-registered `ProcurementSyntheticAdapter` emits both on both Part
   rows (`verticals/procurement/data_adapter/synthetic.py:173-197`; values at
   `:182-183`, `:192-193`). The hero `FastenalCsvAdapter`'s `part.csv` does NOT —
   it is not the vertical's registered adapter (pinned by the substrate test,
   fact 8).
7. **The tripwire oracle — this PLAN intentionally flips it.**
   `tests/verticals/procurement/test_intake_shadow_parity.py:275-292`
   (`test_read_stock_is_blocked_by_per_kind_executor_routing_not_by_data`) pins the
   per-kind map (`dict[StepKind, ...]` with `_SeedQuery` as QUERY) and its
   docstring says: when per-step routing ships, "this fails, and the AC-7 deferral
   falls due for revisit." Per its own design it must be REWRITTEN to pin the new
   contract (SD-4), never deleted or skipped.
8. **The companion data-half test stays green untouched.** `:253-272`
   (`test_read_stock_substrate_exists_the_plan_fact_7_erratum`) — asserts ontology
   declaration + registered-adapter emission.
9. **The downstream judge bounds the honest claim.** The shipped
   `EvaluateStepExecutor` reads `measured_value`
   (`services/engine/procedures/evaluate_step.py:40`) and an entity without a
   numeric reading **fails the step loudly** (D4 fail-and-divert; `:21-27`,
   `:49-65`). Raw Part rows carry `stock_qty`, not `measured_value` — so migrating
   `read_stock` alone does NOT make `low_stock_reorder_round` end-to-end runnable.
   (A fields-only rename projection IS spec-expressible — `ProjectSpec` permits
   `fields` without `latest_per`, `spec.py:310-320` — but that is a semantics
   decision, SD-3.)
10. **The load-gate side is already paved.** `reads` is the typed Q3 entry point
    (`spec.py:360-364`); `validate_read_bindings_for_vertical` fires on every
    production run (`orchestrator.py:751`, `persistence.py:113`); the 4-vertical
    all-shipped-YAMLs load-gate pin shipped in PLAN-0062 PR1, so a newly declared
    `reads: [Part]` must keep that sweep green. The procurement agent declares
    `allowed.step_kinds` but no `object_types` read-allowlist
    (`procedures.yaml:46-48`) — empty = unconstrained (LOCKED-5/OQ-6); confirm at
    build.

## Acceptance Criteria

All offline + deterministic, provable under the required CI `gate` on a fresh PR.
ACs are written to the SD recommendations and re-scope mechanically if Cray picks
otherwise.

- [x] **AC-1 — the router exists and is unit-pinned.** A delegating QUERY-slot
      router (home per SD-2, dispatch rule per SD-1) implementing the plain
      `StepExecutor` protocol: a step WITH declared `reads` dispatches to the
      wrapped declared-grammar executor; a step WITHOUT dispatches to the wrapped
      fallback. Unit tests pin both legs + that the orchestrator's
      `Mapping[StepKind, StepExecutor]` contract is untouched (fact 3's LOCKED-#5
      pattern; the SD-0 tripwire made executable).
- [x] **AC-2 — `read_stock` declares `reads: [Part]`.** The calm-path step gains
      the typed single-read declaration (PLAN-0048 shape — no `join`, no
      `project` under SD-3's recommendation); the shipped-YAML load-gate sweep
      stays green (fact 10); the 16-line deferral note (`procedures.yaml:309-324`)
      and the facet note (`:332`) are rewritten to record the migration + cite this
      PLAN; `facet.input` prose synced to the typed truth (D2-A2 precedent).
- [x] **AC-3 — execution-bound through the production factory.** The registered
      procurement factory (`register_procurement_procedure_executors`) builds the
      router in its QUERY slot: the declared leg = the SHIPPED `QueryStepExecutor`
      bound to the **registry-registered adapter** + real ontology meta (SD-5); the
      fallback leg = the existing `_SeedQuery(seed)`. A test through the
      production-factory path asserts `read_stock`'s step output equals the
      registered adapter's Part rows (both rows; `stock_qty`/`reorder_point`
      present) — the ERRATUM-2 hazard (declared step handed the intake seed) is
      structurally impossible and asserted so.
- [x] **AC-4 — `intake` is behaviorally byte-unchanged.** `intake` (no declared
      reads) still receives `_SeedQuery`'s output identically; the hero audit
      contract, `test_scheduled_procurement_demo`, and the PLAN-0062
      shadow-parity suite pass untouched; the hero procedure block in
      `procedures.yaml` is byte-unchanged (only the calm-path `read_stock` block
      changes).
- [x] **AC-5 — the tripwire flip is handled by design.** The old invariant test
      (fact 7) is REWRITTEN per SD-4 to pin the NEW routing contract; the
      substrate companion test (fact 8) stays green untouched. No test is deleted
      or skipped.
- [x] **AC-6 — PLAN-0062 AC-7 is reopened + discharged by reference.** This PLAN's
      close-out records: the per-step router shipped, `read_stock` migrated, the
      0062 ERRATUM-2 deferral discharged — citing `0062:536-539` without editing
      any ratified 0062 line (L-5).
- [x] **AC-7 — the honest enforcement frame, no over-claim.** Close-out states:
      `read_stock` = declared ✔ · gated ✔ · execution-bound ✔ (production factory
      path); `intake` = unchanged (declared-expressible ✔ per 0062 AC-6, production
      execution = the co-existing seed, derived fields execution-bound ✖);
      `low_stock_reorder_round` end-to-end = **still not production-runnable**
      (fact 9 — `judge_stock`'s `measured_value` contract), honestly labelled as a
      separate future candidate. Nothing may claim more.
- [x] **AC-8 — no regression + pin disclosure.** Full offline suite + ruff +
      ruff-format + `mypy --strict services/` green under CI `gate`; the PR body
      discloses the governance-pin consequence of editing the calm-path YAML
      (L-4); **no MS-S1 / live-LLM call anywhere**.

## Out of Scope

- ❌ **The procurement ontology↔CSV column drift** (`part_no`/`part_id`,
  `price`/`price_thb`, `equipment_id`/`asset_id`) — a separate ranked candidate
  (PLAN-0062 follow-up ii).
- ❌ **Intake derived fields / any `_SeedQuery` retirement / hero-procedure
  restructuring** — L-2 (PLAN-0062 SD-C + OQ-3); the SoD-load-bearing `intake`
  step id is untouched (ADR-0025 D5).
- ❌ **Making `low_stock_reorder_round` end-to-end production-runnable** (the
  `judge_stock` reading contract, the `reorder` action handler wiring, the gate
  leg) — fact 9; its own candidate if ranked (see SD-3).
- ❌ **Any spec/grammar/load-gate change; any new `StepKind`; any orchestrator or
  registry type change** — the tripwire, not a build call.
- ❌ **Ontology YAML changes; any live / MS-S1 run** (CLAUDE.md §8).
- ❌ Touching the other three verticals' factories (they have no seed to route
  around — single-executor QUERY slots stay).

## Surfaced Decisions

Each SD carries a recommendation; **Cray ratifies via AskUserQuestion**; none is
silently decided.

- **SD-0 — is an ADR-016 amendment needed first? Recommendation: NO — build-PLAN
  safe.** ADR-016 explicitly records the executor supply as "an undocumented
  operational expectation, not an engine contract" (`0016:511-513`); the Q4
  amendment's OUT-list pins the grammar stack, not the executor-map shape
  (`0016:1233-1247`); and the recommended shape leaves every engine contract
  byte-untouched — the orchestrator still resolves `executors.get(step.kind)`,
  routing happens INSIDE the vertical's QUERY-slot executor, exactly the
  documented extend-not-replace pattern already shipped for EVALUATE/ACTION
  (fact 3) and Cray-ratified at 0062 ERRATUM 1. *Alternative:* amend ADR-016 to
  bless per-step resolution in the engine core — needed ONLY if the wrapper proves
  insufficient (then the header tripwire fires and this PLAN STOPS at that
  boundary; the fork is not baked in). *Why Cray:* this is the dispatch's explicit
  governance question — whether a PLAN may change how executors resolve.
  ✅ *Ratified (Cray, 2026-07-11):* **NO amendment — build-PLAN safe**, as recommended
  (the header STOP tripwire stands).
- **SD-1 — the router's dispatch rule. Recommendation: declaration-presence** —
  `step.input.reads` non-empty → the declared-grammar executor; else → the
  fallback seed. This encodes "declared ⇒ dispatched" structurally: the exact
  ERRATUM-2 hazard (a declared step silently served by the seed) becomes
  impossible by construction, and future declared procurement reads route
  correctly with zero factory edits. *Alternatives:* (i) a `step_id` set (e.g.
  `seed_steps={"intake"}`) — explicit but re-creates the hazard for every future
  step someone forgets to list; (ii) an orchestrator-level per-step override
  param — engine-core change, SD-0's rejected branch. *Why Cray:* the rule decides
  what happens if `intake` ever gains a declaration (it would flip to the declared
  executor — the honest behavior, but a routing semantics Cray should own).
  ✅ *Ratified (Cray, 2026-07-11):* **declaration-presence**, as recommended.
- **SD-2 — the router's home. Recommendation: an engine module** (e.g.
  `services/engine/procedures/query_router.py`, a small frozen dataclass taking
  `declared: StepExecutor` + `fallback: StepExecutor`), mirroring the Cray-ratified
  engine-module precedent for delegating executors (`env_band_step.py`,
  `governance_step.py` — fact 3); it is vertical-agnostic (dispatches on typed
  `Step` fields only) and the procurement factory is merely its first constructor.
  *Alternative:* procurement-local in `hero_demo/run.py` — smallest blast radius,
  but hides a generic pattern in a 600+-line demo harness and forks house style.
  *Why Cray:* engine-module vs vertical-local is the same fork ERRATUM 1 put to
  Cray; consistency says the same authority picks.
  ✅ *Ratified (Cray, 2026-07-11):* **engine module** (`query_router.py`), as recommended.
- **SD-3 — migration scope. Recommendation: `read_stock` only.** The deferral note
  promised routing; intake stays under 0062's ratified SD-C co-exist (L-2); and
  calm-path end-to-end runnability is a semantics decision, not a routing one
  (fact 9). *Alternatives:* (i) also add `project.fields: {stock_qty:
  measured_value}` to make `judge_stock` runnable — spec-expressible
  (`spec.py:310-320`) but reshapes state into the event-reading convention and
  belongs with the drift/calm-path candidate; (ii) also declare intake's join
  half in YAML — rejected, reopens 0062 SD-5(b). *Why Cray:* scope = the
  demo-visible surface; option (i) is tempting and cheap, so declining it must be
  Cray's call, not the drafter's.
  ✅ *Ratified (Cray, 2026-07-11):* **`read_stock` only**, as recommended (option (i)
  declined — stays a separate future candidate).
- **SD-4 — the tripwire test's rewrite shape. Recommendation: replace-in-place
  with the NEW contract pin** — same file, same erratum-history docstring lineage:
  assert the QUERY slot is the router; assert the `read_stock`-shaped (declared)
  leg dispatches the shipped `QueryStepExecutor`; assert the undeclared leg still
  returns the seed byte-identically. The invariant keeps living where ERRATUM 2
  pinned it. *Alternatives:* delete (loses the executable history); skip-mark
  (dishonest — a permanently-skipped oracle). *Why Cray:* this test IS the
  ERRATUM-2 record's executable half; how it evolves is a governance-memory call.
  ✅ *Ratified (Cray, 2026-07-11):* **replace-in-place with the new contract pin**, as
  recommended.
- **SD-5 — which adapter serves declared procurement reads. Recommendation: the
  registry-registered adapter** (`registry.get_adapter("procurement")` =
  `ProcurementSyntheticAdapter`) + `load_ontology_meta("procurement")` — the OCT
  factory precedent (fact 4), and the ONLY adapter carrying the substrate
  (fact 6). The seed keeps its `FastenalCsvAdapter` requisition untouched — two
  adapters in one factory, each honestly labelled. *Alternative:* bind
  `FastenalCsvAdapter` for hero consistency — its `part.csv` lacks
  `stock_qty`/`reorder_point`, re-creating declaration theater through the adapter
  choice. *Why Cray:* which data a governed read serves is an operational-surface
  call.
  ✅ *Ratified (Cray, 2026-07-11):* **the registry-registered `ProcurementSyntheticAdapter`**,
  as recommended.

## Steps

> **Ratification note (2026-07-11):** all six SDs ratified **as-recommended** (Cray,
> AskUserQuestion) — the ACs/Steps below already reflect the ratified shape; no
> re-scope needed. Code R2 completed the same day (every load-bearing citation
> independently re-verified on disk against `main = 3f7b22c`): verdict **accept,
> no amendment**.

Cheapest gate first; suite green at every boundary. **One PR** (S–M, one coherent
routing change; split into engine-then-vertical PRs only if Cray prefers at
ratification).

### Step 1 — the router + unit pins (AC-1)
The SD-2 module + SD-1 dispatch rule; unit tests for both legs + the
contract-untouched pin. No vertical wiring yet — the tripwire test still passes
here (the factory is unchanged), keeping the flip atomic in Step 2.

### Step 2 — procurement wiring + YAML + the tripwire flip (AC-2..AC-5)
`_executors()` gains the router in its QUERY slot (declared leg =
`QueryStepExecutor(adapter=registry.get_adapter(...), object_type_names, meta)`
per SD-5; fallback = `_SeedQuery(seed)`); `register_procurement_procedure_executors`
threads adapter/meta; `procedures.yaml` `read_stock` gains `reads: [Part]` + note
rewrites; the tripwire test is rewritten per SD-4 IN THE SAME COMMIT the routing
lands (never a red intermediate); the AC-3 execution-bound test + AC-4
byte-unchanged sweeps.

### Step 3 — close-out + disclosures (AC-6..AC-8)
The honest enforcement frame + the 0062 AC-7 discharge-by-reference; PR body
discloses the L-4 pin consequence; STATUS reconcile; conventional commits
referencing PLAN-0064; Code commits via PR per CLAUDE.md §7 (ADR-009 D2).

## Verification

**Binding — and complete: the offline oracle is the entire bar.** No LLM exists
anywhere in this path (L-1), so nothing non-deterministic exists to confirm — no
host-state action, no §8 gate, no live evidence note. The AC matrix runs under the
required CI `gate` on a fresh PR. The heart is the routing property, pinned three
ways: unit (AC-1 both legs), production-factory integration (AC-3 — declared
`read_stock` receives real Part rows, never the seed), and regression (AC-4 —
undeclared `intake` output byte-identical). Pass/fail is fixed by these ACs before
the build runs; the honest frame (AC-7) caps every claim.

## Size estimate + risks

**S–M.** One new ~40-line engine module + tests, one factory edit, one YAML step
edit, one test rewrite (~5-6 files). No orchestrator/registry/spec change (SD-0),
no ontology change, no live runs. Risks: (i) hero-demo blast radius — mitigated by
AC-4's byte-unchanged sweeps + the untouched shadow-parity suite; (ii) the
governance-pin ripple of editing the calm-path YAML — L-4, disclosed per AC-8,
no known production parked runs of `low_stock_reorder_round`; (iii) scope
temptation toward calm-path runnability — walled by SD-3 + Out of Scope; (iv) the
`_executors()` signature change ripples its test callers — contained, the SD-4
rewrite covers the one caller that pins its shape.

## Close-out (2026-07-11, session 118 — same-day draft → ratify → build → close)

**Shipped (ONE PR, #696, `75ed717` → merge `fdd6a9b`).** Step 1 (AC-1):
`services/engine/procedures/query_router.py` — the frozen `QueryStepRouter(declared,
fallback)` on the SD-1 declaration-presence rule, inside one `StepKind` slot (SD-0
honored: zero orchestrator/registry/spec change; the tripwire never fired) + 5 unit pins
in `tests/services/engine/procedures/test_query_router.py`, including two query steps
routed to two different legs through the REAL `run_procedure`. Step 2 (AC-2..AC-5):
`_executors` gained keyword-only `declared_query` (the three offline hero/demo helpers
pass none and keep the bare seed slot — their procedures declare no reads);
`register_procurement_procedure_executors` binds the declared leg to the SHIPPED
`QueryStepExecutor` over the **registry-registered** `ProcurementSyntheticAdapter` +
real ontology meta (SD-5); `procedures.yaml` `read_stock` declares `reads: [Part]` with
the deferral note rewritten to record the migration (hero procedure block
byte-unchanged — AC-4); the ERRATUM-2 tripwire test rewritten IN PLACE per its own
docstring contract (SD-4) — it now pins the router in the PRODUCTION factory's QUERY
slot, the declared `read_stock` receiving the registered adapter's Part rows (never the
seed), and the undeclared `intake` receiving the co-existing seed byte-identically;
`test_operate_executor_factory` gained an autouse `discover_and_register` fixture (the
API-lifespan ordering; the energy-factory-test precedent).

**Verification (AC-8).** CI `gate` green on #696 (full suite + Postgres service + ruff +
format + `mypy --strict services/` + fresh-DB migrations); local full suite WITH
Postgres **2512 passed / 7 skipped** (baseline 2507/7 + the new pins, net of the
tripwire rewrite); the L-4 governance-pin consequence disclosed in the PR body (no known
production parked runs of `low_stock_reorder_round`); no MS-S1 / host-state action.

**The honest enforcement frame (AC-7 — nothing claims more).** procurement
`read_stock` = **declared ✔ · load-gated ✔ · execution-bound ✔ on the production
factory path**; `intake` = unchanged (declared-expressible ✔ per 0062 AC-6, production
execution stays the co-existing `_SeedQuery`, derived fields execution-bound ✖);
`low_stock_reorder_round` end-to-end = **still not production-runnable** — `judge_stock`
reads `measured_value`, which raw Part rows do not carry (fact 9); making the calm path
runnable is a separate future candidate (SD-3's declined option (i) is its starting
point). Scope note, stated plainly: the declared⇒dispatched guarantee is a property of
the **production factory** (AC-3's exact claim); the offline hero/demo helpers keep the
bare seed slot and run procedures with no declared reads.

**PLAN-0062 AC-7 discharge (AC-6).** The per-step router shipped; `read_stock`
migrated; the ERRATUM-2 deferral is discharged — citing
`docs/plans/done/0062-per-vertical-seed-migration.md:536-539` ("a per-step QUERY router
for procurement, which would make `read_stock` migratable and reopen AC-7"). No 0062
line was edited (L-5); the STATUS Active TODO for the router closes with this PLAN.

---

*PLAN-0064 drafted by the in-harness `plan-drafter` subagent (2026-07-11), ADR-013
D1 phased governance authoring (ADR-009 D1). It executes the Cray-picked #1
next-work candidate (session 118) reopening PLAN-0062 AC-7 per ERRATUM 2 — no
ratified fork is reopened; six forks are surfaced (SD-0..SD-5) with
recommendations, none silently decided. Author≠reviewer (ADR-012 D4.3): drafter =
plan-drafter; reviewers = Code R2 (every citation re-verified on disk) + Cray at
SD ratification (AskUserQuestion) and PR merge — separation INTACT. Drafted
uncommitted; Code commits via a `docs/*` PR (ADR-009 D2); the drafter does not
git. AI-assisted (plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
