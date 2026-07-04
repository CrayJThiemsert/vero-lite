# PLAN-0048: Q4 generic run-consume query executor — declared==dispatched for the read side (renders ADR-016 Q4, the Q3-amendment fast-follow)

**Status:** Complete
**Completed:** 2026-07-04 (session 96) — all 15 ACs met; PRs #533–#539.
**Ratified:** 2026-07-04 — SD-1..SD-5 adjudicated **as-recommended** by Cray (typed in-session: "approve SD-1..5 ตาม recommended", relayed via the Code dispatch); the draft merged to main unchanged via `docs/*` PR #533 (merge `761f33d`) per ADR-009 D2
**Owner:** Claude Code
**Created:** 2026-07-04
**Related ADRs:** ADR-016 (the authorizing decision — this PLAN *renders* **Q4** of the D2+D3 Q3 read-side amendment, Accepted 2026-07-01 session 93: "the executor that resolves a query step's `object_type` → `adapter.fetch_objects` → typed entities … is deferred to a fast-follow build PLAN, gated on this amendment Accepted" — it IS Accepted, so this PLAN needs **NO new ADR**; it also renders the ratified OQ-3 (fetch_objects-only bound), OQ-4 (`where` = engine-side post-fetch), OQ-5 (`reads: list[str]`), OQ-6 (empty allowlist = unconstrained) dispositions and the honest declared/load-gated/execution-bound enforcement frame). Also: ADR-007 D1 (the `DataAdapter.fetch_objects` contract this consumes — untouched), ADR-0023 (explicit registry registration — the executor-factory seam this composes into), ADR-0024 D3/D6 (governed ≠ generated — no LLM in the read path), ADR-0019 / ADR-010 IN-3 (determinism invariant precedent the executor mirrors), ADR-006 (Rule-of-Three), ADR-009 D1/D2 (drafter authors ungated; only Code commits), ADR-012 D4.3 (author≠reviewer disclosure), ADR-013 (in-harness `plan-drafter` = phased governance drafter). Substrate: PLAN-0046 (the shipped Q3 contract + load gate this executes), PLAN-0047 Steps 2/4/5/6 (executor-factory seam #526, write-ahead persistence, hash-chained audit_log, per-run governance pinning — the layer this must behave correctly on). Research absorbed (gitignored, on-disk): `docs/research/private/2026-07-03-llm-db-reliability-techniques.md`, `docs/research/private/2026-07-03-semantic-foundation-build-techniques.md`, `docs/research/private/2026-07-03-ontology-llm-market-landscape.md`.

> **Provenance / author≠reviewer disclosure (ADR-012 D4.3).** Originator = Cray — the 2026-07-04 Wave-2 item (a) pick per the session-95 CLOSE handoff (the four ratified design musts: refusal UX, bounded in-allowlist retry, OSI/MCP-aware 3-tool seam, production executor-factory follow-up) — on top of ADR-016 Q4's own ratified deferral naming this exact fast-follow PLAN. Drafter = the in-harness `plan-drafter` subagent (ADR-013 phased authoring / ADR-009 D1). Independent reviewer = Code R2 (fact-pack re-checked on disk) + Cray at SD ratification and PR merge. Drafter ≠ ratifier — separation **INTACT**. Build PLAN — **no new ADR, no ratified Q3/Q4 decision reopened**; genuinely open build-level forks are surfaced as SD-1..SD-5 below, each with a recommendation, none silently decided. Drafted **uncommitted**; Code R2-reviews + commits via a `docs/*` PR (ADR-009 D2). The drafter does not git.

---

## Goal

Render the **Accepted** ADR-016 Q4 decision into a working v1: an **engine-owned, deterministic, generic query-step executor** that resolves a `query` step's declared `input.reads` → `adapter.fetch_objects(object_type)` → the step's threaded output set — giving the read side the **declared==dispatched** property the write side already has (the executor dispatches EXACTLY what the spec declares, as `step.handler` is exactly what the action executor dispatches today). Concretely: (1) a pure **compile** seam (`plan_read`) that turns a step + agent + ontology registry into an executable read plan **or a typed, auditable refusal** — out-of-ontology, outside-allowlist, or unsupported-shape reads **refuse loudly, never guess, never return a silent `[]` that masquerades as "no data"**; (2) the **execute** half (`QueryStepExecutor`, adapter-injected, zero LLM involvement — governed ≠ generated) with a **testable bounded-dispatch property**: exactly one `fetch_objects` call per declared object_type, every dispatch inside `reads ∩ Agent.allowed.object_types`, no retry/repair loop in v1; (3) OQ-4 rendered at run time — `where` narrows the **fetched** set engine-side via the single shared `_matches` predicate (never pushed to the adapter's `filter_expr`); (4) correct behavior on **both** production paths — `run_procedure` (in-memory) and `run_procedure_persisted` (PLAN-0047 write-ahead: the read step's output set and any refusal land as durable per-step records) — without weakening governance pinning; (5) the interface factored to the **compile / execute / inspect** 3-tool shape (dbt-MCP `list/discover + constrained run` convergence — semantic-foundation brief F8) as a clean seam, with MCP plumbing an explicit non-goal. The executor is the **shipped engine default for plain declared reads**; the fate of the four verticals' hand-written projection/join seeds is SD-3 (fact-pack 8: none of them is a plain fetch). Enforcement frame after this PLAN (honest, no over-claim): steps run by the generic executor are **declared ✔ · load-gated ✔ · execution-bound ✔**; steps still on hand-written seeds remain **execution-bound ✖** until migrated.

## Fact-pack findings (verified on main @ 353c04e via Read/Grep over the UNC mount; code-identical to 943a276 — #531 was docs-only)

These bind the build (the live files, not recalled prose).

1. **The Q3 contract + load gate shipped exactly as ratified.** `spec.py:110-145` — `StepInput.reads: list[str] | None` beside `from`/`where`, `extra="forbid"`; `spec.py:603-615` — `AgentAllowed.object_types` mirroring `action_handlers`. The pure gate `validate_read_bindings(procedure, agent, object_type_names)` + the `validate_read_bindings_for_vertical` wrapper + the `has_read_bindings` skip-predicate live at `orchestrator.py:182-245`, wired at **both** production pre-flight sites: `run_procedure` (`orchestrator.py:494`), `run_procedure_persisted` (`persistence.py:79`), and `resume_run` (`persistence.py:235`). No vertical declares `reads`/`object_types` (gate inert — PLAN-0046 SD-2 = Option A).
2. **The executor seam is a per-kind Protocol; failure = raise.** `StepExecutor.execute(step, input_set, ctx) -> StepOutcome` (`orchestrator.py:105-110`); D4 fail-and-divert catches ANY raise and records `reasoning_trace=[{"kind": "error", "summary": f"{type}: {exc}"}]` (`orchestrator.py:577-597`) — the trace **flattens the exception to a string** today, so a *structured* refusal record needs a small disclosed enrichment of that catch (Step 2). `on_failure: escalate_to_human` routes a raising step to `waiting_human` (the refuse → explain → escalate UX comes for free).
3. **`where` today filters the BAG-resolved input, not a fetched set.** `_resolve_input`/`_matches` (`orchestrator.py:369-398`) resolve a step's input from prior-step outputs only; the first step gets `[]`. OQ-4's "post-fetch field-equality filter over the fetched set" therefore MUST be applied **inside the executor** (the orchestrator never sees the fetched set) — reusing the same `_matches` predicate so spec semantics cannot drift.
4. **The adapter contract:** `DataAdapter.fetch_objects(object_type, filter_expr=None, limit=1000) -> list[dict]` (`data_adapter.py:36-43`); the engine keeps the narrowing (`filter_expr` NOT used — OQ-4 ratified). Adapters registered per-vertical via `registry.get_adapter(vertical)` (`registry.py:71-76`). Every existing engine read consumer works over **raw dicts** (`nl_query.py:1048-1055`, `_matches`, `evaluate_step.py:40` `measured_value` convention); "maps to typed entities" is a docstring aspiration with **no shipped code path** — grounds SD-2.
5. **The executor-factory seam (PLAN-0047 Step 2, #526):** `ExecutorFactory = Callable[[], Mapping[StepKind, StepExecutor]]`, `register_procedure_executors` / `get_procedure_executors` (`registry.py:30, 85-106`); `services/api/routers/runs.py:96-100` resolves it per request for `POST /procedures/{id}/run` (`:150,163`) + `/runs/{id}/gate/resolve` (`:216,244`); an unwired vertical gets **409**.
6. **No vertical registers a production executor factory today.** A whole-repo grep finds `register_procedure_executors` only in `registry.py`, `runs.py`, and `tests/api/test_runs_endpoints.py:116`. The procurement hero demo builds its executors **directly** (`verticals/procurement/hero_demo/run.py:213-233`) and never touches the HTTP factory seam — grounds SD-4 (must #4).
7. **The write-ahead path already makes read results + failures durable.** `run_procedure_persisted` commits the running row before step 1 and every `StepResult` (success, suspend, AND failure) via `on_step_complete` (`persistence.py:94-124`; failure commit at `orchestrator.py:594-596`); `artifact["output_set"]` carries each step's output. So a fetched set and a refusal both have an existing durability channel; what they lack is **structure** (fact 2) and an **audit_log** presence — grounds SD-5.
8. **NONE of the four shipped verticals' query steps is a plain fetch.** aquaculture `read_do` = "latest dissolved-oxygen reading per active Pond" (`verticals/aquaculture/procedures.yaml:64-72`) — a latest-per-group projection over multiple reading events per pond (`verticals/aquaculture/data_adapter/synthetic.py:100-194` ships 4 readings for pond-07 alone; a plain `fetch_objects("OperationalEvent")` would judge stale readings, changing run semantics); energy `read_readings` / supply_chain `read_temps` are the same shape; procurement `intake` **joins three types** (`OperationalEvent`+`PurchaseOrder`+`Quotation`, `hero_demo/run.py:169-210`). The generic v1 executor can execute *plain declared reads*; the shipped seeds encode *projections/joins* the spec cannot yet declare — grounds SD-1 + SD-3.
9. **The governance pin does NOT cover `reads`.** `build_governance_snapshot` pins per-step `kind/autonomy/handler/governance_content` + SoD only (`governance_pin.py:34-59`). Once `reads` is execution-bound, a mid-flight `reads` edit changes what a resumed run READS without tripping the PLAN-0047 Step 6 fail-closed pin — grounds SD-5.
10. **Suite baseline:** 2097 passed / 5 skipped; CI (PLAN-0047 Step 7) runs ruff + ruff-format + `mypy --strict` + the full suite with a postgres container + `alembic upgrade head` on every PR. Every step below must keep it green.

## LOCKED (ratified — render faithfully; do NOT re-litigate)

If building any LOCKED item reveals it must change, that is an ADR-016 amendment (G-gated) — **STOP and surface**, never bake a deviation in.

- **LOCKED-1 (ADR-016 Q4, Accepted).** The deliverable is the generic run-consume executor: declared `reads` → `adapter.fetch_objects` → the step's output set, giving the read side declared==dispatched. No new ADR.
- **LOCKED-2 (OQ-3).** The executor + the `object_types` bound cover **`fetch_objects`-style object reads ONLY**. `fetch_links` (link-typed) and `stream_events` (event-typed) are a category mismatch — explicitly OUT; their own future typed bound.
- **LOCKED-3 (OQ-4).** `where` is the **engine-side post-fetch** field-equality filter over the fetched set — NOT pushed down to the adapter's `filter_expr`. One predicate (`_matches`) serves both the bag-resolved and fetched-set narrowing.
- **LOCKED-4 (OQ-5).** `reads` is `list[str]`. (How much of the list the v1 executor *executes* is SD-1 — the cardinality of the field is not reopened.)
- **LOCKED-5 (OQ-6).** Empty `Agent.allowed.object_types` = **UNCONSTRAINED** (the `step_kinds` convention). The executor's runtime re-check follows the SAME convention as the load gate — one shared predicate, no drift.
- **LOCKED-6 (governed ≠ generated).** **No LLM anywhere in the read path.** The executor is deterministic; the LLM never selects, filters, reshapes, or retries data through it. A step's LLM output that wants data consumes the governed executor's typed result.
- **LOCKED-7 (offline-only gate).** The offline oracle/test suite is the binding bar. No MS-S1, no live LLM in any gate. Any live confirming run is **optional evidence, explicitly Cray-gated** (CLAUDE.md §8 host-state rule).
- **LOCKED-8 (scope walls carried from Q3).** Connectors-in-the-procedure stay OUT (mapping layer absorbs source diversity — Cray s84); adapter selection unchanged (the `vertical` string); `from_step` intra-run threading unchanged; the sibling `step_kinds`/`action_handlers` empty-list divergence stays un-"fixed".
- **LOCKED-9 (honest frame — no over-claim).** This PLAN upgrades the enforcement frame ONLY for steps the generic executor runs: **declared ✔ · load-gated ✔ · execution-bound ✔**. Steps still on hand-written seeds remain execution-bound ✖ and the Verification section must say so.

## Design notes (binding for the build — the four ratified musts, absorbed)

- **D-N1 — Refusal UX (must 1).** Out-of-coverage = a **typed, structured, auditable refusal**: a `ReadRefusal` exception carrying `refusal_kind ∈ {unknown_object_type, outside_allowlist, unsupported_read_shape, unbound_query}` + the offending `object_type` + `step_id`. Refusal ≠ no-data: a successful in-coverage fetch that returns zero rows completes the step with `output=[]` **plus a read-provenance trace entry** (object_type, fetched count, post-`where` count) — the two are distinguishable in every persisted record. This renders the dbt-benchmark failure-mode contrast (semantic-foundation brief F2: in-coverage ≈ 100%, out-of-coverage = explicit refusal, never a plausible wrong answer; pitfall P3: without the distinction, refusals get misread as failures) and the market brief's repositioning ("refusal-safety + audit is the durable value; design refuse → explain → escalate as a feature" — 2026-07-03 market-landscape brief, VERDICT + CHANGE/WATCH 1). `on_failure: escalate_to_human` on a query step routes a refusal to `waiting_human` = the escalation UX, already shipped control-plane behavior (fact 2).
- **D-N2 — Bounded dispatch, no retry loop in v1 (must 2).** The v1 executor makes **exactly one** `fetch_objects` dispatch per declared object_type — no execute-validate-retry loop exists, so the must's conditional is satisfied by construction, and the **bound (attempts = 1) + the in-allowlist invariant are asserted as testable properties** (a counting fake adapter; AC-5/AC-6), not assumed. The contract for any FUTURE repair loop is documented in the module docstring: fixed max attempts, every attempt inside `reads ∩ object_types`, deterministic (no LLM reshaping — LOCKED-6); adding such a loop = a new PLAN, and the llm-db brief's "execute-validate-retry inside the existing allowlist" note (2026-07-03, "where the industry moved" section) is its authorizing context.
- **D-N3 — The compile/execute/inspect 3-tool seam (must 3).** The interface is factored so it could later be exposed as the convergent dbt-MCP tool triple (semantic-foundation brief F8: small `list/discover + constrained run` surface beats schema-in-prompt and tool-per-metric): **compile** = `plan_read(step, agent, object_type_names) → ReadPlan | raises ReadRefusal` (pure, no I/O); **execute** = `QueryStepExecutor.execute` running a compiled plan through the injected adapter; **inspect** = `readable_object_types(agent, object_type_names) → frozenset[str]` (= ontology ∩ allowlist, the agent's read coverage). **MCP plumbing is an explicit NON-GOAL** — no server, no transport, no tool registration in this PLAN; the seam just stays clean. Positioning note for the docstring: this executor is the deterministic half of the CaMeL-shaped "LLM proposes, deterministic policy engine disposes" architecture the llm-db brief names as the canonical injection defense (finding 4) — name it explicitly.
- **D-N4 — Production factories (must 4).** The Step-2 registry seam exists and no vertical registers a factory (fact 6). This PLAN **proves the composition offline** — a registered factory wiring the generic query executor drives the real HTTP endpoint in tests (AC-12) — and ships a documented composition recipe; **building the per-vertical production factories is SD-4** (recommendation: a named follow-up PLAN, because the ACTION executor's client wiring is an LLM-surface decision that must not ride in under an offline-only read-side PLAN).

## Decided in this draft (build-level, closed by ratified sources or shipped precedent — named so Cray can veto, not silently chosen)

- **Executor home = a new engine module `services/engine/procedures/query_step.py`.** Mirrors the shipped per-kind executor precedent exactly (`evaluate_step.py`, `action_step.py`); the orchestrator stays control-plane-only (ADR-016 D2). Not an SD: the sibling precedent leaves no defensible alternative.
- **Adapter + registry acquisition = constructor injection.** `QueryStepExecutor(adapter=..., object_type_names=...)`; the composing factory supplies `registry.get_adapter(vertical)` + `frozenset(m.name for m in load_ontology_meta(vertical).object_types)`. No hidden I/O inside the executor — the same purity rationale Cray ratified for PLAN-0046 SD-1, and the same shape as `ActionStepExecutor(client_factory=...)`.
- **`where` post-fetch filtering SHIPS in v1.** OQ-4 ratified the semantics; must 1 closes the question — a declared `where` the executor ignores would be a silent declared≠dispatched divergence (exactly the guess-shaped behavior this PLAN exists to kill). Implemented by promoting `_matches` to a shared public predicate (one source; fact 3).
- **No retry/repair loop in v1** (D-N2) — the bound is a tested property, not a policy hope.
- **Runtime re-check of the bound lives in `plan_read`** and shares its per-step predicate with the load gate `validate_read_bindings` (one refactored helper, both callers). Defense-in-depth beyond pre-flight at near-zero cost, and it makes refusal enforceable for library callers composing the executor directly.

## Acceptance Criteria

Grouped by build step. The **offline suite is the merge gate** (CLAUDE.md §8; LOCKED-7); the refuse-case pass/fail reads (AC-2, AC-7) are **pre-committed in the test module before the tests are written** (Lesson #0026 discipline, mirroring PLAN-0046 AC-5). ACs marked *(per SD-N)* were written to that SD's recommendation; **all five SDs are ratified as-recommended (Cray, 2026-07-04), so every marked scope is FIXED** — the mechanical re-scope path is moot.

### Step 1 — the compile seam: `plan_read` + typed refusal (D-N1/D-N3)

- [ ] **AC-1 — `plan_read` is pure and total over the SD-1 shape matrix.** `plan_read(step, agent, object_type_names) → ReadPlan` performs no I/O and touches no adapter; `ReadPlan` carries the resolved single `object_type` + the `where` mapping. Unit-testable with a fixture registry only.
- [ ] **AC-2 — the refusal matrix is typed, structured, and pre-committed.** `reads=[X]`, X ∉ ontology → `ReadRefusal(unknown_object_type)`; X ∈ ontology but ∉ non-empty allowlist → `ReadRefusal(outside_allowlist)`; `len(reads) > 1` → `ReadRefusal(unsupported_read_shape)` *(per SD-1 — ratified, scope fixed)*; `reads` present + `from_step` present → `ReadRefusal(unsupported_read_shape)` *(per SD-1 — ratified, scope fixed)*; reads-absent entry-point query under the generic executor → `ReadRefusal(unbound_query)` *(per SD-1 — ratified, scope fixed)*. Every refusal names the kind, the offending object_type (where applicable), and the step_id as **structured fields**, not prose only. Empty `object_types` = unconstrained (LOCKED-5).
- [ ] **AC-3 — one bound, zero drift.** The load gate (`validate_read_bindings`) and `plan_read` share a single step-level bound predicate (refactor, no behavior change to the gate); a tripwire test drives the same fixture matrix through BOTH and asserts identical accept/refuse decisions. All PLAN-0046 gate tests stay green untouched.

### Step 2 — the execute half: `QueryStepExecutor` (D-N1/D-N2)

- [ ] **AC-4 — declared==dispatched, positively.** For an in-coverage single read, the executor calls `fetch_objects` with exactly the declared object_type; the step's `output` is the fetched entity set narrowed post-fetch by `where` via the shared `_matches` predicate (LOCKED-3); the `reasoning_trace` carries a read-provenance entry: object_type, fetched count, post-`where` count.
- [ ] **AC-5 — declared==dispatched, adversarially.** Property test over a matrix (varying `reads`/`where`/allowlist/adapter contents, incl. an adapter that returns rows of OTHER types): the set of object_types dispatched to the adapter == exactly the declared read — never one more, never a substitute. Counting fake adapter.
- [ ] **AC-6 — bounded dispatch.** Exactly ONE `fetch_objects` call per execution (attempts = 1, asserted); an adapter exception propagates to D4 fail-and-divert with **no re-fetch**; no code path loops on the adapter. (D-N2 — the must-2 property.)
- [ ] **AC-7 — refusal ≠ no-data, pre-committed.** An out-of-coverage read **raises** (never returns); an in-coverage fetch yielding zero post-`where` rows **completes** with `output=[]` + the provenance trace. The two are distinguishable from the recorded `StepResult` alone. The pass/fail read for both halves is committed before the tests.
- [ ] **AC-8 — structured refusal survives fail-and-divert.** The orchestrator's D4 catch records a raising `ReadRefusal`'s structured payload (kind/object_type/step) in the step's `reasoning_trace` — a small disclosed enrichment of the flatten-to-string catch (fact 2), duck-typed/isinstance-scoped so every other exception's handling is byte-identical. `on_failure: escalate_to_human` routes a refusal to `waiting_human` (refuse → explain → escalate).
- [ ] **AC-9 — backward compat: reads-absent worlds are untouched.** No existing caller, factory, test, or shipped procedure is forced onto the generic executor; the hero-demo path (`hero_demo/run.py`) is byte-unchanged; a reads-absent procedure under its existing hand-written executors runs byte-identically. Suite baseline (fact 10) stays green.

### Step 3 — both production paths + persistence/audit (PLAN-0047 interaction)

- [ ] **AC-10 — in-memory path end-to-end.** `run_procedure` with a purpose-built fixture (agent opts in via `object_types`; procedure declares `reads` on its query step; fake adapter registered) runs query → evaluate → gated action to `waiting_human`; the load gate and the executor agree (nothing the gate accepted is refused at run time for the plain-read shape, and vice versa).
- [ ] **AC-11 — write-ahead path: reads and refusals are durable.** `run_procedure_persisted` commits the read step's `StepResult` (with `artifact["output_set"]` = the fetched set) as it lands; a refusal on this path leaves a durable, queryable refusal `StepResult` (failures commit too — fact 7). *(per SD-5 — ratified, scope fixed)* a refusal additionally appends a `read_refused` audit_log row (hash-chained, PLAN-0047 Step 5) from the persistence seam — the executor itself stays DB-free.
- [ ] **AC-12 — HTTP/registry composition proven offline.** A test-registered `ExecutorFactory` wiring `QueryStepExecutor` (adapter via `registry.get_adapter`) drives the real `POST /procedures/{id}/run` endpoint (the `tests/api/test_runs_endpoints.py` pattern) through suspend; an unwired vertical still 409s. This is the documented composition recipe for SD-4's follow-up.
- [ ] **AC-13 — governance-pin interaction** *(per SD-5 — ratified, scope fixed)*. `reads` (sorted, per step) joins the pinned governance snapshot; a mid-flight `reads` edit fails CLOSED at resume with the standard pin-mismatch refusal; the pin-format change is disclosed in the PR body (a pre-existing `waiting_human` run started before the deploy will refuse at resume — the PLAN-0047 sanctioned cancel-and-restart path, acceptable pre-pilot). If Cray rejects SD-5(b), this AC re-scopes to a test asserting pin behavior is unchanged and the gap is documented. **— MOOT: SD-5(b) ratified as-recommended (2026-07-04); this AC stands as written.**

### Step 4 — seams, docs, and the offline oracle

- [ ] **AC-14 — the 3-tool seam is real and named.** `readable_object_types(agent, object_type_names)` ships tested (the inspect half); the module docstring maps compile/execute/inspect onto the dbt-MCP list/discover + constrained-run shape (D-N3), names MCP plumbing a non-goal, names the CaMeL "deterministic disposer" role, and documents the future-loop contract (D-N2).
- [ ] **AC-15 — the offline oracle is green (the merge bar).** Full suite green (baseline 2097 passed / 5 skipped + the new tests); `ruff` + `ruff-format` + `mypy --strict services/` clean; any new API-facing model carries `Field(description=...)`; **no MS-S1 / live-LLM call anywhere in the gate** (LOCKED-7). The Verification frame states the LOCKED-9 honest claim verbatim.

## Out of Scope

- ❌ **A join / projection grammar** ("latest per X", group-by, multi-type enrichment joins). Fact-pack 8: every shipped seed encodes one; the spec cannot declare them; inventing join semantics here = new `extra="forbid"` spec surface = an **ADR-016 amendment**, not a build call. Multi-read execution refuses typed in v1 *(per SD-1 — ratified, scope fixed)*.
- ❌ **`fetch_links` / `stream_events` executors or bounds** (LOCKED-2 — their own future typed allowlist).
- ❌ **MCP plumbing** — no server, transport, or tool registration (D-N3 keeps the seam only). OSI export + the semantic-context-pack generator (semantic brief R1/F3) stay separate backlog items.
- ❌ **Any NL-query path change** (`nl_query.py` keeps its own fetch; convergence onto the 3-tool seam is a future design note, not this diff).
- ❌ **Retry/repair loops and any LLM participation in the read path** (D-N2, LOCKED-6). LLM-assisted `where` reshaping is explicitly banned through this executor.
- ❌ **Migrating shipped verticals' `procedures.yaml`** to declare `reads`/`object_types` *(per SD-3 — ratified, scope fixed: their steps are projections/joins the plain executor cannot honestly execute)*; retiring the hero-demo `_SeedQuery` or the demo path in any way.
- ❌ **Building the per-vertical production executor factories** *(per SD-4 — ratified, scope fixed: named follow-up PLAN)*.
- ❌ The Box-4 ฿ facet (still N≥3-gated per ADR-016), the `step_kinds`/`action_handlers` empty-list divergence (LOCKED-8), constitutional/convention edits.

## Surfaced Decisions — RATIFIED (Cray, 2026-07-04 — all five as-recommended)

Each was surfaced with options + a fact-pack-grounded recommendation; **Cray ratified all five as recommended** (typed in-session 2026-07-04: "approve SD-1..5 ตาม recommended", relayed via the Code dispatch). The option text and Why-Cray rationale are kept intact for the record — alternatives are historical, not open.

- **SD-1 — the v1 executable read shape (multi-read + reads-absent handling).** ADR-016 OQ-5 ratified `reads: list[str]` and parenthetically located "the multi-read join" with Q4 — but a generic join needs join semantics the spec cannot declare (fact 8), and guessing them violates governed≠generated + must 1. What does the v1 executor execute?
  - *Option A (recommended):* **single-read only.** `len(reads) == 1` → fetch + `where`; `len(reads) > 1` → typed `ReadRefusal(unsupported_read_shape)` (the joins stay hand-written until a join grammar is ratified — an ADR-016 amendment); `reads` + `from_step` together → same refusal (two competing input sources = ambiguous, and the orchestrator would double-apply `where`); reads-absent + `from_step` → **not the generic executor's case** (existing executors keep it; if composed anyway, identity pass-through of the orchestrator-resolved input is the only deterministic reading); reads-absent entry-point → `ReadRefusal(unbound_query)` (a `[]` here is exactly the silent-empty must 1 bans).
  - *Option B:* multi-read = concatenated union of per-type fetches (executes the whole list, but silently invents "union" as the join semantic — plausible-wrong shaped).
  - **Why Cray:** this fixes how much of ADR-016's "multi-read lands with Q4" parenthetical this PLAN claims to deliver — a scope commitment against ratified ADR text, not a code call.
  - **✅ RATIFIED 2026-07-04 = Option A (as recommended).** Single-read only; the AC-2 refusal shapes (multi-read / `reads`+`from_step` / unbound entry) are fixed.
- **SD-2 — result typing: what does "→ typed entities" mean in v1?** ADR-016 Q4's one-liner says "typed entities"; every shipped engine consumer works over raw dicts (fact 4).
  - *Option A (recommended):* **thread the adapter's raw dicts unchanged**; "typed" is delivered as the typed *binding* + typed *refusal* + typed *provenance* (the ReadPlan/trace). Zero new coupling; the downstream judge (`measured_value` convention) and `where` fan-out consume dicts today; Pydantic materialization is named a deferred design note on the inspect seam.
  - *Option B:* validate each fetched dict against the generated ontology model for the object_type (fail loudly on shape garbage), then thread the original dicts. Stronger guarantee, new coupling executor→generated models, and a per-row validation cost.
  - *Option C:* thread typed model instances (breaks the Mapping-shaped engine conventions — effectively a migration).
  - **Why Cray:** Option A reads ADR prose non-literally; that reading should be ratified, not assumed by the drafter.
  - **✅ RATIFIED 2026-07-04 = Option A (as recommended).** Raw dicts threaded unchanged; "typed" = typed binding + typed refusal + typed provenance.
- **SD-3 — fate of the hand-written seeds: retire, deprecate, or leave.** The ADR says the executor "retir[es] the hand-written per-vertical seeds" — but all four are projections/joins (fact 8), and migrating e.g. `read_do` onto a plain `reads: [OperationalEvent]` would silently change run semantics (stale readings get judged).
  - *Option A (recommended):* **deprecate-in-place, retire nothing.** The generic executor becomes the shipped engine default for plain declared reads (all NEW/simple query steps, future verticals); the four seeds stay, each annotated as an interim projection/join executor pending the join/projection grammar; no shipped `procedures.yaml` migrates (declaring `reads` on a seed-run step would claim an execution binding that isn't real — dishonest against LOCKED-9).
  - *Option B:* migrate the three single-source verticals now, accepting the changed semantics (all readings judged, not latest-per-pond) — cheaper retirement, but a silent behavior change to demo-visible runs.
  - **Why Cray:** "retiring the seeds" is ADR-016 Q4's own stated outcome; deferring it is a delivery-scope judgment against ratified text, and Option B changes demo-visible behavior.
  - **✅ RATIFIED 2026-07-04 = Option A (as recommended).** Deprecate-in-place; retire nothing; migrate no shipped `procedures.yaml`.
- **SD-4 — production executor-factory wiring: build now vs named follow-up (must 4).**
  - *Option A (recommended):* **follow-up PLAN.** This PLAN proves the full composition offline through the real endpoint (AC-12) + documents the recipe; the follow-up wires real factories per vertical — because a production factory must also pick the ACTION executor's `client_factory` (an LLM/advisory-stub decision, host-state-adjacent) which must not ride in under an offline-only read PLAN.
  - *Option B:* wire one pilot factory (aquaculture) now with the advisory-stub client — demonstrable end-to-end HTTP run sooner, but it bakes an LLM-surface default nobody ratified and widens this PLAN's blast radius.
  - **Why Cray:** the handoff named this must with "build/wire vs note as follow-up — your recommendation, surface as an SD if genuinely open"; it is genuinely open, and it sequences Wave-2 delivery.
  - **✅ RATIFIED 2026-07-04 = Option A (as recommended).** Production factories = a named follow-up PLAN; this PLAN ships the offline-proven composition recipe (AC-12) only.
- **SD-5 — the read surface in the pin + audit record.** Two halves. **(a) Refusal audit row:** append a `read_refused` audit_log row (hash-chained, PLAN-0047 Step 5) from the persistence seam when a refusal StepResult lands — makes refusal-safety a first-class, tamper-evident audit fact (the market brief's sales claim), ~10 lines. **(b) Pin `reads`:** add per-step sorted `reads` to `build_governance_snapshot` so "which read config governed THIS run" is answered by the run row, and a mid-flight `reads` edit fails closed at resume like a ladder edit (fact 9). Cost of (b): a pin-format change — pre-deploy `waiting_human` runs refuse at resume (sanctioned cancel-and-restart; acceptable pre-pilot, disclosed).
  - *Option A (recommended):* **both (a) and (b) now** — this is the moment `reads` becomes execution-relevant; landing the pin later means a window where the executed read surface is mutable mid-run.
  - *Option B:* (a) only, pin later. *Option C:* neither (StepResult durability alone).
  - **Why Cray:** (b) alters the fail-closed behavior of every future resume and the pin format — an operational-posture decision on PLAN-0047's ratified machinery, not a drafter call.
  - **✅ RATIFIED 2026-07-04 = Option A — both (a) and (b) (as recommended).** The `read_refused` audit row AND `reads` into the pinned snapshot both land in this PLAN; the disclosed pin-format consequence (pre-deploy `waiting_human` runs refuse at resume — sanctioned cancel-and-restart) is accepted.

## Steps

Build order: compile seam first (pure, no I/O — cheapest gate), then the executor, then the paths/persistence, then docs + the full oracle. Each step lands with its tests; the suite stays green at every boundary.

### Step 1 — `plan_read` + `ReadRefusal` + the shared bound (AC-1..AC-3)
- New `services/engine/procedures/query_step.py`: `ReadRefusal` (structured: `refusal_kind`, `object_type`, `step_id`, human-readable detail), `ReadPlan`, `plan_read`, `readable_object_types`.
- Refactor the per-step bound out of `validate_read_bindings` into one shared helper (gate behavior byte-identical; PLAN-0046 tests untouched).
- Pre-commit the AC-2 refusal pass/fail matrix in the test module before writing the tests.
- Gate: unit tests (fixture registry only, no adapter, no DB).

### Step 2 — `QueryStepExecutor` + structured-refusal divert (AC-4..AC-9)
- `QueryStepExecutor(adapter, object_type_names)` — compile via `plan_read`, one `fetch_objects` dispatch, post-fetch `where` via the promoted shared `_matches`, provenance trace, `output=fetched set`.
- Orchestrator D4 catch: record a structured trace entry for exceptions carrying a refusal payload (isinstance-scoped; all other exceptions byte-identical) — disclosed control-plane delta.
- Gate: counting-fake-adapter property tests (AC-5/AC-6), refusal-vs-no-data (AC-7 pre-committed), escalate routing (AC-8), reads-absent no-regression sweep (AC-9).

### Step 3 — both paths, durability, pin (AC-10..AC-13)
- Fixture vertical wiring (real ontology names via `load_ontology_meta`, registered fake adapter, opt-in agent) through `run_procedure` and `run_procedure_persisted`; HTTP composition test per the `test_runs_endpoints` pattern.
- *(per SD-5 — ratified, scope fixed)* `read_refused` audit append in the persistence seam; `reads` into `build_governance_snapshot` + resume-mismatch test + PR-body disclosure of the pin-format change.
- Gate: DB-backed tests (CI postgres), refusal durability on the write-ahead path, pin fail-closed at resume.

### Step 4 — seams, docs, oracle (AC-14..AC-15)
- Module docstring: 3-tool mapping, MCP non-goal, CaMeL naming, future-loop contract, SD-3 deprecation annotations on the seeds *(per SD-3 — ratified: deprecate-in-place)*.
- Gate: full offline suite green; ruff + ruff-format + `mypy --strict services/`; no live calls.

## Verification

- **Gate (CI / offline — the binding bar):** the AC matrix above, all offline; the pre-committed refuse reads (AC-2, AC-7) fixed before their tests; the declared==dispatched + bounded-dispatch properties (AC-5/AC-6) proven with a counting fake adapter; both production paths exercised against real postgres in CI; ruff + ruff-format + `mypy --strict` clean (AC-15).
- **No-regression:** hero-demo path byte-unchanged; reads-absent procedures byte-identical; PLAN-0046 load-gate tests untouched and green; PLAN-0047 write-ahead/gate-state/pin/audit suites green; suite baseline 2097/5 preserved plus the new tests.
- **Honest enforcement frame (LOCKED-9 — verbatim, no over-claim):** after this PLAN, a query step **run by the generic executor** is declared ✔ · load-gated ✔ · **execution-bound ✔** (the executor dispatches exactly the declared read — write-side parity achieved for that step class). A step still on a hand-written seed remains **execution-bound ✖**; nothing in this PLAN may claim runtime read enforcement for seed-run steps or for `fetch_links`/`stream_events`.
- **Optional live evidence (NOT the gate):** a single live confirming run of the fixture composition is possible but is a **host-state action — explicit Cray go required first** (CLAUDE.md §8); the offline oracle alone decides merge.
- **STOP-and-surface:** if building any LOCKED item reveals a ratified ADR-016 decision must change (e.g. the multi-read parenthetical proves un-renderable under SD-1=A), that is an ADR-016 amendment (G-gated) — surface to Cray; never bake the deviation in.

---

## Completion note (2026-07-04, session 96)

All 15 acceptance criteria met; the executor + compile seam + both production
paths + persistence/audit/pin all landed via feature-branch PRs under the
PLAN-0047 Step-7 CI gate (ruff + ruff-format + `mypy --strict` + full suite w/
postgres container + `alembic upgrade head` — every step PR ran green under it).
Final suite: **2131 passed / 5 skipped** (baseline 2097 at plan start → **+34
new tests**). All work offline; MS-S1 never touched; **no new migration**
(reuses PLAN-0047's 0005–0008; SD-5(b) adds `reads` to the existing
`governance_snapshot` JSONB, no DDL). Renders ADR-016 Q4 — no new ADR.

| Step | PR (commits) | Delivered | ACs |
|------|--------------|-----------|-----|
| Draft | #533 (`d107d99` / merge `761f33d`) | plan-drafter authored the Q4 build plan; 5 SDs surfaced | — |
| SD ratify fold | #534 (`260df5a` / merge `c169ec1`) | SD-1..5 ratified as-recommended (Cray), Draft→Ready | — |
| Step 1 — compile seam | #535 (oracle `c104da2` + impl `0e17dc6` / merge `1ff2899`) | `services/engine/procedures/query_step.py`: `ReadRefusal`/`ReadRefusalKind`, `ReadPlan`, `plan_read` (pure/total, single-read only per SD-1), `readable_object_types`; the shared `orchestrator.read_bound_violation` predicate (one bound, byte-identical gate messages — PLAN-0046 tests untouched); 15 tests incl. the AC-3 gate-vs-seam no-drift tripwire; oracle-first two-commit history | AC-1, AC-2, AC-3 |
| Step 2 — execute half | #536 (oracle `462ead2` + impl `f3d362b` / merge `9622307`) | `QueryStepExecutor` (constructor-injected; one `fetch_objects` dispatch per execution — no retry loop; post-fetch `where` via the promoted shared `orchestrator.matches_where`, `filter_expr` never pushed down; read-provenance trace; SD-1 identity pass-through); the isinstance-scoped D4 structured `read_refused` divert in `orchestrator.py` (every other exception byte-identical); 11 tests incl. the adversarial counting-adapter property + the load-gate-accepts/runtime-refuses multi-read split; oracle-first | AC-4, AC-5, AC-6, AC-7, AC-8, AC-9 |
| Step 3 — both paths + persistence/audit/pin | #538 (impl `676fbc2` / merge `65519c0`) | AC-10 in-memory end-to-end vs the real aquaculture ontology; AC-11 write-ahead read durability + the SD-5(a) `read_refused` audit row appended by the persistence seam (executor stays DB-free), on write-ahead AND resume paths; AC-12 the SD-4 composition recipe (`QueryStepExecutor` wired from `registry.get_adapter` drives the real `POST /procedures/{id}/run` to suspend; unwired vertical still 409s); AC-13 the SD-5(b) sorted `reads` in `governance_pin.build_governance_snapshot`, fail-closed at resume on a still-load-gate-valid reads edit; 8 tests | AC-10, AC-11, AC-12, AC-13 |
| Step 4 — seams/docs/oracle | #539 (impl `f7d4972` / merge `ab394b0`) | AC-14: the `query_step.py` module docstring maps compile/execute/inspect onto the dbt-MCP 3-tool shape, names MCP plumbing a non-goal + the CaMeL deterministic-disposer role + the D-N2 future-repair-loop contract; the SD-3 deprecate-in-place annotation on the hero-demo `_SeedQuery`; AC-15: full offline oracle green. Docstring-only, zero behavior change | AC-14, AC-15 |

**SD dispositions (all ratified as-recommended, 2026-07-04):** SD-1 single-read
only · SD-2 raw dicts threaded ("typed" = typed binding+refusal+provenance) ·
SD-3 deprecate-in-place (nothing retired/migrated) · SD-4 production factories =
named follow-up PLAN · SD-5 BOTH the `read_refused` audit row (a) AND `reads` in
the pin (b).

**Disclosed deviations (scope-visible, none amend an ADR):**

- **`_json_safe` adapter-boundary JSON normalization (Step 3, `query_step.py`)** —
  NOT in the plan; added when AC-12 drove the REAL energy synthetic adapter
  through the write-ahead path and its `datetime`-carrying rows broke the JSONB
  `artifact["output_set"]` (the known datetime-in-JSONB trap). ONE `default=str`
  coercion at the adapter boundary; keys/dict shape unchanged so SD-2's raw-dict
  threading stands, only non-JSON scalar TYPES coerce (which a JSONB column
  forces anyway); covered by a dedicated test.
- **SD-5(b) pin-format consequence (disclosed, ratified)** — a `waiting_human`
  run pinned BEFORE the `reads` field existed refuses at resume (the PLAN-0047
  sanctioned cancel-and-restart). Ratified as-recommended, acceptable pre-pilot;
  not a deviation, a disclosed consequence.
- **Concurrent-pytest flake, now resolved** — Steps 1–2 disclosed a
  `test_stop_continuation` failure that reproduced only when the Axis-B
  goal-gate's pytest check ran concurrently with a manual full-suite run in the
  same worktree; independently FIXED by #537 (`fix/inproc-goal-path-leak`, merged
  before Step 3). No longer a live issue.

**Deferred (unchanged from Out of Scope):** the join/projection grammar for
multi-read (a future ADR-016 amendment) · `fetch_links`/`stream_events`
executors + bounds · MCP plumbing / OSI export / the semantic-context-pack
generator · the per-vertical production executor factories (SD-4 named follow-up
PLAN) · NL-query convergence onto the 3-tool seam · retry/repair loops (the D-N2
future contract is documented, not built) · the Box-4 ฿ facet (N≥3-gated).

**Honest enforcement frame (LOCKED-9, verbatim):** after PLAN-0048, a query step
run by the generic executor is declared ✔ · load-gated ✔ · execution-bound ✔
(write-side parity for that step class); a step still on a hand-written seed
remains execution-bound ✖; nothing claims runtime read enforcement for seed-run
steps or for `fetch_links`/`stream_events`.

**Close-out mechanics (committing session 96):** `git mv docs/plans/0048-*.md
docs/plans/done/` in the same PR as this fold — `git add` the edit **before**
`git mv` (project memory: `git mv` of a modified file drops the edit).

> **Completion-fold provenance (ADR-012 D4.3):** This fold was drafted by the
> in-harness `plan-drafter` subagent (session 96) from the Code-supplied
> execution-facts payload; Code R2-reviews and commits (ADR-009 D2); independent
> reviewer: Cray at PR merge. Separation: INTACT.

---

*PLAN-0048 drafted by the in-harness `plan-drafter` subagent (2026-07-04), ADR-013 phased governance authoring (ADR-009 D1). It renders the Accepted ADR-016 Q4 decision + the four Cray-ratified Wave-2 design musts (s95 CLOSE handoff); it opens no new ADR and reopens no ratified OQ. Five build-level forks were surfaced (SD-1..SD-5) with recommendations — none silently decided — and **all five are now RATIFIED as-recommended (Cray, typed in-session 2026-07-04, relayed via the Code dispatch)**: every (per SD-N) marker's scope is fixed and the mechanical re-scope path is moot. Author≠reviewer (ADR-012 D4.3): drafter = plan-drafter; reviewers = Code R2 (fact-pack re-verified on disk; SHA lineage corrected to 353c04e) + Cray at SD ratification and PR merge — separation INTACT. The draft merged to main unchanged via `docs/*` PR #533 (merge `761f33d`, ADR-009 D2); the ratification fold was applied post-merge by the drafter and is committed by Code via a follow-up `docs/*` PR. **Status: Ready for execution** — Code executes per the Steps in a feature branch; only Code commits; the drafter does not git. AI-assisted (plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
