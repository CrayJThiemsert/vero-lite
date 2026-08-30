"""Rationale re-grade tests (session 264, route B1) — pure, offline.

Covers the fairness filter (a role phrase the goal never supplies is never
demanded), separator-insensitive value restatement, the
``measured_value == threshold`` ambiguity flag, and a **scenario** case that
writes a realistic dump file — the same record shape the live benchmark emits,
including the non-breach records a real run interleaves — and drives the real
producer (a ``.jsonl`` on disk) into the real consumer (:func:`score_dump`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmarks.procedure_baseline.rationale_regrade import (
    format_report,
    role_vocabulary,
    score_dump,
    score_rationale,
)

_GOAL = (
    "Read each truck's latest quoted repair joined to its own ceiling, then route the "
    "spend to the human authority the quote's size demands — the head mechanic REQUESTS, "
    "the fleet manager or the owner APPROVES (SoD)."
)


def _signals(rationale: str, **overrides: Any) -> Any:
    base: dict[str, Any] = {
        "item_id": "fleet-001",
        "measured_value": 5001.0,
        "threshold": 4000.0,
        "vocabulary": role_vocabulary(_GOAL),
    }
    base.update(overrides)
    return score_rationale(rationale, **base)


def _record(item_id: str, rationale: str, *, disposition: str = "breach") -> dict[str, Any]:
    """One dump record in the shape the live benchmark writes."""
    return {
        "item_id": item_id,
        "vertical": "fleet_maintenance",
        "scenario": {
            "description": "quote above ceiling",
            "entity_type": "Truck",
            "primary_key": "truck-01",
            "measured_value": 5001.0,
            "unit": "THB",
            "threshold": 4000.0,
            "direction": "above",
            "watch_margin": 500.0,
            "distractors": [],
            "context": {"drivable": True, "quotes_obtained": 1},
        },
        "expected": {"disposition": disposition, "canonical_handler": "escalate"},
        "judgment": {
            "title": "escalate",
            "rationale": rationale,
            "suggested_handler": "escalate",
        },
        "graded": True,
    }


class TestRoleVocabulary:
    def test_only_phrases_the_goal_supplies_are_in_scope(self) -> None:
        vocabulary = role_vocabulary(_GOAL)
        assert set(vocabulary) == {"head mechanic", "fleet manager", "owner"}

    def test_a_phrase_absent_from_the_goal_is_never_demanded(self) -> None:
        # "duty engineer" is a candidate phrase, but this goal never supplies it,
        # so a rationale using it earns nothing — the fairness guarantee.
        signals = _signals("Escalate to the duty engineer.")
        assert signals.roles_named == ()
        assert signals.names_role is False

    def test_a_goal_supplied_phrase_is_detected(self) -> None:
        signals = _signals("Route to the fleet manager for approval.")
        assert signals.roles_named == ("fleet manager",)
        assert signals.names_role is True


class TestCarriesContentBar:
    """The ratified pass rule (2026-08-31): naming a role, and nothing else."""

    def test_naming_a_role_passes_the_bar(self) -> None:
        assert _signals("Route to the fleet manager.").carries_content is True

    def test_stating_amount_and_threshold_without_a_role_does_not_pass(self) -> None:
        # The bar is about WHO decides. A rationale rich in numbers but naming
        # nobody leaves the approver without the one fact the bar is for.
        signals = _signals("The 5001 quote exceeds the 4000 ceiling.")
        assert (signals.names_amount, signals.names_threshold) == (True, True)
        assert signals.carries_content is False

    def test_a_role_absent_from_the_goal_does_not_pass_the_bar(self) -> None:
        # The fairness filter caps the bar too: an ungoverned role earns nothing.
        assert _signals("Escalate to the duty engineer.").carries_content is False

    def test_an_empty_rationale_does_not_pass(self) -> None:
        assert _signals("").carries_content is False


class TestValueRestatement:
    def test_plain_integer_form_counts(self) -> None:
        assert _signals("The quote is 5001 THB.").names_amount is True

    def test_decimal_form_counts(self) -> None:
        assert _signals("The quote is 5001.0 THB.").names_amount is True

    def test_thousands_separator_form_counts(self) -> None:
        assert _signals("The quote is 5,001 THB.").names_amount is True

    def test_a_merely_nearby_number_does_not_count(self) -> None:
        assert _signals("The quote is 5002 THB.").names_amount is False

    def test_threshold_is_scored_independently_of_amount(self) -> None:
        signals = _signals("The 5001 quote exceeds the 4000 ceiling.")
        assert (signals.names_amount, signals.names_threshold) == (True, True)

    def test_a_rationale_with_no_numbers_states_neither(self) -> None:
        signals = _signals("Only truck-04 breaches its threshold; others are safe.")
        assert (signals.names_amount, signals.names_threshold) == (False, False)


class TestAmbiguityFlag:
    def test_equal_amount_and_threshold_is_flagged(self) -> None:
        signals = _signals("Quote 5001 is at the ceiling.", threshold=5001.0)
        assert signals.amount_threshold_ambiguous is True

    def test_distinct_amount_and_threshold_is_not_flagged(self) -> None:
        assert _signals("Quote 5001 over 4000.").amount_threshold_ambiguous is False


class TestScoreDumpScenario:
    """Realistic dump on disk → the real consumer. No stubbed seam."""

    def _write_dump(self, tmp_path: Path) -> Path:
        dump = tmp_path / "run.jsonl"
        records = [
            _record(
                "fleet-001",
                "The 5001 THB quote exceeds the 4000 ceiling; the fleet manager must approve.",
            ),
            _record("fleet-002", "Only truck-02 breaches its threshold."),
            # A real run interleaves non-breach records; they carry no spend to justify.
            _record("fleet-003", "Reading is inside the watch band.", disposition="watch"),
        ]
        dump.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
            encoding="utf-8",
        )
        return dump

    def test_only_breach_records_are_scored(self, tmp_path: Path) -> None:
        signals = score_dump(self._write_dump(tmp_path), role_vocabulary(_GOAL))
        assert [s.item_id for s in signals] == ["fleet-001", "fleet-002"]

    def test_signals_are_read_from_the_records_own_facts(self, tmp_path: Path) -> None:
        scored = score_dump(self._write_dump(tmp_path), role_vocabulary(_GOAL))
        signals = {s.item_id: s for s in scored}
        rich = signals["fleet-001"]
        assert (rich.names_amount, rich.names_threshold, rich.roles_named) == (
            True,
            True,
            ("fleet manager",),
        )
        bare = signals["fleet-002"]
        assert (bare.names_amount, bare.names_threshold, bare.names_role) == (False, False, False)

    def test_blank_lines_do_not_break_the_read(self, tmp_path: Path) -> None:
        dump = self._write_dump(tmp_path)
        dump.write_text(dump.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        assert len(score_dump(dump, role_vocabulary(_GOAL))) == 2

    def test_report_tallies_match_the_scored_signals(self, tmp_path: Path) -> None:
        scored = score_dump(self._write_dump(tmp_path), role_vocabulary(_GOAL))
        report = format_report("cell", scored)
        assert "breach items=2" in report
        assert "names_role      : 1/2" in report
        assert "names_amount    : 1/2" in report
        assert "CARRIES_CONTENT : 1/2" in report

    def test_empty_dump_reports_no_breach_records(self, tmp_path: Path) -> None:
        dump = tmp_path / "empty.jsonl"
        dump.write_text("", encoding="utf-8")
        assert "no breach records" in format_report("cell", score_dump(dump, ()))
