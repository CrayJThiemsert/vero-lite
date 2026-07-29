"""LINE Official Account push — the fleet pilot's ONE outbound channel (PLAN-0096 Step 7 / AC-8).

Six events, one seam, outbound only:

============================  ==================================  ======================
event                          fires when                          goes to
============================  ==================================  ======================
``approval_needed``            a governed run suspends at a gate    the resolved tier's
                                                                    approver
``ratification_due``           a provisional decision is nearing    owner + operator
                               its window
``ratification_overdue``       the window has passed unsigned       owner + operator
``task_chain_stale``           a post-approval checklist item has   operator
                               sat untouched
``export_ready``               the month-end file is available      owner + accounting
``pm_due``                     the 06:00 sweep found trucks past    mechanics
                               their service point
============================  ==================================  ======================

**The sixth arrived by decision, not by drift.** This enum was a closed set of five,
and this docstring required a named producer and a named recipient rule before a
member could be added. The partner supplied both in round-2 answer A3 —
"PM ถึงกำหนด → กลุ่มช่าง" — and Cray ratified the AC-8 amendment (typed,
2026-07-29). The producer is the existing 06:00 scheduled sweep, not a new
scheduler. A seventh still needs the same two answers.

**LINE Notify is gone.** It was discontinued 2025-03-31, so this is the Messaging API
push endpoint on an Official Account. Whether the partner wants that OA to message
people individually or to post into the LINE group his team already lives in is HIS
call and a named intake question — the seam is indifferent, because the push API's
``to`` field takes a user id or a group id equally.

**Outbound only, structurally.** There is no webhook, no reply token, no inbound
handler anywhere in this module or the routers, and PLAN-0096's Out of Scope says so.
Quote photos arrive through เมย์'s upload in the case UI, not through LINE.

**Why this body may carry operational detail when the Telegram one may not.** They are
different channels to different audiences. ``services/notify/telegram.py`` pings OUR
harness chat about OUR infrastructure, so it is strictly no-PII by design. This one
messages the operator's own staff about the operator's own trucks, and a push that
said only "a repair needs approval" would send someone to a screen to find out which —
which is the LINE-archaeology problem the pilot exists to end. So the bodies name the
truck, the amount and the person. They still carry **no third-party personal data** and
no credentials, and they stay short enough to be read on a lock screen.

Best-effort and **never raises**: a notification failure must never break the governed
path that triggered it. A send that did not happen returns ``False`` and is logged —
never swallowed into a success.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import httpx

from services.api.config import settings

logger = logging.getLogger(__name__)

_LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

#: LINE truncates a text message at 5000 characters; nothing here comes close, but a
#: body assembled from operator free text could, and a silently truncated notice is
#: worse than a short one.
_MAX_TEXT = 5000


class LineEvent(StrEnum):
    """The six AC-8 events. A closed set on purpose — every member has a named
    producer and a named recipient rule, so a seventh cannot arrive without a
    decision about who receives it."""

    APPROVAL_NEEDED = "approval_needed"
    RATIFICATION_DUE = "ratification_due"
    RATIFICATION_OVERDUE = "ratification_overdue"
    TASK_CHAIN_STALE = "task_chain_stale"
    EXPORT_READY = "export_ready"
    PM_DUE = "pm_due"


class Recipient(StrEnum):
    """Who a message is addressed to, by ROLE rather than by id.

    Roles, not LINE ids, because the ids are deployment config the partner supplies and
    may change (a staff change, a switch from individuals to a group). Code that named
    an id would have to be edited for a personnel change; code that names a role does
    not."""

    OWNER = "owner"
    OPERATOR = "operator"
    ACCOUNTING = "accounting"
    #: The workshop crew (A3: กลุ่มช่าง). A group rather than a person by the
    #: partner's own choice — routine servicing is whoever is free, not a named
    #: individual, and naming one would make the round stop when he is off.
    MECHANICS = "mechanics"
    #: The approver the DOA ladder actually resolved for THIS spend. Not a fixed
    #: person: a ฿15,000 repair and a ฿48,000 one go to different desks, and sending
    #: both to the owner would recreate the bottleneck the ladder exists to remove.
    RESOLVED_APPROVER = "resolved_approver"


#: Event -> who hears about it (Step 7's recipient table, encoded rather than described).
#: A3 in the partner's own words: "ผมไม่อยากให้ทุกอย่างเด้งเข้ากลุ่มเดียว เดี๋ยวคนปิด
#: แจ้งเตือนหมด" — five distinct destinations, deliberately.
EVENT_RECIPIENTS: dict[LineEvent, tuple[Recipient, ...]] = {
    LineEvent.APPROVAL_NEEDED: (Recipient.RESOLVED_APPROVER,),
    LineEvent.RATIFICATION_DUE: (Recipient.OWNER, Recipient.OPERATOR),
    LineEvent.RATIFICATION_OVERDUE: (Recipient.OWNER, Recipient.OPERATOR),
    LineEvent.TASK_CHAIN_STALE: (Recipient.OPERATOR,),
    LineEvent.EXPORT_READY: (Recipient.OWNER, Recipient.ACCOUNTING),
    LineEvent.PM_DUE: (Recipient.MECHANICS,),
}


@dataclass(frozen=True)
class LineDelivery:
    """What actually happened, per recipient — the honest report of one notify call.

    Returned rather than a bare bool because "sent to the owner but the accounting
    contact is unmapped" is the normal state during onboarding, and a single boolean
    would round it to either a lie or an alarm."""

    event: LineEvent
    sent_to: tuple[str, ...] = ()
    unmapped: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    throttled: tuple[str, ...] = ()

    @property
    def delivered(self) -> bool:
        """True if at least one recipient received it."""
        return bool(self.sent_to)


#: Per (event, target) cooldown anchors. Keyed by both, so an overdue reminder about
#: one truck cannot debounce an approval request about another — the failure mode that
#: makes people stop trusting a channel.
_last_send: dict[tuple[str, str], float] = {}


def reset_cooldown() -> None:
    """Drop every cooldown anchor (used by tests)."""
    _last_send.clear()


def _recipient_map() -> dict[str, str]:
    """Parse ``LINE_RECIPIENTS`` into role -> LINE id, failing SOFT and loudly.

    A malformed value returns empty rather than raising: this is config for a
    best-effort channel, and a JSON typo must not take down the API that reads it. It
    is logged at warning so the mistake is visible rather than presenting as "nobody is
    configured"."""
    raw = settings.line_recipients.strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("LINE_RECIPIENTS is not valid JSON (%s) — treating as unset", exc)
        return {}
    if not isinstance(parsed, dict):
        logger.warning("LINE_RECIPIENTS must be a JSON object — treating as unset")
        return {}
    return {str(role): str(target) for role, target in parsed.items() if target}


def _gates_open() -> bool:
    """True only when LINE push is armed: flag on, token set, at least one recipient."""
    return bool(
        settings.line_notify_enabled and settings.line_channel_access_token and _recipient_map()
    )


def describe_arm_state() -> str:
    """Human-readable arm state for the startup log — booleans only, never the token.

    Mirrors the Telegram notifier's boot diagnostic for the same reason: the enable
    flag left off is a silent per-call no-op, and a channel nobody knows is disarmed is
    worse than no channel at all."""
    if _gates_open():
        return f"ARMED ({len(_recipient_map())} recipient role(s))"
    reasons: list[str] = []
    if not settings.line_notify_enabled:
        reasons.append("LINE_NOTIFY_ENABLED=false")
    if not settings.line_channel_access_token:
        reasons.append("LINE_CHANNEL_ACCESS_TOKEN unset")
    if not _recipient_map():
        reasons.append("LINE_RECIPIENTS empty or unparseable")
    return "DISARMED — " + ", ".join(reasons)


def build_message(event: LineEvent, detail: dict[str, Any]) -> str:
    """The Thai-language body for one event.

    Thai because every reader of these is a Thai speaker doing their job on a phone,
    and an English notification would be one more thing to decode before acting.
    ``detail`` is the caller's operational facts; unknown keys are ignored so a
    producer can pass more than a given body uses without coordinating a schema.
    """
    truck = detail.get("truck") or detail.get("truck_id") or "—"
    amount = detail.get("amount_thb")
    amount_text = f"฿{float(amount):,.0f}" if amount is not None else "—"
    case = detail.get("case_id")
    case_text = f" (เคส {case})" if case else ""

    if event is LineEvent.APPROVAL_NEEDED:
        return (
            f"🔧 รออนุมัติค่าซ่อม{case_text}\n"
            f"รถ {truck} · {amount_text}\n"
            f"ผู้อนุมัติ: {detail.get('approver_role', '—')}"
        )
    if event is LineEvent.RATIFICATION_DUE:
        return (
            f"📝 รอลงนามย้อนหลัง{case_text}\n"
            f"รถ {truck} · {amount_text}\n"
            f"ครบกำหนด {detail.get('due_at', '—')} — ซ่อมไปแล้ว รอเอกสารตามให้ทัน"
        )
    if event is LineEvent.RATIFICATION_OVERDUE:
        return (
            f"⚠️ เลยกำหนดลงนาม{case_text}\n"
            f"รถ {truck} · {amount_text}\n"
            f"ครบกำหนดตั้งแต่ {detail.get('due_at', '—')} — ยังไม่มีใครเซ็นรับรอง"
        )
    if event is LineEvent.TASK_CHAIN_STALE:
        return (
            f"⏳ งานค้าง{case_text}\n"
            f"รถ {truck} · ขั้นตอน \"{detail.get('task', '—')}\"\n"
            f"ไม่มีความเคลื่อนไหว {detail.get('stale_days', '—')} วัน"
        )
    if event is LineEvent.PM_DUE:
        # The whole due SET in one message, not one push per truck: the morning
        # round is planned as a batch ("which trucks today"), and five separate
        # pushes at 06:00 is how a group mutes a channel by breakfast.
        plates = detail.get("plates") or []
        listed = "\n".join(f"  • {plate}" for plate in plates) or "  • —"
        return f"🔧 ถึงกำหนดเข้าศูนย์ {len(plates)} คัน\n{listed}\nรอบเช้า — ยืนยันคิวกับอู่ได้เลย"
    return (
        f"📄 ไฟล์สรุปสิ้นเดือนพร้อมแล้ว — {detail.get('period', '—')}\n"
        f"{detail.get('row_count', '—')} รายการ · "
        f"ตรวจสอบได้ครบ {detail.get('traceable_pct', '—')}%"
    )


async def _push(text: str, *, to: str, transport: httpx.AsyncBaseTransport | None) -> bool:
    """POST one push message. **Never raises** — every failure is swallowed + logged."""
    try:
        async with httpx.AsyncClient(timeout=5.0, transport=transport) as client:
            response = await client.post(
                _LINE_PUSH_URL,
                headers={"Authorization": f"Bearer {settings.line_channel_access_token}"},
                json={"to": to, "messages": [{"type": "text", "text": text[:_MAX_TEXT]}]},
            )
            response.raise_for_status()
    except Exception as exc:  # best-effort — must never raise into the caller
        logger.warning("LINE push failed (to=%s): %s", to, exc)
        return False
    return True


async def notify(
    event: LineEvent,
    detail: dict[str, Any],
    *,
    resolved_approver: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    now: float | None = None,
) -> LineDelivery:
    """Push one event to its recipients. **Never raises.**

    ``resolved_approver`` is the ROLE the DOA ladder resolved for this spend, supplied
    by the caller because only the run knows it — it is looked up in the same recipient
    map as the fixed roles, so an operator who has not mapped that role yet gets an
    ``unmapped`` entry rather than a silent drop.

    ``transport`` and ``now`` are the test-injection seams (an ``httpx.MockTransport``
    and a monotonic-clock value); production passes neither, and with the gates closed
    NO client is constructed at all — which is what keeps the offline suite free of
    outbound sockets (AC-11).
    """
    if not _gates_open():
        return LineDelivery(event=event)

    mapping = _recipient_map()
    current = now if now is not None else time.monotonic()
    sent: list[str] = []
    unmapped: list[str] = []
    failed: list[str] = []
    throttled: list[str] = []

    for recipient in EVENT_RECIPIENTS[event]:
        role = (
            resolved_approver
            if recipient is Recipient.RESOLVED_APPROVER and resolved_approver
            else recipient.value
        )
        target = mapping.get(role)
        if not target:
            unmapped.append(role)
            continue

        key = (event.value, target)
        previous = _last_send.get(key)
        if previous is not None and current - previous < settings.line_notify_cooldown_s:
            throttled.append(role)
            continue

        if await _push(build_message(event, detail), to=target, transport=transport):
            _last_send[key] = current
            sent.append(role)
        else:
            failed.append(role)

    if unmapped:
        logger.warning(
            "LINE %s: no recipient id mapped for %s — the message was not delivered to them",
            event.value,
            ", ".join(unmapped),
        )
    return LineDelivery(
        event=event,
        sent_to=tuple(sent),
        unmapped=tuple(unmapped),
        failed=tuple(failed),
        throttled=tuple(throttled),
    )
