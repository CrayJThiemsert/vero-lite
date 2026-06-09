# Procedure-baseline benchmark — REPORT (PLAN-0019 B-5)

> **Status: PR1 of the Part-B hardening landed; a hardened re-run is pending.** The
> filled result tables below are the **pre-hardening baseline** (run 2026-06-08/09,
> `gpt-oss:20b` on MS-S1, Cray-approved): they were scored under the OLD scheme —
> `echo`-only handler, `valid_handler` folded into the headline. PR1 (this change)
> **ships the real ontology `action_type` handler vocabulary** ((C) product-complete:
> the procedures now fix `step.handler` to `restart` / `start_emergency_aerator` /
> `hold`) and **splits grading into the β headline + α probe** (above). The new α
> handler-probe + the β headline on the real menu are filled by the **next
> Cray-approved RUN** (a host-state change — ASK first). The methodology was
> ratified BEFORE the scored run (anti-moving-target); each hardening step is
> likewise ratified before its re-run.

## Ring-fence (B-6 — binding, anti moving-target)

Any measured number **below** the pre-registered threshold is a **logged finding
that opens a follow-up tuning PLAN** (which model / which prompt). It **MUST NOT**
reopen ADR-016's primitive shape (Accepted/fixed) and is **never** a reason to
move the threshold. The benchmark **reports** — it does not gate (B-3). "Our
stack wins" is the *thesis under test*, not an acceptance condition.

## What is graded (SD-B1 graded unit A) — β headline + α probe

Three independent lanes (PLAN-0019 Part B hardening, Cray-ratified 2026-06-09 — see
the **Handler-determinism finding** below for why handler-selection is split out):

- **β headline = LLM action-proposal correctness** on the **breach** subset, scored
  on the fields the model genuinely OWNS in the governed procedure path: did the
  two-call judgment path (`generate_judgment` → `LlmJudgment`) name the right entity
  (`affected_primary_key`) and the right action class (`action_keywords` — searched
  across `title` / `description` / `rationale`)? A proposal passes iff **every
  scoring field** passes. Threshold: **≥ 85% accuracy** (SD-B1).
- **α probe = handler-selection** (`suggested_handler` vs the correct ontology
  `action_type`, e.g. `restart` / `start_emergency_aerator` / `hold` against the
  isolate/dispatch/reroute/… near-misses). Reported on its **own lane, NOT folded
  into the β headline** — in the procedure path the executed handler is fixed
  deterministically by the author's `step.handler` (ADR-016), so the model's handler
  *guess* is not the product's handler decision. The probe measures it as it would
  matter on the **reactive** path (`recommender._compose_llm_record`, which DOES use
  the guess) — a forward-looking signal.
- **`handler_payload`** is recorded as an **advisory** signal, not a gate.
- **Deterministic disposition** (breach/watch/ok via `crosses_threshold`) is a
  **separately-reported ~100% sanity check** — NOT folded into the headline. It is
  the false-positive guard: watch/ok items assert the engine does NOT fire.
- **Latency** (B-δ): p95 **per LLM call** (= per affected entity = 2 Pattern-B
  calls), measured **warm-first** on an otherwise-quiesced MS-S1. Threshold:
  **≤ 8 s** (SD-B1).

### Handler-determinism finding (the reason for the β/α split)

vero-lite has **two** action paths with **different** handler semantics. The
**reactive** Pipeline-v0 (`recommender._compose_llm_record`) uses the model's
`suggested_handler` guess and `execute()` invokes it. The **procedure** orchestrator
(ADR-016, `action_step._compose_action`) **overrides** the guess with the author's
`step.handler` — a deterministic, allowlist-bounded blast-radius bound. The benchmark
grades the raw `LlmJudgment` (faithful to the reactive path), but PLAN-0019 validates
the **procedure** path, which discards the handler guess. So grading the handler as a
*headline* would measure a field the procedure product overrides. Hence: handler
goes to the **α probe** lane (reactive-path / future-autonomy signal), and the β
headline keeps only the entity + action-class the procedure path actually consumes.

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

> **Pre-hardening baseline (echo-only, `valid_handler` in headline).** Under the
> PR1 β/α split this table corresponds to the **β headline** (entity + action class)
> — those two checks were already in this number, and the trivial `valid_handler`
> check did not move it (echo was the only enum choice). A hardened re-run with the
> α probe on the real `action_type` menu is the next step.

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

The headline is **run-to-run non-deterministic** (sampling on the local model):
the first scored run (#220) was **100% (84/84)**; a second warm run (the B-δ
latency run) was **97.6% (82/84)**. Both clear ≥ 85%; the honest read is
**~98–100%**.

The two misses in the second run were **both inclusive-boundary breaches**
(`aqua-028` DO = 4.0 mg/L, `energy-002` = 90.0 °C) — i.e. the model occasionally
hedges the action *exactly at the threshold*, where the reading is a breach by the
`<=` / `>=` rule but reads as "borderline" in prose. **Boundary cases are the
failure mode**; clear breaches (well inside the band) passed every time. No
`StructuredOutputError` in either run.

## Interpretation — what the 100% does and does NOT say (load-bearing caveat)

The headline **clears ≥ 85%**, but read it precisely — the number reflects an
**easy-by-construction** task, so it is a floor, not a ceiling:

- **`valid_handler` *was* trivially satisfied (pre-hardening).** The baseline ran
  with only `echo` registered, so `suggested_handler` was enum-constrained to one
  choice. **PR1 fixes this**: each vertical now registers its real ontology
  `action_type` vocabulary (the model picks from a 4–5 option menu), and the
  handler-determinism finding reassigns that check to the **α probe** — the β
  headline never claimed to measure handler choice. The hardened re-run will show
  whether the model picks the right `action_type` from the real menu (α).
- **Scenarios are still well-posed (PR2 work).** Single-entity breach readings, with
  the domain parameter + the procedure goal injected, no ambiguity / multi-entity /
  distractor rows. A competent local model handles these reliably — so the **β
  headline's** discriminating power awaits the harder scenarios.
- **Therefore the baseline claim is:** *"gpt-oss:20b reliably identifies the affected
  entity and names the correct action on clearly-posed breach scenarios across three
  verticals (84/84)."* It is **NOT** a claim about hard, ambiguous, or adversarial
  cases.
- **Discriminating-power roadmap (PLAN-0019 Part B hardening).** **PR1 (done):**
  ship the real, distinct action handlers (β/α split + the real `action_type` menu).
  **PR2 (next):** harder scenarios — multi-entity sets, distractors, near-miss
  actions — to give the **β headline** real discriminating power; then a hardened
  re-run. Until then, treat 100% as "the well-posed path works end-to-end," not "the
  model is infallible."

## Latency (B-δ — SD-B1 ≤ 8 s p95 per LLM call)

Measured per **LLM call** (a breach item = 2 Pattern-B calls) via the runner's
`TimingChatClient`, **warm-first** on MS-S1.

| model | n calls | mean | p50 | p95 | max | SD-B1 p95 ≤ 8 s |
|---|---|---|---|---|---|---|
| `gpt-oss:20b` (ADR-0001 pin) | 168 | 13.01 s | 12.12 s | **19.23 s** | 22.52 s | ❌ **OVER (~2.4×)** |

**Finding (NOT a build failure — B-6 ring-fence).** The pinned `gpt-oss:20b` is
**accurate but far over the latency bar** (p95 19.23 s vs the 8 s target; ~13 s
mean/call). The two-call Pattern-B exchange with `think=True` on call 1 generates
a large reasoning trace, which dominates per-call time on the MS-S1 hardware. Per
the ring-fence this is a **logged finding → a tuning PLAN** (candidate levers:
a faster/smaller bound model — the B-4/G-3 sweep; trimming the reasoning pass;
batching) and **does NOT move the 8 s bar or reopen ADR-016**.

The **B-4 / G-3 model-selection sweep** (below) collects the same accuracy +
per-call latency for alternative local models to inform that tuning.

## B-3 comparison (REPORTED, not a gate)

vero-lite governed-procedure stack vs (b) raw text-to-SQL vs (c) RAG, on the same
synthetic questions: accuracy / failure-mode / latency. **TODO — own step (B-γ).**

## B-4 / G-3 model-selection sweep

Same dataset + harness, alternative local models — Cray-scoped to three candidates
(`qwen3.6:35b`, `gemma4:26b`, then `gemma4:12b` added after MS-S1's Ollama was
updated to 0.30.6). Runs were serialized (one model at a time) so MS-S1 stayed
quiesced. The pin ran the full 84 breach items; each candidate ran a **9-item
breach subset** (cost control) and was **re-warmed first**. Rows sorted by latency.

| model | size | structured output | accuracy (n) | mean / p95 latency per call | SD-B1 ≤ 8 s |
|---|---|---|---|---|---|
| **`gpt-oss:20b`** (pin) | 20 B | ✅ reliable | **~98–100%** (84) | **13.0 s** / **19.2 s** | ❌ over (~2.4×) |
| `gemma4:12b` | 12 B | ✅ reliable | **100%** (9/9) | 45.9 s / 81.1 s | ❌ over (far) |
| `qwen3.6:35b` | 35 B | ✅ works | ~87.5% (7/8; 1 timeout) | 46.9 s / **120 s\*** | ❌ over (far) |
| `gemma4:26b` | 26 B | ⚠️ unreliable | not measurable (8/9 errored) | 51.7 s / **120 s\*** | ❌ over (far) |

\* p95 = the **120 s per-call timeout ceiling** (clipped); means are over completed
calls. `gemma4:12b` did **not** hit the ceiling (max 81 s) — its mean is a clean,
real latency.

**Notes per candidate.**
- **`gemma4:12b`** (the *smaller-than-pin* test) — **reliable + perfectly accurate**
  on the subset (9/9, valid JSON every call, zero errors), but **~3.5× SLOWER than
  the pin** (45.9 s mean/call, clean/un-clipped). The key surprise: **fewer
  parameters did NOT mean faster** — gemma generates a long output per call, so
  per-call latency is dominated by generated-token count + architecture/quant, not
  param count. `gpt-oss:20b`'s MXFP4 build is simply much faster here.
- **`qwen3.6:35b`** — structured output *works* (correcting the prior "qwen3.x =
  NOT_JSON" note for this build); accuracy acceptable (one failure was a transport
  timeout, not a wrong answer); ~3.6× slower than the pin; tripped the 120 s timeout.
- **`gemma4:26b`** — **not viable in this run**: 8/9 errored (7 timeouts + 1
  malformed JSON). Same gemma slowness as 12b but bigger, so it hits the 120 s
  ceiling and fails rather than just running slow.

**G-3 conclusion (closes the evidence gap).** Across four
structured-output-capable local models spanning 12 B–35 B, **the ADR-0001 pin
`gpt-oss:20b` is the best on BOTH axes** — highest accuracy *and*, by a wide
margin (≈3.5×), the lowest latency. Crucially, **going smaller did not help**:
`gemma4:12b` is reliable and accurate but far slower, so the latency problem is
**not a param-count problem** and is **not solved by any available alternative**.
The tuning levers therefore live elsewhere — trimming the `think=True` reasoning
pass (the dominant per-call cost), request batching, a faster-architecture small
model not yet on MS-S1, or revisiting the 8 s bar — all for the follow-up tuning
PLAN. **The pin holds.**

*Sweep caveat: candidate numbers are a 9-item directional read (wide CIs), not an
external-grade measurement; timeout-clipped p95s understate true latency. The
qualitative conclusions (pin is best by far; smaller ≠ faster) are robust.*

---

*PLAN-0019 Part B. **B-β headline** + sanity + **B-δ latency + B-4/G-3 model
sweep** filled from Cray-approved live runs (`gpt-oss:20b` / `gemma4:12b` /
`qwen3.6:35b` / `gemma4:26b` on MS-S1, Ollama 0.30.6, 2026-06-08/09). **B-3
baselines** (text-to-SQL + RAG) remain TODO. Per the ring-fence this REPORTS — it
does not gate; the headline 100% and the latency miss are both read with the
caveats above.*
