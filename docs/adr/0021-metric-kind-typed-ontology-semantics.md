# ADR-0021: Metric-kind as typed ontology semantics ("classify, don't synthesize")

**Status:** Proposed
**Date:** 2026-06-15
**Deciders:** Jirachai Thiemsert (founder) — construct choice (D2) confirmed at ratification
**Related:** ADR-008 (YAML ontology specification — D3 grammar, D5 generator, D6 validation; this ADR amends D3), ADR-006 (vertical plugin architecture / Rule of Three), ADR-005 (OCT pivot — energy first), ADR-007 (OCT engine contracts), PLAN-0026 (steps 6–7, AC-8, SD-2, IN-1 — the gated implementation), PLAN-0024 (deterministic aggregates + `resolve` join — its residual this closes), `benchmarks/nl_query_feasibility/RESULTS.md` (2026-06-15 addendum — the proven-negative evidence), `docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md` (the moat argument + external citations), CLAUDE.md §1 (semantic layer = the moat), ADR-009 D1/D2 (Cowork drafts, Code commits), ADR-012 D4.3 (author≠reviewer disclosure)

> **Authoring disclosure (ADR-012 D4.3).** Drafted by Cowork (Tier-1, ADR-009 D1)
> from Code's session-61 dispatch. The substantive argument is lifted from a
> **Cowork (Tier-0) research output** —
> `docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md` — so the
> research-author and this ADR-author sit in the **same tier**; the
> independent-deliberation check is therefore **not** exercised at authoring time.
> **Code's review at PR merge + Cray's ratification are the remaining independent
> checks.** Separation noted, not asserted.

> **Construct choice is a lean, not final (D2).** Cray leans option (b) (a
> QUDT-style quantity-kind ⟂ unit typed pair). This is drafted as the **Proposed**
> construct; (a) and (c) are recorded as considered alternatives. **The construct
> choice is the load-bearing decision Cray confirms at ratification** (the
> Proposed → Accepted step). Until then it is tentative.

## Context

vero-lite's second OCT feature is grounded natural-language (NL) query: an
operator asks a plain-language question and gets an answer **from real ontology
data, never from the model's memory**, via a deliberately three-staged pipeline
(`services/engine/nl_query.py`): **translate** (LLM → a bounded `StructuredQuery`)
→ **execute** (deterministic, no LLM — filters, counts, aggregates in plain code)
→ **phrase** (LLM over only the retrieved records). The load-bearing property is
**12/12 anti-hallucination**: every fact comes from deterministic execution, and
an empty result short-circuits to a fixed "no records" answer.

One residual failure class survives PLAN-0024's enrichment: **filter-omission on
aggregate superlatives** (the spike's nl-08 / nl-11). Asked *"What is the highest
temperature reading, and on which battery?"*, the translate stage emits
`filters:[]` and aggregates `max(measured_value)` over **all** events instead of
the 7 celsius readings, and drops `group_by:asset_id`. The headline number comes
out right **only by luck** (the two `hz` readings at 50.0 sit below the celsius
max); the `top` entity in the answer is the *phrase step's prose*, not the
structured aggregate. At partner data volumes this over-broad fetch blows the
token budget, hits the phrase-stage truncation cap, and dilutes the grounding
receipt.

**The two obvious fixes are PROVEN NEGATIVE** (`RESULTS.md`, 2026-06-15 addendum —
the load-bearing evidence):

- **Model swap is falsified.** A 4-family sweep (`gpt-oss:20b` pin,
  `nemotron-3-nano:30b`, `qwen3.6:35b`, `gemma4:26b`) **all dropped the implied
  filter** on the superlatives (`filters:[]` → all 11 events instead of the 7
  celsius readings); `group_by` was flaky across all four; the larger models were
  **2.5–6× slower**; the dense 26B was the worst (invented a `resolve` to an
  un-named entity, failed a coherent named-entity aggregate after 3 retries). The
  omission is **model-class-general**.
- **Prompt tuning is falsified.** A 3-variant escalation on the pin: a general
  "an aggregate still needs its implied filter" rule had **no effect**; a
  units-coherence rule **regressed** (the model emitted a filter but invented a
  bogus `resolve` placeholder → empty → honest-but-wrong no-data); only a
  near-answer few-shot moved it, flakily (1/2), which is **teaching to the test**.

**The corrected diagnosis is a data-model problem, not an AI problem.** In
`verticals/energy/ontology/energy_v0.yaml`, `OperationalEvent` carries
`measured_value: float` and `unit: string`. `measured_value` is a
**unit-heterogeneous column** — 96.5 (celsius) and 50.0 (hz) live in the same
float — so aggregating across it is physically meaningless, and the schema gives
the model **no metric-kind discriminator** to bind the word "temperature" to. The
model is being faithful to an underspecified schema. This is the classic
Entity-Attribute-Value "one big value column" anti-pattern; the QUDT standard's
answer is to model the **quantity kind** (what is measured) separately from the
**unit** (how it is measured); Palantir Foundry's **value types** make the same
move at the operational layer. (All argued, web-researched and cited, in the
pattern article; two strong external LLMs independently converged on the same
data-model root-cause framing.)

PLAN-0026 splits the fix in two phases. **Phase B** (engine-only, ships first, no
governance gate) adds a deterministic post-translate rewrite seam with a
**best-effort** coherent-unit determination (IN-1) — it derives the coherent unit
from the matched set itself. **Phase A** (this ADR's subject, GATED) declares
metric-kind as a first-class ontology concept so the engine consumes a
**principled** declared binding instead of a best-effort heuristic. Phase A's impl
PR is gated on (a) the T2-vs-T3 roadmap go and (b) **this ADR being Accepted before
the impl PR** (CLAUDE.md §8).

**Why a new ADR rather than amending ADR-008 in place (PLAN-0026 SD-2).**
Metric-kind-as-typed-semantics plus the "classify, don't synthesize" principle is
a **distinct architectural decision** with substantial independent rationale (the
falsified model/prompt fixes, the EAV / unit-heterogeneity root cause, the QUDT
quantity-kind-vs-unit separation, the Foundry value-type precedent) and deserves
its own citation anchor. It **extends** the modeling approach rather than
correcting ADR-008. The binding construct (D2) does, however, touch the grammar,
so this ADR **explicitly amends ADR-008 D3** (see D2).

## Decision

### D1: `measured_kind` becomes a first-class ontology concept on `OperationalEvent`

`OperationalEvent` gains a `measured_kind` enum property
(`temperature | frequency | voltage | …`, extensible per vertical), declared in
each vertical's `<name>_v0.yaml`. The **enum field itself needs no grammar
change**: `type: enum` already fits **ADR-008 D3** and the existing generator
emits it across all five artifacts unchanged — `Literal[...]` Pydantic, a
`TEXT CHECK (...)` SQL constraint, JSON Schema `enum`, MCP tool enum, and a
TypeScript union (ADR-008 D5). What is *new* in this ADR is the **binding** below,
not the field.

### D2: The kind↔unit binding is declared DECLARATIVELY in the ontology — PROPOSED construct: option (b), a QUDT-style quantity-kind ⟂ unit typed pair

The mapping `temperature → celsius`, `frequency → hz`, … is declared **in the
ontology**, not in engine or data-adapter code. The engine reads it from ontology
meta (`OntologyMeta` / `ObjectTypeMeta`); it is never hardcoded.

**Proposed representation (option (b) — modeled on QUDT).** Treat `measured_kind`
(the *quantity kind* — what is measured) and `unit` (how it is measured) as a
**typed pair** governed by a declared compatibility/binding table at the object-type
level — a new grammar construct beyond ADR-008 D3's per-property data types. The
illustrative shape (exact syntax confirmed at ratification):

```yaml
object_types:
  OperationalEvent:
    properties:
      measured_kind:
        type: enum
        values: [temperature, frequency, voltage]
      measured_value:
        type: float
      unit:
        type: string
    # NEW construct (this ADR): declared quantity-kind ⟂ unit binding.
    # The engine reads this from ontology meta; code never hardcodes it.
    quantity_bindings:
      - kind: temperature
        unit: celsius
      - kind: frequency
        unit: hz
      - kind: voltage
        unit: volt
```

**This is the load-bearing decision Cray confirms at ratification** (lean, not
final — see the header note). Rationale for leaning (b): it is the closest fit to
the **real comparative-measurement pipeline task** (metrics compared to drive
operational decisions), it matches the QUDT quantity-kind-vs-unit separation and
the Foundry value-type precedent argued in the pattern article, and it **extends
cleanly to option (c)** (a typed measurement composite) later without re-deciding
the model.

**ADR-008 impact (stated explicitly, per SD-2 caveat):**

- **Amends ADR-008 D3 grammar.** The `quantity_bindings` construct is a new
  object-type-level grammar element that D3 (per-property data types only) does
  not currently express. ADR-008 D3 is therefore **amended** by this ADR to admit
  the binding construct. The per-property `enum` type table in D3 is **unchanged**
  — only the new binding block is added.
- **Generator impact (ADR-008 D5).** The generator must carry the declared
  bindings into engine-consumable ontology meta (`OntologyMeta` / `ObjectTypeMeta`)
  so the execute stage can read them. Whether the binding also surfaces in the
  five generated artifacts (e.g. as JSON-Schema / MCP-tool metadata) or only in
  the in-process ontology meta is an **implementation detail for Code** (PLAN-0026
  step 6) — flagged, not fixed here.
- **Validator impact (ADR-008 D6).** L2 semantic validation gains a check: every
  `measured_kind` enum value referenced by `quantity_bindings` exists in the enum
  and binds to exactly one unit, and every bound unit is consistent with the
  declared `unit` value space. L1 (JSON Schema) gains the binding construct's shape.

### D3: Principle — "classify, don't synthesize"

The translate LLM **classifies** the bounded `measured_kind` enum (a constrained
selection over a known space — the operation LLMs are reliable at). The engine
**deterministically synthesizes** the precise `unit` filter (and the canonical
unit for the aggregate) from the declared binding (D2). **No LLM filter
synthesis; no brittle keyword→value map in code.** The model picks; code composes.

This **preserves the 12/12 anti-hallucination guard** — every fact still comes
from deterministic execution, and the existing empty → fixed-no-data short-circuit
plus PLAN-0026's clarification guard remain intact. It **supersedes Phase B's
best-effort "coherent unit derived from the matched set" heuristic** (PLAN-0026
IN-1): Phase B's rule works for temperature but cannot in general distinguish, e.g.,
"highest **frequency**" from "highest **temperature**" without a declared kind. Once
`measured_kind` is declared and classified, the engine synthesizes the precise unit
filter from the binding rather than guessing it from the data.

### D4: Scope — this ADR decides the MODEL, not the implementation

ADR-0021 decides **the model**: the construct (D2) plus the "classify, don't
synthesize" principle (D3). The **implementation is PLAN-0026 steps 6–7**, gated on
this ADR being Accepted (CLAUDE.md §8). This ADR is **not** a wholesale translate
redesign — classification is introduced for `measured_kind` **specifically**, not
for all properties. A full classify-only translate stage is a PLAN-0026
Out-of-Scope Phase-3 idea, explicitly not decided here.

## Consequences

### Positive

- The **ontology becomes the single source of truth for metric semantics** — the
  CLAUDE.md §1 moat thesis instantiated for the metric-semantics gap. Declare the
  kind once and "highest temperature" / "lowest voltage" become well-posed for
  every downstream consumer (NL engine, generated SQL DDL, API contracts).
- **New metric kinds and new verticals extend by data, not code.** Add
  `voltage`/`pressure`, or a `supply_chain` / `aquaculture` ontology carrying the
  same `OperationalEvent {measured_value, unit}` shape, by declaring a binding —
  no engine change (Rule of Three, ADR-006).
- **Anti-hallucination compounds rather than being traded away** (contrast raw
  text-to-SQL, which gained expressiveness but lost the safety property —
  PLAN-0024). The model only classifies; code composes; ambiguity routes to the
  clarify guard.
- **"Classify, don't synthesize" is a reusable reliability principle** — anywhere
  the engine currently asks the model to invent a structured value, the same move
  applies (declare the space, model picks, code composes).

### Negative

- **A new grammar construct + generator/validator support is required** (the
  `quantity_bindings` block; ADR-008 D5/D6 work) — a real, if bounded, cost in
  PLAN-0026 step 6.
- **ADR-008 D3 is amended**, so ADR-008 is no longer a single self-contained
  ontology-grammar source; readers must follow the amendment pointer.
- Construct (b) is **heavier than option (a)** (a per-enum-value attribute map);
  if the comparative-measurement / composite trajectory does not materialize, (b)
  carries more grammar surface than the immediate need strictly requires.

### Neutral

- The `measured_kind` **enum field** rides entirely on existing ADR-008 D3 + D5
  machinery; only the **binding construct** is new.
- Phase B ships and stands on its own regardless of this ADR's disposition
  (PLAN-0026 OQ-1); ADR-0021 upgrades the Phase-B seam from best-effort to typed —
  it does not block Phase B.

## Alternatives Considered

### Alternative 1: Construct (a) — per-enum-value attribute map

Extend the `enum` property so each value carries metadata (e.g. a
`value_meta` / `unit_for` map: `temperature: celsius, frequency: hz`).

- **Pros:** smallest grammar delta; still declarative in the ontology; still
  enables "classify, don't synthesize" (D3).
- **Cons:** couples the unit binding to the enum-property syntax specifically;
  less faithful to the QUDT quantity-kind-vs-unit separation; does **not** extend
  cleanly to a typed measurement composite (c).
- **Why not chosen (lean):** Cray leans (b) as the closer fit to the
  comparative-measurement pipeline and the clean path to (c). (a) remains a viable
  fallback if ratification prefers the smaller grammar delta — recorded so the
  fallback is on the record.

### Alternative 2: Construct (c) — typed "measurement" composite

A composite value type bundling value + kind + unit into a single typed property.

- **Pros:** most expressive; fully self-describing measurements.
- **Cons:** heaviest grammar + generator change; likely over-scope for v0 (Rule of
  Three, ADR-006 / ADR-008 Alternative 4 "Palantir-lite not Palantir-full").
- **Why not chosen (now):** over-scope for v0. (b) is the **stepping stone** —
  ADR-0021's typed pair extends to (c) later without re-deciding the model.

### Alternative 3: Amend ADR-008 in place (no new ADR)

Home the decision as an amendment to ADR-008 (precedent: ADR-001 Amendment 1).

- **Pros:** keeps all ontology-spec knowledge in one document; lighter ceremony.
- **Cons:** the typed-semantics decision has substantial independent rationale and
  deserves its own citation anchor; it **extends** rather than corrects ADR-008.
- **Why rejected:** distinct decision → own ADR. (Caveat retained and honored: the
  binding construct **does** amend ADR-008 D3 — see D2.)

### Alternative 4: Path-A "thin" — binding in engine / `synthetic.py` code

Hardcode the kind→unit binding in `services/engine/` or the data adapter.

- **Pros:** no grammar change; fastest to ship.
- **Cons:** the knowledge lives in **code, not the ontology** — a weak moat; every
  new kind/vertical is a code change, defeating the §1 thesis.
- **Why rejected:** explicitly rejected by Cray (session 61, Gate 2 = Path B
  principled). Knowledge belongs in the declared ontology.

### Alternative 5: Keyword→value map in the engine

Map question keywords to filter values heuristically in the engine.

- **Pros:** no ontology change.
- **Cons:** brittle; hallucination / over-filter risk; exactly the path the pattern
  article and PLAN-0026 IN-1 reject.
- **Why rejected:** brittle and unsafe; not declarative; loses generality.

### Alternative 6: Raw text-to-SQL / engine-B

Replace the bounded `StructuredQuery` with free-form LLM-generated SQL.

- **Pros:** more expressive (clears joins/aggregates natively).
- **Cons:** **loses the 12/12 anti-hallucination guard** — in the comparison arm it
  improvised a *different* answer (an alarm event for a missing alert) rather than
  admitting the gap.
- **Why rejected:** rejected by PLAN-0024; not re-opened. Anti-hallucination is the
  non-negotiable property (PLAN-0026 AC-5).

## References

- **PLAN-0026** — NL-query aggregate metric-semantics (steps **6–7** = this ADR's
  gated implementation; **AC-8** = `measured_kind` first-class, GATED; **SD-2** =
  amend-ADR-008-vs-new-ADR, this ADR is the "new ADR-0021" disposition; **IN-1** =
  the Phase-B best-effort coherent-unit rule this ADR's D3 supersedes).
- **`benchmarks/nl_query_feasibility/RESULTS.md`** — the 2026-06-15 addendum: the
  4-model sweep + 3-prompt escalation (both NEGATIVE) and the corrected
  "drops filter AND group_by" diagnosis. The proven-negative evidence that makes
  this a data-model decision.
- **`docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md`** — the
  moat argument and external citations (QUDT quantity-kind/unit separation; EAV
  "one big column" anti-pattern; Palantir Foundry Ontology value types; dbt
  Semantic Layer / Open Semantic Interchange; NL2SQL missing-filter / measure-vs-filter
  failure taxonomy; constrained-decoding-as-bounded-selection; clarification-over-confabulation).
- **ADR-008** — YAML ontology specification: **D3** (data types — this ADR amends
  it to admit the binding construct), **D5** (code-generation contract — generator
  must carry the binding into ontology meta), **D6** (validation — L1 + L2 gain the
  binding checks).
- **PLAN-0024** — deterministic aggregates + `resolve` join (done); this ADR closes
  its un-named-entity-superlative residual. The text-to-SQL / engine-B rejection
  (anti-hallucination trade-off) originates here and is not re-opened.
- CLAUDE.md §1 (semantic layer = the moat; Rule of Three), §8 (ADR Accepted before
  impl PR). ADR-005 (OCT pivot), ADR-006 (vertical plugin architecture), ADR-007
  (OCT engine contracts). ADR-009 D1/D2 (Cowork drafts, Code commits), ADR-012
  D4.3 (author≠reviewer disclosure).

## Implementation Notes

- **Number:** `0021` confirmed free at authoring (highest accepted = ADR-0020;
  ADR-0014 is WITHDRAWN; no `0021` file exists). Code confirms the number at commit.
- **Governance gate:** Phase A's impl PR (PLAN-0026 steps 6–7) is gated on this ADR
  being **Accepted before** the PR (CLAUDE.md §8) **and** the T2-vs-T3 roadmap go
  (PLAN-0026 OQ-1).
- **Ratification action:** the construct choice (D2) is the decision Cray confirms
  at Proposed → Accepted. If (a) is preferred over (b) at ratification, D2 and the
  ADR-008 D3 amendment scope narrow accordingly (a per-enum-value attribute map is
  a smaller grammar delta); D1, D3, D4 are unaffected by the (a)/(b) choice.
- Drafted by Cowork (Tier-1, ADR-009 D1); uncommitted. Code reviews + commits via a
  `docs/*` PR (ADR-009 D2). AI-assisted (Claude); no `Co-Authored-By` per CLAUDE.md §7.
