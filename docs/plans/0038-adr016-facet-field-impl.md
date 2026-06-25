# PLAN-0038: ADR-016 D2 Amendment — implement the first-class typed `facet:` Step field

**Status:** Draft
**Owner:** Claude Code (Tier 2 execution; this draft authored by the in-harness `plan-drafter` subagent)
**Created:** 2026-06-25
**Related ADRs:** ADR-016 (§ "D2 Amendment (2026-06-25)" — **Accepted**; the literal spec this PLAN executes), ADR-006 (Rule-of-Three — N=4 justifies extraction now), ADR-0019 (determinism invariant — routing on the deterministic verdict, never LLM confidence), ADR-008 (ontology codegen path — **untouched**; `procedures.yaml` is engine-read), ADR-009 D1/D2 (Cowork/plan-drafter drafts, Code commits), ADR-013 (autonomy-axis relocation)

> **Author≠reviewer disclosure (ADR-012 D4.3).** This PLAN was authored by
> the in-harness `plan-drafter` subagent under ADR-009 D1 interim authoring
> per ADR-013's phased relocation; Code commits via PR (ADR-009 D2; G5 binds
> the subagent — it cannot commit). Outline originator = Cray (the D2
> Amendment greenlight + the build-ready next-step framing, session 77,
> 2026-06-25). Independent reviewer = Cray at PR merge ratification, plus
> Code R2-review at commit. Separation between drafter (plan-drafter) and
> reviewer (Cray) is **INTACT** — the drafter does not ratify and does not
> commit. The amendment spec being implemented was itself drafted by Cowork
> and Cray-ratified upstream; this PLAN mirrors it, it does not re-decide it.

## Goal

Implement the ADR-016 **D2 Amendment (2026-06-25, Accepted)** — promote the
5-facet annotation (`input · decision-condition · llm-assist · output ·
governance`) from a YAML *comment* to a first-class, typed, validated,
**optional** `facet:` field on the `Step` model. This is the implementation the
amendment explicitly **deferred** to a follow-on PLAN (amendment § "Scope
boundary": "OUT: the `spec.py` edit + the four-vertical comment→field
migration"). Three deliverables: (A) the `spec.py` engine edit adding the typed
`facet` sub-model exactly per the amendment's illustrative delta — `BandSource`,
`GateKind`, `DecisionCondition`, `StepFacet`, `Step.facet` — while **keeping**
`extra="forbid"`; (B) migrate the four verticals' comment-facets to the real
`facet:` field using the amendment D2-A3 `gate_kind` mapping; (C) load +
validation tests for the new field and its validators. `facet` is **descriptive
metadata only** — the engine still ignores it at run time (D2-A2/A4); v0 makes
it readable, not consumed.

> **Framing note — first deliberate engine-path edit since CQ-1.** The
> procurement vertical (PLAN-0036) held literal **zero-engine-edit** (CQ-1):
> all four verticals reached 5-facet instrumentation as **config-only** comment
> blocks *precisely because* `Step`'s `extra="forbid"` would reject a real
> `facet:` key. This PLAN is the **first conscious, ADR-sanctioned edit to
> `services/engine/procedures/spec.py`** since that boundary. The D2 Amendment
> *is* the authority that sanctions it (that is exactly why a real-field
> promotion was an ADR amendment, not a config change — amendment Consequences).
> Treat the engine edit as the sensitive, reviewable core of this work.

## Acceptance Criteria

- [ ] **AC-1 (spec delta, literal):** `spec.py` adds the typed `facet` field to
      `Step` exactly per the amendment delta — `BandSource(StrEnum)` (`env` /
      `in_file`); `GateKind(StrEnum)` with the **six** kinds (`env_band`,
      `in_file_band`, `rule_gate`, `scored_rule`, `doa_tier`, `none`);
      `DecisionCondition(BaseModel, extra="forbid")` with `gate_kind` /
      `band_source` / `env_var` / `note`; `StepFacet(BaseModel, extra="forbid")`
      with `decision_condition` + `llm_assist` (typed) and `input` / `output` /
      `governance` (optional non-authoritative `str` notes); and
      `Step.facet: StepFacet | None = Field(default=None, ...)`.
- [ ] **AC-2 (`extra="forbid"` retained):** `Step.model_config` keeps
      `ConfigDict(extra="forbid")` — `facet` is now a **known** key; any other
      unknown key is still rejected (the safety is preserved, not dropped — D2-A1).
- [ ] **AC-3 (`DecisionCondition` validator):** a `@model_validator(mode="after")`
      enforces (i) `band_source` is set **iff** `gate_kind ∈ {env_band,
      in_file_band}`, and (ii) `env_var` is set **only** when
      `band_source == env`. Violations fail loudly at load (D2-A3).
- [ ] **AC-4 (backward-compatible — mirror PLAN-0022 AC-9):** absent `facet`
      yields behaviour **byte-identical** to today; every shipped procedure
      across the four verticals still loads clean via `load_procedures`.
- [ ] **AC-5 (migration round-trips):** all four verticals' migrated
      `procedures.yaml` parse clean via `load_procedures`; the migrated `facet`
      values validate and round-trip (load → model → re-serialised shape matches
      the authored intent).
- [ ] **AC-6 (no re-store for in_file_band):** for `aquaculture.judge`,
      `procurement.judge`, `procurement.judge_stock`, the `facet.decision_condition`
      carries `gate_kind: in_file_band` + `band_source: in_file` and **points at**
      the existing typed `threshold` / `direction` / `watch_margin` — it does
      **not** copy those numeric values into the facet (single source of truth, D2-A3).
- [ ] **AC-7 (test coverage):** new tests cover — each of the six `gate_kind`s;
      the `band_source ⇔ gate_kind` validator (positive + negative); the
      `env_var`-only-with-`env` validator (positive + negative);
      `in_file_band` points-at (asserts the facet does **not** carry the numeric
      band); the non-authoritative `input`/`output`/`governance` notes accept a
      `str`; an **absent-facet** backward-compat case; and a **rejected unknown
      key** case (proving `extra="forbid"` still bites on both `Step` and
      `StepFacet` / `DecisionCondition`).
- [ ] **AC-8 (suite + lint):** full offline suite green — **baseline 1651
      passed** plus the new facet tests — and `ruff` + `ruff-format` +
      `mypy --strict` clean on `services/`. **No live MS-S1** (CLAUDE.md §8;
      this is pure schema/config, no LLM call).

## Out of Scope

- ❌ The **Stage-3 generator** (Rule-of-Three-deferred until the schema is
      extracted — which this PLAN does; the generator itself is a later PLAN).
- ❌ **Any runtime consumption of `facet`** — the engine continues to ignore
      `facet` at run time; it is descriptive metadata only (D2-A2/A4). No
      orchestrator, executor, or recommender change.
- ❌ The **review / config / monitor UI** (gated on this landing; separate PLAN — D7 Phase 3).
- ❌ Any change to existing `kind` / `autonomy` / `input` / `threshold` /
      `direction` / `watch_margin` / `tiers` / `handler` / gates / handlers, or
      to the per-kind `_validate_step` invariants beyond *adding* the facet path.
- ❌ The **ADR-008 ontology codegen** path — `procedures.yaml` is engine-**read**
      (`load_procedures`), not codegen-emitted; the ADR-008 D5/D6 generator and
      its validators are untouched (D2-A4).
- ❌ **Cross-validating `facet.decision_condition` against the typed band**
      (e.g. requiring `threshold` when `gate_kind == in_file_band`) — amendment
      **OQ-A2**, explicitly deferred; v0 keeps `facet` non-authoritative.

## Surfaced decisions (LOCKED vs OPEN)

**LOCKED (derivable from the amendment spec — implement as written):**

- **L-1 — The literal `spec.py` delta.** The enums, the two sub-models, and
  `Step.facet` are fixed by the amendment's illustrative delta (ADR-016
  § "spec.py Step-model delta"). Mirror it; do not re-shape.
- **L-2 — `extra="forbid"` stays on `Step`, `StepFacet`, `DecisionCondition`.**
  D2-A1 is explicit: keep the constraint; `facet` is a known key. (Mirrors every
  other model in `spec.py`.)
- **L-3 — YAML keys use underscores** (`decision_condition`, `llm_assist`) —
  Python-attribute-faithful; the loader needs no alias (amendment "Naming").
- **L-4 — The `gate_kind ↔ step` mapping** is fixed by the amendment D2-A3 table
  + the dispatch's explicit assignment: `energy.judge` / `supply_chain.judge` →
  `env_band` (`band_source: env`, `env_var: OCT_RECOMMEND_THRESHOLD`);
  `aquaculture.judge` / `procurement.judge` / `procurement.judge_stock` →
  `in_file_band` (`band_source: in_file`, points-at); `procurement.compliance` →
  `rule_gate`; `procurement.source` → `scored_rule`; `procurement.approve` →
  `doa_tier`; reads / summaries / audit terminals / simple gated actions with no
  decision → `gate_kind: none` (or omit `decision_condition`).

**OPEN (surfaced for Cray — recommendation given, NOT resolved):**

- **SD-1 — Migration of the three non-authoritative notes
  (`input`/`output`/`governance`).** Each comment block carries all five facets;
  the typed `Step` fields already cover `input` / `output` / the band / the gate.
  - *Option (a) — populate the three `str` notes from the existing comments*
    (uniform 5-facet reading preserved end-to-end; more verbose; faithful to the
    catalog's "shared vocabulary").
  - *Option (b) — emit only `decision_condition` + `llm_assist`* (the net-new
    machine-readable signal; leaner; the typed Step fields already own the other
    three, so the notes are redundant prose).
  - **Code recommendation: (a)** — the catalog (`procedure-archetypes.md`) is
    built on the uniform five-facet reading, and the amendment explicitly models
    the notes as a first-class (if non-authoritative) option to "preserve the
    uniform 5-facet reading" (D2-A2). The verbosity cost is low and one-time.
  - *What makes this a Cray decision:* it trades repo-surface verbosity against
    catalog-fidelity on a public determinism-first repo — a curation/taste call,
    not a correctness one. Both options pass every AC.

- **SD-2 — Comment-block removal vs transitional dual-carry.** When the real
  `facet:` field lands, do we **delete** the `# facet[...]` comment blocks or
  keep both transitionally?
  - *Option (a) — remove the comment blocks* (the typed field is now the single
    carrier).
  - *Option (b) — keep both for one transition window.*
  - **Code recommendation: (a) remove** — the duplication is exactly the drift
    hazard the amendment fought (a comment and a field stating the same fact can
    diverge silently; D2-A2 Alternatives "stores the same fact twice → a drift
    hazard"). One carrier, no drift.
  - *What makes this a Cray decision:* (b) has a transient-readability argument
    (a reviewer diffing the migration PR sees the old prose beside the new field)
    — a review-ergonomics call Cray may weigh against the drift principle.

- **SD-3 — PR granularity.** Ship Step A (engine edit) + Step B (4-vertical
  migration) + Step C (tests) in **one** PR, or **split** (engine edit + its
  tests first; migration second)?
  - *Option (a) — one PR.*
  - *Option (b) — split: land `spec.py` + the schema tests first, then the
    migration.*
  - **Code recommendation: (b) split** — the `spec.py` edit is the CQ-1-breaking,
    engine-path-sensitive part; landing it (with its validator tests) behind its
    own reviewable diff isolates the risky change from the mechanical migration,
    and keeps the "first engine edit since zero-engine-edit" auditable on its own.
    The migration PR then carries only config + round-trip tests.
  - *What makes this a Cray decision:* it is a review-process / blast-radius
    judgment (two small reviewable diffs vs one cohesive PR), and it bears on how
    the sensitive engine edit is surfaced for the independent review — Cray owns
    the review-granularity call.

## Steps

### Step A — `spec.py` engine edit: add the typed `facet` field

Edit **only** `services/engine/procedures/spec.py`. Add, mirroring the existing
`StepInput` / `StepTiers` sub-model pattern and the existing `@model_validator`
per-kind invariants:

1. `class BandSource(StrEnum)` — `ENV = "env"`, `IN_FILE = "in_file"`.
2. `class GateKind(StrEnum)` — the six observed kinds: `ENV_BAND = "env_band"`,
   `IN_FILE_BAND = "in_file_band"`, `RULE_GATE = "rule_gate"`,
   `SCORED_RULE = "scored_rule"`, `DOA_TIER = "doa_tier"`, `NONE = "none"`.
3. `class DecisionCondition(BaseModel)` — `model_config = ConfigDict(extra="forbid")`;
   fields `gate_kind: GateKind`, `band_source: BandSource | None = None`,
   `env_var: str | None = None`, `note: str | None = None`; a
   `@model_validator(mode="after")` enforcing AC-3 — `band_source` set **iff**
   `gate_kind in {ENV_BAND, IN_FILE_BAND}`, and `env_var` set **only** when
   `band_source == ENV`. Raise a clear, step-attributable `ValueError` on each
   violation (match the house error-message style of `_validate_step`).
4. `class StepFacet(BaseModel)` — `model_config = ConfigDict(extra="forbid")`;
   `decision_condition: DecisionCondition | None = None`,
   `llm_assist: str | None = None`, and the three non-authoritative note fields
   `input: str | None = None`, `output: str | None = None`,
   `governance: str | None = None`. (Note `StepFacet.input` is a `str` note —
   distinct from `Step.input: StepInput`; the type difference is intentional.)
5. On `Step`: add
   `facet: StepFacet | None = Field(default=None, description="descriptive 5-facet metadata; optional; non-authoritative for runtime (D2-A2)")`.
   Keep `model_config = ConfigDict(extra="forbid")` **unchanged** (AC-2). Do
   **not** add any cross-validation between `facet` and the typed band (OQ-A2,
   out of scope).

Place the new enums near the existing `StepKind` / `Autonomy` enums and the
sub-models near `StepInput` / `StepTiers`, consistent with file ordering.

### Step B — migrate the four verticals' comment-facets → the real `facet:` field

For each `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml`,
replace each step's `# facet[...]` comment block with a typed `facet:` field
per the L-4 mapping (and SD-1 / SD-2 once Cray rules). Concretely:

- **`energy.judge`, `supply_chain.judge`** →
  `facet.decision_condition: {gate_kind: env_band, band_source: env, env_var: OCT_RECOMMEND_THRESHOLD}`;
  `llm_assist: null`. (No in-file threshold field — the env band is authoritative.)
- **`aquaculture.judge`, `procurement.judge`, `procurement.judge_stock`** →
  `facet.decision_condition: {gate_kind: in_file_band, band_source: in_file}`;
  `llm_assist: null`. **Do NOT re-store** the `threshold` / `direction` /
  `watch_margin` values — they stay on the typed `Step` fields and the facet
  points at them (AC-6).
- **`procurement.compliance`** → `gate_kind: rule_gate` (per-criterion AVL · tax ·
  cert · sanctions · single-source; no band).
- **`procurement.source`** → `gate_kind: scored_rule` (supplier selection is a
  scored rule, never the LLM); `llm_assist: "summarise the candidate quotes (advisory)"`.
- **`procurement.approve`** → `gate_kind: doa_tier` (tiered ฿ DOA);
  `llm_assist: "draft the justification + the approver exec-summary (advisory)"`.
- **Reads / summaries / audit terminals / simple gated actions with no decision**
  (`read_readings`, `intake`, `read_stock`, the `restart` / `hold` / `aerate` /
  `reorder` / `issue_po` action steps, the `echo` audit terminals) →
  `gate_kind: none` **or** omit `decision_condition` entirely. Set `llm_assist`
  to the advisory draft/summary string where the comment had one (e.g. the
  energy `restart_breaches` "propose the restart action (advisory)"; the
  procurement `audit` "draft the decision summary"), else `null`.

Per SD-1, populate `input` / `output` / `governance` notes from the comment
prose (recommendation (a)) **unless Cray rules (b)**. Per SD-2, **remove** the
`# facet[...]` comment blocks (recommendation (a)) **unless Cray rules (b)**.
(Cross-check each migrated step against `docs/conventions/procedure-archetypes.md`
§ "the band-authoring split" table and against `verticals/procurement/README.md`'s
facet map so the migrated values match the catalogued intent.)

### Step C — load + validation tests

Add tests (mirror the existing procedures-spec test module pattern) covering AC-7:

1. Each of the six `gate_kind`s parses into a valid `DecisionCondition`.
2. `band_source ⇔ gate_kind` validator — a positive case per band kind; a
   negative case (e.g. `band_source: env` with `gate_kind: rule_gate` → raises;
   `band_source: None` with `gate_kind: env_band` → raises).
3. `env_var`-only-with-`env` validator — positive (`env_band` + `env` + `env_var`);
   negative (`env_var` set with `band_source: in_file` → raises).
4. `in_file_band` points-at — assert the parsed facet carries `band_source:
   in_file` and **no** numeric band on the facet (the band lives only on `Step`).
5. Non-authoritative notes — `input`/`output`/`governance` accept `str`.
6. Absent-facet backward-compat — a `Step` with no `facet` parses, `facet is
   None`, behaviour unchanged (AC-4).
7. Rejected unknown key — an unknown key on `Step`, on `StepFacet`, and on
   `DecisionCondition` each raises (proves `extra="forbid"` still bites — AC-2).
8. End-to-end — `load_procedures("energy")` / `"supply_chain"` /
   `"aquaculture"` / `"procurement"` all load clean post-migration and the
   migrated facet values validate + round-trip (AC-5).

## Verification

- `load_procedures` over all four verticals loads clean (AC-4/AC-5).
- The new facet tests pass and the `DecisionCondition` validators reject the
  negative cases (AC-3/AC-7).
- Full offline suite: **1651 baseline + new tests**, all green; `ruff`,
  `ruff-format`, `mypy --strict` clean on `services/` (AC-8).
- A grep confirms the `# facet[...]` comment blocks are gone (if SD-2 = remove)
  and that no numeric band value was copied into any `facet` (AC-6).
- **No MS-S1 / live LLM run** — pure schema + config + offline tests (CLAUDE.md §8).
- Run the cheapest gate first (the targeted facet tests) before the full suite,
  per the plan-first discipline (`code-operational-policy` skill).
