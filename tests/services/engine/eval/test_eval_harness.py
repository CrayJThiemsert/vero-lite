"""Eval harness for the stochastic LLM recommender (PLAN-0006 Step 7 / ADR-010 T3).

A stochastic ``recommend()`` cannot be pinned with bit-identical
assertions (ADR-010 T3, risk R5). This harness instead asserts the
INVARIANTS that must hold for EVERY model output, across a set of golden
traces under ``golden_traces/`` — one recorded gpt-oss:20b capture plus
representative outputs covering the stochastic spread.

"The eval passes" means, for every golden trace:

1. it validates as an :class:`LlmJudgment` — schema-valid, every
   required field present;
2. ``confidence`` is within ``[0, 1]``;
3. its ``suggested_handler`` resolves to a registered handler; and
4. it composes into a schema-valid ADR-007 D2 ``RecommendedAction``
   whose hybrid trace carries an ``llm_inference`` step plus at least
   one harness-emitted step, with ``actor_kind == "llm"``.

It does NOT mean any output equals a fixed reference string. New golden
traces are added by dropping a JSON file into ``golden_traces/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from services.engine.actions import RecommendedAction
from services.engine.llm.structured import JudgmentResult, LlmJudgment
from services.engine.recommender import _compose_llm_record
from services.engine.registry import registry

_GOLDEN_DIR = Path(__file__).parent / "golden_traces"


def _load_golden_traces() -> list[dict[str, Any]]:
    """Load every golden-trace fixture, sorted by filename."""
    return [
        json.loads(path.read_text(encoding="utf-8")) for path in sorted(_GOLDEN_DIR.glob("*.json"))
    ]


_GOLDEN = _load_golden_traces()
_IDS = [trace["name"] for trace in _GOLDEN]


async def _noop_handler(_action: Any) -> dict[str, Any]:
    return {}


def test_golden_fixture_set_is_non_empty() -> None:
    """The eval is meaningless without fixtures — guard against an empty set."""
    assert _GOLDEN, "expected at least one golden trace under golden_traces/"


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_validates_as_llm_judgment(trace: dict[str, Any]) -> None:
    """Invariant 1: every golden trace is a schema-valid LlmJudgment."""
    judgment = LlmJudgment.model_validate(trace["model_output"])
    assert judgment.title
    assert judgment.affected_entities


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_confidence_in_range(trace: dict[str, Any]) -> None:
    """Invariant 2: confidence is within [0, 1] (advisory — ADR-010 IN-3)."""
    judgment = LlmJudgment.model_validate(trace["model_output"])
    assert 0.0 <= judgment.confidence <= 1.0


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_handler_resolves(trace: dict[str, Any]) -> None:
    """Invariant 3: suggested_handler resolves to a registered handler."""
    registry.register_handler("energy", "echo", _noop_handler)
    judgment = LlmJudgment.model_validate(trace["model_output"])
    # raises RegistryError if it does not resolve
    registry.get_handler("energy", judgment.suggested_handler)


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_composes_to_valid_envelope(trace: dict[str, Any]) -> None:
    """Invariant 4: the trace composes into a schema-valid hybrid envelope."""
    judgment = LlmJudgment.model_validate(trace["model_output"])
    result = JudgmentResult(
        judgment=judgment,
        thinking="recorded reasoning narrative",
        draft="recorded draft",
        model="gpt-oss:20b",
        attempts=1,
    )
    record = _compose_llm_record(trace["event"], "energy", result)
    action = record.action

    # the composed envelope round-trips as an ADR-007 D2 RecommendedAction
    assert RecommendedAction.model_validate(action.model_dump()) == action

    kinds = [step.kind for step in action.reasoning_trace]
    assert "llm_inference" in kinds
    assert any(kind in {"ontology_query", "rule_check"} for kind in kinds)
    assert action.audit_metadata.actor_kind == "llm"
    assert action.requires_approval is True
