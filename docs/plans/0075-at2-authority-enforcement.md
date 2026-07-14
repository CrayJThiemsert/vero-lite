# PLAN-0075: AT-2 authority enforcement at the run gate — the acting approver must hold the ladder-resolved tier role (doa_tier + severity_tier)

**Status:** Proposed — awaiting Cray ratification (SD-1..SD-6 adjudicated at review)
**Owner:** Claude Code (execution) · Cray (SD adjudication + ratification)
**Created:** 2026-07-15
**Related ADRs:** ADR-0026 (D4 fail-closed conditions — the amendment vehicle per SD-4; D5's "routes/suspends to the resolved approver" promise this PLAN completes; LOCKED #2/#3/#5), ADR-0025 (D6 hard guarantees + D8 red-team oracle discipline), ADR-0031 (D2 moat tripwires; D3 gate-seam row — deliberately NOT built here, SD-3), ADR-016 (RF-1 fail-closed-regardless-of-authn; SP-1 gated→auto hazard precedent), ADR-007 (approve→execute write gate, untouched)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code, session 132; the follow-on itself was
> ratified by Cray at the PLAN-0074 session-131 adversarial review).
> Independent review: Code (R2) at PR; ratification: Cray. Author≠reviewer
> separation: **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.
> All code claims verified against a pinned snapshot of `origin/main`
> @ ff84d9a (2026-07-15).

## Goal

Close the **AT-2 authority-enforcement gap** across the whole authorisation
axis — `doa_tier` (the SHIPPED procurement hero) **and** `severity_tier`
(supply_chain, PLAN-0074): an authority ladder resolves + **audits** which
tier/approver a spend or severity routes to
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
committed test that blesses the bug, and (6) ships an ADR-0025 D8-analog
offline red-team oracle. Framing: this **completes an existing guarantee**
— ADR-0025 D6 (`0025:90`) and ADR-0026 D5 (`0026:71`) already promise the
executor "routes / **suspends to the resolved approver** for that tier" —
it does not invent new policy (no accepted ADR/PLAN ever promised
tier-role *enforcement*; verified clean negative, fact-pack §2).

## Context — LOCKED vs open

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
   (ADR-0031 D2 `0031:118-125`) bind — esp. tripwire 4 (never flip a
   closed governed enum to free strings), live for SD-1(b). **Fail closed
   regardless of authn** (ADR-016 RF-1).
3. **The offline oracle is the gate (CLAUDE.md §8).** `resolve_gated_step`
   is DB-bound (loads the run, appends audit, commits) — a regression test
   written only at that level SKIPS when Postgres is down. The enforcement
   core is therefore a **pure function** (no DB/LLM/network), mirroring
   `check_principal_sod`'s own design (`principal_sod.py:18-19` states it
   verbatim). This purity is a **hard requirement**, not a style choice.

**Open (Cray adjudicates at review):** SD-1 the enforcement predicate (THE
central call), SD-2 the verdict source + multi-entity fan-out rule, SD-3
narrow-fix vs gate-plugin seam, SD-4 the ADR vehicle, SD-5 F-PIN handling,
SD-6 the `GovernedDecision` reconciliation mechanics.

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

**Exploit 1 — procurement (the shipped hero).** Principals
(`verticals/procurement/procedures.yaml:62-77`): `appr-buyer:[approver,
"หน.จัดซื้อ"]`, `appr-pm:[approver, "ผจก.จัดซื้อ"]`, `appr-plant:[approver,
"ผจก.โรงงาน"]`, `appr-director:[approver, "ผอ."]` — roles NON-cumulative.
DoaLadder floors (`:233-236`): 0→หน.จัดซื้อ, 50k→ผจก.จัดซื้อ,
500k→ผจก.โรงงาน, 2M→ผอ. SoD (`:293-297`): `{intake: requester, approve:
approver}`. The hero spend ฿288,000 routes to ผจก.จัดซื้อ (`appr-pm`) —
but **`appr-buyer`** (ladder authority `[0, 50000)` only) holds the
generic `approver`, is distinct from `req-planner`, and resolves the
฿288k gate **unblocked** — and equally a ฿2M+ ผอ.-tier PO.

**Exploit 2 — supply_chain.** Principals
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
(`:405-430`) drives the real hero procedure and resolves the ฿288,000
gate with **`appr-director`** (top tier — NOT the ladder-resolved
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

## Design sketch (contingent on SD-1/SD-2/SD-6 — the shape, not the ratified choice)

- **New pure module** `services/engine/procedures/tier_authority.py`
  (name at Code's discretion), mirroring `principal_sod.py`: a
  `check_tier_authority(...)` pure function returning a **structured
  verdict** (`TierAuthorityVerdict{governed, violations}` with typed
  violation kinds — e.g. `TIER_ROLE_MISMATCH`, `VERDICT_MISSING`,
  `UNKNOWN_PRINCIPAL`), never a bare bool. `check_principal_sod` stays
  **byte-identical** (LOCKED #2).
- **Inputs (SD-2a):** the acting `principal: Person`, the gated step's
  declared `governance_content` (DoaLadder | SeverityLadder | other),
  and the step's **persisted** authority verdicts —
  `target.audit["doa_tier" | "severity_tier"]`, the `to_audit()` list the
  executor wrote at run time (`governance_step.py:242`, `:296`; each
  entry carries `required_role` + `resolved_approver_id`; persisted JSONB
  on the engine-side `StepResult.audit`,
  `services/engine/procedures/runs.py:110`, R2-verified). Two fail-closed
  triggers: (i) verdicts present → enforce the SD-1 predicate against
  **every** verdict; (ii) authority content declared on the step but NO
  verdicts persisted → refuse (the plain-executor bypass above).
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
  fail-closed refusal (both shipped verticals already comply; the check
  makes the one-word flip unrepresentable-at-load).
- **Audit reconciliation (SD-6, recommended (a)):** the run-time
  principal-naming `GovernedDecision` emission moves to **gate time** —
  emitted beside the `sod` tie in/next to `_record_governed_decision`
  after the tier-authority check passes, naming the **acting** principal
  (who now provably holds the tier role). The run-time reasoning-trace
  routing record ("resolved to 'appr-pm'") **stays** — it is honest as
  routing. The hero render keeps working (it reads the `audit["doa_tier"]`
  verdicts, not `governed_decision`: `hero_demo/run.py:365-369`,
  `governance_audit.py:140-165`; the offline builder is updated to match
  the new emission semantics).

## Acceptance Criteria

- [ ] **AC-1 — pure core.** New module with `check_tier_authority` +
  structured verdict; **no DB / LLM / network imports** (pass/fail read:
  the module imports only stdlib + `spec`/verdict types, and its tests run
  with Postgres down); `principal_sod.py` byte-identical (`git diff`
  empty on it).
- [ ] **AC-2 — the predicate (SD-1-ratified; drafted default = (a)
  exact-match).** For every persisted verdict on the gated step:
  `verdict.required_role ∈ principal.roles`, else refuse. Documented
  posture: over-strict, never unsafe (refuses a senior; never admits a
  junior). The multi-entity rule is SD-2's: the principal must satisfy
  **every** verdict. Pass/fail read: pure tests — `appr-buyer` refused at
  ฿288k; `appr-qa` refused at `critical`; the ladder-resolved approver
  passes; under (a) `appr-director` is ALSO refused at ฿288k (this
  assertion encodes the SD-1 resolution and flips if Cray picks (b)).
- [ ] **AC-3 — missing-verdict fail-closed.** A gated step whose declared
  `governance_content` is an authority ladder but whose persisted audit
  carries no `doa_tier`/`severity_tier` verdict list is **refused**
  (violation kind `VERDICT_MISSING`). Pass/fail read: a pure test with
  content-declared + empty audit refuses; the re-harnessed AC-8 test
  would fail without governance executors.
- [ ] **AC-4 — gate wiring.** `resolve_gated_step` invokes the check
  after SoD, before the Phase-1 commit; refusal is durably audited
  (`gate_refused` payload naming the violation) BEFORE the typed error
  propagates; HTTP → 403 with the structured verdict (JSON-safe — heed
  the PLAN-0072 frozenset lesson at `runs.py:389-395`). Non-skippability
  matches the SoD posture: enforcement keys off the persisted audit
  (works even procedure-less), and the declared-content direction fires
  whenever the caller supplies `procedure` (the HTTP surface always does,
  `runs.py:377-386`).
- [ ] **AC-5 — F3.** `validate_governance_complete` refuses a procedure
  whose authority-content step is not a GATED action. Negative tests:
  flipping procurement `approve` / supply_chain disposition `approve` to
  `auto` (fixture copies, not the shipped YAML) fails load; both shipped
  verticals load unchanged. Cross-cite ADR-0025 D6 g2 / ADR-016 SP-1.
- [ ] **AC-6 — audit reconciliation (SD-6-ratified).** After this PLAN, a
  persisted `governed_decision` under kind `doa_tier`/`severity_tier`
  names ONLY a principal who actually acted. Pass/fail read: a
  gate-resolution test asserts the tie names the actor; a suspended
  (unresolved) run carries NO principal-naming authority tie; grep
  confirms the run-time emission (`governance_step.py:231-238`,
  `:285-292`) no longer emits `principal_id` at run time.
- [ ] **AC-7 — the seven over-claim sites corrected.** Per-site
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
- [ ] **AC-8 — the blessing test fixed.**
  `test_procurement_distinct_principals_proceeds` is re-harnessed on the
  governance executors (pattern `hero_demo/run.py:275-290` — which
  requires threading a quote-bearing seed so `scored_rule` stamps the
  spend; the raw synthetic failure events carry no `candidate_quotes`)
  and resolves with the **ladder-resolved** approver; companion negative:
  `appr-buyer` (and, under SD-1(a), `appr-director`) refused on the same
  run shape. No test remains that blesses a non-resolved-tier approver.
- [ ] **AC-9 — the red-team oracle (ADR-0025 D8 analog, offline).** Pure
  fixtures, Postgres-free: (1) junior-refused for `doa_tier` AND
  `severity_tier`; (2) missing-verdict refused (AC-3); (3) an undeclared/
  unknown acting principal refused; (4) the mixed-tier fan-out case
  behaves per the SD-2 ratified rule (under (a)+strict: fails closed);
  (5) F3 hollow case — an `auto` authority step is refused at load. Each
  asserts the structured violation kind, not just "raised".
- [ ] **AC-10 — hero-demo path stays green.** The offline hero
  governance-moment flow (stubbed client) still suspends with the
  `doa_tier` audit (`hero_demo/run.py:359-369`), resolves with `appr-pm`,
  and the render contract (`governance_audit.py`) is intact; the offline
  audit builder's `governed_decision` matches the new gate-time
  semantics.
- [ ] **AC-11 — suite hygiene.** Whole suite deterministic + offline (no
  LLM, no MS-S1, DB tests keep their existing skip behavior); ruff +
  mypy clean; no change to the ADR-007 envelope or `GovernedDecision`'s
  minimal shape (control ref + principal key, ADR-0026 OQ-5) beyond
  emission timing — this clause is contingent on SD-6(a); if Cray picks
  SD-6(b), the OQ-5 shape change it entails is recorded via the SD-4
  ADR vehicle and this clause is amended accordingly; no new StepKind,
  no new engine.
- [ ] **AC-12 — the ADR lands first (SD-4-ratified).** The governance
  decision (the 4th fail-closed condition + the `RoleId`-rank stance from
  SD-1) is recorded in the SD-4 vehicle (amend ADR-0026 D4, or new
  ADR-0032), drafter-authored + Code-committed + **merged before the
  implementation PR** (CLAUDE.md §8 Code Quality). Note for Cray: an
  Accepted-ADR body edit does NOT lift the G1 gate — either vehicle
  routes through the drafter in one pass.

## Out of Scope

- ❌ **F-PIN** — pinning the authority-**derivation** code
  (`cold_chain_assess.py:71` `_DOSE_LADDER`; procurement's runtime ฿
  computation in `governance_step.py:301-348`). The pin hashes the
  Procedure only (`governance_pin.py:42-88`); a deploy can re-route
  authority invisibly to the pin. Different axis (pin integrity, not
  authority enforcement) → SD-5 recommends its own PLAN; the cheap
  `derivation_version` mitigation is noted there for Cray.
- ❌ **F-FACTORY / the ADR-0031 D3 gate-plugin seam.** The trigger HAS
  fired (2nd AT-2 signature, PLAN-0074 merged — D4.1 satisfied), but
  D4.1 does not compel a build and D4.2 gives each seam its own PLAN →
  SD-3. Honest note: F-FACTORY's proper fix (a procedure-scoped
  `sod_steps` — today `ExecutorFactory` is zero-arg, `registry.py:30`,
  and `hero_demo/run.py:278` hardcodes the frozenset) needs that seam;
  severity is LOW (a mis-bound `sod_steps` only mislabels the
  `sod_required` display flag — `governance_step.py:197`, `:256`; actual
  SoD enforcement reads `procedure.separation_of_duties` live at
  `action_step.py:351-353`).
- ❌ **A `RoleId` rank engine primitive** — unless Cray picks SD-1(b);
  under the recommended SD-1(a) rank stays authored data (cumulative
  role sets in YAML). Related unbuilt rank-dependency, cross-referenced
  not fixed: ADR-0026 D5's waiver strict-escalation "run-checkable
  against the resolved role rank" (`0026:71`) stays author-time-only.
- ❌ **ADR-0026 OQ-6** core-Person extraction (own follow-on, per
  PLAN-0074 SD-4 resolution).
- ❌ Any edit to ADR-0031's D3 table (D4.4 fires when a SEAM lands; this
  PLAN deliberately builds none).
- ❌ ERP / live I/O, new StepKinds, generator changes, hero-demo UI
  scenes.

## Steps

### Step 0: Pre-flight baseline
Green run of the existing suite on the branch base (pre-committed
pass/fail read); confirm `test_procurement_sod_gate.py` +
`test_cold_chain_disposition.py` + the golden load gate pass; snapshot
the exact currently-green assertions AC-8 will change.

### Step 1: The ADR vehicle (AC-12; SD-4-gated)
Per Cray's SD-4 call: draft the ADR-0026 D4 amendment (add the 4th
fail-closed condition — "the acting approver does not hold the
ladder-resolved tier role, or the authority verdict is missing" — plus
the SD-1 `RoleId`-rank stance) or a new ADR-0032. Drafter-authored, Code
R2 + committed, merged **before** Steps 2-6's implementation PR.

### Step 2: The pure core (AC-1, AC-2, AC-3)
`tier_authority.py`: typed violation kinds, the SD-1 predicate over N
verdicts (SD-2 rule), the declared-content/missing-verdict fail-closed
direction, structured verdict. Pure tests for every violation kind +
both ladder kinds + the mixed-tier fan-out case.

### Step 3: Gate wiring + audit reconciliation (AC-4, AC-6)
Invoke from `resolve_gated_step` after SoD; durable `gate_refused` audit;
typed error → HTTP 403 (JSON-safe detail); move the authority
`GovernedDecision` emission to gate time per SD-6; update the offline
hero audit builder to match; DB-marked wiring tests (existing skip
posture) — the enforcement logic itself already fully covered offline by
Step 2.

### Step 4: F3 load-time check (AC-5)
`_check_authority_step_gated` in `orchestrator.py` beside
`_check_no_auto_downstream_of_gate`; negative fixture tests both
verticals; shipped YAMLs load unchanged.

### Step 5: Truth pass + the blessing test (AC-7, AC-8)
Correct the seven over-claim sites (the two persisted trace strings
first); re-harness `test_procurement_distinct_principals_proceeds` on the
governance executors with a quote-bearing seed, ladder-resolved approver
+ refusal companions.

### Step 6: Red-team oracle + full verification (AC-9, AC-10, AC-11)
The oracle fixtures; offline hero-demo flow; full suite; ruff + mypy.

## Verification

Offline pytest with pass/fail reads fixed before each run: the pure
tier-authority tests (junior refused / resolved-tier passes /
missing-verdict refused / mixed fan-out per SD-2) run and pass with
Postgres down; the F3 negative fixtures fail load; the grep oracle for
the false trace string returns zero; the re-harnessed procurement test
passes with the ladder-resolved approver and its refusal companions fail
closed; the hero offline flow stays green; DB-marked wiring tests keep
their skip-without-Postgres behavior. No live/host-state run is required;
any live smoke (real Postgres end-to-end) is a separate Cray-gated step
(CLAUDE.md §8).

## Surfaced Decisions (Cray adjudicates at review — recommendations are contingent, veto-open)

- **SD-1 — THE enforcement predicate.** No ADR defines a rank over
  `RoleId` — it is a free string (`spec.py:522`; ADR-0026 `0026:25`,
  `:145`), yet ADR-0026 D5 already leans on "the resolved role rank"
  (`0026:71`). Roles are **non-cumulative** in both verticals (verified
  §Exploits), so the naive `required_role ∈ principal.roles` is an
  exact-match that correctly BLOCKS `appr-buyer` from the ฿288k gate but
  ALSO blocks `appr-director` from it (a director cannot approve a ฿288k
  PO). Failure mode: **over-strict, never unsafe**. Options:
  **(a) exact-match + rank-as-DATA — recommended.** Zero new engine
  primitives, fail-closed; where a senior should approve downward, author
  cumulative roles in the YAML (e.g. `appr-director: [approver, ผอ.,
  ผจก.โรงงาน, ผจก.จัดซื้อ, หน.จัดซื้อ]`). Rank stays a
  declaration-as-data concern — squarely the ADR-0031 D2 moat spirit.
  Cost: AC-8's approver changes to `appr-pm` (or the YAML gains
  cumulative roles, Cray's sub-call).
  **(b) a typed, closed `RoleId`-rank primitive.** Has D5 warrant, but is
  a NEW governed primitive; ⚠ ADR-0031 D2 tripwire 4 is live (must stay
  closed + typed, never a free-string ordering); heavier blast radius.
  **(c) `principal.person_id == verdict.resolved_approver_id` —
  recommend AGAINST:** `holders[0]` is an arbitrary sorted tie-break
  (`doa_tier.py:132`, `severity_tier.py:143`) — non-deterministic policy
  when two people hold a tier role.
  *Why Cray:* this decides who may legally authorise what — business/
  domain judgment, not a code call.
- **SD-2 — verdict source + the multi-entity fan-out rule.**
  **(a) read the persisted engine-written verdicts** on the gated step's
  `audit["doa_tier"|"severity_tier"]` (the very `StepResult` row
  `resolve_gated_step` loads; written at `governance_step.py:242`/`:296`)
  — **recommended**; pin-protected upstream (a mid-flight ladder edit
  already fails the pin, `action_step.py:526`). **(b) re-resolve the
  ladder at the gate** — harder: the authority *quantity* is NOT on the
  gated step's artifact (the `_doa_tier` branch keeps base output =
  action envelopes and drops the spend, `governance_step.py:208`,
  `:245`). Either way the fan-out rule must be stated: `audit["doa_tier"]`
  is a LIST (one verdict per entity), procurement's `approve` fans out
  over compliant candidates (`procedures.yaml:241-244`), one principal
  resolves ALL proposals. Rule options: **(i) the principal must satisfy
  EVERY verdict — recommended** (strictest, most literal). ⚠ Honest
  nuance the dispatch's "i.e. the max tier" glossed: under SD-1(a) with
  non-cumulative YAML roles, a MIXED-tier verdict set is satisfiable by
  NO single principal → fails closed (resolve per-tier / re-propose);
  with cumulative-authored roles (i) ≡ (ii). **(ii) require only the
  max tier's role** — admits a senior over lower-tier items in the same
  set. *Why Cray:* the fan-out rule is an authorisation policy, and (i)
  can refuse resolutions that (ii) permits.
- **SD-3 — build the ADR-0031 D3 gate-plugin seam now, or keep narrow?**
  The trigger HAS fired (D4.1 satisfied — PLAN-0074 merged the 2nd
  signature), and PLAN-0074 SD-3 already pointed its coordination-point
  enumeration at a follow-on. *Recommendation: keep NARROW.* This is a
  security fix on the shipped hero path; it should land small and
  adversarially reviewable (D4.2 gives the seam its own PLAN). Bundling
  a framework refactor with a security fix is how security fixes get
  delayed. Honest flag: F-FACTORY's proper fix needs that seam. *Why
  Cray:* it schedules the moat's abstraction step against a live
  security window.
- **SD-4 — the ADR vehicle.** ADR-0026 D4's fail-closed list is
  exhaustive with no 4th condition (`0026:63-65`), and D5/D6 already
  promise routing to the resolved approver — this completes an existing
  guarantee. *Recommendation:* **amend ADR-0026 D4** (add the 4th
  condition + record the SD-1 rank stance, which is ADR-grade) rather
  than mint ADR-0032. Alternative: a small ADR-0032 if Cray prefers the
  decision at its own address. Either way: drafter-authored,
  Code-committed (an Accepted-body edit does not lift G1), merged before
  the implementation PR.
- **SD-5 — F-PIN: fold in or defer?** The pin covers the ladder +
  autonomy (`governance_pin.py:42-88`, `:57`) but nothing that derives
  the ladder's INPUT (`_DOSE_LADDER`, the runtime ฿ computation) — a
  code deploy re-routes authority invisibly to the pin. Nuance: the
  `autonomy` pin means a gated→auto flip trips an in-flight run, not a
  new one. *Recommendation:* cross-reference + own PLAN (different axis);
  the mitigation is cheap (a `derivation_version` in the snapshot) if
  Cray wants it folded in.
- **SD-6 — `GovernedDecision` reconciliation mechanics.** **(a) move the
  principal-naming authority tie to gate time** (emitted after the
  tier-authority check passes, naming the actor; run-time keeps the
  trace-level routing record) — **recommended**: the audit then never
  names a non-actor, and a suspended run honestly shows routing-only.
  **(b) keep the run-time emission but re-key it as routed-to** —
  ⚠ priced honestly: this is NOT a cheap re-keying.
  `GovernedDecision.principal_id: str` is a **required, non-nullable**
  field under `model_config = ConfigDict(extra="forbid")`
  (`services/engine/actions.py:61-66`, R2-verified) — so
  "`principal_id=None` + a routing field" means making a required field
  optional AND adding a field, i.e. an **envelope change to the
  ADR-0026 OQ-5 minimal shape** (which AC-11 forbids as drafted, and
  which likely needs its own ADR decision via the SD-4 vehicle) — and it
  still leaves two same-kind ties with different meanings. This
  asymmetry is itself a substantive argument for (a). *Why Cray:* what the permanent
  governance record NAMES is an audit-semantics call with compliance
  weight (PDPA/audit-trail posture, CLAUDE.md §8), not a code
  preference.

## References

- ADR-0026 — D4 (`0026:63-65`, the amendment target), D5 (`0026:71`),
  LOCKED #2/#3/#5 (`0026:46-49`), RoleId-free-string (`0026:25`, `:145`)
- ADR-0025 — D6 guarantees + fallback (`0025:90-97`), D8 red-team
  discipline, LOCKED #5 (`0025:51`)
- ADR-0031 — D2 tripwires (`0031:118-125`), D3 gate row (`0031:136`),
  D4.1/D4.2/D4.4 (`0031:148-159`)
- ADR-016 — RF-1 fail-closed-regardless-of-authn; SP-1 gated→auto
  precedent · ADR-007 (write gate, untouched)
- PLAN-0074 (the 2nd signature + s131 review that ratified this
  follow-on; its coordination-point enumeration feeds the SD-3 seam PLAN)
- Code anchors (verified 2026-07-15 vs origin/main ff84d9a):
  `governance_step.py:189-299, 221, 231-238, 242, 279, 285-292, 296`;
  `principal_sod.py:118-208, 139, 176`; `action_step.py:292-302,
  351-353, 392-403, 406-430, 433, 515-519, 526, 532-534, 580`;
  `doa_tier.py:66-68, 113-114, 132-140`; `severity_tier.py:67-69,
  114-125, 143-151`; `draft.py:264-266, 302-304, 331-343`;
  `orchestrator.py:201-205, 562-608, 611-623, 648-682`; `spec.py:522,
  840`; `governance_pin.py:42-88, 57`; `registry.py:30`;
  `runs.py:377-396` (API router); `hero_demo/run.py:275-290, 278,
  359-369`; `hero_demo/governance_audit.py:140-165`;
  `verticals/procurement/procedures.yaml:39, 62-77, 233-236, 241-244,
  293-297`; `verticals/supply_chain/procedures.yaml:28, 43, 61-76,
  290-304`; `cold_chain_assess.py:71`;
  `tests/services/db/test_procurement_sod_gate.py:372-377, 405-430,
  433-454`; `test_doa_tier.py:136-138`; `test_severity_tier.py:140-141`
- Code anchors verified by Code at R2 (2026-07-15, same baseline; these
  two files were outside the drafting snapshot):
  `services/engine/actions.py:61-66` (`GovernedDecision.principal_id:
  str` required, non-nullable, `extra="forbid"` — the SD-6(b) pricing);
  `services/engine/procedures/runs.py:110` (engine-side
  `StepResult.audit` JSONB — the SD-2(a) persistence substrate)
