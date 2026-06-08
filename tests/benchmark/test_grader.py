"""Grader unit tests (PLAN-0019 B-β) — pure, offline.

Covers the deterministic disposition (breach/watch/ok across both directions, the
inclusive boundary, and the no-watch-band case) and the objective LLM-proposal
field checks (entity PK, handler allowlist, payload subset, action-class keywords,
and the no-declared-field guard).
"""

from __future__ import annotations

from typing import Any

from benchmarks.procedure_baseline.grader import classify_disposition, grade_proposal
from benchmarks.procedure_baseline.schema import Disposition, Expected, Scenario
from services.engine.llm.structured import LlmJudgment


def _scenario(**overrides: Any) -> Scenario:
    base: dict[str, Any] = {
        "event_id": "evt-1",
        "entity_type": "Pond",
        "primary_key": "pond-A1",
        "measured_value": 2.1,
        "unit": "mg/L",
        "threshold": 4.0,
        "direction": "below",
        "watch_margin": 1.0,
    }
    base.update(overrides)
    return Scenario(**base)


def _judgment(**overrides: Any) -> LlmJudgment:
    base: dict[str, Any] = {
        "title": "Start emergency aerator on pond-A1",
        "description": "DO crashed below the 4 mg/L floor; aerate to recover oxygen.",
        "rationale": "A breach reading needs immediate aeration.",
        "confidence": 0.9,
        "affected_entities": [{"object_type": "Pond", "primary_key": "pond-A1"}],
        "suggested_handler": "echo",
        "handler_payload": {"pond_id": "pond-A1"},
    }
    base.update(overrides)
    return LlmJudgment.model_validate(base)


# --- classify_disposition (deterministic) ------------------------------------


def test_below_breach_is_inclusive_at_the_floor() -> None:
    assert classify_disposition(_scenario(measured_value=4.0)) is Disposition.BREACH
    assert classify_disposition(_scenario(measured_value=3.9)) is Disposition.BREACH


def test_below_watch_band_just_above_the_floor() -> None:
    assert classify_disposition(_scenario(measured_value=4.5)) is Disposition.WATCH
    assert classify_disposition(_scenario(measured_value=5.0)) is Disposition.WATCH  # upper edge


def test_below_ok_above_the_watch_band() -> None:
    assert classify_disposition(_scenario(measured_value=5.1)) is Disposition.OK


def test_above_breach_is_inclusive_at_the_ceiling() -> None:
    s = _scenario(direction="above", threshold=90.0, watch_margin=5.0)
    assert classify_disposition(s.model_copy(update={"measured_value": 90.0})) is Disposition.BREACH
    assert classify_disposition(s.model_copy(update={"measured_value": 96.5})) is Disposition.BREACH


def test_above_watch_and_ok_bands() -> None:
    s = _scenario(direction="above", threshold=90.0, watch_margin=5.0)
    assert classify_disposition(s.model_copy(update={"measured_value": 85.0})) is Disposition.WATCH
    assert classify_disposition(s.model_copy(update={"measured_value": 89.9})) is Disposition.WATCH
    assert classify_disposition(s.model_copy(update={"measured_value": 84.9})) is Disposition.OK


def test_no_watch_margin_collapses_the_band() -> None:
    """With no watch_margin, a not-breach reading is always ok."""
    s = _scenario(watch_margin=None, measured_value=4.5)
    assert classify_disposition(s) is Disposition.OK


# --- grade_proposal (LLM-graded objective fields) ----------------------------


def test_all_declared_fields_pass() -> None:
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        valid_handlers=["echo"],
        payload_contains={"pond_id": "pond-A1"},
        action_keywords=["aerat"],
    )
    grade = grade_proposal(_judgment(), expected)
    assert grade.passed
    assert {c.name for c in grade.checks} == {
        "affected_primary_key",
        "valid_handler",
        "payload_contains",
        "action_keywords",
    }


def test_wrong_entity_pk_fails() -> None:
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, affected_primary_key="pond-A1"
    )
    judgment = _judgment(affected_entities=[{"object_type": "Pond", "primary_key": "pond-WRONG"}])
    grade = grade_proposal(judgment, expected)
    assert not grade.passed
    assert grade.checks[0].name == "affected_primary_key" and not grade.checks[0].passed


def test_handler_outside_allowlist_fails() -> None:
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, valid_handlers=["echo"]
    )
    grade = grade_proposal(_judgment(suggested_handler="rogue"), expected)
    assert not grade.passed


def test_payload_subset_match_passes_with_extra_keys() -> None:
    """A subset match tolerates extra payload keys the model adds."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        payload_contains={"pond_id": "pond-A1"},
    )
    judgment = _judgment(handler_payload={"pond_id": "pond-A1", "severity": "high"})
    assert grade_proposal(judgment, expected).passed


def test_payload_value_mismatch_fails() -> None:
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        payload_contains={"pond_id": "pond-A1"},
    )
    judgment = _judgment(handler_payload={"pond_id": "pond-Z9"})
    assert not grade_proposal(judgment, expected).passed


def test_action_keywords_match_is_case_insensitive_substring() -> None:
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, action_keywords=["AERAT"]
    )
    assert grade_proposal(_judgment(title="Begin aeration now"), expected).passed
    expected_miss = Expected(
        disposition=Disposition.BREACH, action_expected=True, action_keywords=["restart"]
    )
    assert not grade_proposal(_judgment(title="Aerate", description="oxygen"), expected_miss).passed


def test_no_declared_field_grades_false() -> None:
    """A breach item that declares no objective check cannot pass (authoring guard)."""
    expected = Expected(disposition=Disposition.BREACH, action_expected=True)
    grade = grade_proposal(_judgment(), expected)
    assert not grade.passed
    assert grade.checks == []
