# ADR-016: Governed Procedure Engine — expand the action layer from `anomaly→action` to `anomaly AND normally→action`

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-005 (strategic pivot to OCT — **expands feature-3**), ADR-007 (OCT engine contracts — **generalizes** the D2 `RecommendedAction` envelope; does **not** break it), ADR-008 (YAML ontology spec — the six `object_types` are **untouched**; `procedures.yaml` is a separate spec layer), ADR-001 (LLM model baseline — the local `gpt-oss:20b` pin is the default `Agent` model), ADR-010 (LLM reasoning-hook surface — the per-action reasoning trace generalizes to per-step), ADR-013 (autonomy-axis relocation — safe / human-gated autonomy posture). Implementation deferred to **PLAN-0019**. Grounding research: `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md` (5 Palantir findings, 25 claims 3-0 / 0 killed), `docs/research/private/2026-06-06-impl-approach-reconciliation.md` (on-thesis framing). This ADR does **not** supersede any prior ADR.

**Amendments:** D3 Amendment (2026-06-11) → ADR-0019 (`watch → gated`-proposal routing). **D2 Amendment (2026-06-25)** → first-class typed `facet:` Step field (**Accepted** 2026-06-25 — Cray-ratified). **D2 + D3 Amendment (2026-07-01)** → typed read-side ontology object-binding for query steps (Q3) (**Accepted** 2026-07-01 — Cray-ratified). **D2 + D3 Amendment (2026-07-05)** → typed service-principal for non-human (`schedule`) triggers (S2; requester-never-approver) (**Accepted** 2026-07-05 — Cray-ratified, session 102; OQ-1 = vertical-level registry, OQ-2 = separate `RunContext.service_principal` field, OQ-3 = audit-only `actor_kind`). **Amendment (2026-07-09)** → join/projection grammar for multi-read query steps (Q4) (**Accepted** 2026-07-09 — Cray-ratified, session 115; SD-A Hybrid surface / SD-B two-shape v1 scope / SD-C co-exist + parity migration; OQ-1 = typed `StepInput` `join`/`project` construct, OQ-2 = no repair loop in v1, OQ-3 = join+projection only (computation stays downstream/seed), OQ-4 = warn-first override validation — all as-recommended).

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

### D2 Amendment (2026-06-25): first-class typed `facet:` Step field

> **Status:** **Accepted** (Cray-ratified 2026-06-25, session 77 — both forks: Fork 1 Hybrid scope + Fork 2 Discriminated gate_kind). **Date:** 2026-06-25 (session 77). **Deciders:**
> Jirachai Thiemsert (founder). **Amends:** D2 (the `Step` grammar) — **extends,
> does not reverse or renumber**; mirrors the **D3 Amendment (2026-06-11) /
> ADR-0019** in-place precedent.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray (s77
> greenlight, 2026-06-25). Drafter = Cowork (Tier-1 governance authoring,
> ADR-009 D1). Independent reviewer = Cray at ratification + Code R2-review at
> commit. The drafter is not the ratifier — separation **intact**. The schema
> fork below (**Hybrid + Discriminated**) was adjudicated by Cray *during*
> drafting; the independent-deliberation check is therefore Code's R2-review +
> Cray's ratification, not a separate Cowork deliberation pass.

#### Context for the amendment

D2 fixed the `Step` grammar; PLAN-0019 / PLAN-0022 then shipped it and added the
typed `threshold` / `direction` / `watch_margin` / `tiers` / `handler` fields.
Across **four** verticals (N=4) each `Step` now also carries a **5-facet
annotation** — `input · decision-condition · llm-assist · output · governance` —
but **only as YAML comments**, because `services/engine/procedures/spec.py`
declares `Step` with `ConfigDict(extra="forbid")`, which rejects any real
`facet:` key (PLAN-0037 SD-4 / L-1). The archetype catalog
(`docs/conventions/procedure-archetypes.md`, Step B) names the recurring shapes
(AT-1 / AT-1b / AT-2 / AT-3) those facets reveal. **Rule-of-Three is satisfied**
(N=4 consistently-instrumented examples; ADR-006) — the schema is extracted
**now**, not prematurely.

This amendment promotes `facet:` from a comment to a **first-class, typed,
validated, optional `Step` field** — engine-*readable* (machine-readable for the
Stage-3 generator and a future config / monitor UI), while engine-*consumption*
stays deferred (Scope boundary below).

#### Decision (D2-A1 … D2-A4)

**D2-A1 — Add an optional typed `facet:` sub-model to `Step`; KEEP `extra="forbid"`.**
`facet` becomes a KNOWN key; unknown keys are still rejected — the safety that
`extra="forbid"` provides is preserved (this is **not** merely dropping it).
`facet` is **optional**: absent `facet` = today's behaviour byte-for-byte (every
shipped procedure still loads — backward-compatible, cf. PLAN-0022 AC-9).

**D2-A2 — `facet` is descriptive metadata, NOT a second source of truth (the
*Hybrid* shape).** The `Step` model already types most of what the five facets
describe — `input` (`StepInput`), `output`, the in-file band
(`threshold`/`direction`/`watch_margin`), the gate
(`autonomy`/`handler`/`on_failure`/`tiers`). To avoid storing the same fact
twice (a drift hazard on a public determinism-first repo), `facet` carries:

- the **net-new machine-readable** signal as **typed** sub-fields:
  `decision_condition` (D2-A3) and `llm_assist` (what, if anything, the LLM
  drafts / summarises — advisory only; not modelled anywhere today);
- the three already-typed facets (`input` / `output` / `governance`) as
  **optional, explicitly NON-authoritative human notes** (`str`). The typed
  `Step` fields remain the source of truth; the notes preserve the uniform
  "5-facet" reading of the catalog without re-owning structured values.

**D2-A3 — `decision_condition` is a discriminated shape (the env-vs-in-file split
is *modelled*, not papered over).** The N=4 substrate authors a step's
deterministic decision **six** distinct ways; `decision_condition.gate_kind`
enumerates exactly those — **no speculative future kinds** (Rule-of-Three):

| `gate_kind` | N=4 instance(s) | carries |
|---|---|---|
| `env_band` | `energy.judge`, `supply_chain.judge` | `band_source: env` + `env_var` (e.g. `OCT_RECOMMEND_THRESHOLD`) |
| `in_file_band` | `aquaculture.judge`, `procurement.judge` / `judge_stock` | `band_source: in_file` → the existing typed `threshold`/`direction`/`watch_margin` (NOT re-stored) |
| `rule_gate` | `procurement.compliance` (per-criterion AVL · tax · cert · sanctions · single-source) | — |
| `scored_rule` | `procurement.source` (supplier selection = a scored rule, never the LLM) | — |
| `doa_tier` | `procurement.approve` (tiered ฿ delegation-of-authority) | — |
| `none` | reads / summary / audit terminals (no decision) | — |

`band_source` (`env` \| `in_file`) is present **iff** `gate_kind ∈ {env_band,
in_file_band}`; `env_var` only with `band_source = env`. For `in_file_band` the
facet **points at** the already-typed band fields rather than copying their
values — so the numeric truth lives in exactly one place. (`scored_rule` is the
case the original dispatch's sketch omitted — it is the **governed ≠ generated**
selection gate of AT-2 and must be first-class.)

**D2-A4 — Schema only; no engine consumption; no codegen touched.** v0 makes
`facet` a validated, engine-readable field. The Stage-3 generator that
*consumes* facets stays deferred (Rule-of-Three; Out-of-scope below).
`procedures.yaml` is **engine-read** (`load_procedures`), **not** codegen-emitted
like the ADR-008 ontology — so the ADR-008 D5/D6 generator and its validators are
**untouched**; the only code edit is the `Step` model in `spec.py`.

#### `spec.py` Step-model delta (illustrative — PLAN owns the literal edit)

```python
class BandSource(StrEnum):
    ENV = "env"
    IN_FILE = "in_file"

class GateKind(StrEnum):                  # EXACTLY the N=4 observed kinds (no speculation)
    ENV_BAND = "env_band"
    IN_FILE_BAND = "in_file_band"
    RULE_GATE = "rule_gate"
    SCORED_RULE = "scored_rule"
    DOA_TIER = "doa_tier"
    NONE = "none"

class DecisionCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gate_kind: GateKind
    band_source: BandSource | None = None  # present iff gate_kind ∈ {env_band, in_file_band}
    env_var: str | None = None             # only with band_source == env
    note: str | None = None                # optional human prose
    # @model_validator: band_source ⇔ band gate_kinds; env_var only when band_source == env

class StepFacet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_condition: DecisionCondition | None = None
    llm_assist: str | None = None          # NET-NEW: advisory LLM draft/summary, or None
    # non-authoritative notes — the typed Step fields remain source of truth (D2-A2):
    input: str | None = None
    output: str | None = None
    governance: str | None = None

class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")    # UNCHANGED — facet is now a KNOWN key
    ...
    facet: StepFacet | None = Field(
        default=None,
        description="descriptive 5-facet metadata; optional; non-authoritative for runtime (D2-A2)",
    )
```

YAML (the four verticals' comment facets become migratable to this — a
**follow-on PLAN**, not this amendment):

```yaml
# energy.judge — ENV-authored band (no in-file threshold field)
- step_id: judge
  kind: evaluate
  facet:
    decision_condition: { gate_kind: env_band, band_source: env, env_var: OCT_RECOMMEND_THRESHOLD }
    llm_assist: null
    governance: "verdict = pure function of the reading + the authored (env) band"
# aquaculture.judge — IN-FILE band: facet POINTS AT the typed fields, never re-stores the values
- step_id: judge
  kind: evaluate
  threshold: 4.0
  direction: below
  watch_margin: 1.0
  facet:
    decision_condition: { gate_kind: in_file_band, band_source: in_file }
    llm_assist: null
```

**Naming:** YAML keys use `decision_condition` / `llm_assist` (underscore —
Python-attribute-faithful), not the hyphenated comment form
(`decision-condition`); the loader needs no alias.

#### Alternatives considered (amendment-scope)

- **Keep facets comment-only forever** — rejected: not engine-readable; cannot
  feed the Stage-3 generator or a config UI.
- **Drop `extra="forbid"` wholesale** — rejected: re-opens the unvalidated-key
  hole the constraint exists to close; a typed optional field keeps the safety.
- **Full denormalised 5-string facet** (re-state every typed field) — rejected:
  stores `threshold`/`input`/`output`/etc. twice → a drift hazard. The Hybrid
  shape (D2-A2) keeps one source of truth.
- **Free-form `dict[str, Any]` facet** — rejected: unvalidated; the same hole as
  dropping `extra`.
- **A new standalone ADR** — rejected per Cray: `facet` directly extends the D2
  `Step` grammar, so it belongs as an ADR-016 amendment (the D3 Amendment /
  ADR-0019 in-place precedent).
- **Cross-validate `facet.decision_condition` against the typed band fields**
  (e.g. require `threshold` when `gate_kind = in_file_band`) — **deferred, not
  adopted in v0** (keeps the amendment tight and `facet` non-authoritative; see
  OQ-A2).

#### Consequences

- `Step` gains a typed optional `facet` sub-model; `spec.py` is edited so `facet`
  is a **known** field (typed, NOT `extra="allow"`). Backward-compatible (absent
  = unchanged; cf. AC-9).
- This is the **first deliberate engine edit on the procedures path** since the
  procurement vertical held literal zero-engine-edit — which is exactly why it is
  an **ADR amendment**, not a config change. (The edit itself is the follow-on
  PLAN's; this amendment fixes only the schema.)
- **No drift by construction** for the overlapping facets — `in_file_band` points
  at the typed band; `input` / `output` / `governance` notes are stamped
  non-authoritative.
- The four verticals' comment-only facets become **migratable** to the real field
  — a **follow-on PLAN** (gated on this amendment `Accepted`), not this amendment.
- `facet` + the archetype catalog become the substrate for **Stage 3** (the
  generator) and a future config / monitor UI (D7 Phase 3).
- **No `procedures.yaml` codegen / ADR-008 generator change** — the only code
  touched is `spec.py` (D2-A4).

#### Scope boundary (amendment — keep it tight)

- **IN:** the `facet` **schema** — shape, typing, the env-vs-in-file
  `decision_condition` modelling. Nothing else.
- **OUT:** the `spec.py` edit + the four-vertical comment→field migration
  (follow-on PLAN, gated on `Accepted`); the Stage-3 generator; any runtime
  consumption of facets; any change to `kind` / `autonomy` / `input` /
  `threshold` / gates (all unchanged).

#### Open Questions (amendment)

- **OQ-A1 (catalog growth).** When a 5th vertical lands a decision shape outside
  the six `gate_kind`s, extend the enum (optional field → additive,
  backward-compatible). Do not force-fit (catalog discipline).
- **OQ-A2 (facet↔typed integrity).** Should a later phase cross-validate
  `facet.decision_condition` against the typed band (`in_file_band` ⇒ `threshold`
  set) or against `kind`? Deferred — v0 keeps `facet` non-authoritative; Stage-3
  may promote select integrity checks.
- **OQ-A3 (`llm_assist` structure).** `llm_assist` is free prose in v0. Does the
  Stage-3 generator want it typed (e.g. `{role: draft|summarise, of: <field>}`)?
  Deferred until the generator's needs are concrete.

#### Amendment references

- `docs/conventions/procedure-archetypes.md` — the N=4 archetype catalog (AT-1 /
  1b / 2 / 3) + the band-authoring split table (load-bearing here).
- `docs/plans/done/0037-stage2-facet-retrofit-archetype-catalog.md` — the PREP
  that produced the N=4 5-facet instrumentation + catalog (L-5 env-vs-in-file
  honesty is the input to this amendment).
- `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml` — the
  comment-only 5-facet substrate this field formalizes.
- `services/engine/procedures/spec.py` — the `Step` model
  (`ConfigDict(extra="forbid")`; the typed `threshold`/`direction`/`watch_margin`/
  `tiers`/`handler` fields the Hybrid shape points at).
- ADR-0019 / the D3 Amendment (2026-06-11) — the in-place amendment precedent +
  the determinism invariant (routing on the deterministic verdict, never LLM
  `confidence`; ADR-010 IN-3).
- ADR-008 (D5/D6) — the ontology codegen path that is **untouched**
  (`procedures.yaml` is engine-read).
- ADR-006 (Rule-of-Three) — N=4 justifies extracting the schema now.
- Memory: `project-vero-ultimate-target-generative-procedures` (the
  generate → run → monitor arc).

### D2 + D3 Amendment (2026-07-01): typed read-side ontology object-binding for query steps (Q3)

> **Status:** **Accepted** (Cray-ratified 2026-07-01, session 93). **Date:** 2026-07-01.
> **Deciders:** Jirachai Thiemsert (founder). **Amends:** D2 (the
> `Step` / `StepInput` grammar) **and** D3 (the `Agent.allowed` blast-radius
> allowlist) — **extends, does not reverse or renumber**; mirrors the **D2
> Amendment (2026-06-25)** typed-`facet:` in-place precedent and the **D3
> Amendment (2026-06-11) / ADR-0019** extends-not-reverses precedent. This is a
> **Q3-only** amendment (Rock 3 / O-2).
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray (the
> s84 design direction "bind query steps to ontology objects; the mapping layer
> absorbs source diversity" + the Rock 3 / O-2 gap flag). Drafter = the
> in-harness `plan-drafter` subagent (ADR-013 D2 authoring path / ADR-009 D1
> interim authoring). Independent reviewer = Cowork Tier-1b second-perspective
> review (session 93) + Code R2-verification (all claims checked on disk) + Cray
> ratification (Proposed → Accepted, session 93). Drafter ≠ ratifier —
> separation **intact** (three independent lenses).

#### Context for the amendment

D2/D3 gave the write side of the procedure engine real governance: an `action`
step is `gated` by default (D3), its blast radius is bounded at pre-flight by
`Agent.allowed.action_handlers` (`validate_runnable` refuses to RUN a procedure
whose action step names a non-allowlisted handler; its runtime force is
declared==dispatched), and the `RecommendedAction`
it produces routes through the approve→execute gate (ADR-007). **The mirror-image
READ side has no equivalent seam.** Two gaps, both verified against the shipped
code:

**Gap (A) — a query Step has no typed object-type binding.** `StepInput`
(`services/engine/procedures/spec.py:110-132`) carries **only** `from_step`
(alias `from`) + `where`, under `ConfigDict(extra="forbid")`. The orchestrator's
`_resolve_input` (`orchestrator.py:310-330`) resolves a step's input **only** from
the prior-step output bag (by `from_step`, else the immediately-prior step); the
**first** step gets an empty base `[]` and never touches the adapter. So
`from_step` is an **intra-run** threading path, not a data entry point. Every
vertical names its query object **in prose only** — the `description` string plus
the **non-authoritative** free-text `facet.input`. Consequence: **no shipped query
executor exists in the engine** — each vertical hand-writes a seed executor that
calls `adapter.fetch_objects` manually (e.g. procurement's `_SeedQuery` /
`_intake_seed` in `verticals/procurement/hero_demo/run.py`, which calls
`adapter.fetch_objects("OperationalEvent")` / `("PurchaseOrder")` / `("Quotation")`
directly).

**Gap (B) — the `Agent` has no read-side blast-radius bound.** `AgentAllowed`
(`spec.py:589-597`) = `{step_kinds, action_handlers}`. `action_handlers` bounds
the **write** side and **is pre-flight-checked** (in `validate_runnable`; its
runtime force is declared==dispatched — see the Enforcement-status frame below).
There is **no `object_types`
field** → an agent's read reach is **unbounded**. And there is **zero read-side
access control anywhere**: the `DataAdapter` protocol (`data_adapter.py:24-69`)
assumes the caller is authorized — `fetch_objects(object_type)` /
`fetch_links(link_type)` / `stream_events(event_type)` all take object-type names
but **gate nothing**.

**The binding seam already exists at the adapter.** `ObjectTypeMeta`
(`ontology_meta.py:42-55`) is the typed object registry
(`name`/`primary_key`/`title_key`/`properties`/`quantity_bindings`), sourced from
`verticals/<v>/ontology/<v>_v0.yaml` (`ontology_meta.ontology_path`) via codegen.
The `DataAdapter` **already speaks object-type names** — the read entry point is
just **untyped and unbounded in the procedure spec**. Cray's s84 direction is to
**bind query steps to ontology objects** (the mapping layer absorbs source
diversity); this is **not** connectors-in-the-procedure.

**Three ambiguities the Explore pass flagged (defined here so the Decision is
unambiguous):**

1. **"data source" is overloaded.** *Input-**binding*** = which prior step's
   output set feeds this step (today's `StepInput.from_step`; an **intra-run**
   thread). *Data-**sourcing*** = the executor's job of **fetching the initial /
   external object set** for a query step that has no prior step to thread from.
   **Q3 is about typing the read *entry point* (data-sourcing) as an ontology
   object** — it does **not** change or replace `from_step` (input-binding stays
   as-is).
2. **Adapter binding is implicit today.** The vertical is passed as a **string to
   `run_procedure`** (the seed executor closes over that adapter); the adapter is
   **not named in the procedure spec**. This amendment does not change how the
   adapter is selected — it types **what object** a query step reads through it.
3. **No shipped query executor.** That each vertical supplies a seed/query
   executor is today an **undocumented operational expectation**, not an engine
   contract.

**Rule-of-Three (N=4 — pattern amply extracted per ADR-006; extract now, not
prematurely).** Every vertical's first query step already names its object in
prose:

| vertical | query step | object bound (prose today) |
|---|---|---|
| aquaculture | `read_do` | "per active **Pond**" |
| supply_chain | `read_temps` | "per in-transit **Shipment**" |
| energy | `read_readings` | "per active **Asset**" |
| procurement | `read_stock` / `intake` | "per stocked **Part**" / failure "**work-order(s)**" → PR |

#### Decision (D2/D3-Q1 … Q4)

The read side gets a **typed read contract + a load-time consistency & scoping
gate** (`reads ∈ ontology ∩ Agent.allowed.object_types`, else refuse load),
delivered **contract-first**: type the binding + add the allowlist + **gate at
LOAD time** now (low-risk, no runtime data-flow change), and **defer** the generic
run-consume executor to a fast-follow PLAN.

**Enforcement status (honest frame).** declared ✔ · consistency-gated at load ✔ ·
execution-bound ✖ (deferred to the Q4 generic executor, which makes `reads` the
executed read as `step.handler` is the executed handler today). The write-side
`action_handlers` is itself only pre-flight-checked in `validate_runnable`
(`orchestrator.py:173`; a whole-`services/` grep finds enforcement **only** there
— no per-step runtime re-check); its runtime force derives from
**declared==dispatched** (the executor dispatches EXACTLY `step.handler`) — the
property the read side gains only at Q4. So v1 closes Gap (B) **as a load-time
bound** (true), but it is **not** runtime-enforced parity yet.

**Q1 — Add a typed object-type binding to a query Step's read entry point.**
Introduce a **known** sub-field naming the ontology object a query step reads
(working name `reads` / `object_type`), **keeping `ConfigDict(extra="forbid")`
intact** — the binding becomes a typed key, unknown keys stay rejected. It is
**distinct from** and **additive to** `from_step` (the intra-run thread stays for
threading; `reads` names the data-sourcing entry point). It is **not** carried on
the non-authoritative `facet.input` (that stays a prose note per the 2026-06-25
D2-A2 Hybrid rule — the typed binding is the source of truth). **Exact placement
is surfaced as OQ-1** (recommendation: a `StepInput` sub-field, so the read entry
point sits beside the existing `from`/`where` input grammar).

**Q2 — Add `Agent.allowed.object_types: list[str]` mirroring `action_handlers`.**
This is the read-side counterpart to the write-side handler allowlist — it
**bounds an agent's read blast radius**, closing Gap (B). Shape and default mirror
`action_handlers` exactly (`list[str]`, `default_factory=list`), under the
existing `AgentAllowed(extra="forbid")`.

**Q3 — Enforce at LOAD / validation time (a real read-gate, symmetric with the
write-side handler bound).** A query step's named object_type MUST **(a)** exist
in the vertical's ontology (present in `ObjectTypeMeta` for that vertical) **AND
(b)** be in the running `Agent.allowed.object_types` — else the engine **refuses
to load the procedure** (mirroring how an un-allowlisted `action_handler` is
refused). Enforcement is at **load / pre-flight** (alongside
`validate_runnable`), so it touches **no runtime data flow** — the hero-demo and
live paths are **unaffected** (they keep their hand-written seeds until the
executor lands). This is the low-risk half that delivers read-side governance
**now**.

**Q4 — Defer the generic query executor to a fast-follow build PLAN.** The
executor that resolves a query step's `object_type` → `adapter.fetch_objects` →
typed entities (retiring the hand-written per-vertical seeds) is **deferred**
because it **touches the runtime data flow the hero-demo / live path depends on**,
and because some query steps **enrich / join** rather than do a plain fetch (e.g.
procurement's `intake` reads the failure **work-order** and assembles an enriched
**PurchaseRequisition** set, joining across `OperationalEvent` / `PurchaseOrder` /
`Quotation`). The typed contract (Q1–Q3) must **prove out first**; the executor is
a separate PLAN once the contract is `Accepted`.

**Rationale (capture).** Contract-first: type the binding + add the allowlist to
get a read-side **load-time bound** at low risk now (author + validate +
load-gate), and **consume later** (the run-consume executor is a fast-follow). The
`object_types` allowlist is also the **foundation for future read-side audit /
PDPA** (PLAN-0005 §8.1) — an agent's declared read reach becomes an auditable,
load-gated fact rather than an implicit adapter capability.

#### `spec.py` delta (illustrative — the follow-on PLAN owns the literal edit)

```python
# Q1 — the read entry point on StepInput (OQ-1 recommendation; extra="forbid" kept):
class StepInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_step: str | None = Field(default=None, alias="from")  # UNCHANGED — intra-run thread
    where: dict[str, Any] | None = None                        # UNCHANGED — post-fetch filter (OQ-4)
    reads: list[str] | None = Field(                           # NET-NEW — data-sourcing entry point (OQ-5: list, not str)
        default=None,
        description="ontology object_types this query step reads (each must exist in the vertical's "
        "ObjectTypeMeta AND be in Agent.allowed.object_types) — ADR-016 Q3",
    )

# Q2 — the read-side allowlist mirroring action_handlers:
class AgentAllowed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_kinds: list[StepKind] = Field(default_factory=list)
    action_handlers: list[str] = Field(default_factory=list)   # UNCHANGED — write bound
    object_types: list[str] = Field(                           # NET-NEW — read bound (Q2)
        default_factory=list, description="ontology object_types this agent may read (Q3 load-gate)"
    )
```

Load-gate (Q3), at pre-flight beside `validate_runnable` — **no runtime data-flow
change**: for each `kind == query` step with `input.reads` set, iterate each
element (`each ∈ vertical_object_types` **and** `each ∈ agent.allowed.object_types`),
else refuse to load.

> **Implementation note (build-PLAN concern, not an OQ).** "Beside
> `validate_runnable`" is **not drop-in**: `validate_runnable(procedure, agent)`
> (`orchestrator.py:126`) today receives **only** procedure + agent, **not** the
> object-type registry. The load-gate must thread the vertical's `OntologyMeta`
> into pre-flight so it can assert `reads ∈ ontology`. This is wiring the
> build-PLAN owns — the ADR decides the gate; it does not pretend the signature
> already carries the registry.

#### Scope boundary (amendment — keep it tight)

- **IN:** the **typed read-side binding** (Q1) + the **`object_types` allowlist**
  (Q2) + the **load-time enforcement** (Q3). Read-side load-time bound, contract
  only.
- **OUT — the generic run-consume query executor** (Q4): a **fast-follow build
  PLAN**, gated on this amendment `Accepted`. It touches runtime data flow and the
  enrich/join query steps; the contract proves out first.
- **OUT — the Box-4 economic-impact facet (฿ dimension), EXPLICITLY DEFERRED as a
  self-cancelling deferral.** It is gated on **N ≥ 3 verticals actually carrying
  the ฿ dimension** (today **N = 1** — Fastenal / procurement only). Mirroring the
  **ADR-0025 D7 / ADR-0026 OQ-6** enforceable-re-trigger precedent: a CI / test
  marker (an `xfail`-style assertion) counts verticals carrying the economic
  dimension across `verticals/*/`, and **fails / flags** when the **2nd then 3rd**
  vertical crosses the threshold — so the deferral **cannot silently erode** under
  delivery pressure (governance R5). The economic facet is **not designed here**;
  the marker is the self-cancelling trigger to re-open it at N ≥ 3. **Only the
  *typed* facet is deferred:** the economic dimension is already captured as
  **non-authoritative prose at vertical authoring** (Cray s84) — do **not** read
  "defer the type" as "drop the dimension." The self-cancelling N ≥ 3 marker
  guards the *typed* facet only.
- **OUT:** connectors-in-the-procedure (LOCKED — the mapping layer absorbs source
  diversity, Cray s84); any change to how the adapter is selected
  (`run_procedure`'s vertical string, ambiguity #2); any change to `from_step`
  input-binding, `kind`, `autonomy`, gates, or the D2 `facet` schema (all
  unchanged).

#### Open Questions — RESOLVED (Cray-ratified 2026-07-01, session 93)

- **OQ-1 (field placement).** `StepInput.reads` sub-field **(recommended** — the
  read entry point sits beside the existing `from`/`where` input grammar; one
  cohesive input model) **vs** a top-level `Step.reads`. Both keep
  `extra="forbid"`; the difference is where the read binding conceptually lives.
  **→ RATIFIED: field placement = `StepInput.reads`** (the read entry point sits
  beside the existing `from`/`where` input grammar).
- **OQ-2 (v1 depth).** author + validate + **load-gate (recommended** — real
  read-side governance now, zero runtime-data-flow risk) **vs** full run-consume
  (delivers the executor now but touches the hero-demo/live data flow and the
  enrich/join steps — higher risk, defeats contract-first) **vs**
  validate-only-no-enforce (types the binding but adds **no** actual read-gate —
  documents the gap without closing Gap (B)). The recommendation buys the
  read-side load-time bound at the lowest blast radius.
  **→ RATIFIED: v1 depth = load-gate** — but framed honestly as a typed read
  contract + a load-time consistency & scoping gate, **not** runtime-enforced
  parity (see the Enforcement-status frame in the Decision; execution-bound is
  deferred to the Q4 generic executor).
- **OQ-3 (allowlist verb scope).** Does `Agent.allowed.object_types` gate
  `stream_events` / `fetch_links` too, or only `fetch_objects`-style reads in v1?
  **Recommendation (v1): the query-step object binding only** (Q3).
  **→ RATIFIED: `object_types` bounds `fetch_objects`-style object reads ONLY in
  v1.** `fetch_links` (typed by **link** type) and `stream_events` (typed by
  **event** type) are a **category mismatch** — an `object_types` allowlist cannot
  meaningfully bound a link-type / event-type read — so they are **explicitly OUT
  of v1**, a **separate future bound** (their own typed allowlist, if/when needed,
  likely alongside the Q4 executor).
- **OQ-4 (`reads` ↔ `input.where`).** Is `where` still the **post-fetch**
  narrowing over the fetched object set? **Recommendation: yes** — `reads` names
  **what** to fetch (the object_type); `where` stays the **field-equality filter
  over the fetched set** (unchanged from `_matches` / `_resolve_input`), so the
  set-valued fan-out semantics are preserved.
  **→ RATIFIED: `where` stays the engine-side post-fetch field-equality filter**
  (confirmed; it is **NOT** pushed down to the adapter's separate `filter_expr`
  param — the engine keeps the narrowing).
- **OQ-5 (`reads` cardinality — NEW, ratified).** Is `reads` a single `str` or a
  list? **→ RATIFIED: `reads` is `list[str] | None`, NOT a single `str`.**
  Rationale: procurement `intake` (`verticals/procurement/hero_demo/run.py::_intake_seed`,
  `run.py:186-195`) reads **three** object types (`OperationalEvent` +
  `PurchaseOrder` + `Quotation`) and joins them — a single `str` cannot declare
  that; and a later `str`→`list` widening would be a **breaking** schema change to
  a governance field under `extra="forbid"`. The load-gate iterates each element
  (`each ∈ ontology ∩ Agent.allowed.object_types`). v1 enforcement may still wire
  only the single-object executor path (the multi-read join lands with Q4).
- **OQ-6 (`object_types` empty-list semantics — NEW, ratified).** What does an
  empty `object_types` mean? **→ RATIFIED: empty list = UNCONSTRAINED in v1**
  (backward-compatible, opt-in) — so existing verticals/agents (**none** declare
  `object_types` today) keep loading, and the read-gate only bites when an agent
  **opts in**. **Documented sibling inconsistency (surfaced, NOT fixed here):**
  `step_kinds` empty = **unconstrained** (`orchestrator.py:161` — `if allowed_kinds
  and …`) vs `action_handlers` empty = **fail-closed** (`orchestrator.py:173` —
  any non-None handler "not in `[]`" raises). v1 makes `object_types` follow the
  **`step_kinds` (empty=unconstrained)** convention; the sibling divergence is
  **out of scope** — do **not** "fix" the siblings now, just note it.
- **OQ-A (governance ownership of the new fields — NEW, ratified).** Are `reads`
  and `object_types` human-governed (H) fields? **→ RATIFIED: both are
  HUMAN-GOVERNED (H).** Verified on disk: `object_types` is **already auto-covered**
  because it lives inside `Agent.allowed`, and `allowed` is in
  `AGENT_GOVERNANCE_FIELDS` (`services/engine/procedures/draft.py:65`). `reads` is
  **NOT yet covered** — `input` is not in `STEP_GOVERNANCE_FIELDS`
  (`draft.py:42-53`) — so the build must **ADD `reads` to `STEP_GOVERNANCE_FIELDS`**
  + the draft-disjointness CI (PLAN-0042 Step 1 D4 / ADR-0024 D3 H-only machinery).
  The ADR **decides** they are H-governed; the **wiring is a build-PLAN task**.

#### Consequences

- `StepInput` gains a typed optional **read entry point** (Q1) and `AgentAllowed`
  gains a typed **read allowlist** (Q2); both keep `extra="forbid"`.
  **Backward-compatible**: a query step without `reads` and an agent without
  `object_types` load exactly as today (every shipped procedure + hero-demo still
  loads — the load-gate only fires when `reads` is set).
- The read side gains a **typed read contract + a load-time consistency &
  scoping gate**: an agent's read reach becomes a **declared, consistency-gated,
  auditable** fact — Gap (B) closed **as a load-time bound**. Enforcement status:
  declared ✔ · consistency-gated at load ✔ · execution-bound ✖ (the executed-read
  property arrives with the Q4 generic executor, as `step.handler` is the
  executed handler today). This is **not** runtime-enforced parity yet — even the
  write-side `action_handlers` is only pre-flight-checked in `validate_runnable`
  (`orchestrator.py:173`); its runtime teeth come from declared==dispatched.
- **No runtime data-flow change** — `_resolve_input` and the hand-written seed
  executors are untouched; the hero-demo and live paths are unaffected. The
  generic executor (Q4) that retires the seeds is a **fast-follow PLAN**.
- The `object_types` allowlist becomes the **foundation for read-side audit /
  PDPA** (PLAN-0005 §8.1) — the first typed read-access surface in the engine.
- The Box-4 **economic facet stays out**, guarded by an **enforceable
  self-cancelling N ≥ 3 re-trigger** (ADR-0025 D7 precedent) so the deferral is
  auditable, not a comment that erodes.

#### Amendment references

- `services/engine/procedures/spec.py` — `StepInput` (`:110-132`, the
  `from`/`where` grammar + `extra="forbid"`), `AgentAllowed` (`:589-597`,
  `step_kinds`/`action_handlers`), `Agent` (`:641-654`).
- `services/engine/procedures/orchestrator.py` — `_resolve_input` (`:310-330`,
  the intra-run threading that never touches the adapter) + `run_procedure`.
- `services/engine/data_adapter.py` — the `DataAdapter` protocol (`:24-69`;
  `fetch_objects`/`fetch_links`/`stream_events` take object-type names but gate
  nothing).
- `services/engine/ontology_meta.py` — `ObjectTypeMeta` (`:42-55`) + `ontology_path`
  (`:77-79`), the typed object registry the load-gate validates against.
- `verticals/{aquaculture,supply_chain,energy,procurement}/procedures.yaml` — the
  N=4 query steps that name their object in prose only (`read_do` / `read_temps` /
  `read_readings` / `read_stock` / `intake`).
- `verticals/procurement/hero_demo/run.py` — `_SeedQuery` / `_intake_seed`, the
  hand-written seed executor (the enrich/join case that keeps Q4 deferred).
- ADR-016 D2 Amendment (2026-06-25) — the typed-`facet:` in-place precedent (and
  D2-A2: `facet.input` stays a non-authoritative prose note, so the typed `reads`
  is the source of truth).
- ADR-016 D3 Amendment (2026-06-11) / ADR-0019 — the extends-not-reverses in-place
  precedent.
- ADR-0025 D7 / ADR-0026 OQ-6 — the enforceable self-cancelling Rule-of-Three
  re-trigger precedent (mirrored for the deferred economic facet, N ≥ 3).
- ADR-006 (Rule-of-Three) — N=4 justifies extracting the read-binding schema now.
- ADR-007 D1 (the `DataAdapter` contract) / ADR-008 (the ontology the object_type
  names resolve against, untouched).
- PLAN-0005 §8.1 — the read-side audit / PDPA surface the `object_types` allowlist
  seeds.

### D2 + D3 Amendment (2026-07-05): typed service-principal for non-human triggers

> **Status:** **Accepted** (Cray-ratified, Proposed → Accepted, 2026-07-05 /
> session 102). **Date:** 2026-07-05 (session 101 drafted; session 102 ratified).
> **Deciders:** Jirachai Thiemsert (founder).
> **Amends:** D2 (the `Agent` / principal grammar) **and** D3 (the autonomy +
> `Agent.allowed` blast-radius model) — **extends, does not reverse or
> renumber**; mirrors the **D2 Amendment (2026-06-25)** typed-`facet:` and the
> **D2 + D3 Amendment (2026-07-01)** read-binding in-place precedents.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray
> (session 101 — ratified the PLAN-0052 **S2** direction as-recommended: a typed
> service-principal, requester-never-approver, and the accompanying
> security-IAM / PDPA panel review). Drafter = the in-harness `plan-drafter`
> subagent (ADR-013 D1 phased authoring / ADR-009 D1 interim authoring).
> Independent reviewers = the session-101 **security-IAM / PDPA-DPO panel lens**
> (advisory, `explore-research` read-only review) + **Code R2** (verifies every
> cited `file:line` on disk against fresh evidence and commits per ADR-009 D2) +
> **Cray** at ratification (Proposed → Accepted, landed 2026-07-05 / session
> 102). Drafter ≠ ratifier and no reviewer originated the direction — separation
> **intact**.

#### Context for the amendment

D7 Phase 3 forward-declares a `schedule` (non-human) trigger. Today **every** run
is human-triggered, and the `run_started` audit row coalesces the actor to
`principal.person_id → trigger_context["triggered_by"] → None`
(`services/engine/procedures/persistence.py:132-140`). A non-human run therefore
resolves `actor_person_id = None` — a **PDPA accountability gap**: a consequential
write with no attributable actor. The engine also **hard-blocks** `schedule`
today (`orchestrator.py:138-142` raises `ProcedureError` for any non-`manual`
trigger), so this is **forward-looking** — but the **actor model must be DECIDED
before the S1 scheduler is built** (**S2 before S1**): a scheduler shipped first
would null the audit actor on the exact runs it creates.

This amendment fixes the **actor model** — the *decision*. It does **not** build
the scheduler (S1) or the service-principal machinery (a follow-on build-PLAN,
gated on this Accepted). Grounding: **PLAN-0052** (ADR-016 Phase-3 monitor)
Surfaced-Decision **S2** carries the full folded analysis + invariants M1–M7 +
RF-1..3, produced by the session-101 security-IAM / PDPA panel lens.

The shipped code the decision binds against (all Code R2-verified on disk):

- `services/engine/procedures/spec.py` — `Person` (`:638-657`, the human
  principal SoD compares by `person_id`), `Agent` (`:660-673`) +
  `AgentAllowed` (`:606-616`, `{step_kinds, action_handlers, object_types}`).
- `services/engine/procedures/action_step.py` — `_enforce_principal_sod`
  (`:299`) + `resolve_gated_step` (`:408`) fail-closed on the approver check;
  the audit `actor_kind:"engine"` convention (`:292`).
- `services/engine/procedures/persistence.py:132-140` — the actor-coalesce that
  falls to `None`.
- `services/api/auth.py:71-72` — `api_auth_enabled=false → AuthContext(None,
  None)` (the toggle that makes a plain `gated` approver check inert).
- `services/db/audit_log.py` — the tamper-evident hash-chain that gives the
  trail integrity (the actor field this amendment guarantees is resolvable).

#### Decision (SP-1 … SP-8 — direction LOCKED; only the shape choices below are OQs)

The `schedule` trigger changes only **who fired** a run, never **who approves** a
`gated` write. The actor model gains a **typed service-principal** — a non-human
requester/actor with a stable id + declared scope, bound to the Agent — recorded
as a **never-null** audit actor and classified by `actor_kind`. **No new scope
primitive**; least-privilege reuses the Agent's existing allowlists.

**SP-1 — Requester-only, NEVER approver (the core invariant — preserve
verbatim).** A service-principal is a **requester/actor ONLY, NEVER an
approver**. A `schedule` trigger changes only *who fired* a run, never *who
approves* a `gated` write (still a human at `waiting_human`). Letting a
service-principal satisfy the approver role silently converts `gated`→`auto` and
voids D3 + the fail-safe posture. Grounds: `resolve_gated_step` /
`_enforce_principal_sod` fail-closed (`action_step.py:299,408`).

**SP-2 — Typed identity, bound to the Agent, mirroring `Person` (NOT overloading
it).** A service-principal is a typed identity declared in a **vertical-level
`service_principals:` registry** in the procedures spec (top-level, **beside**
`principals:` / `agents:`) and **bound to the Agent** by reference — the Agent
(the machine actor that RUNS a procedure) references the principal by id, and its
blast radius is that Agent's `allowed.{action_handlers, object_types}` at runtime
(SP-6). It mirrors `Person`'s shape (stable id + declared scope, human-authored /
H-governed). It is a **distinct actor kind** — do **NOT** overload `Person`: SoD
compares `person_id`s, and a service id leaking into that comparison set could
collapse a constraint (RF-3). Keep the namespaces typed-distinct. *(Placement
refined per OQ-1 RATIFIED = vertical-level registry, 2026-07-05 / session 102 —
declared top-level, bound-to-Agent by reference + runtime scope; SP-2's intent
and the RF-3 namespace-distinctness invariant are preserved.)*

**SP-3 — `actor_kind` classifies the actor (`human` vs `service`).** Extend the
existing audit `actor_kind:"engine"` convention (`action_step.py:292`) with
`"service"` vs `"human"` so the trail is **filterable by actor class** — the
highest-leverage PDPA-legibility fix.

**SP-4 — Never-null actor (M2).** Replace the `None` fallback
(`persistence.py:132-140`): a scheduled run resolves the declared service id,
**never** `None`. This is the highest-leverage PDPA fix — every consequential
write carries a resolvable declared actor.

**SP-5 — On-behalf-of chain (M4).** `trigger_context` records **BOTH** the
service-principal (who fired) **AND** the owning human (who scheduled / owns it),
if any — so accountability preserves the human-in-the-loop lineage even for an
automated fire.

**SP-6 — Least-privilege by reuse; no auth material on the identity (M5 / M6).**
The service-principal inherits its Agent's blast radius via the **EXISTING**
`Agent.allowed.{action_handlers, object_types}` (`spec.py:606-616`) — **no new
scope primitive**. The identity is a **declared identity only** in the
local/on-prem model; the API-key transport (`auth.py`) is the **scheduler's**
concern (the trigger transport), kept **separate** from the principal identity.

**SP-7 — H-governed fields (M7).** The new fields are **H** (human-authored) —
add to `STEP_ / AGENT_GOVERNANCE_FIELDS` per the 2026-07-01 OQ-A precedent
(ADR-0024 D3 H-only machinery). A service-principal is never model-emitted.

**SP-8 — The security invariants to record (M1 + RF-1..3).**

- **M1 / RF-1 — reject a service/`None` principal for a `gated` step regardless
  of the authn toggle.** `auth.py:71-72` (`api_auth_enabled=false →
  AuthContext(None, None)`) makes a plain (non-SoD) `gated` step's approver check
  inert — a scheduler driving gate-resolve with authn off would **evaporate the
  human gate**. Gate-resolve MUST fail closed against a service/`None` principal
  **independent of** `api_auth_enabled`.
- **RF-2 — no autonomy elevation.** `auto` on a write stays a **deliberate
  per-step author choice**; a service-principal does **NOT** elevate any step's
  autonomy. A schedule trigger firing an all-`gated` procedure still parks every
  write at `waiting_human`.
- **RF-3 — keep service ids out of the `Person`/SoD comparison set** (the SP-2
  namespace-distinctness invariant, restated as a security property).

**DPO / PDPA framing.** The audit hash-chain (`audit_log.py`) already gives the
trail **integrity**; this amendment guarantees the **actor field is always a
resolvable declared identity** — a non-null, non-repudiable, typed actor on every
consequential write. Together: attributable **and** tamper-evident.

#### Scope boundary (amendment — this is a DECISION, not a build)

- **IN:** the **actor-model decision** — the typed service-principal shape
  (SP-2), `actor_kind` (SP-3), the never-null actor (SP-4), the on-behalf-of
  chain (SP-5), the least-privilege reuse (SP-6), the requester-never-approver
  invariant + RF-1..3 (SP-1, SP-8).
- **OUT — the build** (a follow-on build-PLAN, gated on this `Accepted`):
  implementing the service-principal type + the `actor_kind` field + the
  never-null wiring + the gate-resolve rejection invariant + tests.
- **OUT — the S1 scheduler** that CREATES service-triggered runs (its own
  ADR/PLAN — **S2 before S1**).
- **UNCHANGED:** the ADR-007 `RecommendedAction` envelope, the ADR-008 ontology,
  the `auto` / `gated` model, `autonomy_ceiling`, and the handler / object_type
  allowlists' **existing semantics** (the service-principal *reuses* them; it does
  not alter them).

#### Open Questions (amendment — Cray ratifies at Proposed → Accepted; do NOT silently resolve)

The **direction is LOCKED** (typed service-principal, requester-not-approver — not
an OQ). Only these genuinely-open *shape* choices are surfaced:

- **OQ-1 (identity-shape placement).** Where does the service-principal identity
  live — an **Agent-bound field** (recommended: the service-principal is declared
  on/beside the `Agent` it binds to, so its blast radius is the Agent's
  allowlists by construction — SP-6) **vs** a **vertical-level registry** (a
  top-level `service_principals:` list the `Agent` references by id) **vs**
  **referenced by the `schedule` trigger** (the trigger names the principal).
  *Recommendation:* Agent-bound (least-privilege falls out of SP-6 with no new
  wiring). *Why Cray's call:* it fixes the spec grammar's shape and the
  H-governance field home (SP-7), and the registry alternative is defensible if a
  principal must be shared across Agents.
  **RATIFIED (2026-07-05 / session 102) = vertical-level registry.** A top-level
  `service_principals:` list declared in the vertical's procedures spec (beside
  `principals:` / `agents:`), which an `Agent` references by id. Cray chose the
  registry over the *recommended* Agent-bound option **for the flexibility to
  share one service-principal across multiple Agents**. **SP-6 least-privilege
  holds intact:** the blast radius comes from the Agent that RUNS the procedure
  (`procedure.run_by`) at runtime — a registry-declared identity, once referenced
  by a running Agent, is still bounded by THAT Agent's `allowed.{action_handlers,
  object_types}`; the registry adds an indirection but opens **no scope hole**.
  The choice is **consistent with SP-2** ("declared beside Person/Agent, bound to
  the Agent") — it refines SP-2's placement (declared top-level; bound-to-Agent by
  reference + runtime scope), it does not contradict it (SP-2 wording reconciled
  minimally above; RF-3 namespace-distinctness preserved verbatim).
- **OQ-2 (`RunContext.principal` typing).** Does `RunContext.principal` widen to a
  union (`Person | ServicePrincipal`) **or** does the service actor ride a
  **separate field** (`RunContext.service_principal`, leaving `principal`
  human-only)? *Recommendation:* a **separate field** — it keeps `Person` (and the
  SoD comparison set) free of any service identity by construction (RF-3), rather
  than relying on every SoD call-site to discriminate a union. *Why Cray's call:*
  I did **not** fully trace the `RunContext` dataclass (`persistence.py` /
  `orchestrator.py` reference `RunContext.principal`); the union-vs-separate choice
  ripples through every principal call-site and is a build-shaping decision —
  flag for the build.
  **RATIFIED (2026-07-05 / session 102) = separate field (as INTENT / DIRECTION).**
  The service actor rides a **separate** `RunContext.service_principal` field;
  `RunContext.principal` stays **human-only**, keeping `Person` and the SoD
  comparison set free of any service identity **by construction** (RF-3). This
  ratifies the **DIRECTION**; the exact typing / mechanics are to be **CONFIRMED
  AT BUILD** after the S2 build-PLAN traces the `RunContext` dataclass (the ADR
  flags above that Code did not fully trace `RunContext`) — no fully-specified
  typing is claimed here.
- **OQ-3 (`actor_kind` field home).** Does `actor_kind` live on the **audit
  metadata only** (`action_step.py:292` convention, extended) **or also on the
  principal type** (the service-principal declares its own kind)? *Recommendation:*
  **audit metadata is the source of truth** for filtering the trail; the principal
  type's kind (if added) is derived/redundant — prefer audit-only unless the build
  finds a call-site that needs the kind before the audit row is written. *Why
  Cray's call:* it decides whether `actor_kind` is one field or two, and whether
  the principal type carries a discriminator.
  **RATIFIED (2026-07-05 / session 102) = audit-only.** `actor_kind` lives on the
  **audit metadata** — extend the existing `actor_kind:"engine"` convention
  (`action_step.py:292`) with `"human"` vs `"service"`. The principal type does
  **NOT** carry a redundant `kind` discriminator **UNLESS** the build finds a
  call-site that needs the kind **before** the audit row is written.

Any other genuinely-open shape choice surfaces the same way — but the
**DIRECTION** (typed service-principal, requester-not-approver) is **LOCKED**, not
an OQ.

#### Amendment references

- `services/engine/procedures/persistence.py:132-140` — the `run_started`
  actor-coalesce that falls to `None` (SP-4 replaces it).
- `services/engine/procedures/action_step.py` — `_enforce_principal_sod`
  (`:299`), `resolve_gated_step` (`:408`) fail-closed approver check (SP-1 / M1),
  and the `actor_kind:"engine"` audit convention (`:292`, extended by SP-3).
- `services/engine/procedures/spec.py` — `Person` (`:638-657`), `Agent`
  (`:660-673`), `AgentAllowed` (`:606-616`, the reused `action_handlers` /
  `object_types` allowlists — SP-6).
- `services/api/auth.py:71-72` — the `api_auth_enabled=false → AuthContext(None,
  None)` toggle that makes a plain `gated` approver check inert (RF-1).
- `services/db/audit_log.py` — the tamper-evident hash-chain (integrity; the DPO
  framing).
- `docs/plans/0052-adr016-phase3-oct-monitor.md` — Surfaced-Decision **S2** (the
  full folded analysis + M1–M7 + RF-1..3) and the **S2-before-S1** sequencing
  constraint; S1 (the scheduler) is the sibling surface gated on this amendment.
- ADR-016 D2 Amendment (2026-06-25) / D2 + D3 Amendment (2026-07-01) — the
  in-place, extends-not-reverses amendment precedents this one follows.
- ADR-016 D3 (autonomy model + `Agent.allowed` blast-radius) — the model this
  amendment extends without altering its existing semantics.
- ADR-0024 D3 — the H-only (human-authored) governance-field machinery
  (`STEP_ / AGENT_GOVERNANCE_FIELDS`) the new fields join (SP-7).
- PLAN-0005 §8.1 — the read-side audit / PDPA surface a resolvable declared
  actor serves.

### Amendment (2026-07-09): join/projection grammar for multi-read query steps (Q4)

> **Status:** **Accepted** (Cray-ratified, Proposed → Accepted, 2026-07-09 /
> session 115, via AskUserQuestion — OQ-1..OQ-4 all resolved as-recommended).
> **Date:** 2026-07-09. **Deciders:**
> Jirachai Thiemsert (founder). **Amends:** D2 (the `StepInput` read grammar) —
> **extends, does not reverse or renumber**; mirrors the **D2 Amendment
> (2026-06-25)** typed-`facet:`, the **D2 + D3 Amendment (2026-07-01)**
> read-binding (Q3), and the **D2 + D3 Amendment (2026-07-05)**
> service-principal in-place precedents. This renders the **deferred half of
> Q4**: the 2026-07-01 amendment's OQ-5 located the multi-read join here ("the
> multi-read join lands with Q4"), and PLAN-0048 — which shipped Q4's
> single-read half — explicitly walled the grammar off as "an ADR-016
> amendment, not a build call".
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray —
> the three grammar forks (SD-A Hybrid surface / SD-B two-shape v1 scope /
> SD-C co-exist + parity-guarded migration) were adjudicated by Cray in-session
> 2026-07-09 (session 115) via AskUserQuestion, on top of ADR-016 Q4's own
> ratified deferral naming this exact amendment. Drafter = the in-harness `plan-drafter` subagent
> (ADR-013 D1 phased authoring / ADR-009 D1 interim authoring). Independent
> reviewers = Code R2 (every cited `file:line` re-verified on disk against
> fresh evidence; commits per ADR-009 D2) + Cray at ratification (Proposed →
> Accepted). Drafter ≠ ratifier — separation **intact**. Because the SD forks
> were adjudicated by Cray *during* drafting (the 2026-06-25 precedent), the
> independent-deliberation check is Code's R2 review + Cray's ratification of
> the rendered whole; the genuinely-open shape choices were surfaced as
> OQ-1..OQ-4 and resolved by Cray at ratification (session 115, all four
> as-recommended) — none silently resolved by the drafter.

#### Context

**Where Q4 stands.** The 2026-07-01 amendment typed the read entry point
(`StepInput.reads`) + the `object_types` allowlist + the load gate, and
deferred the run-consume executor to Q4. PLAN-0048 (Complete 2026-07-04, PRs
#533–#539) then rendered Q4's **single-read half**: the engine-owned,
deterministic `QueryStepExecutor` gives a plain declared read
declared==dispatched through the compile / execute / inspect seam. But
**multi-read remains a typed refusal**: `len(reads) > 1` raises
`ReadRefusal(unsupported_read_shape)` with "a join grammar is a future ADR-016
amendment" (`services/engine/procedures/query_step.py:167-175`). PLAN-0048
kept the grammar out of scope on principle — inventing join semantics in a
build would be new `extra="forbid"` spec surface, "an **ADR-016 amendment**,
not a build call" (`docs/plans/done/0048-q4-generic-query-executor.md:95`,
restated in the close-out deferral list `0048:214`). This amendment IS that
decision.

**The declaration gap.** `StepInput.reads: list[str]`
(`services/engine/procedures/spec.py:246-250`) names ontology object-type
NAMES only — it cannot express join keys, projections, or aggregation. And
PLAN-0048 fact-pack 8 (`0048:29`, verified) found that **none** of the four
shipped verticals' query steps is a plain fetch — so under the honest
LOCKED-9 frame every real query step stays **execution-bound ✖** until the
spec can declare what the hand-written seeds actually do.

**The two shapes v1 must express (the actual N=4 substrate — no speculative
grammar):**

1. **Latest-per-group projection** — "latest reading per active
   Asset / Pond / Shipment": the energy / aquaculture / supply_chain OCT
   query steps (`verticals/{energy,aquaculture,supply_chain}/procedures.yaml`).
   The group key IS an ontology-declared relationship — e.g.
   `event_emitted_by_asset` (FK `OperationalEvent.asset_id → Asset.asset_id`,
   `verticals/energy/ontology/energy_v0.yaml:205-209`; the full declared
   `link_types` block at `:197-239`).
2. **Multi-type equi-join enrichment** — procurement `intake`
   (`verticals/procurement/hero_demo/run.py:183-224`): `OperationalEvent` +
   `PurchaseOrder` + `Quotation` joined on `part_id` into one enriched
   `PurchaseRequisition`.

**The intake decomposes into THREE parts** (verified against `_intake_seed`;
this decomposition is why the Hybrid surface wins):

- **(a) a genuine equi-join** — `Quotation ⋈ PurchaseOrder` on `part_id`
  (`run.py:192`). The ontology CAN declare this relationship surface: directly
  (`PurchaseOrder.quote_id → Quotation.quote_id`,
  `verticals/procurement/ontology/procurement_v0.yaml:414`) and transitively
  through `Part` (`Quotation.part_no → Part.part_no` `:390`;
  `PurchaseOrder.part_no → Part.part_no` `:402`).
- **(b) a positional singleton fusion with NO relational key** —
  `OperationalEvent` + `PurchaseOrder`: the seed selects the failure event by
  `event_type == "failure"` and the PO by a constant hero id
  (`run.py:189-191`). The ontology **cannot** declare this; only an explicit
  per-step form can express it.
- **(c) derived / computed fields** — the `compliance` dict, the criticality
  amplification, qty→amount (`run.py:199-224`) — **transforms, NOT joins**:
  no join grammar expresses these; they stay in a downstream transform step or
  the co-existing seed (OQ-3).

**The prerequisite: the ontology already DECLARES the join surface, but it is
not execution-consumable.** Every vertical's `link_types` carry a
`foreign_key` (e.g. `energy_v0.yaml:197-239`), BUT `LinkTypeMeta` **drops
`foreign_key` in projection** (`services/engine/ontology_meta.py:102-108` —
name / from_type / to_type / cardinality only), so the join column never
reaches the typed registry the executor consumes. Likewise, ADR-0027 SD-5's
`join_path` + `grain` on `quantity_bindings` (`ontology_meta.py:71-76`; in the
wild: `verticals/supply_chain/ontology/supply_chain_v0.yaml:120-123`,
`join_path: OperationalEvent.shipment_id -> Shipment.shipment_id`) are parsed
as free-text enrichment hints, NOT executed. The declarative-join substrate
exists on paper; SD-D below promotes it to typed, consumable form.

#### Decision (SD-A … SD-D — SD-A/B/C direction LOCKED, Cray-ratified 2026-07-09, session 115; SD-D entailed by SD-A)

Query steps gain a **declarative join/projection grammar**: a query step
DECLARES its multi-read join + projection as typed, authored, deterministic
spec surface, and the generic executor compiles + runs it — extending
declared==dispatched from single reads to the join shapes the shipped
verticals actually use. The grammar is authored and deterministic end to end;
**no LLM proposes, selects, or reshapes anything in the read path** (LOCKED-6
/ ADR-0024 D3/D6, carried verbatim in the Scope boundary).

**SD-A — grammar surface = HYBRID: ontology-declared default + per-step
explicit override (RATIFIED as the fork pick).** The ontology's declared
`link_types` provide the **default** join: when a step joins declared reads
across a declared relationship, the join keys resolve from the declared
`foreign_key` — the ontology stays the single source of join truth (the moat:
the join is *governed* wherever the ontology can express it). A per-step
**explicit override** (on-keys / projection) covers exactly the shapes the
ontology cannot express — the intake's positional singleton fusion (Context
(b)) and custom projections — as an honest, typed escape hatch: visible in the
spec, load-gated like everything else, never silently guessed. Illustrative
sketch only (the binding home is **OQ-1**; the follow-up build PLAN owns the
literal schema):

```yaml
# ILLUSTRATIVE ONLY — binding home = OQ-1; the build PLAN owns the literal schema.
# shape 1 — latest-per-group projection over a DECLARED link (ontology default):
input:
  reads: [OperationalEvent]
  project: { latest_per: event_emitted_by_asset }  # group key = the link's declared foreign_key
# shape 2 — equi-join enrichment; keys default from a declared link, or an
# explicit per-step override where no declared relationship fits:
input:
  reads: [PurchaseOrder, Quotation]
  join: [ { on: part_id } ]                        # explicit override form (validation posture = OQ-4)
```

**SD-B — v1 scope = EXACTLY the two shipped shapes; general aggregation
DEFERRED (RATIFIED as the fork pick).** v1 expresses (1) latest-per-group
projection and (2) multi-type equi-join enrichment — the shapes the N=4
substrate actually uses (Rule-of-Three discipline, ADR-006: no speculative
grammar). General group-by / max / min / sum / avg aggregation math is
explicitly **OUT**: that computation already lives on the sibling NL-query
surface (`services/engine/nl_query.py:157-161` `group_by`; `:705-782` the
deterministic aggregate computation), which PLAN-0048 walled off (`0048:98` —
no NL-query path change; convergence = a future design note). Unifying the
procedure grammar's projection with the NL-query aggregate surface is **named
as a future design question** — not v1. A third shape a 5th vertical needs =
extend the grammar via this same amendment discipline (the D2-Amendment OQ-A1
catalog-growth convention).

**SD-C — seed migration = CO-EXIST + migrate under run-semantics PARITY tests
(RATIFIED as the fork pick).** The grammar enables NEW declared multi-reads
immediately once built. The four existing hand-written seeds (esp. procurement
`_SeedQuery` / `_intake_seed`) are **NOT force-retired** by this amendment:
they co-exist, then migrate in a follow-up build-PLAN phase (Phase 3), **each
guarded by a run-semantics-parity test** — the declared-grammar run must
produce the same step output as the seed on the same fixture data. This is the
answer to the PLAN-0048 SD-3 deprecate-in-place concern (migration changes
demo-visible run semantics if the grammar's reading diverges from the seed's);
the parity test is the guard. A seed that cannot reach parity (the intake's
derived fields, pending OQ-3) migrates partially or stays, honestly labelled
**execution-bound ✖** per LOCKED-9 — no over-claim.

**SD-D — the declarative-join substrate: promote `foreign_key` into
`LinkTypeMeta` (typed) and parse `join_path` into an execution-consumable
typed form (ENTAILED by SD-A — named here so the decision is complete; the
follow-up build PLAN owns the wiring).** SD-A's ontology-declared default is
unimplementable while the typed registry drops the join column.
`LinkTypeMeta` gains `foreign_key` in typed form (a parsed
`{from_property, to_property}` shape, not the current free-text
`A.x -> B.y` string it drops today), and ADR-0027 SD-5's `join_path` strings
parse into the **same** execution-consumable typed form — one parsed join
shape, two declaring surfaces. This is a **projection-layer promotion**: the
vertical YAMLs already carry the data, so the ADR-008 authored ontology
grammar is **untouched**; the literal `ontology_meta.py` edit + parser +
validation belong to the follow-up build PLAN.

**Enforcement continuity (binding).** Every object_type a joined read names
routes through **the single shared `read_bound_violation` predicate**
(`services/engine/procedures/orchestrator.py:219-237`) against
`ontology ∩ Agent.allowed.object_types` — at BOTH the load gate
(`validate_read_bindings`) AND run-time compile/dispatch — so multi-read opens
**no side door** around the Q3 bound (PLAN-0048 AC-3 one-bound-zero-drift,
extended, not forked).

**Sequencing.** This amendment (the decision) → the follow-up build PLAN (the
grammar schema + compile/execute extension + the SD-D registry promotion) →
per-vertical production factory + seed migration (Phase 3, parity-guarded per
SD-C).

#### Alternatives considered

- **Alternative A — pure ontology-lean (joins ONLY via declared
  `link_types`).** Maximal single-source-of-truth. **Rejected:** it cannot
  express the intake's positional singleton fusion (no relational key, Context
  (b)) nor custom projections → procurement `intake` becomes permanently
  un-migratable, freezing the seed — and LOCKED-9 never closes for the hero
  vertical.
- **Alternative B — pure explicit per-step (all keys authored on the step).**
  Fully general. **Rejected:** it duplicates join knowledge the ontology
  already declares (`foreign_key` in every vertical YAML) → a two-source drift
  hazard (the same argument that shaped the D2-A2 Hybrid facet), and it
  weakens the governed story — the moat is that the **ontology** declares the
  operational semantics.
- **No grammar — keep the hand-written seeds permanently.** **Rejected:**
  every real query step in every shipped vertical stays execution-bound ✖
  (PLAN-0048 fact 8 + LOCKED-9); the read side never reaches
  declared==dispatched parity on real workloads.
- **Full aggregation grammar now (unify with `nl_query`).** **Rejected
  (deferred):** SD-B — speculative surface beyond the N=4 substrate; the
  PLAN-0048 NL-query wall (`0048:98`) stands; unification is a named future
  design question.
- **Force-retire the seeds in this amendment.** **Rejected:** SD-C —
  demo-visible run-semantics risk without a parity guard; migration is a
  build-PLAN phase, parity-gated.
- **A new standalone ADR.** **Rejected:** the grammar directly extends the D2
  `StepInput` read grammar under `extra="forbid"` — the in-place amendment
  precedent (2026-06-25 / 2026-07-01 / 2026-07-05) applies.
- **LLM-assisted join/reshape** (the "flexible" fallback). **Rejected
  outright:** LOCKED-6 / ADR-0024 D3/D6 — no LLM anywhere in the read path;
  the grammar is authored, declarative, deterministic.

#### Scope boundary (amendment — keep it tight)

- **IN:** the grammar **DECISION** — the Hybrid surface (SD-A), the two-shape
  v1 scope (SD-B), the co-exist + parity migration posture (SD-C), the
  substrate-promotion decision (SD-D), and the enforcement-continuity
  property. Nothing else.
- **OUT — the build** (a follow-up build PLAN, gated on this `Accepted`): the
  literal spec schema + validators; the grammar compile/execute extension of
  `plan_read` / `QueryStepExecutor`; the `LinkTypeMeta.foreign_key` +
  `join_path` registry promotion (SD-D wiring); the per-vertical seed
  migration + parity tests (Phase 3); the governance-pin +
  `STEP_GOVERNANCE_FIELDS` wiring.
- **OUT:** general aggregation math / NL-query unification (SD-B);
  `fetch_links` / `stream_events` executors or bounds (LOCKED-2 carried); any
  repair loop (OQ-2 — recommended none).
- **Inherited LOCKs (carried — must-not-violate):**
  - `extra="forbid"` on `StepInput` / `Step` / `AgentAllowed` — any new
    grammar field is a new typed KEY, which is exactly why this is a G-gated
    ADR-016 amendment and not a build call.
  - **NO LLM anywhere in the read path** (LOCKED-6 / ADR-0024 D3/D6) — the
    grammar is authored / declarative / deterministic; no LLM proposes a join
    or a reshape.
  - `where` stays the **engine-side post-fetch field-equality filter**
    (LOCKED-3 / OQ-4 of the Q3 amendment) — never pushed to the adapter.
  - the shared `read_bound_violation` predicate (`orchestrator.py:219-237`)
    remains THE single bound checked by BOTH the load gate
    (`validate_read_bindings`) AND run-time dispatch — every joined/named
    object_type routes through it against
    `ontology ∩ Agent.allowed.object_types` (AC-3; load-acceptance and
    run-dispatch cannot drift).
  - `reads` stays `list[str]` (LOCKED-4 / OQ-5); empty
    `Agent.allowed.object_types` = unconstrained (LOCKED-5 / OQ-6).
  - `fetch_objects`-style **object** reads only (LOCKED-2 / OQ-3) — not
    `fetch_links` / `stream_events`.
  - new grammar fields are **H-governed + pinned** — they join
    `STEP_GOVERNANCE_FIELDS` + `build_governance_snapshot` (the PLAN-0048
    SD-5(b) precedent; a mid-flight grammar edit fails CLOSED at resume).
- **UNCHANGED:** the ADR-007 `RecommendedAction` envelope; the ADR-008
  authored ontology grammar (SD-D promotes the *projection* — the
  `foreign_key` / `join_path` data already exists in every vertical YAML); the
  Q3 load gate's semantics; `from_step` intra-run threading; the
  `DataAdapter` contract and how the adapter is selected.

#### Open Questions (amendment — Cray ratifies at Proposed → Accepted; do NOT silently resolve)

The **direction is LOCKED** (Hybrid surface, two-shape v1 scope, co-exist +
parity migration — SD-A/B/C are ratified forks, not OQs). The four *shape*
choices below were surfaced genuinely open at Proposed and are now **RESOLVED
— all four as-recommended, Cray-ratified 2026-07-09 (session 115) via
AskUserQuestion**; each OQ keeps its deliberation text as the record:

- **OQ-1 (grammar binding home) — RESOLVED (Cray-ratified 2026-07-09, session
  115): extend `StepInput` with the typed `join` / `project` construct** (the
  recommended option); the build PLAN owns the literal schema. *Surfaced as:*
  Extend `StepInput` with a lean typed
  `join` / `project` construct (**recommended** — the read grammar stays one
  cohesive input model beside `from` / `where` / `reads`, mirroring the Q3
  amendment's ratified OQ-1 placement of `reads` on `StepInput`) **vs** a new
  sibling construct (e.g. a top-level `Step.read_plan`). Both keep
  `extra="forbid"`. *Why Cray's call:* it fixes the spec grammar's public
  shape and the H-governance field home.
- **OQ-2 (repair loop) — RESOLVED (Cray-ratified 2026-07-09, session 115): NO
  repair loop in v1**; if a loop is EVER added, the D-N2 future contract
  stands — deterministic, fixed-attempt, in-allowlist, LLM-free. *Surfaced
  as:* **Recommended: NONE in v1** — consistent with
  PLAN-0048 D-N2 (`0048:50`): no execute-validate-retry; the bound
  (attempts = 1 per declared read) stays a tested property. If a loop is EVER
  added it is deterministic, fixed-attempt, in-allowlist, and LLM-free (the
  documented D-N2 future contract). Confirm.
- **OQ-3 (derived/computed-field boundary) — RESOLVED (Cray-ratified
  2026-07-09, session 115): the grammar = join + projection (field
  select / rename) ONLY; arbitrary computation (the intake's `compliance` /
  criticality amplification / qty→amount) stays in a downstream transform step
  or the co-existing seed** — so procurement `intake` migrates **PARTIALLY**
  under the SD-C parity guard (the join half migrates; the derived fields
  stay, honestly labelled execution-bound ✖ per LOCKED-9). *Surfaced as:* The
  grammar covers **join +
  projection (field select / rename) ONLY**; arbitrary computation — the
  intake's `compliance` dict, criticality amplification, qty→amount — stays in
  a downstream transform step or the co-existing seed. **Confirm the
  boundary** — it determines whether `intake` migrates fully (if a downstream
  transform home exists) or partially (the seed keeps the derived fields; the
  join half migrates under the SD-C parity guard).
- **OQ-4 (override validation) — RESOLVED (Cray-ratified 2026-07-09, session
  115): warn-first** — a per-step explicit override join not backed by any
  declared `link_types` relationship emits a WARNING (ontology-vs-step drift
  stays visible), not a rejection (reject would defeat the override, whose
  purpose is the intake's undeclarable fusion); tightening to reject is left
  as a future option. *Surfaced as:* Is a per-step explicit `on`-key override
  validated against the declared `link_types` — **warn** or **reject** when a
  join is not backed by any declared relationship — or left free?
  *Recommendation:* **warn-first** — the override EXISTS precisely for
  undeclared shapes (the intake's fusion), so reject would defeat it, while a
  warning keeps ontology-vs-step drift visible and leaves room to tighten
  later. *Why Cray's call:* it sets how hard the ontology's declared-join
  primacy is enforced against the escape hatch.

#### Amendment references

- `services/engine/procedures/query_step.py:167-175` — the multi-read typed
  refusal (`ReadRefusal(unsupported_read_shape)`, "a join grammar is a future
  ADR-016 amendment") this amendment renders.
- `services/engine/procedures/spec.py:246-250` — `StepInput.reads: list[str]`
  (object-type names only; the declaration gap).
- `services/engine/procedures/orchestrator.py:219-237` —
  `read_bound_violation`, the single shared bound predicate every joined
  object_type keeps routing through (enforcement continuity).
- `services/engine/ontology_meta.py:102-108` — `LinkTypeMeta` drops
  `foreign_key` in projection; `:71-76` — the `join_path` / `grain` free-text
  hints (both promoted by SD-D).
- `verticals/energy/ontology/energy_v0.yaml:197-239` — the declared
  `link_types` + `foreign_key` substrate (`event_emitted_by_asset` at
  `:205-209`).
- `verticals/supply_chain/ontology/supply_chain_v0.yaml:120-123` — the
  ADR-0027 SD-5 `join_path` / `grain` declaration in the wild.
- `verticals/procurement/ontology/procurement_v0.yaml:329-414` — the declared
  procurement relationship surface (`PurchaseOrder.quote_id → Quotation.quote_id`
  `:414`; the transitive `part_no` links via `Part` `:390` / `:402`).
- `verticals/procurement/hero_demo/run.py:183-224` — `_intake_seed`: the
  three-part decomposition (equi-join `:192` / positional fusion `:189-191` /
  derived fields `:199-224`).
- `verticals/{energy,aquaculture,supply_chain}/procedures.yaml` — the
  latest-per-group query steps (shape 1).
- `docs/plans/done/0048-q4-generic-query-executor.md` — the single-read
  predecessor: the grammar named as an ADR-016 amendment (`:95`, `:214`),
  fact-pack 8 (`:29` — no shipped query step is a plain fetch), the D-N2
  no-retry contract (`:50`), the NL-query wall (`:98`), and the research-brief
  authorizing context (`:8`).
- `services/engine/nl_query.py:157-161`, `:705-782` — the sibling
  deterministic aggregate surface SD-B walls off (future unification = a named
  design question).
- ADR-0027 SD-5 — `join_path` + `grain` (the enrichment hints SD-D makes
  execution-consumable).
- ADR-008 — the authored ontology `link_types` grammar (untouched; SD-D is a
  projection-layer promotion).
- ADR-0024 D3/D6 — governed ≠ generated; no LLM in the read path (carried).
- ADR-016 D2 + D3 Amendment (2026-07-01) — Q4's deferral + OQ-5 ("the
  multi-read join lands with Q4"); D2 Amendment (2026-06-25) + D2 + D3
  Amendment (2026-07-05) — the in-place, extends-not-reverses precedents.
- ADR-006 (Rule-of-Three) — the N=4 substrate justifies exactly the two
  shapes, no more.
- `docs/research/private/2026-07-03-llm-db-reliability-techniques.md` (+ the
  two sibling 2026-07-03 briefs, gitignored, on-disk) — the CaMeL
  deterministic-disposer + dbt-MCP compile/execute/inspect seam authorizing
  context PLAN-0048 absorbed (`0048:8,49-51`).

### Amendment (2026-07-11): per-entity `threshold_field` on evaluate steps (same-row v1)

> **Status:** **Accepted** (Cray-ratified 2026-07-11 after Code R2 — the TF-1
> at-most-one validator defect was the R2 catch; OQ-1..OQ-4 ratified
> as-recommended). **Date:** 2026-07-11. **Deciders:** Jirachai Thiemsert
> (founder).
> **Amends:** D2 (the `Step` band grammar — `threshold` / `direction` /
> `watch_margin`, PLAN-0022 Step 3) — **extends, does not reverse or
> renumber**; mirrors the **D2 Amendment (2026-06-25)** typed-`facet:`, the
> **Q3 (2026-07-01)** / **service-principal (2026-07-05)** / **Q4 join
> (2026-07-09)** in-place precedents. This discharges **PLAN-0065 SD-3**: the
> per-part reorder band was ratified-DEFERRED there precisely because it trips
> the L-4 tripwire — "no spec / grammar change without an ADR-016 amendment"
> (`docs/plans/done/0065-calm-path-reorder-runnability.md:101-105`, fact 14
> `:245-256`, SD-3 `:402-407`). This amendment IS that amendment.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray —
> the three forks (TF-1 Fork A grammar-field, TF-2 same-row v1 scope, TF-3
> load-gate seam (a) trace-to-reads) were adjudicated by Cray in-session
> 2026-07-11, on top of PLAN-0065 SD-3's ratified deferral naming this exact
> amendment. Drafter = the in-harness `plan-drafter` subagent (ADR-013 D1
> phased authoring / ADR-009 D1 interim authoring). Independent reviewers =
> Code R2 (every cited `file:line` re-verified on disk against fresh evidence;
> commits per ADR-009 D2) + Cray at ratification (Proposed → Accepted).
> Drafter ≠ ratifier — separation **intact**. The genuinely-open shape details
> are surfaced as OQ-1..OQ-4 below for Cray at ratification — none silently
> resolved by the drafter.

#### Context

**The stand-in this amendment retires.** The shipped deterministic
`EvaluateStepExecutor` compares every entity's `measured_value` against **ONE
scalar authored band**: `Step.threshold: float | None`
(`services/engine/procedures/spec.py:778-782`), consumed at
`evaluate_step.py:82-97`. Procurement's `judge_stock` therefore authors
`threshold: 100.0` — an explicit stand-in whose own YAML comment says "a
per-part band is a Stage-2 refinement -- PLAN-0065 SD-3, deferred"
(`verticals/procurement/procedures.yaml:638-641`; the sibling `judge_stock`
carries the same scalar at `:348`). One floor judges every part, but each part
should band against its **own** `Part.reorder_point` — "Stock level at or
below which a reorder fires" (`verticals/procurement/ontology/
procurement_v0.yaml:191-193`). The data already reaches the judge: the query
step's rename-projection keeps unmapped columns
(`services/engine/procedures/query_step.py:649-663`), so `reorder_point`
rides every row into `judge_stock` (`procedures.yaml:625-632`) — the rows
carry the per-part band; the grammar just cannot name it.

**Precedent clarification (readers will assume D2-A3 — it is NOT).**
PLAN-0065 fact 14 filed this as "ADR-016 D2-A3 territory" (`0065:253`); that
framing is corrected here. D2-A3 is the *facet* rule — a non-authoritative
annotation that **points at** an already-typed scalar band to avoid
double-storing one number. `threshold_field` is the **`reads` /
`project.order_by` precedent** (Q3 amendment OQ-1; Q4 SD-5,
`spec.py:299-303`): a typed step field that **NAMES a declared ontology
column** and is load-validated against `_declared_properties`
(`orchestrator.py:315-317`; the `order_by ∈ base_props` assert at
`:435-439`). The value is per-row data; the *name* is authored, governed spec
surface. Different, established precedent — no facet semantics change.

**Reuse evidence (why a grammar field, not a one-off).** Per-entity
thresholding is conceptually right in all four verticals; 2 of 4 already
carry the limit property: procurement `Part.reorder_point` (**same-row** —
this v1) and energy `Asset.rated_current_a` / `capacity_kw`
(`verticals/energy/ontology/energy_v0.yaml:38-44` — the limit lives on the
**FK-parent**, so consuming it needs a join). supply_chain (`cargo_type`
enum, `supply_chain_v0.yaml:39`) and aquaculture (`species` enum,
`aquaculture_v0.yaml:34`) signal per-class bands but would first need a new
numeric ontology property. N=1 buildable-today case ⇒ v1 is scoped same-row
(Rule-of-Three, ADR-006 — no speculative join/derivation grammar at N=1).

#### Decision (TF-1 … TF-4 — TF-1/2/3 direction LOCKED, Cray-ratified in-session 2026-07-11)

**TF-1 — Fork A: a grammar field `threshold_field`, NOT a custom executor
(LOCKED).** `Step` gains `threshold_field: str | None` — optional; absent =
today's behaviour byte-for-byte (every shipped procedure loads unchanged).
**AT MOST one of** `threshold` / `threshold_field` (mutual exclusion ONLY) is
enforced by a `@model_validator(mode="after")`: BOTH-set raises; NEITHER-set
stays valid. Neither-set MUST stay valid because two of the four shipped
verticals author band-less `evaluate` judges — energy `judge`
(`verticals/energy/procedures.yaml:64-71`) and supply_chain `judge`
(`verticals/supply_chain/procedures.yaml:65-72`) carry
`gate_kind: env_band` and take their band from `EnvBandEvaluateExecutor` via
`env_var` (D2-A3), and NL-only judge steps keep their own custom executors. A
mandatory exactly-one (the `JoinSpec._validate_exactly_one_form` shape,
`spec.py:265-278`) would therefore fail both env-band judges at load — the
**wrong precedent** here (Code R2 catch at review; not-both is the correct
semantics). `ConfigDict(extra="forbid")` is KEPT — `threshold_field` becomes
a known key, which is exactly why this is a G-gated ADR-016 amendment and not
a build call. The existing band invariants extend naturally: the band family
stays evaluate-only, and `direction` / `watch_margin` require *a* band —
scalar or field (`spec.py:813-838`).

```yaml
# ILLUSTRATIVE ONLY — the build PLAN owns the literal schema.
- step_id: judge_stock
  kind: evaluate
  threshold_field: reorder_point   # each Part judges vs ITS OWN reorder_point
  direction: below                 # direction / watch_margin stay step-level scalars (TF-4)
```

**TF-2 — v1 scope = SAME-ROW ONLY (LOCKED).** `threshold_field` names a
column present on the SAME entity rows flowing into the evaluate step
(procurement's `reorder_point`, already projected through — Context). Two
extensions are **explicitly DEFERRED to future amendments** under this same
in-place discipline: (i) the **FK-parent-column** case (energy
`Asset.rated_current_a` — needs a join to reach the reading's parent); (ii)
the **not-yet-present-column** cases (supply_chain `cargo_type` / aquaculture
`species` — need a new numeric ontology property first). Rule-of-Three: do
not over-abstract at N=1 same-row case.

**TF-3 — load-gate validation seam = (a) trace-to-reads (LOCKED).** The
evaluate step has no `reads` of its own, so the load gate traces the step's
`from_step` chain (default = the immediately preceding step) back to the
QUERY step that declared `reads`, obtains that object type, and asserts
`threshold_field ∈ _declared_properties(meta, object_type)` — the
`project.order_by` precedent (`orchestrator.py:435-439`), rendered by
extending `validate_read_bindings` (`orchestrator.py:252-308`), which today
skips every non-QUERY step (`:284`). Drafter-rendered corollaries (contract
entailments — confirm at ratification, OQ-1): **(c1)** an untraceable
provenance (the chain reaches a query step WITHOUT `reads`, e.g. a
seed-backed step, or a non-query origin) **fails CLOSED** with a typed
`ProcedureError` — an un-traceable `threshold_field` is un-governable, the
same fail-loud posture as the join/project meta requirement (`:301-308`);
**(c2)** on a multi-read traced step, validate against the **base read**
(`reads[0]`) declared properties — the `_validate_project` base-props
precedent; **(c3)** also assert `threshold_field` is not renamed away by the
traced step's `project.fields` (a rename SOURCE would pass declared-props at
load yet be absent from the rows at run); **(c4)** the gate's trigger
predicate `has_read_bindings` (`orchestrator.py:213-224`) extends to fire
when any evaluate step declares `threshold_field` (else a reads-plus-field
procedure validates but a hypothetical field-only one silently skips the
gate).

**TF-4 — run semantics + governance (extends, never forks).** In
`EvaluateStepExecutor`: the band-less guard (`evaluate_step.py:82-87`)
becomes `threshold is None AND threshold_field is None`; the per-entity loop
resolves the threshold per row — the scalar, or the row's `threshold_field`
column read with the same numeric / bool-reject / fail-loud discipline as
`_entity_value` (`evaluate_step.py:49-65` — a row without a numeric band
fails the step loudly; D4 diverts, never a silent verdict). The step summary
and audit record `threshold_field` (alongside today's `threshold` /
`direction` / `watch_margin`, `:100-114`). The **determinism invariant is
intact** (`evaluate_step.py:14-19` / ADR-0019 / ADR-010 IN-3): no LLM — the
verdict stays a pure function of the entity and the authored band; the only
change is that the band's *value* is carried per-row by governed data whose
column *name* is authored. `"threshold_field"` joins `STEP_GOVERNANCE_FIELDS`
(`services/engine/procedures/draft.py:42-59`) — a per-row breach floor is
human-authored, governance-sensitive spec surface, same class as `threshold`
(`:46`); it sits directly on `Step` (like `threshold`), so a plain membership
entry suffices — no lift-strip needed (unlike nested `StepInput` fields).

#### Change surface (the build contract — this amendment DECIDES; a follow-up build PLAN builds)

- `services/engine/procedures/spec.py` — `Step.threshold_field: str | None`;
  the at-most-one (not-both) `@model_validator` (TF-1 — NOT the `:265-278`
  exactly-one shape); band-invariant extension (`:813-838`);
  `extra="forbid"` kept.
- `services/engine/procedures/evaluate_step.py` — the guard (`:82-87`);
  per-row threshold resolution reusing the `_entity_value` discipline
  (`:49-65`); summary + audit (`:100-114`).
- `services/engine/procedures/orchestrator.py` — extend
  `validate_read_bindings` (`:252-308`) with the TF-3 `from_step` trace +
  `_declared_properties` assert (`:315-317`, precedent `:435-439`); extend
  `has_read_bindings` (`:213-224`) per c4.
- `services/engine/procedures/draft.py` — `"threshold_field"` into
  `STEP_GOVERNANCE_FIELDS` (`:42-59`).
- `verticals/procurement/procedures.yaml` — migrate the `judge_stock` scalar
  stand-ins (`:348`, `:641`) to `threshold_field: reorder_point` (OQ-3 owns
  the which-sites call; the build PLAN owns fixtures + tests).

#### Alternatives considered

- **Fork B — a custom procurement evaluate executor.** **Rejected (Cray,
  in-session 2026-07-11):** (1) NO precedent exists for a vertical-local
  band/governance executor — the only vertical-local executor is
  procurement's `_SeedQuery`, which the project is actively migrating AWAY
  from (PLAN-0048 seed-migration posture); (2) the closest precedent,
  `EnvBandEvaluateExecutor`, is ENGINE-GENERAL
  (`services/engine/procedures/env_band_step.py`, shared by
  energy + supply_chain) and exists only because D2-A3 pre-ratified the
  env-vs-in_file band-source fork — the precedent is "engine-general wrapper
  rendering a RATIFIED grammar fork", not "a vertical ships a bespoke
  executor"; (3) a Fork-B-done-right (engine-general) would STILL need a
  grammar field to say *which column* — collapsing back into Fork A; (4) it
  fights the stated direction (PLAN-0048 "engine-owned generic"; LOCKED-5
  extend-not-fork; this ADR's own note that a per-vertical executor is an
  undocumented operational expectation, not an engine contract).
- **Seam (b) — a runtime presence check instead of the load gate.**
  **Rejected (Cray — contract-first):** lighter, but the misconfiguration
  surfaces mid-run per-row instead of at load; every other declared-name
  field (`reads`, `join`, `project.order_by`) is load-validated against the
  ontology — a runtime-only check would make `threshold_field` the one
  ungoverned name in the grammar.
- **Keep the scalar stand-in permanently.** **Rejected:** one floor judges
  every part — wrong verdicts the moment a second part's `reorder_point ≠
  100`; the YAML itself labels the scalar a deferred stand-in (`:638-639`).
- **Build the full multi-vertical shape now (FK-parent join + per-class
  bands).** **Rejected (deferred):** TF-2 — speculative beyond the N=1
  same-row substrate; the join case lands as a future amendment when energy
  needs it (Rule-of-Three).
- **A new standalone ADR.** **Rejected:** this directly extends the D2 `Step`
  band grammar under `extra="forbid"` — the in-place amendment precedent
  (2026-06-25 / 2026-07-01 / 2026-07-05 / 2026-07-09) applies.

#### Scope boundary (amendment — keep it tight)

- **IN:** the grammar **DECISION** — the `threshold_field` field + at-most-one
  mutual exclusion (TF-1), the same-row v1 scope (TF-2), the trace-to-reads
  load seam (TF-3), the run semantics / governance-pin posture (TF-4).
  Nothing else.
- **OUT — the build** (a follow-up build PLAN, gated on this `Accepted`): the
  literal `spec.py` / `evaluate_step.py` / `orchestrator.py` / `draft.py`
  edits; the procurement YAML migration + tests; fixtures.
- **OUT (deferred to future amendments):** the FK-parent-column join case
  (energy); per-class bands needing new ontology properties
  (supply_chain / aquaculture); any `stock_qty − reorder_point` derived
  computation (the Q4 OQ-3 wall stands — projection is select/rename only).
- **Inherited LOCKs (carried — must-not-violate):** `extra="forbid"` on
  `Step`; **no LLM in the evaluate path** — the determinism invariant
  (`evaluate_step.py:14-19`, ADR-0019 / ADR-010 IN-3) is untouched;
  `threshold_field` is **H-governed + pinned** (`STEP_GOVERNANCE_FIELDS` +
  governance snapshot — a generated skeleton may never self-declare a breach
  floor); the D2-A3 facet stays non-authoritative point-at metadata.
- **UNCHANGED:** the scalar `threshold` path (byte-for-byte when
  `threshold_field` is absent); `classify_verdict` semantics; the ADR-008
  ontology grammar (`reorder_point` already declared); the Q3/Q4 read grammar
  itself; `from_step` threading semantics.

#### Open Questions (amendment — Cray ratifies at Proposed → Accepted; do NOT silently resolve)

The **direction is LOCKED** (Fork A / same-row v1 / seam (a) — TF-1/2/3 are
ratified forks, not OQs). Four shape details were surfaced; **all four
RATIFIED as-recommended by Cray on 2026-07-11 at Accept** — OQ-1 confirm
c1–c4; OQ-2 no `watch_margin_field` in v1; OQ-3 migrate BOTH `judge_stock`
sites with per-part fixtures; OQ-4 keep `in_file_band`. Recorded inline below
(each recommendation now reads as the ratified disposition):

- **OQ-1 (TF-3 corollaries c1–c4).** The seam's contract entailments —
  untraceable-provenance fail-closed (c1), base-read validation target (c2),
  the `project.fields` rename-source assert (c3), the `has_read_bindings`
  trigger extension (c4) — are drafter-rendered, not Cray-locked.
  *Recommendation:* confirm all four — each is the fail-loud / one-bound
  posture the Q3/Q4 gates already take. *Why Cray's call:* they fix how hard
  the load gate refuses.
- **OQ-2 (symmetric `watch_margin_field` / `direction_field`).**
  *Recommendation:* **NO in v1** — no shipped vertical authors a per-row
  watch margin or direction (Rule-of-Three); a future need lands via this
  same amendment discipline. Naming it here prevents the build PLAN from
  "completing the family" speculatively.
- **OQ-3 (which YAML sites migrate).** Both `judge_stock` scalars (`:348`
  event-flavoured + `:641` scheduled calm-path)? *Recommendation:* **both**,
  in the build PLAN, each with a fixture asserting the per-part verdicts —
  verdict changes for parts whose `reorder_point ≠ 100` are the *point*, so
  the demo-visible delta is asserted, not discovered.
- **OQ-4 (facet `gate_kind` taxonomy).** Does a per-row band stay
  `in_file_band` (the band's *name* is authored in-file; D2-A3 point-at now
  covers `threshold` OR `threshold_field`) or warrant a new `gate_kind`?
  *Recommendation:* **keep `in_file_band`** — the facet is non-authoritative
  metadata (D2-A2); grow the catalog only when a shape genuinely diverges
  (the D2-Amendment OQ-A1 catalog-growth convention).

#### Amendment references

- `docs/plans/done/0065-calm-path-reorder-runnability.md` — the L-4 tripwire
  (`:101-105`), fact 14 (`:245-256` — the fired-at-design-time analysis
  naming a "`threshold_field`-style addition"), SD-3 (`:402-407`, `:567-570`).
- `verticals/procurement/procedures.yaml:638-641` / `:348` — the scalar
  stand-ins; `:625-632` — the projection that already carries
  `reorder_point` to the judge.
- `verticals/procurement/ontology/procurement_v0.yaml:191-193` —
  `Part.reorder_point`.
- `services/engine/procedures/spec.py:778-793` — the scalar band;
  `:265-278` — `JoinSpec._validate_exactly_one_form`, the mandatory-exactly-one
  shape TF-1 deliberately does NOT mirror (band-less env-band judges must keep
  loading — R2 catch); `:299-303` — `order_by`, the named-declared-column
  precedent; `:813-838` — the band invariants.
- `services/engine/procedures/evaluate_step.py:14-19` (determinism),
  `:49-65` (`_entity_value` discipline), `:82-97` (guard + loop),
  `:100-114` (summary + audit).
- `services/engine/procedures/orchestrator.py:213-224` (`has_read_bindings`),
  `:252-308` (`validate_read_bindings` + the `:284` QUERY-only skip +
  `:301-308` fail-loud meta precedent), `:315-317`
  (`_declared_properties`), `:435-439` (the `order_by ∈ base_props`
  precedent TF-3 mirrors).
- `services/engine/procedures/query_step.py:649-663` — `_rename` keeps
  unmapped columns (why `reorder_point` reaches the rows).
- `services/engine/procedures/draft.py:42-59` — `STEP_GOVERNANCE_FIELDS`
  (`threshold` at `:46`).
- `services/engine/procedures/env_band_step.py` — `EnvBandEvaluateExecutor`,
  the engine-general precedent Fork B misreads.
- D2 Amendment (2026-06-25) — D2-A3, the point-at rule this field is NOT;
  Q3 (2026-07-01) / Q4 (2026-07-09) amendments — the named-declared-column +
  load-gate precedents this field IS.
- ADR-006 (Rule-of-Three) — the N=1 same-row scoping; ADR-0019 / ADR-010
  IN-3 — the determinism invariant carried.

### Amendment (2026-07-12): FK-parent-column `threshold_field` — the join extension (per-entity bands, v2)

> **Status:** **Accepted** (Cray-ratified 2026-07-12, typed via
> AskUserQuestion, after Code R2 — no R2 defect; R2 re-verified the
> load-bearing citations on disk and CONFIRMED the SD-1 corrected premise:
> the shipped `_execute_join`, the merged-row band resolution, the band-aware
> `derive_governance_todo`. SD-1..SD-5 ratified as-recommended, with SD-4
> explicitly narrowed to a **supply_chain-only build scope**). **Date:**
> 2026-07-12 (session 121).
> **Deciders:** Jirachai Thiemsert (founder).
> **Amends:** the 2026-07-11 `threshold_field` amendment's **TF-2** (the
> same-row v1 scope) — **extends, does not reverse or renumber**; it
> discharges TF-2's own deferral (i), "the **FK-parent-column** case (energy
> `Asset.rated_current_a` — needs a join to reach the reading's parent)",
> exactly under the in-place discipline TF-2 named for it. It RIDES the
> Accepted **Q4 join amendment (2026-07-09)** — no join-grammar change; the
> decision series is **FKP-1 … FKP-4**, distinct from the same-row TF-1..TF-4.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray —
> three forks typed-ratified 2026-07-12 via AskUserQuestion: (1) direction =
> the **FK-parent join extension** of `threshold_field` (the same-row
> denormalize-the-band-onto-reading-rows hack was REJECTED as dishonest
> modeling); (2) **first demo consumer = supply_chain** (the cold-chain
> per-cargo-type ceiling); (3) **one in-place ADR-016 amendment** (the
> 2026-06-25 / 07-01 / 07-05 / 07-09 / 07-11 precedent). Drafter = the
> in-harness `plan-drafter` subagent (ADR-013 D1 phased authoring / ADR-009 D1
> interim authoring). Independent reviewers = Code R2 (every cited `file:line`
> re-verified on disk against fresh evidence; commits per ADR-009 D2) + Cray
> at ratification (Proposed → Accepted). Drafter ≠ ratifier — separation
> **intact**. The genuinely-open shape questions were surfaced as SD-1..SD-5
> below — none silently resolved; SD-1 includes a **dispatch-premise
> correction from disk evidence** (the join executor's build status), surfaced
> rather than silently adopted in either direction. **All five SDs RATIFIED
> as-recommended by Cray (typed, 2026-07-12), SD-4 explicitly = build scope
> supply_chain ONLY** — recorded inline below; drafter ≠ ratifier, separation
> intact through the Proposed → Accepted flip.

#### Context

**What v1 shipped, and its ratified wall.** The 2026-07-11 amendment (TF-1..
TF-4, built end-to-end as PLAN-0066 — the executor code cited below is the
shipped build) gave `evaluate` steps a per-entity band: `threshold_field`
names a column **on the same rows** flowing into the judge, mutually
exclusive with the scalar `threshold` (`spec.py:796-801`, `:835-845`).
Procurement was, by the amendment's own count, the **only** same-row case
(its N=1 note); TF-2 walled the scope to same-row and explicitly deferred the
FK-parent-column and not-yet-present-column cases to future amendments.

**The session-121 grounding: ALL THREE remaining OCT verticals band by an
FK-parent discriminator, with the reading rows = `OperationalEvent`.**

- **energy** — the limit is `Asset.rated_current_a` (numeric, ALREADY
  declared: `verticals/energy/ontology/energy_v0.yaml:40-44`, "Rated current
  in amperes for current-rated assets (feeders, etc.)"); the reading is
  `OperationalEvent` with FK `asset_id → Asset`
  (`energy_v0.yaml:107-109`; declared link `event_emitted_by_asset`
  `:205-209`). Its `judge` is band-less `env_band` today
  (`verticals/energy/procedures.yaml:64-75` — one env ceiling for every
  asset).
- **supply_chain** — the discriminator is `Shipment.cargo_type` (enum:
  pharma / produce / frozen / biologic,
  `verticals/supply_chain/ontology/supply_chain_v0.yaml:39-41`); there is
  **no numeric band property yet**. `read_temps` reads `OperationalEvent`
  with `project: {latest_per: event_concerns_shipment, order_by: occurred_at}`
  (`verticals/supply_chain/procedures.yaml:47-55`) — a latest-per-group
  **projection, NOT a join**: Shipment columns never reach the judge rows
  today. The `judge` is `env_band` (`:65-76` — one cold-chain ceiling for
  pharma and frozen alike). The ontology already *declares* the join surface:
  the temperature quantity binding carries
  `join_path: OperationalEvent.shipment_id -> Shipment.shipment_id`
  (`supply_chain_v0.yaml:123`).
- **aquaculture** — the discriminator is `Pond.species` (enum,
  `verticals/aquaculture/ontology/aquaculture_v0.yaml:34-36`); `read_do`
  reads `OperationalEvent` via `latest_per: event_emitted_by_pond`
  (`verticals/aquaculture/procedures.yaml:64-76`); the `judge` authors ONE
  scalar in-file floor `threshold: 4.0` for every pond regardless of species
  (`:87-107`).

**Consequence.** There is NO cheap "same-row second vertical" — procurement
exhausted that shape. Giving ANY second vertical a per-entity band requires
reaching an FK-parent column. **Rule-of-Three (ADR-006) is therefore MET for
the FK-parent shape**: three verticals triangulate the same join-then-band
pattern. This amendment is no longer speculative-at-N=1 — it is the ratified
TF-2 deferral coming due on schedule.

**The execution substrate — a corrected premise (drafter finding; ratify
under SD-1).** The dispatch framed the Q4 join executor as "deferred Phase
C", citing the load-gate docstring "join/project = declared ✔ · gated ✔ ·
execution-bound ✖ until Phase C lands the executor extension"
(`services/engine/procedures/orchestrator.py:281-283`). Fresh on-disk
evidence contradicts that docstring: **PLAN-0061 Phase C LANDED** (PR #666,
`docs/plans/done/0061-join-projection-grammar-build.md:3` — "Steps 1-4 built
as four green-gate PRs … #666 Phase C compile/execute"). The executor exists
end-to-end: `_execute_join` runs the SD-1 pinned pipeline — one fetch per
declared read → base `where` → per-join `where` → keyed/fuse joins in
declaration order → latest-per-group → field renames
(`services/engine/procedures/query_step.py:458-520`; `_apply_join`
`:522-581`; `_merge` base-wins collision accounting `:583-603`;
`_latest_per_group` `:605-646`). PLAN-0062 ("Q4 Phase-3") then migrated the
three OCT query steps onto this same `JoinReadPlan` path (projection-only,
per the `procedures.yaml` comments) — it runs in shipped procedures today.
The honest residual ✖ in PLAN-0061's own close-out (`0061:450-452`) applies
to the **not-yet-migrated seed-backed procedures**, not to the executor. What
IS true: **zero shipped procedure declares `join:`** (a repo grep over
`verticals/**/procedures.yaml` returns no matches) — the keyed-join path is
built and offline-tested but production-unexercised. The stale docstring is a
change-surface item below.

**The one genuine blocker this amendment removes.** The `threshold_field`
load gate `_validate_threshold_field_bindings`
(`orchestrator.py:350-386`) validates the band column ONLY against the traced
query step's BASE read — `base = source.input.reads[0]` (`:374-375`, the TF-3
c2 rule). It cannot reach a joined parent type, so an FK-parent band column
refuses at load today even though the executor could deliver it onto the
rows. The gate-domain extension (FKP-2) is the load-bearing change.

#### Decision (FKP-1 … FKP-4 — FKP-1 direction LOCKED, Cray-ratified in-session 2026-07-12; FKP-2/3/4 drafter-rendered, RATIFIED via SD-1..SD-5 at Accept)

**FKP-1 — `threshold_field` may name a column on a JOINED FK-PARENT of the
traced query step (LOCKED direction).** TF-2's scope extends from *same-row*
to *same-row ∪ joined-parent*: when the traced query step declares a Q4
`join`, the band column may live on the joined parent type — the join
delivers it onto the merged rows before the judge. **Zero new grammar
fields**: the reach comes entirely from the already-Accepted Q4 join grammar
on the QUERY step (`reads` + `join` + `project`); the evaluate step's surface
(`threshold_field` + the TF-1 mutual exclusion, `spec.py:835-845`) is
byte-identical. The rejected alternative — denormalizing the parent's band
onto the reading rows at seed/adapter time so same-row v1 "just works" — was
REJECTED by Cray (2026-07-12) as dishonest modeling: the band is a property
of the parent entity, not of each reading; copying it per-row invents data
provenance and a drift hazard. Why this is still a G-gated amendment despite
zero new fields: TF-2's same-row wall was **ratified spec semantics**, and
the L-4 tripwire ("no spec / grammar change without an ADR-016 amendment")
covers semantics, not just fields.

```yaml
# ILLUSTRATIVE ONLY — the build PLAN owns the literal schema, seeds, fixtures.
# supply_chain read_temps: multi-read + declared-link join + latest-per-group
- step_id: read_temps
  kind: query
  input:
    reads: [OperationalEvent, Shipment]
    where: { event_type: reading }
    join:
      - { with: Shipment, link: event_concerns_shipment }  # Q4 SD-A declared default
    project:
      latest_per: event_concerns_shipment
      order_by: occurred_at
      fields: { facility_id: shipment_facility_id }  # the declared facility_id collision, renamed away
- step_id: judge
  kind: evaluate
  threshold_field: temp_ceiling   # each Shipment judges vs ITS OWN cargo-type ceiling
  direction: above                # cold-chain ceiling — breach OVER it
```

**FKP-2 — the load-gate extension (renders SD-3; ratified as-recommended).**
`_validate_threshold_field_bindings` (`orchestrator.py:350-386`) widens its
validation domain from `reads[0]` alone (`:374-375`) to
**`declared_properties(reads[0]) ∪ ⋃ declared_properties(join[].with_read)`**
of the traced query step — the step's own declared `join` names the parent
type, so no new naming surface is needed. Drafter-rendered corollaries
(g1–g4):

- **(g1) fail-closed carried.** A `threshold_field` in NO traced read's
  declared properties refuses with a typed `ProcedureError`; the
  meta-required and no-reads refusals (TF-3 c1) carry unchanged.
- **(g2) ambiguity composes for free.** `_validate_join_project` +
  `_validate_join_collisions` run BEFORE the threshold gate
  (`orchestrator.py:311` then `:312`) and refuse an ontology-DECLARED
  property-name collision between joined types unless `project.fields`
  renames it away (`:461-467`; the equal-named join-key pair is exempt). A
  band-column name that survives to this gate is therefore unambiguous on the
  merged rows **by construction** — no new ambiguity rule is invented.
- **(g3) the rename-away assert carries.** TF-3 c3 extends as-is: a
  `threshold_field` that the traced step's `project.fields` renames away
  refuses at load (a rename SOURCE would pass declared-props yet be absent
  from the rows at run).
- **(g4) runtime-only collisions stay Q4's problem, deliberately.** An
  UNDECLARED runtime key collision keeps the base value and is counted in
  provenance (`_merge`, `query_step.py:583-603`) — the gate governs declared
  reality; this amendment adopts Q4 SD-1's posture rather than forking a
  stricter one for band columns.

**FKP-3 — run semantics: ZERO executor change (verified against the shipped
build).** The per-row band already resolves from the merged row —
`evaluate_step.py:103-109` reads `entity[threshold_field]` through the same
fail-loud `_entity_number` discipline as the reading (`:49-68`); the join
simply delivers the parent's column onto each row before the judge. The
audit already records `threshold_field` (`:131-139`). The **determinism
invariant is untouched** (`evaluate_step.py:14-19`, ADR-0019 / ADR-010 IN-3):
no LLM anywhere in the read or judge path; the band's *value* is per-row
governed data, only its column *name* is authored spec. `draft.py` is also
zero-change: `"threshold_field"` is already in `STEP_GOVERNANCE_FIELDS`
(`draft.py:42-59`, at `:47`) and `derive_governance_todo` is already
band-aware (`:285-288`). **Load-bearing fail-loud consequence (feeds SD-4):**
a joined parent row WITHOUT a numeric band value fails the step loudly — so a
*partially populated* parent band column (energy's `rated_current_a` is
declared "for current-rated assets", i.e. not every Asset carries it) is a
step-failing configuration unless the query narrows to banded rows or the
seed completes the column. Energy is NOT the free second consumer it appears
to be on paper.

**FKP-4 — substrate + first consumer (renders SD-2 / SD-5; ratified as-recommended).**
supply_chain gains a **denormalized numeric band property**
`Shipment.temp_ceiling: float`, seeded per `cargo_type` (pharma / produce /
frozen / biologic each get their ceiling; every shipment that reaches the
judge carries a numeric value, per the FKP-3 fail-loud discipline). After
this, supply_chain is EXACTLY energy's shape — a numeric column on the
FK-parent — so one substrate serves three verticals (Rule-of-Three-consistent
minimal shape; the per-class lookup alternative is OUT, see Alternatives).
The supply_chain `judge` migrates `env_band` → `threshold_field:
temp_ceiling` (per-entity in-file; facet `gate_kind` → `in_file_band` under
the TF OQ-4 kept taxonomy — the band's *name* is authored in-file). The
migrated `read_temps` becomes the **first shipped `join:` consumer** — it
migrates parity-guarded per Q4 SD-C (the declared-grammar run must reproduce
the seed/projection run on the same fixture data, plus the intended
per-cargo verdict deltas asserted explicitly).

#### Change surface (the build contract — this amendment DECIDES; a follow-up build PLAN builds)

- `services/engine/procedures/orchestrator.py` — extend
  `_validate_threshold_field_bindings` (`:350-386`; the `:374-375` base-only
  domain) per FKP-2 g1–g4; **fix the stale Phase-C docstring** (`:281-283` —
  execution-bound is ✔ since PLAN-0061 #666; the honest residual ✖ belongs to
  unmigrated seed-backed procedures, `0061:450-452`).
- `services/engine/procedures/spec.py` — **no field change**; only the
  `threshold_field` description string (`:796-801`, "a same-row ontology
  column") rewords to the extended scope. A docstring edit, not schema.
- `verticals/supply_chain/ontology/supply_chain_v0.yaml` —
  `Shipment.temp_ceiling: float` (a plain new authored property — the ADR-008
  ontology *grammar* is untouched), + the generator ripple (`uv run
  vero-lite …` regeneration: Pydantic / DDL / schema parity, CLAUDE.md §3).
- `verticals/supply_chain/procedures.yaml` — `read_temps` → multi-read +
  declared-link join + kept `latest_per`, with the **declared `facility_id`
  collision renamed away** (`Shipment.facility_id`
  `supply_chain_v0.yaml:53-56` vs `OperationalEvent.facility_id` `:116-118`;
  the `shipment_id` join-key pair is exempt); `judge` → `threshold_field:
  temp_ceiling` + `direction: above` + facet `in_file_band`.
- Seeds / fixtures — per-cargo-type ceilings; a fixture asserting the
  demo-visible per-cargo verdict deltas (the point of the change), plus the
  Q4 SD-C parity test for the migrated read.
- Regression (AC-2-style) — energy's band-less `env_band` judge
  (`verticals/energy/procedures.yaml:64-75`) still loads + runs
  (`EnvBandEvaluateExecutor` stays engine-general); the TF-1 not-both
  invariant already guarantees load — keep the test anyway.
- energy (NOT in the build scope — a labelled follow-on per ratified SD-4;
  recorded here for when it is scheduled) — `judge` →
  `threshold_field: rated_current_a`
  + join via `event_emitted_by_asset` (`energy_v0.yaml:205-209`) + the
  declared `site_id` collision rename (`Asset.site_id` `:54-57` vs
  `OperationalEvent.site_id` `:110-112`) + the FKP-3 partial-population
  narrowing (a `where` to banded/current-rated rows, or seed completion).

#### Alternatives considered

- **Denormalize the band onto the reading rows (same-row v1 "just works").**
  **REJECTED (Cray, 2026-07-12, the LOCKED fork):** dishonest modeling — the
  ceiling is a property of the Shipment/Asset/Pond, not of each reading;
  per-row copies invent provenance and drift the moment the parent's band
  changes between readings.
- **A narrower `threshold_field`-specific parent-column resolver (skip the
  general join).** **Rejected (recommend, SD-1 option c):** it would
  duplicate shipped machinery — `_execute_join` already exists and executes
  (`query_step.py:458-520`) — and inverts Rule-of-Three: the general path is
  built; a special-case sibling is net-new surface plus a SECOND join
  semantics to govern and keep honest.
- **A per-class band LOOKUP grammar (`cargo_type → ceiling` map).**
  **OUT (SD-2 option b):** net-new class-keyed grammar with zero shipped
  consumers of that shape; the denormalized numeric column reuses the one
  substrate all three verticals triangulate. Over-abstraction at this N —
  revisit only if a vertical genuinely cannot store the band per-entity.
- **Keep supply_chain's scalar `env_band` permanently.** **Rejected:** one
  ceiling judges pharma and frozen alike — wrong verdicts by construction the
  moment ceilings diverge, and the per-cargo divergence IS the cold-chain
  demo's point.
- **A new standalone ADR.** **Rejected:** this discharges a deferral the
  2026-07-11 amendment itself named; the in-place precedent
  (2026-06-25 / 07-01 / 07-05 / 07-09 / 07-11) applies.

#### Scope boundary (amendment — keep it tight)

- **IN:** the scope-extension DECISION (FKP-1), the gate-domain extension +
  corollaries (FKP-2), the zero-executor-change / fail-loud confirmation
  (FKP-3), the supply_chain substrate + first-consumer migration (FKP-4).
  Nothing else.
- **OUT — the build** (a follow-up build PLAN, gated on this `Accepted`): the
  literal `orchestrator.py` / `spec.py`-description edits; the ontology
  property + generator ripple; the YAML migrations; seeds, fixtures, parity +
  regression tests; the stale-docstring fix.
- **OUT (deferred, labelled):** aquaculture per-species floors — needs a new
  numeric property on `Pond` and carries `direction: below` floor semantics;
  lands under this same amendment discipline when scheduled (SD-4). Any
  derived arithmetic (`stock_qty − reorder_point` and kin) — the Q4 wall
  stands: projection/join is select / rename / equi-join ONLY; the band is a
  **stored** column, never a computed one. The per-class lookup grammar
  (SD-2 b). NL-query aggregate convergence (Q4 SD-B's named future question).
- **Inherited LOCKs (carried — must-not-violate):** `ConfigDict
  (extra="forbid")` on `Step` — this amendment adds ZERO new fields (a
  semantics-only extension), which is precisely why it is a G-gated amendment
  and not a build call (the L-4 tripwire covers semantics); **NO LLM in the
  query/evaluate path** — the determinism invariant
  (`evaluate_step.py:14-19`, ADR-0019 / ADR-010 IN-3; read path LOCKED-6 /
  ADR-0024) is untouched — the band's VALUE is per-row governed data, only
  its column NAME is authored spec; `threshold_field` stays **H-governed +
  pinned** (`STEP_GOVERNANCE_FIELDS`, `draft.py:42-59` — a generated skeleton
  may never self-declare a breach floor); the **Q4 wall** (select / rename /
  equi-join only — no derived arithmetic); **Rule-of-Three (ADR-006)** — now
  MET for the FK-parent shape (3 verticals), and honored in the other
  direction too: no over-abstraction past it.
- **UNCHANGED:** the scalar `threshold` path; the TF-1 mutual exclusion; the
  TF-3 trace-to-reads seam mechanics (only its validation DOMAIN widens);
  procurement's shipped same-row consumer (byte-for-byte); `classify_verdict`
  semantics; the ADR-008 ontology grammar; the Q4 join grammar itself
  (`JoinSpec` / `ProjectSpec`, `spec.py:228-320`).

#### Open Questions (SD-1 … SD-5 — Cray ratifies at Proposed → Accepted; do NOT silently resolve)

The **direction is LOCKED** (FK-parent join extension / supply_chain first /
in-place amendment). Five decisions were surfaced; **all five RATIFIED
as-recommended by Cray on 2026-07-12 at Accept (typed, via AskUserQuestion)**
— SD-1 = (a) one build PLAN riding the already-shipped executor (the premise
correction ACCEPTED; the stale docstring is fixed in the build PLAN); SD-2 =
(a) the denormalized `Shipment.temp_ceiling: float` per cargo_type, (b) OUT;
SD-3 = the union-domain rule + g1–g4 confirmed; SD-4 = **build scope =
supply_chain ONLY** (energy = optional / labelled follow-on, NOT in the build
scope; aquaculture = labelled follow-on); SD-5 = env_band → threshold_field
confirmed (facet `in_file_band`). Recorded inline below (each recommendation
now reads as the ratified disposition):

- **SD-1 — join-executor dependency + sequencing (THE decision), with a
  corrected premise.** The dispatch's options: (a) this amendment's build
  PLAN bundles the join-executor build; (b) a separate join-executor build
  PLAN first; (c) a narrower threshold_field-specific parent resolution.
  **Fresh disk evidence corrects the premise:** the executor is ALREADY
  SHIPPED (PLAN-0061 Phase C, PR #666; `_execute_join`
  `query_step.py:458-520` runs the full pinned pipeline; PLAN-0062 put the
  projection half into live procedures) — the "deferred Phase C" framing
  traces to a stale docstring (`orchestrator.py:281-283`; the honest ✖ in
  `0061:450-452` covers unmigrated seeds, not the executor). The genuine
  residue is *first-production-consumer risk*: zero shipped procedure
  declares `join:` yet. *Ratified (as-recommended):* **ONE build PLAN riding
  the shipped executor** — nominally (a), but with the feared executor scope
  already discharged; the join-specific residue is retired by the Q4 SD-C
  parity test on the migrated `read_temps`, and the same PLAN fixes the stale
  docstring. Reject (b) — it would schedule a build for code that exists;
  reject (c) — it duplicates shipped machinery (Alternatives). *Why Cray's
  call:* the premise correction itself + the sequencing pick set the build
  PLAN's size and gating; ratifying SD-1 RATIFIED the corrected premise
  (Code R2 confirmed it on disk at review — no defect).
- **SD-2 — the supply_chain band-property shape.** *Ratified
  (as-recommended):* **(a)**
  a denormalized numeric `Shipment.temp_ceiling: float` seeded per
  `cargo_type` — after which supply_chain is exactly energy's
  numeric-FK-parent shape: ONE substrate, three verticals
  (Rule-of-Three-consistent minimal shape). **(b)** a per-class
  `cargo_type → ceiling` lookup = **OUT** (net-new class-keyed grammar;
  over-abstraction at this N). *Why Cray's call:* it authors new governed
  ontology surface for the flagship demo vertical.
- **SD-3 — the gate-extension seam (FKP-2 g1–g4).** *Ratified
  (as-recommended):* the union-domain rule confirmed (base ∪ joined declared
  properties, tied to
  the step's own declared `join`) + all four corollaries — the fail-closed
  c1/c3 posture carries; the collision gate composes by ordering
  (`orchestrator.py:311-312`); runtime-only collisions keep Q4's
  counted-not-refused posture. *Why Cray's call:* it fixes how hard the load
  gate refuses — the same class of call as TF OQ-1.
- **SD-4 — energy in-scope or a follow-on?** *Ratified (NARROWED by Cray):*
  **build scope = supply_chain ONLY.** All three verticals stay NAMED as the
  Rule-of-Three substrate (Context), but **energy is NOT in the build scope**
  — an optional, labelled follow-on (the drafter's optional-second-migration
  step gate was NOT adopted): cheap on paper (`rated_current_a` exists) but
  NOT free — the FKP-3 fail-loud discipline makes its partially-populated
  band column a step-failing config without a narrowing `where` or seed
  completion, plus the `site_id` collision rename; **aquaculture = a labelled
  follow-on** (needs the new per-species property + floor-direction
  semantics). *Why Cray's call:* a demo-scope / build-size trade-off.
- **SD-5 — the supply_chain judge migration.** *Ratified (as-recommended):*
  **confirm**
  `env_band` → `threshold_field` (the exact analogue of procurement's
  scalar → field migration in the 2026-07-11 change surface), with the facet
  moving to `in_file_band` (the TF OQ-4 kept taxonomy); keep the AC-2-style
  regression that the remaining band-less `env_band` judge (energy, if not
  migrated under SD-4) still loads + runs; assert the demo-visible per-cargo
  verdict deltas in fixtures rather than discovering them. *Why Cray's call:*
  it changes the flagship demo's visible behavior.

#### Amendment references

- The 2026-07-11 `threshold_field` amendment (this file, above) — TF-1
  mutual exclusion; TF-2 same-row wall + the deferral this amendment
  discharges; TF-3 c1–c4 seam; TF-4 run semantics; OQ-4 `in_file_band`
  taxonomy; the procurement migration precedent in its change surface.
- The Q4 join amendment (2026-07-09, this file, above) — SD-A declared-link
  default, SD-B two-shape scope, SD-C parity-guarded migration, SD-D typed
  `foreign_key` promotion; the select/rename/equi-join-only wall.
- `docs/plans/done/0061-join-projection-grammar-build.md:3` — Phase C
  compile/execute landed (PR #666); `:414` (Step 3 = Phase C); `:450-452` —
  the honest residual ✖ (unmigrated seeds, not the executor).
- `services/engine/procedures/orchestrator.py:281-283` (the STALE Phase-C
  docstring — change-surface item), `:311-312` (gate ordering: join/collision
  checks before the threshold gate), `:350-386`
  (`_validate_threshold_field_bindings`; `:374-375` the base-read-only
  domain FKP-2 widens), `:403-458` (`_validate_join_project`), `:461-467`
  (the declared-collision refusal + join-key exemption).
- `services/engine/procedures/query_step.py:145-165` (`JoinReadPlan` + the
  pinned pipeline order), `:458-520` (`_execute_join` — the shipped
  executor), `:522-581` (`_apply_join`: keyed inner + fuse), `:583-603`
  (`_merge` base-wins + counted runtime collisions), `:605-646`
  (`_latest_per_group`).
- `services/engine/procedures/evaluate_step.py:14-19` (determinism
  invariant), `:49-68` (`_entity_number` fail-loud numeric discipline),
  `:87-93` (band-less guard), `:103-109` (per-row band resolution — why the
  executor needs zero change), `:131-139` (audit records `threshold_field`).
- `services/engine/procedures/spec.py:796-801` (the `threshold_field` field —
  its "same-row" description string is the only spec.py touch), `:835-845`
  (the TF-1 invariants, unchanged), `:228-320` (`JoinSpec` / `ProjectSpec`,
  unchanged).
- `services/engine/procedures/draft.py:42-59` (`STEP_GOVERNANCE_FIELDS`,
  `threshold_field` at `:47`), `:285-288` (`derive_governance_todo` already
  band-aware) — zero-change, verified.
- `verticals/energy/ontology/energy_v0.yaml:40-44` (`rated_current_a`),
  `:54-57` / `:110-112` (the `site_id` declared collision), `:107-109`
  (the `asset_id` ref), `:205-209` (`event_emitted_by_asset`);
  `verticals/energy/procedures.yaml:64-75` (the band-less `env_band` judge).
- `verticals/supply_chain/ontology/supply_chain_v0.yaml:39-41` (`cargo_type`),
  `:53-56` / `:116-118` (the `facility_id` declared collision), `:113-115`
  (the `shipment_id` ref), `:123` (the declared `join_path`);
  `verticals/supply_chain/procedures.yaml:47-55` (`read_temps` — projection,
  not join), `:65-76` (the `env_band` judge that migrates).
- `verticals/aquaculture/ontology/aquaculture_v0.yaml:34-36` (`species`);
  `verticals/aquaculture/procedures.yaml:64-76` (`read_do`), `:87-107` (the
  one-floor-for-every-pond scalar judge).
- ADR-006 (Rule-of-Three) — MET at N=3 for the FK-parent shape; ADR-0019 /
  ADR-010 IN-3 — the determinism invariant carried; ADR-008 — the ontology
  grammar untouched by a plain new property.

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

### D3 Amendment (2026-06-11): `watch` → `gated`-proposal routing path → see ADR-0019

D3 is **extended** (not reversed, superseded, or renumbered) by **ADR-0019 —
`watch → gated`-proposal routing path** (Accepted, Cray-ratified 2026-06-11): the
deterministic `watch` (ambiguous-data) object set MAY route to a **`gated`
`action` proposal** (an LLM proposes a `RecommendedAction` → the run suspends at
`waiting_human` (D4) → a human approves/rejects via the existing gate) as a
**sanctioned alternative** to a bare `human_task`. The routing trigger is the
engine-computed deterministic verdict (`breach`/`watch`/`ok`), **never** the LLM's
`confidence` (ADR-010 IN-3). No new primitive; the `auto`/`gated` model,
`autonomy_ceiling`, and handler allowlist are unchanged. Consuming plan:
PLAN-0022 (Ready), § Execution Order Phase 0 (the CLAUDE.md §8 gate that ADR-0019
satisfies). **See ADR-0019 for the full decision.**

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
| 4 | `human_task` → **`gated` `action` proposal** *(amended 2026-06-11 — see **ADR-0019**; PLAN-0022 SD-1=a replaces the `human_task` for v1)* | For the **watch** SET: propose a precautionary `RecommendedAction` → suspend at `waiting_human` → technician approves/rejects a concrete recommendation. *(Pre-amendment: a bare offline visual-check `human_task`.)* |
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
- **OQ-2 (`schedule` reuse) — RESOLVED (ADR-0028, Accepted 2026-07-07).** Does the
  `schedule` trigger reuse the existing PLAN-0010 autonomy / recovery loop
  machinery, or does Phase-1 introduce a separate scheduler? **Resolved: a
  separate, purpose-built scheduler** — a long-lived worker/daemon (ADR-0028 SD-1);
  PLAN-0010 reuse was rejected as a category mismatch. (Phase-1 has only `manual` +
  `schedule`; event/Alert is the Phase-0 path.) Built by PLAN-0055 (S1).
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
