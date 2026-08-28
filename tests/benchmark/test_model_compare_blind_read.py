"""Offline tests for the blind prose-read instrument (FDE program phase 1.5).

Like the joiner's tests, these drive the SHIPPED ``run_benchmark._item_record``
into the reader, so the dump contract is never a hand-copied duplicate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.model_compare.blind_read import (
    SheetError,
    build_sheet,
    parse_sheet,
    render_score,
    score,
    side_for,
)
from benchmarks.procedure_baseline.harness import ItemResult
from benchmarks.procedure_baseline.run_benchmark import _item_record
from benchmarks.procedure_baseline.schema import Disposition
from services.engine.llm.structured import EntityRef, LlmJudgment

_VERTICAL = "energy"


def _judgment(title: str, handler: str = "restart", key: str = "asset-E01") -> LlmJudgment:
    return LlmJudgment(
        title=title,
        description=f"{title} — description",
        rationale=f"{title} — rationale",
        confidence=0.9,
        affected_entities=[EntityRef(object_type="Asset", primary_key=key, title=key)],
        suggested_handler=handler,
    )


def _records(items: dict[str, LlmJudgment | None]) -> list[dict[str, object]]:
    """Serialise through the shipped record builder."""
    out = []
    for item_id, judgment in items.items():
        result = ItemResult(
            item_id,
            _VERTICAL,
            Disposition.BREACH,
            Disposition.BREACH,
            True,
            True,
            True,
            None,
            judgment=judgment,
        )
        out.append(_item_record(result))
    return out


def _dump(path: Path, items: dict[str, LlmJudgment | None]) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in _records(items)) + "\n", encoding="utf-8")
    return path


# --- anonymisation ------------------------------------------------------------


def test_the_sheet_never_names_a_model() -> None:
    """The whole point: a rater must not be able to read the answer off the page."""
    left = _records({"energy-001": _judgment("Restart it")})
    right = _records({"energy-001": _judgment("Shut it down", handler="isolate")})

    sheet, _ = build_sheet("gpt-oss:20b", left, "qwen3.8:27b-mtp-q8_0", right, seed=1)

    assert "gpt-oss" not in sheet
    assert "qwen" not in sheet


def test_the_key_records_which_side_each_model_took() -> None:
    left = _records({"energy-001": _judgment("Restart it")})
    right = _records({"energy-001": _judgment("Shut it down")})

    _, key = build_sheet("m-left", left, "m-right", right, seed=1)

    pairing = key["pairings"][0]
    assert {pairing["side_a"], pairing["side_b"]} == {"m-left", "m-right"}


def test_sides_are_shuffled_per_item_not_fixed_per_run() -> None:
    """A rater who spots that A is always the same model is no longer blind."""
    ids = [f"energy-{n:03d}" for n in range(1, 41)]
    left = _records({i: _judgment("left") for i in ids})
    right = _records({i: _judgment("right") for i in ids})

    _, key = build_sheet("m-left", left, "m-right", right, seed=7)

    a_sides = [p["side_a"] for p in key["pairings"]]
    assert "m-left" in a_sides
    assert "m-right" in a_sides


def test_side_assignment_is_reproducible_from_the_seed() -> None:
    assert side_for(42, "energy-001") == side_for(42, "energy-001")


def test_a_different_seed_can_move_an_item() -> None:
    """Positive control for the test above — the assignment is not a constant."""
    assert any(side_for(s, "energy-001") != side_for(1, "energy-001") for s in range(2, 60))


# --- what the sheet includes --------------------------------------------------


def test_only_items_with_a_judgment_on_both_sides_are_paired() -> None:
    """A pair with one empty side invites a preference driven by absence."""
    left = _records({"both": _judgment("a"), "left-only": _judgment("b")})
    right = _records({"both": _judgment("c"), "left-only": None})

    sheet, key = build_sheet("m-left", left, "m-right", right, seed=1)

    assert [p["item_id"] for p in key["pairings"]] == ["both"]
    assert "left-only" not in sheet


def test_no_shared_item_raises_rather_than_producing_an_empty_sheet() -> None:
    left = _records({"a": _judgment("x")})
    right = _records({"b": _judgment("y")})

    with pytest.raises(SheetError, match="share no item"):
        build_sheet("m-left", left, "m-right", right, seed=1)


def test_the_handler_is_shown_beside_the_prose() -> None:
    """Criterion 3 cannot be judged blind to the action the record carries."""
    left = _records({"energy-001": _judgment("Shutdown it", handler="restart")})
    right = _records({"energy-001": _judgment("Restart it", handler="restart")})

    sheet, _ = build_sheet("m-left", left, "m-right", right, seed=1)

    assert "- handler: restart" in sheet


# --- parsing a filled sheet ---------------------------------------------------


def test_a_filled_sheet_parses_to_verdicts() -> None:
    text = "### item a\n\nVERDICT: A\n\n### item b\n\nVERDICT: TIE\n"
    assert parse_sheet(text) == {"a": "A", "b": "TIE"}


def test_a_blank_verdict_is_unfilled_not_a_tie() -> None:
    """A tie is a judgement; a blank is a missing one. They must not merge."""
    assert parse_sheet("### item a\n\nVERDICT: \n")["a"] == "UNFILLED"


def test_an_unrecognised_verdict_raises() -> None:
    with pytest.raises(SheetError, match="unrecognised verdict"):
        parse_sheet("### item a\n\nVERDICT: maybe\n")


def test_a_missing_verdict_line_raises_rather_than_shifting_answers() -> None:
    """Zip-by-position would silently attribute item b's verdict to item a."""
    with pytest.raises(SheetError, match="1 VERDICT"):
        parse_sheet("### item a\n\n### item b\n\nVERDICT: A\n")


# --- scoring back to models ---------------------------------------------------


def test_verdicts_map_back_through_the_key() -> None:
    key = {
        "left_model": "m-left",
        "right_model": "m-right",
        "pairings": [
            {"item_id": "a", "side_a": "m-left", "side_b": "m-right"},
            {"item_id": "b", "side_a": "m-right", "side_b": "m-left"},
        ],
    }

    # Both verdicts say "A", but A is a different model on each item.
    result = score({"a": "A", "b": "A"}, key)

    assert result["preferences"] == {"m-left": 1, "m-right": 1}


def test_unfilled_items_are_excluded_from_the_denominator() -> None:
    key = {
        "left_model": "m-left",
        "right_model": "m-right",
        "pairings": [{"item_id": "a", "side_a": "m-left", "side_b": "m-right"}],
    }

    result = score({"a": "UNFILLED"}, key)

    assert result["scored_n"] == 0
    assert result["unfilled"] == ["a"]
    assert result["preferences"] == {"m-left": 0, "m-right": 0}


def test_an_item_the_key_does_not_know_raises() -> None:
    key = {"left_model": "l", "right_model": "r", "pairings": []}
    with pytest.raises(SheetError, match="does not know"):
        score({"ghost": "A"}, key)


def test_the_output_refuses_to_render_a_percentage() -> None:
    key = {
        "left_model": "m-left",
        "right_model": "m-right",
        "pairings": [{"item_id": "a", "side_a": "m-left", "side_b": "m-right"}],
    }

    text = render_score(score({"a": "A"}, key))

    assert "preferred on 1 of 1 scored items" in text
    assert "%" not in text
