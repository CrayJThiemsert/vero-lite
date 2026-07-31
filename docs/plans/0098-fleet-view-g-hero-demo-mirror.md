# PLAN-0098: Fleet View G — the governed-repair hero surface (a `hero_demo/` mirror by function, not by shape)

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-07-31
**Related ADRs:** ADR-0030 (Box-4 ฿ facet — D2 coexist, D3 disclosed assumptions), ADR-0031 (D4 corollary 1 — seam trigger), ADR-0032 (D1.2 mirror licence, D6 cost-class), ADR-0025/0026 (AT-2 spine lineage), ADR-0034 (fleet flow context)
**Drafted-by:** in-harness `plan-drafter` subagent (ADR-013 D1); independent review: Code (R2) + Cray (ratification) — per ADR-012 D4.3. SD-1..3 ratified by Cray (Jirachai Thiemsert) 2026-07-31, session 196. The drafter's AC-6 carve-out (engine-docstring exception) was withdrawn at Code's R2, 2026-07-31 — the debt is paid separately in PR #1000.

## Goal

Give the fleet_maintenance vertical its View G "Governance Moment" — the second
governed hero after `verticals/procurement/hero_demo/` — by mirroring the donor's
**function** (a deterministic offline capture of the real gate audit + a
server-computed ฿ story, bound to the shipped View G frontend) while deliberately
**not** mirroring the donor's ledger **shape**. Fleet has no committed CSV columns
(its entire data layer is `verticals/fleet_maintenance/data_adapter/synthetic.py`;
directory enumerated this session — no `hero_demo/`, no `data/`), so a
procurement-shaped two-sided supplier ledger would have to invent supplier /
lead-time / downtime figures with no partner provenance. Instead, fleet's Box-4
money beat is built on the **already-shipped, partner-grounded**
`fleet_maintenance_economic_impact` producer
(`verticals/fleet_maintenance/economic_impact.py:90-134`, `kind="overpay_avoided"`,
one Cray-ruled disclosed assumption — 15%, s195), elevated from an optional trace
facet to the **required, validator-enforced** money payload of the fleet hero
endpoint. The vertical seam this requires in `services/api/routers/demo.py` is
built under ADR-0031 D4 corollary 1 (`0031-core-lifecycle-architecture.md:148-149`)
with its trigger **fired at N=2**: procurement (shipped) + fleet (this PLAN) both
need a hero-demo binding on the same routes.

## Design decisions (taken in this draft; Cray ratifies the PLAN as a whole)

### D-A — The ledger-basis question, RESOLVED: eliminate the procurement-shaped ledger for fleet; the ฿ beat IS the `EconomicImpact` facet

Where do fleet's ฿ figures come from? **From the event itself plus one disclosed
assumption — via the real registered producer, not a new parallel computation.**
The synthetic hero event carries the measured anchor
(`data_adapter/synthetic.py:284-287`: `measured_value: 48000.0`, `unit: "THB"` —
the ฿48,000 breach quote, narrative-derived per `synthetic.py:14-17`).
`fleet_maintenance_economic_impact` already turns that into a
baseline-vs-governed pair with `net_benefit_thb = ฿7,200` (48,000 × 0.15) and
carries its honesty machinery **in the type**: `EconomicImpact`
(`services/engine/economic_impact.py:50-91`) has a **required** `assumptions`
field, `basis_refs`, `provisional`, and a `model_validator` pinning
`net_benefit_thb == baseline - governed`.

How is "modelling assumption, not measured data" made **structurally** visible?
Three typed properties of the new response model (Step 1), each with a
regression-catching AC:

1. **Measured and modelled ฿ are different fields.** `quoted_repair_thb` (the
   event's own measured value) is a top-level field; every *derived* ฿ lives only
   inside `impact: EconomicImpact` — the model that carries `assumptions`.
2. **The money cannot appear without its assumptions.** `impact` is **required**
   (`EconomicImpact`, not `EconomicImpact | None`) and a `model_validator`
   rejects `impact.assumptions == []`. A future edit that strips the disclosed
   15% assumption makes the endpoint **fail validation** (RED test), never render
   a modelled ฿ as measured (AC-3).
3. **No escape hatch, honestly.** The producer's `None`-on-ungroundable rule
   (`economic_impact.py:9-10, 102-104`) is *kept*, and the wrapper fails loudly
   when it fires: if the pinned hero event cannot ground a figure, the endpoint
   errors — it does not fabricate a side (AC-3b non-vacuity mutation proves this
   RED).

**Rejected Alternative A — clone the two-sided supplier ledger shape.**
Procurement's `ImpactSide` fields (`services/api/models/demo.py:19-31` —
`supplier_id`, `lead_time_days`, `downtime_thb`, `part_cost_thb`) are literally
CSV columns (`verticals/procurement/data/hero/` — 11 committed CSVs; ADR-0030
`:72-76`). Fleet has none of them; filling them means inventing ≥3 modelling
inputs (truck downtime ฿/hr, off-road days per path, a phantom "supplier") with
zero partner provenance — violating `synthetic.py`'s "Never invented" provenance
discipline (`:6-7`) and overstating where the shipped producer deliberately
understates (`economic_impact.py:50-58`).

**Rejected Alternative B — no ฿ beat for fleet at all.** The ฿ story exists, is
the partner's own origin story (three-quote rule adopted after parts fraud,
`sourcing.py:33-36`), is already computed on `main`, and ADR-0032 D1.4 rides the
pilot KPI on exactly this facet. Omitting it wastes shipped, Cray-ratified work.

**Rejected Alternative C — parameterize `HeroImpactLedger`.** Out of authority:
ADR-0030 D2 (`0030-box4-economic-impact-facet.md:147-149`) pins it "stays exactly
as built"; Alternative 3 there (`:334-338`) explicitly rejects generalizing it
("dismantles the deliberate demo/production firewall"); `extra="forbid"`
(`models/demo.py:22,37,74`) makes silent widening impossible anyway.

### D-B — The router seam: a lazy per-vertical hero-builder registry in `demo.py` (ADR-0031 D4 trigger FIRED at N=2)

`services/api/routers/demo.py` today imports six `verticals.procurement.*`
symbols at module scope (`:34-41`) and hardcodes `"procurement"` (`:78-80`). The
seam: a `_HERO_BUILDERS: dict[str, ...]` registry with **lazy imports inside each
registrar**, dispatched at request time on `settings.oct_vertical`
(`services/api/config.py:179-180`) — the exact pattern already proven at
`services/api/main.py:146-160` (`_PROCEDURE_EXECUTOR_REGISTRARS`, lazy imports,
generic `.get(vertical)` at `:188`). This is **not** cited on ADR-0031 alone: the
trigger is fired — two concrete verticals (procurement shipped, fleet in this
PLAN) press the same route surface (D4 corollary 1, `0031:148-149`). A third
vertical adds one `hero_demo/` package + one registrar entry + a frontend copy
branch — no 4-edit engine pain.

Response contract: `GET /demo/hero/impact` becomes
`response_model=HeroImpactLedger | FleetHeroImpact` — a union **at the route
decorator**; neither model is edited (D2 honored). The two models are disjoint by
construction (`extra="forbid"` both sides; `FleetHeroImpact` requires
`vertical: Literal["fleet_maintenance"]`, which is also the frontend
discriminant; `HeroImpactLedger` requires supplier fields fleet never emits).
`GET /demo/hero/governance` keeps `HeroGovernanceAudit` **unchanged** — it is
already vertical-neutral (`models/demo.py:71-85`: `hero` / `contrast` are
`dict[str, Any]`).

Side effect (a win, stated explicitly): booting `OCT_VERTICAL=fleet_maintenance`
no longer imports procurement's 802-line `hero_demo/run.py` at router-import time.

Fallback for a vertical with **no** registered hero (the settings default is
`energy`, `config.py:180`) is **SD-1 — RULED (a)** (Cray, 2026-07-31): fall back
to the procurement builder, as a registry default visible in code; every
existing deck / runbook / energy-boot demo keeps working byte-for-byte.

### D-C — The fleet governance moment: real engine functions over the loaded spec — nothing restated

`verticals/fleet_maintenance/hero_demo/governance_audit.py` mirrors the donor's
discipline (`verticals/procurement/hero_demo/governance_audit.py:1-24`: real
`resolve_doa_tier` + `check_principal_sod` + `GovernedDecision`/`ControlRef`
ties, no LLM, no DB), with the ladder / persons / SoD loaded **from the spec via
`load_procedures`** — the authored source at `procedures.yaml:291-293` (the
0 / 5,001 / 30,001 rungs, Thai roles), `:103-109` (the three principals),
`:354-359` (SoD) — never a re-typed copy, the same never-restate rule
`economic_impact.py:42-45` already applies to the ฿30,000 threshold.

- **Hero:** the ฿48,000 quote → clears the ฿30,001 rung → `เจ้าของกิจการ`
  (owner), SoD governed (`req-mechanic-tom` ≠ approver).
- **Contrast:** the ฿15,000 quote → mid-ladder → `ผจก.เดินรถ` (the deliberate
  tiering row, `synthetic.py:18-22`).
- **The fleet-specific third card:** the `three_quote` rule-gate verdict from the
  **real** `compute_three_quote` (`sourcing.py:71-94`) with its stamped `basis` —
  the partner's own กฎเหล็ก is the beat procurement's audit doesn't have. It
  rides inside the `hero` dict (no model change).

Arms: fleet v1 ships the **offline-fixture arm only** (the gate). `live=true` on
a fleet boot returns a typed HTTP 400 ("no live arm registered for this
vertical") rather than silently serving the offline capture under a live label.

### D-D — Frontend: a fleet branch in `view-hero.js`, keyed on the typed discriminant

`view-hero.js` is structurally reusable — the joiner (`:35-62`) binds only
`doa_tier` / `sod` / `governed_decision`, all of which fleet produces — but its
copy is procurement-hardcoded (`:99, :213, :233, :390, :401-403`). The fleet
branch keys on the impact payload's `vertical` field: fleet nouns
(truck / garage / quote; the partner's principals), a `rule_gate` card, a
two-sided render off `EconomicImpact.baseline/governed` (`EconomicExposure` has
`label` / `exposure_thb` / `components` — enough for the side-by-side idiom at
`:228-238`), and the assumptions strip (placement = SD-2 — RULED
always-visible, Cray 2026-07-31). The `thb`/`thbM`
helpers (`:22-30`) are reused as-is (both verticals are THB). Event-mode and the
live toggle are hidden on the fleet branch (out of scope below). Every touched
asset bumps its `?v=` token in `index.html` (`docs/conventions/ui.md:106-110`).

## Acceptance Criteria

All offline, DB-free by construction (the two fleet GETs take no
`Depends(get_session)`), so **no AC has a silent-skip path** — there is no
DB-dependent test that could no-op without Postgres. The offline suite is the
gate; any preview is evidence only (inheriting
`tests/api/test_demo_hero_routes.py:1-8` verbatim).

- [x] **AC-1 (scenario test — CLAUDE.md §8, named: `tests/api/test_demo_hero_routes_fleet.py`).**
  With the active vertical pinned to `fleet_maintenance`, `GET /demo/hero/impact`
  returns 200 with: `provisional == true`, `vertical == "fleet_maintenance"`,
  `quoted_repair_thb == 48000`, `impact.kind == "overpay_avoided"`,
  `impact.net_benefit_thb == 7200`, `impact.governed.exposure_thb == 40800`,
  `impact.assumptions` non-empty. The figures are produced by the **real chain**
  — `FleetMaintenanceSyntheticAdapter` (`data_adapter/__init__.py:42`) event →
  the real registered `fleet_maintenance_economic_impact` producer → the real
  response model → plain ASGI client — with **no stub anywhere in the chain**;
  the test pins expected literals (the donor pattern,
  `test_demo_hero_routes.py:39-40`), it never recomputes them from the producer's
  own constants.
- [x] **AC-2.** `GET /demo/hero/governance` (fleet): hero resolves ฿48,000 →
  approver role `เจ้าของกิจการ`; contrast resolves ฿15,000 → `ผจก.เดินรถ`; SoD
  verdict governed with two distinct principals; a `three_quote` block present
  with a `basis` emitted by the real `compute_three_quote`. **Parity tripwire:**
  the test independently loads the spec via `load_procedures` and asserts the
  response's band floors equal the spec's ladder floors (set-equality against the
  authored source — a builder that restates a rung goes RED when the YAML moves).
- [x] **AC-3 (the honesty gate).** (a) Constructing the fleet response model with
  `impact.assumptions == []` raises `ValidationError`. (b) When the producer
  returns `None` for the pinned hero event, the endpoint **errors loudly**
  (asserted in-test); it never emits a payload with a fabricated or absent money
  side. Both directions are proven RED by the Step 6 mutations — not merely
  asserted green.
- [x] **AC-4 (donor parity — verification hygiene, not a verdict).** The existing
  procurement suite `tests/api/test_demo_hero_routes.py` passes with its exact ฿
  assertions unchanged, and `git diff` shows **zero edits** to `HeroImpactLedger`
  / `ImpactSide` / `HeroGovernanceAudit` (ADR-0030 D2; additive-only changes to
  `services/api/models/demo.py`).
- [x] **AC-5 (the seam is real).** `services/api/routers/demo.py` carries no
  module-scope `verticals.procurement` import; a subprocess test imports the
  router module fresh and asserts no `verticals.procurement.*` entry appears in
  `sys.modules` until the procurement builder is actually invoked.
- [x] **AC-6 (zero engine build — ADR-0032 D1.2).** `git diff --stat` at R2 shows
  no change under `services/engine/` (checked at review; if implementation
  discovers an engine change is required, that is a **finding to surface**, and
  this PLAN stops for re-ratification rather than absorbing it).
- [x] **AC-7 (frontend presence tripwire + cache-bust).** A Python test asserts
  the fleet branch marker exists in `view-hero.js` and that every asset edited by
  this PLAN carries a bumped `?v=` token in `index.html` (UI tripwires must be
  Python tests — `docs/conventions/ui.md:101-104`). A live preview under
  `OCT_VERTICAL=fleet_maintenance` is **evidence recorded in the PR body, not a
  gate**.
- [x] **AC-8.** Full offline gate green at CI scope: `pytest -q` (full suite),
  `mypy --strict services/`, `ruff` — not the changed subset only.
- [x] **AC-9 (SD-3(c) narrative fence — the fraud story is copy, never a figure).**
  A Python test (AC-7's shape — UI tripwires are Python tests,
  `docs/conventions/ui.md:101-104`) extracts the fleet branch of `view-hero.js`
  and asserts it contains **no hardcoded ฿-figure literal**: no digit sequence
  formatted as money (`฿`/`THB`-adjacent numerics, comma-grouped amounts) in the
  fleet branch's string literals or template copy — every rendered ฿ must flow
  from the API payload through the `thb`/`thbM` helpers (`view-hero.js:22-30`).
  This is the oracle for SD-3(c)'s hard edge: the origin story
  ("เคยโดนช่างโกงอะไหล่ไปเป็นแสน") renders as Thai prose with **no numeral**, so
  the narrative cannot smuggle in a number the payload does not supply.
  **Honest limits:** a static lexical check — it proves no ฿ literal is baked
  into fleet-branch *source*; it cannot prove the rendered DOM shows only
  payload-derived numbers (a runtime computation could still synthesize one),
  and it does not judge copy semantics. Step 6 mutation 4 proves it non-vacuous.

## Out of Scope

- ❌ **A fleet `POST /demo/hero/event`.** The event route (`demo.py:84-96`) and
  the event bridge wiring stay procurement-only; the fleet frontend branch never
  offers event mode. (Today a fleet boot cannot serve it anyway — it requires the
  procurement executor factory.) Follow-on candidate once the fleet case→event
  path warrants a demo opener.
- ❌ **The View H operate seed.** `main.py:191-199` (`if vertical ==
  "procurement"` + `seed_operate_waiting_human_run`) and
  `scripts/seed_operate_demo.py` are PLAN-0054 Step 6c View H scope — explicitly
  **not** re-scoped here, per the dispatch's adjacent-scope ruling.
- ❌ **A fleet live-run arm** (`build_live_hero_governance_audit` analogue).
  Fleet v1 is offline-only; `live=true` → typed 400.
- ❌ **Any edit to `HeroImpactLedger` / `ImpactSide`** (ADR-0030 D2) — including
  adding a discriminator field to them.
- ❌ **A new AT-2 signature.** The fleet ladder is reused unchanged —
  `procedures.yaml:11-14` verbatim ("NOT a 4th AT-2 signature"); ADR-0032 D6's
  cost-class caveat does not bite.
- ❌ **Re-scoping `services/engine/cli.py` or `main.py:146-153`** — both already
  generic (verified: `_PROCEDURE_EXECUTOR_REGISTRARS` includes fleet at
  `main.py:152`; generic dispatch at `:188`).
- ❌ **A fleet CSV dataset.** The synthetic adapter *is* the data layer;
  inventing CSVs to imitate procurement's provenance would be fake provenance.
- ❌ **Retiring the procurement hero or converging the two ฿ shapes** (ADR-0030
  Alternative 3 territory — a later cleanup, if ever).

## Steps

### Step 1: `FleetHeroImpact` response model (additive, `services/api/models/demo.py`)

`extra="forbid"`; fields: `provisional: Literal[True]`,
`vertical: Literal["fleet_maintenance"]`, `currency: str`, `truck_id: str`,
`case_id: str`, `quoted_repair_thb: Decimal` (the measured anchor),
`impact: EconomicImpact` (required). `model_validator`: `impact.assumptions`
non-empty; `impact.currency == currency`. Docstring states the measured-vs-
modelled field split (D-A) and cites ADR-0030 D2/D3. No existing class touched.

Note: `EconomicImpact.kind`'s Field description
(`services/engine/economic_impact.py:64-67`) was corrected to include
`overpay_avoided` in PR #1000 (a separate change, landed before implementation
begins, with a set-equality vocabulary test) — the vocabulary is already
accurate; this PLAN touches nothing under `services/engine/` (AC-6).

### Step 2: `verticals/fleet_maintenance/hero_demo/` package

- `impact.py` — pin the hero event id (the donor's `_HERO_PO` pattern,
  `ledger.py:27`), fetch it through `FleetMaintenanceSyntheticAdapter`, feed the
  **real** producer (imported, never reimplemented), wrap in `FleetHeroImpact`;
  raise (never fabricate) if the producer returns `None`.
- `governance_audit.py` — per D-C: `load_procedures` → ladder + persons + SoD →
  real `resolve_doa_tier` / `check_principal_sod` / `GovernedDecision` ties for
  hero (฿48,000) + contrast (฿15,000), plus the `compute_three_quote` block. No
  ฿ literal from the YAML restated in code (AC-2 parity tripwire enforces).

### Step 3: the router seam (`services/api/routers/demo.py`)

`_HERO_BUILDERS` lazy registry (procurement + fleet_maintenance); move the six
module-scope procurement imports (`:34-41`) into the procurement registrar;
dispatch on `settings.oct_vertical`; `response_model=HeroImpactLedger |
FleetHeroImpact` on `/impact`; a vertical with no registered hero **falls back
to the procurement builder** (SD-1 RULED (a) — the fallback is the registry
default, visible in code; existing energy-boot demos unchanged byte-for-byte);
`live=true` on fleet → typed 400. Cite ADR-0031 D4 corollary 1 +
the fired N=2 trigger in the module docstring.

### Step 4: offline tests (the gate)

`tests/api/test_demo_hero_routes_fleet.py` (AC-1/2/3 assertions; vertical pinned
via settings override in a fixture) + the AC-5 subprocess import test + the AC-7
presence/cache-bust tripwire + the AC-9 no-smuggled-฿ lexical tripwire. Re-run
the untouched procurement suite (AC-4) — SD-1 RULED (a) keeps the procurement
fallback as the default, so the existing procurement tests need no re-pinning.

### Step 5: frontend fleet branch (`view-hero.js` + `hero.css` + `index.html`)

Per D-D, with the SD rulings applied as typed by Cray (2026-07-31):

- **SD-2 (always-visible):** the fleet assumptions strip renders **always
  visible** — never behind the donor's "show provenance" toggle
  (`view-hero.js:179-193`).
- **SD-3 (c — BOTH):** lead with the measured ฿48,000 quote; show ฿7,200 as
  "recovered by comparison (modelled, understated)"; **and** carry the partner's
  fraud origin story ("เคยโดนช่างโกงอะไหล่ไปเป็นแสน", `procedures.yaml:355-356`)
  as **narrative copy only — never as a rendered figure** (AC-9 is the
  tripwire; the copy carries no numeral).

Weak-oracle territory (accelerator clause): copy otherwise stays conservative —
render the partner's principals, never invent a figure the payload doesn't
carry. `?v=` bump on every touched asset.

### Step 6: non-vacuity sweep (each oracle shown RED against a named counterexample)

For each mutation: copy the target file to `/tmp` **first**, apply the mutation,
observe the named test RED, restore **from the `/tmp` copy** (never
`git checkout` — the false-PASS hazard), observe GREEN. Record all four RED
observations in the PR body.

1. Producer emits `assumptions=[]` → AC-3a validator RED (behaviour change: 200 →
   validation error).
2. Hero-event pin swapped to the ฿15,000 event (≤ ฿30,000 → producer returns
   `None`) → AC-3b RED (the no-escape-hatch property is real).
3. Governance builder's top rung hardcoded to `Decimal("50000")` instead of the
   spec-loaded value → AC-2 RED (hero resolves to the wrong role + parity
   tripwire fires — the builder really reads the spec).
4. A ฿ literal (e.g. `฿100,000`) planted in the fleet branch's copy strings in
   `view-hero.js` → AC-9 RED (the no-smuggled-฿ lexical fence really scans the
   fleet branch, not just any file content).

### Step 7: evidence (not gate)

Boot `OCT_VERTICAL=fleet_maintenance`, open View G, screenshot hero + contrast +
rule-gate + ฿ beat; attach to the PR body as evidence. Explicitly **not** a gate
(CLAUDE.md §8 host-state discipline; `test_demo_hero_routes.py:7`).

## Surfaced decisions (SD-N) — RULED by Cray 2026-07-31

All three decisions ruled by Jirachai Thiemsert (Cray), 2026-07-31, session
196. Nothing below is open. Rejected alternatives are retained deliberately —
the reasoning lineage is the point.

- **SD-1 — Fallback for a vertical with no registered hero** (the boot default is
  `energy`, `config.py:180`; today tab G shows the procurement hero regardless).
  **RULED (a) — fall back to the procurement hero** (Cray, 2026-07-31; as
  recommended). Every existing deck / runbook / energy-boot demo keeps working
  byte-for-byte, zero regression; the fallback is a registry default, visible in
  code. *Rejected:* **(b)** typed 404 + a frontend empty state — more honest
  per-vertical, but changes what an audience sees on an energy boot today.
  (This was a Cray decision because it alters live demo behavior —
  business/demo judgment, not derivable from any ADR.)
- **SD-2 — The fleet assumptions strip: always-visible vs behind the donor's
  "show provenance" toggle** (`view-hero.js:179-193`). **RULED —
  always-visible** (Cray, 2026-07-31; as recommended). Rationale as drafted:
  unlike procurement (ledger figures are CSV-column-derived; only the facet is
  provenance), fleet's *entire* governed delta is assumption-derived, so hiding
  the assumption hides the number's nature. *Rejected:* behind the donor's
  toggle. (Cray decision: trust-shape / audience UX — the s74 lineage ADR-0030
  cites.)
- **SD-3 — The fleet ฿ headline.** Fleet's honest net benefit (฿7,200/event) is
  small next to procurement's ~฿8.1M. **RULED (c) — BOTH** (Cray, 2026-07-31).
  **This differs from the draft's recommendation, which was (a) alone; (c) is
  what governs.** The ruling: lead with the measured ฿48,000 quote and show
  ฿7,200 as the understated modelled recovery, **and** additionally carry the
  partner's fraud origin story ("เคยโดนช่างโกงอะไหล่ไปเป็นแสน",
  `procedures.yaml:355-356`) as **narrative copy only — never as a rendered
  figure** (AC-9 oracles that hard edge). *For the record:* **(a)** — the
  draft's recommendation — was the figures-only variant (measured-first,
  understates, matches the producer's own error-direction discipline); **(b)**
  was the origin-story addition on its own. (Cray decision: demo-narrative
  judgment in weak-oracle territory — no test reads copy; AC-9 fences only the
  no-rendered-figure edge.)

## Verification

The Step 4 offline suite is the gate (AC-1…AC-5, AC-7, AC-9 as tests; AC-8 at
CI scope; AC-4/AC-6 as review-time diff checks). Step 6 proves the new oracles
are non-vacuous (four named RED observations recorded in the PR body). Step 7 is
evidence, never a gate. Done = all ACs checked, the SD-1..3 rulings (typed by
Cray 2026-07-31) applied as specified in Steps 3–5, PLAN archived to
`docs/plans/done/` by Code post-merge.
