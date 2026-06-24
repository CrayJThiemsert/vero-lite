# PLAN-0036: Fastenal Procurement Vertical (Stage 1) — hand-author the 4th vertical

**Status:** Ready for execution
**Owner:** Claude Code (Tier 2 executes; Cowork drafted per ADR-009 D1)
**Created:** 2026-06-24
**Ratified:** 2026-06-24 — SD-1…SD-5 adjudicated by Cray = **confirm-all** (all as-recommended); lifecycle flipped Draft → Ready for execution by Code (PLAN-0034 prong-1 exempts a Draft lifecycle flip from Stop-hook dispatch).
**Related ADRs:** ADR-016 (governed procedure engine — the spine: `kind`/`autonomy`/set-valued/durable-suspend), ADR-008 (YAML ontology grammar — D1 "may extend"), ADR-0019 (`watch→gated` proposal routing; determinism invariant), ADR-0022 (governed entity resolution — supplier identity on the LLM path), ADR-0023 (registry auto-discovery — a new vertical auto-registers, **zero `services/` core edit**), ADR-006 (vertical-plugin architecture + Rule of Three), ADR-0015 (Tier-1 synthetic Mirror demo), ADR-0021 (metric-kind typed quantities), ADR-005 ("Palantir-lite" OCT positioning)
**Related PLANs:** done/0016 (`vero-lite new-vertical` scaffold — the generator this reuses), 0019 (active — procedure-engine Phase-1 baseline + the aquaculture worked example this mirrors), done/0031 (ORM emitter; B1-DP-1), done/0032 (registry auto-discovery), done/0033 (Phase-C demo-UI story-mode overlay — the SD-3 UI vehicle)

> **Author≠reviewer disclosure (ADR-012 D4.3).** This PLAN was **drafted by
> Cowork** (Tier-1, ADR-009 D1) from Code's session-75 dispatch
> (`.claude/handoffs/session-75/2026-06-24-1456-cowork-procurement-stage1-plan-dispatch.md`).
> The vertical pick, trigger model, object model, 7-step hero chain, credibility
> musts, and UI design (LOCKED L-1…L-8) were **Cray + specialist-settled in Code
> session 75** — they originated outside Cowork. Cowork's role here is faithful
> rendering of the LOCKED design + resolving/flagging the SURFACED decisions
> (SD-1…SD-5); it did **not** self-deliberate the substance in its own free-form
> mode, so the ADR-012 D4.3 self-deliberation case does not arise. The drafter is
> Cowork; the **independent reviewers are Code at R2 review + Cray at ratification**.
> Drafter↔reviewer separation is **intact**. Every code path / file / symbol / ADR
> number cited below was re-verified against the live repo this session
> (fact-pack-first, ADR-009 D1 Tier-1 rule #4); the fact-pack + the validator-gap
> note live in the completion handoff.

## Routing note (read first — structural, NOT a quality finding)

A **new PLAN is mechanically G2-gated** for Code / the in-harness `plan-drafter`
(ADR-009 D1; the G2 PreToolUse gate). This PLAN therefore routes **Cowork-drafts →
Code-commits** (ADR-009 D1/D2) regardless of how solid the design is — it is **not**
a finding that the work has gaps. The LOCKED design (dispatch §3) is **solid and
Cray-reviewed**; this draft does not relitigate it. Code commits the returned draft
via a `feat`/`docs` branch + PR (CLAUDE.md §7) and executes in a feature branch
after Cray ratifies Status: Draft → Ready for execution.

---

## Goal

Hand-author a 4th vero-lite vertical — **Procurement**, instantiated on
automotive / auto-parts manufacturing in the EEC (Chonburi–Rayong) — as a
**pure-config plugin** (ontology extension + `procedures.yaml` + handlers + synthetic
Tier-1 adapter + demo UI), running on the **already-shipped ADR-016 governed
procedure engine** with **zero `services/` core edit** (CQ-1, ADR-0023 auto-discovery).
The headline workflow is **asset-failure → governed emergency sourcing** (criticality
band → source → compliance → tiered DOA approval + emergency waiver → PO → audit),
with a **low-stock reorder** calm-path on the same engine. Stage 1 is the **proving
ground** for vero-lite's ultimate 3-phase generative-procedure platform: it (a) proves
the engine on a real high-value, sellable case, and (b) produces the **first concrete
data point** for the future generalized procedure schema. Per Rule-of-Three (ADR-006):
**author by hand now; extract the schema later (Stage 2); build the generator later
(Stage 3).** This PLAN builds **no generic generator**.

## Strategic frame (where Stage 1 sits)

vero-lite's ultimate target (Cray, 2026-06-23) is a **3-phase generative-procedure
platform**: (1) *pre-process* — generate a procedure from a vertical's context
(= ADR-016 Phase 2, frontier); (2) *process* — run the workflow (= the **built**
ADR-016 engine, D2/D4); (3) *post-process* — a monitoring dashboard (= ADR-016
Phase 3, frontier). The core long-run challenge is a **generalized procedure schema**
(common facets: input · decision-condition · llm-assist · output · governance).

| Stage | What | Status | Vehicle |
|---|---|---|---|
| **1 (this PLAN)** | Hand-author the Fastenal procurement vertical | **build now** | config-layer, this PLAN |
| 2 | Extract the generalized procedure schema from the hand-authored data point | frontier | future ADR-016 amendment |
| 3 | Build the pre-process generator (narrative → procedure) | frontier | ADR-016 Phase 2 |
| 4 | Build the post-process monitoring dashboard beyond the demo mockup | frontier | ADR-016 Phase 3 |

The de-risk dossier (5 Tier-0 docs, `docs/research/private/2026-06-22-procurement-*`,
`…-ai-sourcing-competitor-teardown`, `…-platform-incumbent-deepdive`) concluded:
procurement is **config-layer**, **0 new core amendments**; wedge = governed
asset-event-triggered sourcing; moat = packaging × ICP × price (the "Palantir-lite"
thesis, ADR-005). The pitch leads with **asset-ontology-triggered governed sourcing**
— *not* the now-commoditized "governed" / "cross-vertical" claims.

## CQ-1 — technical de-risk (verified against the live repo this session)

Adding a 4th vertical is **config-pure, zero `services/` core edit**:

- `services/engine/discovery.py` (`discover_and_register()`, `:37`) import-scans
  `verticals/*` at startup via `importlib`/`pkgutil`, invoking each vertical's
  conventional `register_<ns>_adapter` / `register_<ns>_handlers` entry functions
  (ADR-0023 D1/D2). Discovery is **additive, idempotent, failure-isolated, and
  test-resettable** (verified in the module docstring + `_register_vertical`). A
  vertical that lives under `verticals/procurement/` with the conventional entry
  functions is **found and registered with no `services/api/main.py` edit**
  (ADR-0023 D5).
- The `vero-lite new-vertical` scaffold generator exists
  (`services/engine/scaffold.py`; CLI in `services/engine/cli.py`) and emits the
  conventional `register_<ns>_adapter` (`:774`) / `register_<ns>_handlers` (`:802`).
- The procedure spec layer (`services/engine/procedures/spec.py`) already validates
  `agents` + `procedures` + `Step` shapes (`kind`/`autonomy`/`input.where`/`tiers`/
  authored `threshold`/`direction`/`watch_margin`) — procurement authors **config only**.

**One caveat (→ SD-2).** The SQLAlchemy ORM emitter (PLAN-0031) writes to a
**committed central dest** (`services/db/models.py` via `_ORM_COMMITTED_DEST`;
B1-DP-1 resolved Option B). IF procurement needs its own **persisted** ORM models,
the **deferred per-vertical ORM layout** (the B1-DP-1 Rule-of-Three follow-up,
trigger "vertical #2 needs an ORM"; Active TODO) is the single core decision point.
Stage 1 is **synthetic Tier-1 (in-memory adapter, no live DB)**, so this caveat does
**not** fire here — see SD-2.

## SURFACED decisions (SD-1…SD-5) — **ADJUDICATED 2026-06-24 = confirm-all**

Per Tier-1 rule #8 ("surface, do not silently choose"), each carried a recommendation
+ reasoning; the final call was Cray's. **Cray adjudicated all five on 2026-06-24 =
confirm-all** — every SD resolves **as-recommended**; the recommendations below are the
ratified positions. (SD-1 standalone vertical · SD-2 no ORM in Stage 1 · SD-3 reuse the
PLAN-0033 overlay architecture, author procurement surfaces · SD-4 5-facet hypothesis +
comment-only annotation · SD-5 ship the 5 advisory surfaces, defer interactive Q&A.)

### SD-1 — Vertical boundary: standalone vs consume an existing asset vertical's events

**Recommendation: standalone `verticals/procurement/`** with its own asset-trigger
base objects (Code's lean). Reasoning: (a) self-contained matches the ADR-006
plugin pattern + ADR-0023 auto-discovery (drop-in, zero core edit); (b) Phase-1 has
**no cross-vertical event-consumption primitive** — consuming `energy`/`aquaculture`
events would require engine work the engine does not model (out of Stage-1 scope);
(c) a self-contained demo narrative is cleaner to sell. **Trade-off / flag:** this
**duplicates the asset-base objects** (`Equipment`/`Plant`/`OperationalEvent`) that
energy/aquaculture/supply_chain already each declare — a **Rule-of-Three signal** that
an "asset core" base could later be extracted. **Do not extract now** (premature; ADR-006
D4). Log as a cross-vertical abstraction *candidate* for the deliberate abstraction step.
**Cray adjudicated 2026-06-24 = confirm (as recommended).**

### SD-2 — ORM destination (the B1-DP-1 per-vertical-layout trigger)

**Recommendation: procurement needs NO ORM emission for Stage 1 → zero core
touch-point.** Reasoning: Stage 1 runs on the **synthetic Tier-1 in-memory adapter**
(`data_adapter/synthetic.py`, ADR-0015) exactly like aquaculture — it does **not**
exercise the live-Postgres persistence path, so the SQLAlchemy ORM
(`services/db/models.py`) is not touched and the **deferred B1-DP-1 per-vertical ORM
layout decision does not fire**. CQ-1's "zero `services/` core edit" holds intact.
**Flag (forward):** procurement's eventual **Tier-2 real-data path** (out of scope, §
Out of Scope) is precisely the "vertical #2 needs an ORM" trigger that activates the
deferred per-vertical ORM layout — that is the one core touch-point, to be decided in
its own PLAN/ADR at that time, **not** here. **Cray adjudicated 2026-06-24 = confirm (as recommended).**

### SD-3 — Demo UI vehicle: extend PLAN-0033 story-mode overlay vs a new view

**Recommendation: reuse the PLAN-0033 (done) overlay *architecture*, author
procurement-specific surfaces.** Reasoning: PLAN-0033 shipped a proven, additive,
offline `view-story.js` pattern — a **SCENES registry + generic shell** with a
two-tier **Motion** teardown contract, on synthetic Tier-1 data (ADR-0015), coexisting
with Views A–E (never replacing), with the `?v=` static-asset cache-bust convention.
Reusing that architecture (not aquaculture's *content*) gives Stage 1 a battle-tested,
no-new-backend, no-CDN substrate. **Nuance:** L-7's 5 operator surfaces
(worklist · process timeline · approval "money screen" · graduation moment · monitoring
dashboard) are **richer than a linear scene arc** — author them as procurement scenes/
panels within the SCENES/shell pattern (the 5 Code-session-75 mockups are the design
reference). **Flag:** this is "extend the pattern, new content", **not** a brand-new
view system and **not** reuse of aquaculture's scenes. **Cray adjudicated 2026-06-24 = confirm** (incl.
the 5 surfaces ship in the Stage-1 demo per the SD-5 advisory scope — pairs with SD-5).

### SD-4 — Schema instrumentation (the Stage-2 hook) — **load-bearing for the platform thesis**

**Confirm the 5-facet hypothesis** (input · decision-condition · llm-assist · output ·
governance) and define how the hand-authored procedure is **annotated** so Stage 2 can
*extract* the generalized schema from it. The 7 hero steps map cleanly:

| Hero step | kind / autonomy | input | decision-condition | llm-assist | output | governance |
|---|---|---|---|---|---|---|
| intake | query / — | PR / CMMS work-order | — | enrich/auto-fill PR | enriched PR set | — |
| judge | evaluate / — | intake set | **deterministic criticality band** | — | criticality verdict | determinism invariant (ADR-0019) |
| source | action / auto | judge (critical) | **on-contract default; RFQ→AVL exception** | summarize quotes | candidate quote(s) | **selection = scored rule, not LLM** |
| compliance | evaluate / — | source set | **per-criterion** AVL/tax/cert/sanctions/single-source | — | per-criterion pass/fail | blocks PO on fail |
| approve | action / **gated** | compliance pass | **DOA tier band (฿)** | draft justification + exec-summary | approval decision | **tiered DOA + emergency waiver + SoD; human approves** |
| issue_po | action / **gated** | approved | — | — | PO | human-gated write |
| audit | action / auto | full run | — | decision-summary | audit record | ties each row to the control evaluated |

**Cross-check (Stage-2 coverage):** the same 5 facets cover aquaculture's shipped
procedure — `read_do`=input, `judge`(threshold/direction/watch_margin)=decision-condition,
`aerate`/`escalate_watch`=output+governance(gated), `summary`=output. The hypothesis holds
across 2 verticals; procurement is the richer data point.

**Recommendation on the annotation mechanism (a verified hard constraint):**
`services/engine/procedures/spec.py` declares **`Step` with `model_config =
ConfigDict(extra="forbid")`** — so a **first-class `facet:` field cannot be added to a
step without amending the ADR-016 spec (a `services/` core edit)**. Therefore, **Stage 1
annotates via structured YAML comments + this PLAN's facet map** (zero core edit;
preserves CQ-1). Promotion to a **first-class `facet` annotation field** is a **Stage-2
ADR-016 amendment** (out of scope here). This mirrors the precedent where PLAN-0035 /
member-(a) deferred a first-class envelope field and kept the signal trace-only.
**Cray adjudicated 2026-06-24 = confirm** (the 5 facets + the comment-only Stage-1 mechanism confirmed).

### SD-5 — Assist-surface scope for the Stage-1 demo

**Recommendation: ship the high-ROI advisory-LLM core; defer interactive surfaces.**
Per L-3 ("governed ≠ generated" — LLM is assistive only, never selects a supplier /
sets a threshold / approves):

- **Ship (Stage-1 demo):** intake PR auto-fill/enrich (from CMMS), **quote summary**,
  **justification draft**, **approver exec-summary**, audit decision-summary — all in the
  L-7 **"AI draft" visual register** (advisory, editable, distinct accent).
- **Defer:** interactive policy Q&A chatbot and any free-text operator-LLM chat (not
  needed for the round-trip demo).

**Offline-gate note (binding, L-8):** every shipped LLM surface is **faked/scripted in
tests** (the offline gate is the acceptance gate); a **live MS-S1 run is host-state /
Cray-gated, NOT an acceptance gate** (CLAUDE.md §8) — mirroring the PLAN-0033 scene-4
live-vs-scripted treatment. **Cray adjudicated 2026-06-24 = confirm** the ship/defer split (pairs with SD-3).

---

## Acceptance Criteria

> Convention (mirrors PLAN-0035): every AC is **`[impl]`** — it is satisfied by the
> **build** (a `feat` feature branch), **not** by committing this Draft PLAN. This PLAN
> **implements nothing on commit.**

### Vertical authoring (L-4, L-5)

- [ ] **AC-1 `[impl]` — Ontology extension (L-4; ADR-008 D1 "may extend").**
      `verticals/procurement/ontology/procurement_v0.yaml` declares the **6 base
      object_types** (mirror aquaculture: `Equipment`(=Asset) · `Plant`(=Site, geo
      lat/lng floats) · `OperationalEvent`(`event_type ∈ {failure, low_stock, …}`) ·
      `Alert` · `RecommendedAction`(`action_type ∈ {emergency_source, reorder, …}`) ·
      `AlertEventLink` join per ADR-008 D4) **plus** the procurement extensions:
      `Part`(part_no, on_contract, preferred_supplier, stock_qty, reorder_point,
      lead_time) · `Supplier`(avl_status, tax_id, cert_status, sanctions_flag,
      single_source_flag) · `Quotation`(price, currency, lead_time, warranty) ·
      `PurchaseOrder`(amount, status, approver_chain) · `ComplianceRule`(type,
      predicate) · `ApprovalTier`(tier, max_amount ฿, approver_role). Validates via
      `vero-lite validate`; the 5 ontology-artifact emitters (Pydantic models · SQL DDL
      · JSON Schema · MCP tools · TS types) run via `vero-lite generate` **unchanged**;
      the ORM emitter dest is **per SD-2** (no per-vertical ORM in Stage 1).
- [ ] **AC-2 `[impl]` — Hero procedure (L-5; the 7-step chain).**
      `verticals/procurement/procedures.yaml` defines an `Agent`
      (`autonomy_ceiling: auto`, `allowed.action_handlers` covering every action step)
      and a hero `Procedure` (`trigger: manual`, L-8) with the 7 steps **intake**
      (query; LLM-assist enrich) → **judge** (evaluate; deterministic criticality band
      via `threshold`/`direction`) → **source** (action/auto; on-contract default,
      RFQ→AVL exception; LLM-assist quote summary; **selection = scored rule**) →
      **compliance** (evaluate; per-criterion) → **approve** (action/**gated**; DOA
      tiers + emergency waiver + SoD; LLM-assist justification + exec-summary) →
      **issue_po** (action/**gated**) → **audit** (action/auto; LLM-assist
      decision-summary). Uses the set-valued `input.from`/`where` fan-out
      (ADR-016 D4) exactly as aquaculture's `aerate`/`escalate_watch`. Loads + validates
      via `load_procedures("procurement")`.
- [ ] **AC-3 `[impl]` — Calm-path procedure (L-2).** A second `Procedure` on the
      **same engine + agent** for **low-stock reorder** (`low_stock` trigger →
      `reorder` action), the familiar MRO contrast. Contract-expiry + human-PR triggers
      are **deferred** (L-2; § Out of Scope).
- [ ] **AC-4 `[impl]` — Handlers = no-op receipt stubs (L-5).**
      `verticals/procurement/handlers.py` registers the procurement
      `RecommendedAction.action_type` vocabulary (e.g. `emergency_source`, `reorder`,
      `request_approval`, `issue_po`, audit/`echo`) as **distinctly-named no-op
      receipt stubs** (mirror aquaculture `handlers.py`); real ERP/email I/O ships with
      the partner (§ Out of Scope).
- [ ] **AC-5 `[impl]` — Synthetic Tier-1 mirror data (L-8; ADR-0015).**
      `verticals/procurement/data_adapter/synthetic.py` (+ `__init__.py` with
      `register_procurement_adapter`) returns a deterministic, no-randomness timeline:
      a **hero beat** — a critical `Equipment` failure at an **abstract automotive /
      auto-parts plant in the EEC** → emergency sourcing of a critical spare, with an
      **on-contract supplier** path *and* an **off-contract RFQ→AVL exception**, a
      **high-฿ amount** that trips a **DOA tier + emergency waiver**, and per-criterion
      compliance — plus a **calm-path low-stock reorder** beat. **All identifiers
      abstract** (no design-partner brand; wording discipline). Adapter dict keys match
      ontology property names (engine does zero field translation).

### Zero-core-edit + governance invariants (L-3, L-6, L-8, CQ-1)

- [ ] **AC-6 `[impl]` — Auto-discovery, zero `services/` core edit (CQ-1; ADR-0023).**
      The vertical registers via `discover_and_register()` import-scan with **no edit
      to `services/api/main.py`** and **no edit to any `services/` engine file**. A
      `git diff --stat` over `services/` shows **0 changed files** attributable to this
      vertical (the acceptance evidence for CQ-1).
- [ ] **AC-7 `[impl]` — "Governed ≠ generated" spine (L-3).** Tests pin that the LLM
      **never** selects the supplier (selection is the scored rule), **never** sets a
      threshold (authored band), and **never** approves (human gate) — the LLM only
      drafts/summarizes. (Mirrors PLAN-0035's "judge never overrides the floor action".)
- [ ] **AC-8 `[impl]` — Credibility musts (L-6).** DOA **tiered in ฿** (e.g. หน.จัดซื้อ
      ≤฿50k · ผจก.จัดซื้อ ≤฿500k · ผจก.โรงงาน ≤฿2M · ผอ. >฿2M); the **emergency waiver
      escalates** approver authority (never skips a gate) + **forces a logged
      justification**; **on-contract default / RFQ exception** (never RFQ a stocked
      contracted item); **SoD** (requester ≠ approver ≠ receiver ≠ AP); compliance
      **per-criterion pass/fail** blocks the PO. Asserted by tests over the synthetic
      hero run.
- [ ] **AC-9 `[impl]` — No confidence theater (L-6; converges with the s74 demo-card
      decision).** The demo shows decision-relevant signals ("quotes vary 18%, review")
      **not** a self-reported confidence badge; any floor-vs-judge confidence signal
      stays **trace-only** (engine/QA, not an operator badge).

### UI + localization (L-7) — scope per SD-3/SD-5

- [ ] **AC-10 `[impl]` — Three visual registers, no exception (L-7).** Every surface
      renders **AI-assist** (advisory, editable, "AI draft" accent) / **rule-decided**
      (deterministic, locked, names the rule) / **human-approved** (name + role +
      timestamp) distinctly.
- [ ] **AC-11 `[impl]` — Operator surfaces (L-7; SD-3 vehicle).** The demo delivers the
      L-7 surfaces — **(1) worklist/inbox home** (urgency-sorted task queue; demo opens
      here) · **(2) process timeline** (7-step pipeline, bottleneck-first, "⏸ waiting
      for your decision" node, rule gates auto-resolve) · **(3) approval "money screen"**
      (ask + criticality + AI exec-summary [editable] + compliance per-criterion + DOA
      ladder + waiver banner + supplier/RFQ compare + SoD + approve/reject) ·
      **(4) graduation moment** (AI-draft → human edit → approve → state flips to solid
      "human-approved") · **(5) monitoring dashboard** (KPI tiles + emergency-waivers-used
      watched + pending-by-tier + an AI-assist *throughput* panel: "AI drafted N · 0
      supplier-selections · 0 approvals") — built on the PLAN-0033 overlay architecture
      (synthetic Tier-1, offline, no-CDN, `?v=` cache-bust), the **final surface count
      per SD-3 Cray adjudication**.
- [ ] **AC-12 `[impl]` — Real KPIs (L-6).** The dashboard shows req-to-PO cycle time,
      rush-freight premium avoided ฿, stockout rate, maverick spend %, % on-contract —
      each with **value + trend + target** (not a vanity number).
- [ ] **AC-13 `[impl]` — Thai localization (L-7).** Keep EN loanwords (PO · RFQ · AVL ·
      lead time · supplier); Thai-primary + (EN tag) for doc nouns (ใบขอซื้อ ·
      ใบสั่งซื้อ · ใบกำกับภาษี); ฿ + VAT 7% + **พ.ศ.** on documents; visible DOA
      hierarchy (tier + title + ฿); natural code-switched Thai LLM drafts (English part
      terms, Thai prose).

### Stage-2 hook + build gate (SD-4, L-8)

- [ ] **AC-14 `[impl]` — 5-facet instrumentation (SD-4).** Each hero step is annotated
      with its 5-facet mapping (input · decision-condition · llm-assist · output ·
      governance) via **structured YAML comments** (no `spec.py` change — `extra="forbid"`),
      and the facet map (this PLAN's SD-4 table) is captured in the vertical README, so
      Stage 2 can extract the generalized schema. Cross-checked to cover aquaculture's
      procedure.
- [ ] **AC-15 `[impl]` — Build gate (L-8).** `ruff` + `ruff-format` clean;
      `mypy --strict` clean (`services/` untouched); pre-commit (incl. the ontology
      JSON-schema check on `verticals/procurement/ontology/*.yaml`) passes; **full test
      suite green** (existing suite unregressed + new procurement tests). A **live MS-S1
      LLM run is host-state / Cray-gated and is NOT an acceptance gate** — the **offline
      gate is the sole acceptance gate** (CLAUDE.md §8).

## Out of Scope

- ❌ **Generalized procedure schema extraction** — Stage 2 (a future ADR-016 amendment;
  Stage 1 only *instruments* the data point, SD-4).
- ❌ **Pre-process generator** (narrative → procedure) — Stage 3 = ADR-016 Phase 2.
- ❌ **Monitoring-dashboard build beyond the demo mockup** — Stage 4 = ADR-016 Phase 3
  (Stage 1 ships the demo dashboard surface only).
- ❌ **The generic procedure generator** — Rule-of-Three forbids building it before the
  schema is extracted (author by hand first).
- ❌ **Real ERP / email / CMMS handler I/O** — handlers are no-op receipt stubs;
  real integration ships with the partner.
- ❌ **Tier-2 real-partner data + the live-DB persistence path** (dbt/SQLMesh mapping,
  PDPA-safe ingestion, the **per-vertical ORM layout** B1-DP-1 follow-up) — Stage 1 is
  synthetic Tier-1 only (ADR-0015); the Tier-2 path is its own future PLAN/ADR (SD-2).
- ❌ **Contract-expiry + human-PR triggers** — deferred (L-2); Stage 1 ships the
  asset-failure hero + low-stock calm-path only.
- ❌ **Branch / conditional / sub-procedure composition** (e.g. a strategic-sourcing
  sub-flow injected only above ฿X) — ADR-016 Phase 4+ (the spec-probe's "genuine
  limit"); model archetypes as separate procedures instead.
- ❌ **Interactive policy-Q&A LLM chat** — deferred assist surface (SD-5).
- ❌ Any `services/**`, `tests/**` *engine-core* edit, any git operation by Cowork
  (Code-only, ADR-009 D2).

## Steps

> Execution is Code's lane (ADR-009 D2), in a feature branch after Cray flips Status →
> Ready for execution. Order chosen so each step is independently PR-able and the
> vertical is runnable as early as possible (mirrors PLAN-0016's sequencing).

### Step 1 — Scaffold the vertical skeleton
Run `vero-lite new-vertical procurement` (`services/engine/scaffold.py` /
`cli.py`) to emit the package skeleton (`ontology/`, `data_adapter/__init__.py` with
`register_procurement_adapter`, `handlers.py` with `register_procurement_handlers`,
`__init__.py`). Confirm auto-discovery picks it up (`discover_and_register()` returns
`procurement`) **with no `services/api/main.py` edit** (AC-6).

### Step 2 — Author the ontology (AC-1)
Write `verticals/procurement/ontology/procurement_v0.yaml`: the 6 base object_types
(mirror `aquaculture_v0.yaml`, Asset→`Equipment`, Site→`Plant`) + the 6 procurement
extension object_types + their `link_types` (ADR-008 D2/D4). `Plant` carries geo
lat/lng floats (Site role). Run `vero-lite validate` + `generate` (6 emitters
unchanged; ORM dest per SD-2 — no per-vertical ORM in Stage 1).

### Step 3 — Author `procedures.yaml` (AC-2, AC-3, AC-14)
Define the `Agent` (`autonomy_ceiling: auto`; `allowed.step_kinds` +
`action_handlers`) and the **hero** 7-step procedure + the **calm-path** reorder
procedure, using `input.from`/`where` set fan-out and authored `threshold`/`direction`
on `judge`. Annotate each step's 5-facet mapping as **structured YAML comments**
(SD-4 / AC-14 — no `spec.py` change). Validate via `load_procedures("procurement")`.

### Step 4 — Handlers as no-op receipt stubs (AC-4)
Author `verticals/procurement/handlers.py` registering the procurement action-type
vocabulary as distinctly-named no-op stubs (mirror aquaculture's
`_stub_action_handler` pattern) + `echo`.

### Step 5 — Synthetic Tier-1 mirror data (AC-5)
Author `data_adapter/synthetic.py`: deterministic hero timeline (critical Equipment
failure → emergency sourcing, on-contract + RFQ→AVL exception, high-฿ DOA + waiver,
per-criterion compliance) + calm-path low-stock beat. Abstract identifiers only. Env
block (`OCT_VERTICAL=procurement`, `OCT_RECOMMEND_*`, recovery values) in the README.

### Step 6 — Demo UI surfaces (AC-10…AC-13; SD-3/SD-5 scope)
On the PLAN-0033 `view-story.js` SCENES/shell + Motion-teardown architecture (additive
overlay, synthetic Tier-1, offline/no-CDN, `?v=` cache-bust), author the L-7 operator
surfaces with the three visual registers, real KPIs, and Thai localization. Final
surface count + assist-surface set per the SD-3/SD-5 Cray adjudication.

### Step 7 — Tests (AC-7, AC-8, AC-9, AC-15)
Offline tests (LLM faked): governed-≠-generated invariants (AC-7), DOA/waiver/SoD/
on-contract/per-criterion-compliance (AC-8), no-confidence-theater (AC-9), the hero +
calm-path runs end-to-end on the synthetic data, and the `services/` zero-diff check
(AC-6). Full suite green; ruff + ruff-format + mypy --strict clean (AC-15).

### Step 8 — Docs + closeout
`verticals/procurement/README.md` (problem · decision · run env · the SD-4 facet map),
a `run-oct-demo` runbook section for the procurement walkthrough, STATUS update, and
`git mv docs/plans/0036-*.md → docs/plans/done/` on completion (Code's lane, ADR-009 D2).

## Verification

- **AC-1…AC-5, AC-14:** `vero-lite validate` + `generate` clean; `load_procedures`
  validates; the hero + calm-path procedures load + run on the synthetic adapter; the
  facet annotations present + the README facet map cross-checks aquaculture.
- **AC-6 (CQ-1):** `git diff --stat services/` shows 0 vertical-attributable changes;
  `discover_and_register()` returns `procurement`.
- **AC-7…AC-9, AC-15:** `pytest` — governed-≠-generated + credibility-must + no-confidence
  invariants green; existing suite unregressed; ruff + ruff-format + mypy --strict clean;
  pre-commit (ontology JSON-schema) passes. **Offline gate is the acceptance gate.**
- **AC-10…AC-13:** the 5 surfaces render the three registers + real KPIs + Thai
  localization (preview workflow / DOM+a11y probes, per PLAN-0033's verification method).
- **Host-state (NOT an acceptance gate):** any live MS-S1 LLM run for the assist
  surfaces is **Cray-gated** (CLAUDE.md §8); minimize live runs; the offline oracle is
  the gate.

---

*Drafted (uncommitted) by Cowork (Tier-1, ADR-009 D1) from Code's session-75 dispatch.
Author≠reviewer disclosure above (ADR-012 D4.3). Code R2-reviews against the dispatch +
commits via PR (ADR-009 D2); Cray ratifies Draft → Ready for execution. AI-assisted
(Claude); no `Co-Authored-By` per CLAUDE.md §7. Number `0036` confirmed free at authoring
— highest PLAN number anywhere is **0035** (`docs/plans/done/0035-…`); active set =
{0004, 0010, 0012, 0019, 0027}; no `0036` collision (Glob this session). Code confirms
at commit.*
