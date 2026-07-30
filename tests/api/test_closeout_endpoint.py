"""PLAN-0096 Step 8 — the close-out record and its repair-order number (AC-9's source).

What the two typed decisions turn into assertions here:

* **Decision A — a human-readable number.** ``RC-<year>-<NNNN>``, reset per year.
  The tests pin the FORMAT and the two invariants that make it usable as an
  accounting key: a case's number never changes, and the series has no gaps.
* **Decision B — the invoice quartet, none derived.** ``vat_thb`` of ``None`` and
  ``Decimal("0.00")`` are asserted to be different stored facts, because a computed
  7% is exactly what was rejected and a test that let them collapse would make
  re-introducing the derivation invisible.

The gap-free assertion is the one worth reading twice. It is not about tidiness:
a missing number in a document series is something an auditor asks about, and the
allocator earns it by only issuing a number when a case actually closes.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

from services.db.repair_case_closeout import (
    ORDER_NO_WIDTH,
    OrderNumberExhaustedError,
    format_repair_order_no,
)


async def _open_case(client: AsyncClient, truck_id: str = "truck-01") -> str:
    response = await client.post("/api/cases", json={"truck_id": truck_id})
    assert response.status_code == 201, response.text
    case_id: str = response.json()["case_id"]
    return case_id


async def _key_closeout(client: AsyncClient, case_id: str, **body: object) -> dict:
    payload: dict[str, object] = {
        "vendor": "อู่คู่สัญญา ปากช่อง",
        "amount_pre_vat_thb": "1000.00",
        "vat_thb": "70.00",
        "total_thb": "1070.00",
        **body,
    }
    response = await client.post(f"/api/cases/{case_id}/closeout", json=payload)
    assert response.status_code == 201, response.text
    result: dict = response.json()
    return result


# --------------------------------------------------------------------------- #
# Decision A — the repair-order number
# --------------------------------------------------------------------------- #


def test_the_format_is_zero_padded_so_the_series_sorts_as_text() -> None:
    """``RC-2026-0002`` must sort before ``RC-2026-0010`` wherever it is displayed."""
    assert format_repair_order_no(2026, 1) == "RC-2026-0001"
    assert format_repair_order_no(2026, 10) == "RC-2026-0010"
    assert format_repair_order_no(2026, 2) < format_repair_order_no(2026, 10)


def test_running_past_the_width_raises_rather_than_widening() -> None:
    """A wider number would sort wrong against every number already issued that year,
    so the allocator refuses instead of silently changing the format at 03:00."""
    assert format_repair_order_no(2026, 10**ORDER_NO_WIDTH - 1) == "RC-2026-9999"
    with pytest.raises(OrderNumberExhaustedError):
        format_repair_order_no(2026, 10**ORDER_NO_WIDTH)


async def test_a_closeout_allocates_a_readable_number(client_with_db: AsyncClient) -> None:
    """AC-9 column 3: เลขที่ใบแจ้งซ่อม is something a human reads off paper.

    The case's own ``case_id`` is a UUID — this is the whole reason the column and
    Decision A exist."""
    case_id = await _open_case(client_with_db)
    closeout = await _key_closeout(client_with_db, case_id)

    assert closeout["repair_order_no"].startswith("RC-")
    assert closeout["repair_order_no"] != case_id
    assert closeout["repair_order_no"].endswith("0001")


async def test_a_correction_reuses_the_number_it_already_has(
    client_with_db: AsyncClient,
) -> None:
    """The number is written on paper in a folder; a re-keying must not change it.

    This is the invariant that forced the two-table split — had the number lived on
    the append-only keying row, this second row would either take a new number or be
    blocked by the constraint that stops two repairs sharing one."""
    case_id = await _open_case(client_with_db)
    first = await _key_closeout(client_with_db, case_id, tax_invoice_no="INV-1")
    corrected = await _key_closeout(client_with_db, case_id, tax_invoice_no="INV-2")

    assert corrected["repair_order_no"] == first["repair_order_no"]

    current = await client_with_db.get(f"/api/cases/{case_id}/closeout")
    assert current.status_code == 200, current.text
    assert current.json()["tax_invoice_no"] == "INV-2"
    assert current.json()["repair_order_no"] == first["repair_order_no"]


async def test_the_series_has_no_gaps_across_cases(client_with_db: AsyncClient) -> None:
    """Three closed repairs get 0001, 0002, 0003 — nothing skipped.

    A number is only issued when a case actually closes, so a case opened and
    abandoned never consumes one."""
    numbers = []
    for _ in range(3):
        case_id = await _open_case(client_with_db)
        numbers.append((await _key_closeout(client_with_db, case_id))["repair_order_no"])

    suffixes = [int(number.rsplit("-", 1)[1]) for number in numbers]
    assert suffixes == [1, 2, 3]
    assert len(set(numbers)) == 3


async def test_an_abandoned_case_consumes_no_number(client_with_db: AsyncClient) -> None:
    """Opening a case that never closes must not create a hole in the series."""
    await _open_case(client_with_db)  # opened, never closed
    closed = await _open_case(client_with_db)

    assert (await _key_closeout(client_with_db, closed))["repair_order_no"].endswith("0001")


# --------------------------------------------------------------------------- #
# Decision B — the invoice quartet, none derived
# --------------------------------------------------------------------------- #


async def test_a_total_that_does_not_add_up_is_refused(client_with_db: AsyncClient) -> None:
    """Caught while เมย์ still has the invoice in her hand, not at month end."""
    case_id = await _open_case(client_with_db)
    response = await client_with_db.post(
        f"/api/cases/{case_id}/closeout",
        json={
            "vendor": "อู่คู่สัญญา ปากช่อง",
            "amount_pre_vat_thb": "1000.00",
            "vat_thb": "70.00",
            "total_thb": "1000.00",
        },
    )
    assert response.status_code == 422
    assert "does not equal" in response.text


async def test_the_garage_is_required_and_never_inferred(client_with_db: AsyncClient) -> None:
    """AC-9 column 5 has no other source, and guessing it would be worse than asking.

    The quote pack records who QUOTED, not who was used; matching a quote to the
    invoice by amount fails on VAT alone, and fails outright when an approved higher
    quote was the one accepted. So the close-out refuses to be keyed without it."""
    case_id = await _open_case(client_with_db)
    response = await client_with_db.post(
        f"/api/cases/{case_id}/closeout",
        json={
            "amount_pre_vat_thb": "1000.00",
            "vat_thb": "70.00",
            "total_thb": "1070.00",
        },
    )
    assert response.status_code == 422
    assert "vendor" in response.text


async def test_the_garage_survives_to_the_export_side(client_with_db: AsyncClient) -> None:
    """Columns 5 and 6 both key off this value, so it has to round-trip intact —
    including Thai text, which is what the partner's garage names actually are."""
    case_id = await _open_case(client_with_db)
    keyed = await _key_closeout(client_with_db, case_id, vendor="ส.เจริญยนต์")

    assert keyed["vendor"] == "ส.เจริญยนต์"
    current = await client_with_db.get(f"/api/cases/{case_id}/closeout")
    assert current.json()["vendor"] == "ส.เจริญยนต์"


async def test_no_vat_is_stored_as_null_not_zero(client_with_db: AsyncClient) -> None:
    """A vendor who charges no VAT has no VAT line — a different fact from 0.00.

    Collapsing them is precisely what back-computing 7% would have done, and the
    rejection of that derivation is only enforceable if the two survive storage
    distinguishably."""
    non_vat = await _open_case(client_with_db)
    zero_vat = await _open_case(client_with_db)

    keyed_none = await _key_closeout(
        client_with_db, non_vat, vat_thb=None, amount_pre_vat_thb="500.00", total_thb="500.00"
    )
    keyed_zero = await _key_closeout(
        client_with_db, zero_vat, vat_thb="0.00", amount_pre_vat_thb="500.00", total_thb="500.00"
    )

    assert keyed_none["vat_thb"] is None
    assert keyed_zero["vat_thb"] is not None
    assert Decimal(keyed_zero["vat_thb"]) == Decimal("0.00")


async def test_a_missing_invoice_number_is_recorded_not_refused(
    client_with_db: AsyncClient,
) -> None:
    """The export reports an incomplete row — that IS the KPI's subject matter.

    Refusing the close-out until the paper arrives would push เมย์ back to the
    notebook, which is the behaviour these tables replace."""
    case_id = await _open_case(client_with_db)
    assert (await _key_closeout(client_with_db, case_id))["tax_invoice_no"] is None


# --------------------------------------------------------------------------- #
# วันที่เอกสาร — AC-9 column 1 (Cray, typed s192; alembic 0021)
# --------------------------------------------------------------------------- #


async def test_the_invoice_date_is_the_one_on_the_paper_not_the_keying_day(
    client_with_db: AsyncClient,
) -> None:
    """The whole reason this column exists rather than reusing ``entered_at``.

    เมย์ keys a July invoice in August routinely. The month-end export decides an
    accounting month from this value, so if it were the keying timestamp the row
    would file into the wrong month while looking completely filled in — and a KPI
    that counts completeness could never flag it. Nothing is missing; it is just
    wrong. So the stored date must be the one supplied, never derived from
    ``entered_at``, and this asserts the two are genuinely different values."""
    case_id = await _open_case(client_with_db)

    keyed = await _key_closeout(
        client_with_db,
        case_id,
        tax_invoice_no="INV-2026-0731",
        tax_invoice_date="2026-07-28",
    )

    assert keyed["tax_invoice_date"] == "2026-07-28"
    assert (
        keyed["entered_at"][:10] != "2026-07-28"
    ), "the fixture must not key on the invoice date, or this proves nothing"
    fetched = await client_with_db.get(f"/api/cases/{case_id}/closeout")
    assert fetched.json()["tax_invoice_date"] == "2026-07-28", "it must survive the round trip"


async def test_a_missing_invoice_date_is_recorded_not_refused(
    client_with_db: AsyncClient,
) -> None:
    """Incomplete is a real state; the export reports it and the KPI counts it.

    Same rule as the missing invoice NUMBER above — a repair can close before the
    paper arrives, and refusing the close-out until it does sends เมย์ back to the
    notebook these tables replace."""
    case_id = await _open_case(client_with_db)
    keyed = await _key_closeout(client_with_db, case_id, tax_invoice_no="INV-2026-0731")
    assert keyed["tax_invoice_date"] is None


async def test_an_invoice_date_without_an_invoice_number_is_refused(
    client_with_db: AsyncClient,
) -> None:
    """Refuse the INCOHERENT, allow the incomplete — the line the total check draws.

    The date is read off the document that carries the number, so a date with no
    number means something was mis-keyed. Storing it would give the export an
    accounting month to file on behind a document nobody can produce — which is
    worse than a blank, because a blank is visibly incomplete and this is not."""
    case_id = await _open_case(client_with_db)

    response = await client_with_db.post(
        f"/api/cases/{case_id}/closeout",
        json={
            "vendor": "อู่คู่สัญญา ปากช่อง",
            "tax_invoice_date": "2026-07-28",
            "amount_pre_vat_thb": "1000.00",
            "vat_thb": "70.00",
            "total_thb": "1070.00",
        },
    )

    assert response.status_code == 422
    assert "tax_invoice_date" in response.text and "tax_invoice_no" in response.text


# --------------------------------------------------------------------------- #
# The deliberate decoupling
# --------------------------------------------------------------------------- #


async def test_keying_the_paperwork_does_not_flip_the_checklist(
    client_with_db: AsyncClient,
) -> None:
    """AC-7 records actor-plus-timestamp per HUMAN flip.

    A system-generated flip would put the server's word in a slot that exists to
    record a person's, so the two acts stay two calls. A UI may put them behind one
    button; the trail still shows who did what."""
    case_id = await _open_case(client_with_db)
    await _key_closeout(client_with_db, case_id)

    chain = await client_with_db.get(f"/api/cases/{case_id}/tasks")
    assert chain.status_code == 200, chain.text
    done = [item for item in chain.json()["items"] if item["status"] == "done"]
    assert done == []


async def test_a_case_with_no_closeout_reports_404(client_with_db: AsyncClient) -> None:
    """Absence is reported as absence — never as an empty close-out with zero money."""
    case_id = await _open_case(client_with_db)
    response = await client_with_db.get(f"/api/cases/{case_id}/closeout")
    assert response.status_code == 404
