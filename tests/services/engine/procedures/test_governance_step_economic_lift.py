"""The ฿-facet STEP-trace lift and its run-scoped ledger (``GovernanceActionExecutor``).

The base :class:`~services.engine.procedures.action_step.ActionStepExecutor` builds the advisory
Box-4 ``economic_impact`` facet into each ``RecommendedAction``'s OWN ``reasoning_trace``
(ADR-0030 / PLAN-0071). ``services/db/run_analytics.py`` reads facets off
``StepResult.reasoning_trace`` instead (its S2 extract-on-read contract), so a facet that is only
nested inside the action envelope is present in the run and unreachable by the ฿ rollup. The
governance wrapper lifts it onto the contracted surface.

These are the wrapper-level invariants of that lift. The end-to-end producer -> rollup evidence
lives in ``tests/services/db/test_economic_facet_reaches_benefit_rollup.py``.

Offline: a stub base executor stands in for the LLM-backed action step, so no MS-S1 and no DB
(CLAUDE.md §8).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.engine.procedures.governance_step import GovernanceActionExecutor
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    RelaxableConstraint,
    Step,
    StepKind,
)

_NET = "247000.00"


def _facet(kind: str = "mortality_avoided", net: str = _NET) -> dict[str, Any]:
    """One ``economic_impact`` ReasoningStep in the shape ``build_economic_steps`` emits."""
    return {
        "step_id": "economic-impact-0",
        "kind": "economic_impact",
        "summary": f"Economic impact ({kind}): net benefit ~฿{net}",
        "detail": {"currency": "THB", "kind": kind, "net_benefit_thb": net},
    }


def _envelope(action_id: str, facets: list[dict[str, Any]]) -> dict[str, Any]:
    """One ``output_set`` entry in the shape ``action_step._entry`` serialises."""
    return {
        "action_id": action_id,
        "status": "proposed",
        "action": {"id": action_id, "reasoning_trace": [{"kind": "rule_check"}, *facets]},
        "receipt": None,
    }


class _StubBase:
    """A base action executor that returns fixed envelopes — the LLM path stands in."""

    def __init__(self, output: list[Any]) -> None:
        self._output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=self._output, reasoning_trace=[], audit={"actor": "stub"})


def _ladder() -> DoaLadder:
    return DoaLadder(
        kind="doa_tier",
        currency="THB",
        tiers=[DoaTier(min_amount=Decimal("0"), approver_role="owner")],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID],
            escalate_to="owner",
            requires_justification=True,
        ),
    )


def _step() -> Step:
    return Step(
        step_id="approve",
        name="Approve",
        kind=StepKind.ACTION,
        autonomy=Autonomy.GATED,
        handler="echo",
        governance_content=_ladder(),
    )


def _ctx() -> RunContext:
    return RunContext(
        agent=Agent(
            agent_id="agent",
            name="Agent",
            autonomy_ceiling=Autonomy.GATED,
            allowed=AgentAllowed(action_handlers=["echo"]),
        ),
        vertical="aquaculture",
    )


def _lifted(outcome: StepOutcome) -> list[dict[str, Any]]:
    return [
        t
        for t in outcome.reasoning_trace
        if isinstance(t, dict) and t.get("kind") == "economic_impact"
    ]


async def test_the_authority_gate_lifts_the_facet_onto_the_step_trace() -> None:
    """The defect this fix closes: ``_doa_tier`` KEEPS ``base_outcome.output``, so the facet is
    not destroyed — it is merely nested where the ฿ rollup does not look. After the lift it is on
    ``StepResult.reasoning_trace``, the surface ``run_analytics`` is contracted to read.

    The un-lifted arm is still asserted (the envelope keeps its own copy), so this cannot pass by
    the facet having MOVED rather than been copied onto the trace."""
    envelopes = [_envelope("action-a", [_facet()])]
    executor = GovernanceActionExecutor(base=_StubBase(envelopes))

    outcome = await executor.execute(_step(), [{"amount": "1", "currency": "THB"}], _ctx())

    assert [t["detail"]["net_benefit_thb"] for t in _lifted(outcome)] == [_NET]
    nested = outcome.output[0]["action"]["reasoning_trace"]
    assert any(
        t.get("kind") == "economic_impact" for t in nested
    ), "the lift must COPY onto the step trace, never strip the action's own facet"


async def test_the_same_action_is_lifted_once_per_run() -> None:
    """The run-scoped ledger. The base executor rebuilds the facet at EVERY action step, so a
    procedure with two action steps over one event (measured: procurement ``source`` + ``approve``,
    supply_chain ``assess`` + ``approve``) carries the same figure twice. Lifting both would
    DOUBLE that vertical's ฿ sum in ``benefit_rollup`` — a worse and quieter defect than the one
    being fixed.

    The SAME executor instance serves every action step of a run (the registry Step-2 contract
    builds it fresh per run), so a second execute() on the same instance is exactly the
    second-action-step case."""
    envelopes = [_envelope("action-a", [_facet()])]
    executor = GovernanceActionExecutor(base=_StubBase(envelopes))
    entity = [{"amount": "1", "currency": "THB"}]

    first = await executor.execute(_step(), entity, _ctx())
    second = await executor.execute(_step(), entity, _ctx())

    assert len(_lifted(first)) == 1
    assert _lifted(second) == [], "the second action step over the same action must not re-lift"


async def test_a_fresh_run_lifts_again() -> None:
    """The ledger is run-scoped, not process-scoped. A new executor instance is a new run, and
    the next run's ฿ must land — a ledger that outlived its run would silently zero every run
    after the first."""
    envelopes = [_envelope("action-a", [_facet()])]
    entity = [{"amount": "1", "currency": "THB"}]

    first = await GovernanceActionExecutor(base=_StubBase(envelopes)).execute(
        _step(), entity, _ctx()
    )
    next_run = await GovernanceActionExecutor(base=_StubBase(envelopes)).execute(
        _step(), entity, _ctx()
    )

    assert len(_lifted(first)) == 1
    assert len(_lifted(next_run)) == 1


async def test_two_distinct_actions_with_an_equal_figure_both_lift() -> None:
    """Why the ledger keys on ``(action_id, facet kind)`` and NOT on the ฿ figure.

    Two DISTINCT entities can legitimately ground the same amount — measured on
    ``aquaculture/morning_pond_health_round``, whose ``aerate`` step carries two ฿247,000
    ``mortality_avoided`` facets under different ``action_id``s. A value-keyed ledger would drop
    one of them and under-report the run, which is the same class of silent wrongness as the
    double count it exists to prevent, in the other direction."""
    envelopes = [
        _envelope("action-pond-a", [_facet()]),
        _envelope("action-pond-b", [_facet()]),
    ]
    executor = GovernanceActionExecutor(base=_StubBase(envelopes))

    outcome = await executor.execute(_step(), [{"amount": "1", "currency": "THB"}] * 2, _ctx())

    assert [t["detail"]["net_benefit_thb"] for t in _lifted(outcome)] == [_NET, _NET]


async def test_the_lifted_entry_is_passed_through_byte_identical() -> None:
    """The ledger key is COMPUTED, never stamped. Nothing downstream of the trace shape (the ฿
    extract-on-read, the trace render) sees a new or changed key, so this fix cannot move a
    number by changing what a facet looks like."""
    facet = _facet()
    executor = GovernanceActionExecutor(base=_StubBase([_envelope("action-a", [facet])]))

    outcome = await executor.execute(_step(), [{"amount": "1", "currency": "THB"}], _ctx())

    assert _lifted(outcome) == [facet]


async def test_a_step_with_no_producer_facet_lifts_nothing() -> None:
    """Advisory + never-raise: an action step whose event grounds no ฿ figure (or a vertical with
    no registered producer at all — ``building_materials`` today) adds nothing to the trace."""
    executor = GovernanceActionExecutor(base=_StubBase([_envelope("action-a", [])]))

    outcome = await executor.execute(_step(), [{"amount": "1", "currency": "THB"}], _ctx())

    assert _lifted(outcome) == []
    assert any(
        isinstance(t, dict) and t.get("kind") == "doa_tier_resolved"
        for t in outcome.reasoning_trace
    ), "the positive control: the instrument DOES see this step's own trace entries"
