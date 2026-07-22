# PLAN-0089: Fleet PM Calm Path — the "Extend an Existing Vertical" Measurement

**Status:** Draft — SD-1…SD-3 below are OPEN (Cray explicitly declined to pre-answer them,
session 161); no implementation before Step-0 ratification.
**Owner:** Claude Code (executes + commits per ADR-009 D2) + Cray (ratifies the SDs at Step 0;
answers the pre-committed intake question(s) in-character as the simulated customer)
**Created:** 2026-07-22 (session 161)
**Related ADRs:** ADR-016 (TF-1 per-entity `threshold_field` band), ADR-0030 (D5 never-raise
advisory precedent), ADR-0032 (D5 positioning honesty — the caveat discipline; D1(3) offline-arm),
ADR-009 D1/D2 (authoring / commit boundary)
**Related PLANs:** PLAN-0086 (the mandate + the measurement model — see below), PLAN-0064/0065/0066
(the AT-3 donor mechanics: per-step declared read, rename-projection, per-entity threshold_field),
PLAN-0085 (gate advisory — why the calm gate carries none), PLAN-0087 (declared criterion
vocabulary — why this PLAN has zero engine-enum exposure), PLAN-0040 (the AT-3 generator template —
SD-2's rejected arm)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1); outline + verified fact-pack
> originated by Code (session 161), work item selected by Cray (s161) after the four-agent
> grounding fan-out. Independent review: Code (R2) + Cray at PR merge. Cray rules on SD-1…SD-3
> at review — each recommendation below is contingent, not chosen.

## Goal

Add the **preventive-maintenance (PM) calm path** to the shipped `fleet_maintenance` vertical —
the AT-3 second procedure PLAN-0086 deliberately deferred — as a **timed, pre-protocolled
experiment measuring the "extend an existing vertical" number**: the marginal hands-on cost of
adding a second governed procedure to a live vertical when a shipped donor archetype exists.
Dual deliverable, mirroring PLAN-0086's structure: (1) a working calm path — read each truck's
odometer, judge it against that truck's own service-due point, park the due set at a single
human go/no-go — the routine contrast to the vertical's AT-2 emergency hero, on the same engine
and agent; (2) the measured number plus its binding honesty caveat, the companion to PLAN-0086's
27m39s "create a new vertical" figure (`docs/plans/done/0086-fleet-vertical-timed-manual-scaffold.md:510-521`).

## Mandate + citation correction

This work item was ratified in advance: **PLAN-0086 SD-3**
(`docs/plans/done/0086-fleet-vertical-timed-manual-scaffold.md:218-237`) resolved (a) — one hero
procedure, with the tire/PM calm path kept as "a named, unscheduled follow-on measuring the
**'extend an existing vertical'** number" (Cray, AskUserQuestion, 2026-07-21 s156). The code
carries the same deferral note at `verticals/fleet_maintenance/procedures_factory.py:9-10`.

**Citation correction (do not propagate the old one):** prior handoffs and STATUS attributed this
deferral to "ADR-0025 SD-3" or "PLAN-0074 SD-3". Both are wrong — ADR-0025 has no SD-3 (its line
114 merely refers to PLAN-0074 SD-3), and PLAN-0074's SD-3 concerns genericizing D2 typed content.
The correct citation is **PLAN-0086 SD-3**, verified on disk in sessions 161 and 162.

## Verified ground (session 161 fact-pack, re-verified on disk by this draft 2026-07-22; executor re-verifies at execution HEAD)

**What exists.** `fleet_maintenance` ships exactly ONE procedure — the AT-2
`governed_repair_approval` (`verticals/fleet_maintenance/procedures.yaml:82-280`; catalogued
`docs/conventions/procedure-archetypes.md:129-141`). No calm path exists; "tire" appears nowhere
in the repo as a modelled concept. The adapter ships **2 Trucks** with live `odometer_km` values
(412,580.0 / 688,140.0 — `verticals/fleet_maintenance/data_adapter/synthetic.py:60,:69`) that
**no procedure, factory, or handler currently reads**. The missing piece is a per-truck
**threshold** field — the `reorder_point` analogue; `minor_repair_ceiling_thb` is money-typed and
cannot serve a km band (`verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:40-46`).

**The donor.** AT-3 (`docs/conventions/procedure-archetypes.md:157-177`):
`query → evaluate (vs a per-entity reorder point) → action/gated`, governance signature = a
deterministic band + a single human approval tier, **no emergency waiver, no DOA ladder, no SoD**.
Two shipped instances, both procurement: `low_stock_reorder_round`
(`verticals/procurement/procedures.yaml:376-455`) and `scheduled_low_stock_reorder_round`
(`:742-812`). The port pattern is near byte-for-byte: declared `reads:` + a **fields-only
rename-projection** into `measured_value` (no arithmetic, no LLM — PLAN-0065 SD-2,
`verticals/procurement/procedures.yaml:403-409`) + `threshold_field` / `direction` on the judge.

**Change surface (all verified).**
- `procedures_factory.py` — **zero change**: StepKind-keyed and procedure-agnostic
  (`verticals/fleet_maintenance/procedures_factory.py:92-113`); the calm path uses only
  QUERY/EVALUATE/ACTION, all registered.
- `services/api/main.py` — **zero change** (fleet already in `_PROCEDURE_EXECUTOR_REGISTRARS`).
- **Zero engine edits.** The only non-vertical touch is one mirror line:
  `PROCEDURE_ARCHETYPES` (`services/api/routers/procedures.py:38-60`) plus its census pins —
  `_EXPECTED` (`tests/api/test_procedures_endpoint.py:29-58`) and `assert total == 11` (`:128`)
  → 12. Since PLAN-0087, `compliance_criteria` is declared in vertical YAML
  (`verticals/fleet_maintenance/procedures.yaml:75-80`) — and AT-3 has no `rule_gate` anyway, so
  the PLAN-0086-era engine-enum exposure is doubly gone.
- `derive_governance_todo` is gate-kind + StepKind generic
  (`services/engine/procedures/draft.py:293-322`): the AT-3 judge owes
  `["threshold_field", "direction"]`, the gated action owes `["handler", "autonomy"]` — both
  authored here.
- **No Alembic, no committed ORM** (`verticals/*/generated/` gitignored, `.gitignore:42`): the
  ontology edit costs a YAML change + adapter values + `uv run vero-lite generate
  fleet_maintenance` (console script — never `python -m`).
- The AT-2 signature counter will NOT fire (`tests/services/engine/procedures/
  test_at2_signature_retrigger.py:12-19` counts AT-2 signatures only; this is AT-3).

**Advisory finding (prevents a wrong AC).** `GateAdvisoryBuilder` is **`doa_tier`-only** — its
`build()` takes a `DoaLadder` + `DoaTierVerdict`s (`services/engine/procedures/gate_advisory.py:108-138`,
never-raise). The calm path's single-tier gate has no ladder, so its parked step carries **no
advisory entry**. Expected behavior, not a defect: the PLAN-0085 advisory is a `doa_tier`
feature. AC-2's test asserts the park + resolution, and must NOT expect an advisory.

**Name-collision check.** `PROCEDURE_ARCHETYPES` is keyed by bare `procedure_id` globally — a
known latent bug, filed separately (Out of Scope). The name chosen here, `pm_service_round`,
collides with nothing in the map (`services/api/routers/procedures.py:38-60`, checked).

**⚠ These three citations have a KNOWN EXPIRY — re-read them at execution HEAD, do not trust
the numbers below.** The separately-filed re-keying task is in flight as this PLAN is written,
and it changes exactly the surface this PLAN's one engine line touches: the map's **key shape**
(bare `procedure_id` → `(vertical, procedure_id)`), the `_EXPECTED` fixture
(`tests/api/test_procedures_endpoint.py:29-58`), and the census pin (`:128`, `total == 11 → 12`
as cited here). Whichever lands first, the other's line numbers and the `11` are stale. The
*shape* of this PLAN's change is unaffected — still one mirror entry plus a census bump — but
the executor must open all three files and read the current values rather than copying them
from here. Ordering is not constrained: either may land first.

**The narrative thread (re-read this draft — gitignored
`docs/research/private/2026-07-21-fleet-maintenance-narrative-DIRTY.md`).** The deferral label
"tire/PM" bundles TWO distinct customer threads: (i) the **tire** pain is genuinely *per-tire* —
"ผมไม่รู้เลยนะว่าเส้นไหนวิ่งไปกี่กิโล ยางเก่าหายไปไหนหมด" (which tire ran how many km; old-tire
shrinkage) — per-tire km + lifecycle tracking that no shipped data source can feed (GPS is
per-truck); (ii) the **routine by-interval PM** beat is *per-truck* ("ปกติพวกผ้าเบรก ไส้กรอง…",
and the shipped fixture's own "เปลี่ยนไส้กรองน้ำมันเครื่องตามระยะ" —
`data_adapter/synthetic.py:104-112`) — exactly the AT-3 donor shape, with the measure
(`odometer_km`) already shipping. The narrative gives **no PM numbers** — the due-point values
must come from a logged customer answer or be marked GUESS — รอแก้ (the PLAN-0086 AC-3
provenance convention). This split is what SD-3 adjudicates.

## The measurement protocol (pre-committed BEFORE the build — binding via AC-4)

A measurement designed after the fact is not a measurement. Fixed now, in PLAN-0086's model
(`docs/plans/done/0086-fleet-vertical-timed-manual-scaffold.md:144-166`):

- **M-1 The claim being measured:** the marginal hands-on cost of adding a second governed
  procedure (a calm-path AT-3) to an existing live vertical, hand-ported from a shipped donor
  archetype. The comparable is PLAN-0086's 27m39s create-a-new-vertical figure; the pitch pair is
  "narrative → new governed vertical: ~28 min; adding a routine governed path to it: X min."
  The two numbers are companions, never summed as one workflow.
- **M-2 Arm:** **manual hand-port, no generator** (SD-2 — see the recommendation and its
  rejected alternative). Allowed tooling = the ontology codegen CLI only (`vero-lite validate` +
  `generate`), same as PLAN-0086's protocol rule.
- **M-3 Clock:** starts when Step 2 (intake) begins, after the untimed Step-1 pre-flight; stops
  at the first AC-5 live-park pass (the same finish line as PLAN-0086's AC-2 — comparability).
  If Cray declines the pre-authorized live run at Step 0, the clock stops at AC-2's first green
  instead and the closeout must note the shorter finish line as a comparability caveat.
- **M-4 Granularity:** checkpoint rows at the Step grain (~6 rows: intake / ontology+adapter+
  regen / procedure spine + handlers / wires + census / tests + offline gate / live park), each
  carrying wall and hands-on separately; interruptions and customer-answer waits logged with
  reason and deducted explicitly (the PLAN-0086 AC-6 arithmetic discipline: phase sums ≈ wall,
  deductions itemized). Timing artifact gitignored under
  `docs/research/private/2026-07-NN-fleet-extension-timing-log.md`; the summary table lands in
  this PLAN's closeout.
- **M-5 Intake:** input = the existing dirtied narrative's PM/consumables thread + up to a
  handful of logged customer questions to Cray in-character (expected: the PM rule — service-due
  interval/points). Every question logged with trigger + answer; waits deducted. A real
  extension starts from a customer request, so a small intake round *strengthens* validity
  rather than contaminating it.
- **M-6 The binding honesty caveat (the AC-7 analogue — never quote the number without it):**

  > The measured time is the marginal cost of a governed calm-path extension under **maximally
  > favourable conditions**: the same operator who built the vertical (PLAN-0086), on a codebase
  > they know deeply, hand-porting a shipped donor procedure (procurement's AT-3) into an engine
  > requiring **zero** engine change, from a narrative already read in session 157. It is a
  > **LOWER BOUND** on extension by a fresh operator. It does NOT measure blind intake (that is
  > PLAN-0086's number, with its own caveat), novel-archetype authoring, generator-assisted
  > extension (SD-2's rejected arm — the scaffolder PLAN's experiment), or scheduler onboarding
  > (SD-1's rejected arm). Never present it summed with PLAN-0086's figure as one workflow.

## Surfaced decisions (SD-N — **all three RESOLVED by Cray, 2026-07-22 s161, AskUserQuestion (typed)**; each ratification is recorded inline below. Step 0 is unblocked.)

### SD-1 — Manual or scheduled trigger?

**Question:** does the calm path ship `trigger: manual` (donor:
`verticals/procurement/procedures.yaml:384`) or `trigger: schedule` (donor: `:750-755`)?

**Options:**
- **(a) Manual.** Build = ~100% vertical config + one mirror line; entirely offline-testable;
  the measurement stays clean.
- **(b) Scheduled (nightly odometer sweep).** Genuinely exercises the scheduler seam on a second
  vertical, and is the more honest eventual product story (PM checks are naturally clocked). Full
  verified cost beyond (a): a `schedule:` descriptor; a `service_principals:` block — **fleet
  declares none**, and without one `_resolve_service_principal` raises `SchedulerWiringError` at
  fire time (`services/engine/procedures/scheduler_wiring.py:127-135`); `agent.
  service_principal_ids`; a ~4-line branch in `services/engine/cli.py:120-131` (today the only
  vertical-specific line in the scheduler path, procurement-only, with an already-stale
  docstring); and a **live daemon smoke — host-state, explicit Cray go, never a CI gate**. Note
  `owning_person_id` is NOT required for AT-3 (headless is valid — `services/engine/procedures/
  spec.py:117,:168`; procurement's own AT-3 says so, `verticals/procurement/procedures.yaml:735-741`).

**Recommendation: (a) manual — and the two questions the dispatch asks have DIFFERENT answers,
resolved by sequencing, not merging.** For the *measurement*: the number is "extend an existing
vertical [with a second governed procedure]"; daemon wiring measures a different capability —
"put an existing procedure on a clock" — which procurement already measured separately
(PLAN-0065). Folding it in blurs both numbers into neither, the exact reasoning PLAN-0086 SD-3
used to defer this very work (`0086:227-232`). For the *product*: scheduled is eventually
righter, and (b)'s cost list shows it is a small, well-understood, mostly-config follow-on —
which is precisely why it loses nothing by waiting. Sequence: manual now (this PLAN), a
`scheduled_pm_service_round` follow-on PLAN when the scheduler-on-a-second-vertical story is
wanted, carrying its own small measurement.
**Rejected:** (b) now — it adds the PLAN's only host-state item and its only engine lines while
diluting the mandated measurement.
**Why Cray:** which number the pitch needs next, and whether the daemon story is worth a
host-state run this cycle, is portfolio judgment.

**RESOLVED/RATIFIED (Cray, 2026-07-22 s161, AskUserQuestion): (a) manual.** The measurement
stays clean and the build stays offline; the scheduled variant is a named follow-on PLAN, not
a deletion. Its verified extra cost (the `schedule:` descriptor, the missing
`service_principals:` block, the agent SP ids, the `cli.py` branch, and the live daemon smoke)
is recorded above so that follow-on starts grounded.

### SD-2 — What exactly is measured, and is the AT-3 generator used?

**Question:** define the number's claim and protocol (done — M-1…M-6 above, adopted as AC-4 on
ratification), and decide the generator arm: the AT-3 skeleton is a **shipped** generator
template (`services/engine/procedures/archetypes/template.py:242-254`).

**Options:**
- **(a) Manual hand-port; label the number "manual extension".** Comparable with PLAN-0086's
  manual baseline (same protocol rule: no generator for parts a future scaffolder replaces —
  `0086:104-107`); directly feeds the scaffolder-tool spec (the seam ledger logic); zero
  dependency on unverified generator mechanics.
- **(b) Generator-instantiated skeleton + hand-finish; label it "generator-assisted extension".**
  Arguably the more valuable claim (it measures the shipped tool), but: it breaks comparability
  with the 27m39s manual baseline; whether the PLAN-0040 pipeline cleanly instantiates AT-3 into
  an *existing* vertical's procedures.yaml is **unverified** (a pre-check would be needed); and
  the two arms cannot both be run by one operator — whichever runs first contaminates the other
  (the operator has then already authored/seen the artifact).

**Recommendation: (a).** One clean manual number now, matching the existing baseline's protocol;
the generator-assisted number belongs to the scaffolder-tool PLAN, which needs exactly that
experiment (generated-vs-hand-written diff against an in-tree manual reference — the reason
PLAN-0086 SD-1 committed the vertical). If (b) is chosen instead, the number MUST be labelled
"extend a vertical *with the generator*" everywhere, M-2/M-6 rewritten, and a bounded generator
pre-check added as a Step-0 gate.
**Rejected:** (b) now, and any both-arms variant (order contamination makes the second arm's
time meaningless).
**Why Cray:** which claim the pitch needs — "a human extends it in X minutes" vs "the tool
extends it" — is a positioning call (ADR-0032 D5).

**RESOLVED/RATIFIED (Cray, 2026-07-22 s161, AskUserQuestion): (a) manual hand-port, labelled
"manual extension".** The number stays comparable with PLAN-0086's manual baseline, and this
build becomes the in-tree manual reference the scaffolder PLAN needs for its own diff
experiment. The generator-assisted number is a different claim and belongs to that PLAN.

### SD-3 — Does a tire get its own object type?

**Question:** ride `Truck` with a per-truck service-due field, or model a first-class `Tire`?

**Options:**
- **(a) Ride `Truck`.** Add ONE ontology property — `Truck.next_service_due_km` (float, the
  **absolute** odometer point at which service is due; the `reorder_point` analogue). It must be
  absolute, not an interval: the judge compares `measured_value` vs `threshold_field` directly
  and the projection grammar is fields-only rename — no arithmetic anywhere to compute
  `last_service + interval` (PLAN-0065 SD-2, `verticals/procurement/procedures.yaml:403-409`).
  Project `odometer_km → measured_value`, `direction: above` (due when the odometer reaches the
  due point). ~100% config, closest to the donor, and honest to the *per-truck* narrative thread
  ("ตามระยะ"). Cost of honesty: (a) does **not** address the customer's actual tire pain, which
  is per-tire — so the procedure is named `pm_service_round`, NOT "tire_*"; naming it "tire"
  without a Tire object would be exactly the silently-dropped-half-a-rule failure the vertical's
  README warns against (`verticals/fleet_maintenance/README.md:48-55`).
- **(b) First-class `Tire`** (+ `tire_on_truck` link, adapter records, regen). This IS how the
  customer thinks about the leak ("เส้นไหนวิ่งไปกี่กิโล ยางเก่าหายไปไหน") — but per-tire km
  needs mount/rotation/position data that neither the narrative, the GPS stream, nor any adapter
  source provides; every per-tire number would be invented (violating the vertical's provenance
  discipline) or elicited in a substantial intake round. That turns this PLAN into a second
  narrative-intake experiment — a different, bigger number than the mandated one.

**Recommendation: (a), with the per-tire thread PARKED by name.** Build the per-truck PM path
now; record in the fleet README's expressiveness-gaps register that the customer's per-tire
km/shrinkage pain is *stated but not modelled*, pending design-partner data (a mount/rotation
source). Sub-choice, strikeable by Cray: add **one** third in-service truck (routine
below-ceiling event + a due `next_service_due_km`) inside the timed run so the sweep reads 3
trucks and the calm path isn't a 2-row demo — guarded by AC-3 (if the hero suite goes red from
the extra truck, the truck is dropped, pre-decided here). Proposed fixture shape either way:
truck-02 due (688,140 ≥ a due point of ~685,000 → breach), truck-01 not due — the hero stays
truck-01's story (AT-2 breakdown), the calm path becomes truck-02's (AT-3 PM), values sourced
per M-5/AC-6.
**Rejected:** (b) now — realism theater without a data source; and any "tire"-named variant of
(a).
**Why Cray:** whether the demo narrative needs the customer's literal tire story now (at
intake-round cost) or the honest per-truck PM story (at config cost) is a demo-portfolio call.

**RESOLVED/RATIFIED (Cray, 2026-07-22 s161, AskUserQuestion): (a) ride `Truck`, AND take the
third truck.** The per-truck PM path ships with an absolute `next_service_due_km` (an interval
is unrepresentable — projection is fields-only rename, no arithmetic), named `pm_service_round`
and never `tire_*`. The per-tire thread is PARKED BY NAME in the vertical README's gaps
register — it is a real customer pain with **no data source**, and inventing per-tire values
would violate provenance. The third synthetic truck is IN for demo believability, guarded by
the AC-3 hero suite with the pre-decided drop-if-red fallback.

## Acceptance Criteria

All gates are offline (CLAUDE.md §8 — the offline oracle is the gate); AC-5 is live *evidence*,
never a CI gate.

- [ ] **AC-1 Offline gate + census (owns the census tripwire):** full suite green at execution
  HEAD including the census updates — `_EXPECTED` fleet entry `"pm_service_round": "AT-3"`
  (`tests/api/test_procedures_endpoint.py:29-58`), `assert total == 11` → `12` (`:128`), and the
  `PROCEDURE_ARCHETYPES` mirror entry (`services/api/routers/procedures.py:38-60`) — plus
  `mypy --strict services/` and `ruff check` / `ruff format --check` at CI scope (the whole
  tree, not the changed subset).
- [ ] **AC-2 Calm-path parked run (offline, owns the run-through tests):** an in-memory run of
  `pm_service_round` completes `read_odometer → judge_service_due`, parks `waiting_human` at the
  gated `schedule_service` step with the breach set = exactly the due truck(s), and a human
  resolution completes the run. Donor patterns: `tests/api/test_calm_path_run_endpoint.py`,
  `tests/verticals/procurement/test_calm_path_production_runnability.py`. The parked trace is
  expected to carry **no advisory entry** (`doa_tier`-only —
  `services/engine/procedures/gate_advisory.py:108-138`); the test asserts park + resolution +
  breach-set and does not reference the advisory either way.
- [ ] **AC-3 Additivity (owns the hero guard):** the AT-2 hero suite
  (`tests/verticals/fleet_maintenance/`) green **unmodified**; the shipped pinned-hash /
  governance-pin suites green (parked runs keep resuming — a new procedure and an
  ontology-property addition must not move any existing procedure's hash); `git diff` over the
  change set touches no file of the five other verticals and no engine file beyond the
  `PROCEDURE_ARCHETYPES` mirror line.
- [ ] **AC-4 The measurement (binding — the PLAN-0086 AC-7 analogue):** the run is executed
  under M-1…M-6 *as pre-committed above* — clock boundaries per M-3, checkpoint rows per M-4
  with consistent arithmetic, intake logged per M-5 — and the **M-6 caveat appears co-located
  with the number everywhere it is recorded** (closeout, STATUS, any pitch note). A protocol
  deviation is recorded as a deviation, never retro-fitted into the protocol.
- [ ] **AC-5 Live park (evidence, not a gate):** boot `OCT_VERTICAL=fleet_maintenance` on the
  local demo stack (local uvicorn + local Docker Postgres — per PLAN-0086 Step 6 precedent
  `0086:482-487`: no MS-S1, no host-state change under §8's definition), fire
  `pm_service_round`, confirm the park by reading the persisted run. Pre-authorized by Cray at
  Step 0 so the clock never waits on a go; the clock stops at first pass (M-3). If the go is
  declined, AC-5 is dropped and M-3's fallback finish line applies.
- [ ] **AC-6 Provenance (the PLAN-0086 AC-3 convention):** every newly-authored value
  (`next_service_due_km` values, handler prose, any third-truck fixture) traces to the dirtied
  narrative's PM/consumables thread or to a logged intake answer, or is marked `GUESS — รอแก้`
  in-file; the fleet README gains the calm-path section, and any newly-discovered
  stated-but-not-enforced rule joins its expressiveness-gaps register
  (`verticals/fleet_maintenance/README.md:48-55`).

## Out of Scope

- ❌ **The `PROCEDURE_ARCHETYPES` global re-keying fix** — the bare-`procedure_id` collision
  hazard is real but **filed separately**; this PLAN only picks a non-colliding name.
- ❌ **The scheduled variant** (SD-1(b), if the recommendation holds): schedule descriptor,
  `service_principals` block, `agent.service_principal_ids`, the `cli.py:120-131` branch, and
  the host-state daemon smoke — a named follow-on PLAN.
- ❌ **A first-class `Tire` object** (SD-3(b), if the recommendation holds) — parked pending a
  design-partner per-tire data source; the README records the gap.
- ❌ **The generator-assisted arm** (SD-2(b), if the recommendation holds) — the scaffolder-tool
  PLAN's experiment, not this one's.
- ❌ **Real PM / garage I/O** — `schedule_pm_service` stays a no-op receipt stub
  (`verticals/fleet_maintenance/handlers.py` pattern), pending the design partner.
- ❌ **Event-trigger variant, new trace kinds, new UI surfaces** — existing views and kinds only.
- ❌ **Any engine change beyond the one mirror line** — if the build discovers one is needed,
  STOP and flag (it falsifies this PLAN's zero-engine claim and belongs in the deviation record).

## Steps

### Step 0: SD ratification gate (untimed)

Present SD-1…SD-3 (and the SD-3 third-truck sub-choice) to Cray via AskUserQuestion; record
per-SD stamps (the PLAN-0086 pattern). Obtain the AC-5 live-run pre-authorization in the same
exchange (M-3). Pre-create the gitignored timing artifact with the M-4 checkpoint template. No
implementation before ratification. If any SD lands against its recommendation, apply the
consequence named in that SD (e.g. SD-2(b) → rewrite M-2/M-6 + add the generator pre-check)
before the clock starts.

### Step 1: Pre-flight (untimed)

Working tree clean (stash unrelated drafts — pre-smoke hygiene), baseline full-suite state known
at execution HEAD, donor files identified. No authoring.

### Step 2: Intake (timed — clock starts)

Re-read the dirtied narrative's PM/consumables thread; ask Cray (in-character) the pre-committed
intake question(s) — the PM rule: which services are interval-based and what due points per truck
class — logging trigger + answer per M-5; waits deducted. Values that remain unanswered are
authored as `GUESS — รอแก้` (AC-6).

### Step 3: Ontology + adapter + regen (timed)

Add `Truck.next_service_due_km` (+ description citing provenance) and the
`RecommendedAction.action_type` vocabulary entry `schedule_pm_service` to
`fleet_maintenance_v0.yaml`; set per-truck due values in `synthetic.py` (truck-02 due, truck-01
not; + the third truck if SD-3's sub-choice holds); run `uv run vero-lite validate
fleet_maintenance && uv run vero-lite generate fleet_maintenance` (verify "OK:" + artifact
mtime; all 7 artifacts stay gitignored).

### Step 4: The procedure spine + handlers (timed)

Author `pm_service_round` in `verticals/fleet_maintenance/procedures.yaml` (3 steps, the donor
port): `read_odometer` (query — `reads: [Truck]`, fields-only `project: {fields: {odometer_km:
measured_value}}`) → `judge_service_due` (evaluate — `threshold_field: next_service_due_km`,
`direction: above`) → `schedule_service` (action — `autonomy: gated`, `handler:
schedule_pm_service`, `input: {from: judge_service_due, where: {verdict: breach}}`); `terminal:
schedule_service`; `trigger:` per SD-1. Extend the agent's `action_handlers` allowlist and
`handlers.py` (`ACTION_TYPES` + `ACTION_DESCRIPTIONS`) with `schedule_pm_service`. No SoD, no
doa_tier, no waiver, no compliance criteria — the AT-3 governance signature
(`docs/conventions/procedure-archetypes.md:176-177`).

### Step 5: Wires + census (timed)

The one mirror line (`PROCEDURE_ARCHETYPES["pm_service_round"] = "AT-3"`) + the census-test
update (`_EXPECTED` fleet entry; `total == 12`). Nothing else outside `verticals/fleet_maintenance/`.

### Step 6: Tests + offline gate (timed)

The AC-2 run-through tests (donor patterns) + the AC-3 hero/pin guards, then the full AC-1 gate
(suite / `mypy --strict services/` / ruff at CI scope).

### Step 7: Live park (timed — clock stops at first AC-5 pass)

Local demo-stack boot, fire, read the persisted parked run. No MS-S1, no host-state change.

### Step 8: Closeout (untimed)

Timing summary table + the M-6 caveat into this PLAN's closeout; STATUS entry (caveat
co-located); PR referencing PLAN-0089 (all commits via branch + PR, CLAUDE.md §7). After merge +
Cray confirmation, `git mv docs/plans/0089-*.md docs/plans/done/`.

## Verification

1. AC-2 + AC-5: the calm path runs and parks — the vertical now tells both stories (emergency
   hero + routine PM) on one engine and agent, the same contrast procurement demonstrates.
2. AC-3: the extension is purely additive — the hero, its hashes, and five other verticals are
   untouched; the "extend" claim would be false if extending broke anything existing.
3. AC-4: the number exists, its arithmetic closes, and it can never travel without its caveat —
   the companion figure to PLAN-0086's, honestly labelled.
4. AC-6: every new value has a named source — the vertical's provenance discipline survives its
   first extension.

---

> **Author≠reviewer disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent from a Code-verified session-161 fact-pack; independent review by Code (R2) and Cray
> at PR merge; SD-1…SD-3 ruled by Cray. Separation intact.
>
> **Added beyond the dispatch's scope (drafter's additions, flagged for R2):** (1) the
> narrative re-read splitting the "tire/PM" label into per-tire vs per-truck threads (grounds
> SD-3); (2) the `GateAdvisoryBuilder`-is-`doa_tier`-only finding and its AC-2 consequence;
> (3) the PLAN-0087 declared-criteria delta (zero engine-enum exposure); (4) the intake round
> (M-5) + provenance AC-6, extending PLAN-0086's AC-3 convention to this run; (5) the SD-3
> third-truck sub-choice; (6) the `next_service_due_km` absolute-vs-interval design constraint
> derived from the fields-only projection grammar; (7) AC-5's local-boot-is-not-host-state
> reading, following PLAN-0086 Step 6 precedent rather than the dispatch's blanket live-run
> wording — flagged for Cray, with the Step-0 pre-authorization as the belt-and-suspenders.
