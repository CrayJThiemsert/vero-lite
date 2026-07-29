"""PLAN-0096 Step 7 / AC-8 — the LINE Official Account notify seam.

Five events, one seam, outbound only. What these cases hold it to:

* **the recipient TABLE is the governance**, not a comment. An approval request goes
  to the tier the ladder resolved, not to the owner by default — sending everything to
  the owner would rebuild the bottleneck the DOA ladder exists to remove;
* **an unmapped recipient is reported, never dropped.** During onboarding the
  accounting contact will not be mapped yet, and a channel that silently swallowed
  those would be indistinguishable from one that worked;
* **the gates come first.** With the flag off or the token unset, no HTTP client is
  constructed at all — which is what makes AC-11's "the offline suite makes zero
  network calls" true by construction rather than by luck.

Transport is injected everywhere (``httpx.MockTransport``), so nothing here can reach
LINE even if a gate were wrongly open.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx
import pytest

from services.api.config import settings
from services.notify.line import (
    EVENT_RECIPIENTS,
    LineEvent,
    Recipient,
    build_message,
    describe_arm_state,
    notify,
    reset_cooldown,
)

_OWNER_ID = "Uowner000000000000000000000000000"
_OPERATOR_ID = "Uoperator0000000000000000000000000"
_TIER_ID = "Utier00000000000000000000000000000"

_DETAIL = {
    "truck": "80-1234 กรุงเทพมหานคร",
    "amount_thb": 48000,
    "case_id": "case-abc123",
    "approver_role": "เจ้าของกิจการ",
    "due_at": "2026-08-05",
    "task": "แจ้งอู่",
    "stale_days": 3,
    "period": "2026-07",
    "row_count": 12,
    "traceable_pct": 92,
}


class _Recorder:
    """Captures every push instead of sending one."""

    def __init__(self, status: int = 200) -> None:
        self.calls: list[dict] = []
        self.status = status

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.calls.append(
                {
                    "url": str(request.url),
                    "auth": request.headers.get("authorization"),
                    "body": json.loads(request.content),
                }
            )
            return httpx.Response(self.status, json={})

        return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _armed(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Arm the channel with a fake token + recipient map, and clear cooldowns."""
    monkeypatch.setattr(settings, "line_notify_enabled", True)
    monkeypatch.setattr(settings, "line_channel_access_token", "test-token")
    monkeypatch.setattr(
        settings,
        "line_recipients",
        json.dumps({"owner": _OWNER_ID, "operator": _OPERATOR_ID, "เจ้าของกิจการ": _TIER_ID}),
    )
    reset_cooldown()
    yield
    reset_cooldown()


# --------------------------------------------------------------------------- #
# The five events reach the right people
# --------------------------------------------------------------------------- #


def test_every_ac8_event_has_a_recipient_rule() -> None:
    """AC-8 names five events; every one has a non-empty recipient tuple.

    A set-equality check, not a spot check: an event added later without a recipient
    decision fails here rather than shipping as a message nobody receives."""
    assert set(EVENT_RECIPIENTS) == set(LineEvent)
    assert all(EVENT_RECIPIENTS[event] for event in LineEvent)


async def test_approval_needed_goes_to_the_resolved_tier_not_the_owner() -> None:
    """The ladder resolved ``เจ้าของกิจการ`` for this ฿48,000 spend, so the push goes
    to that role's id.

    This is the case that would rot most quietly. Defaulting approval requests to the
    owner would look fine in a demo and would recreate exactly the bottleneck the DOA
    ladder was built to remove — วิรัช would never be asked about the repairs that are
    his to approve."""
    recorder = _Recorder()

    result = await notify(
        LineEvent.APPROVAL_NEEDED,
        _DETAIL,
        resolved_approver="เจ้าของกิจการ",
        transport=recorder.transport(),
    )

    assert result.delivered
    assert result.sent_to == ("เจ้าของกิจการ",)
    assert len(recorder.calls) == 1
    assert recorder.calls[0]["body"]["to"] == _TIER_ID
    assert recorder.calls[0]["auth"] == "Bearer test-token"
    assert "api.line.me" in recorder.calls[0]["url"]


async def test_ratification_reminders_reach_both_owner_and_operator() -> None:
    """Two people, two pushes — the owner signs, เมย์ is the one who chases."""
    recorder = _Recorder()

    result = await notify(LineEvent.RATIFICATION_OVERDUE, _DETAIL, transport=recorder.transport())

    assert set(result.sent_to) == {"owner", "operator"}
    assert {call["body"]["to"] for call in recorder.calls} == {_OWNER_ID, _OPERATOR_ID}


async def test_an_unmapped_recipient_is_reported_not_swallowed() -> None:
    """The accounting contact is not mapped yet — an ordinary onboarding state.

    The owner still gets the file notice, and the gap is named in the result and
    logged. A bare boolean return would have rounded this to "sent", and nobody would
    have discovered accounting was never on the channel."""
    recorder = _Recorder()

    result = await notify(LineEvent.EXPORT_READY, _DETAIL, transport=recorder.transport())

    assert result.sent_to == ("owner",)
    assert result.unmapped == ("accounting",)
    assert result.delivered, "a partial delivery is still a delivery"
    assert len(recorder.calls) == 1


async def test_an_unmapped_resolved_approver_blocks_nothing_and_hides_nothing() -> None:
    """A tier whose role has no LINE id yet reports unmapped rather than falling back
    to the owner. Silently rerouting an approval request to someone else's phone would
    misattribute a governance moment."""
    recorder = _Recorder()

    result = await notify(
        LineEvent.APPROVAL_NEEDED,
        _DETAIL,
        resolved_approver="ผจก.เดินรถ",
        transport=recorder.transport(),
    )

    assert result.sent_to == ()
    assert result.unmapped == ("ผจก.เดินรถ",)
    assert recorder.calls == []


# --------------------------------------------------------------------------- #
# The gates — and AC-11's no-network guarantee
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("line_notify_enabled", False),
        ("line_channel_access_token", ""),
        ("line_recipients", ""),
    ],
)
async def test_a_disarmed_channel_never_reaches_the_transport(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    """AC-11: with any gate shut, nothing outbound is even attempted.

    **The assertion is a RECORDED list, not a raising handler, and that is the point.**
    The first version of this case used a transport that raised if touched — and a
    probe proved it vacuous: ``_push`` carries a blanket ``except Exception`` (correct
    on its own terms — a notification must never break its caller), which swallowed the
    explosion and returned ``False``, so every assertion still passed with the gate
    removed entirely. Recording the call and asserting the record is empty afterwards
    cannot be swallowed by anything.
    """
    touched: list[str] = []

    def record(request: httpx.Request) -> httpx.Response:
        touched.append(str(request.url))
        return httpx.Response(200, json={})

    monkeypatch.setattr(settings, field, value)

    result = await notify(
        LineEvent.APPROVAL_NEEDED,
        _DETAIL,
        resolved_approver="เจ้าของกิจการ",
        transport=httpx.MockTransport(record),
    )

    assert touched == [], "a disarmed channel must not reach the transport at all"
    assert not result.delivered
    assert result.sent_to == ()


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("line_notify_enabled", False, "LINE_NOTIFY_ENABLED=false"),
        ("line_channel_access_token", "", "LINE_CHANNEL_ACCESS_TOKEN unset"),
        ("line_recipients", "", "LINE_RECIPIENTS empty"),
        ("line_recipients", "{not json", "LINE_RECIPIENTS empty"),
    ],
)
def test_the_boot_diagnostic_names_the_closed_gate(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object, expected: str
) -> None:
    """A mis-armed channel is a silent per-call no-op, so the startup line has to say
    WHICH gate is shut — the same reason the Telegram notifier carries one."""
    monkeypatch.setattr(settings, field, value)

    state = describe_arm_state()

    assert state.startswith("DISARMED")
    assert expected in state


def test_an_armed_channel_says_so_without_leaking_the_token() -> None:
    """The boot log reports readiness and recipient COUNT — never the token itself."""
    state = describe_arm_state()

    assert state.startswith("ARMED")
    assert "test-token" not in state


# --------------------------------------------------------------------------- #
# Failure + throttling behaviour
# --------------------------------------------------------------------------- #


async def test_a_failing_push_never_raises_into_the_caller() -> None:
    """A notification failure must not break the governed path that triggered it — the
    approval still happened, the message just did not arrive, and the result says so."""
    recorder = _Recorder(status=500)

    result = await notify(LineEvent.RATIFICATION_DUE, _DETAIL, transport=recorder.transport())

    assert not result.delivered
    assert set(result.failed) == {"owner", "operator"}


async def test_the_same_event_to_the_same_person_is_throttled() -> None:
    """A daily overdue sweep must not re-push the same reminder every run.

    Repetition is how a channel gets muted, and a muted channel is worse than none —
    the partner would stop reading the one surface the pilot added."""
    recorder = _Recorder()

    first = await notify(
        LineEvent.RATIFICATION_OVERDUE, _DETAIL, transport=recorder.transport(), now=1000.0
    )
    second = await notify(
        LineEvent.RATIFICATION_OVERDUE, _DETAIL, transport=recorder.transport(), now=1010.0
    )

    assert len(first.sent_to) == 2
    assert second.sent_to == ()
    assert set(second.throttled) == {"owner", "operator"}
    assert len(recorder.calls) == 2, "only the first round reached the transport"


async def test_a_different_event_is_not_debounced_by_an_earlier_one() -> None:
    """Cooldowns are per (event, recipient). An overdue reminder must never suppress an
    approval request to the same person — they are different asks with different
    urgency, and collapsing them would drop the one that matters."""
    recorder = _Recorder()

    await notify(
        LineEvent.RATIFICATION_OVERDUE, _DETAIL, transport=recorder.transport(), now=1000.0
    )
    result = await notify(
        LineEvent.APPROVAL_NEEDED,
        _DETAIL,
        resolved_approver="เจ้าของกิจการ",
        transport=recorder.transport(),
        now=1001.0,
    )

    assert result.sent_to == ("เจ้าของกิจการ",)


# --------------------------------------------------------------------------- #
# Message bodies
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("event", list(LineEvent))
def test_every_event_builds_a_non_empty_thai_body(event: LineEvent) -> None:
    """Every member of the closed set renders. A body that fell through to empty would
    push a blank message — visibly broken to the operator, invisible in the code."""
    text = build_message(event, _DETAIL)

    assert text.strip()
    assert len(text) < 500, "these are read on a lock screen"


def test_the_approval_body_carries_the_facts_that_make_it_actionable() -> None:
    """Truck, amount and who must act. A push that said only "a repair needs approval"
    would send the reader to a screen to find out which one — which is the LINE
    archaeology this pilot exists to end."""
    text = build_message(LineEvent.APPROVAL_NEEDED, _DETAIL)

    assert "80-1234" in text
    assert "฿48,000" in text
    assert "เจ้าของกิจการ" in text


def test_no_credential_ever_reaches_a_message_body() -> None:
    """The bodies carry operational facts about the operator's own fleet — never a
    token. Asserted rather than assumed, because the arm state and the push share a
    module and a copy-paste is all it would take."""
    for event in LineEvent:
        assert "test-token" not in build_message(event, _DETAIL)


def test_recipient_roles_are_a_closed_set() -> None:
    """Every recipient named in the table is a declared role, so a typo in the table
    cannot become an id lookup that silently never matches."""
    named = {r for recipients in EVENT_RECIPIENTS.values() for r in recipients}

    assert named <= set(Recipient)
