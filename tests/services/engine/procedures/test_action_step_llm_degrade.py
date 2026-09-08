"""PLAN-0119 Step 4 / AC-6 — the action step degrades, disclosed, when the LLM arm fails (D-1).

Its own module (battery denominators — see ``test_capacity.py``'s header).

**The defect.** ``generate_judgment`` raising ``OllamaError`` or
``StructuredOutputError`` escaped ``ActionStepExecutor.execute`` and reached the
orchestrator's D4 fail-and-divert, which recorded a ``FAILED`` / ``WAITING_HUMAN``
step carrying a bare ``error`` trace and **no judgment**. The reviewer inherited a
stack-trace fragment where a governed decision should have been. The recommender
has degraded gracefully for this since PLAN-0093; the action step never has.

**Why the base executor.** The fix lives in ``ActionStepExecutor.execute``, which
is what the governance wrapper delegates to, so this is the real seam rather than
a layer above it — the same argument ``test_action_step_economic_trace.py`` makes
at length for the economic facet. The vertical is ``procurement`` because that is
the path AC-6 names.

Offline by construction: fault-injecting local doubles, no MS-S1, no DB
(CLAUDE.md section 8).
"""

from __future__ import annotations

from typing import Any

import pytest

from services.engine.llm.client import ChatResult, OllamaError
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

_VERTICAL = "procurement"
_HANDLER = "raise_po"

_executed: list[str] = []


@pytest.fixture(autouse=True)
def _handler() -> None:
    """A registered handler, and a spy on whether it ever RAN.

    The spy is the load-bearing half: AC-6's fix must not buy a degraded action
    the right to execute, and the only honest way to check that is to watch the
    handler itself rather than a status field.
    """
    _executed.clear()

    async def raise_po(action: Any) -> dict[str, Any]:
        _executed.append(action.id)
        return {"ok": True}

    registry.register_handler(_VERTICAL, _HANDLER, raise_po)


class _UnreachableArm:
    """A client whose every call fails the way a dead MS-S1 fails."""

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> ChatResult:
        raise OllamaError("Ollama call to /api/chat failed: connection refused")


class _UnparseableArm:
    """A reachable model that never produces a valid envelope.

    Drives ``generate_judgment``'s retry loop to exhaustion, which is the OTHER
    failure AC-6 names -- and a different code path from the transport one, since
    the client itself never raises here.
    """

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> ChatResult:
        return ChatResult(
            content="not an envelope",
            thinking=None,
            model="gpt-oss:20b",
            raw={"done_reason": "stop", "message": {"role": "assistant", "content": "x"}},
        )


def _executor(client: Any) -> ActionStepExecutor:
    """An executor whose arm is ``client``.

    ``client_factory`` is called as ``factory(ctx.agent.llm_model)`` -- it takes
    the per-agent model override -- so the lambda accepts and ignores it. The
    shipped ``advisory_stub_factory`` has that same one-argument shape, which is
    why the healthy control below passes the factory itself rather than calling it.
    """
    return ActionStepExecutor(client_factory=lambda _model: client)


def _healthy_executor() -> ActionStepExecutor:
    return ActionStepExecutor(client_factory=advisory_stub_factory)


def _step(autonomy: Autonomy = Autonomy.GATED) -> Step:
    return Step(
        step_id="raise_po",
        name="Raise PO",
        kind=StepKind.ACTION,
        autonomy=autonomy,
        handler=_HANDLER,
    )


def _ctx(ceiling: Autonomy = Autonomy.GATED) -> RunContext:
    return RunContext(
        agent=Agent(
            agent_id="procurement_agent",
            name="Procurement Agent",
            autonomy_ceiling=ceiling,
            allowed=AgentAllowed(action_handlers=[_HANDLER]),
        ),
        vertical=_VERTICAL,
    )


def _entities() -> list[Any]:
    return [{"event_id": "e1", "event_type": "quote_received", "measured_value": 12000}]


def _action(outcome: StepOutcome) -> dict[str, Any]:
    assert len(outcome.output) == 1, f"expected one action, got {len(outcome.output)}"
    action = outcome.output[0]["action"]
    assert isinstance(action, dict)
    return action


def _disclosures(action: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        step
        for step in action["reasoning_trace"]
        if step.get("detail", {}).get("recommendation_mode") == "llm-degrade-stand-in"
    ]


# --------------------------------------------------------------------------
# The degrade happens at all
# --------------------------------------------------------------------------


async def test_a_dead_arm_yields_an_action_instead_of_escaping_the_step() -> None:
    """AC-6's core claim. Before this the exception left ``execute`` entirely."""
    outcome = await _executor(_UnreachableArm()).execute(_step(), _entities(), _ctx())

    assert (
        len(outcome.output) == 1
    ), f"a failed arm must still produce a governed action; output={outcome.output}"


async def test_an_unparseable_arm_degrades_the_same_way() -> None:
    """The second failure AC-6 names, reached by a different path: the client
    never raises, and ``generate_judgment``'s retry loop exhausts instead.
    """
    outcome = await _executor(_UnparseableArm()).execute(_step(), _entities(), _ctx())

    assert (
        len(_disclosures(_action(outcome))) == 1
    ), "an exhausted structuring loop must degrade with a disclosure, not escape"


# --------------------------------------------------------------------------
# It is DISCLOSED, and not dressed as model reasoning
# --------------------------------------------------------------------------


async def test_the_degraded_action_discloses_that_no_model_judgment_stands_behind_it() -> None:
    """SD-8 = (b). An undisclosed stand-in is worse than the bare error it
    replaced: it looks exactly like a judgment somebody made.
    """
    outcome = await _executor(_UnreachableArm()).execute(_step(), _entities(), _ctx())

    [disclosure] = _disclosures(_action(outcome))
    assert (
        disclosure["detail"]["llm_status"] == "OllamaError"
    ), f"the disclosure must name the failure type; detail={disclosure['detail']}"


async def test_the_degraded_trace_carries_no_model_asserted_narrative() -> None:
    """🔴 The property that keeps this fix honest.

    ``build_llm_reasoning_trace`` emits an ``llm_inference`` step carrying a
    MODEL-ASSERTED narrative (ADR-010 D3). There is no model assertion here, so
    presenting a harness-authored stand-in in that shape would be exactly the
    mislabelling that trace kind exists to prevent.

    Carries its own positive control: the trace must be non-empty first, or
    "contains no llm_inference step" would be satisfied by an empty list.
    """
    outcome = await _executor(_UnreachableArm()).execute(_step(), _entities(), _ctx())
    trace = _action(outcome)["reasoning_trace"]

    assert trace, "positive control failed -- a degraded action still needs a trace"
    kinds = [step.get("kind") for step in trace]
    assert (
        "llm_inference" not in kinds
    ), f"a degraded action must not claim model reasoning; kinds={kinds}"


async def test_the_degraded_action_asserts_no_confidence() -> None:
    """Advisory either way (ADR-010 IN-3), but stated rather than omitted so
    nothing downstream reads a missing value as a high one."""
    outcome = await _executor(_UnreachableArm()).execute(_step(), _entities(), _ctx())

    assert _action(outcome)["confidence"] == 0.0, f"got confidence={_action(outcome)['confidence']}"


async def test_the_declared_handler_and_entity_survive_the_degrade() -> None:
    """What the reviewer actually needs, and what a bare ``error`` trace destroyed:
    the procedure author's declared handler and the entity in question.
    """
    action = _action(await _executor(_UnreachableArm()).execute(_step(), _entities(), _ctx()))

    # ``primary_key``, not ``entity_id`` — ``_loop_entity_ref`` builds an
    # ``EntityRef(object_type, primary_key)`` and falls back to the event's
    # ``event_id`` for the key. Derived from the builder rather than assumed.
    carried = (
        action["suggested_handler"],
        [e["primary_key"] for e in action["affected_entities"]],
    )
    assert carried == (_HANDLER, ["e1"]), f"got {carried}"


# --------------------------------------------------------------------------
# 🔴 The safety property this fix must not spend
# --------------------------------------------------------------------------


async def test_a_degraded_action_is_never_auto_executed() -> None:
    """🔴 PRESERVED, not new.

    Before AC-6 the exception failed the step outright, so no run has ever
    auto-executed a handler on a failed LLM arm. Disclosing the failure must not
    quietly buy execution rights the old behaviour did not grant. The handler spy
    is watched rather than a status field, because a status can be right while
    the side effect already happened.
    """
    outcome = await _executor(_UnreachableArm()).execute(
        _step(Autonomy.AUTO), _entities(), _ctx(Autonomy.AUTO)
    )

    assert (
        _executed == []
    ), f"a degraded action must never reach the handler; it ran for {_executed}"
    assert (
        outcome.output[0]["receipt"] is None
    ), f"a degraded action must carry no execution receipt; got {outcome.output[0]['receipt']}"


async def test_a_healthy_arm_under_auto_still_executes() -> None:
    """🔴 THE POSITIVE CONTROL for the test above.

    "the handler did not run" is satisfied by a step that never runs anything.
    Without this, a degrade stuck permanently on -- or an executor that had
    stopped executing altogether -- would read as correct.
    """
    outcome = await _healthy_executor().execute(
        _step(Autonomy.AUTO), _entities(), _ctx(Autonomy.AUTO)
    )

    assert _executed, "positive control failed -- a healthy AUTO action must execute"
    assert _disclosures(_action(outcome)) == [], "a healthy arm must not emit a degrade disclosure"
