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
   one harness-emitted step, with ``actor_kind == "llm"``; and
5. **the envelope the system composes today equals the one recorded in
   the trace** (PLAN-0107 AC-9), ``created_at`` excluded.

Invariants 1-4 compare each file to *itself* — they redden on a malformed
fixture and cannot redden on a composition regression. Invariant 5 is the
one that scores the SYSTEM against the corpus, which is what makes this an
oracle rather than a self-consistency check (CLAUDE.md §8). It does NOT
pin the stochastic model output: the recorded ``model_output`` is an INPUT
to invariant 5, and only the deterministic composition downstream of it is
compared.

New golden traces are added by writing the ``event`` + ``model_output``
(plus ``vertical`` / ``judgment_context`` where they differ from energy's
defaults) and then running ``python -m tools.golden_trace refresh`` to
record ``expected_envelope``. Dropping in a JSON file by hand leaves that
key absent, and invariant 5 fails loudly rather than passing quietly.
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
from tools.golden_trace import (
    DEFAULT_VERTICAL,
    envelope_diff,
    expected_envelope_for,
    judgment_context,
)

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
    """Invariant 3: suggested_handler resolves to a registered handler.

    Resolution is per-vertical, so this reads the trace's own vertical rather
    than assuming energy — traces 04+ cover other ontologies (PLAN-0107 AC-9).
    """
    vertical = trace.get("vertical", DEFAULT_VERTICAL)
    # Register the known handler set, NOT the handler the trace happens to name —
    # registering judgment.suggested_handler here would make the assertion below
    # true by construction and pin nothing.
    registry.register_handler(vertical, "echo", _noop_handler)
    judgment = LlmJudgment.model_validate(trace["model_output"])
    # raises RegistryError if it does not resolve
    registry.get_handler(vertical, judgment.suggested_handler)


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_composes_to_valid_envelope(trace: dict[str, Any]) -> None:
    """Invariant 4: the trace composes into a schema-valid hybrid envelope."""
    judgment = LlmJudgment.model_validate(trace["model_output"])
    context = judgment_context(trace)
    result = JudgmentResult(
        judgment=judgment,
        thinking=context["thinking"],
        draft=context["draft"],
        model=context["model"],
        attempts=context["attempts"],
    )
    # PLAN-0030 added resolved-entities + resolution-trace params; PLAN-0035 added the
    # member-(b) verification-trace param; PLAN-0071 added the economic-impact trace
    # param. This golden test exercises trace COMPOSITION, not
    # resolution/verification/economics -> pass the verbatim entities + no steps.
    record = _compose_llm_record(
        trace["event"],
        trace.get("vertical", DEFAULT_VERTICAL),
        result,
        judgment.affected_entities,
        [],
        [],
        [],
    )
    action = record.action

    # the composed envelope round-trips as an ADR-007 D2 RecommendedAction
    assert RecommendedAction.model_validate(action.model_dump()) == action

    kinds = [step.kind for step in action.reasoning_trace]
    assert "llm_inference" in kinds
    assert any(kind in {"ontology_query", "rule_check"} for kind in kinds)
    assert action.audit_metadata.actor_kind == "llm"
    assert action.requires_approval is True


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_records_an_expected_envelope(trace: dict[str, Any]) -> None:
    """Invariant 5, precondition: the expectation is actually recorded.

    Split from the comparison below on purpose. A trace with no
    ``expected_envelope`` is an unrecorded expectation, and an absence
    assertion folded into the comparison would let the whole corpus go
    vacuous the moment the key stopped being written (CLAUDE.md §8 — a
    negative assertion carries its own positive control or it is empty).
    """
    assert trace.get("expected_envelope"), (
        f"trace '{trace['name']}' records no expected_envelope — "
        "run `python -m tools.golden_trace refresh` to record one"
    )


@pytest.mark.parametrize("trace", _GOLDEN, ids=_IDS)
def test_golden_trace_matches_system_composition(trace: dict[str, Any]) -> None:
    """Invariant 5: the SYSTEM's composed envelope equals the recorded one.

    This is the assertion that makes the corpus an oracle of the system rather
    than a self-consistency check: ``recorded`` is read from disk, ``produced``
    is composed live, so a regression anywhere in ``_compose_llm_record`` or
    the trace builders it calls diverges here. ``created_at`` is the only
    excluded field — see ``tools.golden_trace.producer`` for the measurement
    behind that exclusion.
    """
    recorded = trace["expected_envelope"]
    produced = expected_envelope_for(trace)
    assert envelope_diff(recorded, produced) == [], (
        f"trace '{trace['name']}' no longer describes the system. If the change "
        "was intended, re-record with `python -m tools.golden_trace refresh` and "
        "review the resulting diff as part of the change."
    )
