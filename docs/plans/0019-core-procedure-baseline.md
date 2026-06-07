---
plan: PLAN-0019
title: Core Procedure baseline (Phase 1) — Procedure/Step/PipelineRun/Agent runtime + linear set-valued orchestrator + 3 example procedures + folded empirical benchmark
status: Draft
owner: Claude Code
created: 2026-06-07
related_adrs:
  - ADR-016 (governed procedure engine — THE binding design; this PLAN implements its Phase 1 / D7)
  - ADR-007 (OCT engine contracts — D2 RecommendedAction envelope reused UNCHANGED)
  - ADR-010 (LLM reasoning-hook surface — per-action trace generalized to per-step)
  - ADR-001 (LLM model baseline — gpt-oss:20b pin = the default Agent model)
  - ADR-013 (autonomy-axis relocation — safe / human-gated posture)
  - ADR-006 / ADR-015 (engine-vs-config; Rule-of-Three template-first; multi-vertical thesis)
related_plans:
  - PLAN-0005 / PLAN-0006 (shipped reactive loop — Pipeline v0; reused verbatim by the action step)
  - PLAN-0010 (scheduled-task autonomy loop — the `schedule` trigger reuses this LATER; not built here)
  - PLAN-0016 (aquaculture Tier-1 Mirror demo — the headline vertical)
grounding_research:
  - docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md (private/gitignored; per-concern DEFER lists)
  - docs/research/private/2026-06-06-impl-approach-reconciliation.md (on-thesis framing; evidence-gap G-3)
authored_by: plan-drafter subagent (in-harness; ADR-009 D1 interim authoring under ADR-013 phased relocation — uncommitted draft; Code commits per ADR-009 D2)
---

# PLAN-0019 — Core Procedure baseline (Phase 1)

> **Drafting provenance / author≠reviewer disclosure (ADR-012 D4.3).**
> Drafted (uncommitted) by the in-harness `plan-drafter` subagent under
> ADR-009 D1 interim authoring per ADR-013's phased relocation. The outline
> originator was **Cray** (founder, this session): the MERGE-with-guardrails
> structure (one PLAN, two internal Parts, hard gate), the LOCKED scope
> decisions (SD-1 manual-only trigger, SD-2 three example procedures, SD-3
> Postgres persistence), and the folded empirical benchmark were Cray-originated
> in the dispatch. This draft renders and cross-checks them against ADR-016 +
> the cited ADRs + the grounding research, and surfaces residual choices as
> **Surfaced decisions** (§8) rather than silently resolving them. The
> independent reviewer will be **Cray at ratification** (Draft → Ready for
> execution); **Code commits via PR** (ADR-009 D2; the drafter holds no commit
> authority — G5 composed-identity gate). Separation between drafter
> (`plan-drafter`) and reviewer (Cray) is **INTACT**.
>
> This PLAN **implements ADR-016 Phase 1**. ADR-016 is **Accepted** and fixes
> the primitive SHAPE (`Procedure/Step/PipelineRun/Agent`, the autonomy model,
> linear+set-valued+durable / fail-and-divert, goal-as-runtime-directive, the
> engine-vs-config boundary). This PLAN does **NOT** redesign that shape — it
> only implements it. ADR-016 is merged before this implementation PR per
> CLAUDE.md §8 ("ADRs merged before related implementation").

## 1. Status

**Draft** — authored 2026-06-07 by the `plan-drafter` subagent. Moves to
**Ready for execution** on Code landing the doc on `origin/main`. The three
LOCKED scope decisions below (L-1/L-2/L-3) **and** the two **architectural**
surfaced decisions **SD-A1 (Postgres schema) + SD-A2 (engine home path)** are
**Cray-ratified this session** (2026-06-07) and are recorded, not re-opened.
The remaining **B-side** surfaced decisions (SD-B1 thresholds, SD-B2 dataset,
SD-B3 G-2) stay open and are resolved at their execution step — **SD-B1 MUST
be ratified before any Part B run** (anti moving-target).

### 1.1 LOCKED scope decisions (recorded — do NOT re-open)

| ID | Decision | Resolves |
|---|---|---|
| **L-1 (trigger)** | Phase-1 = **`manual` trigger ONLY**. The orchestrator is **trigger-agnostic** so `schedule` wires in later by reusing PLAN-0010's scheduled-task autonomy loop (**no scheduler is built now**). The aquaculture headline runs via **manual** invocation in Phase 1; its 06:00 schedule is deferred. | **ADR-016 OQ-2 for Phase-1** = manual-only (confirm §8 SD-2) |
| **L-2 (examples)** | **3** hand-authored example procedures: `aquaculture` (headline "Morning Pond Health Round"), `energy`, `supply_chain`. `vet_clinic` is **EXCLUDED** (parked, ADR-005). | ADR-016 D7 Phase-1 "one per existing vertical" |
| **L-3 (persistence)** | `PipelineRun` / `StepResult` persisted in **Postgres via an Alembic migration** (durable resume needs it; matches the existing SQLAlchemy 2.0 async + Alembic + asyncpg stack — PLAN-0005 §5). | ADR-016 D4 (durable / resumable) |

## 2. Context

ADR-016 expands the OCT action layer from reactive-only (`anomaly→action`) to
`anomaly AND normally→action` and establishes a primitive
(`Procedure / Step / PipelineRun / Agent`) — but defers **all** implementation
mechanics to this PLAN (ADR-016 D7 "Phase 1 — PLAN-0019"; Out-of-scope
"Implementation detail → PLAN-0019"). The shipped reactive loop
(PLAN-0005/0006) is reframed as **Pipeline v0**: a 1-step, gated procedure. The
machinery this PLAN must reuse **verbatim** already exists in `services/`:

- The **ADR-007 D2 `RecommendedAction` envelope** — `services/engine/actions.py`
  (`RecommendedAction`, `ReasoningStep`, `EntityRef`, `AuditMetadata`).
  **UNCHANGED** by this PLAN.
- The **approve→execute gate** — `services/engine/recommender.py`
  (`ActionRecord`, `ActionStatus` `proposed→approved→executed/rejected`,
  `approve()` / `reject()` / `execute()`, `ApprovalError`). An `action` step
  routes through this **existing** gate.
- The **vertical registry** — `services/engine/registry.py` (`register_adapter`
  / `register_handler`, `get_adapter` / `get_handler`, `handler_names`). The
  handler **allowlist** (blast-radius bound, ADR-016 D3) is enforced against
  `registry.handler_names(vertical)`.
- The **LLM reasoning seam** — `services/engine/llm/` (two-call Pattern B;
  `gpt-oss:20b` pin, ADR-001) + `services/db/persistence.py` (the OQ-1
  envelope→ontology projection).

This PLAN is **additive**: the engine orchestrator + `Procedure/Step/Agent`
spec loaders + `PipelineRun`/`StepResult` records + Postgres tables are new;
the six-`object_types` ontology (ADR-008) and the `RecommendedAction` envelope
are untouched.

### 2.1 The core shape — MERGE-with-guardrails (one PLAN, two Parts, a HARD GATE)

This PLAN folds the empirical benchmark (formerly a separate "Thread 2") **into
this PLAN's acceptance**, guarded against two named risks: (i) **moving-target**
(thresholds drift to fit results) and (ii) **engineering+research review
tangle** (a deterministic build review entangled with an empirical study). The
guardrails:

- **Part A — Engine** (functional / structural acceptance; **deterministic**).
- **Part B — Benchmark** (empirical / quality acceptance; **guarded**).
- **HARD GATE:** **Part B may NOT start until Part A acceptance is green** — the
  engine must be demo-able at the A/B boundary. Stated explicitly so the build
  cannot be held hostage to an empirical study, and the study cannot run against
  a moving engine.
- **Review separation:** Part A lands via `feat/*` PRs; the Part B harness +
  report lands via its own `test/*` PR (clean per-PR review boundaries — keeps
  the engineering review and the research review from tangling).

## 3. Goal

Implement ADR-016 Phase 1: a **generic, vertical-agnostic engine** in
`services/` that loads `Procedure` / `Step` / `Agent` **specs** from
`verticals/<name>/`, runs a **linear, set-valued, sequential** orchestrator over
`{query, evaluate, action, human_task}` steps, records a durable
`PipelineRun` / `StepResult` history in Postgres that **suspends at
`waiting_human` and resumes across a process restart**, enforces the ADR-016 D3
autonomy model (default-`gated` actions, agent autonomy-ceiling + handler
allowlist) and **fail-and-divert** (`on_failure ∈ {fail, escalate_to_human}`),
reuses the shipped ADR-007 envelope + approve→execute gate **verbatim** for
`action` steps, and injects each `Procedure.goal` into the LLM system prompt for
`evaluate` + action reasoning. Prove it end-to-end with **three hand-authored
example procedures** (the aquaculture "Morning Pond Health Round" headline +
energy + supply_chain) and an integration test exercising a gated-action
**suspend→approve→resume** and set-valued fan-out. **Then** (after the hard
gate) measure engine output quality with a pre-registered, ring-fenced
empirical benchmark that **reports** — never gates on — a comparison vs raw
text-to-SQL + a RAG baseline, and closes evidence-gap **G-3** (per-procedure
local-LLM model selection).

## 4. Acceptance Criteria

### Part A — Engine (deterministic; MUST be green before Part B starts)

- [ ] **A-1 Spec loaders.** `Procedure` / `Step` / `Agent` specs load from
  `verticals/<name>/procedures.yaml` + agent defs into validated Pydantic
  models matching the ADR-016 D2 shapes (`kind ∈ {query, evaluate, action,
  human_task}`; `autonomy ∈ {auto, gated}`; `on_failure ∈ {fail,
  escalate_to_human}`; `trigger ∈ {manual, schedule}` — **only `manual` is
  runnable in Phase 1 per L-1**; a `schedule` spec **loads** but raises a clear
  "deferred to PLAN-0010 reuse" error if invoked). A malformed spec raises a
  precise validation error (negative case).
- [ ] **A-2 Run records.** `PipelineRun` + `StepResult` records persist to
  Postgres via an Alembic migration (L-3); `PipelineRun.status ∈ {running,
  waiting_human, completed, failed, cancelled}`; `StepResult.status ∈
  {pending, processing, complete, waiting_human, failed}`.
- [ ] **A-3 Linear set-valued orchestrator.** A `manual`-triggered run executes
  steps **in order**; each step operates over the **prior step's output object
  set** (set-valued — "per-entity" is set semantics, **no loop construct**); an
  `input` filter predicate narrows the prior set (e.g. the breach subset).
- [ ] **A-4 Autonomy (ADR-016 D3).** `autonomy` is honored on **`action` steps
  only**, default **`gated`**; `query` / `evaluate` always run `auto`;
  `human_task` is inherently human. The engine **refuses** to invoke a handler
  not in the running `Agent`'s `allowed.action_handlers` allowlist
  (blast-radius bound — asserted against `registry.handler_names`), and refuses
  any step autonomy above `Agent.autonomy_ceiling`.
- [ ] **A-5 Durable suspend + resume across restart.** A `gated` action or a
  `human_task` step suspends the run at `status = waiting_human`; a **fresh
  process** loads the persisted `PipelineRun` and **resumes** from the suspended
  step when the human acts (behavioral: persist, simulate restart by
  reconstructing engine state from the DB, then resume).
- [ ] **A-6 Fail-and-divert.** A failed step **aborts the remainder** of the
  run; `on_failure = escalate_to_human` routes the step to `waiting_human`
  **instead of** `failed` (a human takes over rather than the run dying) —
  in-process assertion on the resulting `status`.
- [ ] **A-7 Action step reuses the shipped loop UNCHANGED.** An `action` step
  produces the **ADR-007 D2 `RecommendedAction` envelope** (the existing
  `services/engine/actions.py` class, unchanged) and routes through the
  **existing** `approve()` → `execute()` gate
  (`services/engine/recommender.py`) — asserted by reusing those symbols, not
  re-implementing them.
- [ ] **A-8 Goal as runtime directive (ADR-016 D5).** `Procedure.goal` (+ any
  per-step scoped instruction) is injected into the LLM **system prompt** for
  `evaluate` steps and action reasoning; the bound model defaults to
  `gpt-oss:20b` (ADR-001) via the running `Agent.llm_model` — asserted by a
  captured prompt-assembly probe (the goal text appears in the composed system
  prompt).
- [ ] **A-9 MANDATORY telemetry seam.** **Every** step records `duration_ms`
  **+** `reasoning_trace` (`ReasoningStep[]`, generalizing ADR-007/ADR-010
  per-action trace to **per-step**) **+** `audit` (`AuditMetadata`) into the
  `step_results` table — **regardless of `kind`** (read, judgment, write, human
  task). This is the data Part B consumes; it is required in Part A
  unconditionally. (Behavioral: after a run, every `StepResult` row has a
  non-null `duration_ms`, a trace, and an audit record.)
- [ ] **A-10 Three example procedures author + load** (L-2):
  - **aquaculture — "Morning Pond Health Round" (headline).** The ADR-016
    worked example, run **manually** in Phase 1 (its 06:00 schedule deferred):
    (1) `query`/auto latest DO reading per active `Pond`; (2) `evaluate`/auto
    verdict vs threshold (DO `< 4` mg/L = breach, 4–5 = watch, `> 5` = ok —
    grounded in `aquaculture_v0.yaml` + the shipped `OCT_RECOMMEND_DIRECTION=below`
    crash semantics); (3) `action`/**gated** for the **breach SET**, propose
    `RecommendedAction(action_type=start_emergency_aerator,
    target_pond_id=…)` → human approve → execute (ADR-007 envelope + existing
    gate verbatim); (4) `human_task` for the **watch SET** (technician visual
    check → `waiting_human` → done); (5) `action`/auto round-summary terminal
    artifact.
  - **energy.** A routine over `Asset`/`Site`/`OperationalEvent`
    (`energy_v0.yaml`; `action_type ∈ {restart, isolate, dispatch_technician,
    escalate}`) with at least one `query` → `evaluate` → gated `action` path.
  - **supply_chain.** A routine over `Shipment`/`Facility`/`OperationalEvent`
    (`supply_chain_v0.yaml`; `action_type ∈ {reroute, expedite, hold, inspect,
    escalate}`) with at least one `query` → `evaluate` → gated `action` path.
- [ ] **A-11 Headline integration test (end-to-end).** One pytest case drives
  the aquaculture "Morning Pond Health Round" manually, and asserts: the
  **set-valued fan-out** (breach / watch / ok subsets from one query set), a
  **gated-action suspend→approve→resume** at step 3, the `human_task` suspend at
  step 4, and a terminal round-summary artifact — all behavioral
  (return-value / persisted-row assertions, no `$?`; Lesson #7 §3 methods).
- [ ] **A-12 Project-wide invariants (CLAUDE.md §8).** Type hints + tests on all
  new code; `ruff check services/` clean; `mypy --strict services/` clean;
  `pytest` suite green (read pytest's own `N passed` summary line, not `$?`).

> **HARD GATE (binding).** Part B work **does not begin** until A-1 … A-12 are
> all green and the engine is demo-able. The Part B harness PR is not opened
> before the Part A `feat/*` PRs merge.

### Part B — Benchmark (empirical; guarded; starts only after the hard gate)

- [ ] **B-1 Harness + synthetic ground-truth dataset.** A benchmark harness +
  a **synthetic ground-truth dataset** (questions whose correct answers we
  control) over the three verticals. Size/coverage is **§8 SD-B3** (proposed,
  to ratify).
- [ ] **B-2 Pre-registered ABSOLUTE thresholds ratified BEFORE running.** The
  concrete threshold numbers (§8 **SD-B1**) are **locked in this Acceptance
  Criteria section and Cray-ratified before any Part B run** (anti
  moving-target). A below-threshold measurement = a **logged finding → a
  follow-up tuning PLAN**, NOT a build failure and NOT a reason to move the
  threshold.
- [ ] **B-3 Comparison vs raw text-to-SQL + a RAG baseline — REPORTED, NOT a
  gate.** The harness runs the **same synthetic questions** through (a) the
  vero-lite governed-procedure stack, (b) a raw text-to-SQL baseline, and (c) a
  RAG baseline, and **records accuracy / failure-mode / latency** for each.
  **Acceptance = "comparison run + the three measures recorded + report
  committed" — NOT "our stack wins."** Winning is the *thesis being tested*; a
  loss is a **finding**, not a build failure. *(Load-bearing guardrail — state
  it in the report header.)*
- [ ] **B-4 Per-procedure local-LLM model-selection benchmark → closes G-3.**
  For each example procedure, measure `evaluate`-step accuracy + p95 per-step
  latency across the candidate local model(s) bound per `Agent`, and record the
  selection rationale. This **closes evidence-gap G-3** (ADR-016 established
  only **bindability** per `Agent`, default `gpt-oss:20b`).
- [ ] **B-5 Report committed.** A benchmark report (numbers vs the pre-registered
  thresholds, failure-mode taxonomy, the B-3 comparison, the B-4 model
  selection, and an explicit "below-threshold → follow-up tuning PLAN" note)
  is committed via the Part B `test/*` PR.
- [ ] **B-6 Ring-fence (binding, anti moving-target).** The report states
  explicitly that any measured number below threshold is a **logged finding
  that opens a follow-up tuning PLAN** (which model / which prompt) and **MUST
  NOT reopen ADR-016's primitive shape** (Accepted/fixed). The benchmark may
  inform **tuning only** — it never re-litigates the primitive.

## 5. Out of Scope (defer — Phase 4+ per ADR-016 D7 + Out-of-scope)

- ❌ **branch / condition / loop steps** — Phase 1 is linear (ADR-016 D4; stub schema only in Phase 4+).
- ❌ **parallel / swarm agents** — Phase 4+ (ADR-016 OQ-3; stub only).
- ❌ **streaming / event-driven triggers** — Phase 4+.
- ❌ **per-step auto-retry / backoff / jitter** — Phase-1 fallback = escalate-to-human (research §Concern 2 DEFER).
- ❌ **marketplace / signing / registry / dependency-resolution infra** — versioned config dirs suffice (research §Concern 5 DEFER).
- ❌ **per-step model override** — one model per `Agent` (ADR-016 OQ-1; research §Concern 1 DEFER).
- ❌ **narrative → Procedure** — Phase 2, future PLAN (ADR-016 D7).
- ❌ **OCT monitor / command-control UI** — Phase 3, future PLAN (ADR-016 D7).
- ❌ **the `schedule` trigger** — L-1 / SD-1: the orchestrator is trigger-agnostic, but `schedule` is **deferred to a PLAN-0010-reuse follow-up** (no scheduler built here).
- ❌ **`vet_clinic` example** — parked (ADR-005); L-2 ships three verticals.

## 6. Steps

### Part A — Engine

- **Step A-α — Spec layer.** Define the `Procedure` / `Step` / `Agent` Pydantic
  spec models (ADR-016 D2 shapes) + a loader reading
  `verticals/<name>/procedures.yaml` + agent defs. Trigger-agnostic: `schedule`
  loads but is not runnable (L-1). *(AC A-1.)*
- **Step A-β — Run records + migration.** `PipelineRun` + `StepResult`
  SQLAlchemy models + an Alembic migration (L-3), table shapes per §8 **SD-A1**.
  *(AC A-2, A-9.)*
- **Step A-γ — Orchestrator.** Linear set-valued sequential executor over
  `{query, evaluate, action, human_task}`; the autonomy model (D3); the handler
  allowlist + autonomy-ceiling enforcement; fail-and-divert. *(AC A-3, A-4,
  A-6.)*
- **Step A-δ — Durable suspend/resume.** Persist at `waiting_human`; reconstruct
  engine state from the DB and resume from the suspended step. *(AC A-5.)*
- **Step A-ε — Action-step adapter + goal injection.** Route `action` steps
  through the **existing** ADR-007 envelope + `approve()`/`execute()` gate
  verbatim; inject `Procedure.goal` into the LLM system prompt for `evaluate` +
  action reasoning. *(AC A-7, A-8.)*
- **Step A-ζ — Three example procedures.** Author `procedures.yaml` + agent defs
  for aquaculture (headline), energy, supply_chain (L-2). *(AC A-10.)*
- **Step A-η — Headline integration test + invariants.** End-to-end aquaculture
  test (suspend→approve→resume + fan-out); ruff / mypy --strict / pytest clean.
  *(AC A-11, A-12.)* Lands via `feat/*` PR(s).

> **HARD GATE here** — engine demo-able; Part A PR(s) merged.

### Part B — Benchmark (only after the hard gate)

- **Step B-α — Threshold pre-registration.** Lock the §8 SD-B1 numbers into §4
  Part B and get Cray ratification **before any run**. *(AC B-2.)*
- **Step B-β — Synthetic dataset.** Author the ground-truth dataset (§8 SD-B3
  size/coverage). *(AC B-1.)*
- **Step B-γ — Harness + baselines.** Build the harness; wire the raw
  text-to-SQL + RAG comparison baselines on the **same** questions. *(AC B-3.)*
- **Step B-δ — Model-selection sweep (G-3).** Per-procedure accuracy + latency
  across candidate local models bound per `Agent`. *(AC B-4.)*
- **Step B-ε — Report.** Commit the report (numbers vs pre-registered
  thresholds, failure-mode taxonomy, comparison findings, model selection,
  ring-fence note). *(AC B-5, B-6.)* Lands via a dedicated `test/*` PR.

## 7. Verification

"Done" = all §4 Part A criteria green via Lesson #7 §3 reliable methods (the
aquaculture headline runs end-to-end manually including a gated-action
suspend→approve→resume and set-valued fan-out; ruff / mypy --strict / pytest
clean from their own summary lines); then, **after the hard gate**, all §4
Part B criteria green with the pre-registered thresholds ratified *before* the
run and the comparison **reported, not gated**. Per ADR-009 D2, **Code** runs
verification and commits; the drafter holds no execution or commit authority.

## 8. Surfaced decisions (for Cray — do NOT silently resolve)

> Recommendations below are load-bearing in the draft but **contingent on Cray's
> ratification**. Numbers in SD-B1 / SD-B3 MUST be ratified before any Part B run.

- **SD-1 (confirm L-1 = ADR-016 OQ-2 for Phase-1).** *Recommendation:* confirm
  **manual-only** trigger for Phase-1, orchestrator trigger-agnostic, `schedule`
  deferred to a PLAN-0010-reuse follow-up. *Why a Cray decision:* it formally
  resolves ADR-016 OQ-2 for Phase-1 — an ADR open question, not a Code judgment
  call. (Recorded as L-1; this SD asks for the explicit OQ-2 ratification.)

- **SD-A1 (Postgres table shapes for `PipelineRun` / `StepResult`) — ✅ RATIFIED (Cray, 2026-06-07).**
  *Decision:* `pipeline_runs(run_id PK, procedure_id, agent_id,
  trigger_context JSONB, status, started_at, updated_at)` and
  `step_results(step_result_id PK, run_id FK→pipeline_runs, step_id, status,
  duration_ms INT NULL, artifact JSONB, reasoning_trace JSONB, audit JSONB,
  created_at)` — JSONB for the set-valued artifact + the per-step trace/audit
  (cheapest durable shape; matches the existing async-SQLAlchemy stack and the
  PLAN-0005 BIGINT pin note for any integer columns). The normalized
  `reasoning_steps` child table alternative (more queryable for the Phase-3 OCT
  monitor; heavier now) is **deferred to a Phase-3 optimization if needed**, not
  taken now. *Rationale for early ratification:* the durable schema is
  foundational (resume + the Phase-3 monitor read it) and is awkward to migrate
  later — same class as PLAN-0005 OQ-4.

- **SD-A2 (engine home path under `services/`) — ✅ RATIFIED (Cray, 2026-06-07).**
  *Decision:* `services/engine/procedures/` (a new sub-package: `spec.py`
  loaders, `orchestrator.py`, `runs.py` records) — sits beside the existing
  `services/engine/{actions,recommender,registry}.py` it reuses, honoring the
  ADR-016 D6 "engine in `services/`" boundary. The top-level
  `services/procedures/` alternative is **not taken**. *Rationale for early
  ratification:* a layout choice that sets the import surface for Phase 2/3;
  cheap to pick now, annoying to move later.

- **SD-B1 (pre-registered ABSOLUTE thresholds — ratify BEFORE any Part B run).**
  *Recommendation (candidate numbers, propose-not-blank):* (i) `evaluate`-step
  accuracy **≥ 85%** on the synthetic set; (ii) p95 per-step latency **≤ 8 s**
  on `gpt-oss:20b` (the model warms ~13 s cold per the MS-S1 note — warm first;
  p95 is steady-state). *Why a Cray decision:* these are the anti-moving-target
  guardrail; if they are not ratified **before** the run, the benchmark is not
  pre-registered. They are deliberately conservative starting points — Cray
  should set the bar Cray is willing to hold.

- **SD-B2 (synthetic-dataset size / coverage).** *Recommendation:* ~30 questions
  per vertical (~90 total), covering each example procedure's `query` +
  `evaluate` paths and the breach / watch / ok verdict boundaries (esp.
  aquaculture DO at the 4 mg/L threshold edge). *Alternative:* a larger set for
  tighter CIs (more authoring cost). *Why a Cray decision:* size sets the
  statistical weight of the G-3 / comparison findings and the authoring budget.

- **SD-B3 (G-2 "build-cost via the `new-vertical` generator" — IN Part B or
  deferred?).** *Recommendation:* **surface as OPTIONAL / lean DEFER.** G-2
  (cost to onboard a new vertical via the ADR-006 D3 generator) is more tangential
  to *engine quality* than G-1 / G-3 / G-4; the `new-vertical` generator is itself
  not yet built (PLAN-0005 §3.4 forward reference). *Why a Cray decision:*
  whether to widen Part B's scope to a build-cost measure vs keep Part B focused
  on output quality is a scope/priority call, not a Code judgment.

## 9. References

### Binding design
- `docs/adr/0016-governed-procedure-engine.md` — D2 primitive, D3 autonomy, D4 linear/set-valued/durable/fail-and-divert, D5 goal, D6 engine-vs-config, D7 phases + deferral list, worked example, OQ-1/2/3.

### Reused shipped surfaces (verbatim)
- `services/engine/actions.py` — ADR-007 D2 `RecommendedAction` envelope (UNCHANGED).
- `services/engine/recommender.py` — `ActionRecord` / `ActionStatus` / `approve` / `reject` / `execute` / `ApprovalError` (the existing gate).
- `services/engine/registry.py` — adapter + handler registry; `handler_names` (allowlist source).
- `services/engine/llm/` — two-call Pattern B; `gpt-oss:20b` pin (ADR-001).
- `services/db/persistence.py`, `services/api/routers/actions.py` — the OQ-1 projection + the shipped action-loop endpoints.

### Example-procedure ontologies (L-2)
- `verticals/aquaculture/ontology/aquaculture_v0.yaml` — Pond / Farm / OperationalEvent / Alert / RecommendedAction; `action_type = start_emergency_aerator`; DO threshold 4 mg/L, breach BELOW.
- `verticals/energy/ontology/energy_v0.yaml`, `verticals/supply_chain/ontology/supply_chain_v0.yaml`.

### Grounding research (private/gitignored — reference by path, not as public links)
- `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md` — 5 findings + per-concern DEFER lists.
- `docs/research/private/2026-06-06-impl-approach-reconciliation.md` — on-thesis framing; evidence-gap G-3.

### Governance
- `CLAUDE.md` §6 (Decision / Plan Flow), §8 (ADRs merged before implementation; AI assistive).
- ADR-009 D1 (interim authoring), D2 (only Code commits); ADR-013 (autonomy-axis relocation); ADR-012 D4.3 (author≠reviewer disclosure).

---

*PLAN-0019 (Phase 1) — Draft authored by the `plan-drafter` subagent 2026-06-07.
Implements ADR-016 Phase 1 (Accepted; merged before this implementation PR per
CLAUDE.md §8). Moves to Ready for execution on Cray adjudication of §8 (notably
SD-B1 threshold pre-registration) + Code landing the doc on `origin/main`.*

*AI-assisted per project convention.*
