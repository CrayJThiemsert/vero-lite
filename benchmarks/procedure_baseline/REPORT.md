# Procedure-baseline benchmark — REPORT (PLAN-0019 B-5)

> **Status: results pending the run.** Numbers are filled by the live RUN
> (`run_benchmark.py` against `gpt-oss:20b` on MS-S1, Cray-warmed + Cray-approved
> 2026-06-08). The grading methodology below was **calibrated and Cray-ratified
> BEFORE the scored run** (see the Calibration log) — the anti-moving-target
> discipline: the harness spec is fixed before the headline number exists.

## Ring-fence (B-6 — binding, anti moving-target)

Any measured number **below** the pre-registered threshold is a **logged finding
that opens a follow-up tuning PLAN** (which model / which prompt). It **MUST NOT**
reopen ADR-016's primitive shape (Accepted/fixed) and is **never** a reason to
move the threshold. The benchmark **reports** — it does not gate (B-3). "Our
stack wins" is the *thesis under test*, not an acceptance condition.

## What is graded (SD-B1 graded unit A)

- **Headline = LLM action-proposal correctness** on the **breach** subset: per the
  ground-truth key, did the two-call judgment path (`generate_judgment` →
  `LlmJudgment`) name the right entity (`affected_primary_key`), a valid handler
  (`valid_handlers`, today `[echo]`), and the right action class (`action_keywords`
  — searched across `title` / `description` / `rationale`)? A proposal passes iff
  **every scoring field** passes. `handler_payload` is recorded as an **advisory**
  signal, not a gate (see the Calibration log). Threshold: **≥ 85% accuracy** (SD-B1).
- **Deterministic disposition** (breach/watch/ok via `crosses_threshold`) is a
  **separately-reported ~100% sanity check** — NOT folded into the headline. It is
  the false-positive guard: watch/ok items assert the engine does NOT fire.
- **Latency** (B-δ): p95 **per LLM call** (= per affected entity = 2 Pattern-B
  calls), measured **warm-first** on an otherwise-quiesced MS-S1. Threshold:
  **≤ 8 s** (SD-B1).

## Calibration log (pre-scored-run; Cray-ratified 2026-06-08)

A pre-run smoke against the live model surfaced that the *harness*, not the model,
was mis-measuring. Four **measurement-correctness** fixes were ratified by Cray
**before** the scored run (each captures true positives the grader was missing or
drops an unfair gate — none moves the ≥85% bar or tunes-to-pass):

1. **Event carries the domain parameter.** `scenario_to_event` injects
   `parameter` (`dissolved_oxygen` / `temperature`) so the model knows WHAT is
   measured — faithful to a real ontology-projected event. (Without it the model
   emitted generic "Low Parameter Alert" titles.)
2. **`payload_contains` → advisory.** The live model's `handler_payload` keys are
   free-form (`event_id` / `action` / `recommendation`, never our guessed
   `pond_id`), so a payload subset is informative but not a fair headline gate.
3. **`action_keywords` broadened to per-vertical action lemmas** —
   aquaculture `[aerat, oxygenat]`, energy `[restart, reset, reboot]`,
   supply_chain `[hold, inspect, quarantine, divert]` — to admit the model's
   paraphrases of the same action (action verbs, not the bare parameter name).
4. **`action_keywords` searches `rationale` too** (not just title/description) —
   the model legitimately places its proposed action in any free-text field, and
   empirically it often lands in `rationale`.

Smoke trajectory (18 breach items) as the fixes landed: **44% → 61%** (items 1–3);
the `rationale` fix (item 4) recovered the aquaculture proposals the grader had
been scoring as failures despite a correct "Aeration" recommendation.

## Run provenance

- **Model:** `gpt-oss:20b` (ADR-0001 pin), live on MS-S1 (`192.168.1.133:11434`),
  Cray-warmed + Cray-approved 2026-06-08.
- **Scope:** all 162 items; 84 breach items each ran the live two-call judgment
  path (168 LLM calls); 78 watch/ok items were the deterministic guard (no LLM).
- **Result integrity:** 162/162 item lines, 84/84 breach proposals graded,
  **0 `StructuredOutputError`** (every call produced a schema-valid judgment).

## Results — headline (LLM action-proposal correctness)

| vertical | graded breach items | correct | accuracy | vs ≥85% |
|---|---|---|---|---|
| aquaculture | 28 | 28 | **100.0%** | ✅ PASS |
| energy | 28 | 28 | **100.0%** | ✅ PASS |
| supply_chain | 28 | 28 | **100.0%** | ✅ PASS |
| **overall** | **84** | **84** | **100.0%** | ✅ **PASS (≥ 85%)** |

## Results — deterministic disposition (sanity, ~100% expected)

| vertical | items | correct | accuracy |
|---|---|---|---|
| aquaculture | 54 | 54 | 100.0% |
| energy | 54 | 54 | 100.0% |
| supply_chain | 54 | 54 | 100.0% |
| **overall** | **162** | **162** | **100.0%** |

## Failure-mode taxonomy

**Zero graded failures** (84/84 breach proposals passed; 0 `StructuredOutputError`).
For every breach scenario — including the inclusive-boundary cases (aquaculture DO
4.0, energy 90.0 °C, supply_chain 8.0 °C) — the model named the right entity and
the right action class.

## Interpretation — what the 100% does and does NOT say (load-bearing caveat)

The headline **clears ≥ 85%**, but read it precisely — the number reflects an
**easy-by-construction** task, so it is a floor, not a ceiling:

- **`valid_handler` is trivially satisfied.** Every vertical registers only the
  `echo` handler today (the real `start_emergency_aerator` / `restart` / `hold`
  action types are deferred), so `suggested_handler` is enum-constrained to one
  choice and cannot discriminate. The headline effectively measures **right entity
  + right action verb in the model's free text**, not a structured action-type
  choice.
- **Scenarios are well-posed.** Single-entity breach readings, with the domain
  parameter + the procedure goal injected, no ambiguity / multi-entity / distractor
  rows. A competent local model handles these reliably.
- **Therefore the claim is:** *"gpt-oss:20b reliably identifies the affected entity
  and names the correct action on clearly-posed breach scenarios across three
  verticals (84/84)."* It is **NOT** a claim about hard, ambiguous, or
  adversarial cases.
- **To give the headline discriminating power** (future work): ship real, distinct
  action handlers (so `suggested_handler` becomes a meaningful graded choice), and
  add harder scenarios (multi-entity sets, distractors, near-miss actions). Until
  then, treat 100% as "the well-posed path works end-to-end," not "the model is
  infallible."

## Latency (SD-B1 ≤ 8 s p95 per LLM call)

**Not measured by this run** — the runner is not yet instrumented for per-call
timing. Rigorous p95-per-LLM-call latency (warm, quiesced MS-S1) is the **B-δ**
step. (Wall-clock context only: the 168-call run completed in roughly ~10–15 min.)

## B-3 comparison (REPORTED, not a gate)

vero-lite governed-procedure stack vs (b) raw text-to-SQL vs (c) RAG, on the same
synthetic questions: accuracy / failure-mode / latency. **TODO — own step (B-γ).**

## B-4 per-procedure model selection (closes G-3)

Per-procedure accuracy + p95 per-LLM-call latency across the candidate local
model(s) bound per `Agent`; selection rationale. **TODO — own step (B-δ).**

---

*PLAN-0019 Part B (B-β). Headline + sanity filled from the Cray-approved live run
(`gpt-oss:20b`, MS-S1, 2026-06-08). B-3 baselines + B-4/B-δ model & latency sweep
remain TODO. Per the ring-fence, this REPORTS — it does not gate — and the 100%
is read with the load-bearing caveat above.*
