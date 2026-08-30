"""The consistency metric, and the ruling that defines it.

The load-bearing case is the strict reading: an *acceptable* handler is a
DIFFERENT class of answer, not agreement. That is a domain judgement Cray settled
on 2026-08-30, and it is the difference between reporting 9/14 and 11/14 on the
same run. A test is what stops it drifting back.
"""

from __future__ import annotations

from typing import Any

from benchmarks.procedure_baseline.tier_consistency import band_of, render, score


def _breach(item_id: str, amount: float, handler: str | None) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "scenario": {"measured_value": amount},
        "expected": {"disposition": "breach", "canonical_handler": "escalate"},
        "judgment": None if handler is None else {"suggested_handler": handler},
    }


def _non_breach(item_id: str, disposition: str) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "scenario": {"measured_value": 4_000.0},
        "expected": {"disposition": disposition, "canonical_handler": None},
        "judgment": {"suggested_handler": "echo"},
    }


def test_an_acceptable_handler_does_not_count_as_agreement() -> None:
    """Cray's ruling, 2026-08-30 — the whole definition turns on this.

    ``dispatch_replacement_truck`` is tiered *acceptable* by the grader, but the
    question is who has authority to approve the spend, and dispatching a truck
    answers a different one. Counting it as agreement is the lenient reading that
    was explicitly NOT chosen.
    """
    report = score(
        [
            _breach("a", 6_000.0, "escalate"),
            _breach("b", 7_000.0, "dispatch_replacement_truck"),
        ]
    )

    assert report.agreed == 1, (
        "an acceptable-but-different handler was counted as agreement — that is the "
        "lenient reading, and it is the one Cray ruled against"
    )
    assert report.total == 2


def test_items_are_grouped_by_authority_band_not_pooled() -> None:
    """Two amounts in different bands are different cases; the rule says so.

    Pooling them would let a band that agrees perfectly mask one that does not,
    which is exactly the shape the fleet data has: the owner band was 4/4 while the
    band below it split four ways.
    """
    report = score(
        [
            _breach("mid-1", 6_000.0, "echo"),
            _breach("own-1", 50_000.0, "escalate"),
        ]
    )

    assert len(report.bands) == 2, "the two amounts collapsed into one band"
    assert {band.agreed for band in report.bands} == {0, 1}


def test_watch_and_ok_items_are_excluded() -> None:
    """Neither carries adjudicated ground truth for this question.

    Watch items are calibration-only (PLAN-0022 M-2=b) and ok items run no model
    call at all, so scoring either would move the ratio without measuring anything.
    """
    report = score(
        [
            _breach("a", 6_000.0, "escalate"),
            _non_breach("w", "watch"),
            _non_breach("o", "ok"),
        ]
    )

    assert report.total == 1, "a non-breach item was scored"
    assert report.agreed == 1


def test_an_errored_item_counts_against_the_score() -> None:
    """A run must not be able to improve its consistency by failing more often."""
    report = score([_breach("a", 6_000.0, "escalate"), _breach("b", 7_000.0, None)])

    assert report.total == 2, "the errored item was dropped from the denominator"
    assert report.agreed == 1


def test_the_rendering_names_the_diverging_items() -> None:
    """A ratio cannot be acted on; the item ids can.

    Without this the report says three items disagreed and leaves the reader to go
    find which — which is the step that does not happen.

    The ids are distinctive on purpose: an earlier version asserted a bare "b" was
    present, which the rendering satisfies through the word "acceptable" no matter
    what happens to the ids.
    """
    text = render(
        score(
            [
                _breach("item-agreeing", 6_000.0, "escalate"),
                _breach("item-diverging", 7_000.0, "echo"),
            ]
        )
    )

    assert "item-diverging" in text
    assert "echo" in text
    assert "1/2" in text


def test_band_of_places_amounts_on_the_ladder() -> None:
    """The boundaries are inclusive lower bounds, matching the authored ladder.

    One assertion over all four points rather than four asserts: any change to the
    ladder moves whichever boundary comes first, so as separate claims the rest
    were unwitnessable. Compared as a mapping, a misplacement also reports every
    amount it moved instead of stopping at the first.
    """
    placed = {amount: band_of(amount) for amount in (5_000.0, 5_001.0, 30_000.0, 30_001.0)}

    assert placed == {
        5_000.0: "chang-yai (<5,001)",
        5_001.0: "fleet-manager (5,001-30,000)",
        30_000.0: "fleet-manager (5,001-30,000)",
        30_001.0: "owner (>=30,001)",
    }
