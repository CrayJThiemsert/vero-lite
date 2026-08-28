"""Offline tests for the two-model comparison joiner (FDE program phase 1.5).

The scenario test drives the **real producer into the real consumer**: it builds
real :class:`ItemResult` objects, serialises them through the shipped
``run_benchmark._item_record``, writes real JSONL files, and feeds those files to
``compare.load_dump`` / ``build_model_report``. Nothing about the dump shape is
hand-written here, so a change to the producer's record keys reddens this file
rather than passing against a stale copy of the contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.model_compare.compare import (
    DumpError,
    ItemVerdicts,
    RunRef,
    assign_repeats,
    build_model_report,
    collect_verdicts,
    disagreements,
    load_dump,
    parse_run_ref,
    render,
)
from benchmarks.procedure_baseline.grader import HandlerTier
from benchmarks.procedure_baseline.harness import ItemResult
from benchmarks.procedure_baseline.run_benchmark import _item_record
from benchmarks.procedure_baseline.schema import Disposition

_VERTICAL = "energy"


def _result(
    item_id: str,
    *,
    proposal: bool | None,
    graded: bool = True,
    tier: HandlerTier | None = None,
    error: str | None = None,
) -> ItemResult:
    """One graded item, built through the real dataclass the runner emits."""
    return ItemResult(
        item_id,
        _VERTICAL,
        Disposition.BREACH,
        Disposition.BREACH,
        True,
        graded,
        proposal,
        None,
        error=error,
        probe_tier=tier,
        probe_correct=None if tier is None else tier is HandlerTier.CANONICAL,
    )


def _write_dump(path: Path, results: list[ItemResult]) -> Path:
    """Serialise through the SHIPPED record builder, not a local copy of it."""
    path.write_text(
        "\n".join(json.dumps(_item_record(r)) for r in results) + "\n", encoding="utf-8"
    )
    return path


# --- the shape of a dump ------------------------------------------------------


def test_load_dump_reads_records_the_real_runner_wrote(tmp_path: Path) -> None:
    path = _write_dump(tmp_path / "a.jsonl", [_result("energy-001", proposal=True)])

    records = load_dump(path)

    assert [r["item_id"] for r in records] == ["energy-001"]
    assert records[0]["proposal_correct"] is True


def test_a_missing_dump_raises_rather_than_reporting_zero_of_zero(tmp_path: Path) -> None:
    """An empty comparison must not look like a clean one."""
    with pytest.raises(DumpError, match="not found"):
        load_dump(tmp_path / "absent.jsonl")


def test_an_empty_dump_raises(tmp_path: Path) -> None:
    (tmp_path / "empty.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(DumpError, match="empty"):
        load_dump(tmp_path / "empty.jsonl")


def test_a_file_of_the_wrong_shape_raises(tmp_path: Path) -> None:
    (tmp_path / "other.jsonl").write_text('{"not_an_item": 1}\n', encoding="utf-8")
    with pytest.raises(DumpError, match="item_id"):
        load_dump(tmp_path / "other.jsonl")


# --- run specs ----------------------------------------------------------------


def test_parse_run_ref_accepts_model_and_explicit_repeat() -> None:
    assert parse_run_ref("gpt-oss:20b#2=dumps/a.jsonl") == RunRef(
        model="gpt-oss:20b", repeat=2, path=Path("dumps/a.jsonl")
    )


def test_parse_run_ref_rejects_a_spec_without_a_path() -> None:
    with pytest.raises(DumpError, match="model=path"):
        parse_run_ref("gpt-oss:20b")


def test_repeats_are_assigned_per_model_in_order() -> None:
    refs = [
        RunRef("m1", 0, Path("a")),
        RunRef("m2", 0, Path("b")),
        RunRef("m1", 0, Path("c")),
    ]

    assigned = assign_repeats(refs)

    assert [(r.model, r.repeat) for r in assigned] == [("m1", 1), ("m2", 1), ("m1", 2)]


# --- stability: the reason this module exists ---------------------------------


def test_an_item_that_flips_across_repeats_is_named_and_counted(tmp_path: Path) -> None:
    """The load-bearing case: temperature 0 is not deterministic on Ollama."""
    runs = [
        _write_dump(
            tmp_path / f"r{i}.jsonl",
            [
                _result("stable", proposal=True),
                _result("flaky", proposal=verdict),
            ],
        )
        for i, verdict in enumerate([True, False, True], start=1)
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.flipped_items == ["flaky"]
    assert report.flip_rate == 0.5
    assert report.items_stable_basis == 2
    # majority rescues the flaky item (2 of 3 correct), so accuracy is 100%...
    assert report.majority_accuracy == 1.0
    # ...which is exactly why the flip rate is reported beside it.
    assert report.noisy is True


def test_a_unanimous_run_reports_a_zero_flip_rate(tmp_path: Path) -> None:
    runs = [
        _write_dump(tmp_path / f"u{i}.jsonl", [_result("a", proposal=True)]) for i in range(1, 4)
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.flip_rate == 0.0
    assert report.flipped_items == []
    assert report.noisy is False


def test_a_single_repeat_reports_no_flip_rate_rather_than_zero(tmp_path: Path) -> None:
    """One run is unanimous with itself; 0.0% there would read as 'stable'."""
    run = _write_dump(tmp_path / "solo.jsonl", [_result("a", proposal=True)])

    report = build_model_report("m", [load_dump(run)])

    assert report.flip_rate is None
    assert "not measurable (needs 2+ repeats)" in render([report], [])


def test_two_repeats_do_report_a_flip_rate(tmp_path: Path) -> None:
    """Positive control: the None above is the repeat count, not a broken metric."""
    runs = [
        _write_dump(tmp_path / f"pair{i}.jsonl", [_result("a", proposal=True)]) for i in range(1, 3)
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.flip_rate == 0.0


def test_majority_needs_a_strict_majority() -> None:
    """Two repeats that disagree have no majority — it must not silently pass."""
    entry = ItemVerdicts("x", proposal=[True, False])
    assert entry.majority_proposal() is False
    assert entry.flipped() is True


def test_an_ungraded_item_is_excluded_rather_than_counted_wrong(tmp_path: Path) -> None:
    """The non-breach guard items grade ``None`` — never a failure."""
    runs = [
        _write_dump(
            tmp_path / f"g{i}.jsonl",
            [_result("guard", proposal=None, graded=False), _result("real", proposal=True)],
        )
        for i in range(1, 4)
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.items_seen == 2
    assert report.items_stable_basis == 1  # only 'real' can speak to stability
    assert report.majority_accuracy == 1.0


# --- safety signal ------------------------------------------------------------


def test_a_forbidden_handler_in_any_single_repeat_is_surfaced(tmp_path: Path) -> None:
    """Worst-case, not averaged: one dangerous pick in three runs still counts."""
    runs = [
        _write_dump(tmp_path / f"f{i}.jsonl", [_result("a", proposal=True, tier=tier)])
        for i, tier in enumerate(
            [HandlerTier.CANONICAL, HandlerTier.FORBIDDEN, HandlerTier.CANONICAL], start=1
        )
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.forbidden_items == ["a"]
    assert report.probe_tier_totals["forbidden"] == 1
    assert "FORBIDDEN picks  : a" in render([report], [])


def test_no_forbidden_pick_says_none_rather_than_omitting_the_line(tmp_path: Path) -> None:
    """A positive control: absence must be RENDERED, so a blank cannot read as clean."""
    clean = HandlerTier.CANONICAL
    runs = [
        _write_dump(tmp_path / f"c{i}.jsonl", [_result("a", proposal=True, tier=clean)])
        for i in range(1, 4)
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.forbidden_items == []
    assert "FORBIDDEN picks  : none" in render([report], [])


def test_judgment_errors_are_counted_per_repeat(tmp_path: Path) -> None:
    """A structured-output failure is a model property worth comparing."""
    runs = [
        _write_dump(
            tmp_path / f"e{i}.jsonl",
            [_result("a", proposal=False, error="retry budget exhausted" if i == 2 else None)],
        )
        for i in range(1, 4)
    ]

    report = build_model_report("m", [load_dump(p) for p in runs])

    assert report.error_counts == [0, 1, 0]


# --- the comparison itself ----------------------------------------------------


def test_models_are_compared_on_majority_verdicts_not_single_runs(tmp_path: Path) -> None:
    good = [
        load_dump(_write_dump(tmp_path / f"good{i}.jsonl", [_result("shared", proposal=True)]))
        for i in range(1, 4)
    ]
    # The challenger gets it right once out of three — its MAJORITY is wrong.
    bad = [
        load_dump(_write_dump(tmp_path / f"bad{i}.jsonl", [_result("shared", proposal=verdict)]))
        for i, verdict in enumerate([True, False, False], start=1)
    ]

    diffs = disagreements({"good": collect_verdicts(good), "bad": collect_verdicts(bad)})

    assert diffs == [{"item_id": "shared", "majority": {"bad": False, "good": True}}]


def test_agreeing_models_produce_no_disagreement_rows(tmp_path: Path) -> None:
    """Positive control for the test above — the diff list can be empty."""
    runs_a = [
        load_dump(_write_dump(tmp_path / f"a{i}.jsonl", [_result("shared", proposal=True)]))
        for i in range(1, 4)
    ]
    runs_b = [
        load_dump(_write_dump(tmp_path / f"b{i}.jsonl", [_result("shared", proposal=True)]))
        for i in range(1, 4)
    ]

    assert disagreements({"a": collect_verdicts(runs_a), "b": collect_verdicts(runs_b)}) == []


def test_the_report_warns_that_a_gap_under_the_flip_rate_is_not_a_gap(tmp_path: Path) -> None:
    runs = [
        _write_dump(tmp_path / f"w{i}.jsonl", [_result("a", proposal=True)]) for i in range(1, 4)
    ]

    text = render([build_model_report("m", [load_dump(p) for p in runs])], [])

    assert "smaller than either model's flip rate is not a difference" in text
