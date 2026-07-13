# Event-bridge FULL-LOOP live smoke — RESULT: PASS (real MS-S1 pick → persisted governed run parked at the DOA gate)

**Date:** 2026-07-13 (session 125)
**Event type:** host-state live run (MS-S1 `gpt-oss:20b`, `192.168.1.133:11434`) + a disposable Postgres test DB — **evidence-only, NOT a gate** (CLAUDE.md §8). The offline suite (`tests/api/test_action_event_bridge.py`, `tests/services/db/test_event_procurement_demo.py`) remains the binding bar and stays green.
**Cray-gated go:** given via AskUserQuestion (direction "Prove moat live (event-bridge)" → then "build driver + run the full loop").
**Scope:** the deferred event-bridge live smoke (PLAN-0056 AC-12 / PLAN-0057:35, "the deferred smoke from the s111 handoff"). Sessions 114/115 proved the recommender-level pick live (s114 finding = `reorder`; s115 PASS = `emergency_source` after the PLAN-0060 handler-catalog fix) but **both stopped at `recommend()`** — neither drove the DB fire tail through the `event_bridge_enabled` production loop. This run closes that one remaining stitch: **real pick → `_fire_event_for_record` → `fire_event` → a PERSISTED governed run parked at the DOA gate.**

## Harness

A one-off standalone driver (`~/event_bridge_live_smoke.py`, outside the repo tree so pytest never collects it into CI) faithful to `services/api/routers/actions.py::_populate_store`'s inner body — it calls the SAME production functions (`discover_and_register` → `recommend` → `build_event_resolver` → `fire_event`), replacing only the adapter event-stream with one hand-constructed `reading`-typed CNC-line-down event (measured_value 0.92), exactly as sessions 114/115 did (the shipped procurement synthetic stream emits no qualifying emergency `reading`). The fire writes to a **DISPOSABLE test DB** (`vero_lite_test_bb36873b`, `tests/db_support._assert_not_dev_db`-guarded — never the demo DB); tables dropped on exit. Model pre-warmed via `.claude/skills/ms-s1-ollama/warm.sh gpt-oss:20b 30m` (load 17 s). One live run; §8 minimize-live-runs — **not** re-fired.

- env: `LLM_BACKEND=local`, `OLLAMA_HOST=http://192.168.1.133:11434`, `RECOMMENDER_MODEL=gpt-oss:20b`, `OCT_VERTICAL=procurement`, `HANDLER_CATALOG_ENABLED=true`, `EVENT_BRIDGE_ENABLED=true`, `OCT_RECOMMEND_THRESHOLD=0.9`, `OCT_RECOMMEND_DIRECTION=above` (so criticality 0.92 trips the deterministic detector).

## Pre-committed pass/fail read (fixed BEFORE the run — §8 / Lesson #0026; `.claude/state/goal.json` J1/J2)

- **PASS** (all five): (1) `recommend()` `actor_kind == "llm"` (real model engaged, not the deterministic rule fallback); (2) `suggested_handler == "emergency_source"`; (3) fire `result == "fired"` and `run_status == "waiting_human"`; (4) the suspended `step_id == "approve"` (parked at the DOA gate — a machine never approves, RF-3); (5) the `run_started` audit shows `actor_kind == "service"`, `actor_service_principal_id == "svc-buyer"`, `on_behalf_of.owning_person_id == "req-planner"` (the SP-5 on-behalf-of SoD posture).
- **MISS/FINDING** (not a harness failure): the model engages but picks a non-`emergency_source` handler (the s114 `reorder` outcome) → recorded as a finding, no governed run.
- **INCONCLUSIVE**: `actor_kind != "llm"` (MS-S1 unreachable / timed out → rule fallback).

## Result

| criterion | expected | observed | verdict |
|---|---|---|---|
| recommend engaged | `actor_kind == "llm"` | `llm` (`gpt-oss:20b`, conf 0.99) | ✅ |
| model pick | `emergency_source` | `emergency_source` | ✅ |
| fire outcome | `fired` / `waiting_human` | `fired` / `waiting_human` | ✅ |
| parked at gate | suspended `step_id == "approve"` | `approve` | ✅ |
| DOA tier | ฿288,000 → [50k,500k) → ผจก.จัดซื้อ / `appr-pm` | `appr-pm`, `sod_required: true` | ✅ |
| service actor | `service` / `svc-buyer` / on-behalf `req-planner` | `service` / `svc-buyer` / `req-planner` | ✅ |

**VERDICT: PASS** — the real `gpt-oss:20b` selected `emergency_source` for the CNC line-down event, and that pick propagated through the production fire path into a persisted `event_emergency_sourcing_round@<event_key>` run that parked at the `approve` DOA gate as the service principal on behalf of the owning human. The one stitch no offline test exercised is now proven live. (The `<event_key>` is a 64-bit sha256-truncated dedup key — `2409f15e…`; the full value is a derived idempotency hash, not shown.)

## Evidence (verbatim driver output)

```json
{
  "recommend": {
    "actor_kind": "llm",
    "actor": "gpt-oss:20b",
    "suggested_handler": "emergency_source",
    "confidence": 0.99,
    "title": "Emergency source action",
    "affected_entities": [["Asset", "AST-CNC-014"]]
  },
  "fire": {
    "run_id": "event_emergency_sourcing_round@2409f15e...",
    "result": "fired",
    "run_status": "waiting_human",
    "suspended_step_id": "approve",
    "doa_tier": [{"band": {"min": "50000", "max": "500000"}, "amount": {"value": "288000", "currency": "THB"},
                  "sod_required": true, "required_role": "ผจก.จัดซื้อ", "resolved_approver_id": "appr-pm"}],
    "run_started_audit": {"actor_service_principal_id": "svc-buyer", "actor_kind": "service",
                          "on_behalf_of": {"owning_person_id": "req-planner", "service_principal_id": "svc-buyer"}},
    "trigger_context": {"trigger": "event", "event_kind": "emergency_source",
                        "event_key": "2409f15e... (64-bit dedup hash, truncated)", "entity_ids": ["AST-CNC-014"]}
  },
  "result": "PASS"
}
```

## Significance / next

- **The moat's asset-event trigger is now proven live end-to-end** — from a real model judgment on MS-S1 through the governed engine to a persisted, human-gated run. Sessions 114/115 proved the pick; this proves the *propagation + persistence*. The event-bridge no longer has an unexercised live seam.
- **`event_bridge_enabled` stays default `False`** (ship-dark, ADR-0029 SD-P3). This smoke proves it *works when armed*; flipping the default is a separate product/rollout decision (blast radius: every actionable recommendation would fire a governed run) — **not changed here**.
- The offline gates remain the binding bar; this run is evidence, not a CI gate (§8). No production code changed.
- Related learning: offline fixtures can mask live-model knowledge — one controlled live run is the cheapest catch **and** the cheapest confirm ([[feedback_offline_fixture_masks_live_model_knowledge]]).

## Reference

- Deferred item closed: `docs/plans/done/0056-event-trigger-bridge-build.md` (AC-12) + `docs/plans/done/0057-event-triggered-hero-opener.md:35`.
- Fire path: `services/engine/procedures/event_bridge.py` (`build_event_resolver`, `fire_event`); the production loop `services/api/routers/actions.py::_populate_store` / `_fire_event_for_record`.
- Recommender: `services/engine/recommender.py` (`recommend`, `_build_chat_client`, `_is_recommendation_trigger`).
- Prior live runs (recommender-level): `docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md` (finding) → `docs/logs/2026-07-09-reactive-handler-catalog-live-revalidate.md` (PASS).
- Pre-committed read: `.claude/state/goal.json` (session 125, J1/J2).

AI-assisted (Claude Code, session 125); no `Co-Authored-By` per CLAUDE.md §7.
