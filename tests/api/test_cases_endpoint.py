"""PLAN-0096 Step 2 / AC-3 — the repair-case capture API.

The half of AC-3 that needs a database. Its companion,
``tests/verticals/fleet_maintenance/test_case_id_bridge.py``, proves the link
survives the governed run and needs no DB at all — so a Postgres outage skips the
storage tests without hiding the assertion that earns the KPI.

What the persona constraints turn into assertions here:

* **เมย์/ต้อม type as little as possible.** ``test_a_case_opens_with_only_a_truck_pick``
  is the structural version of "photo-first, zero required typing" — if a field ever
  becomes mandatory, that test fails and the decision has to be made deliberately.
* **The trail protects people, it does not surveil them.** ``opened_by`` is recorded
  from the server-resolved principal, never from whatever the client claims, because
  the KPI answers "who approved / who opened" per baht and a spoofable field cannot.
* **Nothing is detected automatically.** ``test_no_auto_detection_route_exists`` is a
  LOCKED Out-of-Scope item (Q1) asserted as a fact about the router, not a promise in
  a comment.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.api.main import app
from services.api.routers import cases as cases_router
from tests.clock_support import Clock, utc


@pytest.fixture(autouse=True)
def _photo_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point photo storage at a per-test tmp dir — never the repo's var/."""
    target = tmp_path / "repair-case-photos"
    monkeypatch.setattr(settings, "repair_case_photo_dir", str(target))
    return target


async def _open_case(client: AsyncClient, truck_id: str = "truck-01", **body: object) -> dict:
    response = await client.post("/api/cases", json={"truck_id": truck_id, **body})
    assert response.status_code == 201, response.text
    return response.json()


async def test_a_case_opens_with_only_a_truck_pick(client_with_db: AsyncClient) -> None:
    """AC-3: the truck pick is the ONLY required input.

    No description, no photo, no caption — the case that ต้อม can open one-handed on
    the hard shoulder while still holding the phone to his ear."""
    case = await _open_case(client_with_db)

    assert case["truck_id"] == "truck-01"
    assert case["status"] == "open"
    assert case["photos"] == []
    assert case["description"] is None
    assert case["case_id"].startswith("case-")
    assert case["opened_at"], "the minute-1 timestamp is the whole point"


async def test_an_unattributed_case_says_so_rather_than_leaving_a_blank(
    client_with_db: AsyncClient,
) -> None:
    """With authn off and no client-supplied actor, ``opened_by`` records
    ``unattributed`` explicitly.

    'We do not know who opened this' is a FACT the traceability KPI has to be able to
    see and count against itself. A NULL would read downstream as missing data — the
    same as a row that was never asked — and quietly flatter the number."""
    case = await _open_case(client_with_db)
    assert case["opened_by"] == "unattributed"


async def test_a_blank_truck_id_is_refused(client_with_db: AsyncClient) -> None:
    """The one required field is required in substance, not just in type: a
    whitespace-only truck id is a case attached to no truck, which is unauditable."""
    response = await client_with_db.post("/api/cases", json={"truck_id": "   "})
    assert response.status_code == 422


async def test_a_photo_attaches_and_lands_on_disk(
    client_with_db: AsyncClient, _photo_dir: Path
) -> None:
    """The photo's BYTES go to disk and its metadata to the row — and the test checks
    both, because a metadata row pointing at a file that is not there is worse than a
    failed upload: the evidence pack would cite it."""
    case = await _open_case(client_with_db)
    payload = b"\xff\xd8\xff\xe0 fake jpeg bytes"

    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/photos",
        files={"file": ("quote.jpg", payload, "image/jpeg")},
        data={"caption": "ใบเสนอราคาจากอู่"},
    )
    assert response.status_code == 200, response.text
    [photo] = response.json()["photos"]

    assert photo["filename"] == "quote.jpg"
    assert photo["content_type"] == "image/jpeg"
    assert photo["size_bytes"] == len(payload)
    assert photo["caption"] == "ใบเสนอราคาจากอู่"

    stored = _photo_dir / photo["stored_path"]
    assert stored.is_file(), "the metadata promises a file that must exist"
    assert stored.read_bytes() == payload


async def test_an_oversized_photo_is_refused_and_leaves_nothing_behind(
    client_with_db: AsyncClient, _photo_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """413, and no partial file, and no metadata.

    The upload is written in chunks, so the interesting failure is a HALF-written file
    left on disk after the limit trips. That would be a photo the case does not know
    about — invisible, unreferenced, and still consuming the disk a pilot box has to
    live within."""
    monkeypatch.setattr(settings, "repair_case_photo_max_bytes", 16)
    case = await _open_case(client_with_db)

    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/photos",
        files={"file": ("huge.jpg", b"x" * 512, "image/jpeg")},
    )
    assert response.status_code == 413

    fetched = await client_with_db.get(f"/api/cases/{case['case_id']}")
    assert fetched.json()["photos"] == []
    assert list(_photo_dir.rglob("*.jpg")) == [], "a partial write must be cleaned up"


async def test_photos_on_a_missing_case_404(client_with_db: AsyncClient) -> None:
    response = await client_with_db.post(
        "/api/cases/case-does-not-exist/photos",
        files={"file": ("x.jpg", b"x", "image/jpeg")},
    )
    assert response.status_code == 404


async def test_cases_list_newest_first_and_filter_by_truck(
    client_with_db: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """เมย์'s working view: what came in, most recent at the top, filterable to the
    truck someone is phoning about.

    The two opens are stamped through a DRIVEN clock rather than the box's own. That
    is not decoration: read against the real clock this test asserted a property the
    endpoint does not have. Two opens land 1-2 ms apart, this box's wall clock steps
    backwards ~0.067/s (PLAN-0099), and the stamps could tie or invert — so the
    assertion below passed ~99% of the time and failed the rest, which is the flake
    this file's ordering fix was chasing. Five minutes apart states the property the
    endpoint really does guarantee — newest stamp on top — with the clock's
    misbehaviour taken out of the question rather than gambled on.
    """
    clock = Clock(utc(hour=9))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    first = await _open_case(client_with_db, "truck-01")
    clock.shift(minutes=5)
    second = await _open_case(client_with_db, "truck-03")
    assert clock.calls >= 2, (
        "the patch must have landed on the WRITE path — against the real clock this "
        "test is the intermittent one it replaced, and it would read green here"
    )

    listed = (await client_with_db.get("/api/cases")).json()
    assert listed["total"] == 2
    assert [c["case_id"] for c in listed["cases"]] == [second["case_id"], first["case_id"]]

    filtered = (await client_with_db.get("/api/cases", params={"truck_id": "truck-03"})).json()
    assert [c["case_id"] for c in filtered["cases"]] == [second["case_id"]]


async def test_tied_open_stamps_still_list_in_one_stable_order(
    client_with_db: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Eight cases opened on a FROZEN clock all tie on ``opened_at`` — and the list
    must still be the same list every time เมย์ refreshes it.

    This is the property the ``case_id`` tiebreak actually buys, asserted directly
    instead of left to the planner: with ``opened_at`` tied the sort key IS
    ``case_id``, so the answer is ``sorted(...)`` exactly. It matters because the
    endpoint truncates with ``limit`` — an unstable tie lets a boundary case flicker
    on and off page 1 between two reads of data that did not change.

    **Why eight cases and not two.** Without the tiebreak, tied rows come back in
    whatever order the planner produces; for two rows that matches ``sorted`` half
    the time, so a two-row probe green-lights the defect every other run — the exact
    disease this test exists to cure. Eight ties put a false pass at 1/8! ≈ 0.002%,
    so deleting ``RepairCase.case_id`` from the ``order_by`` turns this RED
    deterministically rather than intermittently.

    What this does NOT assert: that the tied order reflects which case was opened
    first. ``case_id`` is a random UUID, so it cannot — see the endpoint's docstring
    and PLAN-0099 §Coverage, which records that trade deliberately.
    """
    clock = Clock(utc(hour=9))
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    opened = [(await _open_case(client_with_db, f"truck-{i:02d}"))["case_id"] for i in range(8)]
    assert clock.calls >= len(opened), "the clock patch must have landed on the WRITE path"

    listed = (await client_with_db.get("/api/cases")).json()
    assert (
        len({c["opened_at"] for c in listed["cases"]}) == 1
    ), "the fixture only means anything if every stamp genuinely tied"
    assert [c["case_id"] for c in listed["cases"]] == sorted(opened)

    again = (await client_with_db.get("/api/cases")).json()
    assert [c["case_id"] for c in again["cases"]] == [
        c["case_id"] for c in listed["cases"]
    ], "same data, same page — the refresh stability the truncating `limit` needs"


async def test_get_missing_case_404(client_with_db: AsyncClient) -> None:
    assert (await client_with_db.get("/api/cases/case-nope")).status_code == 404


# --------------------------------------------------------------------------- #
# PLAN-0096 Step 3 — the quote evidence pack (AC-4's data half)
# --------------------------------------------------------------------------- #


async def _add_quote(
    client: AsyncClient, case_id: str, vendor: str, amount: str, file_bytes: bytes | None = None
) -> dict:
    files = {"file": ("quote.pdf", file_bytes, "application/pdf")} if file_bytes else None
    response = await client.post(
        f"/api/cases/{case_id}/quotes",
        data={"vendor": vendor, "amount_thb": amount},
        files=files,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_a_quote_attaches_its_document_and_round_trips(
    client_with_db: AsyncClient, _photo_dir: Path
) -> None:
    """The attachment round-trip AC-4's data half names: bytes to disk, metadata to
    the row, and the two agreeing."""
    case = await _open_case(client_with_db)
    payload = b"%PDF-1.4 fake quote document"
    quote = await _add_quote(client_with_db, case["case_id"], "อู่ช่างเล็ก", "48000.00", payload)

    assert quote["vendor"] == "อู่ช่างเล็ก"
    attachment = quote["attachment"]
    assert attachment["content_type"] == "application/pdf"
    assert attachment["size_bytes"] == len(payload)
    stored = _photo_dir / attachment["stored_path"]
    assert stored.is_file() and stored.read_bytes() == payload


async def test_a_quote_without_a_document_is_still_recorded(
    client_with_db: AsyncClient,
) -> None:
    """เมย์ often keys the amount off a phone call before the paper arrives.

    Refusing the quote until a file exists would push her back to the notebook this
    whole feature replaces — so the attachment is optional, and the pack reports
    separately how many quotes actually carry one."""
    case = await _open_case(client_with_db)
    quote = await _add_quote(client_with_db, case["case_id"], "ส.เจริญยนต์", "45500.50")
    assert quote["attachment"] is None


async def test_the_quoted_amount_keeps_its_exact_satang(
    client_with_db: AsyncClient,
) -> None:
    """Money is Decimal end to end.

    This figure is what the DOA ladder routes on downstream, and a float round-trip
    that turned 45500.50 into 45500.499999 would be a governance defect wearing a
    rounding error's clothes — PLAN-0078's byte-form discipline exists for exactly
    this hop."""
    case = await _open_case(client_with_db)
    quote = await _add_quote(client_with_db, case["case_id"], "ส.เจริญยนต์", "45500.50")
    assert str(quote["amount_thb"]) == "45500.50"

    pack = (await client_with_db.get(f"/api/cases/{case['case_id']}/evidence")).json()
    assert str(pack["lowest_amount_thb"]) == "45500.50"


async def test_a_negative_quote_is_refused(client_with_db: AsyncClient) -> None:
    """Not a discount — a typo or a credit note. Either way it must not reach a
    ladder that routes authority on ฿."""
    case = await _open_case(client_with_db)
    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/quotes",
        data={"vendor": "อู่", "amount_thb": "-500"},
    )
    assert response.status_code == 422


async def test_a_blank_vendor_is_refused(client_with_db: AsyncClient) -> None:
    """A quote with no vendor cannot answer "bought from whom" — the KPI's own
    question — so it is not a quote."""
    case = await _open_case(client_with_db)
    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/quotes",
        data={"vendor": "   ", "amount_thb": "1000"},
    )
    assert response.status_code == 422


async def test_quotes_and_justifications_on_a_missing_case_404(
    client_with_db: AsyncClient,
) -> None:
    """Evidence must never exist for a case that does not — an orphan quote would
    count toward nothing and be visible in no UI."""
    quote = await client_with_db.post(
        "/api/cases/case-nope/quotes", data={"vendor": "V", "amount_thb": "1"}
    )
    assert quote.status_code == 404
    just = await client_with_db.post(
        "/api/cases/case-nope/justifications", json={"vendor": "V", "reason": "r"}
    )
    assert just.status_code == 404


async def test_a_sole_source_justification_is_recorded(client_with_db: AsyncClient) -> None:
    """ADR-0034 E-3: the evidence ALTERNATIVE, not a waiver — the sourcing rule is
    satisfied a different way rather than relaxed."""
    case = await _open_case(client_with_db)
    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/justifications",
        json={"vendor": "ศูนย์ฮีโน่", "reason": "อะไหล่เฉพาะรุ่น ศูนย์เดียวที่มีของ"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["vendor"] == "ศูนย์ฮีโน่"
    assert body["entered_by"] == "unattributed"


async def test_a_justification_needs_both_a_vendor_and_a_reason(
    client_with_db: AsyncClient,
) -> None:
    """An empty reason is the failure mode that matters: it would satisfy the
    sourcing rule while telling a future auditor nothing at all."""
    case = await _open_case(client_with_db)
    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/justifications",
        json={"vendor": "ศูนย์ฮีโน่", "reason": "   "},
    )
    assert response.status_code == 422


async def test_the_evidence_pack_reports_facts_not_a_verdict(
    client_with_db: AsyncClient,
) -> None:
    """The seam Step 4 reads. Note what is ABSENT from the response: no pass/fail,
    no basis, no threshold. Those are Step 4's to compute, so the partner's ฿30,000
    (Q10) can move without changing how evidence is read."""
    case = await _open_case(client_with_db)
    cid = case["case_id"]
    await _add_quote(client_with_db, cid, "อู่ช่างเล็ก", "48000.00")
    await _add_quote(client_with_db, cid, "อู่ช่างเล็ก", "47000.00")
    await _add_quote(client_with_db, cid, "ส.เจริญยนต์", "45500.50")
    await client_with_db.post(
        f"/api/cases/{cid}/justifications",
        json={"vendor": "ศูนย์ฮีโน่", "reason": "อะไหล่เฉพาะรุ่น"},
    )

    pack = (await client_with_db.get(f"/api/cases/{cid}/evidence")).json()

    assert pack["quote_count"] == 3
    assert pack["distinct_vendor_count"] == 2  # three quotes, two places
    assert pack["has_sole_source_justification"] is True
    assert len(pack["quotes"]) == 3
    assert len(pack["justifications"]) == 1
    # the pack must not have started deciding things
    for verdict_key in ("compliant", "three_quote", "three_quote_basis", "passes"):
        assert verdict_key not in pack


def test_no_auto_detection_route_exists() -> None:
    """LOCKED Out-of-Scope (Q1), asserted against the router rather than promised.

    The partner was asked directly and does not want breakdowns detected for him —
    humans open cases. That is a governance property, not a backlog item: an
    auto-detect endpoint would create governed spend nobody opened a case for, and it
    is exactly the kind of thing that arrives later as a 'convenience'. This test is
    what makes adding one a deliberate act."""
    case_paths = [
        route.path  # type: ignore[attr-defined]
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/cases")
    ]
    assert case_paths, "the case router must be mounted at all"
    assert set(case_paths) == {
        "/api/cases",
        "/api/cases/{case_id}",
        "/api/cases/{case_id}/photos",
        "/api/cases/{case_id}/quotes",
        "/api/cases/{case_id}/justifications",
        "/api/cases/{case_id}/evidence",
        # Added deliberately for PLAN-0096 Step 6 (AC-7): the post-approval
        # checklist. Human-flipped like every other route here — it records what a
        # person reports, and nothing on it advances a case by itself.
        "/api/cases/{case_id}/tasks",
        # Added deliberately for PLAN-0096 Step 8 (AC-9): the close-out keying that
        # the month-end export reads. Same property as every route above — เมย์ types
        # what the invoice says, and it deliberately does NOT flip the `close_case`
        # checklist item, because a system-generated flip would put the server's word
        # in a slot that exists to record a person's.
        "/api/cases/{case_id}/closeout",
        # Added deliberately for PLAN-0096 Step 8: ใบที่ตกลง, the quote this repair
        # was agreed at — the figure the DOA ladder routes on. Human-recorded like
        # every route above: it names one of the quotes เมย์ already keyed, and the
        # server picks nothing (accepting the cheapest automatically would be exactly
        # the auto-detection this test exists to keep out).
        "/api/cases/{case_id}/accepted-quote",
    }
    for path in case_paths:
        assert "detect" not in path and "auto" not in path
