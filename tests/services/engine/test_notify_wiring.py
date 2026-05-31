"""The MS-S1-unreachable notify fires only on OllamaUnreachableError (PLAN-0014).

Recommender (View B) and nl_query (View C) both ping on a genuine
unreachable-host failure and stay silent on other LLM failures — while the
existing fail-safe / degrade behaviour is preserved (the ping is additive).
The notify is spied via monkeypatch; no real Telegram call.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.engine import nl_query, recommender
from services.engine.llm.client import ChatResult, OllamaError, OllamaUnreachableError


def _crossing_event() -> dict[str, Any]:
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


class _UnreachableClient:
    """A chat client that always fails as if MS-S1 were powered off."""

    async def chat(self, *_args: Any, **_kwargs: Any) -> ChatResult:
        raise OllamaUnreachableError("MS-S1 unreachable")


class _ReachableErrorClient:
    """A chat client on a reachable host that errors (NOT unreachable)."""

    async def chat(self, *_args: Any, **_kwargs: Any) -> ChatResult:
        raise OllamaError("reachable but returned bad JSON")


@pytest.fixture
def spy_notify(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Replace the notifier with a counting spy (the engine lazy-imports it)."""
    calls = {"n": 0}

    async def _fake_notify(**_kwargs: Any) -> bool:
        calls["n"] += 1
        return True

    monkeypatch.setattr("services.notify.telegram.notify_llm_unreachable", _fake_notify)
    return calls


# --- recommender (View B) -------------------------------------------------


async def test_recommender_notifies_on_unreachable(
    monkeypatch: pytest.MonkeyPatch, spy_notify: dict[str, int]
) -> None:
    monkeypatch.setattr(
        "services.engine.recommender._build_chat_client", lambda: _UnreachableClient()
    )
    record = await recommender.recommend(_crossing_event(), "energy")

    assert record is not None  # fail-safe rule path still returned
    assert record.action.audit_metadata.actor_kind == "engine"
    assert spy_notify["n"] == 1


async def test_recommender_silent_on_reachable_error(
    monkeypatch: pytest.MonkeyPatch, spy_notify: dict[str, int]
) -> None:
    monkeypatch.setattr(
        "services.engine.recommender._build_chat_client", lambda: _ReachableErrorClient()
    )
    record = await recommender.recommend(_crossing_event(), "energy")

    assert record is not None  # still degrades to the rule path
    assert spy_notify["n"] == 0  # no ping — the box is reachable


# --- nl_query (View C) ----------------------------------------------------


async def test_nl_query_notifies_on_unreachable(spy_notify: dict[str, int]) -> None:
    answer = await nl_query.answer_question(
        "how many assets?", "energy", client=_UnreachableClient()
    )

    assert answer.grounded is False
    assert spy_notify["n"] == 1


async def test_nl_query_silent_on_reachable_error(spy_notify: dict[str, int]) -> None:
    answer = await nl_query.answer_question(
        "how many assets?", "energy", client=_ReachableErrorClient()
    )

    assert answer.grounded is False
    assert spy_notify["n"] == 0
