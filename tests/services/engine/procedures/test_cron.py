"""PLAN-0055 Step 3 (ADR-0028 SD-2) — the pure next_fire cron calculator (AC-10).

Offline, DB-free: exercises the croniter-backed ``next_fire`` helper — the per-schedule
IANA timezone semantics (SD-P1, incl. the TH-tz AC-10 case), the exclusive-of-``after``
walk, and the loud failure on a malformed cron the Step-2 ``Schedule`` descriptor deferred.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from croniter import CroniterError

from services.engine.procedures.cron import next_fire

BKK = ZoneInfo("Asia/Bangkok")


def test_daily_next_fire_in_bangkok() -> None:
    # 10:00 Bangkok -> next "06:00 daily" is the FOLLOWING morning, 06:00 +07:00.
    after = datetime(2026, 7, 7, 10, 0, tzinfo=BKK)
    assert next_fire("0 6 * * *", "Asia/Bangkok", after) == datetime(2026, 7, 8, 6, 0, tzinfo=BKK)


def test_th_tz_maps_to_correct_utc_instant() -> None:
    # AC-10 TH-tz case: 06:00 Asia/Bangkok == 23:00 UTC the previous day (UTC+7, no DST).
    after = datetime(2026, 7, 7, 3, 0, tzinfo=UTC)  # 10:00 Bangkok
    fired = next_fire("0 6 * * *", "Asia/Bangkok", after)
    assert fired.astimezone(UTC) == datetime(2026, 7, 7, 23, 0, tzinfo=UTC)
    # returned aware in the schedule's OWN zone (SD-P1), offset +07:00
    assert fired.utcoffset() == timedelta(hours=7)


def test_walk_is_exclusive_of_after() -> None:
    # `after` landing exactly on a fire slot -> the NEXT slot (never re-fire the same slot).
    on_slot = datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
    assert next_fire("0 6 * * *", "Asia/Bangkok", on_slot) == datetime(2026, 7, 8, 6, 0, tzinfo=BKK)


def test_interval_cron_next_quarter_hour() -> None:
    after = datetime(2026, 7, 7, 8, 7, tzinfo=BKK)
    assert next_fire("*/15 * * * *", "Asia/Bangkok", after) == datetime(
        2026, 7, 7, 8, 15, tzinfo=BKK
    )


def test_same_cron_different_tz_differ_by_instant() -> None:
    after = datetime(2026, 7, 7, 3, 0, tzinfo=UTC)
    bkk = next_fire("0 6 * * *", "Asia/Bangkok", after).astimezone(UTC)
    utc = next_fire("0 6 * * *", "UTC", after).astimezone(UTC)
    assert bkk != utc  # "06:00" in different zones are different instants


def test_naive_after_interpreted_as_local_wall_clock() -> None:
    # a naive `after` is read as already-local wall-clock in tz (10:00 Bangkok).
    fired = next_fire("0 6 * * *", "Asia/Bangkok", datetime(2026, 7, 7, 10, 0))
    assert fired == datetime(2026, 7, 8, 6, 0, tzinfo=BKK)


def test_malformed_cron_raises() -> None:
    # croniter is the authoritative parser — the Step-2 descriptor only checked non-blankness.
    with pytest.raises(CroniterError):
        next_fire("not a cron", "UTC", datetime(2026, 7, 7, 0, 0, tzinfo=UTC))
