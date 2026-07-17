# PLAN-0081: The building_materials governed-credit HERO (build)

**Status:** Draft — SD-A/SD-B/SD-C/SD-D **RESOLVED (Cray, s146)**: SD-A/SD-B
proceed-with-GUESS as proposed; SD-C = stays-deferred (re-arm AT-2 marker at
N=4); **SD-D = (a) — Cray OVERRODE the drafter's (b) recommendation: the
shared/core `Person` extraction lands IN THIS PLAN** (a conscious
scope-expanding override, chosen with the blast-radius framing in view).
Still open: **SD-E** (the shared-`Person` placement) + **OQ-1** (whether
closing ADR-0026 OQ-6 warrants an ADR-0026 amendment) — below.
**Owner:** Claude Code (execution) · Cray (SD-E adjudication + ratification)
**Created:** 2026-07-18
**Related ADRs:** ADR-0032 (D1 wedge / D6 AT-2 cost class), ADR-0025 (D2/D3
typed AT-2 content; D7 re-trigger — the obligation this PLAN pays), ADR-0026
(SoD run-check + principals; OQ-6 Person deferral), ADR-0031 (D3 seam map;
D4.2 own-PLAN rule), ADR-016 (per-entity `threshold_field` FKP band), ADR-0015
(D2 Tier-1 Mirror — the shipped starting state), ADR-006 (D4 Rule of Three),
ADR-0007 (approve→execute gate). Related PLANs: **PLAN-0079** (the tracking
mandate this PLAN executes — read it first), PLAN-0076 (gate-seam tracker; its
T1 trigger is MET by this build, see Step 8), PLAN-0074/0075 (the 2nd AT-2
signature + tier-authority enforcement, reused), PLAN-0077 (SD-8 row-local
wall, honored), PLAN-0078 (declared-transform precedent, mirrored), PLAN-0062
(executor-factory wiring pattern), PLAN-0068 (per-entity band exemplar).

> **Mandate.** PLAN-0079 Step T1 fired this session: Cray commissioned the
> hero (AskUserQuestion, s146) and resolved SD-1 (**trip N=3 in-PLAN — do not
> wait for PLAN-0076 T1**) and SD-2 (**ride the existing `measured_value`
> exposure field — no aggregation, no new field**). Those two adjudications
> are LOCKED inputs here, not re-litigated. PLAN-0079's 3-part spine
> (`0079:115-127`), coordination points (`0079:128-141`) and honest-cost
> framing govern this PLAN's shape. **Also LOCKED (Cray, s146, this PLAN's
> own SD round):** SD-A/SD-B GUESS values proceed as proposed; SD-C = the D7
> deferral stays (AT-2 marker re-arms at N=4); SD-D = (a), the shared/core
> `Person` extraction is IN scope here and CLOSES the ADR-0026 OQ-6 deferral
> (the Person marker TRANSFORMS — it does not re-arm).

## Goal

Build the `building_materials` **governed-credit HERO**: a runnable, offline-
deterministic AT-2 procedure over the shipped Tier-1 Mirror (#765) in which a
trade customer's outstanding credit exposure (the event stream's
`measured_value`, THB) breaches ABOVE the account's own `credit_limit_thb`,
and the release decision runs the full governed spine — **(a)** a
deterministic per-entity exposure band, **(b)** a hard credit-compliance
`rule_gate` (KYC / overdue-AR / blacklist), **(c)** a `doa_tier` human
approval with SoD (sales REQUESTS, credit-control APPROVES) and the engine
audit — using the shipped machinery unchanged (`DoaLadder` `spec.py:958`,
`resolve_doa_tier` `doa_tier.py:95`, `check_tier_authority`
`tier_authority.py:125`). The build consciously pays the hero's true cost
(ADR-0032 D6: never a config-cost item): it is **AT-2 signature #3**, so it
trips the ADR-0025 D7 re-trigger marker and performs the D7 re-evaluation
**in this PLAN** (Step 8 — verdict Cray-ratified: stays deferred, re-arm at
N=4), and — found on verification this session — it is also the **3rd
principal-bearing vertical**, tripping the ADR-0026 OQ-6 Person-extraction
marker. Per Cray's SD-D=(a) override, this PLAN therefore **also extracts
the shared/core `Person` home and migrates all three principal-bearing
verticals (procurement, supply_chain, building_materials) onto it** (Step
9), closing the OQ-6 deferral under ADR-006 D4 Rule of Three. All authored
numbers are demo GUESSES marked "GUESS — รอแก้" (ADR-0032 D1
guess-then-react discipline).

## Current state (verified on `main` 7e34913, 2026-07-17/18)

- `verticals/building_materials/` is a Tier-1 Mirror: ontology
  (`ontology/building_materials_v0.yaml`) + synthetic adapter + a no-op
  `echo` handler stub (`handlers.py:16`) + `generated/` — **no
  `procedures.yaml`, no `procedures_factory.py`** (`services/api/main.py:131-134`
  docstring confirms the mirror registers no executor factory).
- The exposure field ALREADY exists: `OperationalEvent.measured_value`
  (`building_materials_v0.yaml:88-90` — "Current outstanding credit exposure
  (open AR + this order), THB"). The per-account ceiling ALREADY exists:
  `credit_limit_thb` (`:36-41`, a per-entity `threshold_field` band, marked
  "GUESS — รอแก้"). The synthetic timeline already carries the demo beat:
  baseline 250,000 THB then a breach reading of **550,000 THB vs a 500,000
  limit** (`data_adapter/synthetic.py:34-44,61-71`). The adapter wires
  `OperationalEvent` through the real-time anchor
  (`data_adapter/__init__.py:36-42`).
- The `doa_tier` gate reads a FLAT `amount`/`currency` off its input entity
  and **fails closed** otherwise (`governance_step.py:47-57`, `_spend()`).
  Exposure arrives as `measured_value` — hence the reshape seam (Step 4).
- AT-2 is N=2 (`spec.py:822-831`, post-#767); the re-trigger marker re-arms at
  N=3 (`tests/services/engine/procedures/test_at2_signature_retrigger.py:81`
  `_RETRIGGER_N = 3`; the count assertion `:213` **and** the baseline-equality
  assertion `:208` — both fire on a new signature).
- Principal identity is N=2 (`test_principal_identity_retrigger.py:49`
  baseline `["procurement", "supply_chain"]`; re-armed at N=3, `:43,:80`).
- **The principal-identity anatomy the Step-9 extraction operates on
  (verified this session — what is ALREADY shared vs what is per-vertical):**
  the `Person` TYPE, its validators, the YAML parse, the SoD run-check, and
  the API-side principal index are already engine-core —
  `services/engine/procedures/spec.py:1359` (`class Person`), `:1660`
  (`ProceduresSpec.principals`), `:1678-1695` (validators), `:1789` (parse);
  `services/engine/procedures/principal_sod.py` (`check_principal_sod`);
  `services/api/auth.py:49` (`_principal_index(vertical)`). What is
  PER-VERTICAL (the hand-copied pattern the OQ-6 marker counts) is the
  roster homes + wiring: `verticals/procurement/procedures.yaml:64`
  (`principals:`) **plus a SECOND procurement roster source** —
  `person.csv` via `load_fastenal_principals`
  (`verticals/procurement/hero_demo/procedure.py:70-74`) — and the
  `hero_demo/run.py` wiring (`:347-358,:380-382,:542-550,:666,:738-749`);
  `verticals/supply_chain/procedures.yaml:63-84` (`principals:`) + its
  factory wiring (`procedures_factory.py:272,295`).
- No DB work: only energy has a committed ORM; this mirror is in-memory
  synthetic. No ontology change → no regen, no migration (unless SD-E
  resolves to the ontology-layer placement — see SD-E).

## Acceptance Criteria

Each AC carries a pre-committed pass/fail read. Test artifacts are **landed
by Code at build time** (this drafter cannot write `tests/`), per the
PLAN-0079 AC-2 precedent.

- [ ] **AC-1 — the 3-part spine ships, all three, or the PR does not merge.**
  Pass/fail read: `load_procedures("building_materials")` returns the hero
  procedure whose steps carry (a) an `evaluate` band with
  `threshold_field: credit_limit_thb`, `direction: above`; (b) a
  `governance_content: {kind: rule_gate}` compliance step upstream of the
  authority gate; (c) a `governance_content: {kind: doa_tier}` gated action
  plus a `separation_of_duties` constraint binding requester ≠ approver.
  Code lands a guard test asserting exactly this composition (gate-kind
  tuple `("rule_gate", "doa_tier")` read off typed `governance_content`).
  Fails if any leg is missing — a ladder-only form is the hollow-governance
  shape PLAN-0079 forbids (`0079:115-123`).
- [ ] **AC-2 — the reshape seam resolves the DOA tier (the L-2 seam,
  first-class).** Pass/fail read: an in-memory `run_procedure` over the
  synthetic data reaches the `doa_tier` gate with `amount` equal to the
  breach event's `measured_value` (550,000, Decimal-exact via the
  string-coerce) and `currency: "THB"`, and the run suspends
  `waiting_human` at the approve step — no `DoaTierError`. Code lands the
  test. Fails if the gate fail-closes on the shipped happy path or if the
  amount is not byte-derived from `measured_value`.
- [ ] **AC-3 — fail-closed is untouched; the engine diff is bounded to the
  two NAMED scopes.** Pass/fail read: the PR's diff under
  `services/engine/` (and `services/api/auth.py`, if the principal-index
  seam moves) touches **only** (i) the additive `ComplianceCriterion` enum
  block in `spec.py` (Step 2) and (ii) the shared-`Person` extraction
  scope per the SD-E-ratified placement (Step 9 — the `Person`/roster home
  + its loading/index seam). **No change** to `_spend()`,
  `resolve_doa_tier`, `check_tier_authority`, `evaluate_compliance`, or
  `ComplianceRule.blocks_po`, and no change to the SoD fail-closed
  SEMANTICS (`check_principal_sod`'s verdict behavior is preserved even if
  its roster source moves). A non-breach / non-reshaped entity still
  raises `DoaTierError`. *Honest flag (SD-D=(a) consequence): this widens
  the diff well beyond the original "one additive enum block" shape — the
  bound is now these two named scopes, verified at R2 by diff inspection.*
- [ ] **AC-4 — the executor factory is wired (coordination point i).**
  Pass/fail read: `verticals/building_materials/procedures_factory.py`
  exists; `services/api/main.py` gains a lazy
  `_register_building_materials_executors` registrar + a
  `_PROCEDURE_EXECUTOR_REGISTRARS["building_materials"]` entry, and the
  `:131-134` docstring drops building_materials from the mirrors list. Code
  lands a test (PLAN-0062 AC-5 pattern) asserting
  `registry.get_procedure_executors("building_materials")` succeeds after
  the registrar runs — the 409-at-resolve failure mode is covered.
- [ ] **AC-5 — SoD + tier authority are demonstrably enforced.** Pass/fail
  read: Code lands tests asserting (i) gate-resolve by the requesting
  sales principal fails closed (SoD, ADR-0026 D4); (ii) the tier's own
  approver resolves; (iii) a SENIOR principal approves a lower-tier
  exposure via cumulative roles (PLAN-0075 Policy B — roles authored
  cumulatively in the YAML, mirroring `supply_chain/procedures.yaml:63-84`).
- [ ] **AC-6 — the D7 re-evaluation is performed and recorded (Step 8), and
  the marker is honestly re-pointed.** Pass/fail read:
  `test_at2_signature_retrigger.py` is updated in the same PR — the new
  signature added to `_BASELINE_SIGNATURES`, `_RETRIGGER_N` re-armed at
  **4** (the SD-C verdict, Cray-ratified s146: stays-deferred), and the
  module docstring carries the N=3 re-evaluation record mirroring the N=2
  record's form (argument + verdict + what generalised). Fails if the
  marker is silently bumped without the recorded argument, or if CI merges
  RED.
- [ ] **AC-7 — the OQ-6 Person marker TRANSFORMS (Step 9, SD-D=(a)): the
  deferral is CLOSED, not re-deferred.** Pass/fail read: Code lands the
  marker transformation — `test_principal_identity_retrigger.py` changes
  FROM a "FAIL when an Nth vertical ships a per-vertical `Person`"
  re-trigger INTO an assertion that the shared/core `Person` home **is the
  one used across all principal-bearing verticals** (no re-arm at N=4; a
  future vertical adding principals onto the shared home is the INTENDED
  state, and a regression REINTRODUCING a per-vertical roster home fails).
  The module docstring preserves the honest lineage: the N=2 firing was
  answered (per-vertical re-confirmed + follow-on filed, PLAN-0074 AC-12),
  and at N=3 the extraction was **PERFORMED** (this PLAN; ADR-006 D4
  satisfied). Fails if the baseline is merely extended/re-armed, or if the
  lineage record is dropped.
- [ ] **AC-8 — the endpoint coordination points are consciously re-pointed
  (ii + iii).** Pass/fail read: in the same PR,
  `tests/api/test_procedures_endpoint.py` `_EXPECTED` gains
  `building_materials: {<hero_id>: "AT-2"}`; the count pin `:113` bumps
  `9 → 10`; the spec-less guard `:116-140` is **re-pointed, not deleted**
  — via the fixture route its own comment names (`:131`), because after
  this build **zero discovered spec-less verticals remain** (`vet_clinic/`
  is a README-only parked directory that `discover_and_register` cannot
  import — `services/engine/discovery.py:67-68` requires `data_adapter` +
  `handlers`). CI green at merge.
- [ ] **AC-9 — demo discipline (ADR-0032 D1).** Pass/fail read: every
  authored number (ladder tiers, compliance thresholds, principal roster)
  carries a "GUESS — รอแก้" marking in the YAML comments; the whole build
  is deterministic-offline (no MS-S1, no host-state, no DB); the LLM
  appears only as `llm_assist` advisory prose.
- [ ] **AC-10 — PLAN-0079 retires on its own T3 terms.** Pass/fail read: in
  the PR that completes this build, PLAN-0079 moves to `docs/plans/done/`,
  its guard test
  (`tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py`
  — exists on `main`, verified) is deleted **in that same PR**, and the
  STATUS PLAN-0079 pointer retires in the same motion (`0079:228-233`).
  This PLAN itself archives to `done/` per the normal Plan Flow.
- [ ] **AC-11 — the two existing verticals migrate onto the shared `Person`
  home with behavior preserved (the SD-D=(a) blast radius, pinned).**
  Pass/fail read: procurement + supply_chain resolve their principals from
  the shared home; procurement's **dual roster source is unified** (the
  `procedures.yaml:64` block vs `person.csv` via `load_fastenal_principals`,
  `hero_demo/procedure.py:70-74` — one canonical source remains, the other
  becomes a pointer or is retired); `verticals/supply_chain/procedures_factory.py:272,295`
  and `services/api/auth.py:49` read the shared seam. Every existing
  SoD / tier-authority / gate-resolve test passes **unmodified in its
  assertions** (roster-source plumbing may change; verdicts may not). Fails
  if any existing governance verdict changes, or if a per-vertical roster
  home survives alongside the shared one.

## Out of Scope

- ❌ **The transform-grammar aggregation extension** (PLAN-0079 SD-2 option
  (c)) — the PLAN-0077 SD-8 row-local wall is RATIFIED
  (`done/0077-transform-grammar-build.md:558-577`); exposure rides the
  existing `measured_value` field, period (Cray, s146). If build reality
  contradicts this, that is the SD-8 Tripwire path (surface for an ADR-0031
  row amendment) — never an in-PLAN invention.
- ❌ **Any change to `ComplianceRule.blocks_po`** or any other
  bypass-unrepresentable invariant (`spec.py:813-816`). The
  `ComplianceCriterion` enum grows ADDITIVELY only (its own docstring's
  contract, `spec.py:852-860`).
- ❌ **Writing test files by this drafter** — Code lands every test named in
  the ACs at commit time (PLAN-0079 AC-2 precedent).
- ❌ **A new `current_exposure_thb` field, ontology edits, codegen re-runs,
  or DB migrations** — L-2 rides existing fields; the mirror is in-memory.
- ❌ **Schedule- / event-triggered variants** — `trigger: manual` only
  (the PLAN-0019 L-1 precedent all four exemplar verticals follow). No
  `Schedule.owning_person_id` / headless-SoD surface is entered.
- ❌ **Building the AT-2 generator or the ADR-0031 D3 gate-plugin seam** —
  Step 8 *records* the D7 verdict; the extraction itself is PLAN-0076 T1
  territory and PLAN-0076's scope is not reassigned (`0079:137-141`).
- ❌ **Cross-vertical identity SEMANTICS beyond what the extraction needs**
  — the shared `Person` extraction (Step 9, IN scope per SD-D=(a)) unifies
  the roster HOME and its loading/index seam; it does NOT introduce
  cross-vertical SoD comparison, cross-vertical role semantics, or any
  alias-collapse rule change (ADR-0026 OQ-3=(c) stands untouched). The
  three rosters remain per-org demo DATA — different humans per vertical.
- ❌ **UI changes** — the generic `GET /procedures` viewer + OCT monitor
  surfaces the new procedure with zero UI work; none is scoped.
- ❌ **Re-litigating PLAN-0079's L-1/L-2 (SD-1/SD-2)** — Cray-ratified s146.

## Steps

### Step 1: Preflight — verify the anchors, branch, confirm both markers green
On a feature branch off current `main`: confirm `spec.py:822-831` still
records N=2; both re-trigger markers green pre-change
(`test_at2_signature_retrigger.py`, `test_principal_identity_retrigger.py`);
the count pin still `total == 9`; the spec-less guard still passing on
building_materials. Any drift → correct this PLAN's citations in the same PR
(symbols are the stable reference; PLAN-0079 T2 discipline).

### Step 2: Extend `ComplianceCriterion` with the credit block (the ONLY engine edit)
Add the credit-compliance criteria as a third instance-scoped block in
`spec.py` (`:852-872`), mirroring how PLAN-0074 added the GDP block —
additive, commented as building_materials' block. Proposed members (SD-A —
GUESS content, Cray sanity-checks): `kyc` (KYC/identity verification on file
and current), `overdue_ar` (no invoice past due beyond terms + grace), and
`blacklist` (account not suspended / not on the credit blacklist). Rationale
recorded in the enum comment: the N=2 finding — the GATE generalises, the
criterion vocabulary never does (`spec.py:856-860`) — predicts exactly this
kind of growth.

### Step 3: Author the spine part (a) — intake + the per-entity exposure band
Create `verticals/building_materials/procedures.yaml` (namespace, agent,
procedure skeleton; principals arrive in Step 5). The intake `query` step
reads the latest `OperationalEvent` reading per `CustomerAccount` via the
`event_for_account` link with an FK-parent join bringing `credit_limit_thb`
onto the reading (the aquaculture pattern, `aquaculture/procedures.yaml:64-90`
incl. the `site_id` projection-rename for the declared collision — both
objects carry `site_id`). The `judge` `evaluate` step bands each account
against ITS OWN limit: `threshold_field: credit_limit_thb`,
`direction: above` (`aquaculture/procedures.yaml:102` analog; the shipped
`supply_chain` `temp_ceiling` band is the `above`-direction exemplar,
`supply_chain/procedures.yaml:128-129`). Facets per ADR-016 D2 (typed
`decision_condition`; prose non-authoritative). Agent:
`autonomy_ceiling: gated`, `step_kinds: [query, evaluate, action, transform]`
(`transform` in the allowlist per the PLAN-0078 PR-2 precedent,
`supply_chain/procedures.yaml:45-47`).

### Step 4: The `measured_value` → `amount`/`currency` reshape (the L-2 seam, first-class)
A declared `transform` step over the breach subset (`from: judge, where:
{verdict: breach}`) — the enrich/derive path, NOT a bespoke executor —
supplying exactly what the downstream gates read and nothing more:

- `derive: {target: amount, expr: {field: measured_value}}` — the identity
  derive is shipped grammar (`procurement/procedures.yaml:144` precedent);
- `default: {target: currency, value: THB}` (the ontology's `unit` is
  already THB, but the gate contract wants the flat `currency` key —
  `governance_step.py:53-57`);
- `default: {target: compliance, value: {kyc: true, overdue_ar: true,
  blacklist: true}}` — the per-criterion signal map the `rule_gate` executor
  reads (the `supply_chain/procedures.yaml:236-241` precedent), GUESS-marked;
- `coerce: {target: amount, to: string}` so `Decimal(str(...))` is exact on
  the authority threshold (the PLAN-0078 byte-form discipline).

Why this shape is load-bearing: `_spend()` fails CLOSED without flat
`amount`/`currency` (`governance_step.py:47-57`) — this step is the entire
bridge between "exposure as a monitored reading" and "exposure as a governed
spend". Row-local throughout; the SD-8 wall is never approached.

### Step 5: Spine parts (b) + (c) — `rule_gate`, `doa_tier`, SoD, principals
- **(b)** `credit_gate` (`evaluate`, `governance_content: {kind: rule_gate}`)
  with the Step-2 criteria — band-less by design; any failed criterion
  blocks (`blocks_po` is `Literal[True]`, `spec.py:815` — bypass
  unrepresentable). Mirrors `supply_chain/procedures.yaml:359-389`.
- **(c)** `approve` (gated `action`, `governance_content: {kind: doa_tier}`)
  fed `from: credit_gate, where: {compliant: true}`. Proposed ladder (SD-B —
  GUESS, Cray-ratifiable; procurement's 4-tier THB form,
  `procurement/procedures.yaml:300-307`, re-priced for credit):
  `0 → จนท.เครดิต`, `250000 → ผจก.ควบคุมเครดิต`, `1000000 → ผอ.ฝ่ายการเงิน`
  (the shipped 550,000-THB breach lands mid-ladder — the demo shows tiering,
  not always-the-top). Routes on the FULL exposure, not the overage (SD-B
  names this sub-choice).
- **SoD + principals:** `separation_of_duties: distinct_steps [intake,
  approve]` with `required_roles` intake→`requester`, approve→`approver`
  (`supply_chain/procedures.yaml:460-465` form). Principals roster (SD-A/B
  — GUESS): one sales requester + three credit approvers with CUMULATIVE
  roles so a senior approves downward (PLAN-0075 Policy B,
  `supply_chain/procedures.yaml:63-84` form).
- A terminal gated `fulfill` step writes the approved decision via a no-op
  receipt handler (ADR-0007 approve→execute stays the only write path).

### Step 6: Handlers + executor factory + `main.py` wiring (coordination point i)
Extend `handlers.py` with no-op receipt stubs for the ontology
`RecommendedAction.action_type` vocabulary used by the procedure (e.g.
`escalate`, `approve_credit_override` — `building_materials_v0.yaml:137-139`),
registered alongside `echo`. Author
`verticals/building_materials/procedures_factory.py` on the supply_chain
template (`procedures_factory.py:255-303`): `QueryStepRouter` +
`GovernanceEvaluateExecutor(base=…)` + `GovernanceActionExecutor(base=…)` +
`TransformStepExecutor`, with the SoD principal index. Add the lazy registrar
+ dict entry in `services/api/main.py:125-134` and update its docstring
(building_materials leaves the mirrors list). Without this a fired run 409s
at gate-resolve (PLAN-0062; the `run-firing-entrypoint` lesson).

### Step 7: Re-point the endpoint coordination points (ii + iii)
In the SAME PR (these are RED-by-design transitions — CI is RED between the
YAML landing and this step, so they land together): `_EXPECTED` gains the
hero (`test_procedures_endpoint.py:28-46`); `returned == set(_EXPECTED)`
(`:96`) follows automatically; the count pin `total == 9 → 10` (`:113`,
bump the stale "eight/nine" prose comments consciously); the #765 spec-less
guard (`:116-140`) re-points via a FIXTURE (its `:131` alternative) — e.g. a
tmp-path scaffolded spec-less vertical registered for the test — because no
discovered spec-less vertical remains (see AC-8; `vet_clinic/` is
README-only and non-discoverable, `discovery.py:67-68`). Do NOT delete the
guard: the skip path it protects stays live code.

### Step 8: The ADR-0025 D7 re-evaluation at N=3 (first-class — the cost of the hero)
The new signature `("building_materials", ("rule_gate", "doa_tier"),
<enum surface>)` breaks BOTH marker assertions
(`test_at2_signature_retrigger.py:208` baseline-equality, `:213` count).
Perform the D7 re-evaluation as a conscious re-decision, recorded in the
marker's module docstring in the N=2 record's form, and in this PLAN's
closeout:

- **The argument FOR extraction:** N=3 is Rule-of-Three's own trigger
  (ADR-006 D4); three hand-authored governance shapes now ship; the marker's
  own failure text says "extract … or re-argue the deferral in a follow-on
  ADR" (`:213-223`).
- **The argument FOR stays-deferred (Code's recommendation — SD-C, Cray's
  verdict):** D7's recorded N=2 answer — "N>=2 PERMITS genericization, it
  does not mandate it" (`spec.py:826-829`) — and this 3rd signature is the
  WEAKEST possible extraction datum: it introduces no new gate kind, no new
  authority quantity (the money `DoaLadder` is REUSED unchanged, THB and
  all), and grows only the criterion vocabulary — the exact axis the N=2
  finding already established as per-instance forever. What it DOES do is
  fire PLAN-0076 T1's own named trigger ("a third AT-2 signature fires the
  N=3 re-trigger marker", `0076:299-304`) — so the extraction question has a
  live owner and does not need this PLAN to answer it.
- **Mechanics either way:** extend `_BASELINE_SIGNATURES` with the recorded
  argument; re-arm `_RETRIGGER_N` (→ 4 if stays-deferred); never a silent
  bump (`:208-212`: "Re-argue it (do not just update this list)").
- **Record in the closeout** that PLAN-0076 T1's trigger condition is now
  MET; PLAN-0076's own process owns the seam-PLAN opening (scope not
  reassigned, `0079:137-141`).

### Step 9: Extract the shared/core `Person` home + migrate all three verticals (SD-D=(a), Cray s146 — the scope-expanding override)
Shipping `principals:` (unavoidable — SoD + `doa_tier` gate-resolve require
resolvable `Person`s, ADR-0026 D4 / the RF-1 finding) makes
building_materials the THIRD principal-bearing vertical, firing
`test_principal_identity_retrigger.py` (`:71` baseline, `:80` N=3 — whose
failure text says the shared-`Person` extraction "is due, not deferrable").
**Cray chose to pay that debt HERE** — after seeing the blast-radius
framing (this couples an identity refactor to the hero build; the shape
PLAN-0074 SD-4 avoided at N=2) — so ADR-006 D4 Rule of Three is satisfied
by EXTRACTION, not by another recorded deferral. This marker was NOT in
the dispatch's four coordination points — it is coordination point (v).
Sub-steps:

- **9a — Build the shared/core home** at the SD-E-ratified placement
  (Cray adjudicates SD-E before this step executes). What is genuinely
  left to extract (the verified anatomy, Current state above): the TYPE +
  validators + parse + SoD check + API index are ALREADY engine-core; the
  per-vertical copies are the roster HOMES and their loading/index wiring.
  The extraction therefore delivers: one canonical roster home per
  vertical's identities on a SHARED loading/index seam (one core function
  all consumers use), with per-vertical role bindings intact.
- **9b — Migrate the two existing verticals** (the AC-11 touch-points, all
  verified on disk): procurement — the `procedures.yaml:64` `principals:`
  block AND the second roster source (`person.csv` via
  `load_fastenal_principals`, `hero_demo/procedure.py:70-74`) unify into
  the canonical home; re-point the `hero_demo/run.py` wiring
  (`:347-358,:380-382,:542-550,:666,:738-749`). supply_chain — the
  `procedures.yaml:63-84` block + the factory wiring
  (`procedures_factory.py:272,295`). Plus `services/api/auth.py:49`
  (`_principal_index`) if the seam moves. Behavior bar: AC-11 — verdicts
  unchanged, existing test assertions unmodified. building_materials'
  roster (Step 5) lands directly on the shared home (Code may sequence 9a
  before Step 5 to avoid authoring-then-migrating; the end-state is what
  the ACs pin, not the intra-branch order).
- **9c — Transform the marker** (AC-7): from the N-count re-trigger into
  the shared-home assertion; preserve the honest lineage in the docstring
  (N=2 answered per PLAN-0074 AC-12; N=3 extraction PERFORMED by this
  PLAN). The OQ-6 deferral is **CLOSED** — no re-arm.
- **9d — Surface, do not decide (OQ-1 below):** OQ-6 was an ADR-0026 open
  question resolved "(b) per-vertical + re-trigger" (`0026:116`);
  resolving it now by extraction may warrant an ADR-0026 amendment (the
  ADR-0022/ADR-016 in-place-amendment precedent) or a recorded note.
  Cray decides at R2/ratification; the PLAN only flags it.

### Step 10: Offline verification + closeout
Full offline suite green (all Code-landed AC tests + the re-pointed
coordination tests + the re-armed AT-2 marker + the TRANSFORMED Person
marker + the AC-11 migration bar). In-memory `run_procedure`
evidence for AC-2/AC-5 paths. No live/host-state run is required or scoped
(CLAUDE.md §8) — any live OCT demo smoke is separate Cray-gated evidence,
not this PLAN's gate. Then AC-10 bookkeeping: PLAN-0079 → `done/` + its
guard test deleted + STATUS pointer retired, all in the completing PR; this
PLAN archives per Plan Flow.

## Verification

The offline oracle is the gate: `pytest` fully green on the PR head with
every AC's named assertion present — the spine-composition guard (AC-1), the
reshape run-path test (AC-2), the engine-diff scope check (AC-3), the
factory-registration test (AC-4), the SoD/tier-authority triple (AC-5), the
re-armed AT-2 marker with its recorded re-evaluation (AC-6), the TRANSFORMED
Person marker with its preserved lineage (AC-7), the re-pointed endpoint
pins (AC-8), grep-level GUESS-marking (AC-9), and the migration
behavior-preservation bar (AC-11 — existing governance test assertions
unmodified). CI RED states are expected only INTRA-branch (between Steps
3–9); the merged PR is green.

## Surfaced Decisions

**Resolved (Cray, s146) — recorded verdicts, no longer open:**

- **SD-A — RESOLVED = proceed-with-GUESS as proposed** (ADR-0032 D1
  guess-then-react): criteria `{kyc, overdue_ar, blacklist}` (Step 2
  definitions); compliance signals default-true GUESSES in the reshape step
  (the supply_chain precedent); the existing 500,000-limit /
  550,000-breach data kept; the second-account-fails-a-criterion demo
  option approved as pure adapter data. Everything stays clearly marked
  "GUESS — รอแก้", Cray-correctable at the demo.
- **SD-B — RESOLVED = proceed-with-GUESS as proposed:**
  `0 → จนท.เครดิต / 250,000 → ผจก.ควบคุมเครดิต / 1,000,000 → ผอ.ฝ่ายการเงิน`,
  THB, cumulative senior roles, routing on the **FULL exposure** (not the
  over-limit increment).
- **SD-C — RESOLVED = as-recommended: the D7 deferral STAYS; re-arm the
  AT-2 marker at N=4** (Step 8). Recorded argument: the 3rd signature adds
  no new gate kind / authority quantity (doa_tier/THB reused unchanged),
  grows only the criterion vocabulary (the axis the N=2 finding already
  established as per-instance); PLAN-0076 T1's trigger is now met and owns
  the extraction question.
- **SD-D — RESOLVED = (a), OVERRIDING the drafter's (b) recommendation:
  extract the shared/core `Person` IN THIS PLAN** (Step 9). Cray chose (a)
  with the blast-radius framing in view ("heaviest — couples an identity
  refactor to the hero; PLAN-0074 SD-4 avoided exactly this") — a
  conscious scope expansion, honestly rendered: AC-3's engine-diff bound
  widened, AC-11 added to pin the migration behavior bar, and the OQ-6
  marker transforms (deferral CLOSED) instead of re-arming.

**Still open (Cray adjudication — recommended, not decided):**

- **SD-E — WHERE the shared/core `Person` home lands** (gates Step 9a; not
  determinable from precedent — there is no prior N=3 extraction in the
  repo, and ADR-0026's own text points two ways: `:95` "at the ontology
  layer" vs the shipped implementation's spec-layer `Person`,
  `spec.py:1359-1365` "Lives in the procedures spec layer"). Options:
  **(a) engine-core spec-layer module** — a canonical shared roster home +
  one core loading/index function (e.g. beside `principal_sod.py`), with
  each vertical's `procedures.yaml` keeping its role bindings; lightest,
  honors the verified anatomy (type/validators/check already core), no
  codegen touch. **(b) ontology-layer promotion** — `Person` becomes an
  ADR-0008 shared object_type; matches ADR-0026 `:95`'s "ontology layer"
  phrasing + the Implementation-Notes `:157` "ontology object (ADR-0008
  grammar)" wording, but touches codegen + contradicts the shipped
  spec-layer placement, and would drag `generated/` re-runs into scope.
  **(c) a shared top-level rosters file** (one YAML for all verticals'
  principals) — maximal unification, but merges genuinely per-org demo
  DATA and inflates every vertical's identity blast radius. **Code
  recommendation: (a)** — it extracts the PATTERN (the thing the marker
  counts) while leaving per-org data per-vertical; (b) is re-decidable
  later without waste if a real cross-vertical identity consumer appears.
  Why Cray: it is the identity-model placement ADR-0026 OQ-6 called "a
  strategic scope call", now being answered for real.

## Open questions (surfaced, not decided)

- **OQ-1 — does closing ADR-0026 OQ-6 by extraction warrant an ADR-0026
  amendment?** OQ-6 was resolved "(b) per-vertical + enforceable
  re-trigger" in the Accepted ADR (`0026:116`); this PLAN resolves the
  re-trigger's own escalation by PERFORMING the extraction. Options: an
  in-place ADR-0026 amendment (the ADR-0022 / ADR-016 precedent — note
  that an Accepted-ADR body edit is G1-gated: plan-drafter authors, Code
  commits, ratified in ONE pass), or a recorded note in this PLAN's
  closeout + the marker docstring only. Cray decides at R2/ratification.

## References

- **PLAN-0079** (`docs/plans/0079-building-materials-governed-credit-hero-tracking.md`)
  — the mandate: spine `:115-127`, coordination points `:128-141`,
  SD-1/SD-2/SD-3 `:246-263`, T3 retirement `:228-233`.
- **PLAN-0076** (`docs/plans/0076-…md:299-304`) — T1 trigger list naming the
  3rd-signature firing condition.
- **ADR-0026** (`docs/adr/0026-principal-identity-run-enforcement.md`) —
  OQ-6 resolution "(b) per-vertical + enforceable re-trigger" `:116`; the
  "ontology layer" tension `:95` vs Implementation Notes `:157` (the SD-E
  fork); the s132 tier-authority amendment `:170-174`.
- Step-9 / SD-E anchors (all verified on disk this session):
  `services/engine/procedures/spec.py:1340-1356` (`PrincipalAlias`),
  `:1359-1378` (`class Person` — "Lives in the procedures spec layer"),
  `:1660-1668` (`ProceduresSpec.principals`), `:1678-1695` (validators),
  `:1789` (parse); `services/engine/procedures/principal_sod.py`
  (`check_principal_sod`); `services/api/auth.py:49`
  (`_principal_index(vertical) -> dict[str, Person]`);
  `verticals/procurement/procedures.yaml:64` (`principals:`), `:93`
  (`service_principals:`);
  `verticals/procurement/hero_demo/procedure.py:70-74`
  (`load_fastenal_principals` — the second procurement roster source);
  `verticals/procurement/hero_demo/run.py:347-358,380-382,542-550,666,738-749`
  (principal wiring); `verticals/supply_chain/procedures_factory.py:272,295`.
- Code anchors (all verified on disk this session):
  `verticals/building_materials/ontology/building_materials_v0.yaml:36-41,88-90`;
  `verticals/building_materials/data_adapter/synthetic.py:34-44,61-71`;
  `verticals/building_materials/data_adapter/__init__.py:36-42`;
  `verticals/building_materials/handlers.py:16`;
  `services/engine/procedures/governance_step.py:47-57`;
  `services/engine/procedures/spec.py:813-816,822-831,852-872,958`;
  `services/engine/procedures/doa_tier.py:95`;
  `services/engine/procedures/tier_authority.py:125`;
  `services/engine/procedures/orchestrator.py:659-666` (`_is_at2_procedure`);
  `services/engine/discovery.py:62-71`; `services/api/main.py:125-134`;
  `verticals/procurement/procedures.yaml:144,300-307`;
  `verticals/supply_chain/procedures.yaml:45-47,63-84,216-280,337-358,359-389,460-465`;
  `verticals/aquaculture/procedures.yaml:64-90,102`;
  `tests/api/test_procedures_endpoint.py:28-46,96,113,116-140`;
  `tests/services/engine/procedures/test_at2_signature_retrigger.py:81,86-115,208,213`;
  `tests/services/engine/procedures/test_principal_identity_retrigger.py:14-15,43,49,71,80`;
  `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py`
  (exists on `main` — the AC-10 deletion target).

---

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code, session 146, executing PLAN-0079 Step T1 on
> Cray's commissioning decision). Amended same session by the same drafter
> to fold in Cray's SD ratifications (SD-A/B proceed-with-GUESS; SD-C
> stays-deferred; **SD-D = (a) — Cray's override of the drafter's (b)
> recommendation**, expanding scope to the shared-`Person` extraction) and
> to surface SD-E + OQ-1. Independent review: Code (R2) at PR;
> ratification: Cray (SD-E + OQ-1 remain open above). Author≠reviewer
> separation: **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.
> Code fact-pack verified against `main` 7e34913 by Code; every line cited
> above re-read from disk by this drafter, 2026-07-17/18 — except the
> ADR-0026 s132 amendment range `:170-174`, read in partial context (start
> of the amendment section verified; its full extent unverified — Code
> spot-checks at R2).
