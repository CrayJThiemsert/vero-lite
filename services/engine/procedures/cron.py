"""Pure cron next-fire calculator for the S1 scheduler (ADR-0028 SD-2; PLAN-0055 Step 3).

A thin, DB-free wrapper over ``croniter`` — the authoritative cron parser this step adds as
a production dependency (AC-10). :func:`next_fire` computes the next fire instant of a cron
expression evaluated in a per-schedule IANA timezone (SD-P1) — the value the Step-4 fire
function stamps into ``schedule_states.next_fire``. Kept SEPARATE from the ``schedules.py``
ORM so the calculation stays pure + trivially unit-testable (no DB, an injected ``after``).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from croniter import croniter


def next_fire(cron: str, tz: str, after: datetime) -> datetime:
    """The next instant ``cron`` fires strictly AFTER ``after``, evaluated in ``tz``.

    Timezone semantics (ADR-0028 SD-P1): cron fields are WALL-CLOCK in ``tz`` (an IANA
    zone) — ``"0 6 * * *"`` means 06:00 local in ``tz``, not UTC. ``after`` is normalised
    into ``tz`` first: an aware ``after`` is CONVERTED, a naive ``after`` is interpreted as
    already-local wall-clock in ``tz``. The returned datetime is tz-aware in ``tz``.

    The walk is EXCLUSIVE of ``after`` (croniter ``get_next`` semantics): if ``after`` lands
    exactly on a fire slot, the FOLLOWING slot is returned — so a scheduler never re-fires
    the slot it just fired.

    ``croniter`` is the authoritative parser (AC-10): a malformed cron raises a
    ``croniter.CroniterError`` here — the loud failure the Step-2 ``Schedule`` descriptor
    deferred (it validated the tz but only the non-blankness of the cron string).
    """
    zone = ZoneInfo(tz)
    base = after.astimezone(zone) if after.tzinfo is not None else after.replace(tzinfo=zone)
    fired: datetime = croniter(cron, base).get_next(datetime)
    return fired
