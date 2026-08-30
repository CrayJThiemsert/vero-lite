"""Rationale-lane tests (session 264, route B2) — pure, offline.

The lane's whole safety property is **isolation**: it must be visible in its own
field and in the summary, and it must be incapable of moving β or α. Both halves
are asserted here, including the negative one that a green-only suite would miss —
a rationale that FAILS while the headline stays PASS.

Also covers the no-goal default (every offline call site), which is what makes
every β/α figure published before this lane existed still comparable.
"""

from __future__ import annotations

from typing import Any

from benchmarks.procedure_baseline.grader import (
    grade_proposal,
    role_vocabulary,
)
from benchmarks.procedure_baseline.harness import ItemResult, Summary, summarize
from benchmarks.procedure_baseline.schema import Disposition, Expected, Scenario
from services.engine.llm.structured import LlmJudgment

_GOAL = (
    "Judge the quote against that per-truck ceiling, then route the spend to the human "
    "authority the quote's size demands — the head mechanic REQUESTS, the fleet manager "
    "or the owner APPROVES (SoD)."
)


def _judgment(**overrides: Any) -> LlmJudgment:
    base: dict[str, Any] = {
        "title": "escalate the repair spend",
        "description": "route for approval",
        "rationale": "The quote breaches the ceiling.",
        "confidence": 0.9,
        "affected_entities": [{"object_type": "Truck", "primary_key": "truck-01"}],
        "suggested_handler": "escalate",
        "handler_payload": {},
    }
    base.update(overrides)
    return LlmJudgment.model_validate(base)


def _expected(**overrides: Any) -> Expected:
    base: dict[str, Any] = {
        "disposition": "breach",
        "action_expected": True,
        "affected_primary_key": "truck-01",
        "action_keywords": ["escalat"],
        "canonical_handler": "escalate",
    }
    base.update(overrides)
    return Expected(**base)


class TestVocabularyDerivation:
    def test_no_goal_yields_no_vocabulary(self) -> None:
        assert role_vocabulary(None) == ()

    def test_empty_goal_yields_no_vocabulary(self) -> None:
        assert role_vocabulary("") == ()

    def test_only_phrases_the_goal_supplies_are_in_scope(self) -> None:
        assert set(role_vocabulary(_GOAL)) == {"head mechanic", "fleet manager", "owner"}


class TestLaneEmission:
    def test_without_a_goal_no_rationale_check_is_emitted(self) -> None:
        grade = grade_proposal(_judgment(), _expected())
        assert grade.rationale_passed is None
        assert [c.name for c in grade.checks if c.rationale] == []

    def test_with_a_goal_the_check_is_emitted_and_scored(self) -> None:
        grade = grade_proposal(
            _judgment(rationale="Route to the fleet manager for approval."),
            _expected(),
            goal=_GOAL,
        )
        assert grade.rationale_passed is True
        named = [c for c in grade.checks if c.rationale]
        assert [c.name for c in named] == ["names_approver"]
        assert "fleet manager" in named[0].detail

    def test_a_rationale_naming_nobody_fails_the_lane(self) -> None:
        grade = grade_proposal(_judgment(), _expected(), goal=_GOAL)
        assert grade.rationale_passed is False

    def test_a_role_the_goal_never_supplies_earns_nothing(self) -> None:
        grade = grade_proposal(
            _judgment(rationale="Escalate to the duty engineer."), _expected(), goal=_GOAL
        )
        assert grade.rationale_passed is False


class TestLaneIsolation:
    """The load-bearing property: the lane can never move β or α."""

    def test_a_failing_rationale_leaves_the_headline_passing(self) -> None:
        # Rationale names nobody, so the lane fails; every scoring field still passes.
        grade = grade_proposal(_judgment(), _expected(), goal=_GOAL)
        assert grade.rationale_passed is False
        assert grade.passed is True

    def test_a_failing_rationale_leaves_the_probe_passing(self) -> None:
        grade = grade_proposal(_judgment(), _expected(), goal=_GOAL)
        assert grade.rationale_passed is False
        assert grade.probe_passed is True

    def test_the_rationale_check_is_excluded_from_the_scoring_lane(self) -> None:
        grade = grade_proposal(_judgment(), _expected(), goal=_GOAL)
        scoring = [c for c in grade.checks if not c.advisory and not c.probe and not c.rationale]
        assert "names_approver" not in {c.name for c in scoring}

    def test_supplying_a_goal_does_not_change_beta_or_alpha(self) -> None:
        without = grade_proposal(_judgment(), _expected())
        with_goal = grade_proposal(_judgment(), _expected(), goal=_GOAL)
        assert (without.passed, without.probe_passed) == (with_goal.passed, with_goal.probe_passed)


def _result(rationale_correct: bool | None) -> ItemResult:
    return ItemResult(
        item_id="fleet-001",
        vertical="fleet_maintenance",
        disposition_expected=Disposition.BREACH,
        disposition_actual=Disposition.BREACH,
        disposition_correct=True,
        graded=True,
        proposal_correct=True,
        grade=None,
        rationale_correct=rationale_correct,
    )


class TestSummaryAggregation:
    """The lane reaches a reported number — an unaggregated lane is an orphan."""

    def test_the_lane_is_tallied_over_items_that_carry_it(self) -> None:
        summary: Summary = summarize([_result(True), _result(False), _result(True)])
        assert (summary.rationale_graded, summary.rationale_correct) == (3, 2)
        assert summary.rationale_accuracy is not None
        assert abs(summary.rationale_accuracy - 2 / 3) < 1e-9

    def test_items_without_the_lane_are_excluded_from_the_denominator(self) -> None:
        summary = summarize([_result(True), _result(None), _result(None)])
        assert (summary.rationale_graded, summary.rationale_correct) == (1, 1)

    def test_a_run_with_no_goal_reports_no_lane_at_all(self) -> None:
        summary = summarize([_result(None), _result(None)])
        assert summary.rationale_graded == 0
        assert summary.rationale_accuracy is None

    def test_the_lane_does_not_disturb_the_headline_tally(self) -> None:
        summary = summarize([_result(False), _result(False)])
        assert summary.rationale_correct == 0
        assert summary.headline_correct == 2


class TestScenarioThroughTheRealSchema:
    """Drive a real Scenario + real Expected + real LlmJudgment into the real grader."""

    def test_a_realistic_breach_item_scores_all_four_lanes(self) -> None:
        scenario = Scenario(
            event_id="evt-1",
            entity_type="Truck",
            primary_key="truck-01",
            measured_value=5001.0,
            unit="THB",
            threshold=4000.0,
            direction="above",
            watch_margin=500.0,
        )
        assert scenario.measured_value > scenario.threshold
        grade = grade_proposal(
            _judgment(
                rationale=(
                    "The 5001 THB quote is above the truck's ceiling, so the fleet manager "
                    "must approve before any spend."
                )
            ),
            _expected(payload_contains={"amount": 5001.0}),
            goal=_GOAL,
        )
        lanes = {
            "scoring": grade.passed,
            "probe": grade.probe_passed,
            "rationale": grade.rationale_passed,
        }
        assert lanes == {"scoring": True, "probe": True, "rationale": True}
        # advisory is recorded and stays out of every verdict above
        advisory = [c for c in grade.checks if c.advisory]
        assert [c.name for c in advisory] == ["payload_contains"]
