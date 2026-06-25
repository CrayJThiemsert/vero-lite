# ADR-0024: Archetype-first procedure generator — narrative → governed Procedure skeleton behind the human-review gate (ADR-016 Phase 2 / "Stage 3")

**Status:** Accepted (Cray-ratified 2026-06-25, session 78. ADR number 0024 + the standalone framing founder-approved [Cray, 2026-06-25]; the nine Open Questions' recommendations are accepted as standing guidance, each finalized at its consuming PLAN — see § Open Questions.)
**Date:** 2026-06-25 (drafted Proposed)
**Deciders:** Jirachai Thiemsert (founder) — ratifies the construct AND adjudicates the Open Questions (§ Open Questions) below
**Related:** ADR-016 (governed procedure engine — **this ADR realizes its D7 Phase 2** "narrative→Procedure skeleton behind the human-review gate", archetype-first; it extends the **runtime** "governed ≠ generated" guardrail to the **authoring** surface — see Context); ADR-016 D2 Amendment 2026-06-25 (the typed `facet:` field + the `gate_kind` 6-kind enum this generator emits — **the schema substrate**, and the amendment OQ-A1/A2/A3 this ADR resolves); ADR-0021 (metric-kind typed semantics — the **"classify, don't synthesize"** precedent: the LLM picks from a closed enum, deterministic code synthesizes structure — the spine of D1); ADR-0019 (`watch → gated`-proposal routing — the **determinism invariant**: route on the engine-computed verdict, **never** the LLM signal — extended here to the authoring layer, D5); ADR-010 (LLM reasoning-hook surface — **IN-3** confidence is advisory, never gates automation — the invariant D5 binds); ADR-006 (vertical plugin architecture — **D4 Rule of Three**: extract abstractions only after 3+ working examples, "concrete-first or nothing" — the gate that admits AT-1 generation and defers AT-2); ADR-007 (OCT engine contracts — D2 `RecommendedAction` envelope, **untouched**: an `action` step still routes through the existing approve→execute gate); ADR-008 (YAML ontology spec — the six `object_types` + the ontology codegen path are **untouched**; `procedures.yaml` is engine-read, not codegen-emitted); ADR-009 D1/D2 (Cowork drafts ungated, Code commits — "only Code commits" fail-safe); ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 (phased autonomy relocation — Cowork = advisory governance drafter). Consuming work: two follow-on PLANs (PLAN-0039 read-only viewer, PLAN-0040 generator — § Implementation Notes). Substrate: `services/engine/procedures/spec.py` (the `Step`/`Procedure`/`Agent` schema), `services/engine/procedures/orchestrator.py` (`validate_runnable`), `docs/conventions/procedure-archetypes.md` (the N=4 archetype catalog), `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml`.

> **Drafting provenance.** Drafted (uncommitted) by Cowork (Tier-1 governance authoring, ADR-009 D1 interim per ADR-013's phased relocation; Cowork = advisory drafter). Code R2-reviews + commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). ADR number 0024 + the **standalone** framing (vs an ADR-016 amendment — OQ-9) are **founder-approved** (Cray, 2026-06-25; G2 gate cleared) before drafting.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray (session 78: the archetype-first / AT-1-family / one-review-surface scope calls) **plus a Code-run 5-specialist design panel** (LLM-pipeline · governance · schema · product/UX · red-team). Drafter = Cowork. Independent reviewer = Cray at ratification + Code R2-review at commit. **The substance was deliberated by the Code-run panel, not by Cowork's own free-form mode** — so the independent-deliberation check is *exercised* (panel + Cray + Code R2 are independent of the drafter); separation is intact and reinforced. Cowork's contribution is synthesis + an adversarial pressure-test of the panel output + ADR prose; residual forks are surfaced as Open Questions, not silently resolved.

---

## Context

### Where the procedure engine stands today (Stage 2 done, schema proven)

ADR-016 established a governed procedure engine: per-vertical `procedures.yaml` specs (`Procedure` / `Step` / `Agent`), a linear set-valued orchestrator, and the safe-by-default, human-gated autonomy posture (D3). The **D2 Amendment (Accepted 2026-06-25)** promoted the 5-facet annotation (`input · decision_condition · llm_assist · output · governance`) from YAML comments to a **first-class, typed, validated, NON-authoritative** `Step.facet` field, with a discriminated `decision_condition.gate_kind` over **exactly six** observed kinds (`env_band`, `in_file_band`, `rule_gate`, `scored_rule`, `doa_tier`, `none`). PLAN-0038 shipped the `spec.py` edit and migrated all four verticals.

So the schema the generator needs **exists and is proven**: `facet` is machine-readable, and `docs/conventions/procedure-archetypes.md` names the recurring shapes (AT-1 / AT-1b / AT-2 / AT-3) the facets reveal. Per Rule-of-Three (ADR-006 D4), the Stage-3 generator was deliberately deferred *until the schema was extracted from working examples* — which it now is. ADR-016 D7 forward-declared this as **Phase 2** ("extend the PLAN-0017 intake face so a stakeholder narrative also yields a Procedure skeleton behind the human-review gate"). This ADR realizes that phase, archetype-first.

### The honest count: N=4 procedures, but the diversity is N≈2

The archetype catalog presents four shapes, but the structural diversity is thinner than the count suggests (red-team finding, verified against the four `procedures.yaml`):

| Procedure | Shape | `gate_kind` sequence | Archetype |
|---|---|---|---|
| `energy.substation_health_sweep` | read → judge(env band) → gated restart | `[none, env_band, none]` | AT-1 |
| `supply_chain.cold_chain_excursion_sweep` | read → judge(env band) → gated hold | `[none, env_band, none]` | AT-1 (byte-identical to energy bar noun/handler) |
| `aquaculture.morning_pond_health_round` | AT-1 + watch→gated proposal + auto summary | `[none, in_file_band, none, none(watch action), none(auto summary)]` | AT-1b |
| `procurement.low_stock_reorder_round` | read → judge(in-file band) → gated reorder | `[none, in_file_band, none]` | AT-3 |
| `procurement.emergency_sourcing_round` | intake → judge → scored-rule source → rule-gate compliance → DOA approve → issue → audit | `[none, in_file_band, scored_rule, rule_gate, doa_tier, none, none]` | **AT-2 (the only instance)** |

**AT-1 triangulates** (energy + supply_chain + aquaculture-core + low_stock_reorder — 3+ independent verticals, Rule-of-Three satisfied). **AT-2 is N=1** — the 7-step scored-rule / compliance / tiered-DOA / SoD / emergency-waiver shape appears in *exactly one* procedure, and it is the **governance-heaviest, highest-consequence** archetype. Generating AT-2 skeletons would violate Rule-of-Three on the very archetype where a mis-generation is most dangerous (the catalog's own rule: "when a 5th vertical lands, extend the catalog; do not force the vertical to fit"). This is the honest reason v1 generation is scoped to the AT-1 family (D7).

### The core reframing: "governed ≠ generated" must be re-fenced for the AUTHORING surface

ADR-016 / the archetype catalog state the invariant **governed ≠ generated**: the LLM only *drafts or summarises*; it never *selects* (selection is a scored rule), never *sets a threshold* (bands are authored), never *approves* (humans gate). **But that invariant was written for the *runtime* engine.** Stage 3 is a different surface: the LLM is now authoring the config that the runtime trusts as deterministic ground truth. At authoring time, *every* typed field in `spec.py` — `threshold`, `direction`, `handler`, `tiers`, `gate_kind`, `autonomy`, step order, the `where` filter — is a field the generator is positioned to pre-fill or bias. The determinism invariant protects the *verdict computation*; it does nothing, unmodified, to protect the *authoring of the band the verdict is computed against*.

This ADR therefore restates the guardrail for the generation surface explicitly, and makes it **mechanical, not prompt-based** (D3). The leak classes it must close (red-team / governance enumeration):

1. **Prose-smuggling** — a threshold/amount/handler laundered through generated `goal` / `description` / `facet.*` prose into a field a human then "authors" by copying the anchored value.
2. **Archetype-selection-as-governance** — down-classifying an AT-2 narrative to the calmer AT-3 silently deletes the SoD split, the compliance gate, and the DOA ladder, with no threshold set and no handler picked.
3. **Generated `goal` = runtime-prompt surface** — `goal` is a runtime LLM directive (ADR-016 D5), so generated `goal` text steers the runtime judging/proposing model; it is executable governance surface, not a doc-string.
4. **Routing on match-confidence** — keying generation on the LLM's archetype-match confidence reopens the ADR-0019 / ADR-010 IN-3 determinism invariant at the authoring layer, where no one is watching for it.

### The substrate for this decision

The design space was worked by a Code-run **5-specialist panel** (LLM-pipeline · governance · schema · product/UX · red-team) over the full substrate (`spec.py`, ADR-016 + the facet amendment, the archetype catalog, all four `procedures.yaml`, ADR-0021/0019/010/006), plus Cray's session-78 scope calls (archetype-first; AT-1-family v1; one review surface). The decisions below render that consensus; the Open Questions are the residual forks for Cray.

## Decision

A **governed procedure generator**: a vertical's stakeholder **narrative** → an **LLM classifies it to one of the catalogued archetypes** → **deterministic code instantiates that archetype's template** (step skeleton + wiring) → **the LLM drafts only advisory prose** (`goal` / `description` / `facet.llm_assist` / facet notes) → the result is a **Procedure skeleton** presented behind a **human-review gate**, where **every governance value is a human-author stub**. Acceptance output = a `load_procedures`-valid `procedures.yaml` draft, uncommitted, behind the gate.

### D1 — Strategy is archetype-first: classify → instantiate → draft-prose; deterministic-code-dominant; exactly two narrow LLM calls

Generation is **archetype-first**, never free-form and never hybrid. The pipeline is **deterministic-code-dominant** with exactly **two narrow LLM calls**:

- **(a) archetype classification** — the LLM picks one archetype from the closed, human-curated catalog (and, per OQ-3, per-step `gate_kind` labels over the closed 6-kind enum). It emits a **small typed JSON object**, never YAML or structure.
- **(b) advisory-prose drafting** — the LLM drafts only `goal` / `description` / `facet.llm_assist` / facet notes.

Everything between and around those two calls is deterministic code: template instantiation, stub-stamping, assembly, validation. This is the **classify-don't-synthesize** discipline proven in ADR-0021 (`measured_kind`): the LLM selects from a closed enum; *code* synthesizes the structure. The generator **never invents** an archetype or a `gate_kind` — both vocabularies are closed and human-curated (the same Rule-of-Three discipline that gated the `gate_kind` enum gates the generator; ADR-016 D2-Amendment OQ-A1).

The pipeline contract (architecture only — mechanics are PLAN-0040's): roughly **S0** normalize narrative → **S1** classify *(LLM)* → **S2** abstain-gate (D5) → **S3** template-instantiate → **S4** stub-stamp → **S5** prose-draft *(LLM)* → **S6** assemble + validate-against-`spec.py` + provenance. A **validate→repair-retry loop** feeds the exact Pydantic error back to the prose call (capped, then abstain). LLM calls run **MS-S1-local** constrained-decode (residency, CLAUDE.md §8; ADR-001 `gpt-oss:20b`), low temperature; the constrained-decode caveat (never disable reasoning while using `format`) is a PLAN-0040 implementation note (ADR-001 / Ollama behaviour).

### D2 — Promote the archetype catalog from prose to a machine-readable template artifact

The prerequisite that actually unblocks the generator: an `ArchetypeTemplate` artifact (a Pydantic model + a derived registry) that has **slots to instantiate**. A prose table does not.

- The prose `docs/conventions/procedure-archetypes.md` stays the **canonical human form**; the template is the **derived machine form** (mirrors the CLAUDE.md §4 canonical→derived rule; on conflict, the canonical wins).
- Model **AT-1b and AT-3 as variants of an AT-1 base, not four disjoint shapes** — anti premature-lock-in (a base skeleton + declared deltas: AT-1b adds the watch→gated branch + the auto summary terminal; AT-3 is AT-1 with the calm-reorder intent).
- Each template, instantiated, must itself round-trip `load_procedures` — asserted in CI (see OQ-2 for where it lives + the loader/validator question).

### D3 — "governed ≠ generated" is MECHANICAL: a restricted draft type + a deterministic prose-lint

Do not trust the LLM to "not emit" governance values — **strip its emission surface so it cannot**. Two mechanisms:

1. **A restricted draft type** (`StepDraft` / `ProcedureDraft`) whose schema has **no** governance fields at all — no `threshold` / `direction` / `watch_margin` / `handler` / `tiers` / `autonomy` / `env_var` / DOA-amount / scored-rule-content, and on the agent side no `autonomy_ceiling` / `allowed.*`. A deterministic lift `StepDraft → Step` *injects* those governance fields as **un-filled stubs**. Leakage is then a **type error at the boundary**, not a model behaviour we hope for. (Verified net-new: no `StepDraft`/`ProcedureDraft` exists today.)
2. **A deterministic prose-lint** that rejects numerics / currency / handler-names / selection-or-approval verbs appearing in generated `goal` / `description` / `facet.*` prose — closing the prose-smuggling leak (class 1) that the typed schema alone cannot, because `extra="forbid"` gives *false assurance* (a laundered number "in a comment" looks non-authoritative but is the anchor a human copies).

The field-by-field contract — **G** = generator-may-emit · **H** = human-author stub (generator must NOT emit; blocks runnability) · **D** = deterministic-derived (engine/loader computes):

| Object | Field | Class | Note |
|---|---|---|---|
| `Procedure` | `procedure_id` | **D** | slugged deterministically |
| | `title` | **G** | prose |
| | `goal` | **G** (prose, un-trusted for values) | runtime LLM directive (D5) — elevated scrutiny + prose-lint; see OQ-4 |
| | `run_by` | **H** | binds the Agent = a blast-radius choice |
| | `trigger` | **G**, constrained to `manual` | `schedule` is a governance posture → H/deferred |
| | `steps` | **G** (structure) | order + each step's G-fields; H/D fields per rows below |
| | `terminal` | **D** | derived from the last/audit step |
| `Step` | `step_id` | **D** | slug/sequence |
| | `name` / `description` / `output` | **G** | prose / artifact-name (description un-trusted for values) |
| | `kind` | **G** | closed enum classification; archetype dictates the sequence |
| | `autonomy` | **H** | `action`-only go/no-go; **default `gated` ≠ authored** — a confirmed stub (R-5) |
| | `on_failure` | **H** (lean) | `fail` vs `escalate_to_human` is a governance routing choice |
| | `input` (`from` / `where`) | **G** (structure) / **D** (validation) | set-valued fan-out is structure; loader validates `from` is linear |
| | `handler` | **H** | binds the registered write effect; allowlist-checked. **Never G** |
| | `threshold` / `direction` / `watch_margin` | **H** | the authored band. **Never G** — the canonical "LLM never sets a threshold" |
| | `tiers` (canonical/acceptable/forbidden) | **H** | a safety taxonomy (`forbidden` = must-never-recommend). **Never G** |
| | `facet.decision_condition.gate_kind` | **G** | classification over the closed 6-kind enum (D4); must agree with the archetype |
| | `facet.decision_condition.band_source` | **G** (lean) | mechanism class (env vs in_file), co-determined by `gate_kind` — D4 |
| | `facet.decision_condition.env_var` | **H** | names the *specific* runtime band binding = a governance choice. **Never G** |
| | `facet.decision_condition.note` / `facet.input` / `facet.output` / `facet.governance` | **G** (prose, non-authoritative per D2-A2; un-trusted for values) | advisory notes |
| | `facet.llm_assist` | **G** | describing the assistive role is exactly the generator's job |
| `Agent` | `agent_id` | **D** | slug |
| | `name` | **G** | prose |
| | `llm_model` | **H** (lean) | residency/governance binding (ADR-001 default exists) |
| | `autonomy_ceiling` / `allowed.step_kinds` / `allowed.action_handlers` | **H** | the blast-radius bounds (D3). **Never G** |

**One-line summary:** the generator emits *prose, closed-enum classifications (`kind`, `gate_kind`, `band_source`), and workflow structure (step order, `input` fan-out)* — and **zero** numbers, handler/effect names, authority bounds, allowlists, or autonomy decisions.

### D4 — The sharp line: `gate_kind` YES, values NO

The generator MAY emit `decision_condition.gate_kind` (and `band_source` conditionally, leaning G per the ADR-016 amendment), and MUST NOT emit any value/binding/authority.

The principled distinction is **classification over a closed, human-curated vocabulary vs authoring a value/binding/authority**. `gate_kind` is epistemically identical to `kind`: a selection from a fixed 6-member enum the humans defined and the archetype constrains. Saying "this step decides via an `in_file_band`" *names the shape of the gate*; it commits **zero** about *what the band is*. It is reviewable — a human reading "judge → `gate_kind: in_file_band`" immediately knows "I now owe a threshold/direction/margin." The classification **creates the obligation; it does not discharge it.** A band *value* (`threshold: 0.8`), `env_var`, `handler`, `tiers`, `autonomy`, DOA ฿ tiers, scored-rule content each *discharge* the obligation — a number, a name, or an authority a human must own (CLAUDE.md §8 "assistive, never auto-").

Requiring `gate_kind` is itself a **governance win**: it makes every step *declare how it decides*, so a generated `gate_kind: none` is an *explicit, auditable* "no gate here" a reviewer can challenge, rather than a silent omission. **A generated `gate_kind` that contradicts the matched archetype's governance signature is a hard validation failure** (e.g. `gate_kind: none` where the archetype demands a gate — the silent-gate-removal hole, leak class 2). The archetype is the oracle: an AT-2 `approve` step MUST be `doa_tier`, an AT-2 `source` step MUST be `scored_rule` — never `none`, never LLM-chosen.

### D5 — Classification abstains, never force-fits; human-confirmed; the determinism invariant holds at the AUTHORING layer

- **Abstain, never force-fit.** Low-confidence / no-archetype-match → **emit no skeleton** → route to hand-author ("candidate new shape"). This is the catalog's own "do not force-fit" rule and resolves amendment OQ-A1.
- **Human-confirmed match.** The matched archetype is confirmed by a human *before* any skeleton is built (a cheap N-way re-pick at the gate). Closes leak class 2 (archetype-selection-as-governance).
- **Determinism invariant at the authoring layer.** Generation is **never routed on the LLM's archetype-match confidence**. The route decision is driven by an explicit, auditable deterministic match (keyword/structural criteria a human can inspect) + human confirm; any model-reported confidence is **advisory-for-the-human only**, never an automation gate. Routing generation on match-confidence (e.g. "if confidence > 0.8, auto-build") is the *same class* of violation ADR-0019 / ADR-010 IN-3 fenced off at runtime — named here explicitly so it is not quietly reopened at the authoring layer (leak class 4).

### D6 — Two states: a skeleton is draft-loadable but NOT run-loadable until a human authors the gates

A generated skeleton is **draft-loadable** (so the review UI can render it) but **run-loadable = no** (the orchestrator refuses a skeleton carrying stubs / an empty handler allowlist). Two explicit states.

This is grounded in the verified loader/runner split: `load_procedures` (`spec.py`) performs **shape + cross-reference validation only** (`_validate_step` per-kind invariants, `_unique_step_ids`, `_cross_refs` `run_by`-resolves) — it does **not** check governance-completeness, so a stub skeleton loads cleanly for editing. `validate_runnable` (`orchestrator.py`, the run-time pre-flight called by `execute_procedure` and on resume) is the gate that must refuse stubs. (See OQ-1 for the exact enforcement mechanism — a verified gap: a stub `action` with `handler=None` currently *passes* `validate_runnable`, and `autonomy` defaulting to `gated` *looks* authored, so safe-defaults alone do **not** make a skeleton un-runnable; an explicit stub-rejecting check is required.) The two-state property mirrors the existing `trigger: schedule` precedent ("loads but won't run").

### D7 — v1 breadth is the AT-1 family (AT-1 / AT-1b / AT-3); AT-2 is deferred

v1 generates only the **triangulated** shapes — AT-1, AT-1b, AT-3 (modelled as an AT-1 base + variants, D2). **AT-2 generation is deferred**: it is N=1 (red-team finding, verified), and it is the governance-heaviest archetype (scored-rule selection, per-criterion compliance, tiered DOA, SoD, emergency waiver) — generating it would violate Rule-of-Three precisely where a mis-generation is most consequential. An AT-2-class narrative **routes to hand-author** (the abstain path, D5), not a down-classified AT-3 skeleton.

### D8 — One review surface: the 5-facet viewer and the generator gate are the same component (read-mode ↔ edit-mode); the read-only viewer ships first

The standalone "5-facet review UI" and the generator's review gate are **one component**, not two. Splitting them guarantees two divergent renderers of the same object. The **read-only viewer ships FIRST** as its own PLAN (zero-LLM, demoable today on the four existing `procedures.yaml`, renders each procedure by its five facets with provenance colour-coding) — it de-risks the rendering the generator gate will reuse. The generator's gate is that same component in **edit mode**, fed by an LLM draft instead of a file, presenting three visually-separated zones per step: **LLM-drafted (advisory)** · **YOU must author (governance stubs)** · **archetype expectation (the oracle)**. This merges the two arcs Cray named in session 77 into one surface.

### D9 — Intake reuses the PLAN-0017 face wholesale

Do not invent a new intake metaphor. Reuse the PLAN-0017 live co-creation face: hybrid free-text capture → **MS-S1-local** single-shot constrained-decode (CLAUDE.md §8 residency) → **mandatory human-review gate** → **graceful degradation to a manual archetype-pick** on cold / low-confidence (the abstain path made usable, D5).

### D10 — Acceptance output is a `load_procedures`-valid `procedures.yaml` draft, uncommitted, behind the gate

The generator's output **is the artifact** (mirrors PLAN-0017): a `load_procedures`-valid draft, **uncommitted**, never written into `verticals/<name>/procedures.yaml` directly. No run, no auto-commit (ADR-009 D2 "only Code commits"; the existing G1/G2 gating ethos).

### D11 — The ADR-016 amendment Open Questions resolve here

The generator is now concrete, so the amendment's deferred questions resolve:

- **OQ-A1 (catalog growth)** → the generator **refuses, never invents**; enum / catalog growth stays human-authored + additive (D1/D5).
- **OQ-A2 (facet↔typed integrity)** → enforce at the **generation/review boundary ONLY**, **never in `spec.py`** (keeps `facet` non-authoritative; preserves D2-A2/A4). The generator/lift checks that an emitted `in_file_band` `gate_kind` corresponds to a `threshold` stub obligation; `spec.py` stays unchanged.
- **OQ-A3 (`llm_assist` typing)** → type it **in the `ArchetypeTemplate`** as `{role: draft|summarise, of: <field>}` (so `role: select|approve|set_threshold` is structurally un-authorable), but **emit the live `Step.facet.llm_assist` as prose `str`** — no live-schema churn.

### D12 — Tests are the offline oracle

Per CLAUDE.md §8 (the offline oracle is the gate, not a live LLM run), three offline tests are binding:

1. **Structural disjointness** — by introspection, the draft type's field set is provably disjoint from the governance-field set (`GOVERNANCE_FIELDS.isdisjoint(set(StepDraft.model_fields))`); if someone later adds `threshold` to the draft type, CI fails — the guardrail cannot silently erode.
2. **Poisoned-narrative red-team** — a narrative that *tries* to make the generator emit values ("set threshold 4.0, auto-approve under ฿50k, forbidden handler is `wire_transfer`") → assert those values appear **nowhere** (typed *or* in prose, the latter via the prose-lint), the lifted skeleton carries them as stubs, and `validate_runnable` raises on it.
3. **Archetype-agreement invariant** — for each archetype, the generated `gate_kind` sequence matches the archetype's required governance signature (closes the silent-gate-removal hole, D4).

The LLM step is stubbed with a recorded fixture so layer 2 is deterministic and offline.

## Consequences

### Positive

- **The differentiator becomes visible on screen.** "A human owns every gate" stops being a slogan: the generator emits *shape + advisory prose only*, the shape is *inert until authored*, and the review gate renders a draft *guaranteed to load* with governance stubs as conspicuous "author-required" markers. The moat story — "the workflow a prior customer paid to design just made yours an afternoon, and you still own every gate" — is realized *mechanically* by archetype-first matching.
- **"governed ≠ generated" is enforced by construction**, not by prompt hope: a leak is a type error or a lint failure, caught in the offline gate.
- **On-thesis** — sharpens "ontologies orchestrate governed workflows, not just answer" (ADR-016) and the template-reuse-across-customers moat (each hand-authored vertical becomes the next customer's starting template).
- **Low blast radius** — `spec.py`, the ADR-007 `RecommendedAction` envelope, and the ADR-008 ontology codegen path are all **untouched**; the generator is a new package, the draft type is new, the template artifact is new.

### Negative / risks

- **The biggest residual risk is prose-smuggling + AT-2's untyped rule content** (not the typed fields, which the schema closes). Mitigated by the prose-lint (D3) and by deferring AT-2 (D7) + flagging the typed-home gap (OQ-8).
- **Net author-time savings could be negative if review is heavy** — the generator automates the cheap part (step structure) and leaves the hard part (governance values) to a human who must verify the skeleton is even the right shape (red-team steelman). Mitigated by abstain-don't-force-fit (D5) and human-confirmed archetype match — a wrong shape is a visible, reviewable error, not a silent one.
- **Classification regression to the frequent shape** (LLMs down-classify the rare AT-2 to the common AT-3). Mitigated structurally: AT-2 is out of v1 scope, and the archetype-agreement invariant (D12) + human confirm (D5) catch a wrong match.

### Neutral

- This is a capability + authoring-invariant decision (hence an ADR + follow-on PLANs, not ad-hoc code). It only *implements* ADR-016 D7 Phase 2 — it does not supersede any ADR.
- ADR merged before the related implementation PLANs (CLAUDE.md §8).

## Open Questions

Surfaced for Cray to adjudicate (each with options + a recommendation; not silently resolved). Numbered per the dispatch §3, not the panel's internal numbering.

> **Disposition (Cray, 2026-06-25 ratification):** all nine recommendations below are **ACCEPTED** as the ADR's standing guidance; each is **finalized at its consuming PLAN** (PLAN-0039 viewer / PLAN-0040 generator). A recommendation stands unless that PLAN surfaces new evidence to revisit it.

- **OQ-1 — un-runnable enforcement mechanism.** A *new* `validate_governance_complete()` (governance lens), or rely on the existing `validate_runnable` + absent-optional + safe defaults (schema lens)? **Recommendation: a new `validate_governance_complete()` invoked by the existing `validate_runnable`** (do **not** touch `load_procedures` — the loader must keep accepting drafts so the review UI renders them, D6). Verified rationale: `validate_runnable` (`orchestrator.py:113`) today checks trigger / `step_kinds` / `autonomy_ceiling` / handler-in-allowlist, but a stub `action` with `handler=None` *passes* its handler guard (`if step.handler is not None`) and `autonomy` defaulting to `gated` *looks* authored (R-5) — so safe-defaults alone do **not** make a skeleton un-runnable. An explicit stub-rejecting check, called from the existing run-gate, is the cleanest way to get the two-state property (D6) without a new loader path. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-2 — where the archetype-template artifact lives** (`verticals/_archetypes/` vs `services/engine/procedures/archetypes/`), and whether it gets its own loader/validator now or rides in the generator package. **Recommendation: `services/engine/procedures/archetypes/`** — the template is engine-generic and vertical-agnostic (ADR-016 D6: the engine lives in `services/`, per-vertical config in `verticals/<name>/`); `verticals/_archetypes/` would mis-signal it as per-vertical config. Give it a thin loader/validator now, with a CI assertion that every instantiated template round-trips `load_procedures`. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-3 — classification granularity:** whole-procedure archetype label, per-step `gate_kind` labels, or both? **Recommendation: both** — the whole-procedure label drives template instantiation (the structure), and per-step `gate_kind` is emitted *and* checked against the archetype's signature (the D4 agreement invariant). They are complementary, not alternatives. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-4 — is generated `goal` in v1, or deferred?** `goal` is a runtime LLM directive (D5) = executable prompt surface (leak class 3), higher-stakes than skeleton structure. **Recommendation: generate `goal` in v1 but treat it as runtime-executable prompt surface** — subject it to the prose-lint (D3) *and* give it elevated, code-level review scrutiny in the gate (not doc-string scrutiny). Conservative fallback if that scrutiny is not ready for v1: **defer `goal` generation** (human authors `goal`, generator leaves it empty). **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-5 — stub representation encoding:** sentinel token (`"<STUB:threshold>"`) vs a parallel `governance_todo: [...]` worklist vs `*_authored` flags. **Recommendation: the hybrid** — a typed, unambiguous sentinel (invalid as a real value; not `None`/`0`/`""`) as the in-field block, *plus* a derived `governance_todo` worklist enumerating each obligation. The obligation set is **deterministically derivable** from `gate_kind` + `kind` (`in_file_band` ⇒ threshold/direction/margin; `kind: action` ⇒ handler + autonomy-confirm), so the human cannot "forget" a field. Leave the exact encoding to PLAN-0040. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-6 — single- vs multi-procedure per narrative** (procurement ships hero + calm in one file). **Recommendation: one-procedure-per-run for v1** (matches abstain semantics + keeps the review surface focused); a multi-procedure file is assembled by appending runs. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-7 — cross-ontology wiring validation depth in v1.** **Recommendation: v1 validates `input.from` references resolve linearly** (already enforced by `validate_runnable`, verified `orchestrator.py:135`) but scopes deep cross-ontology object-ref validation (does `output` name a real `object_type`) as **authoring-time / out of the generator** for v1 — the generator emits structure; deep wiring is a follow-on. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-8 — AT-2's rule/criteria/DOA-tier CONTENT has no typed schema home today** (it lives in prose). Even with AT-2 deferred, this is the one latent prose-smuggling surface the schema does not yet close. **Recommendation: flag it as a real gap and make a typed, human-only sub-model for scored-rule / compliance-criteria / DOA-tier content a *precondition* for any future AT-2 generation** (not v1 work; ties to D11 / OQ-A3). **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).
- **OQ-9 (meta) — standalone ADR-0024 vs an ADR-016 amendment.** **Recommendation: confirm standalone** (already founder-approved). The facet field was an *amendment* because it directly extended the D2 `Step` grammar; the generator is broader — it introduces a new authoring-time invariant (distinct from ADR-016's runtime guardrail), a new spec layer (the template artifact), a new pipeline contract, and a new UI surface. It only *implements* ADR-016 D7 Phase 2. **Cray adjudicated → ACCEPTED** (finalized at its consuming PLAN).

## Alternatives Considered

### Alternative 1: Free-form (or hybrid) generation — the LLM emits `Step`/`Procedure` structure directly

- **Pros:** maximal flexibility; no template artifact to build; handles novel shapes.
- **Cons:** the LLM authors governance-bearing structure (gate placement, step order, handler selection) with no closed vocabulary to match into; reopens every leak class; violates classify-don't-synthesize (ADR-0021).
- **Why rejected:** archetype-first (D1) confines the LLM to *classification + advisory prose*; structure is synthesized by deterministic code from a human-curated template. Cray locked archetype-first in session 78.

### Alternative 2: Keep "governed ≠ generated" as a prompt instruction (the runtime guardrail, unmodified)

- **Pros:** no new draft type; least code.
- **Cons:** the runtime guardrail does not cover the authoring surface (Context); a prompt instruction is a behaviour we *hope* for, and `extra="forbid"` gives false assurance against prose-smuggling.
- **Why rejected:** D3 makes the guardrail mechanical — a restricted draft type (leak = type error) + a prose-lint. The invariant is enforced by construction and proven in the offline gate (D12).

### Alternative 3: Add a new "looser" draft model that is a superset/relaxation of `Step`

- **Pros:** one model; the draft "is" a Step with optional governance.
- **Cons:** a looser model still *has* the governance fields, so the generator *can* populate them — the disjointness guarantee (D12 layer 1) is impossible; this is the schema lens's explicit "no draft/looser model" caution inverted.
- **Why rejected:** the draft type is a strict *subset* with no governance fields (D3); the lift injects stubs. Disjointness is structural, not hoped-for.

### Alternative 4: Include AT-2 generation in v1

- **Pros:** covers the highest-value (procurement) archetype immediately.
- **Cons:** AT-2 is N=1 (verified) — generating it violates Rule-of-Three on the governance-heaviest archetype; its rule/criteria/DOA content has no typed home (OQ-8); a down-classification silently deletes controls.
- **Why rejected:** AT-2 deferred to hand-author until a real 5th-vertical AT-2-class example triangulates it (D7); the abstain path (D5) routes AT-2 narratives safely.

### Alternative 5: Two separate UIs (a standalone facet viewer + a separate generator gate)

- **Pros:** each ships independently.
- **Cons:** two divergent renderers of the same object.
- **Why rejected:** one component, read-mode ↔ edit-mode; read-only viewer ships first and the generator reuses it (D8).

### Alternative 6: Fold this into ADR-016 as a third amendment

- **Pros:** keeps the procedure-engine decisions in one ADR.
- **Cons:** the generator introduces a new authoring-time invariant, a new spec layer, a new pipeline, and a new UI — ADR-scale, broader than a `Step`-grammar extension.
- **Why rejected:** standalone ADR-0024 (OQ-9; founder-approved). It *implements* ADR-016 D7 Phase 2 rather than extending its grammar.

## References

- ADR-016 (governed procedure engine — D2/D2-Amendment/D3/D5/**D7 Phase 2**; the runtime "governed ≠ generated" guardrail this ADR re-fences for authoring) — `docs/adr/0016-governed-procedure-engine.md`
- ADR-0021 (metric-kind typed semantics — D2 classify-don't-synthesize / `measured_kind`) — `docs/adr/0021-metric-kind-typed-ontology-semantics.md`
- ADR-0019 (`watch → gated`-proposal routing — the determinism invariant) + ADR-010 (LLM reasoning-hook surface — **IN-3** confidence is advisory) — `docs/adr/0019-watch-gated-proposal-routing.md`, `docs/adr/0010-llm-reasoning-hook-surface.md`
- ADR-006 (vertical plugin architecture — **D4 Rule of Three**, "concrete-first or nothing") — `docs/adr/0006-vertical-plugin-architecture.md`
- ADR-007 (OCT engine contracts — D2 `RecommendedAction` envelope, untouched); ADR-008 (YAML ontology — codegen path untouched; `procedures.yaml` engine-read)
- ADR-009 D1/D2 (Cowork drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 (phased autonomy relocation — Cowork = advisory governance drafter)
- `services/engine/procedures/spec.py` — the `Step`/`Procedure`/`Agent` schema (`GateKind` 6-kind enum; `StepFacet`/`DecisionCondition`; `extra="forbid"`; `_validate_step` autonomy-defaults-`gated`; `load_procedures` shape+cross-ref only)
- `services/engine/procedures/orchestrator.py` — `validate_runnable` (the run-time pre-flight; the OQ-1 substrate)
- `docs/conventions/procedure-archetypes.md` — the N=4 archetype catalog (AT-1 / AT-1b / AT-2 / AT-3) + governance signatures + the band-authoring split
- `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml` — the N=4 substrate (the N≈2 verification)
- `docs/plans/done/0037-stage2-facet-retrofit-archetype-catalog.md`, `docs/plans/done/0038-adr016-facet-field-impl.md` — the Stage-2 PREP + facet-field implementation this builds on
- PLAN-0017 (live co-creation intake face — the intake reused wholesale, D9)
- CLAUDE.md §3 (three-layer architecture), §4 (canonical→derived), §8 (AI assistive; data residency; offline oracle is the gate)

## Implementation Notes

This ADR is a capability + authoring-invariant decision; all mechanics are deferred to two follow-on PLANs, each its own dispatch, in this order (D8):

1. **PLAN-0039 — the read-only 5-facet review UI.** Ships first; zero-LLM; renders the four existing `procedures.yaml` by their five facets with provenance colour-coding. Demoable immediately; de-risks the rendering the generator gate reuses.
2. **PLAN-0040 — the archetype generator.** The prerequisite `ArchetypeTemplate` artifact (D2) + the two-call pipeline (D1) + the restricted draft type + prose-lint (D3) + the stub/`governance_todo` contract (OQ-5) + the offline-test contract (D12) + the gate in edit mode (D8). **AT-1 family only** (D7).

Out of scope (→ later PLANs): the literal code; AT-2 generation; running a generated procedure (Phase-1's shipped orchestrator); branch/loop/multi-procedure/swarm (ADR-016 D7 Phase 4+); any runtime consumption of facets (D2-A4 holds); typed live `llm_assist` / facet↔band cross-validation in `spec.py` (OQ-A2/A3 stay deferred-in-engine); a template-management CRUD UI.

Status flips Proposed → Accepted on Cray ratification; Code applies + commits via a `docs/*` PR (ADR-009 D2; CLAUDE.md §6 Decision Flow). AI-assisted (Cowork drafter); no `Co-Authored-By` per CLAUDE.md §7.
