# PLAN-0079: Tracking — the building_materials governed-credit HERO (the 2nd money `doa_tier` = AT-2 signature #3)

**Status:** **Tracking** — a standing TRACKING PLAN per the Cray-ratified s133
convention (PLAN-0076 precedent: "location ≠ tripwire; failing tests are the
real anti-rot"), deliberately OUTSIDE the Proposed→Accepted→`done/` build-PLAN
lifecycle. It **builds nothing and schedules nothing** — it HOMES the
`building_materials` governed-credit HERO so the item and its **honest cost**
cannot rot out of the volatile STATUS rotation, and it names the trigger that
promotes it to a real build PLAN. It must never be read as "do this next."
**Doing nothing is a real option** — the shipped mirror is a supported, tested
end-state with zero rot pressure forcing the hero (see Current state).
**Owner:** Claude Code (tracking custody) · Cray (promotion authority)
**Created:** 2026-07-16
**Related ADRs:** ADR-0032 (D1 wedge / D2 pilot-gate scope / D6 AT-2 cost
class — the strategic anchor), ADR-0025 (D2 Rule-of-Three + D7 re-trigger —
the obligation this PLAN pins), ADR-0031 (D3 seam map; D4.2 own-PLAN rule),
ADR-0015 (D2 Tier-1 Mirror — the shipped state), ADR-008 ("may extend"
Site precedent). Related PLANs: **PLAN-0076** (`Status: Tracking` — the
gate-seam T1 coupling; the exemplar this PLAN mirrors), PLAN-0077 (SD-8
row-local wall, `docs/plans/done/0077-transform-grammar-build.md:558-577`),
PLAN-0074 (the 2nd AT-2 signature), PLAN-0075 (the tier-authority enforcement
the hero inherits).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code, session 138 follow-on to the #765 mirror +
> the #767 stale-N-count kill). Independent review: Code (R2) at PR;
> ratification: Cray. Author≠reviewer separation: **INTACT**. Uncommitted
> draft — Code commits per ADR-009 D2. All code/doc anchors verified against
> the drafting worktree 2026-07-16 (`main` = 4a5cfb7 per dispatch; mirror
> merge = `c52c1ed`, #765).

## Goal

Be the durable, greppable home for the `building_materials` **governed-credit
HERO** — the guessed governed demo asset ADR-0032 D1 contemplates for a
mid-market building-materials distributor (governed customer-credit release:
exposure vs the account's own `credit_limit_thb`, KYC/overdue-AR compliance,
DOA-tiered human approval). Before this PLAN the hero existed **only in
volatile, rotated surfaces** — the s137 STATUS `next_action` frontmatter and
Current Focus block — with **no Active TODO, no PLAN, no ADR build item**
(verified against `docs/STATUS.md` Active TODOs `:264-279` + Next Steps
`:281-286`, 2026-07-16): exactly the rot shape PLAN-0076 was filed to prevent.
Worse, the session-137 handoff had mis-framed the hero as a **cheap
follow-on** — a claim resting on a stale `N=1` code comment that PR **#767**
had to kill. This PLAN records the item, its **true cost class** (ADR-0032
D6: an AT-2-gated hero is *never* a config-cost item), its open design
constraint, and its promotion trigger. Each real build gets its OWN PLAN
(ADR-0031 D4.2); this stub compels nothing.

## Context — anchored to ADR-0032 (Accepted 2026-07-16)

- **D1 (the wedge).** The hero is the "guess-then-react" demo asset: a
  pre-built governed hero in the partner's own shape, corrected not supplied,
  deterministic offline arm, every value marked "guess — correct me." The
  mirror (#765) is the D1 element-2 scaffold; the hero is its governed spine.
- **D6 (the cost class + fit filter).** building_materials passes the
  4-question fit filter (locatable asset = the *commercial* `CustomerAccount`;
  numeric stream = exposure ฿; threshold/band = the per-entity credit band;
  governed approval = credit release). But D6 states the split this PLAN
  exists to keep honest: an **AT-2-gated hero is a different cost class** —
  "it is AT-2 signature #3 … never scope it as a config-cost item"
  (`docs/adr/0032-…:221-227`). Cite D6; the N-count record itself lives in
  `spec.py:822-830`.
- **D2 precision — state it so nobody misreads:** ADR-0032 D2's **pilot gate
  is BINDING for shape-2 / shape-3 work only** ("a future shape-2 or shape-3
  PLAN must cite a live pilot…", `0032:137-144`). The governed-credit hero is
  **shape-1** work (a governed `monitor→decide→approve→act` workflow — shape 1
  is shipped; D1 is the immediate job). **The pilot gate does NOT block this
  hero.** Nothing in this PLAN may be quoted to imply otherwise.

## Current state (verified on disk 2026-07-16 — do not overclaim)

`verticals/building_materials/` IS shipped (#765, merge `c52c1ed`) as a
**Tier-1 Mirror** (ADR-0015 D2): a hand-authored guessed OCT ontology (Asset =
the commercial `CustomerAccount` carrying `credit_limit_thb`,
`ontology/building_materials_v0.yaml:36`; Site = a sales `Branch`, the ADR-008
"may extend" precedent), a synthetic draft adapter, an `echo` handler stub,
and **no `procedures.yaml`**. A spec-less vertical is a **supported, tested
state**: `GET /procedures` explicitly skips it (the #765 fix +
`tests/api/test_procedures_endpoint.py::test_procedures_skips_discovered_vertical_without_a_spec`,
`:116-140`), and the executor-factory registry docstring names it as a
non-registering mirror (`services/api/main.py:131-134`). Live-verified on the
deterministic rule path (s137). **There is no failing test, no marker, and no
external commitment forcing the hero** — the only pressure is strategic (D1).

## THE HONEST COST — what a build PLAN inherits (the substance this stub pins)

1. **It is the 2nd money `doa_tier` signature and AT-2 signature #3 — the D7
   obligation is the real cost.** Keep the two counters distinct (the exact
   confusion #767 killed): AT-2 is **N=2** today — procurement money/`doa_tier`
   (`emergency_sourcing_round` + its schedule/event variants = ONE signature)
   + supply_chain cold-chain disposition (non-money `severity_tier`,
   PLAN-0074) — per `services/engine/procedures/spec.py:822-830` (as corrected
   by #767). The re-trigger marker
   (`tests/services/engine/procedures/test_at2_signature_retrigger.py`)
   **re-arms at N=3**, so a building_materials `doa_tier` **turns CI RED** and
   **OBLIGATES the ADR-0025 D7 re-evaluation** (generator genericize-or-stay
   -deferred, consciously re-decided at N=3). That obligation — not the ladder
   authoring — is the cost; ADR-0032 D6 states the cost-class split, cite it.
2. **The aggregate-exposure design constraint (UNSETTLED — the first thing a
   build PLAN must decide, recorded here, not decided).** Real credit exposure
   = the **SUM of the account's open-AR rows** — an **aggregate the row-local
   transform grammar CANNOT express**: PLAN-0077 SD-8 ratified the row-local
   wall ("any aggregation" is OUT — `done/0077-transform-grammar-build.md:558-577`;
   aggregation is also the standing PLAN-0048 wall). And the `doa_tier` gate
   reads a **flat** `amount` + `currency` off the threaded entity, failing
   closed without them (`services/engine/procedures/governance_step.py:47-65`).
   So exposure must arrive **already computed** — from the DataAdapter / a
   pre-maintained balance field on `CustomerAccount` — not from a `derive`
   transform. Where exactly it comes from is **SD-2 (open)**. If a build PLAN
   instead finds the grammar extension indispensable, that is the PLAN-0077
   SD-8 Tripwire path (surface for an ADR-0031 row amendment), never an
   in-PLAN invention.
3. **The 3-part spine is mandatory or the governance is HOLLOW.** (a) a
   deterministic **exposure band** — exposure vs the account's own
   `credit_limit_thb`, a per-entity `threshold_field` (the aquaculture
   `do_floor` analog, `verticals/aquaculture/procedures.yaml:102`); (b) a hard
   **`rule_gate`** compliance block (KYC / overdue-AR / blacklist —
   `ComplianceRule.blocks_po` is `Literal[True]`, bypass unrepresentable,
   `spec.py:812-815`) **before** the authority tier; (c) **`doa_tier` + SoD +
   audit** (sales REQUESTS, credit-control APPROVES). **The ladder alone is an
   approval form any tool can do** — all three, or the moat evaporates.
   Machinery exists to reuse, not rebuild: `DoaLadder` (`spec.py:957`),
   `resolve_doa_tier` (`doa_tier.py:95`), `check_tier_authority`
   (`tier_authority.py:125`, the PLAN-0075 enforcement); mirror
   `verticals/procurement/hero_demo/` + `verticals/supply_chain/procedures.yaml`.
4. **Named coordination points a build PLAN WILL trip (enumerated so none
   surprises):** (i) the executor factory is hand-wired —
   `services/api/main.py:125-134` `_PROCEDURE_EXECUTOR_REGISTRARS`; an
   unregistered vertical's fired run 409s at resolve; (ii) the #765
   self-cancelling spec-less guard
   (`test_procedures_endpoint.py:129-134`) FIRES the moment
   building_materials gains a spec — re-point it, do NOT delete; (iii) the
   procedure count pin `total == 9` (`test_procedures_endpoint.py:113`);
   (iv) the N=3 re-trigger marker (point 1).
5. **Coupling to PLAN-0076 T1 (stated, not merged).** The D7 obligation lands
   in PLAN-0076 T1 territory — a 3rd AT-2 signature is itself a named T1
   trigger for the gate-plugin-seam PLAN (`0076:280-291`). PLAN-0076 stays
   active with T1 open; this PLAN does **not** reassign its scope. The
   ordering (wait vs trip-and-force) is **SD-1 (open)**.

## Acceptance Criteria

Stub-level — these make the tracking real; none of them builds the hero.

- [ ] **AC-1 — the honest cost is documented, both counters precise.**
  Pass/fail read: this document states (i) AT-2 = N=2 today with the hero as
  the 2nd *money* signature and 3rd *AT-2 signature overall*, citing
  `spec.py:822-830` + ADR-0032 D6; (ii) the D7 obligation as the cost; (iii)
  the SD-8 aggregate wall with the flat-gate-read anchor; (iv) the 3-part
  spine as mandatory-or-hollow. Fails if any is softened to "config-cost /
  cheap follow-on" (the #767-killed framing) or inflated to "blocked".
- [ ] **AC-2 — the presence guard-test (the load-bearing anti-rot mechanism;
  Code lands it at commit time — this drafter cannot write `tests/`).** A
  pure-offline guard
  (`tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py`,
  mirroring `test_at2_followon_tracking_guard.py`) asserts: **(i)** this PLAN
  lives in **active** `docs/plans/` (NOT `done/`) while the hero is neither
  built nor Cray-declined — a premature archive turns CI **RED**; **(ii)**
  `docs/STATUS.md` carries a pointer naming `PLAN-0079` — pruning it turns CI
  **RED**. Sequencing caveat: **#769 is OPEN and `docs/STATUS.md` is BLOCKED**,
  so half (ii) must land **with or after** the STATUS pointer (SD-3), never
  before — a guard born RED is a broken tripwire, not a safeguard. Pass/fail
  read: half (i) green in this PLAN's PR; half (ii) green in the PR that adds
  the pointer; both RED-able as described.
- [ ] **AC-3 — the promotion trigger is recorded (surfaced, not decided).**
  Pass/fail read: Step T1 names what must be TRUE before a build PLAN opens —
  (a) Cray explicitly commissions the hero (a typed decision, not a drifted
  `next_action`); (b) the exposure source is decided (SD-2); (c) the D7
  obligation is consciously accepted — either PLAN-0076 T1 lands first or
  Cray accepts tripping N=3 inside the build PLAN (SD-1). Fails if the PLAN
  reads as scheduling the build or as deciding SD-1/SD-2 itself.
- [ ] **AC-4 — a STATUS pointer references this PLAN, filed by Code AFTER
  #769 unblocks** (this drafter does not write `docs/STATUS.md`; the dispatch
  bars it while #769 is open). Pass/fail read: `docs/STATUS.md` carries an
  Active-TODO (or equivalent durable) line naming PLAN-0079 in the first
  STATUS-touching PR after #769 closes; AC-2 half (ii) is armed in that same
  PR. Fails if this PLAN merges and no pointer lands once STATUS unblocks.

## Out of Scope

- ❌ **Building the hero** — no `procedures.yaml`, no handlers, no factory
  registration, no ladder authoring here. The build gets its OWN PLAN
  (ADR-0031 D4.2) when Step T1 fires.
- ❌ **Deciding the exposure source (SD-2), the T1 ordering (SD-1), or the
  STATUS-pointer timing (SD-3)** — Cray adjudications, surfaced below.
- ❌ **Editing `docs/STATUS.md` in this PR** — #769 is open; AC-4 defers it.
- ❌ **Re-litigating the ADR-0025 D7 deferral or PLAN-0074 SD-3** — the
  generator stays deferred until the N=3 marker fires FOR REAL; this PLAN
  only records that the hero is what would fire it.
- ❌ **Reassigning PLAN-0076's scope or merging the two trackers** — the
  coupling is stated (Honest-cost point 5); each tracker retires on its own
  Step-T3 terms.
- ❌ **Any shape-2/shape-3 framing** — this is shape-1 work; the D2 pilot
  gate is out of frame both ways (it neither blocks the hero nor is loosened
  by it).

## Steps

### Step T0: Verify-and-land (the only work this PLAN itself does)
At R2/commit time, Code: confirms the anchors above still hold on `main`
(`spec.py:822-830` N=2; the re-trigger marker present; the spec-less guard +
count pin at `test_procedures_endpoint.py:113,129-134`); lands the **AC-2
half-(i) guard-test** green; records AC-4 as pending on #769. If any anchor
has drifted, correct the citation in this PLAN in the same PR — symbols are
the stable reference.

### Step T1: WHEN the promotion trigger fires — open the build PLAN
Trigger (ALL of, per AC-3): Cray commissions the hero + SD-2 decided + the
D7 obligation consciously sequenced (SD-1). Response: open a dedicated build
PLAN that (i) authors the 3-part spine (Honest-cost point 3) mirroring the
procurement/supply_chain exemplars; (ii) handles all four named coordination
points (Honest-cost point 4) — including re-pointing the spec-less guard and
bumping the count pin; (iii) performs the D7 re-evaluation the RED marker
demands, recording the genericize-or-defer decision; (iv) satisfies ADR-0032
D1's demo discipline (offline deterministic arm, guess-marked values). If
Cray instead **declines** the hero, that is equally a T3 retirement path —
record the decision and retire this tracker.

### Step T2: Keep the cost record honest (standing)
If a later change moves any pinned fact — the N-count, the SD-8 wall, the
flat gate read, the factory wiring — update THIS PLAN's citation in the
landing PR (the #767 lesson: a stale count in a comment mis-scoped a hero;
this PLAN must never become the next stale count). The guard-test may not be
weakened or deleted except via T3.

### Step T3: Retirement
This PLAN moves to `docs/plans/done/` only when the hero is **built** (its
build PLAN merged) or **explicitly declined by Cray** — and the AC-2
guard-test is deleted **in that same PLAN/PR** (its RED on a premature
archive is the intended forcing function, not a regression to route around).
The STATUS pointer retires in the same motion.

## Verification

Tracking-stub verification is the ACs' pass/fail reads, all offline: AC-1 by
this document's own greppable content ("AT-2 signature #3", "row-local",
"3-part spine", the anchors); AC-2 by the guard-test green/RED behavior in
this PLAN's PR (half i) and the pointer PR (half ii); AC-3 by Step T1's
trigger list; AC-4 by the post-#769 STATUS PR. No live/host-state run is
required or appropriate (CLAUDE.md §8).

## Surfaced decisions (Cray adjudication — recorded open, NOT decided here)

- **SD-1 — T1 ordering: must the hero WAIT for PLAN-0076 T1 (the gate-plugin
  seam), or may it trip the N=3 marker and force the D7 re-evaluation inside
  its own build PLAN?** Recommendation: decide at commissioning time, not
  now — the seam PLAN's own trigger list already names a 3rd signature as one
  of its firing conditions, so either order is coherent. Why Cray: it
  sequences two open obligations against demo timing — a business call.
- **SD-2 — the exposure source:** (a) an adapter-maintained
  `current_exposure_thb` balance field on `CustomerAccount` (synthetic now,
  partner-fed later); (b) a pre-computed upstream aggregate (mapping-layer
  territory); (c) extend the transform grammar with aggregation — the
  PLAN-0077 SD-8 Tripwire path (an ADR-0031 row amendment, heaviest).
  Recommendation: (a) for the demo arc — cheapest, honest about being a
  guess, keeps the SD-8 wall intact. Why Cray: (c) reopens a ratified wall;
  (a)-vs-(b) shapes the partner data-onboarding story (ADR-0032 D1's ladder).
- **SD-3 — STATUS pointer timing:** add the PLAN-0079 pointer in the first
  post-#769 STATUS PR (recommendation — keeps AC-2 half (ii) armed soonest
  without touching a blocked file) vs fold into the next scheduled scribe
  reconcile. Why Cray: it touches the blocked-file exception surface (#769).

## References

- **ADR-0032** (`docs/adr/0032-strategic-frame-demo-to-pilot-wedge-and-3-shape-roadmap.md`)
  — D1 `:93-124`; D2 pilot gate `:126-144`; D6 cost class + fit filter
  `:202-232` (the "never scope it as a config-cost item" line `:221-227`).
- **PLAN-0076** (`docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md`)
  — the Tracking-stub exemplar; T1 triggers `:280-291`; AC-6 guard pattern.
- **PLAN-0077** (`docs/plans/done/0077-transform-grammar-build.md:558-577`) —
  SD-8 row-local wall (aggregation OUT).
- Code anchors (verified in the drafting worktree, 2026-07-16):
  `services/engine/procedures/spec.py:812-815` (bypass unrepresentable),
  `:822-830` (AT-2 N=2, post-#767; re-arms N=3), `:957` (`DoaLadder`);
  `services/engine/procedures/governance_step.py:47-65` (flat `amount`/
  `currency` read, fails closed); `doa_tier.py:95`; `tier_authority.py:125`;
  `services/api/main.py:125-134` (hand-wired registrars; mirrors register
  none); `verticals/building_materials/ontology/building_materials_v0.yaml:36`
  (`credit_limit_thb`); `verticals/aquaculture/procedures.yaml:102`
  (`threshold_field: do_floor` analog);
  `tests/api/test_procedures_endpoint.py:113` (count pin), `:116-140`
  (spec-less skip guard, self-cancelling `:129-134`);
  `tests/services/engine/procedures/test_at2_signature_retrigger.py` (N=3
  re-arm); `tests/services/engine/procedures/test_at2_followon_tracking_guard.py`
  (the guard pattern AC-2 mirrors).
- STATUS evidence for the no-durable-home finding (read-only; #769 blocks
  edits): `docs/STATUS.md:264-286` (Active TODOs + Next Steps — no hero
  entry) vs the volatile-only mentions (`:4-7` frontmatter, `:21-60` s137
  Current Focus block).
