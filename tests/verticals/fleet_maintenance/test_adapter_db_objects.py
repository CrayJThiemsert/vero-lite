"""PLAN-0109 AC-6 / AC-7 / AC-10 — the fleet adapter's DB branch.

Every DB-backed type is read from a row seeded with its ruled-OUT columns NON-NULL, so the
absence of those columns from the projected dict is an exclusion with a positive control
beside it, not the vacuous absence of a field that was empty anyway (CLAUDE.md §8). The
ruled-IN free text round-trips verbatim; timestamps leave as ISO strings and money as float.

The synthetic half (AC-7) is compared against the unchanged base adapter rather than against
remembered values, so "untouched" is measured, not recalled.

DB-backed tests SKIP when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.db.base import Base
from services.db.repair_case import RepairCase
from services.db.repair_case_evidence import RepairCaseAcceptedQuote, RepairCaseQuote
from services.engine.registry import registry
from tests.db_support import create_test_engine, drop_all_bounded
from verticals.fleet_maintenance.data_adapter import (
    FleetMaintenanceSyntheticAdapter,
    register_fleet_maintenance_adapter,
)
from verticals.fleet_maintenance.data_adapter.db_objects import (
    NEWEST_FIRST_COLUMN,
    FleetMaintenanceAdapter,
)
from verticals.fleet_maintenance.data_adapter.db_projection import DB_BACKED_TYPES

_OPENED = datetime(2026, 9, 1, 8, 30, tzinfo=UTC)
_DESCRIPTION = "เบรกไม่อยู่ ขาลงเขาปากช่อง"
_VENDOR = "อู่ช่างเอก"
_NOTE = "ลูกค้าประจำ ขอส่วนลด"
_REASON = "อู่ที่ถูกกว่าไม่มีอะไหล่ ต้องรอสองอาทิตย์"

#: AC-6's pass read, fixed before the build: exactly the declared property set per type.
_REPAIR_CASE_KEYS = {
    "case_id",
    "truck_id",
    "opened_by",
    "opened_at",
    "description",
    "status",
    "work_type",
}
_QUOTE_KEYS = {"quote_id", "case_id", "vendor", "amount_thb", "entered_by", "entered_at"}
_ACCEPTED_KEYS = {
    "accepted_id",
    "case_id",
    "quote_id",
    "reason",
    "accepted_by",
    "accepted_at",
    "lowest_amount_at_acceptance_thb",
    "lowest_at_acceptance_basis",
}


@pytest.fixture
async def maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(eng, expire_on_commit=False)
    async with eng.begin() as conn:
        await drop_all_bounded(conn)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def _seed(maker: async_sessionmaker[AsyncSession]) -> None:
    """One case with a photo, one quote with a note AND a document, one acceptance with a reason."""
    upload = {
        "content_type": "image/jpeg",
        "size_bytes": 12,
        "uploaded_at": _OPENED.isoformat(),
    }
    async with maker() as session:
        session.add(
            RepairCase(
                case_id="case-a",
                truck_id="truck-01",
                opened_by="req-mechanic-tom",
                opened_at=_OPENED,
                description=_DESCRIPTION,
                work_type="breakdown",
                photos=[
                    {**upload, "photo_id": "p1", "filename": "front.jpg", "stored_path": "a/p1"}
                ],
            )
        )
        await session.flush()
        session.add(
            RepairCaseQuote(
                quote_id="quote-a",
                case_id="case-a",
                vendor=_VENDOR,
                amount_thb=Decimal("12000.00"),
                entered_by="req-mechanic-tom",
                entered_at=_OPENED + timedelta(minutes=5),
                note=_NOTE,
                attachment={
                    **upload,
                    "photo_id": "q1",
                    "filename": "quote.jpg",
                    "stored_path": "a/q1",
                },
            )
        )
        await session.flush()
        session.add(
            RepairCaseAcceptedQuote(
                accepted_id="accept-a",
                case_id="case-a",
                quote_id="quote-a",
                reason=_REASON,
                accepted_by="appr-fleet-manager-wirat",
                accepted_at=_OPENED + timedelta(minutes=30),
                lowest_amount_at_acceptance_thb=Decimal("9500.00"),
                lowest_at_acceptance_basis="recorded",
            )
        )
        await session.commit()


async def _only_row(maker: async_sessionmaker[AsyncSession], object_type: str) -> dict[str, object]:
    rows = await FleetMaintenanceAdapter(session_factory=maker).fetch_objects(object_type)
    assert len(rows) == 1, f"{object_type}: expected the one seeded row, read {len(rows)}"
    return rows[0]


# --------------------------------------------------------------------------- #
# AC-6 — the projection, per type
# --------------------------------------------------------------------------- #


async def test_a_repair_case_is_projected_onto_its_declared_properties(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(maker)
    async with maker() as session:
        stored_photos = (await session.execute(sa.select(RepairCase.photos))).scalar_one()
    # Positive control: the row really carries a photo.
    assert stored_photos

    row = await _only_row(maker, "RepairCase")

    assert "photos" not in row
    assert set(row) == _REPAIR_CASE_KEYS
    assert row["description"] == _DESCRIPTION
    assert datetime.fromisoformat(str(row["opened_at"])) == _OPENED
    assert isinstance(row["opened_at"], str)


async def test_a_quote_is_projected_without_its_note_or_its_document(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(maker)
    async with maker() as session:
        stored = (
            await session.execute(sa.select(RepairCaseQuote.note, RepairCaseQuote.attachment))
        ).one()
    # Positive control: the row really carries a note and a document.
    assert stored.note == _NOTE
    assert stored.attachment is not None

    row = await _only_row(maker, "RepairCaseQuote")

    assert "note" not in row
    assert "attachment" not in row
    assert set(row) == _QUOTE_KEYS
    assert row["vendor"] == _VENDOR
    assert row["amount_thb"] == 12000.0
    assert type(row["amount_thb"]) is float


async def test_an_accepted_quote_is_projected_with_its_reason_and_without_its_seq(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(maker)
    async with maker() as session:
        stored_seq = (await session.execute(sa.select(RepairCaseAcceptedQuote.seq))).scalar_one()
    # Positive control: the database really assigned a seq.
    assert stored_seq is not None

    row = await _only_row(maker, "RepairCaseAcceptedQuote")

    assert "seq" not in row
    assert set(row) == _ACCEPTED_KEYS
    assert row["reason"] == _REASON
    assert row["lowest_amount_at_acceptance_thb"] == 9500.0


async def test_rows_come_newest_first_so_a_limit_keeps_the_newest(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    async with maker() as session:
        for case_id, minutes in (("case-older", 0), ("case-newer", 60)):
            session.add(
                RepairCase(
                    case_id=case_id,
                    truck_id="truck-01",
                    opened_by="req-mechanic-tom",
                    opened_at=_OPENED + timedelta(minutes=minutes),
                )
            )
        await session.commit()

    rows = await FleetMaintenanceAdapter(session_factory=maker).fetch_objects("RepairCase", limit=1)

    assert [row["case_id"] for row in rows] == ["case-newer"]


def test_every_db_backed_type_has_a_newest_first_column() -> None:
    assert set(NEWEST_FIRST_COLUMN) == set(DB_BACKED_TYPES)


# --------------------------------------------------------------------------- #
# AC-7 — the synthetic half is untouched, and the registrar serves the new adapter
# --------------------------------------------------------------------------- #


async def test_the_synthetic_types_are_served_exactly_as_the_base_adapter_serves_them() -> None:
    base, extended = FleetMaintenanceSyntheticAdapter(), FleetMaintenanceAdapter()
    differing = [
        object_type
        for object_type in ("Truck", "Depot", "Vendor")
        if await extended.fetch_objects(object_type) != await base.fetch_objects(object_type)
    ]
    assert differing == []


async def test_health_check_keeps_every_existing_key_and_adds_exactly_one() -> None:
    base = await FleetMaintenanceSyntheticAdapter().health_check()
    extended = await FleetMaintenanceAdapter().health_check()
    assert {key: extended[key] for key in base} == base
    assert set(extended) - set(base) == {"db_backed_types"}


def test_the_registrar_registers_the_db_aware_adapter() -> None:
    adapter = register_fleet_maintenance_adapter()
    assert isinstance(adapter, FleetMaintenanceAdapter)
    assert registry.get_adapter("fleet_maintenance") is adapter


def test_the_subclass_overrides_only_the_three_methods_it_must() -> None:
    """What makes the golden oracle's two-line registrar substitution honest.

    Row 4 of the scaffolder oracle treats the donor registrar instantiating this class as
    equivalent to instantiating the scaffolded base. That holds only while this is a true
    subclass that leaves ``fetch_links`` / ``stream_events`` to the base.
    """
    assert issubclass(FleetMaintenanceAdapter, FleetMaintenanceSyntheticAdapter)
    overridden = sorted(
        name for name, value in vars(FleetMaintenanceAdapter).items() if inspect.isfunction(value)
    )
    assert overridden == ["__init__", "fetch_objects", "health_check"]
