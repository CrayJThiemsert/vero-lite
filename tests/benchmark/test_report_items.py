"""The question-and-answer report: what a reviewer has to be able to read.

The point of the report is that a pass/fail column cannot answer "would this be
usable by the person who has to act on it". These check that the three things
that answer it — the item's own question, the model's own prose, and the grader's
own reason — actually reach the page, and that the two things a reader could be
misled by (an invented question, a silently absent oracle) are marked instead.
"""

from __future__ import annotations

from typing import Any

from benchmarks.procedure_baseline.report_items import render_report

_RATIONALE = "Quote meets the ceiling; the sourcing gate wants three quotes and got one."


def _record(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "item_id": "fleet-001",
        "vertical": "fleet_maintenance",
        "graded": True,
        "proposal_correct": False,
        "probe_tier": "forbidden",
        "error": None,
        "checks": [
            {
                "name": "forbidden_keywords",
                "passed": False,
                "detail": "decoy action verb in title: ['tow']",
                "advisory": False,
                "probe": False,
            }
        ],
        "judgment": {
            "title": "Tow truck-01 to partner garage",
            "description": "d",
            "rationale": _RATIONALE,
            "confidence": 0.92,
            "affected_entities": [{"object_type": "Truck", "primary_key": "truck-01"}],
            "suggested_handler": "tow_to_partner_garage",
            "handler_payload": {"truck_id": "truck-01"},
        },
        "draft": "long reasoning " * 200,
        "thinking": None,
        "judgment_latency_s": 171.9,
        "scenario": {
            "description": "฿5,001 — exactly at the ceiling; inclusive breach, mid band.",
            "entity_type": "Truck",
            "primary_key": "truck-01",
            "measured_value": 5001.0,
            "unit": "THB",
            "threshold": 5001.0,
            "direction": "above",
            "watch_margin": 500.0,
            "distractors": [],
            "context": {"drivable": True},
        },
        "expected": {
            "disposition": "breach",
            "action_expected": True,
            "canonical_handler": "escalate",
            "forbidden_keywords": ["tow"],
        },
        "calls": [
            {
                "role": "reasoning",
                "done_reason": "stop",
                "eval_count": 1893,
                "prompt_eval_count": 1120,
                "content_chars": 7528,
                "thinking_chars": None,
                "truncated": False,
            }
        ],
    }
    record.update(overrides)
    return record


def test_the_report_carries_the_question_the_prose_and_the_reason() -> None:
    """All three, in one place — the whole reason the report exists.

    A verdict alone cannot be reviewed for usability: it says the model was wrong
    without saying what it was asked or what it actually wrote.
    """
    report = render_report([_record()])

    assert "฿5,001 — exactly at the ceiling" in report, "the QUESTION is missing"
    assert _RATIONALE in report, "the model's own prose is missing"
    assert "decoy action verb in title: ['tow']" in report, "the grader's REASON is missing"


def test_a_truncated_call_is_flagged_at_the_top_of_the_report() -> None:
    """A reader must meet the caveat before the content, not after it."""
    cut = _record()
    cut["calls"][0]["truncated"] = True
    cut["calls"][0]["done_reason"] = "length"

    report = render_report([cut])
    head = report[: report.index("## `fleet-001`")]

    # The COUNT, not the bare phrase. "No call hit the generation cap." contains
    # "hit the generation cap", so the loose form is satisfied by the clean
    # header and cannot distinguish the two states at all — measured, by a probe
    # that flipped the header to clean and still saw this assertion pass.
    assert "**1 call(s) hit the generation cap**" in head, (
        "the cap warning is not in the report header, so a reader reaches the "
        "items believing the reasoning behind them was complete"
    )


def test_a_clean_report_says_so_rather_than_staying_silent() -> None:
    """The positive control for the test above — and a claim in its own right.

    Silence would be indistinguishable from a report that cannot detect
    truncation at all.
    """
    report = render_report([_record()])

    assert "No call hit the generation cap." in report
    assert "hit the generation cap** —" not in report


def test_an_unrecorded_question_is_marked_absent_not_invented() -> None:
    """A dump written before the question was carried must not be papered over."""
    report = render_report([_record(scenario=None, expected=None)])

    assert "not recorded in this dump" in report
    assert "฿5,001" not in report, "a question was rendered for a record that has none"
    # Not vacuous: the ANSWER still renders, so the absence above is the missing
    # question rather than a record that failed to render at all.
    assert _RATIONALE in report


def test_a_backfilled_question_is_marked_as_backfilled() -> None:
    """Reconstructed from a file that may have changed is not what the run wrote.

    The same rendered question is honest in one case and misleading in the other;
    only the mark tells them apart.
    """
    plain = render_report([_record()])
    backfilled = render_report([_record()], backfilled_ids=frozenset({"fleet-001"}))

    assert "backfilled from the dataset" in backfilled
    assert "backfilled from the dataset" not in plain


def test_a_missing_done_reason_is_spelled_out_not_shown_as_a_clean_stop() -> None:
    """An absent oracle must read as absent.

    Rendering nothing there would look identical to a call that ended cleanly,
    which is the "zero from silence" failure in the run report one layer up.
    """
    unmeasured = _record()
    unmeasured["calls"][0]["done_reason"] = None

    report = render_report([unmeasured])

    assert "no done_reason reported" in report
    # The control: with the field present, the report names the real reason
    # instead, so the string above is a genuine branch and not a constant.
    assert "no done_reason reported" not in render_report([_record()])


def test_the_draft_is_folded_but_its_true_length_is_stated() -> None:
    """Folding must not misrepresent how much reasoning there was."""
    report = render_report([_record()], max_draft_chars=100)

    assert "Reasoning draft — 3,000 characters" in report
    assert "more characters elided" in report
