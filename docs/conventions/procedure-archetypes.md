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
| **AT-2** `request→approve→fulfill` | intake → judge → source(scored rule) → compliance(rule gate) → tiered DOA(human) → fulfill(write) → audit | `procurement.emergency_sourcing_round` (manual); `procurement.scheduled_emergency_sourcing_round` (S1 schedule-triggered variant) | per-criterion rule gate + tiered DOA + emergency waiver (escalate-never-skip) + SoD (manual) + traceable audit |
| **AT-3** `monitor→reorder` | read_stock → judge(reorder point) → gated reorder | `procurement.low_stock_reorder_round` (manual); `procurement.scheduled_low_stock_reorder_round` (S1 schedule-triggered) | deterministic reorder-point band + single-tier human approval |

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
- **Governance signature (the credibility musts, L-6):**
  - **Source selection is a scored RULE**, never the LLM (the LLM only summarises
    quotes); on-contract by default, RFQ→AVL only as a logged exception.
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

The routine MRO calm-path: **read stock, judge against a reorder point, reorder
the low set after one human go/no-go.** Structurally close to AT-1 (a band → a
gated action), but the cadence and intent differ — a steady restock loop, not an
anomaly remediation — so it is catalogued distinctly.

- **Shape:** `query (read stock) → evaluate (judge vs reorder point) → action/gated (reorder)`
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
- **Governance signature:** a deterministic reorder-point band; a single human
  approval tier (no emergency waiver, no escalated DOA).

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
- **Remaining frontier — AT-2 generation (deferred, ADR-0024 D7):** the generator
  triangulates AT-1 across 3+ verticals, but **AT-2 is still N=1**
  (`procurement.emergency_sourcing_round` — the only governance-heavy instance;
  the schedule-triggered variant is the same archetype, not a second instance). A
  2nd AT-2-shaped vertical is the Rule-of-Three prerequisite before AT-2 extraction.

## Sources / related

- `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml` — the
  5-facet maps this catalog is derived from (PLAN-0037 Step A).
- `verticals/procurement/README.md` — the procurement 5-facet map table + the
  credibility musts (L-6).
- `docs/plans/done/0037-stage2-facet-retrofit-archetype-catalog.md` — the PLAN
  that produced the instrumentation + this catalog (Step B).
- ADRs: **ADR-016** (procedure engine), **ADR-006** (vertical plugin +
  Rule-of-Three), **ADR-0019** (tiered decision routing / determinism invariant),
  **ADR-0015** (Tier-1 synthetic), **ADR-008** (ontology grammar).
- Memory (Tier 0): `project-vero-ultimate-target-generative-procedures` (the
  3-phase target + template-reuse framing).
