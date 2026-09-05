# s280 — `num_predict`, reasoning tokens, and the empty-body failure: SETTLED

**Live calls used: 27 of the 30 authorised** (1 warm + 26 generation). Plus 4 read-only
metadata requests (`/api/version`, `/api/tags`, `/api/ps`, `/api/show`) which generate
nothing. No host configuration changed, no model pulled, nothing deleted.

**Authorisation note.** I acted on the dispatching agent's statement that the project
owner authorised this round under CLAUDE.md §8. I did not independently see that go.

Host: `http://192.168.1.133:11434`, **Ollama 0.32.15**. Model: `gpt-oss:20b`
(MXFP4, 20.9B), loaded with **`context_length` 32768** (`/api/ps`).
Prompt: the **real** production Stop-classifier prompt — built by importing
`.claude/hooks/_sonnet_classifier.py` and calling `_build_system_prompt(_load_registry())`
+ `_build_user_message(payload)` over **real session transcripts** from
`~/.claude/projects/...`. 32,708-char system prompt, ~2.0–2.4 KB user message,
`format = OLLAMA_DECISION_FORMAT`, `temperature 0`, `keep_alive 10m`. Production shape.

Pre-registration (pass/fail read fixed before the first generation call):
`scratchpad/s280-PREREG.md`. Raw data: `/tmp/s280_results.jsonl` (WSL).

---

## 1. The headline: the dispatcher's hypothesis is HALF right, and the half that is wrong changes the sizing rule

> **`num_predict` bounds the reasoning pass. But it does NOT bound reasoning *plus*
> content — it is applied PER CHANNEL. Reasoning gets up to `num_predict`; the JSON
> answer then gets a fresh `num_predict` of its own. The empty bodies happen because
> the reasoning pass alone exceeds the cap and generation stops at `length` before the
> answer channel is ever entered.**

So the answer to the question as asked — *"does the budget get consumed by reasoning,
crowding out the tokens needed to emit the JSON?"* — is: **the reasoning does not crowd
out the answer; it pre-empts it.** The answer is not squeezed short, it is never begun.
The practical consequence for the empty bodies is identical, but the **sizing rule is
different**:

| | rule |
|---|---|
| dispatcher's hypothesis implied | `num_predict > reasoning + content` |
| **measured** | **`num_predict > max(reasoning, content)`** |

On both of our workloads reasoning ≫ content (1,008 vs 27 median for the classifier;
~800 vs ~250 for intake), so **the reasoning demand is what sets the cap**.

### Probe A — pre-committed discriminator #1: does `len(thinking)` scale with `num_predict`?

Sweep on one fixed real Stop payload. **All values measured, none derived:**

| `num_predict` | `done_reason` | `eval_count` | `prompt_eval_count` | thinking chars | content chars | JSON? | wall s |
|---|---|---|---|---|---|---|---|
| 64 | length | 64 | 9568 | 245 | **0** | – | 10.31 |
| 128 | length | 128 | 9568 | 544 | **0** | – | 8.64 |
| 256 | length | 256 | 9568 | 1095 | **0** | – | 20.79 |
| 512 | length | 512 | 9568 | 2165 | **0** | – | 33.83 |
| 1024 | length | 1024 | 9568 | 4439 | **0** | – | 22.35 |
| 2048 | **stop** | 21 | **10639** | 4611 | 82 | ✅ | 23.61 |
| *omitted* | **stop** | 21 | **10639** | 4611 | 82 | ✅ | 28.03 |

`thinking_chars / num_predict` = **3.83, 4.25, 4.28, 4.23, 4.34** — monotonic, and a flat
tokenizer ratio across a **16× range** of N. The pre-committed H1 criterion (monotonic,
ratio in 2.5–5.0, ≥3 points over ≥4×) is **met on all five points**; the H2 criterion
(constant thinking) is **refuted** (245 → 4439 is 18×).

Pre-committed discriminator #2 also fired: content demand on this case is **21 tokens**,
so H2 required `num_predict=64` to deliver. **It truncated.** The flip point sits between
1024 and 2048 — two orders of magnitude above the content demand.

Note the 1024 row against the 2048 row: at the cap the model had emitted **4,439 of the
eventual 4,611** thinking chars. It is the *same* reasoning stream, cut at 96% of the way
through. `num_predict` is unambiguously bounding the reasoning.

### Probe B — pre-committed discriminator #3: shared budget or per-channel?

The reanalysis in §3 threw up a contradiction with a *shared* budget, so I probed it
directly on a purpose-built case with **large content** (an essay under a `format`
schema), where the two models make opposite predictions. Pre-committed read (fixed
before running): choose N with `max(R,C) < N < R+C`; **stop ⇒ per-segment**,
**length ⇒ shared**; a control at `N2 < max(R,C)` must truncate or the probe is void.

| label | `num_predict` | `done_reason` | `eval_count` | `prompt_eval_count` | think ch | content ch | JSON? |
|---|---|---|---|---|---|---|---|
| calibrate | 8 | length | 8 | **141** (true prompt) | 21 | 0 | – |
| calibrate | 4096 | stop | 1906 | 400 | 1172 | 10313 | ✅ |
| **DISCRIM** | **2035** | **stop** | **1810** | 400 | 1172 | 9391 | ✅ |
| CONTROL | 1500 | length | 1500 | 400 | 1172 | 8305 | ❌ (cut mid-essay) |

`R` = 400 − 141 = **259** reasoning tokens. `C` = **1810** content tokens.
**R + C = 2069 > num_predict = 2035, and the call returned `stop` with complete valid
JSON.** A shared budget cannot produce that. **Shared budget refuted.**

The control is equally informative: content alone hit 1500 and stopped at `length` with
`eval_count == 1500` — the content channel got its own full 1500 **after** 259 reasoning
tokens had already been spent.

### The complete accounting rule (this corrects `RESULTS.md` §Correction and the `CallMetrics` docstring)

| field | what it actually is |
|---|---|
| `prompt_eval_count` | true prompt tokens **+ reasoning tokens, iff the reasoning channel closed successfully** |
| `eval_count` | tokens of the **last channel generated** — reasoning if truncated in reasoning, content otherwise |
| `eval_duration` | likewise, the **last channel only** |
| `num_predict` | applied **per channel** |
| `done_reason="length"` + `content_chars == 0` | truncated **inside reasoning** — this is the empty-body failure |
| `done_reason="length"` + `content_chars > 0` | truncated **inside content** |
| `done: false`, no counters at all | generation **aborted** (see §4) |

**Third independent confirmation.** `total_duration − eval_duration − prompt_eval_duration
− load_duration` — the residual `RESULTS.md` flagged as unexplained — divided by the
`prompt_eval_count`-delta reasoning tokens gives a consistent decode rate across all nine
classifier calls: **45.2, 48.2, 43.7, 44.2, 29.0, 42.4, 46.0, 47.1, 45.6 tok/s**. The
residual *is* the reasoning decode time, and it reconciles exactly.

**This closes `RESULTS.md`'s explicitly-unresolved question.** Its feared reading — "~1,100
tokens under a 1024 cap, which a single shared budget could not produce" — was **correct
about the token count and correct to doubt the single budget**: there is no single budget.
Ollama issue #17978 and `thinking/parser.go` are reconcilable: the parser is a splitter,
but generation for a thinking model runs as more than one budgeted segment.

---

## 2. Reasoning-demand distribution — the Stop-classifier workload, `gpt-oss:20b`

8 distinct real Stop payloads at `num_predict=4096`, **all 9/9 returned `stop` with valid
JSON**. Reasoning tokens measured by `prompt_eval_count` delta (a direct token count), with
`thinking_chars / 4.184` as an independent cross-check:

| case | `prompt_eval_count` | **R (pe delta)** | R (chars ÷ 4.184) | content tok | wall s |
|---|---|---|---|---|---|
| 0 | 10231 | **658** | 620 | 17 | 14.8 |
| 1 | 10669 | **1008** | 953 | 28 | 21.5 |
| 2 | 10738 | **1188** | 1146 | 27 | 27.7 |
| 3 | 10757 | **1143** | 1187 | 34 | 26.9 |
| 4 | 11710 | **2142** | 2061 | 19 | **74.2** |
| 5 | 10237 | **666** | 619 | 26 | 16.3 |
| 6 | 10487 | **877** | 867 | 20 | 19.8 |
| 7 | 10467 | **800** | 665 | 29 | 17.5 |
| 4 *(repeat)* | 10639 | **1071** | 1102 | 21 | 23.6 |

Sorted: **658, 666, 800, 877, 1008, 1071, 1143, 1188, 2142.** Median **1008**, max **2142**.

| cap | classifier calls exceeding it |
|---|---|
| **1024** | **4 / 9 = 44%** |
| 2048 | 1 / 9 = 11% |
| 3072 | 0 / 9 |
| 4096 | 0 / 9 |

**That 44% is an independent replication of the s273b empty-body rate** (`gpt-oss` 53%,
n=19) on a completely different workload and prompt. Same cause, same magnitude.

### 🔴 The finding that matters more than the distribution: demand is NOT stable per input

Case 4 and the sweep's fixed case are **the same transcript, the same prompt, temperature
0** — and they needed **2142** and **1071** reasoning tokens. A **2× spread on identical
input.** So there is no such thing as "this Stop event's demand"; the distribution is over
*(input × run)*, and retrying an input does not sample a different input — it re-rolls the
same die. This explains why the intake retry loop never rescued `bs-03` / `rm-03`
(1024/1024/1024 three times) while rescuing others.

### Per model (offline reanalysis of the s273b intake artifacts — no live calls)

Applying the same accounting to `.claude/benchmark-results/intake-s273b-*`. Reasoning
tokens via `prompt_eval_count` delta (the retry prompt is exactly +80 tokens, readable off
the triples, e.g. `bs-03` 654 / 734 / 734):

| arm | R on delivering attempts (n) | truncated (R > 1024) |
|---|---|---|
| `gpt-oss:20b` | 448, 513, 706, 754, 807, 824, 864, 988, 1004 (n=9) | 10 / 19 = **53%** |
| `qwen3.8:27b-q4_K_M` | 681, 710, 842, 893, 904, 923 (n=6) | 17 / 23 = **74%** |
| `qwen3.8:27b-q8_0` | 762, 797, 850, 889, 920, 980 (n=6) | 18 / 24 = **75%** |

**Every delivering attempt has R ≤ 1024. Every truncated attempt has R > 1024. Zero
exceptions in 66 attempts, across two model families and three quantizations.** That is
the cleanest confirmation in this report, and it is free — it was already on disk.

It also **resolves the apparent contradiction** that sent me to Probe B: `bs-01` att1
(R=988, C=326, sum **1314**) and `rm-02` (R=1004, C=183, sum 1187) *delivered* under a
1024 cap. Under a shared budget that is impossible; under the per-channel rule it is
routine, because both channels are individually under 1024.

**`RESULTS.md`'s "it is the call path, not the model" conclusion survives and is now
mechanistic:** the Qwen arms are worse because their reasoning demand sits closer to 1024,
not because they emit differently.

---

## 3. Can reasoning be bounded or disabled separately? **No — and the effort lever is actively broken here.**

`/api/show` reports `capabilities: [completion, tools, thinking]`, so the model advertises
it. Measured, `gpt-oss:20b` + `format`, Ollama 0.32.15:

| `think` | `num_predict` | result |
|---|---|---|
| `"low"` | omitted | 🔴 `done: false`, **no counters at all**, empty content, thinking 1662 ch |
| `"low"` | omitted | 🔴 `done: false`, empty content, thinking 2126 ch — **degenerated into a repetition loop** (`"... ... ... ..."`) |
| `"medium"` | omitted | 🔴 `done: false`, empty content, thinking 2243 ch |
| `"medium"` | **4096** | 🔴 `done: false`, empty content, thinking 2243 ch |
| `"high"` | omitted | ✅ `stop`, `eval_count` 29, valid JSON, 15.7 s |
| `"high"` | omitted | 🔴 `done: false`, empty content, thinking 9473 ch, 83.6 s |
| `"high"` | **4096** | 🔴 `done: false`, empty content, thinking 2716 ch |
| **omitted (production)** | 64…4096 | ✅ **11 / 11 well-formed envelopes** |

**6 of 7 explicit-`think` calls returned a broken envelope**, and **a `num_predict` cap
does not fix it** — the same failure occurs at 4096. So this is the `think` option itself,
not a truncation. The response has no `done_reason`, no `eval_count`, no durations, and
`done: false`; `_call_ollama` would raise `ValueError("Ollama envelope missing
message.content")` and the classifier would fail closed to `pause`.

I did **not** find a mechanism for this in the Ollama source — I am reporting behaviour.
It is consistent with the prior register: `RESULTS-1.6.md` already found `gptoss/think_off`
**inexpressible** (a boolean `think` is discarded), and `RESULTS.md` cited issue #18044
(`think: false` disables the *parser*, not the *generation*) and #17566 (a real thinking
budget is **unmerged**). Nothing in Ollama 0.32.15 gives a separate reasoning budget.

**Recommendation: do not pass `think` at all.** Omitting it — exactly what production does
today — is the only configuration measured to be reliable (11/11).

One further note for the record: `RESULTS-1.6.md` found that on **qwen**, `think_off` cost
rationale quality materially (β 4/14 vs 11/14 on the handler-probe axis). Even if the lever
worked, the evidence says it is not free.

---

## 4. Recommendation — and yes, the two consumers should differ

### Latency arithmetic (measured decode rates 29.0 – 48.2 tok/s)

| cap | at 29 tok/s | at 43.5 tok/s | at 48 tok/s |
|---|---|---|---|
| 1024 | 36 s | 24 s | 21 s |
| 2048 | **71 s** | 47 s | 42 s |
| 3072 | 107 s | 71 s | 64 s |
| 4096 | **142 s** | 94 s | 85 s |

### (a) Benchmark runs — **`num_predict = 4096`, and raise `llm_request_timeout_s` to ≥ 180 s**

* 9/9 delivered at 4096 with valid JSON; max observed demand 2142 = **52% of the cap**.
* 21/21 intake delivering attempts had R ≤ 1004 — 4096 is ~4× that.
* 🔴 **The cap alone is not enough.** `llm_request_timeout_s` defaults to **120.0**
  (`services/api/config.py:163`). A 4096-token reasoning pass at the measured 29 tok/s
  takes **142 s** — the client would abort and **discard every token**, which is the exact
  failure the `num_predict` knob was added to prevent. Raising the cap without raising the
  timeout swaps a truncation for a total loss. **Both must move together.**
* Latency is free here — batched, `systemd --user`, no interactive deadline. The asymmetry
  is decisive: a cap set too high costs seconds on pathological calls; a cap set too low
  costs a **data point**, and it does so *non-randomly* (it silences exactly the hard
  cases), which is a bias, not just a loss. `RESULTS.md` already carries that scar —
  `rm-03`/`bs-03` are scored `wrong` for a truncation.

### (b) Production Stop hook — **`num_predict = 2048`, keep the 75 s timeout**

`.claude/hooks/_sonnet_classifier.py:723` sends `options: {"temperature": 0}` and **no
`num_predict`**, with `OLLAMA_TIMEOUT_SEC = 75`.

* **The binding constraint here is the timeout, not the cap.** At 29–48 tok/s, 75 s buys
  only **2,175–3,600 tokens**. Any cap above ~2,600 is unreachable *by construction* — the
  timeout fires first. So 4096 would be theatre on this path.
* 2048 at the worst measured rate = **71 s**, just inside the 75 s budget. It is the
  largest cap that can actually complete.
* It covers **8 of 9** measured demands. The 9th (2142) truncates → empty body →
  `ValueError` → **fail-closed `pause`**. For a Stop gate that is the safe direction, and
  it is the same outcome the timeout would have produced — but ~30 s sooner and with a
  `done_reason` you can log.
* 🔴 **Uncapped is genuinely risky and it is not hypothetical.** With `context_length`
  32768 and a ~9.6 k prompt, an uncapped runaway can generate ~23,000 tokens ≈ **8–13
  minutes**. I measured a real production-shape Stop payload at **74.23 s / 2142 tokens**
  — a whisker inside the 75 s timeout — and a runaway at **83.6 s with no answer**. The
  tail is already touching the ceiling.
* **Honest framing: for this consumer the cap is a bounded-latency and diagnosability
  improvement, not a correctness fix.** It does not lower the empty-body rate below ~11%.

### The real fix for the Stop hook, which is not a cap at all

The system prompt is **32,708 chars / 9,568 tokens**. That prompt is what drives a
600–2,100-token reasoning pass on a decision whose answer is **17–34 tokens**. The
leverage is in shrinking the registry that goes into that prompt, or moving to a smaller /
faster model — not in tuning `num_predict`. A cap cannot make the model think less; it can
only decide whether you get an answer or a `length`.

### Two documentation defects to fix at the source

1. `services/engine/llm/client.py` — the `CallMetrics` docstring says *"`eval_count` is
   generated tokens — the model's actual DEMAND, which is what a cap should be chosen
   from."* **It is the last channel's tokens.** Sizing a cap from it under-counts by the
   entire reasoning pass — the exact error that produced a 1024 default.
2. `services/api/config.py:168` — `llm_max_output_tokens` is described as a
   *"Server-side generation cap"*. It is a **per-channel** cap, and the channel that binds
   is the reasoning one, not the output. The name actively misleads.

Also still open from `RESULTS.md`, and unchanged by this work: `scaffold.py:676` asks for
an entire synthetic dataset under the same 1024 global cap and falls back silently; and
the hook's `keep_alive: "10m"` vs the app's `"30m"` still have no shared source.

---

## 5. What I did NOT test, and how these probes could mislead

1. **n = 9 cannot support a 99% claim, and I will not fabricate one.** With 9/9 under 4096,
   the exact binomial 95% upper bound on the exceedance rate at 4096 is **28%** — that is
   all n=9 licenses. Every "99%" framing in this report is deliberately absent. What is
   solid is the *negative*: 1024 is too low, measured at 44% / 53% / 74% / 75% on four
   workload-model pairs.
2. **The intake reanalysis is right-censored at 1024.** 45 of 66 attempts have demand
   "> 1024" and no upper value. The upper tail **cannot** be estimated from that file at
   all — my per-arm delivering figures are a *truncated* sample and are biased **low** by
   construction. Only my own 4096 run is uncensored.
3. **Run-to-run variance is at least 2× on identical input** (§2). Any per-input demand
   model is worthless, and a cap chosen from a median will fail often.
4. **The per-channel law was probed live on `gpt-oss:20b` only**, with one discriminator
   pair. The Qwen evidence is offline consistency (66/66, zero exceptions) — strong, but it
   is a *consistency check*, not a live confirmation that Qwen's thinking path is also
   per-channel. If Qwen were shared-budget, its cap would need to be larger than I imply.
5. **Prompt-token counts for cases 0–3, 5–7 are estimated** from a single measured anchor
   (3.6323 chars/token, from the one case with a truncated baseline). Errors there
   propagate into R. Mitigation: the independent `thinking_chars ÷ 4.184` estimator agrees
   within 4% on 7 of 9 cases and 17% on the worst (case 7). The *conclusions* do not depend
   on those cases — the sweep, Probe B, and the intake pe-deltas all stand on directly
   measured baselines.
6. **`stream: false` only.** Counter semantics under `stream: true` are untested and could
   differ; the classifier and the app both use `stream: false`, so this matches production.
7. **Box contention is a live confound.** Case 4 decoded at 29.0 tok/s while its 8 siblings
   ran 42–48. I could not tell thermal throttling from another tenant. My latency
   recommendations use the slow figure, so they are conservative — but if 29 tok/s is
   itself optimistic, the 2048/75 s margin evaporates.
8. **All calls ran warm** (`keep_alive` 10m, `expires_at` confirmed via `/api/ps`). A cold
   load adds ~22–36 s per prior measurement, which would push a 2048-token call **over**
   the 75 s Stop-hook timeout. The Stop hook's real p99 is worse than my numbers.
9. **I did not test whether a bigger cap improves decision QUALITY.** 8 of 9 dist calls
   answered `pause` with thin reasons ("No action taken."). More reasoning tokens buys a
   *delivered* answer, not a *better* one. `RESULTS-1.6.md` is the relevant prior here.
10. **The `done: false` mechanism is unexplained.** I report the behaviour (6/7) and
    verified it is not truncation (it persists at `num_predict=4096`) and not context
    exhaustion (32768 context vs ~11.8 k used). I did not read the Ollama source, so
    "`think` as a string is broken on this stack" is an empirical claim about this
    server + model + `format` combination, not a diagnosis.
11. **One payload shape.** Every classifier call used a synthetic `Stop` event
    (`stop_hook_active: false`) over a real transcript. `PreToolUse` payloads — which are
    the ones that actually gate governance writes — were not probed and may reason
    differently.

### Where the probes could actively mislead

* **The strongest result rests on `prompt_eval_count` being reasoning re-attribution.** If
  Ollama instead re-*prefills* the reasoning text as prompt for a second pass, the number
  is the same but the mechanism is "two generation calls, each with its own
  `num_predict`". Every recommendation in §4 is unchanged — but a reader should not treat
  "one stream, counters re-attributed" as established. The residual-duration reconciliation
  (§1) actually favours the two-pass reading.
* **`4.184` chars/token was calibrated on this model, this prompt, this language.** It is
  used only as a cross-check, never load-bearing — but do not port it to another workload.
* **A green `stop` is not a green answer.** `content_parses_json` is checked and was
  `True` on all 9 dist calls, but nothing here scores whether the *decision* was right.

---

*Data: `/tmp/s280_results.jsonl` (27 live calls), `/tmp/s280_raw_*.json` (raw envelopes),
scripts `s280_probe.py` / `s280_seg.py` / `s280_intake2.py` / `s280_final.py` in this
scratchpad. Pre-registration written before the first generation call:
`s280-PREREG.md`. Offline reanalysis source:
`.claude/benchmark-results/intake-s273b-{gptoss,qwen-q4,qwen-q8}/` (gitignored, still
present). Nothing was written into the repository working tree.*
