"""PLAN-0022 Step 3 — the engine's deterministic verdict math (single shared
definition; ADR-0019).

Pure-Python (no DB, no LLM): exercises ``classify_verdict`` across both breach
directions, the inclusive breach boundary, the watch-band edges, the collapsed
(``None``-margin) band, and the ``crosses_threshold`` fail-safe direction
handling. The escalation trigger this function feeds is deterministic by
construction — the model's ``confidence`` is not even an input (ADR-010 IN-3;
the full AC-8 determinism test lands with the Phase-2 ``watch -> gated``
wiring).
"""

from __future__ import annotations

import pytest

from services.engine.procedures.verdict import Verdict, classify_verdict


def _below(value: float) -> Verdict:
    """aquaculture DO-crash semantics: breach BELOW the 4.0 floor, watch band 1.0."""
    return classify_verdict(value, threshold=4.0, direction="below", watch_margin=1.0)


def _above(value: float) -> Verdict:
    """energy over-temperature semantics: breach ABOVE the 90.0 ceiling, watch band 5.0."""
    return classify_verdict(value, threshold=90.0, direction="above", watch_margin=5.0)


def test_below_breach_is_inclusive_at_the_floor() -> None:
    assert _below(4.0) is Verdict.BREACH
    assert _below(3.9) is Verdict.BREACH


def test_below_watch_band_just_above_the_floor() -> None:
    assert _below(4.02) is Verdict.WATCH
    assert _below(5.0) is Verdict.WATCH  # inclusive upper edge


def test_below_ok_above_the_watch_band() -> None:
    assert _below(5.1) is Verdict.OK


def test_above_breach_is_inclusive_at_the_ceiling() -> None:
    assert _above(90.0) is Verdict.BREACH
    assert _above(96.5) is Verdict.BREACH


def test_above_watch_and_ok_bands() -> None:
    assert _above(85.0) is Verdict.WATCH  # inclusive lower edge
    assert _above(89.9) is Verdict.WATCH
    assert _above(84.9) is Verdict.OK


def test_none_watch_margin_collapses_the_band() -> None:
    """AC-9: with no authored watch_margin every not-breach reading is ok —
    a margin-less procedure behaves byte-for-byte as today."""
    assert classify_verdict(4.5, threshold=4.0, direction="below", watch_margin=None) is Verdict.OK
    assert classify_verdict(4.5, threshold=4.0, direction="below") is Verdict.OK  # default None


def test_direction_is_normalized_like_crosses_threshold() -> None:
    """The watch band must follow the same case/space normalization as the
    breach edge — ' Below ' is 'below' on both sides of the band math."""
    assert classify_verdict(3.9, threshold=4.0, direction=" Below ", watch_margin=1.0) is (
        Verdict.BREACH
    )
    assert classify_verdict(4.5, threshold=4.0, direction=" Below ", watch_margin=1.0) is (
        Verdict.WATCH
    )


def test_garbled_direction_fails_safe_to_above() -> None:
    """Anything not 'below' means 'above' (the crosses_threshold fail-safe),
    and the watch band sits below the ceiling accordingly."""
    assert classify_verdict(90.0, threshold=90.0, direction="sideways", watch_margin=5.0) is (
        Verdict.BREACH
    )
    assert classify_verdict(86.0, threshold=90.0, direction="sideways", watch_margin=5.0) is (
        Verdict.WATCH
    )
    assert classify_verdict(84.0, threshold=90.0, direction="sideways", watch_margin=5.0) is (
        Verdict.OK
    )


@pytest.mark.parametrize("value", [3.0, 4.0, 4.5, 5.0, 6.0])
def test_verdict_is_a_pure_function_of_the_reading(value: float) -> None:
    """Determinism invariant (ADR-0019 / AC-3 spirit): repeated classification of
    the same reading is identical — no hidden state, no model signal in the
    signature."""
    assert _below(value) is _below(value)
