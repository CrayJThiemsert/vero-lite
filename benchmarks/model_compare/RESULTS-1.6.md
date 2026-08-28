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
| gptoss / think_off | 10% | 100% canon | 0 | 40.7 s | 144.8 s | 0 | `restart` ×10 |
| gptoss / skip | 30% | 100% canon | 0 | **27.2 s** | 48.0 s | 0 | `restart` ×10 |
| qwen / full | 30% | 0% | **3** | 188.9 s | 300.1 s | 3 | escalate ×3, dispatch ×4 |
| qwen / **think_off** | **80%** | 75% canon | **2** | 62.4 s | 300.1 s | 2 | **restart ×6**, dispatch ×2 |
| qwen / **skip** | 60% | 30% canon | **0** | 85.2 s | 116.6 s | 0 | restart ×3, dispatch ×6, escalate ×1 |

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

`gptoss/think_off` is a latency anomaly worth noting: p95 **144.8 s** against
`full`'s 45.6 s. Running call 1 with `think=false` is slower than running it with
thinking on. Unexplained; recorded rather than smoothed over.

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
