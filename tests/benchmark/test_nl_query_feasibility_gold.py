"""Offline tests for the NL-query feasibility spike (session 58).

Pure, no network: the gold set is well-formed + internally consistent, and the
safety-relevant scorer (``score_case``) implements the documented matrix
(expressible = deterministic result check; ceiling = phrase-rescue substring
check; honesty = grounded/no-data). The live run is manual (MS-S1).
"""

from __future__ import annotations

from typing import Any

from benchmarks.nl_query_feasibility.harness import load_gold, score_case
from services.engine.nl_query import AggregateResult, NlAnswer, StructuredQuery


def _answer(
    *,
    grounded: bool = True,
    ids: list[str] | None = None,
    count: int = 0,
    answer: str = "",
    object_type: str = "OperationalEvent",
    agg: AggregateResult | None = None,
) -> NlAnswer:
    """Build an NlAnswer with just the fields score_case reads."""
    ids = ids or []
    return NlAnswer(
        question="q",
        answer=answer,
        grounded=grounded,
        query=StructuredQuery(object_type=object_type),
        source_object_type=object_type,
        source_object_ids=ids,
        source_objects=[],
        result_count=count,
        aggregate=agg,
    )


def test_gold_set_is_well_formed_and_consistent() -> None:
    vertical, cases = load_gold()
    assert vertical == "energy"
    assert len(cases) >= 10
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case id"
    for c in cases:
        assert c["text"].strip(), c["id"]
        assert isinstance(c["ceiling"], bool), c["id"]
        if not c["ceiling"]:
            # expressible cases carry a deterministic gold result
            assert c["expected_object_type"], c["id"]
            assert "expected_count" in c, c["id"]
            # expected_count must agree with the id list when one is given
            if c.get("expected_ids"):
                assert c["expected_count"] == len(c["expected_ids"]), c["id"]
        else:
            # ceiling cases carry the load-bearing answer facts (or are honesty probes)
            assert c.get("expected_answer_substrings") or "expected_grounded" in c, c["id"]
    # both lanes must be exercised
    assert any(c["ceiling"] for c in cases)
    assert any(not c["ceiling"] for c in cases)


def _case(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"id": "x", "text": "q", "category": "t", "ceiling": False}
    base.update(kw)
    return base


def test_score_expressible_result_match() -> None:
    case = _case(expected_count=2, expected_ids=["a", "b"], expected_grounded=True)
    assert score_case(case, _answer(ids=["a", "b"], count=2)) == "correct"
    assert score_case(case, _answer(ids=["b", "a"], count=2)) == "correct"  # set, order-free


def test_score_expressible_wrong_on_count_or_ids() -> None:
    case = _case(expected_count=2, expected_ids=["a", "b"])
    assert score_case(case, _answer(ids=["a", "b"], count=3)) == "wrong"  # count off
    assert score_case(case, _answer(ids=["a", "c"], count=2)) == "wrong"  # ids off


def test_score_expressible_wrong_on_grounded_mismatch() -> None:
    case = _case(expected_count=1, expected_ids=["a"], expected_grounded=True)
    assert score_case(case, _answer(grounded=False, ids=["a"], count=1)) == "wrong"


def test_score_ceiling_rescue_via_substrings() -> None:
    case = _case(ceiling=True, expected_answer_substrings=["96.5", "Battery Bank A"])
    good = _answer(answer="The highest is 96.5 C on Battery Bank A.")
    bad = _answer(answer="The highest reading is on Battery Bank A.")  # missing 96.5
    assert score_case(case, good) == "correct"
    assert score_case(case, bad) == "wrong"


def test_score_ceiling_substring_is_case_insensitive() -> None:
    case = _case(ceiling=True, expected_answer_substrings=["battery bank a"])
    assert score_case(case, _answer(answer="It is Battery Bank A.")) == "correct"


def test_score_honesty_no_data_probe() -> None:
    """grounded=false + count 0 + a 'No ...' answer is correct; inventing is wrong."""
    case = _case(
        ceiling=True,
        expected_grounded=False,
        expected_count=0,
        expected_answer_substrings=["No"],
    )
    honest = _answer(grounded=False, count=0, answer="No Alert records match that query.")
    invented = _answer(grounded=True, count=2, answer="There are 2 open alerts.")
    assert score_case(case, honest) == "correct"
    assert score_case(case, invented) == "wrong"  # grounded mismatch


def test_score_aggregate_value_match() -> None:
    """A ceiling=false aggregate case is scored on the computed value (tolerant)."""
    case = _case(expected_count=3, expected_grounded=True, expected_aggregate={"value": 41.3})
    agg = AggregateResult(operation="avg", property="measured_value", value=123.9 / 3)
    assert score_case(case, _answer(count=3, agg=agg)) == "correct"  # 41.3 within tolerance
    off = AggregateResult(operation="avg", property="measured_value", value=99.0)
    assert score_case(case, _answer(count=3, agg=off)) == "wrong"
    assert score_case(case, _answer(count=3, agg=None)) == "wrong"  # no aggregate computed


def test_score_aggregate_top_group_match() -> None:
    """A group-by superlative is scored on which group carries the extreme value."""
    case = _case(
        expected_count=7,
        expected_grounded=True,
        expected_aggregate={"top": "Battery Bank A"},
    )
    groups = {"Battery Bank A": 96.5, "Battery Bank B": 43.2}
    hot = AggregateResult(operation="max", property="measured_value", value=96.5, groups=groups)
    assert score_case(case, _answer(count=7, agg=hot)) == "correct"
    flipped = AggregateResult(
        operation="max",
        property="measured_value",
        value=43.2,
        groups={"Battery Bank A": 10.0, "Battery Bank B": 43.2},
    )
    assert score_case(case, _answer(count=7, agg=flipped)) == "wrong"
