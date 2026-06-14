"""Per-question evaluation + aggregation for the NL-query feasibility spike.

Pure scoring logic (``score_case`` / ``summarize``) is offline-testable; the
live runner (``run_case``) drives the shipped ``answer_question`` engine-A path
against MS-S1 and is exercised only by ``run_benchmark.py`` (manual).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from benchmarks.procedure_baseline.harness import percentile
from services.engine.llm.structured import ChatClient
from services.engine.nl_query import NlAnswer, answer_question

GOLD_PATH = Path(__file__).parent / "gold.yaml"

OUTCOMES = ("correct", "wrong", "invalid")


def load_gold(path: Path = GOLD_PATH) -> tuple[str, list[dict[str, Any]]]:
    """Load + lightly validate the gold set (full validation is the offline test)."""
    yaml = YAML(typ="safe")
    with path.open(encoding="utf-8") as handle:
        data: dict[str, Any] = yaml.load(handle)
    vertical = str(data["vertical"])
    cases = data["cases"]
    if not isinstance(cases, list) or not cases:
        raise SystemExit("gold.yaml: no cases")
    return vertical, cases


@dataclass(frozen=True)
class CaseResult:
    """One question's outcome, scored."""

    qid: str
    category: str
    ceiling: bool
    got_object_type: str | None
    got_filter_count: int
    got_ids: tuple[str, ...]
    got_count: int
    grounded: bool
    outcome: str  # correct | wrong | invalid
    latency_s: float
    answer: str
    query_json: str
    reason: str


def score_case(case: dict[str, Any], ans: NlAnswer) -> str:
    """Outcome for one case.

    ceiling=false → ``result_ok``: the executed result (count + id set) equals
    the hand-verified gold — invariant to how the filter was phrased.
    ceiling=true → ``answer_ok``: the phrased answer carries every expected
    substring (the phrase-step "rescue"), plus any grounded/count expectation
    (the honesty probe). A correct expected_grounded mismatch is always wrong.
    """
    expected_grounded = case.get("expected_grounded")
    if expected_grounded is not None and ans.grounded != bool(expected_grounded):
        return "wrong"

    if case.get("ceiling"):
        if "expected_count" in case and ans.result_count != case["expected_count"]:
            return "wrong"
        subs = case.get("expected_answer_substrings", []) or []
        low = ans.answer.lower()
        return "correct" if all(str(s).lower() in low for s in subs) else "wrong"

    # expressible: deterministic executed-result check
    if ans.result_count != case["expected_count"]:
        return "wrong"
    expected_ids = set(case.get("expected_ids", []) or [])
    if expected_ids and set(ans.source_object_ids) != expected_ids:
        return "wrong"
    return "correct"


async def run_case(case: dict[str, Any], vertical: str, client: ChatClient) -> CaseResult:
    """Run one question through the shipped engine-A path and score it."""
    start = time.perf_counter()
    try:
        ans = await answer_question(case["text"], vertical, client=client)
    except Exception as exc:  # answer_question degrades internally; this is defensive
        return CaseResult(
            qid=str(case["id"]),
            category=str(case.get("category", "")),
            ceiling=bool(case.get("ceiling")),
            got_object_type=None,
            got_filter_count=0,
            got_ids=(),
            got_count=0,
            grounded=False,
            outcome="invalid",
            latency_s=time.perf_counter() - start,
            answer="",
            query_json="",
            reason=f"error: {exc}",
        )
    latency = time.perf_counter() - start
    outcome = score_case(case, ans)
    return CaseResult(
        qid=str(case["id"]),
        category=str(case.get("category", "")),
        ceiling=bool(case.get("ceiling")),
        got_object_type=ans.query.object_type if ans.query is not None else None,
        got_filter_count=len(ans.query.filters) if ans.query is not None else 0,
        got_ids=tuple(ans.source_object_ids),
        got_count=ans.result_count,
        grounded=ans.grounded,
        outcome=outcome,
        latency_s=latency,
        answer=ans.answer,
        query_json=ans.query.model_dump_json() if ans.query is not None else "",
        reason="",
    )


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    """Aggregate one run: expressible accuracy, ceiling rescue rate, latency."""
    expressible = [r for r in results if not r.ceiling]
    ceiling = [r for r in results if r.ceiling]
    latencies = [r.latency_s for r in results]

    def acc(rows: list[CaseResult]) -> float | None:
        return sum(1 for r in rows if r.outcome == "correct") / len(rows) if rows else None

    return {
        "n": len(results),
        "correct": sum(1 for r in results if r.outcome == "correct"),
        "wrong": [r.qid for r in results if r.outcome == "wrong"],
        "invalid": [r.qid for r in results if r.outcome == "invalid"],
        "expressible_acc": acc(expressible),
        "ceiling_rescue": acc(ceiling),
        "latency_p50_s": round(percentile(latencies, 50.0), 2) if latencies else 0.0,
        "latency_p95_s": round(percentile(latencies, 95.0), 2) if latencies else 0.0,
        "latency_max_s": round(max(latencies), 2) if latencies else 0.0,
    }
