"""PLAN-0022 Phase 2b — the ``watch -> gated``-proposal routing (ADR-0019; SD-1=a).

Offline (no DB, mock ``ChatClient``): drives the REAL shipped aquaculture
"Morning Pond Health Round" spec with the REAL ``EvaluateStepExecutor`` (reading
the REAL Step-authored band from ``procedures.yaml``) + the REAL
``ActionStepExecutor``. Proves the load-bearing engine change end-to-end in
memory: the deterministic judge fans the watch subset into a ``gated``
``increase_water_exchange`` proposal that suspends at ``waiting_human`` — and
**AC-8**: that escalation fires from the engine's watch-band math, byte-for-byte
**independent of the model's ``confidence``** (ADR-010 IN-3 / ADR-0019
determinism invariant). The durable suspend/resolve/resume lifecycle for the new
step lives in ``tests/services/db/test_procedure_headline.py``.
"""

from __future__ import annotations

import json
from typing import Any

from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import (
    RunContext,
    StepExecutor,
    StepOutcome,
    execute_steps,
    run_procedure,
)
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Agent, Procedure, Step, StepKind, load_procedures
from services.engine.registry import RegistryError, registry

# Readings against the REAL authored band (threshold 4.0, below, watch_margin 1.0):
# one breach, one watch, one ok. object_type/primary_key are the ontology-projected
# entity keys _loop_entity_ref sources deterministically.
PONDS: list[dict[str, Any]] = [
    {"object_type": "Pond", "primary_key": "p1", "event_id": "e1", "measured_value": 3.2},
    {"object_type": "Pond", "primary_key": "p2", "event_id": "e2", "measured_value": 4.5},
    {"object_type": "Pond", "primary_key": "p3", "event_id": "e3", "measured_value": 6.1},
]


async def _noop_handler(_action: Any) -> dict[str, Any]:
    return {"ok": True}


def _register_handlers() -> None:
    """Idempotent within one test — the AC-8 test drives two full runs (the
    conftest registry reset is per-test, not per-run)."""
    for name in ("echo", "start_emergency_aerator", "increase_water_exchange"):
        try:
            registry.register_handler("aquaculture", name, _noop_handler)
        except RegistryError:
            pass  # already registered by this test's earlier run


class _FakeChat:
    """Pattern-B mock: a reasoning draft on call-1 (no ``response_format``), a canned
    judgment on call-2 — with an injectable ``confidence`` (the AC-8 variable)."""

    def __init__(self, confidence: float) -> None:
        self.confidence = confidence
        self.calls = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls += 1
        if response_format is None:
            return ChatResult(content="draft", thinking="t", model="gpt-oss:20b", raw={})
        judgment = {
            "title": "Increase water exchange",
            "description": "Borderline dissolved oxygen; precautionary water exchange.",
            "rationale": "DO sits in the 4-5 watch band.",
            "confidence": self.confidence,
            "affected_entities": [{"object_type": "Pond", "primary_key": "p"}],
            "suggested_handler": "echo",  # must be a REGISTERED handler (semantic check)
            "handler_payload": {},
        }
        return ChatResult(content=json.dumps(judgment), thinking=None, model="gpt-oss:20b", raw={})


class _Query:
    """Fixed-output query executor (the fake ``read_do``)."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=self.output, reasoning_trace=[{"kind": "query", "summary": "r"}])


def _headline() -> tuple[Procedure, Agent]:
    spec = load_procedures("aquaculture")
    proc = next(p for p in spec.procedures if p.procedure_id == "morning_pond_health_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return proc, agent


def _executors(chat: _FakeChat, ponds: list[dict[str, Any]]) -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Query(ponds),
        StepKind.EVALUATE: EvaluateStepExecutor(),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: chat),
    }


async def _run_to_escalation(
    confidence: float, ponds: list[dict[str, Any]]
) -> tuple[list[Any], list[Any], _FakeChat]:
    """Run the headline to the aerate suspend, then continue past it to the
    escalate_watch suspend (the control-plane continuation ``resume_run`` drives
    in production, DB-free here). Returns (judge output, escalation step results,
    the chat mock)."""
    _register_handlers()
    procedure, agent = _headline()
    chat = _FakeChat(confidence)
    executors = _executors(chat, ponds)

    first = await run_procedure(procedure, agent, executors, vertical="aquaculture", run_id="r1")
    assert first.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert first.step_results[-1].step_id == "aerate", "the breach gate suspends first"
    judge_sr = next(sr for sr in first.step_results if sr.step_id == "judge")
    judge_output = (judge_sr.artifact or {})["output_set"]

    ctx = RunContext(agent=agent, vertical="aquaculture", goal=procedure.goal or None)
    escalate_index = next(i for i, s in enumerate(procedure.steps) if s.step_id == "escalate_watch")
    results, status = await execute_steps(
        procedure.steps,
        executors,
        ctx,
        "r1",
        prior_outputs={"judge": judge_output},
        start_index=escalate_index,
    )
    assert status is PipelineRunStatus.WAITING_HUMAN
    return judge_output, results, chat


async def test_watch_subset_routes_to_a_gated_proposal() -> None:
    """The load-bearing 2b wiring: the REAL judge band fans the watch pond into a
    gated proposal — the author's escalation handler, suspended for the human."""
    judge_output, results, _chat = await _run_to_escalation(0.9, PONDS)

    assert [e["verdict"] for e in judge_output] == ["breach", "watch", "ok"]
    escalation = results[0]
    assert escalation.step_id == "escalate_watch"
    assert escalation.status == StepResultStatus.WAITING_HUMAN.value
    proposals = (escalation.artifact or {})["output_set"]
    assert [p["action_id"] for p in proposals] == ["action-e2"], "only the watch subset"
    proposal = proposals[0]
    assert proposal["status"] == "proposed", "gated: proposed, never executed before approval"
    # The executed handler is the AUTHOR's escalation handler (step.handler override),
    # and the affected entity is the deterministic loop entity — not model guesses.
    assert proposal["action"]["suggested_handler"] == "increase_water_exchange"
    (entity,) = proposal["action"]["affected_entities"]
    assert (entity["object_type"], entity["primary_key"]) == ("Pond", "p2")


async def test_empty_watch_set_still_suspends_with_no_proposals() -> None:
    """Parity with the pre-amendment human_task: suspension is step-kind-based, so
    an empty watch set parks at waiting_human with zero proposals (a plain
    resume_run threads it forward — no resolve needed)."""
    no_watch = [
        {"object_type": "Pond", "primary_key": "p1", "event_id": "e1", "measured_value": 3.2},
        {"object_type": "Pond", "primary_key": "p3", "event_id": "e3", "measured_value": 6.1},
    ]
    _judge, results, _chat = await _run_to_escalation(0.9, no_watch)

    escalation = results[0]
    assert escalation.status == StepResultStatus.WAITING_HUMAN.value
    assert (escalation.artifact or {})["output_set"] == []


async def test_ac8_watch_escalation_is_independent_of_confidence() -> None:
    """AC-8 (the PLAN-0022 determinism test): the watch -> gated escalation fires
    from the engine's watch-band math and is INDEPENDENT of the model's
    ``confidence`` — identical routing under a near-zero and a near-one confidence;
    confidence appears only as advisory metadata on the proposal (ADR-010 IN-3)."""
    judge_low, results_low, chat_low = await _run_to_escalation(0.05, PONDS)
    judge_high, results_high, chat_high = await _run_to_escalation(0.99, PONDS)

    # The deterministic judge never consulted the model at all.
    assert judge_low == judge_high

    low = (results_low[0].artifact or {})["output_set"]
    high = (results_high[0].artifact or {})["output_set"]
    # Identical routing: the same (single) watch entity escalates, same handler,
    # same affected entities, same proposed status.
    assert [p["action_id"] for p in low] == [p["action_id"] for p in high] == ["action-e2"]
    assert low[0]["action"]["suggested_handler"] == high[0]["action"]["suggested_handler"]
    assert low[0]["action"]["affected_entities"] == high[0]["action"]["affected_entities"]
    assert low[0]["status"] == high[0]["status"] == "proposed"
    # confidence flowed through as ADVISORY metadata only — surfaced, not routing.
    assert low[0]["action"]["confidence"] == 0.05
    assert high[0]["action"]["confidence"] == 0.99
    # And the model was consulted only AFTER routing, on already-routed subsets —
    # never by the judge: 2 Pattern-B calls for the 1 breach entity (aerate) +
    # 2 for the 1 routed watch entity (escalate_watch) account for EVERY call.
    assert chat_low.calls == chat_high.calls == 4
