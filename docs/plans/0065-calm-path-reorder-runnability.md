# PLAN-0065: Calm-path reorder runnability — the `stock_qty → measured_value` projection + the manual-run proof + the scheduled sibling

**Status:** Ready for execution (rev 3, fully ratified) — **all five SDs
ratified** (Cray, 2026-07-11, AskUserQuestion; SD-1..SD-4 at rev 2, SD-5 at
rev 3); commit-ready pending Code R2 of the SD-5 delta (Code commits via a
docs PR, ADR-009 D2)
**Owner:** Claude Code (executes); Cray ratified the surfaced decisions
**Created:** 2026-07-11 (rev 2 same-day — SD ratification re-scoped XS → S–M;
rev 3 same-day — SD-5 ratified (b))
**Origin:** Cray picked this as the **#1 next-work candidate** (session 119,
2026-07-11, via AskUserQuestion after the next-work-analyst ranking — the session
after PLAN-0064 closed). It is the direct sequel to PLAN-0064: its SD-3 explicitly
**declined option (i)** — adding `project.fields: {stock_qty: measured_value}` —
and deferred it as "a separate future candidate"
(`docs/plans/done/0064-per-step-query-router-procurement.md:261-272`), and its AC-7
close-out recorded `low_stock_reorder_round` end-to-end as **"still not
production-runnable"** (`0064:189-195`, `:377-386`, fact 17). This PLAN picks up a
**deliberately scope-punted option** — it does NOT re-litigate a rejection, and no
ratified 0064 line is edited (reopening happens by cross-reference from here).
**Ratification (2026-07-11):** SD-2 and SD-4 ratified **as-recommended**; SD-1
ratified **(b) with BOTH sub-options** — prove the existing manual-run endpoint
end-to-end (i) AND add a scheduled sibling procedure (ii) — after fresh grounding
**corrected** rev 1's "no production trigger invokes it" premise (fact 10); SD-3
ratified **DEFERRED on a newly-grounded basis** — the per-part band **trips the L-4
tripwire at design time** (fact 14), so it defers to its own ADR-016-amendment
PLAN, not merely out of preference. **SD-5 ratified (b) at rev 3** — the scheduled
sibling CARRIES `owning_person_id: req-planner` (the NON-recommended option —
Cray's accountability-parity call; the divergent path was verified ACCEPTED on
disk before encoding, fact 13a).
**Related ADRs:** ADR-016 — the Q3 typed-reads contract + the Q4 grammar amendment:
`project.fields` is **shipped Q4 grammar** (PLAN-0061 SD-1 / Q4 SD-B shape 1,
`services/engine/procedures/spec.py:281-320`), so no amendment is needed for the
BUILT scope (facts 4–5); the per-part band would need one (fact 14) and is deferred.
ADR-0028 (S1 scheduler — SD-P1 schedule descriptor, SP-5 owning person; the shipped
machinery the sibling reuses). Also ADR-0024 D3/D6 (no LLM in the read/evaluate
path — carried, LOCKED), ADR-0025 D5 (SoD/doa_tier — `intake` untouched; the calm
path carries neither), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (authoring/commit
boundaries + disclosure).
**Related PLANs:** PLAN-0064 (the origin — its ratified lines are history, not an
editable surface); PLAN-0048 (the shipped single-read `QueryStepExecutor`);
PLAN-0061 (the join/project grammar + `ProjectSpec` + the load gate); PLAN-0062
(SD-C seed co-exist — `intake` untouched); PLAN-0047 (the run/gate-resolve
endpoints + the persisted write-ahead driver the manual-run proof rides);
PLAN-0055 (the scheduler machinery the sibling reuses — Step 8 = the shipped
`scheduled_emergency_sourcing_round` model).

> **Authorship disclosure (ADR-012 D4.3):** drafted (rev 1), revised (rev 2), and
> finalized (rev 3, fully ratified) by the in-harness `plan-drafter` subagent
> (ADR-013 D1 phased authority). Outline originator: Cray — the session-119
> next-work pick + the same-day SD ratifications; the dispatch fact-packs were
> Code-prepared 2026-07-11, and the drafter re-verified every load-bearing
> citation on disk — including every rev-2 and rev-3 citation — before building
> on it. Independent review: Code R2 + Cray at SD
> ratification and PR merge; Code commits per ADR-009 D2 — the drafter does not
> git. Separation: **INTACT**.

> **This is a build PLAN — no new ADR:** every engine contract remains
> **byte-untouched** — no spec, grammar, orchestrator, registry, executor, daemon,
> or `StepKind` change. The manual-run endpoint EXISTS (fact 10); the scheduler
> machinery EXISTS (fact 12); the repo-code diff is YAML (one `input` block + one
> NEW additive procedure block), the archetype catalog/mirror, and tests.
> **Tripwire (L-4) — STOP and surface for an ADR-016 amendment if execution finds**
> the shipped `ProjectSpec` / load gate / `QueryStepExecutor` / scheduler wiring
> does NOT express or execute the built scope as facts 4–6 and 11–13 establish.
> The tripwire has already fired ONCE at design time — for the per-part band —
> and SD-3 defers that scope accordingly (fact 14). Never bake a deviation in.

## Goal

Make the procurement calm-path `low_stock_reorder_round` **honestly runnable in
production**, in three tightly-coupled moves. **(1) Unblock the chain:** add the
declared rename-projection `project: {fields: {stock_qty: measured_value}}` to
`read_stock` — today the production factory path CRASHES at `judge_stock` (the
shipped `EvaluateStepExecutor` reads `measured_value`; raw `Part` rows carry
`stock_qty` — facts 2–3), and the existing green test does not cover it (fact 8).
**(2) Prove the production entry point:** the generic manual-run endpoint
`POST /procedures/{procedure_id}/run` already exists and runs this procedure
(fact 10 — rev 1's "no production trigger invokes it" was CORRECTED at
ratification); an API-level test proves the chain runs end-to-end over HTTP to the
`reorder` gate. **(3) Fire it unattended:** author a NEW distinct
`scheduled_low_stock_reorder_round` sibling (the trigger enum forbids flipping the
manual one — fact 11) on the shipped PLAN-0055 scheduler machinery, parking
headless at the same single human gate. The calm path still parks at ONE human
go/no-go — nothing auto-approves (RF-1/RF-3 unchanged). Everything is **offline,
deterministic, MS-S1-independent**; CI `gate` is the binding bar.

## LOCKED (inherited — render faithfully; do NOT re-litigate)

- **L-1 (ADR-0024 D3/D6).** No LLM anywhere in the read/evaluate path. The
  projection is pure declared-grammar; `llm_assist: null` stays on every step of
  both the calm path and its scheduled sibling.
- **L-2 (PLAN-0062 SD-C, ratified).** The `intake` `_SeedQuery` seed co-exists
  untouched. Among EXISTING YAML the only edited step is the calm-path
  `read_stock`; the scheduled sibling is a NEW additive block. The
  SoD-load-bearing `intake` step id is untouched (ADR-0025 D5).
- **L-3 (PLAN-0061/0048 pin machinery — the governance-pin consequence).** Editing
  the calm-path `read_stock` `input` changes what NEW runs of
  `low_stock_reorder_round` pin; a pre-deploy parked run of an EDITED procedure
  fails CLOSED at resume — disclosed in the PR body per AC-8 (no known production
  parked runs of this calm-path). The NEW sibling id has no pre-existing runs, so
  no resume hazard attaches to it. Mirrors PLAN-0064's L-4.
- **L-4 (the STOP tripwire).** No orchestrator / registry / spec / grammar /
  daemon change; no new `StepKind`; no new grammar field. Facts 4–6 + 11–13
  establish the shipped machinery already expresses the built scope — if execution
  finds it does NOT, STOP and surface for an ADR-016 amendment. It fired at DESIGN
  time for the per-part band (fact 14) — which is exactly why SD-3 is deferred,
  not built.

## Substrate facts (drafter re-verified on disk, 2026-07-11; rev-2 facts 10–16 re-verified post-ratification)

1. **The procedure + its three steps.**
   `verticals/procurement/procedures.yaml:299-371` — `read_stock` (`:320-332`):
   `kind: query`, `input.reads: [Part]`, **no `project`** (the PLAN-0064 declared
   single-read, PLAN-0048 shape); `judge_stock` (`:333-349`): `kind: evaluate`,
   `threshold: 100.0`, `direction: below`, facet
   `decision_condition: {gate_kind: in_file_band, band_source: in_file}` (`:345`);
   `reorder` (`:350-371`): `kind: action`, `autonomy: gated`, `handler: reorder`,
   `input: {from: judge_stock, where: {verdict: breach}}`; `terminal: reorder`
   (`:371`). `trigger: manual` (`:307`). **No `doa_tier`, no
   `separation_of_duties`** — an AT-3 procedure (load-bearing for fact 13).
2. **The chokepoint — the judge reads `measured_value`, loudly.**
   `services/engine/procedures/evaluate_step.py:40` — `VALUE_FIELD =
   "measured_value"`; `_entity_value` (`:49-65`) raises `ValueError` for any entity
   without a numeric `measured_value` (`:60-64`). The production EVALUATE slot is
   `GovernanceEvaluateExecutor(base=EvaluateStepExecutor())`
   (`verticals/procurement/hero_demo/run.py:282`), and a non-`rule_gate` evaluate —
   `judge_stock`'s `in_file_band` is not a `ComplianceGate` — delegates straight to
   the base (`services/engine/procedures/governance_step.py:262-285`). So on the
   production factory path, `judge_stock` over raw `Part` rows **crashes**.
3. **Part rows carry `stock_qty` + `reorder_point`, never `measured_value`.**
   Adapter: `verticals/procurement/data_adapter/synthetic.py:173-197` emits **TWO**
   Part rows — the hero spindle (`stock_qty: 0`, `reorder_point: 1`, `:182-183`)
   and the calm-path filter (`stock_qty: FILTER_STOCK_QTY = 40` `:47/:192`,
   `reorder_point: FILTER_REORDER_POINT = 100` `:48/:193`). Ontology:
   `verticals/procurement/ontology/procurement_v0.yaml:171-199` — `Part` props =
   {part_no, name, on_contract, preferred_supplier, stock_qty, reorder_point,
   lead_time, fits_equipment_id}, `primary_key: part_no`; **no `measured_value`
   property** (no rename-target collision, fact 5).
4. **The fix is spec-expressible with ZERO grammar change.** `ProjectSpec`
   (`services/engine/procedures/spec.py:281-320`): `fields` is an optional
   select/rename map `{source_field: output_name}` (`:304-308`); the validator
   (`:310-320`) permits a fields-only projection.
5. **Load-gate valid.** `_validate_project`
   (`services/engine/procedures/orchestrator.py:412-452`) for a fields-only
   projection checks only that the rename TARGET does not collide with a kept base
   prop (`:446-452`); `measured_value ∉ (Part props − {stock_qty})` → passes. It
   fires at both the load gate (`:378-380`) and plan compile
   (`query_step.py:188-193`).
6. **Execution path — one fetch, no join, deterministic, meta available.** A
   `project`-declaring step compiles via `_compile_join_plan`
   (`services/engine/procedures/query_step.py:321-331`); for a single read +
   fields-only it yields `JoinReadPlan(reads=("Part",), joins=(), group_by=None,
   fields={"stock_qty": "measured_value"})` (`:180-259`) — exactly ONE
   `fetch_objects` dispatch, no join, no LLM. `_rename` (`:648-664`) **moves**
   `stock_qty → measured_value` and keeps every other field. The join-plan path
   requires executor meta (`:322-330`) — the production factory constructs
   `QueryStepExecutor(adapter=registered_adapter, object_type_names=..., meta=meta)`
   (`run.py:645-647`) ✔.
7. **The production QUERY slot routes the declared read there.**
   `run.py:271-284` — `QueryStepRouter(declared=..., fallback=_SeedQuery(seed))`
   (`:276`; declaration-presence, 0064 SD-1); registered per-vertical (`:650`).
   Pinned by `tests/verticals/procurement/test_intake_shadow_parity.py` (`:50`,
   `:304`).
8. **The existing green test does NOT cover the production path.**
   `tests/services/engine/test_procurement_vertical.py:169-179` runs test-local
   executors: `_Query` is a canned fixed-output stub that **ignores `step.input`
   entirely** (`:41-50`), fed `OperationalEvent` rows carrying
   `measured_value=40.0` (`synthetic.py:150`) — it asserts one `["breach"]`. It
   stays green before AND after this PLAN and proves nothing about the Part-row
   production path.
9. **Both Part rows breach — under the fixed band AND their own points.** With
   `threshold: 100.0` / `below`: spindle 0 ≤ 100 breach, filter 40 ≤ 100 breach —
   the production-path judge yields `["breach", "breach"]` and the reorder set =
   both parts. Per-part semantics agree on the shipped data (0 ≤ 1, 40 ≤ 100), so
   SD-3's deferral distorts nothing demo-visible today.
10. **CORRECTED at ratification — a production run surface ALREADY invokes this
    procedure.** Rev 1 claimed "no production trigger invokes it", conflating the
    read-only VIEWER map (`services/api/routers/procedures.py:36-44` — AT-3 at
    `:41`) with the run surface. The generic manual-run endpoint exists:
    `POST /procedures/{procedure_id}/run` (`services/api/routers/runs.py:272`,
    `run_procedure_endpoint`); `_find_procedure` (`:86-93`) does NOT check
    `trigger` — a `manual` procedure runs fine (the orchestrator allows
    `{MANUAL, SCHEDULE, EVENT}` — `_RUNNABLE_TRIGGERS`,
    `services/engine/procedures/orchestrator.py:148`, guard `:168-172`); it
    executes via `run_procedure_persisted` (`:299`) with SERVER-resolved identity
    (`:277`, `:292-293`; `RunProcedureRequest` carries only optional
    `trigger_context`, `services/api/models/runs.py:17-27`); the gated `reorder`
    parks `waiting_human` and a human resolves via
    `POST /runs/{run_id}/gate/resolve` (`runs.py:324`). Reachable in production
    when `OCT_VERTICAL=procurement` — the executor factory registers at startup
    (`services/api/main.py:161-163`). The `reorder` handler exists + is
    allowlisted (`verticals/procurement/handlers.py:26-28`, `:92-99+`;
    `procedures.yaml:52`); the gated step suspends BEFORE any handler fires.
11. **One trigger per procedure — the sibling MUST be a distinct id.** A
    `schedule` descriptor is present **IFF** `trigger == schedule` —
    `_validate_schedule_descriptor`,
    `services/engine/procedures/spec.py:1034-1053` (note: the YAML comment at
    `procedures.yaml:387` cites "spec.py:823-842" — a **stale line-cite**; `:823-842`
    is the Step per-kind validator; the invariant is real, at `:1034-1053`).
    Flipping `low_stock_reorder_round` to `schedule` would break its manual runs;
    also SD-P3 skip-if-in-flight keys on `procedure_id` (`procedures.yaml:386-390`;
    the event variant echoes the same rationale, `:593-597`). Hence
    `scheduled_low_stock_reorder_round` = a NEW distinct procedure block.
12. **The shipped model + machinery the sibling reuses (PLAN-0055 / ADR-0028).**
    Model: `scheduled_emergency_sourcing_round` (`procedures.yaml:402-419`) —
    `trigger: schedule` (`:414`), descriptor `cron: "0 6 * * *"`, `timezone:
    Asia/Bangkok`, `owning_person_id: req-planner` (`:415-419`). Machinery:
    `schedule_procedures` selects `Trigger.SCHEDULE`
    (`services/engine/procedures/scheduler_wiring.py:54-56`);
    `sync_schedule_states` upserts one `ScheduleState` per schedule procedure
    (`:59-99`); `build_resolver` (`:164-194`) resolves the agent's service
    principal + the optional owning person; on fire the daemon passes
    `principal=run.owning_person` to `run_procedure_persisted`
    (`services/engine/procedures/scheduler.py:271-276`;
    `ScheduledRun.owning_person: Person | None = None` — "``None`` for a headless
    schedule", `:66-77`).
13. **`owning_person_id` is OPTIONAL — a headless AT-3 fire fails nothing
    closed.** `Schedule.owning_person_id: str | None = Field(default=None, …)`
    (`spec.py:115-124`): "None = fully headless — valid only for a procedure with
    no SoD requester to resolve (a doa_tier procedure requires SoD … so it needs
    one)"; `_resolve_owning_person` returns `None` for a headless schedule
    (`scheduler_wiring.py:146-161`); the cross-ref is validated only when present
    (`spec.py:1226-1236`). `low_stock_reorder_round` has NO `doa_tier` and NO
    `separation_of_duties` (fact 1) — the emergency siblings need an owning person
    ONLY because doa_tier ⇒ SoD ⇒ a resolvable requester
    (`procedures.yaml:392-401`). A headless fire of the calm-path sibling runs the
    auto steps and parks at the gated `reorder`; the RESOLVING human's identity
    comes from gate-resolve authentication (RF-1), not from the run. Whether to
    omit or carry it anyway = **SD-5** (ratified (b) — carry; see 13a).
    **13a (rev 3 — the SD-5(b) divergent path verified ACCEPTED).** Because Cray
    picked the NON-recommended option, its safety was grounded before encoding:
    **no validator rejects a non-None `owning_person_id` on a no-SoD procedure.**
    `Schedule._validate_schedule` (`spec.py:126-139`) validates ONLY cron
    non-blankness + IANA tz — it never inspects `owning_person_id`; the sole
    owning-person validation in the spec is the presence-guarded cross-ref
    (`spec.py:1226-1236` — a non-None value must name a declared principal;
    `req-planner` IS declared, `procedures.yaml:62-63`), and no validator couples
    `owning_person_id` to `separation_of_duties`/`doa_tier`
    (`_validate_separation_of_duties`, `spec.py:1076-1090`, checks SoD step
    references only). At run time a non-None principal on a no-SoD run is the
    manual endpoint's NORMAL case — `runs.py:307` passes `principal=auth.person`
    for every procedure (incl. energy's no-SoD sweep, fact 16); the fire path
    mirrors it (`scheduler.py:271-276`), simply recording the accountable human;
    no SoD gate consumes it, and gate-resolve authenticates its own approver
    (RF-1). ACCEPTED at load, at the headless fire, and at resolve.
14. **Why the per-part band trips L-4 (SD-3's grounded deferral).** The shipped
    executor compares each entity's `measured_value` against ONE scalar authored
    band: `Step.threshold: float | None` (`spec.py:778-782`);
    `classify_verdict(_entity_value(…), step.threshold, direction, watch_margin)`
    (`evaluate_step.py:82-97`) — no per-entity / field-referenced threshold
    exists. And projection is select/rename ONLY — "arbitrary computation stays
    downstream" (`spec.py:288-289`) — so a `stock_qty − reorder_point` derivation
    is not read-expressible either. Per-part banding therefore needs EITHER a
    grammar amendment (a `threshold_field`-style addition — ADR-016 D2-A3
    territory) OR a custom procurement evaluate executor — both break this PLAN's
    zero-engine-code-change basis. **The L-4 tripwire fired at design time**;
    deferred to its own ADR-016-amendment PLAN (harmless today per fact 9).
15. **The catalog/mirror + two verified count pins the sibling ripples.**
    `PROCEDURE_ARCHETYPES` (`services/api/routers/procedures.py:36-44`) is a
    read-only derived MIRROR of the canonical
    `docs/conventions/procedure-archetypes.md` — "the catalog grows first, the map
    mirrors it; never the reverse" (`:27-31`; the "Seven shipped procedures"
    comment `:31-35` needs a prose sync).
    `tests/api/test_procedures_endpoint.py` pins the per-vertical map (`:23-35`)
    and asserts `total == 7` (`:87-89`) → becomes 8 + a new AT-3 entry.
    `tests/services/db/test_scheduled_procurement_demo.py:114-117` pins
    procurement to **exactly one** schedule procedure
    (`assert [r.procedure_id for r in rows] == [_PROC_ID]`) → must be updated for
    two.
16. **The API-test harness precedent for the manual-run proof.**
    `tests/api/test_runs_endpoints.py` drives energy's sweep run → suspend →
    resolve → resume over HTTP only: authn ON with a provisioned bearer-key digest
    (`:29-31`, `:49-50`), the `_principal_index` seam monkeypatched (`:37-54` —
    the OQ-6 membership boundary), `httpx.AsyncClient`, executors via
    `registry.register_procedure_executors`, DB via
    `tests.db_support.create_test_engine`. The AC-3 test mirrors this shape but
    binds the REAL procurement factory; note procurement DECLARES principals, so
    the bearer identity must resolve against them (or the seam is patched per the
    precedent).
17. **The origin frame (0064, not edited).** AC-7 close-out: end-to-end "**still
    not production-runnable**" (`0064:189-195`, `:377-386`); SD-3 ratified
    "`read_stock` only", **option (i) declined** — "stays a separate future
    candidate" (`0064:261-272`). This PLAN is that candidate.

## Acceptance Criteria

Written to the ratified SDs — SD-1 (b) both / SD-2 / SD-3 deferred / SD-4 /
SD-5 (b) carry `owning_person_id: req-planner`. All offline + deterministic,
provable under CI `gate`.

- [ ] **AC-1 — the projection lands, prose synced to the typed truth.**
      `read_stock.input` gains exactly `project: {fields: {stock_qty:
      measured_value}}` (SD-2); `reads: [Part]` unchanged. The step's facet
      `input`/`output` prose + note are synced to the post-projection shape (rows
      carry `measured_value` — renamed, not duplicated; `reorder_point` kept); the
      PLAN-0064 migration comment block (`procedures.yaml:309-319`) is NOT
      rewritten — at most a one-line PLAN-0065 addendum.
- [ ] **AC-2 — the production-factory chain runs end-to-end (SD-4).** A new test
      builds the PRODUCTION factory executors (the shadow-parity harness
      precedent, fact 7) and runs `low_stock_reorder_round` through the real
      `run_procedure`: `read_stock` output = the registered adapter's TWO Part
      rows each carrying numeric `measured_value` (0 and 40) and NO `stock_qty`
      key (fact 6 — rename moves); `judge_stock` verdicts `["breach", "breach"]`
      (fact 9); the run suspends `WAITING_HUMAN` with the last step `reorder`.
      Pre-committed red (Lesson #0026): against the unedited YAML the same test
      dies with the exact `ValueError: … no numeric 'measured_value'`
      (`evaluate_step.py:60-64`) — verified locally pre-fix; never committed red.
- [ ] **AC-3 — the manual-run endpoint proof (SD-1 (b)(i)).** An API-level test
      (harness per fact 16; real procurement factory + registered adapter) drives
      `POST /procedures/low_stock_reorder_round/run` with an authenticated
      identity: 200; persisted run `waiting_human`; `suspended_step == "reorder"`;
      the judge verdicts derive from the projected `measured_value` over Part
      rows; `triggered_by` = the server-resolved person (never the body). This is
      the honest "runnable end-to-end from a production entry point" proof.
      (Gate-resolve itself is already covered by the PLAN-0047 tests; parking at
      the gate is this AC's end state.)
- [ ] **AC-4 — the scheduled sibling (SD-1 (b)(ii)).** A NEW distinct procedure
      `scheduled_low_stock_reorder_round` (fact 11 — never a flip of the manual
      one): `trigger: schedule` + descriptor (`cron`, `timezone: Asia/Bangkok`,
      **`owning_person_id: req-planner`** per the ratified SD-5(b) — modeled on
      the emergency sibling's descriptor, `procedures.yaml:415-419`; effect: the
      owning person becomes the fired run's `principal`, fact 13a), same
      three-step calm-path chain, `llm_assist: null` throughout (L-1). Canonical-first catalog growth: the
      `docs/conventions/procedure-archetypes.md` entry lands FIRST, then the
      `PROCEDURE_ARCHETYPES` mirror (AT-3) + its "seven procedures" comment sync
      (fact 15). A fire-path test (model:
      `tests/services/db/test_scheduled_procurement_demo.py`) proves
      `sync_schedule_states` registers it and the fire path runs the chain
      headless to `FireResult.FIRED` + `waiting_human` at `reorder` — a machine
      never approves (RF-3).
- [ ] **AC-5 — byte-unchanged + count-pin regressions.** `intake`, the hero
      `emergency_sourcing_round`, and the scheduled/event AT-2 variants
      byte-unchanged; the ONLY YAML deltas are the `read_stock` projection (AC-1)
      and the NEW `scheduled_low_stock_reorder_round` block (AC-4). The
      shadow-parity suite green UNTOUCHED; the existing event-based calm-path test
      (fact 8) green untouched. The two verified count pins updated deliberately
      (fact 15): `test_procedures_endpoint` `total == 7 → 8` + the new map entry;
      `test_scheduled_procurement_demo` exactly-one-schedule assertion → the
      two-schedule set (its emergency-sibling assertions otherwise unchanged).
- [ ] **AC-6 — the shipped-YAML load-gate sweep stays green** across all four
      verticals — now also covering the NEW block: descriptor shape, tz vs
      zoneinfo, and the CARRIED `owning_person_id: req-planner` cross-ref, which
      the load gate MUST validate against the declared procurement `principals`
      (`spec.py:1226-1236`; `req-planner` is declared, `procedures.yaml:62-63` —
      facts 5, 11–13/13a).
- [ ] **AC-7 — the honest frame, no over-claim (rewritten per ratified SD-1).**
      Close-out states exactly what is proven: the calm path **runs end-to-end
      from a production entry point** — the manual-run endpoint executes
      read → judge → reorder to the human gate (AC-3) — **and fires unattended**
      on the nightly clock via the scheduled sibling (AC-4); in BOTH paths the run
      **parks at a single human go/no-go** — nothing auto-approves, no PO issues
      until a human acts (RF-1/RF-3). The rev-1 "no production trigger invokes it"
      caveat is retired as CORRECTED (fact 10 — the viewer map was conflated with
      the run surface). Nothing may claim more (e.g. no claim about live
      deployment, MS-S1, or the per-part band).
- [ ] **AC-8 — no regression + disclosures.** Full offline suite + ruff +
      ruff-format + `mypy --strict services/` green under CI `gate`; the PR body
      discloses the L-3 governance-pin consequence (edited
      `low_stock_reorder_round`: no known production parked runs; the NEW sibling
      id: no pre-existing runs, no resume hazard); **no MS-S1 / live-LLM /
      host-state action anywhere** (CLAUDE.md §8).

## Out of Scope

- ❌ **The procurement ontology↔CSV column drift** (`part_no`/`part_id`,
  `price`/`price_thb`, `equipment_id`/`asset_id`) — a separate ranked candidate.
  (`stock_qty` is NOT one of the drift pairs.)
- ❌ **The per-part reorder-point band — SD-3, ratified-DEFERRED because it TRIPS
  the L-4 tripwire** (fact 14: single scalar `step.threshold`; no per-entity
  threshold; no read-side arithmetic — it needs a grammar amendment or a custom
  evaluate executor). Deferred to its own ADR-016-amendment PLAN; harmless today
  (fact 9: identical verdicts on the shipped 2-part data). The fixed
  `threshold: 100.0` stays.
- ❌ **Auto-approving / auto-resolving the `reorder` gate** in either path — the
  single human go/no-go is the calm path's contract (RF-1/RF-3).
- ❌ **Any scheduler/daemon/engine code change** — the sibling reuses PLAN-0055
  machinery as-is (L-4); **no event-trigger sibling** (schedule only, per the
  ratified SD-1 (b)(ii)).
- ❌ **Any `intake` / `_SeedQuery` change; any hero-procedure change**
  (byte-unchanged — L-2, AC-5).
- ❌ **Any ontology YAML / generated-artifact / schema change; any
  spec/grammar/StepKind change** (L-4); **any live / MS-S1 run** (CLAUDE.md §8).
- ❌ The offline hero/demo helpers' bare-seed QUERY slots — they do not run this
  procedure; unchanged.

## Surfaced Decisions

**All five SDs ratified** by Cray 2026-07-11 (AskUserQuestion; SD-1..SD-4 at
rev 2, SD-5 at rev 3). SD-5 was surfaced at rev 2, never silently decided; Cray
resolved it AGAINST the drafter's recommendation — encoded only after the
divergent path was verified ACCEPTED on disk (fact 13a).

- **SD-1 — what "runnable" means.** *Rev-1 recommendation was (a) chain-only,
  premised on "no production trigger invokes it" — that premise was CORRECTED by
  fresh grounding (fact 10: the generic manual-run endpoint already runs it).*
  ✅ *Ratified (Cray, 2026-07-11):* **(b) with BOTH sub-options** — (i) prove the
  manual-run endpoint end-to-end (AC-3) and (ii) add the scheduled sibling
  (AC-4). Re-scopes the PLAN XS → S–M.
- **SD-2 — the projection shape.** Recommendation: exactly
  `project: {fields: {stock_qty: measured_value}}` — minimal, shipped-grammar
  (fact 4), keeps `reorder_point` (fact 6).
  ✅ *Ratified (Cray, 2026-07-11):* **as recommended.**
- **SD-3 — the per-part band.** Recommendation was OUT of scope as the YAML's own
  deferred Stage-2 (`procedures.yaml:335-339`).
  ✅ *Ratified (Cray, 2026-07-11):* **DEFERRED — on the stronger, newly-grounded
  basis that it trips L-4 at design time** (fact 14): not buildable inside this
  PLAN's zero-engine-change contract; its future home is an ADR-016-amendment
  PLAN (a `threshold_field`-style grammar addition or a custom evaluate
  executor). Fact 9 records why deferring distorts nothing demo-visible today.
- **SD-4 — where the runnability invariant lives.** Recommendation: a NEW
  production-factory-path test; the existing event-based test stays untouched
  (they pin different invariants — fact 8).
  ✅ *Ratified (Cray, 2026-07-11):* **as recommended.**
- **SD-5 (NEW, rev 2) — does the scheduled sibling carry `owning_person_id`?**
  Grounding (fact 13): it is NOT required — the field's function is SoD-requester
  resolution, and this AT-3 procedure has no SoD / `doa_tier`; the spec
  explicitly blesses the fully-headless `None` for exactly this case.
  **Recommendation was (a) omit** — the mechanically-minimal, spec-blessed shape.
  *Alternative (b):* carry `owning_person_id: req-planner` for accountability
  parity with the hero siblings — its REAL effect is that the owning person
  becomes the fired run's `principal` (`scheduler.py:271-276`), i.e. the run
  record names the accountable human behind the unattended sweep. *Why Cray:*
  what a demo-visible run/audit record NAMES on an unattended run is an
  accountability-surface call, not the drafter's.
  ✅ *Ratified (Cray, 2026-07-11, rev 3):* **(b) carry `owning_person_id:
  req-planner`** — the NON-recommended option, Cray's explicit accountability
  call: the run record names the accountable human behind the unattended sweep
  (fact 13a). The divergent path was verified ACCEPTED on disk before encoding —
  no validator rejects a non-None owning person on a no-SoD schedule (fact 13a:
  `spec.py:126-139`, `:1226-1236`, `:1076-1090`; `runs.py:307`;
  `scheduler.py:271-276`). **The risk-(v) STOP guard stays as the build-time
  backstop — if execution observes ANY fail-closed behavior at the headless fire
  or the gate-resolve contradicting facts 13/13a, STOP and surface for a Cray
  re-decision; never silently drop or alter the ratified field.**

## Steps

Cheapest gate first (Lesson #0026: pass/fail read fixed before the run); suite
green at every commit boundary. **Ideally ONE PR** (S–M; all five SDs are
ratified — no step is gated on a pending decision).

### Step 1 — the production-path chain test, red-verified locally (AC-2's oracle)
Author the SD-4 test against the PRODUCTION factory executors; run it against the
UNEDITED YAML and confirm the pre-committed red: the exact
`ValueError: … no numeric 'measured_value'` (fact 2). Nothing is committed red.

### Step 2 — the projection + prose sync (AC-1, AC-6)
`read_stock.input` gains the SD-2 projection; facet prose + note synced;
hero/intake blocks byte-unchanged. Run the cheapest oracle first — the
shipped-YAML load-gate sweep — then the Step-1 test flips green. Steps 1+2 land in
the SAME commit.

### Step 3 — the manual-run endpoint proof (AC-3)
The API-level test per fact 16: authn ON, real procurement factory + registered
adapter, `POST /procedures/low_stock_reorder_round/run` → `waiting_human` at
`reorder`, verdicts from the projected `measured_value`, server-resolved
`triggered_by`.

### Step 4 — the scheduled sibling (AC-4)
Canonical catalog entry FIRST (`docs/conventions/procedure-archetypes.md`), then:
the NEW `scheduled_low_stock_reorder_round` YAML block (distinct id — fact 11;
descriptor with `owning_person_id: req-planner` per the ratified SD-5(b), modeled
on `procedures.yaml:402-419` incl. `:415-419`), the `PROCEDURE_ARCHETYPES` mirror
+ comment sync, the two deliberate count-pin updates (fact 15), and the fire-path
test (headless fire → parks at `reorder`; the fired run's `principal` =
`req-planner`, fact 13a).

### Step 5 — regression sweeps + hygiene (AC-5, AC-8 hygiene)
Full offline suite (shadow-parity untouched-green; the event-based calm-path test
untouched-green; the updated count pins green); ruff + ruff-format +
`mypy --strict services/`.

### Step 6 — close-out + disclosures (AC-7, AC-8)
The rewritten honest frame per the ratified SD-1 (retire the corrected rev-1
caveat; nothing claims more); PR body discloses the L-3 pin consequence; STATUS
reconcile; conventional commits referencing PLAN-0065; Code commits via PR per
CLAUDE.md §7 (ADR-009 D2). On completion:
`git mv docs/plans/0065-*.md docs/plans/done/`.

## Verification

**Binding — and complete: the offline oracle is the entire bar.** No LLM exists
anywhere in this path (L-1), so nothing non-deterministic exists to confirm — no
host-state action, no §8 gate, no live evidence note. The AC matrix runs under the
required CI `gate` on a fresh PR (the endpoint + scheduler tests are DB-backed —
the disposable per-checkout test DB / CI Postgres service, as in PLAN-0055/0064).
The heart is runnability proven at THREE depths, each with a pre-fixed pass/fail
read: the executor chain (AC-2, red→green on the exact chokepoint error), the
production HTTP entry point (AC-3), and the unattended clock (AC-4) — capped by
the byte-unchanged + deliberate count-pin regressions (AC-5/AC-6) and the
honest-frame ceiling on every claim (AC-7).

## Size estimate + risks

**S–M.** One YAML `input` edit + one NEW YAML procedure block, the canonical
catalog entry + its API mirror line, three new tests (chain / endpoint /
fire-path), two deliberate count-pin updates, close-out docs (~8–9 files). Zero
engine-code change (the no-ADR basis); no ontology change; no live runs. Risks:
(i) **the L-4 tripwire** — already fired at design time for the per-part band
(SD-3 deferred accordingly); for the BUILT scope it remains the STOP guard —
never bake a deviation in; (ii) **rename MOVES `stock_qty`** — post-projection
rows no longer carry it; nothing downstream of `read_stock` reads it, and AC-1
syncs the facet prose; (iii) **the governance-pin ripple** — L-3, disclosed per
AC-8 (edited calm-path: no known parked runs; new sibling id: no resume hazard);
(iv) **the two-breach output** (fact 9) — the reorder set = BOTH parts (the hero
spindle at 0 breaches data-honestly); recorded so AC-2/AC-3 assertions don't
surprise; (v) **the SD-5(b) divergent path** — verified ACCEPTED at load, fire,
and resolve BEFORE encoding (fact 13a); if execution nonetheless observes any
fail-closed behavior, STOP and surface for a Cray re-decision — never silently
drop or alter the ratified `owning_person_id: req-planner`; (vi) **count-pin
ripples** — the two VERIFIED pins (fact 15) are updated deliberately; any
additional unpinned assumption of "one procurement schedule procedure" that
surfaces in the sweep is updated with the same deliberate-change note;
(vii) **API-test membership** — procurement declares principals, so the AC-3
bearer identity must resolve against them (or patch the `_principal_index` seam
per the fact-16 precedent); (viii) **stale-cite hygiene** — the YAML comment's
"spec.py:823-842" (fact 11) is a stale line-cite in a 0064-adjacent comment
block; correct it ONLY if that block is already being touched by AC-1's addendum,
otherwise leave (no ratified-line edits).

---

*PLAN-0065 drafted, revised, and finalized (rev 3, fully ratified) by the
in-harness `plan-drafter` subagent (2026-07-11), ADR-013 D1 phased governance
authoring (ADR-009 D1). It executes the Cray-picked #1 next-work candidate
(session 119) — PLAN-0064 SD-3's deliberately deferred option (i) — under all
five ratified SDs: SD-1 (b) both / SD-2 / SD-3 deferred-per-tripwire / SD-4 /
SD-5 (b), the last resolved AGAINST the drafter's recommendation by Cray's
explicit accountability call and encoded only after the divergent path was
verified ACCEPTED on disk (fact 13a); none silently decided; rev 1's "no
production trigger" claim is corrected on-record (fact 10). Author≠reviewer
(ADR-012 D4.3): drafter = plan-drafter; reviewers = Code R2 (every rev-1, rev-2,
AND rev-3 citation re-verified on disk) + Cray at SD ratification
(AskUserQuestion) and PR merge — separation INTACT. Drafted uncommitted; Code
commits via a `docs/*` PR (ADR-009 D2); the drafter does not git. AI-assisted
(plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
