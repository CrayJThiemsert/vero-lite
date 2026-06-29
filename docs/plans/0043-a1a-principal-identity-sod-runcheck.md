# PLAN-0043: A1a — principal-identity construct + fail-closed principal-SoD run-check

**Status:** Draft
**Owner:** Claude Code (executes); `plan-drafter` subagent (this draft, uncommitted)
**Created:** 2026-06-29
**Related ADRs:** ADR-0026 (D1–D4 = this PLAN's scope; D5–D6 = OUT, a later A1b PLAN), ADR-0025 (the AT-2 D5/D6 semantics IMPLEMENTED here, never re-decided), ADR-0008 (the `Person` ontology grammar), ADR-016 (the `StepExecutor` + orchestrator seam this extends — not a new engine), ADR-0024 D3 (`governed ≠ generated`), ADR-0007 (the only external write path — untouched), ADR-006 D4 (Rule of Three — OQ-6 per-vertical now), ADR-011 (the deferred audit-framework — A1b/OQ-5, OUT), ADR-009 D1/D2 (drafter authors ungated, only Code commits)

> **Drafting provenance.** Drafted (uncommitted) by the in-harness `plan-drafter` subagent under ADR-013 D1 phased authority. This is a **new PLAN** — Code is G2-gated from authoring it; the independent drafter authors, Code R2-reviews + commits via a `feat/*` PR after Cray ratifies (ADR-009 D2). The subagent does not git.

---

## Goal

Make the AT-2 separation-of-duties that ADR-0025 shipped **structurally** ENFORCED at **run time** on a **resolved human principal**, fail-closed. Today the run path is identity-blind end-to-end (`RunContext` carries no human principal; `resolve_gated_step` carries no "who approved"), so two structurally-distinct steps can resolve to one human and still pass — the Alternative-5 failure ADR-0025 rejected role-label SoD to prevent. A1a builds exactly the floor that closes this gap: (1) a first-class human-authored `Person`/`Principal` ontology object carrying its role(s) plus the procedure's step→required-role map (resolution path `step → required_role → Person`); (2) a `RunContext.principal: Person | None` ambient seam plus a load-bearing explicit `principal` argument threaded onto `resolve_gated_step`; (3) a new **additive** fail-closed principal-SoD run-check that fails closed (emits NO "governed" verdict) when either constrained step's role does not resolve to a `Person`, or the two principals collapse to one canonical human (PK match OR declared alias-set overlap, OQ-3=(c)); and (4) an offline oracle with pre-committed pass/fail reads for the alias-collapse case, the unresolvable-role case, and the happy path (two distinct resolved principals → governed). A1a is the principal construct + the run-check only — the per-kind run executors (`doa_tier`/`rule_gate`/`scored_rule`) and the audit-to-control side-effect are **A1b** (ADR-0026 D5–D6, a later PLAN). The author-time STRUCTURAL gate STAYS unchanged; this is a new run-time layer, never a replacement. No live LLM, no MS-S1: the offline tests ARE the gate (CLAUDE.md §8).

## Acceptance Criteria

Each criterion carries a pre-committed pass/fail read written **before** the corresponding test/code is authored (CLAUDE.md §8 — the offline oracle is the gate). All are offline (no live MS-S1, LLM stubbed).

- [ ] **AC-1 — the `Person`/`Principal` object exists (ADR-0008 grammar, ADR-0026 D1/D2).** PASS: a typed `Person` model exists with a canonical identity key (PK), a typed role binding carrying ≥1 `RoleId`, and a declared alias-set field; every new field has `Field(description=...)`; it loads as an ontology object (per SD-1/SD-2 homes once Cray rules). FAIL: any of {no canonical PK, role(s) untyped as free string with no binding, no alias-set field, a missing `Field(description=...)`}.
- [ ] **AC-2 — the step→required-role map exists and is human-authored (ADR-0026 D2, OQ-1=(a)).** PASS: a typed, human-authored map naming the `RoleId` each SoD-constrained step requires exists on the authored spec (home per SD-1), and resolution `step → required_role → Person` is exercised by a unit test. FAIL: the required-role is carried in untyped free-text / `trigger_context`, or resolution skips the role indirection.
- [ ] **AC-3 — `Person` + bindings are H (governed ≠ generated; ADR-0024 D3 recursive disjointness).** PASS: `Person`, the role binding, the alias-set, and the step→required-role map are registered in `GOVERNANCE_FIELDS` (the appropriate `*_GOVERNANCE_FIELDS` subset) and are **structurally absent / unreachable from every draft type** — extending the existing `test_no_*_reachable_from_any_draft_type` recursive-disjointness pattern (`tests/services/engine/procedures/test_draft_lift_governance.py:251-257`) to cover the new `Person`/binding types, with a positive control proving the authoritative model DOES reach them. FAIL: any draft type (`StepDraft`/`ProcedureDraft`/`AgentDraft`) reaches `Person` or a binding type; or a new field is absent from `GOVERNANCE_FIELDS`.
- [ ] **AC-4 — `RunContext.principal` + the explicit `principal` arg exist (ADR-0026 D3, OQ-2).** PASS: `RunContext` (`orchestrator.py:79`) gains `principal: Person | None = None` (the ambient resolution); `resolve_gated_step` (`action_step.py:220`) gains an explicit `principal` argument (the load-bearing "who approved THIS gate"); both typed `Person`, both mypy-clean; the `trigger_context` blob is NOT used as the carrier. FAIL: the principal is read off `trigger_context`, or either seam is `Any`/dict-typed, or `resolve_gated_step` still carries no caller-supplied principal.
- [ ] **AC-5 — happy path: two distinct resolved principals → "governed".** PASS: a fixture procedure with a `SoDConstraint` over two steps whose required roles resolve to **two distinct `Person`s** (distinct PKs, non-overlapping alias-sets) passes the run-check and the gate proceeds to a "governed" verdict. FAIL: the run-check fails closed on a legitimately distinct pair (false-positive collapse / availability bug).
- [ ] **AC-6 — NEGATIVE REGRESSION (the core deliverable): alias-collapse fails closed, NO governed verdict.** PASS: a fixture where two structurally-distinct steps (passing the author-time `SoDConstraint`) resolve to **one canonical `Person`** — detected by **either** a PK match **or** a declared alias-set overlap (OQ-3=(c)) — causes the run-check to **fail closed**: the gate does NOT pass and **no "governed" verdict is emitted**. FAIL: the run proceeds / emits a governed verdict for a collapsed pair (the Alternative-5 failure mode).
- [ ] **AC-7 — NEGATIVE REGRESSION: an unresolvable role fails closed, NO governed verdict.** PASS: a fixture where a SoD-constrained step's required role does not resolve to any `Person` (or a constrained step has no resolvable principal) causes the run-check to **fail closed** with no governed verdict. FAIL: a missing principal silently passes (defaults to "governed" or skips the check).
- [ ] **AC-8 — the author-time structural gate is UNCHANGED (regression).** PASS: `validate_governance_complete`, the `SoDConstraint` ≥2-distinct-steps invariant, and the `Procedure._validate_separation_of_duties` dangling-ref check behave bit-identically — every shipped vertical's procedures still load + validate unchanged; the existing AT-2 author-time test suite is green with zero edits to its expectations. FAIL: any author-time validation expectation changes, or a previously-loadable procedure now fails author-time (or vice versa).
- [ ] **AC-9 — fail-closed is the DEFAULT, not an opt-in.** PASS: the run-check is invoked unconditionally on the approval path for any procedure carrying a `SoDConstraint`; an unresolved / collapsed principal cannot be bypassed by omitting an argument (a `principal=None` on a SoD-constrained gate fails closed, never "open"). FAIL: the check is skippable by passing `None` or by a procedure-level flag.
- [ ] **AC-10 — the OQ-6 N≥2 re-trigger marker is present (self-cancelling deferral).** PASS: a per-vertical `Person` (procurement) ships now, AND an enforceable re-evaluation marker (a CI-checkable flag / test, mirroring ADR-0025 D7) exists that will fire when a 2nd vertical needs identity — so the shared/core extraction deferral is self-cancelling, not a silent comment. FAIL: `Person` is genericized to a shared/core object now (out of scope), or the deferral is only a prose `# TODO` with no enforcement.
- [ ] **AC-11 — ruff + mypy clean; offline-only.** PASS: `ruff` + `mypy` clean on all new/changed modules; the full offline test suite is green with the LLM stubbed and **no MS-S1 reachability** (no `192.168.1.133` traffic, no live `/api/*` call). FAIL: any lint/type error, or any test requires a live model.

## Out of Scope

- ❌ **A1b — the deterministic per-kind run-enforcement executors (ADR-0026 D5).** `doa_tier` (tier from `Decimal` spend + ladder → route/suspend to the resolved approver), `rule_gate` (block the PO on a failed `ComplianceRule`), `scored_rule` (deterministic supplier selection) — a **later A1b PLAN**. *A1a BEFORE A1b is LOCKED: A1b without A1a would certify an un-owned control as governed — the ADR-0025 D8 red-team fixture-3 failure.*
- ❌ **A1b — the audit-to-control engine side-effect (ADR-0026 D6 / OQ-5).** The minimal human-principal audit field + the `autonomy: auto`-forbidden-downstream-of-a-gate check — a **later A1b PLAN**.
- ❌ **OQ-4 — the spend→tier ฿ source for `doa_tier` routing.** Resolved as-recommended in ADR-0026 but it is A1b-adjacent (consumed by the `doa_tier` executor) → A1b.
- ❌ **OQ-5 — the minimal audit-principal field design** → A1b (it touches ADR-011 territory; A1a does not add the audit field).
- ❌ **The AT-2 generator** (ADR-0025 D7 — Rule-of-Three-deferred until N≥2). The classify generator's AT-2 **abstain** path stays (PLAN-0041 LOCKED).
- ❌ **Genericizing `Person` to a shared/core object beyond the first vertical** (OQ-6=(b)). A1a ships a **per-vertical** `Person` + the N≥2 re-trigger marker (AC-10); the actual core/shared extraction is gated on that flag and is NOT in scope.
- ❌ **Live ERP / email I/O behind the ADR-0007 write gate.** Render / route / block only; ADR-0007 stays the only external write path (LOCKED #3). No PO is issued.
- ❌ **Live MS-S1 / LLM in the run path.** The offline tests are the gate; any live run is host-state → separate Cray go.
- ❌ **Re-deciding any ADR-0025 D5/D6 semantics or any ADR-0026 OQ.** All six OQs are RESOLVED (Cray, s87); this PLAN implements them, never re-litigates.

## Steps

Ordered so each is a small, reviewable, PR-sized unit and the dependency chain is correct: the ontology object + bindings first (nothing resolves without them), the run-context seam next, the run-check third, the offline oracle last. **None is host-state — A1a is fully offline.** None of these Steps is itself G-gated (G2 gates *new PLAN/ADR* authoring, which is this drafter's job, already done); each Step's PR is a normal `feat/*` Code commit.

### Step 1: The `Person`/`Principal` ontology object + role binding (ADR-0026 D1/D2; OQ-1=(a))

Add the typed `Person`/`Principal` model (ADR-0008 grammar) as the first-class resolvable identity: a canonical identity key (PK), a typed role binding carrying ≥1 `RoleId`, and a declared alias-set field (the OQ-3 alias chain). Every field gets `Field(description=...)`. Supersede — point at, do not re-store — the `procurement_v0.yaml` near-miss fields (`ApprovalTier.approver_role` `:325-327`, `PurchaseOrder.approver_chain` `:283-285`): they become pointers at the typed `Person`, not the identity. **Decision shape SD-1/SD-2** (exact YAML home of the step→required-role map; physical home of the alias-set on `Person`) — see *Surfaced decisions*; the recommendation is load-bearing in this step but contingent on Cray.
**Satisfies:** AC-1 (partial), AC-2 (the role binding half).
**Gate/host-state:** neither.

### Step 2: The step→required-role map (ADR-0026 D2; OQ-1=(a))

Add the typed, human-authored **step→required-role** map naming the `RoleId` each SoD-constrained step demands, on the authored spec (home per SD-1 — recommended on `Procedure` alongside `separation_of_duties`, or as a typed field on `SoDConstraint`). Unit-test the full resolution path `step → required_role → Person`. Keep it human-author-only.
**Satisfies:** AC-2 (the map half), AC-1 (completes).
**Gate/host-state:** neither.

### Step 3: Register the new fields as H + recursive draft-disjointness (ADR-0024 D3)

Register `Person`, the role binding, the alias-set, and the step→required-role map in the correct `*_GOVERNANCE_FIELDS` subset(s) in `draft.py` (`:42-69`). Extend the recursive-disjointness test (`test_draft_lift_governance.py:251-257`, the `_reachable_models` / `_AT2_CONTENT_TYPES` pattern) so the new identity/binding types are in the never-reachable set for `StepDraft`/`ProcedureDraft`/`AgentDraft`, with a positive control proving the authoritative spec DOES reach them (so the assertion is non-vacuous). Mirrors the existing AT-2 `governance_content` disjointness exactly.
**Satisfies:** AC-3.
**Gate/host-state:** neither.

### Step 4: The `RunContext.principal` seam + the explicit `principal` arg (ADR-0026 D3; OQ-2)

Add `principal: Person | None = None` to `RunContext` (`orchestrator.py:79`, the frozen dataclass — the ambient resolution). Thread an explicit `principal` argument onto `resolve_gated_step` (`action_step.py:220` — the load-bearing "who approved THIS gate"). Both typed `Person`. The `trigger_context` blob is NOT the carrier (REJECTED, OQ-2). No behaviour change yet — this is the typed plumbing the run-check (Step 5) consumes; existing callers default `principal=None` and the run-check (Step 5) makes `None` on a SoD-constrained gate fail closed.
**Satisfies:** AC-4, AC-9 (the seam half).
**Gate/host-state:** neither.

### Step 5: The fail-closed principal-SoD run-check (ADR-0026 D4; OQ-3=(c)) — the core A1a deliverable

Add the new run-time check, invoked on the approval path for any procedure carrying a `SoDConstraint`: resolve the requester step's principal and the approver step's principal via the Step 1/2 bindings (`step → required_role → Person`); **fail closed** (no "governed" verdict; the gate does not pass) when (i) either constrained step's required role does not resolve to a `Person`, (ii) the two principals are the same canonical human — detected by a `Person` PK match **OR** a declared alias-set overlap (OQ-3=(c)) — or (iii) a constrained step has no resolvable principal. This is the run-side complement to the author-time structural SoD — the author-time gate STAYS (verify via AC-8). Fail-closed is the unconditional default (AC-9), never opt-in.
**Satisfies:** AC-6, AC-7, AC-9 (completes), AC-8 (asserts the author-time gate is untouched).
**Gate/host-state:** neither.

### Step 6: The offline oracle — pre-committed fixtures (CLAUDE.md §8)

Write the deterministic offline fixtures, each with its pass/fail read pre-committed in the AC list ABOVE (this step authors the tests AFTER the reads are fixed): (a) **happy path** — two SoD-constrained steps resolving to two distinct `Person`s → emits "governed" (AC-5); (b) **alias-collapse** — two structurally-distinct steps resolving to one canonical `Person` (one via PK match, one via declared alias-set overlap — cover both OQ-3 triggers) → fails closed, no governed verdict (AC-6); (c) **unresolvable role** — a constrained step's required role resolves to no `Person` → fails closed, no governed verdict (AC-7). LLM stubbed; no MS-S1; assert no live `/api/*` traffic (AC-11). Add the OQ-6 N≥2 re-trigger marker test (AC-10).
**Satisfies:** AC-5, AC-6, AC-7, AC-10, AC-11.
**Gate/host-state:** neither — offline is the gate; a live run, if ever proposed, is host-state → separate Cray go.

## Verification

How we know it worked (all offline, LLM stubbed, no MS-S1):

1. `ruff` + `mypy` clean on every new/changed module (AC-11).
2. The full offline suite green, including: the recursive-disjointness test extended to the new identity/binding types with a non-vacuous positive control (AC-3); the happy-path "governed" assertion (AC-5); the two negative regressions failing closed with **no governed verdict** (AC-6 alias-collapse via both PK-match and alias-overlap; AC-7 unresolvable role); the author-time structural-gate regression unchanged across every shipped vertical (AC-8); the unconditional fail-closed default (AC-9); the OQ-6 N≥2 re-trigger marker (AC-10).
3. Each fixture's expected verdict matches the **pre-committed** read in the AC list (fixed before the test was authored — CLAUDE.md §8).
4. Manual diff-review confirms the `trigger_context` blob is NOT a principal carrier (OQ-2), `Person`/bindings are absent from every draft type (AC-3), and ADR-0007 remains the only external write path (no PO emission anywhere in A1a).

## Surfaced decisions (residual shape forks ADR-0026 leaves open)

ADR-0026 LOCKS the model (HYBRID), the phasing (A1a before A1b), and resolves all six OQs — but two **physical-shape** questions inside OQ-1/OQ-3 are not pinned to a concrete field home. They are surfaced here, not silently chosen; the recommendations are load-bearing in Steps 1–2 but contingent on Cray's ratification at PLAN sign-off.

- **SD-1 — the exact home of the step→required-role map.** OQ-1=(a) fixes *that* the procedure authors a step→required-role map (resolution `step → required_role → Person`) but not *where* the map physically lives. Options: (a) a typed `dict[StepId, RoleId]` field on `Procedure` (sibling to `separation_of_duties`); (b) a typed `required_role: RoleId | None` field on each `SoDConstraint`'s named steps (co-located with the constraint that uses it); (c) a `required_role` field on `Step` itself. **Recommendation: (b)** — co-locating the required role with the `SoDConstraint` that consumes it keeps the run-check's two inputs (the constrained steps + their required roles) in one typed object, mirrors how `governance_content` lives on the `Step` that points at it, and avoids a free-floating procedure-level map that can dangle. **Why this is a Cray decision, not a Code judgment:** it sets the identity↔role authoring shape the whole A1a run-check resolves against, and like the `Person` PK (OQ-1's own framing) it is hard to unwind once authored procedures ship against it.

- **SD-2 — the physical home + type of the declared alias-set on `Person`.** OQ-3=(c) fixes *that* alias-collapse is detected by a canonical PK match **OR** a declared alias-set overlap, but not the alias-set's field shape. Options: (a) a `frozenset[str]` of alias identity keys directly on `Person` (each string a secondary identity the human declares); (b) a separate `PrincipalAlias` link object the `Person` references; (c) a `frozenset[PersonId]` of other `Person` PKs declared as aliases. **Recommendation: (a)** — a flat `frozenset[str]` alias-key set on `Person` is the minimal shape that makes "overlap" a simple set-intersection at run time, needs no second object for N=1, and stays human-authored on the durable identity record. (Re-evaluate (b) if N≥2 identity verticals need a shared alias model — folds into the OQ-6 re-trigger.) **Why this is a Cray decision:** the alias-set is the second of the two OQ-3 collapse triggers; too loose (any overlapping string) risks a false-collapse availability cost, too strict risks a missed real collapse — the same correctness crux OQ-3 flagged, now at the field level.

## Residual gaps / open questions

None. D1–D4 + the resolved OQ-1/OQ-2/OQ-3 (and the OQ-6 deferral marker) are fully renderable from ADR-0026 + the verified seams; the only residual forks are the two physical-shape questions surfaced as SD-1/SD-2 above, which are flagged for Cray rather than silently resolved. OQ-4/OQ-5 are A1b-scoped and correctly excluded.
