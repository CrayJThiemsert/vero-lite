# PLAN-0084: Map↔Monitor Run Linkage + Seed Rotation

**Status:** Draft
**Owner:** Claude Code (executes + commits per ADR-009 D2)
**Created:** 2026-07-20 (session 155, demo-rehearsal ask)
**Related ADRs:** ADR-0029 (event bridge), ADR-009 D1/D2 (authoring / commit boundary)
**Related PLANs:** PLAN-0052 (Monitor read model — the projection this widens), PLAN-0054 (operate-demo seed), PLAN-0057 (event opener), PLAN-0083 (canonical column renames — the seed's own `asset_id`/`part_id` output keys are its downstream contract, Out-of-Scope there)
**Conventions:** `docs/conventions/ui.md` — canonical for all UI work (ontology-driven: NO hardcoded asset/run ids in JS; `?v=` cache-bust on every edited asset)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1); outline + fact-pack
> originated by Code (session 155), ratified scope by Cray via AskUserQuestion.
> Independent review: Code (R2) + Cray at PR merge.
> **Amended 2026-07-20 (same session, post-#825):** SD-A…SD-E ratifications folded in
> by `plan-drafter` from Code's post-ratification dispatch. SD-B and SD-D were ratified
> WIDER than the draft recommendations — Step 4b and the Step 5 rework are amendment
> content, not annotation. R2 = Code; Cray at PR merge.

## Goal

Make the OCT demo flow coherent across views. Today, seeding a procurement run
(`python scripts/seed_operate_demo.py`) creates a `waiting_human` run visible ONLY in
View H (Monitor); View A (Operational Map) shows the affected asset with no indication
anything is happening, and there is no navigation from the map node to the run. This
PLAN delivers: (1) the map reflects the seeded run on the related asset node, (2) the
node's detail panel offers a button that jumps to the exact run in Monitor, and (3) the
seed script can opt-in ROTATE among the existing CSV assets so repeat rehearsals show
different problem nodes — with the default invocation preserved for the tuned runbook
beats.

## Locked decisions (Cray, AskUserQuestion, session 155 — do not reopen)

- **L-1 Scope = "Flow + หมุน asset เดิม":** build the map↔monitor linkage AND opt-in
  seed rotation over the EXISTING CSV assets. Explicitly REJECTED: creating genuinely
  new objects per seed — that would need a server-side injection endpoint (an
  ungoverned-POST class deliberately not being added). Grounded: objects live in the
  adapter's per-process memory loaded from CSV at boot — `GET /objects/{type}` reads
  `registry.get_adapter(vertical).fetch_objects()` (`services/api/routers/actions.py:197-202`),
  so a separate script process cannot inject them.
- **L-2 Routing:** PLAN-first via plan-drafter (this document); Code reviews + commits
  per ADR-009 D2.

## Verified ground (Code @ HEAD `8439e6d`, re-confirmed by plan-drafter this draft — executor re-verifies before building)

**Seed path**
- `scripts/seed_operate_demo.py` (48 lines; positional `run_id` arg only, no flags) →
  `seed_operate_waiting_human_run(session, run_id=...)`
  (`verticals/procurement/hero_demo/run.py:705`), which runs the YAML
  `emergency_sourcing_round` to the `approve` gate, persisted with
  `trigger_context={"source": "operate-demo-seed", "triggered_by": requester.person_id}`
  (run.py:750).
- `_intake_seed` (run.py:204-241) picks `next(e for e in events if e["event_type"] == "failure")`
  (run.py:217 — **first match; row order becomes load-bearing once multiple failure rows
  exist**), the pinned hero PO `_HERO_PO = "PO-2026-0412"` (run.py:70, used at :219), and
  quotes filtered by the PO's part (run.py:220). `asset_id = req["equipment_id"]`
  (run.py:232) = `AST-CNC-014` — the seeded run ALREADY references an existing map
  object; nothing links back.
- The event-fired builder `build_event_hero_governance_audit` SHARES `_intake_seed`
  (run.py:571), so parameterizing it must default to today's behaviour.

**API read model (PLAN-0052)**
- `trigger_context` is persisted and loadable (run.py:572). The Monitor list model is
  **`RunSummaryView`** (`services/api/models/runs.py:104-128` — the dispatch's
  "RunListItem" name is this class): it already projects `trigger` / `triggered_by`
  from `trigger_context` via `_trigger_of` / `_triggered_by`
  (`services/api/routers/runs.py:152-161`, applied at :231-232 list, :271-272 detail)
  and has NO asset/subject field today.
- The procurement ontology's asset object type is **`Equipment`**, `primary_key:
  equipment_id` (`verticals/procurement/ontology/procurement_v0.yaml:27-28`). Map nodes
  are keyed by each type's pk value from `/meta` + `/objects`, so
  `{"object_type": "Equipment", "primary_key": "AST-CNC-014"}` addresses the node.

**UI seams (shipped precedent)**
- Cross-view events: `assets/app.js:148-158` — `oct:goto` (view B: `ViewAnomaly.setFocus(action)`
  BEFORE `go()` — the pre-mount focus pattern) and `oct:navobj` (→ view A +
  `ViewMap.focusObject`).
- Map flags derive ONLY from `/recommendations` (`assets/view-map.js:74-80`
  `recomputeFlags`; procurement has zero recommendations, so the map shows no problem
  today). `renderDetail` (view-map.js:280-315) already renders an anomaly banner with a
  cross-view button ("Investigate in Anomaly & Decision" → `oct:goto`, :311) — the exact
  pattern for the new "Open in Monitor" button.
- Monitor: `selectRun(id)` exists internally (view-monitor.js:221); exports ONLY
  `{ mount }` (:667-668). Run rows carry `data-testid="run-row-<id>"` (:185). Monitor
  reads `/runs` via its own `getJSON` (:68) — **direct fetch, deliberately NO mock
  fallback** (`state.listData = await getJSON('/runs')` :168).
- `mock.js` `handle()` (:235) covers `/meta`, `/objects/*`, `/recommendations`,
  `/query` — **NOT `/runs`** (grep-confirmed: zero `/runs` matches in mock.js). The
  generic `O.API.request` silently falls back to mock on ANY non-ok/non-JSON response
  (`assets/api.js:37-45`) — so the map's new runs-read MUST use a Monitor-style no-mock
  `getJSON` and degrade to "no run flags", never break the map offline, and never let
  the mock fabricate runs.
- Cache-busting: per-file `?v=` tokens in `services/api/static/index.html` (:9-14 rule
  comment; e.g. `view-map.js?v=c24` at :45) — bump every edited asset.

**Event-fired path (SD-D ground)**
- `POST /demo/hero/event` (`services/api/routers/demo.py:84-96`) →
  `build_event_hero_governance_audit` (run.py:~486-597) fires via the ADR-0029 bridge.
  Its `trigger_context` is stamped **inside the engine**
  (`services/engine/procedures/event_bridge.py:198-204`):
  `{"trigger": "event", "event_kind", "event_key", "entity_ids": sorted(entity_ids), "detected_at"}`
  (+ `"fired_at"` at :316). Engine changes are Out of Scope here — AND the event's
  entity id is `_EVENT_ASSET_ID = "CNC-Line-07"` (run.py:456, a PLAN-0057 OQ-1 pin),
  which matches NO map-node primary key (assets are `AST-*`). Both facts reshape SD-D.

**Rotation constraints (fixtures @ `verticals/procurement/data/hero/`)**
- `asset.csv`: 5 assets — AST-CNC-014 (DOWN, ฿85k/h, CRITICAL); AST-CNC-009 (฿82k/h,
  HIGH — **no PO row**); AST-PRESS-03 (฿120k/h, CRITICAL); AST-ROBOT-21 (฿64k/h, HIGH);
  AST-CONV-05 (฿38k/h, MED).
- `purchase_order.csv`: 4 POs spanning 4 assets — hero PO-2026-0412 (PRT-SPN-700,
  AST-CNC-014, ฿288,000, TIER-CTRL); PO-2026-0407 (PRT-BLT-110, AST-CONV-05, ฿7,200,
  TIER-SUP); PO-2026-0410 (PRT-HYD-450, AST-PRESS-03, ฿19,000, TIER-MGR); PO-2026-0411
  (PRT-SVO-220, AST-ROBOT-21, ฿99,000, TIER-MGR).
- `operational_event.csv`: exactly ONE `failure` event (EVT-CNC-014-FAIL, AST-CNC-014,
  0.92) + one `reading` (EVT-CNC-014-BASE, 0.30, info).
- `quotation.csv`: quotes ONLY for `PRT-SPN-700` (3 rows). Other POs' parts have ZERO
  quotes → the scored_rule has no candidates for them. Rotation is therefore NOT
  config-free: each rotatable asset needs a failure-event row + quote rows for its part.
- `GET /recommendations` derives from `stream_events("reading")` only
  (actions.py:182), so added `failure`-type rows do NOT create recommendations
  (verified — no anomaly-flag side effect on the map).
- Test blast radius (grep of `tests/verticals/procurement/`): no `len(events)`-style
  COUNT pins found; adapter tests select by pk (`test_fastenal_csv_adapter.py:147-149`
  asserts EVT-CNC-014-FAIL's `event_type`), `test_transform_migration_parity.py:67-72`
  uses hardcoded in-test dicts (CSV-independent), BUT
  `test_intake_shadow_parity.py:90` declares the intake filter
  `{"where": {"event_type": "failure"}}` — with multiple failure rows, the declared
  filter vs the hand-coded first-match `next()` can diverge. Named re-check in Step 5.
- Rotation changes the OPERATE beat: different PO totals land different DOA tiers → a
  different approver at the gate (the runbook `docs/runbooks/run-oct-demo.md` "log in as
  appr-pm" beat is tuned to ฿288,000/TIER-CTRL). Default seed behaviour must stay
  byte-identical (see AC-3's precise wording) and rotation is opt-in.

**Post-ratification grounding (Code, s155; re-confirmed on disk by the drafter at amendment time)**
- `link_asset_uses_part.csv` row `LNK-AUP-003,AST-CNC-009,PRT-SPN-700,2` — CNC-009
  already links to the HERO part, so its rotation PO can reuse `PRT-SPN-700` and the
  EXISTING 3 quotations serve it. CNC-009's fixture cost = 1 PO row + 1 failure-event
  row (no new part / quote rows).
- `part.csv`: PRT-SPN-700 (Spindle Bearing Set 70mm) — on-contract ฿42,000 /
  emergency-expedite ฿78,500 per SET.
- The literal `CNC-Line-07` appears in FOUR files repo-wide (drafter re-grep at
  amendment time — the dispatch said three; the fourth is
  `docs/status-archive/2026-h1e-status.md`, also historical): `run.py` (:456), the
  archived `docs/plans/done/0057-event-triggered-hero-opener.md` (DO NOT edit), the
  status archive (DO NOT edit), and this PLAN. **No test pins the literal.** BUT the
  event dedup key / `event_run_id` DERIVES from `entity_ids`, so tests may pin the
  resulting run-id SHAPE without containing the literal — Step 4b's grep covers this
  before assuming zero test churn.

## Surfaced decisions — ALL RESOLVED (Cray, 2026-07-20 s155, AskUserQuestion; per-SD stamps below)

### SD-A — `subject` field shape + exposure surface

**Question:** what shape does the run's subject reference take, and which endpoint(s)
expose it?
**Recommendation:** a typed nested model `RunSubjectRef {object_type: str, primary_key: str}`,
stamped under `trigger_context["subject"]` and projected on **both** the list
(`RunSummaryView` — the map consumes the list) and the detail view (coherence, trivial
to add at routers/runs.py:271-272, and lets Monitor's detail header later say *what*
the run is about). Values are data-driven from `_intake_seed` (`"Equipment"` +
`req["equipment_id"]`), never hardcoded ids.
**Alternatives:** flat keys (`subject_type`/`subject_pk`) — less self-describing;
list-only exposure — saves nothing real and forecloses the detail header.
**Why Cray:** this becomes the demo-visible linkage vocabulary and a
forward-compatible read-model field (PLAN-0052 lineage) — an API-surface commitment.
**RESOLVED/RATIFIED (Cray, 2026-07-20 s155, AskUserQuestion): as recommended** — typed
`RunSubjectRef {object_type, primary_key}` under `trigger_context["subject"]`,
projected on BOTH list (`RunSummaryView`) and detail. PLAN change: none — Step 2
already carries this shape.

### SD-B — which assets become rotatable + the exact fixture rows

**Question:** which of the 4 non-hero assets get rotation fixtures, and what rows?
**Recommendation:** the **3 PO-backed assets** — AST-PRESS-03 (TIER-MGR, ฿19,000),
AST-ROBOT-21 (TIER-MGR, ฿99,000), AST-CONV-05 (TIER-SUP, ฿7,200). Each gets 1 `failure`
event row (asset-matched, measured ≥ 0.8 so the judge bands breach) + 3 quotation rows
for its part (mirroring the hero's 3-quote comparison shape). **Exclude AST-CNC-009**
in v1: it has no PO row, so making it rotatable also means authoring a PO fixture —
wider blast radius (PO rows feed the impact ledger + adapter link tests) for no extra
demo value. Treat the tier spread (SUP/MGR/CTRL) as a demo FEATURE — mid-ladder variety
shows the DOA ladder doing work — mitigating the confusion risk via the Step 5 stdout
line that names the required approver.
**Alternatives:** all 4 (author a CNC-009 PO too); or a minimal single alternate asset.
**Why Cray:** fixture values are demo-narrative content (฿ amounts, tier optics) — the
rehearsal script is Cray's.
**RESOLVED/RATIFIED (Cray, 2026-07-20 s155, AskUserQuestion): ทั้ง 4 ตัว — ALL FOUR
non-hero assets rotatable (WIDER than the 3-asset recommendation; AST-CNC-009 is IN).**
The exclusion rationale is retired by post-ratification ground: CNC-009 already links
to the hero part (`LNK-AUP-003`), so its PO reuses `PRT-SPN-700` + the existing 3
quotes — fixture cost 1 PO row + 1 failure-event row, not a new part/quote set. PLAN
change: Step 5 reworked to 4 assets incl. the CNC-009 PO-reuse design (the ฿/tier
value is a Step-5 authoring choice, not a new SD); AC-7 now covers all 4; AC-8 gains
the impact-ledger PO-read grounding check.

### SD-C — map marker semantics + which statuses light it

**Question:** reuse the red anomaly ring, or a distinct marker; which run statuses count?
**Recommendation:** a **distinct "governed run in flight" marker** (visually separate
from the `/recommendations` anomaly ring — conflating "anomaly detected" with "governed
run awaiting a human" muddies exactly the attribution legibility PLAN-0080 established).
Light it for `waiting_human` + `running`; never for `completed` / `failed` /
`cancelled`. `waiting_human` is the demo state; including `running` costs nothing and
is honest for the brief pre-gate window.
**Alternatives:** reuse the anomaly ring (cheaper, semantic collision); `waiting_human`
only (a running run would be invisible again — the original bug in miniature).
**Why Cray:** the marker is demo-stage vocabulary Cray narrates live.
**RESOLVED/RATIFIED (Cray, 2026-07-20 s155, AskUserQuestion): as recommended** —
distinct "governed run in flight" marker; lights for `waiting_human` + `running`;
never terminal states. PLAN change: none — Step 3 already implements this set.

### SD-D — event-fired path stamping (`POST /demo/hero/event`)

**Question:** should the event-fired run light the map too, and how — given the ground
above (engine-stamped `trigger_context`, engine Out of Scope, and
`entity_ids=["CNC-Line-07"]` matching no map pk)?
**Recommendation:** **(a) defer** — v1 lights the SEED path only; ship the map ingest
filtering on `subject` presence, so event runs simply carry no marker (no error, no
special case). Record the clean future path in this PLAN: **(d)** align
`_EVENT_ASSET_ID` to the ontology pk `AST-CNC-014` so the bridge's existing
`entity_ids` ARE ontology references and a projection-layer mapping becomes honest —
but that changes the event dedup key → `event_run_id` → PLAN-0057 OQ-1 pin + tests +
the beat-1 "sense" cue narrative, a scope of its own.
**Rejected:** (b) projection-layer mapping from today's `entity_ids` — `CNC-Line-07`
would need a hardcoded id map in JS or API (ui.md violation); (c) vertical-side
post-fire mutation of the persisted `trigger_context` — overwrites an engine-owned
provenance stamp from outside the engine, an integrity smell.
**Why Cray:** whether both demo entry points must light the map in v1 is a rehearsal
priority call, and (d) touches a ratified PLAN-0057 pin.
**RESOLVED/RATIFIED (Cray, 2026-07-20 s155, AskUserQuestion): รวม re-pin ใน PLAN นี้เลย —
execute option (d) IN THIS PLAN (WIDER than the defer recommendation); both demo entry
points light the map in v1.** PLAN change: new Step 4b — the `_EVENT_ASSET_ID` re-pin
(vertical constant only; the engine bridge builder stays untouched, so the engine
Out-of-Scope line HOLDS) + the API-side `entity_ids`→`subject` projection-resolve +
the test-surface grep + the PLAN-0057 OQ-1 supersession recorded in this PLAN. AC-2
extended (legacy `CNC-Line-07` runs project `subject=None` fail-soft); new AC-9
(event-path live check); Out-of-Scope last line flipped.

### SD-E — multi-run display on one asset

**Question:** repeat seeds accumulate `waiting_human` runs on the same node — list all
vs cap?
**Recommendation:** panel section lists **newest-first, capped at 5**, with a final
"+N more — open Monitor" line (fires `oct:goto {view:'H'}` without a run id). The node
marker itself lights on ≥ 1 in-flight run (no count badge in v1). Rationale: rehearsal
loops seed repeatedly (the seed script's own docstring: append-only audit log → always
a NEW run); an unbounded list degrades the panel by Thursday.
**Alternatives:** list all (unbounded growth); newest-only (hides the accumulation an
operator might need to cancel).
**Why Cray:** panel real estate during a live demo is a presentation call.
**RESOLVED/RATIFIED (Cray, 2026-07-20 s155, AskUserQuestion): as recommended** —
newest-first, cap 5, "+N more — open Monitor" tail; marker on ≥ 1 in-flight run. PLAN
change: none — Step 3's panel section already specifies this.

## Acceptance Criteria

- [ ] **AC-1 Offline gate:** full suite green (baseline 2915 passed / 7 skipped at
  `8439e6d` — re-baseline at execution HEAD) + `mypy` strict + `ruff` clean, per
  CLAUDE.md §8. Scope = whole tree, not the changed subset.
- [ ] **AC-2 Projection tests:** `subject` present when stamped; `None` for legacy /
  unstamped runs (backward compat with runs already persisted in demo DBs); malformed
  `subject` blobs project as `None` (fail-soft), covered on list AND detail (per SD-A).
  **Extended per SD-D (d):** the Step 4b `entity_ids`→`subject` resolve is covered
  too — an event run whose entity id resolves to exactly one ontology object projects
  that subject; legacy event runs with the OLD `CNC-Line-07` id (already persisted in
  demo DBs) project `subject=None` fail-soft — never an error.
- [ ] **AC-3 Default-seed compatibility:** the default invocation
  (`python scripts/seed_operate_demo.py`) produces a run identical to today's **except
  the additive `trigger_context["subject"]` key**: same intake seed dict, same hero
  PO / part / quotes / ฿288,000 / TIER-CTRL / approver, same run behaviour; zero
  rotation side effects; existing positional `run_id` arg still works. Verified by a
  test asserting the intake seed dict + the non-`subject` trigger_context keys are
  unchanged, and that the default failure-event pick is EVT-CNC-014-FAIL **by
  asset-keyed selection, not row order** (Step 5).
- [ ] **AC-4 Live linkage check (8101 demo):** seed → map shows the marker on the
  correct node → node panel → "Open in Monitor" → Monitor opens with THAT exact run
  selected (`data-testid="run-row-<id>"` focused/selected) — **with the connection
  strip reading `LIVE`** (api.js silently serves mock data on backend errors; a
  `degraded` strip invalidates the check).
- [ ] **AC-5 Graceful degradation:** with `/runs` unreachable, the map renders fully
  with zero run markers — no mock fallback for runs, no console-visible breakage, no
  broken panel.
- [ ] **AC-6 ui.md conformance:** no hardcoded asset/run ids in JS (linkage fully
  data-driven from `/runs` + `/meta`); `?v=` tokens bumped on every edited asset in
  `index.html`.
- [ ] **AC-7 Rotation (ALL FOUR non-hero assets — SD-B as ratified):** `--asset <id>`
  seeds the named asset's PO end-to-end for EACH of AST-CNC-009, AST-PRESS-03,
  AST-ROBOT-21, AST-CONV-05 (scored_rule has real quote candidates — CNC-009 via the
  hero part's existing 3 quotes; run parks at `waiting_human`); stdout names the
  resolved DOA tier + the approver the operator must log in as; an unknown /
  non-rotatable asset id fails with a clear message listing the rotatable ids
  (data-driven from the fixtures, not a hardcoded list).
- [ ] **AC-8 Fixture blast radius:** with the new failure/quote/PO rows,
  `test_intake_shadow_parity` + `test_fastenal_csv_adapter` +
  `test_transform_migration_parity` (and the rest of `tests/verticals/procurement/`)
  pass; `GET /recommendations` output is unchanged (reading-derived only —
  actions.py:182); the impact ledger's ฿ figures are unchanged by the new CNC-009 PO
  row (grounded per Step 5 — whether `build_hero_impact_ledger` reads ALL PO rows or
  only `_HERO_PO`).
- [ ] **AC-9 Event-path live check (8101 demo — SD-D (d)):** `POST /demo/hero/event`
  → map marker lights on AST-CNC-014 → node panel lists the event run → "Open in
  Monitor" opens THAT exact run — **with the connection strip reading `LIVE`** (same
  rigor + silent-mock caveat as AC-4).

## Out of Scope

- ❌ Any server-side object-injection endpoint (L-1 rejection — the ungoverned-POST
  class stays out).
- ❌ Auth/audit on `/runs` or `/query` (the separate read-path-governance candidate,
  s154/s155 analysis).
- ❌ Engine (`services/engine/`) changes of any kind — this exclusion HOLDS under
  SD-D (d): the event bridge's `trigger_context` builder stays UNTOUCHED (it stamps
  whatever `entity_ids` it receives, event_bridge.py:198-204); only the VERTICAL
  constant (`run.py:456`) + the API-side projection (`routers/runs.py`) move.
- ❌ Coupling to the `/recommendations` reactive path (run markers are a parallel,
  independent signal; `recomputeFlags` semantics untouched).
- ❌ Runbook rewrite beyond a short §-note on rotation + approver tiers
  (`docs/runbooks/run-oct-demo.md`).
- ❌ Other verticals (energy etc.) — energy runs simply carry no `subject` and light
  nothing, by construction (same code path as SD-D's defer).
- ~~Event-path map lighting, if Cray ratifies SD-D (a)~~ — **FLIPPED IN SCOPE:**
  SD-D resolved (d)-in-plan (Step 4b + AC-9). Line retained struck-through for the
  amendment audit trail.

## Steps

### Step 0: SD ratification gate

Present SD-A…SD-E to Cray (AskUserQuestion). No implementation before ratification —
SD-B decides fixture content, SD-D decides Step 1's breadth. Record ratified picks in
this PLAN (checkbox edits per step).

**SATISFIED — 2026-07-20 (s155, AskUserQuestion):** all five SDs ratified; resolutions
recorded in the per-SD stamps above. SD-B and SD-D landed WIDER than recommended →
Step 4b (new) + the Step 5 rework below are the resulting amendment content.

### Step 1: Subject stamp on the seed path

In `seed_operate_waiting_human_run` (run.py:705), add
`"subject": {"object_type": "Equipment", "primary_key": seed["asset_id"]}` to the
`trigger_context` (:750) — value taken from the already-computed intake seed (the
`req["equipment_id"]` read, run.py:232), NOT a literal. Additive; existing keys
untouched. Defensive check (project memory `new_governance_pin_field_only_when_supplied`
analog): grep `services/engine/procedures/persistence.py` to confirm `trigger_context`
does not feed any config-pin hash before shipping (expected: it does not — it is run
metadata; if it does, stop and surface).
**Verify:** unit test — seeded run's persisted `trigger_context["subject"]` equals the
hero asset; all pre-existing keys byte-identical (AC-3's test lands here or in Step 5).

### Step 2: API projection (`subject` on the PLAN-0052 read model)

- `services/api/models/runs.py`: add `RunSubjectRef(BaseModel)` (`object_type: str`,
  `primary_key: str`, `Field(description=...)` per §8) + optional
  `subject: RunSubjectRef | None = None` on `RunSummaryView` (:104) and the detail view
  (per SD-A).
- `services/api/routers/runs.py`: add `_subject_of(trigger_context) -> RunSubjectRef | None`
  beside `_trigger_of`/`_triggered_by` (:152-161) — fail-soft on missing/malformed
  (non-dict, missing keys, non-str values → `None`); wire at :231-232 (list) and
  :271-272 (detail).
- No DB/schema change (projection widening only — same posture as PLAN-0052).
**Verify:** AC-2 tests (stamped / legacy-None / malformed-None; list + detail).

### Step 3: Map — runs ingest, marker, panel section

In `assets/view-map.js`:
- Add a Monitor-style `getJSON('/runs')` (view-monitor.js:68 precedent — raw `fetch`,
  JSON-or-throw, **never** `O.API.request`, which silently mocks: api.js:37-45). On any
  failure → empty run set; map otherwise unchanged (AC-5).
- On mount (beside :69-71 loads), fetch runs; build `runFlags: pk → [runs]` from
  entries whose `subject` is present, whose `subject.object_type` is a mapped geo type,
  and whose `status` ∈ the SD-C set. Purely data-driven (AC-6).
- Node rendering: distinct in-flight marker per SD-C (visually separate from the
  anomaly ring class).
- `renderDetail` (:280): after the anomaly banner block (:295-315), add a "Governed
  runs" section when `runFlags` has the node's pk — per run: run id (mono), status
  badge, "Open in Monitor →" button firing
  `document.dispatchEvent(new CustomEvent('oct:goto', {detail: {view: 'H', run: r.run_id}}))`
  (the :311 button pattern); newest-first + cap per SD-E.
- Bump `?v=` for `view-map.js` in `index.html` (:45).
**Verify:** offline JS is exercised by AC-4 (live) + AC-5 (kill `/runs`, e.g. backend
down while static served / temporary 500) — record both observations.

### Step 4: Monitor focus + app wiring

- `assets/view-monitor.js`: export `focusRun(runId)` alongside `mount` (:667-668) using
  the pre-mount focus pattern (`ViewAnomaly.setFocus` precedent, app.js:150): set
  `state.selected = runId` (+ clear stale `detailData`) so the subsequent `mount()`
  path (:660-664 `loadList` → `loadDetail` → polls) renders that run selected.
- `assets/app.js` `oct:goto` handler (:148-154): add
  `if (d.view === 'H' && d.run && O.ViewMonitor && O.ViewMonitor.focusRun) O.ViewMonitor.focusRun(d.run);`
  before `go()` — mirroring the view-B branch.
- Bump `?v=` for `view-monitor.js` + `app.js`.
**Verify:** AC-4 end-to-end click-through; the selected row is `run-row-<id>`.

### Step 4b: Event-path lighting — SD-D (d) re-pin + projection-resolve

*(Amendment content — added when Cray ratified SD-D wider than the draft's defer
recommendation.)*

- **Re-pin the vertical constant:** `_EVENT_ASSET_ID = "AST-CNC-014"` (run.py:456;
  today `"CNC-Line-07"`). This is the VERTICAL's detected-entity id — the engine's
  `event_bridge.py` builder is untouched (it stamps whatever `entity_ids` it receives,
  :198-204), so the Out-of-Scope engine exclusion holds. State this in the PR body.
- **PLAN-0057 OQ-1 supersession — recorded HERE:** PLAN-0057 OQ-1 pinned the detected
  entity as `CNC-Line-07` (spindle-bearing seizure narrative). SD-D (d) supersedes
  that pin with the ontology pk `AST-CNC-014`, so the bridge's `entity_ids` become
  honest ontology references. The archived
  `docs/plans/done/0057-event-triggered-hero-opener.md` and
  `docs/status-archive/2026-h1e-status.md` are historical — DO NOT edit them; this
  paragraph is the durable record of the supersession.
- **Test-surface grep BEFORE assuming zero churn:** no test pins the literal
  `CNC-Line-07` (re-grepped at amendment time — Verified ground), but the event dedup
  key → `event_run_id` DERIVES from `entity_ids`: grep `event_run_id` / `run-event` /
  the dedup-key builder's test surface (`event_bridge` tests + the PLAN-0057
  integration tests) and fix any run-id-SHAPE pins the re-pin moves.
- **Projection half (API-side — allowed):** extend Step 2's `_subject_of`
  (`routers/runs.py`) — when a run has NO `subject` key but `trigger == "event"` with
  `entity_ids`, resolve each id against the ACTIVE vertical's ontology objects
  (`/meta` types + the adapter's object pks — data-driven, NEVER a hardcoded id map,
  ui.md). Exactly one match of a known type → project that subject; zero / ambiguous →
  `None` (fail-soft — legacy `CNC-Line-07` runs in demo DBs resolve to nothing and
  project `None`, never error). With the re-pin, `entity_ids=["AST-CNC-014"]` resolves
  to `Equipment` honestly.
- **Build-time decision (executor decides at implementation — NOT a new SD):**
  resolve cost — per-request adapter scan vs a lazily-built cached pk→object_type
  index. *Drafter recommendation:* the cached lazy index — adapter objects are
  per-process CSV memory loaded at boot (actions.py:197-202), static per process, so
  the index is correct and O(1) per run row on the list endpoint; a per-request scan
  is acceptable if measured trivial at demo scale. Record the pick in the PR body.
- **Beat-1 "sense" cue:** the trigger cue (run.py:591-596) now displays
  `AST-CNC-014` — fold one line into the Step 6 runbook §-note (within its existing
  scope, not a rewrite).
**Verify:** AC-9 live click-through; AC-2's event-projection cases; the test-surface
grep findings recorded in the PR body.

### Step 5: Seed rotation (opt-in CLI + fixtures)

- **Parameterize** `_intake_seed(adapter, *, po_id: str = _HERO_PO)` (or asset-keyed —
  executor's call, but the DEFAULT must be the hero PO so the sharing event builder
  (run.py:571) and the default seed are untouched). Failure-event selection becomes
  **asset-keyed**: match `event_type == "failure"` AND the event's asset ref equal to
  the PO's `equipment_id` — verify the adapter's canonical key name for the event's
  asset ref (PLAN-0083 renames; CSV column `asset_id`) before coding. This removes the
  row-order dependency (run.py:217) for the default path too (AC-3).
- `seed_operate_waiting_human_run(..., asset_id: str | None = None)`: `None` = today's
  behaviour; an asset id resolves to its PO (data-driven from the adapter's
  PurchaseOrder set; ambiguity or no-PO → clear error listing rotatable ids, AC-7).
- `scripts/seed_operate_demo.py`: move to `argparse` — positional `run_id` (optional,
  back-compat), `--asset <id>`, `--rotate` (advance through the rotatable set —
  simplest stateless form: pick pseudo-randomly or by daily index from the non-hero
  rotatable assets; document the choice in `--help`). stdout gains: resolved tier + the
  approver to log in as (read from the parked run's `approve` step `doa_tier` audit —
  `resolved_tier_id` / `resolved_approver_id`, the run.py:541-542 read pattern).
- **Fixtures (SD-B as ratified: ALL FOUR non-hero assets):**
  - AST-PRESS-03 / AST-ROBOT-21 / AST-CONV-05 (already PO-backed): 1 failure-event row
    each (asset-matched, measured ≥ 0.8 so the judge bands breach) + 3 quotation rows
    for each part (PRT-HYD-450 / PRT-SVO-220 / PRT-BLT-110), mirroring the hero's
    3-quote comparison shape.
  - AST-CNC-009 (no PO today): 1 failure-event row + 1 NEW PO row REUSING the hero
    part `PRT-SPN-700` (already linked: `link_asset_uses_part.csv` LNK-AUP-003) so the
    EXISTING 3 quotations serve it — no new part / quote rows. *Step-5 authoring
    choice (Cray can tweak at PR review — NOT a new SD):* propose
    `qty 1 × ฿78,500` (the part's emergency-expedite unit price) = **฿78,500 total →
    expected TIER-MGR** (fixture precedent: ฿19,000 and ฿99,000 both land TIER-MGR),
    distinct from the hero's ฿288,000/TIER-CTRL, so the 5-asset rotation spans
    SUP → MGR ×3 → CTRL. Executor VERIFIES the landed tier against the DOA ladder in
    `procedures.yaml` before pinning the row's `required_tier_id`.
  - All rows follow the EXISTING CSV headers verbatim (the adapter maps to canonical
    names — PLAN-0083). Keep the hero rows byte-identical.
- **Blast-radius re-check (named in Verified ground):** run
  `tests/verticals/procurement/` — specifically `test_intake_shadow_parity` (the
  declared `where: {"event_type": "failure"}` filter vs multi-row fixtures),
  `test_fastenal_csv_adapter`, `test_transform_migration_parity`; plus assert
  `GET /recommendations` unchanged (AC-8).
**Verify:** AC-3 (default byte-compat test), AC-7 (rotated seed live: log in as the
stdout-named approver, resolve the gate), AC-8.

### Step 6: Gate, live verification, runbook note

- Full offline gate (AC-1) on the merge-ready branch.
- Live 8101 walkthrough (AC-4, AC-5, AC-7): Docker Desktop Postgres up
  (`vero-postgres`), demo `DATABASE_URL`, `OCT_VERTICAL=procurement`. Local demo stack
  only — no MS-S1, no host-state change (CLAUDE.md §8).
- `docs/runbooks/run-oct-demo.md`: short §-note — rotation flags, the tier→approver
  table for the rotatable assets, and the "strip must read LIVE" check (Out-of-Scope
  boundary: a note, not a rewrite).
- PR referencing PLAN-0084; after merge + Cray confirmation,
  `git mv docs/plans/0084-*.md docs/plans/done/`.

## Verification

How we know it worked, in one line each:
1. AC-4's click-through succeeds on LIVE (screenshot / transcript in the PR) — the
   original s155 complaint (map blind to the seeded run, no navigation) is gone.
2. AC-3's byte-compat test pins today's rehearsal beats — the runbook's appr-pm flow
   replays unchanged.
3. AC-7 rotated seed shows a DIFFERENT problem node + a different approver tier on a
   second rehearsal pass.
4. AC-1/AC-8 keep the whole tree green — the linkage is additive, nothing regressed.
