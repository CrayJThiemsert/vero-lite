"""Tests for governed action verify+reshape — the deterministic floor.

ADR-0022 member (b) / PLAN-0035 Phase 1. Offline + deterministic: constructed
``LlmJudgment`` objects and a fake ``ChatClient`` drive the verify (no live Ollama,
no host-state). Asserts the CONTRACT (a consistent
proposal kept; a prose-omission reshaped from the structured handler; the wrong-handler
NOT rescued (AC-5); echo / an unregistered handler skipped; the end-to-end recommend()
trace; the D-6 import boundary), not incidental shape (Lesson #7 §3).
"""

from __future__ import annotations

import ast
import json
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from services.engine.action_verification import (
    VERIFICATION_MODE_DETERMINISTIC,
    verify_action_expression,
)
from services.engine.actions import EntityRef
from services.engine.llm.client import ChatResult
from services.engine.llm.structured import LlmJudgment
from services.engine.recommender import recommend
from services.engine.registry import registry

_AQUA_ACTIONS = ("start_emergency_aerator", "increase_water_exchange", "dispatch_technician")


# --- fakes + helpers ------------------------------------------------------


class _FakeAdapter:
    """Minimal energy-shaped DataAdapter serving a fixed object universe."""

    vertical_name = "energy"

    def __init__(self, objects: dict[str, list[dict[str, Any]]]) -> None:
        self._objects = objects

    async def fetch_objects(
        self, object_type: str, filter_expr: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        return self._objects.get(object_type, [])

    async def fetch_links(
        self, link_type: str, from_pk: str | None = None, to_pk: str | None = None
    ) -> list[dict[str, Any]]:
        return []

    async def stream_events(
        self, event_type: str, since: datetime | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        _none: list[dict[str, Any]] = []
        for event in _none:  # pragma: no cover - never streamed in these tests
            yield event

    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok"}


class _FakeChatClient:
    """Replays canned ChatResults (mirrors test_recommender / test_entity_resolution)."""

    def __init__(self, *, results: list[ChatResult]) -> None:
        self._results = list(results)

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        return self._results.pop(0)


async def _stub(_action: Any) -> dict[str, Any]:
    return {"executed": True}


def _register_aqua_handlers(vertical: str = "aquaculture") -> None:
    registry.register_handler(vertical, "echo", _stub)
    for name in _AQUA_ACTIONS:
        registry.register_handler(vertical, name, _stub)


def _register_assets(*asset_ids: str) -> None:
    objects = {"Asset": [{"asset_id": aid, "name": aid} for aid in asset_ids]}
    registry.register_adapter(_FakeAdapter(objects))


def _chat(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _judgment(
    *,
    handler: str,
    title: str = "Start the emergency aerator on pond A116",
    description: str = "Dissolved oxygen crossed the breach threshold; start the aerator now.",
    rationale: str = "Aeration restores dissolved oxygen above the safe band.",
) -> LlmJudgment:
    return LlmJudgment(
        title=title,
        description=description,
        rationale=rationale,
        confidence=0.9,
        affected_entities=[EntityRef(object_type="Pond", primary_key="pond-A116")],
        suggested_handler=handler,
        handler_payload={},
    )


# The 5 §B-3 "assessment-prose" shape: the structured handler is correct, but the prose
# is framed as a breach assessment that never states the action verb/object.
_OMITTING = {
    "title": "Assess the dissolved-oxygen breach on pond A116",
    "description": (
        "Conduct a breach assessment: verify the reading, inspect the pond, document it."
    ),
    "rationale": "A structured breach assessment is the response to the threshold crossing.",
}


def _detail(step: Any) -> dict[str, Any]:
    assert step.kind == "action_verification"
    assert step.detail is not None
    return step.detail


# --- verify_action_expression: the contract (AC-1/2/3/4/5) ----------------


def test_consistent_proposal_is_kept_with_a_consistent_trace() -> None:
    """AC-2: prose that expresses the handler's action -> outcome 'consistent' (no reshape)."""
    _register_aqua_handlers()
    steps = verify_action_expression(_judgment(handler="start_emergency_aerator"), "aquaculture")

    assert len(steps) == 1
    detail = _detail(steps[0])
    assert detail["outcome"] == "consistent"
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC


def test_prose_omission_is_reshaped_from_the_structured_handler() -> None:
    """AC-3: prose omits the action (the 5-case shape) -> reshaped, surfaced from the handler."""
    _register_aqua_handlers()
    steps = verify_action_expression(
        _judgment(handler="start_emergency_aerator", **_OMITTING), "aquaculture"
    )

    detail = _detail(steps[0])
    assert detail["outcome"] == "reshaped"
    assert detail["surfaced_action"] == "start_emergency_aerator"  # from the structured handler
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC


def test_wrong_handler_is_not_rescued() -> None:
    """AC-5 (BINDING anti-regression): member (b) reshapes the EXPRESSION, never the
    SELECTION — a wrong handler stays wrong; the surfaced action is the model's own
    (wrong) handler, never silently corrected to the right one."""
    _register_aqua_handlers()
    # The model chose the wrong action (increase_water_exchange) AND omitted it in prose.
    steps = verify_action_expression(
        _judgment(handler="increase_water_exchange", **_OMITTING), "aquaculture"
    )

    detail = _detail(steps[0])
    assert detail["outcome"] == "reshaped"
    assert detail["surfaced_action"] == "increase_water_exchange"  # the wrong handler, faithfully
    assert detail["surfaced_action"] != "start_emergency_aerator"  # NOT rescued to the right one


def test_echo_no_op_handler_is_skipped() -> None:
    """AC: the no-op round-summary terminal is not an operational action -> skipped."""
    _register_aqua_handlers()
    steps = verify_action_expression(_judgment(handler="echo"), "aquaculture")

    assert _detail(steps[0])["outcome"] == "skipped"


def test_unregistered_handler_is_skipped_not_fabricated() -> None:
    """AC: a handler not registered for the vertical -> skipped (never fabricate an action)."""
    _register_aqua_handlers()
    steps = verify_action_expression(_judgment(handler="teleport_pond"), "aquaculture")

    assert _detail(steps[0])["outcome"] == "skipped"


# --- integration via recommend() (AC-1 end-to-end) ------------------------


def _crossing_event() -> dict[str, Any]:
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


def _judgment_json(*, handler: str, title: str, description: str, rationale: str) -> str:
    return json.dumps(
        {
            "title": title,
            "description": description,
            "rationale": rationale,
            "confidence": 0.9,
            "affected_entities": [{"object_type": "Asset", "primary_key": "asset-battery-01"}],
            "suggested_handler": handler,
            "handler_payload": {"event_id": "event-reading-03"},
        }
    )


async def test_recommend_reshapes_a_prose_omission_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: the LLM path adds an action_verification step; a prose-omission with a
    correct structured handler reshapes (surfaced from the handler) in the governed trace."""
    registry.register_handler("energy", "echo", _stub)
    registry.register_handler("energy", "start_emergency_aerator", _stub)
    _register_assets("asset-battery-01")
    judgment = _judgment_json(
        handler="start_emergency_aerator",
        title="Assess the over-temperature breach on the battery",
        description="Conduct a breach assessment: verify the reading, inspect the asset.",
        rationale="A structured breach assessment is the correct response to the crossing.",
    )
    fake = _FakeChatClient(results=[_chat("draft", thinking="r"), _chat(judgment)])
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "llm"  # the LLM path completed
    verif = [s for s in record.action.reasoning_trace if s.kind == "action_verification"]
    assert len(verif) == 1
    assert verif[0].detail is not None
    assert verif[0].detail["outcome"] == "reshaped"
    assert verif[0].detail["surfaced_action"] == "start_emergency_aerator"


async def test_recommend_verification_error_falls_back_to_rule_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-7 / IN-4: a verify error propagates to the deterministic fail-safe, never the loop."""
    registry.register_handler("energy", "echo", _stub)
    registry.register_handler("energy", "start_emergency_aerator", _stub)
    _register_assets("asset-battery-01")
    judgment = _judgment_json(
        handler="start_emergency_aerator",
        title="Start the emergency aerator",
        description="Start the aerator now.",
        rationale="Aeration restores dissolved oxygen.",
    )
    fake = _FakeChatClient(results=[_chat("draft", thinking="r"), _chat(judgment)])
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: fake)

    def _boom(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("verify exploded")

    monkeypatch.setattr("services.engine.recommender.verify_action_expression", _boom)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "engine"  # the deterministic fail-safe


# --- D-6 contamination boundary (BINDING) ---------------------------------


def _imported_modules(path: Path) -> set[str]:
    """The module names imported by the file at ``path`` (AST, not substrings)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_d6_verifier_imports_nothing_from_benchmarks() -> None:
    """D-6: the product verifier imports nothing from benchmarks/."""
    import services.engine.action_verification as av

    modules = _imported_modules(Path(av.__file__))
    assert not any(m.startswith("benchmark") for m in modules), modules


def test_d6_benchmark_grader_does_not_import_the_verifier() -> None:
    """D-6: the benchmark grader does not import the product verifier."""
    grader = Path("benchmarks/procedure_baseline/grader.py")
    modules = _imported_modules(grader)
    assert "services.engine.action_verification" not in modules, modules
