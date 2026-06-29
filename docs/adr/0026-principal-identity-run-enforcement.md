# ADR-0026: Principal-identity capability + AT-2 run-time enforcement — resolve a HUMAN principal at run time and enforce separation-of-duties / tiered-DOA / scored-rule / compliance gating AT RUN (the deferred ADR-0025 AC-13-ALT "A2 run path")

**Status:** Accepted
**Ratified:** 2026-06-29 (Jirachai Thiemsert / Cray, session 87) — all 6 Open Questions adjudicated as-recommended; see § Open Questions.
**Date:** 2026-06-29
**Deciders:** Jirachai Thiemsert (founder) — ratifies the construct AND adjudicates the Open Questions (§ Open Questions)
**Related:** ADR-0025 (the AT-2 / managerial-process layer — **this ADR IMPLEMENTS its D5/D6 semantics; it does NOT re-decide them** — the principal-identity SoD, the four D6 hard guarantees, the fail-closed-on-alias-collapse rule are FIXED here, never weakened; ADR-0025 D5/D6 + the four hard guarantees, `:84-97`; Alternative 5 = role-label SoD REJECTED, `:179-182`; D8 red-team fixture 3 = identity-collapse + un-gated-audit → fail closed, `:110-112`); ADR-0008 (the YAML ontology grammar — the home for the first-class `Person`/`Principal` resolvable object); ADR-0007 (the `RecommendedAction` approve→execute write gate — **the only external write path, untouched**: run-enforcement routes / suspends / blocks / audits, it does **not** issue the real PO); ADR-016 (the governed procedure engine — D2 the `Step`/`Procedure`/`Agent` grammar; the `StepExecutor` Protocol + the orchestrator run path this ADR's A1b executors extend, **not a new engine**; D2-A4 the descriptive `facet:` stays non-authoritative); ADR-0024 D3 (the "governed ≠ generated" partition — principals + role bindings are **H** human-author-only governance data, never model-emitted); ADR-006 D4 (Rule of Three — the gate on the `Person` core-vs-per-vertical scope, OQ-6); ADR-011 (the deferred audit-framework — OQ-5 keeps the human-principal field minimal so it does not pre-empt it); ADR-009 D1/D2 (the in-harness `plan-drafter` drafts ungated, only Code commits); ADR-012 D4.3 / ADR-013 (author≠reviewer; phased authority). Consuming work: a follow-on PLAN (its own dispatch) for the A1a→A1b build.

> **Drafting provenance.** Drafted (uncommitted) by the in-harness `plan-drafter` subagent under ADR-013 D1 phased authority (the advisory governance drafter). Code R2-reviews + commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). The subagent does not git. This is a **new ADR** — Code is G2-gated from authoring it (the same path ADR-0024 / ADR-0025 used); the independent design lens is the point.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray (the ratified HYBRID principal-model fork + the A1a/A1b phasing). Drafter = the `plan-drafter` subagent. The independent reviewer = Cray at ratification + Code R2 at commit. The residual forks are surfaced as Open Questions, not silently resolved.

---

## Context

### What ADR-0026 is, and why it is exactly the capability ADR-0025 deferred

ADR-0025 shipped the AT-2 managerial layer at boundary **OQ-A=A1** (author + render only). It typed AT-2's governance content (`DoaLadder` / `ScoredRule` / `ComplianceGate` / `SoDConstraint`, all human-author-only and authoritative — `spec.py:293-442`), made `validate_governance_complete` AT-2-aware so the run-gate can no longer be tricked into loading an empty AT-2 (`orchestrator.py:171-209`), and added the scoped prose-lint (`spec.py:578-654`). It explicitly **deferred** the run-time half — the **A2 run path** — recording it as **AC-13-ALT** (`docs/plans/done/0042-at2-managerial-build.md:72`) "gated on a principal-identity-resolution capability that does not exist in the procedures engine today (no `principal`/`identity`/`requester` model in `spec.py`/`orchestrator.py`) … built only when that capability lands, as a separate PLAN."

**ADR-0026 is that capability + that run path.** It does not re-open any ADR-0025 decision — D5/D6 set the *semantics* (principal-identity SoD, not role labels; the four hard guarantees; fail-closed on unresolvable / alias-collapse). ADR-0026 decides the **construct** that makes those semantics runnable: how a HUMAN principal is *resolved* at run time, where the resolved principal travels on the approval call path, and the deterministic per-kind executors that enforce the typed AT-2 content the moment it runs.

### The fact-pack finding that frames the build: the engine has no principal model today

Verified against HEAD. **There is no principal/role-rank model anywhere on the run path:** `RunContext` (`orchestrator.py:78-91`) carries `agent` / `vertical` / `trigger_context` / `goal` — no human principal; `Agent` (`spec.py:562-575`) is the **machine** actor that *runs* a procedure, not the human who *approves*; `RoleId = str` (`spec.py:254`) is a free string with no rank; `Procedure.run_by` (`spec.py:622`) is one `agent_id`. The human go/no-go path is identity-blind end to end: `resolve_gated_step` (`action_step.py:220-313`) takes `decisions: Mapping[action_id, "approve"|"reject"]` and carries **NO "who approved"**; `resume_run` (`persistence.py:65-151`) threads no identity; the audit dict (`action_step.py:211-216`) records `actor=ctx.agent.agent_id` / `actor_kind="engine"` — no human-principal field; `AuditMetadata` (`actions.py:33-38`) likewise has `actor` / `actor_kind` but no human identity.

Consequently the SoD that ADR-0025 shipped is **structural only**: `SoDConstraint` (`spec.py:432-442`) asserts `distinct_steps: frozenset[StepId]` (≥2) and the procedure validator (`spec.py:640-654`) checks only dangling references. As `SoDConstraint`'s own docstring states, "the resolved-PRINCIPAL distinctness (fail-closed on alias-collapse) is the deferred A2 run check (OQ-A=A1; AC-13-ALT)." Two steps can be *structurally* distinct yet resolve to **one human** (small org, on-call, alias chains) — the Alternative-5 failure mode ADR-0025 rejected role-label SoD precisely to prevent. ADR-0026 closes that gap with a resolved-principal check.

### Near-miss ontology data the `Person` object supersedes (not duplicates)

The procurement vertical already gestures at human authority without a resolvable identity entity: `ApprovalTier.approver_role: string` (`procurement_v0.yaml:311-327`), `PurchaseOrder.approver_chain: json` (`:283-285`, a free-form "requester ≠ approver ≠ receiver ≠ AP" chain). These are **role labels and prose chains**, not resolvable principals — exactly what cannot enforce principal-identity SoD. The HYBRID model makes a typed ontology `Person`/`Principal` object the first-class resolvable identity that these near-miss fields *point at* rather than re-encode (mirroring ADR-0025 D2's "point at, do not re-store" discipline).

### "governed ≠ generated" must hold for principals and role bindings too

Principals, the step→role map, and the role→principal binding are the **highest-consequence** governance data in the system — they decide *who is allowed to approve a spend*. Per ADR-0024 D3 they are **H** (human-author-only): structurally absent from any draft type, registered in `GOVERNANCE_FIELDS`, never model-emitted. An LLM may *summarise* a quote; it may never *synthesise* a principal or a binding (LOCKED).

---

## Decision

Build the **principal-identity capability** and use it to **enforce AT-2 governance at RUN time** — implementing the ADR-0025 D5/D6 semantics, never re-deciding them. The build is **phased**; each decision below is tagged **A1a** (the principal construct + the fail-closed principal-SoD run-check) or **A1b** (the deterministic per-kind run-enforcement executors + the audit-to-control side-effect). The author-time STRUCTURAL gate ADR-0025 shipped **STAYS** — A1 is **ADDITIVE at run time, not a replacement**.

### LOCKED (render faithfully; do NOT re-litigate)

1. **ADR-0025 D5/D6 semantics are FIXED.** SoD on resolved **principal identity** (requester_principal ≠ approver_principal), **never** role labels; **fail closed** if either is unresolvable to a distinct human or they collapse to one human. The four D6 hard guarantees (principal-level SoD; audit-to-control as an engine side-effect; render/route/block-only with no ERP I/O; no live LLM in the run path) are requirements, not options. ADR-0026 **implements** these — it never weakens them.
2. **The author-time STRUCTURAL gate STAYS.** `validate_governance_complete` + the `SoDConstraint` ≥2-distinct-steps + dangling-ref checks are unchanged; the principal-SoD run-check is a NEW additive layer at run time.
3. **Render / route / block only.** No ERP / external I/O. ADR-0007 stays the only external write path: run-enforcement routes / suspends / blocks / audits; it does **not** issue the real PO. The ADR-007 approve→execute gate is the only path to an irreversible write, behind the human go/no-go.
4. **`governed ≠ generated`.** Principals + role bindings are HUMAN-authored governance data, never LLM-generated (ADR-0024 D3).
5. **Run = ADR-016 territory.** The A1b executors extend the shipped `StepExecutor` Protocol + orchestrator (`orchestrator.py:94-99`, `:212-224`) — **not a new engine** — and honor D2-A4 (the descriptive facet stays non-authoritative; the resolved principal lives on a typed seam, never in the facet).

### D1 [A1a] — The principal model is HYBRID: a typed ontology `Person`/`Principal` object + a `RunContext.principal` run-context seam (LOCKED FORK — render, do not re-litigate)

A typed ontology **`Person`/`Principal` object** (ADR-0008 grammar) is the **first-class resolvable identity entity** — the durable, human-authored governance record of *who* a principal is. A **`RunContext.principal` seam** (`orchestrator.py:78-91`, a new field) carries the **resolved** principal onto the approval call path at run time. This is the HYBRID: the ontology object is the *resolvable identity*; the run-context field is the *resolution carrier*. SoD is then defined precisely as ADR-0025 D5/D6 require: **two DISTINCT resolved `Person` principals (requester_principal ≠ approver_principal), fail-closed if either is unresolvable or they collapse to one human.** The structural `SoDConstraint` (which two *steps* must differ) stays author-time; the resolved-principal distinctness is the run check this seam makes possible.

### D2 [A1a] — Role→principal binding + step→required-role map (implements OQ-1)

For the run-check to resolve "the requester" and "the approver" to `Person`s, the engine needs (a) which role each SoD-constrained step requires, and (b) which principal holds that role at run time. **Recommendation (surfaced as OQ-1):** the procedure authors a **step→required-role** map (a typed, human-authored field naming the `RoleId` each constrained step demands), and the `Person` object **carries its role(s)** as a typed binding — so resolution is `step → required_role → Person`, and SoD compares the resolved `Person`s. This keeps the binding human-authored (`governed ≠ generated`) and on the ontology object (the durable record), not smuggled into a run-context blob. The exact home is **OQ-1** — Cray adjudicates.

### D3 [A1a] — The `RunContext.principal` plumbing + identity on the approval call (implements OQ-2)

The resolved principal must reach the approval decision point. **Recommendation (surfaced as OQ-2):** add `RunContext.principal: Person | None` **AND** thread an explicit `principal` argument onto `resolve_gated_step` (`action_step.py:220`) — the run-context seam is the *ambient* resolution; the explicit arg on the resolve call is the *load-bearing* identity that names *who actually approved this gate*. The approve decision records that principal (D6 audit). The `trigger_context` blob is rejected as the carrier (it is untyped, non-authoritative, and would re-open a prose-smuggling surface). **OQ-2** — Cray confirms the seam.

### D4 [A1a] — The fail-closed principal-SoD run-check (the core A1a deliverable, implements ADR-0025 D5/D6)

A new run-time check, invoked on the approval path: resolve the requester step's principal and the approver step's principal via the D2 bindings; **the run fails closed** (no "governed" verdict; the gate does not pass) if (i) either step's required role does not resolve to a `Person`, (ii) the two principals are the **same canonical human** (alias-collapse), or (iii) a constrained step has no resolvable principal at all. This is the run-side complement to ADR-0025's author-time structural SoD — together they realize the D5 "SoD is enforced on resolved principal identity, fails closed if either is unresolvable to a distinct human." **Alias-collapse detection is OQ-3** (what makes two principals "the same human" — a canonical `Person` identity key); the fail-closed trigger needs that crisp definition before it can be implemented.

### D5 [A1b] — The deterministic per-kind run-enforcement executors (extend the shipped `StepExecutor` seam)

Once a principal resolves, the typed AT-2 content (`spec.py:293-442`) is enforced deterministically at run, via new executors hooking the shipped `StepExecutor` Protocol + the `_suspends`/`resolve_gated_step` path (LLM only summarises; no generation, ADR-0019 IN-3):

- **`doa_tier`** — computes the required tier from the `Decimal` spend amount + the `DoaLadder` (the total-cover, strictly-monotonic ladder `spec.py:338-369`), then **routes / suspends to the resolved approver** for that tier (the spend→tier ฿ source is **OQ-4**). The `EmergencyWaiverPolicy` strict-escalation (`escalate_to` is a *higher* authority than every relaxed tier — deferred at author-time per the waiver docstring `spec.py:310-316`) is now run-checkable against the resolved role rank.
- **`rule_gate`** — **blocks the PO** on any failed `ComplianceRule` (`blocks_po: Literal[True]`, `spec.py:399-423`); compliance is non-waivable by type.
- **`scored_rule`** — **selects** the supplier per the typed `ScoredRule` (`spec.py:387-396`); the selection logic is human-authored and deterministic.

All three are **render / route / block only** (LOCKED #3) — no ERP I/O, no PO emission; ADR-0007 stays the only write path.

### D6 [A1b] — Audit-to-control as an engine side-effect (each governed decision ties to its control + the resolved principal, implements OQ-5)

Every route / block / select decision emits an audit record naming **the control that governed it AND the resolved principal who owns the decision** — an **engine side-effect, not an authorable step** (it cannot be authored `auto` / omitted, and `autonomy: auto` is forbidden on any step downstream of a gate; ADR-0025 D6 guarantee 2 / red-team Attack 5). This requires the audit surface (`action_step.py:211-216` / `AuditMetadata` `actions.py:33-38`) to gain a **human-principal field**. **Recommendation (surfaced as OQ-5):** keep it **minimal** (one resolved-principal identity key + the governing-control reference) so it does **not** pre-empt the deferred ADR-011 audit-framework — ADR-0026 adds the field the run-enforcement strictly needs, and the full audit model stays ADR-011's to design.

## Consequences

### Positive

- **The deferred ADR-0025 A2 run path becomes buildable.** The capability AC-13-ALT named as "does not exist today" is constructed; the structural SoD ADR-0025 shipped gains its resolved-principal complement; the Box-3 "a human owns every gate" story becomes mechanically true (the DOA tier *routes* to a real human, the compliance gate *blocks*, SoD *holds on real identities*, every decision is *traceable to its control + its owner*).
- **SoD finally enforces what ADR-0025 D5 specified.** Alias-collapse (two structurally-distinct steps, one human) — the exact Alternative-5 failure mode ADR-0025 rejected role-label SoD to avoid — fails closed.
- **The near-miss ontology data is superseded cleanly.** `approver_role: string` / `approver_chain: json` become *pointers at* a typed resolvable `Person`, not the identity itself.
- **Low blast radius.** It extends the shipped engine (ADR-016) + the shipped typed AT-2 content (ADR-0025), introduces no new generation surface, and leaves the ADR-0007 write gate + the ADR-0008 ontology codegen path untouched.

### Negative / risks

- **Running raises blast radius from "wrong document" to "wrong procurement action."** A bug in tier computation, alias-collapse detection, or compliance-blocking mis-routes or fails to block. Mitigated by the LOCKED render/route/block-only boundary + the ADR-0007 human approve→execute gate (the only write path) + the fail-closed default.
- **Alias-collapse is a genuinely hard problem (OQ-3).** A too-loose canonical identity key lets two real humans collapse to one (false SoD pass); a too-strict one fails a legitimate distinct pair closed (availability cost). The crisp definition is a ratification-gating Open Question, not a detail.
- **`Person` from N=1 risks a Rule-of-Three repeat (OQ-6).** Defining a shared/core identity object from one vertical re-runs the ADR-0025 N=1 tension at the ontology layer; a per-vertical `Person` defers it but fragments identity. OQ-6 surfaces the fork.
- **The audit field touches ADR-011's territory.** Mitigated by OQ-5's minimal-field discipline (the run-enforcement's strict need only); the full framework stays ADR-011's.

### Neutral

- This is a capability + ontology + run-invariant decision (hence an ADR + a follow-on PLAN, not ad-hoc code). It **implements** ADR-0025 D5/D6 + decides the deferred AC-13-ALT construct; it does **not** supersede ADR-0025 or ADR-016 — it extends both. ADR merged before the related implementation PLAN (CLAUDE.md §8).

## Open Questions

Surfaced for Cray to adjudicate (options + a recommendation; not silently resolved). The HYBRID principal model (D1) and the A1a/A1b phasing are LOCKED forks — these OQs resolve the *construct details* within them.

- **OQ-1 — where the step→role and role→principal bindings live.** Options: (a) the `Person` object **carries its role(s)** + the procedure authors a **step→required-role** map (resolution = `step → role → Person`); (b) a **separate** step→principal binding table (no role indirection); (c) roles on a separate Role object the `Person` references. **Recommendation: (a)** — keeps the binding human-authored + on the durable ontology object, mirrors the ADR-0025 "point at, do not re-store" discipline, and makes role a first-class typed token rather than a free string. *Cray decision (not a Code judgment): it sets the identity↔role data model shape that the whole A1a run-check builds on, and is hard to unwind once `Person` ships.* **RESOLVED (Cray, s87) — as-recommended: (a).** The `Person` object carries its role(s) and the procedure authors a step→required-role map; resolution path = step → required_role → Person; SoD compares the resolved `Person`s.

- **OQ-2 — which seam supplies the run-time principal at approval.** Options: (a) `RunContext.principal` only; (b) an explicit `principal` arg on `resolve_gated_step` only; (c) `trigger_context` blob. **Recommendation: `RunContext.principal` + an explicit `principal` on the resolve call** — the run-context field is the ambient resolution, the explicit arg is the load-bearing "who approved THIS gate" the audit (D6) records. (c) is rejected (untyped, non-authoritative, re-opens prose-smuggling). *Cray decision: it sets the run-path identity contract `resolve_gated_step` carries forever.* **RESOLVED (Cray, s87) — as-recommended.** `RunContext.principal` (the ambient resolution) **plus** an explicit `principal` arg on `resolve_gated_step` (the load-bearing "who approved THIS gate", which the D6 audit records); the `trigger_context` blob is REJECTED as the carrier.

- **OQ-3 — how alias-collapse is DETECTED (what makes two principals "the same human").** Options: (a) a canonical `Person` primary-key identity match (two role bindings resolving to the same `Person.id` = collapse); (b) an explicit alias set on `Person` (a human declares their alias chain); (c) both — PK match OR a declared alias overlap. **Recommendation: (c)** — PK match is the floor; the declared alias set catches the on-call / second-account case that a bare PK would miss; fail closed when either fires. *Cray decision: the fail-closed trigger's correctness hinges on this definition — too loose lets real SoD violations pass, too strict fails legitimate pairs closed; it is the crux of the D4 run-check.* **RESOLVED (Cray, s87) — as-recommended: (c).** Alias-collapse is detected by a canonical `Person` PK match **OR** a declared alias-set overlap (both) — fail closed when either fires.

- **OQ-4 — the spend→tier ฿ amount SOURCE at run time for `doa_tier` routing (A1b-adjacent).** Options: which entity in the run input set carries the spend (the `PurchaseOrder.total_amount`? a per-line sum? the run trigger payload?), and currency reconciliation (the entity's `currency` enum `procurement_v0.yaml:278-279` vs the `DoaLadder.currency` THB ladder). **Recommendation:** read the spend from the named run-set entity the `doa_tier` step consumes (its `StepInput.from_step` output), as `Decimal`, and **fail closed on a currency mismatch** between the entity and the ladder (never silently convert). *Cray decision: it sets which run-set field is authority-bearing for tier routing; a wrong pick mis-routes a real approval.* **RESOLVED (Cray, s87) — as-recommended.** Read the spend from the named run-set entity the `doa_tier` step consumes (its `StepInput.from_step` output), as `Decimal`; **fail closed on a currency mismatch** between that entity and the `DoaLadder` THB ladder — never silently convert.

- **OQ-5 — the audit `actor`/`actor_kind` gains a human-principal field — minimal vs pre-empting ADR-011.** Options: (a) **minimal** — one resolved-principal identity key + the governing-control reference, ADR-011 designs the rest later; (b) design the **full** human-principal audit model now in ADR-0026. **Recommendation: (a)** — add only what the run-enforcement strictly needs so ADR-0026 does not pre-decide the deferred audit-framework's shape. *Cray decision: it draws the boundary between ADR-0026's run-need and ADR-011's framework — a scope-overlap call, not a Code judgment.* **RESOLVED (Cray, s87) — as-recommended: (a) minimal.** Add only one resolved-principal identity key + the governing-control reference; ADR-0026 does NOT pre-empt the deferred ADR-011 audit-framework's shape.

- **OQ-6 — the `Person` object shape: per-vertical vs shared/core identity (Rule-of-Three).** Options: (a) a **core/shared** `Person` from the start (one identity model across verticals); (b) a **per-vertical** `Person`, extract a shared one at N≥3 (ADR-006 D4 "concrete-first or nothing"). **Recommendation: (b) with an enforceable re-trigger** (mirroring ADR-0025 D7) — a per-vertical `Person` now, a CI flag to re-evaluate the shared/core extraction at N≥2 verticals needing identity, so the Rule-of-Three deferral is self-cancelling rather than a silent comment. *Cray decision: it is the same N=1-vs-Rule-of-Three crux ADR-0025 OQ-1 faced, now at the identity layer — a strategic scope call.* **RESOLVED (Cray, s87) — as-recommended: (b) with an enforceable re-trigger.** A per-vertical `Person` now + an enforceable N≥2 re-evaluation flag for the shared/core extraction (mirrors ADR-0025 D7 — a self-cancelling deferral, not a silent comment).

## Alternatives Considered

### Alternative 1: Enforce SoD on role labels (`requester_role ≠ approver_role`) — no principal identity
- **Pros:** checkable at author-time with no identity resolution; no `Person` object needed.
- **Cons:** roles resolve to humans at run; a single principal holding both roles (small org, on-call, alias chains) passes structurally and fails in fact.
- **Why rejected:** **ADR-0025 Alternative 5 already rejected this** (`0025:179-182`); ADR-0026 implements D5/D6's resolved-principal SoD. Re-deciding it is out of scope (LOCKED #1).

### Alternative 2: Carry the principal in the untyped `trigger_context` blob (no new typed seam)
- **Pros:** no schema change to `RunContext`; "just pass a dict."
- **Cons:** untyped + non-authoritative; an identity in a free-form blob is a prose-smuggling surface and unenforceable by type; the audit could not reliably name "who approved."
- **Why rejected:** D1/D3 put the principal on a typed `RunContext.principal` seam + an explicit resolve-call arg; the principal is a first-class typed `Person`, never a blob field.

### Alternative 3: Amend ADR-0025 rather than write a new ADR-0026
- **Pros:** one document for the whole AT-2 story.
- **Cons:** ADR-0025 is Accepted at boundary OQ-A=A1; the run/principal path is a substantial new capability (a new ontology object + a run-context seam + run executors + an audit field), not an errata.
- **Why rejected:** the dispatch LOCKS this as a NEW ADR citing ADR-0025 D5/D6 (the semantics it implements), ADR-0008 (the Person grammar), ADR-0007 (the write path) — too large for an amendment.

### Alternative 4: Build the A1b run-executors first, retrofit principal identity later
- **Pros:** the deterministic tier/compliance/scored logic is the visible "demo" win.
- **Cons:** D5 (A1b) enforcement without D4 (A1a) principal-SoD would certify an un-owned control as governed — the exact red-team fixture-3 failure (`0025:110-112`); the routing target (the resolved approver) does not exist without the principal construct.
- **Why rejected:** the phasing is LOCKED **A1a before A1b** — the principal construct + fail-closed SoD run-check is the floor the executors stand on.

## References

- ADR-0025 (the AT-2 managerial layer — D5/D6 semantics IMPLEMENTED here, not re-decided; the four hard guarantees `:84-97`; Alternative 5 role-label SoD rejected `:179-182`; D8 red-team fixture 3 `:110-112`) — `docs/adr/0025-at2-managerial-layer.md`
- ADR-0008 (the YAML ontology grammar — the `Person`/`Principal` object home) · ADR-0007 (the `RecommendedAction` approve→execute write gate — the only write path, untouched) · ADR-016 (the procedure engine — the `StepExecutor` seam + orchestrator the A1b executors extend) · ADR-0024 D3 (governed ≠ generated, the G/H/D partition) · ADR-0019 / ADR-010 IN-3 (the determinism invariant) · ADR-006 D4 (Rule of Three — OQ-6) · ADR-011 (the deferred audit-framework — OQ-5) · ADR-009 D1/D2 · ADR-012 D4.3 / ADR-013
- `docs/plans/done/0042-at2-managerial-build.md:72` — **AC-13-ALT**, the deferred A2 run path this ADR builds (the verbatim "gated on a principal-identity-resolution capability that does not exist today")
- `services/engine/procedures/orchestrator.py:78-91` (`RunContext` — no principal: the D1/D3 seam target), `:94-99` (the `StepExecutor` Protocol — the D5 hook), `:171-209` (`validate_governance_complete` — the author-time gate that STAYS), `:212-224` (`_suspends` at `waiting_human`)
- `services/engine/procedures/spec.py:254` (`RoleId = str`, free string — D2), `:293-369` (`DoaTier`/`DoaLadder` — the D5 `doa_tier` content; the resolved-tier escalation deferred to here), `:387-423` (`ScoredRule`/`ComplianceGate`, `blocks_po: Literal[True]` — D5), `:432-442` (`SoDConstraint` = STRUCTURAL distinct-steps — the author-time half D4 complements), `:562-575` (`Agent` = machine actor, not the human principal), `:640-654` (the dangling-ref SoD validator)
- `services/engine/procedures/action_step.py:158-217` (`ActionStepExecutor` + the identity-blind audit dict — D6 gains a human-principal field), `:220-313` (`resolve_gated_step` — carries NO "who approved"; the D3 explicit-principal-arg target)
- `services/engine/procedures/persistence.py:65-151` (`resume_run` — no identity threaded)
- `services/engine/actions.py:33-38` (`AuditMetadata` — `actor`/`actor_kind`, no human-identity field; the D6 / OQ-5 minimal-extension target)
- `verticals/procurement/ontology/procurement_v0.yaml:311-327` (`ApprovalTier.approver_role: string`) + `:283-285` (`PurchaseOrder.approver_chain: json`) — the near-miss role-label data the `Person` object supersedes
- CLAUDE.md §6 (Decision Flow) · §7 (no `Co-Authored-By`) · §8 (AI assistive; data residency; the offline oracle is the gate; render/route/block-only honors the irreversible-write boundary)

## Implementation Notes

This ADR decides the capability + the ontology object + the run invariant; the mechanics are a **follow-on PLAN** (its own dispatch — built only after ratification + the OQ adjudications), which owns, in order:

1. **[A1a] The `Person`/`Principal` ontology object** (ADR-0008 grammar) + the role→principal binding + the step→required-role map (per OQ-1) — human-authored, registered in `GOVERNANCE_FIELDS`, absent from every draft type (ADR-0024 D3 recursive disjointness).
2. **[A1a] The `RunContext.principal` seam + the explicit `principal` arg on `resolve_gated_step`** (per OQ-2) — the typed identity carrier; the `trigger_context` blob is not the carrier.
3. **[A1a] The fail-closed principal-SoD run-check** (D4) with the OQ-3 canonical-identity / alias-collapse definition — the negative regression: two structurally-distinct steps resolving to one `Person` (or an unresolvable role) MUST fail closed and emit no "governed" verdict. The pass/fail read is pre-committed before the test is written.
4. **[A1b] The deterministic per-kind executors** (D5) extending the shipped `StepExecutor` seam: `doa_tier` (tier from the `Decimal` spend + ladder → route/suspend to the resolved approver, spend source per OQ-4), `rule_gate` (block the PO on any failed criterion), `scored_rule` (select per the typed rule; LLM only summarises) — render/route/block-only, no ERP I/O.
5. **[A1b] The audit-to-control engine side-effect** (D6) — the minimal human-principal audit field (per OQ-5) + the `autonomy: auto`-forbidden-downstream-of-a-gate check; every governed decision ties to its control + the resolved principal.
6. **The offline oracle** — the principal-SoD fail-closed fixtures (alias-collapse, unresolvable role) + the tier-routing / compliance-block / scored-select enforcement tests; the LLM is stubbed (deterministic, offline; no live MS-S1; CLAUDE.md §8). A live run, if ever proposed, is host-state → Cray go.

Out of scope (→ later PLANs): the AT-2 **generator** (ADR-0025 D7, Rule-of-Three-deferred until N≥2); making the *classify generator* emit AT-2 (the abstain path stays — PLAN-0041 LOCKED); live ERP / email I/O behind the ADR-0007 write gate; genericizing `Person` to a shared/core object beyond the first vertical (OQ-6, gated on the N≥2 re-trigger); the full ADR-011 audit-framework.

Status flips Proposed → Accepted on Cray ratification; Code applies + commits via a `docs/*` PR (ADR-009 D2; CLAUDE.md §6 Decision Flow). AI-assisted (`plan-drafter` subagent); no `Co-Authored-By` per CLAUDE.md §7.
