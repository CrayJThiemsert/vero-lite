"""Offline unit tests for the procedure-baseline benchmark (PLAN-0019 B-β).

CI-collected (``testpaths = ["tests"]``); the live runner is NOT. Every test here
is deterministic + offline (Lesson #7 §3): the loader/grader are pure, and the
harness flow is exercised with a mock ``ChatClient`` — no live LLM, no MS-S1.
"""
