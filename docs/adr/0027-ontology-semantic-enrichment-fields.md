# ADR-0027: Ontology semantic-enrichment fields (synonyms, sample_values, verified_queries, metric grain) — an ADR-008 grammar amendment

**Status:** Accepted (ratified 2026-07-04 — SD-1…SD-7 all confirmed as-recommended; SD-6 follow-up build = PLAN-0050)
**Date:** 2026-07-04

> **Erratum (2026-07-04, PLAN-0050 Step 7).** During the R2 build, Code read
> `services/engine/code_generator.py::emit_context_pack` + its 3 helpers
> (`:536-658`) and captured fresh on-disk evidence: the shipped R1 emitter (PLAN-0049
> Step 4) does **NOT** read the four enrichment fields
> (`synonyms`/`sample_values`/`verified_queries`/`grain`). It reads only structural
> fields (`type`/`values`/`target`/`required`/`description`) + `quantity_bindings`
> kind→unit, and emits a **hardcoded, unconditional** "## Notes … not yet populated"
> degrade note — which fires even for the now-fully-enriched energy vertical (the
> enriched energy context pack carries no Thai synonym / verified query / sample
> value). So the ADR's original "already reads these fields when present … zero
> emitter change" forward-reference was **factually incorrect**: R2 requires a
> **small, localized emitter change** (teach the 3 helpers to render the enrichment
> + make the degrade note conditional). **Cray's decision (2026-07-04):** amend this
> ADR to correct the premise (this erratum), then make the small emitter change (a
> separate follow-up authorized in PLAN-0050 Step 7). The **DESIGN is unchanged** —
> D1–D4, the four constructs, D2/D3 invariants, and SD-1…SD-7 all stand; only the
> incorrect emitter forward-reference is corrected. Status stays **Accepted**.
**Deciders:** Jirachai Thiemsert (founder) — ratifies the surfaced decisions
**Related:** ADR-008 (YAML ontology specification — D2 grammar, D3 types, D5 generator, D6 validation; **this ADR amends D2/D3**), ADR-0021 (metric-kind typed semantics — the `quantity_bindings` grammar-amendment precedent this mirrors), ADR-0024 (governed ≠ generated — machine drafts, human canonicalizes), ADR-006 (vertical plugin architecture / Rule of Three), ADR-005 (OCT pivot — energy first), PLAN-0049 (the R1 semantic-context-pack + SD-1 carve-out that originated this ADR), `docs/research/private/2026-07-03-semantic-foundation-build-techniques.md` (F4 + F9 + P1/P2 + R2 — the convergent-fields + Thai-moat evidence), ADR-009 D1/D2 (drafter drafts, Code commits), ADR-012 D4.3 (author≠reviewer disclosure)

> **Authoring disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authority) from Code's session-95
> dispatch. The substantive argument is lifted from a Code-dispatched **web-research
> output** — `docs/research/private/2026-07-03-semantic-foundation-build-techniques.md`
> — so the research-author and this ADR-author are distinct actors; **Code's R2
> review at PR merge + Cray's ratification are the independent checks.** Separation
> noted, not asserted.

> **Carve-out origin (PLAN-0049 SD-1, ratified 2026-07-04).** This ADR is the
> prerequisite carved out of PLAN-0049 by ratified SD-1: the R1 semantic-context-pack
> emitter (PLAN-0049 Step 4) ships *reading* these fields when present, but the fields
> themselves are a **grammar amendment** — new ontology constructs — and per the
> ADR-0021 precedent a grammar amendment gets its own ADR before the build. PLAN-0049's
> executable steps {1, 2, 4, 5} shipped independently; **R2's build is the remaining
> follow-up**, deferred to a named PLAN (see SD-6).

## Context

vero-lite's moat is the semantic layer (CLAUDE.md §1): a per-vertical YAML ontology
that grounds NL-query and anomaly reasoning so answers come from declared semantics,
never model memory. ADR-0021 proved the pattern for *metric* semantics (`measured_kind`
+ `quantity_bindings`). This ADR extends the same move to the **NL-facing** semantic
layer.

The 2026 build-techniques research (F4) finds a **convergent set of metadata fields**
that every mature semantic-view format carries and a hand-authored YAML likely lacks:
**synonyms** arrays, **sample_values** (treated as the closed filtering set when
populated), **verified_queries** (curated known-good NL→answer pairs), and metric
**grain**/join-path. F1 quantifies the payoff — a compact hand-authored semantic
context pack raised NL-analytics accuracy **+17–23pp, model-independent**. F9 is the
sharpest edge for vero-lite: multilingual text-to-SQL collapses to ~4% on
enterprise-grade benchmarks, **Thai is in no benchmark found**, and hand-authored Thai
synonyms + closed sample_values are doing work "no benchmark or vendor covers" — a
**moat**, not a nicety.

Two pitfalls constrain the design. **P1:** free-form LLM ontology generation
hallucinates — outputs must be constrained. **P2:** auto-learned semantics conflate
popularity with correctness — every promotion must be human-gated. Both point the same
way: these fields are **machine-drafted, human-canonicalized** curated content that
never auto-writes into the governed core (ADR-0024 D3/D6).

**Why a new ADR (mirrors ADR-0021's SD-2 disposition).** These fields are new grammar
constructs beyond ADR-008 D2/D3 (per-property data types + object/link structure only).
That is the exact shape ADR-0021 handled with a dedicated ADR for `quantity_bindings`.
This ADR **decides the grammar**; it does **not** build (SD-6).

**Forward-compat (small emitter change required — corrected by the 2026-07-04
erratum).** The shipped R1 emitter
(`services/engine/code_generator.py::emit_context_pack` + its 3 helpers, PLAN-0049
Step 4) carries a **hardcoded, unconditional** "## Notes … not yet populated"
degrade note but does **NOT** read the four enrichment fields — it reads only
structural fields + `quantity_bindings` kind→unit (verified 2026-07-04,
`:536-658`). So when R2's build lands, R1 does **not** gain the enrichment for free:
R2 requires a **small, localized emitter change** — the 3 helpers
(`_context_pack_property_line`, `_context_pack_object_lines`,
`_context_pack_measure_lines`) gain enrichment rendering and the degrade note
becomes **conditional** (fires only when the fields are absent). This is a bounded
follow-up (PLAN-0050 Step 7), not a design change; D1–D5 are unaffected.

## Decision

### D1: Four optional semantic-enrichment constructs are added to the ADR-008 grammar

The ontology grammar gains four **optional** constructs. Their placement and shape were
**surfaced for ratification** (SD-1…SD-5) — the recommendations below were load-bearing
in this draft and were **confirmed as-recommended at ratification (2026-07-04)**:

1. **`synonyms`** (th + en alternate names) — for NL matching. Recommend a lang-keyed
   map `{th: [...], en: [...]}` (SD-2), attachable at both **object-type** and
   **property** level (SD-1). The Thai/EN separation is the moat (F9).
2. **`sample_values`** — representative values for a property. Recommend
   **property-level**, semantically the **closed filtering set when populated** (F4),
   distinct-but-compatible with an enum's `values` (SD-3).
3. **`verified_queries`** — curated NL-question → trusted-answer pairs. Recommend
   **object-type-level** (or top-level), the answer side chosen for **least coupling**
   in v1 (SD-4).
4. **metric `grain` / join-path** — the aggregation grain / join semantics for a
   measured quantity. Recommend attaching to the existing ADR-0021 `quantity_bindings`
   construct rather than inventing a parallel metric block (SD-5).

### D2: Backward-compat is a HARD INVARIANT — absent = byte-identical load

Every field is **optional**. An ontology YAML that declares none of them loads
**byte-identically** to today, generates the same five artifacts, and validates
unchanged — exactly the ADR-0021 `quantity_bindings` default-absent pattern
(`ontology_meta.py` uses `default_factory=list`; L1 marks the construct optional; the
L2 check no-ops when the key is absent). This is not a nice-to-have; it is the
invariant that lets R2 land without touching any existing vertical.

### D3: Standing rule — governed ≠ generated (machine drafts, human canonicalizes)

Per ADR-0024 D3/D6 and research P1/P2, these fields are **curated content**. A machine
(the R3 bootstrap or the R4 usage loop, both out of scope here) may *draft* them, but a
**human canonicalizes every value via a normal PR**. Usage signals never write directly
into the governed YAML. This is recorded as a **standing rule for these fields**, not a
one-time note.

### D4: Enforcement depth — L1 shape + L2 consistency (recommended; SD-7)

Recommend mirroring `quantity_bindings`: **L1** (`ontology_schema.json`) gains each
construct's optional sub-schema (well-formedness); **L2** (`ontology_validator.py`)
gains a `_check_*` consistency pass (e.g. a `verified_queries` referencing only real
object_types/properties; a `synonyms`/`sample_values` well-formedness / referent check),
following the `_check_quantity_bindings` pattern (:291). Alternative: free-form-until-
consumed (SD-7).

### D5: Scope — this ADR decides the GRAMMAR, not the implementation

Like ADR-0021 D4: this ADR decides the model (D1–D4). The **build is a follow-up PLAN**
(SD-6) that will amend L1 (`ontology_schema.json`) + the Pydantic projection
(`ontology_meta.py`: new optional attrs on `PropertyMeta` / `ObjectTypeMeta`, mirroring
`QuantityBinding`) + the L2 validator, and backfill the v1 verticals (energy-v1 +
supply-chain-v1 — the natural batch boundary per research R2). The R1 emitter requires
a small, localized change to render the enrichment (forward-reference above, as
corrected by the 2026-07-04 erratum) — not a free consume.

## Consequences

### Positive

- The **ontology becomes the source of truth for the NL-facing semantic layer**, not
  just structure + metric kinds — the §1 moat extended to synonyms/samples/known-good
  queries. Best-evidenced 2026 intervention (F1, +17–23pp).
- **Thai alias coverage becomes a first-class authored artifact** — a moat no benchmark
  or vendor covers (F9).
- **R1 gains enrichment via a small, localized emitter change** — the shipped emitter
  carried a hardcoded degrade note but did not read the fields; the 3 helpers gain
  enrichment rendering + the note becomes conditional (corrected by the 2026-07-04
  Step-7 erratum; the design is unchanged, the cost is bounded).
- **`sample_values`-as-closed-set aligns with the closed-enum philosophy** (F4) and the
  emitter's existing "CLOSED — refuse, do not guess" framing.
- The **governed ≠ generated rule (D3)** pre-wires the safe adoption path for the R3
  bootstrap and R4 usage loop without deciding either now.

### Negative

- **New grammar surface + generator/validator support** (four constructs; L1/L2/Pydantic
  work) — a real, if bounded, cost in the follow-up PLAN.
- **ADR-008 D2/D3 is amended again** (after ADR-0021), so ADR-008 is further from a
  single self-contained grammar source; readers follow two amendment pointers.
- **Curation is manual labor** — Thai synonyms + verified_queries are hand-authored per
  vertical (D3); the payoff is the moat, but the cost is real and recurring.

### Neutral

- Absent fields change nothing (D2 invariant); every existing vertical loads unchanged.
- The build's sequencing (defer vs bundle) is SD-6 — this ADR's disposition does not
  force either.

## Alternatives Considered

### Alternative 1: Amend ADR-008 in place (no new ADR)

- Pros: keeps grammar knowledge in one document; lighter ceremony.
- Cons: these are new constructs with independent rationale (the convergent-fields
  evidence, the Thai moat, P1/P2); they deserve a citation anchor.
- Why rejected: distinct decision → own ADR — the exact ADR-0021 SD-2 disposition.
  Caveat honored: the constructs **do** amend ADR-008 D2/D3 (D1).

### Alternative 2: A separate side-car semantics file (not in the ontology YAML)

- Pros: keeps the governed structural YAML lean; separates curated from structural.
- Cons: splits the single-source-of-truth; the R1 emitter + generator already read one
  `doc` — a side-car doubles the load path and drift surface.
- Why rejected: one ontology = one source of truth (§1); optional in-YAML constructs
  (D2) already keep absent-cost at zero.

### Alternative 3: Free-form / untyped enrichment blob until consumed (SD-7 alt)

- Pros: fastest to ship; no L1/L2 work.
- Cons: no well-formedness or referent guarantee; drift + silent-wrong risk (research
  P3, F10); loses the parity-tested rigor the rest of the ontology has.
- Why rejected (lean): D4 recommends L1+L2, mirroring `quantity_bindings`. Recorded as
  SD-7 for ratification.

## Surfaced Decisions (SD) / Open Questions (OQ)

Each SD carried a recommendation. **Ratified 2026-07-04: SD-1 … SD-7 all confirmed as-recommended (none overridden).**

- **SD-1 (field placement).** Which construct attaches where — property-level, object-
  type-level, or metric-level? **Recommend:** `synonyms` at BOTH object-type + property
  level; `sample_values` property-level; `verified_queries` object-type-level (or
  top-level, see SD-4); `grain`/join-path on `quantity_bindings` (SD-5). *Why a Cray
  decision:* placement sets the grammar shape all four surfaces implement; multiple
  defensible cuts. **Ratified 2026-07-04 — as-recommended.**
- **SD-2 (`synonyms` shape).** Lang-keyed map `{th: [...], en: [...]}` vs a flat list?
  **Recommend the lang-keyed map** — the Thai moat (F9) argues for explicit language
  separation, and it keeps EN/TH matchers independent. *Alt:* flat list (simpler,
  loses lang signal). **Ratified 2026-07-04 — as-recommended.**
- **SD-3 (`sample_values` semantics).** Closed enumerated set vs open examples; and its
  relationship to an enum property's `values`. **Recommend:** closed-set-when-populated
  (matches F4 + the emitter's closed-enum framing), **distinct from** `values`
  (`sample_values` = representative data for non-enum props; `values` = the enum's
  definitional set — a property may have neither, either, or overlap by intent). *Why
  Cray:* redundancy-vs-distinctness is a modeling call. **Ratified 2026-07-04 — as-recommended.**
- **SD-4 (`verified_queries` shape).** The answer side: a natural-language expected
  answer, an NL-query IR, or the structured `QueryFilter` from
  `services/engine/nl_query.py`? **Recommend the least-coupling v1** — a
  `{question, answer}` NL pair (answer = expected natural-language answer or a short
  grounded fact), deferring any IR/`QueryFilter` binding until a consumer needs it.
  *Why Cray:* couples (or decouples) the ontology to the NL-query engine's internal
  shape. **Ratified 2026-07-04 — as-recommended.**
- **SD-5 (`grain`/join-path placement + shape).** On `quantity_bindings`? a new
  per-metric construct? a top-level `metrics` block? **Recommend attaching to
  `quantity_bindings`** (already the per-kind metric-semantics home, ADR-0021) — extend
  each binding with an optional `grain` + optional join-path rather than a parallel
  block. *Alt:* a first-class `metrics` block (heavier; over-scope for v1).
  **Ratified 2026-07-04 — as-recommended.**
- **SD-6 (build sequencing).** ADR-only now, defer the build to a follow-up PLAN (the
  ADR-0021→PLAN-0026 pattern) vs bundle build into this ADR's PR. **Recommend
  ADR-only + a named follow-up PLAN** — matches the precedent and CLAUDE.md §8 (ADR
  Accepted before impl PR). **Follow-up PLAN named at ratification: PLAN-0050.**
  **Ratified 2026-07-04 — as-recommended.**
- **SD-7 (enforcement depth).** L1 shape + L2 consistency (D4, mirrors
  `quantity_bindings`) vs free-form-until-consumed (Alternative 3). **Recommend
  L1+L2** — parity with the rest of the ontology's rigor; the marginal cost is one
  `_check_*` per construct. **Ratified 2026-07-04 — as-recommended.**

## References

- **`docs/research/private/2026-07-03-semantic-foundation-build-techniques.md`** — F4
  (convergent metadata fields: synonyms/sample_values/verified_queries/grain), F1
  (+17–23pp context-pack effect), F9 (Thai = uncovered moat), P1/P2 (constrain
  generation; human-gate promotion), R2 (the enrichment recommendation + v1-batch
  boundary).
- **ADR-0021** — the grammar-amendment precedent: `quantity_bindings` as a dedicated
  ADR + the "amend-in-place vs new-ADR" (SD-2) disposition this mirrors; D4
  "decides the model, not the implementation."
- **ADR-008** — YAML ontology specification: **D2** (top-level structure), **D3**
  (data types) — both **amended** by this ADR to admit the four constructs; **D5**
  (generator carries them into ontology meta), **D6** (L1 + L2 gain the checks).
- **ADR-0024** — governed ≠ generated (D3/D6); the standing rule in D3.
- **PLAN-0049** — the R1 semantic-context-pack emitter + the SD-1 carve-out that
  originated this ADR; steps {1,2,4,5} shipped, R2 build is the remaining follow-up.
- **Surfaces the follow-up PLAN will touch:** `services/engine/ontology_schema.json`
  (L1), `services/engine/ontology_meta.py` (`PropertyMeta` / `ObjectTypeMeta` optional
  attrs, mirroring `QuantityBinding`), `services/engine/ontology_validator.py`
  (`_check_*` mirroring `_check_quantity_bindings`), and the v1 vertical backfill.
  `services/engine/code_generator.py::emit_context_pack` (the emitter + its 3 helpers,
  `:536-658`) **must be extended to render them** — the shipped emitter carried a
  hardcoded "not yet populated" degrade note only and did not read the fields
  (corrected by the 2026-07-04 Step-7 erratum).
- CLAUDE.md §1 (semantic layer = the moat; Rule of Three), §8 (ADR Accepted before
  impl PR). ADR-009 D1/D2 (drafter drafts, Code commits), ADR-012 D4.3 (author≠reviewer
  disclosure), ADR-013 D1 (plan-drafter phased authority).

## Implementation Notes

- **Number:** `0027` assigned by the caller (dispatch `target_number`); no `0027` file
  existed at authoring (`docs/adr/0027*.md` glob empty). Code confirms at commit.
- **Scope walls:** R3 (schema-guided LLM bootstrap) and R4 (usage-mined loop) stay
  **OUT** — later, post-partner. Band-expressiveness and mapping-layer items are
  unrelated threads — **OUT**.
- **Governance gate:** the follow-up build PR (SD-6) is gated on this ADR being
  **Accepted before** the PR (CLAUDE.md §8).
- **Ratification outcome (2026-07-04):** SD-1 … SD-7 **all confirmed as-recommended**
  (none overridden). SD-6's follow-up build PLAN is named **PLAN-0050** (next free
  number). D1–D5 stand as drafted; the ADR-008 D2/D3 grammar amendment proceeds with
  the four optional constructs. The follow-up build PR (PLAN-0050) is gated on this ADR
  being Accepted before the PR (CLAUDE.md §8) — now satisfied.
- Drafted by the in-harness `plan-drafter` (ADR-013 D1); uncommitted. Code R2-reviews +
  commits via a `docs/*` PR (ADR-009 D2). AI-assisted (Claude); no `Co-Authored-By` per
  CLAUDE.md §7.
