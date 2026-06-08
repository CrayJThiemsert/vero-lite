"""vero-lite benchmarks (PLAN-0019 Part B).

A top-level package (kept OUT of ``services/``) for the empirical-quality
benchmarks that *report* — never gate — on engine output (PLAN-0019 §2.1
review-separation; B-6 ring-fence). The live runners hit MS-S1 and are NOT
collected by CI (``pytest`` ``testpaths = ["tests"]``); the grader/loader logic
is unit-tested offline under ``tests/benchmark/`` with a mock ``ChatClient``.
"""
