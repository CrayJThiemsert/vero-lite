# ADR-010: LLM Reasoning-Hook Surface

**Status:** Accepted
**Date:** 2026-05-22
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-007 (OCT engine contracts — D2 RecommendedAction envelope [unchanged], D4 layer ownership), ADR-001 (LLM model baseline), ADR-002 (network topology — MS-S1 MAX local LLM server), ADR-009 (Cowork-as-Tier-1 + K-1/K-2 workflow; T7 earmark shifting the LLM-reasoning-hook slot to ADR-010), CLAUDE.md §6 (Decision Flow) + §8 (AI-assistive + data residency); grounding research `docs/research/private/2026-05-21-llm-reasoning-hook-design.md` and `docs/research/private/2026-05-22-llm-reasoning-hook-local-models.md`

## Context

PLAN-0005 Phase 2 (OCT Engine Runtime Layer, merged — PR #4, merge commit
`c646bab`) shipped a deliberately **rule-based** recommender. The
governing intent (recommender.py OQ-3) was "prove the pipe runs, then swap
the brain": `services/engine/recommender.py::recommend()` applies a single
deterministic threshold rule (reading ≥ `OVERTEMP_THRESHOLD_CELSIUS`) and
emits a `RecommendedAction` envelope (ADR-007 D2) wrapped in an
`ActionRecord` at status `proposed`. The read → recommend → approve →
execute loop runs end-to-end on the energy vertical with real persistence.

The documented next step (PLAN-0005 §8.1 revisit register, row 1; restart
bridge `2026-05-21-1900-code-plan0005-phase2-close-restart-bridge.md` §3)
is the **brain swap**: replacing the rule recommender with an LLM. This
ADR fixes the **surface** of that swap — the five decisions that determine
how an LLM plugs into the existing contracts — so a subsequent PLAN-0006
can execute against a settled design.

This ADR specifies **policy and surface**, not implementation. The
ADR-007 D2 `RecommendedAction` envelope **does not change** (it was
defined production-grade precisely so the LLM hook could populate it
without a schema revision). What changes is *who/what fills the envelope*
and *how the fill is constrained, traced, and guarded*.

### Forces at play

- **Data residency (CLAUDE.md §8).** Local LLM on MS-S1 MAX (ADR-002) is
  the default; Claude API is permitted only with consent on non-PII data.
  The energy vertical's data is synthetic and non-PII, so both are
  technically viable — making D1 a deliberate strategic call, not a
  forced one.
- **AI is assistive (CLAUDE.md §8).** AI output is "assistive — never
  auto-diagnostic". The recommender *proposes*; a human *approves*.
- **Structured-output reliability vs reasoning.** Constrained decoding
  guarantees a schema-valid envelope but interacts badly with model
  "thinking" modes (research §3.4; and concretely at the Ollama layer —
  see D2 and Implementation Notes). This is the load-bearing technical
  catch this ADR folds into a binding resolution.
- **Contained blast radius.** The swap is one function. The approval gate,
  persistence (`services/db/`), API wiring, and the existing test suite
  are designed to be unaffected (D5).

### Routing audit trail (per dispatch + CLAUDE.md §6)

The framing for this ADR was produced in **Cowork** as a Tier-0 research
pass (`2026-05-21-llm-reasoning-hook-design.md`, plus the model/hardware
follow-on `2026-05-22-llm-reasoning-hook-local-models.md`) flowing
directly into this Tier-1 ADR draft, **without** an intervening Chat
free-form discussion step. CLAUDE.md §6 Decision Flow step 1 ("discuss in
Chat free-form") is the **default, not a mandate**; for a fact-grounded
decision already anchored in two cited research files, Cray approved
routing straight from Tier-0 research to the Tier-1 draft. This paragraph
is the routing audit trail; the Chat step remains the default for
decisions that are exploratory rather than fact-grounded.

## Decision

Five decisions (D1–D5). Each states the choice, rationale, and
alternatives. **D1 was the strategic data-residency call reserved for
Cray; it was ratified 2026-05-22 as option A** (local LLM default + a
Claude API consent-gated fallback). D2–D5 are the recommended engineering
choices.

### D1: Inference backend — local LLM default + Claude API consent-gated fallback (Ratified by Cray 2026-05-22: option A)

**Decision (ratified by Cray 2026-05-22 — option A):** the recommender
path uses the **local LLM on MS-S1 MAX** (ADR-002) as the default backend,
with the Claude API available only as an explicit, consent-gated fallback
for cases where local quality is insufficient (mirroring the ADR-001
cloud-fallback posture). The energy vertical's synthetic, non-PII data
means a hosted primary would not violate CLAUDE.md §8 today — so this was a
strategic moat choice, not a compliance gate, and Cray adjudicated it
deliberately.

**Ratification rationale (Cray, 2026-05-22):** local-default keeps data on
the operational hot path inside the residency boundary — which is the moat
(ADR-001) and is **forward-compatible with real design-partner data**,
which will be PII/sensitive (energy + supply-chain operators; the parked
vet-clinic Phase 2 is PII by definition, CLAUDE.md §8). Building a hosted
hot path now would incur a rework + consent debt the moment real partner
data replaces synthetic data. The hosted fallback is retained for hard
cases (consent-gated, non-PII only) and remains available for
**authoring / development-time** use on synthetic data, which does not
touch the runtime residency boundary.

**Rationale:** the local-first capability *is* the data-residency moat
(ADR-001 Alt-2 "cloud as primary defeats the strategy"). Research §2.1 +
the model survey confirm in-envelope open models run on MS-S1 MAX at
usable single-stream throughput (≈40–55 tok/s for 30B–120B-MoE class),
which is adequate for a human-reviewed proposal even under D2's
two-pass/retry cost. Hosted strict-mode APIs are more capable at schema
conformance today (research §3.2), which is the live trade-off.

**Alternatives considered:**
- *Claude API as primary.* Pros: strongest reasoning + strict-mode schema
  conformance, zero local-ops burden. Cons: erodes the residency moat;
  per-token cost; vendor dependency on the operational hot path. *Why not
  (recommendation):* defeats the strategic differentiator; reserved as
  fallback.
- *Local-only, no fallback.* Pros: maximal residency purity. Cons: no
  escape hatch for hard cases. *Why not:* ADR-001 already establishes a
  consent-gated cloud fallback; removing it is stricter than current
  policy requires.

> **D1 ratified by Cray 2026-05-22 = option A** (local default + Claude API
> consent-gated fallback). The other four decisions are backend-agnostic
> and hold under this choice.

### D2: Structured output — JSON-schema-constrained generation + validate-and-retry loop

**Decision:** the LLM returns a valid `RecommendedAction` (ADR-007 D2) via
**JSON-Schema-constrained generation** — the `RecommendedAction` Pydantic
model serialised to JSON Schema and supplied as the generation constraint
(Ollama `format` for the local path; the equivalent strict-mode/tool
schema for the hosted fallback) — wrapped in a **validate-and-retry loop**
(schema validation + a bounded retry feeding the validator error back as
context; Instructor/Pydantic-AI are supported over Ollama). Retries capped
at 2–3 (research §4.2).

**Rationale:** constrained decoding makes a *schema-valid* envelope true by
construction; the retry loop covers the residual semantic and
occasional-malformed cases. The engine already emits JSON Schema
(ADR-008), so no new schema authoring is required — the envelope model is
the schema.

**Binding catch folded in (research §3.4 + brief 3b):** constrained
decoding conflicts with model "thinking" — and concretely, **Ollama issue
#15260** shows that setting `think=false` *together with* a `format` JSON
schema silently disables the schema constraint on some models (gemma4 is
named — and gemma4 is the ADR-001 baseline). The structuring call
**must not** naively combine `think=false` with `format`. This is promoted
from advisory to a **binding pre-implementation verification item** (see
Implementation Notes IN-1) rather than a downstream surprise.

**Alternatives considered:**
- *Function/tool-calling (TOOLS mode).* Pros: ergonomic for small
  extractions; provider re-prompts on malformed calls. Cons: coarser
  control; not guaranteed without strict mode. *Why not (primary):*
  retained as a permissible secondary invocation mode, not the main path
  for the full envelope.
- *Prompt-only + downstream validate.* Pros: simplest. Cons: no
  by-construction guarantee. *Why not:* insufficient reliability for an
  envelope that gates an operational action.

### D3: Reasoning trace — hybrid `llm_inference` + harness-emitted steps, treated as a review artifact

**Decision:** the LLM path populates `RecommendedAction.reasoning_trace`
(already present in ADR-007 D2) with a **hybrid** trace:
- `ReasoningStep(kind="llm_inference")` carrying the model-asserted
  rationale (the new LLM analogue of the rule recommender's
  `kind="rule_check"` steps), and
- harness-emitted `ReasoningStep(kind="ontology_query")` /
  `kind="rule_check"` steps recording what the engine actually did
  (evidence retrieved, thresholds checked).

`AuditMetadata.actor_kind` is set to `"llm"` on the LLM path (the enum
already admits `'engine' | 'llm' | 'human'`). The trace is treated as a
**human-review + audit artifact**, explicitly **not** a guaranteed-faithful
explanation of the model's computation.

**Rationale:** the `kind` enum was authored with `"llm_inference"` already
listed, so the envelope anticipates this. The 2026 faithfulness literature
(research §4.2 — "chain-of-thought is not explainability") warns that a
model's narrated reasoning is often post-hoc rationalisation; pairing the
model's narrative (labelled) with harness-emitted factual steps gives a
trace that is auditable where it counts and honest about where it is
merely model-asserted. This aligns with CLAUDE.md §8 (assistive): the
trace supports the human approver, it does not replace them.

**Alternatives considered:**
- *Model-emitted trace only.* Pros: richest narrative; simplest to
  capture. Cons: lowest fidelity; risks presenting rationalisation as
  fact. *Why not:* unsafe to show an operator as justification without the
  faithfulness caveat.
- *Harness-emitted (infra) trace only.* Pros: faithful by construction
  (it logs real operations). Cons: shallow on "why". *Why not:* loses the
  reviewer-useful narrative; the hybrid keeps both, labelled.

### D4: Guardrail boundary — the existing approval gate is the guardrail

**Decision:** the existing minimal approval gate **is** the guardrail
boundary, confirmed unchanged. The LLM *proposes* (`requires_approval=True`
on every recommendation, as today); a human must `approve()` before
`execute()` runs the registered handler. No new gate is introduced by this
ADR. Defense-in-depth additions (output validation per D2; registry +
range + entity-PK semantic checks; containment of untrusted free-text in
ingested operational data before it reaches the prompt) layer *behind* the
same human-approval boundary.

**Rationale:** this matches both the external consensus and the closest
prior art. OWASP's 2025 LLM Top 10 names human-in-the-loop approval for
consequential/irreversible actions as the primary control against
"Excessive Agency" and prompt injection (research §5); Palantir AIP stages
LLM-generated proposals for human review with an inspectable decision log
(research §6). The engine's `approve()`→`execute()` lifecycle already
encodes exactly this. CLAUDE.md §8 ("assistive — never auto-diagnostic")
makes human approval non-negotiable for the recommender.

**Prompt-injection note (folded):** the novel exposure relative to a
chatbot is that **ingested operational data is the injection surface**
(asset labels, free-text event fields). Containment + least-privilege
handler access + the human gate is the posture; no published technique
fully prevents injection (research §5.3). Treated as a binding design
constraint on the prompt-assembly step (IN-2), not a new gate.

**Alternatives considered:**
- *Auto-execute high-confidence proposals.* Pros: lower latency, less
  human toil. Cons: violates CLAUDE.md §8; removes the OWASP-prescribed
  control. *Why not:* out of bounds for assistive AI.
- *Add a second LLM-judge gate before the human.* Pros: may filter weak
  proposals. Cons: adds a second unfaithful component; complexity. *Why
  not now:* deferred; the human gate is the boundary, an LLM pre-filter is
  an optimisation for a later ADR.

### D5: Swap surface — `recommend()` becomes LLM-backed under the same signature

**Decision:** `services/engine/recommender.py::recommend(event: dict[str,
Any], vertical: str) -> ActionRecord | None` becomes LLM-backed **under the
same signature**. It returns the same `ActionRecord` (status `proposed`,
wrapping the same ADR-007 D2 envelope). The `ActionStatus` lifecycle,
`approve()`/`reject()`/`execute()`, the registry-resolved
`suggested_handler` dispatch, persistence (`services/db/`), and API wiring
are **unaffected**. A **fail-safe** is required: if the LLM path fails
after the D2 retry budget, `recommend()` falls back to a deterministic
result (the existing rule path) or returns `None` — it never raises into
the runtime loop.

**Confidence handling (folded):** the rule path hard-codes
`RULE_CONFIDENCE = 0.8`. A model-reported confidence is poorly calibrated
(research §3.4/§4.2); on the LLM path, `confidence` is treated as
**advisory only** and surfaced to the human reviewer as such, not used to
gate automation (consistent with D4). Whether to derive confidence
externally is left to PLAN-0006 / a future ADR.

**Rationale:** containing the swap to one function with an unchanged
signature is what makes the "swap the brain, keep the pipe" intent (OQ-3)
real: the blast radius is one function and its prompt-assembly + parsing
helpers. The unchanged envelope (ADR-007 D2) and unchanged gate (D4) mean
existing tests for the lifecycle remain valid.

**Alternatives considered:**
- *New function / endpoint for the LLM path.* Pros: clean separation.
  Cons: forks the call path; duplicates wiring; breaks the "same pipe"
  containment. *Why not:* the signature is already the right seam.
- *Change `ActionRecord` / envelope for LLM output.* Pros: could carry
  LLM-specific fields. Cons: ADR-007 D2 is deliberately stable and
  production-grade. *Why not:* the envelope already carries everything
  needed (`reasoning_trace`, `confidence`, `audit_metadata.actor_kind`).

## Consequences

### Positive

- **Zero envelope churn.** ADR-007 D2 stays fixed; the LLM hook populates
  existing fields (`reasoning_trace`, `confidence`, `audit_metadata`).
- **Contained blast radius.** One function changes (D5); gate, persistence,
  API, and lifecycle tests are untouched.
- **Guardrail already in place** (D4): the approval gate the engine shipped
  in Phase 2 is the OWASP/AIP-aligned control; no new safety surface to
  build before the swap.
- **The load-bearing technical catch is surfaced now** (D2/IN-1), not
  discovered mid-implementation — the think/format interaction is a
  pre-implementation verification item.

### Negative

- **Non-determinism enters the recommender.** Phase 2's deterministic unit
  tests no longer fully characterise `recommend()`; an eval strategy is
  needed (see Risks + follow-on T3).
- **Latency + ops cost.** Constrained generation + a retry loop (and, if
  D3's hybrid trace uses a separate reasoning pass, a second call) cost
  more than the rule path. Acceptable for a human-gated proposal but real.
- **Backend ops burden if local (D1).** The MS-S1 MAX serving path on
  gfx1151 is version-sensitive (research brief 3b §2.2); a serving-config
  runbook item is implied.

### Neutral

- **D1 left open for Cray.** The other four decisions are backend-agnostic
  and hold either way.
- **Confidence semantics narrowed to advisory** (D5) rather than removed —
  the field stays in the envelope; only its automation role is constrained.

### Risks

- **Trace faithfulness** (D3): if an operator over-trusts the
  `llm_inference` narrative, the labelling discipline is the only mitigation
  short of a faithfulness audit (research §4.2). Regression trigger:
  reviewers treating the narrative as verified fact.
- **think/format interaction** (D2/IN-1): if unverified, the structuring
  call can silently emit unconstrained output. Mitigated by IN-1 as a
  required pre-implementation check.
- **Prompt injection via operational data** (D4/IN-2): no full prevention;
  containment + human gate only.
- **Eval gap**: a stochastic `recommend()` needs an eval suite (cf.
  Palantir AIP Evals, research §6.3); absence is a quality risk, not a
  correctness one given the human gate.

### Reversibility

Fully reversible. Because D5 keeps the signature and D4/ADR-007-D2 keep the
gate and envelope, reverting to the rule recommender is reinstating the
deterministic `recommend()` body — no contract unwind. D1 was ratified by
Cray 2026-05-22 (option A); the ADR is Accepted pending Code's commit
(ADR-009 D2).

### Required follow-on commits (TODOs for Code — separate commits)

This ADR is an uncommitted draft (ADR-009 D2: only Code commits). None of
these edits are made here:

1. **T1 — Commit this ADR** to `docs/adr/0010-llm-reasoning-hook-surface.md`
   at status `Accepted` (D1 ratified by Cray 2026-05-22 = option A).
2. **T2 — Author PLAN-0006** (the execution plan for the swap) once this
   ADR is accepted: Goal, Acceptance Criteria, Out of Scope, Steps —
   per CLAUDE.md §6 Plan Flow. PLAN-0006 owns the *how* (prompt assembly,
   parsing, retry wiring, fallback); this ADR owns the *what/surface*.
3. **T3 — Eval strategy** for a non-deterministic `recommend()` (eval suite
   / golden-trace fixtures) — scope in PLAN-0006 or a follow-on; the
   action-approval/audit framework remains earmarked ADR-011+.
4. **T4 — Update `docs/STATUS.md`** Recent Decisions + Next Steps with
   ADR-010 and the PLAN-0006 hand-off.

## Alternatives Considered (cross-cutting)

### Alternative 1: Defer the swap; keep the rule recommender for now

- **Pros:** zero risk; deterministic tests stay authoritative.
- **Cons:** the rule path was always explicitly a scaffold (OQ-3); deferring
  indefinitely strands the moat work (reasoning-driven recommendations).
- **Why rejected:** the swap is the documented next step; this ADR de-risks
  it by fixing the surface before code is written.

### Alternative 2: Specify the full implementation in this ADR

- **Pros:** one document.
- **Cons:** mixes abstraction levels (policy/surface vs prompt/parsing
  mechanics); harder to revise atomically (the ADR-007 Alt-3 reasoning).
- **Why rejected:** surface in the ADR, mechanics in PLAN-0006 — consistent
  with the project's ADR→PLAN→Code flow.

### Alternative 3: Introduce the action-approval/audit framework here too

- **Pros:** self-contained safety story.
- **Cons:** that framework is separately earmarked (ADR-011+; ADR-007
  Consequences); the existing minimal gate (D4) is sufficient for the swap.
- **Why rejected:** scope separation; D4 confirms the current gate is the
  boundary for now.

## References

- **Grounding research (Tier-0, this effort):**
  `docs/research/private/2026-05-21-llm-reasoning-hook-design.md` (§2
  local serving, §3 structured output + §3.4 grammar/thinking conflict, §4
  reasoning-trace faithfulness, §5 OWASP guardrails, §6 Palantir AIP, §7
  decision surface) and
  `docs/research/private/2026-05-22-llm-reasoning-hook-local-models.md`
  (§2 MS-S1 MAX throughput + serving path, §3/§4 candidate models, §4.1
  Ollama `think`/`format` bug #15260, §5 Pattern-B configs)
- **ADR-007** (`docs/adr/0007-oct-engine-contracts.md`) — D2
  `RecommendedAction` envelope (unchanged here; `ReasoningStep.kind`,
  `AuditMetadata.actor_kind` enums), D4 layer ownership
- **ADR-001** (`docs/adr/0001-llm-model-baseline.md`) — pinned baseline
  (`gemma4:26b`, `qwen2.5-coder:32b`); cloud-fallback posture (D1)
- **ADR-002** (`docs/adr/0002-network-topology.md`) — MS-S1 MAX local LLM
  server (`http://ms-s1-max:11434`), data-residency LAN boundary
- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — Cowork
  Tier-1 authorship + D2 commit boundary + D3 K-1/K-2 workflow; T7
  earmark shift to ADR-010
- **Swap surface:** `services/engine/recommender.py`
  (`recommend()` signature, `RULE_CONFIDENCE`, `ActionStatus`,
  `approve()`/`execute()` gate)
- **CLAUDE.md** §6 (Decision/Plan Flow — routing audit trail), §8
  (AI-assistive + data residency)

## Implementation Notes

For PLAN-0006 / Code. Cowork has no commit authority (ADR-009 D2); Code
reviews and commits this file and the T1–T4 follow-ons.

- **IN-1 (binding) — verify the `think`/`format` interaction before relying
  on it.** Per Ollama issue #15260, `think=false` + `format` (JSON schema)
  silently disables the schema constraint on some models (gemma4 named —
  the ADR-001 baseline). PLAN-0006 must pin a model + Ollama version and
  *test* that the structuring call (D2) actually constrains output; if it
  does not, omit `think` (accept thinking latency) or use a model whose
  structured-output path is verified (research brief 3b §4.1/§5).
- **IN-2 (binding) — isolate untrusted operational text** in prompt
  assembly (D4): free-text fields from ingested events must be segregated/
  labelled, never concatenated with system-instruction authority; least-
  privilege handler/registry access so a compromised prompt cannot reach
  an unintended handler.
- **IN-3 — confidence is advisory** on the LLM path (D5); surface to the
  reviewer, do not gate automation on it.
- **IN-4 — fail-safe** (D5): LLM failure after the retry budget falls back
  to the rule path or returns `None`; never raise into the runtime loop.
- This ADR was drafted by Cowork (Tier-1, ADR-009 D1) from Tier-0 research,
  per the Cray-approved routing recorded in Context. Per K-1, Cowork could
  not run `validate_handoff.py`; the companion completion handoff records
  the mental-validation substitute and flags the gap. AI-assisted per
  project convention.
