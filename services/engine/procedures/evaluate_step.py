"""Deterministic evaluate-step executor (PLAN-0022 Phase 2a; ADR-0019; SD-6).

The engine-owned ``evaluate`` :class:`StepExecutor` — the prerequisite the design
seed missed (PLAN-0022 fact 2 / SD-6): until now the ``judge`` step's
breach/watch/ok verdict had **no shipped engine producer** (callers provided
fakes). Per entity in the step's input set it computes the three-way ``verdict``
from the **Step-authored band** (``threshold`` / ``direction`` / ``watch_margin``
— the PLAN-0022 Step 3 config surface) via
:func:`services.engine.procedures.verdict.classify_verdict` (the single shared
band definition, which itself reuses ``recommender.crosses_threshold`` for the
breach edge), and tags the entity: ``{**entity, "verdict": ...}`` — exactly the
shape the ``where: {verdict: ...}`` named-input fan-out filters on.

**Determinism invariant (ADR-0019 / ADR-010 IN-3, load-bearing).** This executor
makes **no LLM call** and takes no model signal: the verdict — and therefore the
``watch -> gated`` escalation routing built on it — is a pure function of the
observed reading and the authored band. ``confidence`` is not an input by
construction. Any future change that lets a model signal influence the verdict is
an ADR-010 reopen, surfaced explicitly (PLAN-0022 SD-2).

The reading is taken from the entity's ``measured_value`` field — the
ontology-projected event convention shared by the reactive path
(``recommender._rule_recommend``), the benchmark harness
(``scenario_to_event``), and ``action_step._loop_entity_ref``'s HEDGE. An entity
without a numeric reading fails the step loudly (D4 fail-and-divert catches it;
the author chooses ``on_failure: escalate_to_human`` for human takeover) rather
than being silently tagged or dropped.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from services.engine.procedures.orchestrator import ProcedureError, RunContext, StepOutcome
from services.engine.procedures.spec import Step
from services.engine.procedures.verdict import Verdict, classify_verdict

VALUE_FIELD = "measured_value"
"""The entity field carrying the reading — the ontology-projected event shape."""

_FAILSAFE_DIRECTION = "above"
"""An unset ``direction`` fails safe to ``above`` — the ``crosses_threshold``
semantics for an unset/garbled direction, mirrored here so the authored band and
the breach edge can never disagree."""


def _entity_value(step_id: str, entity: Any) -> float:
    """The entity's numeric reading, or a loud ``ValueError`` (a judge step over
    entities without readings is a data/config error — D4 diverts it, never a
    silent verdict). ``bool`` is rejected explicitly (it is an ``int`` subclass —
    ``True`` must not silently judge as ``1.0``)."""
    if not isinstance(entity, Mapping):
        raise ValueError(
            f"evaluate step '{step_id}': entity {entity!r} is not a mapping — "
            f"cannot read its '{VALUE_FIELD}'"
        )
    raw = entity.get(VALUE_FIELD)
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise ValueError(
            f"evaluate step '{step_id}': entity {entity.get('event_id', entity)!r} has no "
            f"numeric '{VALUE_FIELD}' (got {raw!r}) — a deterministic verdict needs a reading"
        )
    return float(raw)


@dataclass(frozen=True)
class EvaluateStepExecutor:
    """The deterministic ``evaluate`` StepExecutor (SD-6). See module docstring."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        """Tag each input entity with its deterministic ``verdict``.

        Requires the step's authored ``threshold`` (PLAN-0022 Step 3) — a
        band-less evaluate step is a configuration error for THIS executor
        (callers with NL-only judge steps keep providing their own executor, so
        existing procedures are untouched — AC-9). An absent ``watch_margin``
        collapses the watch band (not-breach == ok); an absent ``direction``
        fails safe to ``above``.
        """
        if step.threshold is None:
            raise ProcedureError(
                f"evaluate step '{step.step_id}' has no authored threshold — the deterministic "
                "evaluate executor reads the Step band config (threshold / direction / "
                "watch_margin, PLAN-0022 Step 3); author it or provide a custom executor"
            )
        direction = step.direction or _FAILSAFE_DIRECTION
        counts: dict[str, int] = {verdict.value: 0 for verdict in Verdict}
        output: list[Any] = []
        for entity in input_set:
            verdict = classify_verdict(
                _entity_value(step.step_id, entity),
                step.threshold,
                direction,
                step.watch_margin,
            )
            output.append({**entity, "verdict": verdict.value})
            counts[verdict.value] += 1
        summary = (
            f"judged {len(output)} entities vs threshold {step.threshold} "
            f"({direction}, watch_margin {step.watch_margin}): "
            f"{counts[Verdict.BREACH.value]} breach / {counts[Verdict.WATCH.value]} watch / "
            f"{counts[Verdict.OK.value]} ok"
        )
        trace = [{"kind": "verdict_computed", "summary": summary, "counts": counts}]
        audit = {
            "actor": ctx.agent.agent_id,
            "actor_kind": "engine",
            "deterministic": True,
            "threshold": step.threshold,
            "direction": direction,
            "watch_margin": step.watch_margin,
        }
        return StepOutcome(output=output, reasoning_trace=trace, audit=audit)
