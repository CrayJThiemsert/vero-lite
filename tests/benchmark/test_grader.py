"""Grader unit tests (PLAN-0019 B-β; tiered α probe per PLAN-0022 Step 1) — pure,
offline.

Covers the deterministic disposition (breach/watch/ok across both directions, the
inclusive boundary, and the no-watch-band case — delegated to the engine's
``classify_verdict``, asserted here as non-regression) and the objective
LLM-proposal field checks (entity PK, the tiered handler probe, payload subset,
action-class keywords, and the no-declared-field guard).
"""

from __future__ import annotations

from typing import Any

from benchmarks.procedure_baseline.grader import (
    HandlerTier,
    classify_disposition,
    classify_handler_tier,
    declares_handler_tiers,
    grade_proposal,
    grade_watch_proposal,
)
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
        canonical_handler="echo",
        payload_contains={"pond_id": "pond-A1"},
        action_keywords=["aerat"],
    )
    grade = grade_proposal(_judgment(), expected)
    assert grade.passed
    assert {c.name for c in grade.checks} == {
        "affected_primary_key",
        "handler_tier",
        "payload_contains",
        "action_keywords",
    }
    # payload_contains is advisory; handler_tier is the α probe — neither gates the headline.
    payload_check = next(c for c in grade.checks if c.name == "payload_contains")
    assert payload_check.advisory is True
    handler_check = next(c for c in grade.checks if c.name == "handler_tier")
    assert handler_check.probe is True
    assert grade.probe_passed is True  # suggested_handler 'echo' == canonical_handler
    assert grade.handler_tier is HandlerTier.CANONICAL


def test_wrong_entity_pk_fails() -> None:
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, affected_primary_key="pond-A1"
    )
    judgment = _judgment(affected_entities=[{"object_type": "Pond", "primary_key": "pond-WRONG"}])
    grade = grade_proposal(judgment, expected)
    assert not grade.passed
    assert grade.checks[0].name == "affected_primary_key" and not grade.checks[0].passed


def test_unicode_hyphen_in_entity_pk_normalizes_to_a_match() -> None:
    """The energy-007 gold case (B-6 calibration, Cray-ratified 2026-06-12): the
    model emitted the dataset key 'asset-E07' with U+2011 NON-BREAKING HYPHEN in
    place of the ASCII hyphen — three dump-verified occurrences across runs. A
    glyph variant is not an entity-identity error: key comparison normalizes
    the Unicode hyphen family to ASCII '-'."""
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, affected_primary_key="asset-E07"
    )
    judgment = _judgment(
        affected_entities=[{"object_type": "Asset", "primary_key": "asset" + chr(0x2011) + "E07"}]
    )
    grade = grade_proposal(judgment, expected)
    assert grade.passed
    check = next(c for c in grade.checks if c.name == "affected_primary_key")
    assert check.passed


def test_unicode_hyphen_does_not_mask_a_real_pk_mismatch() -> None:
    """Normalization fixes the glyph, not the identity — a wrong key with a
    Unicode hyphen still fails."""
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, affected_primary_key="asset-E07"
    )
    judgment = _judgment(
        affected_entities=[{"object_type": "Asset", "primary_key": "asset" + chr(0x2011) + "E08"}]
    )
    grade = grade_proposal(judgment, expected)
    assert not grade.passed


def test_unicode_hyphen_decoy_still_trips_the_precision_check() -> None:
    """Normalization applies to forbidden_primary_keys too: naming a decoy
    sibling with a Unicode hyphen still counts as naming the decoy."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="asset-E07",
        forbidden_primary_keys=["asset-E08"],
    )
    judgment = _judgment(
        affected_entities=[
            {"object_type": "Asset", "primary_key": "asset-E07"},
            {"object_type": "Asset", "primary_key": "asset" + chr(0x2011) + "E08"},
        ]
    )
    grade = grade_proposal(judgment, expected)
    assert not grade.passed
    check = next(c for c in grade.checks if c.name == "forbidden_primary_keys")
    assert not check.passed


def test_handler_tier_is_an_alpha_probe_not_a_headline_gate() -> None:
    """A wrong handler pick FAILS the α probe but must NOT drag down the β headline —
    in the procedure path the executed handler is fixed by step.handler (ADR-016), so
    the model's handler guess is a reactive-path signal, scored on its own lane."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",  # a scoring field carries the headline
        canonical_handler="start_emergency_aerator",
    )
    # right entity, WRONG handler (a near-miss action_type, neither canonical nor acceptable)
    grade = grade_proposal(_judgment(suggested_handler="escalate"), expected)
    assert grade.passed  # headline carried by the entity scoring field
    handler_check = next(c for c in grade.checks if c.name == "handler_tier")
    assert handler_check.probe and not handler_check.passed
    assert grade.probe_passed is False
    assert grade.handler_tier is HandlerTier.OTHER


def test_handler_tier_probe_passes_on_the_canonical_action_type() -> None:
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        canonical_handler="start_emergency_aerator",
    )
    grade = grade_proposal(_judgment(suggested_handler="start_emergency_aerator"), expected)
    assert grade.passed and grade.probe_passed is True
    assert grade.handler_tier is HandlerTier.CANONICAL


def test_handler_tier_probe_passes_on_an_acceptable_alternative() -> None:
    """PLAN-0022 Step 1: a benign defensible alternative passes the probe as
    'acceptable' — distinguished from canonical in the tier, identical in
    pass/fail (the PLAN-0020 SD-1 'inspect is benign' finding made first-class)."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        canonical_handler="start_emergency_aerator",
        acceptable_handlers=["increase_water_exchange"],
    )
    grade = grade_proposal(_judgment(suggested_handler="increase_water_exchange"), expected)
    assert grade.passed and grade.probe_passed is True
    assert grade.handler_tier is HandlerTier.ACCEPTABLE


def test_handler_tier_flags_a_forbidden_pick_explicitly() -> None:
    """A handler guess containing a forbidden_keywords near-miss classifies
    'forbidden' (fails the probe, named explicitly in reporting — SD-4=a: derived
    from the existing keywords, not a new dataset tier)."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        canonical_handler="hold",
        acceptable_handlers=["inspect"],
        forbidden_keywords=["expedite", "reroute"],
    )
    grade = grade_proposal(_judgment(suggested_handler="expedite_shipment"), expected)
    handler_check = next(c for c in grade.checks if c.name == "handler_tier")
    assert handler_check.probe and not handler_check.passed
    assert grade.probe_passed is False
    assert grade.handler_tier is HandlerTier.FORBIDDEN


def test_classify_handler_tier_prefers_canonical_over_acceptable() -> None:
    """Tier precedence: an exact canonical match classifies canonical even if the
    same handler is (mis-)listed under acceptable_handlers."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        canonical_handler="hold",
        acceptable_handlers=["hold", "inspect"],
    )
    assert classify_handler_tier("hold", expected) is HandlerTier.CANONICAL


def test_classify_handler_tier_with_acceptable_only() -> None:
    """An item may declare only acceptable_handlers (no single canonical pick);
    the probe still grades, with no canonical tier reachable."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        acceptable_handlers=["inspect", "hold"],
    )
    assert classify_handler_tier("inspect", expected) is HandlerTier.ACCEPTABLE
    assert classify_handler_tier("restart", expected) is HandlerTier.OTHER
    grade = grade_proposal(_judgment(suggested_handler="inspect"), expected)
    assert grade.probe_passed is True and grade.handler_tier is HandlerTier.ACCEPTABLE


def test_probe_only_breach_item_has_no_headline_grade() -> None:
    """The handler tier alone is a probe, not a scoring field — a breach item that
    declares ONLY it cannot pass the headline even when the probe passes (the
    dataset-consistency guard forbids such items)."""
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, canonical_handler="echo"
    )
    grade = grade_proposal(_judgment(suggested_handler="echo"), expected)
    assert not grade.passed  # no scoring field declared
    assert grade.probe_passed is True  # but the probe itself passed


def test_no_probe_field_means_no_handler_tier() -> None:
    """An item that declares neither canonical_handler nor acceptable_handlers has
    no probe lane: probe_passed and handler_tier are both None."""
    expected = Expected(
        disposition=Disposition.BREACH, action_expected=True, affected_primary_key="pond-A1"
    )
    grade = grade_proposal(_judgment(), expected)
    assert grade.probe_passed is None
    assert grade.handler_tier is None


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


def test_forbidden_primary_keys_fails_when_a_decoy_is_named() -> None:
    """PR2 precision: naming a decoy sibling fails the headline (over-inclusion)."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        forbidden_primary_keys=["pond-A2", "pond-A3"],
    )
    judgment = _judgment(
        affected_entities=[
            {"object_type": "Pond", "primary_key": "pond-A1"},
            {"object_type": "Pond", "primary_key": "pond-A2"},  # a decoy
        ]
    )
    grade = grade_proposal(judgment, expected)
    assert not grade.passed
    check = next(c for c in grade.checks if c.name == "forbidden_primary_keys")
    assert not check.passed and not check.advisory and not check.probe


def test_forbidden_primary_keys_passes_when_only_the_breach_is_named() -> None:
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        forbidden_primary_keys=["pond-A2", "pond-A3"],
    )
    grade = grade_proposal(_judgment(), expected)  # default names only pond-A1
    assert grade.passed
    assert next(c for c in grade.checks if c.name == "forbidden_primary_keys").passed


def test_forbidden_keywords_fails_when_the_decoy_verb_is_the_title_action() -> None:
    """PR2 precision: recommending the near-miss action (verb in the TITLE) fails."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        forbidden_keywords=["feed"],
    )
    grade = grade_proposal(_judgment(title="Adjust feeding schedule for pond-A1"), expected)
    assert not grade.passed
    assert not next(c for c in grade.checks if c.name == "forbidden_keywords").passed


def test_forbidden_keywords_passes_when_the_decoy_verb_only_appears_in_the_body() -> None:
    """The decoy verb may appear in description/rationale (the model ruling it out) —
    only the TITLE (the recommended action) is checked."""
    expected = Expected(
        disposition=Disposition.BREACH,
        action_expected=True,
        affected_primary_key="pond-A1",
        action_keywords=["aerat"],
        forbidden_keywords=["feed"],
    )
    judgment = _judgment(
        title="Start emergency aerator on pond-A1",
        description="Aerate now; do NOT feed during the oxygen crash.",
        rationale="Feeding would worsen the crash, so hold feed and aerate.",
    )
    grade = grade_proposal(judgment, expected)
    assert grade.passed  # 'feed' is in the body, not the title
    assert next(c for c in grade.checks if c.name == "forbidden_keywords").passed


def test_no_declared_field_grades_false() -> None:
    """A breach item that declares no objective check cannot pass (authoring guard)."""
    expected = Expected(disposition=Disposition.BREACH, action_expected=True)
    grade = grade_proposal(_judgment(), expected)
    assert not grade.passed
    assert grade.checks == []


# --- grade_watch_proposal (PLAN-0022 Phase-3 watch-tier lane — M-1/M-2) -------


def test_watch_grade_unscored_when_no_tiers_declared() -> None:
    """M-2=b calibration-first: a watch item with no handler ground truth grades
    UNSCORED — the handler is recorded for the distribution report, tier/passed
    stay None (report-don't-fail)."""
    expected = Expected(disposition=Disposition.WATCH, action_expected=False)
    assert not declares_handler_tiers(expected)
    grade = grade_watch_proposal(_judgment(suggested_handler="inspect"), expected)
    assert grade.handler == "inspect"
    assert grade.tier is None
    assert grade.passed is None


def test_watch_grade_scored_canonical_and_acceptable_pass() -> None:
    """M-1: lane-pass = proposed handler ∈ {canonical, acceptable}, via the SAME
    classify_handler_tier as the α probe (the taxonomy is defined once). The
    schema permits the tier fields on a watch item today — only authoring waits
    on calibration evidence (M-2=b)."""
    expected = Expected(
        disposition=Disposition.WATCH,
        action_expected=False,
        canonical_handler="increase_water_exchange",
        acceptable_handlers=["inspect"],
    )
    assert declares_handler_tiers(expected)
    canonical = grade_watch_proposal(
        _judgment(suggested_handler="increase_water_exchange"), expected
    )
    assert canonical.passed is True and canonical.tier is HandlerTier.CANONICAL
    acceptable = grade_watch_proposal(_judgment(suggested_handler="inspect"), expected)
    assert acceptable.passed is True and acceptable.tier is HandlerTier.ACCEPTABLE


def test_watch_grade_names_a_forbidden_pick_and_fails_other() -> None:
    """M-1 / SD-4=a: a forbidden_keywords hit on the proposed handler is named
    explicitly (FORBIDDEN), distinct from a merely-non-canonical OTHER — both
    fail the scored lane."""
    expected = Expected(
        disposition=Disposition.WATCH,
        action_expected=False,
        acceptable_handlers=["inspect"],
        forbidden_keywords=["expedite", "reroute"],
    )
    forbidden = grade_watch_proposal(_judgment(suggested_handler="expedite_shipment"), expected)
    assert forbidden.passed is False and forbidden.tier is HandlerTier.FORBIDDEN
    other = grade_watch_proposal(_judgment(suggested_handler="hold"), expected)
    assert other.passed is False and other.tier is HandlerTier.OTHER
