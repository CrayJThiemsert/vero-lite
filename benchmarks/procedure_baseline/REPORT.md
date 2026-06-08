# Procedure-baseline benchmark — REPORT (PLAN-0019 B-5)

> **Status: PLACEHOLDER.** The numbers below are filled by the live RUN
> (`run_benchmark.py` against `gpt-oss:20b` on MS-S1), which is a **host-state
> change — Cray go-ahead required before warming / running** (handoff §5;
> `project_ms_s1_ollama_reachability`). This file ships in the scaffold so the
> report's *shape* — and its load-bearing guardrails — are reviewed before any
> number exists to argue about.

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
  (`valid_handlers`, today `[echo]`), the right action class (`action_keywords`),
  and — where declared — the right `handler_payload` (subset match)? Threshold:
  **≥ 85% accuracy** (SD-B1).
- **Deterministic disposition** (breach/watch/ok via `crosses_threshold`) is a
  **separately-reported ~100% sanity check** — NOT folded into the headline. It is
  the false-positive guard: watch/ok items assert the engine does NOT fire.
- **Latency** (B-δ): p95 **per LLM call** (= per affected entity = 2 Pattern-B
  calls), measured **warm-first** on an otherwise-quiesced MS-S1. Threshold:
  **≤ 8 s** (SD-B1).

## Results — headline (LLM action-proposal correctness)

| vertical | graded breach items | correct | accuracy | vs ≥85% |
|---|---|---|---|---|
| aquaculture | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| energy | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| supply_chain | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| **overall** | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

## Results — deterministic disposition (sanity, ~100% expected)

| vertical | items | correct | accuracy |
|---|---|---|---|
| _TBD_ | | | |

## Failure-mode taxonomy

_TBD — categorize each graded failure (wrong entity / wrong handler / wrong action
class / payload miss / StructuredOutputError) once the run produces them._

## B-3 comparison (REPORTED, not a gate)

vero-lite governed-procedure stack vs (b) raw text-to-SQL vs (c) RAG, on the same
synthetic questions: accuracy / failure-mode / latency. **TODO — own step (B-γ).**

## B-4 per-procedure model selection (closes G-3)

Per-procedure accuracy + p95 per-LLM-call latency across the candidate local
model(s) bound per `Agent`; selection rationale. **TODO — own step (B-δ).**

---

*PLAN-0019 Part B. Scaffold placeholder; filled after the Cray-approved live run.*
