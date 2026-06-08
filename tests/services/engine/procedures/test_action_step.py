"""PLAN-0019 A-7 — the action-step adapter (ADR-016 D2/D3; AC A-7).

Offline: a fake ``ChatClient`` replays canned judgments and a spy handler proves
the shipped ``approve()`` -> ``execute()`` gate is REUSED (not re-implemented).
No DB, no live LLM (Lesson #7 §3 behavioural assertions). The DB-gated
suspend -> resolve -> resume flow lives in
``tests/services/db/test_procedure_action_gate.py``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.orchestrator import ProcedureError, RunContext
from services.engine.procedures.spec import Agent, AgentAllowed, Autonomy, Step, StepKind
from services.engine.registry import registry


class FakeChatClient:
    """Replays canned ChatResults in order; records every call's messages."""

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls.append({"think": think, "messages": messages})
        if not self._results:
            raise AssertionError("FakeChatClient exhausted its canned results")
        return self._results.pop(0)


class SpyHandler:
    """Records the actions it executes — proves whether the gate fired."""

    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def __call__(self, action: Any) -> dict[str, Any]:
        self.calls.append(action)
        return {"ok": True, "executed": action.id}


def _result(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _judgment_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "Start emergency aerator on pond p7",
        "description": "Dissolved oxygen fell below the 4 mg/L breach threshold.",
        "rationale": "DO 3.2 mg/L is a breach; aerate to recover oxygen.",
        "confidence": 0.92,
        "affected_entities": [{"object_type": "Pond", "primary_key": "p7"}],
        "suggested_handler": "aerate",
        "handler_payload": {"pond_id": "p7"},
    }
    base.update(overrides)
    return base


def _judgment_results(n: int, **overrides: Any) -> list[ChatResult]:
    """``n`` entities -> n*(call-1 draft + call-2 judgment) canned results."""
    out: list[ChatResult] = []
    for _ in range(n):
        out.append(_result("reasoning draft", thinking="thought"))
        out.append(_result(json.dumps(_judgment_dict(**overrides))))
    return out


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["aerate", "other"]),
    )


def _ctx(*, goal: str | None = None) -> RunContext:
    return RunContext(agent=_agent(), vertical="aquaculture", goal=goal)


def _action_step(*, autonomy: Autonomy, handler: str | None = "aerate") -> Step:
    return Step(step_id="act", name="Act", kind=StepKind.ACTION, autonomy=autonomy, handler=handler)


async def test_gated_action_proposes_without_executing() -> None:
    """A gated action only PROPOSES — the handler must NOT fire before approval."""
    spy = SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    executor = ActionStepExecutor(client_factory=lambda _m: FakeChatClient(_judgment_results(1)))

    outcome = await executor.execute(
        _action_step(autonomy=Autonomy.GATED), [{"pond": "p7", "event_id": "e7"}], _ctx()
    )

    assert len(outcome.output) == 1
    entry = outcome.output[0]
    assert entry["status"] == "proposed"
    assert entry["receipt"] is None
    assert entry["action"]["suggested_handler"] == "aerate"
    assert spy.calls == [], "a gated action must not execute its handler before approval"
    assert outcome.reasoning_trace[0]["kind"] == "action_proposed"


async def test_auto_action_executes_inline() -> None:
    """An auto action approves + executes inline (no human gate)."""
    spy = SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    executor = ActionStepExecutor(client_factory=lambda _m: FakeChatClient(_judgment_results(1)))

    outcome = await executor.execute(
        _action_step(autonomy=Autonomy.AUTO), [{"pond": "p7", "event_id": "e7"}], _ctx()
    )

    entry = outcome.output[0]
    assert entry["status"] == "executed"
    assert entry["receipt"] == {"ok": True, "executed": "action-e7"}
    assert len(spy.calls) == 1
    assert outcome.reasoning_trace[0]["kind"] == "action_executed"


async def test_suggested_handler_is_step_handler_not_llm_guess() -> None:
    """The composed envelope uses the author's declared step.handler, deterministic
    and allowlist-bounded — NOT the model's suggested_handler."""
    registry.register_handler("aquaculture", "aerate", SpyHandler())
    registry.register_handler("aquaculture", "other", SpyHandler())
    # the model judges 'other' (registered, passes the semantic check) ...
    fake = FakeChatClient(_judgment_results(1, suggested_handler="other"))
    executor = ActionStepExecutor(client_factory=lambda _m: fake)

    # ... but the step declares 'aerate' — the author's declaration wins.
    outcome = await executor.execute(
        _action_step(autonomy=Autonomy.GATED, handler="aerate"),
        [{"pond": "p7", "event_id": "e7"}],
        _ctx(),
    )

    assert outcome.output[0]["action"]["suggested_handler"] == "aerate"


async def test_set_valued_one_action_per_entity() -> None:
    """Set semantics: one RecommendedAction per entity in the input set (no loop)."""
    registry.register_handler("aquaculture", "aerate", SpyHandler())
    executor = ActionStepExecutor(client_factory=lambda _m: FakeChatClient(_judgment_results(2)))

    outcome = await executor.execute(
        _action_step(autonomy=Autonomy.GATED),
        [{"pond": "p3", "event_id": "e3"}, {"pond": "p7", "event_id": "e7"}],
        _ctx(),
    )

    assert len(outcome.output) == 2
    assert {e["action_id"] for e in outcome.output} == {"action-e3", "action-e7"}


async def test_action_step_without_handler_raises() -> None:
    """An action step that declares no handler cannot propose an action."""
    executor = ActionStepExecutor(client_factory=lambda _m: FakeChatClient([]))
    with pytest.raises(ProcedureError, match="no handler"):
        await executor.execute(
            _action_step(autonomy=Autonomy.GATED, handler=None), [{"pond": "p7"}], _ctx()
        )


async def test_goal_is_threaded_into_action_reasoning() -> None:
    """A-8 x A-7: the executor threads ctx.goal into the reasoning system prompt."""
    registry.register_handler("aquaculture", "aerate", SpyHandler())
    fake = FakeChatClient(_judgment_results(1))
    executor = ActionStepExecutor(client_factory=lambda _m: fake)

    await executor.execute(
        _action_step(autonomy=Autonomy.GATED),
        [{"pond": "p7", "event_id": "e7"}],
        _ctx(goal="Run the morning pond health round."),
    )

    system = fake.calls[0]["messages"][0]["content"]
    assert "Run the morning pond health round." in system
