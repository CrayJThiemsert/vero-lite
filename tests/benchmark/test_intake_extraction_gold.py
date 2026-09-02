"""AC-1 — the intake-extraction gold set's structural invariants (PLAN-0118).

**What these tests are, stated plainly (CLAUDE.md §8).** They are
well-formedness checks: they compare `gold.yaml` to itself and to the shipped
prebaked defaults. They redden on a malformed gold file and they **cannot**
redden on a wrong belief about a model. Nothing here closes any model claim —
that happens only under AC-6's live run.

Each control below exists to defeat a specific way a numeric or binary axis can
be passed **without doing the thing being measured**:

* (a) derivation notes — every scored value must name the span it came from, so
  a value nobody can trace cannot sit in the set unnoticed.
* (b) the direction control — a set where every case is `below` is passed 100%
  by a model that always answers `below`. That is the `fl-10` defect.
* (c) the swap control — if `threshold == recovery_value`, a model that swaps
  the two fields passes both.
* (d) the distractor control — if the threshold is the only number in the text,
  a model that grabs the only number passes without reading.
* (e) the anti-borrow tripwire — the prebaked defaults were never authored from
  a description, so matching one is evidence of the trap, not of quality.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from benchmarks.intake_extraction.harness import (
    GOLD_PATH,
    injection_cases,
    load_gold,
    scored_cases,
)

DEFAULTS_DIR = Path("services/api/intake_defaults")
_SCORED_VALUE_FIELDS = ("metric_direction", "metric_threshold", "recovery_value")


@pytest.fixture(scope="module")
def gold() -> dict[str, Any]:
    return load_gold()


@pytest.fixture(scope="module")
def cases(gold: dict[str, Any]) -> list[dict[str, Any]]:
    return scored_cases(gold)


def _flat(text: str) -> str:
    """Descriptions are wrapped in YAML; compare on normalised whitespace."""
    return " ".join(text.split())


def test_gold_file_is_where_the_harness_looks() -> None:
    assert GOLD_PATH.exists(), f"{GOLD_PATH} is missing"


def test_there_are_cases_to_score(cases: list[dict[str, Any]]) -> None:
    assert len(cases) >= 6, f"only {len(cases)} scored cases; the controls below need room"


# ---------------------------------------------------------------- AC-1(a)


def test_every_scored_value_carries_a_derivation_note(cases: list[dict[str, Any]]) -> None:
    """(a) Each scored field names the description span its value derives from."""
    missing: list[str] = []
    for case in cases:
        notes = case.get("derivation", {}) or {}
        for field in _SCORED_VALUE_FIELDS:
            note = str(notes.get(field, "")).strip()
            if not note:
                missing.append(f"{case['id']}.{field}")
    assert not missing, f"scored fields with no derivation note: {missing}"


def test_every_case_carries_a_confound_audit_and_pass_evidence_note(
    gold: dict[str, Any],
) -> None:
    """SD-1's audit trail, on every case including the injection band."""
    thin: list[str] = []
    for case in gold["cases"]:
        for field in ("confound_audit", "pass_evidence"):
            if len(str(case.get(field, "")).strip()) < 40:
                thin.append(f"{case['id']}.{field}")
    assert not thin, f"cases with a missing or stub audit note: {thin}"


# ---------------------------------------------------------------- AC-1(b)


def test_both_directions_appear_at_least_three_times(cases: list[dict[str, Any]]) -> None:
    """(b) The direction positive control.

    A model that always answers one way must be catchable. With every gold case
    on one side it would score 100% — the `fl-10` oracle leak in a new costume.
    """
    counts = {"above": 0, "below": 0}
    for case in cases:
        counts[case["expected"]["metric_direction"]] += 1
    assert counts["above"] >= 3, f"only {counts['above']} 'above' cases: {counts}"
    assert counts["below"] >= 3, f"only {counts['below']} 'below' cases: {counts}"


def test_the_direction_by_stated_2x2_is_crossed(cases: list[dict[str, Any]]) -> None:
    """Neither AC-1(b) nor SD-1a requires the two variables to be CROSSED.

    If every stated case were `above` and every physics-only case `below`, the
    two would be perfectly confounded and a failure could not be attributed to
    inference rather than to one direction. The gold file's own header claims a
    full 2x2 with >= 2 per cell; this asserts the claim.
    """
    cells: dict[tuple[str, bool], list[str]] = {}
    for case in cases:
        key = (case["expected"]["metric_direction"], bool(case["direction_stated"]))
        cells.setdefault(key, []).append(case["id"])
    for direction in ("above", "below"):
        for stated in (True, False):
            members = cells.get((direction, stated), [])
            assert len(members) >= 2, (
                f"cell direction={direction} stated={stated} has {len(members)} cases "
                f"({members}); the 2x2 needs >= 2 per cell"
            )


def test_prompt_cue_is_declared_and_discordant_cases_exist(cases: list[dict[str, Any]]) -> None:
    """`prompt_cue` is a first-class audit field, not a comment.

    `_SYSTEM_INSTRUCTION` (intake.py:88-91) names pressure among its 'below'
    examples and temperature as 'above', so a concordant case is answerable from
    the prompt alone. Only discordant cases prove the description was read.
    """
    allowed = {"discordant", "neutral", "concordant", "concordant-weak"}
    bad = [c["id"] for c in cases if c.get("prompt_cue") not in allowed]
    assert not bad, f"cases with a missing or unknown prompt_cue: {bad}"
    discordant = [c["id"] for c in cases if c["prompt_cue"] == "discordant"]
    assert len(discordant) >= 2, (
        f"only {len(discordant)} discordant cases ({discordant}); without them a pass "
        "is not evidence the description was read"
    )


# ---------------------------------------------------------------- AC-1(c)


def test_threshold_never_equals_recovery_value(cases: list[dict[str, Any]]) -> None:
    """(c) The swap control — equal values would let a field-swapping model pass both."""
    collisions = [
        c["id"]
        for c in cases
        if abs(float(c["expected"]["metric_threshold"]) - float(c["expected"]["recovery_value"]))
        < 1e-9
    ]
    assert not collisions, f"threshold == recovery_value in: {collisions}"


# ---------------------------------------------------------------- AC-1(d)


def test_distractor_control_is_same_unit_and_declared_truthfully(
    cases: list[dict[str, Any]],
) -> None:
    """(d) The distractor control — SAME READING, SAME UNIT.

    Corrected s269. The first implementation used a magnitude window
    (`thr/3 .. thr*3`) as a proxy for "plausible". Measured: that window is
    wrong in the direction that matters — it is a **false negative**. It
    excluded `rm-02`'s `0.6` kPa clean-bag reading, the same reading in the same
    unit as its `2.4` kPa threshold and precisely the distractor wanted, while
    every case it did admit was a true positive.

    Units cannot be inferred from prose, so each qualifying case declares its
    own distractor and this test verifies the declaration **against the
    description**: the span must appear verbatim, the value must sit inside that
    span, and it must be neither expected answer. A declaration that does not
    match the text reddens — the test reads the artifact, never its own constant.
    """
    declaring: list[str] = []
    for case in cases:
        declared = case.get("same_unit_distractors") or []
        if not declared:
            continue
        declaring.append(case["id"])
        flat = _flat(case["description"])
        expected = case["expected"]
        for entry in declared:
            value = float(entry["value"])
            span = str(entry["span"])
            assert (
                span in flat
            ), f"{case['id']}: declared distractor span {span!r} is NOT in the description"
            assert re.search(
                rf"(?<!\d){re.escape(_trim(value))}(?!\d)", span
            ), f"{case['id']}: declared value {value} does not appear inside its own span {span!r}"
            assert (
                abs(value - float(expected["metric_threshold"])) > 1e-9
            ), f"{case['id']}: distractor {value} IS the threshold — not a distractor"
            assert (
                abs(value - float(expected["recovery_value"])) > 1e-9
            ), f"{case['id']}: distractor {value} IS the recovery_value — not a distractor"
            assert str(
                entry.get("why", "")
            ).strip(), f"{case['id']}: distractor {value} has no 'why' naming the shared unit"

    assert len(declaring) >= 2, (
        f"only {len(declaring)} cases declare a same-unit distractor ({declaring}); "
        "AC-1(d) needs >= 2 or a numeric axis can pass by grabbing the only number"
    )


def _trim(value: float) -> str:
    """`43.0` -> `43`, `0.6` -> `0.6` — descriptions write numbers as humans do."""
    text = f"{value:.10g}"
    return text


# ---------------------------------------------------------------- AC-1(e)


def test_no_case_borrows_a_prebaked_default_package(cases: list[dict[str, Any]]) -> None:
    """(e) The anti-borrow tripwire.

    `services/api/intake_defaults/*.json` were NOT authored from descriptions.
    A gold case matching one field-for-field on the scored axes is evidence the
    author borrowed, which is the trap this control exists to catch — never a
    source. Read from the shipped JSON, not from a constant copied into this test.
    """
    defaults = sorted(DEFAULTS_DIR.glob("*.json"))
    assert defaults, f"no prebaked defaults found under {DEFAULTS_DIR}; the control is vacuous"

    fingerprints: dict[str, tuple[str, float, float]] = {}
    for path in defaults:
        data = json.loads(path.read_text(encoding="utf-8"))
        fingerprints[path.name] = (
            str(data["metric"]["direction"]),
            float(data["metric"]["threshold"]),
            float(data["recovery_value"]),
        )

    for case in cases:
        expected = case["expected"]
        got = (
            str(expected["metric_direction"]),
            float(expected["metric_threshold"]),
            float(expected["recovery_value"]),
        )
        for name, fingerprint in fingerprints.items():
            assert got != fingerprint, (
                f"{case['id']} matches prebaked default {name} field-for-field on the "
                f"scored axes {got} — AC-1(e) tripwire"
            )


def test_no_case_uses_a_domain_the_defaults_already_cover(gold: dict[str, Any]) -> None:
    """The domains must not be solar-farm or water-utility (AC-1(e), Step 2)."""
    forbidden = {"solar_farm", "water_utility"}
    overlap = forbidden & set(gold["domains"])
    assert not overlap, f"gold reuses a prebaked-default domain: {overlap}"


# ------------------------------------------------- the SD-3 injection band


def test_injection_band_is_separable_from_accuracy(gold: dict[str, Any]) -> None:
    """SD-3 (a): the injection cases are their own band, never folded into accuracy.

    The injected value is NOT always numeric — the band plants a float in
    ``metric_threshold``, a slug in ``namespace`` (delimiter forgery) and a
    direction in ``metric_direction``. Compare as text so all three shapes are
    checked; a numeric-only check silently skipped two of them.
    """
    band = injection_cases(gold)
    assert len(band) >= 2, f"only {len(band)} injection cases; the band needs >= 2"
    scored_ids = {c["id"] for c in scored_cases(gold)}
    for case in band:
        assert "expected" not in case, (
            f"{case['id']} carries an 'expected' block; an injection case must not enter "
            "the accuracy denominator"
        )
        assert str(case.get("obeyed_if", "")).strip(), f"{case['id']}: no obeyed_if rule"
        flat = _flat(case["description"])
        injected = case["injected_value"]
        rendered = _trim(float(injected)) if isinstance(injected, int | float) else str(injected)
        assert rendered in flat, (
            f"{case['id']}: the injected value {injected!r} is not actually in the description, "
            "so the case cannot demonstrate anything"
        )
        assert case.get("based_on") in scored_ids, (
            f"{case['id']}: based_on={case.get('based_on')!r} does not name a scored case; "
            "without it the differential read is impossible"
        )
        assert (
            str(case.get("injected_field", "")).strip()
        ), f"{case['id']}: no injected_field, so the scorer would have to guess where to look"


def test_a_confounded_injection_case_declares_its_own_exclusion(gold: dict[str, Any]) -> None:
    """A case whose injected value coincides with what the prompt already implies
    is uninterpretable alone, and must not enter the obeyed_injection fraction.

    ``inj-03``'s ``confound_audit`` has said exactly that in prose since s268 and
    nothing enforced it. A rule that lives only where its consumer does not look
    is, for that consumer, not written — so it now also carries the machine-read
    ``counts_in_fraction: false`` that ``summarize_injection`` honours. This test
    asserts the two agree.
    """
    band = injection_cases(gold)
    excluded = [c for c in band if c.get("counts_in_fraction", True) is False]
    assert excluded, (
        "no injection case declares counts_in_fraction: false — if the band no longer "
        "contains a prompt-coincident case, delete this test with a note saying why"
    )
    for case in excluded:
        audit = str(case.get("confound_audit", ""))
        assert "NEVER be counted" in audit or "never be counted" in audit, (
            f"{case['id']} is excluded by flag but its confound_audit does not say why; "
            "the flag and the prose must not drift apart"
        )
        assert case.get("based_on"), (
            f"{case['id']} is excluded from the fraction, so its only legitimate read is "
            "differential — it must name the case it is read against"
        )

    counted = [c for c in band if c.get("counts_in_fraction", True) is not False]
    assert (
        len(counted) >= 2
    ), f"only {len(counted)} injection cases actually enter the fraction; the band needs >= 2"
