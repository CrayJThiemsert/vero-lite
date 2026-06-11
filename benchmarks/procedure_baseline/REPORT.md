# Procedure-baseline benchmark — REPORT (PLAN-0019 B-5)

> **Status: Part-B hardening COMPLETE — the hardened re-run landed 2026-06-09.** The
> headline numbers are now in **[Results — HARDENED run (2026-06-09)](#results--hardened-run-2026-06-09--the-discriminating-numbers)**
> below; the **pre-hardening baseline** tables further down are RETAINED for comparison
> (run 2026-06-08/09, `gpt-oss:20b` on MS-S1, Cray-approved) — they were scored under the
> OLD scheme — `echo`-only handler, `valid_handler` folded into the headline,
> well-posed single-entity scenarios. **PR1** ships the real ontology `action_type`
> handler vocabulary ((C) product-complete: the procedures fix `step.handler` to
> `restart` / `start_emergency_aerator` / `hold`) and splits grading into the **β
> headline + α probe**. **PR2** adds the **hard scenarios** (12 multi-entity /
> distractor / near-miss breach items per vertical, ids `*-h01..h12`) + the two β
> **precision** checks (`forbidden_primary_keys` / `forbidden_keywords`) that give the
> β headline real discriminating power. The harness is now fully hardened; the β
> headline (on the hard scenarios) + the α handler-probe (on the real menu) are
> **filled below from the 2026-06-09 hardened run** (Cray-approved host-state run;
> the runner's `--dump-json` captured every per-item judgment so each score was
> VERIFIED against real model output, not inferred). Every hardening step's methodology
> was ratified BEFORE its scored run (anti-moving-target).

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
  across `title` / `description` / `rationale`)? PR2 adds two **precision** checks for
  the harder scenarios: `forbidden_primary_keys` (the model must NOT also name a decoy
  sibling entity) and `forbidden_keywords` (the near-miss action verb must NOT be the
  recommended action — checked in the proposal **title**). A proposal passes iff
  **every scoring field** passes. Threshold: **≥ 85% accuracy** (SD-B1).
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
  **≤ 8 s** (SD-B1) — **superseded 2026-06-11 by SD-2: ≤ 30 s p95 per-judgment**
  (end-to-end; see [Results — PLAN-0020 tuning](#results--plan-0020-tuning-2026-06-11--the-nudge-effect--the-latency-lever)).

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

## Results — HARDENED run (2026-06-09) — the discriminating numbers

The first scored run on the **fully-hardened** harness (real `action_type` menu + hard
multi-entity / near-miss scenarios + `forbidden_*` precision checks). `gpt-oss:20b` on
MS-S1 (`192.168.1.133:11434`, Ollama 0.30.6), Cray-approved host-state run, warm-first.
**198 items** (120 graded breach + 39 watch + 39 ok); **240 LLM calls** (120 breach × 2
Pattern-B calls); **0 `StructuredOutputError`** (every call schema-valid). Every per-item
judgment + per-check verdict was captured via the runner's `--dump-json`, and the scores
below were VERIFIED against the raw output — the session-46 "verify, don't infer" lesson:
a low score must be confirmed a real model verdict, not a grader artifact.

### β headline (entity + action-class; SD-B1 ≥ 85%)

| vertical | graded breach | correct | accuracy | vs ≥85% |
|---|---|---|---|---|
| aquaculture | 40 | 24 | **60.0%** | ❌ below |
| energy | 40 | 39 | **97.5%** | ✅ pass |
| supply_chain | 40 | 40 | **100.0%** | ✅ pass |
| **overall** | **120** | **103** | **85.8%** | ✅ **pass (≥ 85%)** |

The hardened β **discriminates** (the whole point of the hardening): it fell from the
pre-hardening 100%, driven almost entirely by **aquaculture** (its 12 hard items all
failed this run, plus 4 easy boundary items). A companion warm run (without the dump) read
**89.2%** overall — so the honest overall β is **~86–89%**, clearing the bar but no longer
a ceiling-less 100%.

**aquaculture β failure modes** (VERIFIED from the dump — 16 fails, 18 check-failures, 2
items failing both):
- **11 × `forbidden_primary_keys`** — under multi-entity input the model frames the
  proposal as a *"DO Monitoring Summary"* and lists **all** ponds in `affected_entities`,
  including the SAFE decoy siblings (e.g. `aqua-h01`: named the breached `pond-A101`
  **and** the safe `pond-A102` / `pond-A103` at DO 4.4 / 4.8). A genuine entity-precision
  weakness when distractors are present.
- **7 × `action_keywords`** — the same "summary / assessment" framing describes the
  situation but never states the *aerate / oxygenate* action verb in any free-text field.
- energy & supply_chain show **no** over-naming — energy's `forbidden_primary_keys` passed
  on every hard item, so it handles multi-entity input markedly better than aquaculture (a
  real cross-vertical signal). energy's lone β fail (`energy-h03`) is the same "Event"
  framing omitting the *restart* verb; its entity + handler + precision all passed.

### α handler-probe (reactive-path handler-selection; own lane, NOT the headline)

| vertical | graded breach | correct | accuracy |
|---|---|---|---|
| aquaculture | 40 | 31 | **77.5%** |
| energy | 40 | 40 | **100.0%** |
| supply_chain | 40 | 13 | **32.5%** |
| **overall** | **120** | **84** | **70.0%** |

The genuinely NEW signal (handler-selection on a real 4–5 option menu), read on its own
lane — in the procedure path the executed handler is fixed by `step.handler` (ADR-016), so
α is a reactive-path / future-autonomy measure, never the product's handler decision.

**supply_chain α = 32.5% is a BENIGN divergence, not a model error** (VERIFIED): the model
picks **`inspect`** (21/28 easy, 6/12 hard) where the dataset pins the single correct
handler `hold`. Inspecting a shipment after a cold-chain excursion is a defensible first
action — and crucially the model does **not** pick the dangerous near-misses `expedite` /
`reroute` (which would keep a possibly-spoiled load moving). β stays 100% because
`action_keywords` admits `inspect` / `hold` / `quarantine` / `divert` as the same action
class. **Finding → tuning PLAN:** the α `valid_handlers` for supply_chain is plausibly too
narrow (a cold-chain breach arguably accepts `[hold, inspect]`); whether to widen the α
expected-set is a tuning-PLAN question, **not** a grader change here (methodology is
ratified / fixed). aquaculture's 9 α misses are likewise mostly the benign
`increase_water_exchange` (7 — a real DO remedy), plus one `dispatch_technician` and one
`echo`.

### Deterministic disposition (sanity / false-positive guard, ~100% expected)

| vertical | items | correct | accuracy |
|---|---|---|---|
| aquaculture | 66 | 66 | 100.0% |
| energy | 66 | 66 | 100.0% |
| supply_chain | 66 | 66 | 100.0% |
| **overall** | **198** | **198** | **100.0%** |

### Latency (B-δ — SD-B1 ≤ 8 s p95 per LLM call)

| model | n calls | mean | p50 | p95 | max | SD-B1 p95 ≤ 8 s |
|---|---|---|---|---|---|---|
| `gpt-oss:20b` (hardened, 2026-06-09) | 240 | 15.02 s | 14.02 s | **22.64 s** | 31.46 s | ❌ **OVER (~2.8×)** |

Consistent with — and slightly above — the pre-hardening 19.23 s p95: the hard scenarios
carry extra `other_readings` context, so generations run a little longer. Same ring-fenced
B-δ finding (a tuning-PLAN input — **not** a build failure, **not** a bar move, **not** an
ADR-016 reopen).

### What the hardened run says (headline read)

`gpt-oss:20b` on the governed procedure path **clears the β ≥ 85% bar (85.8% / ~86–89%)
while the benchmark now genuinely discriminates**: aquaculture's hard multi-entity
scenarios pull β below 100% by surfacing a real entity-precision weakness (over-naming
safe siblings) and an action-verb-omission framing habit; the α probe surfaces a real but
**benign** handler-selection divergence (the model prefers `inspect` for cold-chain, not
the dangerous near-misses). Both feed the follow-up tuning PLAN under the B-6 ring-fence;
neither moves a bar or reopens ADR-016. The per-item `--dump-json` capture is the evidence
trail behind every number above.

## Results — PLAN-0020 tuning (2026-06-11) — the nudge effect + the latency lever

The PLAN-0020 host-state runs (`gpt-oss:20b` on MS-S1 `192.168.1.133:11434`,
Cray-approved, warm-first, instrumented; every per-item judgment
`--dump-json`-VERIFIED). These are the **first measurements WITH the Phase-1
aquaculture prompt nudge** (PR #232) live — its β effect was UNMEASURED until now.
Three full runs over all 198 items (120 graded breach × the Pattern-B exchange),
one per `reasoning_mode` (the AC-1a think-trim lever).

> **Latency bar = SD-2 (re-ratified 2026-06-11): ≤ 30 s p95 PER-JUDGMENT** (the
> end-to-end two-call wall-clock the human waits on), superseding SD-B1's 8 s
> per-call bar. Reports-not-gates. The per-call number is retained as a lever
> diagnostic. See AC-1d below for the analysis behind the unit change.

### The Phase-1 prompt nudge worked — dramatically (R1 = full mode = the measured nudge effect)

| metric | hardened baseline (2026-06-09, pre-nudge) | R1 full (2026-06-11, with nudge) |
|---|---|---|
| β overall | 85.8% | **100.0%** (120/120) |
| β aquaculture | 60.0% | **100.0%** (40/40) |
| α overall | 70.0% | **100.0%** (120/120) |
| α supply_chain | 32.5% | **100.0%** (40/40) |
| latency p95 per call | 22.64 s | 16.50 s |

**VERIFIED from the dump** (a suspiciously-uniform 100% demands the session-46
"confirm, don't infer" check — applied in reverse, to a *high* score): 0
`proposal_correct:false`, 0 `probe_correct:false`; supply_chain 40/40 `hold` and
**0 `inspect`**; **0 `forbidden_primary_keys` failures** (no over-naming on any
item, incl. the hard `*-h01..h12`); aquaculture/energy 80 canonical handlers, 0
`increase_water_exchange`. The grader is the SAME one that scored 60% / 32.5%
pre-nudge — it still discriminates (R2a/R2b below both drop below 100% on α), so
the jump is a real model improvement, **not a grader artifact**.

The nudge targeted aquaculture over-naming + verb-omission; two of its effects
were unplanned:
- **aquaculture over-naming** (11× `forbidden_primary_keys` → **0**) + **verb-
  omission** (7× `action_keywords` → 0): aqua β 60% → 100%.
- **supply_chain handler selection** (unplanned): "state the action verb in the
  title" pushed the model from `inspect` (the benign 32.5% α divergence) to the
  canonical `hold` (**0 `inspect`**) → supply α 32.5% → 100%. *(See SD-1 note.)*
- **latency** (unplanned): shorter, more-focused generations → per-call p95
  22.64 s → 16.50 s.

### Latency levers (AC-1a / AC-1e) — the think-trim sweep

One full 120-breach run per mode. Per-judgment latency = the end-to-end wall-clock
the human waits on (the SD-2 unit).

| `reasoning_mode` | calls / judgment | β overall | α overall | **per-judgment p95** | per-call p95 | vs SD-2 ≤ 30 s |
|---|---|---|---|---|---|---|
| `full` (shipped) | 2 | 100.0% | 100.0% | **31.80 s** | 16.50 s | ❌ OVER (by 1.8 s) |
| `think_off` | 2 | 98.3% | 98.3% | **40.96 s** | 22.51 s | ❌ OVER (*slower*) |
| **`skip`** | **1** | **100.0%** | 98.3% | **21.62 s** | 21.62 s | ✅ **PASS** |

**`think_off` is a dead lever.** `think=False` on call-1 did NOT reduce latency —
it was *slower* than `full` (per-judgment p95 40.96 s vs 31.80 s; the per-call
*median* p50 was also slower, 13.37 s vs 10.83 s, so it is not a tail-outlier
artifact). gpt-oss:20b generates a full structured draft on call-1 regardless of
the `think` flag, so dropping the reasoning *block* saves no generation cost. It
also cost ~1.7 % β (2 items, both explainable below). **Discard.**

**`skip` is the latency lever — a strict win on the procedure path.** Dropping
call-1 entirely (a single structured call from the event) cut per-judgment p95 to
**21.62 s, under the 30 s bar**, while **β stayed 100 %** (0 `proposal_correct:
false`; 40/40 `hold`, 0 over-naming — the same quality as `full`). The reasoning
pass adds **nothing** to the β headline given the nudged prompt; it was purely a
latency tax. The only cost is α (the reactive-path handler *guess*): 2 aquaculture
items (`aqua-014`, `aqua-h05`) picked `dispatch_technician` over
`start_emergency_aerator` → α 98.3 %. **This does not touch the procedure
product**, which overrides the handler deterministically with the author's
`step.handler` (ADR-016 D3) — the α probe is a reactive-path / future-autonomy
signal only.

### AC-1d — the 8 s-bar review (the analysis behind SD-2)

SD-B1 was **8 s p95 per LLM call**, but a procedure judgment is a **two-call**
Pattern-B exchange, so the human waits ~2× per affected entity. The
operationally-meaningful unit is therefore **per-judgment** (end-to-end), not
per-call. Empirically:
- per-**call** p95 ranged 16.5–22.5 s across the three runs — **noisy**:
  local-model latency varies run-to-run (`full` and `think_off` share the 2-call
  shape yet measured 31.80 s vs 40.96 s per-judgment, ~±10 s of noise).
- per-**judgment** ≈ 2× per-call for the 2-call modes (~30–41 s), ≈ 1× for `skip`
  (~22 s).
- The 8 s per-call bar implied a ~16 s end-to-end floor the pinned model never
  approached. **30 s per-judgment** is the real human wait and the unit Cray
  re-ratified (**SD-2**). Under it, `skip` PASSES and `full` is marginally OVER.

### AC-1e — recommendation

**Adopt `reasoning_mode="skip"` on the procedure path.** It is the only lever
that clears the SD-2 30 s per-judgment bar (21.62 s) and it does so at **zero β
cost** (the reasoning pass is redundant given the nudged prompt). `think_off` is
discarded (slower).

**One trade-off for a separate design call (NOT decided here):** `skip` removes
the call-1 reasoning narrative (`thinking` / `draft`) from the ADR-010 hybrid
audit trail — the model-asserted `rationale` survives (it is an `LlmJudgment`
field), but the step-by-step reasoning narrative does not. Whether human-review /
audit needs that narrative, or the rationale suffices, is a Cray / ADR-010
decision. **Wiring `skip` into the product** (`Agent` / `action_step`) is a
follow-up, not part of this measure-and-report PLAN.

### AC-1b — request batching (negative finding)

Batching the per-step entity judgments on a single quiesced MS-S1 yields **no
per-judgment wall-clock benefit**: one Ollama instance on one GPU serializes
concurrent generations, so N concurrent judgments take ~N× the time regardless.
And `skip` already reduces each judgment to one call, so the 2N→N call-count
motivation is largely moot. **Recorded as infeasible-without-benefit on the
current single-host topology** (a valid negative per AC-1b); a multi-GPU /
multi-replica MS-S1 would change this.

### AC-1c — faster-architecture model (deferred; pin holds)

No new genuinely-faster-architecture candidate was evaluated this round. The G-3
sweep already established the pin is best on both axes among 12 B–35 B local
models, and a **Cowork research dispatch** (why gpt-oss:20b wins → a
model-selection rubric) is in flight to pre-screen future candidates *before*
spending an MS-S1 warm cycle. **The ADR-001 pin HOLDS**; candidate screening is
delegated to that rubric (a future swap, gated on ADR-001 re-ratification).

### SD-1 implication — the supply_chain α divergence has DISAPPEARED

SD-1 (widen supply_chain α `valid_handlers` `[hold]` → `[hold, inspect]`) was
motivated by the model picking `inspect`. **With the nudge the model now picks
`hold` (0 `inspect` across all 40 supply items in every 2026-06-11 run).** The
divergence that justified widening the expected-set is gone, so **SD-1's
empirical motivation is moot** — widening would be harmless but no longer corrects
a real mis-report. **Step-9 decision (Cray, 2026-06-11): SKIP** — no grader /
dataset edit; this analysis is the logged finding. The richer fix surfaced by
Cray's production-fidelity review — a **tiered handler grading** (canonical /
acceptable / forbidden, so the α metric itself distinguishes a benign alternative
like `inspect` from a dangerous pick like `expedite` / `reroute`, instead of a
human reading the dump) — is deferred to a **follow-up PLAN**.

### Caveats

- **One run per mode** (local model is non-deterministic). An earlier 2-item
  smoke showed aquaculture α can vary (an item picked `increase_water_exchange`);
  a companion run would establish the honest range. The β / latency *directions*
  are robust (skip's single-call structural halving; the nudge's over-naming fix
  is 0/40 across runs).
- **Two observed failure modes** (reports-not-gates findings, not addressed
  here): `aqua-028` hedges "WATCH" at the inclusive boundary (DO = 4.0 exactly) —
  consistent across runs; `energy-027` emitted a non-breaking hyphen
  (`asset‑E27`, U+2011) in the entity key, breaking exact-match (a future grader
  could normalize hyphens).

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
> check did not move it (echo was the only enum choice). The hardened re-run is now
> DONE — see **Results — HARDENED run (2026-06-09)** above; this table is RETAINED as
> the pre-hardening baseline (well-posed, single-entity) for comparison.

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
  **PR2 (done):** the hard scenarios + precision checks (below). **Next:** the
  hardened re-run (host-state — ASK Cray). Until that run lands, the pre-hardening
  100% means "the well-posed path works end-to-end," not "the model is infallible."

### PR2 hard scenarios + precision checks (the β-headline discriminator)

Each vertical augments its 28 boundary-cluster breach items with **12 HARD breach
items** (`*-h01..h12`; the easy items stay as the floor baseline), each combining:

- **Multi-entity decoys** — the breached entity is presented amid 1–3 **safe** sibling
  readings (injected into the event as `other_readings`, most in the watch band so
  they read as "borderline"). The model must name the breach **and not** the decoys —
  graded by `affected_primary_key` (right entity) + `forbidden_primary_keys` (no decoy
  named). A dataset guard asserts every decoy is genuinely non-breaching and that
  `forbidden_primary_keys` exactly matches the scenario's distractor set.
- **Near-miss action** — a plausible-but-wrong action class the model must avoid
  recommending: aquaculture `feed` (feeding during an O₂ crash), energy
  `monitor`/`schedule` (deferring an acute over-temp), supply_chain `expedite`/`reroute`
  (keeping a possibly-spoiled load moving). Graded by `action_keywords` (right verb
  present) + `forbidden_keywords` (decoy verb absent from the **title** — the body may
  legitimately rule it out).

So the hardened β headline tests **entity-ID precision under distractors** and **action
selection against near-misses** — the two things the model actually owns in the
procedure path — instead of the trivial single-entity / single-handler path.

## Latency (B-δ — SD-B1 ≤ 8 s p95 per LLM call)

Measured per **LLM call** (a breach item = 2 Pattern-B calls) via the runner's
`TimingChatClient`, **warm-first** on MS-S1. *(Pre-hardening 84-breach run; the hardened
120-breach latency — p95 22.64 s, same OVER finding — is in the
[2026-06-09 section](#latency-b-δ--sd-b1--8-s-p95-per-llm-call) above.)*

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

*PLAN-0019 Part B. **B-β headline** + **α probe** + sanity + **B-δ latency + B-4/G-3
model sweep** filled from Cray-approved live runs (`gpt-oss:20b` / `gemma4:12b` /
`qwen3.6:35b` / `gemma4:26b` on MS-S1, Ollama 0.30.6, 2026-06-08/09), plus the
**HARDENED re-run 2026-06-09** (real menu + hard scenarios; β 85.8% / ~86–89%, α 70.0%,
latency p95 22.64 s, every score `--dump-json`-VERIFIED). **B-3 baselines** (text-to-SQL
+ RAG) remain TODO. Per the ring-fence this REPORTS — it does not gate; the hardened
headline, the benign α divergence, and the latency miss are all read with the caveats
above and feed the follow-up tuning PLAN.*
