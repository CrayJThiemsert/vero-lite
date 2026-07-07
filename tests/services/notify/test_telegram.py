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


# --- notify_schedule_missed (PLAN-0055 Step 7 / AC-8) ---------------------------------------


async def test_schedule_missed_sends_when_armed(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    captured: dict[str, Any] = {}
    sent = await telegram.notify_schedule_missed(
        schedule_id="procurement:reorder",
        scheduled_for="2026-07-07T06:00:00+07:00",
        transport=_capturing_transport(captured),
        now=1000.0,
    )
    assert sent is True
    assert "/botTESTTOKEN/sendMessage" in captured["url"]
    assert captured["body"]["chat_id"] == "999"
    assert "MISSED" in captured["body"]["text"]
    assert "procurement:reorder" in captured["body"]["text"]


async def test_schedule_missed_ignores_llm_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """The schedule gate has NO llm_backend condition — a missed round is a clock/ops event,
    so it fires even when the LLM backend is hosted (unlike notify_llm_unreachable)."""
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    sent = await telegram.notify_schedule_missed(
        schedule_id="s", scheduled_for="t", transport=_capturing_transport({}), now=1000.0
    )
    assert sent is True


async def test_schedule_missed_noop_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
    captured: dict[str, Any] = {}
    sent = await telegram.notify_schedule_missed(
        schedule_id="s", scheduled_for="t", transport=_capturing_transport(captured), now=1000.0
    )
    assert sent is False
    assert captured == {}


async def test_schedule_missed_noop_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    sent = await telegram.notify_schedule_missed(
        schedule_id="s", scheduled_for="t", transport=_capturing_transport({}), now=1000.0
    )
    assert sent is False


async def test_schedule_missed_cooldown_is_independent_of_llm_anchor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The two notifiers hold SEPARATE cooldown anchors — an MS-S1 ping must not debounce a
    schedule-missed alert, and vice versa (distinct events)."""
    _arm(monkeypatch)
    count = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        count["n"] += 1
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    # an LLM ping at t=1000 must NOT block the first schedule alert at the same instant.
    assert await telegram.notify_llm_unreachable(transport=transport, now=1000.0) is True
    assert (
        await telegram.notify_schedule_missed(
            schedule_id="s", scheduled_for="t", transport=transport, now=1000.0
        )
        is True
    )
    # the schedule alert's OWN anchor debounces a second one inside the window.
    assert (
        await telegram.notify_schedule_missed(
            schedule_id="s", scheduled_for="t", transport=transport, now=1100.0
        )
        is False
    )
    assert count["n"] == 2


async def test_schedule_missed_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("telegram unreachable")

    sent = await telegram.notify_schedule_missed(
        schedule_id="s", scheduled_for="t", transport=httpx.MockTransport(handler), now=1000.0
    )
    assert sent is False  # swallowed, no exception escapes


def test_schedule_missed_message_carries_no_pii() -> None:
    msg = telegram.build_schedule_missed_message(
        schedule_id="procurement:reorder", scheduled_for="2026-07-07T06:00:00+07:00"
    )
    assert "MISSED" in msg
    assert "procurement:reorder" in msg
    for forbidden in ("shipment", "asset-", "select ", "operator question", "person"):
        assert forbidden.lower() not in msg.lower()


# --- notify_event_fire_failed (PLAN-0056 Step 7 / AC-10) ------------------------------------


async def test_event_fire_failed_sends_when_armed(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    captured: dict[str, Any] = {}
    sent = await telegram.notify_event_fire_failed(
        procedure_id="event_emergency_sourcing_round",
        event_kind="asset_failure",
        transport=_capturing_transport(captured),
        now=1000.0,
    )
    assert sent is True
    assert "/botTESTTOKEN/sendMessage" in captured["url"]
    assert captured["body"]["chat_id"] == "999"
    assert "FAILED to fire" in captured["body"]["text"]
    assert "asset_failure" in captured["body"]["text"]


async def test_event_fire_failed_ignores_llm_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """No llm_backend condition — a dropped/failed event fire is an ops event, so it fires even
    when the LLM backend is hosted (like notify_schedule_missed, unlike notify_llm_unreachable)."""
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    sent = await telegram.notify_event_fire_failed(
        procedure_id="p", event_kind="k", transport=_capturing_transport({}), now=1000.0
    )
    assert sent is True


async def test_event_fire_failed_noop_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_notify_enabled", False)
    captured: dict[str, Any] = {}
    sent = await telegram.notify_event_fire_failed(
        procedure_id="p", event_kind="k", transport=_capturing_transport(captured), now=1000.0
    )
    assert sent is False
    assert captured == {}


async def test_event_fire_failed_noop_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    sent = await telegram.notify_event_fire_failed(
        procedure_id="p", event_kind="k", transport=_capturing_transport({}), now=1000.0
    )
    assert sent is False


async def test_event_fire_failed_cooldown_is_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A separate cooldown anchor — a schedule-missed (or MS-S1) alert must not debounce an
    event-fire-failed alert at the same instant, and the event alert's own anchor debounces its
    second send inside the window."""
    _arm(monkeypatch)
    count = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        count["n"] += 1
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    # a schedule-missed alert at t=1000 must NOT block the first event-fire alert at that instant.
    assert (
        await telegram.notify_schedule_missed(
            schedule_id="s", scheduled_for="t", transport=transport, now=1000.0
        )
        is True
    )
    assert (
        await telegram.notify_event_fire_failed(
            procedure_id="p", event_kind="k", transport=transport, now=1000.0
        )
        is True
    )
    # the event alert's OWN anchor debounces a second one inside the window.
    assert (
        await telegram.notify_event_fire_failed(
            procedure_id="p", event_kind="k", transport=transport, now=1100.0
        )
        is False
    )
    assert count["n"] == 2


async def test_event_fire_failed_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _arm(monkeypatch)

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("telegram unreachable")

    sent = await telegram.notify_event_fire_failed(
        procedure_id="p", event_kind="k", transport=httpx.MockTransport(handler), now=1000.0
    )
    assert sent is False  # swallowed, no exception escapes


def test_event_fire_failed_message_carries_no_pii() -> None:
    msg = telegram.build_event_fire_failed_message(
        procedure_id="event_emergency_sourcing_round", event_kind="asset_failure"
    )
    assert "FAILED to fire" in msg
    assert "asset_failure" in msg
    for forbidden in ("shipment", "select ", "operator question", "person", "pump-7"):
        assert forbidden.lower() not in msg.lower()


def test_event_fire_failed_message_handles_unmapped_procedure() -> None:
    msg = telegram.build_event_fire_failed_message(procedure_id=None, event_kind="asset_failure")
    assert "no mapped procedure" in msg
    assert "asset_failure" in msg
