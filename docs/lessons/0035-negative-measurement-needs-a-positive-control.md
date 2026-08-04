# Lesson #0035 — A measured zero is only as strong as the string you searched for

**Date:** 2026-08-04 (session 205; the wrong number had stood since s180)
**Class:** advisory (measurement discipline / verification)
**Trigger:** the OQ-4 re-measure. Re-running a pre-committed criterion did not
just answer it — it found that the **baseline the criterion was written against
was wrong by 56 events**, and that the criterion's prescribed remedy pointed at
an ADR that never backed the thing being retired.

## The lesson

**When a measurement's result is an absence, the search key must be recovered
from the artifact that *emits* it — never from a document that *quotes* it. And
a zero is not evidence until a positive control proves the method can find a
one.**

An absence has no shape of its own. `0 denies` and `0 denies found by a search
for a string that never existed` are the same characters on the page, produced
by the same command, and there is nothing in the output of either to tell them
apart. The only thing that separates them is a control: *make the method find
something you already know is there, first.* If it cannot re-find the known
positives, its zeros are noise wearing the costume of data.

The corollary is about **where a wording gets recovered from.** A quote in a
lesson, a runbook, or a PLAN is a *transcription* — accurate at the moment it
was taken, of the surface it was taken from, and silently divergent from the
live emitter thereafter. Recover from the emitter.

## The incident, measured

The s180 baseline for OQ-4 banked, over 113 transcripts:

| | s180 banked | s205 re-measured |
|---|---|---|
| L1 **denies** | **0** | **≥ 56** |
| L1 **warns** | 3 | **3** ✓ |
| **true positives** | 0 | 0 ✓ |

Two of the three rows were right. The deny row was wrong by at least 56 events
across 19 days, at a rate of **1.33 % of all 4,201 Write/Edit operations in the
window** — i.e. the guard was hard-walling legitimate work roughly every 75
edits, while the record said it had never hard-walled anything at all.

**Root cause: there were three deny wordings, not two.** The measurement note
was explicitly careful about this — it warned that P2 had "rewrote the deny
message wholesale" and instructed a future re-runner to search *both* wordings.
It recovered the pre-P2 form and searched for it. But the form it recovered was:

```
hit 6 times in this session (Cray E.4 threshold = 6)
```

— which is what `docs/lessons/0012-…:26` quotes, under the heading "verbatim
from the live fire". Every actual transcript emission reads:

```
hit N times in this turn (Cray E.4 threshold = 6)
```

`session` → `turn`. One word, and the search matched nothing, 56 times. The warn
count was correct in the same run because the warn string had been recovered
from the hook source rather than from a doc.

**The zero was load-bearing.** It was not a stray number: it was the premise of
OQ-4's reasoning ("real non-progress signals with, so far, zero observed
instances") and of the criterion built on top of it. Four sessions of planning
cited it. Nothing downstream could have caught it, because everything downstream
consumed the conclusion rather than the method.

## What made the re-measure trustworthy

Three things, in the order they mattered:

1. **A positive control, declared before the run.** The baseline named its three
   warns and their targets. The re-measure's pass condition included *re-finding
   those three* — and the run was to be **discarded**, not reported, if it found
   none. It found 3/3. Only then were its other numbers worth reading.
2. **A structural key, not a substring.** Genuine emissions land in exactly two
   JSON positions — `attachment.blockingError.blockingError` for a warn, a
   bare-string `toolUseResult` or a `permissionDecisionReason` leaf for a deny.
   A raw substring sweep returned **253 hits across 101 files**, roughly 3× the
   truth: docs quoting the string, agent prose discussing OQ-4, prior
   measurement attempts, and the measuring session's own transcript. Keying on
   structure made the pollution disappear without hand-filtering.
3. **An exposure denominator.** "0 denies post-AC-7" means nothing until you can
   say the window contained **1,369 Write/Edit operations over 31 transcripts**.
   A zero over an idle window is not a finding; a zero over a busy one is.

Two smaller traps, both hit and both worth naming:

- **The first dedupe key undercounted, 29 vs 56.** Keying on `(file, kind, text)`
  collapsed repeat denies on the same target, because a second firing on the same
  file at the same threshold produces *byte-identical* text. Keying on
  `(timestamp, target)` separated them. A dedupe key that includes the payload
  but not the occasion silently merges real events.
- **A single surviving firing can be synthetic.** The one post-AC-7 warn was
  induced — a self-test of the guard, fired three minutes after a human turn
  asking for a live-check, on a scratchpad file named `l1_livecheck.py`. Counted
  naively it would have satisfied the criterion's "≥ 1 false positive" arm and
  flipped the outcome. **Read the intent around a lone data point before letting
  it decide anything.**

## The second finding: the remedy's premise was also unchecked

The criterion prescribed "dispatch Cowork to draft an **ADR-013 amendment**
retiring L1". Grounding that before acting on it showed ADR-013 never backed L1:
`:90` states trigger E.4 in terms of "the same *problem*" and never names L1, and
`:333-336` says the ADR "codifies E.1–E.5 only" and that "PLAN-0008+ must carry
its own ratification for … stateful loop-detection". The correct vehicle is a
PLAN, on the PLAN-0092 precedent ("No ADR amendment — zero ADR backing").

Same shape as the measurement error, one level up: **a remedy recorded years
earlier is a claim about the repo, and it decays exactly like a quoted string
does.** Check the remedy's premise at the moment you execute it, not at the
moment you wrote it down.

## How to apply

- Any time a result is **an absence**, name the positive control *before* the
  run and state what it would mean if the control fails. "No fresh evidence =
  INSUFFICIENT-EVIDENCE, not a pass" (CLAUDE.md §8) extends to: *no control =
  not a zero.*
- Recover a search key from the **emitting code**, not from a doc quoting it. If
  the emitter has changed over time, recover **every** historical form from the
  emitter's own history and verify each still matches something.
- Prefer a **structural key** (a field path, a record type) over a substring
  whenever the corpus also *discusses* the thing being counted. Governance repos
  always discuss the thing being counted.
- Report the **denominator** alongside a zero.
- When a stored criterion tells you what remedy to apply, **ground the remedy's
  premise too**. It is a forward reference, and forward references rot
  ([[feedback_verify_doc_forward_reference_vs_code]]).

## Related

- CLAUDE.md §8 — "the offline oracle is the gate"; positive controls for absence
  claims.
- CLAUDE.md §6 — "Verification is hygiene, not a verdict". The s180 baseline is
  classified **was an error** (a wrong measurement), not *superseded by new
  info*: the deny events existed at the moment it was taken.
- [`0026-interpret-before-run-pre-commit-outcome-meaning.md`](0026-interpret-before-run-pre-commit-outcome-meaning.md) — pre-committing what each outcome means.
- [`0012-loop-detect-l1-vs-governance-doc-fillup-passes.md`](0012-loop-detect-l1-vs-governance-doc-fillup-passes.md) — holds the divergent quote at `:26`. Left as-is: it is an accurate record of *that* fire, and the defect was trusting it as the canonical wording.
- [`0029-verify-full-suite-not-subset.md`](0029-verify-full-suite-not-subset.md) — the same family: a narrowed check reporting a clean result.
