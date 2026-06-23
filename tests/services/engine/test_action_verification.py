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

from services.api.config import settings
from services.engine.action_verification import (
    VERIFICATION_MODE_DETERMINISTIC,
    VERIFICATION_MODE_HYBRID,
    augment_with_advisory_judge,
    judge_action_expression,
    verify_action_expression,
)
from services.engine.actions import EntityRef
from services.engine.llm.client import ChatResult, OllamaError, OllamaUnreachableError
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
    """Replays canned ChatResults, or always raises (mirrors test_entity_resolution)."""

    def __init__(
        self, *, results: list[ChatResult] | None = None, error: Exception | None = None
    ) -> None:
        self._results = list(results or [])
        self._error = error

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if self._error is not None:
            raise self._error
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


# --- Phase 2: the advisory local-LLM-judge (judge FAKED, offline) ---------
#
# Constraint ①: the offline oracle is the gate — every judge here is a fake
# ChatClient; a live MS-S1 run is Cray-gated host-state, NOT a gate (CLAUDE.md §8).


def _verdict_json(
    *, expresses_action: bool, confidence: float, rationale: str = "judge rationale"
) -> str:
    return json.dumps(
        {
            "expresses_action": expresses_action,
            "confidence": confidence,
            "rationale": rationale,
        }
    )


async def test_judge_agreement_raises_confidence_when_floor_consistent() -> None:
    """AC-8(viii): floor consistent + judge agrees (expresses) -> hybrid mode, high
    confidence; the floor outcome is unchanged."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator")  # prose states it -> consistent
    floor = verify_action_expression(judgment, "aquaculture")
    assert _detail(floor[0])["outcome"] == "consistent"
    judge = _FakeChatClient(results=[_chat(_verdict_json(expresses_action=True, confidence=0.95))])

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=judge)

    detail = _detail(steps[0])
    assert detail["verification_mode"] == VERIFICATION_MODE_HYBRID
    assert detail["outcome"] == "consistent"  # floor outcome unchanged
    assert detail["judge_agreement"] is True
    assert detail["confidence_signal"] == "high"
    assert detail["judge"]["expresses_action"] is True


async def test_judge_agreement_when_floor_reshaped() -> None:
    """AC-8(viii): floor reshaped (prose omits) + judge agrees it omits -> hybrid, high
    confidence; the surfaced action stays the structured handler's."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator", **_OMITTING)  # prose omits -> reshaped
    floor = verify_action_expression(judgment, "aquaculture")
    assert _detail(floor[0])["outcome"] == "reshaped"
    judge = _FakeChatClient(results=[_chat(_verdict_json(expresses_action=False, confidence=0.9))])

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=judge)

    detail = _detail(steps[0])
    assert detail["outcome"] == "reshaped"
    assert detail["surfaced_action"] == "start_emergency_aerator"  # unchanged
    assert detail["judge_agreement"] is True
    assert detail["confidence_signal"] == "high"
    assert detail["verification_mode"] == VERIFICATION_MODE_HYBRID


async def test_judge_disagreement_never_overrides_the_floor_action() -> None:
    """Constraint ② (the load-bearing invariant): the judge is ADVISORY — on disagreement
    the floor's outcome AND the surfaced action stand; only the confidence signal drops.
    The judge can never rescue/flip a reshaped verdict to consistent."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator", **_OMITTING)  # floor: reshaped
    floor = verify_action_expression(judgment, "aquaculture")
    # The judge DISAGREES: it thinks the prose DOES express the action (expresses=True).
    judge = _FakeChatClient(results=[_chat(_verdict_json(expresses_action=True, confidence=0.8))])

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=judge)

    detail = _detail(steps[0])
    assert detail["outcome"] == "reshaped"  # NOT flipped to consistent by the judge
    assert detail["surfaced_action"] == "start_emergency_aerator"  # unchanged
    assert detail["judge_agreement"] is False
    assert detail["confidence_signal"] == "low"


async def test_judge_not_called_when_floor_skipped() -> None:
    """A floor 'skipped' (echo / no operational action) -> the judge is not engaged at all
    (no judge fields are added); the trace stays (a)-only."""
    _register_aqua_handlers()
    judgment = _judgment(handler="echo")  # floor: skipped
    floor = verify_action_expression(judgment, "aquaculture")
    assert _detail(floor[0])["outcome"] == "skipped"
    exploding = _FakeChatClient(error=AssertionError("judge must not run on a skipped floor"))

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=exploding)

    detail = _detail(steps[0])
    assert detail["outcome"] == "skipped"
    assert "judge" not in detail  # the judge was never invoked
    assert "judge_status" not in detail
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC


async def test_judge_disabled_returns_floor_unchanged() -> None:
    """judge_client is None (the verification_judge_enabled lever off) -> the floor's
    (a)-only steps are returned byte-unchanged (Phase-1-identical)."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator", **_OMITTING)
    floor = verify_action_expression(judgment, "aquaculture")

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=None)

    assert steps is floor  # the same list object — nothing layered on
    detail = _detail(steps[0])
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC
    assert "judge" not in detail


async def test_judge_unreachable_degrades_to_a_only_disclosed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-8(ix) / constraint ④: judge unreachable -> mode '(a)-only' DISCLOSED in the trace
    (not silent); the floor stands; the IN-4 notify is reused. Never raises."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator", **_OMITTING)
    floor = verify_action_expression(judgment, "aquaculture")
    notified: dict[str, bool] = {}

    async def _fake_notify() -> bool:
        notified["called"] = True
        return True

    monkeypatch.setattr("services.notify.telegram.notify_llm_unreachable", _fake_notify)
    judge = _FakeChatClient(error=OllamaUnreachableError("MS-S1 is unreachable"))

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=judge)

    detail = _detail(steps[0])
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC  # (a)-only disclosed
    assert detail["judge_status"] == "unreachable"
    assert "judge_disclosure" in detail  # disclosed, not silent
    assert detail["outcome"] == "reshaped"  # floor stands
    assert detail["surfaced_action"] == "start_emergency_aerator"
    assert notified.get("called") is True  # reused the IN-4 OllamaUnreachable notify


async def test_judge_reachable_error_degrades_to_a_only() -> None:
    """Constraint ④: a reachable-but-errored judge -> '(a)-only' disclosed (no notify); the
    floor stands. The advisory judge never harms the load-bearing result."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator", **_OMITTING)
    floor = verify_action_expression(judgment, "aquaculture")
    judge = _FakeChatClient(error=OllamaError("reachable but HTTP 500"))

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=judge)

    detail = _detail(steps[0])
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC
    assert detail["judge_status"] == "error"
    assert detail["outcome"] == "reshaped"


async def test_judge_unusable_verdict_degrades_to_a_only() -> None:
    """A reachable judge that returns non-JSON / schema-invalid output -> ActionJudgeError
    inside, caught -> '(a)-only' disclosed; the floor stands."""
    _register_aqua_handlers()
    judgment = _judgment(handler="start_emergency_aerator")
    floor = verify_action_expression(judgment, "aquaculture")
    judge = _FakeChatClient(results=[_chat("this is not json at all")])

    steps = await augment_with_advisory_judge(floor, judgment, judge_client=judge)

    detail = _detail(steps[0])
    assert detail["verification_mode"] == VERIFICATION_MODE_DETERMINISTIC
    assert detail["judge_status"] == "error"


async def test_judge_action_expression_parses_a_verdict() -> None:
    """Step 8: the judge call parses the structured verdict (expresses/confidence/rationale)
    + the judging model name."""
    judge = _FakeChatClient(
        results=[
            _chat(_verdict_json(expresses_action=True, confidence=0.7, rationale="prose names it"))
        ]
    )

    result = await judge_action_expression(
        _judgment(handler="start_emergency_aerator"), "start_emergency_aerator", judge_client=judge
    )

    assert result.verdict.expresses_action is True
    assert result.verdict.confidence == 0.7
    assert result.verdict.rationale == "prose names it"
    assert result.model == "gpt-oss:20b"


async def test_recommend_hybrid_judge_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end with the lever ON: recommend() runs floor -> advisory judge; a prose
    omission (floor reshaped) + a judge that agrees it omits -> a 'hybrid' trace whose
    surfaced action is still the structured handler's."""
    registry.register_handler("energy", "echo", _stub)
    registry.register_handler("energy", "start_emergency_aerator", _stub)
    _register_assets("asset-battery-01")
    judgment = _judgment_json(
        handler="start_emergency_aerator",
        title="Assess the over-temperature breach on the battery",
        description="Conduct a breach assessment: verify the reading, inspect the asset.",
        rationale="A structured breach assessment is the correct response to the crossing.",
    )
    verdict = _verdict_json(expresses_action=False, confidence=0.92)
    fake = _FakeChatClient(results=[_chat("draft", thinking="r"), _chat(judgment), _chat(verdict)])
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: fake)
    monkeypatch.setattr(settings, "verification_judge_enabled", True)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    verif = [s for s in record.action.reasoning_trace if s.kind == "action_verification"]
    assert len(verif) == 1
    detail = verif[0].detail
    assert detail is not None
    assert detail["verification_mode"] == VERIFICATION_MODE_HYBRID
    assert detail["outcome"] == "reshaped"
    assert detail["judge_agreement"] is True  # floor omits + judge expresses=False -> agree
    assert detail["judge"]["expresses_action"] is False


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
