"""PLAN-0041 Step 4 — offline validators for the classify-enrichment fixture set (OQ-C).

These assert the labelled set is WELL-FORMED to the OQ-C spec (the arm counts, the
measured-only / borderline markers, uniqueness) — the mergeable, zero-host-state half of
Step 4. They do NOT call the model: the live before/after twin metric (AC-7) is the
Cray-gated Step 5 (``test_classify_enrichment_live``). Deliberately structural — content
sniffing the narratives would re-introduce the offline-fixture-masks-live-behaviour trap.
"""

from __future__ import annotations

from collections import Counter

from tests.services.engine.procedures.classify_enrichment_fixtures import (
    EXPECTED_LABELS,
    FIXTURES,
)


def test_fixture_set_size_is_26() -> None:
    """The OQ-C set is 26 narratives (Arm A 15 + Arm B 11)."""
    assert len(FIXTURES) == 26


def test_arm_a_lift_composition() -> None:
    """Arm A (lift) = 6 AT-1 + 5 AT-3 + 4 AT-1b. AT-1 + AT-3 are the GATED denominator (11);
    AT-1b is measured-only (OQ-E)."""
    arm_a = [f for f in FIXTURES if f.arm == "A_lift"]
    by_label = Counter(f.expected for f in arm_a)
    assert by_label["AT-1"] == 6
    assert by_label["AT-3"] == 5
    assert by_label["AT-1b"] == 4
    # the gated Arm-A metric denominator is AT-1 + AT-3 = 11 (the "≥ 9/11 after" read)
    assert by_label["AT-1"] + by_label["AT-3"] == 11


def test_arm_b_abstain_composition() -> None:
    """Arm B (zero-regression, HARD) = 11 genuine AT-2-class narratives, all expected to
    abstain — the 11/11 hard gate."""
    arm_b = [f for f in FIXTURES if f.arm == "B_abstain"]
    assert len(arm_b) == 11
    assert all(f.expected == "abstain" for f in arm_b)


def test_at_least_two_borderline_at2_traps() -> None:
    """≥ 2 borderline AT-2 (an AT-1-looking anomaly→action that hides a per-criterion gate or
    a DOA tier mid-flow) — the realistic down-classification trap (R1). Borderline cases are
    Arm B and must still abstain."""
    borderline = [f for f in FIXTURES if f.borderline]
    assert len(borderline) >= 2
    for f in borderline:
        assert f.arm == "B_abstain"
        assert f.expected == "abstain"


def test_measured_only_is_exactly_the_at1b_set() -> None:
    """``measured_only`` marks exactly the AT-1b fixtures (reported, not gated — OQ-E); no
    other label carries it, and every AT-1b carries it."""
    for f in FIXTURES:
        assert f.measured_only == (f.expected == "AT-1b")


def test_every_expected_label_is_in_the_closed_route_space() -> None:
    """Each expected route is one of the closed v1 routes (AT-1 family + abstain) — AT-2 is
    never an expected label (classify-don't-synthesize; AT-2 absent by construction)."""
    for f in FIXTURES:
        assert f.expected in EXPECTED_LABELS
    assert "AT-2" not in EXPECTED_LABELS


def test_fixture_ids_unique_and_narratives_nonempty() -> None:
    """Stable unique ids (so a live per-fixture result is attributable) + every narrative is
    substantive prose (not an empty stub)."""
    ids = [f.fixture_id for f in FIXTURES]
    assert len(set(ids)) == len(ids)
    for f in FIXTURES:
        assert f.fixture_id.strip()
        assert len(f.narrative.split()) >= 12  # a real multi-step narrative, not a keyword
