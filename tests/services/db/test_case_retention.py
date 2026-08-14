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


async def test_delete_case_erases_one_named_case_and_leaves_its_neighbour_standing(
    db_engine: AsyncEngine, tmp_path: Path
) -> None:
    """The DSR shape ``sweep`` cannot express: one NAMED case, whatever its age.

    ``sweep`` selects its work set from ``opened_at`` and can say nothing else,
    so this is the seam a DSR-on-request path calls. Both halves are asserted:
    a unit that erased the whole table would satisfy "the named case is gone"
    just as happily, and the neighbour is deliberately YOUNGER than the cutoff —
    an age-driven deletion would have spared it for the wrong reason, so it is
    also the case a leaked age filter would visibly fail to touch.
    """
    photo_root = tmp_path / "photos"
    (photo_root / "case-named").mkdir(parents=True)
    (photo_root / "case-named" / "photo-abc.jpg").write_bytes(b"jpeg-bytes")

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        session.add_all(
            [
                _case("case-named", age_days=1),
                _case("case-neighbour", age_days=1),
            ]
        )
        await session.flush()
        session.add(
            RepairCaseTaskEvent(
                event_id="evt-1",
                case_id="case-named",
                item_key="arrange_tow",
                status="done",
                actor="req-mechanic-tom",
                at=_NOW - timedelta(days=1),
            )
        )
        await session.commit()

    async with maker() as session:
        await repair_case_retention.delete_case(session, "case-named", photo_root=photo_root)

    async with maker() as session:
        survivors = sorted((await session.execute(sa.select(RepairCase.case_id))).scalars())
        orphans = list(
            (
                await session.execute(
                    sa.select(RepairCaseTaskEvent.event_id).where(
                        RepairCaseTaskEvent.case_id == "case-named"
                    )
                )
            ).scalars()
        )
    assert survivors == ["case-neighbour"], "a DSR erasure must not reach past the named case"
    assert orphans == [], "the named case's FK children go with it"
    assert not (photo_root / "case-named").exists(), "and so does its upload directory"


async def test_delete_case_leaves_the_session_usable_after_a_failure(
    db_engine: AsyncEngine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RULED (Cray, typed, s232): the deletion unit rolls back its OWN partial work.

    The failure is injected by emptying ``_FK_CHILD_MODELS`` so the root delete
    hits a live ForeignKeyViolation — a real DB-level abort AFTER a statement has
    run, which is the only shape that actually dirties the session. Injecting at
    ``rmtree`` instead would raise before any SQL and this test would pass
    against a unit that never rolled back at all: green by construction, proving
    nothing.

    Asserted by USING the session rather than inspecting it. A session left
    inside a failed transaction raises on its next statement, so a query that
    SUCCEEDS is the proof — and it survives any refactor of how the rollback is
    spelled. The caller (``sweep`` today, a DSR path tomorrow) never has to know
    it inherited a mess.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        session.add(_case("case-x", age_days=1))
        await session.flush()
        session.add(
            RepairCaseTaskEvent(
                event_id="evt-x",
                case_id="case-x",
                item_key="arrange_tow",
                status="done",
                actor="req-mechanic-tom",
                at=_NOW - timedelta(days=1),
            )
        )
        await session.commit()

    monkeypatch.setattr(repair_case_retention, "_FK_CHILD_MODELS", ())

    async with maker() as session:
        with pytest.raises(Exception):  # noqa: B017 — the driver's FK error, not our type
            await repair_case_retention.delete_case(session, "case-x", photo_root=tmp_path)

        # No rollback of our own: if delete_case did not clean up, this raises.
        survivors = list((await session.execute(sa.select(RepairCase.case_id))).scalars())

    assert survivors == ["case-x"], (
        "the failed deletion must leave the row intact AND the session usable — "
        "a raise here instead means delete_case propagated without rolling back"
    )


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
