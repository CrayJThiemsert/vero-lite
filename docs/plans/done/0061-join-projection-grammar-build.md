# PLAN-0061: Q4 join/projection grammar build — multi-read query steps (renders the ADR-016 Q4 amendment, Accepted 2026-07-09)

**Status:** Complete — all 8 ACs met (Steps 1-4 built as four green-gate PRs: #664 Phase A substrate `978caca`, #665 Phase B schema+governance+gate `93e01d1`/`7fb7497`, #666 Phase C compile/execute `0d738e1`, #667 Phase D fixtures end-to-end; full offline suite 2452 passed / 7 skipped, repo-wide ruff + mypy clean; SD-6 honored — no live run, the offline oracle was the entire bar; session 115, 2026-07-09). SD-1..SD-6 ratified as-recommended by Cray (session 115, AskUserQuestion).
**Owner:** Claude Code (executes); Cray ratifies the surfaced decisions
**Created:** 2026-07-09
**Related ADRs:** ADR-016 — the **"Amendment (2026-07-09): join/projection grammar for
multi-read query steps (Q4)"** (`docs/adr/0016-governed-procedure-engine.md:1010-1377`,
**Accepted**, Cray-ratified session 115, OQ-1..OQ-4 all resolved as-recommended) is the
authorizing decision — this PLAN **executes** it and needs **NO new ADR** and reopens
**no ratified fork** (SD-A/B/C/D + OQ-1..4 are LOCKED below). Also: ADR-0027 SD-5
(`join_path`/`grain` — the second declaring surface SD-D promotes), ADR-008 (the authored
ontology grammar — untouched; SD-D is projection-layer only), ADR-0024 D3/D6
(governed ≠ generated — no LLM in the read path), ADR-006 (Rule-of-Three — exactly the
two shipped shapes), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (authoring/commit
boundaries + disclosure).
**Related PLANs:** PLAN-0048 (`docs/plans/done/0048-q4-generic-query-executor.md` — the
single-read predecessor this extends: the compile/execute/inspect seam, the typed-refusal
taxonomy, the one-bound-zero-drift property AC-3, the D-N2 no-repair contract `:50`, the
NL-query wall `:98`, and the explicit deferral of this grammar as "an ADR-016 amendment,
not a build call" `:95`, `:214`); PLAN-0046 (the Q3 load gate this extends); PLAN-0047
(governance pin + write-ahead persistence — the machinery the new fields join); PLAN-0050
(the backward-compat-gate precedent for additive ontology-projection changes).

> **Authorship disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent (ADR-013 D1 phased authority). Outline originator: Cray — the ADR-016 Q4
> amendment's ratified Sequencing names this exact build PLAN
> (`0016:1196-1199`), and the Phase-2 build dispatch is Cray's session-115 next-work
> pick. Independent review: Code R2 (every `file:line` citation re-verified on disk)
> + Cray at SD ratification (via AskUserQuestion, the 0058/0059/0060 pattern) and PR
> merge; Code commits per ADR-009 D2 — the drafter does not git. Separation: **INTACT**.

> **This is a build PLAN — no new ADR.** The architecture is settled: the amendment is
> Accepted with all four OQs resolved. **Tripwire — STOP and surface for an ADR-016
> amendment if execution finds any of:** (i) a join/projection shape the two-shape v1
> grammar cannot honestly express without new spec semantics (do NOT invent a third
> shape — SD-B walls it off; a 5th vertical's new shape = the OQ-A1 amendment
> discipline), (ii) the `LlmJudgment` schema or the ADR-007 `RecommendedAction`
> envelope contract would have to change (the amendment's UNCHANGED list,
> `0016:1270-1274`), or (iii) any inherited LOCK below must bend. Never bake a
> deviation in.

## Goal

Render the Accepted ADR-016 Q4 join/projection-grammar amendment into working code: a
`query` step can **declare** its multi-read join + projection as typed, authored,
deterministic spec surface, and the generic `QueryStepExecutor` compiles + runs it —
extending declared==dispatched from single reads (PLAN-0048) to **exactly the two shapes
the N=4 substrate uses** (`0016:1147-1159`): **(1) latest-per-group projection**
("latest reading per active Asset/Pond/Shipment" — the OCT query steps,
`verticals/aquaculture/procedures.yaml:64-72`, `verticals/energy/procedures.yaml:43-50`,
`verticals/supply_chain/procedures.yaml:43-50`) and **(2) multi-type equi-join
enrichment** (the procurement intake's join half,
`verticals/procurement/hero_demo/run.py:183-224`). Today multi-read is a typed refusal:
`plan_read` raises `ReadRefusal(unsupported_read_shape)` at `len(reads) > 1`
(`services/engine/procedures/query_step.py:167-175`) — this PLAN replaces that refusal
with a compiled, governed plan **when a valid `join`/`project` declaration is present**
(and keeps the refusal when it is not). Includes the SD-D substrate promotion
(`LinkTypeMeta.foreign_key` + ADR-0027 `join_path` → one execution-consumable typed
shape) that the ontology-declared default join requires. It does **NOT** migrate any
shipped vertical's `procedures.yaml` — that is the separate parity-guarded Phase-3 PLAN
(SD-C). Everything here is offline, deterministic, and MS-S1-independent: **no LLM
anywhere in the read path** (LOCKED-6 / ADR-0024 D3/D6).

## LOCKED (ratified in the amendment — render faithfully; do NOT re-litigate)

- **L-1 (SD-A, ratified).** Grammar surface = **HYBRID**: the ontology's declared
  `link_types.foreign_key` is the **default** join; a typed per-step **explicit
  override** covers exactly the shapes the ontology cannot declare — the intake's
  positional singleton fusion (`0016:1089-1093`) and custom projections
  (`0016:1121-1132`).
- **L-2 (SD-B, ratified).** v1 scope = **EXACTLY two shapes**: latest-per-group
  projection + multi-type equi-join enrichment. General group-by/aggregation math is
  OUT — it stays the `nl_query.py` surface (`0016:1147-1159`; PLAN-0048 wall `0048:98`).
- **L-3 (SD-C, ratified).** Seed co-existence + parity-guarded migration is a
  **separate Phase-3 PLAN** (`0016:1161-1172`). This PLAN builds grammar + executor +
  substrate; no shipped vertical's `procedures.yaml` or seed changes.
- **L-4 (SD-D, entailed).** Promote `LinkTypeMeta.foreign_key` to a typed
  `{from_property, to_property}` shape and parse ADR-0027 `join_path` into the SAME
  typed form — projection-layer only; the ADR-008 authored YAML grammar is untouched
  (`0016:1174-1186`).
- **L-5 (OQ-1, resolved).** The construct home = **`StepInput`** gains the typed
  `join`/`project` fields (`extra="forbid"`); this PLAN owns the literal schema
  (`0016:1284-1293`).
- **L-6 (OQ-2, resolved).** **NO repair loop**: exactly one `fetch_objects` dispatch
  per declared read; the documented D-N2 future contract stands unbuilt
  (`0016:1294-1301`; `0048:50`).
- **L-7 (OQ-3, resolved).** Grammar = **join + projection (field select/rename)
  ONLY**; arbitrary computation (the intake's `compliance`/criticality/qty→amount,
  `run.py:199-224`) stays downstream or in the co-existing seed (`0016:1302-1315`).
- **L-8 (OQ-4, resolved).** **Warn-first** override validation: a per-step override
  join not backed by a declared `link_types` relationship WARNS, never rejects
  (`0016:1316-1328`).
- **L-9 (inherited invariants — carried verbatim, `0016:1248-1269`).**
  `extra="forbid"` on `StepInput`/`Step`/`AgentAllowed` (`spec.py:214-250`); **no LLM
  in the read path**; `where` stays the engine-side post-fetch field-equality filter
  via the single `matches_where` predicate (`orchestrator.py:414-426`) — never pushed
  to the adapter; the single shared `read_bound_violation` predicate
  (`orchestrator.py:219-237`) is THE bound at BOTH the load gate
  (`validate_read_bindings`, `orchestrator.py:240-274`) AND run-time compile/dispatch
  — every joined/named object_type routes through it (PLAN-0048 AC-3, extended not
  forked); `reads` stays `list[str]`; empty `allowed.object_types` = unconstrained;
  `fetch_objects`-style object reads only (no `fetch_links`/`stream_events`); new
  grammar fields are **H-governed + pinned** — they join `STEP_GOVERNANCE_FIELDS`
  (`services/engine/procedures/draft.py:42-54`) and `build_governance_snapshot`
  (`services/engine/procedures/governance_pin.py:42-72`), so a mid-flight grammar edit
  fails CLOSED at resume (the PLAN-0048 SD-5(b) `reads` precedent,
  `governance_pin.py:66-70`).

## Substrate facts (verified on disk, 2026-07-09 — the extension points)

1. **The compile/execute seam.** `plan_read` (`query_step.py:116-181`) is pure/total:
   plan-or-refuse; the multi-read refusal at `:167-175` is the exact line this PLAN
   renders. `ReadPlan` (`:102-113`) carries a single `object_type` + `where`.
   `QueryStepExecutor` (`:214-285`) makes exactly ONE `fetch_objects` dispatch
   (`:261`), narrows post-fetch via `matches_where` (`:262-266`), emits a
   `read_provenance` trace (`:267-278`), and JSON-normalizes at the adapter boundary
   via `_json_safe` (`:198-211` — the datetime-in-JSONB guard joined rows also need).
   `ReadRefusalKind` (`:60-70`) has four values — additive extension allowed, existing
   values untouched.
2. **The construct home.** `StepInput` (`spec.py:214-250`): `extra="forbid"` (`:235`),
   `from_step`/`where`/`reads` (`:237-250`). OQ-1 adds `join`/`project` here.
3. **The bound + the gate.** `read_bound_violation` (`orchestrator.py:219-237`);
   `validate_read_bindings` (`:240-274`) **already iterates every entry of
   `step.input.reads`** through it (`:263-264`) — multi-read bound coverage at load
   exists; what Phase B adds is join/project **structural** validation.
   `plan_read` today bound-checks only `reads[0]` (`query_step.py:176-179`) because
   the multi-read refusal fires first — the extension must bound-check EVERY declared
   read at compile too.
4. **The substrate gap (SD-D).** `LinkTypeMeta` (`ontology_meta.py:102-108`) carries
   name/from_type/to_type/cardinality only; the loader (`:196-206`) **drops the YAML's
   `foreign_key`**. `QuantityBinding.grain`/`join_path` (`:66-77`) are free-text
   strings. The YAML data exists in every vertical: e.g.
   `verticals/energy/ontology/energy_v0.yaml:197-239` (`event_emitted_by_asset`
   `:205-209`, FK `OperationalEvent.asset_id -> Asset.asset_id` at `:209`);
   `verticals/procurement/ontology/procurement_v0.yaml:386-414` (`quotation_for_part`
   FK `:390`, `po_for_part` FK `:402`, `po_from_quotation` FK `:414`);
   `verticals/supply_chain/ontology/supply_chain_v0.yaml:119-123` (`join_path:
   OperationalEvent.shipment_id -> Shipment.shipment_id` at `:123`).
5. **Shape 1's target semantics.** The OCT query steps declare "latest X reading per
   active/in-transit Y" as facet prose only (aquaculture `read_do`
   `procedures.yaml:64-72`; energy `read_readings` `:43-50`; supply_chain `read_temps`
   `:43-50`) — no typed `reads` anywhere (PLAN-0048 fact 1). The house "latest"
   convention is argmax over the event timestamp: `max(crossing, key=lambda e:
   e["occurred_at"])` (`services/engine/demo_events.py:67`).
6. **Shape 2's target semantics.** `_intake_seed` (`run.py:183-224`) decomposes three
   ways (`0016:1080-1097`): (a) genuine equi-join — quotes filtered on
   `q["part_id"] == req["part_id"]` (`:192`), declarable via the procurement links
   (fact 4); (b) positional singleton fusion — failure event by
   `event_type == "failure"` (`:189`) + PO by the constant hero id (`:190-191`), NO
   relational key — only the explicit override form expresses it; (c) derived fields
   (`:193-224`) — OUT per L-7. The seed executor `_SeedQuery` (`run.py:130`, wired
   `:244`) is untouched (L-3).
7. **The H-governance machinery.** `STEP_GOVERNANCE_FIELDS` (`draft.py:42-54`)
   includes `reads` (`:52`); `_strip_read_binding` (`:176-188`) strips it at lift
   (`lift_to_step` `:191-221`, strip at `:217`) because `StepDraft` reuses the runtime
   `StepInput` — `join`/`project` ride the same struct and need the same strip.
   `build_governance_snapshot` pins sorted `reads` per step
   (`governance_pin.py:66-70`; format-change consequence documented `:24-30`).

## Acceptance Criteria

Everything below is **offline and deterministic**, each provable under the required CI
`gate` on a fresh PR (prove main-green via the PR's CI, not a named subset).

- [x] **AC-1 — SD-D promotion, backward-compat gated.** `LinkTypeMeta` gains a typed
      optional `foreign_key: {from_property, to_property}` (default `None`) parsed from
      the YAML `A.x -> B.y` string; `QuantityBinding` gains the SAME typed shape parsed
      from `join_path` (the free-text `join_path`/`grain` fields stay, additive
      sibling). Backward-compat gate (the PLAN-0050 pattern): every pre-existing
      projection field is **byte-identical** for all five verticals' ontologies; the
      new fields are additive-only; a pinned test asserts **every shipped `foreign_key`
      and `join_path` string parses successfully** (no shipped declaration regresses to
      `None`). A malformed/absent string projects to `None` — ontology load never gets
      stricter (SD-4).
- [x] **AC-2 — the typed construct is `extra="forbid"`, H-governed, and pinned.**
      `StepInput` gains `join`/`project` per the ratified SD-1 schema; every new model
      is `extra="forbid"`. `"join"` + `"project"` enter `STEP_GOVERNANCE_FIELDS`
      (`draft.py:42-54`), the lift strips them to absent stubs (extending
      `_strip_read_binding`, `:176-188` — a generated skeleton never self-declares its
      join surface), and `build_governance_snapshot` pins their canonical JSON per step
      (mirroring `reads`, `governance_pin.py:66-70`); a mid-flight `join`/`project`
      edit **fails CLOSED at resume** (tested). The pin-format consequence is disclosed
      in the PR body (pre-deploy `waiting_human` runs refuse at resume — the PLAN-0047
      sanctioned cancel-and-restart, the PLAN-0048 SD-5(b) precedent).
- [x] **AC-3 — the load gate governs the grammar (no execution yet at this AC).**
      `validate_read_bindings` extended: a declared-link join resolves its keys from
      the promoted typed `foreign_key` (refusing typed when the named link does not
      exist, does not connect the declared reads, or carries no parseable
      `foreign_key`); a `latest_per` link's `from_type` must equal the read it groups;
      an explicit `on`/fusion override **not backed by any declared relationship WARNS,
      never rejects** (L-8, asserted via `pytest.warns`); every object_type any
      join/read names routes through `read_bound_violation` at BOTH the gate AND
      `plan_read` — the PLAN-0048 AC-3 tripwire test extends to drive the same
      join-shape matrix through both and assert identical accept/refuse/warn decisions.
- [x] **AC-4 — shape 1 compiles + executes deterministically.** A single-read step with
      `project: {latest_per: <link>, order_by: <property>}` fetches ONCE, groups rows
      by the link's typed `from_property`, keeps argmax(`order_by`) per group with the
      SD-5 deterministic tie-break, applies field select/rename, and emits provenance
      (per-read fetched/post-where counts + rows-excluded-missing-key counts). Rows
      missing the group key or `order_by` are **excluded and counted in provenance**,
      never guessed.
- [x] **AC-5 — shape 2 compiles + executes deterministically.** A multi-read step with
      a `join` chain executes: one `fetch_objects` per declared read (exactly
      `len(reads)` dispatches — the D-N2 bound extended, asserted with a counting fake
      adapter), keys from the declared link by default, the explicit `on` override
      honored (with the load-time warn), and the `fuse` singleton form refusing typed
      when either side is not exactly one row post-narrowing. Output = flat merged
      rows (no nesting — L-7); collisions per the ratified SD-1 rule.
- [x] **AC-6 — end-to-end on the production paths via test fixtures.** BOTH shapes run
      end-to-end through `run_procedure` with test-module-embedded procedures + fake
      adapters over REAL shipped ontologies (energy for shape 1, procurement for shape
      2 — read-only; no vertical file changes, SD-3); shape 2 additionally runs through
      `run_procedure_persisted` proving the joined output set lands JSONB-safe
      (`_json_safe` covers merged rows) and the pinned `join`/`project` fields
      round-trip.
- [x] **AC-7 — existing behavior unchanged.** A join-absent single-read step is
      **byte-identical** to PLAN-0048 behavior (plan, dispatch, provenance, refusals);
      a join-absent multi-read still refuses `unsupported_read_shape` (the `:167-175`
      refusal narrows, does not vanish); the four existing `ReadRefusalKind` values are
      untouched (new kinds additive only); PLAN-0046/0047/0048 suites pass untouched;
      the hero-demo path is byte-unchanged.
- [x] **AC-8 — offline gate green.** Full suite + ruff + ruff-format + `mypy --strict
      services/` green under the required CI `gate` on a fresh PR; new API-facing
      fields carry `Field(description=...)`; **no MS-S1 / live-LLM call anywhere in
      any gate** (SD-6 — see Verification).

## Out of Scope

- ❌ **Phase 3: per-vertical production factories + seed migration + run-semantics
  parity tests** — the separate follow-up PLAN the amendment names (L-3 / SD-C,
  `0016:1161-1172`, `:1196-1199`). No shipped `procedures.yaml`, no seed retirement,
  no `_SeedQuery` change.
- ❌ **General aggregation math / `nl_query` unification** (L-2 / SD-B; the PLAN-0048
  wall `0048:98` stands — no `nl_query.py` change of any kind).
- ❌ **Any repair loop** (L-6 / OQ-2; the D-N2 future contract stays documentation).
- ❌ **`fetch_links` / `stream_events`** executors or bounds (inherited LOCK).
- ❌ **Changing the ADR-008 authored ontology grammar** — SD-D promotes the
  *projection* only; every vertical YAML is byte-untouched (L-4).
- ❌ **LLM anywhere in the read path** (L-9) — no proposal, selection, reshaping, or
  retry by a model; this PLAN never touches MS-S1.
- ❌ Nesting/aggregating joined rows into list-valued fields (the seed's
  `candidate_quotes` reshape) — a transform, not a join/projection (L-7); the fixture
  proves the flat join half only.
- ❌ UI/`GET /meta` rendering of the new typed fields (the payload gains additive keys;
  consuming them is a future UI concern).

## Surfaced Decisions

Build-level forks only — the direction is LOCKED above. Each SD carries a
recommendation; **Cray ratifies via AskUserQuestion (the 0058/0059/0060 pattern)**;
none is silently decided. ACs/Steps are written to the recommendations and re-scope
mechanically if Cray picks otherwise. **All six were RATIFIED as-recommended by Cray
(session 115, 2026-07-09, via AskUserQuestion):** SD-1 = the lean two-construct schema;
SD-2 = four phases / one PR each; SD-3 = test-module fixtures over real ontologies (no
shipped-file change); SD-4 = `JoinKeyMeta` additive, malformed→None; SD-5 = explicit
`order_by` + FK-`from_property` group key + primary-key tie-break; SD-6 = offline
binding bar only, no live run. The Recommendation/Alternatives/Why-Cray text below is
retained as the deliberation record; the ACs/Steps above are the settled shape.

- **SD-1 — the literal `join`/`project` schema on `StepInput`.**
  *Recommendation:* the lean two-construct shape, `extra="forbid"` throughout,
  covering exactly the two shapes and nothing speculative:

  ```yaml
  # shape 1 — latest-per-group over a declared link (ontology-default group key):
  input:
    reads: [OperationalEvent]
    project:
      latest_per: event_emitted_by_asset   # declared link; group key = its typed foreign_key.from_property
      order_by: occurred_at                # explicit ordering property (SD-5)
      fields: {measured_value: latest_do}  # optional select/rename (L-7) — omit to keep all fields

  # shape 2 — equi-join enrichment; base read = reads[0], each join names its side:
  input:
    reads: [OperationalEvent, PurchaseOrder, Quotation]
    where: {event_type: failure}           # narrows the BASE read post-fetch (existing semantics)
    join:
      - with: PurchaseOrder                # must be a declared read
        fuse: true                         # positional singleton fusion (Context (b)) — warn-first
        where: {po_id: PO-2025-4187}       # narrows the JOINED side post-fetch, pre-join
      - with: Quotation
        on: {left: part_id, right: part_id}  # explicit equi-key override — warn-first (L-8)
        # or: link: po_from_quotation        # declared-link default (keys from typed foreign_key)
  ```

  Pinned pipeline order (deterministic, one order): fetch each declared read once →
  step-level `where` narrows the base read; per-join `where` narrows that joined side
  (all via the single `matches_where` predicate — L-9 preserved: engine-side,
  post-fetch, never pushed down) → joins apply in declaration order producing flat
  merged rows → `project.latest_per`/`order_by` → `project.fields`. `JoinSpec` requires
  exactly one of `link`/`on`/`fuse`. Collision rule: an ontology-DECLARED property-name
  collision between joined types refuses at LOAD unless `project.fields` renames it
  (declared properties are known at load via `ObjectTypeMeta`); a runtime-only
  (adapter-extra) key collision keeps the base value and is counted in provenance —
  no silent clobber either way.
  *Alternatives:* (i) the amendment's minimal illustrative sketch (`join: [{on:
  part_id}]`, `0016:1134-1145` — explicitly non-binding) — cannot express the intake's
  fusion or per-side narrowing, so shape 2 stays un-declarable (defeats the amendment);
  (ii) a richer relational construct (nesting, computed fields, multi-key on-clauses) —
  speculative beyond the N=4 substrate, walled off by L-2/L-7.
  *Why Cray:* this fixes the public `extra="forbid"` spec grammar every future vertical
  author writes — the amendment explicitly assigns the literal schema to this PLAN's
  ratification (`0016:1131-1132`).

- **SD-2 — phasing.**
  *Recommendation:* **four phases, one PR each** (Steps 1–4): **A** SD-D substrate
  (additive, backward-compat gated) → **B** grammar schema + H-governance + load gate
  (no execution) → **C** compile/execute → **D** fixtures end-to-end + full oracle.
  Each phase lands green under CI `gate`; oracle-first (tests-before-impl) two-commit
  history inside each PR where practical (the PLAN-0048 pattern).
  *Alternative:* one monolithic PR — smaller overhead, but it couples an ontology-
  projection change, a spec-surface change, and executor semantics into one review and
  loses the per-boundary green guarantee.
  *Why Cray:* phase boundaries = review boundaries; Cray owns how much lands per
  ratifiable increment.

- **SD-3 — offline testing without migrating a shipped vertical.**
  *Recommendation:* **test-module-embedded fixtures over real shipped ontologies**:
  construct `Procedure`/`Agent` objects (declaring `join`/`project`) directly in the
  test modules, register fake adapters, and load the REAL energy + procurement
  ontology meta read-only for link/FK resolution — zero shipped-file changes, and the
  fixtures double as the documented authoring examples for Phase 3. (House gotcha,
  honored: no fixture files under `docs/plans/` — G2 fires on non-plan docs there;
  everything lives in committed test modules.)
  *Alternative:* temporarily migrate one shipped seed (e.g. aquaculture `read_do`) —
  **rejected**: that is Phase 3 by definition (L-3), changes demo-visible run
  semantics, and would need the parity guard this PLAN deliberately does not build.
  *Why Cray:* it decides whether any shipped vertical's observable behavior can move
  in this PLAN (recommendation: none can).

- **SD-4 — the SD-D typed shape, parser home, and backward-compat guarantee.**
  *Recommendation:* one Pydantic model `JoinKeyMeta {from_property: str, to_property:
  str}`; `LinkTypeMeta.foreign_key: JoinKeyMeta | None = None`
  (`ontology_meta.py:102-108`); `QuantityBinding` gains `join_key: JoinKeyMeta | None`
  parsed from the existing `join_path` string (`:66-77` — the string fields stay).
  Parser = one module-level helper in `ontology_meta.py` (both declaring surfaces, one
  parser — "one parsed join shape, two declaring surfaces", `0016:1182-1184`): parses
  `"A.x -> B.y"`, validates the type prefixes against the link's
  `from_type`/`to_type` (a mismatch parses to `None`). **Backward-compat guarantee:**
  additive-only — malformed/absent strings project to `None` (ontology LOAD never gets
  stricter than today); strictness bites only at the Phase-B load gate, only for steps
  that DECLARE a join needing that link (typed refusal); a pinned test proves every
  shipped FK/join_path parses (AC-1), so no shipped declaration silently degrades.
  *Alternatives:* parse-fail = load error (fail-closed at ontology load) — rejected:
  changes load behavior for YAMLs that load fine today, violating the byte-identical
  gate; a separate `join_meta.py` module — rejected: the projection already owns these
  models, and two homes invite drift.
  *Why Cray:* the promotion changes the `GET /meta` payload (additively) for every
  vertical and sets the failure posture of the declared-join substrate — an
  operational-surface call, not a drafter call.

- **SD-5 — latest-per-group semantics.**
  *Recommendation:* **the ordering field is explicit** — `project.order_by` names a
  declared property of the read type (no hard-coded field name; the fixtures use
  `occurred_at`, matching the house argmax convention, `demo_events.py:67`); the
  **group key = the declared link's typed `foreign_key.from_property`** (the amendment
  sketch's "group key = the link's declared foreign_key", `0016:1139`), with the load
  gate asserting the read type == the link's `from_type`. Determinism rules: per group
  keep max(`order_by`); ties break by the row's value at the read type's declared
  `primary_key` (max, lexicographic) — fully deterministic across adapter orderings;
  rows missing the group key or `order_by` are excluded + counted in provenance (never
  guessed, never crash the step).
  *Alternatives:* hard-code `occurred_at` (rejected — bakes one vertical's field name
  into engine grammar); ordering from `QuantityBinding.grain` (rejected — `grain` is an
  aggregation hint, not an ordering property, and not every read has a binding);
  first-row-wins ties (rejected — adapter-order-dependent = non-deterministic).
  *Why Cray:* these semantics define what "latest per active X" MEANS for every future
  declared projection — and Phase 3's parity tests will hold the migrated seeds to
  exactly this reading.

- **SD-6 — verification posture: offline binding bar ONLY.**
  *Recommendation:* **no live run of any kind.** Unlike PLAN-0060 (whose AC-7 needed a
  live model), every deliverable here is deterministic and MS-S1-independent — no LLM
  exists in the read path (L-9) — so the offline suite under CI `gate` is not just the
  binding bar, it is the ENTIRE bar. No host-state action, no Cray §8 gate needed, no
  `docs/logs/` live-evidence note.
  *Alternative:* a confirming live end-to-end demo run — rejected: nothing
  non-deterministic exists to confirm; it would be a pure host-state cost
  (CLAUDE.md §8 minimize-live-runs) with zero evidence value.
  *Why Cray:* §8 makes live-run posture explicitly Cray's call; this SD records the
  deliberate decision NOT to ask for one, so its absence is a ratified choice rather
  than an omission.

## Steps

Build order = cheapest gate first; the suite stays green at every phase boundary.

### Step 1 — Phase A: the SD-D substrate promotion (AC-1)
`ontology_meta.py`: add `JoinKeyMeta` + the one shared `A.x -> B.y` parser; populate
`LinkTypeMeta.foreign_key` in the loader (`:196-206` — stop dropping the YAML key) and
`QuantityBinding.join_key` beside the kept `join_path` string (`:66-77`). Tests: the
PLAN-0050-style backward-compat gate (pre-existing projection fields byte-identical for
all five verticals; new fields additive), the all-shipped-FKs-parse pin (energy
`:197-239`, procurement `:386-414`, supply_chain `join_path` `:123`, + aquaculture +
vet_clinic as declared), malformed-string → `None`, prefix-mismatch → `None`. Zero
behavior change anywhere else — no consumer reads the new fields yet.

### Step 2 — Phase B: grammar schema + H-governance + load gate (AC-2, AC-3)
`spec.py`: `JoinSpec`/`ProjectSpec` (+ nested `JoinOn`) per the ratified SD-1, wired
into `StepInput` (`:214-250`), all `extra="forbid"`, every field
`Field(description=...)`. H-governance: `"join"`/`"project"` into
`STEP_GOVERNANCE_FIELDS` (`draft.py:42-54`); extend the lift strip (`:176-188`,
applied at `:217`) so a generated draft's `join`/`project` become absent stubs (the
disjointness test extends); pin canonical JSON per step in `build_governance_snapshot`
(mirroring `reads`, `governance_pin.py:66-70`) + the fail-closed resume-mismatch test +
the PR-body pin-format disclosure. Load gate: extend `validate_read_bindings`
(`orchestrator.py:240-274`) with the SD-1 structural checks (link exists/connects/has
typed FK; `latest_per` direction; `with` ∈ `reads`; declared-collision rule;
`order_by`/`primary_key` declared on the read type) + the L-8 warn-first override
warning; every named object_type keeps routing through `read_bound_violation`
(`:219-237`). No execution change — `plan_read` still refuses multi-read at this
boundary.

### Step 3 — Phase C: compile + execute the two shapes (AC-4, AC-5, AC-7)
`query_step.py`: extend `ReadPlan` (or add a sibling multi-read plan carrying the
resolved typed join keys + projection) and `plan_read` (`:116-181`) — a valid
`join`/`project` declaration compiles (bound-checking EVERY declared read via
`read_bound_violation`, closing fact-3's reads[0]-only note); join-absent multi-read
keeps refusing `unsupported_read_shape` (the `:167-175` message updates honestly);
new refusal kinds are additive (existing four untouched). Extend
`QueryStepExecutor.execute` (`:236-285`): exactly one `fetch_objects` per declared
read (counting-fake-adapter property test — the D-N2 bound extended), the SD-1
pipeline order, the SD-5 argmax + tie-break + excluded-row provenance, `_json_safe` at
every adapter boundary, per-read provenance entries. Byte-identical single-read
no-regression sweep (AC-7).

### Step 4 — Phase D: offline binding bar end-to-end (AC-6, AC-8)
Test fixtures per SD-3: shape 1 end-to-end over the real energy ontology
(`event_emitted_by_asset`, fake adapter shipping multiple readings per asset +
rows with missing keys) and shape 2 end-to-end over the real procurement ontology
(declared-link join + `on` override + `fuse` fusion, flat merged rows, non-singleton
fusion refusal) through `run_procedure`; shape 2 through `run_procedure_persisted`
(JSONB-safe joined output; pinned `join`/`project` round-trip). Full oracle: suite +
ruff + ruff-format + `mypy --strict services/` green under CI `gate` on a fresh PR.
Conventional commits `feat(engine): ...` referencing PLAN-0061; Code commits via PR per
CLAUDE.md §7 (ADR-009 D2).

## Verification

How do we know it worked? **Binding — and complete (SD-6):** the AC matrix, entirely
offline under the required CI `gate` on a fresh PR. The deterministic properties are
tested as properties: one-dispatch-per-declared-read (counting fake adapter),
identical gate/compile decisions on the same join matrix (the extended AC-3 tripwire),
argmax + tie-break determinism, refusal-vs-warn split (`pytest.warns`), fail-closed
pin at resume, and the byte-identical no-regression sweeps (single-read behavior,
ontology projection, hero demo). **There is NO live run** — this PLAN is deterministic
and MS-S1-independent end to end (no LLM in the read path, L-9); the offline oracle is
not just the gate, it is the entire bar. **Honest enforcement frame (LOCKED-9
inherited):** after this PLAN, a query step that DECLARES `join`/`project` and runs
under the generic executor is declared ✔ · load-gated ✔ · execution-bound ✔ for the
two v1 shapes; the four shipped verticals' hand-written seeds remain
**execution-bound ✖** until the Phase-3 migration PLAN lands their parity-guarded
`procedures.yaml` declarations — nothing here may claim otherwise.

## Open Questions

- **OQ-1 — new `ReadRefusalKind` member naming** (e.g. `unresolvable_join` /
  `join_shape_violation` for non-singleton fusion, unconnectable links, collision
  refusals). Additive either way; settle at Step 3 review against the existing
  taxonomy's grain (`query_step.py:60-70`).
- **OQ-2 — the warn channel for L-8.** `warnings.warn` with a dedicated
  `ProcedureWarning` category (testable via `pytest.warns`, recommended default in the
  Steps) vs a structured load-report the API could surface later. Settle at Step 2
  review; the ratified semantics (warn, never reject) are fixed either way.
- **OQ-3 — `project.fields` rename-collision edge** — whether a rename may TARGET an
  existing kept field name (recommend: load-time refusal, same rule as declared
  collisions). Settle at Step 2 review.

## Size estimate

**M–L.** Four phased PRs: a contained ontology-projection promotion (Step 1), a
spec + governance + gate extension (Step 2), the executor semantics core (Step 3 — the
genuinely new logic: join pipeline + latest-per-group), and a fixture/oracle pass
(Step 4). No migration, no UI, no live runs; the blast radius is bounded by AC-7's
byte-identical guarantees.

---

*PLAN-0061 drafted by the in-harness `plan-drafter` subagent (2026-07-09), ADR-013 D1
phased governance authoring (ADR-009 D1). It executes the Accepted ADR-016 Q4
join/projection-grammar amendment (`0016:1010-1377`) — SD-A/B/C/D and OQ-1..OQ-4 are
LOCKED and none is reopened; six build-level forks are surfaced (SD-1..SD-6) with
recommendations, none silently decided. Author≠reviewer (ADR-012 D4.3): drafter =
plan-drafter; reviewers = Code R2 (every citation re-verified on disk) + Cray at SD
ratification (AskUserQuestion) and PR merge — separation INTACT. Drafted uncommitted;
Code commits via a `docs/*` PR (ADR-009 D2); the drafter does not git. AI-assisted
(plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
