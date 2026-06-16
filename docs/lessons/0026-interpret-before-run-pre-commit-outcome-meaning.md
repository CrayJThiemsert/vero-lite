# Lesson #0026 — Interpret before you run: pre-commit what each outcome will mean

**Date:** 2026-06-16 (session 62)
**Class:** advisory (Code-execution discipline)
**Trigger:** PLAN-0026 AC-9 live MS-S1 re-verify. The run was trustworthy
*because* the engine + harness + gold set were read **before** the run, so every
possible outcome was pre-classified — a regression could be told apart from
noise, and a lucky pass from a real validation.

## The lesson

Before running any eval / benchmark / verification, write down — *before* the
run — the targets and, for each possible outcome, **what it will MEAN**:

- **pass** (the criterion you are verifying),
- **known-acceptable-miss** (out of *this* task's scope, or known
  nondeterminism), and
- **real failure** (a regression in what you changed).

If you cannot pre-classify the outcomes, you cannot tell a regression from noise
after the run, and you will either false-alarm or claim false confidence.

## Why — the two failure modes it prevents

- **False alarm** — reading an out-of-scope or nondeterministic miss as a
  regression. AC-9's only miss was nl-01 (a simple-list filter-omission — a known,
  pre-existing model-nondeterminism gap explicitly **out of PLAN-0026's scope**,
  with a green offline gold test). Pre-classified, "11/12 not 12/12" reads as
  expected noise; un-pre-classified, it reads as a failure and triggers a
  pointless investigation (or a bogus "regression" claim).
- **False confidence** — reading a lucky or off-route pass as a validation. On
  nl-08/nl-11 the live model emitted the `unit=celsius` filter *itself*, so the
  Phase-A coherence seam never fired — the run confirmed end-to-end correctness
  but did **not** exercise the seam (the offline oracle, AC-7, is what proves the
  seam). Having read the engine first made that distinction visible and kept the
  write-up honest; otherwise "it passed" would have falsely claimed the seam was
  live-validated.

This generalizes the recurring vero-lite failure class: **a green result against
the wrong thing is worse than a red one** — it is false confidence that survives
review. Same family as: verify-a-pin-before-overriding-it (a green smoke against
an ADR-rejected model); the `uv run vero-lite` silent no-op (a clean exit that
wrote nothing); verify-relayed-responses-vs-audit-log (a stale replay read as
fresh). The fix is always the same: **know what the result will MEAN before you
produce it.**

## How to apply

- **Read the result-producing code first** — the harness + the scoring + the
  exercised path. For `vero-lite` that is the engine path the question/feature
  touches (e.g. `services/engine/nl_query.py` for an NL-query eval).
- **Pre-commit the acceptance criteria** — ideally as a `/goal` (ADR-0018 /
  PLAN-0021) so the Stop-hook gate + `goal-evaluator` can adversarially check the
  evidence — plus a one-line meaning for each non-target outcome.
- **Verify the evidence with the Read tool** (never piped `cat`/`wc`), judged
  against those criteria; report misses as **out-of-scope/known vs regression**
  explicitly, never as a bare pass/fail count.

Procedure home: the `code-operational-policy` skill ("Plan-first for costly /
host-state / irreversible / multi-step work"). Related: Lesson #3 (worktree),
the `ms-s1-ollama` skill (host-state mechanics), `benchmarks/nl_query_feasibility/RESULTS.md`
(the AC-9 addendum this lesson was distilled from).
