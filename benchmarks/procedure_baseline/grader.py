"""Grader for the procedure-baseline benchmark (PLAN-0019 B-β; SD-B1).

Two pure scoring functions:

* :func:`classify_disposition` — the **deterministic** breach/watch/ok verdict.
  Reuses the engine's own ``crosses_threshold`` (``services/engine/recommender``)
  as the single source of truth for the breach decision, then layers the watch
  band. This is the ~100% sanity check, reported separately (SD-B1 excludes the
  deterministic rule from the headline).
* :func:`grade_proposal` — the **LLM-graded** headline (SD-B1 graded unit A, "β"):
  objective field checks on the model's :class:`LlmJudgment` (the part the model
  can get wrong). The headline scores the fields the model genuinely OWNS in the
  governed **procedure** path — the affected entity (``affected_primary_key``) and
  the action class (``action_keywords``). Each field is scored only when the item
  declares it; the proposal passes iff every declared **scoring** check passes.

The model's ``suggested_handler`` (``valid_handlers``) is graded as a separate **α
probe**, NOT a headline gate: in the procedure path the executed handler is
deterministically fixed by the author's ``step.handler`` (ADR-016), so the model's
handler *guess* is overridden and is not the product's handler decision. The probe
measures handler-selection as it would matter on the **reactive** path
(``recommender._compose_llm_record``, which DOES use the guess) — a
forward-looking signal, reported on its own lane. ``payload_contains`` stays an
**advisory** signal. Headline / probe / advisory are aggregated separately.
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
    """One graded objective field — its name, pass/fail, and a human-readable detail.

    Three lanes, set by the two flags (a check is in exactly one):

    * **scoring** (both flags False) — drives ``GradeResult.passed`` (the β headline:
      ``affected_primary_key``, ``action_keywords``).
    * ``advisory`` — recorded + reported but does NOT drive ``passed`` (e.g.
      ``payload_contains``: the live model's payload KEY shape is free-form, so a
      payload subset is informative but not a fair headline gate — B-β calibration,
      Cray-ratified 2026-06-08).
    * ``probe`` — the **α** reactive-path handler-selection signal (``valid_handler``):
      recorded + aggregated on its OWN lane, NOT a headline gate, because the
      procedure path overrides the model's handler guess with ``step.handler``
      (ADR-016) — PLAN-0019 Part B hardening, Cray-ratified 2026-06-09.
    """

    name: str
    passed: bool
    detail: str
    advisory: bool = False
    probe: bool = False


@dataclass(frozen=True)
class GradeResult:
    """The outcome of grading one LLM proposal against its expected key.

    ``passed`` (the β headline) is the conjunction of every declared **scoring**
    :class:`FieldCheck` (neither ``advisory`` nor ``probe``); an item that declares no
    scoring field grades ``False`` (a breach item must declare at least one scoring
    check — enforced by the dataset-consistency test). ``probe_passed`` is the α
    handler-selection outcome (``None`` when the item declares no probe field), tracked
    separately so the headline and the probe never contaminate each other.
    """

    passed: bool
    checks: list[FieldCheck]
    probe_passed: bool | None = None


def grade_proposal(judgment: LlmJudgment, expected: Expected) -> GradeResult:
    """Score an :class:`LlmJudgment` against the item's expected key.

    Grades exactly the fields ``expected`` declares (each ``None`` field is
    skipped): the affected-entity PK + the 'action class' keywords (the β headline
    **scoring** fields the model owns in the procedure path), the handler (the **α
    probe** — recorded, not a gate), and the handler-payload subset (**advisory**).
    All objective — no fuzzy/semantic scoring.
    """
    checks: list[FieldCheck] = []

    if expected.affected_primary_key is not None:
        keys = sorted({entity.primary_key for entity in judgment.affected_entities})
        passed = expected.affected_primary_key in keys
        detail = f"expected {expected.affected_primary_key!r} in {keys}"
        checks.append(FieldCheck("affected_primary_key", passed, detail))

    if expected.valid_handlers is not None:
        # α PROBE: the model's free handler guess vs the correct action(s). NOT a
        # headline gate — the procedure path fixes the executed handler via
        # step.handler (ADR-016), so this measures the reactive-path handler choice.
        passed = judgment.suggested_handler in expected.valid_handlers
        detail = f"{judgment.suggested_handler!r} in {expected.valid_handlers}"
        checks.append(FieldCheck("valid_handler", passed, detail, probe=True))

    if expected.payload_contains is not None:
        mismatched = {
            key: value
            for key, value in expected.payload_contains.items()
            if judgment.handler_payload.get(key) != value
        }
        # ADVISORY: payload keys are free-form, so this is informative, not a gate.
        detail = f"missing/mismatched: {mismatched}"
        checks.append(FieldCheck("payload_contains", not mismatched, detail, advisory=True))

    if expected.action_keywords is not None:
        # Search ALL three free-text fields — the model legitimately places its
        # proposed action in any of title / description / rationale (empirically it
        # often lands in rationale). B-β calibration, Cray-ratified 2026-06-08.
        haystack = f"{judgment.title}\n{judgment.description}\n{judgment.rationale}".lower()
        passed = any(keyword.lower() in haystack for keyword in expected.action_keywords)
        detail = f"any of {expected.action_keywords} in title/description/rationale"
        checks.append(FieldCheck("action_keywords", passed, detail))

    scoring = [check for check in checks if not check.advisory and not check.probe]
    passed = bool(scoring) and all(check.passed for check in scoring)
    probe_checks = [check for check in checks if check.probe]
    probe_passed = all(check.passed for check in probe_checks) if probe_checks else None
    return GradeResult(passed=passed, checks=checks, probe_passed=probe_passed)
