# Model comparison — result (2026-08-28, session 259)

> Run under Cray's typed go for host-state (CLAUDE.md section 8). Bars and their
> reading order were fixed in `DECISION.md` **before** any model was contacted;
> nothing below was edited after seeing a number.

## Verdict

**KEEP `gpt-oss:20b` for the phase-2 dry-run.** The challenger fails **B2**
(structured-output integrity) and **B6** (latency) decisively, and B2 is an
earlier bar than either accuracy or stability, so the comparison stops there.

**This is not a finding that the challenger writes worse proposals.** On the
items it completed it did better on the graded headline. It is a finding that it
**cannot complete the workload on this box within the shipped client's timeout**.

## Scope, stated so no number here is over-quoted

20 items from the head of the **energy** procedure-baseline set (`--limit 20`,
`--dataset-dir` holding only `energy.yaml`). Incumbent: 3 repeats. Challenger:
**1 repeat — stopped early** once B2 failed, per DECISION.md's own stop rule and
CLAUDE.md section 8's minimise-live-runs discipline. **No number here is a
66-item number, and none is a product-quality number.**

## The bars, in their fixed reading order

| Bar | `gpt-oss:20b` | `qwen3.8:27b-mtp-q8_0` | Result |
|---|---|---|---|
| **B1** tag verified on the box | present | **present** — exact match in `/api/tags` | ✅ both |
| **B2** judgment errors ≤ incumbent, every repeat | **1, 0, 0** of 20 | **10 of 20** (`Ollama call to /api/chat failed`) | 🔴 **challenger FAILS** |
| **B3** no forbidden handler, ever | none | none | ✅ both |
| **B4** majority accuracy | 10.0% (2/20) | 30.0% (6/20) | ⚠️ see below |
| **B5** flip rate ≤ 0.15 | **45.0% — NOISY** | not measurable (1 repeat) | 🔴 **INSUFFICIENT-EVIDENCE** |
| **B6** p95 within 2x incumbent | p95/call **25.9–28.4 s** | p95/call **120.1 s** (4.4x); per-judgment p95 **235.5 s** vs the 30 s SD-2 bar → OVER | 🔴 **challenger FAILS** |

The B6 number is the loud one: the challenger's per-call p95 sits **on** the
120 s client timeout, i.e. most calls did not finish — which is also what B2 is
measuring from the other side.

## Three findings worth more than the verdict

**1. The recorded 97.5% baseline is NOT comparable to any run made today.** The
REPORT's energy figure (39/40) predates three commits to `services/engine/llm/`
that changed the shared prompt — `8324cba` (deterministic `affected_entities`
override + prompt nudge), `bef462f` (think-trim lever), `4d54683` (handler
catalog). Same shape as the NL benchmark's retired `11/12`. **Do not read today's
low numbers as a regression against it**; read them as a different measurement.

**2. `gpt-oss:20b` picks the right handler and then writes prose that contradicts
it.** Across 60 judgments its `suggested_handler` was `restart` — **canonical
100% of the time, zero forbidden** — while the failing titles were overwhelmingly
*"Shutdown asset-EXX due to temperature breach"*, plus one *"Ignore event"*. The
graded miss is `action_keywords` alone: the entity is right, the handler is right,
the sentence a human reads says something else. This is precisely the class
`verify_action_expression` exists to catch (ADR-0022 member (b)), and it matters
directly for phase 2, where a person approves by reading that prose.

**3. The measurement itself is variance-dominated at this size.** The incumbent's
**flip rate is 45%** — 9 of 20 items changed verdict between identical runs. Per
DECISION.md B5 that makes the accuracy comparison **INSUFFICIENT-EVIDENCE**, and
it is why the verdict rests on B2 and B6 instead. It also retires today's β number
as a baseline for anything: a figure that moves 45% of the time is not a figure.

## What the challenger actually did

Its handler picks were `escalate` (4) and `dispatch_technician` (6) — **registered
handlers, not invalid output**. The dataset pins `restart` as canonical and
declares no acceptable alternatives, so those grade as `other`, not as
`forbidden`. For a 96 C asset, escalating to a human is a defensible action; the
0% alpha score is "different from the pinned answer", not "dangerous". Of the 10
items it completed, 6 passed the headline — better prose/handler alignment than
the incumbent showed, on a tenth of the sample and with no second repeat.

**If the timeout is ever the thing that changes** (a longer
`llm_request_timeout_s`, a smaller quantisation, more headroom on the box), this
model is worth re-running. B2 and B6 failed **as configured today**, not as a
statement about the weights.

## Instrument defect found by using it

The joiner reported `flip rate 0.0%` for a model measured **once** — unanimous
with itself by construction, and it read as "stable". Fixed in the same session:
`flip_rate` is now `None` below two repeats and renders as *"not measurable
(needs 2+ repeats)"*, with a test and a positive control. The bug was only
reachable because the challenger's run was stopped early; a clean 3-vs-3 run
would have hidden it.

## Not done

**The blind Thai prose read (DECISION.md section 5) was not run.** The corpus is
English, and the challenger produced only 10 usable judgments against the
incumbent's 60 — too thin and too asymmetric to rate. The instrument for it
(`blind_read.py`) is built, tested and battery-verified, and is language-agnostic
so it serves the phase-2 Thai corpus unchanged. **The rater must be someone who
has not read the dumps** — which excludes the agent that diagnosed these failures.

## Evidence

Dumps: `.claude/benchmark-results/s259-mc-gptoss-{1,2,3}.jsonl`,
`s259-mc-qwen-1.jsonl`, joined report `s259-mc-report.json`; console logs
`/tmp/mc-gptoss-{1,2,3}.log`, `/tmp/mc-qwen-1.log` (latency lives only in the
console output, not in the dumps).

⚠️ `.claude/benchmark-results/` is untracked **and unignored** — this evidence
lives only in the working tree until it is deliberately copied somewhere durable.
That has already cost this repo one set of dumps.
