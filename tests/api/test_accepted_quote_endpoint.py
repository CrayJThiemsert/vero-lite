"""PLAN-0096 Step 8 — ใบที่ตกลง, the accepted quote.

This primitive exists because its absence caused two separate defects, and the
tests are written against those defects rather than against the happy path:

* **The gate had no number to route on.** ``repair_case_closeout.total_thb`` is
  written after the work the DOA ladder was meant to authorise, and the evidence
  pack's ``lowest_amount_thb`` is the CHEAPEST quote, which is not what was agreed
  whenever an approved higher quote won on lead time or parts availability. The
  accepted quote is the first row that carries the governed figure at the moment it
  becomes true.
* **Nothing recorded which garage was used** — the gap migration ``0018`` patched
  by adding ``repair_case_closeout.vendor``. A quote carries the amount and the
  vendor together, so one acceptance answers both questions.

Two typed decisions (Cray, s191) are what the assertions pin:

* **The FK is required.** An acceptance must name a quote already recorded against
  THIS case, so the figure an authority threshold routes on always traces to
  evidence somebody entered. ``test_a_quote_from_another_case_cannot_be_accepted``
  is the adversarial half — the composite foreign key makes it a schema property,
  not a habit.
* **A reason is required only when the cheapest was not accepted.** The audit
  question is "why did you not take the cheapest one", so it is demanded exactly
  when that question arises. ``test_accepting_a_dearer_quote_without_a_reason_is_refused``
  is the load-bearing test in this file.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from decimal import Decimal

from httpx import AsyncClient


async def _open_case(client: AsyncClient, truck_id: str = "truck-01") -> str:
    response = await client.post("/api/cases", json={"truck_id": truck_id})
    assert response.status_code == 201, response.text
    case_id: str = response.json()["case_id"]
    return case_id


async def _add_quote(client: AsyncClient, case_id: str, vendor: str, amount: str) -> str:
    response = await client.post(
        f"/api/cases/{case_id}/quotes",
        data={"vendor": vendor, "amount_thb": amount},
    )
    assert response.status_code == 201, response.text
    quote_id: str = response.json()["quote_id"]
    return quote_id


async def _accept(client: AsyncClient, case_id: str, quote_id: str, **body: object):
    return await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": quote_id, **body},
    )


# --------------------------------------------------------------------------- #
# The reason rule — required exactly when the cheapest was not accepted
# --------------------------------------------------------------------------- #


async def test_accepting_the_cheapest_quote_needs_no_reason(client_with_db: AsyncClient) -> None:
    """The common case must not nag.

    Demanding a reason for every acceptance would train เมย์ to type "ถูกสุด" into
    the box, which is the shape of a control that produces compliance text instead
    of information."""
    case_id = await _open_case(client_with_db)
    cheap = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    await _add_quote(client_with_db, case_id, "อู่ช่างเล็ก", "48000.00")

    response = await _accept(client_with_db, case_id, cheap)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["reason"] is None
    assert body["quote"]["vendor"] == "ส.เจริญยนต์"
    assert Decimal(str(body["quote"]["amount_thb"])) == Decimal("45500.50")
    assert Decimal(str(body["lowest_amount_at_acceptance_thb"])) == Decimal("45500.50")


async def test_accepting_a_dearer_quote_without_a_reason_is_refused(
    client_with_db: AsyncClient,
) -> None:
    """THE test in this file.

    Refusing at write time rather than flagging at month end is the point: right now
    เมย์ knows why the dearer garage was used, and in four weeks reconstructing it is
    an archaeology dig through LINE — the failure mode this whole flow replaces. The
    error names both figures so the person reading it can see what is being asked."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    dear = await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    response = await _accept(client_with_db, case_id, dear)

    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert "51000.00" in detail and "45500.50" in detail


async def test_a_dearer_quote_is_accepted_when_the_reason_is_given(
    client_with_db: AsyncClient,
) -> None:
    """An approved higher quote is a NORMAL governed outcome, not an exception.

    Lead time and parts availability legitimately beat price; the control exists to
    capture the reasoning, never to force the cheapest choice."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    dear = await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    response = await _accept(
        client_with_db, case_id, dear, reason="เจ้าเดียวที่มีอะไหล่พร้อม รออีก 5 วันไม่ได้"
    )

    assert response.status_code == 201, response.text
    assert "อะไหล่พร้อม" in response.json()["reason"]


async def test_a_whitespace_only_reason_does_not_satisfy_the_rule(
    client_with_db: AsyncClient,
) -> None:
    """A blank that LOOKS filled is worse than a blank.

    Without this, the cheapest-quote question is answerable by pressing space."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    dear = await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    response = await _accept(client_with_db, case_id, dear, reason="   ")

    assert response.status_code == 422, response.text


async def test_a_tied_lowest_quote_needs_no_reason(client_with_db: AsyncClient) -> None:
    """Two garages quoting the same figure: neither is 'not the cheapest'.

    The rule is a comparison against the lowest amount, not against a single
    privileged row, so a tie must not demand an explanation nobody can give."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    twin = await _add_quote(client_with_db, case_id, "อู่ช่างเล็ก", "45500.50")

    response = await _accept(client_with_db, case_id, twin)

    assert response.status_code == 201, response.text


# --------------------------------------------------------------------------- #
# The required FK — the accepted figure must trace to recorded evidence
# --------------------------------------------------------------------------- #


async def test_an_unknown_quote_cannot_be_accepted(client_with_db: AsyncClient) -> None:
    """A free-typed amount would reopen exactly the hole this table closes."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")

    response = await _accept(client_with_db, case_id, "quote-does-not-exist")

    assert response.status_code == 422, response.text
    assert "quote-does-not-exist" in response.json()["detail"]


async def test_a_quote_from_another_case_cannot_be_accepted(client_with_db: AsyncClient) -> None:
    """The adversarial half of the required FK.

    A real quote id, a real case — and the wrong pairing. This is refused at the API
    for the readable message, and the composite foreign key on
    ``(case_id, quote_id)`` refuses it again underneath, so the invariant survives
    any future write path that forgets to check."""
    case_a = await _open_case(client_with_db)
    case_b = await _open_case(client_with_db, truck_id="truck-02")
    await _add_quote(client_with_db, case_a, "ส.เจริญยนต์", "45500.50")
    foreign = await _add_quote(client_with_db, case_b, "อู่ช่างเล็ก", "12000.00")

    response = await _accept(client_with_db, case_a, foreign)

    assert response.status_code == 422, response.text
    assert case_a in response.json()["detail"]


# --------------------------------------------------------------------------- #
# Append-only — a change of mind is a new row, never an edit
# --------------------------------------------------------------------------- #


async def test_changing_the_agreed_garage_supersedes_without_erasing(
    client_with_db: AsyncClient,
) -> None:
    """The latest acceptance is the current position; the earlier one stays readable.

    A flag on the quote row would have made this an UPDATE, and the trail is framed
    to the partner as evidence protecting his people — one that can be quietly
    rewritten protects nobody."""
    case_id = await _open_case(client_with_db)
    first = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    second = await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    initial = await _accept(client_with_db, case_id, first)
    assert initial.status_code == 201, initial.text
    switched = await _accept(client_with_db, case_id, second, reason="เจ้าแรกปฏิเสธงาน")
    assert switched.status_code == 201, switched.text

    current = await client_with_db.get(f"/api/cases/{case_id}/accepted-quote")
    assert current.status_code == 200, current.text
    assert current.json()["quote"]["quote_id"] == second
    # Two distinct rows, not one row edited twice.
    assert initial.json()["accepted_id"] != switched.json()["accepted_id"]


async def test_reading_before_anything_is_accepted_is_a_404(client_with_db: AsyncClient) -> None:
    """'Nothing agreed yet' is a normal state of a real case, reported as absence."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")

    response = await client_with_db.get(f"/api/cases/{case_id}/accepted-quote")

    assert response.status_code == 404, response.text


# --------------------------------------------------------------------------- #
# The evidence pack — what the gate and the export will read
# --------------------------------------------------------------------------- #


async def test_the_pack_reports_the_accepted_figure_not_the_cheapest(
    client_with_db: AsyncClient,
) -> None:
    """``accepted_amount_thb`` is the governed number; ``lowest_amount_thb`` is not.

    The two disagreeing is the entire reason this field exists — a gate reading the
    cheapest quote would route a ฿51,000 repair on a ฿45,500 figure."""
    case_id = await _open_case(client_with_db)
    await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    dear = await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")
    await _accept(client_with_db, case_id, dear, reason="เจ้าเดียวที่มีอะไหล่")

    pack = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()

    assert Decimal(str(pack["lowest_amount_thb"])) == Decimal("45500.50")
    assert Decimal(str(pack["accepted_amount_thb"])) == Decimal("51000.00")
    assert pack["accepted_vendor"] == "อู่ริมทางปากช่อง"
    assert pack["accepted_the_cheapest"] is False


async def test_the_pack_distinguishes_nothing_accepted_from_accepted_the_cheapest(
    client_with_db: AsyncClient,
) -> None:
    """``accepted_the_cheapest`` is three-valued on purpose.

    A bool would collapse "nobody has agreed anything" into the reassuring answer,
    and the KPI counts exactly that difference."""
    case_id = await _open_case(client_with_db)
    cheap = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    before = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()
    assert before["accepted_the_cheapest"] is None
    assert before["accepted_quote_id"] is None

    await _accept(client_with_db, case_id, cheap)

    after = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()
    assert after["accepted_the_cheapest"] is True
    assert after["accepted_quote_id"] == cheap


async def test_a_cheaper_quote_arriving_later_does_not_rewrite_history(
    client_with_db: AsyncClient,
) -> None:
    """A correct decision must not look unjustified in hindsight.

    เมย์ accepts the only quote she has; a cheaper one arrives the next morning.
    Judged against today's numbers the acceptance is 'not the cheapest' and carries
    no reason — which would read as a control failure. ``lowest_amount_at_acceptance``
    is what keeps the record honest, and it is DERIVED from the append-only
    ``entered_at`` rather than stored, so it cannot itself go stale."""
    case_id = await _open_case(client_with_db)
    only = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    accepted = await _accept(client_with_db, case_id, only)
    assert accepted.status_code == 201, accepted.text

    await _add_quote(client_with_db, case_id, "อู่ช่างเล็ก", "39000.00")

    pack = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()
    assert Decimal(str(pack["lowest_amount_thb"])) == Decimal("39000.00")
    assert Decimal(str(pack["lowest_amount_at_acceptance_thb"])) == Decimal("45500.50")
    assert pack["accepted_the_cheapest"] is True
