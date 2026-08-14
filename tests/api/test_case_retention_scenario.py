"""PLAN-0105 Step 6 / AC-10 — the retention scenario (CLAUDE.md §8, binding).

The real producer driven into the real consumer on realistic simulated data: a
visitor opens a case through Tab I's own routes with Thai free text, a photo, and
a quote pack; the case drives a governed run to a resolved gate, so real
``repair_case_run_link`` rows exist; the case is then really aged past the cutoff
and swept **through the callable the periodic task itself invokes**.

**Nothing on either side of the seam is mocked.** Two bindings are redirected —
which database, and which upload directory — because a test that deleted from the
dev DB or from the repo's real photo directory would be a different kind of
wrong. The sweep's ordering, its deletion set, its disk removal and its projection
refresh all run for real.

**Why the aftermath is inspected per table by name.** The AC's own wording:
*"not via a rowcount aggregate that could pass with one table forgotten"*. The
table list here is written out INDEPENDENTLY of the sweep's ``FK_CHILD_TABLES``
— if the test read the sweep's own list, dropping a table from that list would
silently stop the test checking it, which is the exact failure Step 4's guard and
this test are both aimed at. Step 4 ties both lists to the live metadata; this
one keeps its own copy on purpose.

**The control case is not decoration.** "The aged case is gone" passes just as
happily against a sweep that deleted everything, and a retention control that
deletes too much fails in the direction nobody notices until a partner asks for
their data.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api import case_retention_task
from services.api.config import settings
from services.db.repair_case import RepairCase
from services.db.repair_case_retention import CASE_RETENTION_DAYS
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.run_link import case_id_of

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"

_MECHANIC = "req-mechanic-tom"
_OWNER = "appr-owner"
_MECHANIC_KEY = "test-key-req-mechanic-tom"
_OWNER_KEY = "test-key-appr-owner"
_HEADERS = {"Authorization": f"Bearer {_MECHANIC_KEY}"}
_OWNER_HEADERS = {"Authorization": f"Bearer {_OWNER_KEY}"}

#: The six FK children, named here rather than imported from the sweep — see the
#: module docstring. A table dropped from the sweep's list must still be checked
#: by this test, or the two artifacts would agree with each other into a gap.
_CHILD_TABLES = (
    "repair_case_order_number",
    "repair_case_closeout",
    "repair_case_task_event",
    "repair_case_quote",
    "repair_case_justification",
    "repair_case_accepted_quote",
)

#: SD-4 ruled (a): RETAINED. Named separately from the children above because the
#: assertion on it points the OTHER way.
_RUN_LINK_TABLE = "repair_case_run_link"


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    """Process-global caches; a leak makes a later test lie."""
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exactly what the API lifespan registers, with authn ON.

    Authn is load-bearing: the run endpoint persists ``step_principals`` from the
    server-resolved principal, so an unauthenticated fire produces a run whose
    gate can never be resolved — and no gate resolution means no run-link rows,
    which is half of what this scenario exists to inspect.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(
        settings,
        "api_keys",
        {_digest(_MECHANIC_KEY): _MECHANIC, _digest(_OWNER_KEY): _OWNER},
    )


@pytest.fixture
def retention_bindings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    api_db_maker: async_sessionmaker[AsyncSession],
) -> Path:
    """Point the sweep at the test database and a temp upload directory.

    These are the only two redirections in this module, and neither touches the
    seam under test. ``photo_root()`` is deliberately NOT stubbed — the routes and
    the sweep both call it, so redirecting the SETTING keeps them agreeing by
    construction, which is the property ``_photo_root``'s docstring claims.
    """
    photos = tmp_path / "photos"
    monkeypatch.setattr(settings, "repair_case_photo_dir", str(photos))
    monkeypatch.setattr(case_retention_task, "async_session", api_db_maker)
    return photos


async def _open_a_full_case(client: AsyncClient, *, description: str) -> str:
    """One case with everything a real one accumulates, through the real routes."""
    opened = await client.post(
        "/api/cases",
        json={"truck_id": "truck-01", "work_type": "breakdown", "description": description},
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]

    photo = await client.post(
        f"/api/cases/{case_id}/photos",
        files={"file": ("เพลาหัก.jpg", b"\xff\xd8\xff-not-really-a-jpeg", "image/jpeg")},
        data={"caption": "เพลาหน้าขวา"},
        headers=_HEADERS,
    )
    assert photo.status_code == 200, photo.text

    chosen = ""
    for vendor, amount in (
        ("ส.เจริญยนต์", "58000.00"),
        ("อู่ริมทางปากช่อง", "62000.00"),
        ("อู่ช่างเล็ก", "59500.00"),
    ):
        quoted = await client.post(
            f"/api/cases/{case_id}/quotes",
            data={"vendor": vendor, "amount_thb": amount},
            files={"file": ("ใบเสนอราคา.pdf", b"%PDF-1.4 not really", "application/pdf")},
            headers=_HEADERS,
        )
        assert quoted.status_code == 201, quoted.text
        if vendor == "อู่ริมทางปากช่อง":
            chosen = quoted.json()["quote_id"]

    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": chosen, "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้"},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text

    justified = await client.post(
        f"/api/cases/{case_id}/justifications",
        json={"vendor": "อู่ริมทางปากช่อง", "reason": "เจ้าเดียวที่มีเพลารุ่นนี้ในสต็อก"},
        headers=_HEADERS,
    )
    assert justified.status_code == 201, justified.text

    flipped = await client.post(
        f"/api/cases/{case_id}/tasks",
        json={"item_key": "arrange_tow", "status": "done"},
        headers=_HEADERS,
    )
    assert flipped.status_code == 201, flipped.text
    return case_id


async def _drive_to_a_resolved_gate(
    client: AsyncClient, session: AsyncSession, case_id: str
) -> str:
    """Fire the hero and resolve its gate, so real run-link rows exist."""
    from services.engine.procedures.persistence import load_run

    fired = await client.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    run_id: str = fired.json()["run_id"]

    loaded = await load_run(session, run_id)
    target = next(sr for sr in loaded.step_results if sr.step_id == _GATE_STEP)
    assert target.artifact is not None
    proposals = list(target.artifact["output_set"])
    assert case_id in {case_id_of(p) for p in proposals}, (
        "the parked gate must be about the real case, or the run-link rows this "
        "scenario inspects would belong to something else"
    )

    decisions = {
        str(p["action_id"]): ("approve" if case_id_of(p) == case_id else "reject")
        for p in proposals
    }
    resolved = await client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATE_STEP, "decisions": decisions},
        headers=_OWNER_HEADERS,
    )
    assert resolved.status_code == 200, resolved.text
    return run_id


async def _rows_for(session: AsyncSession, table: str, case_id: str) -> int:
    result = await session.execute(
        sa.text(f"SELECT count(*) FROM {table} WHERE case_id = :cid"),  # noqa: S608
        {"cid": case_id},
    )
    return int(result.scalar_one())


async def _counts(session: AsyncSession, case_id: str) -> dict[str, int]:
    return {t: await _rows_for(session, t, case_id) for t in (*_CHILD_TABLES, _RUN_LINK_TABLE)}


async def test_a_case_and_everything_hanging_off_it_is_gone_ninety_days_later(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_active: None,
    retention_bindings: Path,
) -> None:
    """The whole regime, end to end, with the aftermath inspected rather than assumed."""
    photo_root = retention_bindings

    expired_id = await _open_a_full_case(
        client_with_db, description="เพลาขาดกลางทางแถวปากช่อง มีเสียงดังใต้ท้องรถมาหลายวัน"
    )
    await _drive_to_a_resolved_gate(client_with_db, db_session, expired_id)

    # --- the control: a fresh case that must survive untouched -----------------
    control_id = await _open_a_full_case(client_with_db, description="ไฟหน้าขวาไม่ติด เพิ่งแจ้งเมื่อเช้านี้")

    # --- preconditions, so every "gone" below is a real change -----------------
    before = await _counts(db_session, expired_id)
    populated = {t for t, n in before.items() if n}
    assert len(populated & set(_CHILD_TABLES)) >= 3, (
        "fewer than three FK-child tables carry rows for this case, so most of the "
        f"per-table assertions below would pass vacuously. Populated: {sorted(populated)}. "
        f"Empty (recorded, not silently accepted): "
        f"{sorted(set(_CHILD_TABLES) - populated)}"
    )
    assert before[_RUN_LINK_TABLE] > 0, (
        "no run-link rows: SD-4's retention assertion would then be satisfied by an "
        "absence rather than by a deliberate keep"
    )
    expired_dir = photo_root / expired_id
    control_dir = photo_root / control_id
    assert expired_dir.is_dir() and any(expired_dir.iterdir()), "the uploads must be on disk"
    assert control_dir.is_dir() and any(control_dir.iterdir())

    await case_projection.refresh(db_session)
    assert expired_id in {f.case_id for f in case_projection.facts()}, (
        "the projection must be serving the case BEFORE the sweep, or 'no longer "
        "served' afterwards would be true for the wrong reason"
    )

    # --- age the DATA's timeline, not the clock the sweep reads ----------------
    await db_session.execute(
        sa.update(RepairCase)
        .where(RepairCase.case_id == expired_id)
        .values(opened_at=datetime.now(UTC) - timedelta(days=CASE_RETENTION_DAYS + 1))
    )
    await db_session.commit()

    # --- the sweep, through the task's own callable ----------------------------
    report = await case_retention_task._sweep_once()
    assert report.expired_found == 1, f"only the aged case is expired: {report}"
    assert report.deleted == 1
    assert report.failed_case_ids == ()

    # --- aftermath: the row -----------------------------------------------------
    remaining = set(
        (await db_session.execute(sa.select(RepairCase.case_id))).scalars(),
    )
    assert expired_id not in remaining
    assert control_id in remaining, "the control case must survive — see the module docstring"

    # --- aftermath: each child table, BY NAME ----------------------------------
    after = await _counts(db_session, expired_id)
    for table in _CHILD_TABLES:
        assert after[table] == 0, (
            f"{table} still holds {after[table]} row(s) for the deleted case "
            f"(it held {before[table]} before the sweep)"
        )

    # --- aftermath: the seventh table, asserted as PRESENCE (SD-4 ruled (a)) ----
    assert after[_RUN_LINK_TABLE] == before[_RUN_LINK_TABLE], (
        "run-link rows are RETAINED by ruling — they carry no visitor free text and "
        "are governance-decision history. Asserted as presence, never as the absence "
        "of a delete: that table has no FK, so a sweep that simply FORGOT it would "
        "look identical to one that deliberately kept it"
    )

    # --- aftermath: the disk ----------------------------------------------------
    assert not expired_dir.exists(), "the case's upload directory must be gone"
    assert control_dir.is_dir() and any(control_dir.iterdir()), (
        "the control's files must be untouched — a sweep that cleared the whole photo "
        "root would satisfy every assertion above"
    )

    # --- aftermath: the in-memory projection ------------------------------------
    served = {f.case_id for f in case_projection.facts()}
    assert expired_id not in served, (
        "the projection serves from RAM, so a deleted case keeps being served until "
        "the sweep refreshes it — a retention leak no DB assertion would catch"
    )


async def test_a_case_one_day_short_of_the_cutoff_keeps_everything(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_active: None,
    retention_bindings: Path,
) -> None:
    """The boundary, driven through the real routes rather than a bare row insert.

    Step 1's unit test already pins 89-vs-91 on hand-built rows. This one pins it
    on a case that went through the whole intake — because the thing that would
    break the boundary in production is a change to what ``opened_at`` MEANS on a
    real case, not arithmetic on a literal.
    """
    photo_root = retention_bindings
    case_id = await _open_a_full_case(client_with_db, description="เบรกมีเสียงตอนลงเขา")

    await db_session.execute(
        sa.update(RepairCase)
        .where(RepairCase.case_id == case_id)
        .values(opened_at=datetime.now(UTC) - timedelta(days=CASE_RETENTION_DAYS - 1))
    )
    await db_session.commit()

    report = await case_retention_task._sweep_once()
    assert report.expired_found == 0, f"a case one day short of the cutoff is not expired: {report}"
    assert report.deleted == 0

    survivors = set((await db_session.execute(sa.select(RepairCase.case_id))).scalars())
    assert case_id in survivors
    counts = await _counts(db_session, case_id)
    assert sum(counts.values()) > 0, "its children are still there"
    assert (photo_root / case_id).is_dir(), "and so are its files"


def test_this_module_is_db_backed_and_a_skip_is_never_satisfaction() -> None:
    """A standing reminder in executable form.

    The two scenarios above skip when Postgres is unreachable. AC-10 closes only on
    a run where they EXECUTED, and this test — which needs no database — is the
    line that stays green either way, so a session that skipped everything else
    still reports a green module. Read the counts, not the colour.
    """
    assert _CHILD_TABLES, "the per-table list must not be empty"
    assert _RUN_LINK_TABLE not in _CHILD_TABLES, (
        "the retained table must never join the deleted list — that single edit would "
        "invert SD-4 while every assertion in this module still passed"
    )
