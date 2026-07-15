# PLAN-0076: AT-2 follow-on tracking — the gate-plugin seam (F-FACTORY) and F-PIN's remainder (derivation pin)

**Status:** Proposed — Cray ratifies at PR. **STUB / TRACKING PLAN, not a build plan** — it is the durable home for two deferrals Cray ratified in PLAN-0075 (session 132) so neither rots; each real build gets its OWN PLAN (ADR-0031 D4.2).
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

**What landed (PLAN-0075 AC-13 — PROVENANCE-ONLY).** supply_chain's
`_DOSE_LADDER` + `_TOP_SEVERITY` are hashed into the run's governance
snapshot via a live per-vertical provider (`registry.py:39`
`DerivationHashProvider`; `cold_chain_assess.py:82` `derivation_hash()`;
threaded through `build_governance_snapshot(procedure, *,
derivation_hash=None)`, `governance_pin.py:56-58`). This buys (i)
**mid-flight tamper-evidence** (a run-start↔resolve derivation mismatch
fails closed at the pin) and (ii) **audit provenance** (which derivation
governed THIS run). **It does not close F-PIN.**

**What remains open (F-PIN is NOT closed — do not record it as closed
anywhere):**

1. **The new-run re-routing threat.** The governance pin is a per-run
   projection captured at run-start and re-checked at resolve; it only
   catches a run-start↔resolve MISMATCH. A deploy that changes the
   derivation BEFORE a run starts is pinned as normal, without complaint
   (`governance_pin.py` module docstring `:43-44` discloses this
   verbatim).
2. **Procurement's imperative ฿ derivation.** `unit_price × qty` math —
   no clean datum to hash; exactly why AC-13 EXCLUDED procurement.

**Honest deferral rationale (the C3 correction — the earlier "different
axis" framing was RETRACTED; both SD-5 reviewers rejected it).** The
derivation gap is the **same authority axis one layer down** (an authority
decision whose input is untrusted is not fully enforced) — but a **lower
threat tier**: exploiting it requires code access + a PR + a deploy (a
code-access / deploy-hygiene concern), whereas the bug PLAN-0075 closed
was exploitable by an ordinary operational user (a junior approver, no
code change).

**Proper form (load-bearing): "declare the derivation as data," NOT "hash
more code."** `verticals/supply_chain/cold_chain_assess.py:70-71` states
verbatim that `_DOSE_LADDER` "IS THE DATUM A TRANSFORM GRAMMAR WOULD
DECLARE (ADR-0031 D3 row-1) — it lives in code today, and that is the
finding, not an oversight" (constants at `:73-78`). Once the derivation is
promoted to **declared governance data** (a transform StepKind — ADR-0031
D3 row-1), the EXISTING pin covers it for free (the snapshot already
serialises each step's typed `governance_content`,
`governance_pin.py:81-85`), and a hand-rolled procurement code-hash would
be throwaway work. **Dependency:** F-PIN's remainder is therefore
genuinely BLOCKED-BY / folds into the future **ADR-0031 D3 row-1
transform-grammar PLAN** (row-1's own trigger: a second vertical with
messy-intake derived fields; case 1, procurement's `_SeedQuery` residue,
is already on disk).

**The standing tripwire (already in place).** The AC-13(d)
self-cancelling marker
`tests/services/engine/procedures/test_derivation_pin.py::test_fpin_residual_procurement_unpinned_marker`
(`:205-224`): it passes now (supply_chain pinned, procurement un-pinned)
and **FAILS the moment a procurement derivation hash lands**, with a
failure message routing through PLAN-0075 SD-5 / Out of Scope — which
point at THIS follow-on. **This PLAN is where that marker points.** The
failing assertion is the deferral self-cancelling, not a test bug.

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
(`test_fpin_residual_procurement_unpinned_marker`), and files the AC-5
STATUS Active-TODO entry. If either marker is absent/red on `main`,
escalate to Cray — do not silently repair.

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

### Step T2: WHEN the transform-grammar PLAN opens — fold F-PIN's remainder in
Trigger: ADR-0031 D3 row-1's case-2 (a second vertical with messy-intake
derived fields) fires, or a design partner requires deploy-time
derivation governance (which would also revisit the threat-tier
rationale — a Cray call). Response: the transform-grammar PLAN promotes
`_DOSE_LADDER`/`_TOP_SEVERITY` (and procurement's ฿ derivation) to
declared governance data; the existing pin then covers them via
`governance_content` for free; retire the AC-13 code-hash provider and
update/retire the self-cancelling marker in the same PLAN. F-PIN closes
THERE, not here.

### Step T3: Keep the tripwires honest (standing)
Neither marker may be deleted, skipped, or weakened without closing the
tracking it guards (route to Cray). When
`test_fpin_residual_procurement_unpinned_marker` fails because a
procurement derivation hash landed, that failure is the deferral
self-cancelling: close F-PIN's tracking here and update the marker in the
landing PLAN. This PLAN moves to `docs/plans/done/` only when BOTH
deferrals have been either built (via their own PLANs) or explicitly
re-adjudicated by Cray.

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
