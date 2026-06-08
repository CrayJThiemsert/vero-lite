"""Grader for the procedure-baseline benchmark (PLAN-0019 B-β; SD-B1).

Two pure scoring functions:

* :func:`classify_disposition` — the **deterministic** breach/watch/ok verdict.
  Reuses the engine's own ``crosses_threshold`` (``services/engine/recommender``)
  as the single source of truth for the breach decision, then layers the watch
  band. This is the ~100% sanity check, reported separately (SD-B1 excludes the
  deterministic rule from the headline).
* :func:`grade_proposal` — the **LLM-graded** headline: objective field checks on
  the model's :class:`LlmJudgment` (the part the model can get wrong). Each field
  is scored only when the item declares it; the proposal passes iff every declared
  check passes.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmarks.procedure_baseline.schema import Disposition, Expected, Scenario
from services.engine.llm.structured import LlmJudgment
from services.engine.recommender import crosses_threshold


def classify_disposition(scenario: Scenario) -> Disposition:
    """Deterministic breach/watch/ok verdict for a scenario.

    ``breach`` is delegated to ``crosses_threshold`` (the exact engine semantics:
    ``below`` -> ``measured <= threshold``, else ``measured >= threshold``). A
    not-breach reading is ``watch`` when it sits within ``watch_margin`` of the
    breach floor (on the safe side), else ``ok``. With no ``watch_margin`` the
    watch band collapses and not-breach is always ``ok``.
    """
    if crosses_threshold(scenario.measured_value, scenario.threshold, scenario.direction):
        return Disposition.BREACH
    margin = scenario.watch_margin
    if margin is not None:
        if scenario.direction == "below":
            # safe side is ABOVE the floor; watch = floor < value <= floor + margin
            if scenario.measured_value <= scenario.threshold + margin:
                return Disposition.WATCH
        elif scenario.measured_value >= scenario.threshold - margin:
            # safe side is BELOW the ceiling; watch = ceiling - margin <= value < ceiling
            return Disposition.WATCH
    return Disposition.OK


@dataclass(frozen=True)
class FieldCheck:
    """One graded objective field — its name, pass/fail, and a human-readable detail."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class GradeResult:
    """The outcome of grading one LLM proposal against its expected key.

    ``passed`` is the conjunction of every declared :class:`FieldCheck`; an item
    that declares no graded field grades ``False`` (a breach item must declare at
    least one objective check — enforced by the dataset-consistency test).
    """

    passed: bool
    checks: list[FieldCheck]


def grade_proposal(judgment: LlmJudgment, expected: Expected) -> GradeResult:
    """Score an :class:`LlmJudgment` against the item's expected key.

    Grades exactly the fields ``expected`` declares (each ``None`` field is
    skipped): the affected-entity PK (the model named the right entity), the
    handler (within the registered allowlist), the handler-payload subset, and the
    'action class' keywords. All objective — no fuzzy/semantic scoring.
    """
    checks: list[FieldCheck] = []

    if expected.affected_primary_key is not None:
        keys = sorted({entity.primary_key for entity in judgment.affected_entities})
        passed = expected.affected_primary_key in keys
        detail = f"expected {expected.affected_primary_key!r} in {keys}"
        checks.append(FieldCheck("affected_primary_key", passed, detail))

    if expected.valid_handlers is not None:
        passed = judgment.suggested_handler in expected.valid_handlers
        detail = f"{judgment.suggested_handler!r} in {expected.valid_handlers}"
        checks.append(FieldCheck("valid_handler", passed, detail))

    if expected.payload_contains is not None:
        mismatched = {
            key: value
            for key, value in expected.payload_contains.items()
            if judgment.handler_payload.get(key) != value
        }
        checks.append(
            FieldCheck("payload_contains", not mismatched, f"missing/mismatched: {mismatched}")
        )

    if expected.action_keywords is not None:
        haystack = f"{judgment.title}\n{judgment.description}".lower()
        passed = any(keyword.lower() in haystack for keyword in expected.action_keywords)
        detail = f"any of {expected.action_keywords} in title/description"
        checks.append(FieldCheck("action_keywords", passed, detail))

    return GradeResult(passed=bool(checks) and all(check.passed for check in checks), checks=checks)
