"""Deferred-ratification state — computed, never stored (ADR-0034 D3(6); PLAN-0096 Step 5).

A waiver-invoked gate can be decided FIRST and ratified after: the partner's own
practice, stated in Q9 as *"เคาะก่อน ทำเอกสารทีหลัง"*, with the control being not a ฿
cap but a reconciliation window — *"ไม่เกินอาทิตย์ บัญชีจะเริ่มถามแล้ว"* (Q11). This
module answers the one question that window raises: **where does this obligation
stand right now?**

**Why the answer is computed and not a column.** An obligation that expires would
otherwise need something to write ``overdue`` into the record at expiry — and there
is no principal performing that write. Every other state change in this engine is
attributable to a person or a declared service actor; an actor-less mutation would
be the first exception, and it would sit in exactly the audit trail whose whole
value is that every entry has an author. So expiry is a function of the record and
the clock, and the record itself only ever changes when a human does something to it.

The practical consequence is a good one: ``now`` is a parameter, so overdue logic is
fully testable offline with no clock manipulation, and the render, the month-end
export and the LINE reminder all derive the same answer from the same function
rather than three drifting copies.

Pure + deterministic: no DB, no network, no LLM, no ambient clock.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

#: The audit key the provisional resolution writes its obligation under.
RATIFICATION_KEY = "ratification"

RatificationState = Literal["none", "pending", "ratified", "overdue", "refused"]


@dataclass(frozen=True)
class RatificationView:
    """The computed standing of one step's ratification obligation.

    ``state`` is what a human or a report should act on; the rest is the evidence it
    was derived from, carried along so a caller never has to re-read the audit block
    to explain the answer it was just given.
    """

    state: RatificationState
    due_at: datetime | None = None
    ratify_by_role: str | None = None
    attested_approver_id: str | None = None
    recorded_by: str | None = None
    ratified_by: str | None = None
    refused_by: str | None = None

    @property
    def is_outstanding(self) -> bool:
        """True while someone still owes a signature — pending OR overdue.

        The distinction between those two is urgency, not obligation: an overdue
        ratification is still owed, and a report that treated 'overdue' as closed
        would quietly retire the very cases that most need chasing.
        """
        return self.state in ("pending", "overdue")


def _as_str(value: Any) -> str | None:
    """Narrow a JSONB-sourced value to ``str | None``.

    The audit block is JSONB, so nothing about its shape is guaranteed at the type
    level. Coercing here rather than trusting it keeps a corrupt record from putting
    a non-string into a field every consumer renders."""
    return value if isinstance(value, str) else None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def due_at_from(decided_at: datetime, window_days: int) -> datetime:
    """The ratification deadline for a decision taken at ``decided_at``.

    One place, so the driver that WRITES the deadline and any report that recomputes
    it can never disagree by a day.
    """
    return decided_at + timedelta(days=window_days)


def ratification_state(audit: Mapping[str, Any] | None, now: datetime) -> RatificationView:
    """Compute the ratification standing from a step's audit block.

    Returns ``state="none"`` when the step carries no ratification obligation at all —
    the overwhelmingly common case, since the provisional path is reachable only for a
    waiver-invoked resolution under an authored window. A step that never took that
    path is not "not yet ratified"; it has nothing to ratify, and conflating the two
    would make every ordinary approval look like an outstanding obligation.

    Precedence is refused > ratified > overdue > pending, and the order matters:
    a refusal and a ratification are both TERMINAL human acts, so neither may be
    reinterpreted as 'overdue' merely because the clock later passed the deadline.
    Only an obligation nobody has answered can go overdue.
    """
    if not audit:
        return RatificationView(state="none")
    block = audit.get(RATIFICATION_KEY)
    if not isinstance(block, Mapping):
        return RatificationView(state="none")

    due_at = _as_datetime(block.get("due_at"))

    def _view(
        state: RatificationState,
        *,
        ratified_by: str | None = None,
        refused_by: str | None = None,
    ) -> RatificationView:
        return RatificationView(
            state=state,
            due_at=due_at,
            ratify_by_role=_as_str(block.get("ratify_by_role")),
            attested_approver_id=_as_str(block.get("attested_approver_id")),
            recorded_by=_as_str(block.get("recorded_by")),
            ratified_by=ratified_by,
            refused_by=refused_by,
        )

    if block.get("refused_at") or block.get("refused_by"):
        return _view("refused", refused_by=_as_str(block.get("refused_by")))
    if block.get("ratified_at") or block.get("ratified_by"):
        return _view("ratified", ratified_by=_as_str(block.get("ratified_by")))
    if due_at is not None and now > due_at:
        return _view("overdue")
    return _view("pending")
