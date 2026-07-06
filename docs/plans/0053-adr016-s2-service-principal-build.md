# PLAN-0053: ADR-016 D2+D3 — typed service-principal build (S2, before S1)

**Status:** Phase A COMPLETE (s102); Phase B ACTIVE (s104, 2026-07-06)
**Owner:** Claude Code
**Created:** 2026-07-05
**Related ADRs:** ADR-016 (D2 + D3 Amendment 2026-07-05, **Accepted** — typed
service-principal for non-human triggers), ADR-0026 (principal-SoD run-check),
ADR-0024 D3 (H-only governance machinery), ADR-013 D1/D2 (phased authoring + the
only-Code-commits gate)

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent under ADR-013 D1 phased authoring / ADR-009 D1 interim
> authoring. Outline originator = Cray (session 102 — ratified the ADR-016 S2
> amendment Proposed → Accepted, with OQ-1/2/3 shape picks). Independent reviewer
> = **Code R2** (re-verifies every cited `file:line` against fresh on-disk
> evidence and commits per ADR-009 D2) + **Cray** at PLAN ratification.
> Separation: **INTACT** — the drafter did not originate the direction and does
> not ratify.
>
> **Phase-B-activation amendment (session 104, 2026-07-06).** This edit —
> activating Phase B as the build scope and recording the SD-2/SD-3 ratifications
> — was also **`plan-drafter`-authored**. Cray ratified **SD-2 (omit-when-None)**
> and **SD-3 (list `service_principal_ids` on `Agent`)** on 2026-07-06 / session
> 104; **Code R2-reviews** (re-verifies the newly cited `file:line` — the
> `compute_row_hash` / `verify_chain` anchors and the Phase-A runs.py finding)
> **and commits** per ADR-009 D2. Separation: **INTACT** — the drafter recorded
> Cray's ratifications faithfully, did not originate them, and does not ratify.

---

## Goal

Implement the **actor-model** decided by the now-Accepted ADR-016 D2+D3
service-principal amendment: give every consequential write a **never-null,
typed, non-repudiable actor** and make the human `gated` approval gate
**fail-closed independent of the authn toggle**. Concretely: add a typed
`ServicePrincipal` identity in a **vertical-level `service_principals:` registry**
(OQ-1), carry it on a **separate `RunContext.service_principal` field** leaving
`RunContext.principal` human-only (OQ-2), classify every audit actor by an
**audit-only `actor_kind`** ∈ {`human`, `service`, `engine`} (OQ-3), thread the
actor through **all three** `RunContext` construction sites (fixing the
`resume_run` never-null gap), and — the security headline — make `gated`
gate-resolve **reject a `None`/service principal on ANY gated step regardless of
`api_auth_enabled`** (RF-1, the broad version), while keeping service ids out of
the `Person`/SoD comparison set (RF-3). This is **S2 before S1**: it decides and
builds the actor model *before* a scheduler exists to create service-triggered
runs, so the scheduler cannot ship a null-actor audit gap.

The build is **two phases** (SD-1 **RATIFIED 2026-07-05 / session 102 = SPLIT,
Phase A first**): **Phase A** — the human-governed-approval critical path (RF-1
broad hardening + `actor_kind:"human"` + never-null-on-resume, **no new DB
column**); **Phase B** — the full S1-facing actor model (`ServicePrincipal`
registry type + Agent reference + on-behalf-of chain + the
`actor_service_principal_id` audit migration + RF-3 namespace machinery).
**Phase A ([A] tags) is THIS build / first PR; Phase B ([B] tags) is a named
sequel** (can bundle with S1) — see the *Immediate build scope* note under Steps.

## Acceptance Criteria

Every AC is verifiable by a pytest test OR a grep/read of the named `file:line`.
Phase tags (**[A]** / **[B]**) mark the phasing split proposed in SD-1; if Cray
picks single-build, all ACs are in scope for one PLAN.

- [ ] **AC-1 [A] — RF-1 broad gate hardening (the security headline).**
  `resolve_gated_step` (`action_step.py:408`) rejects a `None` **and** a service
  principal on **ANY** `gated` step — **including a plain gated step with NO SoD
  constraint** — and does so **independent of `api_auth_enabled`**. Verified by a
  pytest that resolves a plain non-SoD gated step with `principal=None` and
  `settings.api_auth_enabled=False` and asserts the resolve **raises** (no
  handler fires, no `output_set` rewrite, run left `waiting_human`). This is
  **new, broader** than today: currently only SoD-constrained steps fail closed
  (`_enforce_principal_sod` at `action_step.py:319-341` is a no-op on a non-SoD
  step), and authn-off (`auth.py:71-72`) makes the plain approver check inert.
- [ ] **AC-2 [A] — SP-1 requester-never-approver preserved verbatim in intent.**
  A `service_principal` value can never satisfy the approver role at a `gated`
  gate: the RF-1 rejection in AC-1 fires whether the principal is `None` **or** a
  service identity. Verified by a pytest that attempts to resolve a gated step
  passing a service actor as the approver and asserts rejection (a service actor
  reaching the approver seam is the SP-1 collapse `gated`→`auto`, blocked).
- [ ] **AC-3 [A] — never-null actor on the human resolve path, incl. resume.**
  `resume_run` (`persistence.py:238-298`) threads a `principal` (and, Phase B, a
  `service_principal`) into its `RunContext` (`persistence.py:293-298`, which
  today passes **neither** → defaults `None`); the `run_started` /
  gate-resolution audit rows for a human path carry `actor_person_id` (never
  `None` when a principal is resolvable). Verified by a pytest that resumes a
  gated run and asserts the resolved audit row's actor is the human's
  `person_id`, not `None`.
- [ ] **AC-4 [A] — `actor_kind:"human"` on the human resolve / run-start audit
  (OQ-3 audit-only).** The audit metadata for a human-driven resolve / run-start
  records `actor_kind:"human"` (extending the existing `"engine"` convention at
  `action_step.py:290-296`); the principal **type** carries no redundant `kind`
  discriminator. Verified by a pytest asserting the audit dict's `actor_kind` and
  by a grep that `Person` (`spec.py:638-657`) gains no `kind` field.
- [ ] **AC-5 [B] — typed `ServicePrincipal`, distinct from `Person` (SP-2 /
  RF-3).** A `ServicePrincipal` type exists in `spec.py` mirroring `Person`'s
  shape (stable id + declared scope) but is a **distinct** Pydantic model with
  `model_config = ConfigDict(extra="forbid")`; it is **never** substitutable for
  `Person` in the SoD comparison set. Verified by a pytest asserting
  `ServicePrincipal` is not a `Person` subtype and a grep that
  `check_principal_sod` / `_enforce_principal_sod` (`action_step.py:299-341`)
  compare only `person_id`s — no service id reaches them (RF-3).
- [ ] **AC-6 [B] — vertical-level `service_principals:` registry (OQ-1).**
  `VerticalProcedures` (`spec.py:778-837`) gains
  `service_principals: list[ServicePrincipal]` (default empty), parsed by
  `parse_procedures` via `doc.get("service_principals") or []`
  (`spec.py:851-875`), with a `@model_validator` enforcing unique
  `service_principal_id`s (mirroring `_validate_principals` at
  `spec.py:800-817`). Verified by a pytest loading a spec with a duplicate
  service id (raises) and one with a valid registry (loads; absent key → empty,
  every existing vertical unchanged).
- [ ] **AC-7 [B] — Agent references a service-principal by id (SP-2 / SP-6).** An
  `Agent` (`spec.py:660-673`) may reference a registry `ServicePrincipal` by id;
  a `@model_validator` on `VerticalProcedures` (mirroring the `run_by`
  cross-ref at `spec.py:829-835`) rejects a dangling reference. Least-privilege
  is unchanged: the service actor's blast radius is the **running Agent's**
  `allowed.{action_handlers, object_types}` (`spec.py:606-616`) at runtime — **no
  new scope primitive** (SP-6). Verified by a pytest with a dangling Agent→service
  reference (raises) and a valid one (loads).
- [ ] **AC-8 [B] — separate `RunContext.service_principal` field (OQ-2).**
  `RunContext` (`orchestrator.py:81-102`) gains
  `service_principal: ServicePrincipal | None = None` **beside** the human-only
  `principal`; it is threaded through **all three** construction sites —
  `orchestrator.py:565-571`, `persistence.py:143-149`, and
  `persistence.py:293-298` (`resume_run`). Verified by a grep asserting all three
  sites pass the field and a pytest constructing a `RunContext` with a service
  actor + `principal=None`.
- [ ] **AC-9 [B] — `actor_kind:"service"` + on-behalf-of chain (SP-3 / SP-5).**
  A service-triggered path records `actor_kind:"service"` AND records **both**
  the service id (who fired) and the owning human (who scheduled/owns it, if any)
  in `trigger_context` (SP-5). Verified by a pytest asserting a service run's
  audit `actor_kind` and the presence of both lineage keys. (Exercised end-to-end
  only once S1 creates service-triggered runs — this AC verifies the wiring is
  present and unit-testable via a synthetic service `RunContext`.)
- [ ] **AC-10 [B] — never-null service actor (SP-4).** The `run_started`
  actor-coalesce (`persistence.py:130-140`) resolves the declared service id when
  a run is service-triggered, **never** `None`; the new
  `actor_service_principal_id` column (AC-11) carries it. Verified by a pytest
  that a service-triggered `run_procedure_persisted` writes a non-null service
  actor.
- [ ] **AC-11 [B] — `audit_log` migration + hash-canonical change.** `AuditLog`
  (`audit_log.py:55-79`) gains a nullable `actor_service_principal_id: str | None`
  column via an Alembic migration; `compute_row_hash` (`audit_log.py:82-111`)
  includes the new field in the canonical sorted-key JSON so the tamper-evident
  hash-chain stays byte-recomputable. Verified by a pytest asserting a row with a
  service actor recomputes its `row_hash` identically and the prev/row-hash chain
  verifies, plus a read of the migration file. (See Step 8 + SD-2.)
- [ ] **AC-12 [A+B] — SP-7 H-governed fields, never model-emitted.** The new
  human-authored fields register in the draft governance machinery
  (`draft.py:42-88`): `service_principals` joins the identity H-set (guarded by
  the recursive TYPE-disjointness test the way `PRINCIPAL_GOVERNANCE_FIELDS`
  guards `Person`/`PrincipalAlias` — `draft.py:73-80`, since `ServicePrincipal`
  is a `VerticalProcedures`-level record, not a draft surface); any new
  `Agent`-level reference field joins `AGENT_GOVERNANCE_FIELDS`
  (`draft.py:70`). Verified by the existing draft-disjointness test extended to
  assert `ServicePrincipal` is unreachable from any draft type.
- [ ] **AC-13 [A+B] — `extra="forbid"` + full-suite green.** Every new/edited
  Pydantic model keeps `model_config = ConfigDict(extra="forbid")`; the full
  `pytest` suite (binding the disposable `<db>_test`, skipping without Postgres —
  mirroring `tests/api/test_monitor_runs.py`) is green; `ruff` + `mypy` clean.
  Verified by CI + a grep for `extra="forbid"` on `ServicePrincipal`.

## Out of Scope

- ❌ **The S1 scheduler** that CREATES service-triggered runs (its own later
  ADR/PLAN — **S2 before S1**). This PLAN does **not** lift the `validate_runnable`
  hard-block on non-`manual` triggers (`orchestrator.py:138-142`); S1 does.
- ❌ **The Control-leg v1 governed-approval UI** (the human-approver hero surface
  — its own PLAN). Phase A here is the *engine* critical path that UI depends on,
  not the UI itself.
- ❌ **API-key transport / scheduler auth material** on the service identity
  (SP-6 — the identity is a *declared identity only*; the API-key transport in
  `auth.py` is the scheduler's concern, kept separate).
- ❌ **Any change to `Person` / SoD comparison semantics, the `auto`/`gated`
  model, `autonomy_ceiling`, or the handler/object_type allowlists' existing
  semantics** (the service-principal *reuses* them; RF-2 — no autonomy elevation).
- ❌ **`docs/STATUS.md` reconcile** (a follow-on `docs(status):` PR after merge).

## Steps

Steps are ordered; each cites the `file:line` it touches (re-confirm on disk at
implementation — the fact-pack is verified grounding, not a substitute for R2).
**[A]** / **[B]** tags mark the SD-1 phasing split.

> **Immediate build scope (SD-1 RATIFIED 2026-07-05 / session 102 = SPLIT).**
> **Phase A — the [A]-tagged Steps (1–3) + the [A+B] Steps' Phase-A portion
> (9–10) — is THIS build / the first PR.** It ships RF-1 broad gate hardening,
> `actor_kind:"human"`, and never-null-on-resume with **no new DB column**.
> **The [B]-tagged Steps (4–8) are Phase B — a named sequel** (can bundle with
> S1); they stay documented here as the full Phase-B scope, not deleted, but are
> **out of THIS PR's scope**. Phase B is drafted/ratified separately (SD-2 and
> SD-3 are deferred to it — see Surfaced Decisions).
>
> **➡ Phase B ACTIVATED for build (session 104, 2026-07-06).** Phase A shipped
> in session 102. **Phase B is now the ACTIVE build scope: the [B]-tagged Steps
> (4–8) + the [A+B] Steps (9–10).** Its two deferred decisions are now
> **RATIFIED** below — **SD-2 = omit-when-None** (add `actor_service_principal_id`
> to `compute_row_hash`'s canonical dict only when non-None) and **SD-3 = a list
> `service_principal_ids: list[str]` on `Agent`**. Step 8's SD-2 pointer is
> updated to follow the ratified omit-when-None rule.
>
> **On-disk Phase-A finding (verified session 104).** Phase A shipped the RF-1
> human-approver guard at the **HTTP endpoint** (`services/api/routers/runs.py:337-344`
> — `auth.person_id is None → 403`), **not** at the library. The library
> chokepoint `resolve_gated_step` (`services/engine/procedures/action_step.py:408+`)
> still has **no broad `None`/service rejection** — it only runs the SoD check,
> which is inert on a non-SoD step (docstring `action_step.py:443-444`). The code
> comment at `runs.py:334-336` explicitly states the library-level rejection is
> **Phase B**. So **Phase B Step 1 (library portion) + Step 6 (service arm)
> genuinely land the library guard — it is still open.** Classification:
> `superseded by new info` (the [A] tag anticipated the library location; Phase A
> implemented it at HTTP; the library guard is Phase B per the shipped code
> comment) — **not an error**.

### Step 1 [A]: RF-1 broad gate-resolve hardening (the security headline)

Add a fail-closed guard at the top of `resolve_gated_step`
(`action_step.py:408-496`, before the SoD check at `:490-496`) that **rejects a
`None` principal AND a service principal on ANY `gated` step**, regardless of
`settings.api_auth_enabled` (`auth.py:71-72`). Today the only fail-closed is
`_enforce_principal_sod` (`action_step.py:319-341`), which is a **no-op on a
non-SoD step** — so a plain gated step + authn-off resolves silently with no
approver. The new guard raises a typed error (`ProcedureError` or a dedicated
`GateApproverError`) before any approve/execute. Preserve SP-1 verbatim in
intent: *a service-principal is a requester/actor ONLY, NEVER an approver.*
Touches: `action_step.py:408-496`. (This is the load-bearing Phase-A item and can
land **independently of any new type or column** — a `None` check needs no
`ServicePrincipal`; the service-actor arm of the check is completed in Step 6.)

### Step 2 [A]: `actor_kind:"human"` on the human resolve / run-start audit (OQ-3)

Extend the audit-metadata convention (`action_step.py:290-296`, currently
hardcoding `actor_kind:"engine"`) so a human-driven resolve / run-start records
`actor_kind:"human"`. Audit-only source of truth per OQ-3 — do **not** add a
`kind` field to `Person` (`spec.py:638-657`). Touches: `action_step.py:290-296`,
`persistence.py:130-140` (the `run_started` append).

### Step 3 [A]: never-null actor on the resume path — fix `resume_run` (SP-4, human)

`resume_run`'s `RunContext` (`persistence.py:293-298`) passes **neither**
`principal` nor `service_principal` today → both default `None`, so a resumed
step's audit actor is null. Add a `principal: Person | None = None` parameter to
`resume_run` (sig `persistence.py:238-246`) and thread it into that `RunContext`
(and, Phase B, `service_principal`). Update the HTTP resume call-site to pass the
resolved `auth.person`. Touches: `persistence.py:238-246`, `persistence.py:293-298`,
+ the resume router call-site (mirror the resolve call-site `runs.py:313-362`
passing `principal=auth.person`).

### Step 4 [B]: the `ServicePrincipal` type (SP-2 / RF-3)

Add a `ServicePrincipal` Pydantic model to `spec.py` (near `Person`,
`spec.py:638-657`), mirroring `Person`'s shape (stable
`service_principal_id` + declared scope) but a **DISTINCT** type with
`model_config = ConfigDict(extra="forbid")`. It must be **unreachable** from the
SoD comparison set — `check_principal_sod` / `_enforce_principal_sod`
(`action_step.py:299-341`) keep comparing `person_id`s only (RF-3). Do **not**
give it a `roles`/approver field that could tempt an approver-seam reuse (SP-1).
Touches: `spec.py` (new type near `:638`).

### Step 5 [B]: vertical-level `service_principals:` registry + Agent reference (OQ-1 / SP-6)

On `VerticalProcedures` (`spec.py:778-798`) add
`service_principals: list[ServicePrincipal] = Field(default_factory=list, ...)`;
in `parse_procedures` (`spec.py:851-875`) parse `doc.get("service_principals") or
[]` (mirror the `principals` parse at `:873`). Add a `@model_validator`
enforcing unique `service_principal_id`s (mirror `_validate_principals`,
`spec.py:800-817`) and a cross-ref that any Agent→service reference resolves
(mirror the `run_by` cross-ref, `spec.py:829-835`). Decide the Agent-reference
field shape (SD-3). Least-privilege is unchanged (SP-6): the blast radius is the
**running** Agent's `allowed.{action_handlers, object_types}`
(`spec.py:606-616`) — the registry adds indirection, **no scope hole**. Touches:
`spec.py:778-875`.

### Step 6 [B]: `RunContext.service_principal` + thread all three sites (OQ-2 / SP-4)

Add `service_principal: ServicePrincipal | None = None` to `RunContext`
(`orchestrator.py:81-102`), **beside** the human-only `principal` (do NOT widen
`principal` to a union — RF-3 by construction). Thread it through **all three**
construction sites: `orchestrator.py:565-571`, `persistence.py:143-149`,
`persistence.py:293-298`. Complete the RF-1 service-actor arm from Step 1 (a
service value at the approver seam is rejected). Replace the `None` fallback in
the `run_started` coalesce (`persistence.py:130-140`) so a service-triggered run
resolves the declared service id, never `None` (SP-4). Touches:
`orchestrator.py:81-102,565-571`, `persistence.py:130-140,143-149,293-298`.

### Step 7 [B]: `actor_kind:"service"` + on-behalf-of chain (SP-3 / SP-5)

Extend the audit metadata (`action_step.py:290-296`, and the persistence
audit path) so a service-triggered path records `actor_kind:"service"` AND
records **both** the service id (who fired) and the owning human (who
scheduled/owns it, if any) in `trigger_context` (SP-5 on-behalf-of lineage).
Touches: `action_step.py:290-296`, `persistence.py:130-140` (+ `trigger_context`
shape).

### Step 8 [B]: `audit_log` migration + hash-canonical change (call-out — see SD-2)

Add a **nullable** `actor_service_principal_id: str | None` column to `AuditLog`
(`audit_log.py:55-79`) via a new **Alembic migration** (append-only; the
`audit_log` mutation-block trigger at `:50-51` means no UPDATE/DELETE — the
migration only ADDs a nullable column, existing rows unaffected). **Add the new
field to `compute_row_hash`'s canonical JSON** (`audit_log.py:82-111`, in the
sorted-key dict at `:96-110`) so the sha256 hash-chain stays byte-recomputable.
**Load-bearing implication (SD-2 RATIFIED = omit-when-None):**
`actor_service_principal_id` is added to `compute_row_hash`'s canonical dict
**only when non-None** (omit-when-None, SD-2 RATIFIED); a `None` value ⇒ the key
is absent, so every pre-migration row recomputes **byte-identically** and the
chain never needs an epoch. `verify_chain` (`audit_log.py:163-192`) passes the
row's `actor_service_principal_id` through unchanged. This is a real,
load-bearing build item, not a rubber-stamp. Touches: `audit_log.py:55-79,82-111`
+ a new `alembic/versions/*.py`.

### Step 9 [A+B]: SP-7 — register the H-governed fields (never model-emitted)

`service_principals` is a `VerticalProcedures`-level human-identity record (like
`principals`), so it is guarded by the **recursive TYPE-disjointness** test the
way `PRINCIPAL_GOVERNANCE_FIELDS` guards `Person`/`PrincipalAlias`
(`draft.py:73-80`) — assert `ServicePrincipal` is unreachable from any draft
type. Any **Agent-level** reference field added in Step 5 joins
`AGENT_GOVERNANCE_FIELDS` (`draft.py:70`). No service-principal field is ever
model-emitted (ADR-0024 D3). Touches: `draft.py:42-88` + the draft-disjointness
test.

### Step 10 [A+B]: tests (see Test plan)

Add the pytest coverage enumerated in the Test plan. Bind the disposable
`<db>_test`, skip without Postgres (mirror `tests/api/test_monitor_runs.py:1-35`
+ `tests/db_support.create_test_engine`). Ensure `ruff` + `mypy` clean and the
full suite green (AC-13).

## Surfaced Decisions

### SD-1 (HEADLINE) — Split Phase A / Phase B, or single build?

**Question.** Build S2 as **two PRs/phases** (Phase A: RF-1 broad hardening +
`actor_kind:"human"` + never-null-on-resume — **no new DB column**; Phase B: the
`ServicePrincipal` registry + Agent reference + on-behalf-of + the
`actor_service_principal_id` migration + RF-3 machinery), or **one build**?

**Code recommendation: SPLIT — ship Phase A first.** Phase A is the **critical
path** to Cray's stated downstream driver, **Control-leg v1 "governed approval
from the UI"** (a HUMAN approver hero: named person + SoD + audit). Phase A is
fully exercisable **today** (a human resolves a gate — no scheduler needed),
needs **no DB migration** (a human actor uses the existing `actor_person_id`
column), and closes the sharpest real security gap now (RF-1: a plain gated step
+ authn-off silently resolves with no approver — AC-1). Phase B's machinery
(`ServicePrincipal` type, on-behalf-of chain, `actor_service_principal_id`
column) is fully exercised only once **S1** creates service-triggered runs, so it
can follow Phase A (or bundle with S1) without blocking the human hero.

**Alternatives considered.** (a) **Single build** — clean single Accepted-ADR
closure, but couples the human-hero critical path to the DB migration + hash
change (Step 8), delaying the UI-facing win behind machinery that has no live
exerciser until S1. (b) **Phase B first** — inverts the S2-before-S1 rationale's
own priority (the *human* gate is the shipping hero; the service actor is
forward-looking).

**Why this is Cray's call, not a Code judgment.** It sets delivery sequencing
against Cray's roadmap (Control-leg B timing) and decides whether the
Accepted-ADR closes in one PR or two — a scope/sequencing decision, and the ADR
explicitly left the *build* shape open. Recommendation is load-bearing in the
phase tags above but contingent on Cray's ratification.

> **✅ RATIFIED (Cray, 2026-07-05 / session 102) = SPLIT — Phase A first.** Ship
> Phase A (the [A]-tagged ACs/Steps: RF-1 broad gate hardening,
> `actor_kind:"human"`, never-null-on-resume — **no new DB column**) as the
> immediate build scope / first PR. Phase B (the [B]-tagged items:
> `ServicePrincipal` registry type + Agent reference + on-behalf-of + the
> `actor_service_principal_id` audit migration + RF-3 machinery) follows as a
> **sequel** (can bundle with S1). Matches the Code recommendation above.

### SD-2 — `audit_log` hash-canonical change: null-serialization vs chain-epoch boundary

**Question.** Adding `actor_service_principal_id` to `compute_row_hash`'s
canonical JSON (`audit_log.py:96-110`) changes the hash inputs. Existing rows
were hashed **without** the field. How is the boundary handled so the
tamper-evident chain stays verifiable across the migration?

**Code recommendation: null-serialization-identical (Option a).** Add the field
as `"actor_service_principal_id": None` in the canonical dict for pre-migration
semantics — but this only round-trips cleanly if the verifier for **old rows**
also injects the key as `null`. If old rows must recompute **byte-identically to
their stored hash** (they were hashed without the key), a naive add **breaks the
chain**. Safer: treat the migration as a **chain-epoch boundary** (Option b) —
the new column starts hashing at the first post-migration row, and the verifier
knows the epoch. **Recommendation: Option b (epoch boundary)** — it never
retro-changes a stored hash, and the append-only mutation-block trigger
(`audit_log.py:50-51`) already forbids rewriting old rows.

**Alternatives.** (a) null-key-in-canonical (simpler code, risks a silent chain
break if old-row recompute isn't handled); (b) epoch boundary (safe, needs a
verifier-side epoch marker); (c) defer the column entirely to Phase B and land
Phase A first (folds into SD-1 = split).

**Why Cray's call.** It touches the **tamper-evident audit integrity guarantee**
(the DPO/PDPA framing) — the highest-consequence invariant in the amendment. A
wrong choice silently voids `verify_chain`. If SD-1 = split, this decision lands
**with Phase B** and Phase A ships without touching the hash canonical at all
(flagged in Step 8).

> **✅ RATIFIED (Cray, 2026-07-06 / session 104) = omit-when-None.** Include
> `actor_service_principal_id` in `compute_row_hash`'s canonical dict **ONLY when
> non-None** (None ⇒ the key is omitted from the canonical JSON).
>
> This **SUPERSEDES** the plan's original Code-recommended default (Option b, the
> chain-epoch boundary). Classification: `superseded by new info` (evolution — the
> epoch rec was sound when drafted, before reading the code) — **not an error**.
>
> **Why it changed.** A close read of the REAL `compute_row_hash`
> (`services/db/audit_log.py:82-111`) surfaced that for an **additive nullable
> column**, omit-when-None is strictly better than epoch: it is **DB-independent**
> (the epoch would be an `audit_id` boundary that DIFFERS per database → needs
> per-DB persisted epoch state → new fragility in `verify_chain`, the one
> component that must never be wrong), it is a **1-line** conditional, and it
> preserves tamper-evidence while old rows recompute **byte-identically** (the
> protobuf absent-optional-field property).
>
> **Proven on-disk before ratification.** A prototype importing the ACTUAL
> production `compute_row_hash` as v1 verified the full chain across a simulated
> migration boundary (0 breaks), caught every tamper case (service-id flip,
> hide-actor→None, old-row payload), and confirmed
> `omit(service=None) == prod v1 hash` byte-for-byte — **7/7 checks**.
>
> **Escalation note.** Epoch / schema-versioning remains the documented answer IF
> a future **NON-additive** audit change ever arrives (reformat/rename an existing
> field, change the hash algorithm) — adopt it **lazily at that boundary**, do
> **not** pre-pay its complexity now.

### SD-3 — Agent→service-principal reference field shape

**Question.** How does an `Agent` (`spec.py:660-673`) reference a registry
`ServicePrincipal` by id — a single `service_principal_id: str | None`, a list
`service_principal_ids: list[str]`, or a reference carried on the `procedure`
(`run_by` already binds the Agent)?

**Code recommendation: a list `service_principal_ids: list[str]` on `Agent`
(default empty)**, cross-ref-validated on `VerticalProcedures` (mirror the
`run_by` check, `spec.py:829-835`). A list matches OQ-1's "share one
service-principal across multiple Agents" rationale symmetrically (an Agent may
also front several service identities) and keeps the blast-radius home on the
Agent (SP-6). It joins `AGENT_GOVERNANCE_FIELDS` (`draft.py:70`, Step 9).

**Alternatives.** (a) single id (simpler, but a 1:1 Agent↔service cap contradicts
the registry's share rationale); (b) reference on the trigger/`schedule`
(rejected by OQ-1 as the least-scoped placement); (c) list on Agent
(recommended).

**Why Cray's call.** It fixes the spec grammar's public shape (a YAML-authoring
surface) and the H-governance field home (SP-7) — an authoring-contract decision
the ADR left to the build. Lands in Phase B.

> **✅ RATIFIED (Cray, 2026-07-06 / session 104) = list `service_principal_ids:
> list[str]` on `Agent`** (default empty), cross-ref-validated on
> `VerticalProcedures` like `run_by`. **As-recommended** (the plan's Code
> default above).

## Test plan

All DB tests bind the disposable `<db>_test` via `tests/db_support.create_test_engine`
and **skip gracefully without Postgres**, mirroring `tests/api/test_monitor_runs.py:1-35`.
Pure-Pydantic/spec tests need no DB.

**Phase A (no new column):**
- **T-1 (AC-1, RF-1 — the load-bearing test).** A **plain gated step with NO SoD
  constraint** + `settings.api_auth_enabled=False` + `principal=None` → the
  `resolve_gated_step` call **RAISES**; assert no handler ran, `output_set`
  unchanged, run still `waiting_human`. This is the explicit RF-1 broad-rejection
  test the fact-pack requires (today this path resolves silently).
- **T-2 (AC-2, SP-1).** Resolving a gated step passing a **service** actor as the
  approver → RAISES (a service can never be an approver).
- **T-3 (AC-3, SP-4 human/resume).** Resume a `waiting_human` gated run with a
  resolved human `principal` → the resolved audit row's `actor_person_id` is the
  human's id, **not** `None` (regression test for the `resume_run` null gap).
- **T-4 (AC-4, OQ-3).** A human resolve/run-start audit dict carries
  `actor_kind:"human"`; grep asserts `Person` has no `kind` field.

**Phase B:**
- **T-5 (AC-5/AC-6/AC-7, SP-2/OQ-1/RF-3).** Load a spec with a valid
  `service_principals:` registry (loads; absent key → empty). Duplicate
  `service_principal_id` → RAISES. Dangling Agent→service reference → RAISES.
  Assert `ServicePrincipal` is **not** a `Person` subtype and no service id
  reaches `check_principal_sod` (RF-3).
- **T-6 (AC-8, OQ-2).** Construct a `RunContext` with a `service_principal` +
  `principal=None`; grep-assert all three construction sites
  (`orchestrator.py:565-571`, `persistence.py:143-149,293-298`) pass the field.
- **T-7 (AC-9/AC-10, SP-3/SP-4/SP-5).** A synthetic service `RunContext` →
  `actor_kind:"service"`, a non-null service actor, and BOTH the service id and
  the owning-human key present in `trigger_context`.
- **T-8 (AC-11, hash-chain).** A row with a service actor recomputes its
  `row_hash` identically; the prev/row-hash chain across the migration boundary
  verifies (exercises SD-2's chosen boundary handling). Read-assert the Alembic
  migration adds a **nullable** column.

**Cross-phase:**
- **T-9 (AC-12, SP-7).** The draft-disjointness test asserts `ServicePrincipal`
  is unreachable from any draft type (mirrors the `Person`/`PrincipalAlias`
  guard).
- **T-10 (AC-13).** Grep `extra="forbid"` on `ServicePrincipal`; full `pytest`
  suite green, `ruff` + `mypy` clean.

## Sequels (named, OUT of scope here)

- **S1 — the scheduler** that CREATES service-triggered runs (lifts the
  `validate_runnable` non-`manual` block, `orchestrator.py:138-142`) — its own
  ADR/PLAN, gated on this build. **S2 before S1.**
- **Control-leg v1 governed-approval UI** — the human-approver hero surface that
  Phase A unblocks — its own PLAN.
- **`docs(status):` reconcile** — a follow-on tiny PR after this merges.

## Verification

Each AC maps to a T-n pytest and/or a `file:line` grep/read above. The RF-1 broad
rejection (AC-1 / T-1) is the load-bearing security gate and MUST have the
explicit "plain gated step + authn off rejects a None principal at resolve" test.
The `audit_log` migration + hash-canonical change (Step 8 / AC-11 / SD-2) is
verified by both a chain-recompute pytest and a read of the migration file. Code
R2 re-confirms every cited `file:line` against fresh on-disk evidence before
commit (ADR-009 D2).
