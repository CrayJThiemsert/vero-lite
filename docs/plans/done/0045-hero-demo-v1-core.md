# PLAN-0045: Hero-demo v1 core build (C1 adapter · governance-moment render · ฿-impact ledger)

**Status:** Complete (2026-07-01, session 92) — moved to `done/`
**Owner:** both (Code executes; Cray ratifies the SDs first)
**Created:** 2026-06-30
**Related ADRs:** ADR-006 (vertical plugin), ADR-007 (DataAdapter), ADR-0023 (registry auto-discovery), ADR-0025 (AT-2 / DOA tiers), ADR-0026 (governed_decision / OQ-5 audit-to-control); PLAN-0039/0042 (read-only procedure viewer), PLAN-0043/0044 (A1b principal-SoD + render contract)

> ## Completion (2026-07-01, session 92)
>
> **Hero-demo v1 core is COMPLETE** — all eight acceptance criteria met on `main`, offline gate
> green (`ruff` + `mypy --strict` + `pytest`; no live MS-S1, §8). The build went BEYOND the
> SD-1=(b) fixture recommendation to a live-run layer (C-3 `run_hero_governance_moment` drives the
> real orchestrator loop; C-4 `?live=true` toggle; C-5 Cray-approved live MS-S1 smoke confirmed
> `governed == offline`).
>
> | AC | Shipped by |
> |----|-----------|
> | AC-1 (C1 `FastenalCsvAdapter` round-trip) | #493 Step 1 (`85eafaa`) |
> | AC-2 (zero `services/` core edit) | #493 |
> | AC-3/4/5 (governance-moment render — DoaTier / SoD / `governed_decision` join, no reshape) | #493 Step 1b/2 + the render `view-hero.js` |
> | AC-6 (B1 ฿-impact ledger, provisional) | #493 Step 3 (`b76c080`) |
> | AC-7 (contrast case PO-2026-0411 → MANAGER, data-driven) | #493 |
> | AC-8 (offline gate — ruff + mypy --strict + pytest) | ✅ throughout |
>
> **Surfaced-decision dispositions:** SD-1 resolved beyond (b) — a real live-run layer landed
> (#496 C-3/C-4; the C-1 fixture path is the offline fallback). SD-2 = the `view-hero.js`
> governance-moment screen (reused the read-only viewer's decomposition seam). SD-3 = (a) the
> derived `GET /demo/hero/impact` API view.
>
> **Out-of-scope items stayed out:** the `rule_gate`/`scored_rule` A1b work (PLAN-0044); the
> hero-demo `compliance` harness→`rule_gate`-executor swap is an OPTIONAL follow-up (not an AC of
> this PLAN). B2 real Fastenal numbers + the hybrid LLM-extraction path remain deferred.

> **Drafting note (author≠reviewer, ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent under ADR-013 D1 phased authority; outline originated by Code (session 88 dossier);
> independent reviewer = Cray at PR merge. Separation INTACT.
>
> **Three Surfaced Decisions (SD-1 RUN path, SD-2 render composition, SD-3 ledger home) are NOT
> ratified.** The Steps below carry the recommended option as load-bearing but contingent — Cray
> adjudicates before execution. SD-1 is the gating decision for the whole demo flow.

## Goal

Build the three CORE pieces of hero-demo v1 (`narrative → governed → run → ฿`, Cray-LOCKED scope,
dossier §3/§8) on the Fastenal/procurement anchor: **C1** a real `FastenalCsvAdapter` feeding the
canonical demo dataset (5 object + 2 link CSVs) through the existing `DataAdapter` protocol with
**zero `services/` core edits** (mirror procurement CQ-1 / ADR-0023 auto-discovery); the **governance-
moment render** — a NEW demo screen that, on a run hitting the AT-2 gate, displays the three SHIPPED
A1b structured fields (`DoaTierVerdict`, `PrincipalSoDVerdict`, `governed_decision`) joined on their
shipped keys, **no reshape**; and **B1** the ฿-impact ledger (baseline on-AVL exposure → governed
off-AVL decision), computed from dataset columns. Offline is the gate (ruff + mypy --strict + pytest;
NO live MS-S1, CLAUDE.md §8).

## Acceptance Criteria

- [ ] **AC-1 (C1 ingest):** `FastenalCsvAdapter` conforms to `DataAdapter`
      (`services/engine/data_adapter.py:24`); `fetch_objects` returns the 5 object types
      (`Asset`/`Part`/`Supplier`/`PurchaseOrder`/`ApprovalTier`) and `fetch_links` returns the 2
      explicit link types **+** the 4 inline-FK links synthesized from `purchase_order.csv`
      (`po_references_part`, `po_sourced_from_supplier`, `po_for_asset`, `po_requires_tier` —
      dataset §"ingestion mapping"). Round-trip test: CSV → adapter dicts → assert hero rows
      (`AST-CNC-014`, `PRT-SPN-700`, `PO-2026-0412` total 288000, `TIER-CTRL`).
- [ ] **AC-2 (zero core edit):** the diff touches only `verticals/` (+ a demo screen + tests);
      grep-assert no change under `services/engine/procedures/*` or `services/engine/*.py` core
      (registration is explicit `register_*_adapter`, mirror procurement `__init__.py`).
- [ ] **AC-3 (governance moment — DoaTier):** the screen renders, from `audit["doa_tier"]`,
      `amount ฿288,000` > Manager band `[15001,200000]` → `resolved_tier_id=TIER-CTRL`,
      `required_role=CONTROLLER`, `sod_required=true` — using the SHIPPED `DoaTierVerdict` shape
      (`doa_tier.py:59`; `amount{value,currency}` Decimal-as-str, `band{min,max|None}`), no reshape.
- [ ] **AC-4 (governance moment — SoD):** renders the SoD verdict (`PrincipalSoDVerdict`,
      `principal_sod.py:75`) showing requester `MAINT_PLANNER` ≠ approver `CONTROLLER` satisfies the
      distinct-principals constraint.
- [ ] **AC-5 (governance moment — governed_decision join):** renders `audit["governed_decision"]`
      (`action_step.py:311-330`, each `{control_ref:{kind,id}, principal_id}`) and joins on the
      EXACT shipped keys: `control_ref.id == resolved_tier_id` (doa_tier route) or the sorted distinct_steps
      (sod route); `principal_id == Person.person_id` (`spec.py:629`). No fuzzy matching.
- [ ] **AC-6 (B1 ฿-impact):** the ledger shows baseline (on-AVL wait, ~฿9.76M exposure) → governed
      (off-AVL emergency, ~฿1.65M exposure), computed from dataset columns
      (`downtime_cost_per_hour_thb`, lead-time days, `on_contract_unit_price_thb` /
      `quoted_unit_price_thb`, qty); expedite premium ฿52,500 derivable. **All figures labelled
      provisional / demo-grade** (dossier §10).
- [ ] **AC-7 (contrast case):** `PO-2026-0411` (฿99,000 emergency) renders as `TIER-MGR`, NO
      Controller escalation — proving the gate is data-driven, not hardcoded.
- [ ] **AC-8 (offline gate):** `ruff` clean · `mypy --strict` clean · `pytest` green for the new
      adapter + render-contract + ledger tests. No live MS-S1; the offline oracle is the gate.

## Out of Scope

- ❌ **Hybrid LLM-extraction** (free-text → LLM-extract → attest) — DEFERRED Sovereign-AI follow-on
  (dossier §7/§10); step-3 ships manual-structured first. Not this PLAN.
- ❌ **`emergency_override` / `post_hoc_review` gate + attestation** — separate AT-2 ADR (dossier §6/§9).
- ❌ **Measurement / KPI · notification/reporting · data-trigger / kanban / monitor dashboard.**
- ❌ **Deep P2P controls** (AVL→budget→three-way match; SoD conflict matrix; WHT/VAT) — C2/AT-2 ADRs.
- ❌ **AC-9 hardening + A1b Steps 2/4/5** (rule_gate/scored_rule). **Do NOT touch
  `services/engine/procedures/*`** — the concurrent session owns the remaining A1b work.
- ❌ **B2 real Fastenal numbers** — demo-grade provisional figures only (a later `verticals/` PR; Cray supplies).
- ❌ The questionnaire screen (separate product PLAN).

## Steps

### Step 1: C1 — `FastenalCsvAdapter` (verticals/, zero core edit)
Add `verticals/procurement/data_adapter/fastenal_csv.py` (a real CSV-backed `DataAdapter` alongside the
synthetic one) + the canonical CSVs as a committed demo fixture under `verticals/procurement/data/hero/`.
Mirror the procurement `__init__.py` registration shape (`register_fastenal_csv_adapter` →
`registry.register_adapter`; explicit, ADR-0023 / CQ-1). Implement `fetch_objects` (per-file dict
mapping, dataset §ingestion), `fetch_links` (2 explicit link files + 4 inline-FK links synthesized from
`purchase_order.csv`), `stream_events` (empty/none for v1), `health_check` (record counts). Decimal-safe
parsing of THB columns. **Tests:** round-trip (AC-1) + conformance to the `@runtime_checkable` protocol
+ zero-core-edit grep guard (AC-2).

### Step 2: Governance-moment render — the NEW demo screen (SD-2 contingent)
Add a new read-only demo screen (own route/asset; NOT an oct-demo extension, dossier §8 D3) that takes a
run's gate audit and renders the three shipped fields **bound directly, no reshape** (AC-3/4/5). **[Code rec,
SD-2]** reuse `view-procedures.js`'s pure `facetModel(step)` decomposition seam (the AC-7 de-risk seam) for
the structural scaffold, add a thin purpose-built `governanceMoment(audit)` joiner over `doa_tier` /
`PrincipalSoDVerdict` / `governed_decision`. Render the join visibly (audit → control → principal). Include
the AC-7 contrast row (`PO-2026-0411` → TIER-MGR, no escalation). **Tests:** a render-contract test asserting
the join keys resolve on the hero audit (fixture captured per SD-1) + the contrast case.

### Step 3: B1 — ฿-impact ledger (SD-3 contingent)
Compute baseline (on-AVL 14-day wait: `downtime_cost_per_hour_thb` × productive-hours + on-contract part
cost) vs governed (off-AVL 2-day: downtime × hours + emergency quote) from dataset columns; surface
baseline → governed + expedite-premium ฿52,500 (AC-6). **[Code rec, SD-3]** a derived read-only API view
(`GET /demo/hero/impact`) so the math is server-side + unit-testable, FE renders the returned ledger.
**All numbers labelled provisional** (a visible demo-grade badge). **Tests:** ledger math unit test against
the dataset columns (exact ฿ values).

### Step 4: Offline gate + wiring
Wire the demo screen to the run path chosen in SD-1; run the full offline gate (AC-8). No live MS-S1.

## Verification

How we know it worked (all offline, fresh on-disk evidence — CLAUDE.md §6 "offline oracle is the gate"):
- `pytest` green on the round-trip (AC-1), zero-core-edit grep guard (AC-2), the render-contract join test
  (AC-3/4/5/7), and the ledger math test (AC-6); `ruff` + `mypy --strict` clean (AC-8).
- Manual screen check: load the demo screen on the hero run → the three fields render with the join drawn
  (฿288k > ฿200k → Controller; MAINT_PLANNER ≠ CONTROLLER; control_ref/principal_id tied); the contrast PO
  stays at TIER-MGR; the ฿-ledger shows baseline → governed with the provisional badge.
- Diff inspection confirms zero `services/engine/procedures/*` and `services/engine/*` core edits.

## Surfaced decisions (NOT ratified — Cray adjudicates before execution)

**SD-1 (KEY — gating) — the RUN path.** Audit fields are produced at RUN time, but there is no run API
today (in-memory `PipelineRun`; no `POST /procedures/{id}/run`). How does the demo go run → capture the gate
audit → render?
- **[Code recommendation] (b) a recorded/fixture run for v1** — capture one real hero-run's gate audit
  (produced by the SHIPPED A1b path) as a committed fixture the render binds to; defer a live run endpoint.
  Reason: smallest credible slice, keeps the render honest (binds to real shipped shapes), and avoids
  building a run-API surface this PLAN's scope explicitly excludes — the fixture is captured FROM the real
  engine path, so it is not a hand-authored mock (dodges the fixture-masks-live trap, per the captured-from-
  real-output discipline in the dossier §7 eval note).
- Alternatives: **(a) a thin `POST /procedures/{id}/run` returning run+audit** — most product-shaped but a
  new API surface + larger; **(c) run in-process behind the demo screen** — no new public API but couples the
  screen to engine internals and risks touching `procedures/*` (concurrent-session hold).
- **Why a Cray decision:** it sets whether v1 ships a live run-API (product-shaping + scope expansion) vs a
  recorded run, and it is the seam the render + the whole demo flow hang on. Multiple defensible answers;
  reversal cost touches Steps 2+4. Not a Code judgment call.

**SD-2 — render composition (reuse vs purpose-built).** New screen (LOCKED), but how much to reuse
`view-procedures.js`'s facet-render internals vs a purpose-built component?
- **[Code recommendation] reuse the pure `facetModel` decomposition seam for scaffold + a thin purpose-built
  `governanceMoment(audit)` joiner.** Reason: `facetModel` is already the AC-7 "pure decomposition" de-risk
  seam (PLAN-0039/0042) — reuse keeps the read-only viewer and the demo screen consistent; but the three A1b
  audit fields are a different shape than a Step's facets, so a thin dedicated joiner is cleaner than forcing
  them through facet slots.
- Alternative: a fully purpose-built screen (more freedom, more duplicated render code + drift risk).
- **Why a Cray decision:** it is a UX/architecture trade (consistency vs purpose-fit) with no single
  derivable answer; Code recommends but should not silently pick the demo's primary surface.

**SD-3 — B1 ledger home (derived API view vs front-end computation).**
- **[Code recommendation] a derived read-only API view (`GET /demo/hero/impact`).** Reason: server-side math
  is unit-testable against exact ฿ columns (the AC-6 oracle) and keeps the FE thin; consistent with SD-1(b)/(a)
  living server-side.
- Alternative: FE computes over fetched objects (fewer endpoints, but the ฿ math becomes untested JS).
- **Why a Cray decision:** couples to SD-1's choice (if SD-1=(b) fixture-only, a tiny derived view is still
  fine; if SD-1=(a) run-API, fold impact into that surface) — Cray should resolve SD-1 and SD-3 together.

## Residual gaps / open questions

- **RUN-path dependency (SD-1):** Steps 2 + 4 cannot be fully specified until SD-1 is ratified — the render's
  input source (fixture vs live endpoint) is the seam. The Steps carry option (b) as load-bearing-but-contingent.
- **Hero-knob:** the dataset offers a swappable "single Fanuc servo-drive" hero (฿185k→฿241k, qty 1) vs the
  qty-3 bearing set. The PLAN assumes the canonical bearing-set hero (`PO-2026-0412`); confirm at execution if
  Cray prefers the cleaner single-premium-part variant.
- **Person→role principals fixture:** the SoD/`resolved_approver_id` join needs declared `Person` records
  mapping `CONTROLLER`/`MAINT_PLANNER` to `person_id`s (the dataset's CSVs carry roles, not principals). Whether
  these live in the C1 dataset or a small demo principals fixture is a Step-1 execution detail to confirm.
