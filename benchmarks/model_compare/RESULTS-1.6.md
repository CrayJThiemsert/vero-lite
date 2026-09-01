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
- ~~`gptoss/full` and `gptoss/skip` have **not been run** (`gptoss/think_off` is
  inexpressible and the harness raises). The matrix is 3 of 5 cells.~~
  **Superseded by §9** (session 263, 2026-08-30): both cells were run and the
  matrix is now 5 of 5. `gptoss/think_off` remains inexpressible. Kept rather
  than deleted — it is the record of what was open when §8 was written.
- Nothing here measures **Thai prose quality**, which is what the phase-2 tasks
  actually are.

**Evidence:** `.claude/benchmark-results/s262-2a-pass1`, `-pass2`,
`s262-2b-qwen-think-off`, `s262-2b-qwen-skip` (`.log` + `.jsonl`) — **gitignored**,
present only on the dev machine, which is why the numbers are transcribed above
rather than referenced. Consistency is computed by
`benchmarks/procedure_baseline/tier_consistency.py`; the strict reading it applies
is Cray's typed ruling of 2026-08-30 (see `docs/lessons/0050-*`).

## 9. Session 263 — stage 2c: the matrix completed, and the model ranking inverts

Run 2026-08-30 under Cray's typed §8 host-state go. Two cells, `fleet_maintenance`,
20 items, `LLM_MAX_OUTPUT_TOKENS=16384`, `--retry-budget 1 --request-timeout 900
--allow-truncation`, model **`gpt-oss:20b`** (the ADR-0001 pin). Both cells cleared
the pass/fail read — **fixed before any result existed**: sentinel `rc=0`,
`TRUNCATION: 0`, deterministic 20/20, scored denominator 14 (so the cells compare
against 2b), and `DUMP: wrote 20 item records`. The on-disk record of that read
(`.claude/state/goal.json`, `created` 16:22:16) was written 99 s into the first
cell, which had started at 16:20:37 and emitted no aggregate line until 16:29:30;
the second cell started at 16:30:06. Stated this way rather than as "before the
run" because that is the part a reader can check from disk, and it is the part
that matters — no criterion could have been tuned to a result none of them had
yet seen.

### The complete 5-cell matrix

`latency p95` is the **per-BREACH-judgment** figure (the SD-2 acceptance bar), not
per-call — the same column §8 uses.

| cell | model | β headline | α probe (canon/accept/forbid/other) | consistency | latency p95 | LLM calls | wall |
|---|---|---|---|---|---|---|---|
| `full` (pass 1) | qwen | 85.7% | 78.6% (9/2/1/2) | 9/14 | 172.3 s | 34 | 43 m |
| `full` (pass 2) | qwen | 85.7% | 78.6% (9/2/1/2) | 9/14 | 183.7 s | 34 | 43 m |
| `think_off` | qwen | 78.6% | 57.1% (8/0/**3**/3) | 8/14 | 353.4 s | 34 | 49 m |
| `skip` | qwen | 85.7% | 85.7% (10/2/1/1) | 10/14 | 113.3 s | 17 | 27 m |
| 🔴 **`full`** | **gpt-oss** | **100%** | **100% (14/0/0/0)** | **14/14** | **38.1 s** | 34 | **8 m 53 s** |
| 🔴 **`skip`** | **gpt-oss** | **100%** | **100% (14/0/0/0)** | **14/14** | **33.1 s** | 17 | **7 m 08 s** |

🔴 **`gpt-oss:20b` is perfect on all three quality axes, in both reasoning modes** —
every breach item scored, every handler pick canonical, zero forbidden picks, and
consistency 14/14 under Cray's strict reading (mid band 10/10 `escalate`, owner band
4/4 `escalate`; no divergence to explain). It is also faster end to end, compared
**same mode against same mode**: `full` **4.8×** (42 m 59 s → 8 m 53 s), `skip`
**3.8×** (26 m 53 s → 7 m 08 s). Both figures are `.wrap` START→EXIT deltas. A
wider-sounding band is available only by comparing cells of *different* reasoning
modes, which is not a like-for-like speedup and is not claimed here.

⚠️ **This inverts §1's model ranking, but it is NOT a single-variable result.**
§1 measured gpt-oss at β 10–30% and qwen at 30–80% — on `energy`, before
`num_predict` existed, with generation cut at a client timeout. §9 changes **two**
variables at once (dataset `energy` → `fleet`, and cut → correctly bounded
generation), so it establishes *that the ranking is opposite here*, and **not**
which of the two changes caused it. Isolating that needs `gptoss` re-run on
`energy` under the current bound — not run, not scheduled.

### `skip` vs `full` for gpt-oss — a clean single-variable comparison

Same model, dataset and bound; only `--reasoning-mode` differs. β, α and
consistency are **identical** (100% / 100% / 14/14), so for this model the
reasoning pass buys **no measurable quality** while costing **double the calls**
and ~25% more wall clock. This strengthens §8's "`skip` wins" for a *different*
reason: there `skip` won on quality, here it **ties** on quality and wins on cost.
The §8 trade-off is unchanged and still unsettled — `skip` emits no reasoning
trace, and the product surfaces one (`llm_inference`, ADR-010 D3).

The watch lane (unscored calibration) is the one place the two modes differ:
`full` returned `{echo: 3}`, `skip` returned `{escalate: 1, echo: 2}`.

### Generation demand — a profile shaped nothing like qwen's

| cell | model | reasoning min / median / max | structuring min / median / max |
|---|---|---|---|
| `full` | qwen | 1,294 / 1,876 / 2,457 | 360 / 531 / 733 |
| `think_off` | qwen | 582 / 1,765 / 4,727 | 364 / 519 / 725 |
| `skip` | qwen | *(no call 1)* | 425 / 592 / 745 |
| **`full`** | **gpt-oss** | **215 / 540 / 7,247** | **83 / 114 / 148** |
| **`skip`** | **gpt-oss** | *(no call 1)* | **93 / 142 / 167** |

Two contrasts worth keeping:

- **The 1024 default fails differently per model.** For `qwen/full` 1024 is below
  the *minimum* demand (1,294), so it cut **every** item. For `gptoss/full` the
  median is 540 — comfortably under 1024 — while the max is 7,247, so 1024 would
  have cut **some** items and left others whole. A silent partial cut is the harder
  failure to notice, because the aggregate still looks plausible.
- **gpt-oss structures ~5× more cheaply** (max 148/167 vs qwen's 733/745) while its
  reasoning is far more variable (max 7,247 vs 2,457). A strict cap for
  `gptoss/full` (100% `stop`, ×1.5 over max) is ≈ **10,900 → 12288**, well above
  qwen's ≈ 4096.

### Still NOT concluded

- Both `gptoss` cells are **n=1**; their reproducibility is **unverified**. Only
  `qwen/full` has ever been repeated. The two `gptoss` cells agreeing 14/14 is
  cross-*mode* agreement under different configurations — it is **not** a
  determinism check and must not be read as one.
- `gptoss/think_off` remains **inexpressible** (the model discards a boolean
  `think`; the harness raises). The matrix is 5 of 5 *runnable* cells, not 6.
- ⚠️ **`fleet` no longer discriminates for the pinned model.** With β, α and
  consistency all at ceiling, this dataset can measure a regression in `gpt-oss`
  but can no longer measure an improvement, and cannot rank two good models. A
  harder dataset — or harder items in this one — is the prerequisite for any
  further model comparison on `fleet`.
- Latency still **misses the SD-2 bar**: p95 38.1 s / 33.1 s against ≤ 30 s. Much
  closer than qwen's 113–353 s, but `-> OVER` in both cells.
- Nothing here measures **Thai prose quality**, unchanged from §8.

**Evidence:** `.claude/benchmark-results/s263-2c-gptoss-full`,
`s263-2c-gptoss-skip` (`.log` + `.jsonl`) — **gitignored**, present only on the dev
machine, which is why the numbers are transcribed above rather than referenced.
Wall-clock figures are the `[wrap] START` → `EXIT` deltas in the matching `.wrap`
files. Consistency is computed by
`benchmarks/procedure_baseline/tier_consistency.py`.

## 10. Session 263 — the quantization confound, measured

§9 recorded that its model-ranking inversion changed two variables at once. This
resolves a third one §9 did not raise: `qwen3.8:27b-mtp-q4_K_M` is a **4-bit**
*post-training compression*, while `gpt-oss:20b` is natively MXFP4 — the build is
trained for that precision. An **8-bit** qwen (`qwen3.8:27b-mtp-q8_0`) was present
on MS-S1 and had never been run.

Run 2026-08-30 under Cray's typed §8 go, **one variable changed**: identical to
`s262-2a-pass1` in dataset, item set, bound, reasoning mode, retry budget and
timeout — only the model tag differs. All six pass/fail criteria cleared
(sentinel `rc=0`, `TRUNCATION: 0 of 34`, deterministic 20/20, denominator 14,
`DUMP: wrote 20 item records`, zero no-judgment).

**Interpretation rule, fixed before the run.** The metrics are counts out of 14,
so one item is 7.1 points: a change of **±1 item is within the resolution of the
test and is not a finding**; **≥2 items** is material. Recorded here because the
result was going to be interpreted, not merely logged.

### The three cells

| cell | β headline | α probe (canon/accept/forbid/other) | consistency | latency p95 | wall |
|---|---|---|---|---|---|
| qwen **q4_K_M** | 85.7% | 78.6% (9/2/1/2) | 9/14 | 172.3 s | 42 m 59 s |
| qwen **q8_0** | 85.7% | **85.7%** (**12**/0/1/1) | **12/14** | 203.1 s | 48 m 52 s |
| `gpt-oss:20b` | **100%** | **100%** (14/0/0/0) | **14/14** | **38.1 s** | **8 m 53 s** |

**Verdict: the quantization confound was real for α and consistency, and absent
for β.** α-canonical and consistency each moved **+3 items** — over the
pre-committed threshold. β did not move at all (12/14 either way). The ranking
does **not** flip: gpt-oss still leads on all three. But the gap narrows from five
items to two, and what remains is a different kind of gap.

### What actually changed — the item-level view

q8 corrected **exactly the five items q4 got wrong**, and broke two new ones:

| item | quote | quotes on file | q4 | q8 | movement |
|---|---|---|---|---|---|
| `fleet-003` | ฿12,400 | 1 | `tow_to_partner_garage` | `escalate` | → canonical |
| `fleet-004` | ฿22,800 | 2 | `echo` | `escalate` | → canonical |
| `fleet-009` | ฿9,800 | 1 | `dispatch_replacement_truck` | `escalate` | → canonical |
| `fleet-011` | ฿7,300 | 1 | `dispatch_replacement_truck` | `escalate` | → canonical |
| `fleet-012` | ฿6,900 | 1 | `echo` | `escalate` | → canonical |
| `fleet-002` | ฿5,200 | 1 | `escalate` | `echo` | → off |
| `fleet-006` | **฿30,001** | **1** | `escalate` | `tow_to_partner_garage` | → off |

All five q4 errors were the same defect: the sourcing-hygiene gate cited as the
reason for overriding the escalation, on items **below** the rule's authored
฿30,000 threshold — a threshold the procedure goal explicitly says is "authored in
the typed rule, never in this prose". q4 supplied ฿5,001 (the DOA ceiling) in its
place. At 8-bit that behaviour drops from **five items to one** (`fleet-002`).

### 🔴 `fleet-006` — the trap item, and the only model that saw it

`fleet-006` is ฿30,001 with **one quote in hand**: the single breach item in the
dataset where the amount clears the ฿30,000 sourcing threshold *and* the quote
count fails it. The gate genuinely fires there and nowhere else.

**q8 is the only one of the three models that blocked on it.** q4 and gpt-oss both
escalated straight past.

It is still scored `forbidden`, and correctly so — it picked `tow_to_partner_garage`,
the dataset's planted decoy verb, and the gate is evaluated **deterministically
with no LLM** (the step's own description says so), making gate evaluation not the
model's lane at all. But the error class is categorically different from q4's:
q4 applied a rule that did not apply, five times; q8 applied a rule that did
apply, in a lane that is not its own, once. A grader that reports both as "one
non-canonical pick" is not seeing the distinction.

### What this does and does not settle

- **Settled:** roughly **60% of the qwen-vs-gpt-oss handler gap on this dataset was
  quantization, not the model.** Any future claim about qwen's judgment quality
  must name the quantization or it is unfalsifiable.
- **Settled:** gpt-oss still wins on every axis, and remains **5.3× faster** on the
  SD-2 bar (38.1 s vs 203.1 s p95) and **5.5× faster** end to end. The ADR-0001 pin
  is not challenged by this result.
- **Not settled:** q8 is **n=1** and its reproducibility is unverified, like every
  cell except `qwen/full` q4.
- **Not settled:** whether `fleet-002` and `fleet-006` are two samples of one
  residual behaviour or two different defects. n=1 cannot separate them.
- **Unchanged from §9:** `fleet` is at ceiling for the pinned model, so it still
  cannot rank two good models — and this run is an illustration of the cost, since
  q8's genuine improvement was invisible to β and showed only in α and consistency.

**Evidence:** `.claude/benchmark-results/s263-2d-qwen-q8-full` (`.log` + `.jsonl` +
`.wrap`), against `s262-2a-pass1` and `s263-2c-gptoss-full` — all **gitignored**.
Amounts and quote counts read from each item's `measured_value` and
`context.quotes_obtained` in the dumps. The ฿30,000 threshold is the design
partner's Q10 figure, held in `verticals/fleet_maintenance/sourcing.py` and
deliberately absent from the prompt (`procedures.yaml` rule_gate note, ADR-0025 D4).

## 11. Session 263 — the defect was in the DIRECTIVE, and fixing it closed the gap

🔴 **Everything above §11 was measured against a procedure goal that contained a
contradiction. This section is the other side of that line: numbers from §8–§10 are
NOT comparable with anything measured after it.**

### What the models were actually told

Reading the assembled prompt (`services/engine/llm/prompt.py`) rather than the
benchmark's reader-facing summary showed the system instruction is well-built — it
separates trusted config from untrusted operator data, contains injection with
explicit delimiters, and carries a full **action catalog with a description per
handler** (`handler_catalog_enabled` defaults True; `run_benchmark` calls
`discover_and_register()` and fails closed if a vertical registers nothing). The
models were not choosing blind.

The defect was one clause of the procedure goal. It told the model to **check** the
sourcing gate, told it the gate **blocks the spend on failure**, told it the
threshold is *"authored in the typed rule, never in this prose"* — and the event then
handed it `quotes_obtained`. The next clause said to route the *compliant* spend.

A reader following that reaches: one quote of three, gate fails, spend blocked, no
compliant spend to route. **That is what qwen concluded.** The key says `escalate`
regardless — correctly, because the gate is evaluated **deterministically downstream
with no LLM** (the step's own description says so). The directive never said that.

**Scale of the mismatch: 11 of the 14 breach items carry fewer than three quotes, so
the invitation was live on nearly every graded item; the rule it points at fires on
exactly one (`fleet-006`).**

### The gold set was NOT the defect

Audited before changing anything, because changing the directive and the key together
would have made the re-measure uninterpretable. The key varies **honestly** on the
signals it grades — `drivable=True` (9 items) → `acceptable: []` with `tow` forbidden;
`drivable=False` (5) → `tow_to_partner_garage` acceptable; `load_aboard` (2) →
`dispatch_replacement_truck` also acceptable. It is **flat on `quotes_obtained`**:
canonical is `escalate` for all 14 regardless. The key was right; the directive was
asking for something else.

### The change

`verticals/fleet_maintenance/procedures.yaml`, the goal's third clause only —
*"check the sourcing-hygiene gate … which blocks the spend on failure"* becomes
*"note that a sourcing-hygiene gate on competing quotes is applied DOWNSTREAM by the
engine and not by you — it may block the spend after your recommendation, so route
the spend as if it will pass and never withhold a routing decision on quote counts"*.

The gate stays *visible* to the model deliberately: ADR-010 D3 surfaces the reasoning
trace to operators, so the trace should say a gate is still pending rather than imply
the spend is settled. No ฿ figure and no handler name enters the prose, so ADR-0025
D4's load-time lint is unaffected — confirmed, along with `goal_coverage` still
matching `repair`/`quote`, and the full offline gate at CI scope (ruff clean · mypy
`--strict services/ verticals/` clean on 201 · **pytest 4636 passed, 8 skipped**).
`fleet_maintenance` is the scaffolder golden donor and **no golden test reddened**.

### The re-measure — one variable, the goal

`qwen3.8:27b-mtp-q8_0`, `full`, identical to §10's cell in every other respect.
**gpt-oss could not be the test cell: already at ceiling, it was structurally
incapable of showing an improvement** — the §9 ceiling problem now obstructing
verification of our own fix.

| cell | β | α (canon/accept/forbid/other) | consistency | latency p95 | wall |
|---|---|---|---|---|---|
| q8, old goal | 85.7% | 85.7% (12/0/1/1) | 12/14 | 203.1 s | 48 m 52 s |
| **q8, fixed goal** | **100%** | **100% (14/0/0/0)** | **14/14** | 396.3 s | 49 m 24 s |
| `gpt-oss`, old goal | 100% | 100% (14/0/0/0) | 14/14 | 38.1 s | 8 m 53 s |

Pre-committed read, fixed before the run: both `fleet-002` and `fleet-006` returning
to `escalate` = the fix works; one = partial; neither = the goal was not the cause.
**Both returned.** Every mechanical criterion cleared (sentinel `rc=0`, `TRUNCATION:
0 of 34`, deterministic 20/20, denominator 14, `DUMP: wrote 20 item records`, zero
no-judgment).

### The mechanism, not just the score

| | old goal | fixed goal |
|---|---|---|
| items whose reasoning mentions the gate | 17 of 17 | 14 of 17 |
| breach items where it **overrode** the routing | **2** | **0** |
| items naming the gate as **downstream** | **0** | **15** |

The model did not stop reasoning about the gate — it started reasoning about it
*correctly*. It still raises it, now frames it as a downstream step, and no longer
withholds a routing decision on quote counts. Rationales came out cleaner too:
*"The quote size requires escalation to the appropriate human approval tier rather
than terminal approval at this stage."*

### What this costs, and what it does not settle

- ⚠️ **Latency p95 roughly doubled** (203.1 s → 396.3 s) on a mean that barely moved
  (178.5 → 186.1) — one slow item, not a shift. Recorded rather than explained: n=1
  cannot tell an outlier from a regression.
- **n=1**, like every cell but the 4-bit `full` pass.
- **`gpt-oss` has not been re-run under the fixed goal.** It scored 100% while
  ignoring the defective clause, so it has nothing to gain — but "nothing to gain" is
  a prediction, not a measurement.
- 🔴 **`fleet` is now at ceiling for TWO models.** It could already not measure an
  improvement; it can no longer separate the two candidates at all. Harder items are
  now blocking, not merely advisable.
- Two dataset-hygiene items surfaced by the audit, both independent of this change and
  **not** acted on: `fleet-006` is keyed as a pure-authorisation item though it is the
  one item where the gate genuinely fires, with no written ruling saying why; and
  `forbidden: ['tow']` is declared on only 6 of the 9 `drivable=True` items, so the
  same wrong answer grades `forbidden` or `other` depending on which item a model errs
  on — the header's own "dataset convention scoring as a model defect" hazard.

**Evidence:** `.claude/benchmark-results/s263-2e-qwen-q8-goalfix` (`.log` + `.jsonl` +
`.wrap`) against `s263-2d-qwen-q8-full`. Gate-mechanism counts computed over both
dumps' `draft` + `rationale` fields. Gold-set audit read from
`benchmarks/procedure_baseline/dataset/fleet_maintenance.yaml`.

## 12. Session 263 — gpt-oss under the fixed goal: the prediction, measured

§11 predicted that `gpt-oss:20b` had nothing to gain from the goal fix, because it
scored 100% while ignoring the defective clause — and flagged that "nothing to gain"
was a prediction, not a measurement. It is now a measurement. Same cell as §9's
`gptoss/full`, one variable changed (the goal).

| gpt-oss `full` | β | α (canon/accept/forbid/other) | consistency | p95 breach | wall |
|---|---|---|---|---|---|
| old goal | 100% | 100% (14/0/0/0) | 14/14 | 38.1 s | 8 m 53 s |
| **fixed goal** | **100%** | **100% (14/0/0/0)** | **14/14** | 46.1 s | 7 m 12 s |

**Every score is identical.** All six mechanical criteria cleared. The fix is neutral
for this model, as predicted — and the prediction is now retired as a claim.

### Why it is neutral — the mechanism confirms the story

| gpt-oss | old goal | fixed goal |
|---|---|---|
| items whose reasoning mentions the sourcing gate | **1 of 17** | **0 of 17** |
| items naming it as downstream | 0 | 1 |

Against qwen's 17-of-17 mentions under the same old goal, this is the direct evidence
for §11's account: **gpt-oss never engaged with the contradictory clause at all.** A
directive it does not read cannot mislead it, and repairing that directive cannot
help it. Its 100% under the old goal was compliance-by-omission, not comprehension.

### What did NOT improve — and what that isolates

Its rationales are unchanged in quality. `fleet-004` still reads, verbatim:

> Only truck-04 breaches its threshold; all other readings are safe context.

No amount, no authority tier, no reason. This is the expected result and a useful
one: it isolates the two defects cleanly. **The goal fix was the remedy for wrong
actions; it is not a remedy for thin reasoning.** Rationale quality is unmeasured by
β, α and consistency alike, so nothing in this matrix would ever have caught it —
that remains open work.

(One rationale did improve: `fleet-006` now names both figures — *"The measured repair
quote of 30 001 THB is above the threshold of 5 001 THB, triggering an escalation."*
One item is not a trend.)

### An observation that is NOT a finding

Aggregate reasoning demand looks tighter — max 7,247 → 1,498 tokens. Read per item,
the 7,247 was **`fleet-016`, a watch item** (unscored calibration), which fell to 872,
while other items moved both ways (+915, +562, +529) and the **median rose** (540 →
622).

More importantly: **`gpt-oss` reproducibility has never been measured.** Only the
4-bit qwen `full` cell was ever repeated. So a per-item token delta between these two
runs cannot be separated from ordinary run-to-run variation, and no causal claim
about the goal change's effect on generation length is available from n=1 per side.
Recorded because the number is visible in the logs and would otherwise be read as a
result.

### Where this leaves the matrix

🔴 **Both models now sit at 100% / 100% / 14-of-14 on `fleet` under the fixed goal.**
The dataset can no longer distinguish them on any axis it measures, and this section
is the second consecutive run where the ceiling prevented a measurement rather than
merely limiting one.

⚠️ **Corrected 2026-08-31 (session 264).** This section used to close by calling
harder items the *blocking prerequisite* for any further model, prompt or
quantization comparison on this vertical. **Superseded, not wrong when written:**
§13 scores a **fourth axis this dataset never measured** — whether the rationale
names the human authority the spend routes to — and it separates the two models
cleanly on the fourteen items already in hand, with no live run. Harder items stay
necessary for the always-`escalate` exploit — §11 records that `canonical_handler`
is `escalate` for all fourteen breach items regardless — but they are no longer a
precondition for comparing models on this vertical.

<!-- retired: "Harder items are the blocking prerequisite" -->

**Evidence:** `.claude/benchmark-results/s263-2f-gptoss-goalfix` (`.log` + `.jsonl` +
`.wrap`) against `s263-2c-gptoss-full`. Per-item reasoning tokens read from each
dump's `calls[].eval_count` where `role == "reasoning"`.

---

## 13. Session 264 — the fourth axis: does the rationale name the approver?

§12 left the two models tied at 100% / 100% / 14-of-14, with the matrix unable to
separate them on any lane it scored. Every one of those lanes grades **which** answer
the model gave. None grades whether the model's `rationale` carries the facts a human
approver needs in order to act on it.

This section scores that fourth thing **offline, from the dumps already on disk** — no
live model, no MS-S1, no `CLAUDE.md` §8 go — and finds a clean separation on the
fourteen items already in hand.

### What is scored

`benchmarks/procedure_baseline/rationale_regrade.py` reads a run's `--dump-json` file
and scores each **breach** item's `judgment.rationale` against that item's own facts:

| signal | what it asks |
|---|---|
| `names_amount` | does the rationale state the item's own `measured_value`? |
| `names_threshold` | does it state the item's own `threshold`? |
| `roles_named` | which goal-supplied human-role phrases does it use? |

All three are literal substring or numeric matches, holding to `grader.py`'s standing
"all objective — no fuzzy/semantic scoring" discipline. Numeric matching folds
thousands separators, so `5001`, `5001.0` and `5,001` are one fact.

### Why the role check is fair

The role vocabulary is **not a hand-authored word list**. It is the intersection of a
candidate phrase set with **the procedure goal's own prose**, so a phrase is only ever
demanded of a model that was handed it in its prompt. For `governed_repair_approval`
that yields exactly `head mechanic`, `fleet manager`, `owner` — the three the goal
names in *"the head mechanic REQUESTS, the fleet manager or the owner APPROVES
(SoD)"*. Edit the goal and the check follows; a phrase the goal never supplies is
never required.

🔴 **This also caps how strict the bar can be** — see "The bar", below.

### Comparability across the goal fix

The pre-fix goal (`0a1061f~1`) carries that clause **verbatim and unchanged**, so the
demanded vocabulary is identical on both sides of the fix and this signal compares
across all six cells. **§11's comparability line on β / α / consistency is untouched
and still stands** — nothing here re-grades those lanes, and `grader.py` is not
modified.

### The measurement — all six cells

Out of 14 breach items each. `CARRIES_CONTENT` is the ratified verdict and equals
`names_role` by definition.

| cell | model | goal | `names_amount` | `names_threshold` | **`names_role`** | mean chars |
|---|---|---|---|---|---|---|
| `s262-2a-pass1` | qwen **q4** | old | 9/14 | 9/14 | 7/14 | 468 |
| `s263-2d-qwen-q8-full` | qwen **q8** | old | 5/14 | 4/14 | 4/14 | 304 |
| 🔴 **`s263-2e-qwen-q8-goalfix`** | **qwen q8** | **fixed** | 5/14 | 4/14 | **8/14** | 289 |
| `s263-2c-gptoss-full` | gpt-oss `full` | old | 3/14 | 3/14 | 1/14 | 131 |
| `s263-2c-gptoss-skip` | gpt-oss `skip` | old | 3/14 | 3/14 | 1/14 | 181 |
| 🔴 **`s263-2f-gptoss-goalfix`** | **gpt-oss `full`** | **fixed** | 6/14 | 6/14 | **0/14** | 116 |

🔴 **The models separate in every cell with no overlap** — qwen 4–8, gpt-oss 0–1. The
ceiling is no longer a blocker for model comparison on this vertical.

Two effects the three existing lanes were blind to:

- the goal fix **doubled** qwen q8's role-naming (4 → 8) while its β stayed pinned at
  100% — the fix did more than §11 could see
- **`gpt-oss` names no human role on any of its 14 items under the fixed goal**,
  though the goal supplies all three phrases. Its `fleet-004` rationale, verbatim:
  *"Only truck-04 breaches its threshold; all other readings are safe context."*
  qwen on the same item names the ceiling, the missing approval **and** the tier.

### The bar

**Role-naming alone — Cray-ratified 2026-08-31.** `carries_content` is true iff the
rationale names at least one goal-supplied role. Deliberately the weakest of the three
candidate rules, and the reason is a property of the **system**, not of the models:
the richer criteria an approver would actually want — is this the right supplier, does
their delivery history support accepting this quote, how does it compare with the
alternatives — rest on facts **the ontology does not yet carry**. A pass rule may only
demand what the run supplies, the same fairness principle the vocabulary filter
applies. Requiring the amount as well would have scored 0/14 against ~3/14 — rejected
as **unmeasurable, not as undesirable**.

That makes raising this bar an **ontology** move before it is a grader move: each
supplier-evaluation fact that enters the ontology and the goal makes a stricter rule
answerable.

### 🔴 The load-bearing negative result

**`names_amount` does not separate the models, and `gpt-oss` scores higher on it**
(6/14 vs 5/14 under the fixed goal). A check built on the intuitive *"the rationale
must state the amount"* would have ranked `gpt-oss` the better writer — the reverse of
what the text shows. Mean rationale length is no better: `gptoss/skip` is longer than
`gptoss/full` (181 vs 131) at identical role coverage. Of the three signals only the
role check carries governance weight, and that was not predictable in advance.

### What is NOT settled

- **Observation, not a finding:** qwen **q4** named roles *more* than **q8** under the
  old goal (7 vs 4), opposite to their β / α ordering. Both cells are n=1 and
  `gpt-oss` reproducibility has still never been measured (§12), so this cannot be
  separated from run-to-run variation.
- **The always-`escalate` exploit is untouched.** A model could write a role-naming
  rationale and still answer `escalate` on every item for full marks. Harder items
  remain the fix for that; this axis restores *discrimination*, not *validity*.
- **`fleet-001` cannot distinguish `names_amount` from `names_threshold`** — its
  `measured_value` and `threshold` are the same number, so one numeral satisfies both.
  Flagged by the tool rather than silently double-counted.

**Evidence:** `.claude/benchmark-results/{s262-2a-pass1, s263-2d-qwen-q8-full,
s263-2e-qwen-q8-goalfix, s263-2c-gptoss-full, s263-2c-gptoss-skip,
s263-2f-gptoss-goalfix}.jsonl`, scored by
`benchmarks/procedure_baseline/rationale_regrade.py` (merged in
[#1323](https://github.com/CrayJThiemsert/vero-lite/pull/1323), `b425bde` + `e141338`).
Each cell's model identity was confirmed from its own `.log` rather than its filename.
The instrument's own assertions were witnessed RED under an 8-probe battery
(`tools/probe_battery`, 27 claims, coverage `COMPLETE`, `GAPS: 0`), with the bar probed
in both directions. Re-runnable offline at any time — the dumps are gitignored but the
scorer is not.

---

## 14. Session 267 — the reasoning mode's effect on rationale quality, scored offline

§13 added the rationale axis and scored six cells with it. Three dumps on disk were
never scored by it, and two of them are the only cells this repo owns that vary the
**reasoning mode** on a fixed model: `qwen3.8:27b-mtp-q4_K_M` on `fleet`, old goal, in
`full` / `think_off` / `skip`. Scoring them answers the quality half of "thinking on
vs off" — **offline, from dumps already paid for, with no MS-S1 run and no §8 go**.

Model identity and reasoning mode were read from each dump's own `.log`, not from its
filename. All four cells graded **14 breach items**, so no count below moves for a
shrunken denominator.

### The pass/fail read was fixed on disk before any score existed

`.claude/benchmark-results/s267-a1-PASS-FAIL-READ.md` (gitignored; reproduced in
substance here). It pre-committed the control, the resolution, and — deliberately —
what each possible outcome would mean for the plan, so the result could not be
interpreted to suit it afterwards.

### 🔴 The precondition, measured rather than inherited

§13 states the pre-fix goal carries the role clause "verbatim and unchanged", which
is what licenses comparing this signal across the `0a1061f` line. That is an
inherited premise, so it was re-measured: the goal **texts differ** (724 vs 785
chars) while `role_vocabulary` returns the **identical** set on both sides —
`head mechanic` / `fleet manager` / `owner`. §13's licence holds.

⚠️ Establishing it needed a direct YAML parse, because `rationale_regrade.extract_goal`
**cannot** answer the question: it uses only `goal_source.parent.name` and loads the
goal from the current checkout, so a caller pointing it at a historical
`procedures.yaml` is silently handed today's goal. That is deliberate (it keeps the
text identical to the live spine's) but it was not stated; its docstring and `--help`
now say so.

### The control gated the run

| cell | mode | `names_amount` | `names_role` | mean chars |
|---|---|---|---|---|
| `s262-2a-pass1` | `full` | 9/14 | **7/14** | 468 |
| `s262-2a-pass2` | `full` (repeat) | 9/14 | **7/14** | 468 |

The repeat reproduces the first run on **every** signal, down to the mean, min and max
rationale length. Two things follow: the scorer is deterministic, so any difference
below is the model and not the instrument; and s262's byte-identity finding is
independently reconfirmed through a different instrument. `pass1`'s 7/14 also
reproduces §13's published figure exactly.

### The measurement

| mode | `names_role` | vs `full` | pre-committed reading |
|---|---|---|---|
| `full` (shipped) | **7 / 14** | — | baseline |
| `think_off` | **4 / 14** | **−3** | 🔴 **MATERIAL** |
| `skip` | **5 / 14** | −2 | ⚠️ **observed, not established** |

**`think_off` costs rationale quality**, on the one axis that carries governance
weight, at the resolution fixed before the run.

The `skip` result is reported as unresolved on purpose. `full` was measured
*bit-exactly reproducible* in s262, so if `skip` is equally deterministic its −2 is
real — but that determinism is **unmeasured for `skip`**, and one repeat would settle
it. It is neither promoted to a finding nor discarded.

### 🔴 The load-bearing negative result, for the second time

| | `names_amount` | `names_role` | mean chars |
|---|---|---|---|
| `full` | 9/14 | **7/14** | 468 |
| `think_off` | 11/14 | **4/14** | **507** |
| `skip` | **14/14** | **5/14** | 474 |

**A bar built on "the rationale must state the amount" would rank `skip` FIRST** — a
perfect 14 of 14 — while on the ratified bar it is worse than the shipped mode. And
length inverts too: `think_off` writes the **longest** rationales and names the
**fewest** roles.

§13 measured this inversion **between two models**. This is the same inversion
**inside one model, across its own reasoning modes**, on a different set of cells —
an independent second instance of lesson #0051's warning that an unvalidated axis
does not merely fail to discriminate, it can rank backwards.

### What this does and does not settle

- **Settles:** turning the reasoning pass off costs rationale quality for this model
  at this quantisation, materially, on the ratified bar.
- **Settles:** `names_amount` and mean length are unusable as quality proxies here —
  now shown twice, on independent cell sets.
- **Does NOT settle** anything about `gpt-oss` (its `think_off` is inexpressible) or
  about q8 (no q8 cell exists in `think_off` or `skip`).
- **Does NOT settle** whether this axis predicts what a human approver values. That
  is the blind read's job, and it has still never been run.
- **Bears on the plan as pre-committed:** the case for cutting a q8 `think_off` live
  cell now rests on measured *quality* as well as on speed and an unverified
  flag-honour claim. The `skip` question is one repeat away from an answer.

**Evidence:** `.claude/benchmark-results/{s262-2a-pass1, s262-2a-pass2,
s262-2b-qwen-think-off, s262-2b-qwen-skip}.jsonl`, scored by
`benchmarks/procedure_baseline/rationale_regrade.py`. Gitignored, which is why every
figure is transcribed here. Re-runnable offline at any time.

*AI-assisted (Claude Code, session 267); no `Co-Authored-By` per CLAUDE.md §7.*

---

## 15. Session 267 — what β's entity half actually measures, and what it does not

🔴 **Every β figure in §8–§14 stands. What changes is the sentence a reader is
allowed to write next to one.** No lane moved, no number moved, no run was
re-scored.

### The defect, and where it was already refuted

`grader.py`'s module docstring claimed the headline scores *the fields the model
genuinely owns in the governed procedure path*, naming `affected_primary_key` as
one of them. Measured false. And the refutation was **already written two
paragraphs below it**: the reason `suggested_handler` is a probe rather than a
headline — the product overrides the model's guess — applies to the entity fields
verbatim. It was simply never applied to them.

This is not a new theory about the benchmark. It is an **internal inconsistency
in the module's own stated rationale**, carried since the lane was written.

### What each field's fate actually is

| field | procedure path | reactive path |
|---|---|---|
| `affected_primary_key` | **overridden** — the loop entity replaces it | a **wrong** key is replaced by the deterministic event-subject anchor; a right one is kept canonical |
| `forbidden_primary_keys` | **overridden** | 🔴 a decoy is a **real** entity, so it resolves and **survives** |
| `handler_payload` | **passes through** | **passes through** |

Sources: `action_step._compose_action` (its docstring names both overrides) and
`recommender._compose_llm_record` (its docstring: the entities are
*"governed-resolved … NOT the model's verbatim list"*).

### 🔴 The inversion, stated plainly

**The headline grades a field neither path ships verbatim; the one model-owned
field that does reach the executed envelope — `handler_payload` — is graded
`advisory=True`.** The advisory flag is there for a *measurement* reason (payload
keys are free-form), never because the field does not matter, and that reason is
sound. But the two together mean the benchmark's most prominent number is its
least product-facing one.

### What follows, and what deliberately does not

- **β's entity half is kept scoring.** The capability is real, the over-naming it
  penalises is exactly why the override exists, and the `forbidden_primary_keys`
  half genuinely ships on the reactive path.
- 🔴 **No β figure may be quoted as "what the product would have done."** It is a
  model-choice instrument. That distinction is now written at the module
  docstring and at the check site, with the dead sentence declared retired.
- **Nothing was re-laned.** Moving the entity checks off the headline would retire
  every β figure this repo has published — the #1149 precedent, where a prompt
  change cost the whole engine-A accuracy lineage. A correction that costs the
  comparability line has to be worth more than the misreading it fixes, and a
  relabelling is not.
- **Open, deliberately not taken here:** whether a genuine product-behaviour axis
  should exist, built on `handler_payload` plus the prose. That is an additive
  lane and a separate decision.

### How it was found

Four specialist reviews (Fable 5, read-only) of a proposed selection criterion.
One of them proposed this; **its specific claim about the reactive path was
wrong** — it said that path uses the model's guess, when the docstring says the
entities are governed-resolved there. Checking the artifact rather than relaying
the claim made the finding **stronger**: not "one path discards it" but *neither
path ships it verbatim*, with the decoy half as the single exception.

*AI-assisted (Claude Code, session 267); no `Co-Authored-By` per CLAUDE.md §7.*
