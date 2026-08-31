# Lesson 0051: A saturated benchmark may be missing an axis, not needing harder data

**Status:** Advisory (names a diagnostic order and records the measurement behind
it; the axis it produced ships as the rationale lane in
`benchmarks/procedure_baseline/grader.py`)
**Source:** Sessions 263 → 264 on `fleet` — a conclusion drawn, then falsified
with the same data that produced it

## The claim

When every model scores 100% and the benchmark stops discriminating, the reflex
is *"the items are too easy — we need harder ones."* That reflex names a real
option and skips a cheaper one.

**Ask first what dimension the instrument never scored.** A saturated benchmark
can be measuring everything it measures perfectly, on the wrong set of things.
Harder data is the answer only after that question has been asked and answered.

The order matters because the two options are wildly asymmetric in cost. New
items need authoring, ratification, a live run per cell and a §8 host-state go —
and they create a permanent comparability line, because every figure measured on
the old item set stops comparing. A missing axis, if one exists, is scored
**offline against runs already paid for**.

## What happened

Session 263 closed with `gpt-oss:20b` and `qwen3.8:27b-mtp-q8_0` both at
**100% β / 100% α / 14-of-14 consistency** on `fleet`, and recorded the
conclusion in `RESULTS-1.6.md` §12:

> Harder items are the **blocking prerequisite** for any further model, prompt,
> or quantization comparison on this vertical.

It was an honest reading of every axis then measured. It was also wrong about
what was blocking, and the evidence to see that was already on disk.

*(That sentence is a **retired** claim — `RESULTS-1.6.md` §12 carries its
`<!-- retired: … -->` marker. It is quoted here with emphasis inside it, which is
how `docs/conventions/retired-claims.md` permits a correction narrative to repeat
a dead claim without resurrecting it. The first draft of this lesson quoted it
plainly and the pre-commit guard refused the commit — correctly.)*

**All three existing lanes grade _which_ answer the model gave** — β the affected
entity and action class, α the handler pick, consistency whether same-case items
draw the same class. **None of them reads the `rationale`**, which is the part a
human approver actually has to act on.

Session 264 scored one question — *does the rationale name the human authority
the spend routes to?* — over the six dumps already on disk. Out of 14 breach
items:

| cell | model | goal | names a role |
|---|---|---|---|
| `s262-2a-pass1` | qwen q4 | old | 7/14 |
| `s263-2d` | qwen q8 | old | 4/14 |
| `s263-2e` | qwen q8 | **fixed** | **8/14** |
| `s263-2c-full` | gpt-oss | old | 1/14 |
| `s263-2c-skip` | gpt-oss | old | 1/14 |
| `s263-2f` | gpt-oss | **fixed** | **0/14** |

**Separation in every cell, no overlap, zero MS-S1 runs, no §8 go needed.** The
ceiling was never the dataset's difficulty. It was the instrument's coverage.

Two things fell out that no amount of harder data would have produced: the goal
fix had **doubled** qwen's role-naming (4 → 8) while its β stayed pinned at
100%, and `gpt-oss` names **no** human role on **any** of its fourteen items
despite the goal handing it all three phrases.

## The cautionary half — the intuitive axis ranks backwards

This lesson is not "add a fourth axis and you win." Three candidate signals were
scored on the same runs, and **two of them are worse than useless**:

| signal | gpt-oss | qwen q8 | verdict |
|---|---|---|---|
| states the quoted amount | **6/14** | 5/14 | ranks the models **backwards** |
| mean rationale length | 116 | 289 | tracks verbosity, not content |
| **names the approver** | **0/14** | **8/14** | the separating signal |

A check built on the obvious *"the rationale must state the amount"* would have
concluded `gpt-oss` was the better writer. Read the two texts and the ordering is
not close:

- **gpt-oss, `fleet-004`:** *"Only truck-04 breaches its threshold; all other
  readings are safe context."*
- **qwen q8, same item:** *"...whose repair quote is above its per-truck ceiling.
  No human approval has been recorded yet, so the decision must be escalated to
  the required authority tier."*

**A new axis is a hypothesis, not a fix.** It has to be scored against a case
whose answer is already known — here, prose a human can read and rank — before
any conclusion rests on it. The cost of skipping that step is not a null result;
it is a confident inversion.

## Where this fires

- A model / prompt / quantization comparison that has stopped separating.
- Any acceptance bar where every candidate passes. A gate nothing fails is
  either a solved problem or an unmeasured dimension, and the two look identical
  from the pass rate alone.
- The moment a plan names "harder cases" as its gating dependency. That may be
  right — session 264 did **not** retire the need for harder `fleet` items, it
  retired their status as a *precondition*. The always-`escalate` exploit is a
  **validity** defect and still needs new items; the ceiling was a
  **discrimination** defect and did not.

## What this does NOT say

- Not "benchmarks never need harder data." They do — see the exploit above.
- Not "always add axes." Two of the three candidates measured here were noise or
  worse; an unvalidated axis is a new way to be confidently wrong.
- Not a claim that the s263 conclusion was careless. It was true of every axis
  the dataset then measured, and is recorded as **superseded by new info, not an
  error** (`CLAUDE.md` §6) — the retirement in `RESULTS-1.6.md` §12 says so
  explicitly.

## References

- `benchmarks/model_compare/RESULTS-1.6.md` §12 (the retired claim, with its
  `<!-- retired: ... -->` marker) and **§13** (the full measurement).
- `benchmarks/procedure_baseline/rationale_regrade.py` — the offline scorer; any
  of §13 is re-derivable in seconds without touching MS-S1.
- `benchmarks/procedure_baseline/grader.py` — where the axis became a scored
  lane, isolated from β/α by construction.
- Lesson #0052 — the constraint on *how strict* a new axis may be.
- Lesson #0037 (a scan's blind spot is the intersection of its axes) — the
  sibling case, where the axes exist and the gap is between them; here the axis
  was absent outright.
- `docs/conventions/retired-claims.md` — how §12's claim was retired rather than
  deleted.
