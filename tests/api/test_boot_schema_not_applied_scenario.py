"""PLAN-0103 Step 10 — the boot report when the schema was never migrated.

CLAUDE.md §8 scenario test. It drives the **real** producer into the **real**
consumer: a genuinely schemaless Postgres, the real `case_projection.refresh`
query, the real `asyncpg` error, the real SQLAlchemy wrapper, and the real
`_absorb_boot_load_failure` arm — with only the log captured.

⚠️ **A fabricated exception would make this test vacuous.** The whole claim under
test is that `_is_schema_not_applied` recognises what the driver *actually*
raises: a hand-built object carrying `sqlstate="42P01"` would agree with the
implementation by construction and would still pass if asyncpg reported the code
somewhere else, or if SQLAlchemy stopped exposing `.orig`. So the fault is
injected by **omitting `create_all`** — the same omission a real bring-up makes
when it skips `alembic upgrade head`.

DB-backed against the disposable test DB. These tests **skip when Postgres is
unreachable**, and a skip is never satisfaction.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.main import (
    _absorb_boot_load_failure,
    _is_environment_absent,
    _is_schema_not_applied,
)
from services.db.base import Base
from tests.db_support import create_test_engine
from verticals.fleet_maintenance import case_projection


@pytest.fixture
async def schemaless_engine() -> AsyncIterator[AsyncEngine]:
    """A REACHABLE database with NO tables — the state `up -d` leaves behind.

    Deliberately never calls `Base.metadata.create_all`. That omission IS the
    scenario: it is what a bring-up that skipped `alembic upgrade head` produces,
    and it is the only way to obtain the driver's own error rather than one this
    test invented.
    """
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    yield eng
    await eng.dispose()


@pytest.fixture(autouse=True)
def _clean_projection() -> AsyncIterator[None]:
    case_projection.reset()
    yield
    case_projection.reset()


async def _real_missing_table_error(engine: AsyncEngine) -> Exception:
    """Provoke the driver's genuine undefined_table failure via the real reader."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        try:
            await case_projection.refresh(session)
        except Exception as exc:  # the object under test IS the exception
            return exc
    raise AssertionError(
        "case_projection.refresh() SUCCEEDED against a schemaless database — the "
        "fixture is not producing the scenario it claims to, so every assertion "
        "below would be vacuous"
    )


async def test_the_real_driver_error_is_recognised_as_schema_not_applied(
    schemaless_engine: AsyncEngine,
) -> None:
    """The classifier matches what asyncpg REALLY raises, not what we assumed it does.

    This is the assertion that a mock could not make. It fails if the SQLSTATE is
    wrong, if SQLAlchemy stops exposing `.orig`, or if the driver reports the code
    on a different attribute — each a silent regression that would send the boot
    log back to describing an unmigrated schema as an absent database.
    """
    exc = await _real_missing_table_error(schemaless_engine)

    assert _is_schema_not_applied(exc), (
        f"the driver's real undefined_table error was not recognised: {exc!r} — "
        "the boot log will misreport a skipped migration as an absent database"
    )


async def test_the_boot_report_names_the_cause_and_the_command_that_fixes_it(
    schemaless_engine: AsyncEngine, caplog: pytest.LogCaptureFixture
) -> None:
    """A RED that names what broke, per Lesson #0043 — applied to a boot log.

    Asserted on the rendered message rather than on the format string, because
    what an operator standing at the host actually reads is the rendered line.
    """
    exc = await _real_missing_table_error(schemaless_engine)
    recorded: list[str] = []

    with caplog.at_level(logging.INFO):
        _absorb_boot_load_failure(
            recorded.append,
            exc,
            what="fleet live cases",
            degraded="the event stream serves the synthetic fixture only",
        )

    schema_records = [r for r in caplog.records if "SCHEMA IS NOT APPLIED" in r.getMessage()]
    assert len(schema_records) == 1, "exactly one boot line should name the cause"
    record = schema_records[0]
    message = record.getMessage()

    assert record.levelno == logging.ERROR, (
        "an unmigrated schema on a system about to be published is not a WARNING — "
        "it warned at WARNING level before s232 and read as an ordinary DB-less boot"
    )
    assert "alembic upgrade head" in message, "the line must carry the fix, not just the fault"
    assert "alembic current" in message, "and the confirmation step"
    assert "HEALTHY" in message, (
        "the line must say the process will report healthy anyway — that is the part "
        "an operator cannot infer, and the reason the failure reaches a visitor"
    )
    assert recorded == [f"SCHEMA NOT APPLIED: {exc}"], (
        "the projection's own status must carry the cause too: the boot log scrolls, "
        "the recorded reason is what a later reader sees"
    )


async def test_the_catch_all_also_claims_this_error_which_is_why_arm_order_matters(
    schemaless_engine: AsyncEngine,
) -> None:
    """Pins the PRECONDITION that makes the ordering load-bearing — not the ordering.

    ⚠️ Name says what it does. Reordering the two arms does **not** redden this
    test; it reddens
    ``test_the_boot_report_names_the_cause_and_the_command_that_fixes_it``, which
    reads the log the reordering would change. This one exists because that
    protection is only meaningful while the catch-all still swallows this error:
    `_is_environment_absent` is a stub that absorbs everything, so it returns True
    here too, and a reorder would hand the operator "absent database" — the exact
    misdescription the schema arm exists to prevent, invisible because both arms
    are fail-soft and the process boots either way.

    If the stub is ever replaced and this assertion goes False, the ordering has
    stopped being load-bearing: revisit both tests rather than deleting either.
    """
    exc = await _real_missing_table_error(schemaless_engine)

    assert _is_environment_absent(exc), (
        "precondition: the catch-all still claims this error — if this ever goes "
        "False the ordering below stops being load-bearing and this test should be "
        "revisited rather than deleted"
    )
    assert _is_schema_not_applied(exc), "and the specific arm also claims it"
