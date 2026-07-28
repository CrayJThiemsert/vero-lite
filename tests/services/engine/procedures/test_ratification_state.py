"""PLAN-0096 Step 5 / AC-5 + AC-6 — the ratification schema and the computed state.

Two claims, both offline:

* **AC-6, the schema-drift tripwire.** A waiver WITHOUT ``ratification_window_days``
  must serialise byte-identically to the pre-change model. This is AC-2's twin: AC-2
  catches YAML drift across verticals, this catches drift in the MODEL itself, and
  the field only exists at all because both were made to pass deliberately.
* **AC-5's pure half.** ``ratification_state`` is the function the render, the
  month-end export and the LINE reminder all read. It is a pure function of the
  record and an injected clock, so every boundary below is exact rather than
  approximately-now.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.engine.procedures.ratification import (
    RATIFICATION_KEY,
    due_at_from,
    ratification_state,
)
from services.engine.procedures.runs import StepResultStatus
from services.engine.procedures.spec import EmergencyWaiverPolicy

_DECIDED = datetime(2026, 7, 20, 9, 0, tzinfo=UTC)
_DUE = due_at_from(_DECIDED, 7)


def _audit(**block: object) -> dict[str, object]:
    return {
        RATIFICATION_KEY: {
            "due_at": _DUE.isoformat(),
            "ratify_by_role": "เจ้าของกิจการ",
            "attested_approver_id": "appr-owner",
            "recorded_by": "req-mechanic-tom",
            **block,
        }
    }


# --------------------------------------------------------------------------- #
# AC-6 — only-when-supplied, at the model
# --------------------------------------------------------------------------- #


def test_a_waiver_without_a_window_serialises_as_if_the_field_did_not_exist() -> None:
    """AC-6, and the reason the serializer on EmergencyWaiverPolicy exists.

    ``PipelineRun.governance_hash`` hashes the resolved config and FAILS CLOSED on a
    mismatch at resume — by design, so a mid-flight ladder edit can never silently
    govern an old run. A new field that always serialised (even as ``null``) would
    therefore have broken every in-flight run in every vertical the moment this model
    gained it, including five verticals that have never heard of ratification.

    Measured, not theoretical: neutering the serializer reddens the cross-vertical
    hash fixture for procurement and building_materials — the two verticals with
    doa_tier ladders — and leaves the other three green."""
    waiver = EmergencyWaiverPolicy(relaxes=["three_bid"], escalate_to="เจ้าของกิจการ")

    dumped = waiver.model_dump(mode="json")
    assert "ratification_window_days" not in dumped
    assert dumped == {
        "relaxes": ["three_bid"],
        "escalate_to": "เจ้าของกิจการ",
        "requires_justification": True,
        "justification": "",
    }


def test_an_authored_window_does_serialise() -> None:
    """The other half: only-when-supplied must not mean never-supplied. An authored
    window has to reach the pin, because it CHANGES what the gate may do."""
    waiver = EmergencyWaiverPolicy(
        relaxes=["three_bid"], escalate_to="เจ้าของกิจการ", ratification_window_days=7
    )
    assert waiver.model_dump(mode="json")["ratification_window_days"] == 7


def test_a_window_below_one_day_is_unrepresentable() -> None:
    """``ge=1``: a zero- or negative-day window would make an obligation that was
    overdue at the instant it was created, which is not a window at all."""
    for bad in (0, -1):
        with pytest.raises(ValueError):
            EmergencyWaiverPolicy(
                relaxes=["three_bid"], escalate_to="x", ratification_window_days=bad
            )


def test_the_provisional_status_is_additive_and_distinct() -> None:
    """The new member must not disturb the existing ones — persisted rows carry these
    strings, and a changed value would silently reinterpret history."""
    assert StepResultStatus.RESOLVED_PROVISIONAL.value == "resolved_provisional"
    assert StepResultStatus.RESOLVED.value == "resolved"
    assert StepResultStatus.WAITING_HUMAN.value == "waiting_human"


# --------------------------------------------------------------------------- #
# AC-5 (pure half) — the computed state, boundary by boundary
# --------------------------------------------------------------------------- #


def test_a_step_with_no_obligation_is_none_not_pending() -> None:
    """An ordinary approval has nothing to ratify.

    Reporting it as 'pending' would put every normal gate in the partner's chase
    list — the fastest possible way to teach him to ignore the list."""
    assert ratification_state(None, _DECIDED).state == "none"
    assert ratification_state({}, _DECIDED).state == "none"
    assert ratification_state({"doa_tier": []}, _DECIDED).state == "none"


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        pytest.param(_DECIDED, "pending", id="just-decided"),
        pytest.param(_DUE - timedelta(seconds=1), "pending", id="one-second-before-due"),
        pytest.param(_DUE, "pending", id="exactly-at-due-is-still-in-time"),
        pytest.param(_DUE + timedelta(seconds=1), "overdue", id="one-second-after-due"),
    ],
)
def test_the_overdue_boundary_is_exact(now: datetime, expected: str) -> None:
    """AC-5's ``due_at`` edge. Exactly-at-the-deadline is still IN time: the partner's
    control is "ไม่เกินอาทิตย์" — not exceeding a week — so the week itself is his."""
    assert ratification_state(_audit(), now).state == expected


def test_a_ratified_obligation_never_becomes_overdue_later() -> None:
    """Precedence, and it is not cosmetic. A terminal human act cannot be
    reinterpreted by the passage of time: if the owner signed inside the window, a
    report run a month later must still say 'ratified', not 'overdue'."""
    view = ratification_state(
        _audit(ratified_at=_DUE.isoformat(), ratified_by="appr-owner"),
        _DUE + timedelta(days=90),
    )
    assert view.state == "ratified"
    assert view.ratified_by == "appr-owner"
    assert view.is_outstanding is False


def test_a_refusal_is_terminal_and_outranks_everything() -> None:
    """The owner declining to ratify is an ANSWER, not a lapse.

    Nothing un-executes — the money is spent — so the honest record is a named,
    exported exception rather than a pretence that the obligation is still open
    (ADR-0034 D3(4): fail-VISIBLE, because fail-closed is impossible after the fact)."""
    view = ratification_state(
        _audit(refused_at=_DUE.isoformat(), refused_by="appr-owner"), _DUE + timedelta(days=90)
    )
    assert view.state == "refused"
    assert view.refused_by == "appr-owner"
    assert view.is_outstanding is False


def test_overdue_still_counts_as_outstanding() -> None:
    """Urgency changed; the obligation did not. A report that treated overdue as
    closed would retire exactly the cases that most need chasing."""
    pending = ratification_state(_audit(), _DECIDED)
    overdue = ratification_state(_audit(), _DUE + timedelta(days=3))
    assert pending.is_outstanding and overdue.is_outstanding


def test_the_view_carries_the_evidence_it_was_derived_from() -> None:
    """A caller told 'overdue' should not have to re-read the audit block to say WHO
    owes the signature — that round trip is where a second, drifting reader gets
    written."""
    view = ratification_state(_audit(), _DUE + timedelta(days=1))
    assert view.ratify_by_role == "เจ้าของกิจการ"
    assert view.attested_approver_id == "appr-owner"
    assert view.recorded_by == "req-mechanic-tom"
    assert view.due_at == _DUE


def test_a_malformed_due_at_does_not_crash_a_report() -> None:
    """Defensive on the READ side only. A corrupt timestamp must not take down the
    month-end export mid-run; it degrades to 'pending', which keeps the obligation
    visible and chaseable rather than silently dropping it."""
    view = ratification_state({RATIFICATION_KEY: {"due_at": "not-a-date"}}, _DECIDED)
    assert view.state == "pending"
    assert view.due_at is None
