"""The case list past its own page size, end to end (PLAN-0107 AC-7, ② data reach).

**Why this scenario exists.** The case-list UI requests ``limit=20``
(``services/api/static/assets/view-case.js``); the server defaults to 50 and clamps
at 500. Before this build the live tree held **two** cases, so nothing — no fixture,
no running system — ever reached the truncation boundary. The ``limit`` clause, the
``opened_at``/``case_id`` tiebreak and the overflow behaviour of the list were all
unexercised, and the 919px clipped render that shipped to a live customer-facing
system came from a tree nothing reproduced. **A state no test can reach is a state
no oracle can judge.**

Nothing is stubbed on either side of the seam under test. The producer is the REAL
live seed (``operate_seed.seed_case_list_history`` — the same function the API
lifespan calls) plus the REAL capture endpoint (``POST /api/cases``); the consumer
is the REAL list endpoint (``GET /api/cases``) reached over HTTP. A version of this
test that inserted rows with a hand-built ``session.add`` and then called the query
function directly would agree with itself by construction.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.db.repair_case import CASE_STATUS_CLOSED
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.operate_seed import (
    _CASE_LIST_HISTORY,
    CASE_LIST_HISTORY_PREFIX,
    seed_case_list_history,
)

#: The UI's own request. Hard-coded here on purpose: this test is the thing that
#: pins the boundary, so reading the number out of the JS would make it agree with
#: whatever the JS said, including a wrong value.
_UI_LIMIT = 20

#: 19 seeded + 2 opened over HTTP. The point of the +2 is that it is > _UI_LIMIT:
#: at exactly 20 the truncation boundary is untestable.
_LIVE_CASES = 2


@pytest.fixture(autouse=True)
def _clean_projection() -> Iterator[None]:
    """The projection cache is process-global; a leaked one would make a later test lie."""
    case_projection.reset()
    yield
    case_projection.reset()


async def _seed(maker: async_sessionmaker[AsyncSession]) -> int:
    """Run the REAL live seed on the SAME engine the API client writes through.

    ``api_db_maker`` exists for exactly this: a second, independent
    ``async_session()`` would be a different asyncpg connection and collides with
    the one the client holds (`another operation is in progress`, measured).
    """
    async with maker() as session:
        return await seed_case_list_history(session)


async def _open_case(client: AsyncClient, truck_id: str, description: str) -> str:
    response = await client.post(
        "/api/cases",
        json={"truck_id": truck_id, "work_type": "breakdown", "description": description},
    )
    assert response.status_code == 201, response.text
    case_id: str = response.json()["case_id"]
    return case_id


async def _list(client: AsyncClient, **params: object) -> list[dict]:
    response = await client.get("/api/cases", params=params)
    assert response.status_code == 200, response.text
    cases: list[dict] = response.json()["cases"]
    return cases


@pytest.fixture
async def overflowing_list(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession]
) -> AsyncClient:
    """21 cases: the real backlog seed plus two opened through the real endpoint."""
    inserted = await _seed(api_db_maker)
    assert inserted == len(_CASE_LIST_HISTORY), (
        f"the backlog seed inserted {inserted} case(s), expected {len(_CASE_LIST_HISTORY)} — "
        "with fewer than 19 the list cannot exceed the UI's page size and every "
        "assertion below would be vacuously true"
    )
    await _open_case(client_with_db, "truck-01", "เพลาขาดกลางทาง รถจอดข้างทางพร้อมของเต็มคัน")
    await _open_case(client_with_db, "truck-02", "เบรกลมรั่ว จอดรอช่างที่อู่")
    return client_with_db


async def test_the_tree_actually_exceeds_the_ui_page_size(
    overflowing_list: AsyncClient,
) -> None:
    """Anti-vacuity: every assertion below is about TRUNCATION, which needs overflow.

    If the tree ever holds ≤ 20 cases this test reddens FIRST and names why, rather
    than letting the limit assertions pass because there was nothing to cut.
    """
    total = len(await _list(overflowing_list, limit=500))
    assert total > _UI_LIMIT, (
        f"the tree holds {total} case(s), which does not exceed the UI's limit of "
        f"{_UI_LIMIT} — the truncation boundary is unreachable, so the limit "
        "assertions in this module would be vacuously true"
    )
    assert total == len(_CASE_LIST_HISTORY) + _LIVE_CASES


async def test_the_ui_limit_truncates_to_exactly_twenty_newest_first(
    overflowing_list: AsyncClient,
) -> None:
    """The UI's own request returns one page, newest first — the clause under test."""
    page = await _list(overflowing_list, limit=_UI_LIMIT)
    assert len(page) == _UI_LIMIT, (
        f"GET /api/cases?limit={_UI_LIMIT} returned {len(page)} cases. The UI asks for "
        "this exact limit; a server that ignores it hands the browser an unbounded list."
    )
    opened = [case["opened_at"] for case in page]
    assert opened == sorted(opened, reverse=True), "the page is not newest-first"


async def test_the_page_is_stable_across_two_reads(overflowing_list: AsyncClient) -> None:
    """Repeatability at the boundary — the reason the ``case_id`` tiebreak exists.

    Without the tiebreak two cases sharing an ``opened_at`` leave their relative
    order to the planner, so a boundary case flickers on and off page 1 between two
    reads of unchanged data. This box's wall clock steps backwards (PLAN-0099
    measured it), which is what makes the tie reachable rather than theoretical.
    """
    first = [case["case_id"] for case in await _list(overflowing_list, limit=_UI_LIMIT)]
    second = [case["case_id"] for case in await _list(overflowing_list, limit=_UI_LIMIT)]
    assert first == second, "two reads of unchanged data returned different pages"


async def test_the_boundary_case_is_excluded_at_the_ui_limit_and_present_by_default(
    overflowing_list: AsyncClient,
) -> None:
    """The case that falls off page 1 is really there — truncation, not absence."""
    page = {case["case_id"] for case in await _list(overflowing_list, limit=_UI_LIMIT)}
    everything = [case["case_id"] for case in await _list(overflowing_list, limit=500)]
    dropped = [case_id for case_id in everything if case_id not in page]
    assert dropped, "nothing was truncated — see the anti-vacuity test above"
    assert set(dropped) <= set(everything)
    # The dropped ones are the OLDEST, which is what "newest first + limit" means.
    assert dropped == everything[_UI_LIMIT:]


async def test_the_backlog_seed_is_idempotent(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession]
) -> None:
    """A second boot must not double the list.

    The seed runs on EVERY boot by design (placed before the run's early-return, so
    an upgraded deployment is not left with a two-case list), which makes idempotency
    load-bearing rather than tidy.
    """
    first = await _seed(api_db_maker)
    second = await _seed(api_db_maker)
    assert first == len(_CASE_LIST_HISTORY)
    assert second == 0, "the second seed inserted rows — a restart would grow the list"

    listed = await _list(client_with_db, limit=500)
    backlog = [c for c in listed if c["case_id"].startswith(CASE_LIST_HISTORY_PREFIX)]
    assert len(backlog) == len(_CASE_LIST_HISTORY)


async def test_the_backlog_is_closed_so_it_cannot_compete_for_the_event_slot(
    overflowing_list: AsyncClient,
) -> None:
    """CLOSED is the property that keeps this seed from damaging the demo.

    An OPEN backlog case would sit in the event stream and could displace a truck's
    latest event — the failure that once cost the demo its ฿48,000 axle breach. This
    pins the property rather than trusting the seed's comment.
    """
    listed = await _list(overflowing_list, limit=500)
    backlog = [c for c in listed if c["case_id"].startswith(CASE_LIST_HISTORY_PREFIX)]
    assert backlog, "no backlog case found — the seed did not run"
    not_closed = [c["case_id"] for c in backlog if c["status"] != CASE_STATUS_CLOSED]
    assert not not_closed, (
        f"{len(not_closed)} backlog case(s) are not CLOSED: {not_closed}. An open "
        "backlog case competes for its truck's latest-event slot and can displace the "
        "demo's hero breach."
    )
