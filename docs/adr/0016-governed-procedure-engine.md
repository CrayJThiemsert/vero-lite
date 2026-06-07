# ADR-016: Governed Procedure Engine — expand the action layer from `anomaly→action` to `anomaly AND normally→action`

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-005 (strategic pivot to OCT — **expands feature-3**), ADR-007 (OCT engine contracts — **generalizes** the D2 `RecommendedAction` envelope; does **not** break it), ADR-008 (YAML ontology spec — the six `object_types` are **untouched**; `procedures.yaml` is a separate spec layer), ADR-001 (LLM model baseline — the local `gpt-oss:20b` pin is the default `Agent` model), ADR-010 (LLM reasoning-hook surface — the per-action reasoning trace generalizes to per-step), ADR-013 (autonomy-axis relocation — safe / human-gated autonomy posture). Implementation deferred to **PLAN-0019**. Grounding research: `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md` (5 Palantir findings, 25 claims 3-0 / 0 killed), `docs/research/private/2026-06-06-impl-approach-reconciliation.md` (on-thesis framing). This ADR does **not** supersede any prior ADR.

> **Drafting provenance.** Drafted (uncommitted) by the in-harness
> `plan-drafter` subagent under ADR-009 D1 interim authoring per ADR-013's
> phased relocation; Code commits via PR (ADR-009 D2). ADR number (ADR-016)
> founder-approved (G2 gate cleared) before drafting. The capability
> framing (`anomaly AND normally→action`), the `Procedure/Step/PipelineRun/Agent`
> primitive shape, and the Phase-strategy were Cray-originated in the dispatch;
> this draft renders and cross-checks them against the cited ADRs + research,
> and surfaces residual choices as Open Questions / Surfaced decisions rather
> than silently resolving them. **Author≠reviewer disclosure (ADR-012 D4.3):**
> outline originator = Cray (founder); independent reviewer = Cray at PR merge
> ratification (Proposed → Accepted). Separation between drafter (plan-drafter)
> and reviewer (Cray) is **intact**.

## Context

### Where the action layer is today (reactive only)

vero-lite's OCT action layer is currently **reactive**. An `OperationalEvent`
crosses a threshold → an `Alert` is derived → the recommender emits a single
`RecommendedAction` (ADR-007 D2 envelope, filled by an LLM per ADR-010) →
a human approves → a registered handler executes. This is the shipped
propose→approve→execute loop (PLAN-0005 Phase 2, PLAN-0006 LLM brain-swap;
ADR-010 Context). It answers exactly one question: *"something went wrong —
what single action do you recommend?"*

That covers OCT feature-3 (ADR-005: "anomaly detection + suggested action")
but only its reactive half. It does **not** cover a vertical's *normal /
routine operating workflow* — the multi-step sequence a human operator runs
day-to-day (e.g. a morning round: read every pond's dissolved-oxygen, judge
each against threshold, act on the bad ones, schedule a check on the
borderline ones, write a summary). Today that whole routine is invisible to
the engine; only the one breach inside it (step 3 of that round) is modeled.

### What the founder wants, and why it is on-thesis

Cray wants the engine to **also** cover the routine — the day-to-day operating
procedure — as governed, human-gated, agentic execution, and to do so as a
**reusable cross-vertical engine** (the same config-driven, multi-vertical
thesis that already powers the ontology generator and the Tier-1 Mirror demo,
ADR-015 / ADR-006).

This is squarely on-thesis (`2026-06-06-impl-approach-reconciliation.md` §1,
row 3): vero-lite's edge over the closest cousin (semantic / metrics layers)
is precisely that **an ontology proposes governed *actions* with a trace, a
human gate, and a fail-safe — semantic layers only answer.** Extending from
`anomaly→action` to `anomaly AND normally→action` doubles down on the one axis
the reconciliation named as the differentiator. It also keeps vero-lite at the
**safe, audited, human-gated end of the agentic spectrum** rather than chasing
unbounded autonomous tool-calling, which has a documented reliability gap
(reconciliation §1 row 3; the "LLM-as-planner" framing). The differentiator
sharpens from *"ontologies answer questions"* to *"ontologies orchestrate
governed workflows, not just answer."*

### The empirical grounding (Palantir, verified)

The primitive shape below is grounded in how Palantir *actually* models the
same five concerns, distilled to a **minimal** adoption (anti-scope-creep) in
`2026-06-07-palantir-5-concerns-pipeline-design.md`. All five findings were
verified 3-0 (0 killed) against primary `palantir.com/docs` (2026 currency
confirmed):

1. **Agent-as-actor is first-class** — an AIP Agent (now "AIP Chatbot") is an
   independently-authored entity with a declared, typed tool set and an LLM
   binding (`agent-studio/core-concepts`, `agent-studio/tools`).
2. **Failure semantics live in Foundry Automate, not the agent** — per-effect
   retries/fallback and **strict fail-and-divert** (a failed effect halts the
   remainder), and there is **no run-status enum** ("waiting for human" is a
   staged-Action proposal, not a named lifecycle state)
   (`automate/retries`, `automate/effect-fallback`).
3. **Approval is a per-WRITE / per-Action setting** — Command/Action approval
   attaches to write steps; **reads/queries/calculations are not gated**
   (`agent-studio/commands-as-tools`, `logic/aip-logic-integration-automate`).
4. **Goal = a runtime LLM directive** — the Instructions / system-prompt is
   compiled into the raw system prompt; freeform NL, not structured metadata
   (`agent-studio/core-concepts`, `logic/blocks`).
5. **Engine-vs-config = code-signed Marketplace product bundles** — config
   (Ontology / Actions / Automations / Agents) is packaged as a portable,
   self-contained bundle, so the same engine serves many enrollments
   (`marketplace/foundry-products`, `foundry-devops/export-import-products`).

vero-lite adopts the high-leverage **patterns** from each, in mid-market-simple
form (one local model per agent, versioned config directories instead of a
signing/registry product), and **defers** the heavyweight parts (multi-agent
swarm, retry/backoff, marketplace infra).

## Decision

This ADR establishes a **capability + a primitive**; all implementation
mechanics are deferred to **PLAN-0019**.

### D1: Capability expansion — `anomaly→action` becomes `anomaly AND normally→action`

OCT feature-3 (ADR-005) is expanded from reactive-only to cover both the
anomaly path **and** the normal / routine operating workflow. The existing
reactive loop is **reframed as the degenerate case** — call it **"Pipeline
v0"**: a 1-step, event/`Alert`-triggered, human-gated procedure. Nothing about
the shipped loop changes; it is recast as the simplest instance of the general
primitive in D2. The general case adds multi-step, manually- or
schedule-triggered, governed procedures over the same ontology and the same
action gate.

### D2: New primitive — `Procedure / Step / PipelineRun / Agent`

This is the core decision. Two of the four are **specs** authored per-vertical
alongside the ontology YAML (the six-`object_types` ontology of ADR-008 is
**untouched** — `procedures.yaml` and agent defs are a **separate spec layer**);
one is a **run-time record** that is purely **additive** (it does **not** modify
the ADR-007 `RecommendedAction` envelope).

#### `Procedure` — a SPEC (`verticals/<name>/procedures.yaml`)

```yaml
procedure_id: <stable_id>
title: <string>
goal: <freeform NL directive>      # runtime LLM directive — see D5 (NOT documentation)
run_by: <agent_id>                 # the Agent that runs this Procedure (see Agent below)
trigger: manual | schedule         # event/Alert is the already-existing Phase-0 path (Pipeline v0)
steps:                             # ordered, LINEAR, SET-VALUED list — see D4
  - <Step>
  - ...
terminal: <step_id | artifact spec>  # final step / produced artifact
```

#### `Step`

```yaml
step_id: <stable_id>
name: <string>
description: <string>
kind: query | evaluate | action | human_task
autonomy: auto | gated            # applies to `action` steps ONLY; default = gated (D3)
                                  #   query/evaluate are ALWAYS auto; human_task is inherently human
on_failure: fail | escalate_to_human
input:  <prior-step output> [+ optional filter predicate]   # set-valued; see D4
output: <produced object set / artifact>
```

- `kind` is the type of work: a read (`query`), a deterministic/LLM judgment
  (`evaluate`), a consequential write (`action`), or offline human work
  (`human_task`).
- `autonomy` is an axis of `action` steps **only** — a "go/no-go checkpoint"
  is just a `gated` action (the human approves the consequential write
  itself), which is why there is no separate `human_gate` kind.

#### `Agent` — a SPEC (`verticals/<name>/`, the actor that RUNS a Procedure)

```yaml
agent_id: <stable_id>
name: <string>
llm_model: <local Ollama model>    # DEFAULT = gpt-oss:20b per ADR-001 (Amendment 1; structured-gen path)
autonomy_ceiling: auto | gated     # the MAX autonomy this agent may exercise
allowed:                           # allowlist — BOUNDS blast radius (D3)
  step_kinds: [query, evaluate, action, human_task]
  action_handlers: [<registered handler name>, ...]
```

Per-**procedure** model selection is achieved by `run_by` pointing at
different `Agent`s — a vertical may define several `Agent`s binding different
local models. Per-**step** model override is **deferred** (Palantir finding 1
"one model per agent"; research §"Concern 1" DEFER list).

#### `PipelineRun` — a run-time RECORD (purely ADDITIVE)

```python
# Illustrative shape (NOT the ADR-007 RecommendedAction envelope — that is unchanged).
run_id: str
procedure_id: str
agent_id: str
trigger_context: dict            # what fired this run (manual actor / schedule tick / event)
started_at: datetime
status: running | waiting_human | completed | failed | cancelled
step_results: list[StepResult]   # one per step

# StepResult
step_id: str
status: pending | processing | complete | waiting_human | failed
duration_ms: int | None
artifact: <produced object set / output>     # the step's output
reasoning_trace: <ReasoningStep[]>           # generalizes ADR-007 D2 / ADR-010 per-action trace to per-step
audit: <AuditMetadata>                        # generalizes ADR-007 D2 AuditMetadata to per-step
```

An `action` step **produces a `RecommendedAction`** (the ADR-007 D2 envelope,
**unchanged**) and routes it through the **existing** approve→execute gate.
The reasoning trace and audit metadata that ADR-007/ADR-010 attach per-action
are **generalized to per-step** in `step_results` — every step (read, judgment,
write, human task) carries its own trace + audit, which is the legibility
upgrade the OCT monitor (D7, Phase 3) consumes.

### D3: Autonomy model + safe-agentic posture

- **Autonomy attaches to WRITE / `action` steps only.** `query` and `evaluate`
  are always `auto` — reads and judgments are never gated (Palantir finding 3:
  no human-review gate on reads/calc). This is a deliberate refinement of the
  earlier human-gate seam.
- **`action` defaults to `gated`** — safe-by-default. Human review is
  **opt-out**, not opt-in (mirrors Palantir's Command approval = enabled by
  default). A vertical author must consciously set `autonomy: auto` on a write.
- **`Agent.autonomy_ceiling` + `allowed`** bound what the engine may do
  autonomously: the ceiling caps the maximum autonomy any step under that
  agent may exercise, and the `allowed` allowlist (step kinds + action
  handlers) **bounds blast radius** — the engine cannot invoke a handler the
  agent is not allowlisted for.
- **Posture (explicit).** vero-lite occupies the **human-gated, audited,
  fail-safe end of the agentic spectrum**, *against* unbounded autonomous
  agents. The reconciliation note (`2026-06-06-impl-approach-reconciliation.md`
  §1) names the agentic reliability gap as the reason the safe end is the
  product, not a limitation. This aligns with ADR-013's safe / human-gated
  autonomy posture and CLAUDE.md §8 ("AI outputs are assistive — never
  auto-...").

### D4: Linear + set-valued steps; durable, resumable runs

- **Linear.** Phase-1 steps are a **linear** ordered list — no branch / no
  loop. (Branch/condition + loop are Phase-4+ stub-only — D7.)
- **Set-valued.** A step operates over an **object set** (the prior step's
  output set), not a single entity. **"Per-entity" is set semantics, not a
  loop construct** — grounded in Palantir Automate's object-set model
  (failure is per-object: a failing object stops while siblings continue;
  research §"Concern 2"). `input` may carry an optional filter predicate that
  narrows the prior step's set (e.g. "the breach subset").
- **Durable / resumable.** `PipelineRun`s are **not synchronous**. A `gated`
  or `human_task` step **suspends** the run at `status = waiting_human`
  (possibly for hours or days) and the run **resumes** when the human acts.
- **Failure semantics = fail-and-divert.** A failed step **aborts the
  remainder** of the run (Palantir's strict fail-and-divert). `on_failure =
  escalate_to_human` routes the step to `waiting_human` **instead of**
  `failed` — a human takes over rather than the run dying. The explicit
  `status` enum is an **addition** over Palantir (which has no run-status
  enum) — a deliberate legibility win for the OCT monitor.

### D5: `goal` is a runtime LLM directive, not documentation

`Procedure.goal` (and per-step scoped instructions) are **freeform NL injected
into the LLM system prompt at run time** to steer LLM-backed steps (`evaluate`,
and the reasoning inside an `action`). It is **not** mere documentation
(Palantir finding 4: the Goal/objective equivalent is a runtime directive
compiled into the system prompt, not structured metadata). Well-scoped
per-procedure prompts are the **robustness lever** that lets a small **local**
model (`gpt-oss:20b`, ADR-001) perform reliably on a narrow, well-specified
task — the prompt narrows the task, the local model is sized for it.
(Structured / typed objective schemas and goal-decomposition planners are
deferred — research §"Concern 4" DEFER.)

### D6: Engine-vs-config boundary (the reusable cross-vertical engine)

- **The ENGINE is generic and vertical-agnostic** — the orchestrator plus the
  `Procedure / Step / PipelineRun / Agent` runtime — and lives in `services/`.
- **All per-vertical CONFIG** lives under `verticals/<name>/`: the ontology
  YAML (ADR-008, untouched) **plus** `procedures.yaml` **plus** the `Agent`
  definitions.

This is **already vero-lite's structure**; the ADR records it as the boundary
that makes **one engine serve many verticals**, validating the Rule-of-Three
template-first strategy (ADR-006 D4 / ADR-015). It is the direct analogue of
Palantir's code-signed Marketplace product bundles (finding 5) — same
principle, **mid-market-simple**: ours are versioned per-vertical config
directories, not a signed/registry product. (Full marketplace / signing /
dependency-resolution infra is deferred — research §"Concern 5" DEFER.)

### D7: Phase strategy (high-level; implementation in PLANs)

| Phase | Scope | Status / owner |
|---|---|---|
| **Phase 0 — substrate** | the existing `anomaly→action` loop, reframed as Pipeline v0 (D1) | **shipped** (PLAN-0005/0006) |
| **Phase 1 — Core Procedure baseline** | the primitive (D2) + a linear, set-valued orchestrator over `{query, evaluate, action, human_task}` + **one hand-authored example procedure per existing vertical** | **PLAN-0019** |
| **Phase 2 — narrative→Procedure** | extend the PLAN-0017 intake face so a stakeholder narrative also yields a **Procedure skeleton** behind the human-review gate | future PLAN |
| **Phase 3 — OCT as Command / Control / Monitor center** | pipelines list / live run detail / config UI (consumes the per-step trace + the run-status enum) | future PLAN |
| **Phase 4+ — DEFERRED (stub schema only)** | branch/condition + loop steps; parallel / swarm agents; `schedule`→streaming / event-driven triggers; per-step auto-retry/backoff; marketplace / signing / registry | **not in scope** (deferral list) |

## Worked example (real aquaculture ontology) — "Morning Pond Health Round"

A concrete Phase-1 procedure on the shipped `aquaculture` vertical
(`verticals/aquaculture/ontology/aquaculture_v0.yaml`), to keep the primitive
grounded. `trigger: schedule` (daily 06:00, `Farm`-scoped), `run_by` an Agent
bound to `gpt-oss:20b`:

| # | `kind` / `autonomy` | What it does (set-valued) |
|---|---|---|
| 1 | `query` / auto | Latest dissolved-oxygen reading per active `Pond` — `OperationalEvent` with `event_type = reading`, `measured_value` in mg/L. Output = a set of (pond, DO) pairs. |
| 2 | `evaluate` / auto | Verdict per pond vs threshold: DO < 4 = **breach**, 4–5 = **watch**, > 5 = **ok**. Output = three pond subsets. |
| 3 | `action` / **gated** | For the **breach** SET, propose `RecommendedAction(action_type = start_emergency_aerator, target_pond_id = …)` → **human approve → execute**. Reuses the ADR-007 D2 envelope + the existing gate verbatim. |
| 4 | `human_task` | For the **watch** SET, assign a technician an offline visual-check task (`waiting_human` → done). |
| 5 | `action` / auto | Write a round-summary **terminal** artifact. |

**Note the reframing in action:** step 3 **is** the existing `anomaly→action`
machinery (the Pipeline-v0 degenerate case of D1) — now invoked *from inside a
routine* rather than only from a standalone breach event. The routine wraps the
reactive loop; the reactive loop is unchanged.

## Out of scope / Non-goals

State explicitly — this ADR is a **capability / decision** document, not an
implementation spec:

- **Implementation detail** → **PLAN-0019** (Phase 1). The orchestrator
  mechanics, persistence, suspend/resume plumbing, and the concrete Pydantic
  shapes are PLAN-0019's.
- **Selecting WHICH local model fits each procedure** → a downstream **Thread-2
  empirical benchmark** closing evidence-gap **G-3** (local-LLM
  accuracy/latency behind the semantic layer;
  `2026-06-06-impl-approach-reconciliation.md` §4 gap 3). This ADR only
  establishes that the model is **bindable per `Agent`** (default `gpt-oss:20b`).
- **All Phase-4+ deferred features** — branch / condition / loop steps,
  parallel / swarm agents, streaming / event-driven triggers, per-step
  auto-retry / backoff, marketplace / signing / registry (D7 deferral list).

## Consequences

### Positive

- **Bigger capability surface** — the engine covers routine operating
  workflows, not just anomaly response (D1); OCT feature-3 doubles in reach.
- **Reusable cross-vertical engine** — generic engine in `services/` + per-vertical
  config in `verticals/<name>/` (D6) validates the Rule-of-Three template-first
  strategy (ADR-006 / ADR-015) and reuses the exact structure already in place.
- **Sharper differentiator** — *"ontologies orchestrate governed workflows, not
  just answer"* extends the reconciliation's load-bearing line (semantic layers
  answer; an ontology proposes governed actions with a trace + gate + fail-safe).
- **More legible run lifecycle than Palantir** — the explicit
  `PipelineRun.status` enum + per-step trace/audit is an *addition* over
  Palantir's effect-level-only model (no run-status enum) — directly feeds the
  Phase-3 OCT monitor.
- **Additive / low blast radius** — the ADR-007 `RecommendedAction` envelope
  and the six-`object_types` ontology (ADR-008) are **untouched**;
  `PipelineRun` is a new record and `procedures.yaml` is a new spec layer. The
  shipped reactive loop is reframed, not rewritten.

### Negative / risks

- **Agentic reliability risk** — multi-step LLM-backed execution can compound
  errors. **Mitigated** by default-`gated` action steps (D3), the
  `autonomy_ceiling` + handler allowlist (D3), and fail-and-divert with
  escalate-to-human (D4) — vero-lite stays at the safe end of the spectrum.
- **Scope-creep risk** — "agentic workflow engine" invites unbounded ambition.
  **Mitigated** by the explicit Phase-4+ deferral list (D7) and the minimal-adoption
  discipline that already trimmed the Palantir patterns (research DEFER lists).
- **Another authored artifact per vertical** — `procedures.yaml` (+ `Agent`
  defs) is one more thing to author and maintain per vertical, on top of the
  ontology YAML. Acceptable: it is the price of the routine-workflow capability
  and is still pure config (no per-vertical engine code).

### Neutral

- This is a capability / strategic-posture decision (expand the action layer) —
  hence an ADR + PLAN rather than ad-hoc code.
- This ADR merges **before** PLAN-0019's implementation PR (CLAUDE.md §8
  "ADRs merged before related implementation").

### Open Questions

- **OQ-1 (model-binding granularity).** Phase-1 binds **one model per `Agent`**
  (per-procedure selection via `run_by`); per-**step** model override is
  deferred. Does per-step override ever become worth the complexity, or does
  multi-Agent-per-vertical cover it permanently? (Palantir's own per-agent vs
  per-block granularity is only partially documented — research §"Concern 1"
  caveat; moot for us at one local pin.) Deferred.
- **OQ-2 (`schedule` reuse).** Does the `schedule` trigger reuse the existing
  PLAN-0010 autonomy / recovery loop machinery, or does Phase-1 introduce a
  separate scheduler? (Phase-1 has only `manual` + `schedule`; event/Alert is
  the Phase-0 path.) Deferred to PLAN-0019 dispatch.
- **OQ-3 (multi-agent orchestration shape).** When Phase-4+ adds parallel /
  swarm agents, is delegation a first-class primitive or composed via an
  `action` step that invokes another `Procedure`? (Palantir does not evidence a
  first-class swarm primitive — research §Open-questions.) Deferred — stub
  schema only in Phase 1.

## Alternatives Considered

### Alternative 1: Unbounded autonomous agent (tool-calling, no gates)

- **Pros:** maximal capability; least authoring (the LLM plans + acts freely).
- **Cons:** documented agentic reliability gap (reconciliation §1); no
  fail-safe; not auditable per step; contradicts CLAUDE.md §8 "assistive, never
  auto-" and ADR-013's human-gated posture.
- **Why rejected:** the **safe, gated, audited end** of the spectrum is the
  product (the differentiator), not a limitation to escape.

### Alternative 2: Mirror Palantir 1:1 (two products + a deployment layer)

- **Pros:** battle-tested; full feature parity (retries, fallback, marketplace,
  k-LLM multi-provider, swarm).
- **Cons:** solo-dev / mid-market scope (the ADR-008 Alt-4 "Palantir-lite not
  Palantir-full" framing); most of it is YAGNI for Phase 1; multi-provider
  k-LLM contradicts the local-LLM residency posture (ADR-001/ADR-002).
- **Why rejected:** adopt the **patterns** (agent-as-actor, fail-and-divert,
  per-write gate, runtime-directive goal, engine-vs-config) in minimal form;
  defer the heavyweight machinery (research DEFER lists per concern).

### Alternative 3: Branch/loop + parallel steps in Phase 1

- **Pros:** richer procedures immediately; closer to a general workflow engine.
- **Cons:** large surface; control-flow + parallel orchestration is where
  agentic reliability and failure-semantics complexity concentrate.
- **Why rejected:** Phase-1 is **linear + set-valued + sequential** by design
  (D4); set semantics already cover "per-entity" without a loop construct.
  Branch/loop/parallel are Phase-4+ stub-only (D7).

### Alternative 4: Extend the six-`object_types` ontology (ADR-008) to carry procedures

- **Pros:** one spec file per vertical; no new artifact.
- **Cons:** conflates the domain model (objects/links) with operational
  workflow; would modify the ADR-008 grammar (which must stay untouched);
  couples two layers that version and review independently.
- **Why rejected:** keep them **separate** — `procedures.yaml` + `Agent` defs
  are a distinct spec layer beside the ontology (D2/D6). The ontology stays a
  pure domain model.

## References

- ADR-005 (strategic pivot to OCT — the three OCT features; feature-3 expanded here)
- ADR-007 (OCT engine contracts — D2 `RecommendedAction` envelope, generalized not broken)
- ADR-008 (YAML ontology specification — six `object_types`, untouched; `procedures.yaml` is a separate layer)
- ADR-001 (LLM model baseline — `gpt-oss:20b` Amendment 1 pin; the default `Agent` model)
- ADR-010 (LLM reasoning-hook surface — the per-action trace generalized to per-step)
- ADR-013 (autonomy-axis relocation — safe / human-gated autonomy posture)
- ADR-006 (vertical plugin architecture — D4 Rule of Three; engine-vs-config), ADR-015 (Tier-1 Mirror demo; same multi-vertical thesis)
- `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md` — 5 Palantir findings (25 claims 3-0 / 0 killed); primary `palantir.com/docs` URLs (agent-studio, automate, logic, marketplace, foundry-devops)
- `docs/research/private/2026-06-06-impl-approach-reconciliation.md` — on-thesis framing (action-layer differentiator; agentic reliability gap; evidence-gap G-3 local-LLM benchmark)
- `verticals/aquaculture/ontology/aquaculture_v0.yaml` — the worked-example ontology (Pond / Farm / OperationalEvent / Alert / RecommendedAction; `action_type = start_emergency_aerator`; DO threshold 4 mg/L, breach below)
- CLAUDE.md §3 (three-layer architecture), §8 (AI assistive, data residency)

## Implementation Notes

- **PLAN-0019** is the Phase-1 build: the `Procedure / Step / PipelineRun /
  Agent` runtime + a linear, set-valued, sequential orchestrator over
  `{query, evaluate, action, human_task}` + one hand-authored example procedure
  per existing vertical (the "Morning Pond Health Round" above is the
  aquaculture headline). PLAN-0019 owns all implementation mechanics; this ADR
  fixes only the capability + the primitive shape.
- Phase-2 (narrative→Procedure) folds into a future extension of the PLAN-0017
  intake face; Phase-3 (OCT monitor) is its own future PLAN. Both are
  forward-declared here, not drafted.
- Evidence-gap **G-3** (which local model per procedure) is a Thread-2 empirical
  benchmark, **not** this ADR or PLAN-0019 — the ADR only establishes
  bindability per `Agent`.
- Status flips Proposed → Accepted on Cray ratification; Code applies the edit +
  commits (ADR-009 D2; CLAUDE.md §6 Decision Flow).
