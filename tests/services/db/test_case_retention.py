"""PLAN-0105 Step 1 — the case-retention sweep (AC-1, AC-4, AC-9, and the
unit-level half of AC-2/AC-3).

DB-backed against the disposable test DB. ⚠️ These tests **skip when Postgres is
unreachable**, and the PLAN is explicit that a skip is never satisfaction: an AC
closes only on a run where the test actually executed.

The full seven-table + disk + projection aftermath on realistic data is Step 6's
scenario test (AC-10, CLAUDE.md §8). What lives here is the sweep's own
behaviour: the age boundary, the deletion set, and what a partial failure leaves
behind.
"""

from __future__ import annotations

import ast
import shutil
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db import repair_case_retention
from services.db.base import Base
from services.db.repair_case import RepairCase
from services.db.repair_case_retention import CASE_RETENTION_DAYS, sweep
from services.db.repair_case_run_link import RepairCaseRunLink
from services.db.repair_case_task import RepairCaseTaskEvent
from tests.db_support import create_test_engine
from verticals.fleet_maintenance import case_projection

_NOW = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture(autouse=True)
def _clean_projection() -> AsyncIterator[None]:
    """The sweep refreshes the in-memory projection, which is module-global.

    Without this the state one test leaves behind is read by the next one — the
    same class of leak that makes a globally-cached view serve deleted rows in
    production, which is precisely what the refresh exists to prevent.
    """
    case_projection.reset()
    yield
    case_projection.reset()


def _case(case_id: str, *, age_days: int) -> RepairCase:
    """One visitor-opened case, aged by moving ``opened_at`` into the past.

    Ages the DATA's timeline rather than stubbing the clock the sweep reads:
    ``opened_at`` is the real anchor, so a case aged this way is
    indistinguishable from one that genuinely sat there for that long.
    """
    return RepairCase(
        case_id=case_id,
        truck_id="TRK-01",
        opened_by="req-mechanic-tom",
        opened_at=_NOW - timedelta(days=age_days),
        description=f"เบรกมีเสียงดัง ({case_id})",
    )


async def test_ac1_the_boundary_is_the_cutoff_not_a_neighbourhood(db_engine: AsyncEngine) -> None:
    """89 days survives, 91 days goes — the same boundary shape the prompt log uses.

    Asserting only "an old case is deleted" would pass just as happily against a
    sweep that deleted everything, which is the failure that would matter most.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        session.add_all(
            [
                _case("case-young", age_days=CASE_RETENTION_DAYS - 1),
                _case("case-old", age_days=CASE_RETENTION_DAYS + 1),
            ]
        )
        await session.commit()

    async with maker() as session:
        report = await sweep(session, photo_root=Path("/nonexistent"), now=_NOW)

    assert report.expired_found == 1
    assert report.deleted == 1
    assert report.failed_case_ids == ()
    assert report.cutoff == _NOW - timedelta(days=CASE_RETENTION_DAYS)

    async with maker() as session:
        survivors = set(
            (await session.execute(sa.select(RepairCase.case_id))).scalars(),
        )
    assert survivors == {"case-young"}, "the 89-day case must survive its own boundary"


async def test_the_fk_children_go_and_the_run_link_is_deliberately_left_standing(
    db_engine: AsyncEngine,
) -> None:
    """SD-1 (b) deletes the FK children; SD-4 (a) RETAINS the run link.

    The run-link assertion is a POSITIVE presence check, never the absence of a
    delete: that table carries no FK, so a sweep that simply forgot it would look
    identical to one that deliberately kept it. Asserting presence is what makes
    the ruling testable at all.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        session.add(_case("case-old", age_days=CASE_RETENTION_DAYS + 1))
        await session.flush()
        session.add(
            RepairCaseTaskEvent(
                event_id="evt-1",
                case_id="case-old",
                item_key="arrange_tow",
                status="done",
                actor="req-mechanic-tom",
                at=_NOW - timedelta(days=CASE_RETENTION_DAYS),
            )
        )
        session.add(
            RepairCaseRunLink(
                link_id="link-1",
                case_id="case-old",
                run_id="run-1",
                step_id="approve",
                outcome="ratified",
                linked_at=_NOW - timedelta(days=CASE_RETENTION_DAYS),
            )
        )
        await session.commit()

    async with maker() as session:
        report = await sweep(session, photo_root=Path("/nonexistent"), now=_NOW)
    assert report.deleted == 1

    async with maker() as session:
        events = list(
            (
                await session.execute(
                    sa.select(RepairCaseTaskEvent.event_id).where(
                        RepairCaseTaskEvent.case_id == "case-old"
                    )
                )
            ).scalars()
        )
        links = list(
            (
                await session.execute(
                    sa.select(RepairCaseRunLink.link_id).where(
                        RepairCaseRunLink.case_id == "case-old"
                    )
                )
            ).scalars()
        )
    assert events == [], "the FK child must go with its parent"
    assert links == ["link-1"], "SD-4 (a): the run link is RETAINED — asserted as presence"


async def test_ac4_a_failed_unlink_leaves_the_row_and_the_next_pass_finishes_the_job(
    db_engine: AsyncEngine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files-first (SD-2 (a)) makes the unreachable-and-undeleted state unconstructible.

    The fault is injected at the OS boundary BELOW the seam under test — the seam
    being the sweep's ordering and error handling, which is exactly what must not
    be stubbed. With the row still present, the bytes are still discoverable
    (the row names every ``stored_path``) and the case is retried; had rows gone
    first, a stranded file would be findable by nothing at all.
    """
    photo_root = tmp_path / "photos"
    case_dir = photo_root / "case-old"
    case_dir.mkdir(parents=True)
    (case_dir / "photo-abc.jpg").write_bytes(b"jpeg-bytes")

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        session.add(_case("case-old", age_days=CASE_RETENTION_DAYS + 1))
        await session.commit()

    def _refuse(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("simulated: the directory could not be removed")

    monkeypatch.setattr(shutil, "rmtree", _refuse)
    async with maker() as session:
        blocked = await sweep(session, photo_root=photo_root, now=_NOW)

    assert blocked.expired_found == 1
    assert blocked.deleted == 0
    assert blocked.failed_case_ids == ("case-old",), "a failed case is NAMED so it can be fixed"

    async with maker() as session:
        still_there = list((await session.execute(sa.select(RepairCase.case_id))).scalars())
    assert still_there == ["case-old"], "the row survives so the bytes stay discoverable"
    assert (case_dir / "photo-abc.jpg").exists()

    monkeypatch.undo()
    async with maker() as session:
        retried = await sweep(session, photo_root=photo_root, now=_NOW)

    assert retried.deleted == 1
    assert retried.failed_case_ids == ()
    assert not case_dir.exists(), "the retry removes the directory it could not remove before"
    async with maker() as session:
        remaining = list((await session.execute(sa.select(RepairCase.case_id))).scalars())
    assert remaining == []


def test_ac9_the_module_does_not_inherit_the_prompt_log_regime() -> None:
    """LOCKED-1's independence, enforced structurally rather than by comment.

    Reads the module's REAL import table out of its source, not a list this test
    keeps of its own — a guard that checked its own copy would agree with itself
    forever. ADR-0035 D6 governs the prompt log; it does not reach case text, so
    a future change to D6's 90 must not silently move this one, and vice versa.
    """
    source = Path(repair_case_retention.__file__).read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    offenders = sorted(m for m in imported if "prompt_log" in m)
    assert not offenders, (
        f"the case-retention module imports {offenders} — LOCKED-1 makes its 90 days an "
        "INDEPENDENT decision that merely coincides with the prompt log's"
    )
