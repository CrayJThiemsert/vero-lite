"""PLAN-0022 Phase 2a — the deterministic ``evaluate`` StepExecutor (SD-6).

Offline, pure-Python (no DB, no LLM — the executor makes no LLM call by
construction, which IS the ADR-0019 determinism invariant). Exercises verdict
tagging from the Step-authored band, field preservation, the loud failure modes
(band-less step; unreadable entity), and the fail-safe direction default.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import ProcedureError, RunContext
from services.engine.procedures.spec import Agent, Step, StepKind

# The aquaculture worked-example band: breach BELOW 4.0, watch band 1.0 (4.0-5.0).
_BAND = {"threshold": 4.0, "direction": "below", "watch_margin": 1.0}


def _step(**band: Any) -> Step:
    return Step.model_validate(
        {"step_id": "judge", "name": "Judge", "kind": StepKind.EVALUATE.value, **band}
    )


def _ctx() -> RunContext:
    return RunContext(agent=Agent(agent_id="pond_agent", name="Pond Agent"), vertical="aquaculture")


def _pond(pond_id: str, value: Any) -> dict[str, Any]:
    return {"pond_id": pond_id, "event_id": f"e-{pond_id}", "measured_value": value}


async def test_tags_each_entity_with_its_deterministic_verdict() -> None:
    """breach / watch / ok per the authored band — the where: {verdict: ...}
    fan-out key the downstream steps filter on."""
    executor = EvaluateStepExecutor()
    ponds = [_pond("p1", 3.2), _pond("p2", 4.5), _pond("p3", 6.1)]

    outcome = await executor.execute(_step(**_BAND), ponds, _ctx())

    assert [e["verdict"] for e in outcome.output] == ["breach", "watch", "ok"]


async def test_preserves_entity_fields_and_only_adds_verdict() -> None:
    executor = EvaluateStepExecutor()
    pond = _pond("p1", 3.2)

    outcome = await executor.execute(_step(**_BAND), [pond], _ctx())

    assert outcome.output == [{**pond, "verdict": "breach"}]
    assert pond == _pond("p1", 3.2), "the input entity must not be mutated"


async def test_absent_watch_margin_collapses_the_band() -> None:
    """AC-9 semantics at the executor level: no watch_margin -> not-breach is ok."""
    executor = EvaluateStepExecutor()
    step = _step(threshold=4.0, direction="below")

    outcome = await executor.execute(step, [_pond("p1", 4.5)], _ctx())

    assert outcome.output[0]["verdict"] == "ok"


async def test_unset_direction_fails_safe_to_above() -> None:
    """Mirrors crosses_threshold: an unauthored direction means 'above'."""
    executor = EvaluateStepExecutor()
    step = _step(threshold=90.0, watch_margin=5.0)

    outcome = await executor.execute(
        step, [_pond("a1", 96.5), _pond("a2", 86.0), _pond("a3", 70.0)], _ctx()
    )

    assert [e["verdict"] for e in outcome.output] == ["breach", "watch", "ok"]


async def test_empty_input_set_yields_empty_output() -> None:
    executor = EvaluateStepExecutor()

    outcome = await executor.execute(_step(**_BAND), [], _ctx())

    assert outcome.output == []
    assert outcome.reasoning_trace[0]["counts"] == {"breach": 0, "watch": 0, "ok": 0}


async def test_bandless_step_raises_procedure_error() -> None:
    """A band-less evaluate step is a config error for THIS executor (callers with
    NL-only judge steps keep providing their own executor — AC-9)."""
    executor = EvaluateStepExecutor()

    with pytest.raises(ProcedureError, match="no authored threshold"):
        await executor.execute(_step(), [_pond("p1", 3.2)], _ctx())


@pytest.mark.parametrize("bad_value", [None, "low", True])
async def test_entity_without_numeric_reading_raises(bad_value: Any) -> None:
    """An unreadable reading fails LOUDLY (D4 diverts it) — never a silent verdict.
    bool is rejected explicitly (int subclass; True must not judge as 1.0)."""
    executor = EvaluateStepExecutor()

    with pytest.raises(ValueError, match="no numeric 'measured_value'"):
        await executor.execute(_step(**_BAND), [_pond("p1", bad_value)], _ctx())


async def test_non_mapping_entity_raises() -> None:
    executor = EvaluateStepExecutor()

    with pytest.raises(ValueError, match="is not a mapping"):
        await executor.execute(_step(**_BAND), [3.2], _ctx())


async def test_trace_and_audit_record_the_band_and_counts() -> None:
    """Telemetry seam: the trace names the verdict split; the audit pins the
    authored band + the deterministic actor (auditability of the moat)."""
    executor = EvaluateStepExecutor()
    ponds = [_pond("p1", 3.2), _pond("p2", 2.8), _pond("p3", 4.5), _pond("p4", 6.1)]

    outcome = await executor.execute(_step(**_BAND), ponds, _ctx())

    trace = outcome.reasoning_trace[0]
    assert trace["kind"] == "verdict_computed"
    assert trace["counts"] == {"breach": 2, "watch": 1, "ok": 1}
    assert outcome.audit is not None
    assert outcome.audit["deterministic"] is True
    assert outcome.audit["threshold"] == 4.0
    assert outcome.audit["direction"] == "below"
    assert outcome.audit["watch_margin"] == 1.0
