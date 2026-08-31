"""Which accounting month a UTC instant belongs to. Tests only.

``load_monthly_export`` windows a month in ``EXPORT_TIMEZONE`` (Asia/Bangkok), so a
row stamped ``datetime.now(UTC)`` belongs to the month that is current **in
Bangkok**, not the month that is current in UTC. Those two disagree for the last
seven hours of every UTC month — 17:00 to 24:00 UTC on its final day — and a test
that seeds "now" and then asks for the **UTC** month goes red in that window with
nothing changed and nobody at fault.

Measured 2026-09-01 00:16 +07 (2026-08-31 17:16 UTC): five call sites across two
modules asked for month 8 while their own seed had landed in month 9, and ``main``
went red on the clock alone. ``month_bounds(2026, 8)`` ends at 2026-08-31T17:00Z;
the seeded audit row sat 16 minutes past it.

**The product is not affected and this helper is deliberately not in it.** The
export route takes ``year`` and ``month`` as path parameters — the caller names the
accounting month, which is the right shape for an accounting export — and nothing
in the product derives a month from a clock. If that ever changes, this is the rule
it must follow, and the function should move rather than be copied.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from services.db.repair_spend_export import EXPORT_TIMEZONE


def accounting_month(now: datetime) -> tuple[int, int]:
    """Return ``(year, month)`` of the accounting month ``now`` falls in."""
    local = now.astimezone(ZoneInfo(EXPORT_TIMEZONE))
    return local.year, local.month
