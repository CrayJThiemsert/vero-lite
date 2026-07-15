# PLAN-0075: AT-2 authority enforcement at the run gate — the acting approver must hold the ladder-resolved tier role (doa_tier + severity_tier)

**Status:** Proposed — Cray ratifies the PLAN itself at PR. **SD-1 / SD-2 / SD-4 / SD-6 RATIFIED (Cray, session 132)**; **SD-3 = keep NARROW, CONFIRMED (Cray, s132, after a 3-specialist review — with the architect's binding tracked-follow-on condition)**; **SD-5 = ADJUDICATED SPLIT (Cray, s132): defer the bulk of F-PIN; FOLD IN the supply_chain derivation-provenance half now (AC-13, provenance-only)**.
**Owner:** Claude Code (execution) · Cray (ratification at PR)
**Created:** 2026-07-15
**Related ADRs:** ADR-0026 (D4 — **amended 2026-07-15 per ratified SD-4**: the 4th fail-closed condition + the `RoleId`-rank stance + the every-verdict fan-out rule + the gate-time actor-named audit tie + the derivation residual-risk note — §Amendment (2026-07-15) in the ADR; D5's "routes/suspends to the resolved approver" promise this PLAN completes; LOCKED #2/#3/#5), ADR-0025 (D6 hard guarantees + D8 red-team oracle discipline), ADR-0031 (D2 moat tripwires; D3 gate-seam row — NOT built here, tracked follow-on per SD-3; D3 row-1 — the proper form of the F-PIN follow-on per SD-5), ADR-016 (RF-1 fail-closed-regardless-of-authn; SP-1 gated→auto hazard precedent), ADR-007 (approve→execute write gate, untouched)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code, session 132; the follow-on itself was
> ratified by Cray at the PLAN-0074 session-131 adversarial review).
> Independent review: Code (R2) at PR; ratification: Cray. Author≠reviewer
> separation: **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.
> All code claims verified against a pinned snapshot of `origin/main`
> @ ff84d9a (2026-07-15); anchors outside the snapshot are attributed to
> Code's R2 verification where so marked.
> **Updated 2026-07-15 (same session, post-R2):** SD-1/2/4/6 ratifications
> recorded (Cray, s132); Corrections 1 (fan-out cardinality = 1 today) and
> 2 (procurement has TWO authority surfaces) applied; the ADR-0026 D4
> amendment drafted as this PLAN's Deliverable A.
> **Updated 2026-07-15 (same session, post-specialist-review):** SD-3
> confirmed narrow with a durably-tracked follow-on; SD-5 split — the
> supply_chain derivation-provenance half folded in (AC-13 / Step 7), the
> rest deferred on an honest threat-tier rationale; C1 residual-risk
> sentence added to the ADR-0026 D4(iv) amendment; C2/C3 corrections
> applied to the F-PIN notes below.

## Goal

Close the **AT-2 authority-enforcement gap** across the whole authorisation
axis — `doa_tier` on **BOTH procurement surfaces** (the YAML vertical AND
the hero_demo in-code procedure — §Surface inventory) **and**
`severity_tier` (supply_chain, PLAN-0074): an authority ladder resolves +
**audits** which tier/approver a spend or severity routes to
(`governance_step.py:189-299`), but **no gate path enforces that the acting
approver holds the resolved tier role** — the live SoD run-check tests only
the procedure's *generic* step→role map (`principal_sod.py:139`, sole role
test `required not in person.roles` at `:176`; it never reads the ladder).
A lower-tier approver can resolve a gate the ladder routed to the top tier,
and the persisted audit then **names an authority who never acted**
(`governance_step.py:231-238`, `:285-292`). This PLAN (1) builds the
enforcement as a **pure, offline-testable function** called from
`resolve_gated_step`, (2) requires an authority-content step to be
`autonomy: gated` at load (F3), (3) reconciles the two `GovernedDecision`
emissions so the audit names who acted, (4) corrects all seven over-claim
sites including the two persisted runtime trace strings, (5) fixes the
committed test that blesses the bug, (6) ships an ADR-0025 D8-analog
offline red-team oracle covering all three authority surfaces, and (7)
folds in the ratified SD-5 provenance half: supply_chain's derivation
constants are hashed into the run's governance snapshot (AC-13,
provenance-only). Framing: this **completes an existing guarantee** —
ADR-0025 D6 (`0025:90`) and ADR-0026 D5 (`0026:71`) already promise the
executor "routes / **suspends to the resolved approver** for that tier" —
it does not invent new policy (no accepted ADR/PLAN ever promised
tier-role *enforcement*; verified clean negative, fact-pack §2). The
governance decision itself is now recorded in the **ADR-0026 Amendment
(2026-07-15)** — this PLAN implements it.

## Context — LOCKED / RATIFIED vs open

**LOCKED direction (Cray, session-131 review; do not re-litigate):**

1. **This follow-on exists.** Cray ratified it out of the PLAN-0074 s131
   adversarial review; the s131 commit already stamped the gap into
   `severity_tier.py:114-125` ("⚠ ENFORCEMENT SCOPE … a lower-tier
   approver can today resolve a gate this ladder routed to a higher
   tier … tracked for the gate-seam PLAN").
2. **Hard constraints (fact-pack §6; a violating design must be
   rejected):** render / route / **block** only — the ADR-007
   approve→execute gate stays the ONLY write path; a new check may only
   BLOCK (ADR-0025 D6 g3 `0025:94`, ADR-0026 LOCKED #3 `0026:47`).
   **Additive, never replacing** `check_principal_sod` (ADR-0026 LOCKED #2
   `0026:46`). Extend the shipped orchestrator, **not a new engine**
   (ADR-0025 LOCKED #5 `0025:51`, ADR-0026 LOCKED #5 `0026:49`). **No LLM**
   in the governed path (ADR-0025 D6 g4 `0025:95`). **Moat tripwires**
   (ADR-0031 D2 `0031:118-125`) bind. **Fail closed regardless of authn**
   (ADR-016 RF-1).
3. **The offline oracle is the gate (CLAUDE.md §8).** `resolve_gated_step`
   is DB-bound (loads the run, appends audit, commits) — a regression test
   written only at that level SKIPS when Postgres is down. The enforcement
   core is therefore a **pure function** (no DB/LLM/network), mirroring
   `check_principal_sod`'s own design (`principal_sod.py:18-19` states it
   verbatim). This purity is a **hard requirement**, not a style choice.

**RATIFIED (Cray, session 132):** **SD-1 = (a)** exact-match +
rank-as-DATA (`verdict.required_role ∈ principal.roles`; NO engine rank
primitive over `RoleId`; downward approval, where wanted, is authored as
cumulative role sets in YAML). **SD-2 = (a) source + (i) rule** (read the
persisted verdicts off the gated step's `audit["doa_tier"|"severity_tier"]`;
the acting principal must satisfy **EVERY** verdict on the step).
**SD-4 = amend ADR-0026 D4** (done — the amendment is drafted, Deliverable
A of this session; Code commits + merges it before the implementation PR).
**SD-6 = (a)** (the principal-naming authority `GovernedDecision` moves to
gate time, naming the ACTOR; run-time keeps the trace-level routing
record; no OQ-5 envelope change).

**ADJUDICATED after the 3-specialist review (Cray, session 132):**
**SD-3 = keep NARROW, confirmed** — with the architect's binding
condition: the ADR-0031 D3 gate-plugin seam is a **durably-tracked
follow-on** (filed stub PLAN + STATUS entry), never a bare out-of-scope
bullet (the repo's rot precedent: ADR-0031 OQ-4 records that the ADR-0025
D7 CI marker was promised and long unbuilt). **SD-5 = split** — the bulk
of F-PIN is deferred on the **threat-tier** rationale (see SD-5; the
"different axis" framing was rejected by both reviewers), and the cheap
supply_chain **derivation-provenance** half is folded in NOW (AC-13,
Step 7 — PROVENANCE-ONLY; it does not close F-PIN).

## The reproduced gap (verified end-to-end against ff84d9a — not hypothetical)

The chain: (1) `GovernanceActionExecutor._doa_tier` / `._severity_tier`
(`governance_step.py:189-245`, `:247-299`) resolve the ladder at the
**action** step, write the verdict to the step trace + `audit`, and
delegate to the base — the verdict is **never carried forward as a
constraint**. (2) The `gated` action proposes; the orchestrator suspends
at `waiting_human` (`orchestrator.py:611-623` `_suspends`, keyed on
`Autonomy.GATED`). (3) The human approves via `resolve_gated_step`
(`action_step.py:433`); its identity checks are the RF-1 approver guard
(`:515-519`), the governance pin (`:525-526`), and
`_enforce_sod_with_refusal_audit` → `check_principal_sod` (`:532-534`).
(4) `check_principal_sod` tests only `sod.required_roles.get(step_id)` —
the **generic** map (`approve: approver`) — at `principal_sod.py:139`/
`:176`. **Decisive negative (re-verified by this drafter):** the only
readers of the verdict's `resolved_approver_id` / `required_role` are the
verdict constructors (`doa_tier.py:133-140`, `severity_tier.py:144-151`),
their `to_audit()` projections, the hero render
(`hero_demo/governance_audit.py:147`, `:162`), and tests —
`principal_sod.py` and `action_step.py` contain **zero** hits.

⚠ The name collision at the heart of the bug: `SoDConstraint.required_roles`
(`spec.py:840`) is the **generic, enforced** map;
`DoaTierVerdict.required_role` / `SeverityTierVerdict.required_role` is the
**ladder-resolved, un-enforced** tier role.

### Surface inventory — THREE AT-2 authority surfaces, not two

Enforcement and regression coverage must name their surface; each AC below
does. *(Correction 2, session 132 — the first draft conflated S1 and S2.)*

- **S1 — procurement, the YAML vertical.** `load_procedures("procurement")`
  → `emergency_sourcing_round` (`verticals/procurement/procedures.yaml`):
  DoaLadder floors `0 / 50000 / 500000 / 2000000`, Thai tier roles
  (หน.จัดซื้อ / ผจก.จัดซื้อ / ผจก.โรงงาน / ผอ., `:233-236`), principals
  `req-planner, appr-buyer, appr-pm, appr-plant, appr-director`
  (`:62-77`). ฿288,000 → `[50000, 500000)` → **ผจก.จัดซื้อ / `appr-pm`**.
  This is the surface `tests/services/db/test_procurement_sod_gate.py`
  drives (`_procurement()` at `:357-361`).
- **S2 — procurement, the hero_demo in-code procedure.**
  `hero_demo/procedure.py::fastenal_doa_ladder()` (`:36-46`, R2-verified —
  outside the drafting snapshot): a **DIFFERENT ladder**, floors
  `0 / 15001 / 200001 / 1000001`, roles `SUPERVISOR / MANAGER / CONTROLLER
  / VP_OPERATIONS`, principals loaded from CSV (`:74`, R2-verified).
  ฿288,000 → `[200001, 1000001)` → **`CONTROLLER` / `appr-controller`**
  (`test_hero_run.py:73-75`, `test_hero_governance_audit.py:51,57` —
  R2-verified). The demo path — a junior approving HERE is the most
  visible failure.
- **S3 — supply_chain, the YAML vertical.** SeverityLadder
  (`verticals/supply_chain/procedures.yaml:290-304`), principals
  (`:61-76`).

All three carry the SAME gap: S2's offline audit builder passes the same
generic map `required_roles={"intake": "requester", "approve":
"approver"}` to `check_principal_sod`
(`hero_demo/governance_audit.py:53-56`, snapshot-verified), and no surface
reads the ladder verdict at the gate. The enforcement core (pure, reads
the persisted verdicts — surface-agnostic) covers all three by
construction; the per-surface work is regression coverage + audit-builder
alignment.

**Exploit 1 — procurement S1 (the shipped YAML vertical).** Principals
(`verticals/procurement/procedures.yaml:62-77`): `appr-buyer:[approver,
"หน.จัดซื้อ"]`, `appr-pm:[approver, "ผจก.จัดซื้อ"]`, `appr-plant:[approver,
"ผจก.โรงงาน"]`, `appr-director:[approver, "ผอ."]` — roles NON-cumulative.
DoaLadder floors (`:233-236`): 0→หน.จัดซื้อ, 50k→ผจก.จัดซื้อ,
500k→ผจก.โรงงาน, 2M→ผอ. SoD (`:293-297`): `{intake: requester, approve:
approver}`. The hero-scenario spend ฿288,000, evaluated on THIS ladder,
routes to ผจก.จัดซื้อ (`appr-pm`) — but **`appr-buyer`** (ladder authority
`[0, 50000)` only) holds the generic `approver`, is distinct from
`req-planner`, and resolves the ฿288k gate **unblocked** — and equally a
฿2M+ ผอ.-tier PO. *(On S2, the same ฿288,000 resolves on the Fastenal
ladder to `CONTROLLER` / `appr-controller` — a junior CSV principal
holding only the generic role exploits it identically.)*

**Exploit 2 — supply_chain S3.** Principals
(`verticals/supply_chain/procedures.yaml:61-76`); SeverityLadder
(`:290-304`): negligible→จนท.ประกันคุณภาพ … critical→ผอ.ฝ่ายคุณภาพ.
**`appr-qa`** resolves a `critical` disposition the ladder routed to
`appr-qdir`.

**The audit is affirmatively misleading (worse than incomplete).** At
**run** time, *before any human acts*, the executor emits
`GovernedDecision(control_ref=ControlRef(kind="doa_tier", id=tier),
principal_id=v.resolved_approver_id)` — who the ladder **routed to**, not
who acted (`governance_step.py:231-238`; `severity_tier` analog
`:285-292`). When a lower-tier approver resolves the gate, the run still
carries a `doa_tier` control tie naming `appr-pm`, while
`_record_governed_decision` (`action_step.py:392-403`) separately records
the actual actor under the `sod` control kind. **The persisted audit
names an authority who never acted.** For a governance product this
violates even the ADR-0025 D6 conservative fallback ("a read-only
artifact is strictly safer than a run path that certifies an un-owned
control as owned", `0025:97`) — the current state *certifies*.

**F3 — one word from a self-authorising authority gate.** No validator
requires `Autonomy.GATED` on a step carrying `doa_tier`/`severity_tier`
content: `_is_filled`'s docstring states "`autonomy` is always present
(defaulted `gated` = safe), so it never blocks a run"
(`draft.py:302-304`); the agent ceiling (`orchestrator.py:201-205`) is
`auto` for procurement (`procedures.yaml:39`) and for supply_chain's
`cold_chain_qa_agent` (`:43`); and the existing
`_check_no_auto_downstream_of_gate` (`orchestrator.py:648-682`, invoked
from `validate_governance_complete:608`) guards only auto steps **after**
a gate — it never requires the authority step **itself** to be gated.
*(Refinement vs the dispatch fact-pack: "the only autonomy guard is the
agent ceiling" understated this near-miss guard — but the F3 conclusion
stands, and the fix is that guard's natural sibling.)* An `auto`
authority step never reaches `waiting_human` → `resolve_gated_step` never
runs → the SoD run-check never fires (it lives only there,
`action_step.py:532`); the auto branch approves + executes **inline**
(`action_step.py:292-302`). ADR-016 SP-1 already names this hazard class
("silently converts `gated`→`auto`"). Softener, stated honestly: the
governance pin DOES cover `autonomy` (`governance_pin.py:57`), so a
mid-flight flip fails an **in-flight** run at resume — but not a new run.

**The committed test that blesses the bug — plus a harness finding this
drafter adds to the fact-pack.**
`tests/services/db/test_procurement_sod_gate.py::test_procurement_distinct_principals_proceeds`
(`:405-430`, surface S1) drives the real hero procedure and resolves the
฿288,000 gate with **`appr-director`** (top tier — NOT the ladder-resolved
`appr-pm`), asserting pass + the audit tie `principal_id:
"appr-director"`. Under exact-match it fails. **Additionally (new,
verified):** that test binds the **plain** `ActionStepExecutor`
(`:372-377`) — not `GovernanceActionExecutor` — so its approve step's
audit carries **no `doa_tier` verdicts at all**. Any enforcement that
reads the persisted verdicts and is *inert on absence* would let this
test keep passing with `appr-director` — a silent bypass shape. The
enforcement must therefore **fail closed when the gated step declares
authority content but no verdict is persisted** (AC-3), and the test must
be re-harnessed on the governance executors (AC-8).

**Fan-out cardinality today = 1 (Correction 1, verified).** The hero run
seeds a SINGLE-element intake (`hero_demo/run.py:347` — `seed = [await
_intake_seed(adapter)]`, snapshot-verified), and `test_hero_run.py:72`
destructures `[doa] = hero["doa_tier"]` (R2-verified), requiring exactly
one verdict. So **no shipped run currently carries a mixed-tier verdict
set** — the SD-2(i) every-verdict rule is safe to adopt now, and the
mixed-tier deadlock (under non-cumulative roles, satisfiable by no single
principal) is **LATENT, not live**. Consequence: this PLAN does **not**
author cumulative role sets into the shipped YAML (Code's recommendation,
veto-open — keeps the diff small); rank-as-data remains the *documented
supported mechanism* for granting downward approval, exercised when a
multi-requisition run or a design partner needs it.

## Design sketch (per the RATIFIED SD-1(a) / SD-2(a)+(i) / SD-6(a) — Cray, s132)

- **New pure module** `services/engine/procedures/tier_authority.py`
  (name at Code's discretion), mirroring `principal_sod.py`: a
  `check_tier_authority(...)` pure function returning a **structured
  verdict** (`TierAuthorityVerdict{governed, violations}` with typed
  violation kinds — e.g. `TIER_ROLE_MISMATCH`, `VERDICT_MISSING`,
  `UNKNOWN_PRINCIPAL`), never a bare bool. `check_principal_sod` stays
  **byte-identical** (LOCKED #2).
- **Inputs (ratified SD-2(a)):** the acting `principal: Person`, the gated
  step's declared `governance_content` (DoaLadder | SeverityLadder |
  other), and the step's **persisted** authority verdicts —
  `target.audit["doa_tier" | "severity_tier"]`, the `to_audit()` list the
  executor wrote at run time (`governance_step.py:242`, `:296`; each
  entry carries `required_role` + `resolved_approver_id`; persisted JSONB
  on the engine-side `StepResult.audit`,
  `services/engine/procedures/runs.py:110`, R2-verified). Two fail-closed
  triggers: (i) verdicts present → enforce the ratified SD-1(a) predicate
  against **every** verdict (SD-2 rule (i)); (ii) authority content
  declared on the step but NO verdicts persisted → refuse (the
  plain-executor bypass above).
- **Call site:** `resolve_gated_step`, **after**
  `_enforce_sod_with_refusal_audit` (`action_step.py:532-534`) and
  **before** the Phase-1 decide/commit (`:544` / the `:580` commit) — SoD
  stays the primary check (additive layering, LOCKED #2; and the ordering
  preserves `test_procurement_requester_cannot_self_approve`'s
  `ROLE_MISMATCH` assertion, `:433-454`). A refusal is durably audited
  before the exception propagates (mirror `_enforce_sod_with_refusal_audit`
  `:406-430`, `action="gate_refused"`); the HTTP surface maps it to 403
  like `PrincipalSoDError` (`runs.py:387-396`).
- **F3 load check:** a new `_check_authority_step_gated` sibling of
  `_check_no_auto_downstream_of_gate`, invoked from
  `validate_governance_complete` (`orchestrator.py:608`): a step whose
  `governance_content` is a `DoaLadder` / `SeverityLadder` must be an
  ACTION step whose effective autonomy is `Autonomy.GATED` — a load-time,
  fail-closed refusal (all shipped surfaces already comply; the check
  makes the one-word flip unrepresentable-at-load).
- **Audit reconciliation (ratified SD-6(a)):** the run-time
  principal-naming `GovernedDecision` emission moves to **gate time** —
  emitted beside the `sod` tie in/next to `_record_governed_decision`
  after the tier-authority check passes, naming the **acting** principal
  (who now provably holds the tier role). The run-time reasoning-trace
  routing record ("resolved to 'appr-pm'") **stays** — it is honest as
  routing. The hero render keeps working (it reads the `audit["doa_tier"]`
  verdicts, not `governed_decision`: `hero_demo/run.py:365-369`,
  `governance_audit.py:140-165`; the offline builder is updated to match
  the new emission semantics, and its generic-map SoD projection at
  `governance_audit.py:53-56` gains the same tier-authority alignment).
- **Derivation provenance (ratified SD-5 fold-in — supply_chain only,
  PROVENANCE-ONLY):** the supply_chain derivation constants
  (`_DOSE_LADDER`, `cold_chain_assess.py:71-75`, an already-hashable
  `tuple[tuple[Decimal, ExcursionSeverity], ...]` — **plus the separate
  `_TOP_SEVERITY` top-band constant at `:76-77`**, which a
  ladder-tuple-only hash would silently miss) are hashed
  **automatically** (canonical serialisation of the constants, never a
  manual version string a deploy can forget to bump) into the run's
  governance snapshot. Honest wiring cost: `build_governance_snapshot`
  (`governance_pin.py:42`) takes ONLY the `Procedure` and has no reach to
  vertical code — the fold-in threads an **optional derivation-hash
  parameter** from run-start snapshot capture through the resolve-side
  re-check (`assert_governance_pin`, `action_step.py:526`). A small
  signature/threading change — a real coordination point, not free.

## Acceptance Criteria

Each AC names its surface(s): **S1** = procurement YAML, **S2** =
procurement hero_demo in-code, **S3** = supply_chain YAML, **ALL** =
surface-agnostic engine work.

- [ ] **AC-1 (ALL) — pure core.** New module with `check_tier_authority` +
  structured verdict; **no DB / LLM / network imports** (pass/fail read:
  the module imports only stdlib + `spec`/verdict types, and its tests run
  with Postgres down); `principal_sod.py` byte-identical (`git diff`
  empty on it).
- [ ] **AC-2 (ALL; asserted on S1 + S3 roles) — the ratified predicate
  (SD-1 = (a), Cray s132).** For every persisted verdict on the gated
  step: `verdict.required_role ∈ principal.roles`, else refuse — NO
  engine rank primitive; the multi-entity rule is the ratified SD-2(i):
  the principal must satisfy **every** verdict. Documented posture:
  over-strict, never unsafe (refuses a senior; never admits a junior;
  downward approval, where wanted, is authored as cumulative role sets in
  YAML — not authored in this PLAN, per Correction 1). Pass/fail read:
  pure tests — `appr-buyer` refused at ฿288k (S1 roles); `appr-qa`
  refused at `critical` (S3 roles); the ladder-resolved approver passes;
  `appr-director` is ALSO refused at ฿288k (the ratified exact-match
  behavior, asserted as such).
- [ ] **AC-3 (ALL) — missing-verdict fail-closed.** A gated step whose
  declared `governance_content` is an authority ladder but whose
  persisted audit carries no `doa_tier`/`severity_tier` verdict list is
  **refused** (violation kind `VERDICT_MISSING`) — now also ADR-backed as
  D4 condition (iv)'s second clause (ADR-0026 Amendment 2026-07-15).
  Pass/fail read: a pure test with content-declared + empty audit
  refuses; the re-harnessed AC-8 test would fail without governance
  executors.
- [ ] **AC-4 (ALL) — gate wiring.** `resolve_gated_step` invokes the check
  after SoD, before the Phase-1 commit; refusal is durably audited
  (`gate_refused` payload naming the violation) BEFORE the typed error
  propagates; HTTP → 403 with the structured verdict (JSON-safe — heed
  the PLAN-0072 frozenset lesson at `runs.py:389-395`). Non-skippability
  matches the SoD posture: enforcement keys off the persisted audit
  (works even procedure-less), and the declared-content direction fires
  whenever the caller supplies `procedure` (the HTTP surface always does,
  `runs.py:377-386`).
- [ ] **AC-5 (ALL) — F3.** `validate_governance_complete` refuses a
  procedure whose authority-content step is not a GATED action. Negative
  tests: flipping procurement `approve` / supply_chain disposition
  `approve` to `auto` (fixture copies, not the shipped YAML) fails load;
  all shipped surfaces load unchanged. Cross-cite ADR-0025 D6 g2 /
  ADR-016 SP-1.
- [ ] **AC-6 (ALL) — audit reconciliation (RATIFIED SD-6 = (a), Cray
  s132).** After this PLAN, a persisted `governed_decision` under kind
  `doa_tier`/`severity_tier` names ONLY a principal who actually acted.
  Pass/fail read: a gate-resolution test asserts the tie names the actor;
  a suspended (unresolved) run carries NO principal-naming authority tie;
  grep confirms the run-time emission (`governance_step.py:231-238`,
  `:285-292`) no longer emits `principal_id` at run time.
- [ ] **AC-7 (ALL) — the seven over-claim sites corrected.** Per-site
  checklist (the reviewer walks EACH anchor against the diff — a single
  grep is NOT the acceptance): (1) `governance_step.py:221` + (2) `:279`
  — persisted trace strings, reworded to name the real mechanism (the
  tier-authority run-check refuses at the gate); (3) `doa_tier.py:66-68`
  verdict-class docstring; (4) `doa_tier.py:113-114` resolver docstring;
  (5) `severity_tier.py:67-69` verdict-class docstring (the site s131
  missed — ⚠ its phrase WRAPS a line break, evading any line-based
  grep); (6) `test_doa_tier.py:136-138` + (7)
  `test_severity_tier.py:140-141` test comments (both live under
  `tests/`, invisible to a `services/`-scoped oracle). Plus the
  `severity_tier.py:114-125` ⚠ scope note updated from "known gap" to
  "closed by PLAN-0075". Pass/fail read (two-part, BOTH must hold):
  (i) a **multiline** grep (`rg -U`, or the harness Grep tool with
  `multiline: true`) over **`services/` AND `tests/`** for the
  three-phrasing disjunction
  `SoD\s+run-check('s)?\s+(fails\s+closed\s+at\s+the\s+gate|job\s+at\s+the\s+gate|fail-closed\s+surface\s+at\s+the\s+gate)`
  returns zero hits (`\s` spans the line-wrap; the disjunction is
  scoped to the FALSE-claim phrasings so `principal_sod.py`'s
  legitimate "principal-SoD run-check" prose does not false-positive);
  (ii) the seven-site checklist is confirmed one-by-one at R2.
  Rationale for the two-part read: the sites use THREE distinct
  phrasings ("fails closed at the gate" / "job at the gate" /
  "fail-closed surface at the gate") and one wraps a line break — a
  single-phrase, single-tree, line-based grep reports green with 5 of 7
  sites uncorrected, the exact failure mode this PLAN exists to
  prevent.
- [ ] **AC-8 (S1 — the YAML vertical ONLY) — the blessing test fixed.**
  `test_procurement_distinct_principals_proceeds` is re-harnessed on the
  governance executors (pattern `hero_demo/run.py:275-290` — which
  requires threading a quote-bearing seed so `scored_rule` stamps the
  spend; the raw synthetic failure events carry no `candidate_quotes`)
  and resolves with the **ladder-resolved `appr-pm`** (S1's ladder —
  NOT S2's `appr-controller`; the surfaces must not be conflated again);
  companion negatives: `appr-buyer` AND `appr-director` refused on the
  same run shape (ratified exact-match). No test remains that blesses a
  non-resolved-tier approver.
- [ ] **AC-9 (ALL) — the red-team oracle (ADR-0025 D8 analog, offline).**
  Pure fixtures, Postgres-free: (1) junior-refused for `doa_tier` AND
  `severity_tier`; (2) missing-verdict refused (AC-3); (3) an undeclared/
  unknown acting principal refused; (4) the **mixed-tier fan-out fixture —
  a guard against a LATENT regression, not a live bug** (Correction 1:
  shipped fan-out cardinality is 1 today, `hero_demo/run.py:347` +
  `test_hero_run.py:72`; the fixture proves a future N>1 run under
  non-cumulative roles fails closed — satisfiable by no principal —
  rather than silently admitting anyone); (5) F3 hollow case — an `auto`
  authority step is refused at load. Each asserts the structured
  violation kind, not just "raised".
- [ ] **AC-10 (S2 — the hero_demo in-code surface) — the demo path is
  enforced, regression-tested, and stays green.** *(Corrected: the first
  draft wrongly said the hero demo resolves with `appr-pm` — S2 has its
  OWN ladder and resolves ฿288,000 to `CONTROLLER` / `appr-controller`,
  `test_hero_run.py:73-75` R2-verified.)* (a) The offline hero
  governance-moment flow (stubbed client) still suspends with the
  `doa_tier` audit (`hero_demo/run.py:359-369`) and resolves with
  **`appr-controller`** — green. (b) A NEW S2 regression: a junior CSV
  principal holding only the generic `approver` role is **refused** at
  the hero gate (the most visible failure surface — the demo). (c) The
  offline audit builder (`governance_audit.py`) matches the new
  gate-time SD-6(a) emission semantics, and its generic-map projection
  (`:53-56`) reflects the tier-authority check alongside SoD. (d) The
  render contract is intact (it reads the `audit["doa_tier"]` verdicts).
- [ ] **AC-11 (ALL) — suite hygiene.** Whole suite deterministic + offline
  (no LLM, no MS-S1, DB tests keep their existing skip behavior); ruff +
  mypy clean; no change to the ADR-007 envelope or `GovernedDecision`'s
  minimal shape (control ref + principal key, ADR-0026 OQ-5) beyond
  emission timing (unconditional — SD-6(a) is ratified); no new StepKind,
  no new engine.
- [ ] **AC-12 (governance) — the ADR amendment lands first (RATIFIED SD-4,
  Cray s132).** The ADR-0026 D4 Amendment (2026-07-15) — the 4th
  fail-closed condition, the `RoleId`-rank stance, the every-verdict
  fan-out rule, the actor-named audit tie, and the C1 derivation
  residual-risk note — is **drafted (Deliverable A, this session)** and
  is Code-committed + **merged before the implementation PR** (CLAUDE.md
  §8 Code Quality). Status stays Accepted (in-place amendment per the
  ADR-0022 / ADR-016 precedent).
- [ ] **AC-13 (S3 — supply_chain ONLY) — derivation provenance in the run
  pin (PROVENANCE-ONLY; the ratified SD-5 fold-in, Cray s132).** The
  supply_chain derivation constants — `_DOSE_LADDER`
  (`cold_chain_assess.py:71-75`, an already-hashable
  `tuple[tuple[Decimal, ExcursionSeverity], ...]`) **AND the separate
  `_TOP_SEVERITY` top-band constant (`:76-77`; drafter finding: a
  ladder-tuple-only hash would leave the unbounded critical band
  un-covered)** — are hashed **automatically** (canonical serialisation
  of the constants themselves, NEVER a manual `derivation_version`
  string a deploy can forget to bump) into the supply_chain run's
  governance snapshot, threaded per the design sketch (an optional
  derivation-hash parameter from run-start capture through
  `assert_governance_pin`, `action_step.py:526` — a small but real
  signature/threading coordination point; `build_governance_snapshot`
  at `governance_pin.py:42` has no reach to vertical code today).
  **Semantics, stated exactly:** this buys (i) **mid-flight
  tamper-evidence** (a run-start↔resolve derivation mismatch fails
  closed at the pin) and (ii) **audit provenance** (the record of which
  derivation governed THIS run); it does **NOT** close the new-run
  re-routing threat (a new run started on already-changed code pins the
  changed derivation without complaint) — **F-PIN stays open** (SD-5
  tracked follow-on). Stored-run compatibility ≈ zero real blast radius
  (snapshot-field precedents: PLAN-0048 `reads`, PLAN-0061 `join`; only
  energy has committed stored runs and energy carries no authority
  ladder). Procurement is EXCLUDED (its ฿ derivation is imperative
  `unit_price × qty` math with no clean datum — follow-on). Pass/fail
  read: offline tests prove (a) the supply_chain snapshot carries a
  deterministic derivation hash (stable across processes); (b) a mutated
  `_DOSE_LADDER` OR `_TOP_SEVERITY` between run-start and resolve fails
  closed at the pin; (c) procurement + energy + aquaculture snapshots
  are byte-identical to before (no cross-vertical bleed); (d) a
  self-cancelling marker documents the F-PIN residual (procurement
  un-pinned), tripping when a procurement derivation hash lands and
  pointing at the follow-on PLAN.

## Out of Scope

- ❌ **Authoring cumulative role sets into the shipped YAML** (Correction
  1 — fan-out cardinality is 1 today, so nothing requires it; rank-as-data
  stays the documented mechanism, exercised when a real multi-requisition
  run or design partner needs it). Code's recommendation, veto-open.
- ❌ **F-PIN's remainder — TRACKED FOLLOW-ON, not a bare deferral**
  (ratified SD-5 split). What remains open after the AC-13 fold-in: the
  **new-run re-routing threat** (a deploy that changes the derivation
  before a run starts is pinned as normal) and **procurement's imperative
  ฿ derivation** (`unit_price × qty` — no clean datum to hash). Honest
  deferral rationale (C3 — the "different axis" framing is retracted;
  both SD-5 reviewers rejected it): the derivation gap is the **same
  authority axis one layer down**, but a **lower threat tier** — it
  requires code access + a PR + a deploy (a code-access/deploy-hygiene
  concern), whereas the bug this PLAN closes is exploitable by an
  ordinary operational user (a junior approver, no code change).
  Tracking (tripwire-backed, per the governance reviewer — the rot
  precedent is ADR-0031 OQ-4's long-unbuilt ADR-0025 D7 marker): a
  **filed stub PLAN + a STATUS Active-TODO entry** (both — Code files at
  commit time), plus the AC-13(d) self-cancelling marker. The follow-on's
  **proper form is "declare the derivation as data," not "hash more
  code"**: `cold_chain_assess.py:68-70` states verbatim that
  `_DOSE_LADDER` "IS THE DATUM A TRANSFORM GRAMMAR WOULD DECLARE
  (ADR-0031 D3 row-1)" — once promoted to declared governance data, the
  EXISTING pin covers it for free (`governance_pin.py:59-63`,
  `governance_content`), and a hand-rolled procurement code-hash would be
  throwaway work.
- ❌ **F-FACTORY / the ADR-0031 D3 gate-plugin seam — TRACKED FOLLOW-ON,
  not a bare deferral** (SD-3 confirmed narrow, Cray s132; the
  architect's binding condition). The trigger HAS fired (2nd AT-2
  signature, PLAN-0074 merged — D4.1 satisfied), but D4.1 does not compel
  a build and D4.2 gives each seam its own PLAN. Tracking: the same
  **filed stub PLAN + STATUS entry** as F-PIN's remainder folds in
  F-FACTORY (procedure-scoped `sod_steps` via a procedure-aware
  `ExecutorFactory` — today zero-arg, `registry.py:30`, with
  `hero_demo/run.py:278` hardcoding the frozenset) **+ the ADR-0031 OQ-4
  CI-marker debt check** (⚠ drafter flag: PLAN-0074 AC-11 armed
  `test_at2_signature_retrigger.py` at this baseline, so the OQ-4 debt is
  likely already PAID — the stub PLAN verifies it exists on main rather
  than carrying the debt forward unexamined; the rot PRECEDENT stands as
  motivation either way). Severity context: a mis-bound `sod_steps` only
  mislabels the `sod_required` display flag (`governance_step.py:197`,
  `:256`); actual SoD enforcement reads `procedure.separation_of_duties`
  live at `action_step.py:351-353`.
- ❌ **A `RoleId` rank engine primitive** — RESOLVED OUT by the ratified
  SD-1(a): rank stays authored data. Related unbuilt rank-dependency,
  cross-referenced not fixed: ADR-0026 D5's waiver strict-escalation
  "run-checkable against the resolved role rank" (`0026:71`) stays
  author-time-only (the Amendment's D5-reconciliation note records the
  reading).
- ❌ **ADR-0026 OQ-6** core-Person extraction (own follow-on, per
  PLAN-0074 SD-4 resolution).
- ❌ Any edit to ADR-0031's D3 table (D4.4 fires when a SEAM lands; this
  PLAN deliberately builds none — the AC-13 provenance hash is a pin
  field, not a seam).
- ❌ ERP / live I/O, new StepKinds, generator changes, hero-demo UI
  scenes.

## Steps

### Step 0: Pre-flight baseline
Green run of the existing suite on the branch base (pre-committed
pass/fail read); confirm `test_procurement_sod_gate.py` +
`test_cold_chain_disposition.py` + `test_hero_run.py` +
`test_hero_governance_audit.py` + the golden load gate pass; snapshot
the exact currently-green assertions AC-8 (S1) and AC-10 (S2) will
change.

### Step 1: The ADR amendment lands (AC-12; SD-4 RATIFIED)
The ADR-0026 D4 Amendment (2026-07-15) is **already drafted** (Deliverable
A of the s132 drafting session — the 4th fail-closed condition, the
rank-as-data stance + D5 reconciliation, the every-verdict rule, the
actor-named tie, the C1 residual-risk note). Code R2-reviews + commits it
and **merges before** the Steps 2-7 implementation PR.

### Step 2: The pure core (AC-1, AC-2, AC-3)
`tier_authority.py`: typed violation kinds, the ratified exact-match
predicate over N verdicts (every-verdict rule), the declared-content/
missing-verdict fail-closed direction, structured verdict. Pure tests for
every violation kind + both ladder kinds + the mixed-tier fan-out case
(latent-regression guard).

### Step 3: Gate wiring + audit reconciliation (AC-4, AC-6)
Invoke from `resolve_gated_step` after SoD; durable `gate_refused` audit;
typed error → HTTP 403 (JSON-safe detail); move the authority
`GovernedDecision` emission to gate time per ratified SD-6(a); update the
offline hero audit builder (S2) to match; DB-marked wiring tests
(existing skip posture) — the enforcement logic itself already fully
covered offline by Step 2.

### Step 4: F3 load-time check (AC-5)
`_check_authority_step_gated` in `orchestrator.py` beside
`_check_no_auto_downstream_of_gate`; negative fixture tests; shipped
YAMLs + the hero_demo in-code procedure load unchanged.

### Step 5: Truth pass + the blessing test (AC-7, AC-8 — S1)
Correct the seven over-claim sites (the two persisted trace strings
first); re-harness `test_procurement_distinct_principals_proceeds` on the
governance executors with a quote-bearing seed, the S1 ladder-resolved
`appr-pm` + refusal companions (`appr-buyer`, `appr-director`).

### Step 6: Red-team oracle + S2 regression (AC-9, AC-10)
The oracle fixtures (incl. the latent mixed-tier guard); the S2 hero-demo
junior-refusal regression + `appr-controller` happy path + audit-builder
alignment.

### Step 7: SD-5 fold-in — supply_chain derivation provenance (AC-13) + full verification (AC-11)
Thread the optional derivation-hash parameter (run-start capture →
`assert_governance_pin` re-check); hash `_DOSE_LADDER` + `_TOP_SEVERITY`
automatically into the supply_chain snapshot; the AC-13 offline tests
(deterministic hash / mid-flight mutation fails closed / no
cross-vertical bleed / the self-cancelling F-PIN-residual marker); file
the SD-3+SD-5 follow-on stub PLAN + STATUS entry (Code, at commit time);
then the full suite + ruff + mypy (AC-11) as the finale.

## Verification

Offline pytest with pass/fail reads fixed before each run: the pure
tier-authority tests (junior refused / resolved-tier passes /
missing-verdict refused / mixed fan-out fails closed as a latent guard)
run and pass with Postgres down; the F3 negative fixtures fail load; the
AC-7 two-part oracle (multiline three-phrasing grep over `services/` +
`tests/` = zero hits, AND the seven-site checklist walked at R2) holds;
the re-harnessed S1 procurement test passes with `appr-pm` and its
refusal companions fail closed; the S2 hero offline flow resolves with
`appr-controller` and refuses a generic-role junior; the AC-13 provenance
tests hold (deterministic supply_chain derivation hash; a mid-flight
`_DOSE_LADDER`/`_TOP_SEVERITY` mutation fails closed at the pin;
procurement/energy/aquaculture snapshots byte-identical; the
self-cancelling F-PIN-residual marker green); DB-marked wiring tests keep
their skip-without-Postgres behavior. No live/host-state run is required;
any live smoke (real Postgres end-to-end) is a separate Cray-gated step
(CLAUDE.md §8).

## Surfaced Decisions — adjudication state (2026-07-15, session 132)

- **SD-1 — THE enforcement predicate. RATIFIED (Cray, s132) = (a).**
  Exact-match + rank-as-DATA: `verdict.required_role ∈ principal.roles`;
  NO engine rank primitive over `RoleId` (which stays a free string,
  `spec.py:522`; ADR-0026 `0026:25`, `:145`); where a senior should
  approve downward, that is expressed by authoring cumulative role sets
  in YAML. Failure posture: over-strict, never unsafe. Per Correction 1
  the shipped YAML is NOT given cumulative roles in this PLAN (fan-out
  cardinality is 1 today — Code's recommendation, veto-open); rank-as-data
  is the documented supported mechanism for when a multi-requisition run
  or a design partner needs downward approval. Rejected alternatives
  recorded: (b) a typed rank primitive (ADR-0031 D2 tripwire-4 exposure;
  heavier blast radius); (c) `person_id == resolved_approver_id`
  (non-deterministic — `holders[0]` is an arbitrary sorted tie-break,
  `doa_tier.py:132`, `severity_tier.py:143`). Recorded in the ADR-0026
  Amendment (2026-07-15).
- **SD-2 — verdict source + fan-out rule. RATIFIED (Cray, s132) = (a)
  source + (i) rule.** Read the persisted engine-written verdicts off the
  gated step's `audit["doa_tier"|"severity_tier"]` (the very `StepResult`
  row `resolve_gated_step` loads; written at `governance_step.py:242`/
  `:296`; pin-protected upstream, `action_step.py:526`); the acting
  principal must satisfy **EVERY** verdict. The mixed-tier consequence is
  **latent, not live** (Correction 1: shipped cardinality = 1 —
  `hero_demo/run.py:347` single-element seed, snapshot-verified;
  `test_hero_run.py:72` destructures exactly one verdict, R2-verified);
  a future N>1 mixed-tier run under non-cumulative roles fails closed —
  guarded by the AC-9 fixture. Rejected alternative recorded: (b)
  re-resolve at the gate (the authority quantity is NOT on the gated
  step's artifact — the `_doa_tier` branch keeps base output = action
  envelopes and drops the spend, `governance_step.py:208`, `:245`).
  Recorded in the ADR-0026 Amendment (2026-07-15).
- **SD-3 — build the ADR-0031 D3 gate-plugin seam now, or keep narrow?
  CONFIRMED narrow (Cray, s132, after a 3-specialist review — architect +
  security ~85% concurrence), WITH the architect's binding condition:**
  the seam is a **durably-tracked follow-on** — a filed stub PLAN + a
  STATUS Active-TODO entry (shared with F-PIN's remainder; Code files
  both at commit time) — never a bare out-of-scope bullet, because the
  repo has a documented deferral-rot precedent (ADR-0031 OQ-4: the
  ADR-0025 D7 CI marker was promised and long unbuilt). The follow-on
  folds in F-FACTORY (procedure-scoped `sod_steps` via a procedure-aware
  `ExecutorFactory`) + the OQ-4 marker-debt check (⚠ drafter flag:
  PLAN-0074 AC-11 likely already paid it — verify on main, don't assume).
  Rationale for narrow stands: a security fix on the shipped hero path
  should land small and adversarially reviewable (D4.2 gives the seam its
  own PLAN); bundling a framework refactor with a security fix is how
  security fixes get delayed.
- **SD-4 — the ADR vehicle. RATIFIED (Cray, s132) = amend ADR-0026 D4**
  (not a new ADR-0032). The amendment is DRAFTED (Deliverable A, this
  session): D4 condition (iv), the rank stance + D5 reconciliation, the
  fan-out rule, the actor-named tie, and the C1 derivation residual-risk
  note (specialist review); Status stays Accepted (in-place amendment per
  the ADR-0022 / ADR-016 precedent); drafter-authored, Code-committed (an
  Accepted-body edit does not lift G1), merged before the implementation
  PR.
- **SD-5 — F-PIN: fold in or defer? ADJUDICATED SPLIT (Cray, s132, after
  a 3-specialist review): defer the BULK; fold in the supply_chain
  derivation-provenance half NOW (AC-13, Step 7 — PROVENANCE-ONLY).**
  The pin covers the ladder + autonomy (`governance_pin.py:42-88`, `:57`)
  but nothing that derives the ladder's INPUT. **What the fold-in buys,
  stated exactly (C2 — the earlier "cheap `derivation_version` closes
  it" note was WRONG and is retracted):** the snapshot is a per-run
  projection captured at run-start and re-checked at resolve, failing
  closed only on a run-start↔resolve MISMATCH — so a derivation hash
  buys (i) mid-flight tamper-evidence and (ii) audit provenance ("which
  derivation governed THIS run"); it does **NOT** close the new-run
  re-routing threat (a new run started on already-changed code pins the
  changed derivation without complaint), and it is only clean for
  supply_chain's data-tuple constants — procurement's imperative ฿ math
  has no clean datum. **F-PIN is NOT closed** — do not record it as
  closed anywhere. **Honest deferral rationale (C3 — "different axis" is
  retracted; both reviewers rejected it):** the derivation gap is the
  SAME authority axis one layer down (an authority decision whose input
  is untrusted is not fully enforced) — but a lower THREAT TIER: it
  requires code access + a PR + a deploy, whereas the bug this PLAN
  closes is exploitable by an ordinary operational user (a junior
  approver, no code change). **Tracking (tripwire-backed):** the filed
  stub PLAN + STATUS entry (shared with SD-3's seam follow-on) + the
  AC-13(d) self-cancelling marker. **The follow-on's proper form is
  "declare the derivation as data," not "hash more code"**:
  `cold_chain_assess.py:68-70` states verbatim that `_DOSE_LADDER` "IS
  THE DATUM A TRANSFORM GRAMMAR WOULD DECLARE (ADR-0031 D3 row-1)"; once
  promoted to declared governance data, the existing pin covers it for
  free (`governance_pin.py:59-63`, `governance_content`), making a
  hand-rolled procurement code-hash throwaway work.
- **SD-6 — `GovernedDecision` reconciliation mechanics. RATIFIED (Cray,
  s132) = (a).** The principal-naming authority tie moves to gate time
  (emitted after the tier-authority check passes, naming the actor;
  run-time keeps the trace-level routing record): the audit never names a
  non-actor, and a suspended run honestly shows routing-only. No OQ-5
  envelope change. Rejected alternative recorded with its true price: (b)
  run-time routed-to re-keying is NOT cheap —
  `GovernedDecision.principal_id: str` is required, non-nullable, under
  `extra="forbid"` (`services/engine/actions.py:61-66`, R2-verified), so
  (b) would be an envelope change to the OQ-5 minimal shape (a required
  field made optional AND a new field), which AC-11 forbids. Recorded in
  the ADR-0026 Amendment (2026-07-15).

## References

- **ADR-0026 Amendment (2026-07-15)** — the ratified governance decision
  this PLAN implements (D4 condition (iv); rank-as-data; every-verdict;
  actor-named tie; the C1 derivation residual-risk note) —
  `docs/adr/0026-principal-identity-run-enforcement.md`
- ADR-0026 — D4 (`0026:63-65`, now amended), D5 (`0026:71`),
  LOCKED #2/#3/#5 (`0026:46-49`), RoleId-free-string (`0026:25`, `:145`)
- ADR-0025 — D6 guarantees + fallback (`0025:90-97`), D8 red-team
  discipline, LOCKED #5 (`0025:51`)
- ADR-0031 — D2 tripwires (`0031:118-125`), D3 gate row (`0031:136`) +
  row-1 (the transform grammar the F-PIN follow-on's declare-as-data form
  lands in), D4.1/D4.2/D4.4 (`0031:148-159`), OQ-4 (the deferral-rot
  precedent SD-3's tracking answers)
- ADR-016 — RF-1 fail-closed-regardless-of-authn; SP-1 gated→auto
  precedent · ADR-007 (write gate, untouched)
- PLAN-0074 (the 2nd signature + s131 review that ratified this
  follow-on; its coordination-point enumeration feeds the SD-3 seam PLAN;
  its AC-11 likely paid the OQ-4 marker debt — verify)
- Code anchors (verified by the drafter 2026-07-15 vs origin/main
  ff84d9a): `governance_step.py:189-299, 221, 231-238, 242, 279,
  285-292, 296`; `principal_sod.py:118-208, 139, 176`;
  `action_step.py:292-302, 351-353, 392-403, 406-430, 433, 515-519, 526,
  532-534, 580`; `doa_tier.py:66-68, 113-114, 132-140`;
  `severity_tier.py:67-69, 114-125, 143-151`; `draft.py:264-266,
  302-304, 331-343`; `orchestrator.py:201-205, 562-608, 611-623,
  648-682`; `spec.py:522, 840`; `governance_pin.py:42-88, 57, 59-63`;
  `registry.py:30`; `runs.py:377-396` (API router);
  `hero_demo/run.py:275-290, 278, 347, 359-369`;
  `hero_demo/governance_audit.py:48, 53-56, 140-165`;
  `verticals/procurement/procedures.yaml:39, 62-77, 233-236, 241-244,
  293-297`; `verticals/supply_chain/procedures.yaml:28, 43, 61-76,
  290-304`; `cold_chain_assess.py:62-77` (the derivation constants:
  `_DOSE_LADDER` `:71-75`, `_TOP_SEVERITY` `:76-77`, the ADR-0031 D3
  row-1 "THIS IS THE DATUM" comment `:68-70`);
  `tests/services/db/test_procurement_sod_gate.py:357-361, 372-377,
  405-430, 433-454`; `test_doa_tier.py:136-138`;
  `test_severity_tier.py:140-141`
- Code anchors verified by Code at R2 / session 132 (same baseline; these
  files were outside the drafting snapshot):
  `services/engine/actions.py:61-66` (`GovernedDecision.principal_id:
  str` required, non-nullable, `extra="forbid"` — the SD-6(b) pricing);
  `services/engine/procedures/runs.py:110` (engine-side
  `StepResult.audit` JSONB — the SD-2(a) persistence substrate);
  `hero_demo/procedure.py:36-46` (the S2 Fastenal ladder — floors
  0/15001/200001/1000001, roles SUPERVISOR/MANAGER/CONTROLLER/
  VP_OPERATIONS) + `:74` (CSV principals);
  `test_hero_run.py:72-75` (single-verdict destructure; ฿288,000 →
  CONTROLLER/appr-controller); `test_hero_governance_audit.py:51, 57`
