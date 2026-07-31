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

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.routers import cases as cases_router
from services.db.case_events import governed_case_facts
from services.db.repair_case_closeout import RepairCaseCloseout
from services.db.repair_case_evidence import (
    LOWEST_AT_ACCEPTANCE_RECONSTRUCTED,
    LOWEST_AT_ACCEPTANCE_RECORDED,
    RepairCaseAcceptedQuote,
)
from services.db.repair_spend_export import load_monthly_export
from tests.clock_support import Clock, utc


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


# --------------------------------------------------------------------------- #
# PLAN-0099 Step 1 — forcing tests: the clock is DRIVEN, not observed.
#
# The test directly above is the un-forced version of the same property, and it
# passes ~99.1% of the time by luck: the defect needs a backward clock step to land
# inside a 90-166 ms window, which this box produces about 0.9% of the time. That
# is what made it an intermittent CI failure instead of a caught bug.
#
# Every test below stamps the writes itself, through the REAL HTTP path, so the
# inversion happens on demand. Each is expected RED against pre-fix code for a
# stated reason, and that RED is the acceptance evidence — see PLAN-0099 Step 1.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("step_back_ms", "shape"),
    [(5.0, "a -5 ms backward step"), (0.0, "an exact tie")],
)
async def test_the_acceptance_figure_survives_a_lying_clock(
    client_with_db: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    step_back_ms: float,
    shape: str,
) -> None:
    """AC-1. POST and GET must not disagree about the same case.

    เมย์ accepts the only quote she has. A cheaper one is entered afterwards — but
    the wall clock has stepped backwards in between, so the later quote carries an
    EARLIER stamp than the acceptance. The derivation admits it, and the case's
    governed figure silently changes after the fact: the POST said ฿45,500.50 and a
    later GET says ฿39,000.00 for the same acceptance, with
    ``accepted_the_cheapest`` flipping to False so a correct decision reads as a
    control failure.

    RED today at the final assertion (an amount mismatch, not an error).
    """
    clock = Clock(utc(hour=9))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    case_id = await _open_case(client_with_db)
    only = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")

    clock.set(utc(hour=10))
    accepted = await _accept(client_with_db, case_id, only)
    assert accepted.status_code == 201, accepted.text
    at_write = Decimal(str(accepted.json()["lowest_amount_at_acceptance_thb"]))
    assert at_write == Decimal("45500.50"), "the write-time answer is the reference"

    clock.back(milliseconds=step_back_ms)
    await _add_quote(client_with_db, case_id, "อู่ช่างเล็ก", "39000.00")

    assert clock.calls > 0, (
        "the patched clock was never consulted — the monkeypatch landed on the wrong "
        "module, so every assertion below would be measuring unpatched behaviour"
    )

    later = (await client_with_db.get(f"/api/cases/{case_id}/accepted-quote")).json()
    at_read = Decimal(str(later["lowest_amount_at_acceptance_thb"]))
    assert at_read == at_write, (
        f"POST and GET disagree about the same acceptance under {shape}: the write "
        f"recorded {at_write} and the read derives {at_read}. The figure the DOA "
        "ladder routes on cannot depend on when it is asked."
    )

    pack = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()
    assert Decimal(str(pack["lowest_amount_at_acceptance_thb"])) == at_write
    assert (
        pack["accepted_the_cheapest"] is True
    ), "a quote entered AFTER the acceptance made the acceptance look unjustified"


async def test_the_accepted_quote_is_never_excluded_from_its_own_comparison(
    client_with_db: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-2. The boundary case the 63 existing tests leave unpinned.

    A single quote, accepted at the same instant it was entered. The accepted quote
    must be inside the set it is compared against, so the answer is "yes, the
    cheapest" — never ``None`` on a case that demonstrably HAS an acceptance.

    **This test is GREEN against pre-fix code, and that is stated rather than
    hidden.** It is a semantics pin, not a reproduction: its oracle is the rejected
    ``<`` variant (PLAN-0099 Out of Scope), under which both fields read ``None``
    and this test goes RED. Recording it now is what stops that "fix" from being
    made later by someone reading `<=` as an off-by-one.
    """
    clock = Clock(utc(hour=9))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    case_id = await _open_case(client_with_db)
    only = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    accepted = await _accept(client_with_db, case_id, only)
    assert accepted.status_code == 201, accepted.text
    assert clock.calls > 0, "the patched clock was never consulted"

    pack = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()
    assert pack["lowest_amount_at_acceptance_thb"] is not None, (
        "a case WITH an acceptance reported no comparison figure — the accepted quote "
        "was excluded from its own comparison set"
    )
    assert Decimal(str(pack["lowest_amount_at_acceptance_thb"])) == Decimal("45500.50")
    assert pack["accepted_the_cheapest"] is True


async def test_an_acceptance_is_never_reported_as_uncomparable(
    client_with_db: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-2, under the failure mode actually observed rather than under a tie.

    **This fixture was not invented — it was caught.** Running the Step 1 tests for
    the first time (s197), the byte-untouched existing test
    ``test_the_pack_distinguishes_nothing_accepted_from_accepted_the_cheapest``
    failed with ``assert None is True``, then passed 5/5 when re-run in isolation.
    The mechanism is this PLAN's own defect firing naturally on a test the PLAN does
    not name: a backward clock step between the quote writes and the acceptance
    leaves ``accepted_at`` EARLIER than every quote's ``entered_at``, the filtered
    derivation matches nothing, and a case that demonstrably HAS an acceptance
    reports that its comparison figure is unknown.

    That is a strictly worse shape than the reported flake. There, the case gets the
    WRONG figure; here it gets NO figure, and ``accepted_the_cheapest`` collapses to
    ``None`` — the same value that means "nothing has been accepted yet". The month-
    end KPI counts exactly that difference.

    Forced here with a 400 ms step, the smallest backward jump measured on this box.
    RED today at the first assertion.
    """
    clock = Clock(utc(hour=10))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    case_id = await _open_case(client_with_db)
    cheap = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    clock.back(milliseconds=400)
    accepted = await _accept(client_with_db, case_id, cheap)
    assert accepted.status_code == 201, accepted.text
    assert clock.calls > 0, "the patched clock was never consulted"

    pack = (await client_with_db.get(f"/api/cases/{case_id}/evidence")).json()
    assert pack["accepted_quote_id"] == cheap, "the acceptance itself must still be readable"
    assert pack["lowest_amount_at_acceptance_thb"] is not None, (
        "a case WITH an acceptance reported no comparison figure at all. Every quote "
        "was excluded from the comparison because the acceptance carries an earlier "
        "stamp than all of them — which is a clock artefact, not a fact about the case."
    )
    assert pack["accepted_the_cheapest"] is True, (
        "accepted_the_cheapest collapsed to the value that means 'nothing accepted "
        "yet' on a case that has an acceptance — the exact conflation the field is "
        "three-valued to prevent"
    )


async def test_the_gate_reads_the_current_decision_not_the_superseded_one(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3. The DOA gate's input under a backward clock step.

    The garage is changed after the first acceptance — an ordinary governed outcome,
    and the table is append-only precisely so both rows survive. If the clock steps
    backwards in between, the newest row carries the older stamp, and the reader
    keyed on that stamp hands the gate the SUPERSEDED acceptance: the wrong amount,
    the wrong vendor, and ``reason=None`` where a reason was actually given.

    That is worse than a display bug. It is the number an authority threshold routes
    on, so a repair the owner must sign can be presented as one the fleet manager
    may sign.

    RED today: the assertions read the first acceptance's values.
    """
    clock = Clock(utc(hour=9))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    case_id = await _open_case(client_with_db)
    cheap = await _add_quote(client_with_db, case_id, "ส.เจริญยนต์", "45500.50")
    dear = await _add_quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "51000.00")

    clock.set(utc(hour=10))
    first = await _accept(client_with_db, case_id, cheap)
    assert first.status_code == 201, first.text

    clock.back(milliseconds=5)
    second = await _accept(client_with_db, case_id, dear, reason="เจ้าแรกปฏิเสธงาน")
    assert second.status_code == 201, second.text
    assert clock.calls > 0, "the patched clock was never consulted"

    facts = await governed_case_facts(db_session)
    ours = next((f for f in facts if f.case_id == case_id), None)
    assert ours is not None, "the open case with an acceptance is missing from the gate input"

    assert ours.accepted_amount_thb == Decimal("51000.00"), (
        f"the gate was handed {ours.accepted_amount_thb} — the SUPERSEDED acceptance. "
        "The operator's current decision is ฿51,000.00 at อู่ริมทางปากช่อง."
    )
    assert ours.accepted_vendor == "อู่ริมทางปากช่อง"
    assert ours.accepted_reason == "เจ้าแรกปฏิเสธงาน", (
        "the reason went missing with the row: the superseded acceptance was the "
        "cheapest, so it carries no reason, and the gate reads a dearer repair as "
        "though nobody had to justify it"
    )


# --------------------------------------------------------------------------- #
# PLAN-0099 AC-10 — a reconstructed figure is distinguishable from a recorded one
# --------------------------------------------------------------------------- #


async def test_a_reconstructed_figure_is_distinguishable_from_a_recorded_one(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-10: the provenance marker travels to every surface that reads the figure.

    Cray's SD-2 ruling turns on this being true END TO END, not merely stored: NULL
    would say "not captured", and a plain backfilled number would speak with false
    authority — so a reconstructed value must arrive at the reader still labelled as
    a reconstruction. It is a good guess derived from the same wall-clock comparison
    PLAN-0099 retires, which means it carries that derivation's ~0.9 % chance of
    naming the wrong quote. Marking it does not remove that risk. It DISCLOSES it, at
    the point of reading.

    **What this test proves and what it does not.** Migration ``0023`` actually
    writing ``reconstructed`` onto legacy rows is proven separately, against real
    alembic, by ``test_0023_backfills_the_legacy_reading_and_marks_it_reconstructed``.
    Here the legacy row is seeded in the shape that migration leaves, and what is
    under test is the half Step 3 built: that the marker survives from the row to
    POST, to GET, to the evidence pack and to the month-end export row. The two
    together are the end-to-end claim; neither is it alone.

    *Counterexample this is RED against:* give the basis a default of ``recorded`` at
    any layer — ORM, ``server_default``, or a response model default — and the legacy
    case reads ``recorded``, which is the marked-number-that-lies failure the ruling
    exists to prevent.
    """
    clock = Clock(utc(day=15, hour=3))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    # --- the RECORDED case: written the way the POST handler writes one -------
    recorded_case = await _open_case(client_with_db, truck_id="truck-01")
    cheap = await _add_quote(client_with_db, recorded_case, "ส.เจริญยนต์", "45500.50")
    await _add_quote(client_with_db, recorded_case, "อู่ริมทางปากช่อง", "51000.00")
    posted = await _accept(client_with_db, recorded_case, cheap)
    assert posted.status_code == 201, posted.text

    # --- the RECONSTRUCTED case: the shape 0023 leaves on a legacy row --------
    legacy_case = await _open_case(client_with_db, truck_id="truck-02")
    legacy_quote = await _add_quote(client_with_db, legacy_case, "อู่ช่างเล็ก", "62000.00")
    db_session.add(
        RepairCaseAcceptedQuote(
            accepted_id="accepted-legacy",
            case_id=legacy_case,
            quote_id=legacy_quote,
            reason=None,
            accepted_by="admin-may",
            accepted_at=clock.now_value,
            lowest_amount_at_acceptance_thb=Decimal("62000.00"),
            lowest_at_acceptance_basis=LOWEST_AT_ACCEPTANCE_RECONSTRUCTED,
        )
    )
    # Both cases carry money so both reach the export (``is_reportable``). Inserted
    # rather than posted: the point here is the acceptance's provenance, and driving
    # the close-out endpoint would add a second write path to reason about.
    for n, (case_id, vendor) in enumerate(((recorded_case, "ส.เจริญยนต์"), (legacy_case, "อู่ช่างเล็ก"))):
        db_session.add(
            RepairCaseCloseout(
                closeout_id=f"closeout-{n}",
                case_id=case_id,
                vendor=vendor,
                tax_invoice_no=f"INV-{n}",
                tax_invoice_date=None,
                amount_pre_vat_thb=Decimal("1000.00"),
                vat_thb=Decimal("70.00"),
                total_thb=Decimal("1070.00"),
                entered_by="admin-may",
                entered_at=clock.now_value,
            )
        )
    await db_session.commit()

    got_recorded = await client_with_db.get(f"/api/cases/{recorded_case}/accepted-quote")
    got_legacy = await client_with_db.get(f"/api/cases/{legacy_case}/accepted-quote")
    pack_recorded = await client_with_db.get(f"/api/cases/{recorded_case}/evidence")
    pack_legacy = await client_with_db.get(f"/api/cases/{legacy_case}/evidence")
    assert got_recorded.status_code == 200, got_recorded.text
    assert got_legacy.status_code == 200, got_legacy.text
    assert clock.calls > 0, "the patched clock was never consulted"

    export = await load_monthly_export(db_session, year=2026, month=7, now=utc(day=31))
    rows = {row.case_id: row for row in export.rows}

    # POST and GET agree — they read one stored fact rather than each deriving one.
    assert posted.json()["lowest_at_acceptance_basis"] == LOWEST_AT_ACCEPTANCE_RECORDED
    assert posted.json()["lowest_amount_at_acceptance_thb"] == "45500.50"
    assert posted.json()["accepted_the_cheapest"] is True
    assert got_recorded.json() == posted.json(), (
        "POST and GET disagree about the same acceptance — the defect PLAN-0099 "
        "reproduced deterministically, where the write recorded 45500.50 and the "
        "read re-derived 39000.00 from a clock that had stepped backwards"
    )

    # The legacy row is legible AS a reconstruction, everywhere it is read.
    assert got_legacy.json()["lowest_at_acceptance_basis"] == LOWEST_AT_ACCEPTANCE_RECONSTRUCTED
    assert pack_legacy.json()["lowest_at_acceptance_basis"] == LOWEST_AT_ACCEPTANCE_RECONSTRUCTED
    assert pack_recorded.json()["lowest_at_acceptance_basis"] == LOWEST_AT_ACCEPTANCE_RECORDED

    # ...including in the document accounting actually reads, where the basis sits
    # beside BOTH the figure and the boolean derived from it (ruling req 1 + req 3).
    assert rows[recorded_case].lowest_at_acceptance_basis == LOWEST_AT_ACCEPTANCE_RECORDED
    assert rows[recorded_case].lowest_amount_at_acceptance_thb == Decimal("45500.50")
    assert rows[recorded_case].accepted_the_cheapest is True
    assert rows[legacy_case].lowest_at_acceptance_basis == LOWEST_AT_ACCEPTANCE_RECONSTRUCTED
    assert rows[legacy_case].lowest_amount_at_acceptance_thb == Decimal("62000.00")
    assert rows[legacy_case].accepted_the_cheapest is True
