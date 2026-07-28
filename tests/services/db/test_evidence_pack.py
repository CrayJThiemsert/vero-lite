"""PLAN-0096 Step 3 / AC-4 (data half) — the quote evidence pack.

The pack is the seam Step 4 computes `compliance.three_quote` from, so its counting
is governance-critical: get `distinct_vendor_count` wrong and a repair that was never
price-compared sails through a rule the partner adopted after being defrauded on
parts. These tests therefore lean hardest on the cases where "how many quotes" and
"how many vendors" DISAGREE.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker

from services.db.base import Base
from services.db.evidence_pack import load_evidence_pack
from services.db.repair_case import CASE_STATUS_OPEN, RepairCase
from services.db.repair_case_evidence import RepairCaseJustification, RepairCaseQuote
from tests.db_support import create_test_engine

_BASE_TIME = datetime(2026, 7, 20, 3, 0, tzinfo=UTC)


async def _session_factory() -> async_sessionmaker:
    engine = await create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


def _case(case_id: str = "case-t1") -> RepairCase:
    return RepairCase(
        case_id=case_id,
        truck_id="truck-01",
        opened_by="admin-may",
        opened_at=_BASE_TIME,
        description=None,
        status=CASE_STATUS_OPEN,
        photos=[],
    )


def _quote(case_id: str, n: int, vendor: str, amount: str, attachment: dict | None = None):
    return RepairCaseQuote(
        quote_id=f"quote-{n}",
        case_id=case_id,
        vendor=vendor,
        amount_thb=Decimal(amount),
        entered_by="admin-may",
        entered_at=_BASE_TIME + timedelta(minutes=n),
        note=None,
        attachment=attachment,
    )


async def test_an_empty_pack_reports_zeroes_rather_than_raising() -> None:
    """A case with no evidence yet is a NORMAL state, not an error.

    Step 4 must fail CLOSED on it — but that is Step 4's judgment to make from
    facts. Raising here would push the decision into exception handling, where a
    caller's ``except`` could quietly turn 'no evidence recorded' into 'carry on'."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        await session.commit()
        pack = await load_evidence_pack(session, "case-t1")

    assert pack.quote_count == 0
    assert pack.distinct_vendor_count == 0
    assert pack.has_sole_source_justification is False
    assert pack.lowest_amount_thb is None
    assert pack.quotes_on_file is False


async def test_three_quotes_from_three_vendors_is_a_real_comparison() -> None:
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        session.add_all(
            [
                _quote("case-t1", 1, "อู่ช่างเล็ก", "48000.00"),
                _quote("case-t1", 2, "ส.เจริญยนต์", "45500.50"),
                _quote("case-t1", 3, "อู่ริมทางปากช่อง", "51000.00"),
            ]
        )
        await session.commit()
        pack = await load_evidence_pack(session, "case-t1")

    assert pack.quote_count == 3
    assert pack.distinct_vendor_count == 3
    assert pack.lowest_amount_thb == Decimal("45500.50")
    assert pack.has_sole_source_justification is False


async def test_three_quotes_from_one_vendor_is_not_three_vendors() -> None:
    """The case that makes the two counts worth reporting separately.

    Three quotes from the same garage — a revision, a re-quote, a second call — is
    not a price comparison, and the partner's Q10 rule is three PLACES ("สามเจ้า").
    A pack that reported only ``quote_count`` would let Step 4 wave this through as
    'three quotes on file', which is the exact hollow-compliance shape the sourcing
    rule exists to prevent."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        session.add_all(
            [
                _quote("case-t1", 1, "อู่ช่างเล็ก", "48000.00"),
                _quote("case-t1", 2, "อู่ช่างเล็ก", "47000.00"),
                _quote("case-t1", 3, "อู่ช่างเล็ก", "46000.00"),
            ]
        )
        await session.commit()
        pack = await load_evidence_pack(session, "case-t1")

    assert pack.quote_count == 3
    assert pack.distinct_vendor_count == 1


async def test_vendor_identity_ignores_case_and_surrounding_whitespace() -> None:
    """เมย์ types these by hand from whatever the paperwork says.

    "SomChai Motors" and "somchai motors " are one vendor, and counting them as two
    would INFLATE the comparison — the direction of error that matters, because it
    manufactures compliance that did not happen. Nothing fuzzier than trim+casefold
    is attempted: fuzzy matching would start merging vendors the operator meant to
    keep apart, which hides a genuine single-source situation."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        session.add_all(
            [
                _quote("case-t1", 1, "SomChai Motors", "10000.00"),
                _quote("case-t1", 2, "somchai motors ", "10500.00"),
                _quote("case-t1", 3, "  Different Shop", "9900.00"),
            ]
        )
        await session.commit()
        pack = await load_evidence_pack(session, "case-t1")

    assert pack.quote_count == 3
    assert pack.distinct_vendor_count == 2


async def test_justifications_are_append_only_and_the_latest_describes_the_position() -> None:
    """A correction is a new row; the earlier attempt stays on the record."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        session.add_all(
            [
                RepairCaseJustification(
                    justification_id="just-1",
                    case_id="case-t1",
                    vendor="ศูนย์ฮีโน่",
                    reason="อะไหล่เฉพาะรุ่น ศูนย์เดียวที่มีของ",
                    entered_by="admin-may",
                    entered_at=_BASE_TIME + timedelta(minutes=1),
                ),
                RepairCaseJustification(
                    justification_id="just-2",
                    case_id="case-t1",
                    vendor="ศูนย์ฮีโน่ สาขาโคราช",
                    reason="แก้ไข: สาขาโคราชเป็นที่เดียวที่มีของพร้อมส่ง",
                    entered_by="appr-fleet-manager-wirat",
                    entered_at=_BASE_TIME + timedelta(minutes=9),
                ),
            ]
        )
        await session.commit()
        pack = await load_evidence_pack(session, "case-t1")

    assert pack.has_sole_source_justification is True
    assert pack.sole_source_vendor == "ศูนย์ฮีโน่ สาขาโคราช"
    assert "แก้ไข" in (pack.sole_source_reason or "")


async def test_a_pack_only_sees_its_own_case() -> None:
    """Cross-case bleed would be the worst possible failure here: case B's quotes
    satisfying case A's sourcing rule is fabricated compliance, and it would be
    invisible in every UI."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case("case-a"))
        session.add(_case("case-b"))
        session.add_all(
            [
                _quote("case-a", 1, "Vendor A1", "1000.00"),
                _quote("case-b", 2, "Vendor B1", "2000.00"),
                _quote("case-b", 3, "Vendor B2", "2200.00"),
            ]
        )
        await session.commit()
        pack_a = await load_evidence_pack(session, "case-a")
        pack_b = await load_evidence_pack(session, "case-b")

    assert (pack_a.quote_count, pack_a.distinct_vendor_count) == (1, 1)
    assert (pack_b.quote_count, pack_b.distinct_vendor_count) == (2, 2)
    assert pack_a.vendors == ("Vendor A1",)


async def test_a_quote_without_a_document_is_sql_null_not_jsonb_null() -> None:
    """The trap this asserts against was real, and measured on the dev DB.

    SQLAlchemy's JSONB default renders Python ``None`` as the JSON value ``null``,
    which is not SQL NULL. Three rows were stored — one deliberately without a
    document — and all three reported ``attachment IS NULL = false``. The Python-side
    pack was correct throughout (it counted 2 documents), so nothing user-visible was
    wrong; what was wrong was that any SQL asking "which quotes are missing their
    paperwork" would have returned NOTHING, forever, silently. Step 8's month-end
    export is precisely that query.

    Asserted in SQL rather than through the ORM on purpose: reading it back through
    Python would return ``None`` either way and prove nothing."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        session.add_all(
            [
                _quote("case-t1", 1, "V1", "100.00", attachment={"photo_id": "p1"}),
                _quote("case-t1", 2, "V2", "200.00", attachment=None),
            ]
        )
        await session.commit()

        nulls = (
            (
                await session.execute(
                    sa.text(
                        "SELECT vendor FROM repair_case_quote "
                        "WHERE attachment IS NULL ORDER BY vendor"
                    )
                )
            )
            .scalars()
            .all()
        )

    assert list(nulls) == [
        "V2"
    ], "a quote with no document must be SQL NULL so the export can find it"


async def test_attachment_count_tracks_documents_not_quotes() -> None:
    """A quote keyed off a phone call is still a quote; it is just weaker evidence,
    and the export needs to be able to say which is which."""
    maker = await _session_factory()
    async with maker() as session:
        session.add(_case())
        session.add_all(
            [
                _quote("case-t1", 1, "V1", "100.00", attachment={"photo_id": "p1"}),
                _quote("case-t1", 2, "V2", "200.00", attachment=None),
            ]
        )
        await session.commit()
        pack = await load_evidence_pack(session, "case-t1")

    assert pack.quote_count == 2
    assert pack.attachment_count == 1
