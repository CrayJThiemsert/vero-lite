"""AC-6 / AC-9 — the economic-impact facet at the ``recommend()`` integration level
(PLAN-0071). Proves the ADR-0030 D5 advisory invariants end-to-end:

* **AC-9 (RED evidence) + AC-6(b):** WITHOUT a producer the action carries NO
  ``economic_impact`` step; WITH one the action's own fields are IDENTICAL and the
  facet is strictly **appended last** — it never alters the action.
* **AC-6(c) — the finding-(ii) correctness contract:** a **raising** producer NEVER
  demotes the good LLM judgment to the ``_rule_recommend`` fail-safe
  (``actor_kind`` stays ``"llm"``, never ``"engine"``).

Offline + deterministic — a fake ``ChatClient`` drives the LLM path (no MS-S1,
no host-state; CLAUDE.md §8).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest

from services.engine.economic_impact import (
    EconomicExposure,
    EconomicImpact,
    register_economic_producer,
)
from services.engine.llm.client import ChatResult
from services.engine.recommender import recommend
from services.engine.registry import registry
from verticals.energy.economic_impact import register_energy_economic_impact


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
        for event in _none:  # pragma: no cover - never streamed here
            yield event

    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok"}


class _FakeChatClient:
    """Replays canned ChatResults for the two-call recommend() exchange."""

    def __init__(self, results: list[ChatResult]) -> None:
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


def _chat(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Start the emergency aerator on the battery",
            "description": "Over-temperature crossed the breach threshold; start the aerator now.",
            "rationale": "Aeration restores the safe band.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "Asset", "primary_key": "asset-battery-01"}],
            "suggested_handler": "start_emergency_aerator",
            "handler_payload": {"event_id": "event-reading-03"},
        }
    )


def _crossing_event() -> dict[str, Any]:
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


def _register_energy() -> None:
    registry.register_handler("energy", "echo", _stub)
    registry.register_handler("energy", "start_emergency_aerator", _stub)
    registry.register_adapter(
        _FakeAdapter({"Asset": [{"asset_id": "asset-battery-01", "name": "battery"}]})
    )


def _patch_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point recommend() at a fresh two-result fake (one recommend() call per patch)."""
    monkeypatch.setattr(
        "services.engine.recommender._build_chat_client",
        lambda: _FakeChatClient([_chat("draft", thinking="r"), _chat(_judgment_json())]),
    )


def _impact() -> EconomicImpact:
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="avoided_outage",
        baseline=EconomicExposure(label="unmitigated outage", exposure_thb=Decimal("480000")),
        governed=EconomicExposure(label="governed intervention", exposure_thb=Decimal("75000")),
        net_benefit_thb=Decimal("405000"),
        assumptions=["outage ฿120,000/hr; 4h unmitigated vs 0.5h governed"],
    )


def _action_fields(action: Any) -> dict[str, Any]:
    """Every action-defining field EXCEPT the reasoning trace (which grows the facet)."""
    return {
        "title": action.title,
        "description": action.description,
        "confidence": action.confidence,
        "suggested_handler": action.suggested_handler,
        "handler_payload": action.handler_payload,
        "requires_approval": action.requires_approval,
        "affected_entities": [(e.object_type, e.primary_key) for e in action.affected_entities],
    }


async def test_facet_appends_without_altering_the_action(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-9 RED (no facet pre-producers) + AC-6(b): WITH a producer the action's own
    fields are byte-identical and the facet is appended LAST."""
    _register_energy()

    _patch_llm(monkeypatch)
    base = await recommend(_crossing_event(), "energy")
    assert base is not None
    assert base.action.audit_metadata.actor_kind == "llm"
    assert [s for s in base.action.reasoning_trace if s.kind == "economic_impact"] == []  # AC-9 RED

    async def _producer(event: Any, vertical: str) -> EconomicImpact:
        return _impact()

    register_economic_producer("energy", _producer)
    _patch_llm(monkeypatch)
    withp = await recommend(_crossing_event(), "energy")
    assert withp is not None
    assert _action_fields(withp.action) == _action_fields(base.action)  # action UNCHANGED
    econ = [s for s in withp.action.reasoning_trace if s.kind == "economic_impact"]
    assert len(econ) == 1
    assert withp.action.reasoning_trace[-1].kind == "economic_impact"  # appended LAST
    assert EconomicImpact.model_validate(econ[0].detail) == _impact()


async def test_real_energy_producer_carries_the_sdg_facet(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-9 GREEN flip: the REAL energy producer (registered as discovery does it) makes a
    composed action on the mocked LLM path carry exactly one ``economic_impact`` step whose
    ``net_benefit_thb`` is the ratified SD-G ฿405,000 (baseline ฿480,000 - governed ฿75,000)."""
    _register_energy()
    register_energy_economic_impact()  # the same call discovery._register_economic_producer makes

    _patch_llm(monkeypatch)
    record = await recommend(_crossing_event(), "energy")
    assert record is not None
    assert record.action.audit_metadata.actor_kind == "llm"
    econ = [s for s in record.action.reasoning_trace if s.kind == "economic_impact"]
    assert len(econ) == 1
    assert record.action.reasoning_trace[-1].kind == "economic_impact"  # appended LAST
    impact = EconomicImpact.model_validate(econ[0].detail)
    assert impact.kind == "avoided_outage"
    assert impact.provisional is True
    assert impact.net_benefit_thb == Decimal("405000")  # SD-G arithmetic


async def test_raising_producer_does_not_demote_to_rule_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-6(c) / finding (ii): a raising producer must NOT be caught by recommend()'s IN-4
    fail-safe and demote the good LLM judgment to _rule_recommend."""
    _register_energy()

    async def _boom(event: Any, vertical: str) -> EconomicImpact:
        raise RuntimeError("producer exploded")

    register_economic_producer("energy", _boom)
    _patch_llm(monkeypatch)
    record = await recommend(_crossing_event(), "energy")
    assert record is not None
    assert record.action.audit_metadata.actor_kind == "llm"  # NOT demoted to the "engine" fail-safe
    assert [s for s in record.action.reasoning_trace if s.kind == "economic_impact"] == []
