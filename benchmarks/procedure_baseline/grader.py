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

The model's ``suggested_handler`` is graded as a separate **tiered α probe**, NOT
a headline gate: in the procedure path the executed handler is deterministically
fixed by the author's ``step.handler`` (ADR-016), so the model's handler *guess*
is overridden and is not the product's handler decision. The probe measures
handler-selection as it would matter on the **reactive** path
(``recommender._compose_llm_record``, which DOES use the guess) — a
forward-looking signal, reported on its own lane. PLAN-0022 Step 1 tiers the
probe (:func:`classify_handler_tier`): **canonical** (the single correct
``canonical_handler``) / **acceptable** (a benign defensible alternative in
``acceptable_handlers``) / **forbidden-or-other** (everything else — with a
``forbidden_keywords`` hit flagged explicitly in reporting per SD-4=a, never a
new dataset tier). ``payload_contains`` stays an **advisory** signal. Headline /
probe / advisory are aggregated separately.

:func:`grade_watch_proposal` is the PLAN-0022 Phase-3 **watch-tier lane**
(escalation correctness — M-1, Cray-ratified 2026-06-12): on a deterministic
``watch`` disposition the LLM's proposed handler is classified with the SAME
tier helper (the taxonomy is defined once); lane-pass = canonical or acceptable.
Under M-2=b (calibration-first) a watch item that declares no handler tiers
grades **unscored** — the handler is recorded for the per-vertical distribution
report, never failed. The lane is reported on its own; it never touches β or α.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from benchmarks.procedure_baseline.schema import Disposition, Expected, Scenario
from services.engine.llm.structured import LlmJudgment
from services.engine.procedures.verdict import classify_verdict


def classify_disposition(scenario: Scenario) -> Disposition:
    """Deterministic breach/watch/ok verdict for a scenario.

    Delegates to the engine's ``classify_verdict`` — the PLAN-0022 single shared
    definition of the band math (``crosses_threshold`` breach edge + the watch
    band on the safe side; a ``None`` ``watch_margin`` collapses the band), so
    the dataset's dispositions and the engine semantics can never silently drift.
    """
    verdict = classify_verdict(
        scenario.measured_value,
        scenario.threshold,
        scenario.direction,
        scenario.watch_margin,
    )
    return Disposition(verdict.value)


class HandlerTier(StrEnum):
    """The tiered α-probe classification of one ``suggested_handler``
    (PLAN-0022 Step 1).

    Three tiers: ``canonical`` and ``acceptable`` pass the probe;
    ``forbidden``/``other`` together are the failing tier. ``forbidden`` is NOT
    a separate dataset tier (SD-4=a — it derives from the existing
    ``forbidden_keywords``); it is split out here only so reporting names a
    dangerous pick explicitly instead of lumping it with a merely-non-canonical
    one.
    """

    CANONICAL = "canonical"
    ACCEPTABLE = "acceptable"
    FORBIDDEN = "forbidden"
    OTHER = "other"


def classify_handler_tier(suggested_handler: str, expected: Expected) -> HandlerTier:
    """Classify the model's handler guess against the item's tiered expectation.

    ``canonical`` — exactly the declared ``canonical_handler``; ``acceptable`` —
    in ``acceptable_handlers`` (a benign defensible alternative); otherwise
    ``forbidden`` when the handler name contains a ``forbidden_keywords`` entry
    (the dangerous near-miss, e.g. ``expedite``/``reroute``), else ``other``.
    Shared by the α probe and (Phase 3) the escalation-correctness lane — the
    taxonomy is defined once.
    """
    if expected.canonical_handler is not None and suggested_handler == expected.canonical_handler:
        return HandlerTier.CANONICAL
    if expected.acceptable_handlers is not None and suggested_handler in (
        expected.acceptable_handlers
    ):
        return HandlerTier.ACCEPTABLE
    handler = suggested_handler.lower()
    if any(keyword.lower() in handler for keyword in expected.forbidden_keywords or []):
        return HandlerTier.FORBIDDEN
    return HandlerTier.OTHER


def declares_handler_tiers(expected: Expected) -> bool:
    """True when the item pins handler ground truth (``canonical_handler`` and/or
    ``acceptable_handlers``) — the condition for the α probe and for a SCORED
    watch-lane grade. Under M-2=b (calibration-first) watch items declare neither
    yet, so the watch lane reports a distribution instead of pass/fail.
    """
    return expected.canonical_handler is not None or expected.acceptable_handlers is not None


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
    * ``probe`` — the **α** reactive-path handler-selection signal
      (``handler_tier``): recorded + aggregated on its OWN lane, NOT a headline
      gate, because the procedure path overrides the model's handler guess with
      ``step.handler`` (ADR-016) — PLAN-0019 Part B hardening, Cray-ratified
      2026-06-09; tiered canonical/acceptable/forbidden-or-other by PLAN-0022
      Step 1 (``passed`` = canonical or acceptable).
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
    ``handler_tier`` is the three-way α classification behind ``probe_passed``
    (PLAN-0022 Step 1; ``None`` when no probe field is declared) — ``passed`` =
    canonical or acceptable.
    """

    passed: bool
    checks: list[FieldCheck]
    probe_passed: bool | None = None
    handler_tier: HandlerTier | None = None


def grade_proposal(judgment: LlmJudgment, expected: Expected) -> GradeResult:
    """Score an :class:`LlmJudgment` against the item's expected key.

    Grades exactly the fields ``expected`` declares (each ``None`` field is
    skipped): the affected-entity PK + the 'action class' keywords, plus the PR2
    precision add-ons — ``forbidden_primary_keys`` (no decoy sibling named) and
    ``forbidden_keywords`` (no near-miss verb in the title) — together the β headline
    **scoring** fields the model owns in the procedure path; the tiered handler
    classification (the **α probe** — recorded, not a gate; PLAN-0022 Step 1); and
    the handler-payload subset (**advisory**). All objective — no fuzzy/semantic
    scoring.
    """
    checks: list[FieldCheck] = []
    handler_tier: HandlerTier | None = None

    if expected.affected_primary_key is not None:
        keys = sorted({entity.primary_key for entity in judgment.affected_entities})
        passed = expected.affected_primary_key in keys
        detail = f"expected {expected.affected_primary_key!r} in {keys}"
        checks.append(FieldCheck("affected_primary_key", passed, detail))

    if expected.forbidden_primary_keys is not None:
        # β HEADLINE precision (PR2): the model must NOT name a decoy sibling entity.
        named = {entity.primary_key for entity in judgment.affected_entities}
        offenders = sorted(named & set(expected.forbidden_primary_keys))
        passed = not offenders
        detail = f"decoy(s) named: {offenders}" if offenders else "no decoy entity named"
        checks.append(FieldCheck("forbidden_primary_keys", passed, detail))

    if expected.canonical_handler is not None or expected.acceptable_handlers is not None:
        # α PROBE: the model's free handler guess, tiered canonical / acceptable /
        # forbidden-or-other (PLAN-0022 Step 1). NOT a headline gate — the procedure
        # path fixes the executed handler via step.handler (ADR-016), so this
        # measures the reactive-path handler choice. Pass = canonical or acceptable.
        handler_tier = classify_handler_tier(judgment.suggested_handler, expected)
        passed = handler_tier in (HandlerTier.CANONICAL, HandlerTier.ACCEPTABLE)
        detail = (
            f"{judgment.suggested_handler!r} -> {handler_tier.value} "
            f"(canonical {expected.canonical_handler!r}, "
            f"acceptable {expected.acceptable_handlers or []})"
        )
        checks.append(FieldCheck("handler_tier", passed, detail, probe=True))

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

    if expected.forbidden_keywords is not None:
        # β HEADLINE precision (PR2): the near-miss action verb must NOT be the
        # RECOMMENDED action — checked in the TITLE (the imperative action line),
        # not the body (where the model may legitimately rule the decoy out).
        title = judgment.title.lower()
        hits = sorted({kw for kw in expected.forbidden_keywords if kw.lower() in title})
        passed = not hits
        detail = f"decoy action verb in title: {hits}" if hits else "no decoy action verb in title"
        checks.append(FieldCheck("forbidden_keywords", passed, detail))

    scoring = [check for check in checks if not check.advisory and not check.probe]
    passed = bool(scoring) and all(check.passed for check in scoring)
    probe_checks = [check for check in checks if check.probe]
    probe_passed = all(check.passed for check in probe_checks) if probe_checks else None
    return GradeResult(
        passed=passed, checks=checks, probe_passed=probe_passed, handler_tier=handler_tier
    )


# --- Watch-tier lane (PLAN-0022 Phase 3 — escalation correctness, M-1/M-2) ----


@dataclass(frozen=True)
class WatchGrade:
    """The watch-lane outcome for one ``watch`` item's LLM proposal (M-1).

    ``handler`` is the model's ``suggested_handler`` verbatim — the per-vertical
    distribution evidence the M-2=b calibration run reports. ``tier`` /
    ``passed`` are ``None`` exactly when the item declares no handler tiers
    (unscored — the M-2=b state for every watch item until ground truth is
    pinned from calibration evidence); otherwise ``tier`` is the shared
    :func:`classify_handler_tier` classification and ``passed`` = canonical or
    acceptable (a ``forbidden`` hit is named explicitly via the tier, never
    lumped with merely-non-canonical — SD-4=a reporting).
    """

    handler: str
    tier: HandlerTier | None
    passed: bool | None


def grade_watch_proposal(judgment: LlmJudgment, expected: Expected) -> WatchGrade:
    """Grade one watch item's LLM proposal on the watch-tier lane (M-1).

    Reuses :func:`classify_handler_tier` — the taxonomy is defined once, shared
    with the α probe. When the item declares no ``canonical_handler`` /
    ``acceptable_handlers`` (M-2=b calibration-first: no watch ground truth is
    authored yet), the grade is **unscored**: the handler is recorded for the
    distribution report and ``passed`` stays ``None`` rather than failing.
    """
    if not declares_handler_tiers(expected):
        return WatchGrade(handler=judgment.suggested_handler, tier=None, passed=None)
    tier = classify_handler_tier(judgment.suggested_handler, expected)
    passed = tier in (HandlerTier.CANONICAL, HandlerTier.ACCEPTABLE)
    return WatchGrade(handler=judgment.suggested_handler, tier=tier, passed=passed)
