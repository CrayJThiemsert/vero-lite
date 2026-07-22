# PLAN-0076: AT-2 follow-on tracking — the gate-plugin seam (F-FACTORY) and F-PIN's remainder (derivation pin)

**Status:** **Tracking** (ratified by Cray at merge, s133 panel review) — a standing TRACKING PLAN, deliberately OUTSIDE the Proposed→Accepted→`done/` build-PLAN lifecycle: it builds nothing, so it has no "Complete" event. Per **Step T3** it stays in active `docs/plans/` until BOTH tracked deferrals are built (each via its OWN PLAN, ADR-0031 D4.2) or Cray re-adjudicates — archiving it to `done/` while either deferral is open would mislabel open work as *resolved* (the s133 anti-rot + info-arch review). Its presence + the STATUS pointer are made **load-bearing by a guard-test (AC-6)**, so they cannot silently vanish. The durable home for two deferrals Cray ratified in PLAN-0075 (s132) so neither rots; each real build gets its OWN PLAN (ADR-0031 D4.2).
**Owner:** Claude Code (execution) · Cray (ratification at PR)
**Created:** 2026-07-15
**Related ADRs:** ADR-0031 (D3 gate-plugin seam row 3 + row-1 transform grammar; D4.1/D4.2/D4.4 fractal Rule-of-Three; OQ-4 deferral-rot precedent), ADR-0025 (D7 AT-2-generator re-trigger — the marker this PLAN verifies paid), ADR-006 (D4 Rule of Three), ADR-0026 (D4 as amended 2026-07-15 — the enforcement this tracking sits behind). Originating context: **PLAN-0075** (SD-3 + SD-5, the ratified adjudications this PLAN records) and **PLAN-0074** (the 2nd AT-2 signature whose s131 review seeded them; `docs/plans/done/0074-…`).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code; the tracking obligation itself was
> ratified by Cray at the PLAN-0075 session-132 specialist review —
> SD-3's architect condition + SD-5's tracking clause). Independent
> review: Code (R2) at PR; ratification: Cray. Author≠reviewer
> separation: **INTACT**. Uncommitted draft — Code commits per ADR-009
> D2. All code/doc anchors verified against the current drafting
> worktree 2026-07-15 (post-PLAN-0075-implementation tree; several
> PLAN-0075 line cites @ ff84d9a have drifted — current lines are used
> throughout, symbols are the stable reference). Note: the PLAN-0075
> AC-13 implementation (`DerivationHashProvider`, `registry.py:39`;
> `derivation_hash()`, `cold_chain_assess.py:82`) is **present in this
> tree**; Code confirms its merge state on `origin/main` at R2.

## Goal

Be the **filed stub PLAN** that PLAN-0075 SD-3's architect condition and
SD-5's tracking clause explicitly require — a durably-tracked follow-on,
never a bare out-of-scope bullet — for the two deferrals ratified by Cray
in session 132: **(A) F-FACTORY**, the ADR-0031 D3 row-3 gate-plugin seam
(procedure-scoped `sod_steps` via a procedure-aware `ExecutorFactory`,
folding in the ADR-0031 OQ-4 CI-marker-debt check), and **(B) F-PIN's
remainder** (the new-run re-routing threat + procurement's imperative ฿
derivation, after the AC-13 supply_chain provenance fold-in). The repo has
a documented deferral-rot precedent — ADR-0031 OQ-4 records that the
ADR-0025 D7 CI marker was promised and long unbuilt — so this PLAN records
each deferral's honest severity, its standing tripwires, and the **proper
form** of each fix, and it is where those tripwires point when they fire.
It builds nothing: each seam waits for its own N≥2 trigger and its own
PLAN (ADR-0031 D4.2).

## Context — LOCKED / RATIFIED (do not re-litigate)

1. **SD-3 = keep NARROW, CONFIRMED** (Cray, s132, after a 3-specialist
   review) — with the architect's binding condition: the gate-plugin seam
   is a durably-tracked follow-on (this filed stub PLAN + a STATUS
   Active-TODO entry), never a bare out-of-scope bullet. Rationale for
   narrow stands and is not re-argued here: a security fix on the shipped
   hero path should land small + adversarially reviewable; bundling a
   framework refactor with a security fix is how security fixes get
   delayed (PLAN-0075 SD-3).
2. **SD-5 = ADJUDICATED SPLIT** (Cray, s132): defer the BULK of F-PIN;
   fold in the supply_chain derivation-provenance half NOW (PLAN-0075
   AC-13, Step 7 — PROVENANCE-ONLY). **F-PIN is NOT closed** — this PLAN
   must never be read as closing it, and nothing here records it closed.
3. This PLAN **records** those adjudications and their tripwires; it does
   not reopen them. Reopening either is a Cray decision with the
   reversal-cost of PLAN-0075's shipped enforcement weighed in
   (CLAUDE.md §6, "Verification is hygiene, not a verdict").

## The two tracked deferrals

### (A) F-FACTORY — the ADR-0031 D3 gate-plugin seam (SD-3)

**The problem.** The registry's executor-factory contract is zero-arg —
`ExecutorFactory = Callable[[], "Mapping[StepKind, StepExecutor]"]`
(`services/engine/registry.py:30`; contract declared `registry.py:26-46`
per ADR-0031's own anchor list). Because the factory receives **no
`procedure` argument**, a vertical's `sod_steps` (and supply_chain's
`stamp_steps`) are **vertical-scoped** — unioned across every procedure —
while the thing they configure is **procedure-scoped**:

- procurement **hardcodes** `sod_steps=frozenset({"intake", "approve"})`
  (`verticals/procurement/hero_demo/run.py:278`) — a named drift point
  from PLAN-0074's coordination-point list: a renamed step there silently
  drops the `sod_required` flag;
- supply_chain **derives** `sod_steps` from the spec's own
  `separation_of_duties` constraints
  (`verticals/supply_chain/procedures_factory.py::_sod_steps`, `:247-255`
  — better: cannot drift on a rename), but it is still vertical-scoped,
  unioned across its two procedures. The factory's module docstring
  (`procedures_factory.py:37-49`) records this residual verbatim,
  including the proper fix — the code itself already points here.

**Severity, stated honestly (the deferral is defensible because of
this).** A mis-bound `sod_steps` only mislabels the `sod_required`
**display flag** on the emitted verdict
(`services/engine/procedures/governance_step.py:196`/`:203` and
`:247`/`:253` — `sod_required = step.step_id in self.sod_steps`).
**Actual SoD enforcement reads `procedure.separation_of_duties` LIVE at
the gate** (`services/engine/procedures/action_step.py:376-378` guard +
the `check_principal_sod` call at `:384`, on the `resolve_gated_step`
path, `:546`; cited as `action_step.py:351-353` in PLAN-0075 @ ff84d9a —
drifted by the PLAN-0075 implementation itself, same symbols). So this is
an **audit-flag over-mark, never an enforcement gap**. Today no `step_id`
collides across supply_chain's two procedures, so it is **inert**
(`procedures_factory.py:43-44` states this; a stray `assess` through the
severity stamp additionally fails CLOSED).

**A SIBLING vocabulary pressure, recorded here so it is tracked rather than lost
(PLAN-0087 AC-8).** `ComplianceCriterion` was not the only engine-owned criterion
vocabulary. `services/engine/procedures/scored_rule.py:53-59` holds
`_KNOWN_CRITERIA = frozenset({"criticality", "lead_time", "unit_price"})` — the
`scored_rule` gate's vocabulary — whose own comment says *"a future AT-2 vertical
EXTENDS this map, never a silent mis-score"*. **PLAN-0087 deliberately did NOT open
it**, and the reason is a real design difference, not scope-trimming: unlike a
`rule_gate` criterion (a pure label the engine uses as a string key — which is why
opening it was behaviourally inert), each scored criterion carries **executor
semantics** (`criticality` is scored by lead-time readiness, `scored_rule.py:22-23`,
amplified by `event_criticality` at `:197`). Opening it means "a declared criterion
needs a declared scoring rule" — a `derive`-grammar-shaped problem. **Its extension
pressure to date is ZERO** (both scored-rule verticals fit inside the original three
names), so Rule-of-Three does not order it yet. **Its trigger:** the first vertical
that demands a scored criterion outside the set — and it is self-announcing, because
`_weights` (`:169-181`) fails CLOSED with `ScoredRuleError` rather than mis-scoring
silently. When it fires, it routes here.

**Trigger status.** The D3 row-3 N≥2 trigger (the 2nd AT-2 signature) HAS
fired — PLAN-0074 merged. But ADR-0031 D4.1 does not COMPEL a build (the
seam map is not a roadmap), and D4.2 gives the seam its own PLAN. This
stub is the tracking in between.

**Proper form (recorded, not built).** A **procedure-aware
`ExecutorFactory`**: key `sod_steps` / `stamp_steps` on
`(procedure_id, step_id)`, which requires the executor to know its
procedure — an engine-contract change, i.e. the ADR-0031 D3 row-3
gate-plugin seam. The seam PLAN must conform to the ADR-0031 D4.2 shape
(typed, declaration-as-data, one seam per core, D2 moat tripwires) and
update the D3 row on landing (D4.4). PLAN-0074's coordination-point
enumeration feeds it (PLAN-0075 References).

**Folded in: the ADR-0031 OQ-4 CI-marker-debt check.** Stated precisely:
ADR-0031 (ratified 2026-07-14) recorded the ADR-0025 D7 AT-2-generator
count-assertion as **ABSENT on disk** ("only the principal-identity
mirror `test_principal_identity_retrigger.py` exists" — ADR-0031 header +
OQ-4, `0031:258-270`), and resolved that the PLAN adding the 2nd
signature owns arming it. PLAN-0074 AC-11 (session 131) **subsequently
built it**:
`tests/services/engine/procedures/test_at2_signature_retrigger.py` —
its header states it owns the ADR-0031 OQ-4 marker, counts distinct AT-2
**signatures** (not procedure entries), records the N=2 re-evaluation as
performed (generator stays deferred), and **re-arms at N=3**. So the OQ-4
debt is **likely already PAID**; this PLAN's AC-2 **verifies** that on
`main` and records it paid — it does NOT rebuild the marker or carry the
debt forward unexamined. The rot PRECEDENT stands as the motivation for
filing this stub at all.

### (B) F-PIN's remainder — after the AC-13 provenance fold-in (SD-5)

**What landed (PLAN-0075 AC-13 — PROVENANCE-ONLY), and what SUPERSEDED it.**
supply_chain's `_DOSE_LADDER` + `_TOP_SEVERITY` were hashed into the run's
governance snapshot via a live per-vertical provider, threaded through
`build_governance_snapshot`. This bought (i) **mid-flight tamper-evidence**
(a run-start↔resolve derivation mismatch fails closed at the pin) and (ii)
**audit provenance** (which derivation governed THIS run). **It did not
close F-PIN.**

> **SUPERSEDED 2026-07-17 by PLAN-0078 PR-5 (Step T2, CLOSED).** That
> code-hash existed only because the derivation lived in CODE, where a
> snapshot of the DECLARATION could not reach it. Both shipped derivations
> are now declared data, the per-step `transform` key pins them directly,
> and the code-hash is retired end-to-end (AC-10) — so every symbol named in
> the paragraph above is GONE from the tree. Both guarantees (i)+(ii) are
> preserved in declared form; see Step T2. **This is evolution, not an
> error** — AC-13 was the right call for the world it shipped into.

**What remains open (F-PIN is NOT closed — do not record it as closed
anywhere):**

1. **The new-run re-routing threat.** The governance pin is a per-run
   projection captured at run-start and re-checked at resolve; it only
   catches a run-start↔resolve MISMATCH. A deploy that changes the
   derivation BEFORE a run starts is pinned as normal, without complaint
   (`governance_pin.py` module docstring `:43-44` discloses this
   verbatim).
2. ~~**Procurement's imperative ฿ derivation.** `unit_price × qty` math —
   no clean datum to hash; exactly why AC-13 EXCLUDED procurement.~~
   **RESOLVED 2026-07-17 (PLAN-0078 PR-4, Step T2).** The premise was that
   the ฿ math had no clean datum. Declaring it produced one: `derive_spend`
   (`amount = mul(selected_unit_price, qty)`), which rides the pin like any
   other declared derivation. **Item 1 above is what remains — and it is
   the whole of what "F-PIN is open" now means.**

**Honest deferral rationale (the C3 correction — the earlier "different
axis" framing was RETRACTED; both SD-5 reviewers rejected it).** The
derivation gap is the **same authority axis one layer down** (an authority
decision whose input is untrusted is not fully enforced) — but a **lower
threat tier**: exploiting it requires code access + a PR + a deploy (a
code-access / deploy-hygiene concern), whereas the bug PLAN-0075 closed
was exploitable by an ordinary operational user (a junior approver, no
code change).

**Proper form (load-bearing): "declare the derivation as data," NOT "hash
more code." — VINDICATED, then EXECUTED (PLAN-0077 + PLAN-0078; T2 CLOSED).**
`cold_chain_assess.py` stated verbatim that `_DOSE_LADDER` "IS THE DATUM A
TRANSFORM GRAMMAR WOULD DECLARE (ADR-0031 D3 row-1) — it lives in code today,
and that is the finding, not an oversight". The prediction that followed —
promote the derivation to declared governance data and *"the EXISTING pin
covers it for free… a hand-rolled procurement code-hash would be throwaway
work"* — **held on both counts**: the pin needed no new mechanism, and the
AC-13 code-hash was retired as the throwaway it was predicted to be. This is
the reason T2 was written as a fold-in rather than a build. **Dependency
(discharged):** F-PIN's remainder was BLOCKED-BY the ADR-0031 D3 row-1
transform-grammar PLAN; row-1's trigger fired, PLAN-0077 shipped the grammar,
and PLAN-0078 migrated both verticals onto it.

**The standing tripwire — FIRED AS DESIGNED, then rewritten (T2/T3).** The
AC-13(d) self-cancelling marker
(`test_derivation_pin.py::test_fpin_residual_procurement_unpinned_marker`)
asserted supply_chain-pinned + procurement-un-pinned, and was built to fail
the moment procurement's derivation became pinnable — routing whoever hit it
back to THIS PLAN. That is exactly what PLAN-0078 did: the deferral
self-cancelled rather than rotted, which is the mechanism working, not a
regression. Per **T3** the marker was **rewritten in the PLAN that closed the
tracking it guarded** (PLAN-0078 PR-5 — never deleted, skipped, or weakened);
`test_derivation_pin.py` now asserts the end state both derivations reached.

**What still points HERE:** T1 / F-FACTORY only (its tripwires are in section
(A)), plus the AC-6 guard-test that keeps this PLAN + its STATUS pointer
load-bearing. F-PIN's new-run threat remains open with **no self-cancelling
marker of its own** — by construction: no test can detect a derivation that
changed before any run started. It is tracked by this document, deliberately.

## Acceptance Criteria

Stub-level — these make the tracking real; none of them builds anything.

- [ ] **AC-1 — both deferrals documented with honest severity +
  rationale.** Pass/fail read: §A states the F-FACTORY severity as an
  audit-flag over-mark, never an enforcement gap (live SoD reads
  `procedure.separation_of_duties`), and §B states the C3 threat-tier
  rationale (same axis, lower tier; "different axis" retracted) — both
  mirroring PLAN-0075 SD-3/SD-5 language, contradicting neither. Fails if
  either severity claim is missing, softened into "no impact", or
  inflated into "enforcement gap".
- [ ] **AC-2 — the OQ-4 marker debt verified PAID on `main`.** Pass/fail
  read: Code (R2) confirms
  `tests/services/engine/procedures/test_at2_signature_retrigger.py`
  exists on `origin/main` and its header claims OQ-4/PLAN-0074-AC-11
  ownership with the N=3 re-arm. (Verified present in the drafting
  worktree 2026-07-15; the nuance stands recorded: ADR-0031 recorded the
  marker ABSENT, PLAN-0074 AC-11 built it AFTER — this AC verifies, it
  does not assume or rebuild.) Fails if the file is absent on `main` —
  in which case the debt is real again and this PLAN's tracking escalates
  to Cray, not to a silent rebuild.
- [ ] **AC-3 — the F-PIN tripwire is named and points here.** Pass/fail
  read: §B names
  `test_derivation_pin.py::test_fpin_residual_procurement_unpinned_marker`
  as the AC-13(d) self-cancelling marker and states the pointer chain
  (marker → PLAN-0075 SD-5/Out-of-Scope → this PLAN). Fails if the marker
  is unnamed or the chain dead-ends.
- [ ] **AC-4 — the proper form of each fix is recorded.** Pass/fail read:
  §A records the procedure-aware `ExecutorFactory` keyed on
  `(procedure_id, step_id)` (the D3 row-3 seam); §B records
  declare-the-derivation-as-data (D3 row-1) with the BLOCKED-BY/fold-into
  dependency on the transform-grammar PLAN, and explicitly rejects a
  hand-rolled procurement code-hash as throwaway. Fails if either proper
  form is absent or inverted (e.g. "hash more code").
- [ ] **AC-5 — a STATUS Active-TODO entry references this PLAN.**
  Companion artifact: **Code files it at commit time** (this drafter does
  not write `docs/STATUS.md`). Pass/fail read: `docs/STATUS.md` carries
  an Active-TODO line naming PLAN-0076 as the shared SD-3 + SD-5 tracking
  home, landed in the same PR or the immediately-following
  `docs(status):` reconcile. Fails if this PLAN merges with no STATUS
  entry.
- [ ] **AC-6 — the tracker is load-bearing by MECHANISM, not convention
  (s133 panel, the anti-rot review — Cray-ratified enhancement).** A pure
  offline guard-test
  (`tests/services/engine/procedures/test_at2_followon_tracking_guard.py`,
  the `tests/services/db/test_load_run_ordering_guard.py` static-guard
  pattern) asserts, while the deferrals are open: **(i)** this PLAN lives
  in **active** `docs/plans/` (NOT `docs/plans/done/`) — so a premature
  archive-to-`done/` turns the build **RED**; **(ii)** `docs/STATUS.md`
  still carries the Active-TODO line naming `PLAN-0076` (AC-5) — so
  pruning the STATUS pointer turns the build **RED**. Rationale: the OQ-4
  rot was a promise nothing FAILED on (a doc read, never executed); this
  converts the PLAN-presence + STATUS-pointer from passively-ignorable
  into a failing build — the panel's finding that *location is convention,
  not tripwire, unless a mechanism makes it one*. Retiring the tracker
  (Step T3) means deleting this guard **in the same PLAN** that archives
  this one — intentional, never silent. Pass/fail read: the guard is green
  with the PLAN in `docs/plans/` + the STATUS line present; moving the
  PLAN to `done/` OR deleting the STATUS line turns it RED.

## Out of Scope

- ❌ **Any actual BUILD of the gate-plugin seam or the transform
  grammar** — each seam gets its own PLAN with its own acceptance
  criteria when its own trigger fires (ADR-0031 D4.2); no PLAN may cite
  the seam map alone as justification (D4.1). This stub compels nothing.
- ❌ **Re-litigating SD-3 or SD-5** — Cray ratified them (s132); this
  PLAN records the adjudications + tripwires. Reopening is a Cray call
  with reversal-cost weighed (CLAUDE.md §6).
- ❌ **A hand-rolled procurement code-hash** — throwaway work; the proper
  form is declare-as-data, after which the existing pin covers it for
  free (§B).
- ❌ **Recording F-PIN as closed** — AC-13 was provenance-only; the
  new-run re-routing threat and procurement's ฿ derivation stay open.
- ❌ **Rebuilding or editing the OQ-4 marker** — AC-2 verifies it exists
  on `main`; PLAN-0074 AC-11 owns it (owner + AC named per ADR-0031
  D4.3).
- ❌ Edits to ADR-0031's D3 table — D4.4 fires when a seam LANDS; this
  PLAN lands none.

## Steps

Stub-level: what to do WHEN each trigger fires, and how the tripwires
stay honest. Not implementation detail.

### Step T0: Verify-and-record (the only work this PLAN itself does)
At R2/commit time, Code performs the AC-2 `main` check
(`test_at2_signature_retrigger.py` exists; header owns OQ-4, re-armed at
N=3), confirms the AC-13 marker is green on `main`
(`test_fpin_residual_procurement_unpinned_marker`), files the AC-5 STATUS
Active-TODO entry, and lands the **AC-6 presence guard-test** (green with
this PLAN in active `docs/plans/` + the STATUS pointer present). If either
marker is absent/red on `main`, escalate to Cray — do not silently repair.

### Step T1: WHEN the F-FACTORY trigger next presses — open the seam PLAN
Trigger to watch for (any one): a supply_chain (or any vertical's) second
procedure reuses a SoD/stamp `step_id` (the inert collision goes live —
the over-mark stops being hypothetical); a third AT-2 signature fires the
N=3 re-trigger marker; or the 4-edit gate-shape pain (D3 row 3, ≥4
coordination points) bites again in a real PLAN. Response: open the
dedicated gate-plugin-seam PLAN per ADR-0031 D4.2 — procedure-aware
`ExecutorFactory`, `sod_steps`/`stamp_steps` keyed on
`(procedure_id, step_id)`, retiring the `hero_demo/run.py:278` hardcode
and the `procedures_factory.py:37-49` residual note; seed it from
PLAN-0074's coordination-point enumeration; update the D3 row on landing
(D4.4).

> **Trigger FIRED (session 151, 2026-07-19) — the seam PLAN is NOT yet opened
> (that stays Cray's call).** The "third AT-2 signature fires the N=3 re-trigger
> marker" condition is now MET: PLAN-0081 shipped
> `building_materials.governed_credit_release` (the 3rd AT-2 signature), which
> re-armed `test_at2_signature_retrigger.py` and obligated the ADR-0025 D7
> re-evaluation (performed; verdict Cray-ratified — generator stays deferred,
> marker re-arms at N=4). This RECORDS that T1's watched trigger has pressed;
> per ADR-0031 D4.1 the seam map "is not a roadmap" and D4.1 does not compel a
> build, so opening the dedicated gate-plugin-seam PLAN remains a conscious
> Cray decision. PLAN-0076 stays `Status: Tracking` and its guard stays armed.

> **Trigger FIRED A SECOND TIME — and this time the deferral is CANCELLED
> (session 157, 2026-07-21, PLAN-0086; Cray-ratified, typed).** `N=4` was
> reached: PLAN-0086 shipped `fleet_maintenance.governed_repair_approval`, the
> 4th distinct AT-2 signature, which fired
> `test_at2_signature_retrigger.py`. Unlike the `N=3` pressing, the answer was
> **not** "re-arm" — the AT-2-generator deferral (ADR-0025 D7) is **cancelled
> and the extraction is DUE**.
>
> *Why this firing was different.* By gate SHAPE fleet taught nothing new (its
> composition and authority quantity are byte-identical to
> building_materials'; only the criterion vocabulary differs — the axis N=2
> already fixed as per-instance). What decided it was the OTHER axis: shipping
> fleet required extending the closed shared `ComplianceCriterion` enum in
> engine code, making **four consecutive verticals, four engine-level enum
> extensions**. The recurring pressure is not a gate composition — it is the
> engine bending to admit each instance's vocabulary. Cray's stated rationale:
> accept the cost now for future flexibility.
>
> *What this obligates (T1's response, still to be opened as its own PLAN).*
> The best-evidenced extraction is narrower and better-supported than "build an
> AT-2 generator": stop requiring an engine edit per vertical (open /
> per-vertical criterion vocabulary), inside the ADR-0031 D4.2 gate-plugin-seam
> frame — procedure-aware `ExecutorFactory`, `sod_steps`/`stamp_steps` keyed on
> `(procedure_id, step_id)`, retiring the `hero_demo/run.py` hardcode.
> **PLAN-0086 deliberately did NOT perform any of it** — it is a
> vertical-scaffold PLAN, and framework surgery inside it would have been out of
> scope and destructive to its own timed measurement. A new PLAN is G2-gated for
> Code, so the seam PLAN must be drafted by `plan-drafter` / Cowork and
> committed separately (ADR-009 D1/D2).
>
> PLAN-0076 stays `Status: Tracking`, T1 stays OPEN, and the retrigger module's
> new `test_at2_extraction_obligation_is_owned` guard now fails if this PLAN is
> archived or loses this record — a cancelled deferral with no owner is strictly
> worse than the deferral was.

> **T1 PARTIALLY DISCHARGED — the criterion-vocabulary half shipped as PLAN-0087
> (session 158, 2026-07-21).** The extraction the `N=4` firing made due has been paid
> on the axis the evidence actually supported: `ComplianceCriterion` is retired from
> engine code, each vertical DECLARES its own `rule_gate` vocabulary in its
> `procedures.yaml` (`VerticalProcedures.compliance_criteria`, membership-validated at
> load), and a new AT-2 vertical now ships its gate with **zero engine diff** — proven,
> not asserted, by PLAN-0087 AC-1's proof pair (a fixture criterion that exists nowhere
> in `services/` loads and gates, with a static guard keeping it that way).
>
> *Scope, and why the split.* **SD-1 = (a), Cray-ratified (typed, session 158):** the
> vocabulary half only. **The F-FACTORY half — the procedure-aware `ExecutorFactory`,
> `sod_steps`/`stamp_steps` keyed on `(procedure_id, step_id)` — REMAINS OPEN and is
> still owned here**, with its named triggers armed (an **observable** SoD over-mark —
> see the s160 correction below; the gate-shape 4-edit pain biting in a real PLAN). Its
> evidence never matched the vocabulary half's: it is an **inert audit display-flag
> over-mark that is not yet observable**, whereas the vocabulary pressure was 4 engine
> edits in 4 consecutive verticals. Building it now would be abstraction ahead of
> pressure — the thing ADR-0031 D4.1 forbids.
>
> *Correction (session 165, 2026-07-23) — this paragraph previously read "zero live
> collisions", and that was **wrong**.* `tests/services/engine/procedures/test_sod_step_id_scope_guard.py:30-37`
> (session 160) established on disk that **collisions already exist**: procurement
> ships five procedures in one file and reuses `intake` and `approve` across three of
> them. **What is actually zero is the OVER-MARK** — all three declare the identical
> `distinct_steps: [intake, approve]`, so the per-vertical union equals each
> per-procedure set and the flattening cannot be observed. The distinction is
> load-bearing *for this PLAN specifically*, because T1's first named trigger was
> worded "a live `step_id` collision" — read literally, that trigger had **already
> fired**, which was never the intent. The trigger is therefore restated above as an
> **observable over-mark**: one procedure reusing `approve` without declaring it
> SoD-constrained. The s160 guard is what now turns RED when that happens.
>
> *What is NOT corrected: the ADR-0031 D4.1 citation stands.* A session-165 grounding
> pass proposed that D4.1 was miscited because "T1's trigger already fired twice
> (N=3 s151, N=4 s157)". **Refuted against the text above:** those firings are the
> **AT-2-signature / criterion-vocabulary** axis, and that obligation was *discharged*
> by PLAN-0087. F-FACTORY carries its own, still-unfired triggers, so D4.1's
> "must also show its trigger fired" bar is exactly the applicable rule.
>
> *Anchor drift corrected while shipping PLAN-0087 (§A above is stale on both counts):*
> procurement's `sod_steps` hardcode is at `verticals/procurement/hero_demo/run.py:298`,
> not `:278`; and **three** verticals now DERIVE `sod_steps` from their spec's own
> `separation_of_duties` (`supply_chain/procedures_factory.py:244`,
> `building_materials/procedures_factory.py:64`,
> `fleet_maintenance/procedures_factory.py:61`) — only procurement's hero demo still
> hardcodes. So F-FACTORY's *hardcode-drift* half is **N=1 and shrinking** (the vertical
> template fixed it by convention) while its *vertical-scoping* half is **N=3 and
> unchanged**. A future seam PLAN should argue the second, not the first.
>
> *Consequence for this PLAN's lifecycle:* it does **NOT** archive. T1 is partial and
> F-PIN's remainder (§B item 1) is open by construction, so per Step T3 both the
> `test_at2_extraction_obligation_is_owned` guard and the AC-6 presence guard stay
> armed and stay pointed here. **No guard re-homing occurred, deliberately** — re-homing
> is required only when this PLAN archives.

### Step T2: WHEN the transform-grammar PLAN opens — fold F-PIN's remainder in
**STATUS: CLOSED 2026-07-17 (session 143) by PLAN-0078 PR-5** — per Step T3's
rule that a marker may only be rewritten in the PLAN that closes the tracking
it guards. **This closes the REMAINDER FOLD-IN ONLY. F-PIN itself is NOT
closed** — see the "What remains open" note below, which stands unchanged.

*Trigger (recorded as fired):* ADR-0031 D3 row-1's case-2 (a second vertical
with messy-intake derived fields) fired, and PLAN-0077 shipped the transform
grammar; PLAN-0078 then migrated both shipped verticals onto it.

*Response, as executed (each leg verifiable on disk):*

1. **The derivations are declared governance data.** supply_chain's
   `_DOSE_LADDER`/`_TOP_SEVERITY` → the `enrich` transform's `map_value` bands
   + mandatory `above` (`verticals/supply_chain/procedures.yaml`, PLAN-0078
   PR-3); procurement's imperative ฿ → the `derive_spend` transform
   (`verticals/procurement/procedures.yaml`, PR-4). The "no clean datum to
   hash" premise that scoped AC-13 to supply_chain is **dissolved**, not
   worked around.
2. **The existing pin covers them for free** — exactly as this Step predicted:
   `_step_governance_snapshot` pins `step.transform` canonically + by_alias
   (`services/engine/procedures/governance_pin.py`).
3. **The AC-13 code-hash provider is retired end-to-end** (PLAN-0078 AC-10):
   provider, registration, the registry seam, the `governance_pin` parameter,
   and the pass-through across all 8 files — grep-clean outside `docs/`.
4. **The self-cancelling marker is REWRITTEN, never deleted/skipped/weakened**
   (T3): `tests/services/engine/procedures/test_derivation_pin.py`. Its retired
   form asserted the supply_chain-pins / procurement-does-not ASYMMETRY; that
   premise is gone, so it now asserts the end state — every shipped derivation
   rides the pin as declared data. The mid-flight fail-closed guarantee it
   guarded is re-homed at full strength (the replacement drives
   `assert_governance_pin` to its raise, incl. the unbounded top band — the
   AC-13 drafter finding, preserved in declared form).

*What did NOT close, and must not be recorded as closed:* the **new-run
re-routing threat** (item 1 of "What remains open" below). It is an
architectural property of per-run pinning — a fresh run on already-changed
declared data pins the change without complaint — and is orthogonal to WHERE
the derivation lives, so declaring the derivation could never have closed it.
PLAN-0078 L-4 states the same. **F-PIN stays open and tracked.**

*Consequence for this PLAN's own lifecycle:* T2 is discharged, T1
(F-FACTORY) is **not** — so per T3 this PLAN does **not** archive, and the
AC-6 guard-test stays armed.

### Step T3: Keep the tripwires honest (standing)
Neither marker may be deleted, skipped, or weakened without closing the
tracking it guards (route to Cray). When
`test_fpin_residual_procurement_unpinned_marker` fails because a
procurement derivation hash landed, that failure is the deferral
self-cancelling: close F-PIN's tracking here and update the marker in the
landing PLAN. This PLAN moves to `docs/plans/done/` only when BOTH
deferrals have been either built (via their own PLANs) or explicitly
re-adjudicated by Cray — and the **AC-6 guard-test is deleted in that
SAME PLAN** (its RED on a premature archive is the intended forcing
function, not a regression to route around).

## Verification

This is a tracking stub, so verification = the ACs' pass/fail reads, all
offline: AC-1/AC-3/AC-4 are satisfied by this document's own §A/§B
content (greppable: "audit-flag over-mark", "declare the derivation as
data", the marker's test id); AC-2 is Code's R2 check of
`test_at2_signature_retrigger.py` on `origin/main`; AC-5 is the STATUS
entry in the merged PR (or its immediate `docs(status):` reconcile). No
live/host-state run is required or appropriate.

## References

- **PLAN-0075** (`docs/plans/0075-at2-authority-enforcement.md`) — SD-3
  (`:647-661`) + SD-5 (`:670-699`) ratified adjudications; Out of Scope
  F-PIN-remainder + F-FACTORY bullets (`:486-524`); AC-13 (`:445-478`).
  Source of truth for scope + framing, mirrored here.
- **ADR-0031** (`docs/adr/0031-core-lifecycle-architecture.md`) — D3 seam
  map (`:127-138`; row-1 transform grammar `:134`, row-3 gate seam
  `:136`); D4 corollaries D4.1–D4.4 (`:148-159`); OQ-4 (`:258-270`,
  RESOLVED s130).
- **ADR-0025** — D7 re-trigger (the deferral the OQ-4 marker enforces);
  **ADR-006** — D4 Rule of Three.
- **PLAN-0074** (`docs/plans/done/0074-at2-signature-2-supply-chain-cold-chain-disposition.md`)
  — AC-11 built the re-trigger marker; its coordination-point enumeration
  feeds the future seam PLAN.
- Code anchors (verified in the drafting worktree, 2026-07-15):
  `services/engine/registry.py:30` (zero-arg `ExecutorFactory`), `:39`
  (`DerivationHashProvider`, AC-13);
  `verticals/procurement/hero_demo/run.py:278` (hardcoded `sod_steps`);
  `verticals/supply_chain/procedures_factory.py:37-49` (residual note),
  `:247-255` (`_sod_steps`), `:276`, `:299-301`;
  `services/engine/procedures/governance_step.py:196,203,247,253`
  (`sod_required` display flag);
  `services/engine/procedures/action_step.py:376-378,384,546` (live SoD
  read + `check_principal_sod` + `resolve_gated_step`; PLAN-0075's
  `:351-353` @ ff84d9a drifted);
  `services/engine/procedures/governance_pin.py:43-44,56-58,81-85`
  (re-routing disclosure; `derivation_hash` param; `governance_content`
  branch — PLAN-0075's `:59-63` drifted);
  `verticals/supply_chain/cold_chain_assess.py:70-78,82` ("THIS IS THE
  DATUM…" comment + constants + `derivation_hash()`; PLAN-0075's
  `:68-70` drifted);
  `tests/services/engine/procedures/test_at2_signature_retrigger.py`
  (OQ-4 marker, re-armed N=3);
  `tests/services/engine/procedures/test_derivation_pin.py:205-224`
  (the AC-13(d) self-cancelling F-PIN marker).
