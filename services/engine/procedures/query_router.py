"""Per-step QUERY routing inside one ``StepKind`` slot (PLAN-0064 Steps 1-2).

The orchestrator resolves ONE executor per ``StepKind``
(``executors.get(step.kind)`` — :mod:`~services.engine.procedures.orchestrator`),
so a vertical whose QUERY slot is a fixed seed cannot honestly serve a second,
different query step: the declared step would pass the load gate and still be
handed the seed at run time — declared ✔ / execution-bound ✖ (PLAN-0062
ERRATUM 2, the procurement ``read_stock`` deferral). This router closes that
gap INSIDE the slot: the orchestrator's ``Mapping[StepKind, StepExecutor]``
contract is untouched (extend not replace, LOCKED #5 — the same
delegating-wrapper pattern as ``GovernanceEvaluateExecutor`` in
:mod:`~services.engine.procedures.governance_step` and
``EnvBandEvaluateExecutor`` in :mod:`~services.engine.procedures.env_band_step`).
ADR-016 records a vertical's executor supply as "an undocumented operational
expectation, not an engine contract", so no amendment is needed (PLAN-0064
SD-0, Cray-ratified).

Dispatch rule (SD-1, ratified): **declaration-presence** — a step that DECLARES
``input.reads`` routes to the ``declared`` executor (the shipped declared-grammar
:class:`~services.engine.procedures.query_step.QueryStepExecutor`); a step
without a declaration routes to the ``fallback`` (the vertical's seed). This
makes "declared ⇒ dispatched" structural: the ERRATUM-2 hazard cannot recur for
any future declared read, with zero further factory edits.

Deterministic and vertical-agnostic — dispatches on typed :class:`Step` fields
only (no step-id lists, no vertical knowledge), no LLM anywhere (LOCKED-6
carried).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.spec import Step


@dataclass(frozen=True)
class QueryStepRouter:
    """Route one QUERY slot per step: declared ``input.reads`` → ``declared``; else ``fallback``.

    Both legs implement the plain :class:`StepExecutor` protocol, and so does
    the router — a composing factory (e.g. procurement's ``_executors``) simply
    places the router in its ``StepKind.QUERY`` slot; the orchestrator never
    knows routing happened.
    """

    declared: StepExecutor
    fallback: StepExecutor

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        """Delegate to ``declared`` iff the step declares ``input.reads`` (SD-1)."""
        if step.input is not None and step.input.reads:
            return await self.declared.execute(step, input_set, ctx)
        return await self.fallback.execute(step, input_set, ctx)
