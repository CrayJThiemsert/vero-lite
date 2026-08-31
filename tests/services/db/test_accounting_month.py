"""Clock-independent guard for the accounting-month rule (session 266).

The bug this closes is only observable for seven hours of each month, so a test
that merely runs "now" would pass for the other 99% of the time and prove nothing.
These cases pin instants **inside** the trap window explicitly.
"""

from __future__ import annotations

from datetime import UTC, datetime

from services.db.repair_spend_export import EXPORT_TIMEZONE, month_bounds
from tests.support.accounting_month import accounting_month


def test_the_accounting_month_is_the_bangkok_month_not_the_utc_month() -> None:
    """The exact instant that reddened `main` on 2026-08-31.

    17:16 UTC on the last day of August is already 00:16 on 1 September in Bangkok,
    so a row stamped then belongs to SEPTEMBER's report.
    """
    trap = datetime(2026, 8, 31, 17, 16, tzinfo=UTC)
    # Positive control: the UTC month really is the earlier one, so the assertion
    # below is about the conversion and not about a date that never differed.
    assert trap.month == 8
    assert accounting_month(trap) == (2026, 9)


def test_the_accounting_month_agrees_with_the_window_the_export_actually_uses() -> None:
    """The helper must name the month whose bounds CONTAIN the instant.

    This is the property the five call sites depend on, asserted against
    `month_bounds` itself rather than against a second copy of the timezone rule.
    """
    for instant in (
        datetime(2026, 8, 31, 16, 59, tzinfo=UTC),  # still August in Bangkok
        datetime(2026, 8, 31, 17, 0, tzinfo=UTC),  # September begins in Bangkok
        datetime(2026, 8, 31, 17, 16, tzinfo=UTC),  # the measured failure
        datetime(2026, 9, 15, 12, 0, tzinfo=UTC),  # mid-month, no ambiguity
    ):
        year, month = accounting_month(instant)
        start, end = month_bounds(year, month, timezone=EXPORT_TIMEZONE)
        assert start <= instant < end, f"{instant.isoformat()} is not inside its own month"


def test_the_utc_month_would_have_been_wrong_for_the_trap_instant() -> None:
    """Non-vacuity: the old rule really does put the row outside the window.

    Without this, the two tests above would still pass if `month_bounds` happened to
    be timezone-blind, and the helper would be guarding nothing.
    """
    trap = datetime(2026, 8, 31, 17, 16, tzinfo=UTC)
    start, end = month_bounds(trap.year, trap.month, timezone=EXPORT_TIMEZONE)
    assert not (start <= trap < end), "the UTC month would have contained it after all"
