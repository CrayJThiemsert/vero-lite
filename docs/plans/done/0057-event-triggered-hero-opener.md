# PLAN-0057: Event-triggered hero-demo opener

**Status:** Complete
**Completed:** 2026-07-08 — all 8 ACs met, **live-verified end-to-end**. PRs #638 (Step 1 + Step 5), #639 (Steps 2 + 4), #640 (Step 3 / AC-2). Dev DB migrated `0009 → 0011` (Cray-approved, host-state §8) to run the live smoke: `POST /demo/hero/event → 200`; sense (`CNC-Line-07`) → govern (DOA/SoD) → act (`Approve as appr-pm` → COMPLETED) → ฿ ledger → Replay, on `oct-demo-procurement`.
**Owner:** both (Claude Code executes; Cray ratifies the surfaced decisions)
**Created:** 2026-07-08
**Ratified:** 2026-07-08 — SD-1..SD-5 as-recommended + OQ-1/OQ-2 resolved (Cray, via AskUserQuestion); Code R2-verified SD-2 (demo.py:14 no-mutation invariant) + SD-4 (fire_event → run_procedure_persisted, event_bridge.py:309) on disk
**Related ADRs:** ADR-0029 (event-trigger bridge), ADR-0025 (DOA/SoD/`doa_tier`, D5 SoD), ADR-016 (procedure engine). Related PLANs: PLAN-0045 (hero v1 render + ฿ ledger), PLAN-0056 (event bridge), PLAN-0054 (procurement executor factory).

> **This is a build PLAN — no new ADR.** If execution uncovers a design fork that would need an ADR, STOP and surface it; do not bake it in.

## Goal

Make the just-shipped event bridge (PLAN-0056 / ADR-0029) **visible** in the existing hero-demo surface. Today the hero demo runs the **MANUAL** `emergency_sourcing_round` in-memory (PLAN-0045). This PLAN adds an **EVENT opener**: a detected asset-failure event auto-fires the governed `event_emergency_sourcing_round` procedure via `fire_event` → the run executes its auto steps and **parks** at the `doa_tier` DOA gate (`waiting_human`) → a **distinct** authored approver (`appr-pm`, SoD vs the `req-planner` owner) resolves it → `COMPLETED` → the **same** governance-moment + ฿-ledger render the manual opener already draws.

This is a **DEMO COMPOSITION over already-shipped plumbing** — NOT a new engine capability. The event procedure, the fire path, the executor factory, the render, and the ฿ ledger are all shipped; the gap is a thin demo route + a `view-hero.js` toggle + one route-level test.

## Frame (state explicitly)

- The manual opener stays byte-identical: `GET /demo/hero/governance` (`verticals/procurement/hero_demo/run.py:281` `run_hero_governance_moment`) runs the MANUAL `emergency_sourcing_round` in-memory to its `approve` gate and returns the hero contract.
- The event opener fires `event_emergency_sourcing_round` (`verticals/procurement/procedures.yaml:591`; `trigger: event`, `event_trigger.event_kind: emergency_source`, `owning_person_id: req-planner`) and renders the SAME `HeroGovernanceAudit` contract + the SAME `/demo/hero/impact` ฿ ledger (which is deterministic/offline and path-agnostic — reused unchanged).
- **Key disk fact (load-bearing):** `fire_event` (`services/engine/procedures/event_bridge.py:282`) ALREADY drives a **persisted** run via `run_procedure_persisted` and parks at the gate. And `tests/services/db/test_event_procurement_demo.py` ALREADY proves fire → park at `doa_tier` (`appr-pm`) → distinct-approver resolve → `COMPLETED` at the **engine** layer. So this PLAN does NOT re-prove the bridge — its new test proves the **demo projection** (the parked event run → hero render contract).

## Acceptance Criteria

- [x] **AC-1 (event opener route).** A demo route fires `event_emergency_sourcing_round` via `build_event_resolver` → `fire_event` (directly, MS-S1-free, `event_bridge_enabled`-independent) to a persisted `waiting_human` run, and returns that parked run's gate audit in the **existing `HeroGovernanceAudit` contract** (`services/api/models/demo.py:60`) — same `hero` shape (`po_id`, `doa_tier[0]`, `sod`, `governed_decision`, `declared_tier_id`, `is_off_avl_override`) `view-hero.js`'s `governanceMoment()` joiner already consumes (`static/assets/view-hero.js:35`). No reshape of the contract.
- [x] **AC-2 (distinct-approver resolve renders COMPLETED).** After `appr-pm` (SoD-distinct vs `req-planner`) resolves the parked gate, the opener reflects the run reaching `COMPLETED` (the replay/approve beat of the mockup). Resolve path reuses `resolve_gated_step` + `resume_run` exactly as the shipped engine test does.
- [x] **AC-3 (UI toggle).** `view-hero.js` gains a "manual opener" vs "event-triggered opener" toggle that **reuses** the existing governance-moment + ฿-ledger render; no second view, no duplicated joiner.
- [x] **AC-3b (sense cue).** The event opener surfaces `event_kind` / `detected_at` / `fired_at` from the persisted run's `trigger_context` (the mockup's beat-1 "sense") in the event view; render-only, deterministic, no engine change.
- [x] **AC-4 (฿ ledger reused unchanged).** The event opener renders the SAME `/demo/hero/impact` ledger (`verticals/procurement/hero_demo/ledger.py`) — no new ledger code, no figure change.
- [x] **AC-5 (ONE integration test, MS-S1-free, pass/fail PRE-COMMITTED).** A single integration test (pass/fail read fixed BEFORE the test is written — Lesson #0026) proves: event-fire → park-at-`doa_tier` → distinct-approver (`appr-pm`) resolve → `COMPLETED` → hero-contract projection is well-formed. DB-backed disposable `<db>_test`; deterministic `advisory_stub_factory` (no live model, CLAUDE.md §8).
- [x] **AC-6 (full offline suite green — the merge gate).** ruff + mypy + full pytest green; the required CI `gate` runs the FULL suite per PR (Lesson #0029). The offline suite is the gate, not a named subset.
- [x] **AC-7 (no engine / ADR / flag change).** No change to the procedure engine, no new ADR, no change to `event_bridge_enabled`'s default (`False`), no change to the recommender→bridge production path.

**Non-acceptance optional (host-state §8, Cray-gated — EVIDENCE, not the gate):** a LIVE end-to-end smoke where the real recommender emits `suggested_handler == emergency_source` on MS-S1 → real fire through the `event_bridge_enabled` production loop. This is the deferred smoke from the s111 handoff. List it; do NOT make merge depend on it.

**UX intent (not an AC):** the show_widget mockup Cray approved this session (sense → govern → act → ฿ with a replay control). Reference it as intent; the ACs are grounded in code contracts, not mockup pixels.

## Out of Scope

- ❌ The Q4 generic-query-executor residue / join-grammar ADR (the factory's QUERY kind binds a hand-written `_SeedQuery`; the event procedure's steps are action/gate, so the residue does not touch this PLAN).
- ❌ Any behavior change to the recommender→bridge PRODUCTION live path (`services/api/routers/actions.py` under `event_bridge_enabled`).
- ❌ Any new ADR; any change to `event_bridge_enabled`'s `False` default.
- ❌ KPI / notification / questionnaire dossier backlog pieces.
- ❌ New engine capability of any kind — this is demo composition only.

## Steps

### Step 1: Event-opener service function (the projection)
Add a `procurement/hero_demo` helper that: loads the procurement spec, `build_event_resolver` + `fire_event` (via the SHIPPED `register_procurement_procedure_executors` factory, `run.py:392`) to a persisted `waiting_human` run keyed on the demo asset-failure event (**OQ-1 resolved:** `event_kind="emergency_source"`, `entity_ids=["CNC-Line-07"]` — a spindle-bearing seizure, mockup-consistent, NOT `pump-7`), loads the parked run, and **projects** its `source` step `scored_rule` + `approve` step `doa_tier` (+ derived `sod`) into the existing hero contract dict. Also project the persisted run's `trigger_context` (`event_kind` / `detected_at` / `fired_at`) into the response as the beat-1 "sense" cue (AC-3b; render-only). Reuse `run_hero_governance_moment`'s projection shape (`run.py:347-364`) — extract/share rather than duplicate. Deterministic (advisory stub), MS-S1-free.

### Step 2: Demo route
Expose the event opener over HTTP returning `HeroGovernanceAudit` (reuse the response_model). See **SD-2** for endpoint shape (new route vs `?trigger=event` param) — this route performs a DB write (fires/persists a run), which is a genuine fork against the existing `/demo/hero/governance` "no mutation, no DB" documented invariant.

### Step 3: Resolve beat
Wire the distinct-approver resolve (`appr-pm`) so the opener can show park → approve → `COMPLETED`, reusing `resolve_gated_step` + `resume_run` exactly as `tests/services/db/test_event_procurement_demo.py` does. See **SD-4** (persisted, already implied by `fire_event`).

### Step 4: `view-hero.js` toggle
Add the manual/event toggle reusing the existing `governanceMoment()` joiner + ฿-ledger render (**SD-3**). In the event view, render the projected `trigger_context` (`event_kind` / `detected_at` / `fired_at`) as the beat-1 "sense" cue (AC-3b; render-only). Version any static asset edit with a `?v=` bump (project memory: preview caches static JS).

### Step 5: Integration test (AC-5)
Write the single MS-S1-free integration test with a PRE-COMMITTED pass/fail read. Scope it to the DEMO projection (route/service layer returns a well-formed hero contract for the parked event run + the resolve→COMPLETED beat) — do NOT re-prove the engine-level bridge (already covered by `test_event_procurement_demo.py`). See **SD-5**.

### Step 6: Full-suite green + PR
ruff + mypy + full pytest; PR referencing PLAN-0057, ADR-0029, ADR-0025. Code R2 + commit (ADR-009 D2 — only Code commits).

## Verification

- **Offline (the gate):** AC-5 test green + full suite green under the required CI `gate` (full suite, per PR). Verify on-disk with fresh evidence (`confirmed — prior intact` only with a pre-committed read + a fresh artifact — CLAUDE.md §6).
- **Demo surface:** the event toggle renders the governance moment + ฿ ledger; the parked gate resolves to `COMPLETED` via `appr-pm`.
- **Optional live (Cray-gated, host-state §8):** real recommender → `emergency_source` → real fire — evidence only, never the merge gate.

## Surfaced decisions (SD-N — Cray adjudicates; recommendations are contingent)

- **SD-1 — fire the event DIRECTLY vs route through the recommender + `event_bridge_enabled`.** *Recommend:* fire directly via `fire_event` (deterministic, MS-S1-free, flag-independent) for the demo; the recommender→bridge live path stays the separate deferred host-state smoke. *Why Cray:* it fixes the demo's trust boundary (deterministic demo vs live proof). ✅ RATIFIED 2026-07-08 (Cray, via AskUserQuestion, as-recommended)
- **SD-2 — new endpoint (`/demo/hero/event`) vs extend `/demo/hero/governance` with `?trigger=event`.** *Recommend:* a thin **new** route that REUSES the `HeroGovernanceAudit` response_model, NOT a param on the existing GET. *Why (disk evidence):* `services/api/routers/demo.py:12-15` documents `/demo/hero/governance` as "No mutation, no DB, no LLM"; the event opener necessarily writes/persists a run, so extending that GET breaks its stated invariant. This is a defensible deviation from the dispatch's "extend, lighter" lean — surfaced because the on-disk invariant makes the by-surface-lighter option semantically heavier. *Why Cray:* it's a demo-surface contract call (mutation semantics on a documented read-only prefix). ✅ RATIFIED 2026-07-08 (Cray, via AskUserQuestion, as-recommended)
- **SD-3 — UI toggle in `view-hero.js` vs a separate view.** *Recommend:* the toggle, reusing the existing joiner + ฿-ledger render (no duplicated render path). *Why Cray:* demo UX shape. ✅ RATIFIED 2026-07-08 (Cray, via AskUserQuestion, as-recommended)
- **SD-4 — persistence via `run_procedure_persisted` vs in-memory.** *Recommend:* persisted. *Note (disk):* this is effectively decided by choosing `fire_event`, which ALREADY calls `run_procedure_persisted` internally (`event_bridge.py:309`); in-memory would mean bypassing `fire_event` and re-implementing the fire path (worse). Persisted also matches the mockup's real approve→complete beat. *Why Cray:* confirm the durable-parked-run posture for the demo. ✅ RATIFIED 2026-07-08 (Cray, via AskUserQuestion, as-recommended)
- **SD-5 — integration-test layer: HTTP route (TestClient) vs service-function.** *Recommend:* assert at the service-function/projection layer + a thin route smoke, scoped to the DEMO projection only (the engine bridge is already proven by `test_event_procurement_demo.py`). *Why Cray:* scoping the ONE test so it does not redundantly re-prove shipped plumbing. ✅ RATIFIED 2026-07-08 (Cray, via AskUserQuestion, as-recommended)

## Residual gaps / open questions

- **OQ-1 (event payload asset)** — RESOLVED 2026-07-08: `entity_ids=["CNC-Line-07"]` (spindle-bearing seizure), mockup-consistent. Baked into Step 1.
- **OQ-2 (sense cue in render)** — RESOLVED 2026-07-08: IN SCOPE. Folded into AC-3b + Steps 1/4 (project + render `trigger_context`; render-only, no engine change).
- None open.
