"""AC-8 — ``GET /runs`` carries a bounded newest-N default (PLAN-0112 SD-6 RULED (b)).

**Why the bound became load-bearing.** ``done/0110`` G4 recorded the run population as
structurally bounded at two: ``POST /procedures/{id}/run`` is excluded from the published
allowlist, so runs came from the boot seed alone. That paragraph carried its own
tripwire — *"if that route is ever admitted, the cap question reopens"*, with a second
trigger for the day server-side firing landed. PLAN-0112 Step 3 was that day: a visitor's
accepted quote now mints a governed run through the event bridge, so the population has
an unbounded axis and ``list_runs``' missing ``.limit()`` (G-15) stopped being safe.

**Two properties are asserted, and they pull in opposite directions on purpose.**

* the **list** is bounded to the newest N — and *newest* is asserted, not just the
  count: a bound that returned the OLDEST N would satisfy a length check perfectly
  while showing an operator the least relevant page of their own system;
* the **``waiting_human_count``** is NOT bounded. It is the "waiting on me" badge Tab H
  paints (named as such in ``operate_seed.py``'s own docstring). Counting the page
  instead of the population would make the badge shrink as newer runs arrived, silently
  under-reporting decisions that are still pending — a governed action nobody is told
  about is the failure this surface exists to prevent.

The bound is read from ``settings.runs_list_default_limit`` rather than hardcoded, which
is what lets these tests exercise it at N=3 instead of seeding 201 rows.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import services.api.main as api_main
from services.api.config import settings
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.operate_seed import DEMO_HISTORY_RUN_ID, DEMO_RUN_ID

_N = 3
_T0 = datetime(2026, 8, 22, 6, 0, tzinfo=UTC)
_VERTICAL = "fleet_maintenance"


async def _seed_runs(
    session: AsyncSession, count: int, *, status: str = PipelineRunStatus.COMPLETED.value
) -> list[str]:
    """``count`` runs, each one hour newer than the last. Returns ids OLDEST-first."""
    ids: list[str] = []
    for i in range(count):
        run_id = f"run-bound-{i:02d}"
        started = _T0 + timedelta(hours=i)
        session.add(
            PipelineRun(
                run_id=run_id,
                procedure_id="governed_repair_approval",
                agent_id="fleet-ops-agent",
                trigger_context={"source": "seeded-for-the-bound"},
                status=status,
                started_at=started,
                updated_at=started,
            )
        )
        ids.append(run_id)
    await session.commit()
    return ids


@pytest.fixture
def bound_at_n(monkeypatch: pytest.MonkeyPatch) -> int:
    """Exercise the real setting at a small N — the reason it is a setting at all."""
    monkeypatch.setattr(settings, "runs_list_default_limit", _N)
    return _N


async def _listed(client: AsyncClient) -> dict[str, object]:
    response = await client.get("/runs")
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body


async def test_the_list_returns_the_newest_n_not_merely_n(
    client_with_db: AsyncClient, db_session: AsyncSession, bound_at_n: int
) -> None:
    """AC-8's pass read: seed N+1, read N back — and prove they are the NEWEST N."""
    seeded = await _seed_runs(db_session, bound_at_n + 1)
    assert len(seeded) == bound_at_n + 1

    body = await _listed(client_with_db)
    runs = body["runs"]
    assert isinstance(runs, list)
    returned = [r["run_id"] for r in runs]

    assert len(returned) == bound_at_n, (
        f"seeded {len(seeded)} runs under a bound of {bound_at_n} and got "
        f"{len(returned)} back: {returned}"
    )
    # `seeded` is oldest-first, so the newest N are its tail, reversed to newest-first.
    assert returned == list(reversed(seeded[-bound_at_n:])), (
        f"the bound returned {returned}; the newest {bound_at_n} are "
        f"{list(reversed(seeded[-bound_at_n:]))}. A length-only assertion would pass "
        "here even if the endpoint served the OLDEST page."
    )
    assert seeded[0] not in returned, "the oldest run must be the one pushed out"


async def test_the_waiting_badge_counts_the_population_not_the_page(
    client_with_db: AsyncClient, db_session: AsyncSession, bound_at_n: int
) -> None:
    """The badge must not shrink because the list did.

    This is the assertion that distinguishes "bounded the query" from "bounded the
    truth". With every seeded run parked, the page holds N and the badge must still
    report N+1 — the number of decisions actually waiting on a human.
    """
    seeded = await _seed_runs(
        db_session, bound_at_n + 1, status=PipelineRunStatus.WAITING_HUMAN.value
    )

    body = await _listed(client_with_db)
    runs = body["runs"]
    assert isinstance(runs, list)

    assert len(runs) == bound_at_n, "precondition: the list itself is bounded"
    assert body["waiting_human_count"] == len(seeded), (
        f"the badge reports {body['waiting_human_count']} with {len(seeded)} runs "
        f"parked at waiting_human. Counting the bounded page would give "
        f"{bound_at_n} and hide a pending decision from the person who owes it."
    )
    assert body["waiting_human_count"] > len(runs), (
        "the whole point of this test is a badge LARGER than the page; if these are "
        "equal the bound was not exercised and the assertion above is vacuous"
    )


async def test_the_default_bound_is_wide_enough_to_be_a_cap_not_a_page_size(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """Guards the number itself, which no other test reads.

    A default of, say, 2 would satisfy every bounded-ness assertion above and quietly
    turn Tab H into a two-row window. The shipped default is a CAP on an unbounded
    scan, so it is asserted to clear the demo population by a wide margin — and to
    exist at all, which a ``None`` default would not.
    """
    assert settings.runs_list_default_limit >= 50, (
        f"the shipped bound is {settings.runs_list_default_limit}; below ~50 this stops "
        "being a cap on an unbounded scan and becomes an un-paged page size"
    )
    seeded = await _seed_runs(db_session, 5)
    body = await _listed(client_with_db)
    runs = body["runs"]
    assert isinstance(runs, list)
    assert {r["run_id"] for r in runs} >= set(seeded), (
        "a handful of runs must all fit under the SHIPPED default, or the demo's own "
        "two runs could fall off the end of Tab H"
    )


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    """Process-global caches and the hook registry; a leak makes a later test lie."""
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_booted(
    monkeypatch: pytest.MonkeyPatch, api_db_maker: async_sessionmaker[AsyncSession]
) -> None:
    """The REAL boot seed block, pointed at the DISPOSABLE test database."""
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "oct_demo_seed_operate", True)
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(api_main, "async_session", api_db_maker)


async def test_both_demo_runs_are_within_the_bound_after_a_real_boot(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_booted: None
) -> None:
    """AC-8's second clause, against the ACTUAL seed block rather than fixture rows.

    The demo runs are the OLDEST things on a freshly booted system, so they are exactly
    what a newest-N bound would drop first. Asserted through ``GET /runs`` — the payload
    Tab H reads — because a bound that hid the demo would break the beat while every
    row-level test above stayed green.
    """
    await api_main._seed_fleet_operate_demo(_VERTICAL)
    await case_projection.refresh(db_session)

    body = await _listed(client_with_db)
    runs = body["runs"]
    assert isinstance(runs, list)
    painted = {r["run_id"] for r in runs}

    assert DEMO_RUN_ID in painted, (
        f"{DEMO_RUN_ID} is not within the bound — the visitor-facing beat is invisible "
        f"on Tab H. Painted: {sorted(painted)}"
    )
    assert DEMO_HISTORY_RUN_ID in painted, (
        f"{DEMO_HISTORY_RUN_ID} is not within the bound — the ฿ history the KPI panel "
        f"reads is invisible. Painted: {sorted(painted)}"
    )
