# Event-bridge recommender live smoke — RESULT: FINDING (real model picks `reorder`, not `emergency_source`)

**Date:** 2026-07-08 (session 114)
**Event type:** host-state live run (MS-S1 `gpt-oss:20b`, `192.168.1.133:11434`) — **evidence-only, NOT a gate** (CLAUDE.md §8). The offline gates (`tests/api/test_action_event_bridge.py`, `tests/services/db/test_event_procurement_demo.py`) remain the binding bar and stay green.
**Scope:** the deferred event-bridge live smoke (PLAN-0056/0057 §8 host-state item) — does the REAL recommender choose `emergency_source` for a procurement critical-asset-failure event, feeding the governed `event_emergency_sourcing_round` procedure?
**Harness:** a one-off `recommend()`-only driver (no DB; the whole fire→gate→COMPLETED tail is already deterministic-offline-gated). Single live exchange; §8 minimize-live-runs — one run, deliberately **not** re-fired to fish for `emergency_source` (contamination anti-pattern).

## Summary / RESULT

The real model **engaged cleanly** — `actor_kind == "llm"` (NOT the deterministic rule fallback), confidence 1.0, entity resolved to `AST-CNC-014`, full action-verification trace — but chose **`suggested_handler == "reorder"`**, NOT `emergency_source`. The event prompt explicitly stated line-down / on-hand spare exhausted / "sourced URGENTLY from an emergency supplier … normal reorder lead time is unacceptable."

This is the offline-fixture-masks-live-knowledge trap made concrete: every offline fixture encodes `emergency_source`; the real `gpt-oss:20b` picks `reorder`.

## Root cause (offline trace) — a fixable reactive-prompt gap, NOT a model limitation

The reactive recommender shows the model **bare handler NAMES only** — no per-handler descriptions, no when-to-pick guidance, and `goal=None` on the reactive path. Given only the tokens `reorder` vs `emergency_source` for "a bearing failed, the spare ran out," `reorder` is a defensible surface reading.

- **Registration keeps names only** — handlers are `name → no-op callable` with no description slot (`services/engine/registry.py:64-69`; `verticals/procurement/handlers.py:26-34` = bare `ACTION_TYPES` tuple).
- **The enum reaches the model as names only** (`services/engine/llm/structured.py:111-125`, fed at `:188`); the `suggested_handler` field description is generic (`:103-105`); the semantic check verifies the name *resolves*, not that it is *appropriate* (`:257-263`) → `reorder` passes.
- **The judgment prompt never lists handlers or gives emergency-vs-reorder guidance** (`services/engine/llm/prompt.py`); the reactive path threads no `goal`.
- The distinguishing prose **exists** but only in `procedures.yaml` step descriptions (`emergency_source` source step `:139-143`; `reorder` step `:337-340`) + the `emergency_sourcing_round` goal (`:93-103`) — these thread into the **governed** procedure path, not the reactive judgment prompt.
- **The governed procedure path is UNAFFECTED** — there the handler is author-pinned (`procedures.yaml:146`) and "the LLM never selects it" (governed ≠ generated, `handlers.py:14-16`).

## Significance

- **The shipped hero demo is unaffected** — `run_hero_event_governance_moment` uses the deterministic advisory stub, not the live recommender.
- Only the deferred **live-recommender → `emergency_source`** path is affected; the **demo premise is recoverable** via a prompt fix.
- The gap is **cross-vertical** — every vertical's reactive recommender selects handlers from bare names. → **next-work candidate:** "surface per-handler descriptions in the reactive judgment prompt" (capture descriptions at registration + render an *Available actions* catalog; own small PLAN, cross-vertical blast radius, then one controlled live re-validate). **Deferred per Cray (session 114):** record this finding + proceed to the KPI panel first.

## Key facts

| field | value |
|---|---|
| `actor_kind` | `llm` (real model engaged, not the rule fallback) |
| `suggested_handler` | **`reorder`** (expected `emergency_source`) |
| `confidence` | 1.0 |
| `affected_entities` | `[('Asset', 'AST-CNC-014')]` (resolved cleanly) |
| enum shown to model | `['echo','emergency_source','escalate','issue_po','reorder','request_approval']` (names only) |
| env | `LLM_BACKEND=local`, `OLLAMA_HOST=http://192.168.1.133:11434`, `RECOMMENDER_MODEL=gpt-oss:20b`, `OCT_VERTICAL=procurement` |

## Reference

- Event bridge: `services/engine/procedures/event_bridge.py`; PLAN-0056 / PLAN-0057 (`docs/plans/done/`)
- Recommender reactive path: `services/engine/recommender.py` (`recommend()`, `_is_recommendation_trigger:109-122`, `_rule_recommend:248-318`)
- Prompt / enum: `services/engine/llm/structured.py`, `services/engine/llm/prompt.py`
- Offline gates (binding bar, green): `tests/api/test_action_event_bridge.py`, `tests/services/db/test_event_procurement_demo.py`
- Related learning: offline fixtures can mask live-model knowledge — a single live run is the cheapest catch.

AI-assisted (Claude Code, session 114); no `Co-Authored-By` per CLAUDE.md §7.
