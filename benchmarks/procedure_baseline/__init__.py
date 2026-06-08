"""Procedure-baseline benchmark (PLAN-0019 Step B-β; AC B-1).

Measures **LLM action-proposal correctness** (SD-B1 graded unit A) on the
governed-procedure engine: per scenario the deterministic ``evaluate`` routing
(``crosses_threshold``) is a ~100% sanity check (reported separately, NOT folded
into the headline), and on the **breach** subset the live two-call judgment path
(``generate_judgment`` -> ``LlmJudgment``) is graded against a human-authored
ground-truth key — the part where the bound local model can actually be *wrong*.

Layout::

    benchmarks/procedure_baseline/
      schema.py         # dataset item models (Scenario / Expected / BenchmarkItem / Dataset)
      loader.py         # load_dataset / load_all — pure YAML -> models
      grader.py         # classify_disposition (deterministic) + grade_proposal (objective)
      harness.py        # evaluate_item (deterministic -> if breach, LLM -> grade) + summarize
      run_benchmark.py  # live runner skeleton (manual; hits MS-S1; NOT collected by CI)
      dataset/*.yaml    # human-authored ground truth (reviewable)
      REPORT.md         # B-5 (filled after the live run)

The grader/loader/harness are pure + injection-seamed (a ``ChatClient`` is passed
in), so the offline ``tests/benchmark/`` suite exercises the whole flow with a
mock client; only the actual RUN needs the live ``gpt-oss:20b`` on MS-S1.
"""
