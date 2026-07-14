# PLAN-0074: AT-2 signature #2 — supply_chain cold-chain excursion DISPOSITION (governed request→approve→fulfill, non-money authority)

**Status:** Proposed — awaiting Cray ratification (SD-1..SD-4 adjudicated at review)
**Owner:** Claude Code (execution) · Cray (SD adjudication + ratification)
**Created:** 2026-07-14
**Related ADRs:** ADR-0025 (D2/D4/D5/D7/D8), ADR-0031 (D3 row-3 + row-1, D4.3, OQ-4), ADR-0026 (OQ-6), ADR-016 (OQ-A1 additive enum growth), ADR-006 (D4 Rule of Three), ADR-007 (approve→execute write gate, untouched)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code; session-130 direction by Cray). Independent
> review: Code (R2) at PR; ratification: Cray. Author≠reviewer separation:
> **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.

## Goal

Hand-author the **second AT-2 governed-procedure signature** (the governance-heavy
`request→approve→fulfill` archetype) on the **supply_chain** vertical — a
**cold-chain excursion disposition** procedure (a reefer breach of `temp_ceiling`
routes an *existing pharma cargo* to a governed disposition:
release-with-CoA / re-ice+expedite / quarantine+rework / destroy) — reaching
**N≥2** on the AT-2 shape (ADR-0025 D7 / ADR-0031 D3 row-3 "Path 2"). The second
instance deliberately presses seams procurement does not: the authority quantity
is **NON-MONEY** (a patient-safety / regulatory-severity tier — SD-1), which
`DoaLadder` cannot represent (money-typed by construction: `spec.py:625-627`
`currency` + `Decimal min_amount`), forcing a genuine **4th gate kind + new typed
content model**. The PLAN enumerates and closes **all ~8 gate-extension
coordination points** (three of which are silent governance holes — §Coordination
points), and **arms the ADR-0025 D7 CI marker this PLAN owns** (ADR-0031 OQ-4
resolution: "the PLAN that adds the 2nd AT-2 signature owns the marker").

## Context — LOCKED direction (Cray, session 130; do not re-litigate)

1. **Host vertical = supply_chain.** Disposition of an existing cargo — the run
   buys nothing. `scored_rule` selects an **action/disposition lane, not a
   supplier**; `rule_gate` is **GDP/GxP regulatory-quality** (stability budget /
   MKT, batch quarantine, licensed-disposal vendor, CoA/customs), not
   vendor-hygiene.
2. **Fork = ADD a 4th gate kind + a new typed content model** (the harder path,
   chosen over "reuse 3 kinds + widen enums"). The authority quantity is
   non-money; the exact quantity + model shape is **SD-1** (Cray confirms at
   review — Code's synthesis, veto-open).
3. **Moat tripwires (ADR-0031 D2) bind:** typed, closed, declaration-as-data —
   never eval/expression (tripwire 1), never an open worker StepKind (tripwire
   2), never free-string on a governed enum (tripwire 4). Additive enum growth
   only (ADR-016 OQ-A1).
4. **The generator stays AT-2-abstaining.** This PLAN never makes the generator
   emit the new kind (`_AT2_ONLY_KINDS` grows so the abstain guard covers it).
5. **Deterministic-offline acceptance** (fixtures / in-memory `run_procedure`);
   any MS-S1/live run is Cray-gated (CLAUDE.md §8). Money stays `Decimal`. The
   new content model stays **list/tuple-typed** (no set fields) or extends
   `governance_pin`'s explicit sorting (§Coordination points, hole 3).

**What supply_chain has today** (verified 2026-07-14, main=25238db): one AT-3
calm-path procedure (`cold_chain_excursion_sweep`,
`verticals/supply_chain/procedures.yaml` — query → in_file_band judge vs
per-cargo `temp_ceiling` → gated `hold`). No principals, no SoD, no AT-2 gate.
Its executor factory is already registered (`services/api/main.py:125-130`,
PLAN-0062 AC-5). The vertical is **in-memory synthetic** — no committed ORM, no
Alembic, no schema-parity, no NL-gold coupling: this PLAN is **YAML + engine
code + tests only, zero migration**.

## The procedure shape (design sketch — SD-1-contingent)

`cold_chain_excursion_disposition` (trigger: manual, v1):

| step | kind | gate | content |
|------|------|------|---------|
| `intake` | query | none | the excursion event + affected cargo batch (magnitude, duration, cargo stability budget, batch value-at-risk) |
| `assess` | action | `scored_rule` | selects the **disposition lane** from the four; stamps the derived authority quantity (severity) onto the entity (SD-2) |
| `gdp_gate` | evaluate | `rule_gate` | GDP/GxP compliance: extends `ComplianceCriterion` additively (e.g. `stability_budget`, `batch_quarantine`, `licensed_disposal_vendor`, `coa_customs`) |
| `approve` | action | **NEW 4th kind** (SD-1; working name `severity_tier`) | the non-money authority ladder: severity tier → approver role; SoD vs `intake` |
| `fulfill` | action (gated) | none | proposes the disposition action (ADR-007 envelope); no-op receipt handler stub; human go/no-go |

**N=2 triangulation finding (record, don't hide):** `ScoredRule`'s
`default_source: SourcePolicy` / `exception_policy: ExceptionPolicy` are
procurement-shaped. Reuse via **additive, instance-scoped members** (e.g.
`SourcePolicy += validated_lane`, `ExceptionPolicy +=
deviation_quarantine_logged`) per the `spec.py:514` / `scored_rule.py:51`
extension comments — and record which `ScoredRule` parts proved generic
(criteria+weights) vs vertical-scoped (source/exception policy) as input to the
future genericization PLAN (SD-3).

## Coordination points (the "≥4-edit pain" is really ~8 — ALL are ACs)

ADR-0031 D3 row-3 names 4; on-disk enumeration (verified) finds **~8**, three of
them **silent governance holes** (⚠). This list is the reference artifact the
future gate-seam PLAN consumes (no edit to Accepted ADR-0031's body — D4.4 fires
only when the seam itself lands).

1. `GateKind` member — `spec.py:200-211`.
2. New typed content model + `AT2Governance` union arm — `spec.py:703`.
3. Resolver module (pattern: `doa_tier.py:93`, `scored_rule.py:169`, `rule_gate.py:104`).
4. Run-side dispatch — `governance_step.py:134-139` (action; keys on **content
   type** via isinstance) + `:299-302` (evaluate).
5. ⚠ `draft.py:264` `_AT2_GATE_KINDS` — the obligation side keys on the
   **gate-kind enum** (`draft.py:280`), a mechanism parallel to #4. A new kind
   absent here owes NO `governance_content` → the run gate **silently accepts an
   empty gate**. Also `draft.py:328-338` `derive_procedure_governance_todo`
   hardcodes `DOA_TIER → separation_of_duties` — the new authority kind must be
   added (it needs SoD too). Note: **no `gate_kind→resolver` registry exists**
   (confirmed absent); correspondence is enforced only at run via `_is_filled`
   (`draft.py:312`) — see Step 1's load-time check.
6. ⚠ Prose-lint hole — `spec.py:981` `_at2_role_vocab` + `spec.py:994-1011`
   `_at2_free_text_surfaces` hardcode `isinstance(gc, DoaLadder | ScoredRule)`.
   A new content model's note/prose fields are **invisible to the ADR-0025 D4
   prose-lint** → a role/severity token could be smuggled into free-text.
7. ⚠ Run-pin determinism — `governance_pin.py:13-17` asserts AT-2 content types
   carry **no set-typed fields**; a set field silently breaks cross-process
   run-pin hash stability. Keep the new model list/tuple-typed (or extend the
   pin's explicit sorting).
8. `generator/pipeline.py:82` `_AT2_ONLY_KINDS` — classify-time abstain guard; a
   kind absent here can be LLM-emitted without abstaining.
   Plus: the supply_chain factory binds its **own** `sod_steps` (procurement
   hardcodes `frozenset({"intake","approve"})` at `hero_demo/run.py:278` — a
   named drift point), and the test-side `_AT2_CONTENT_TYPES` disjointness set
   (`test_draft_lift_governance.py:218-229`) must name the new model types.

## Acceptance Criteria

- [ ] **AC-1** `GateKind` gains one new member (SD-1 name; additive — no
  existing member renamed/removed; ADR-016 OQ-A1). Docstring updated: 7 observed
  kinds, N-vertical provenance.
- [ ] **AC-2** New typed content model (SD-1 shape) + union arm in
  `AT2Governance` (`spec.py:703`), `extra="forbid"`, discriminator `kind` =
  the new gate-kind value; `model_validator` enforcing **total ordinal cover**
  (analog of `DoaLadder._validate_ladder`: every severity value maps to exactly
  one tier; strictly-monotone tier floors; non-empty). No set-typed fields
  (coordination point 7); no `Decimal`-typed money (non-money by construction).
  Marked **instance-scoped / provisional** per ADR-0025 D2 discipline.
- [ ] **AC-3** Deterministic, fail-closed resolver module (pattern
  `resolve_doa_tier`): reads the authority quantity off the input entity
  (contract defined in Step 4; absent/invalid ⇒ typed error, fail closed —
  analog of `governance_step.py:39-57` `_spend`).
- [ ] **AC-4** Run-side wiring: `governance_step.py` action dispatch
  (`:134-139`) + evaluate dispatch (`:299-302`) gain the new content-type arm;
  render/route/block only — no irreversible I/O (ADR-007 gate untouched).
- [ ] **AC-5** Obligation side (⚠ hole 1): `_AT2_GATE_KINDS` gains the new
  kind; `derive_governance_todo` derives its `governance_content` obligation;
  `derive_procedure_governance_todo` extended so the new authority kind **also
  owes `separation_of_duties`**. Negative test: a procedure carrying the new
  gate kind with **absent or mismatched** content FAILS
  `validate_governance_complete` (hollow-but-complete refused).
- [ ] **AC-6** Prose-lint coverage (⚠ hole 2): `_at2_role_vocab` +
  `_at2_free_text_surfaces` extended to the new model's role-bearing and
  free-text fields; a seeded severity/role token in a note **blocks load**.
- [ ] **AC-7** Run-pin (⚠ hole 3): a test asserts the new content model
  round-trips `build_governance_snapshot` deterministically (and that it carries
  no set-typed fields), preserving the `governance_pin.py:13-17` invariant.
- [ ] **AC-8** `_AT2_ONLY_KINDS` (`generator/pipeline.py:82`) gains the new
  kind; an abstain test proves the generator still refuses AT-2-class narratives
  including the new kind (generator remains AT-1-only:
  `archetypes/template.py:255`, `generator/schemas.py:40`).
- [ ] **AC-9** `verticals/supply_chain/procedures.yaml` ships: a `principals:`
  block (≥2 Persons — requester + approver; pure YAML, parsed generically by
  `auth.py:49-60`; **no ORM/migration**), `separation_of_duties`
  (`distinct_steps` ⊇ {intake, approve} + `required_roles` resolving to declared
  Persons — `principal_sod.py:118-189` fails closed otherwise), and the
  disposition procedure per the design sketch. It loads through the existing
  golden gate (`test_example_procedures.py:32` already lists supply_chain —
  `validate_runnable` → `validate_governance_complete` per procedure). The
  existing `cold_chain_excursion_sweep` stays byte-identical.
- [ ] **AC-10** Executor factory: `verticals/supply_chain/procedures_factory.py`
  binds `GovernanceActionExecutor`/`GovernanceEvaluateExecutor` (pattern
  `hero_demo/run.py:255-290`) with supply_chain's **own** `sod_steps` and the
  new-kind resolver; an in-memory `run_procedure` test drives the full
  intake→assess→gdp_gate→approve(suspend)→fulfill path offline.
- [ ] **AC-11** **The D7 marker (this PLAN owns it — ADR-0031 OQ-4):** new test
  `tests/services/engine/procedures/test_at2_signature_retrigger.py` counting
  **distinct AT-2 signatures**, not procedure entries (procurement's 3 entries
  are trigger variants of ONE signature — `procedure-archetypes.md:171`; a naive
  count reads ≥3 and false-fires). Predicate: `orchestrator.py:636
  _is_at2_procedure`; dedup key (Code judgment, veto-open): `(vertical,
  ordered tuple of the procedure's AT-2 gate kinds)`. Template:
  `test_principal_identity_retrigger.py` (glob `verticals/*/procedures.yaml`,
  self-cancelling message). Semantics: fires at distinct signatures ≥ N →
  "re-evaluate the AT-2 generator deferral (ADR-0025 D7)". **Because this PLAN
  itself creates N=2, the re-evaluation happens AT THIS REVIEW (SD-3):** the
  marker documents the recorded SD-3 resolution + baseline (N=2, date,
  PLAN-0074) and trips again at N≥3.
- [ ] **AC-12** **Collateral re-trigger owned (ADR-0026 OQ-6):** adding
  supply_chain principals fires `test_principal_identity_retrigger.py:47` +
  `:55` **by design** (self-cancelling). Per SD-4: update the baseline to
  `["procurement", "supply_chain"]`, record the resolution path chosen
  (follow-on recommended), bump `_RETRIGGER_N` per the test's own instruction —
  never merged silently red.
- [ ] **AC-13** Test-side H-partition coverage: `_AT2_CONTENT_TYPES`
  (`test_draft_lift_governance.py:218-229`) gains every new model type, keeping
  recursive draft-disjointness + facet-unreachability true for the new content.
  (Correction vs the dispatch fact-pack: the hardcoded vertical lists at
  `test_example_procedures.py:32`, `test_spec.py:630`, `test_prose_lint.py:18`,
  `test_draft_lift_governance.py:75` **already include supply_chain** — no
  append needed; the content-type set is the real gap.)
- [ ] **AC-14** Offline red-team oracle (ADR-0025 D8 analog, for the NEW model):
  (1) hollow-but-complete — empty/duplicate/non-covering severity tiers,
  `approver_role == requester role` → refused; (2) free-text-leak — severity +
  role tokens seeded in notes/description → prose-lint blocks load; (3)
  identity-collapse — SoD roles resolving to one principal → run fails closed,
  no "governed" verdict.
- [ ] **AC-15** Whole suite deterministic + offline (no DB required beyond
  existing skips, no LLM, no MS-S1); enum extensions
  (`ComplianceCriterion` / `SourcePolicy` / `ExceptionPolicy`) are additive
  only and all procurement golden tests stay green.
- [ ] **AC-16** A load-time gate_kind↔content correspondence check (a present
  `governance_content` whose `kind` mismatches the step's `gate_kind` is
  rejected at load, not just counted unfilled at run) — closes the named
  two-parallel-mechanisms hazard cheaply. *Code judgment, veto-open: Cray may
  strike this AC if it is scope creep; drafts with absent content are
  unaffected (tightening only).*

## Out of Scope

- ❌ The **AT-2 generator** (stays deferred + abstaining — ADR-0025 D7; this
  PLAN records the N=2 re-evaluation via AC-11/SD-3, it does not build it).
- ❌ **Genericizing the D2 types / extracting a generic AT-2 framework or the
  ADR-0031 gate-plugin seam** (SD-3 recommends a follow-on PLAN; this PLAN's
  coordination-point enumeration is that PLAN's input).
- ❌ **Shared/core Person extraction** (ADR-0026 OQ-6 — SD-4 recommends a
  follow-on; this PLAN only updates the marker baseline honestly).
- ❌ A **transform StepKind / expression grammar** (ADR-0031 D3 row-1 — SD-2
  default is the action-stamp pattern; if implementation proves derived-field
  intake is needed, that arms row-1 case-2 for its OWN future PLAN — never
  inlined here).
- ❌ Live carrier / disposal / ERP I/O (handlers stay no-op receipt stubs behind
  the ADR-007 gate); DB/ORM/Alembic work (supply_chain is in-memory synthetic).
- ❌ Hero-demo UI scene for the new procedure (AT-2 renders read-only via the
  existing viewer; a demo scene is follow-on).
- ❌ Any edit to ADR-0031's D3 table (D4.4 fires when the SEAM lands, not now).

## Steps

### Step 0: Pre-flight baseline
Green run of the existing suite (pre-committed pass/fail read); confirm the
golden gate + retrigger tests pass on the branch base.

### Step 1: Spec layer (coordination points 1, 2, 6 + AC-16)
`GateKind` member; the SD-1 severity enum + content model + union arm +
total-cover validator; extend `_at2_role_vocab` / `_at2_free_text_surfaces` to
the new model; the load-time correspondence check; additive
`ComplianceCriterion` / `SourcePolicy` / `ExceptionPolicy` members.

### Step 2: Obligation layer (point 5 + AC-13)
`_AT2_GATE_KINDS`, `derive_governance_todo`, `derive_procedure_governance_todo`
(new kind owes SoD); `_AT2_CONTENT_TYPES` additions; negative
hollow-but-complete tests.

### Step 3: Resolver + run wiring (points 3, 4, 7, 8)
Resolver module (fail-closed entity contract); `governance_step.py` dispatch
arms; the governance-pin determinism test; `_AT2_ONLY_KINDS` + abstain test.

### Step 4: The supply_chain procedure (AC-9, AC-10)
`procedures.yaml` (principals, SoD, agent allowlist extension, the five steps —
`cold_chain_excursion_sweep` untouched); factory bindings with own `sod_steps`;
the offline end-to-end `run_procedure` test. Entity contract: `intake` carries
magnitude/duration/stability-budget scalars; `assess` stamps the derived
severity (SD-2 action-stamp), which `approve`'s resolver reads fail-closed.

### Step 5: The two markers (AC-11, AC-12)
Arm `test_at2_signature_retrigger.py` (distinct-signature count, N=2 baseline
recording the SD-3 resolution, trips at N≥3); update
`test_principal_identity_retrigger.py` per SD-4's ratified outcome.

### Step 6: Red-team oracle + full verification (AC-14, AC-15)
The three fixtures; full offline suite; ruff + mypy clean.

## Verification

Offline pytest (fixtures / in-memory) with pass/fail reads fixed before each
run: the golden load gate covers the new procedure; the hollow / leak /
identity-collapse fixtures each fail closed; both markers green with honest
baselines; procurement's AT-2 suite byte-identical green; no live host-state
runs (any live smoke is a separate Cray-gated step, CLAUDE.md §8).

## Surfaced Decisions (Cray adjudicates at review — recommendations are contingent, not chosen)

- **SD-1 — the exact non-money authority quantity + content-model shape.**
  *Recommendation:* a **closed ordinal severity enum** (e.g. `ExcursionSeverity
  {negligible < minor < major < critical}`, derived deterministically from
  excursion magnitude × duration vs the cargo's stability budget) + a
  **`SeverityLadder`** (`kind="severity_tier"`; `tiers: list[SeverityTier
  {min_severity, approver_role, note}]`, total ordinal cover — structurally
  DoaLadder-analogous but severity-keyed, invalid severities unrepresentable).
  **No emergency-waiver analog in v1** (waiver is procurement-shaped; adding one
  is scope). *Alternatives:* (a) batch-value-at-risk in ฿ reusing `DoaLadder` —
  easier, doesn't press the seam (Cray already leaned away); (b) a continuous
  `Decimal` risk score with numeric thresholds — re-imports DoaLadder's shape
  with different units, weaker than a closed ordinal. *Why Cray:* the authority
  quantity defines what the approver legally/organizationally authorizes —
  domain + business judgment, not a code call.
- **SD-2 — transform seam vs action-stamp for the intake-derived quantity.**
  *Recommendation:* the **scored_rule-style action-stamp suffices** for v1 (a
  scalar ordinal derived from two scalars, stamped at `assess` — the
  `governance_step.py:199-209` pattern). If implementation shows genuinely
  messy multi-field derived intake, that is ADR-0031 D3 **row-1 case-2 armed**
  (two seams pressed at once — a feature, recorded, but the transform grammar
  ships in its own PLAN, never inline).
- **SD-3 — genericize the D2 types now (N≥2 unlocks it) or keep
  instance-scoped?** *Recommendation:* type the 2nd instance
  **instance-scoped** + arm the marker in THIS PLAN; **defer** the generic
  AT-2-framework extraction (and the ADR-0031 gate-plugin seam) to a follow-on
  PLAN fed by this PLAN's triangulation findings — avoids a mega-PLAN. N≥2
  *permits* genericization (D7); it does not mandate it here. *Why Cray:* it
  schedules the moat's abstraction step.
- **SD-4 — ADR-0026 OQ-6 (core Person extraction) handling.** *Recommendation:*
  **follow-on** — this PLAN updates the fired marker honestly (baseline =
  2 verticals, `_RETRIGGER_N` bumped, resolution path named per the test's own
  docstring) and files the follow-on; extracting a shared `Person` here would
  double the blast radius. *Alternative:* in-scope extraction (one PR, but
  couples an identity-model refactor to a gate-kind PLAN). *Why Cray:* it is a
  second self-cancelling deferral being answered — same class of call as SD-3.

## References

- ADR-0025 — D2 (typed union, instance-scoped), D4 (prose-lint + H-partition),
  D5 (semantic completeness), D7 (the N≥2 re-trigger this PLAN fires + owns),
  D8 (the red-team oracle AC-14 mirrors)
- ADR-0031 — D3 row-3 (gate seam; this PLAN is its named trigger event) + row-1
  (transform seam, SD-2), D4.3 (owned markers), OQ-4 (marker ownership → this
  PLAN), D2 tripwires
- ADR-0026 OQ-6 (+ `test_principal_identity_retrigger.py`) · ADR-016 OQ-A1 ·
  ADR-006 D4 · ADR-007 (write gate)
- Code anchors (verified 2026-07-14, main=25238db): `spec.py:200-211, 514,
  538-567, 570-628, 664-706, 981-1011`; `draft.py:264-338`;
  `governance_step.py:39-57, 134-139, 199-209, 299-302`;
  `governance_pin.py:13-17, 42-70`; `generator/pipeline.py:82`;
  `orchestrator.py:636`; `main.py:125-130`; `hero_demo/run.py:255-290, 278`;
  `test_draft_lift_governance.py:218-229`; `procedure-archetypes.md:150-172`;
  `verticals/supply_chain/procedures.yaml`
