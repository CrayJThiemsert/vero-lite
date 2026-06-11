"""Deterministic three-way verdict math (PLAN-0022 Step 3; ADR-0019).

The **single shared definition** of the breach/watch/ok band — engine-owned so
the routing trigger is always a deterministic function of authored thresholds
over observed data, never a model signal (ADR-0019 determinism invariant;
ADR-010 IN-3). Consumers:

* the deterministic ``evaluate`` executor (PLAN-0022 Phase 2a — the SD-6
  prerequisite) computes the per-entity ``verdict`` fan-out key from the
  ``Step``-authored ``threshold`` / ``direction`` / ``watch_margin``;
* the procedure-baseline benchmark grader
  (``benchmarks.procedure_baseline.grader.classify_disposition``) delegates
  here, so the dataset's declared dispositions and the engine semantics can
  never silently drift apart.

The breach edge is delegated to ``recommender.crosses_threshold`` (the engine's
existing single source of truth, including its fail-safe direction handling);
this module layers only the watch band on the safe side of the floor.
"""

from __future__ import annotations

from enum import StrEnum

from services.engine.recommender import crosses_threshold


class Verdict(StrEnum):
    """The three-way disposition an ``evaluate`` step assigns per entity.

    ``breach`` fires the deterministic action path; ``watch`` is the ambiguous
    band that MAY route to a ``gated`` proposal (ADR-0019); ``ok`` is a no-op.
    The values are the ``where: {verdict: ...}`` fan-out vocabulary in
    ``procedures.yaml``.
    """

    BREACH = "breach"
    WATCH = "watch"
    OK = "ok"


def classify_verdict(
    measured_value: float,
    threshold: float,
    direction: str,
    watch_margin: float | None = None,
) -> Verdict:
    """Classify one reading into ``breach`` / ``watch`` / ``ok``.

    ``breach`` is exactly ``crosses_threshold`` (``below`` -> ``measured <=
    threshold``, anything else fails safe to ``above`` -> ``measured >=
    threshold``). A not-breach reading is ``watch`` when it sits within
    ``watch_margin`` of the breach floor on the safe side (``below``: ``floor <
    value <= floor + margin``; ``above``: ``ceiling - margin <= value <
    ceiling``), else ``ok``. A ``None`` ``watch_margin`` collapses the watch
    band — every not-breach reading is ``ok``, preserving pre-PLAN-0022
    behaviour byte-for-byte (AC-9).
    """
    if crosses_threshold(measured_value, threshold, direction):
        return Verdict.BREACH
    if watch_margin is not None:
        if direction.strip().lower() == "below":
            # safe side is ABOVE the floor; watch = floor < value <= floor + margin
            if measured_value <= threshold + watch_margin:
                return Verdict.WATCH
        elif measured_value >= threshold - watch_margin:
            # safe side is BELOW the ceiling; watch = ceiling - margin <= value < ceiling
            return Verdict.WATCH
    return Verdict.OK
