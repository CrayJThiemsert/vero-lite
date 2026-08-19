"""A credit note keyed as a close-out, driven into the month-end ฿ figure.

PLAN-0107 AC-11. The AC asks for ONE signed outcome pinned at the ฿ aggregation
seam — *"correct signed aggregation if the domain admits credits/refunds, or an
explicit loud rejection if it does not"* — picked after reading the seam. Reading
it settles the pick, and not in the direction the phrasing suggests.

🔴 **The domain HAS credit notes; this RECORD cannot hold one.** เมย์ receives
ใบลดหนี้ (Cray, typed 2026-08-19). But ``repair_case_closeout`` is append-only with
LATEST-WINS: :func:`services.db.repair_case_closeout.latest_closeout` returns one
row per case and **both** consumers read it — ``_build_row`` in
``services.db.repair_spend_export`` and ``get_closeout`` in
``services.api.routers.cases``.
⚠️ Cited by SYMBOL rather than by line on purpose: the two line numbers this module
first carried were measured correct against ``main`` and were stale the moment this
very module landed 41 lines above one of them.
A credit-note row therefore does not JOIN the invoice it credits,
it **REPLACES** it. So "admit the negative and let ``sum()`` handle it" is not the
lenient option, it is the silent one: the month-end figure would report the credit
as the repair's entire cost while every row looked perfectly filled in — the failure
a completeness KPI structurally cannot see, and the same trap ``tax_invoice_date``
and ``seq`` carry their own docstrings against.

The refusal is therefore INTERIM and says so at the seam. It leaves month-end
**knowably incomplete** rather than **invisibly wrong**, until a schema exists that
can hold an invoice and its credit as two coexisting facts.

**Nothing is stubbed on either side.** The producer is the real shipped
``POST /api/cases/{id}/closeout`` route with authn on; the consumer is the real
:func:`services.db.repair_spend_export.load_monthly_export` and its real
``total_thb`` aggregation. A test that asserted the 422 alone would prove a guard
exists and say nothing about the figure the guard protects — and the figure is the
entire reason the guard is there.

⚠️ The month filter for a close-out with no governed run is ``entered_at`` (the
keying moment, server clock), **not** ``tax_invoice_date``. A test keyed on the
invoice date would silently select an empty month and pass while asserting nothing.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.repair_case_closeout import latest_closeout
from services.db.repair_spend_export import EXPORT_TIMEZONE, load_monthly_export
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_MECHANIC = "req-mechanic-tom"

_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}

#: The invoice as issued. Realistic Thai fleet paperwork: pre-VAT + 7% VAT = total.
_INVOICE = {
    "vendor": "อู่คู่สัญญา ปากช่อง",
    "tax_invoice_no": "INV-2026-0091",
    "tax_invoice_date": "2026-08-14",
    "amount_pre_vat_thb": "18691.59",
    "vat_thb": "1308.41",
    "total_thb": "20000.00",
}

#: The credit note เมย์ would key if nothing refused it. 🔴 Internally COHERENT —
#: -14,018.69 + -981.31 = -15,000.00 satisfies the totals comparison exactly, which
#: is why the negative check cannot be a side effect of that comparison.
_CREDIT_NOTE = {
    "vendor": "อู่คู่สัญญา ปากช่อง",
    "tax_invoice_no": "CN-2026-0007",
    "tax_invoice_date": "2026-08-20",
    "amount_pre_vat_thb": "-14018.69",
    "vat_thb": "-981.31",
    "total_thb": "-15000.00",
}


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
    """Exactly what the API lifespan registers, with authn ON.

    Authn on is load-bearing: ``entered_by`` falls back to the unattributed marker
    without a resolved principal, and a close-out nobody is attributable for is a
    different record from the one this module is about.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


async def _open_case(client: AsyncClient) -> str:
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "ปั๊มน้ำรั่วระหว่างวิ่งสระบุรี",
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    return str(opened.json()["case_id"])


def _this_month() -> tuple[int, int]:
    """The accounting month the export selects for a close-out keyed NOW.

    Bangkok, not UTC: ``load_monthly_export`` takes its bounds in
    ``EXPORT_TIMEZONE``, so on the last evening of a month UTC and Bangkok name
    different months and a UTC-derived pair would read an empty one.
    """
    now_bkk = datetime.now(UTC).astimezone(ZoneInfo(EXPORT_TIMEZONE))
    return now_bkk.year, now_bkk.month


async def test_a_credit_note_is_refused_at_the_producer(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The refusal exists, is a 422, and names why rather than just failing."""
    case_id = await _open_case(client_with_db)

    refused = await client_with_db.post(
        f"/api/cases/{case_id}/closeout", json=_CREDIT_NOTE, headers=_HEADERS
    )

    assert refused.status_code == 422, refused.text
    detail = refused.json()["detail"]
    # Every negative field is named, so เมย์ is told WHICH number to look at.
    assert "amount_pre_vat_thb" in detail
    assert "vat_thb" in detail
    assert "total_thb" in detail
    # And the reason, not merely the fact. A guard whose message says "invalid"
    # sends the reader to the wrong document.
    assert "ใบลดหนี้" in detail
    assert "REPLACE" in detail


async def test_the_coherent_credit_note_is_refused_by_the_sign_check_not_the_totals(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """🔴 The non-obvious half, and the reason the sign check is its own door.

    ``_CREDIT_NOTE`` satisfies ``total == pre_vat + vat`` exactly. Were the sign
    check removed, the totals comparison would pass it straight through — so a
    green totals guard is no evidence at all about negative money, and a future
    refactor that folded the two checks together would reopen this hole while
    every totals test stayed green.
    """
    pre_vat = Decimal(_CREDIT_NOTE["amount_pre_vat_thb"])
    vat = Decimal(_CREDIT_NOTE["vat_thb"])
    total = Decimal(_CREDIT_NOTE["total_thb"])
    assert pre_vat + vat == total, "the fixture must stay coherent or this pins nothing"

    case_id = await _open_case(client_with_db)
    refused = await client_with_db.post(
        f"/api/cases/{case_id}/closeout", json=_CREDIT_NOTE, headers=_HEADERS
    )

    assert refused.status_code == 422, refused.text
    # The totals message would name "does not equal"; the sign message names the
    # credit note. Asserting the DISCRIMINATOR, not just the status code.
    assert "does not equal" not in refused.json()["detail"]


async def test_the_refused_credit_note_leaves_the_month_end_figure_intact(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The producer→consumer half: what the refusal actually protects.

    The ฿ figure is read from the real month-end aggregation before and after the
    refused attempt. Asserting the 422 alone would leave the interesting claim —
    that nothing downstream moved — entirely unmeasured.
    """
    case_id = await _open_case(client_with_db)

    keyed = await client_with_db.post(
        f"/api/cases/{case_id}/closeout", json=_INVOICE, headers=_HEADERS
    )
    assert keyed.status_code == 201, keyed.text

    year, month = _this_month()
    before = await load_monthly_export(db_session, year=year, month=month, now=datetime.now(UTC))
    invoice_total = Decimal(_INVOICE["total_thb"])
    assert before.total_thb == invoice_total, (
        "the invoice must reach the month-end figure, or the assertions below "
        "compare two empty totals and pass vacuously"
    )

    refused = await client_with_db.post(
        f"/api/cases/{case_id}/closeout", json=_CREDIT_NOTE, headers=_HEADERS
    )

    # ⚠️ The ฿ assertions come BEFORE the status-code one, deliberately. Written the
    # other way round this module passed its probe for the wrong reason: disarming
    # the guard reddened the 422 line and returned, so the month-end assertion — the
    # claim the module exists to make — was never executed and had never been
    # witnessed RED at all. Ordering it first makes the money the assertion that
    # fires, which is what CLAUDE.md §8 asks of a load-bearing green.
    after = await load_monthly_export(db_session, year=year, month=month, now=datetime.now(UTC))
    assert after.total_thb == invoice_total, (
        "the credit note moved the month-end ฿ figure — the replacement failure "
        "this guard exists to prevent"
    )

    # And the case still reports the INVOICE, not the credit. This distinguishes
    # "the write was refused" from "the write landed but the month happened not to
    # select it" — two states the figure above cannot tell apart on its own.
    current = await latest_closeout(db_session, case_id)
    assert current is not None
    assert (
        current.tax_invoice_no == _INVOICE["tax_invoice_no"]
    ), "the credit note replaced the invoice as the case's current close-out"
    assert current.total_thb == invoice_total

    assert refused.status_code == 422, refused.text


async def test_the_guard_does_not_refuse_an_ordinary_zero_vat_invoice(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Positive control: the guard rejects NEGATIVE, not merely non-positive.

    A garage that is VAT-registered and billed an exempt repair keys ``0.00`` VAT,
    which is a real and different fact from the NULL a non-registered garage keys.
    Without this case a guard written as ``<= 0`` would pass every assertion above
    while refusing correct paperwork in production.
    """
    case_id = await _open_case(client_with_db)

    keyed = await client_with_db.post(
        f"/api/cases/{case_id}/closeout",
        json={**_INVOICE, "amount_pre_vat_thb": "20000.00", "vat_thb": "0.00"},
        headers=_HEADERS,
    )

    assert keyed.status_code == 201, keyed.text
    current = await latest_closeout(db_session, case_id)
    assert current is not None
    assert current.vat_thb == Decimal("0.00")
