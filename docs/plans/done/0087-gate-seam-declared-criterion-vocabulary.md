# PLAN-0087: The gate-seam criterion-vocabulary extraction — a vertical declares its own `rule_gate` vocabulary; the engine stops owning it

**Status:** **COMPLETE — all 8 ACs met; shipped as PR #840 (merge `c6eec65`), archived
to `done/` in session 159 (2026-07-21).** SD-1 … SD-3 were RATIFIED by Cray (typed,
2026-07-21, session 158), all three as recommended: SD-1 = (a) vocabulary-only ·
SD-2 = (a) no preceding ADR · SD-3 = (a) `ExceptionPolicy` stays closed. House
discipline observed: this PLAN went `Draft → Complete` and was **never** flipped to
`Accepted` (an `Accepted`-status PLAN is G1-gated for its own closeout).
**Owner:** Claude Code (executes + commits per ADR-009 D2) · Cray (SD ratification +
PR merge)
**Created:** 2026-07-21 (session 158)
**Closed:** 2026-07-21 (session 159) — see "Closeout" below.
**Related ADRs:** ADR-0031 (D3 row-3 gate-plugin seam — the frame; the moat tripwires
3/4 immediately above D3 — the constraint; D4.1–D4.4 — the discipline), ADR-0025
(D2 typed AT-2 content + the provisional-until-N≥2 caveat; D3 unrepresentable bypass —
preserved intact; D7 — the cancelled deferral this PLAN pays), ADR-006 (D4 Rule of
Three), ADR-0029 (SD-3 — the declaration-as-data precedent), ADR-016 (OQ-A1 additive
enum growth — the idiom this PLAN retires *for this one label-class enum only*).
**Related PLANs:** **PLAN-0076 Step T1 / F-FACTORY** (the standing owner — this PLAN
discharges its criterion-vocabulary half; read its two T1 trigger-firing records
first), PLAN-0086 (the N=4 firing + the Cray cancellation this PLAN executes),
PLAN-0081 (the N=3 firing + re-arm), PLAN-0074 (the N=2 finding: the criterion
vocabulary is per-instance forever), PLAN-0077 (the row-1 precedent: a declared,
closed, load-gated grammar — and the subset-with-honest-deferral precedent),
PLAN-0078 (declare-as-data vindicated end-to-end; the "only-when-supplied" pin
discipline reused here).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the in-harness
> `plan-drafter` subagent under ADR-013 D1 phased authority (dispatch originated by
> Code, session 158; the extraction obligation itself was ratified by Cray, typed,
> 2026-07-21, at the PLAN-0086 N=4 escalation). Independent review: Code (R2) at PR;
> ratification: Cray. Author≠reviewer separation: **INTACT**. Uncommitted draft —
> Code commits per ADR-009 D2. All code anchors below re-verified on disk by the
> drafter against `main = 8682b9c`, 2026-07-21, unless marked otherwise; the
> executor re-verifies before building (symbols are the stable reference).

## Goal

Discharge **PLAN-0076 Step T1 (F-FACTORY)** — the extraction Cray made DUE by
cancelling the ADR-0025 D7 deferral at N=4 — by removing the one edit that has
recurred in **four out of four** AT-2 verticals: extending the closed shared
`ComplianceCriterion` enum in engine code so a new vertical's `rule_gate` can name
its own criteria. After this PLAN, a vertical **declares its criterion vocabulary in
its own `procedures.yaml`** (a closed, typed, load-validated set — the
declaration-as-data idiom ADR-0031 D3 row-1 and ADR-0029 SD-3 already ratified
twice), and the engine validates + enforces the *gate* (block on any fail,
non-waivable by type) without owning the *labels*. The migration is
behaviour-preserving: every shipped procedure's governance hash is unchanged, parked
runs keep resuming, and every closed-by-type ADR-0025 D3 guarantee survives intact.
The evidence leads, not the abstraction: 4 verticals, 4 consecutive engine-level
enum extensions, and a member that carries **no executor semantics anywhere in the
engine** — opening this vocabulary is behaviourally inert and overwhelmingly
evidenced, which is exactly the Rule-of-Three bar (ADR-006 D4).

## Context — LOCKED / RATIFIED (do not re-litigate)

1. **The ADR-0025 D7 AT-2-generator deferral is CANCELLED. The extraction is DUE.**
   Cray, typed, 2026-07-21 (session 157), at the PLAN-0086 escalation — a conscious,
   informed pick made with BOTH readings laid out: the "fleet is a strictly weaker
   datum than N=3 and should not count" reading (by gate SHAPE fleet taught nothing —
   composition and authority quantity byte-identical to building_materials'), and
   the "four consecutive verticals, four engine-level enum extensions" reading that
   won (Rule-of-Three is about repeated PRESSURE on shared code, and the pressure
   shows on the governed-enum surface, not the gate composition). Rationale as
   given, verbatim: *"ยอมเจ็บในตอนนี้แล้วในอนาคตจะยืดหยุ่นดีกว่า"* — accept the cost
   now for future flexibility. Full record:
   `tests/services/engine/procedures/test_at2_signature_retrigger.py` module
   docstring (the N=4 section) and PLAN-0076 Step T1's second trigger-firing block.
2. **The owner is PLAN-0076 Step T1 (F-FACTORY)** per ADR-0031 D4.2 (each seam gets
   its own PLAN). **This PLAN is that PLAN** — the seam PLAN T1's own text says must
   be opened by `plan-drafter` and committed separately (ADR-009 D1/D2).
3. **PLAN-0086 deliberately performed none of the extraction.** It was a
   vertical-scaffold PLAN under a timed measurement; framework surgery inside it
   would have been out of scope and destructive to its own number. Its restraint is
   not a defect.
4. **F-PIN is NOT closed and nothing here records it closed.** PLAN-0076 §B item 1
   (the new-run re-routing threat) stays open by construction. This PLAN discharges
   **T1 only** — and (see SD-1 / AC-6) T1's *criterion-vocabulary* half at that,
   under the recommendation.
5. **The best-evidenced extraction is NOT "build an AT-2 generator" in the
   abstract.** The cancellation is about the engine-edit-per-vertical pressure; the
   classify-generator's AT-2 abstain path stays intact (ADR-0025 LOCKED #3). The
   marker's own resolution text says exactly this.

## Current state (grounded — verified on `main = 8682b9c`, 2026-07-21)

### The pressure: `ComplianceCriterion`, a closed shared enum, bent four times

- `services/engine/procedures/spec.py:853-885` — `class ComplianceCriterion(StrEnum)`:
  **13 members in 4 instance-scoped blocks, one per vertical, each commented with its
  owning PLAN** — procurement (`avl, tax, cert, sanctions, single_source`),
  supply_chain (`stability_budget, batch_quarantine, licensed_disposal_vendor,
  coa_customs`, PLAN-0074), building_materials (`kyc, overdue_ar, blacklist`,
  PLAN-0081), fleet_maintenance (`three_quote`, PLAN-0086). The docstring concedes
  the finding itself: *"The blocks are instance-scoped, NOT a generic vocabulary: an
  AT-2 vertical extends this enum with its own gate's criteria."*
- **The member carries NO executor semantics — the strongest fact this PLAN has.**
  Full consumer census (drafter grep, 2026-07-21): in `services/` the symbol appears
  at `spec.py:853` (definition) and `spec.py:1039` (`ComplianceRule.criterion`
  field) — nowhere else. The **only** engine consumer of a member is
  `services/engine/procedures/rule_gate.py:135-136`, which uses
  `rule.criterion.value` as a **plain string key** into the candidate's
  `{criterion: bool}` compliance-signal map (`COMPLIANCE_FIELD`,
  `rule_gate.py:40-43`). There is **no member-keyed branching anywhere**. The
  vocabulary is a pure **label**; opening it is behaviourally inert. Test-side
  consumers (all mechanical constructor/import sites, enumerated for Step 4):
  `test_at2_signature_retrigger.py:115,348`, `test_rule_gate.py:41,60-68`,
  `test_red_team_at2.py:49,137`, `test_draft_lift_governance.py:48,592`,
  `test_spec.py:23,850` (+ prose-history mentions in two hero-test docstrings that
  need no code change).

### The contrast that must NOT be flattened: label-class vs executor-keyed enums

| Enum | Class | Evidence | This PLAN's action |
|---|---|---|---|
| `ComplianceCriterion` (`spec.py:853-885`) | **label** — engine keys on nothing; `.value` used as a string map key only | 4/4 verticals, 4 engine extensions | **OPEN** — extract to per-vertical declaration |
| `ExceptionPolicy` (`spec.py:905-915`) | **label** — executor stamps it as `source_path` provenance, never keys on it (its own docstring: *"growth here is safe"*) | 1 extension ever (supply_chain, PLAN-0074) | **stays closed** under the SD-3 recommendation — named candidate, own trigger |
| `SourcePolicy` (`spec.py:888-902`) | **executor-keyed** — `scored_rule.py` keys provenance on the MEMBER ITSELF (`rule.default_source is ON_CONTRACT`); its docstring says a third member would invert a vertical's provenance | 0 extensions; N=2 finding says NOT freely extensible | **stays closed** — out of scope |
| `ExcursionSeverity` (`spec.py:1059-1072`) | **executor-keyed** — ordinal authority quantity, ranked via `SEVERITY_BY_RANK` (`spec.py:1075`) | authority surface, not a label | **stays closed** — out of scope |
| `RelaxableConstraint` (`spec.py:918-923`) | **safety type** — the CLOSED waiver set that *"CANNOT name compliance or separation-of-duties (non-waivable by type)"* (ADR-0025 D3) | the moat itself | **byte-unchanged** — AC-3 pins it |

A PLAN that opened all of these alike would be wrong. This PLAN acts on exactly one
label-class enum — the one with 4/4 evidence.

### A SECOND pressure point on the same axis — named, adjudicated, deliberately deferred

`services/engine/procedures/scored_rule.py:53-59` — `_KNOWN_CRITERIA =
frozenset({"criticality", "lead_time", "unit_price"})`, a hardcoded engine-level
criterion vocabulary for the `scored_rule` gate, whose comment says the quiet part
out loud: *"a future AT-2 vertical EXTENDS this map, never a silent mis-score"*;
`_weights` (`:169-181`) fails CLOSED (`ScoredRuleError`) on any criterion outside
it. So "the engine bends per instance" is an **N=2-surfaces** finding, not N=1.
**But the difficulty differs and this PLAN does not conflate them:** unlike
`ComplianceCriterion`, these three DO carry executor semantics — each is scored
differently (`criticality` is scored by lead-time readiness, `:22-23`, amplified by
`event_criticality`, `:197`). Opening it means "a declared criterion needs a
declared scoring rule" — a real design problem (a `derive`-grammar-shaped one), not
a relabelling — and its extension pressure to date is **zero** (both scored-rule
verticals fit inside the original three names). Rule-of-Three line drawn here: the
label-class vocabulary opens now at 4 extensions' evidence; the scored-rule
vocabulary is the **harder half with its own trigger** — the first vertical that
demands a scored criterion outside `_KNOWN_CRITERIA` (the fail-closed
`ScoredRuleError` is its self-announcing tripwire). Step 8 records this in
PLAN-0076 §A so it is tracked, not lost.

### The seam frame (ADR-0031 D3 row 3 + D4) and what this PLAN does to it

- D3 row 3, current-state column: adding a gate shape touches ≥4 coordination points
  — the `GateKind` member (now `spec.py:202-216`, 7 members incl. `severity_tier`),
  the typed content model + the `AT2Governance` union arm (now **`spec.py:1143-1145`**,
  a 4-arm discriminated union), a resolver module (`doa_tier.py` / `scored_rule.py` /
  `rule_gate.py`), and the wiring in `governance_step.py` + `derive_governance_todo`.
  Pre-designed seam: *"a governance-gate plugin unit: content-model + resolver +
  obligation-contributor registered as ONE typed unit; plus decision-as-data."*
- **What the N=4 instances actually pressed is narrower than the pre-design.** No
  vertical since the pre-design has needed a new gate *shape* (fleet reused
  `(rule_gate, doa_tier)` byte-identically); all four needed a new *vocabulary*.
  ADR-0031's own Negative section anticipates exactly this: *"if the N≥2 instances
  press a different shape than pre-designed, the PLAN must feel free to deviate (the
  map is a default, not a cage) — deviation = amend this ADR's row."* This PLAN
  ships the vocabulary seam and leaves the full plugin unit pre-designed for the
  pressure that has not yet arrived (the same subset-with-honest-deferral move
  PLAN-0077 made on row 1, explicitly in-authority per D4.2). D4.4 obligates the
  row update on landing — AC-7.
- D4.1 is satisfied twice over: the trigger fired at N=3 (recorded, re-armed) and at
  N=4 (recorded, **cancelled** — Cray, typed).

### The F-FACTORY (ii) half — drift-corrected state (do not copy PLAN-0076 §A's anchors)

PLAN-0076 §A's 2026-07-15 anchors have drifted; current state, verified:

- Procurement's hardcode is at `verticals/procurement/hero_demo/run.py:298`
  (`sod_steps=frozenset({"intake", "approve"})`) — **not** `:278` as PLAN-0076 says.
- PLAN-0076 §A describes a 2-vertical world that no longer exists. **THREE**
  verticals now derive `sod_steps` from the spec's own `separation_of_duties`:
  `verticals/supply_chain/procedures_factory.py:244`,
  `verticals/building_materials/procedures_factory.py:64`,
  `verticals/fleet_maintenance/procedures_factory.py:61`. Only procurement's hero
  demo still hardcodes. So the *hardcode-drift* half of F-FACTORY is **N=1 and
  shrinking** (the template fixed it by convention), while the *vertical-scoping*
  half (the derived set unioned across a vertical's procedures, keyed on `step_id`
  alone) is **N=3 and unchanged**. `stamp_steps` remains supply_chain-only
  (`procedures_factory.py:298`, `cold_chain_assess.py:236-239`).
- Severity, stated in PLAN-0076 AC-1's exact pinned wording: a mis-bound `sod_steps`
  only mis-marks the `sod_required` **display flag** on the emitted verdict
  (`services/engine/procedures/governance_step.py:201` and `:260` — verified);
  actual SoD enforcement reads `procedure.separation_of_duties` LIVE at the gate
  (`action_step.py`, the `check_principal_sod` call on the `resolve_gated_step`
  path). **An audit-flag over-mark, never an enforcement gap** — with **zero** live
  `step_id` collisions today. This is why SD-1 recommends deferring this half: its
  evidence is an inert display-flag risk, not the 4/4 enforcementless-but-recurring
  engine edit Cray's cancellation was about.

### What the migration must not move

- `ExecutorFactory = Callable[[], "Mapping[StepKind, StepExecutor]"]` —
  `services/engine/registry.py:30`, zero-arg, registered per vertical via
  `register_procedure_executors` (`:100-112`). Untouched under SD-1(a).
- The governance pin: `_step_governance_snapshot` (`governance_pin.py:58`) pins
  `governance_content.model_dump(mode="json")` (`:74-78`) — a `StrEnum` criterion
  already serializes as its plain string value, so a validated-string criterion
  carrying the identical value pins **byte-identically**. Vertical-level declaration
  blocks are precedentedly OUTSIDE the pin surface (`governance_pin.py:19-22`
  discloses that `principals` / `principal_aliases` are not pinned — the pinned
  surface is the rule configuration, not the vertical directory). The new
  `compliance_criteria` block is a **load gate**, not a run-time input; the rules a
  run enforces are already pinned per step, unchanged.
- The census + guard module (`test_at2_signature_retrigger.py`):
  `_BASELINE_SIGNATURES` (`:150-188`) pins the 4-signature census and **stays armed
  for signature #5**; `_content_enum_surface` (`:212-235`) reads
  `rule.criterion.value` for a `rule_gate` — the ONE reader line this PLAN changes,
  deliberately (AC-5). `test_at2_extraction_obligation_is_owned` (`:300-320`)
  asserts PLAN-0076 exists in **active** `docs/plans/` and still contains the
  literal `"N=4"` — AC-6 keeps both true. PLAN-0076's AC-6 presence guard
  (`test_at2_followon_tracking_guard.py`) likewise stays armed.

## The design — a declared, closed, load-validated per-vertical criterion vocabulary

The shape ADR-0031 D4.2 pins (typed, declaration-as-data, one seam per core, moat
tripwires honored), instantiated the same way the repo has already ratified twice
(D3 row-1's transform grammar, PLAN-0077; ADR-0029 SD-3's event→procedure binding):

1. **The identifier type.** `CriterionId` — an `Annotated[str, ...]` constrained to
   a lowercase snake-case identifier (length-bounded; no whitespace, no uppercase,
   no punctuation beyond `_`). The PLAN pins the **constraint class**; the exact
   pattern surface is the executor's (the ADR-0031 OQ-1 constraint-vs-surface
   split). A prose sentence, a ฿ amount, or a role token is **unrepresentable as a
   criterion id by pattern** — the first of three answers to moat tripwire 4.
2. **The declaration home.** `VerticalProcedures.compliance_criteria:
   list[CriterionId]` (default empty) — the same human-author-only, `extra="forbid"`
   declared-block home that already carries `principals` / `principal_aliases` /
   `service_principals` (`spec.py:1655-1700`). Human-author-only (H, ADR-0024 D3 /
   ADR-0025 D4): never reachable from any draft type — the declaration is authored,
   not generated.
3. **The load validator** — a `model_validator(mode="after")` on
   `VerticalProcedures`, mirroring `_validate_principals` (`spec.py:1683-1700`) in
   shape and failure philosophy:
   - duplicate declared ids → rejected;
   - **every `ComplianceRule.criterion` across every procedure's `rule_gate`
     content must be a declared member** — a dangling criterion is *"an authoring
     error, not a silent collapse that never fires"* (the second answer to tripwire
     4: the set stays **closed per vertical**, enforced at load);
   - a vertical carrying ≥1 `rule_gate` content with an absent/empty declaration →
     load refused (the declaration is mandatory exactly where it is used —
     "only-when-supplied": verticals without a `rule_gate` (energy, aquaculture)
     author nothing and are untouched);
   - declared-but-unused ids are permitted (a vocabulary may pre-declare; same
     permissiveness as an unreferenced principal).
4. **The field flip.** `ComplianceRule.criterion: CriterionId` (was
   `ComplianceCriterion`, `spec.py:1039`). Serialized bytes identical (`"kyc"` is
   `"kyc"`), so the pinned snapshot is unchanged. `blocks_po: Literal[True]` and
   everything else in `ComplianceRule` / `ComplianceGate` (`spec.py:1032-1056`)
   untouched.
5. **The retirement.** `class ComplianceCriterion` is deleted from `spec.py` — the
   extraction is real only if the engine stops owning the vocabulary. `rule_gate.py`
   drops its two `.value` accesses (`:135-136` — the criterion is already the
   string). The 5 test-module constructor sites (census above) update mechanically.
6. **The migration.** Each of the 4 rule_gate verticals' `procedures.yaml` gains its
   declaration block with **exactly its current member set** (procurement 5,
   supply_chain 4, building_materials 3, fleet_maintenance 1 — transcribed from
   `spec.py:865-885` and human-reviewed against each YAML's authored rules, the
   ADR-0025 Implementation-Note discipline: a criterion is never silently changed in
   transcription). No `criterion:` line in any YAML changes — YAML already authors
   plain strings that the enum coerced.
7. **The tripwire-4 answer, on the record (the third leg).** Moat tripwire 4 forbids
   *"flipping a closed governed enum to accept free strings."* This design accepts
   **no free strings**: the vocabulary remains (i) pattern-constrained by type,
   (ii) a **closed set per vertical**, declared as data, (iii) membership-validated
   at load with authoring-error refusal, and (iv) label-class by verified census —
   no engine behaviour keys on a member. What changes is WHERE the closure lives:
   vertical declaration instead of engine code — which is not the tripwire's target
   but the ADR's own preferred idiom (D2: *"typed and auditable
   (declaration-as-data), never arbitrary code"*; row-1 and ADR-0029 SD-3 are the
   ratified precedents). The honest residue — that no single global enum enumerates
   all criteria any more — is stated, not hidden; the reviewer's counter-position is
   SD-2(b), left genuinely pickable.
8. **What a 5th vertical does after this PLAN.** Ships its `rule_gate` by declaring
   `compliance_criteria: [its, own, ids]` in its own `procedures.yaml` — **zero
   engine diff**. That is the discharged pressure, and AC-1 proves it by test, not
   by prose.

**ADR-0025 D3 is structurally untouched.** The waiver axis
(`EmergencyWaiverPolicy.relaxes: list[RelaxableConstraint]`) remains typed to the
closed engine enum — a declared criterion id **cannot** be named in `relaxes` (the
type spaces are disjoint by construction), so compliance stays non-waivable by type
no matter what a vertical declares. AC-3 pins this.

## Surfaced decisions (SD-N — ALL THREE RATIFIED by Cray, typed, 2026-07-21, session 158)

> **Ratification record.** Cray ratified SD-1, SD-2 and SD-3 **all as recommended**,
> in one typed instruction, after reading PR #840 (which carried the three
> recommendations with their alternatives). This is a typed Cray pick, not a Code
> inference or a silence-implies-consent. The recommendations below were written
> *contingent*; they are now *chosen*, and the per-SD stamps record which.

### SD-1 — The scope fork: vocabulary-only, or fold in the procedure-aware `ExecutorFactory`? — **RESOLVED = (a)**

> **RESOLVED (Cray, typed, 2026-07-21, session 158): (a) — this PLAN ships the
> criterion-vocabulary extraction only.** The procedure-aware `ExecutorFactory` half
> stays tracked at PLAN-0076 T1 as its explicitly-open remainder, with its named
> triggers armed (a live `step_id` collision; the gate-shape 4-edit pain biting in a
> real PLAN). Step 8's annotation records T1 as **partially discharged**.

PLAN-0076 T1 bundles two things whose evidence is not equally strong.

- **(a) — RECOMMENDED: this PLAN ships the criterion-vocabulary extraction only
  (i); the procedure-aware `ExecutorFactory` (ii) stays tracked in PLAN-0076 T1 as
  its explicitly-open remaining half.** The vocabulary half is what N=4 actually
  evidenced (4/4 verticals, 4 engine edits) and what Cray's cancellation was about.
  The factory half's evidence is an **inert audit display-flag over-mark with zero
  live `step_id` collisions** (PLAN-0076 §A states this itself, and the drift
  correction above shows its hardcode half is N=1-and-shrinking) — building it now
  would be abstraction ahead of pressure, the exact thing ADR-0031 D4.1 forbids.
  Honest deferral is in-authority (D4.2; the PLAN-0077 precedent). PLAN-0076 T1 is
  annotated as **partially discharged** (Step 8), stays in active `docs/plans/`,
  and its own named triggers for the factory half stay armed (a live `step_id`
  collision; the gate-shape 4-edit pain biting in a real PLAN).
- **(b) fold (ii) in:** also change `ExecutorFactory` to be procedure-aware and key
  `sod_steps` / `stamp_steps` on `(procedure_id, step_id)`, retiring the
  `hero_demo/run.py:298` hardcode and the four factories' vertical-scoped derivation
  in the same PLAN. Shape if picked: (1) contract change in `registry.py` (factory
  receives the procedure, or returns a keyed map); (2) migrate 4 factories + the
  hero demo; (3) display-flag parity test (the emitted `sod_required` flags are
  byte-identical for every shipped procedure). Cost: an engine-contract change with
  4-vertical blast radius riding in the same PR as a schema migration — two
  independently-revertable changes fused; and its trigger has not actually fired
  (zero collisions). If picked, the steps above are drafted as a scope addendum
  before implementation.
- **Why this is Cray's call, not Code's:** it adjudicates how much of a
  Cray-ratified obligation (T1) one PLAN consumes, and whether an unfired trigger
  is worth pre-paying while the tree is open — portfolio sequencing, not an
  engineering derivation.

### SD-2 — Does an ADR land first? — **RESOLVED = (a)**

> **RESOLVED (Cray, typed, 2026-07-21, session 158): (a) — no preceding standalone
> ADR.** The PLAN lands inside already-ratified authority (ADR-0025 D2's own
> "genericization gated behind the D7 re-trigger" clause, consumed when D7 fired at
> N=4 and Cray cancelled it; ADR-0031 D4.2's delegation of each seam to its own
> PLAN), and carries the D4.4 row amendment at landing (AC-7). Alternative (b) — a
> preceding **ADR-0034** — was declined. **Consequence, binding:** AC-7 is now the
> only governance-record obligation this PLAN owes ADR-0031, and it is not optional;
> a shipped extraction with a silent D3 row is a FAIL.

CLAUDE.md §8 binds: ADRs merge before the related implementation PR. The question
is whether this design *needs* one.

- **(a) — RECOMMENDED: no preceding standalone ADR; the PLAN lands inside already-
  ratified authority, carrying the D4.4 row amendment.** The chain: ADR-0025 D2
  marked the AT-2 content types **provisional-until-N≥2** with *"genericization
  gated behind the D7 re-trigger"* — that gate has now been consumed by its own
  design (D7 fired at N=4 and Cray, typed, resolved it as extraction-DUE), so
  changing the D2-named `ComplianceCriterion` type is the move ADR-0025 itself
  pre-authorized, not a contradiction of it. ADR-0031 D4.2 delegates each seam to
  its own PLAN and pins only the shape — which this design conforms to
  (declaration-as-data, typed, load-gated, tripwires honored per the three-leg
  argument above) — and ADR-0031's own text prescribes the remedy for
  pressed-a-narrower-shape deviation: **amend the D3 row** (its Negative section +
  D4.4), which this PLAN does at landing via the G1 route (AC-7). Net: the
  authority exists; a standalone ADR would restate it.
- **(b) a short preceding ADR-0034** ("gate criterion vocabularies are
  vertical-declared data") that explicitly amends ADR-0025 D2's `StrEnum` line and
  annotates tripwire 4's boundary. The strongest arguments FOR: the D7 cancellation
  currently lives in a test docstring + two PLANs, and an ADR would be its durable
  governance home; and where an *interpretation* of a moat tripwire is load-bearing,
  ratifying the interpretation beats arguing it in a PLAN. Cost: one more
  governance cycle (plan-drafter → R2 → ratify → merge) before an extraction whose
  behaviour change is provably nil.
- **Why this is Cray's call:** it prices governance formality against delivery on a
  moat-adjacent line — exactly the kind of precedent-setting judgment (what rides
  on a PLAN vs what demands an ADR) that ADR-009 reserves to Cray.
- **Sequencing note (binding either way):** under (b), the ADR merges first and
  this PLAN's Step 2 blocks on it; under (a), the D3 row amendment lands with/
  immediately after the implementation PR per D4.4 — there is no ADR-before-PR
  obligation because no ADR text is contradicted (that is the (a) claim; picking
  (b) rejects the claim).

### SD-3 — `ExceptionPolicy`: open alongside, or stay closed? — **RESOLVED = (a)**

> **RESOLVED (Cray, typed, 2026-07-21, session 158): (a) — `ExceptionPolicy` stays
> closed in the engine**, recorded as the named label-class candidate with its own
> trigger (its 2nd extension). It stays in Out of Scope; `_content_enum_surface`'s
> scored_rule branch is therefore NOT touched, which keeps the AC-5 reader change at
> its deliberate minimum (the rule_gate branch only).

- **(a) — RECOMMENDED: stays closed in the engine; recorded as the named
  label-class candidate with its own trigger (its 2nd extension).** It is
  label-class by verified census (the executor stamps `source_path`, never keys —
  its docstring says growth is safe), so the same declared-vocabulary mechanism
  fits — but its extension pressure is **N=1** (one member added, ever, by
  PLAN-0074) vs `ComplianceCriterion`'s 4. Opening it now is speculative
  generalization the evidence does not yet order (ADR-006 D4); the recorded trigger
  makes the deferral honest, not silent.
- **(b) open it in the same pass** (`exception_policies` declared block, same
  validator shape). FOR: the mechanism is identical and marginal cost is small;
  a future scored-rule vertical's exception label would otherwise be a 5th engine
  edit on a sibling axis. AGAINST: it doubles the census-reader touch
  (`_content_enum_surface` reads `exception_policy.value` on the scored_rule
  branch) and widens a moat-adjacent diff for a pressure that has fired once.
- **Why this is Cray's call:** same Rule-of-Three seam-timing judgment Cray has
  adjudicated at every firing (N=2, N=3, N=4) — it is precisely not a Code default.

## Acceptance Criteria

Each with a pre-committed pass/fail read (fixed here, before the build).

- [x] **AC-1 — the engine-edit-per-vertical pressure is discharged, proven by
  test.** A fixture vertical spec carrying a **novel** criterion id (one that
  appears nowhere in `services/`) loads through `load_procedures_file` and
  `evaluate_compliance` gates on it (passes when its signal is true, blocks when
  false/absent) — with **zero engine diff**. Pass/fail read: (i) the positive test
  is green; (ii) its negative twin — the same fixture with the criterion
  **undeclared** — is refused at load with the authoring-error message; (iii) a
  repo grep for the fixture's criterion id matches only the test module (the
  static-guard pattern; the executor may embed the grep as an in-test assertion).
  Fails if shipping the fixture vocabulary would have required touching anything
  under `services/`.
- [x] **AC-2 — the migration is behaviour-preserving: no shipped procedure's
  governance hash moves.** Pass/fail read: the existing pinned-hash suites
  (`tests/services/db/test_governance_pin.py`, `test_derivation_pin.py`, the
  per-vertical migration-parity tests) are green **with no pinned constant edited
  in this change** (an edited pin = the hash moved = FAIL); the full suite is
  green; the `compliance_criteria` block is added ONLY to the four rule_gate
  verticals (energy + aquaculture YAMLs byte-identical — the only-when-supplied
  discipline, PLAN-0078/PLAN-0086 precedent). Parked runs keep resuming by
  construction (the pinned per-step bytes are unchanged; the declaration block is
  outside the pin surface, `governance_pin.py:19-22` precedent).
- [x] **AC-3 — the closed-by-type guarantees survive (ADR-0025 D3).** Pass/fail
  read: `RelaxableConstraint` (`spec.py:918-923`) is byte-unchanged;
  `EmergencyWaiverPolicy.relaxes` remains typed to it (mypy strict green proves no
  `str` path in); `blocks_po: Literal[True]` unchanged; the existing D3 test suite
  (red-team fixtures incl. `test_red_team_at2.py`) green after the mechanical
  constructor updates. Fails if any declared criterion id can be named in
  `relaxes`, or if any D3 validator is loosened.
- [x] **AC-4 — the tripwire-4 defense holds mechanically, not rhetorically.**
  Pass/fail read: three negative load tests are green — (i) a criterion id with
  whitespace/prose (e.g. `"vendor must have three quotes"`) is refused by pattern;
  (ii) an undeclared-but-well-formed criterion in a rule is refused by membership;
  (iii) a vertical with `rule_gate` content and no declaration block is refused.
  Plus: the declaration is H-discipline — `compliance_criteria` is reachable from
  no draft type (the ADR-0025 D4 disjointness check extends/covers it). Fails if
  any free-string path onto the governed spine survives.
- [x] **AC-5 — the census pin's fate is argued, not drifted.** Pass/fail read: the
  `_BASELINE_SIGNATURES` block (`test_at2_signature_retrigger.py:150-188`) is
  **byte-identical** in the diff (the 4-signature census and its enum-surface
  fingerprints are unchanged — same strings, same order); the reader change is
  exactly the deliberate minimum (`_content_enum_surface`'s rule_gate branch reads
  `rule.criterion` instead of `rule.criterion.value`; `_procurement_shaped_procedure`
  passes the id string directly; the `ComplianceCriterion` import is removed); the
  module docstring gains a short landing note ("the extraction landed —
  PLAN-0087") without altering the N=2/N=3/N=4 history;
  `test_at2_generator_deferral_retrigger` stays armed for signature #5. Fails if
  the baseline moved or the reader changed what it fingerprints.
- [x] **AC-6 — the ownership guard stays load-bearing; no re-homing occurs, and
  that is argued.** `test_at2_extraction_obligation_is_owned` requires re-homing
  only if PLAN-0076 archives. It does **not** archive in this PLAN under either
  SD-1 branch: F-PIN's remainder (§B item 1) is open by construction, and
  PLAN-0076 T3 archives only when BOTH deferrals close — so the guard, the AC-6
  presence guard, and PLAN-0076 all stay exactly where they are. Pass/fail read:
  post-change, both guard tests are green; PLAN-0076 remains in active
  `docs/plans/`; its Step T1 carries the new PLAN-0087 annotation (Step 8) and
  **still contains the literal string `"N=4"`**. Fails if any guard is deleted,
  skipped, weakened, or if the annotation drops the N=4 record.
- [x] **AC-7 — ADR-0031 D4.4 is paid: the D3 row-3 row is updated on landing.**
  The row's current-state column records the criterion-vocabulary extraction as
  shipped ("criterion vocabulary: declared per vertical — see PLAN-0087"), notes
  that the instances pressed a narrower shape than the full pre-designed plugin
  unit (which remains the pre-design for the un-arrived pressure), and — under
  SD-1(a) — that the plugin-unit half remains tracked at PLAN-0076 T1. Mechanics:
  an Accepted-ADR body edit is G1-gated for Code, so the row text is authored via
  a small `plan-drafter` dispatch and lands in the same PR or the immediately
  following `docs(adr):` PR. Pass/fail read: the updated row is on `main` within
  the landing sequence; a stale row (extraction shipped, row silent) is a FAIL —
  *"a stale map is worse than no map."*
- [x] **AC-8 — the second pressure point is recorded, not built.** Pass/fail read:
  PLAN-0076 §A (via the Step 8 annotation) names `scored_rule._KNOWN_CRITERIA` as
  the executor-keyed sibling vocabulary with its own trigger (the first vertical
  demanding an out-of-set scored criterion; the fail-closed `ScoredRuleError` at
  `scored_rule.py:174-179` is the self-announcing tripwire) and states why it did
  not ship here (executor semantics per criterion; zero extensions to date). The
  `_weights` fail-closed test stays green. Fails if the sibling pressure is
  scoped out silently or if `_KNOWN_CRITERIA` is opened without its own design.

## Closeout (session 159, 2026-07-21T20:02+07:00)

**Shipped as PR [#840](https://github.com/CrayJThiemsert/vero-lite/pull/840)** — merge
commit `c6eec65`; build commits `e45d379` (this PLAN, Draft) → `57e6839` (SD ratification,
Steps 0–1) → `069cdf7` (Steps 2–5, the flip + the enum retirement) → `d9a0ad1` (Step 6,
the AC-1 proof pair) → `16c3622` / `bdd07ed` / `4f9cb7a` (Step 8 i/ii/iii).

Every AC above was re-read against **fresh on-disk evidence at closeout** — not carried
over from the build session's notes (CLAUDE.md §6 "Verification is hygiene, not a
verdict": the label requires both the pre-committed pass/fail read *and* a fresh
artifact). The closeout reads, in the order performed:

| AC | Closeout read (session 159) | Result |
|---|---|---|
| AC-1 | Repo-wide grep for `zzz_fixture_only_sourcing_check` → **exactly one file**, `test_declared_criterion_vocabulary.py`; its three proof tests present (`..._loads_and_gates_with_zero_engine_diff`, `..._undeclared_twin_is_refused_at_load`, `..._is_confined_to_this_module`) | ✅ |
| AC-2 | `git diff --name-only 8682b9c c6eec65` → the four `rule_gate` verticals' YAMLs only; **`energy` + `aquaculture` absent from the diff entirely**; grep of the whole diff for `sha256` / `config_hash` → **no match** | ✅ |
| AC-3 | `RelaxableConstraint` (`spec.py:911`) and `blocks_po: Literal[True]` (`spec.py:1043`) present and unchanged; `ComplianceCriterion` survives in `services/` **only as the retirement note** (`spec.py:870`) and one historical comment (`draft.py:101`); `mypy --strict services/` clean (98 files) | ✅ |
| AC-4 | The three negative load tests present and green (`..._prose_shaped_criterion_is_refused_by_type`, `..._undeclared_criterion_is_refused_by_membership`, `..._rule_gate_with_no_declaration_is_refused`), plus the H-discipline test `test_compliance_criteria_is_a_human_authored_governance_field` | ✅ |
| AC-5 | The `#840` diff of `test_at2_signature_retrigger.py` carries **no `±` line inside `_BASELINE_SIGNATURES`** — only the docstring landing note and the deliberate reader change (`rule.criterion` in place of `rule.criterion.value`) | ✅ |
| AC-6 | `"N=4"` present **3×** in PLAN-0076; PLAN-0076 **still in active `docs/plans/`** (not archived by this closeout — deliberate: T1 is only partially discharged and §B item 1 is open by construction); both guard tests green in the full run | ✅ |
| AC-7 | ADR-0031 D3 row 3 on `main` reads *"Criterion vocabulary: shipped — see PLAN-0087"* with the plugin-unit half recorded as still pre-designed and tracked at PLAN-0076 T1 | ✅ |
| AC-8 | `_KNOWN_CRITERIA` recorded in PLAN-0076 §A with its trigger and its fail-closed `ScoredRuleError` tripwire, and with the reason it did not ship here (executor semantics per scored criterion) | ✅ |

**Gate (Step 7) re-run at closeout, on `main = c6eec65`:** full suite **2954 passed /
7 skipped** (169.91s) · `mypy --strict services/` **clean, 98 source files**. Matches the
build session's figures exactly — `confirmed — prior intact`.

**Deliberately NOT done, and why (carried forward, not dropped):**

- **PLAN-0076 is NOT archived.** Its Step T1 keeps the procedure-aware `ExecutorFactory`
  half, and §B item 1 (F-PIN's new-run re-routing threat) is open by construction. The
  AC-6 presence guard therefore stays ARMED and **no guard re-homing occurred** — re-homing
  is owed only when PLAN-0076 itself archives (PLAN-0076 Step T3).
- **`scored_rule._KNOWN_CRITERIA` was not opened** — zero extension pressure to date, and
  its shape is `derive`-grammar-like rather than vocabulary-like (AC-8).
- **The stale `N=2` / `N=3` doc drift in ADR-0025 D7 and ADR-0032 was NOT folded in here.**
  Session 157 expected this PLAN to carry it; it did not — AC-7 obligated exactly one
  ADR-0031 table row and nothing more. The item remains open in STATUS and needs its own
  small `plan-drafter` dispatch (both are G1-gated Accepted-ADR body edits). Recorded here
  so the expectation and the outcome do not silently diverge.

## Out of Scope

- ❌ **An "AT-2 generator" in the abstract.** The cancellation is about the
  engine-edit-per-vertical pressure, NOT about emitting AT-2 skeletons; the
  classify-generator abstain path stays (ADR-0025 LOCKED #3, D7's own resolution
  text).
- ❌ **Recording F-PIN as closed** — PLAN-0076 §B item 1 stays open by construction;
  nothing here touches it.
- ❌ **Opening `SourcePolicy`** (executor-keyed; a third member inverts provenance —
  its docstring), **`ExcursionSeverity` / `SeverityLadder`** (ordinal authority
  quantities), or **`RelaxableConstraint`** (the D3 safety type — byte-pinned by
  AC-3).
- ❌ **Opening `scored_rule._KNOWN_CRITERIA`** — the harder, executor-semantic half;
  recorded with its own trigger (AC-8), built only when that trigger fires, via its
  own design (a declared scoring rule, not a relabelling).
- ❌ **`ExceptionPolicy`** — under the SD-3 recommendation; flips into scope only by
  Cray's (b) pick.
- ❌ **The procedure-aware `ExecutorFactory` / `(procedure_id, step_id)`-keyed
  `sod_steps`/`stamp_steps`** — under the SD-1 recommendation; stays tracked at
  PLAN-0076 T1 with its named triggers armed.
- ❌ **The un-modelled fleet customer values** — the ฿20,000 quote-comparison
  trigger and the ฿10,000 emergency cap + ratification window (PLAN-0086 AC-3 gap
  note). A thresholded `rule_gate` criterion or a capped/windowed waiver would each
  be an ADR-0025 **D3 amendment** — candidates, not scheduled, and not this PLAN.
- ❌ **The fleet tire/PM calm-path second procedure** (PLAN-0086 SD-3's separate,
  unscheduled follow-on).
- ❌ **Validating compliance-signal-map keys against the declared vocabulary**
  (e.g. a transform `default` emitting a signal key outside the declaration) — a
  possible future load-lint on a different surface (transform semantics), noted
  here so its omission is a decision, not an oversight.
- ❌ **New UI surfaces, new trace kinds, DB migrations** — none; this is a
  schema/load-gate change with an inert runtime footprint.

## Steps

### Step 0: SD ratification gate (blocking) — **DISCHARGED 2026-07-21 (session 158)**

Present SD-1…SD-3 to Cray. No implementation before ratification. Record picks as
per-SD stamps (the PLAN-0084/0085/0086 pattern). If SD-2 = (b), this PLAN blocks
until ADR-0034 merges; if SD-1 = (b), draft the fold-in scope addendum first.

> **DISCHARGED.** Cray ratified all three as recommended in one typed instruction
> (SD-1 = (a), SD-2 = (a), SD-3 = (a)) after reading PR #840. Neither blocking
> branch fired: no ADR-0034 gate, no fold-in addendum. **Step 1 is unblocked.**

### Step 1: Baseline capture (the pre-committed pass read is fixed here) — **DISCHARGED 2026-07-21 (session 158)**

Run the pinned-hash suites + the retrigger module + the full suite at execution
HEAD and record green (the `confirmed — prior intact` baseline). Re-run the
`ComplianceCriterion` consumer census (Grep) and diff it against the enumeration in
Current State — a set mismatch means the tree moved since drafting: stop and
re-ground before editing. Verification: baseline figures recorded in the working
notes; census set-equality confirmed.

> **DISCHARGED — baseline green, census set-equality CONFIRMED** (Code, session 158,
> at branch `docs/plan0087-gate-seam-criterion-vocabulary`, tree = `main` `8682b9c`
> + this docs-only PLAN):
>
> - **Suite: 2943 passed / 7 skipped** — identical to the `8682b9c` figure carried in
>   from PLAN-0086's close, so the pre-existing baseline is `confirmed — prior intact`
>   (not a re-measurement that found drift). The pinned-hash suites
>   (`test_governance_pin`, `test_derivation_pin`), the retrigger module, and the
>   AC-6 presence guard all ride inside this run and are green.
> - **Census set-equality: EXACT.** `services/` yields precisely the two sites this
>   PLAN's Current State enumerates — `spec.py:853` (definition), `spec.py:1039`
>   (`ComplianceRule.criterion` field) — and nothing else; the member consumer remains
>   `rule_gate.py:135-136` alone. `tests/` yields exactly the five constructor/import
>   modules enumerated for Step 4 (`test_at2_signature_retrigger.py:115,348`,
>   `test_rule_gate.py:41,60-68`, `test_red_team_at2.py:49,137`,
>   `test_draft_lift_governance.py:48,592`, `test_spec.py:23,850`) plus the two
>   prose-only hero-test docstrings. **The tree has not moved since drafting** — the
>   Step 1 stop-and-re-ground condition did NOT fire.
> - **Process note (recorded so it is not repeated at Steps 2–7):** the first attempt
>   at this baseline ran the pinned-hash subset CONCURRENTLY with the full suite and
>   produced two spurious `asyncpg` failures in `test_governance_pin.py`. The test DB
>   is scoped per checkout — **one `pytest` per checkout**. Those results were
>   discarded, not diagnosed; the figures above come from a single clean run.

### Step 2: The declaration home + validator (engine side, additive)

Add `CriterionId`, `VerticalProcedures.compliance_criteria`, and the
`_validate_compliance_criteria` model_validator (design items 1–3), with unit
tests: duplicates refused; dangling rule criterion refused (message names the
vertical + the undeclared id + the declared set, mirroring `_validate_principals`
wording); rule_gate-present-but-undeclared refused; no-rule_gate + no-block loads
clean. Verification: new tests green; mypy strict green; every EXISTING test still
green (the validator cannot fire on the not-yet-migrated YAMLs in this window —
sequence Steps 2–4 into one PR so the tree is never red between them).

### Step 3: Migrate the four YAMLs (additive, human-reviewed)

Add the `compliance_criteria` block to procurement / supply_chain /
building_materials / fleet_maintenance `procedures.yaml` with exactly the current
member sets (design item 6). Human-review each transcription against the vertical's
authored rules — a criterion is never silently changed. Verification:
`load_procedures_file` green for all six verticals; energy + aquaculture YAML
byte-identical (git diff empty on both).

### Step 4: The flip + the retirement

`ComplianceRule.criterion: CriterionId`; delete `class ComplianceCriterion`; drop
the two `.value` accesses in `rule_gate.py`; mechanically update the five
enumerated test modules (constructor sites pass the id string). Verification: mypy
strict green; repo grep — `ComplianceCriterion` appears **zero** times in
`services/` and survives in `tests/` only as prose history (no import, no
construction); full rule_gate behaviour suite green with identical verdicts.

### Step 5: The census reader — deliberate, minimal, argued

Apply exactly the AC-5 change set to `test_at2_signature_retrigger.py`.
Verification: the module is green; `git diff` shows the `_BASELINE_SIGNATURES`
block untouched; the docstring landing note added.

### Step 6: The AC-1 proof pair

The novel-criterion fixture test (positive + undeclared-twin negative + the
grep/static assertion) and the AC-4 negative trio, homed with the engine's
procedure tests. Verification: all green; the fixture id appears only in the test
module.

### Step 7: The behaviour-preservation gate

Full suite + `mypy --strict services/` + ruff at CI scope; confirm the AC-2 read:
no pinned-hash constant edited anywhere in the diff. Verification: the offline
oracle is the gate (CLAUDE.md §8) — this gate, green, is the PLAN's finish line
for code.

### Step 8: Governance-record closeout

(i) Annotate PLAN-0076 Step T1 (a Tracking-status PLAN — Code-editable): the
criterion-vocabulary half is DISCHARGED by PLAN-0087 (link + date); under SD-1(a)
the procedure-aware-factory half remains OPEN with its named triggers restated; add
the AC-8 sibling-pressure paragraph to §A (`scored_rule._KNOWN_CRITERIA`, its
trigger, its tripwire). The annotation **preserves the literal `"N=4"`** and both
guard tests stay green (AC-6). (ii) Land the AC-7 ADR-0031 D3 row-3 update via the
G1 plan-drafter route. (iii) Companion artifact, filed by Code at commit time (not
by this drafter): the STATUS reconcile pointing PLAN-0076's Active-TODO line at the
new split state. Verification: guard tests green post-edit; the row text on `main`;
STATUS line present in the landing PR or the immediate `docs(status):` reconcile.

## Verification

Offline-first, and offline-sufficient: the ACs' pass/fail reads are all executable
with no DB beyond the existing suite's needs, no LLM, no MS-S1, no host-state
change (CLAUDE.md §8). **No live run is required or appropriate for acceptance.**
An optional live boot of one migrated vertical (e.g.
`OCT_VERTICAL=fleet_maintenance`, confirm the parked doa_tier gate + the rule_gate
verdict on the seeded run — the PLAN-0086 AC-2 shape) would be *evidence, not a
gate*, and needs Cray's explicit go before running. The decisive artifacts are:
AC-1's proof pair (the pressure is gone), AC-2's untouched pins (nothing moved),
AC-5/AC-6's untouched governance tripwires (nothing rotted).

## References

- **Dispatch:** `.claude/handoffs/session-158/2026-07-21-1817-code-plan-drafter-gate-seam-criterion-vocabulary-dispatch.md`
  (fact-pack verified by Code against `main = 8682b9c`; two PLAN-0076 anchor-drift
  corrections + the second pressure point originate there and were re-verified by
  this drafter).
- **PLAN-0076** (`docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md`)
  — Step T1 (both firing records: N=3 re-arm, N=4 cancellation); §A F-FACTORY
  severity wording (AC-1 pins "audit-flag over-mark, never an enforcement gap");
  Step T3 (guards retire only in the PLAN that closes their tracking); AC-6
  presence guard.
- **ADR-0031** (`docs/adr/0031-core-lifecycle-architecture.md`) — D2 principle +
  moat tripwires 3/4 (`:119-125`); D3 row 3 (`:136`); D4.1–D4.4 (`:148-159`);
  Negative §: "the map is a default, not a cage — deviation = amend this ADR's
  row" (`:178-180`).
- **ADR-0025** (`docs/adr/0025-at2-managerial-layer.md`) — D2 (typed union +
  provisional-until-N≥2 + "genericization gated behind the D7 re-trigger",
  `:75`); D3 (unrepresentable bypass; `RelaxableConstraint` non-waivable);
  D7 (the cancelled deferral); LOCKED #3 (abstain path stays).
- **The guard module:**
  `tests/services/engine/procedures/test_at2_signature_retrigger.py` — module
  docstring N=2/N=3/N=4 history; `_BASELINE_SIGNATURES` (`:150-188`);
  `_content_enum_surface` (`:212-235`); `test_at2_generator_deferral_retrigger`
  (`:285-297`); `test_at2_extraction_obligation_is_owned` (`:300-320`);
  `_procurement_shaped_procedure` (`:339-367`).
- **Code anchors** (drafter-verified on disk 2026-07-21 against `main = 8682b9c`;
  symbols are the stable reference):
  `services/engine/procedures/spec.py:853-885` (`ComplianceCriterion`, 13 members /
  4 blocks), `:888-902` (`SourcePolicy`, executor-keyed), `:905-915`
  (`ExceptionPolicy`, label), `:918-923` (`RelaxableConstraint`), `:1032-1056`
  (`ComplianceRule` / `ComplianceGate`; `criterion` field `:1039`), `:1059-1075`
  (`ExcursionSeverity` + `SEVERITY_BY_RANK`), `:1143-1145` (`AT2Governance`,
  4-arm), `:202-216` (`GateKind`, 7 members), `:1655-1700` (`VerticalProcedures` +
  `_validate_principals`);
  `services/engine/procedures/rule_gate.py:40-43` (`COMPLIANCE_FIELD`), `:135-136`
  (the only member consumer — plain string key);
  `services/engine/procedures/scored_rule.py:53-59` (`_KNOWN_CRITERIA`), `:169-181`
  (`_weights` fail-closed), `:22-23,197` (criticality executor semantics);
  `services/engine/registry.py:30` (zero-arg `ExecutorFactory`), `:100-112`
  (`register_procedure_executors`);
  `services/engine/procedures/governance_pin.py:58,74-78` (`_step_governance_snapshot`
  pins `model_dump(mode="json")`), `:19-22` (vertical-level blocks outside the pin
  surface);
  `services/engine/procedures/governance_step.py:201,260` (`sod_required` display
  flag);
  `verticals/procurement/hero_demo/run.py:298` (the surviving `sod_steps` hardcode
  — corrected from PLAN-0076's stale `:278`);
  `verticals/supply_chain/procedures_factory.py:244,298` /
  `verticals/building_materials/procedures_factory.py:64` /
  `verticals/fleet_maintenance/procedures_factory.py:61` (three verticals derive;
  `stamp_steps` supply_chain-only, + `cold_chain_assess.py:236-239`).
- **Test-side constructor census (Step 4's mechanical set):**
  `test_at2_signature_retrigger.py:115,348`; `test_rule_gate.py:41,60-68`;
  `test_red_team_at2.py:49,137`; `test_draft_lift_governance.py:48,592`;
  `test_spec.py:23,850`.
