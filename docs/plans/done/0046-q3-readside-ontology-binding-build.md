# PLAN-0046: Q3 read-side ontology object-binding — the typed read contract + load-time consistency & scoping gate (renders ADR-016 D2+D3 Q3 amendment, Accepted 2026-07-01)

**Status:** **Complete** (executed + merged 2026-07-02, session 93 — PR #511 `878b517`, merge `d95f0a2`; all 11 ACs met; full offline suite 2066 passed / 5 skipped)

> **Completion note (2026-07-02, session 93).** Executed in ONE PR (**#511**, feat
> `878b517`, merge `d95f0a2`) the morning after ratification. **AC→PR mapping:**
> AC-1..3 (the typed read contract — `StepInput.reads: list[str] | None` +
> `AgentAllowed.object_types`, backward-compat) / AC-4..8 (the
> `validate_read_bindings` load-gate per **SD-1 = Option A** — pure entry point +
> the `validate_read_bindings_for_vertical` production wrapper wired at
> `run_procedure` + `persistence.resume_run`; `validate_runnable`'s signature +
> all ~12 call-sites untouched; the AC-5 refuse pass/fail read pre-committed in
> the test module BEFORE the tests; the AC-7 wiring test runs against the REAL
> aquaculture registry) / AC-9..10 (H-governance — `reads` ∈
> `STEP_GOVERNANCE_FIELDS`; `object_types` confirmed covered via `allowed`,
> asserted not re-added) / AC-11 (ruff + ruff-format + `mypy --strict services/`
> clean; **full offline suite 2066 passed / 5 skipped**) — all in #511.
> **SD dispositions:** SD-1 = Option A (built as ratified); SD-2 = Option A (no
> vertical migrated — the gate proven on fixtures + the real registry; inert
> until opt-in). **One build-level hardening beyond the PLAN's letter
> (disclosed in the PR, consistent with OQ-A "never model-emitted", no ADR
> decision changed):** `StepDraft` REUSES `StepInput`, so a generated draft CAN
> physically carry `reads` — `lift_to_step` now strips it to an ABSENT stub
> (`_strip_read_binding`, the OQ-C C1 inject-absent pattern / the `env_var`
> precedent) with a CI tripwire test (`test_lift_strips_reads_from_draft_input`).
> **Honest frame delivered as LOCKED-9:** declared ✔ · consistency-gated at
> load ✔ · execution-bound ✖ (the Q4 generic run-consume executor remains a
> SEPARATE later PLAN). Offline-only — no host-state, no live run.
**Owner:** Claude Code
**Created:** 2026-07-01
**Related ADRs:** ADR-016 (the decision spine — this PLAN *renders* the **D2 + D3 Amendment (2026-07-01): typed read-side ontology object-binding for query steps (Q3)**, Accepted session 93; renders its ratified OQ-1..6/A + the honest declared/consistency-gated/execution-bound enforcement frame + the "Implementation note" seam it explicitly flagged as a build task). Also: ADR-016 D2 (the `Step`/`StepInput` grammar this extends), D3 (the `Agent.allowed` blast-radius allowlist this mirrors on the read side), D2 Amendment 2026-06-25 (D2-A2: `facet.input` stays non-authoritative prose → the typed `reads` is the source of truth), ADR-0024 D3 (the G/H governed≠generated partition + the draft-disjointness machinery `reads` must join), ADR-0025 / PLAN-0042 (the AT-2 build whose `governance_content`-added-to-`STEP_GOVERNANCE_FIELDS` precedent this exactly mirrors for `reads`), ADR-007 D1 (the `DataAdapter` contract — untouched), ADR-008 (the ontology the object_type names resolve against — untouched), ADR-006 (Rule-of-Three: N=4 query steps justify extracting the read-binding schema now), ADR-009 D1/D2 (drafter authors ungated, only Code commits), ADR-012 D4.3 (author≠reviewer disclosure), ADR-013 (the in-harness `plan-drafter` is the phased governance drafter). Substrate: `services/engine/procedures/{spec.py,orchestrator.py,draft.py,persistence.py}`, `services/engine/ontology_meta.py`, `services/engine/data_adapter.py`, `verticals/*/procedures.yaml`.

> **Provenance / author≠reviewer disclosure (ADR-012 D4.3).** Originator = Cray (the s84 design direction "bind query steps to ontology objects; the mapping layer absorbs source diversity" + the Rock 3 / O-2 read-side gap) + ADR-016's Q4/OQ-2 ratification that named a **fast-follow build PLAN** as the vehicle for the contract-first delivery. Drafter = the in-harness `plan-drafter` subagent (ADR-013 phased authoring path / ADR-009 D1). Independent reviewer = Cray at PR-merge ratification + Code R2-verification (fact-pack re-checked on disk). Drafter ≠ ratifier — separation **INTACT**. **Build PLAN — NO new ADR, no new decisions** beyond what ADR-016 Q3 OQ-1..6/A already ratified. Drafted **uncommitted**; Code R2-reviews + commits via a `docs/*` PR (ADR-009 D2). The drafter does not git.

---

## Goal

Render the **Accepted** ADR-016 Q3 amendment (D2+D3, session 93) into an executable v1 that delivers the read side a **typed read contract + a load-time consistency & scoping gate**, exactly as ratified — **contract-first, zero runtime-data-flow change**. Concretely: (1) type the read entry point — `StepInput.reads: list[str] | None` (OQ-1=`StepInput` sub-field; OQ-5=`list[str]`; keep `extra="forbid"`; distinct from and additive to `from_step`) — and the read-side blast-radius allowlist — `AgentAllowed.object_types: list[str]` (default_factory=list, mirroring `action_handlers`; OQ-6 empty=UNCONSTRAINED); (2) add the **load-time gate**: for each `kind == query` step with `input.reads` set, each named object_type MUST exist in the vertical's `ObjectTypeMeta` **AND** be in the running `Agent.allowed.object_types`, else refuse to load (`ProcedureError`) — mirroring how an un-allowlisted `action_handler` is refused, at pre-flight, touching **no runtime data flow**; (3) wire `reads` into the H-governance partition (`STEP_GOVERNANCE_FIELDS` + the draft-disjointness CI — `object_types` is already covered via `allowed ∈ AGENT_GOVERNANCE_FIELDS`); (4) prove it with the offline suite (the binding gate per CLAUDE.md §8) — accept/refuse, multi-object list, backward-compat (every shipped procedure + hero-demo still loads with the gate inert), H-governance disjointness. **The honest enforcement frame is preserved verbatim: declared ✔ · consistency-gated at load ✔ · execution-bound ✖** (execution-binding arrives with the deferred Q4 generic executor). This extends the shipped engine (ADR-016) + the shipped draft layer (ADR-0024) — **not** a new engine; the generic run-consume query executor (Q4) is a **separate later PLAN** (Out of Scope).

## Fact-pack findings (verified on main @ cb7eb05 via Read/Grep over the UNC mount)

Confirm the ADR's cited substrate + surface the one wiring nuance the ADR itself flagged as a build task. These bind the build (the live files, not the ADR prose).

1. **`StepInput` carries only `from`/`where` today, under `extra="forbid"`.** `spec.py:110-132` — `from_step` (alias `from`) + `where`, `ConfigDict(extra="forbid", populate_by_name=True)`. `reads` is a **net-new known key** here; unknown keys stay rejected (Q1 keeps the `extra="forbid"` safety).
2. **`AgentAllowed = {step_kinds, action_handlers}`; no read bound.** `spec.py:589-597`, `ConfigDict(extra="forbid")`, both `list[...]` with `default_factory`. `object_types` is the exact read-side mirror of `action_handlers` (Q2).
3. **`validate_runnable(procedure, agent)` takes ONLY (procedure, agent) — NOT the ontology registry.** `orchestrator.py:126`. The write-side `action_handlers` bound is enforced here (`orchestrator.py:173` — a whole-`services/` grep finds enforcement **only** there). The empty-list conventions diverge exactly as the ADR OQ-6 noted: `step_kinds` empty = **unconstrained** (`orchestrator.py:161` — `if allowed_kinds and …`) vs `action_handlers` empty = **fail-closed** (`orchestrator.py:173`). v1 makes `object_types` follow the **`step_kinds` (empty=unconstrained)** convention (OQ-6); the sibling divergence is **noted, NOT fixed** here.
4. **The seam the ADR's "Implementation note" flagged is real.** `validate_runnable` has **2 PRODUCTION call-sites — `orchestrator.py:425` (`run_procedure`) + `persistence.py:91` — plus ~10 TEST call-sites** (`test_orchestrator.py` ×6, `test_example_procedures.py:50`, `test_generator_pipeline.py:270`, `test_draft_lift_governance.py:197`, `tests/verticals/procurement/test_fastenal_procedure.py:34`). **None** passes an `OntologyMeta`. The registry loader is `load_ontology_meta(vertical)` (`ontology_meta.py:99`) — it takes a **vertical string** and returns `OntologyMeta` with `.object_types: list[ObjectTypeMeta]` (each `.name`). So the load-gate has a clean way to *build* the object-name set from a vertical string. This **strengthens SD-1 Option A** (RESOLVED below): a separate `validate_read_bindings` leaves **ALL ~12** `validate_runnable` call-sites untouched, whereas threading into `validate_runnable` (Option B) would have churned all ~12 (not 3).
5. **`_resolve_input` / `_matches` never touch the adapter (the intra-run thread).** `orchestrator.py:301-330` — resolves input **only** from the prior-step output bag; the first step gets `[]`. So `from_step` is an **intra-run** thread, `reads` is the **data-sourcing entry point** — distinct axes, and the load-gate changes **zero** of this runtime path (ADR Q3 / Consequences).
6. **`object_types` is ALREADY H-governance-covered; `reads` is NOT.** `draft.py:65` — `AGENT_GOVERNANCE_FIELDS = {"llm_model","autonomy_ceiling","allowed"}`, and `object_types` lives *inside* `Agent.allowed` → auto-covered (confirm, do NOT re-add). `STEP_GOVERNANCE_FIELDS` (`draft.py:42-53`) does **not** contain `input`/`reads` → **`reads` must be ADDED** (OQ-A). The precedent is exact: PLAN-0042 added `governance_content` to `STEP_GOVERNANCE_FIELDS` the same way (`draft.py:51`). The disjointness CI lives in `tests/services/engine/procedures/test_draft_lift_governance.py`.
7. **No vertical declares `object_types` today; every query step names its object in prose only.** N=4 (aquaculture `read_do` / supply_chain `read_temps` / energy `read_readings` / procurement `read_stock`+`intake`). So the gate is **inert until a vertical opts in** (OQ-6 backward-compat) — which is the basis for the OQ-2 recommendation (do NOT migrate existing verticals in v1). procurement `intake` reads **three** object types + joins them (`OperationalEvent`+`PurchaseOrder`+`Quotation`, `hero_demo/run.py::_intake_seed`) — the reason OQ-5 ratified `reads` as `list[str]` and the reason the executor is deferred (Q4).

## LOCKED (from ADR-016 Q3 — render faithfully; do NOT re-litigate)

Each maps to a ratified Q3 decision (OQ-1..6/A, session 93). Built to, not reopened. If the fact-pack ever showed a LOCKED item *must* change to build it, that is an ADR-016 amendment (G-gated) — **STOP and surface**, never bake a deviation into the PLAN.

- **LOCKED-1 (Q1 / OQ-1 field placement).** The read binding is `StepInput.reads` (beside `from`/`where`), **not** a top-level `Step.reads`. `extra="forbid"` kept. Distinct from + additive to `from_step`. NOT on the non-authoritative `facet.input` (D2-A2 — the typed binding is the source of truth).
- **LOCKED-2 (OQ-5 cardinality).** `reads` is `list[str] | None`, **NOT** a single `str` (procurement `intake` reads 3 types; a later `str`→`list` widening would be a breaking `extra="forbid"` schema change).
- **LOCKED-3 (Q2).** `AgentAllowed.object_types: list[str] = Field(default_factory=list)` — shape + default mirror `action_handlers` exactly, under the existing `AgentAllowed(extra="forbid")`.
- **LOCKED-4 (Q3 / OQ-2 v1 depth).** v1 depth = **load-gate**: each `reads` element MUST **(a)** exist in the vertical's `ObjectTypeMeta` **AND (b)** be in `Agent.allowed.object_types`, else refuse to load. At **load / pre-flight** — **zero runtime-data-flow change**. Framed as a typed read contract + load-time consistency & scoping gate, **NOT** runtime-enforced parity.
- **LOCKED-5 (OQ-6 empty-list semantics).** Empty `object_types` = **UNCONSTRAINED** (backward-compatible, opt-in) — follow the **`step_kinds`** convention, **NOT** `action_handlers`' fail-closed. Do **NOT** "fix" the sibling `step_kinds`/`action_handlers` divergence — note it only.
- **LOCKED-6 (OQ-3 verb scope).** `object_types` bounds `fetch_objects`-style **object** reads ONLY in v1. `fetch_links` (link-typed) + `stream_events` (event-typed) are a **category mismatch** → explicitly OUT (a separate future bound).
- **LOCKED-7 (OQ-4 `reads` ↔ `where`).** `where` stays the engine-side **post-fetch** field-equality filter (unchanged `_matches`/`_resolve_input`); it is **NOT** pushed to the adapter's `filter_expr`. `reads` names **what** to fetch; `where` narrows the fetched set.
- **LOCKED-8 (OQ-A governance ownership).** Both `reads` and `object_types` are **HUMAN-GOVERNED (H)**. `object_types` is already covered (inside `allowed ∈ AGENT_GOVERNANCE_FIELDS`) — **confirm, do NOT re-add**. `reads` must be **ADDED** to `STEP_GOVERNANCE_FIELDS` + covered by the draft-disjointness CI.
- **LOCKED-9 (enforcement frame — honest, verbatim).** declared ✔ · consistency-gated at load ✔ · **execution-bound ✖** (deferred to Q4). v1 closes Gap (B) **as a load-time bound**, **not** runtime-enforced parity. This framing MUST appear in the PLAN's Verification + not be over-claimed.

## Acceptance Criteria

Grouped by build step. The **offline suite is the merge gate** (CLAUDE.md §8); there is **no live run** in this PLAN (no adapter fetch, no MS-S1 — the gate is pure load-time validation). Per CLAUDE.md §8 the pass/fail read for the refuse cases (AC-4/AC-5) is **pre-committed before the tests are written**.

### Step 1 — the typed read contract (Q1/Q2 — additive, gate not yet wired)

- [ ] **AC-1 — `StepInput.reads` (Q1 / LOCKED-1,2).** In `spec.py` `StepInput`: `reads: list[str] | None = Field(default=None, description=...)`, `extra="forbid"` unchanged, distinct from `from_step`. Absent `reads` loads byte-for-byte as today.
- [ ] **AC-2 — `AgentAllowed.object_types` (Q2 / LOCKED-3).** In `spec.py` `AgentAllowed`: `object_types: list[str] = Field(default_factory=list, description=...)`, `extra="forbid"` unchanged, shape mirrors `action_handlers`. Absent/empty `object_types` loads as today (UNCONSTRAINED — LOCKED-5).
- [ ] **AC-3 — additive no-regression (every shipped procedure + hero-demo still loads).** With Step 1's fields optional and the gate NOT yet wired, all shipped `verticals/*/procedures.yaml` still `load_procedures` and still pass the *current* `validate_runnable` (no vertical declares `reads`/`object_types` — fact-pack 7). Includes the hero-demo path.

### Step 2 — the load-time gate + the OntologyMeta-threading seam (Q3 — OQ-1 seam is the load-bearing task)

- [ ] **AC-4 — the load-gate ACCEPTS a consistent read binding.** A `kind == query` step with `reads=[X]` where `X ∈ vertical ObjectTypeMeta.names` AND `X ∈ agent.allowed.object_types` loads without error. Multi-object: `reads=[X, Y]` with both consistent also loads (LOCKED-2 — the gate iterates each element).
- [ ] **AC-5 — the load-gate REFUSES on either failed condition (`ProcedureError`), pass/fail pre-committed.** `reads=[X]` where **X ∉ ontology** → refuse; where **X ∈ ontology but ∉ allowlist** → refuse; a multi-object list with ANY element failing either condition → refuse. The message names the offending object_type + which condition it failed (mirrors the `action_handler` refusal `orchestrator.py:173`). The refuse pass/fail read is committed **before** the test is written.
- [ ] **AC-6 — OQ-6 backward-compat: empty `object_types` = UNCONSTRAINED.** An agent with `object_types=[]` running a query step **with `reads` set** does NOT trip the allowlist half of the gate (follows the `step_kinds` empty=unconstrained convention — `if agent_object_types and …`), so the gate only bites when the agent opts in. A query step with **no `reads`** never invokes the gate at all. (The sibling `action_handlers` fail-closed divergence is left UNTOUCHED — LOCKED-5.)
- [ ] **AC-7 — the OntologyMeta-threading seam is wired per SD-1 = Option A (RESOLVED, Cray-ratified session 93).** The seam adds a **new** entry point `validate_read_bindings(procedure, agent, object_type_names)` (an explicit registry arg — `frozenset[str]` of object-type names, built by callers via `load_ontology_meta(vertical).object_types`) invoked at the **2 PRODUCTION pre-flight sites — `run_procedure` (`orchestrator.py:425`) + `persistence.py:91` — beside `validate_runnable`**, WITHOUT touching `validate_runnable`'s `(procedure, agent)` signature or ANY of its ~12 call-sites (2 production + ~10 test — fact-pack 4). Testable with a fixture registry — no filesystem I/O inside the validator.
- [ ] **AC-8 — zero runtime-data-flow change (LOCKED-4,9).** `_resolve_input` / `_matches` / the hand-written seed executors (`hero_demo/run.py`) are **byte-unchanged**; the hero-demo + live paths are unaffected. The gate is pure load-time validation — no `adapter.fetch_objects` call is added anywhere in this PLAN.

### Step 3 — H-governance wiring (OQ-A)

- [ ] **AC-9 — `reads` added to `STEP_GOVERNANCE_FIELDS` (OQ-A / LOCKED-8).** `draft.py:42-53` gains `"reads"` (mirroring the PLAN-0042 `governance_content` precedent at `draft.py:51`). `reads` is NEVER declared on `StepDraft` (it stays a runtime/H field the generator cannot emit).
- [ ] **AC-10 — the draft-disjointness CI covers `reads`; `object_types` confirmed already-covered.** The disjointness test (`tests/services/engine/procedures/test_draft_lift_governance.py`) asserts `reads` is not reachable from any draft type — adding `reads` to a draft type later **fails CI**. `object_types` coverage via `allowed ∈ AGENT_GOVERNANCE_FIELDS` is **confirmed by an assertion, NOT re-added** (fact-pack 6).

### Step 4 — the offline oracle (CLAUDE.md §8)

- [ ] **AC-11 — the offline test suite is green (the merge bar).** Load-gate accept/refuse (AC-4/AC-5), multi-object list (AC-4), backward-compat — no `reads` / empty `object_types` still loads for **every** shipped procedure + hero-demo (AC-3/AC-6), H-governance disjointness (a draft type cannot carry `reads`; AC-10). `ruff` + `ruff-format` + `mypy --strict services/` clean; full offline suite passes; **no live MS-S1** (the gate is load-time only — no adapter fetch).

## Out of Scope

- ❌ **The generic run-consume query executor (Q4)** — resolves `reads` → `adapter.fetch_objects` → typed entities and retires the hand-written per-vertical seeds. A **SEPARATE later PLAN**, gated on this contract proving out (ADR-016 Q4). It touches runtime data flow (the hero-demo/live path) + the enrich/join query steps (procurement `intake` joins `OperationalEvent`/`PurchaseOrder`/`Quotation`). **Nothing in this PLAN calls `adapter.fetch_objects`.**
- ❌ **Migrating existing verticals to DECLARE `reads`/`object_types`** (OQ-2 below — recommend NO in v1; leave the gate inert until a vertical opts in). The gate proves out on a new/test procedure fixture.
- ❌ The **Box-4 economic-impact facet** (฿ dimension) — explicitly deferred by ADR-016 Q3 as a self-cancelling N≥3 marker (today N=1, procurement only). Not designed here.
- ❌ **`fetch_links` / `stream_events` read bounds** (OQ-3 — category mismatch; a separate future typed allowlist, likely alongside Q4).
- ❌ Any change to `from_step` input-binding, `where` (stays post-fetch engine-side — OQ-4), `kind`, `autonomy`, gates, or the D2 `facet` schema — all unchanged. Connectors-in-the-procedure (LOCKED OUT — the mapping layer absorbs source diversity, Cray s84). Any change to how the adapter is selected (`run_procedure`'s vertical string).
- ❌ **"Fixing" the `step_kinds`/`action_handlers` empty-list divergence** (OQ-6 — noted, not fixed).
- ❌ Editing constitutional / convention / lesson files (Code amends per ADR-009 D2 follow-on TODOs).

## Surfaced Decisions — RESOLVED (Cray-ratified 2026-07-01, session 93)

Each was surfaced with options + a fact-pack-grounded recommendation (plan-drafter discipline); **both are now Cray-ratified as recommended** and folded into AC-7 + Step 2 (SD-1) and Out of Scope + AC-4/5/6 (SD-2). These were **build-level** calls ADR-016 Q3 left to this PLAN; neither reopens a ratified Q3 decision.

- **SD-1 — THE crux: the OntologyMeta-threading seam (ADR-016 Q3 "Implementation note" — a real design task, not an OQ in the ADR).** `validate_runnable(procedure, agent)` (`orchestrator.py:126`) does NOT carry the vertical's `OntologyMeta` today, and it has ~12 call-sites (2 production + ~10 test — fact-pack 4). The load-gate needs the object-type registry to assert `reads ∈ ontology`. How should it reach it?
  - *Option A (recommended) — a SEPARATE load-gate entry point that takes the registry, called alongside `validate_runnable`.* A new `validate_read_bindings(procedure, agent, ontology_meta: OntologyMeta)` (or `object_type_names: frozenset[str]`) invoked at each pre-flight site next to `validate_runnable`. **Grounding:** keeps `validate_runnable`'s signature (procedure, agent) untouched → all ~12 call-sites (2 production + ~10 test) don't churn; the registry-building call (`load_ontology_meta(vertical)`) is threaded at the call-sites (which already know the vertical string), not buried in `validate_runnable`; smallest blast radius; mirrors how the write-side handler check is a discrete assertion. The caller passes the registry explicitly, so there is no hidden I/O inside the validator (testable with a fixture registry, no filesystem).
  - *Option B — thread `OntologyMeta` (or the vertical string) INTO `validate_runnable`.* One entry point, but changes a shipped signature with ~12 call-sites (2 production + ~10 test) and either forces every caller to supply a registry or makes the validator do a `load_ontology_meta(vertical)` I/O call internally (harder to unit-test, couples the pure validator to filesystem). More churn, less clean separation.
  - **Recommendation: Option A** — the separate `validate_read_bindings` entry point taking an explicit registry. It keeps the pure `validate_runnable` contract stable, isolates the new read-gate as an independently-testable unit, and threads the `load_ontology_meta(vertical)` call at the sites that already own the vertical string.
  - **✅ RESOLVED — Option A (Cray-ratified session 93).** New `validate_read_bindings(procedure, agent, object_type_names: frozenset[str])`, callers build the registry via `load_ontology_meta(vertical).object_types`, invoked at the 2 production pre-flight sites beside `validate_runnable`; `validate_runnable`'s `(procedure, agent)` signature and all ~12 call-sites stay untouched. Rationale: smallest blast radius (the Code R2 recount strengthens this — Option B would have churned all ~12, not 3) + no hidden I/O in the pure validator. The seam is now DECIDED, not contingent — see AC-7 + Step 2.
- **SD-2 — migrate existing verticals to declare `reads`/`object_types` in v1, or leave them absent (gate inert)?** No vertical declares either today (fact-pack 7), so the gate is inert until opt-in (OQ-6 backward-compat).
  - *Option A (recommended) — leave all four verticals ABSENT; prove the gate on a new dedicated test fixture procedure/agent.* **Grounding:** OQ-6 designed the gate to be inert-until-opt-in precisely so v1 lands at zero blast radius; a shipped-vertical migration is a **value-authoring** act (which objects each agent may read is an H-governed blast-radius decision — LOCKED-8) that belongs with the Q4 executor when reads become executed, not decorative; keeps this PLAN's diff to the schema + gate + tests. The accept/refuse ACs (AC-4/AC-5/AC-6) exercise the gate against a purpose-built fixture, which is a cleaner oracle than retrofitting a shipped procedure.
  - *Option B — add a single token opt-in example* (e.g. aquaculture `read_do` declares `reads=[Pond]` + its agent declares `object_types=[Pond]`) to demonstrate a live opt-in.
  - **Recommendation: Option A** (leave absent; gate proves out on a fixture). If Cray wants a demonstrable opt-in for the demo narrative, Option B is a one-line follow-on — but authoring an agent's real read reach across four verticals is Q4-adjacent H-authoring, not a v1 schema concern.
  - **✅ RESOLVED — Option A (Cray-ratified session 93).** No vertical declares `reads`/`object_types` in v1; the gate is inert until opt-in. "Migrate existing verticals" stays in Out of Scope; the accept/refuse ACs (AC-4/AC-5/AC-6) exercise a purpose-built fixture procedure+agent. Rationale: OQ-6 designed the gate to land at zero blast radius, and shipped-vertical migration is Q4-adjacent H-authoring, not a v1 schema concern.

## Steps

Build order: the typed fields land first (Step 1, additive — everything still loads because the gate is not yet wired), then the gate + its seam (Step 2, the load-bearing SD-1 work), then the H-governance wiring (Step 3), then the offline oracle (Step 4).

### Step 1 — the typed read contract (AC-1..AC-3)
- `spec.py` `StepInput`: add `reads: list[str] | None = Field(default=None, description="ontology object_types this query step reads (each must exist in the vertical's ObjectTypeMeta AND be in Agent.allowed.object_types) — ADR-016 Q3")`. Keep `extra="forbid"`. Distinct from `from_step`.
- `spec.py` `AgentAllowed`: add `object_types: list[str] = Field(default_factory=list, description="ontology object_types this agent may read (Q3 load-gate)")`. Keep `extra="forbid"`. Mirror `action_handlers`.
- Tests (`tests/services/engine/procedures/test_spec.py`): the new fields load; absent `reads` / empty `object_types` load unchanged; every shipped vertical + hero-demo still `load_procedures` (AC-3).

### Step 2 — the load-gate + the OntologyMeta seam (AC-4..AC-8)
- **SD-1 = Option A (RESOLVED — Cray session 93).** Add `validate_read_bindings(procedure, agent, object_type_names: frozenset[str])` in `orchestrator.py` beside `validate_runnable`; iterate each `kind == query` step's `reads` (if set), assert each element `∈ object_type_names` AND (if `agent.allowed.object_types` non-empty — OQ-6) `∈ agent.allowed.object_types`, else raise `ProcedureError` naming the object_type + failed condition. Thread `load_ontology_meta(vertical).object_types` → `frozenset(m.name for m in …)` at the **2 production pre-flight call-sites** (`run_procedure` `orchestrator.py:425`, `persistence.py:91`), which already own the vertical string. `validate_runnable`'s signature + all ~12 of its call-sites stay untouched.
- Pre-commit the pass/fail read for the refuse cases (AC-5) **before** writing the test.
- Confirm `_resolve_input`/`_matches`/`hero_demo/run.py` are byte-unchanged (AC-8) — no `adapter.fetch_objects` added.
- Tests (`test_orchestrator.py`): accept (single + multi-object list), refuse (∉ ontology, ∉ allowlist, mixed list), empty-`object_types`-unconstrained, no-`reads`-never-gates.

### Step 3 — H-governance wiring (AC-9/AC-10)
- `draft.py`: add `"reads"` to `STEP_GOVERNANCE_FIELDS` (`:42-53`, mirroring `governance_content` at `:51`); keep `reads` off `StepDraft`.
- Tests (`test_draft_lift_governance.py`): extend the draft-disjointness assertion to cover `reads` (a draft type carrying `reads` fails CI); add a confirming assertion that `object_types` is covered via `allowed ∈ AGENT_GOVERNANCE_FIELDS` (do NOT re-add it).

### Step 4 — the offline oracle (AC-11)
- Full offline suite green; `ruff` + `ruff-format` + `mypy --strict services/` clean; no live MS-S1 (the gate is load-time only).

## Verification

Mapped to the gate-vs-evidence split (CLAUDE.md §8). Because v1 is a **load-time gate with zero runtime-data-flow change**, **the gate is fully offline and there is no live run in this PLAN** (no adapter fetch, no MS-S1).

- **Gate (CI / offline) — the binding bar:** the load-gate accepts a consistent binding + multi-object list (AC-4); refuses ∉-ontology / ∉-allowlist / mixed-list, pass/fail pre-committed (AC-5); empty `object_types` = unconstrained + no-`reads`-never-gates (AC-6); the SD-1 seam wired without churning the three `validate_runnable` call-sites (AC-7); the H-governance disjointness covers `reads` (AC-10); `ruff` + `ruff-format` + `mypy --strict services/` clean (AC-11).
- **No-regression:** every shipped procedure + the hero-demo still `load_procedures` and still pass the *current* `validate_runnable` (fact-pack 7 — no vertical declares the new fields); `_resolve_input`/`_matches`/the hand-written seeds byte-unchanged (AC-8); the ADR-007 approve→execute write gate + the D2 `facet` schema + `from_step`/`where` all untouched.
- **Honest enforcement frame (LOCKED-9 — must not be over-claimed):** the PLAN delivers **declared ✔ · consistency-gated at load ✔ · execution-bound ✖**. v1 closes Gap (B) as a **load-time bound**, NOT runtime-enforced parity — even the write-side `action_handlers` is only pre-flight-checked (`orchestrator.py:173`); its runtime teeth come from declared==dispatched, the property the read side gains only at Q4. The Verification MUST not claim a runtime read-gate.
- **STOP-and-surface:** if building any LOCKED item reveals an Accepted ADR-016 Q3 decision must change, that is an ADR-016 amendment (G-gated) — surface to Cray, do not bake a deviation into the build.

---

*PLAN-0046 drafted (uncommitted) by the in-harness `plan-drafter` subagent (session 93+), ADR-013 phased governance authoring (ADR-009 D1). Its shape is LOCKED by the ADR-016 D2+D3 Q3 amendment (Accepted 2026-07-01) — a focused **build/execution** PLAN, **no new ADR, no new decisions** beyond OQ-1..6/A. It renders the Accepted Q3 amendment's Decision + the honest declared/consistency-gated/execution-bound frame + the "Implementation note" seam it explicitly flagged as a build task. **Both Surfaced Decisions are now RESOLVED (Cray-ratified session 93): SD-1 = Option A (separate `validate_read_bindings` entry point) + SD-2 = Option A (leave verticals absent, prove on a fixture)** — folded into AC-7 + Step 2 (SD-1) and Out of Scope + AC-4/5/6 (SD-2). Reviewer chain: Code R2 (fact-pack re-checked on disk, incl. the `validate_runnable` call-site recount → 2 production + ~10 test, which strengthens SD-1 Option A) + Cray ratification of both SDs. Author≠reviewer (ADR-012 D4.3): drafter = plan-drafter, reviewer = Cray at PR merge + Code R2 — separation INTACT. **Status: Ready for execution.** Code R2-reviews + commits via a `docs/*` PR (ADR-009 D2). The drafter does not git. AI-assisted (plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
