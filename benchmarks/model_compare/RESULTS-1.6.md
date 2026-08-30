# Phase 1.6 — think-on vs think-off matrix (2026-08-28, session 259)

> Run under Cray's typed go. Ceiling: **300 s per judgment** — Cray's rule that one
> task should not exceed five minutes, and that anything past it is treated as
> something being wrong and its log kept.
>
> **This run supersedes the phase-1.5 verdict.** See §3.

## 1. The matrix

Energy, 10 items, one repeat per cell, `--judgment-deadline 300 --retry-budget 1
--request-timeout 300`, sequential, one driver holding a lock.

| cell | β headline | α probe | 5-min breaches | p50 | p95 | errors | handlers emitted |
|---|---|---|---|---|---|---|---|
| gptoss / full | 10% | 100% canon | 0 | 29.6 s | 45.6 s | 0 | `restart` ×10 |
| gptoss / think_off ⚠️ | 10% | 100% canon | 0 | 40.7 s | 144.8 s | 0 | `restart` ×10 |
| gptoss / skip | 30% | 100% canon | 0 | **27.2 s** | 48.0 s | 0 | `restart` ×10 |
| qwen / full | 30% | 0% | **3** | 188.9 s | 300.1 s | 3 | escalate ×3, dispatch ×4 |
| qwen / **think_off** | **80%** | 75% canon | **2** | 62.4 s | 300.1 s | 2 | **restart ×6**, dispatch ×2 |
| qwen / **skip** | 60% | 30% canon | **0** | 85.2 s | 116.6 s | 0 | restart ×3, dispatch ×6, escalate ×1 |

⚠️ **`gptoss / think_off` is NOT a sixth configuration.** Measured session 261:
`gpt-oss:20b` discards a boolean `think`, so that row and `gptoss / full` are the
same request run twice. Read the pair as a repeat — a free measurement of this
model's run-to-run noise — and never as a think-on/think-off contrast. Full
reasoning in §4.

The `qwen` rows are **not known to be affected, and not known to be clean either.**
Their handler distributions differ sharply between the two modes (escalate ×3 /
dispatch ×4 under `full`; restart ×6 / dispatch ×2 under `think_off`), which is
consistent with the flag being honoured — but that is an inference from behaviour,
not the direct check run against gpt-oss. **Marked `asserted-not-verified`.** The
same one-item probe would settle it, and until it does, no conclusion should rest
on qwen's think-off cell being a genuine second configuration.

## 2. The finding that closes the JSON question

**Every qwen "error" was a deadline cut. The counts match exactly — 3/3, 2/2,
0/0.** Under a 300 s per-judgment budget qwen produced **zero transport failures
and zero schema failures**, against the 10 errors phase 1.5 recorded under a
120 s per-call timeout.

So the phase-1.5 error count measured the harness, not the model. Combined with
the earlier finding that every handler qwen emitted was a valid enum member,
**qwen's structured-output handling is clean**: the Ollama #15260 family concern
(`think=false` with `format`) is not implicated, and the CHECKPOINT-0 caller
contract held throughout.

The cut tasks are named rather than merely counted — the reason the deadline
records per-item elapsed time:

* `qwen/full` — energy-001 (300.06 s), energy-002 (300.11 s), energy-008 (300.13 s)
* `qwen/think_off` — energy-002 (300.01 s), energy-008 (300.11 s)
* `qwen/skip` — none

**energy-002 and energy-008 were cut in both thinking modes.** That is a pattern,
not variance, and it is the thread to pull in the next investigation.

## 3. The phase-1.5 verdict is superseded

The pre-committed reading, fixed before any model was contacted, was: *if
`qwen+skip` or `qwen+think_off` fits the five-minute ceiling with β no lower than
`qwen+full`, then the timeout is a setting rather than a model limit and the
phase-1.5 verdict must be revisited.*

**`qwen/skip` fits the ceiling completely (0 breaches, p95 116.6 s) and scores
β 60% against `qwen/full`'s 30%.** The condition is met.

Phase 1.5 was decided correctly on the evidence it had. That evidence was
produced by a configuration that crippled the challenger: a per-call timeout
tuned to the incumbent, with the reasoning pass on.

## 4. The deeper result — the reasoning pass hurts BOTH models

| model | full | best without a full thinking pass |
|---|---|---|
| gpt-oss:20b | β 10% | β **30%** (skip) |
| qwen3.8:27b | β 30% | β **80%** (think_off) |

Turning the reasoning pass off improved the headline for **both** models, so this
is a property of **our pipeline**, not of either model. It also matches the
prose/handler divergence measured in phase 1.5, where gpt-oss picked the
canonical handler 100% of the time while writing "Shutdown asset-EXX" in the
title — the reasoning draft talks the model out of the action its own structured
field names.

The mechanism is visible in qwen's handler distribution across modes: with
thinking **on** it never once picked the canonical `restart` (escalate ×3,
dispatch ×4); with thinking **off** it picked `restart` 6 of 8. The reasoning pass
was steering it away from the correct answer, not toward it.

**The `gptoss/think_off` "latency anomaly" recorded here has been SUPERSEDED — see
the note below before reading its p95 against `full`'s.** This paragraph originally
reported p95 **144.8 s** against `full`'s 45.6 s and called the difference
unexplained. It has an explanation, and it is not about latency.

> ⚠️ **SUPERSEDED 2026-08-29 (session 261) — the anomaly is not an anomaly.**
>
> `gpt-oss:20b` **discards a boolean `think`** — it takes `"low"`/`"medium"`/`"high"`.
> Measured live: a 1-item run with `reasoning_mode=think_off` came back with a
> **3,105-character reasoning trace**, i.e. the flag was ignored outright and the
> model reasoned exactly as it does under `full`.
>
> So `gptoss/full` and `gptoss/think_off` **were the same request**, and the p95
> gap between them is run-to-run variance between two samples of ONE configuration —
> a free noise measurement, not a latency finding. Nothing was slower for being
> asked to think less, because it was never asked.
>
> Two further consequences for the table above: gpt-oss's 10% → 30% β "improvement"
> is a 2-item move inside its own measured 45% flip rate, and the next matrix has
> **five cells, not six** — `gptoss/think_off` is now registered as inexpressible
> for this model, and the harness raises rather than scoring it (PR #1312).
>
> Classified **superseded by new info**, not "was an error": at the time of writing
> nothing captured the reasoning trace, so the observation was honest about what
> could then be seen. The capture shipped in PR #1311, which is what made this
> checkable at all.

<!-- retired: "Running call 1 with `think=false` is slower than running it with thinking on. Unexplained" -->
<!-- The claim above is dead: the two cells were one configuration. Kept in place,
     struck through by the note, so the reasoning lineage stays readable. -->


## 5. What CANNOT be concluded

* **No winner is declared.** Every cell is n=10, **one repeat**, so no stability
  was measured at all. Phase 1.5 measured the incumbent's flip rate at **45%** on
  20 items — nine of twenty items changing verdict between identical runs. A
  single-run β carries uncertainty of that order, and the gaps here, while
  consistent in direction across all six cells, are not separated from it.
* **`qwen/think_off` still fails Cray's five-minute rule** — 2 of 10 cut. Only
  `qwen/skip` satisfies it outright.
* Measured on **energy only**, whose ground truth pins `restart` as canonical with
  no acceptable alternatives. The fleet set authored this session — which declares
  acceptable handlers honestly and spans two DOA bands — **has never been run**.
* Every β number here is a **10-item** number. Never quote one as if it came from
  the 66-item energy set.

## 6. What the next run must do

1. **Repeats.** Three per cell at minimum, joined through
   `benchmarks.model_compare.compare`, so the flip rate is reported beside the
   accuracy and a gap smaller than the noise is visible as such.
2. **Narrow the matrix.** `gptoss/skip`, `qwen/think_off`, `qwen/skip` are the only
   three configurations still in contention; the other three are answered.
3. **Add fleet.** It is the set that can separate "picked a defensible action"
   from "matched the pinned string", which energy structurally cannot.
4. **Investigate energy-002 / energy-008.** Two items cut in both thinking modes
   is a reproducible signal about specific inputs, not about the model.

## 7. Evidence

`benchmarks/model_compare/evidence/s259-m16-<model>-<mode>.{jsonl,log}` — six
cells, each dump carrying per-item `judgment_latency_s`. Console logs hold the
latency aggregates and the DEADLINE line; the dumps hold the per-item numbers the
aggregates cannot reconstruct.

Operational note for whoever runs the next matrix: the driver must hold
`/tmp/s259_matrix.lock` and run under `systemd-run --user`. A `nohup ... &` fired
from inside a `wsl bash -lc` invocation loses its wrapper while its python child
survives, which looks exactly like a healthy run until the second cell never
starts. Any monitor watching WSL state must run its commands **through**
`wsl bash -lc`: the Monitor tool's own shell is Git Bash on the Windows side,
where `/tmp` is a different filesystem and `pgrep` cannot see WSL processes. Both
mistakes were made in this run; the lock exists so the second cannot recur.
---

## 8. Session 262 — measured against §4, on `fleet`, under a correct bound

§4 concludes that **the reasoning pass hurts BOTH models** and that this is a
pipeline property. That was measured on `energy`, **before `num_predict` existed**,
when generation ran to the client timeout and was CUT. Session 262 re-measured the
same lever on `fleet` with a server-side cap and **zero truncation in every run**,
and the conclusion does not hold there.

All four cells: `fleet_maintenance`, 20 items, `LLM_MAX_OUTPUT_TOKENS=16384`,
`--retry-budget 1 --request-timeout 900`, model `qwen3.8:27b-mtp-q4_K_M`.

| cell | β headline | α probe (canon/accept/forbid/other) | consistency | latency p95 | LLM calls |
|---|---|---|---|---|---|
| `full` (pass 1) | 85.7% | 78.6% (9/2/1/2) | **9/14** | 172.3 s | 34 |
| `full` (pass 2) | 85.7% | 78.6% (9/2/1/2) | **9/14** | 183.7 s | 34 |
| `think_off` | 78.6% | **57.1%** (8/0/**3**/3) | **8/14** | **353.4 s** | 34 |
| **`skip`** | **85.7%** | **85.7%** (10/2/1/1) | **10/14** | **113.3 s** | **17** |

🔴 **`think_off` is worse than `full` on every axis here** — β down, handler probe
down 21 points, forbidden picks tripled (1 → 3), consistency down, and it is the
**slowest** of the three. The phase-1.6 observation that `think_off` runs slower
(retired at §4 as unexplained) reappears under a correct bound.

✅ **`skip` wins on every measured axis at half the calls.** ⚠️ But `skip` runs no
call 1, so there is **no reasoning trace** — and the product surfaces one
(`llm_inference`, ADR-010 D3). That is a product trade-off, not a number, and it
is not settled here.

### Generation demand — the first real per-cell figures

| cell | reasoning min / median / max | structuring min / median / max |
|---|---|---|
| `full` | **1,294 / 1,876 / 2,457** | 360 / 531 / 733 |
| `think_off` | **582 / 1,765 / 4,727** | 364 / 519 / 725 |
| `skip` | *(no call 1)* | 425 / 592 / 745 |

The shipped `llm_max_output_tokens` default of **1024 is below the MINIMUM `full`
reasoning demand**, so every item's call 1 was cut, not some. A strict cap (100%
`done_reason == "stop"`, ×1.5 over max) gives ≈ **3,700 → 4096** for `qwen/full`.

### Reproducibility — and what it does to §5

The two `full` passes are **byte-identical**: drafts character for character,
rationales, handlers and every `eval_count` the same, while judgment latency
differed on 17 of 20 (plus differing file hashes, start times and sentinels). At
`temperature=0.0` with nothing truncated, this model is deterministic on this
dataset. §5's *"every cell is a single repeat, against a 45% flip rate"* caveat is
therefore **contradicted, not corrected** — the 45% has not been re-measured under
the current bound, and a run terminated on wall-clock is not reproducible by
construction. Tracked as an Active TODO in `docs/STATUS.md`.

### What is still NOT concluded

- `think_off` and `skip` are **n=1**, and their reproducibility is **unverified** —
  only `full` was repeated.
- `gptoss/full` and `gptoss/skip` have **not been run** (`gptoss/think_off` is
  inexpressible and the harness raises). The matrix is 3 of 5 cells.
- Nothing here measures **Thai prose quality**, which is what the phase-2 tasks
  actually are.

**Evidence:** `.claude/benchmark-results/s262-2a-pass1`, `-pass2`,
`s262-2b-qwen-think-off`, `s262-2b-qwen-skip` (`.log` + `.jsonl`) — **gitignored**,
present only on the dev machine, which is why the numbers are transcribed above
rather than referenced. Consistency is computed by
`benchmarks/procedure_baseline/tier_consistency.py`; the strict reading it applies
is Cray's typed ruling of 2026-08-30 (see `docs/lessons/0050-*`).
