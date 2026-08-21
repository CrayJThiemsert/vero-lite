"""The ฿ facet lands on the STEP trace, once per run (``ActionStepExecutor``).

:func:`~services.engine.economic_impact.build_economic_steps` composes the advisory Box-4
``economic_impact`` facet into each ``RecommendedAction``'s OWN ``reasoning_trace`` (ADR-0030 /
PLAN-0071), which persists inside ``StepResult.artifact["output_set"]``.
``services/db/run_analytics.py`` reads facets off ``StepResult.reasoning_trace`` instead (its S2
extract-on-read contract) — so a facet that only rides the envelope is present in the run and
invisible to the ฿ rollup behind Tab J. The executor emits it onto both.

**Why these tests live against the BASE executor and not the governance wrapper.**
``GovernanceActionExecutor._scored_rule`` used to lift the facet, and mirroring that into its
authority-gate branches is the change that looks smaller. It cannot be complete: ``aquaculture``
and ``energy`` bind this executor BARE, with no governance wrapper at all, so a wrapper-level
lift can never reach them — and they are two of the four verticals whose ฿ was silently zero.

End-to-end producer -> rollup evidence, including that the facet survives ``_scored_rule``'s
output replacement, lives in ``tests/services/db/test_economic_facet_reaches_benefit_rollup.py``.

Offline: the deterministic ``advisory_stub_factory`` stands in for the LLM, and the producer is a
local fake — no MS-S1, no DB (CLAUDE.md §8).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

import pytest

from services.engine.economic_impact import (
    EconomicExposure,
    EconomicImpact,
    register_economic_producer,
)
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Step,
    StepKind,
)
from services.engine.registry import registry

_VERTICAL = "aquaculture"
_NET = Decimal("247000.00")
_KIND = "mortality_avoided"


def _impact(net: Decimal = _NET, kind: str = _KIND) -> EconomicImpact:
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind=kind,
        baseline=EconomicExposure(label="ungoverned", exposure_thb=net + Decimal("1000")),
        governed=EconomicExposure(label="governed", exposure_thb=Decimal("1000")),
        net_benefit_thb=net,
        assumptions=["fixture"],
    )


def _register_producer(*, grounds: bool = True) -> None:
    """A producer in the shipped shape: an ``EconomicImpact``, or ``None`` when it cannot
    ground a ฿ figure (the OQ-C discipline — a facet that cannot be grounded is absent,
    never guessed)."""

    async def producer(event: Mapping[str, Any], vertical: str) -> EconomicImpact | None:
        return _impact() if grounds else None

    register_economic_producer(_VERTICAL, producer)


@pytest.fixture(autouse=True)
def _handler() -> None:
    """The judgment's ``suggested_handler`` is enum-constrained to the vertical's REGISTERED
    handlers, so the step cannot compose an action without one. Once per test — conftest's
    autouse ``_reset_registry`` clears it again afterwards."""

    async def aerate(action: Any) -> dict[str, Any]:
        return {"ok": True}

    registry.register_handler(_VERTICAL, "aerate", aerate)


def _executor() -> ActionStepExecutor:
    return ActionStepExecutor(client_factory=advisory_stub_factory)


def _step() -> Step:
    return Step(
        step_id="aerate",
        name="Aerate",
        kind=StepKind.ACTION,
        autonomy=Autonomy.GATED,
        handler="aerate",
    )


def _ctx() -> RunContext:
    return RunContext(
        agent=Agent(
            agent_id="pond_agent",
            name="Pond Agent",
            autonomy_ceiling=Autonomy.GATED,
            allowed=AgentAllowed(action_handlers=["aerate"]),
        ),
        vertical=_VERTICAL,
    )


def _entities(*event_ids: str) -> list[Any]:
    return [{"event_id": e, "event_type": "reading", "measured_value": 3.2} for e in event_ids]


def _facets(outcome: StepOutcome) -> list[dict[str, Any]]:
    return [
        t
        for t in outcome.reasoning_trace
        if isinstance(t, dict) and t.get("kind") == "economic_impact"
    ]


async def test_the_facet_reaches_the_step_trace_not_only_the_action_envelope() -> None:
    """The defect this closes. Both copies are asserted: the envelope keeps its own (nothing
    was moved out from under the action), and the step trace gains one (the ฿ rollup can now
    reach it)."""
    _register_producer()

    outcome = await _executor().execute(_step(), _entities("e1"), _ctx())

    assert [t["detail"]["net_benefit_thb"] for t in _facets(outcome)] == [str(_NET)]
    nested = outcome.output[0]["action"]["reasoning_trace"]
    assert any(
        t.get("kind") == "economic_impact" for t in nested
    ), "the emission must COPY onto the step trace, never strip the action's own facet"


async def test_the_step_trace_copy_is_the_same_bytes_as_the_envelope_copy() -> None:
    """Money stays a JSON string on both surfaces. A step-trace copy that serialised
    ``net_benefit_thb`` as a float would still satisfy the test above and would silently
    de-rate the figure the moment ``benefit_rollup`` cast it."""
    _register_producer()

    outcome = await _executor().execute(_step(), _entities("e1"), _ctx())

    [nested] = [
        t
        for t in outcome.output[0]["action"]["reasoning_trace"]
        if t.get("kind") == "economic_impact"
    ]
    assert _facets(outcome) == [nested]
    assert isinstance(nested["detail"]["net_benefit_thb"], str)


async def test_the_facets_follow_every_action_entry_in_the_trace() -> None:
    """Ordering is preserved deliberately: the governance wrapper's retired lift appended the
    facets AFTER all of the step's action entries, and the trace render and any order-sensitive
    reader should not have to notice that the emission moved."""
    _register_producer()

    outcome = await _executor().execute(_step(), _entities("e1", "e2"), _ctx())

    kinds = [t.get("kind") for t in outcome.reasoning_trace if isinstance(t, dict)]
    assert kinds == ["action_proposed", "action_proposed", "economic_impact", "economic_impact"]


async def test_two_distinct_actions_with_an_equal_figure_both_emit() -> None:
    """Why the ledger keys on ``(action_id, facet kind)`` and NOT on the ฿ figure.

    Two DISTINCT entities can legitimately ground the same amount — measured on the real
    ``aquaculture/morning_pond_health_round``, whose ``aerate`` step carries two ฿247,000
    ``mortality_avoided`` facets under different ``action_id``s. A value-keyed ledger would drop
    one and under-report the run: the same class of silent wrongness as the double count the
    ledger exists to prevent, in the other direction."""
    _register_producer()

    outcome = await _executor().execute(_step(), _entities("e1", "e2"), _ctx())

    assert [t["detail"]["net_benefit_thb"] for t in _facets(outcome)] == [str(_NET), str(_NET)]
    action_ids = [entry["action"]["id"] for entry in outcome.output]
    assert len(set(action_ids)) == 2, "the fixture must actually carry two distinct actions"


async def test_the_same_action_is_emitted_once_per_run() -> None:
    """The run-scoped ledger. The facet is rebuilt at EVERY action step, so a procedure running
    two action steps over one event carries the same figure twice — measured on
    ``procurement/emergency_sourcing_round`` (``source`` + ``approve``) and
    ``supply_chain/cold_chain_excursion_disposition`` (``assess`` + ``approve``). Emitting both
    would DOUBLE those verticals' ฿ sums in ``benefit_rollup``.

    One executor instance serves every action step of a run (each vertical factory constructs it
    inside its per-run ``factory()``), so a second ``execute()`` on the same instance IS the
    second-action-step case."""
    _register_producer()
    executor = _executor()

    first = await executor.execute(_step(), _entities("e1"), _ctx())
    second = await executor.execute(_step(), _entities("e1"), _ctx())

    assert len(_facets(first)) == 1
    assert _facets(second) == [], "the second action step over the same action must not re-emit"
    assert any(
        t.get("kind") == "economic_impact" for t in second.output[0]["action"]["reasoning_trace"]
    ), "the action's OWN facet is unconditional — only the step-trace copy is deduped"


async def test_a_fresh_run_emits_again() -> None:
    """The ledger is run-scoped, not process-scoped. A ledger that outlived its run would
    silently zero every run after the first — a far worse failure than the double count, and one
    that would look exactly like the bug being fixed here."""
    _register_producer()

    first = await _executor().execute(_step(), _entities("e1"), _ctx())
    next_run = await _executor().execute(_step(), _entities("e1"), _ctx())

    assert len(_facets(first)) == 1
    assert len(_facets(next_run)) == 1


async def test_a_producer_that_cannot_ground_a_figure_adds_nothing() -> None:
    """Advisory + never-raise. A vertical with no producer (``building_materials`` today), or an
    event the producer declines to price, leaves the trace untouched."""
    _register_producer(grounds=False)

    outcome = await _executor().execute(_step(), _entities("e1"), _ctx())

    assert _facets(outcome) == []
    assert any(
        isinstance(t, dict) and t.get("kind") == "action_proposed" for t in outcome.reasoning_trace
    ), "the positive control: the instrument DOES see this step's own trace entries"
