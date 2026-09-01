"""Offline tests for ``nl_query_feasibility.harness.summarize`` (session 266).

This function had **no test at all** until now — the `summarize` tests elsewhere
under ``tests/benchmark/`` belong to ``benchmarks.procedure_baseline.harness``, a
different module. It nonetheless produced every headline figure in
``RESULTS.md``, which is exactly the shape CLAUDE.md §8 warns about: a
measurement a decision rests on, with nothing that could redden on a wrong value.

The behaviour under test is the s266 split of the ceiling lane. Measured s265 on
``gold_fleet.yaml``: all three ceiling failures across two models were
translate-side and none reached the phrase step, so the single ``ceiling_rescue``
rate reported 0% / 50% "rescue" for a step that never ran.
"""

from __future__ import annotations

from benchmarks.nl_query_feasibility.harness import CaseResult, summarize
from benchmarks.procedure_baseline.harness import P95_MIN_SAMPLES

_A_QUERY = '{"object_type":"Truck","operation":"list","filters":[]}'


def _r(
    qid: str,
    *,
    ceiling: bool,
    outcome: str,
    grounded: bool = True,
    query_json: str = _A_QUERY,
    latency: float = 1.0,
) -> CaseResult:
    """One scored case. Only the fields ``summarize`` reads are varied."""
    return CaseResult(
        qid=qid,
        category="t",
        ceiling=ceiling,
        got_object_type="Truck",
        got_filter_count=0,
        got_ids=(),
        got_count=0,
        grounded=grounded,
        outcome=outcome,
        latency_s=latency,
        answer="an answer",
        query_json=query_json,
        reason="",
    )


def test_ceiling_acc_carries_the_old_value_under_a_name_that_does_not_lie() -> None:
    """The rename keeps every pre-s266 figure comparable — only the name changed.

    ``ceiling_rescue`` named the phrase step; it counted the whole lane. The
    value is unchanged, so historical RESULTS numbers still line up.
    """
    row = summarize(
        [_r("c1", ceiling=True, outcome="correct"), _r("c2", ceiling=True, outcome="wrong")]
    )
    assert row["ceiling_acc"] == 0.5
    assert row["ceiling_n"] == 2
    # The misleading key is gone. Positive control for the negative assertion:
    # an absent key would satisfy `not in` even if summarize returned nothing.
    assert "ceiling_acc" in row, "the replacement key must exist, or the check below is vacuous"
    assert "ceiling_rescue" not in row


def test_phrase_rescue_excludes_a_case_translate_never_delivered() -> None:
    """The load-bearing claim: only a case the phrase step was GIVEN records for
    can count as a rescue.

    This is the qwen shape measured s265 — fl-09 grounded and correct, fl-10
    ungrounded and wrong. The lane accuracy and the rescue rate must disagree,
    which is the entire reason for the split.
    """
    row = summarize(
        [
            _r("fl-09", ceiling=True, outcome="correct", grounded=True),
            _r("fl-10", ceiling=True, outcome="wrong", grounded=False),
        ]
    )
    # Asserted FIRST and unaffected by the rescue denominator: under a mutation of
    # that denominator this stays green, which is what rules out "something
    # unrelated broke" when the claim below reddens (CLAUDE.md §8).
    assert row["ceiling_acc"] == 0.5
    assert row["phrase_rescue_n"] == 1, "the ungrounded case must not sit in the denominator"
    assert row["phrase_rescue"] == 1.0
    # Non-vacuity: if these were equal the split would be measuring nothing.
    assert row["phrase_rescue"] != row["ceiling_acc"]


def test_phrase_rescue_is_none_not_zero_when_nothing_reached_the_phrase_step() -> None:
    """A 0% would read as "the phrase step failed" when it was never asked.

    This is the gpt-oss shape measured s265: both ceiling cases ungrounded.
    """
    row = summarize(
        [
            _r("fl-09", ceiling=True, outcome="wrong", grounded=False, query_json=""),
            _r("fl-10", ceiling=True, outcome="wrong", grounded=False),
        ]
    )
    assert row["phrase_rescue_n"] == 0
    assert row["phrase_rescue"] is None
    # Positive control: the run was not empty, and the lane itself scored 0.
    assert row["ceiling_n"] == 2
    assert row["ceiling_acc"] == 0.0


def test_ceiling_translated_n_counts_only_cases_that_emitted_a_query() -> None:
    """Separates a translate HARD-fail from a translate SEMANTICS fail.

    Both leave the phrase step with nothing, but only the second is what a wider
    translate vocabulary (PLAN-0117) can move — so they must not be one number.
    """
    row = summarize(
        [
            _r("hard-fail", ceiling=True, outcome="wrong", grounded=False, query_json=""),
            _r("wrong-filter", ceiling=True, outcome="wrong", grounded=False),
        ]
    )
    # Green control first: the lane size does not depend on the translate filter.
    assert row["ceiling_n"] == 2
    assert row["ceiling_translated_n"] == 1
    assert row["phrase_rescue_n"] == 0


def test_the_s265_before_baseline_ceiling_lane_reproduces() -> None:
    """Pin the measured BEFORE shapes so RESULTS.md is reproducible from code.

    Both models' ceiling pairs, exactly as dumped s265. The prose in RESULTS.md
    is a claim about these numbers; this is the thing that reddens if it drifts.
    """
    gptoss = summarize(
        [
            _r("fl-09", ceiling=True, outcome="wrong", grounded=False, query_json=""),
            _r("fl-10", ceiling=True, outcome="wrong", grounded=False),
        ]
    )
    assert (gptoss["ceiling_acc"], gptoss["ceiling_translated_n"]) == (0.0, 1)
    assert (gptoss["phrase_rescue"], gptoss["phrase_rescue_n"]) == (None, 0)

    qwen = summarize(
        [
            _r("fl-09", ceiling=True, outcome="correct", grounded=True),
            _r("fl-10", ceiling=True, outcome="wrong", grounded=False),
        ]
    )
    assert (qwen["ceiling_acc"], qwen["ceiling_translated_n"]) == (0.5, 2)
    assert (qwen["phrase_rescue"], qwen["phrase_rescue_n"]) == (1.0, 1)


def test_the_split_leaves_the_expressible_lane_and_latency_untouched() -> None:
    """Regression guard: the ceiling change must not move the other headlines."""
    row = summarize(
        [
            _r("e1", ceiling=False, outcome="correct", latency=1.0),
            _r("e2", ceiling=False, outcome="wrong", latency=3.0),
            _r("c1", ceiling=True, outcome="correct", latency=5.0),
        ]
    )
    assert row["n"] == 3
    assert row["correct"] == 2
    assert row["expressible_acc"] == 0.5
    assert row["wrong"] == ["e2"]
    assert row["invalid"] == []
    assert row["latency_max_s"] == 5.0


def test_summarize_withholds_p95_on_a_gold_set_too_small_to_support_one() -> None:
    """The NL gold sets are 10-13 cases, so a nearest-rank p95 is the MAXIMUM.

    Every NL p95 ever recorded was therefore `latency_max_s` under a percentile's
    name. `None` is the honest report, and `latency_max_s` still carries the tail
    a reader actually wanted — asserted here so the two cannot be confused.
    """
    row = summarize(
        [
            _r("c1", ceiling=False, outcome="correct", latency=1.0),
            _r("c2", ceiling=False, outcome="correct", latency=2.0),
            _r("c3", ceiling=False, outcome="correct", latency=9.0),
        ]
    )
    assert row["n"] == 3
    assert row["latency_p95_s"] is None  # withheld, NOT the 9.0 nearest-rank gives
    assert row["latency_max_s"] == 9.0  # the tail is still reported, named correctly
    assert row["latency_p50_s"] == 2.0  # p50 on a small sample is still a median


def test_summarize_reports_a_real_p95_once_the_sample_supports_one() -> None:
    """At P95_MIN_SAMPLES the statistic separates from the maximum.

    Nineteen fast cases and one slow one: a genuine p95 sits on the fast body.
    If these two ever compare equal the gate has stopped doing anything — this is
    the positive control for the withholding test above, which on its own would
    also pass if `latency_p95_s` were hard-coded to None.
    """
    results = [_r(f"c{i}", ceiling=False, outcome="correct", latency=1.0) for i in range(19)]
    results.append(_r("slow", ceiling=False, outcome="correct", latency=100.0))
    row = summarize(results)

    assert row["n"] == P95_MIN_SAMPLES
    assert row["latency_p95_s"] == 1.0
    assert row["latency_max_s"] == 100.0
    assert row["latency_p95_s"] != row["latency_max_s"]
