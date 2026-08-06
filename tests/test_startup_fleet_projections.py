"""The boot-time fleet projection loads actually RUN (PLAN-0096 Step 8/9 / AC-10).

Both loads sit behind ``except Exception`` handlers whose whole job is to let the
DB-less demo (PLAN-0095) boot. That fail-soft is correct, and it is also a place where
a *programming* error can hide indefinitely: a NameError raised inside the ``try``
lands in the same handler as an unreachable database and logs the same reassuring
"NOT loaded — serving fixture values" line. An operator reading that line has no way to
tell "no database here" from "this code has never once executed".

It happened. ``async_session`` was imported inside the ``vertical == "procurement"``
seed branch, which made it function-local for the whole of ``lifespan`` (Python binds
locals at compile time), so every boot that was not a procurement demo-seed boot —
including ``OCT_VERTICAL=fleet_maintenance`` itself — raised UnboundLocalError into the
fail-soft handler. Both refreshes were dead code against a perfectly healthy Postgres.

So the guard is here rather than left to the fail-soft path to notice. No test here
needs a database: opening an ``AsyncSession`` does not connect
(``services/db/session.py`` is a lazy-engine module), so the first proves the refreshes
are REACHED with the real session open, the second lets both real refreshes run and
asserts that whatever failure the handler absorbs is a database failure and not a bug,
and the third pins the reporting split itself — independently of which exception types
``_is_environment_absent`` ends up classifying, so it neither presumes that policy nor
goes stale when it lands.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api import main
from services.api.main import app
from services.db.case_events import CaseFacts
from verticals.fleet_maintenance import case_projection, pm_projection

#: Substrings that mean "a name in this module did not resolve", not "the database is
#: not there". A genuine connection failure names a host, a port, or a driver; it never
#: names a Python identifier local to ``services.api.main``.
_NAME_BUG_MARKERS = (
    "async_session",
    "pm_projection",
    "case_projection",
    "not associated with a value",
    "is not defined",
)


@pytest.fixture(autouse=True)
def _clean_projections() -> Iterator[None]:
    """Both views are process-global; a boot in one test would leak into the next."""
    pm_projection.reset()
    case_projection.reset()
    yield
    pm_projection.reset()
    case_projection.reset()


def test_boot_reaches_both_fleet_projection_refreshes(monkeypatch: pytest.MonkeyPatch) -> None:
    """The refreshes run at startup — the regression that made them dead code.

    Stubs only the two projection reads (their own behaviour is covered by
    ``tests/verticals/fleet_maintenance/test_case_projection.py`` and the DB-backed
    scenario suites). Everything up to the call is the real thing: the real lifespan,
    the real discovery, the real ``async_session`` open. Before the import was hoisted
    to module scope this recorded nothing at all.
    """
    reached: list[str] = []

    async def _record_pm(session: AsyncSession) -> dict[str, dict[str, float]]:
        assert isinstance(session, AsyncSession)
        reached.append("pm")
        return {}

    async def _record_case(
        session: AsyncSession, *, now: datetime | None = None
    ) -> list[CaseFacts]:
        assert isinstance(session, AsyncSession)
        reached.append("case")
        return []

    monkeypatch.setattr(pm_projection, "refresh", _record_pm)
    monkeypatch.setattr(case_projection, "refresh", _record_case)

    with TestClient(app):
        pass

    assert reached == ["pm", "case"], (
        "the boot-time fleet projection loads did not run — PLAN-0096 Step 8/9 is dead "
        f"code on this boot (reached: {reached})"
    )


def test_an_absorbed_fleet_load_failure_is_a_database_failure_not_a_bug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Nothing stubbed: both real refreshes run, and the fail-soft handler is read.

    Whether they succeed depends on whether a database is reachable, which is exactly
    what must NOT be asserted here — this test has to pass in CI (no database) and on a
    dev box (one running) alike. What is invariant either way is the *class* of failure
    the handler is allowed to absorb.
    """
    with caplog.at_level(logging.INFO, logger="uvicorn.error"), TestClient(app):
        pass
    messages = [record.getMessage() for record in caplog.records]

    # Precondition, read from the SUT's own output: the block ran at all. Without this
    # the assertions below pass vacuously the moment the fleet block stops executing.
    pm_lines = [m for m in messages if "fleet PM overrides" in m]
    case_lines = [m for m in messages if "fleet live cases" in m]
    assert pm_lines, "no boot line for the PM view — the fleet block did not run"
    assert case_lines, "no boot line for the live-case view — the fleet block did not run"

    # Checked two ways on purpose, because a code bug surfaces differently depending on
    # whether _is_environment_absent has been filled in yet: today it is absorbed as the
    # reason on the WARNING, and once the policy lands it becomes an ERROR carrying a
    # traceback. Asserting only the first would go quietly vacuous the day it changes.
    fleet_errors = [
        r
        for r in caplog.records
        if r.levelno >= logging.ERROR
        and ("fleet PM overrides" in r.getMessage() or "fleet live cases" in r.getMessage())
    ]
    assert not fleet_errors, (
        "a boot-time fleet load failed with a PROGRAMMING error, not an unreachable "
        f"database: {[r.getMessage() for r in fleet_errors]}"
    )
    for line in (*pm_lines, *case_lines):
        if "NOT loaded" not in line:
            continue
        for marker in _NAME_BUG_MARKERS:
            assert marker not in line, (
                f"the fail-soft handler absorbed a programming error, not an unreachable "
                f"database ({marker!r} in the logged reason): {line}"
            )


@pytest.mark.parametrize("environmental", [True, False])
def test_the_two_boot_failure_causes_are_reported_differently(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, environmental: bool
) -> None:
    """The reporting split, pinned independently of the classification policy.

    ``_is_environment_absent`` is stubbed on both sides rather than exercised, so this
    tests the half that is finished — that the two causes produce *distinguishable*
    output — without presuming which exception types Cray's policy will sort where.
    Both branches keep the process alive; only the volume and the recorded reason differ.
    """
    recorded: list[str] = []
    monkeypatch.setattr(main, "_is_environment_absent", lambda exc: environmental)

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        main._absorb_boot_load_failure(
            recorded.append,
            NameError("cannot access local variable 'async_session'"),
            what="fleet PM overrides",
            degraded="trucks serve fixture values",
        )

    (record,) = (r for r in caplog.records if "fleet PM overrides" in r.getMessage())
    (reason,) = recorded
    if environmental:
        assert record.levelno == logging.WARNING
        assert record.exc_info is None, "an absent database does not need a traceback"
        assert not reason.startswith("BUG:")
        assert "cannot access local variable" in record.getMessage()
    else:
        assert record.levelno == logging.ERROR, "a code bug must not log at WARNING"
        assert record.exc_info is not None, "a code bug must carry its traceback"
        assert reason.startswith(
            "BUG: "
        ), f"health_check must be able to tell a bug from a missing database, got {reason!r}"
        assert "PROGRAMMING error" in record.getMessage()
