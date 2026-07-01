# ADR-016: Governed Procedure Engine — expand the action layer from `anomaly→action` to `anomaly AND normally→action`

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-005 (strategic pivot to OCT — **expands feature-3**), ADR-007 (OCT engine contracts — **generalizes** the D2 `RecommendedAction` envelope; does **not** break it), ADR-008 (YAML ontology spec — the six `object_types` are **untouched**; `procedures.yaml` is a separate spec layer), ADR-001 (LLM model baseline — the local `gpt-oss:20b` pin is the default `Agent` model), ADR-010 (LLM reasoning-hook surface — the per-action reasoning trace generalizes to per-step), ADR-013 (autonomy-axis relocation — safe / human-gated autonomy posture). Implementation deferred to **PLAN-0019**. Grounding research: `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md` (5 Palantir findings, 25 claims 3-0 / 0 killed), `docs/research/private/2026-06-06-impl-approach-reconciliation.md` (on-thesis framing). This ADR does **not** supersede any prior ADR.

**Amendments:** D3 Amendment (2026-06-11) → ADR-0019 (`watch → gated`-proposal routing). **D2 Amendment (2026-06-25)** → first-class typed `facet:` Step field (**Accepted** 2026-06-25 — Cray-ratified). **D2 + D3 Amendment (2026-07-01)** → typed read-side ontology object-binding for query steps (Q3) (**Proposed** — awaiting Cray ratification).

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

> **Status:** **Proposed** (awaiting Cray ratification). **Date:** 2026-07-01.
> **Deciders:** Jirachai Thiemsert (founder) — to ratify. **Amends:** D2 (the
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
> interim authoring). Independent reviewer = Code R2-review at commit + Cray at
> ratification (Proposed → Accepted). The drafter is not the ratifier —
> separation **intact**.

#### Context for the amendment

D2/D3 gave the write side of the procedure engine real governance: an `action`
step is `gated` by default (D3), its blast radius is bounded by
`Agent.allowed.action_handlers` (enforced at run time — the engine refuses to
invoke a handler the agent is not allowlisted for), and the `RecommendedAction`
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
the **write** side and **is** enforced at run time. There is **no `object_types`
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

The read side gets **governance parity with the write side**, delivered
**contract-first**: type the binding + add the allowlist + **gate at LOAD time**
now (low-risk, no runtime data-flow change), and **defer** the generic
run-consume executor to a fast-follow PLAN.

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
get **read-side governance parity at low risk now** (author + validate +
load-gate), and **consume later** (the run-consume executor is a fast-follow). The
`object_types` allowlist is also the **foundation for future read-side audit /
PDPA** (PLAN-0005 §8.1) — an agent's declared read reach becomes an auditable,
enforced fact rather than an implicit adapter capability.

#### `spec.py` delta (illustrative — the follow-on PLAN owns the literal edit)

```python
# Q1 — the read entry point on StepInput (OQ-1 recommendation; extra="forbid" kept):
class StepInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_step: str | None = Field(default=None, alias="from")  # UNCHANGED — intra-run thread
    where: dict[str, Any] | None = None                        # UNCHANGED — post-fetch filter (OQ-4)
    reads: str | None = Field(                                 # NET-NEW — data-sourcing entry point
        default=None,
        description="ontology object_type this query step reads (must exist in the vertical's "
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
change**: for each `kind == query` step with `input.reads` set, assert
`reads ∈ vertical_object_types` **and** `reads ∈ agent.allowed.object_types`, else
refuse to load.

#### Scope boundary (amendment — keep it tight)

- **IN:** the **typed read-side binding** (Q1) + the **`object_types` allowlist**
  (Q2) + the **load-time enforcement** (Q3). Read-side governance parity, contract
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
  the marker is the self-cancelling trigger to re-open it at N ≥ 3.
- **OUT:** connectors-in-the-procedure (LOCKED — the mapping layer absorbs source
  diversity, Cray s84); any change to how the adapter is selected
  (`run_procedure`'s vertical string, ambiguity #2); any change to `from_step`
  input-binding, `kind`, `autonomy`, gates, or the D2 `facet` schema (all
  unchanged).

#### Open Questions (for Cray ratification)

- **OQ-1 (field placement).** `StepInput.reads` sub-field **(recommended** — the
  read entry point sits beside the existing `from`/`where` input grammar; one
  cohesive input model) **vs** a top-level `Step.reads`. Both keep
  `extra="forbid"`; the difference is where the read binding conceptually lives.
- **OQ-2 (v1 depth).** author + validate + **load-gate (recommended** — real
  read-side governance now, zero runtime-data-flow risk) **vs** full run-consume
  (delivers the executor now but touches the hero-demo/live data flow and the
  enrich/join steps — higher risk, defeats contract-first) **vs**
  validate-only-no-enforce (types the binding but adds **no** actual read-gate —
  documents the gap without closing Gap (B), so no governance parity). The
  recommendation buys the governance parity at the lowest blast radius.
- **OQ-3 (allowlist verb scope).** Does `Agent.allowed.object_types` gate
  `stream_events` / `fetch_links` too, or only `fetch_objects`-style reads in v1?
  **Recommendation: all read verbs in principle** (the allowlist is a read-reach
  bound, not a fetch-verb bound); **v1 enforcement scope = the query-step object
  binding** (Q3), with events/links folding in when the executor lands (Q4).
- **OQ-4 (`reads` ↔ `input.where`).** Is `where` still the **post-fetch**
  narrowing over the fetched object set? **Recommendation: yes** — `reads` names
  **what** to fetch (the object_type); `where` stays the **field-equality filter
  over the fetched set** (unchanged from `_matches` / `_resolve_input`), so the
  set-valued fan-out semantics are preserved.

#### Consequences

- `StepInput` gains a typed optional **read entry point** (Q1) and `AgentAllowed`
  gains a typed **read allowlist** (Q2); both keep `extra="forbid"`.
  **Backward-compatible**: a query step without `reads` and an agent without
  `object_types` load exactly as today (every shipped procedure + hero-demo still
  loads — the load-gate only fires when `reads` is set).
- The read side reaches **governance parity** with the write side: an agent's
  read reach becomes a **bounded, enforced, auditable** fact (Gap B closed at
  load time), symmetric with `action_handlers`.
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
