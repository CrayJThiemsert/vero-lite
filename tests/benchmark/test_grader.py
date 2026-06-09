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
    # payload_contains is advisory; valid_handler is the α probe — neither gates the headline.
    payload_check = next(c for c in grade.checks if c.name == "payload_contains")
    assert payload_check.advisory is True
    handler_check = next(c for c in grade.checks if c.name == "valid_handler")
    assert handler_check.probe is True
    assert grade.probe_passed is True  # suggested_handler 'echo' in valid_handlers ['echo']


def test_wrong_entity_pk_fails() -> None:
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, affected_primary_key="pond-A1"
    )
    judgment = _judgment(affected_entities=[{"object_type": "Pond", "primary_key": "pond-WRONG"}])
    grade = grade_proposal(judgment, expected)
    assert not grade.passed
    assert grade.checks[0].name == "affected_primary_key" and not grade.checks[0].passed


def test_valid_handler_is_an_alpha_probe_not_a_headline_gate() -> None:
    """A wrong handler pick FAILS the α probe but must NOT drag down the β headline —
    in the procedure path the executed handler is fixed by step.handler (ADR-016), so
    the model's handler guess is a reactive-path signal, scored on its own lane."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",  # a scoring field carries the headline
        valid_handlers=["start_emergency_aerator"],
    )
    # right entity, WRONG handler (a near-miss action_type)
    grade = grade_proposal(_judgment(suggested_handler="escalate"), expected)
    assert grade.passed  # headline carried by the entity scoring field
    handler_check = next(c for c in grade.checks if c.name == "valid_handler")
    assert handler_check.probe and not handler_check.passed
    assert grade.probe_passed is False


def test_valid_handler_probe_passes_on_the_correct_action_type() -> None:
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        valid_handlers=["start_emergency_aerator"],
    )
    grade = grade_proposal(_judgment(suggested_handler="start_emergency_aerator"), expected)
    assert grade.passed and grade.probe_passed is True


def test_probe_only_breach_item_has_no_headline_grade() -> None:
    """valid_handlers alone is a probe, not a scoring field — a breach item that
    declares ONLY it cannot pass the headline even when the probe passes (the
    dataset-consistency guard forbids such items)."""
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, valid_handlers=["echo"]
    )
    grade = grade_proposal(_judgment(suggested_handler="echo"), expected)
    assert not grade.passed  # no scoring field declared
    assert grade.probe_passed is True  # but the probe itself passed


def test_payload_subset_match_is_advisory_only() -> None:
    """A payload subset match is recorded as a PASSED advisory check — but, being
    advisory, it does NOT by itself make the headline grade pass (no scoring field)."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        payload_contains={"pond_id": "pond-A1"},
    )
    judgment = _judgment(handler_payload={"pond_id": "pond-A1", "severity": "high"})
    grade = grade_proposal(judgment, expected)
    check = next(c for c in grade.checks if c.name == "payload_contains")
    assert check.advisory and check.passed
    assert not grade.passed  # advisory-only: no scoring field declared


def test_payload_value_mismatch_does_not_fail_the_headline() -> None:
    """A payload mismatch is an advisory miss — it must NOT drag down a proposal
    that passes its scoring fields (free-form payload keys are not a fair gate)."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        payload_contains={"pond_id": "pond-A1"},
    )
    judgment = _judgment(handler_payload={"pond_id": "pond-Z9"})
    grade = grade_proposal(judgment, expected)
    payload_check = next(c for c in grade.checks if c.name == "payload_contains")
    assert payload_check.advisory and not payload_check.passed
    assert grade.passed  # the scoring field (affected_primary_key) carries it


def test_action_keywords_match_is_case_insensitive_substring() -> None:
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, action_keywords=["AERAT"]
    )
    assert grade_proposal(_judgment(title="Begin aeration now"), expected).passed
    expected_miss = Expected(
        disposition=Disposition.BREACH, action_expected=True, action_keywords=["restart"]
    )
    judgment = _judgment(title="Aerate", description="oxygen", rationale="add oxygen now")
    assert not grade_proposal(judgment, expected_miss).passed


def test_action_keywords_match_in_rationale() -> None:
    """The action verb often lands in the rationale field — it must be searched
    (B-β calibration: title/description can be generic while rationale carries the act)."""
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, action_keywords=["aerat"]
    )
    judgment = _judgment(
        title="Pond DO Breach Response",
        description="Recommendation for the event",
        rationale="Aeration is the mandated response after human approval.",
    )
    assert grade_proposal(judgment, expected).passed


def test_no_declared_field_grades_false() -> None:
    """A breach item that declares no objective check cannot pass (authoring guard)."""
    expected = Expected(disposition=Disposition.BREACH, action_expected=True)
    grade = grade_proposal(_judgment(), expected)
    assert not grade.passed
    assert grade.checks == []
