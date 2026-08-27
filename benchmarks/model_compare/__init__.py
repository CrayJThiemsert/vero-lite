"""Two-model comparison over the procedure-baseline graded dataset (FDE program phase 1.5).

Answers ONE question: **which local model do we bind for the phase-2 dry-run** —
the pinned ``gpt-oss:20b`` or a challenger. It is a *decision instrument*, not a
new benchmark: every graded number here is produced by the shipped
``benchmarks.procedure_baseline`` runner and grader, unforked.

What is REUSED (nothing re-implemented)
---------------------------------------
``run_benchmark.py`` already takes ``--model`` and ``--dump-json`` (the B-delta
per-model sweep), and ``grader.grade_proposal`` already scores entity + action
class + the tiered handler probe. So a per-model run needs **no new code at all**.

What is NEW here, and why it has to exist
-----------------------------------------
1. **A joiner.** Nothing in the repo reads two dump files and puts them
   side by side.
2. **A stability measure.** Ollama at ``temperature=0`` is NOT deterministic and
   this repo has already been burned by that: a prior experiment recorded
   *"variance dominates — 5 of 7 options flipped verdict on unchanged evidence"*.
   A single run per model would therefore compare two samples of noise. Every
   model is run **three times** and compared on its **majority verdict**, with
   the per-item flip rate reported next to the accuracy so a reader can see how
   much of any gap is signal.

Non-goals (deliberate)
----------------------
* No live-run entry point. The exact command sequence lives in ``DECISION.md``;
  adding a second way to reach MS-S1 is a way to get the warm/sequencing wrong
  (host-state is Cray-gated per CLAUDE.md section 8).
* No new grading logic. A metric this module cannot compute from the shipped
  dump is reported as absent, never approximated.
* Thai-prose quality is NOT measured here — the procedure-baseline dataset is
  English, so this instrument cannot speak to it. ``DECISION.md`` carries that
  as a separate, explicitly smaller blind-rating step over the same dumps.
"""
