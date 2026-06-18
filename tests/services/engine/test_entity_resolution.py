"""Tests for governed entity resolution (ADR-0022 member (a) / PLAN-0030).

Offline + deterministic: a fake ``DataAdapter`` supplies the declared universe and
a fake ``ChatClient`` drives the LLM path (no live Ollama, no host-state). Asserts
the CONTRACT (resolving PK kept canonical; non-resolving PK -> deterministic
subject fall-back + trace; the never-invent negative; mixed multi-entity; a
resolution error -> the deterministic fail-safe; the SD-2 convergence; the D-6
import boundary), not incidental shape (Lesson #7 §3).
"""

from __future__ import annotations

import ast
import json
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from services.engine.actions import EntityRef
from services.engine.entity_resolution import (
    event_subject_ref,
    normalize_entity_key,
    resolve_affected_entities,
)
from services.engine.llm.client import ChatResult
from services.engine.recommender import _rule_recommend, recommend
from services.engine.registry import registry

_NARROW_NBSP = chr(0x202F)  # the aqua-h06 separator
_NB_HYPHEN = chr(0x2011)  # the asset-E07 separator


# --- fakes ----------------------------------------------------------------


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
    """Replays canned ChatResults, or always raises (mirrors test_recommender)."""

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


def _chat(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _judgment_json(primary_key: str = "asset-battery-01") -> str:
    return json.dumps(
        {
            "title": "Investigate over-temperature on the battery",
            "description": "Reading 96.5 celsius crossed the 90.0 celsius threshold.",
            "rationale": "Temperature is above the safe threshold; escalate for review.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "Asset", "primary_key": primary_key}],
            "suggested_handler": "echo",
            "handler_payload": {"event_id": "event-reading-03"},
        }
    )


async def _echo_handler(_action: Any) -> dict[str, Any]:
    return {"executed": True}


def _register_assets(*asset_ids: str) -> None:
    """Register an energy adapter whose Asset universe is exactly ``asset_ids``."""
    objects = {"Asset": [{"asset_id": aid, "name": aid} for aid in asset_ids]}
    registry.register_adapter(_FakeAdapter(objects))


def _event(asset_id: str = "asset-battery-01") -> dict[str, Any]:
    return {"event_id": "event-reading-03", "event_type": "reading", "asset_id": asset_id}


def _crossing_event() -> dict[str, Any]:
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


# --- normalizer (AC-1) ----------------------------------------------------


def test_normalize_recovers_separator_and_case_variants() -> None:
    assert normalize_entity_key("asset-battery-01") == normalize_entity_key("ASSET-BATTERY-01")
    assert normalize_entity_key("pond-A116") == normalize_entity_key(f"pond{_NARROW_NBSP}A116")
    assert normalize_entity_key("asset-E07") == normalize_entity_key(f"asset{_NB_HYPHEN}E07")


def test_normalize_does_not_invent_a_match() -> None:
    """Recover-only: a genuinely different key still fails to match."""
    assert normalize_entity_key("asset-battery-01") != normalize_entity_key("asset-battery-99")


# --- resolve_affected_entities (AC-2/3/5/8) -------------------------------


async def test_resolving_pk_kept_with_canonical_key() -> None:
    """AC-2: a model PK matching (case/separator variant) keeps the CANONICAL key."""
    _register_assets("asset-battery-01")
    emitted = [EntityRef(object_type="Asset", primary_key="ASSET-BATTERY-01")]

    resolved, steps = await resolve_affected_entities(_event(), "energy", emitted)

    assert [e.primary_key for e in resolved] == ["asset-battery-01"]
    assert resolved[0].object_type == "Asset"
    assert steps[0].kind == "entity_resolution"
    assert steps[0].detail is not None and steps[0].detail["outcome"] == "resolved"


async def test_non_resolving_pk_falls_back_to_subject_and_traces() -> None:
    """AC-3: a non-resolving PK -> the deterministic event subject anchor + a trace."""
    _register_assets("asset-battery-01")
    emitted = [EntityRef(object_type="Asset", primary_key="asset-ghost-99")]
    event = _event("asset-battery-01")

    resolved, steps = await resolve_affected_entities(event, "energy", emitted)

    assert resolved == [event_subject_ref(event)]
    assert steps[0].detail is not None and steps[0].detail["outcome"] == "fallback"


async def test_never_certifies_an_invented_pk() -> None:
    """AC-3 never-invent negative: a well-formed but non-existent PK is NOT certified."""
    _register_assets("asset-battery-01")
    invented = "asset-phantom-42"
    emitted = [EntityRef(object_type="Asset", primary_key=invented)]

    resolved, _ = await resolve_affected_entities(_event(), "energy", emitted)

    assert all(e.primary_key != invented for e in resolved)


async def test_mixed_multi_entity_resolves_each_independently() -> None:
    """AC-8(iv): a mixed judgment -> each entity resolved or fell back independently."""
    _register_assets("asset-battery-01", "asset-inverter-01")
    emitted = [
        EntityRef(object_type="Asset", primary_key="asset-inverter-01"),  # resolves
        EntityRef(object_type="Asset", primary_key="asset-ghost-99"),  # falls back
    ]
    event = _event("asset-battery-01")

    resolved, steps = await resolve_affected_entities(event, "energy", emitted)

    outcomes = [s.detail["outcome"] for s in steps if s.detail is not None]
    assert outcomes == ["resolved", "fallback"]
    assert resolved[0].primary_key == "asset-inverter-01"
    assert resolved[1] == event_subject_ref(event)


async def test_unknown_object_type_falls_back() -> None:
    """An object_type not in the ontology cannot resolve -> fall back, never invent."""
    _register_assets("asset-battery-01")
    emitted = [EntityRef(object_type="Nonexistent", primary_key="whatever-1")]
    event = _event()

    resolved, steps = await resolve_affected_entities(event, "energy", emitted)

    assert resolved == [event_subject_ref(event)]
    assert steps[0].detail is not None and steps[0].detail["outcome"] == "fallback"


# --- SD-2 convergence (AC-5) ----------------------------------------------


def test_subject_anchor_converges_with_rule_path() -> None:
    """SD-2: event_subject_ref is the SAME EntityRef the deterministic :265 path emits."""
    event = _crossing_event()
    record = _rule_recommend(event, "energy")
    assert record is not None
    assert record.action.affected_entities == [event_subject_ref(event)]


# --- integration via recommend() (AC-1 end-to-end, AC-8(v)/IN-4) ----------


async def test_recommend_llm_path_resolves_and_traces(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1 end-to-end: the LLM path resolves affected_entities + adds a resolution trace."""
    registry.register_handler("energy", "echo", _echo_handler)
    _register_assets("asset-battery-01")
    fake = _FakeChatClient(results=[_chat("draft", thinking="r"), _chat(_judgment_json())])
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "llm"  # the LLM path completed
    assert [e.primary_key for e in record.action.affected_entities] == ["asset-battery-01"]
    assert any(s.kind == "entity_resolution" for s in record.action.reasoning_trace)


async def test_recommend_resolution_error_falls_back_to_rule_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-8(v)/IN-4: a resolution error (no adapter registered) routes to the fail-safe."""
    registry.register_handler("energy", "echo", _echo_handler)
    # No adapter registered -> resolve_affected_entities raises -> deterministic fail-safe.
    fake = _FakeChatClient(results=[_chat("draft", thinking="r"), _chat(_judgment_json())])
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "engine"


async def test_recommend_resolves_non_existent_model_pk_to_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: a model that names a NON-declared asset -> governed fall-back, not the
    invented PK (the whole point of the universality lever)."""
    registry.register_handler("energy", "echo", _echo_handler)
    _register_assets("asset-battery-01")
    fake = _FakeChatClient(
        results=[_chat("draft", thinking="r"), _chat(_judgment_json(primary_key="asset-ghost-99"))]
    )
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "llm"  # path still completes
    keys = [e.primary_key for e in record.action.affected_entities]
    assert "asset-ghost-99" not in keys  # the invented PK is never certified


# --- D-6 contamination boundary (AC-6) ------------------------------------


def _imported_modules(path: Path) -> set[str]:
    """The set of module names imported by the file at ``path`` (AST, not substrings —
    so a docstring mention of 'benchmark' does not register as an import)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_d6_resolver_imports_nothing_from_benchmarks() -> None:
    """AC-6 / D-6: the product resolver imports nothing from benchmarks/."""
    import services.engine.entity_resolution as er

    modules = _imported_modules(Path(er.__file__))
    assert not any(m.startswith("benchmark") for m in modules), modules


def test_d6_benchmark_grader_does_not_import_the_resolver() -> None:
    """AC-6 / D-6: the benchmark grader does not import the product resolver."""
    grader = Path("benchmarks/procedure_baseline/grader.py")
    modules = _imported_modules(grader)
    assert "services.engine.entity_resolution" not in modules, modules
