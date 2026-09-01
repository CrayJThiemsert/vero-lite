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

from benchmarks.procedure_baseline.harness import P95_MIN_SAMPLES, percentile
from services.engine.llm.structured import ChatClient
from services.engine.nl_query import AggregateResult, NlAnswer, answer_question

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
    expected_agg = case.get("expected_aggregate")
    if expected_agg is not None and not _aggregate_ok(expected_agg, ans.aggregate):
        return "wrong"
    return "correct"


def _aggregate_ok(expected: dict[str, Any], agg: AggregateResult | None) -> bool:
    """Check a deterministically-computed aggregate against gold expectations.

    Supports ``{value: X}`` (overall aggregate, within tolerance),
    ``{top: name}`` (the group carrying the extreme value for a max/min), and
    ``{groups: {name: n, ...}}`` (PLAN-0104 — the FULL per-group breakdown).

    The ``groups`` check is deliberately EXACT and tolerance-free, unlike
    ``value``: it scores grouped counts, whose values are cardinalities of
    records — integers, where "within 0.05" would be meaningless. Exactness is
    also what gives the check teeth. Equality of the whole mapping means a
    missing group, an extra group, a mislabelled key (an un-relabelled
    ``asset-battery-01`` instead of ``Battery Bank A``) and a grouping collapsed
    into one bucket holding the total each score ``wrong`` — a subset or
    best-effort match would let every one of those through.
    """
    if agg is None:
        return False
    if "value" in expected and (
        agg.value is None or abs(agg.value - float(expected["value"])) > 0.05
    ):
        return False
    if "top" in expected:
        if not agg.groups:
            return False
        chooser = min if agg.operation == "min" else max
        top = chooser(agg.groups, key=lambda k: agg.groups[k])
        if top != expected["top"]:
            return False
    if "groups" in expected:
        want = {str(k): float(v) for k, v in dict(expected["groups"]).items()}
        got = {str(k): float(v) for k, v in agg.groups.items()}
        if got != want:
            return False
    return True


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
    """Aggregate one run: expressible accuracy, the ceiling lane, latency.

    The ceiling lane is reported as THREE numbers, not one. A ceiling case can
    fail on either side of the engine, and the single ``ceiling_rescue`` rate
    this used to publish could not tell them apart:

    * translate never handed the phrase step anything (no query emitted, or a
      query that retrieved no records), or
    * the phrase step had records and still failed to carry the expected facts.

    Measured s265 on ``gold_fleet.yaml``: **all three ceiling failures across two
    models were translate-side, and none reached the phrase step** — so the old
    metric reported 0% and 50% "rescue" for a step that never ran. Only the
    second kind is a rescue failure, and only the first is what a wider translate
    vocabulary (PLAN-0117) can move.

    Every denominator is published as a count, because the ceiling lane is small
    (2 cases on ``gold_fleet.yaml``) and a bare percentage over n=2 reads as a
    rate it is not.
    """
    expressible = [r for r in results if not r.ceiling]
    ceiling = [r for r in results if r.ceiling]
    # Translate emitted a query at all — an empty `query_json` is the hard-fail
    # shape (`run_case` also writes it when `answer_question` raised).
    translated = [r for r in ceiling if r.query_json]
    # The phrase step can only RESCUE a case it was given records for. `grounded`
    # is the engine's own record of that, so this reads the SUT, not a proxy.
    rescuable = [r for r in ceiling if r.grounded]
    latencies = [r.latency_s for r in results]

    def acc(rows: list[CaseResult]) -> float | None:
        return sum(1 for r in rows if r.outcome == "correct") / len(rows) if rows else None

    return {
        "n": len(results),
        "correct": sum(1 for r in results if r.outcome == "correct"),
        "wrong": [r.qid for r in results if r.outcome == "wrong"],
        "invalid": [r.qid for r in results if r.outcome == "invalid"],
        "expressible_acc": acc(expressible),
        # Renamed from `ceiling_rescue`, same value: the fraction of ceiling cases
        # scored correct. Comparable to every figure recorded before s266 — only
        # the name changed, because the old one named a step it did not measure.
        "ceiling_acc": acc(ceiling),
        "ceiling_n": len(ceiling),
        "ceiling_translated_n": len(translated),
        # None, never 0.0, when nothing reached the phrase step: a 0% would read
        # as "the phrase step failed" when it was never asked.
        "phrase_rescue": acc(rescuable),
        "phrase_rescue_n": len(rescuable),
        "latency_p50_s": round(percentile(latencies, 50.0), 2) if latencies else 0.0,
        # None, never a float, below P95_MIN_SAMPLES: nearest-rank returns the
        # sample MAXIMUM there, so a number here would be `latency_max_s` wearing
        # a percentile's name. This gold set is 13 cases, so it has never once
        # been able to support a real p95 — every NL p95 on record was the max.
        # Same shape as `phrase_rescue` above: absent beats unsupported.
        "latency_p95_s": (
            round(percentile(latencies, 95.0), 2) if len(latencies) >= P95_MIN_SAMPLES else None
        ),
        "latency_max_s": round(max(latencies), 2) if latencies else 0.0,
    }
