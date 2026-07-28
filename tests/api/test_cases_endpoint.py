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
    client_with_db: AsyncClient,
) -> None:
    """เมย์'s working view: what came in, most recent at the top, filterable to the
    truck someone is phoning about."""
    first = await _open_case(client_with_db, "truck-01")
    second = await _open_case(client_with_db, "truck-03")

    listed = (await client_with_db.get("/api/cases")).json()
    assert listed["total"] == 2
    assert [c["case_id"] for c in listed["cases"]] == [second["case_id"], first["case_id"]]

    filtered = (await client_with_db.get("/api/cases", params={"truck_id": "truck-03"})).json()
    assert [c["case_id"] for c in filtered["cases"]] == [second["case_id"]]


async def test_get_missing_case_404(client_with_db: AsyncClient) -> None:
    assert (await client_with_db.get("/api/cases/case-nope")).status_code == 404


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
    }
    for path in case_paths:
        assert "detect" not in path and "auto" not in path
