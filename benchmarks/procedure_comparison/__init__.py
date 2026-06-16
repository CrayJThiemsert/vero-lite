"""B-γ comparison baselines (PLAN-0027 / PLAN-0019 Step B-γ / AC B-3).

The three-arm comparison of the vero-lite governed-procedure stack against two
baselines, on the energy **breach subset** (D-5), graded on the **common
sub-task** (D-1: affected entity + action class, reusing the procedure-baseline
``grade_proposal``):

* arm (a) — the governed-procedure stack; its numbers are **reused** from
  ``benchmarks/procedure_baseline/REPORT.md`` (D-2 — NOT re-run here);
* arm (b) — raw text-to-SQL (``text_to_sql_arm``; D-3);
* arm (c) — lean-but-real RAG (``rag_arm``; D-4 / SD-5), a CLEAN naive baseline
  with NO procedure/ontology/verify/reshape layer (D-6 contamination guard).

Reports-not-gates (B-3/B-6): a baseline matching or beating arm (a) is a
**finding**, never a build failure.
"""
