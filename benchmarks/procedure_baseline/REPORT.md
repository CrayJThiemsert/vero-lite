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
  *(Since PLAN-0022 Phase 3, watch items additionally run the LLM judgment and are
  graded on the **watch-tier lane** — see the methodology section below; their
  deterministic disposition stays this sanity check, and `ok` items still make no
  LLM call.)*
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

## Watch-tier lane methodology (PLAN-0022 Phase 3 — ratified BEFORE any scored run)

> **Provenance.** Methodology M-1..M-4 was **Cray-ratified 2026-06-12** (session 55,
> quoted: "M-2: เลือก (b) + เห็นชอบ M-1/3/4"), per the B-6 anti-moving-target
> discipline: the scoring scheme below is fixed **before** the first scored run that
> exercises it. The first run — calibration-only by design (M-2=b) — ran later the
> same day (Cray go, session 56): see
> [Results — watch-lane CALIBRATION run](#results--watch-lane-calibration-run-2026-06-12)
> below. PLAN-0022 Step 5 / SD-3 is the design source.

- **M-1 — the lane (per SD-3 / SD-4=a).** Watch items now RUN the LLM judgment
  (previously the harness made no LLM call for non-breach) and are graded on a
  **new watch-tier lane**, never folded into β. Item lane-pass = proposed handler ∈
  {`canonical`, `acceptable`}; a `forbidden_keywords` hit is named explicitly via
  the shared `classify_handler_tier` — the same taxonomy as the α probe, defined
  once. The lane mirrors α's isolation discipline: own fields, own aggregation, own
  print segment, own dump keys.
- **M-2 = (b) — calibration-first (the load-bearing choice).** Watch items'
  ground-truth `canonical_handler` / `acceptable_handlers` are **not authored
  yet** — no REPORT evidence exists, because the watch path never ran an LLM. The
  first scored run therefore treats the watch lane as **calibration-only**: it
  reports the suggested-handler **distribution per vertical** (counts; no pass/fail
  pinned, no bar). Ground truth gets pinned from that evidence in a follow-up —
  mirroring the B-β calibration precedent (Cray-ratified 2026-06-08, "Calibration
  log" below). Implementation consequence: a watch item that declares no handler
  tiers grades **unscored** (distribution evidence), never a fail. *(Since
  PINNED — #286, Cray-adjudicated 2026-06-12 from the calibration distribution;
  see [Results — watch-lane first SCORED run](#results--watch-lane-first-scored-run-2026-06-12).)*
- **M-3 — mis-routing columns are structural.** "Acted deterministically on a
  watch item" / "escalated a breach item" / "fired on ok" are **structurally
  impossible in this harness**: the dataset disposition and the lane selection both
  derive from the same `classify_verdict` (the single shared band definition), so
  the existing deterministic sanity lane covers them. They are reported as
  structural — no fake failure surface is invented. (In the *product*, AC-8's named
  determinism test — identical routing under varied `confidence` — covers the
  equivalent invariant.)
- **M-4 — latency stays breach-scoped.** Watch-item judgment latency is recorded
  as its **own diagnostic** (n / mean / p50 / p95 / max; no bar). The SD-2
  **≤ 30 s p95 per-judgment** acceptance bar remains **breach-scoped**. **No bar
  moves** (B-3/B-6).

The determinism invariant holds throughout (AC-3 / ADR-0019): the watch lane grades
the model's *proposal* on items the **deterministic** watch band routed; `confidence`
never routes (advisory display only, ADR-010 IN-3).

## Results — watch-lane first SCORED run (2026-06-12)

The first run grading the watch lane against **pinned** ground truth (#286 —
the M-2=b follow-up; Cray adjudicated the pinning the same day from the
calibration distribution below). Same recipe as the calibration run:
`gpt-oss:20b` (ADR-0001 pin) on MS-S1, warm-first (model already resident),
full 198 items, `reasoning_mode=full`, **318 LLM calls**, **0 errors / 0
`StructuredOutputError`**; first full-run use of the carrier-proof
`run_detached.sh` launcher (sentinel `0 2026-06-12T21:25:22+07:00`; ~67 min).
Every number below was **VERIFIED against the `--dump-json` records**: all 39
watch records carry `watch_graded: true` + a real tier/handler — the scored
state, flipped automatically by the dataset pinning, **zero harness change**.

### Watch-tier lane (the headline of this run) — 97.4% (38/39)

| vertical | lane | tier split | handler distribution |
|---|---|---|---|
| aquaculture | **100% (13/13)** | canonical 13 | `start_emergency_aerator` 13 |
| energy | **100% (13/13)** | canonical 13 | `restart` 13 |
| supply_chain | **92.3% (12/13)** | canonical 6 / acceptable 6 / **forbidden 1** | `inspect` 6 / `hold` 6 / **`reroute` 1** |

**The one FAIL is the lane doing its job.** `supply-040` (7.8 °C — a hair
below the 8.0 ceiling): the model judged *"Proceed — No breach detected;
continue normal operations"* and suggested `reroute` at `confidence` 1.0
(VERIFIED from the dump record) — exactly the dangerous near-miss class
(keep the possibly-compromised load moving) the calibration run surfaced
3/13 times, now **scored forbidden** via the declared `forbidden_keywords`.
Run-to-run note: the reroute instinct appeared 1/13 this run vs 3/13 in
calibration (same band, same recipe) — the class is real but intermittent;
the lane now scores it every time it appears.

### Companion lanes (same run) — β / α / sanity

| lane | result | note |
|---|---|---|
| β headline | **98.3%** (118/120) — ✅ ≥ 85% | aqua 39/40, energy 39/40, supply 40/40 |
| α handler-probe | **100.0%** (120/120: canonical 117 / acceptable 3 / forbidden 0 / other 0) | own lane |
| deterministic | **100.0%** (198/198) | the M-3 structural columns are covered here |

The two β misses are the **same two known items** (dump-verified):

- `aqua-028` — the inclusive-boundary hedger (DO = 4.0) again: a real remedy
  proposal with no `aerat`/`oxygenat` lemma → `action_keywords` miss.
- `energy-007` — the **non-breaking-hyphen class, third occurrence across
  runs** (`asset‑E07` U+2011 vs expected ASCII `asset-E07` → exact-match miss
  on `affected_primary_key`). The hyphen-normalization grader change stays
  **PENDING Cray ratification** (B-6) — now with 3 data points.

### Latency (same run) — SD-2 nominally OVER, two readings

| unit | n | mean | p50 | p95 | max | bar |
|---|---|---|---|---|---|---|
| per **breach** judgment (SD-2) | 120 | 22.12 s | 21.39 s | **30.18 s** | 57.15 s | ❌ **OVER ≤ 30 s (by 0.18 s)** |
| per **watch** judgment (M-4 diagnostic) | 39 | 31.67 s | 27.95 s | 54.10 s | 56.38 s | — (no bar, by design) |
| per LLM call (lever diagnostic) | 318 | 12.23 s | 11.02 s | 21.32 s | 43.54 s | — |

Recorded without moving any bar (B-6): (1) **the straddle reading holds** —
full-mode SD-2 p95 across runs now reads 31.80 → 28.73 → 30.18 s, all inside
the documented ±10 s run-to-run noise band around the 30 s bar; (2) **a
contamination source unique to this run**: session 57 is the first session
whose live Stop/PreToolUse classifier ALSO generates on MS-S1
(`gpt-oss:20b`, #282), and a handful of classifier calls overlapped the
measured window — structurally violating the serialize discipline (the
classifier is wired into the harness, not a choice). If a clean SD-2 verdict
is ever needed, rerun with the session quiesced or with
`CLAUDE_CLASSIFIER_BACKEND=sonnet` for the run window. The watch-latency
diagnostic repeats the calibration shape (slow tail, p95 ~54 s).

### Run provenance / integrity

- Artifacts: `.claude/benchmark-results/2026-06-12-watch-scored.{log,jsonl,wrap,done}`
  (198/198 item records; gitignored working artifacts, retained locally).
- First production run on `run_detached.sh`: the systemd unit survived its
  launcher and wrote the `.done` sentinel as its last act, as designed. The
  harness-side *watcher* monitor died silently mid-run (the known
  lost-notification class) — completion truth was recovered via the
  content-based test (sentinel + `DUMP: wrote 198` + empty `pgrep`), i.e. the
  sentinel design carried exactly the failure it was built for.

## Results — watch-lane CALIBRATION run (2026-06-12)

The first scored run exercising the watch-tier lane (Cray go 2026-06-12, session
56). `gpt-oss:20b` (ADR-0001 pin) on MS-S1 (`192.168.1.133:11434`), warm-first
(cold load 25 s), full 198 items, `reasoning_mode=full` (the shipped default),
**319 LLM calls** (120 breach + 39 watch, ×2 Pattern-B calls, +1 in-budget retry),
**0 `StructuredOutputError`**, **0 watch-lane errors**. Every number below was
**VERIFIED against the `--dump-json` records** (the session-46 "confirm, don't
infer" discipline): all 39 watch records carry `watch_pass: null` /
`watch_tier: null` (unscored — the M-2=b calibration state, exactly as designed)
and a real model judgment.

### The calibration evidence — suggested-handler distribution per vertical (M-2=b)

Counts only — **no pass/fail pinned, no bar** (the methodology above). This table
is the evidence base from which the watch ground truth
(`canonical_handler`/`acceptable_handlers` per watch item) gets pinned in the
follow-up; **Cray adjudicates the pinning**.

| vertical | watch items judged | suggested-handler distribution |
|---|---|---|
| aquaculture | 13 | `start_emergency_aerator` **13** |
| energy | 13 | `restart` **13** |
| supply_chain | 13 | `hold` **5** / `inspect` **5** / **`reroute` 3** |

**Reading.** aquaculture and energy are **unanimous**: on the ambiguous watch
band the model proposes the same canonical handler the breach path executes —
the escalation proposal is "do the breach remedy, pending human approval."
supply_chain **splits** — and surfaces the lane's first real safety signal: in
**3/13** watch judgments the model proposed **`reroute`** (titles VERIFIED from
the dump: *"Continue"*, *"Proceed with shipment ship-S33"*, *"Proceed"* — each at
`confidence` 1.0). On a borderline cold-chain excursion the model's instinct is
to *keep the possibly-compromised load moving* — precisely the dangerous
near-miss class (`expedite`/`reroute`) the breach-path β precision checks exist
for, now observed on the watch band where no check yet scores it. **Pinning
implication (for the follow-up, not decided here):** if the supply_chain watch
ground truth pins around `{hold, inspect}` with the existing
`forbidden_keywords` (`expedite`/`reroute`), those three picks classify
**forbidden** and the lane discriminates exactly as intended. Per the B-6
ring-fence this is a logged finding feeding the pinning follow-up — no bar, no
grader change here.

### Companion lanes (same run) — β / α / sanity

| lane | result | note |
|---|---|---|
| β headline | **98.3%** (118/120) — ✅ ≥ 85% | aqua 39/40, energy 39/40, supply 40/40 |
| α handler-probe | **100.0%** (120/120: canonical 117 / acceptable 3 / forbidden 0 / other 0) | own lane |
| deterministic | **100.0%** (198/198) | the M-3 structural columns are covered here |

The two β misses, **VERIFIED from the dump as real model verdicts**:

- `aqua-028` — the **known inclusive-boundary hedger** (DO = 4.0 exactly;
  consistent across runs since 2026-06-08). This run it proposed
  *"Exchange-Water for Pond A28"* — a real DO remedy, but no `aerat`/`oxygenat`
  lemma in any free-text field → `action_keywords` miss.
- `energy-007` — the **non-breaking-hyphen failure mode again** (same class as
  `energy-027` in the 2026-06-11 runs): the model named the correct entity as
  `asset‑E07` (U+2011) where the dataset expects `asset-E07` (ASCII) →
  exact-match miss on `affected_primary_key`. Two occurrences across runs make
  hyphen normalization a **standing grader-calibration candidate** — a
  measurement-correctness fix in the spirit of the 2026-06-08 calibration log,
  but it touches ratified methodology, so it waits for Cray ratification (B-6).

### Latency (same run)

| unit | n | mean | p50 | p95 | max | bar |
|---|---|---|---|---|---|---|
| per **breach** judgment (SD-2) | 120 | 21.67 s | 21.02 s | **28.73 s** | 57.08 s | ✅ **PASS ≤ 30 s** |
| per **watch** judgment (M-4 diagnostic) | 39 | 32.12 s | 29.78 s | **54.21 s** | 55.55 s | — (no bar, by design) |
| per LLM call (lever diagnostic) | 319 | 12.08 s | 10.91 s | 21.10 s | 43.69 s | — |

**First SD-2 PASS in `full` mode** (the 2026-06-11 `full` run read 31.80 s —
within the documented ±10 s run-to-run noise band, so read this as "full mode
straddles the bar," not "full mode got faster"; `skip` remains the ratified
under-the-bar lever at 21.62 s). The **watch judgments run notably slower than
breach** (mean 32.12 s vs 21.67 s; p95 54.21 s vs 28.73 s) — recorded as the M-4
diagnostic; if watch escalation latency ever matters operationally, that is a
new conversation (and a new bar proposal), not a silent fold into SD-2.

### Run provenance / integrity

- Artifacts: `.claude/benchmark-results/2026-06-12-plan0022-phase3-calibration.{log,jsonl}`
  (198/198 item records; gitignored working artifacts, retained locally).
- The run wrapper hit the known **one-off background reap** (~59 min in, heartbeat
  stopped, no `[wrap] EXIT` marker) but the benchmark process itself completed and
  wrote the full log + dump — artifacts intact, integrity unaffected (matches the
  documented one-off pattern; not a TTL).

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

**Addendum — hyphen normalization (Cray-ratified 2026-06-12).** The model
intermittently emits **U+2011 NON-BREAKING HYPHEN** inside otherwise-correct
entity keys (`asset‑E07` vs the dataset's ASCII `asset-E07`) — three
dump-verified occurrences across runs (energy-007 ×2: the 2026-06-11 full run +
the 2026-06-12 scored run; energy-027 ×1: 2026-06-11). Same
measurement-correctness class as items 1–4: an entity-identity miss on a glyph
variant is a grader artifact, not a model error. Fix: primary-KEY comparisons
(`affected_primary_key` / `forbidden_primary_keys`) normalize the Unicode
hyphen/dash family (U+2010..U+2014, U+2212) to ASCII `-` on **both** sides
(`normalize_primary_key`); free-text matching (`action_keywords` /
`forbidden_keywords`) is deliberately untouched — no evidence of need. No bar
moves; the known aqua-028 hedger miss is NOT in this class and remains a real
model miss. Effect verified by re-grading the stored 2026-06-12 scored-run dump
offline: energy-007 flips to PASS (β would read 119/120 = 99.2%); the published
run tables stay **as-run** — recorded numbers are never rewritten retroactively
(anti moving-target).

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

## B-3 comparison (REPORTED, not a gate) — the three-arm baseline (B-γ)

> **Reports-not-gates (B-3/B-6).** "Our stack wins" is the **thesis under test**,
> NOT an acceptance condition. A baseline matching or beating arm (a) is a
> **finding**, never a build failure, and moves no bar / reopens no ADR-016 shape.
> The methodology was pre-registered + Cray-ratified BEFORE this scored run
> (PLAN-0027 §3–§4); one measurement-correctness calibration (the arm-(c)
> free-text case/hyphen normalization) was ratified from the pre-run smoke, also
> before the run. As-run numbers are never rewritten retroactively.

**The comparison (PLAN-0027).** The vero-lite governed-procedure stack (arm a) vs
two baselines — (b) raw text-to-SQL, (c) lean-but-real RAG — on the **energy
breach subset** (40 items), graded on the **common sub-task** (D-1: name the
affected entity + the correct action class, reusing `grade_proposal`). Arm (a) is
**reused** from the runs above (D-2 — NOT re-run). Scored run: `gpt-oss:20b`
(ADR-0001 pin) on MS-S1, 2026-06-16, warm-first; **0 errors / 0 invalid SQL**;
every per-item score VERIFIED from `--dump-json` with the Read tool (session-46
confirm-don't-infer).

### Results — per-arm accuracy / failure-mode / latency

| arm | entity-ID | action-class | entity **+** action (common sub-task) | latency / item | failure-mode |
|---|---|---|---|---|---|
| **(a) governed-procedure stack** (reused, D-2) | — | — | **97.5–100%** (39–40/40) | p95 **~28.7–31.8 s** (2-call judgment) | the known boundary/glyph misses (above) |
| **(b) raw text-to-SQL** | **100%** (40/40) | **structurally N/A** (D-3) | **incomplete** — SQL returns data, not an action | p95 **10.2 s** (1 SQL-gen call) | 0 invalid, 0 wrong; **0 action proposals possible** |
| **(c) lean RAG** | **97.5%** (39/40) | **100%** (40/40) | **97.5%** (39/40) | p95 **3.21 s** (1 freeform call) | 1 entity miss (`energy-h05`: model abbreviated `asset-E113` → `E113`) |

*(arm b latency p50 8.16 s / max 12.05 s; arm c p50 2.25 s / max 4.17 s; arm a per the SD-2 rows above.)*

**Reading — three honest findings:**

1. **Raw entity+action accuracy does NOT separate the governed stack from lean
   RAG.** Arm (c) scored **97.5%** on the common sub-task — level with arm (a)'s
   97.5% (hardened) / 100% (nudged). On *this* measure a naive
   retrieval-augmented baseline is as accurate as the governed path. Per the
   ring-fence this is a **finding, not a failure** — and it is the load-bearing
   one: it relocates the moat claim OFF "raw NL→action accuracy" (where RAG ties)
   and ONTO the governance layer (§3.4 below), which the comparison was designed
   to isolate.
2. **Raw SQL cannot propose an action at all (D-3, structural).** Arm (b) nailed
   entity-ID (40/40 — every query wrote the correct `WHERE measured_value >= 90`
   threshold join and returned the breach asset), but text-to-SQL **returns data,
   not an action proposal**, so it is *structurally* unable to produce the
   action-class half of the operator's question. The 100% entity number is only
   half the sub-task — recorded as the structural finding, never scored wrong.
3. **The baselines are 3–15× faster** (arm c p95 3.2 s, arm b 10.2 s vs arm a's
   ~30 s per judgment). The governed stack's two-call reason→structure exchange
   costs latency the single-call baselines do not — a logged finding
   (reports-not-gates), consistent with the B-δ latency findings above.

### What the comparison is designed to show (§3.4 narrative — Cray-directed)

The qualitative differentiator between arm (a) and arm (c) is a **governed
inter-step contract layer**, NOT raw accuracy on this sub-task (where they tie).
vero-lite's procedure engine can (i) **verify** an LLM step's output for
*semantic* consistency against that step's requirement and (ii) **reshape** the
output to fit the next step's input contract. A naive RAG baseline structurally
lacks this — no deterministic disposition (breach/watch/ok), no handler
allowlist, no audit trail, no inter-step contract glue. Two concrete tells
surfaced in THIS run even where the headline tied:

- arm (c)'s sole miss (`energy-h05`) is an **output-fidelity** failure the
  governed path cannot make: the model identified the right physical unit but
  emitted a **non-canonical reference** (`E113` instead of the ontology key
  `asset-E113`). The governed stack emits the schema-constrained PK by
  construction — a downstream system can act on it; the RAG string cannot be
  trusted to be canonical.
- arm (c) has **no disposition / allowlist / audit** — it will equally
  confidently "restart" whatever a prompt frames as a breach, with no
  deterministic false-positive guard and no bounded handler set. The headline
  parity is on *accuracy*; the gap is on *governability*.

So the arm(a)–arm(c) parity on raw accuracy, read with these tells, IS the
evidence: the moat is the governance layer over and above retrieval-augmented
generation, not a raw-accuracy edge.

> **Forward-pointer / future-work (OUT OF SCOPE for B-γ).** The **verify +
> reshape** layer above is a **separate, future procedure-engine enhancement**
> (ADR-016 area) — NOT built or measured in B-γ (measurement-only). The engine
> **today** already has structured-output **schema** validation
> (`StructuredOutputError`, `services/engine/llm/structured.py`); the enhancement
> would extend that from schema-validation to **semantic-verify + inter-step
> reshape**. Recorded as a forward-pointer for a future PLAN/ADR; it is NOT added
> to arm (c) (D-6 contamination guard).

### Run provenance / integrity

- **Model:** `gpt-oss:20b` (ADR-0001 pin), live on MS-S1 (`192.168.1.133:11434`),
  Cray-approved host-state run 2026-06-16, warm-first.
- **Scope:** 40 energy breach items × arms (b) + (c) = 80 LLM calls (1 per
  arm-item); arm (a) reused (D-2). 0 errors / 0 invalid SQL.
- **Calibration (ratified before the run — B-6):** the arm-(c) free-text entity
  match is case- + hyphen-normalized (a measurement-correctness fix surfaced by
  the pre-run smoke — `energy-001`'s `Asset‑E01`, capital + U+2011; the free-text
  analogue of the grader's `normalize_primary_key` hyphen calibration). It only
  *recovers* a correctly-named entity, never invents one — it helps the baseline,
  so the arm(a)–arm(c) parity is if anything conservative for the thesis. Lands
  with this REPORT's companion engineering PR; the offline mock gate stays the
  oracle.
- **Artifacts:** `.claude/benchmark-results/2026-06-16-bgamma-scored.{log,jsonl}`
  (40/40 item records; gitignored working artifacts, retained locally). Every
  number above VERIFIED against the `--dump-json` records.
- **Harness:** `benchmarks/procedure_comparison/` (PLAN-0027); the offline mock
  gate (ruff / mypy --strict / pytest) is green and is the oracle — this live run
  is evidence, not the gate.

### B-γ cross-vertical extension — aquaculture + supply_chain (PLAN-0028)

> **Does the energy finding REPLICATE across verticals?** PLAN-0028 extends the
> three-arm comparison from energy to two more verticals — **aquaculture** (a
> below-floor dissolved-oxygen breach) and **supply_chain** (an above-ceiling
> cold-chain temperature breach). Same methodology; D-1..D-6 + the joint SD-1↔SD-2
> fairness binding inherited verbatim (PLAN-0027). Arm (a) **reused** from the
> per-vertical hardened/nudged runs (D-2 — NOT re-run); arms (b)+(c) run fresh.
> Scored run: `gpt-oss:20b` (ADR-0001 pin) on MS-S1, 2026-06-17, warm-first, ONE
> combined sweep (80 breach items = 40+40); **0 errors / 0 invalid SQL**; every
> score VERIFIED from `--dump-json` with the Read tool.

**aquaculture breach subset (40 items; corpus `aquaculture_v0` = 11 snippets, k=4):**

| arm | entity-ID | action-class | entity **+** action | latency p50 / p95 | failure-mode |
|---|---|---|---|---|---|
| **(a) governed** (reused, D-2) | — | — | **100%** nudged (40/40) · **60%** hardened (24/40) | ~28.7–31.8 s p95 | OQ-3: read the nudged headline, disclose the 60→100 range |
| **(b) raw text-to-SQL** | **0%** (0/40) | structurally N/A (D-3) | **incomplete** | 11.5 s / 14.6 s | 40 wrong, 0 invalid — over-constrains with a guessed free-text `description LIKE '%dissolved_oxygen%'` → 0 rows |
| **(c) lean RAG** | **100%** (40/40) | **100%** (40/40) | **100%** (40/40) | 2.7 s / 4.2 s | none (post-PLAN-0029 calibration; see below) |

**supply_chain breach subset (40 items; corpus `supply_chain_v0` = 10 snippets, k=4):**

| arm | entity-ID | action-class | entity **+** action | latency p50 / p95 | failure-mode |
|---|---|---|---|---|---|
| **(a) governed** (reused, D-2) | — | — | **100%** (40/40, hardened + nudged) | ~28.7–31.8 s p95 | — |
| **(b) raw text-to-SQL** | **100%** (40/40) | structurally N/A (D-3) | **incomplete** | 8.7 s / 9.9 s | 0 wrong, 0 invalid — clean `unit='celsius' AND measured_value>=8` threshold join |
| **(c) lean RAG** | **100%** (40/40) | **100%** (40/40) | **100%** (40/40) | 3.7 s / 4.9 s | none |

**Reading — the finding REPLICATES, with a sharper explanatory variable:**

1. **arm (c) lean RAG ties arm (a) governed on BOTH new verticals** (100% / 100%),
   exactly as on energy (97.5% ≈ arm a). The arm-c≈arm-a parity is **not an energy
   fluke — it replicates** (OQ-2: all three reported honestly; the tie does
   replicate). Per the ring-fence this is a **finding, not a failure** — it
   re-confirms the moat relocation OFF raw NL→action accuracy and ONTO the
   governance layer (§3.4).
2. **arm (b) raw text-to-SQL swings 0% (aquaculture) ↔ 100% (supply_chain)** — the
   most informative result. The explanatory variable is the **semantic distance**
   between the operator's NL question and the physical schema encoding:
   supply_chain's breach is a clean numeric threshold
   (`unit='celsius' AND measured_value>=8`) the model expresses directly, and the
   entity IS the `asset_id` primary key → **low distance → 100%**. aquaculture's
   breach meaning lives partly in a free-text `description` literal the model must
   guess (`'%dissolved_oxygen%'` → 0 rows) and the entity is a named `site`/pond
   subtype → **high distance → 0%**. Raw text-to-SQL's accuracy is a function of
   **schema-vocabulary luck**; the ontology/governed stack declares that mapping
   once and removes the dependence. **Semantic distance ↑ ⇒ the value of the
   ontology ↑** (the inverse of "harder vertical = our stack looks worse": harder
   *mapping* = the moat matters *more*).
3. **The baselines stay 3–10× faster** (arm c ~4 s p95, arm b ~10–15 s vs arm a's
   ~30 s) — consistent across verticals; a logged finding (reports-not-gates).

**OQ-3 — aquaculture arm (a) headline.** The reused aquaculture arm (a) reads the
**nudged 100%** (40/40, PLAN-0020 R1) as the external-grade headline AND discloses
the **60→100 range**: the hardened run (2026-06-09) scored 24/40 = 60% on the full
precision key; the Phase-1 prompt nudge lifts it to 40/40. The 60% basis is graded
on arm (a)'s full hardened key, so a "60%-basis arm c beats arm a" reading would be
confounded by the grading asymmetry in the next caveat — hence the range is
disclosed, nothing hidden.

**OQ-1 fairness disclosures (R-OQ1-1..4, PLAN-0028 §3.5; D-6 intact — corpus+prompt levers only):**

- **Corpus size + retrieved fraction (§3.5 A).** `aquaculture_v0` = **11 snippets**,
  `supply_chain_v0` = **10 snippets** (energy ≈ 10) — structural parity (same
  snippet KINDS), sized to each vertical's action vocabulary, **not** an identical
  count. Each uses **one consolidated breach-action playbook snippet** naming all
  breach lemmas together (aquaculture `aerate`/`aeration`/`oxygenate`; supply_chain
  `hold`/`inspect`/`quarantine`/`divert`) so the action-relevant snippet reliably
  ranks **top-4 of ~10–11** under k=4.
- **Retriever near-oracle caveat (§3.5 B).** The retriever is the locked
  deterministic **lexical** top-k (D-4, not re-opened). Under the joint binding the
  action-relevant snippet is guaranteed surface-token-retrievable, so lexical
  retrieval behaves as a **near-oracle** for the graded lemmas — retrieval is
  *generous* to arm (c), so an arm(a)≈arm(c) **parity is conservative for the moat
  thesis**, not a lexical handicap. Robustness is claimed only for corpora honouring
  the binding.
- **Parity disambiguation / over-cover guard (§3.5 D).** The binding is two-sided:
  every breach lemma is covered AND no snippet names a dataset entity key
  (`pond-A`/`ship-S`) or hands the model the per-item answer (asserted in tests — arm
  (c) must still pick the breached entity from the readings and map condition →
  action). The dangerous near-miss actions are disambiguated in-corpus.
- **Inherited grading-asymmetry caveat (D-1 `_reduced_expected`).** Arm (c) is graded
  on the **common sub-task** — entity-present (`affected_primary_key`) + action-class
  (`action_keywords`) — via the D-1 reduced expected; it is **NOT** graded on arm
  (a)'s full hardened key (no `forbidden_primary_keys` precision add-on, no handler
  probe). Arm (c)'s "100%" is therefore a **looser entity grade** than arm (a)'s
  hardened key — the comparison is on the common sub-task both arms share, not arm
  (a)'s full precision bar.

**A2 — equal-rubric re-grade (closes the inherited grading-asymmetry caveat above
+ OQ-3).** To remove the asymmetry as a confound, arm (a) is re-graded on the
**same reduced rubric arm (c) uses** (`_reduced_expected` = entity-present +
action-class only) — recomputed **offline** from arm (a)'s RAW judgments with the
CURRENT grader (same normalizer, no host-state re-run). On the identical reduced
rubric:

| vertical | arm (a) hardened (full → reduced) | arm (a) nudged (full → reduced) | arm (c) reduced |
|---|---|---|---|
| energy | 39 → **39** (97.5%) | 40 → **40** (100%) | 39/40 (97.5%) |
| aquaculture | 24 → **33** (60% → 82.5%) | 40 → **40** (100%) | 40/40 (100%) |
| supply_chain | 40 → **40** (100%) | 40 → **40** (100%) | 40/40 (100%) |

The six **full-key** numbers reproduce the arm-(a) headlines stated above (hardened
39/24/40, nudged 40/40/40), confirming the recompute reads the right dumps. The
original "arm c 100% vs arm a 60%" reading (aquaculture) confounded **two** levers —
the full-vs-reduced **rubric** AND the hardened-vs-nudged **prompt**. A2 separates
them: matching the rubric lifts hardened arm (a) **24 → 33** (all nine lifted items
pass entity + action and failed full only on the dropped precision add-ons —
`forbidden_primary_keys`, plus `handler_tier` on two); the residual 33 → 40 is the
**prompt** lever, closed by the REPORT's headline (nudged) basis. Once **both**
confounds are removed — same rubric AND nudged prompt — arm (a) **ties-or-exceeds
arm (c) on all three verticals** (energy 40 ≥ 39, aquaculture 40 = 40, supply_chain
40 = 40). → The apparent arm-c advantage was a rubric + prompt confound, **not a
real accuracy edge**; the moat-relocation reading (§3.4) stands. *(Offline re-grade
`benchmarks/procedure_comparison/regrade_arm_a.py` (committed — reproduces this full
table; all-120 sanity assert: every recomputed full-key grade matches the stored
`proposal_correct`); dumps `2026-06-09-hardened-dump.jsonl` + `r1b.jsonl`
(PLAN-0020 R1 nudged) are gitignored scratch.)*

**PLAN-0029 measurement calibration (the one aquaculture arm-c recovery).** As-run,
aquaculture arm (c) scored **39/40** — one miss, `aqua-h06`: the model named the
right pond `pond-A116` but with a **U+202F NARROW NO-BREAK SPACE** separator the
hyphen-only `normalize_primary_key` did not fold, so a correctly-named entity graded
a miss. PLAN-0029 extended the B-6 grader calibration to fold the
whitespace-separator family ({U+0020, U+00A0, U+2007, U+202F, U+2060} → ASCII `-`,
recover-only / never-invent) and **offline re-graded** the stored dumps (no
host-state re-run): exactly `aqua-h06` flipped → aquaculture arm (c) **39/40 →
40/40**; supply_chain unchanged; arm (b) whitespace-invariant (carried forward). The
**canonical** numbers in the tables above are post-calibration; the as-run 39/40 and
the re-grade before→after are retained in the artifacts. Same standard as the energy
U+2011 hyphen calibration — recovers only a correctly-named entity, so the
arm(a)≈arm(c) parity stays conservative.

**Threats to validity (recorded honestly):**

- **supply_chain is a 3-way ceiling tie** (a = b = c = 100%) → on this vertical the
  comparison is **non-discriminating**: a clean numeric-threshold breach is easy for
  all three paradigms. Only **aquaculture discriminates** (arm b collapses to 0%), so
  the cross-vertical discrimination evidence rests on ~**1.5 discriminating
  verticals** (energy + aquaculture), not 2.
- **Rule-of-Three not yet satisfied.** A third vertical chosen for **high semantic
  distance** (free-text / relational, where raw SQL is stressed) is needed before any
  abstraction is extracted from this pattern.
- **The governed entity-resolution gap is a forward-pointer, not measured here.** The
  product LLM-path (`recommender._compose_llm_record`) currently trusts the
  model-emitted entity primary_key verbatim; the genuine universality investment
  (resolve against the declared object universe) is routed to a future ADR +
  PLAN-0030, OUT OF SCOPE for B-γ (D-6).

**Run provenance.** `gpt-oss:20b` on MS-S1, Cray-approved host-state run 2026-06-17,
warm-first, ONE combined sweep (80 calls). Artifacts:
`.claude/benchmark-results/2026-06-17-bgamma-{aquaculture,supply_chain}.{log,jsonl}`
(40 item records each; gitignored, retained locally) + the offline re-grade
(`benchmarks/procedure_comparison/regrade.py`, PLAN-0029). Every number VERIFIED
against the `--dump-json` records via the Read tool. The offline mock gate stays the
oracle; this live run is evidence.

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
latency p95 22.64 s, every score `--dump-json`-VERIFIED), the **PLAN-0020 tuning runs
2026-06-11** (nudge effect + the `skip` lever), and the **watch-lane CALIBRATION run
2026-06-12** (PLAN-0022 Phase 3 / M-2=b: the per-vertical suggested-handler
distribution incl. the supply_chain `reroute` 3/13 safety signal; β 98.3%, first SD-2
PASS in `full` mode; watch-judgment latency M-4 diagnostic), and the **B-3
three-arm comparison (B-γ) 2026-06-16** (PLAN-0027: arm (b) raw text-to-SQL
100% entity-ID but structurally no action — D-3; arm (c) lean RAG 97.5% entity
+ action, level with arm (a) — the finding that relocates the moat from raw
accuracy to the governance layer). Per the ring-fence this REPORTS — it does not
gate; every finding above feeds its follow-up (the watch ground-truth pinning,
the hyphen normalization candidate, the tuning PLAN, the verify+reshape
forward-pointer) and moves no bar.*
