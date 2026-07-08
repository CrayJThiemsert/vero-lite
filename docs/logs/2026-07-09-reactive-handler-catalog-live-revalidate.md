# Reactive handler catalog live re-validate — RESULT: PASS (catalog flips `reorder` → `emergency_source`)

**Date:** 2026-07-09 (session 115)
**Event type:** host-state live run (MS-S1 `gpt-oss:20b`, `192.168.1.133:11434`) — **evidence-only, NOT a gate** (CLAUDE.md §8; PLAN-0060 AC-7). Cray-gated go given via AskUserQuestion. The offline suite (AC-1..AC-6, 2389 passed / 7 skipped, PR #655) remains the binding bar.
**Scope:** PLAN-0060 AC-7 — with `handler_catalog_enabled` ON, does the REAL reactive recommender now select `emergency_source` (not `reorder`) for the session-114 CNC line-down event that produced the finding (`docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md`)?
**Harness:** a one-off driver measuring the pick at the exact locus the catalog changes — `generate_judgment(client, event, "procurement", include_handler_catalog=<off|on>)` — the precise quantity of interest (`suggested_handler`); `recommend()` only wraps the same pick. Model warmed via `.claude/skills/ms-s1-ollama/warm.sh gpt-oss:20b 30m` (load 17s). MS-S1 released after (keep_alive 30m expiry).

## Pre-committed pass/fail read (fixed BEFORE the run — §8 / Lesson #0026)

- **PASS** = FLAG-ON `suggested_handler == "emergency_source"` AND the model engaged (a returned `JudgmentResult` ⇒ `actor_kind == llm`, not the rule fallback).
- **CONTROL** = FLAG-OFF `suggested_handler == "reorder"` (≠ `emergency_source`) — reproduces the session-114 finding on this reconstructed event, so the flip can be attributed to the catalog and not to a more-explicit event.
- **INCONCLUSIVE** if FLAG-OFF already yielded `emergency_source` (event too explicit — variable not isolated).
- One controlled A/B run; each arm fired **once**; **not** re-fired to fish (contamination anti-pattern).

## Result

| arm | `suggested_handler` | engaged | confidence | title | affected_entities |
|---|---|---|---|---|---|
| **FLAG-OFF (control)** | **`reorder`** | yes (`gpt-oss:20b`, 1 attempt) | 1.0 | "SOURCE CNC Bearing" | `[('spindle_bearing','AST-CNC-014')]` |
| **FLAG-ON (test)** | **`emergency_source`** | yes (`gpt-oss:20b`, 1 attempt) | 1.0 | "emergency_source" | `[('asset','AST-CNC-014')]` |

**VERDICT: PASS** — same event, the catalog flag the only moved variable; the flag-off arm reproduced the `reorder` finding, the flag-on arm flipped the pick to `emergency_source`. The pre-committed oracle is met.

## Event (faithful reconstruction)

The session-114 driver was not persisted (scratchpad, gone). Reconstructed from the finding note's recorded narrative + the hero `operational_event.csv` (`EVT-CNC-014-FAIL`, `AST-CNC-014`): a `reading`-typed event, `measured_value 0.92 criticality`, description *"CNC Machining Center #14 spindle bearing failure — line down; on-hand spare exhausted. The replacement bearing must be sourced URGENTLY from an emergency supplier because the normal reorder lead time is unacceptable while the production line is down."* The flag-off control reproducing `reorder` confirms the reconstruction is faithful to the finding.

- env: `LLM_BACKEND=local`, `OLLAMA_HOST=http://192.168.1.133:11434`, `RECOMMENDER_MODEL=gpt-oss:20b`, `OCT_VERTICAL=procurement`
- enum shown to the model (unchanged both arms): `['echo','emergency_source','escalate','issue_po','reorder','request_approval']`
- catalog rendered (flag-on): each handler as `name — description`, incl. `emergency_source — Urgent off-cycle sourcing for a critical failure or line-down … the hero/emergency path.` vs `reorder — Routine on-contract restock at the normal lead time — the calm path …`.

## Significance / next

- The session-114 root cause (reactive prompt shows bare names) is **fixed**: per-handler descriptions in the trusted instruction let the model distinguish urgent-critical-failure from routine-restock. The event-bridge demo premise (`actions.py:131,:143` fires the governed run only when `suggested_handler == "emergency_source"`) is **unblocked** for the live recommender.
- The `suggested_handler` enum was byte-unchanged across arms (AC-5 held live); the flip is a pure prompt effect.
- **On PASS → the SD-4 default flip** (`handler_catalog_enabled` default `False → True`) proceeds as its own PR (this is the AC-7-gated consequence the ratified SD-4 authorized).

## Reference

- PLAN-0060 (`docs/plans/0060-reactive-judgment-handler-catalog.md`); Steps 1-6 shipped PR #655 (`4d54683`).
- Finding this closes: `docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md`.
- Related learning: offline fixtures can mask live-model knowledge — one controlled live run is the cheapest catch (and the cheapest confirm of the fix).

AI-assisted (Claude Code, session 115); no `Co-Authored-By` per CLAUDE.md §7.
