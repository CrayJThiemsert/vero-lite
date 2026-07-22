# Procedure Archetypes — vero-lite

> The reusable **workflow shapes** observed across vero-lite's instrumented
> verticals. Derived from the SD-4 **5-facet** annotation in each vertical's
> `procedures.yaml` (PLAN-0037 Step A — N=4 instrumented). This catalog is the
> **canonical reference** the Stage-2 generalized procedure schema (the ADR-016
> `facet:` amendment, "Step C") and the Stage-3 procedure generator will cite.

---

## Why this exists

The "generative procedures" target ([`project-vero-ultimate-target-generative-procedures`])
is a 3-phase arc — **generate → run → monitor** — on a generalized procedure
schema. Per **Rule-of-Three** (ADR-006), that schema is extracted only **after**
enough working examples exist. PLAN-0037 brought all four verticals to consistent
5-facet instrumentation (**N=4**); this catalog names the shapes that instrumentation
reveals, so the extraction (Step C) works from a structured substrate rather than
ad-hoc reading.

It is a **descriptive** artifact (it names what already ships), not a prescriptive
one (it does not constrain future procedures). When a 5th vertical lands, extend
the catalog; do not force the vertical to fit an existing archetype.

## The five facets (shared vocabulary)

Every step in every archetype is described by the same five attributes — the
common columns the generalized schema is extracted from:

| Facet | Question it answers |
|---|---|
| **input** | what the step consumes (which prior step's set, or a raw source) |
| **decision-condition** | the rule/band that governs the step (deterministic; never the LLM) |
| **llm-assist** | what (if anything) the LLM drafts/summarises — advisory only |
| **output** | what the step produces |
| **governance** | the gate/control: human approval, determinism invariant, fixed handler, audit |

**Invariant across all archetypes — governed ≠ generated (L-3):** the LLM only
**drafts or summarises**. It never selects (selection is a scored rule), never
sets a threshold (bands are authored), and never approves (humans gate). Every
archetype below preserves this.

## Quick reference

| Archetype | Shape | Instances | Governance signature |
|---|---|---|---|
| **AT-1** `anomaly→action` | sense → judge(band) → gated action on breach | `energy`, `supply_chain`, `aquaculture` (core) | 1 deterministic band; 1 human gate on the irreversible write; handler fixed |
| **AT-1b** `+ watch + summary` (AT-1 variant) | AT-1 **+** watch→gated proposal **+** auto summary terminal | `aquaculture.morning_pond_health_round` | AT-1 + ADR-0019 watch→gated escalation + an auto (un-gated) terminal receipt |
| **AT-2** `request→approve→fulfill` | intake → (judge) → select(scored rule) → compliance(rule gate) → **tiered authority gate**(human) → fulfill(write) → (audit) | `procurement.emergency_sourcing_round` (manual); `procurement.scheduled_emergency_sourcing_round` (S1 schedule-triggered variant); **`supply_chain.cold_chain_excursion_disposition`** (the 2nd SIGNATURE — non-money authority, PLAN-0074); **`building_materials.governed_credit_release`** (the 3rd SIGNATURE — money authority reused, new criterion vocabulary, PLAN-0081); **`fleet_maintenance.governed_repair_approval`** (the 4th SIGNATURE — money authority reused again, `three_quote`, PLAN-0086) | per-criterion rule gate + a tiered human authority gate + SoD + traceable audit. **The authority QUANTITY is per-instance:** ฿ spend (`doa_tier`, procurement + building_materials + fleet_maintenance) or excursion severity (`severity_tier`, supply_chain); **the criterion vocabulary is per-instance too** (vendor-hygiene / GDP / credit-compliance / three-quote) |
| **AT-3** `monitor→reorder` | read(measure) → judge(per-entity threshold) → gated action on breach | `procurement.low_stock_reorder_round` (manual); `procurement.scheduled_low_stock_reorder_round` (S1 schedule-triggered); **`fleet_maintenance.pm_service_round`** (manual — the 2nd VERTICAL to carry AT-3, and the first to band a NON-stock measure, PLAN-0089) | deterministic per-entity band + single-tier human approval |

---

## AT-1 — `anomaly→action`

The minimal OCT loop: **read a signal, judge it against a deterministic band,
act on the breach set after a human go/no-go.** The vertical-agnostic core of
"anomaly detection + suggested action with reasoning trace" (Phase-1 OCT
feature 3).

- **Shape:** `query (read) → evaluate (judge vs band) → action/gated (act on breach)`
- **Instances:**
  - `energy.substation_health_sweep` — read asset temps → judge vs over-temp → gated `restart`.
  - `supply_chain.cold_chain_excursion_sweep` — read shipment temps → judge vs ceiling → gated `hold`.
  - `aquaculture.morning_pond_health_round` (core path) — read DO → judge vs floor → gated `start_emergency_aerator`.
- **Governance signature:** a single deterministic band (the determinism
  invariant, ADR-0019 / ADR-010 IN-3); the action handler is **fixed** (the
  LLM's wider proposal menu is graded separately — the α probe, PLAN-0019 Part
  B); exactly one human gate on the irreversible write.
- **Facet shape:** `read` = pure read (no decision, no llm-assist); `judge` =
  deterministic band, no llm-assist; `act` = fixed handler, llm proposes
  (advisory), human gates.

## AT-1b — `anomaly→action + watch escalation + summary` (AT-1 variant)

AT-1 with two additions: a **second band-routed branch** for the borderline
"watch" zone, and an **auto summary terminal**. The watch branch is the ADR-0019
tiered-routing innovation — the borderline set routes to a *gated proposal* (the
human decides on a concrete machine recommendation) rather than a bare "go look".

- **Shape:** `AT-1 + action/gated (watch→precautionary proposal) + action/auto (summary terminal)`
- **Instance:** `aquaculture.morning_pond_health_round` — breach → gated
  `start_emergency_aerator`; **watch** → gated `increase_water_exchange`; whole
  set → auto `echo` round summary.
- **Governance signature:** AT-1's, **plus** the watch→gated escalation (routing
  trigger = the deterministic verdict, **never** confidence — ADR-010 IN-3),
  **plus** an auto (un-gated) terminal — but the terminal is a no-op `echo`
  receipt artifact, **not** an operational action, so auto autonomy is safe there.

## AT-2 — `request→approve→fulfill`

The governance-heaviest shape: a **governed acquisition** under authority limits,
compliance gates, separation of duties, and audit. Each prior step's output
fans into the next via a named-input `where` filter, narrowing the set as it
passes each gate.

- **Shape:** `query (intake/enrich) → evaluate (judge) → action/auto (source via scored rule) → evaluate (per-criterion compliance gate) → action/gated (tiered DOA approval) → action/gated (fulfill/issue) → action/auto (audit)`
- **Instances:**
  - `procurement.emergency_sourcing_round` (7 steps, `trigger: manual`) — the full hero: SoD + issue_po write gate.
  - `procurement.scheduled_emergency_sourcing_round` (6 steps, `trigger: schedule`, PLAN-0055 Step 8 / ADR-0028 S1) — the **automated** variant. Fired nightly by the scheduler daemon **as a service principal** (`svc-buyer`, run_started `actor_kind:"service"`); it runs the auto steps and PARKS at the DOA human gate — a machine can never approve its own spend (RF-3). Two deliberate deltas from the manual hero, both consequences of being **headless**: (1) **no `separation_of_duties`** — a scheduled run has no human requester (it fires as the service actor, `owning_person=None`), so a requester≠approver split is inapplicable; the governance moment for an automated trigger is the human approval gate itself. (2) It ends at `approve → audit` (no separate `issue_po` gate) — the automated sweep produces an approved, audited sourcing decision; PO issuance follows via the manual flow.
  - `supply_chain.cold_chain_excursion_disposition` (5 steps, `trigger: manual`, PLAN-0074) — **the
    2nd AT-2 SIGNATURE** (the procurement entries above are trigger variants of ONE signature; this
    is a genuinely second one, on a second vertical). A reefer breach routes the affected pharma
    batch to a governed disposition: `intake → assess`(scored rule picks the disposition lane +
    stamps the derived excursion severity) `→ gdp_gate`(rule gate: GDP/GxP quality) `→
    approve`(**`severity_tier`** — human) `→ fulfill`(gated write). **What it proved by being
    different:** the AT-2 authority quantity is **not inherently money**. A cold-chain disposition
    is authorised on **patient-safety / regulatory severity** (how much of the cargo's stability
    budget the excursion burned), which `DoaLadder` cannot represent (money-typed by construction)
    — hence a 4th gate kind + its own typed content model (`SeverityLadder`, ADR-0025 D2 discipline;
    the ADR-0031 D3 gate-kind seam's first concrete pressure). The money is still present (each
    lane has a cost, and the scored rule prices it) — it simply does not authorise. No emergency
    waiver: a waiver is procurement-shaped, and there is no waiving patient safety.
  - `building_materials.governed_credit_release` (6 steps, `trigger: manual`, PLAN-0081) — **the
    3rd AT-2 SIGNATURE** (a governed credit release: a trade customer's outstanding exposure
    breaches ABOVE their approved credit limit on a new order). `intake`(latest exposure per
    account, its credit limit joined on) `→ judge`(per-entity band vs the account's OWN
    `credit_limit_thb`, `direction: above`) `→ reshape`(a declared transform — the L-2 seam that
    derives the flat `amount`/`currency` the authority gate reads from the breach `measured_value`,
    + the credit-compliance signal map) `→ credit_gate`(**`rule_gate`** — KYC / overdue-AR /
    blacklist, blocks on any fail) `→ approve`(**`doa_tier`** — human, SoD: sales requests,
    credit-control approves) `→ fulfill`(gated write). **What it proved by being the 3rd:** it
    REUSES the money `doa_tier` ladder UNCHANGED (฿ authority — no new gate kind, no new authority
    quantity) and grows only the criterion vocabulary (`ComplianceCriterion += {kyc, overdue_ar,
    blacklist}`) — re-confirming the N=2 finding at N=3 (the authority quantity + the compliance
    criteria are per-instance; the GATE shape generalises). The ฿550,000 shipped breach lands
    mid-ladder (`ผจก.ควบคุมเครดิต`, the `[250k, 1M)` tier) — the demo shows tiering, not
    always-the-top.
  - `fleet_maintenance.governed_repair_approval` (6 steps, `trigger: manual`, PLAN-0086) — **the
    4th AT-2 SIGNATURE** (an emergency roadside breakdown: a repair quote above the truck's minor-
    repair ceiling needs governed approval). `intake`(latest event per truck, the truck's
    `minor_repair_ceiling_thb` joined on) `→ judge`(per-entity band vs that ceiling,
    `direction: above`) `→ reshape`(the same declared-transform seam — derives the flat
    `amount`/`currency` + the compliance signal map) `→ quote_gate`(**`rule_gate`** — `three_quote`)
    `→ approve`(**`doa_tier`** — ฿ tiers + emergency waiver, human, SoD: `[intake, approve]`)
    `→ fulfill`(gated write). **What it proved by being the 4th:** by gate SHAPE, nothing — the
    composition and the money authority quantity are byte-identical to building_materials'. What it
    proved was a COST fact: a fourth vertical meant a fourth ENGINE edit to the closed criterion
    enum, and that recurrence — not any generalising gate — is what cancelled the ADR-0025 D7
    deferral (see § Forward — how this feeds the generative-procedures arc). It is also the first
    vertical shipping the PLAN-0085 gate advisory ON.
- **Governance signature (the credibility musts, L-6):**
  - **Selection is a scored RULE**, never the LLM (the LLM only summarises the candidates);
    the pre-qualified default path by default, a deviation only as a logged exception.
  - **Per-criterion compliance** (AVL · tax · cert · sanctions · single-source)
    is a hard rule gate — any failed criterion **blocks the PO**.
  - **Tiered DOA** (delegation-of-authority bands in ฿) escalates the approver to
    the tier the amount demands; the **emergency waiver** relaxes 3-bid/sole-source
    **but escalates the approver + forces a logged justification — it never skips
    a gate**.
  - **Separation of Duties** — requester ≠ approver.
  - **Audit** ties every decision to the control that governed it (traceability).
- **Facet shape:** `auto` appears twice (source, audit) — but `source` is a
  *proposal* whose selection is deterministic, and `audit` is a no-op summary
  artifact; the two operational writes (`approve`, `issue_po`) stay **gated**.

## AT-3 — `monitor→reorder`

The routine calm-path: **read a measure, judge it against that entity's own
threshold, act on the breach set after one human go/no-go.** Structurally close
to AT-1 (a band → a gated action), but the cadence and intent differ — a steady
upkeep loop, not an anomaly remediation — so it is catalogued distinctly.

The measure is **not** necessarily stock. PLAN-0089 generalized the shape: the
band is a per-entity `threshold_field` over whatever numeric the vertical
monitors — units on hand *below* a reorder point, or odometer km *above* a
service-due point. The direction is per-instance; the signature is not.

- **Shape:** `query (read a measure) → evaluate (judge vs a per-entity threshold) → action/gated (act on the breach set)`
- **Instances:**
  - `procurement.low_stock_reorder_round` (3 steps, `trigger: manual`) — the single-tier
    calm contrast to AT-2's hero ladder, on the same engine + agent.
  - `procurement.scheduled_low_stock_reorder_round` (3 steps, `trigger: schedule`,
    PLAN-0065 Step 4 / ADR-0028 S1) — the **automated** calm-path: fired nightly by the
    scheduler daemon as the `svc-buyer` service principal (on behalf of `req-planner`,
    SP-5); it reads stock, judges, and PARKS at the human reorder go/no-go (a service actor
    never reorders past the gate — RF-3). Unlike the AT-2 scheduled variant it carries **no
    `separation_of_duties`** (AT-3 has no DOA tier / SoD), but it DOES carry
    `owning_person_id: req-planner` for accountability parity (the run principal names the
    accountable human; no SoD role consumes it — PLAN-0065 SD-5(b)).
  - `fleet_maintenance.pm_service_round` (3 steps, `trigger: manual`, PLAN-0089) — the **2nd
    vertical** to carry AT-3, and the first instance banding a **non-stock** measure: each
    truck's `odometer_km` is rename-projected to `measured_value` and judged `above` its own
    `next_service_due_km`, so the breach set is the trucks past their service interval. The
    direction is INVERTED versus the procurement instances (stock breaches *below* a floor; an
    odometer breaches *above* a ceiling) — which is what established that AT-3's signature is
    the per-entity band + single gate, not the stock semantics. The routine contrast to the
    same vertical's AT-2 `governed_repair_approval`, on one shared engine + agent. The
    threshold is stored **absolute** (`last_service + interval`), never as an interval: the
    fields-only projection grammar has no arithmetic to compute one.
- **Governance signature:** a deterministic per-entity band; a single human
  approval tier (no emergency waiver, no escalated DOA, no SoD).

---

## Cross-cutting: the band-authoring split (load-bearing for Step C)

The N=4 instrumentation reveals that the `judge` step's deterministic band is
authored **two ways** — the generalized schema (Step C) must model **both**:

| Vertical | `judge` band source | Fields |
|---|---|---|
| `energy` | **ENV** | `OCT_RECOMMEND_THRESHOLD`, `direction=above` — no in-file field |
| `supply_chain` | **ENV** | `OCT_RECOMMEND_THRESHOLD`, `direction=above` — no in-file field |
| `aquaculture` | **IN-FILE** | `threshold:4.0` / `direction:below` / `watch_margin:1.0` |
| `procurement` | **IN-FILE** | `threshold:0.8` / `above` / `watch_margin:0.2` (hero) · `100.0` / `below` (calm) |
| `building_materials` | **IN-FILE** (per-entity) | `threshold_field:credit_limit_thb` / `direction:above` — each account bands vs its OWN limit (ADR-016 FKP) |

Each vertical's `decision-condition` facet states its **actual** source. This is
not an inconsistency to "fix" — it is a real degree of freedom (env-overridable
demo bands vs authored per-procedure bands) the schema must preserve.

## Forward — how this feeds the generative-procedures arc

- **Step C — SHIPPED (PLAN-0038, 2026-06-25):** the ADR-016 D2 amendment promoted
  `facet:` from a YAML comment to a first-class **typed** schema field
  (`services/engine/procedures/spec.py` `Step.facet: StepFacet | None`, with a
  discriminated `decision_condition.gate_kind`) — `Step` keeps `extra="forbid"`
  because `facet` is now a *declared* key. This catalog + the per-vertical 5-facet
  maps were its input.
- **Stage 3 — SHIPPED (ADR-0024 Accepted, PLAN-0040):** the archetype procedure
  generator (`services/engine/procedures/generator/` + the machine-readable
  `ArchetypeTemplate` registry, ADR-0024 D2). The Rule-of-Three gate (≥3 verticals)
  is satisfied (N=4: aquaculture / energy / procurement / supply_chain).
- **Remaining frontier — AT-2 generation (deferred, ADR-0024 D7 / ADR-0025 D7):** the generator
  triangulates AT-1 across 3+ verticals. **AT-2 reached N=4 on 2026-07-21** (PLAN-0086):
  `procurement.emergency_sourcing_round` (money authority) + `supply_chain.cold_chain_excursion_disposition`
  (severity authority) + `building_materials.governed_credit_release` (money authority reused, a NEW
  compliance-criterion vocabulary) + `fleet_maintenance.governed_repair_approval` (money authority
  reused again, `three_quote`) are four distinct SIGNATURES — the schedule/event-triggered
  procurement variants are the same signature, not further instances. **The D7 re-trigger FIRED at
  N=2 and again at N=3, and each time was re-evaluated, not deferred in silence (PLAN-0074 SD-3 /
  PLAN-0081 Step 8, both Cray-ratified):** the generator STAYED deferred + abstaining. **At N=4 the
  D7 deferral was CANCELLED (PLAN-0087)** — and note WHAT cancelled it: not a gate SHAPE finally
  generalising, but the recurring cost of four verticals needing four ENGINE edits to a closed
  criterion enum. The answer was to let a vertical DECLARE its own `rule_gate` vocabulary
  (`VerticalProcedures.compliance_criteria`, membership-validated at load), so a 5th vertical ships
  its gate with zero engine diff. The marker constant is **retired and guards nothing**; what turns
  RED on a 5th signature is the `_BASELINE_SIGNATURES` equality assertion in
  `test_at2_signature_retrigger.py`. The generator **still abstains** on AT-2
  (`generator/pipeline.py` `_AT2_ONLY_KINDS`): N≥2 *permits* the genericization the D7 re-trigger
  guarded, it does not mandate it. What N=2 revealed and N=3/N=4 re-confirmed — the authority
  quantity is per-instance (money vs severity), the compliance criterion vocabulary is per-instance
  (vendor-hygiene / GDP / credit / three-quote), but the GATE shapes generalised unchanged — is the
  input to the remaining extraction question (the procedure-aware `ExecutorFactory`), which is owned
  by **PLAN-0076 T1**, not by this catalog.

## Sources / related

- `verticals/{energy,supply_chain,aquaculture,procurement,building_materials}/procedures.yaml` — the
  5-facet maps this catalog is derived from (PLAN-0037 Step A; building_materials added PLAN-0081).
- `verticals/procurement/README.md` — the procurement 5-facet map table + the
  credibility musts (L-6).
- `docs/plans/done/0037-stage2-facet-retrofit-archetype-catalog.md` — the PLAN
  that produced the instrumentation + this catalog (Step B).
- ADRs: **ADR-016** (procedure engine), **ADR-006** (vertical plugin +
  Rule-of-Three), **ADR-0019** (tiered decision routing / determinism invariant),
  **ADR-0015** (Tier-1 synthetic), **ADR-008** (ontology grammar).
- Memory (Tier 0): `project-vero-ultimate-target-generative-procedures` (the
  3-phase target + template-reuse framing).
