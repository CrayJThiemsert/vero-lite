# PLAN-0040: Archetype-first procedure generator (ADR-0024 PLAN-β) — narrative → governed skeleton behind the human-review gate (AT-1 family v1)

**Status:** Ready for execution
**Owner:** Claude Code
**Created:** 2026-06-26
**Related ADRs:** ADR-0024 (the decision spine — D1–D12 + the nine Cray-ratified OQs, *finalized here*; the G/H/D partition table D3; the offline-test contract D12), ADR-016 (D2 `Step` grammar + the 2026-06-25 typed-`facet:` amendment — the schema this authors; **D7 Phase 2** this realizes; the runtime "governed ≠ generated" guardrail re-fenced for authoring), ADR-0021 (classify-don't-synthesize / `measured_kind` — the D1 spine), ADR-0019 + ADR-010 IN-3 (the determinism invariant, extended to the authoring layer D5), ADR-006 (D4 Rule-of-Three — admits AT-1, defers AT-2), ADR-001 (MS-S1-local `gpt-oss:20b` — residency, CLAUDE.md §8), ADR-009 D1/D2 (Cowork drafts, Code commits), ADR-012 D4.3 (author≠reviewer disclosure), ADR-013 (phased autonomy relocation — Cowork = advisory governance drafter). Builds on PLAN-0039 (the read-only viewer + the AC-7 `facetModel` seam this grafts edit-mode onto), PLAN-0038 (the typed `facet:` field), PLAN-0017 (the intake face reused, D9), PLAN-0022 (the authored band + `tiers` taxonomy).

> **Provenance / author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray (session-78 sequencing + session-80 explicit go to start PLAN-0040) + ADR-0024 D1–D12 (Accepted; all 9 OQ recommendations Cray-ratified, finalized at this consuming PLAN) + the Code-run 5-specialist design panel. Drafter = Cowork (Tier-1 governance authoring, ADR-009 D1 interim per ADR-013 phased relocation). Reviewers = Cray (ratification) + Code R2 (commit). The substance was **not** self-deliberated in Cowork's own free-form mode — it descends from the Accepted ADR-0024 — so the independent-deliberation check is exercised. The §"Surfaced Open Questions" forks (OQ-A…E) are presented with options + a recommendation, **not** silently resolved. Drafted **uncommitted**; Code commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). **Cowork does not git** (G5 binds).

---

## Goal

Ship a **governed procedure generator** (ADR-016 D7 Phase 2, archetype-first): a vertical's stakeholder **narrative** → an **LLM classifies it to one catalogued archetype** (closed enum) → **deterministic code instantiates that archetype's template** (step skeleton + wiring) → **the LLM drafts only advisory prose** → a **`Procedure` skeleton** presented behind a **human-review gate**, where **every governance value is a human-author stub**. The acceptance output is a `load_procedures`-valid `procedures.yaml` **draft, uncommitted, behind the gate** (no run, no auto-commit). **v1 generates the AT-1 family only — AT-1 / AT-1b / AT-3 (modelled as an AT-1 base + variants); AT-2 is deferred** (N=1, governance-heaviest — routes to hand-author via the abstain path). The thesis made mechanical: the generator emits *shape + advisory prose only*, the shape is *inert until authored*, and a governance leak is a **type error or a lint failure caught in the offline gate** — never a model behaviour we hope for.

## Fact-pack findings (verified against the live repo — Tier-1 rule #4)

These confirm the substrate ADR-0024 + the dispatch assumed, and surface **two divergences** that shape the build (flagged rather than silently absorbed).

1. **The OQ-1 run-gate gap is real and located.** `validate_runnable` (`services/engine/procedures/orchestrator.py:113`) guards a handler only when present — `if step.handler is not None and step.handler not in agent.allowed.action_handlers` (line 154). A stub `action` with `handler=None` therefore **passes** the run-gate, and `autonomy` defaults to `gated` in `_validate_step` (`spec.py:301-304`) so a stub *looks* authored. Confirms D6/OQ-1: a **new** `validate_governance_complete()` is required; safe-defaults alone do not make a skeleton un-runnable.
2. **`input.from` linearity is already enforced** at `orchestrator.py:135-141` (a `from` that is not an earlier step raises `ProcedureError`). Confirms OQ-7: v1 leans on the existing linear check; deep cross-ontology object-ref validation stays out of scope.
3. **`StepDraft` / `ProcedureDraft` / `ArchetypeTemplate` / `GOVERNANCE_FIELDS` / `validate_governance_complete` / `governance_todo` are net-new in code** — a repo-wide grep finds them **only** in docs (ADR-0024, PLAN-0039, STATUS.md), never in `services/`. Confirms D3 "verified net-new." `services/engine/procedures/` today holds `spec.py` + `orchestrator.py` + `runs.py`; `archetypes/` (OQ-2 home) does not yet exist.
4. **The AT-1-family governance signature is simple — the `judge` step is the only non-`none` gate.** Verified across the live `procedures.yaml`: AT-1 `[none, env_band|in_file_band, none]`; AT-1b (`aquaculture`) `[none, in_file_band, none, none, none]`; AT-3 (`procurement.low_stock_reorder`) `[none, in_file_band, none]`. So for v1 the archetype-agreement oracle (D12-3) reduces to: the `judge` step **must** be a band kind (`env_band` or `in_file_band`), never `none` and **never** an AT-2-only kind (`scored_rule` / `rule_gate` / `doa_tier`); every other step is `none`. A v1 skeleton that would need an AT-2-only `gate_kind` is an **abstain**, not a down-classified AT-3.
5. **The H-class stubs the AT-1 family must leave** (from the live shapes): on `judge` — `threshold`/`direction`/`watch_margin` (in-file band) **or** `facet.decision_condition.env_var` (env band); on each `action` — `handler`, `autonomy` (a confirmed stub even at its `gated` default), `tiers` (optional); on `Procedure` — `run_by`; on `Agent` — `llm_model`, `autonomy_ceiling`, `allowed.step_kinds`, `allowed.action_handlers`. These are exactly the **never-G** fields in the ADR-0024 D3 table.
6. **DIVERGENCE A — the AC-7 `facetModel` seam is reusable but edit-mode needs three concrete extensions** (the dispatch's "reuse `facetModel` UNCHANGED + flip `editable`" is *nearly* but not *exactly* true). Verified in `services/api/static/assets/view-procedures.js`: (a) `facetModel` hard-codes `editable: false` on every field (`field = (label, value, provenance) => ({…, editable: false})`, line 38) — edit-mode needs `editable` **derived from the field's G/H/D class**, not a constant; (b) `facetModel` only emits a field **when it is present** (`if (step.handler) …`, lines 42-71) — a *stub* field (absent value) won't render at all, so the "YOU must author" zone needs the stub surfaced even when unset; (c) `renderField` already has the seam branch but renders the input `disabled: true` (line 276) — edit-mode must un-disable it. **Net:** the seam genuinely avoids a rewrite, but Phase C is a *small, real* extension of `facetModel` + `renderField`, not a zero-line flip. Surfaced so the PLAN budgets it.
7. **DIVERGENCE B — an in-field sentinel is incompatible with the typed `Step` schema** (a fact-pack correction to ADR-0024 OQ-5's "in-field sentinel" lean — see OQ-C). `Step.threshold` is `float | None`, `Step.handler` is `str | None`, etc., under `extra="forbid"`. A sentinel like `"<STUB:threshold>"` **cannot** be carried in `Step.threshold` (Pydantic rejects a non-float), and a generated skeleton must stay `load_procedures`-valid (D6). Making the sentinel fit would require widening the *runtime* schema in `spec.py` — forbidden (ADR-0024 keeps `spec.py` untouched; OQ-A2 keeps integrity checks out of `spec.py`). Resolution in OQ-C: the stub is the field **absent** on the lifted `Step` (its valid `None` state) + the obligation carried in a derived `governance_todo`; the sentinel, if any, lives only in the **draft layer** (`StepDraft`/`ProcedureDraft`), never in a typed `Step`.

## LOCKED (from ADR-0024 — render faithfully; do NOT re-litigate)

Each maps to an Accepted ADR-0024 decision; built to, not reopened.

- **LOCKED-1 (D1)** — archetype-first, deterministic-code-dominant, **exactly two narrow LLM calls** (classify + advisory-prose). Pipeline **S0** normalize → **S1** classify *(LLM)* → **S2** abstain-gate → **S3** template-instantiate → **S4** stub-stamp → **S5** prose-draft *(LLM)* → **S6** assemble + validate-against-`spec.py` + provenance; a capped validate→repair-retry loop feeds the exact Pydantic error back to the prose call, then abstains. LLM = MS-S1-local `gpt-oss:20b` constrained-decode, low temp. Classify-don't-synthesize (ADR-0021): the LLM selects from a closed enum; **code** synthesizes structure; the generator **never invents** an archetype or a `gate_kind`.
- **LOCKED-2 (D2)** — promote the prose archetype catalog to a machine-readable `ArchetypeTemplate` artifact (Pydantic model + derived registry **with slots to instantiate**). Prose `docs/conventions/procedure-archetypes.md` stays **canonical**; the template is **derived** (canonical wins, CLAUDE.md §4). Model **AT-1b and AT-3 as variants of an AT-1 base** (base skeleton + declared deltas). Each instantiated template round-trips `load_procedures` — **CI-asserted**. Lives in **`services/engine/procedures/archetypes/`** (OQ-2).
- **LOCKED-3 (D3)** — "governed ≠ generated" is MECHANICAL, two mechanisms: (1) a **restricted draft type** (`StepDraft`/`ProcedureDraft`) with **no governance fields**; a deterministic lift `StepDraft → Step` injects them as un-filled stubs (leak = a type error at the boundary). (2) a **deterministic prose-lint** rejecting numerics / currency / handler-names / selection-or-approval verbs in generated `goal`/`description`/`facet.*` prose. Built to the **G/H/D partition table** (ADR-0024 D3).
- **LOCKED-4 (D4)** — the sharp line: generator MAY emit `decision_condition.gate_kind` (+ `band_source`, leaning G); MUST NOT emit any value/binding/authority. A generated `gate_kind` contradicting the matched archetype's signature is a **HARD validation failure** (finding #4: AT-1-family `judge` must be a band kind; non-`judge` must be `none`).
- **LOCKED-5 (D5)** — classification **abstains, never force-fits**; the matched archetype is **human-confirmed before any skeleton is built**; generation is **never routed on the LLM's match-confidence** (the ADR-0019 / ADR-010 IN-3 invariant at the authoring layer — the route is a deterministic, auditable match + human confirm).
- **LOCKED-6 (D6)** — two states: **draft-loadable** (`load_procedures` keeps accepting drafts — do NOT touch it) but **NOT run-loadable** until a human authors the gates (OQ-1: a new `validate_governance_complete()` invoked by `validate_runnable`).
- **LOCKED-7 (D7)** — v1 breadth = the AT-1 family (AT-1 / AT-1b / AT-3). **AT-2 generation is DEFERRED**; an AT-2-class narrative routes to hand-author (the abstain path), never a down-classified AT-3 skeleton.
- **LOCKED-8 (D8)** — one review surface: the gate **IS** the PLAN-0039 component in edit-mode (reuse `facetModel`; flip `editable` on H-class fields per finding #6; `mode:'edit'`). Three visually-separated zones per step: **LLM-drafted (advisory)** · **YOU must author (governance stubs)** · **archetype expectation (the oracle)**. No second renderer.
- **LOCKED-9 (D9)** — intake reuses the PLAN-0017 face wholesale (hybrid free-text → MS-S1-local single-shot constrained-decode → mandatory human-review gate → graceful degradation to a manual archetype-pick on cold/low-confidence).
- **LOCKED-10 (D10)** — acceptance output = a `load_procedures`-valid draft, **uncommitted, behind the gate**; never written into `verticals/<name>/procedures.yaml` directly; no run; no auto-commit (ADR-009 D2).
- **LOCKED-11 (D11)** — the ADR-016 amendment OQs resolve here: OQ-A1 refuse-never-invent (enum/catalog growth stays human-authored + additive); OQ-A2 facet↔typed integrity enforced at the **generation/review boundary ONLY, never in `spec.py`**; OQ-A3 type `llm_assist` in the **`ArchetypeTemplate`** as `{role: draft|summarise, of: <field>}` but **emit the live `Step.facet.llm_assist` as prose `str`** (no live-schema churn).
- **LOCKED-12 (D12)** — three binding offline tests (structural disjointness; poisoned-narrative red-team; archetype-agreement invariant); the LLM step is stubbed with a **recorded fixture** so the red-team layer is deterministic + offline.

**Other Cray-ratified OQ guidance folded in:** OQ-3 classify at **both** granularities (whole-procedure label drives instantiation; per-step `gate_kind` emitted *and* checked); OQ-6 **one-procedure-per-run** for v1 (a multi-procedure file is assembled by appending runs); OQ-7 v1 validates `input.from` resolves linearly (already in `validate_runnable`, finding #2); OQ-8 **flag** that AT-2's rule/criteria/DOA-tier CONTENT has no typed schema home and name a typed human-only sub-model as a **precondition for any future AT-2** (NOT v1 work).

## Acceptance Criteria

Grouped by the three phases (OQ-A). **Phase A is the gate-defining, moat-critical, fully-offline landing**; B and C build on it.

### Phase A — the offline guardrail spine (zero-LLM)

- [ ] **AC-A1 — `ArchetypeTemplate` artifact (LOCKED-2 / D2).** A Pydantic `ArchetypeTemplate` model + a derived registry in **`services/engine/procedures/archetypes/`**, modelling an **AT-1 base + AT-1b / AT-3 variant deltas** (not three disjoint shapes), each with **slots to instantiate** (step sequence, per-step `kind` + `gate_kind` + which fields are G/H/D). A thin loader/validator. `Field(description=...)` on every field (CLAUDE.md §8).
- [ ] **AC-A2 — every instantiated template round-trips `load_procedures` (CI-asserted).** A test instantiates each AT-1-family template into a `procedures.yaml`-shaped mapping and asserts it loads via `load_procedures` (shape + cross-ref clean) — the D2 round-trip invariant.
- [ ] **AC-A3 — restricted draft type + lift (LOCKED-3 mechanism 1 / D3).** `StepDraft` / `ProcedureDraft` Pydantic types with **zero** governance fields (no `threshold`/`direction`/`watch_margin`/`handler`/`tiers`/`autonomy`/`env_var`/DOA-amount/scored-rule content; agent-side no `autonomy_ceiling`/`allowed.*`). A deterministic `lift_to_step(StepDraft) -> Step` that injects the governance fields as **absent stubs** (finding #7: absent `None`, never an in-field sentinel) and produces a `load_procedures`-valid `Step`.
- [ ] **AC-A4 — structural disjointness test (LOCKED-12-1 / D12).** A `GOVERNANCE_FIELDS` frozenset + a test asserting `GOVERNANCE_FIELDS.isdisjoint(set(StepDraft.model_fields))` (and the `ProcedureDraft`/agent-draft analogue). Adding `threshold` to the draft type later **fails CI** — the guardrail cannot silently erode.
- [ ] **AC-A5 — deterministic prose-lint (LOCKED-3 mechanism 2 / D3).** A pure `prose_lint(text) -> [violations]` rejecting numerics / currency symbols / registered handler-names / selection-or-approval verbs, run over every generated `goal`/`description`/`facet.*` string. Unit-tested on positive + negative cases.
- [ ] **AC-A6 — `validate_governance_complete()` (LOCKED-6 / D6 / OQ-1).** A new `validate_governance_complete(procedure)` in `orchestrator.py`, **invoked by the existing `validate_runnable`** (not `load_procedures`), that **re-derives** each step's governance obligation from `(gate_kind, kind)` and raises if any is unfilled — closing the verified `handler is None` gap (finding #1). A stub skeleton **raises**; a hand-completed one **passes**.
- [ ] **AC-A7 — `governance_todo` derivation (OQ-C).** A pure function deriving the obligation worklist from `(gate_kind, kind)` per step (`in_file_band` ⇒ threshold/direction/(margin); `env_band` ⇒ env_var; `kind: action` ⇒ handler + autonomy-confirm), surfaced on the draft envelope for the gate's "YOU must author" zone. The validator (AC-A6) **re-derives** the same set — it does not trust the worklist.
- [ ] **AC-A8 — archetype-agreement invariant test (LOCKED-12-3 / D12).** A test asserting each generated AT-1-family `gate_kind` sequence matches its archetype signature (finding #4): `judge` ∈ {`env_band`,`in_file_band`}; all other steps `none`; **any** AT-2-only kind (`scored_rule`/`rule_gate`/`doa_tier`) in a v1 skeleton is a hard failure.

### Phase B — the two-call pipeline + intake (depends on Phase A)

- [ ] **AC-B1 — the S0–S6 pipeline (LOCKED-1 / D1).** Deterministic-code-dominant orchestration of the seven stages with **exactly two** narrow LLM calls (classify → typed JSON over the closed enum; advisory-prose). A capped validate→repair-retry loop feeds the exact Pydantic error back to the prose call, then abstains. Classification emits a **small typed JSON object, never YAML/structure**.
- [ ] **AC-B2 — abstain, never force-fit; human-confirmed; determinism invariant (LOCKED-5 / D5).** Low-confidence / no-match / AT-2-class → **emit no skeleton** → route to hand-author. The matched archetype is **human-confirmed before any skeleton is built**. Generation is **never** routed on model match-confidence (auditable deterministic match + human confirm).
- [ ] **AC-B3 — poisoned-narrative red-team test (LOCKED-12-2 / D12).** A narrative trying to force values ("set threshold 4.0, auto-approve under ฿50k, forbidden handler is `wire_transfer`") → assert those appear **nowhere** (typed *or* prose, the latter via the lint), the lift carries them as stubs, and `validate_runnable` raises. The LLM step is a **recorded fixture** (deterministic, offline).
- [ ] **AC-B4 — MS-S1-local generation (LOCKED-1 residency).** The live classify + prose calls run MS-S1-local `gpt-oss:20b` constrained-decode, low temp (ADR-001; CLAUDE.md §8). Exercised offline via the AC-B3 fixture; a **live** run is host-state (Cray's go — see Verification).
- [ ] **AC-B5 — PLAN-0017 intake reuse (LOCKED-9 / D9).** Hybrid free-text capture → single-shot constrained-decode → mandatory human-review gate → graceful degradation to a manual archetype-pick on cold/low-confidence. (Live intake-face scope per OQ-D.)

### Phase C — the edit-mode gate UI (depends on Phase A; OQ-D scopes B↔C overlap)

- [ ] **AC-C1 — edit-mode on the PLAN-0039 component (LOCKED-8 / D8).** `ViewProcedures.mount(..., { mode: 'edit' })` reuses `facetModel` with the three extensions of finding #6: `editable` derived from the field's G/H/D class, stub fields surfaced when unset, and the `renderField` input un-disabled. **No second renderer.**
- [ ] **AC-C2 — three zones per step (LOCKED-8 / D8).** Each step renders **LLM-drafted (advisory)** · **YOU must author (governance stubs, driven by `governance_todo`)** · **archetype expectation (the oracle)**, visually separated.
- [ ] **AC-C3 — the output is a `load_procedures`-valid draft, uncommitted, behind the gate (LOCKED-10 / D10).** The gate yields a draft that round-trips `load_procedures` but **fails `validate_governance_complete`** until authored; never written to `verticals/<name>/procedures.yaml`; no run; no auto-commit.

## Out of Scope

- ❌ **AT-2 generation** (LOCKED-7 / D7) and its typed rule/criteria/DOA-tier sub-model (OQ-8 — a **precondition** for any future AT-2, not v1).
- ❌ **Running** a generated procedure (the shipped orchestrator executors); any change to `run_procedure`/`execute_steps` beyond the new `validate_governance_complete` call.
- ❌ **Auto-commit / write-back** into `verticals/*/procedures.yaml` (LOCKED-10; ADR-009 D2).
- ❌ Branch / loop / **multi-procedure-per-run** / swarm (ADR-016 Phase 4+; OQ-6 = one-per-run v1).
- ❌ Facet **runtime consumption** — the engine still does not read `facet` to drive behaviour (D2-A4 holds).
- ❌ Deep cross-ontology object-ref validation (does `output` name a real `object_type`) — OQ-7 (v1 leans on the existing linear `input.from` check, finding #2).
- ❌ Typed live `llm_assist` / facet↔band cross-validation **in `spec.py`** (OQ-A2/A3 stay deferred-in-engine; `spec.py` is untouched).
- ❌ A template-management / CRUD UI; persisting gate state; any DB.
- ❌ Editing `spec.py`'s runtime schema (no sentinel field, no draft union — finding #7). The draft types are a **new, separate** package.
- ❌ (Conditional on OQ-A/OQ-D) the **live MS-S1 intake face** and **generated `goal`**, if Cray defers them per those forks.

## Surfaced Open Questions for Cray (options + recommendation; Cray adjudicates)

ADR-0024 left these residual build-level forks to "the consuming PLAN." Each is presented with options + a recommendation; **none silently resolved**.

- **OQ-A — build-sequencing / slice (the big one).**
  - *Option A1 (recommended):* **one PLAN-0040, three internal phases A → B → C, with Phase A (the offline spine) a hard, independently-merged boundary** — the D12 offline tests are green on Phase A alone before B starts. Keeps the ADR-0024 "PLAN-0040 = the generator" structure + single ADR→PLAN traceability; gives the low-risk first landing; lets the spine teach the pipeline's real shape before B.
  - *Option A2:* **split now** — PLAN-0040 [offline spine] + a new PLAN-0041 [pipeline + intake + gate UI]. Cleaner per-PLAN size, but mints a second G2-gated PLAN (another Cowork dispatch) before the spine exists to inform it.
  - **Recommendation: A1, with A2 as the fallback _at the Phase-A boundary_** — if Phase A proves larger than ~one session, split B+C into PLAN-0041 then (an evidence-based split point, not an upfront guess). **Cray adjudicates.**
- **OQ-B — generated `goal` in v1, or defer? (finalizes ADR-0024 OQ-4.)** `goal` is a runtime LLM directive = executable prompt surface (leak class 3), higher-stakes than skeleton structure.
  - *Option B1:* generate `goal` in v1, behind the prose-lint **and** the D8 elevated-scrutiny zone.
  - *Option B2 (recommended):* **defer `goal` generation until the edit-mode gate's elevated-scrutiny zone ships** — until then the generator leaves `goal` empty (`goal: ""`, already the `spec.py` default) and the human authors it. Concretely: **goal-generation rides with Phase C** (the gate). If OQ-A defers the gate to PLAN-0041, goal-gen defers with it. Rationale: generating the highest-stakes G-field *without* the elevated-review affordance present is the exact leak-class-3 risk; tie it to the affordance. **Cray adjudicates.**
- **OQ-C — the exact stub encoding (finalizes ADR-0024 OQ-5; see finding #7).** ADR-0024 leaned a hybrid (in-field **sentinel** + derived `governance_todo`). **Fact-pack correction:** an in-field sentinel is incompatible with the typed `Step` schema (a non-float in `Step.threshold` fails Pydantic; making it fit means widening the runtime schema in `spec.py` — forbidden).
  - *Option C1 (recommended):* **drop the in-field sentinel for typed `Step` fields.** The stub = the governance field **absent (`None`)** on the lifted `Step` (its valid state, `load_procedures`-clean) + the obligation carried in a derived **`governance_todo`** worklist on the draft envelope (deterministically derived from `(gate_kind, kind)`). `validate_governance_complete()` **re-derives** the obligation set and refuses the run if any is unfilled (the gate does not trust the worklist; the worklist is the human's authoring aid). In the **draft layer only** (`StepDraft`/`ProcedureDraft` — never a typed `Step`), a typed `GovernanceStub {field, reason, archetype_expectation}` records each obligation for the gate's "YOU must author" zone.
  - *Option C2:* widen `spec.py` to accept a sentinel union on the typed fields — **rejected** (pollutes the runtime schema; violates ADR-0024's untouched-`spec.py` constraint + OQ-A2).
  - **Recommendation: C1.** **Cray adjudicates** (this is the one fork where the PLAN diverges from the ADR's lean — surfaced per Tier-1 rule #12).
- **OQ-D — v1 UI + live-intake scope.** The pipeline is fully exercisable offline via the D12 recorded fixture; the live intake face is a host-state surface (MS-S1, CLAUDE.md §8).
  - *Option D1 (recommended):* **v1 lands the edit-mode gate render (AC-C1/C2/C3) exercised against a recorded-fixture draft (offline); DEFER the live MS-S1 single-shot intake face to a follow-on milestone** (Phase C-live, gated on Cray's host-state go). Everything provable offline ships; the one host-state surface lands last + minimal.
  - *Option D2:* land the live intake face in v1 too (more demoable, but a host-state dependency in the v1 gate).
  - **Recommendation: D1** (ties to OQ-A: the gate render is Phase C; the live intake is the last, host-state-gated step). **Cray adjudicates.**
- **OQ-E — acceptance / demo evidence.** The three D12 offline tests are the **gate**; a live generation is **evidence** (CLAUDE.md §8).
  - **Recommendation:** **Gate (CI / offline)** = AC-A4 (disjointness) + AC-B3 (poisoned-narrative → stubs-not-values + `validate_runnable` raises) + AC-A8 (archetype-agreement) **all green**, + every `ArchetypeTemplate` round-trips `load_procedures` (AC-A2) + `validate_governance_complete` refuses a stub and accepts a hand-completed skeleton (AC-A6) + `ruff`/`mypy --strict` clean. **Evidence (live, Cray's host-state go)** = a poisoned-narrative run on MS-S1 emitting a stub skeleton (values nowhere, `governance_todo` populated) + a clean AT-1-family narrative producing a `load_procedures`-valid draft behind the gate. **Demo artifact** = the poisoned-narrative draft rendered in the gate's three zones. **Cray adjudicates.**

## Steps

### Phase A — the offline guardrail spine (zero-LLM, moat-critical, the gate-defining landing)

#### Step A1: `ArchetypeTemplate` artifact + registry (AC-A1 / AC-A2)
- New package `services/engine/procedures/archetypes/` (net-new, finding #3). Define `ArchetypeTemplate` (Pydantic, `extra="forbid"`, `Field(description=...)`): an ordered step-slot list, each slot carrying its `kind`, its required `gate_kind` (the oracle), and its G/H/D field map; plus the `llm_assist` typing `{role: draft|summarise, of: <field>}` (LOCKED-11 / OQ-A3).
- Model the **AT-1 base** (read `query`/`none` → `judge` `evaluate`/band → `act` `action`/`none`) + **AT-1b delta** (+ `escalate_watch` `action`/`none` + `summary` `action`/`auto`/`none`) + **AT-3 delta** (calm-reorder intent on the AT-1 base). Source the shapes from `docs/conventions/procedure-archetypes.md` (canonical) + the live `verticals/*/procedures.yaml` (finding #4).
- Thin loader/registry + a CI test instantiating each template and round-tripping `load_procedures` (AC-A2).

#### Step A2: restricted draft type + lift (AC-A3 / AC-A4)
- New module (e.g. `services/engine/procedures/draft.py`): `StepDraft` / `ProcedureDraft` (and an agent-draft) with **zero** governance fields; a `GOVERNANCE_FIELDS` frozenset enumerating the never-G fields (finding #5).
- `lift_to_step(StepDraft) -> Step` injecting governance fields as **absent stubs** (finding #7: `None`, no in-field sentinel); the result round-trips `load_procedures`.
- The structural-disjointness test (AC-A4): `GOVERNANCE_FIELDS.isdisjoint(set(StepDraft.model_fields))` (+ the procedure/agent analogues).

#### Step A3: the deterministic prose-lint (AC-A5)
- Pure `prose_lint(text) -> list[Violation]` rejecting numerics, currency symbols, registered handler-names (sourced from the agent allowlists / handler registry), and selection-or-approval verbs. Unit tests (positive + negative). Run over every generated prose string in S6.

#### Step A4: `validate_governance_complete()` + `governance_todo` (AC-A6 / AC-A7)
- Add `validate_governance_complete(procedure)` to `orchestrator.py`, **called by `validate_runnable`** (do NOT touch `load_procedures`, LOCKED-6). Re-derive each step's obligation from `(gate_kind, kind)`; raise `ProcedureError` if any is unfilled — closing the `handler is None` gap (finding #1) and the `autonomy`-looks-authored gap.
- A pure `derive_governance_todo(...)` (AC-A7) producing the obligation worklist for the draft envelope; the validator re-derives, does not trust it.

#### Step A5: the offline test suite (AC-A4 / AC-A8 + the A6 behaviour)
- Structural disjointness (AC-A4); archetype-agreement invariant (AC-A8, finding #4); `validate_governance_complete` refuses a stub skeleton + accepts a hand-completed one (AC-A6). All zero-LLM. **Phase A is DONE only when these are green** (the gate, CLAUDE.md §8).

### Phase B — the two-call pipeline + intake

#### Step B1: the S0–S6 pipeline (AC-B1 / AC-B2)
- Deterministic-code orchestration of S0 normalize → S1 classify *(LLM, typed JSON over the closed enum)* → S2 abstain-gate (LOCKED-5: low-confidence / no-match / AT-2-class → abstain → hand-author) → S3 template-instantiate (from the AC-A1 registry) → S4 stub-stamp (the AC-A2 lift) → S5 prose-draft *(LLM)* + prose-lint (AC-A5) → S6 assemble + `load_procedures` validate + provenance. The capped validate→repair-retry loop, then abstain.
- Human-confirmed archetype match **before** any skeleton is built (LOCKED-5); the route is the deterministic match, never model confidence.

#### Step B2: MS-S1-local LLM integration (AC-B4) + the recorded fixture (AC-B3)
- Wire the two calls to MS-S1-local `gpt-oss:20b` constrained-decode, low temp (ADR-001; CLAUDE.md §8 residency; never disable reasoning while using `format`). Record a fixture of both calls so the red-team layer (AC-B3) is deterministic + offline. A **live** run is host-state — Cray's go (Verification).
- The poisoned-narrative red-team test (AC-B3).

#### Step B3: PLAN-0017 intake reuse (AC-B5; scope per OQ-D)
- Reuse the PLAN-0017 face: free-text → classify → mandatory review gate → graceful degradation to manual archetype-pick. Live intake-face scope deferred per OQ-D D1 (recorded-fixture path lands in v1; live face host-state-gated).

### Phase C — the edit-mode gate UI (the one review surface)

#### Step C1: edit-mode on the PLAN-0039 component (AC-C1)
- `ViewProcedures.mount(..., { mode: 'edit' })`. Extend `facetModel` per finding #6: derive `editable` from the field's G/H/D class (H-class = editable), surface stub fields when unset, and un-disable the `renderField` input. Reuse the existing palette + provenance classes; **no second renderer**.

#### Step C2: the three zones (AC-C2)
- Per step: **LLM-drafted (advisory)** (the G prose) · **YOU must author (governance stubs)** (driven by `governance_todo`, AC-A7) · **archetype expectation (the oracle)** (the template's required `kind`/`gate_kind`). If OQ-B = B1, the generated `goal` renders in an elevated-scrutiny affordance here.

#### Step C3: the draft output + (host-state) live evidence (AC-C3; OQ-E)
- The gate yields a `load_procedures`-valid draft that **fails `validate_governance_complete`** until authored; uncommitted; no write-back; no run. The **live** MS-S1 generation evidence (OQ-E) runs only with Cray's host-state go.

## Verification

Mapped to the gate-vs-evidence split (CLAUDE.md §8):

- **Gate (CI / offline) — the binding bar:** the three D12 tests green — structural disjointness (AC-A4), poisoned-narrative red-team emitting stubs-not-values with `validate_runnable` raising (AC-B3), archetype-agreement invariant (AC-A8); every `ArchetypeTemplate` round-trips `load_procedures` (AC-A2); `validate_governance_complete` refuses a stub skeleton and accepts a hand-completed one (AC-A6); `ruff` + `ruff-format` clean; `mypy --strict services/` clean. **Phase A alone must clear its slice of this gate before Phase B starts** (OQ-A A1).
- **Evidence (live, Cray's host-state go — minimize live runs, CLAUDE.md §8):** a poisoned-narrative run on MS-S1 `gpt-oss:20b` emitting a stub skeleton (values nowhere; `governance_todo` populated); a clean AT-1-family narrative producing a `load_procedures`-valid draft behind the gate; the gate's three zones rendered. Evidence, **not** the gate.
- **Seam check (D8 / finding #6):** edit-mode reuses `facetModel` with the three named extensions — no second renderer; if a parallel renderer appears, LOCKED-8 is violated even if pixels render.
- **No-regression:** `spec.py` runtime schema untouched (finding #7); `load_procedures` untouched (LOCKED-6); Views A–E + the read-only `GET /procedures` unchanged; the only `orchestrator.py` change is the additive `validate_governance_complete` call.
- **Guardrail-erosion tripwire:** AC-A4 — if anyone later adds a governance field to the draft type, CI fails. The mechanical guarantee, not a hoped-for behaviour.

---

*PLAN-0040 drafted (uncommitted) by Cowork (session 80), Tier-1 governance authoring (ADR-009 D1 interim per ADR-013 phased relocation). Its shape is LOCKED by ADR-0024 D1–D12 (all 9 OQs Cray-ratified, finalized here) — a focused execution PLAN, not a new design fork; the OQ-A…E forks are the residual build-level calls ADR-0024 left to the consuming PLAN, surfaced not silently resolved (two diverge from the ADR/dispatch leans — findings #6/#7 + OQ-C, flagged per Tier-1 rules #4/#12). Code R2-reviews + commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). Cowork does not git (G5). AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*
