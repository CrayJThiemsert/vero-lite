"""The month-end export, end to end (PLAN-0096 Step 8 item 5 / AC-9).

The constitutional scenario test for this build (CLAUDE.md §8): a real repair case
captured over the real HTTP routes, approved through the real gate driver, closed out
through the real close-out route, then downloaded through the real export endpoint.

**Nothing is stubbed on either side of the seam, and the seam is long.** The producer
is `POST /api/cases` + `/quotes` + `/accepted-quote` + `POST /procedures/{id}/run`;
the middle is the real `resolve_gated_step` firing the real registered hook; the
consumer is `GET /api/exports/repair-spend/{year}/{month}.csv`. A test that handed a
list of hand-built rows to `to_csv` would prove the formatter formats and say nothing
about whether a repair anybody actually did ever reaches the file — and "the export is
empty for real work" is the failure this build exists to prevent.

**The month under test is derived from the run, never from the wall clock.** The gate
decision lands at `datetime.now()`, so the export is asked for the Asia/Bangkok month
that decision fell in. Hard-coding a month would make this suite start failing on the
first of every month, and pinning `now` would take the endpoint's own clock out of
the path — the one thing the scenario is here to exercise.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.repair_spend_export import CSV_ENCODING, EXPORT_COLUMNS
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.action_step import (
    WaiverInvocation,
    ratify_gated_step,
    resolve_gated_step,
)
from services.engine.procedures.spec import load_procedures
from tests.support.accounting_month import accounting_month
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.sourcing import PASSING_BASES

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"
_OWNER = "appr-owner"
_MECHANIC = "req-mechanic-tom"
BKK = ZoneInfo("Asia/Bangkok")

_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


def _person(person_id: str) -> Any:
    spec = load_procedures(_VERTICAL)
    return next(p for p in spec.principals if p.person_id == person_id)


async def _accepted_case(client: AsyncClient, *, vendor: str = "อู่คู่สัญญา ปากช่อง") -> str:
    """A real ฿62,000 axle case with three garages compared and one agreed.

    ``vendor`` is a parameter because the agreed garage decides whether the export
    can fill รหัสผู้ขาย: the contracted garage has an Express code and `เจ๊หงส์` does
    not. That is the difference the KPI is built to notice.
    """
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทางแถวปากช่อง",
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]
    chosen = ""
    for name, amount in ((vendor, "62000.00"), ("ส.เจริญยนต์", "58000.00"), ("อู่ช่างเล็ก", "59500.00")):
        quoted = await client.post(
            f"/api/cases/{case_id}/quotes",
            data={"vendor": name, "amount_thb": amount},
            headers=_HEADERS,
        )
        assert quoted.status_code == 201, quoted.text
        if name == vendor:
            chosen = quoted.json()["quote_id"]
    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": chosen, "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้"},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text
    return case_id


async def _approve_through_the_gate(
    client: AsyncClient, session: AsyncSession, case_id: str
) -> None:
    """Fire the hero and approve THIS case at the real gate; reject the rest.

    The gate refuses a partial resolution, so the fixture rows riding along in the
    same round must each be decided too.
    """
    fired = await client.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    body: dict[str, Any] = fired.json()
    ours = next(str(p["action_id"]) for p in body["proposals"] if case_id in str(p["action_id"]))
    decisions = {
        str(p["action_id"]): ("approve" if str(p["action_id"]) == ours else "reject")
        for p in body["proposals"]
    }
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    await resolve_gated_step(
        session,
        body["run_id"],
        _GATE_STEP,
        decisions,
        _person(_OWNER),
        procedure=procedure,
        principals=list(spec.principals),
    )
    assert gate_hooks.failures() == [], "the hook is fail-soft; a swallowed error must show here"


async def _resolve_provisionally(client: AsyncClient, session: AsyncSession, case_id: str) -> str:
    """ต้อม RECORDS a decision เฮีย gave by phone — ADR-0034's E-2 path.

    The recorder is the mechanic, not the owner, and that is the whole shape of it:
    the approval happened on the shoulder of a road, so the person at a keyboard is
    recording someone else's authority. No `governed_decision` tie is emitted until
    that someone signs, which is exactly why the export must read the attested
    approver from the ratification block instead.
    """
    fired = await client.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    body: dict[str, Any] = fired.json()
    ours = next(str(p["action_id"]) for p in body["proposals"] if case_id in str(p["action_id"]))
    decisions = {
        str(p["action_id"]): ("approve" if str(p["action_id"]) == ours else "reject")
        for p in body["proposals"]
    }
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    await resolve_gated_step(
        session,
        body["run_id"],
        _GATE_STEP,
        decisions,
        _person(_MECHANIC),
        procedure=procedure,
        principals=list(spec.principals),
        waiver_invocation=WaiverInvocation(
            justification="รถเสียกลางทาง โทรหาเฮียแล้วเคาะมาว่าให้ซ่อมเลย"
        ),
    )
    assert gate_hooks.failures() == []
    return str(body["run_id"])


async def _ratify(session: AsyncSession, run_id: str, *, decision: str = "ratify") -> None:
    """เฮีย signs afterwards — the ONLY path to `ratify_gated_step`.

    There is no HTTP route for this; `services/api/routers/` has no ratify endpoint,
    so the driver IS the production surface and calling it directly is the real
    consumer rather than a shortcut around one.
    """
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    await ratify_gated_step(
        session,
        run_id,
        _GATE_STEP,
        _person(_OWNER),
        decision=decision,  # type: ignore[arg-type]
        procedure=procedure,
        principals=list(spec.principals),
    )
    assert gate_hooks.failures() == []


async def _key_closeout(client: AsyncClient, case_id: str, *, vendor: str) -> None:
    keyed = await client.post(
        f"/api/cases/{case_id}/closeout",
        json={
            "vendor": vendor,
            "tax_invoice_no": "INV-2026-0042",
            "tax_invoice_date": "2026-07-28",
            "amount_pre_vat_thb": "57943.93",
            "vat_thb": "4056.07",
            "total_thb": "62000.00",
        },
        headers=_HEADERS,
    )
    assert keyed.status_code == 201, keyed.text


def _parse(body: bytes) -> tuple[list[str], list[dict[str, str]]]:
    """Decode and parse exactly as a consumer would, BOM included."""
    text = body.decode(CSV_ENCODING)
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def _this_month() -> tuple[int, int]:
    """The Asia/Bangkok accounting month the gate decision just landed in.

    Delegates to the shared helper so the timezone rule has ONE home. This
    module had it right; two other modules wrote their own version against the
    UTC clock and took `main` red at the s266 month boundary.
    """
    return accounting_month(datetime.now(UTC))


async def test_a_real_approved_repair_reaches_the_month_end_file(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """THE claim: open a case, approve it, close it out — and it is in the file.

    Every column asserted here was produced by a different part of the system: the
    order number by the close-out route, the approver by the gate, the vehicle code
    by the ontology fixture, the sourcing basis by the hook reading the engine's own
    artifact. A green here means all of them agree about one repair.
    """
    case_id = await _accepted_case(client_with_db)
    await _approve_through_the_gate(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    year, month = _this_month()
    got = await client_with_db.get(
        f"/api/exports/repair-spend/{year}/{month}.csv", headers=_HEADERS
    )
    assert got.status_code == 200, got.text
    assert got.headers["content-type"].startswith("text/csv")
    assert f"repair-spend-{year}-{month:02d}.csv" in got.headers["content-disposition"]

    header, rows = _parse(got.content)
    assert header == list(EXPORT_COLUMNS), "the file's own header must be AC-9's 15 columns"
    assert len(rows) == 1, "one governed repair, one Express entry"
    row = rows[0]
    assert row["เลขที่ใบกำกับภาษี"] == "INV-2026-0042"
    assert row["วันที่เอกสาร"] == "2026-07-28"
    assert row["ผู้ขาย / อู่"] == "อู่คู่สัญญา ปากช่อง"
    assert row["รหัสผู้ขาย"] == "V-001"
    assert row["ทะเบียนรถ"] == "80-1234 กรุงเทพมหานคร"
    assert row["รหัสรถ"] == "T-001"
    assert row["ประเภทงาน"] == "breakdown"
    assert row["จำนวนเงินรวม"] == "62000.00"
    assert row["ผู้อนุมัติ"] == _OWNER, "the gate's approver, not the recorder"
    assert row["เลขที่ใบแจ้งซ่อม"].startswith("RC-"), "the human-readable repair-order number"
    assert row["ศูนย์ต้นทุน"] == "", "ships unfilled pending the partner's granularity answer"


async def test_the_file_is_readable_by_excel_on_windows(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The bytes carry a UTF-8 BOM.

    Not a nicety: เมย์ opens this by double-clicking it, and Excel on Windows reads a
    BOM-less UTF-8 file as the system codepage — every Thai header and vendor name
    becomes mojibake while the file stays perfectly valid UTF-8 to any tool used to
    check it. The failure is invisible to the developer and total for the user.
    """
    case_id = await _accepted_case(client_with_db)
    await _approve_through_the_gate(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    year, month = _this_month()
    got = await client_with_db.get(
        f"/api/exports/repair-spend/{year}/{month}.csv", headers=_HEADERS
    )

    assert got.content.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM missing — Excel will mojibake this"
    assert "วันที่เอกสาร" in got.content.decode(CSV_ENCODING)


async def test_the_cover_reports_the_kpi_for_the_same_month(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The cover and the file describe the same data, computed the same way."""
    case_id = await _accepted_case(client_with_db)
    await _approve_through_the_gate(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    year, month = _this_month()
    cover = await client_with_db.get(
        f"/api/exports/repair-spend/{year}/{month}/cover", headers=_HEADERS
    )
    assert cover.status_code == 200, cover.text
    body = cover.json()

    assert body["row_count"] == 1
    assert body["traceable_row_count"] == 1
    assert body["traceability_pct"] == 100.0
    assert body["ungoverned_row_count"] == 0
    assert body["total_thb"] == "62000.00"


async def test_an_uncoded_vendor_drops_the_live_kpi_below_one_hundred(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-9's non-vacuity bar, on the REAL end-to-end path.

    Identical to the happy case in every respect except the garage: `เจ๊หงส์` is used
    but not yet opened in Express. The unit tests already show the predicate notices;
    this shows the whole pipeline does, which is the claim the KPI actually makes.
    """
    case_id = await _accepted_case(client_with_db, vendor="เจ๊หงส์")
    await _approve_through_the_gate(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="เจ๊หงส์")

    year, month = _this_month()
    cover = await client_with_db.get(
        f"/api/exports/repair-spend/{year}/{month}/cover", headers=_HEADERS
    )
    body = cover.json()

    assert body["row_count"] == 1
    assert body["traceable_row_count"] == 0
    assert body["traceability_pct"] == 0.0

    got = await client_with_db.get(
        f"/api/exports/repair-spend/{year}/{month}.csv", headers=_HEADERS
    )
    _, rows = _parse(got.content)
    assert rows[0]["ผู้ขาย / อู่"] == "เจ๊หงส์"
    assert rows[0]["รหัสผู้ขาย"] == "", "reported honestly as blank, never guessed"


async def test_the_sourcing_basis_survives_the_whole_round_trip(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The basis the gate saw reaches the cover's audit-answer proxy (alembic 0022).

    The full path: `compute_three_quote` -> the ingested event -> the engine's
    persisted artifact -> the hook -> the link column -> the export. Five hand-offs,
    any one of which could drop it silently.
    """
    case_id = await _accepted_case(client_with_db)
    await _approve_through_the_gate(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    from services.db.repair_spend_export import load_monthly_export

    year, month = _this_month()
    export = await load_monthly_export(db_session, year=year, month=month, now=datetime.now(UTC))

    (row,) = export.rows
    assert row.three_quote_basis in PASSING_BASES
    assert export.cover_summary().audit_answer_pct == 100.0


async def test_a_month_with_no_spend_is_an_empty_file_not_an_error(
    client_with_db: AsyncClient, fleet_active: None
) -> None:
    """An empty month is a real answer, and the header still has to be there.

    A 404 would be wrong — "nothing was spent" and "the report does not exist" are
    different facts, and an accountant checking a quiet month deserves the first.
    """
    got = await client_with_db.get("/api/exports/repair-spend/2019/3.csv", headers=_HEADERS)
    assert got.status_code == 200
    header, rows = _parse(got.content)
    assert header == list(EXPORT_COLUMNS)
    assert rows == []

    cover = await client_with_db.get("/api/exports/repair-spend/2019/3/cover", headers=_HEADERS)
    assert cover.json()["traceability_pct"] is None, "no spend has no score, never 100"


async def test_an_emergency_approval_appears_on_the_cover_as_a_labelled_exception(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Step 10's exception walkthrough: waiver → provisional → the export says so.

    The row is in the file like any other repair — the money was spent and accounting
    must key it — and the cover names it as an outstanding obligation. Both at once is
    the point: an export that hid emergency spend would understate the month, and one
    that only flagged it without listing it would leave accounting nothing to key.

    **ผู้อนุมัติ is เฮีย, not ต้อม.** No `governed_decision` tie exists yet on this
    path, so a reader that fell back to `audit_log.actor_person_id` would print the
    mechanic who keyed the record as the person who authorised the spend.
    """
    case_id = await _accepted_case(client_with_db)
    await _resolve_provisionally(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    year, month = _this_month()
    cover = (
        await client_with_db.get(
            f"/api/exports/repair-spend/{year}/{month}/cover", headers=_HEADERS
        )
    ).json()

    assert cover["row_count"] == 1, "emergency spend is still spend — it stays in the file"
    assert cover["outstanding_ratification_count"] == 1
    (exception,) = cover["exceptions"]
    assert exception["case_id"] == case_id
    assert exception["state"] == "pending"
    assert exception["approver"] == _OWNER, "the ATTESTED approver, never the recorder"
    assert exception["total_thb"] == "62000.00"
    assert exception["justification_ref"], "the tamper-evident handle must be carried"

    got = await client_with_db.get(
        f"/api/exports/repair-spend/{year}/{month}.csv", headers=_HEADERS
    )
    _, rows = _parse(got.content)
    assert rows[0]["ผู้อนุมัติ"] == _OWNER


async def test_ratifying_afterwards_changes_the_label_the_export_shows(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The second half of the exception walkthrough: เฮีย signs, the report moves.

    Same month, same money, same row — only the obligation's standing changes. An
    export that could not show that would make the whole deferred-ratification
    mechanism invisible to the person chasing signatures, which is the one job the
    reconciliation window exists to support.
    """
    case_id = await _accepted_case(client_with_db)
    run_id = await _resolve_provisionally(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    year, month = _this_month()
    before = (
        await client_with_db.get(
            f"/api/exports/repair-spend/{year}/{month}/cover", headers=_HEADERS
        )
    ).json()
    assert before["exceptions"][0]["state"] == "pending"
    assert before["outstanding_ratification_count"] == 1

    await _ratify(db_session, run_id)

    after = (
        await client_with_db.get(
            f"/api/exports/repair-spend/{year}/{month}/cover", headers=_HEADERS
        )
    ).json()
    assert after["exceptions"][0]["state"] == "ratified"
    assert after["outstanding_ratification_count"] == 0, "nobody owes a signature any more"
    assert after["row_count"] == before["row_count"], "the money did not move, only the standing"


async def test_an_ordinary_approval_produces_no_exception_entry(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The contrast case, without which the two tests above prove nothing.

    If every approval produced an exception entry, `state == "pending"` above would be
    satisfied by a report that flagged the entire month.
    """
    case_id = await _accepted_case(client_with_db)
    await _approve_through_the_gate(client_with_db, db_session, case_id)
    await _key_closeout(client_with_db, case_id, vendor="อู่คู่สัญญา ปากช่อง")

    year, month = _this_month()
    cover = (
        await client_with_db.get(
            f"/api/exports/repair-spend/{year}/{month}/cover", headers=_HEADERS
        )
    ).json()

    assert cover["row_count"] == 1
    assert cover["exceptions"] == []
    assert cover["outstanding_ratification_count"] == 0


async def test_an_impossible_month_is_refused(
    client_with_db: AsyncClient, fleet_active: None
) -> None:
    """Month 13 is a 422, not a 500 from date arithmetic deep in the reader."""
    got = await client_with_db.get("/api/exports/repair-spend/2026/13.csv", headers=_HEADERS)
    assert got.status_code == 422
