"""The ``env_band`` evaluate executor (PLAN-0062 Step 1; ADR-016 D2-A3).

ADR-016 D2-A3 models two ways a step's deterministic band is authored: ``in_file``
— the band lives on the ``Step`` as ``threshold`` / ``direction`` / ``watch_margin``
(aquaculture, procurement) — and ``env`` — the band comes from the runtime
environment, with **no** in-file ``threshold`` (``energy.judge``,
``supply_chain.judge``). The shipped
:class:`~services.engine.procedures.evaluate_step.EvaluateStepExecutor` implements
only the ``in_file`` half: a band-less step raises. This module is the ``env`` half —
the executable counterpart of a band source the ADR already ratified.

**It does not read ``facet``.** ADR-016 **D2-A4** makes ``facet`` schema-only:
engine-*readable*, never engine-*consumed*. So the env band is NOT selected by
inspecting ``step.facet.decision_condition.gate_kind``; it is selected by the
**vertical's factory**, which registers this executor for the ``evaluate``
``StepKind`` (energy / supply_chain) in place of the bare base. The only trigger
here is the typed truth: an ``evaluate`` step with **no authored** ``threshold``
takes its band from ``settings``; a step that authors one is an ``in_file`` band and
delegates through unchanged. A vertical whose ``evaluate`` steps are band-less for
some other reason (procurement's ``rule_gate`` compliance) must not register this
executor — it composes a band, it does not detect one.

**Extend, never fork** (PLAN-0062 L-5; LOCKED #5). The band *math* is not
re-implemented: the step is rebound with the env-sourced band and handed to the
wrapped ``base``, so :func:`~services.engine.procedures.verdict.classify_verdict`
remains the single shared band definition, and the determinism invariant (no LLM,
no model signal — ADR-0019 / ADR-010 IN-3) is **inherited** rather than re-asserted.
The orchestrator's ``StepKind``-keyed contract is untouched, mirroring
:class:`~services.engine.procedures.governance_step.GovernanceEvaluateExecutor`.

**An env band is necessarily watch-less.** ``Step``'s own validator refuses a
``direction`` or ``watch_margin`` authored without a ``threshold`` to band around
(PLAN-0022 Step 3), so on the only branch this executor binds — ``threshold is
None`` — both are guaranteed ``None`` too. The whole band therefore comes from
``settings``, and with no ``watch_margin`` counterpart in the environment the watch
band collapses: an env band judges **breach / ok**, exactly the two-verdict shape
energy's ``judge`` facet declares.

The band's provenance rides the step audit (``band_source`` + the two ``env_var``s)
so a run's trail records that the numbers came from the environment, not the YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from services.api.config import settings
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.spec import Step

THRESHOLD_ENV_VAR = "OCT_RECOMMEND_THRESHOLD"
"""The env var carrying the band's numeric edge — the ``env_var`` the
``decision_condition`` facet names for energy / supply_chain (ADR-016 D2-A3)."""

DIRECTION_ENV_VAR = "OCT_RECOMMEND_DIRECTION"
"""The env var carrying the breach direction (``above`` | ``below``)."""


@dataclass(frozen=True)
class EnvBandEvaluateExecutor:
    """Delegating wrapper: bind the env band, then run the shipped base executor."""

    base: StepExecutor

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        """Judge ``input_set`` against the runtime env band when the step authors none.

        An authored ``threshold`` means ``in_file`` — delegate untouched, so one
        registered executor serves a vertical that mixes both band sources. Otherwise
        rebind the step with the env threshold + direction (the ``Step`` validator
        guarantees it authored neither) and let the base do the band math + tagging.
        """
        if step.threshold is not None:
            return await self.base.execute(step, input_set, ctx)
        bound = step.model_copy(
            update={
                "threshold": settings.oct_recommend_threshold,
                "direction": settings.oct_recommend_direction,
            }
        )
        outcome = await self.base.execute(bound, input_set, ctx)
        audit: dict[str, Any] = {
            **(outcome.audit or {}),
            "band_source": "env",
            "env_var": THRESHOLD_ENV_VAR,
            "direction_env_var": DIRECTION_ENV_VAR,
        }
        return replace(outcome, audit=audit)
