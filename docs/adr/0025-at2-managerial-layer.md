# ADR-0025: The AT-2 / managerial-process layer — make DOA / SoD / scored-rule / approval-tier governance first-class, runnable, and demoable (the Box-3 "Action = contract" story), and close the run-gate's AT-2 blindness

**Status:** Accepted
**Date:** 2026-06-28
**Ratified:** 2026-06-28 (session 84) by Jirachai Thiemsert (Cray), **per the recommendations** — **OQ-1 = (c)** (build the managerial layer; defer the generator under the enforceable N≥2 re-trigger — the N=1 "(b)-minus-codegen" trade is accepted *because closing the live run-gate-blindness defect requires typing the AT-2 obligation regardless*); **OQ-2 = (b)'s discipline inside (a)'s mechanism** (typed, but instance-scoped + provisional-until-N≥2, genericization gated on the D7 re-trigger); **OQ-3 = D6's boundary** (enforce deterministically under the four hard guarantees, else fall back to author + render — the concrete v1 run-vs-author call is made in the follow-on PLAN per the four-guarantee feasibility); **OQ-4 / OQ-5 = as recommended**. Code R2 independently verified the substrate (the AT-2 run-gate-blindness defect is live on HEAD; `validate_governance_complete` is shipped; AT-2 = N=1).
**Deciders:** Jirachai Thiemsert (founder) — ratifies the construct AND adjudicates the Open Questions (§ Open Questions), especially **OQ-1** (the scope-vs-Rule-of-Three crux)
**Related:** ADR-0024 (archetype-first procedure generator — **this ADR revisits its D7** AT-2-deferral and **decides its OQ-8** typed-content precondition; it inherits the D3 "governed ≠ generated made mechanical" draft type + the G/H/D field partition); ADR-016 (governed procedure engine — D2 the `Step`/`Procedure`/`Agent` grammar; **D2-A4** facets are non-authoritative at run time; D3 safe-by-default autonomy + agent blast-radius allowlist; the run path this ADR's run option (OQ-3) extends, **not a new engine**); ADR-016 D2 Amendment 2026-06-25 (the typed `facet:` + the `gate_kind` 6-kind enum); ADR-0019 / ADR-010 IN-3 (the determinism invariant — route on the engine verdict, never the LLM signal); ADR-006 D4 (Rule of Three — "concrete-first or nothing"; the gate that defers the AT-2 generator); ADR-007 (the `RecommendedAction` envelope + the approve→execute gate, **untouched** — the irreversible-write gate the run option reuses verbatim); ADR-009 D1/D2 (Cowork drafts ungated, only Code commits); ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 (Cowork = advisory governance drafter). Substrate: `services/engine/procedures/spec.py` (`GateKind`, `Step`/`Procedure`/`Agent`, `DecisionCondition`, `extra="forbid"`), `services/engine/procedures/orchestrator.py` (`validate_runnable` / `validate_governance_complete`), `services/engine/procedures/draft.py` (`StepDraft`, `GOVERNANCE_FIELDS`, `derive_governance_todo` / `unfilled_governance`), `verticals/procurement/procedures.yaml` (`emergency_sourcing_round` — the only AT-2), `services/api/static/assets/view-procedures.js` + PLAN-0039 (AT-2 renders read-only today), `docs/conventions/procedure-archetypes.md` (the AT-2 governance signature). Consuming work: a follow-on PLAN (its own dispatch — OQ-5).

> **Drafting provenance.** Drafted (uncommitted) by Cowork (Tier-1 governance authoring; ADR-009 D1 interim per ADR-013's phased relocation — Cowork = advisory drafter). Code R2-reviews + commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). **Cowork does not git** (G5). This is a **new ADR**, so Code is G2-gated from authoring it (ADR-009 D1 — the same path ADR-0024 used); the independent design lens is the point, not a rubber stamp, because the ADR **revisits an Accepted-ADR decision** (ADR-0024 D7) and **decides ADR-0024 OQ-8**.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Originator = Cray (session 84: the locked O-1→O-3→O-2→O-4 sequence + the Rock-4 Box-3 finding that the managerial layer is vero-lite's strongest sellable box) **plus** Code (the s84 dispatch that scoped O-3 and surfaced the forks). Drafter = Cowork. **A Cowork-run adversarial panel (governance · schema · red-team lenses) pressure-tested this draft** under Cray's standing s81 go. *Honesty note:* unlike ADR-0024's **Code-run** 5-specialist panel (independent of the Cowork drafter), this panel is **Cowork's own subagents** — it is an adversarial self-review that materially sharpened the design, **not** an independent deliberation. The genuine independent-review checks remain **Cray at ratification + Code R2 at commit**; residual forks are surfaced as Open Questions, not silently resolved.

---

## Context

### What O-3 is, and why it is Cowork's to draft

Session 84 locked the Rock sequence O-1 → **O-3** → O-2 → O-4. O-1 (the Box-4 ฿-impact pitch artifact) shipped. **O-3 is the AT-2 / managerial-process layer**: making the governance-heaviest archetype — delegation-of-authority (DOA) tiers, separation of duties (SoD), scored-rule selection, per-criterion compliance, the emergency waiver, and traceable audit — **first-class** in the schema, **runnable** (the gate actually gates), and **demoable** as the Box-3 "Action = contract" story. The Rock-4 research (`docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md` §4 RQ-B1c, §1.4, §9 O-3) found that Box 3 (governed process — operational *and* managerial) is vero-lite's strongest market fit, and that the market leader monetizes exactly it: Palantir's April-2026 framing that **"each Action is like a contract: what it does, who can trigger it, under what conditions, and what gets logged"** is ≈ a verbatim description of vero-lite's `Agent.allowed` + gate + audit. The procurement design-partner archetype (Fastenal-class) *demands* the managerial controls (DOA / waiver / SoD / on-contract). The s84 insight: **our roadmap gap (deferred AT-2) is the business-model gap (the managerial layer the leader sells as the trust differentiator).**

This is a new ADR that revisits ADR-0024 D7 (which deferred AT-2) and decides ADR-0024 OQ-8 (the typed-content precondition) — so Code is G2-gated and Cowork drafts the independent design (ADR-009 D1).

### The same research's central finding — the evidence asymmetry: the bullish ROI numbers are vendor-authored; the independent evidence is skeptical

> _[Recorded 2026-07-17 (session 142): this finding is from the same session-84 Rock-4 research this ADR already cites above; it is rehomed here from `docs/STATUS.md` (its Active-TODO bullet is being trimmed to a pointer) because its only other full home is the gitignored research note. It changes no Decision (D1–D8), no LOCKED item, and no Open Question in this ADR.]_

Beyond the Box-3 market-fit conclusion above, the Rock-4 research (~48 sources, vendor-vs-independent tagged, adversarially balanced) reached one conclusion that outranks any individual number it collected: **the evidence asymmetry is itself the story — the bullish ROI numbers for this product category are almost all vendor-authored, and the independent evidence is mostly skeptical.** Every load-bearing number was tagged with one of three provenance grades: **[VENDOR-CLAIM]** (asserted by the vendor, or by its customer at a co-marketing / investor event — marketing-grade), **[VENDOR-COMMISSIONED]** (third-party-authored — e.g. a Forrester TEI — but vendor-funded, and usually modeling a *composite organization* rather than a measured customer), and **[INDEPENDENT]** (analyst / academic / journalist / standards body with no vendor commission; sub-flagged *sell-side* or *advocacy*). The middle tag is the non-obvious trap: an "independent author" is **not** independent evidence when the funding is the vendor's and the "customer" is a modeled composite.

**Why it is recorded here:** it constrains how vero-lite makes ROI claims to a design partner — the honest posture is **conservative, customer-calibrated numbers, never borrowed vendor-grade claims**. That posture is already house practice, and this finding is the evidence base that explains *why* it is correct, not a new decision: the O-1 Box-4 ฿-pitch artifact (the same O-sequence, one slot earlier) was deliberately built on a conservative hand-computed ฿ example whose numbers are "a customer-calibrated floor to avoid the too-good-to-be-true backfire" (`docs/status-archive/2026-h1-status.md:1462-1466`). Source-by-source detail stays in the gitignored working note this ADR already cites, referenced by path only per the ADR-0032 public-repo boundary: `docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md` (§0 for the tag taxonomy, §1.4).

### The honest tension this ADR must resolve (not bury): AT-2 is still N=1

ADR-0024 D7 deferred the AT-2 *generator* for reasons **none of which have changed**: AT-2 appears in **exactly one** procedure (`procurement.emergency_sourcing_round`, gate sequence `[none, in_file_band, scored_rule, rule_gate, doa_tier, none, none]` — verified; the vertical's only other procedure, `low_stock_reorder_round`, is calm-path AT-3 with no scored-rule / rule-gate / DOA gate), it is the governance-heaviest archetype, and its rule/criteria/DOA **content has no typed schema home** (OQ-8). What changed is the *strategic priority* of the managerial layer, not the example count. The job of this ADR is to separate **what is Rule-of-Three-safe to build now** (closing a live defect; giving the existing AT-2's content a typed home; running the hand-authored AT-2) from **what stays deferred** (generating AT-2 skeletons) — and to do so without pretending the N=1 tension is gone. **OQ-1 is that fork, and it is the single most valuable call in this ADR.**

### The fact-pack finding that re-frames everything: the run-gate is blind to AT-2 content *today*

The shipped run-gate `validate_governance_complete()` (`orchestrator.py`, PLAN-0040 Step A4) refuses to run a skeleton that still carries un-authored governance stubs. It derives each step's obligations from `derive_governance_todo(step)` (`draft.py`), which today returns obligations **only** for `in_file_band` (→ `threshold`/`direction`), `env_band` (→ `env_var`), and `action` steps (→ `handler`/`autonomy`). For `scored_rule`, `rule_gate`, and `doa_tier` it returns **nothing**.

The consequence, verified against the live code: **an AT-2 procedure with empty DOA tiers, no compliance rules, and no scored-rule criteria is currently judged "governance-complete" and run-loadable.** The one archetype whose entire reason for existing is governance is the one the governance-completeness gate cannot see. This is exactly the latent surface ADR-0024 OQ-8 named ("AT-2's rule/criteria/DOA content lives in prose; a typed home is a precondition for any future AT-2"), now confirmed as a **shipped defect**, not a future risk. The procurement AT-2 is safe in practice only because its content is hand-written in prose (`facet.note` / `description`) — which is precisely the prose-smuggling surface the typed schema is supposed to close.

This re-frames the ADR: the primary deliverable is **closing a live governance hole** (and giving OQ-8 content its typed home) — the sellable Box-3 demo is the *evidence* that the hole is closed, not the motivation that justifies new abstraction. Closing the hole requires typing *some* AT-2 obligation regardless of strategy; the only question is how far (OQ-2).

### "governed ≠ generated" must hold at the AUTHORING surface for AT-2 content too

ADR-0024 D3 made the invariant mechanical for the AT-1 family: the generator emits a restricted `StepDraft` with **no** governance fields, so a leak is a type error; a deterministic lift injects governance as absent stubs; a prose-lint rejects laundered values. AT-2's content (DOA ฿-tiers, scored-rule weights, compliance predicates, approver authority, SoD) is the **highest-consequence** governance content in the system. Whatever typed home it gets must be **human-author-only**, structurally absent from any draft type, registered in `GOVERNANCE_FIELDS`, and protected by the prose-lint — or the typed home becomes a *new* generation target and re-opens the very surface OQ-8 flagged.

---

## Decision

Make the **AT-2 / managerial-process layer first-class** by (1) giving AT-2's governance **content** a typed, human-only, authoritative home in the spec; (2) extending the run-gate so it can **see** that content (closing the blindness defect); (3) optionally enforcing the gates **at run** under hard guarantees so the Box-3 demo's gate actually gates; and (4) **deferring the AT-2 generator** under an enforceable Rule-of-Three re-trigger. Every decision below is rendered against the LOCKED substrate and is contingent where noted on the Open-Question fork it implements.

### LOCKED (the substrate — render faithfully; do NOT re-litigate)

1. **"governed ≠ generated" is untouched** (ADR-0024 D3). Every governance value stays a human-author stub / typed human-only field — never model-emitted. The OQ-8 typed sub-model (D2) is a typed **HUMAN-authored** home, **not** a generation target.
2. **AT-2 is already partly first-class** — name what exists so this ADR adds only the delta: the gate kinds `scored_rule` / `rule_gate` / `doa_tier` exist in `GateKind`; procurement **hand-authors** the AT-2 procedure; **PLAN-0039 already renders AT-2 read-only**. This ADR builds on that; it does not start from zero.
3. **The AT-2 cross-check / abstain path stays intact** (ADR-0024 D4/D7; PLAN-0041 LOCKED). The classify generator still **abstains** on AT-2-class narratives. This ADR does **not** make the *generator* emit AT-2 (that is OQ-1 option (b), recommended against).
4. **Rule-of-Three is binding** (ADR-006 D4). The AT-2 *generator* stays deferred while AT-2 is N=1; D7 states the enforceable re-trigger.
5. **Run = ADR-016 territory.** If AT-2 *runs* (OQ-3), it extends the shipped orchestrator (`validate_runnable` / `validate_governance_complete` + the per-kind executors) — **not** a new engine — and honors ADR-016 D2-A4 (the descriptive `facet:` stays non-authoritative at run time; the new authoritative content lives on typed `Step`/`Procedure` fields, never in the facet).

### D1 — Scope is the managerial LAYER, not the generator: author + run + demo on HAND-AUTHORED AT-2 (implements OQ-1, recommended (c))

O-3 builds the layer that makes a hand-authored AT-2 procedure first-class — a typed content home (D2), a run-gate that sees it (D5), deterministic run-enforcement under guarantees (D6), and the Box-3 demo (D8) — and **defers the AT-2 generator** (D7). In OQ-1's terms this is option **(a)** (the layer, generator deferred); the **recommendation is (c) = (a) + D7's enforceable Rule-of-Three re-trigger**, which makes the deferral self-cancelling at N≥2. It deliberately does **not** extend the classify-generator to emit AT-2 (LOCKED #3). The framing is *closing a defect + giving OQ-8 content a home*, not *adding a generative capability*: the minimum typing needed to make the run-gate AT-2-aware is the floor; everything beyond that floor is justified by the Box-3 demo and scoped conservatively (D2, Rule-of-Three caveat).

### D2 — The OQ-8 typed sub-model: human-only, AUTHORITATIVE, instance-scoped, provisional (implements OQ-2)

Give AT-2's content a typed home as **authoritative top-level fields** (the source of truth, like `Step.threshold`), **not** inside the non-authoritative `facet` (D2-A4). The `gate_kind` **points at** the content — mirroring the shipped `in_file_band → Step.threshold` pattern (D2-A3: point at, do not re-store). Concretely, one optional **discriminated union** on `Step`, keyed to the AT-2 `gate_kind`, plus a procedure-level SoD constraint:

- `Step.governance_content: AT2Governance | None`, where `AT2Governance = Annotated[DoaLadder | ScoredRule | ComplianceGate, Field(discriminator="kind")]`. The discriminator literal is the structural link to `gate_kind` (D4 enforces correspondence). One field, not four bare `Optional`s — it narrows the `extra="forbid"` surface and makes a leaked variant one test, not four.
  - **`DoaLadder`** (on a `doa_tier` action step): `tiers: list[DoaTier]` (`DoaTier{ min_amount: Decimal, approver_role: RoleId }`, money is `Decimal`, never `float`) + `emergency_waiver: EmergencyWaiverPolicy` (D3).
  - **`ScoredRule`** (on a `scored_rule` action step): `criteria: list[ScoredCriterion{ name, weight: Decimal }]` + `default_source: SourcePolicy` (enum, e.g. `on_contract`) + `exception_policy: ExceptionPolicy` (enum, e.g. `rfq_avl_logged`). The selection logic is deterministic and human-authored; the LLM only summarises quotes.
  - **`ComplianceGate`** (on a `rule_gate` evaluate step): `rules: list[ComplianceRule{ criterion: ComplianceCriterion (StrEnum: avl|tax|cert|sanctions|single_source), spec: Predicate, blocks_po: Literal[True] }]`.
- `Procedure.separation_of_duties: list[SoDConstraint]`, `SoDConstraint{ distinct_steps: frozenset[StepId] (min 2) }` — genuinely procedure-scoped (it spans steps); a `model_validator` rejects dangling `step_id` references and degenerate single-step sets.

**Rule-of-Three caveat (load-bearing, per the red-team).** A typed sub-model *is* an abstraction, and it is extracted from **N=1**. To avoid moving the Rule-of-Three violation from the generator into the type system, the models are **scoped tightly to the observed `emergency_sourcing_round` signature**, marked **provisional-until-N≥2** in their docstrings, and **genericization is gated behind the D7 re-trigger**. We type the content because the run-gate hole *requires* a typed obligation to close (D5) and OQ-8 *requires* a home — not to pre-build a reusable AT-2 framework. See OQ-2 for the promoted-reusable-vs-instance-scoped fork.

### D3 — Bypass is UNREPRESENTABLE, not defaulted-false (the structural-impossibility principle)

A safety bool a future edit can flip (`skips_gate=False`, `blocks_po=False`) is not a guarantee. The typed model removes the *ability to express* a bypass:

- **The emergency waiver carries no skip.** `EmergencyWaiverPolicy{ relaxes: list[RelaxableConstraint] (closed enum, e.g. three_bid | sole_source; non-empty), escalate_to: RoleId, requires_justification: Literal[True] = True }`. There is **no** field that removes a gate, lowers a tier, or skips compliance/SoD — so "skip" is unrepresentable. A `model_validator` requires the waiver to **strictly escalate** (`escalate_to` is a *higher* authority than every tier it relaxes). Compliance and SoD are **non-waivable by type** (the `RelaxableConstraint` enum cannot name them).
- **Compliance always blocks.** `ComplianceRule.blocks_po: Literal[True]` — a non-blocking "compliance" rule is unrepresentable (it would not be a gate).
- **The DOA ladder is total and unambiguous.** A `DoaLadder` `model_validator` enforces: single currency across tiers; `min_amount` strictly increasing (no overlap, no equal thresholds); first tier `min_amount == 0` (every spend ≥ 0 maps to exactly one half-open `[min_i, min_{i+1})` band; top tier unbounded); `tiers` non-empty; and **no `approver_role` equal to a resolved requester role** (checked at author-time and re-checked at run — D5).

### D4 — governed ≠ generated holds for AT-2 content at the AUTHORING surface (extends ADR-0024 D3)

- `governance_content` and `separation_of_duties` are **H** (human-author-only): added to `GOVERNANCE_FIELDS`, **never** declared on `StepDraft` / `ProcedureDraft`, injected by the lift as **absent** stubs.
- The CI disjointness test extends to **recursive** disjointness: no `DoaTier` / `ScoredRule` / `ComplianceRule` (nor any union variant) is reachable from any draft type's fields — a generated value is a type error at the boundary.
- **D2-A4 stays structurally true:** a CI check asserts no AT-2 content type is reachable from `StepFacet.model_fields`; the facet's `decision_condition` may only carry the `gate_kind` (point at), never embed a ladder.
- The ADR-0024 **prose-lint is extended** to the AT-2 free-text surfaces (the waiver justification, tier/criterion `note`/`label`, `description`, `goal`): a ฿-amount, a weight, or an approver-role token appearing in any free-text field **blocks load**. These free-text fields are **non-authoritative by type** (never a gate input) and render with a "GENERATED — NOT A CONTROL" provenance band. This closes the residual prose-smuggling vector the typed fields alone do not (red-team Attack 1).

### D5 — The run-gate becomes AT-2-aware: SEMANTIC completeness, not presence (closes the shipped blindness defect)

Extend `derive_governance_todo` (and therefore `validate_governance_complete`) so the AT-2 gate kinds owe their content: a `scored_rule` action owes a `scored_rule`; a `rule_gate` evaluate owes ≥1 `ComplianceRule`; a `doa_tier` action owes a `DoaLadder`; and a procedure carrying a `doa_tier` step owes a `separation_of_duties` constraint. **Completeness is semantic, not mere presence** (red-team Attacks 2/3): an empty / duplicate / unreachable / `∞`-floored tier ladder, a zero-criteria scored rule, a compliance gate with no rules, or an SoD whose roles resolve to one principal must each **fail** the gate. SoD is enforced on resolved **principal identity** (requester_principal ≠ approver_principal), not role labels, and **fails closed** if either is unresolvable to a distinct human. This makes the existing procurement AT-2's content a typed-authoring obligation (the migration in D6 / Implementation Notes) and shuts the hole permanently — with a **negative regression test** (a hollow-but-complete AT-2 skeleton MUST be refused) as a ratification gate.

### D6 — The run boundary (implements OQ-3): enforce deterministically UNDER hard guarantees, else author + render

The Box-3 demo is far stronger if the gate *gates*. Making the hand-authored AT-2 *run* is Rule-of-Three-safe (it runs an existing example; it does not *generate* one) and extends the shipped orchestrator, not a new engine (LOCKED #5). The run path **may** enforce deterministically — the `doa_tier` step computes the required tier from the ฿ amount + ladder and routes/suspends to that approver; the `rule_gate` step blocks the PO on any failed criterion; the `scored_rule` step selects on the typed rule (LLM only summarises) — **iff** these four guarantees hold in v1, each a hard requirement:

1. **Principal-level SoD at run** (not role labels; reject alias-collapse; fail closed).
2. **Audit-to-control is an engine side-effect**, not an authorable step: every route/block/select decision emits a record naming the control that governed it; the audit obligation cannot be authored `auto`/omitted, and `autonomy: auto` is forbidden on any step downstream of a gate (red-team Attack 5).
3. **Irreversible-write boundary**: the run path is **render / route / block only** — no ERP I/O, no PO emission, no irreversible side-effect; the existing ADR-007 approve→execute gate stays the only path to a write, behind the human go/no-go.
4. **No live LLM, no generation** in the v1 run path (the offline oracle is the gate; CLAUDE.md §8).

**If any guarantee cannot be met in v1, the conservative fallback (author + render only, the gate visible but not enforced) is the correct ship** — a read-only artifact is strictly safer than a run path that certifies an un-owned control as owned (red-team §3). OQ-3 is Cray's to set; D6 is the recommended boundary.

### D7 — Defer the AT-2 generator with an ENFORCEABLE Rule-of-Three re-trigger

The AT-2 *generator* stays deferred (LOCKED #3/#4). Two reinforcements over a bare "deferred":

- **The re-trigger is enforceable, not a comment.** A CI assertion counts AT-2-class procedures across `verticals/*/procedures.yaml`; when **N ≥ 2** (e.g. the Fastenal hand-authored AT-2 + a second triangulate the shape), the assertion flags "re-evaluate the AT-2 generator deferral (ADR-0025 D7)" so the deferral cannot silently erode under delivery pressure (governance R5). Genericizing the D2 types from instance-scoped to reusable is gated on the same N ≥ 2.
- **Deferring the generator *is* the defense against routing-into-AT-2** (red-team Attack 4): because AT-2 is hand-authored and the classify-generator abstains on AT-2 narratives (PLAN-0041 LOCKED), there is no automated path that mis-routes a benign narrative *into* AT-2 to inherit a rich, defaulted control surface. The archetype assignment stays a human-authored, logged, immutable decision.

_[Recorded 2026-07-22 (session 160): **outcome amendment — the D7 arc completed.** This note records what subsequently HAPPENED; it changes no Decision (D1–D8), no LOCKED item, and no Open Question — the "N ≥ 2" text above remains the faithful record of the 2026-06-28 decision and is deliberately NOT rewritten. The arc: the re-trigger **fired at N=2** (supply_chain cold-chain disposition, PLAN-0074) and the re-evaluation was **performed** — generator stayed deferred (PLAN-0074 SD-3, Cray-ratified). It **fired again at N=3** (building_materials `governed_credit_release`, PLAN-0081) — re-evaluated, still deferred (PLAN-0081 Step 8, Cray-ratified). At **N=4** (fleet_maintenance `governed_repair_approval`, PLAN-0086) the deferral was **CANCELLED, not re-armed** (Cray, typed, 2026-07-21, session 157, at the PLAN-0086 escalation). What forced the cancellation was NOT a gate shape finally generalising: it was four verticals each needing an engine edit to the closed `ComplianceCriterion` enum — the D2 instance-scoped types recurring as an engine-edit-per-vertical tax. PLAN-0087 executed the cancellation's answer by retiring that enum from engine code: each vertical now **declares** its own criterion vocabulary (`VerticalProcedures.compliance_criteria`, membership-validated at load), so a fifth vertical ships its `rule_gate` with zero engine diff. The enforcement mechanism this D promised has itself changed shape: the `N < _RETRIGGER_N` count assertion is **retired** (its own docstring says it guards nothing) and **replaced** by the `_BASELINE_SIGNATURES` set-equality census pin in `tests/services/engine/procedures/test_at2_signature_retrigger.py`, which turns RED on a FIFTH signature — a moved baseline still means "stop and re-argue", so the deferral-cannot-silently-erode intent of this D survives its original mechanism. The *generator* itself still abstains on AT-2 (LOCKED #3 stands); the residual extraction item is the procedure-aware `ExecutorFactory`, owned by PLAN-0076 Step T1 (F-FACTORY) — which is why PLAN-0076 is not archived.]_

### D8 — The Box-3 "Action = contract" demo + the offline oracle (implements OQ-4)

The demo is the managerial scene the research says sells: a proposed procurement action that **routes to a specific human approver** (because its ฿ amount crosses a DOA tier) or **blocks** (because a compliance criterion fails or SoD is unsatisfied), each with the **audit line tying the decision to the control that governed it**. The binding offline oracle (mirroring ADR-0024 D12; the LLM is stubbed with fixtures so the suite is deterministic and offline) makes the red-team fixtures the acceptance gate:

1. **Hollow-but-complete skeleton** — empty/duplicate/`∞` DOA tiers, zero compliance rules, `approver_role == requester_role` → `validate_governance_complete` **rejects** (closes the live hole; D5).
2. **Leak-in-free-text corpus** — a ฿-amount, a weight, and an approver-role token seeded into the waiver justification, a tier `note`, and a criterion `label` → the prose-lint **blocks load** and the fields are typed non-authoritative (D4).
3. **Identity-collapse + un-gated-audit run** — SoD roles resolving to one principal, plus an audit step authored `auto`/absent and a downstream `auto` step → the run **fails closed** and emits no "governed" verdict (D6).

No live MS-S1 is needed (generation is out of scope).

## Consequences

### Positive

- **A live governance defect is closed.** The run-gate stops being blind to the one archetype that is all governance; an empty AT-2 can no longer be certified run-loadable. This is true value independent of the demo.
- **The differentiator becomes demoable.** "A human owns every gate" stops being a slogan for AT-2: the DOA tier *routes*, the compliance gate *blocks*, SoD *holds on real identities*, and every decision is *traceable to its control* — the Box-3 "Action = contract" story, realized mechanically.
- **OQ-8 is decided** with a typed home that is human-only by construction — and the prose-smuggling surface it named is closed by the extended prose-lint, not merely flagged.
- **On-thesis, low blast radius.** It extends the shipped engine (ADR-016) and the shipped draft layer (ADR-0024), introduces no new generation surface, and leaves the ADR-007 write gate and the ADR-008 ontology codegen path untouched.

### Negative / risks

- **The Rule-of-Three tension is real and unresolved by fiat** (red-team §2): typing AT-2 content from N=1 commits AT-2-shaped engineering against a single example. If the second AT-2 differs (different criteria set, non-฿ DOA, multi-party SoD), the authoritative types and the run path are wrong and already load-bearing — costlier to unwind than deferred prose. Mitigated by D2's instance-scoping + provisional marking + the D7 re-trigger gating genericization; **OQ-2 surfaces the stronger "keep it inline until N≥2" alternative for Cray.**
- **Running raises blast radius from "wrong document" to "wrong procurement action."** A bug in tier computation or compliance-blocking mis-routes or fails to block. Mitigated by the D6 hard guarantees and the conservative author+render fallback; the human approve→execute gate (ADR-007) remains the only write path.
- **The free-text leak surface can never be fully typed away** (the waiver justification must be free-text). Mitigated, not eliminated, by the prose-lint + non-authoritative typing + provenance banding (D4).
- **Migration risk:** the shipped procurement AT-2 carries its content in prose; once D5's obligations land, it fails `validate_governance_complete` until typed. Sequenced in Implementation Notes (type the content + extend the gate in one PR, guarded by a green golden test; the prose→typed transcription is human-reviewed against the source so a DOA threshold is not silently changed).

### Neutral

- This is a capability + schema + authoring-invariant decision (hence an ADR + a follow-on PLAN, not ad-hoc code). It *revisits* ADR-0024 D7 and *decides* its OQ-8; it does not supersede ADR-016 or ADR-0024 — it extends both. ADR merged before the related implementation PLAN (CLAUDE.md §8).

## Open Questions

Surfaced for Cray to adjudicate (options + a recommendation; not silently resolved). Numbered per the dispatch §3.

- **OQ-1 — THE CENTRAL FORK: scope vs Rule-of-Three (AT-2 is N=1). What does O-3 build?**
  - **(a) The managerial LAYER, generator DEFERRED.** Type the OQ-8 content, make the hand-authored AT-2 run-gate-aware + (per OQ-3) runnable, build the Box-3 demo — no generator extension.
  - **(b) Extend the GENERATOR to emit AT-2 now.** Higher leverage if it worked, but N=1 violates Rule-of-Three on the governance-heaviest archetype (the exact reason ADR-0024 D7 deferred it). **Recommended against.**
  - **(c) Hybrid: (a) now + a NAMED, ENFORCEABLE generator re-trigger** (D7: CI flags re-evaluation at N≥2; genericization of the D2 types gated on the same). **← Recommendation.** It closes the live run-gate hole and decides OQ-8 now (real, shipped exposure), delivers the sellable Box-3 story, and honestly defers the generator while making the deferral self-cancelling. *The strongest counter Cray should weigh (red-team §2): the typed sub-model is itself an abstraction from N=1 — "(b)-minus-codegen." The mitigation that makes (c) defensible is that closing the run-gate defect requires* some *typed obligation regardless, and D2 scopes the types to the one observed instance and gates any genericization on N≥2.* **State the choice explicitly — it is the load-bearing call.**

- **OQ-2 — the typed sub-model: promoted-reusable vs instance-scoped.** Both close the run-gate hole and decide OQ-8; they differ on Rule-of-Three exposure.
  - **(a) Promote named, reusable authoritative types now** (`DoaLadder` / `ScoredRule` / `ComplianceGate` / SoD as shared schema). Cleanest for a future second AT-2 — *if* it fits.
  - **(b) Keep the content instance-scoped / provisional now, genericize at N≥2** (the red-team's stronger Rule-of-Three stance). Less elegant, but it does not harden a one-example abstraction into the authoritative schema + run path.
  - **Recommendation: (b)'s discipline inside (a)'s mechanism** — define the typed models (needed to close the hole + give OQ-8 a home), but scope them tightly to the observed `emergency_sourcing_round` signature, mark them **provisional-until-N≥2**, and gate genericization on the D7 re-trigger. The schema-panel shape stands: one discriminated `Step.governance_content` union keyed to `gate_kind`; `Decimal` money; a strict-monotonic total-cover ladder validator; bypass made unrepresentable (D3); `extra="forbid"`; added to `GOVERNANCE_FIELDS` with recursive disjointness + a poisoned-narrative leak test.

- **OQ-3 — run vs author-only.** Does v1 make the AT-2 procedure *execute* (DOA gate routes, SoD enforced, compliance blocks, audit traces) or stop at *author + render*?
  - **Recommendation: enforce deterministically UNDER the four D6 hard guarantees** (principal-level SoD; audit-to-control as an engine side-effect; render/route/block-only with no ERP I/O; no live LLM/generation) — **else fall back to author + render**. Running makes the Box-3 gate actually gate (the demo the research says sells) and is Rule-of-Three-safe; but a run path that cannot guarantee the four is worse than read-only, so the fallback is explicit and Cray sets the boundary.

- **OQ-4 — what proves O-3 (acceptance + demo).** **Recommendation:** the offline oracle = the three red-team fixtures (D8) + the typed-sub-model + obligation-derivation unit tests + (if OQ-3 run) the DOA-routing / SoD / compliance-block enforcement tests; the demo artifact = the "Action = contract" managerial scene (route-to-human / block + the audit line). No live MS-S1.

- **OQ-5 — ADR-only, ADR + follow-on PLAN, or an ADR-0024 amendment?** **Recommendation: a standalone ADR-0025** (it revisits an Accepted-ADR decision (D7) and decides OQ-8 + adds a schema layer + a run boundary — too big for an amendment), then a **follow-on PLAN** (its own dispatch) for the build. The PLAN — not this ADR — owns the migration sequencing (type the existing procurement AT-2 + extend the gate in one PR behind a green golden test; consider a `schema_version` for any persisted specs).

## Alternatives Considered

### Alternative 1: Do nothing now — keep AT-2 deferred + read-only (the status quo)
- **Pros:** zero new blast radius; maximal Rule-of-Three conservatism.
- **Cons:** leaves the **shipped run-gate blindness** open (an empty AT-2 is run-loadable today) and leaves OQ-8's prose-smuggling surface open; forgoes the research-validated Box-3 differentiator.
- **Why rejected:** the run-gate hole is a live defect that requires typing *some* AT-2 obligation to fix; "do nothing" is not actually safe.

### Alternative 2: Put AT-2 content in the non-authoritative `facet`, made authoritative-for-AT-2
- **Pros:** one place for all step metadata; no new top-level fields.
- **Cons:** violates ADR-016 D2-A4 (the facet is non-authoritative at run time) or forces a corrosive "this facet sub-field is authoritative" carve-out; the engine would not consume it.
- **Why rejected:** D2 puts authoritative content on typed top-level `Step`/`Procedure` fields; `gate_kind` only *points at* it; a CI check keeps AT-2 content unreachable from the facet.

### Alternative 3: Four bare `Optional` governance fields on `Step`
- **Pros:** simplest to write.
- **Cons:** widens the `extra="forbid"` / disjointness surface; per-kind validation becomes N independent None-checks; a leak is four tests, not one.
- **Why rejected:** one discriminated `governance_content` union keyed to `gate_kind` (D2) is tighter and ties the gate↔content correspondence to a single discriminator equality.

### Alternative 4: Model the emergency waiver with a `skips_gate: bool = False` (defaulted-safe) flag
- **Pros:** explicit and readable.
- **Cons:** a future edit flips the bool; "safe by default" is not "safe by construction."
- **Why rejected:** D3 removes the skip field entirely — skipping a gate, lowering a tier, or waiving compliance/SoD is **unrepresentable**, which is strictly stronger than defaulted-false.

### Alternative 5: Enforce SoD on role labels (`requester_role ≠ approver_role`)
- **Pros:** checkable at author-time with no identity resolution.
- **Cons:** roles resolve to humans at run; a single principal holding both roles (small org, on-call, alias chains) passes structurally and fails in fact.
- **Why rejected:** D5/D6 enforce SoD on resolved **principal identity** at run and fail closed on alias-collapse / unresolvable identity.

### Alternative 6: Extend the generator to emit AT-2 now (OQ-1 (b))
- **Pros:** covers the highest-value archetype immediately.
- **Cons:** N=1 violates Rule-of-Three on the governance-heaviest archetype; down-classification silently deletes controls (ADR-0024 leak class 2).
- **Why rejected:** the generator stays deferred (D7) with an enforceable re-trigger; the abstain path (PLAN-0041) routes AT-2 narratives to hand-author.

## References

- ADR-0024 (archetype-first procedure generator — **D7** AT-2 deferral revisited here; **OQ-8** decided here; **D3** the mechanical "governed ≠ generated" + the G/H/D partition inherited) — `docs/adr/0024-procedure-generator.md`
- ADR-016 (governed procedure engine — D2 grammar; **D2-A4** facet non-authoritative; D3 autonomy + allowlist; the run path OQ-3 extends) — `docs/adr/0016-governed-procedure-engine.md`
- ADR-0019 / ADR-010 IN-3 (the determinism invariant) · ADR-006 D4 (Rule of Three) · ADR-007 (the `RecommendedAction` approve→execute write gate, untouched) · ADR-009 D1/D2 (Cowork drafts, only Code commits) · ADR-012 D4.3 (author≠reviewer) · ADR-013 (Cowork = advisory drafter)
- `services/engine/procedures/spec.py` — `GateKind` (the 6 kinds incl. `scored_rule`/`rule_gate`/`doa_tier`), `Step`/`Procedure`/`Agent`, `DecisionCondition` (the `in_file_band → threshold` point-at precedent, D2-A3), `extra="forbid"`, `_validate_step`, `load_procedures` (shape + cross-ref only)
- `services/engine/procedures/orchestrator.py` — `validate_runnable` → `validate_governance_complete` (the run-gate the D5 extension targets)
- `services/engine/procedures/draft.py` — `StepDraft` / `GOVERNANCE_FIELDS` / `derive_governance_todo` / `unfilled_governance` (the verified AT-2 blindness: no obligation for `scored_rule`/`rule_gate`/`doa_tier`)
- `verticals/procurement/procedures.yaml` — `emergency_sourcing_round` (the only AT-2; the N=1 fact) + `low_stock_reorder_round` (the calm-path AT-3 contrast)
- `services/api/static/assets/view-procedures.js` + `docs/plans/done/0039-readonly-facet-viewer.md` — AT-2 renders read-only today (the delta is author/run/demo, not render)
- `docs/conventions/procedure-archetypes.md` — the AT-2 governance signature (scored-rule selection · per-criterion rule gate · tiered DOA + emergency waiver "escalate-never-skip" · SoD · traceable audit)
- `docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md` §4 RQ-B1c / §1.4 / §9 O-3 (the Box-3 "Action = contract" strategic WHY) · `.claude/handoffs/session-84/2026-06-27-2349-code-strategy-4box-rocks-discussion.md` (the Box-3 reframe)
- CLAUDE.md §4 (canonical→derived), §6 (Decision Flow), §7 (no `Co-Authored-By`), §8 (AI assistive; data residency; the offline oracle is the gate)

## Implementation Notes

This ADR decides capability + schema + an authoring/run invariant; the mechanics are a **follow-on PLAN** (its own dispatch — OQ-5), which owns, in order:

1. **Type the existing procurement AT-2 content + extend the run-gate in ONE PR**, guarded by a green golden test that loads every shipped vertical through `validate_governance_complete` across the diff. The prose→typed transcription of the procurement DOA tiers / compliance criteria / scored-rule is **human-reviewed against the source procedure** so a DOA threshold is not silently changed. Consider a `schema_version` if any procedure specs are persisted/replayed.
2. **The discriminated `Step.governance_content` union + the `Procedure.separation_of_duties` field** (D2) with the D3 validators (Decimal money; strict-monotonic total-cover ladder; unrepresentable bypass; strict-escalation waiver; non-waivable compliance/SoD).
3. **The `derive_governance_todo` / `validate_governance_complete` extension** to semantic AT-2 completeness (D5) + the new fields in `GOVERNANCE_FIELDS` + recursive draft-disjointness + the `StepFacet`-unreachability check (D4).
4. **The extended prose-lint** over the AT-2 free-text surfaces (D4) + the "GENERATED — NOT A CONTROL" provenance banding in the viewer (reusing the PLAN-0039 component in edit mode).
5. **(If OQ-3 = run)** the deterministic enforcement executors (DOA tier routing on `Decimal` amount; principal-level SoD; compliance block; scored-rule select; audit-to-control as an engine side-effect) under the D6 hard guarantees — extending the shipped orchestrator, not a new engine; **else** ship author + render only.
6. **The offline oracle** = the three red-team fixtures (D8) + the unit suite. The LLM is stubbed with recorded fixtures (deterministic, offline; CLAUDE.md §8).

Out of scope (→ later PLANs): the AT-2 **generator** (D7, Rule-of-Three-deferred until N≥2); making the *classify generator* emit AT-2 (the abstain path stays — PLAN-0041 LOCKED); live ERP/email I/O behind the write gate; the Box-4 economic-impact facet (O-2); agent-interop (O-4).

Status flips Proposed → Accepted on Cray ratification; Code applies + commits via a `docs/*` PR (ADR-009 D2; CLAUDE.md §6 Decision Flow). AI-assisted (Cowork drafter + a Cowork-run adversarial panel); no `Co-Authored-By` per CLAUDE.md §7.
