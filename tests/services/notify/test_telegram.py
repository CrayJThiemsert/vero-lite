"""Tests for the native async Telegram notifier (PLAN-0014).

Offline via `httpx.MockTransport`; the cooldown clock is injected via the
`now` seam. Covers: no-op gates, the captured sendMessage POST, debounce,
never-raises, no-PII body, and the `/warm` tap-link.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from services.api.config import settings
from services.notify import telegram


def _arm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arm the notifier (flag on, local backend, env set) + reset the cooldown."""
    monkeypatch.setattr(settings, "telegram_notify_enabled", True)
    monkeypatch.setattr(settings, "llm_backend", "local")
    monkeypatch.setattr(settings, "telegram_bot_token", "TESTTOKEN")
    monkeypatch.setattr(settings, "telegram_chat_id", "999")
    monkeypatch.setattr(settings, "telegram_notify_cooldown_s", 600.0)
    monkeypatch.setattr(settings, "oct_public_base_url", "")
    telegram.reset_cooldown()


def _capturing_transport(captured: dict[str, Any]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    return httpx.MockTransport(handler)


async def test_sends_when_armed(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    captured: dict[str, Any] = {}
    sent = await telegram.notify_llm_unreachable(
        transport=_capturing_transport(captured), now=1000.0
    )
    assert sent is True
    assert "/botTESTTOKEN/sendMessage" in captured["url"]
    assert captured["body"]["chat_id"] == "999"
    assert "unreachable" in captured["body"]["text"]


async def test_noop_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
    captured: dict[str, Any] = {}
    sent = await telegram.notify_llm_unreachable(
        transport=_capturing_transport(captured), now=1000.0
    )
    assert sent is False
    assert captured == {}


async def test_noop_when_backend_not_local(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    sent = await telegram.notify_llm_unreachable(transport=_capturing_transport({}), now=1000.0)
    assert sent is False


async def test_noop_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    sent = await telegram.notify_llm_unreachable(transport=_capturing_transport({}), now=1000.0)
    assert sent is False


async def test_cooldown_debounces_second_send(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    count = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        count["n"] += 1
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    assert await telegram.notify_llm_unreachable(transport=transport, now=1000.0) is True
    assert (
        await telegram.notify_llm_unreachable(transport=transport, now=1100.0) is False
    )  # within window
    assert (
        await telegram.notify_llm_unreachable(transport=transport, now=2000.0) is True
    )  # past window
    assert count["n"] == 2


def test_describe_arm_state_armed(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    assert telegram.describe_arm_state() == "ARMED"


def test_describe_arm_state_flag_off_names_the_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
    state = telegram.describe_arm_state()
    assert state.startswith("DISARMED")
    assert "TELEGRAM_NOTIFY_ENABLED=false" in state


def test_describe_arm_state_lists_all_closed_gates_without_leaking_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    monkeypatch.setattr(settings, "telegram_bot_token", "SECRET-TOKEN")
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    state = telegram.describe_arm_state()
    assert "TELEGRAM_NOTIFY_ENABLED=false" in state
    assert "llm_backend='hosted'" in state
    assert "TELEGRAM_CHAT_ID unset" in state
    # token is set here, so it is not a reason — and its value must never appear
    assert "TELEGRAM_BOT_TOKEN unset" not in state
    assert "SECRET-TOKEN" not in state


async def test_never_raises_on_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("telegram unreachable")

    sent = await telegram.notify_llm_unreachable(transport=httpx.MockTransport(handler), now=1000.0)
    assert sent is False  # swallowed, no exception escapes


def test_message_carries_no_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "recommender_model", "gpt-oss:20b")
    monkeypatch.setattr(settings, "ollama_host", "http://192.168.1.133:11434")
    monkeypatch.setattr(settings, "ollama_keep_alive", "30m")
    monkeypatch.setattr(settings, "oct_public_base_url", "")
    msg = telegram.build_message(occurred_at="2026-05-31T16:00:00Z")
    assert "unreachable" in msg
    assert "/api/generate" in msg
    assert "keep_alive" in msg
    for forbidden in ("shipment", "asset-", "select ", "operator question"):
        assert forbidden.lower() not in msg.lower()


def test_message_adds_warm_link_when_base_url_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "oct_public_base_url", "http://192.168.1.50:8096/")
    msg = telegram.build_message(occurred_at="t")
    assert "http://192.168.1.50:8096/warm" in msg
