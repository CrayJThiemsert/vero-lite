"""Native async Telegram notifier for MS-S1-unreachable events (PLAN-0014).

Best-effort, non-blocking, **never raises**. When an OCT local-LLM call fails
because MS-S1 MAX is unreachable, this pings the operator (with a cooldown) so
the box can be powered on + warmed. An `httpx` POST to the Telegram
``sendMessage`` API — reusing the **existing** harness bot/chat env vars
(ADR-013 D5), no new bot. The body carries **no PII** (no operator question,
no object/record data, no partner identifiers) per CLAUDE.md §8 / PDPA: only a
fixed advisory + a warm one-liner (+ a ``/warm`` tap-link when
``OCT_PUBLIC_BASE_URL`` is set).

Design invariants (PLAN-0014 / mirrors the ADR-010 IN-4 fail-safe posture):
no-op gates checked first (flag off / non-local backend / env unset), a
process-local cooldown (debounces UI polling), a short timeout, and a blanket
``except`` so a notify failure can never break the request path.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

import httpx

from services.api.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"

# Process-local timestamp (monotonic) of the last SUCCESSFUL send — the cooldown
# anchor (SD-4). Resets on process restart (no cross-restart persistence).
_last_send_monotonic: float | None = None

# A SEPARATE cooldown anchor for scheduler missed-round alerts (PLAN-0055 Step 7 / AC-8) so
# they never debounce against the MS-S1-unreachable pings — distinct events, distinct limits.
_last_schedule_send_monotonic: float | None = None


def _warm_one_liner() -> str:
    """The copy-pasteable warm command — model + host + keep_alive from config."""
    return (
        f"curl {settings.ollama_host}/api/generate -d "
        f'\'{{"model":"{settings.recommender_model}",'
        f'"keep_alive":"{settings.ollama_keep_alive}"}}\''
    )


def build_message(*, occurred_at: str) -> str:
    """Build the no-PII advisory body (a fixed line + UTC time + warm one-liner).

    Never includes the operator question, object/record data, or partner
    identifiers (CLAUDE.md §8 / PDPA — AC-no-pii).
    """
    lines = [
        f"⚠️ vero-lite OCT: an LLM request reached MS-S1 at {occurred_at} "
        "but it is unreachable. Power it on + warm the model:",
        _warm_one_liner(),
    ]
    base = settings.oct_public_base_url.rstrip("/")
    if base:
        lines.append(f"Or tap to warm: {base}/warm")
    return "\n".join(lines)


def _gates_open() -> bool:
    """True only when notifications are armed: flag on, local backend, env set."""
    return bool(
        settings.telegram_notify_enabled
        and settings.llm_backend == "local"
        and settings.telegram_bot_token
        and settings.telegram_chat_id
    )


def describe_arm_state() -> str:
    """Human-readable arm state for the startup log — booleans only, never the token.

    Returns ``"ARMED"`` when every gate is open, else
    ``"DISARMED — <reason>[, <reason>...]"`` naming each closed gate. Logged once
    at app startup so a mis-arm (e.g. the enable flag left off — the silent gate
    that returns no per-call log) is self-evident at boot without exposing
    ``telegram_bot_token`` (only its set/unset state is reported).
    """
    if _gates_open():
        return "ARMED"
    reasons: list[str] = []
    if not settings.telegram_notify_enabled:
        reasons.append("TELEGRAM_NOTIFY_ENABLED=false")
    if settings.llm_backend != "local":
        reasons.append(f"llm_backend={settings.llm_backend!r} (need 'local')")
    if not settings.telegram_bot_token:
        reasons.append("TELEGRAM_BOT_TOKEN unset")
    if not settings.telegram_chat_id:
        reasons.append("TELEGRAM_CHAT_ID unset")
    return "DISARMED — " + ", ".join(reasons)


def reset_cooldown() -> None:
    """Reset both process-local cooldown anchors (used by tests)."""
    global _last_send_monotonic, _last_schedule_send_monotonic
    _last_send_monotonic = None
    _last_schedule_send_monotonic = None


async def _post_telegram(text: str, *, transport: httpx.AsyncBaseTransport | None) -> bool:
    """POST one message to the Telegram ``sendMessage`` API. Returns ``True`` iff delivered.

    **Never raises** — every failure is swallowed + logged (both notifiers are best-effort and
    must never break their caller). ``transport`` is the test-injection seam (an
    ``httpx.MockTransport``); production passes ``None``.
    """
    url = f"{_TELEGRAM_API}/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=5.0, transport=transport) as client:
            response = await client.post(
                url, json={"chat_id": settings.telegram_chat_id, "text": text}
            )
            response.raise_for_status()
    except Exception as exc:  # best-effort — must never raise into the caller
        logger.warning("telegram notify failed: %s", exc)
        return False
    return True


async def notify_llm_unreachable(
    *,
    transport: httpx.AsyncBaseTransport | None = None,
    now: float | None = None,
) -> bool:
    """Best-effort ping that MS-S1 is unreachable. Returns ``True`` iff a message
    was sent. **Never raises** — every failure is swallowed + logged.

    ``transport`` and ``now`` are test-injection seams (an
    ``httpx.MockTransport`` and a monotonic-clock value); production passes
    neither.
    """
    global _last_send_monotonic
    if not _gates_open():
        return False

    current = now if now is not None else time.monotonic()
    if (
        _last_send_monotonic is not None
        and current - _last_send_monotonic < settings.telegram_notify_cooldown_s
    ):
        return False

    occurred_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = build_message(occurred_at=occurred_at)
    if not await _post_telegram(text, transport=transport):
        return False

    _last_send_monotonic = current
    return True


def _schedule_gates_open() -> bool:
    """True when Telegram alerts are armed for the scheduler: flag on + bot token + chat id.

    Unlike :func:`_gates_open` there is **no** ``llm_backend`` condition — a missed scheduled
    round is a clock / ops event, independent of which LLM backend (or none) is configured.
    """
    return bool(
        settings.telegram_notify_enabled
        and settings.telegram_bot_token
        and settings.telegram_chat_id
    )


def build_schedule_missed_message(*, schedule_id: str, scheduled_for: str) -> str:
    """The no-PII missed-round advisory body (PLAN-0055 Step 7 / AC-8).

    Carries only operational identifiers (the schedule id + the scheduled slot) — never
    object / record / partner data (CLAUDE.md §8 / PDPA).
    """
    return (
        f"⚠️ vero-lite scheduler: a scheduled run was MISSED — schedule "
        f"'{schedule_id}', slot {scheduled_for}. The daemon was down across one or more "
        "fire slots (skip-no-backfill policy); check the scheduler daemon is running."
    )


async def notify_schedule_missed(
    *,
    schedule_id: str,
    scheduled_for: str,
    transport: httpx.AsyncBaseTransport | None = None,
    now: float | None = None,
) -> bool:
    """Best-effort ping that a scheduled round was MISSED (SD-P2 skip-no-backfill; PLAN-0055
    Step 7 / AC-8) so the *absence* of a run is detectable. Returns ``True`` iff a message was
    sent. **Never raises** — every failure is swallowed + logged. ``transport`` / ``now`` are
    the same test seams as :func:`notify_llm_unreachable`; production passes neither.
    """
    global _last_schedule_send_monotonic
    if not _schedule_gates_open():
        return False

    current = now if now is not None else time.monotonic()
    if (
        _last_schedule_send_monotonic is not None
        and current - _last_schedule_send_monotonic < settings.telegram_notify_cooldown_s
    ):
        return False

    text = build_schedule_missed_message(schedule_id=schedule_id, scheduled_for=scheduled_for)
    if not await _post_telegram(text, transport=transport):
        return False

    _last_schedule_send_monotonic = current
    return True
