"""The case ↔ run link, end to end (PLAN-0096 Step 8, build-order item 3).

The table AC-9's two approval columns — วันที่อนุมัติ and ผู้อนุมัติ — will be
filled from. Before it, the only path from a repair case to the run that approved
it was a full JSONB scan matching a `case_id` buried in an action's reasoning
trace, with a string-vs-string amount join as the fallback.

Nothing is stubbed on either side of the seam. The producer is the real HTTP
capture surface plus the real shipped procedure fired through the real run
endpoint; the consumer is the real `resolve_gated_step` driver, which fires the
real registered hook. A test that called `link_resolved_cases` directly would
prove the writer works and say nothing about whether the engine ever calls it —
and "the engine never calls it" is the entire failure this build exists to fix.

**Every test here also asserts the hook recorded no failure.** That is not
belt-and-braces: the hook is fail-soft by design, because an audit convenience
must never roll back a human's approval. Session 191 measured what a fail-soft
handler does to an oracle — it swallowed an exception so completely that the test
asserting the resulting absence stayed green. `gate_hooks.failures()` exists so
"the hook wrote nothing" and "the hook exploded" cannot be read as the same result.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.repair_case_run_link import RepairCaseRunLink
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.persistence import load_run
from services.engine.procedures.spec import load_procedures
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"
#: The owner tier is what a ฿62,000 repair routes to under the partner's real ladder.
_OWNER = "appr-owner"


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


def _person(person_id: str):
    spec = load_procedures(_VERTICAL)
    return next(p for p in spec.principals if p.person_id == person_id)


async def _resolve(session: AsyncSession, run_id: str, decisions: dict[str, str]):
    """Resolve the hero's gate the way the run itself demands.

    ``procedure`` and ``principals`` are NOT optional here: the hero carries a
    separation-of-duties constraint, so the orchestrator persisted a
    ``step_principals`` map, and ``_enforce_principal_sod`` refuses to run the
    live SoD check without them rather than silently skipping it (ADR-0026 D4).
    Passing them is what makes this the real driver path and not a weakened one.
    """
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    return await resolve_gated_step(
        session,
        run_id,
        _GATE_STEP,
        decisions,
        _person(_OWNER),
        procedure=procedure,
        principals=list(spec.principals),
    )


async def _accepted_case(client: AsyncClient) -> str:
    """A real ฿62,000 axle case with three garages compared and the dearest agreed."""
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทางแถวปากช่อง",
        },
    )
    case_id: str = opened.json()["case_id"]
    chosen = ""
    for vendor, amount in (
        ("ส.เจริญยนต์", "58000.00"),
        ("อู่ริมทางปากช่อง", "62000.00"),
        ("อู่ช่างเล็ก", "59500.00"),
    ):
        quoted = await client.post(
            f"/api/cases/{case_id}/quotes", data={"vendor": vendor, "amount_thb": amount}
        )
        assert quoted.status_code == 201, quoted.text
        if vendor == "อู่ริมทางปากช่อง":
            chosen = quoted.json()["quote_id"]
    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": chosen, "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้"},
    )
    assert accepted.status_code == 201, accepted.text
    return case_id


async def _links(session: AsyncSession, case_id: str) -> list[RepairCaseRunLink]:
    rows = await session.execute(
        sa.select(RepairCaseRunLink)
        .where(RepairCaseRunLink.case_id == case_id)
        .order_by(RepairCaseRunLink.linked_at, RepairCaseRunLink.outcome)
    )
    return list(rows.scalars())


async def test_approving_a_real_case_records_which_run_decided_it(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The whole claim: approve at the gate, and the case knows its run afterwards.

    This is what makes AC-9's วันที่อนุมัติ / ผู้อนุมัติ answerable for a real
    repair instead of only for the demo fixture."""
    case_id = await _accepted_case(client_with_db)

    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={})
    assert fired.status_code == 200, fired.text
    run_id = fired.json()["run_id"]
    ours = next(p["action_id"] for p in fired.json()["proposals"] if case_id in str(p["action_id"]))

    await _resolve(db_session, run_id, {ours: "approve"})

    links = await _links(db_session, case_id)
    assert len(links) == 1, "one decision, one link row"
    assert links[0].run_id == run_id
    assert links[0].step_id == _GATE_STEP
    assert links[0].outcome == "approved"
    assert gate_hooks.failures() == [], "the hook is fail-soft; a swallowed error must show here"


async def test_a_rejected_case_is_linked_too_and_says_so(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """A reject is a governed decision, not an absence.

    The KPI counts spend that is fully traceable; a repair someone declined is
    traceable, and a link table that recorded only approvals would quietly turn
    every rejection into a missing row."""
    case_id = await _accepted_case(client_with_db)
    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={})
    run_id = fired.json()["run_id"]
    ours = next(p["action_id"] for p in fired.json()["proposals"] if case_id in str(p["action_id"]))

    await _resolve(db_session, run_id, {ours: "reject"})

    links = await _links(db_session, case_id)
    assert [link.outcome for link in links] == ["rejected"]
    assert gate_hooks.failures() == []


async def test_the_same_resolution_twice_does_not_double_count_the_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Idempotent by the schema, not by care.

    A manual run is re-fireable without limit and the driver can be re-entered; a
    second link row for one decision would inflate the traceability KPI, which is
    the one number this whole PLAN exists to make honest."""
    case_id = await _accepted_case(client_with_db)
    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={})
    run_id = fired.json()["run_id"]
    ours = next(p["action_id"] for p in fired.json()["proposals"] if case_id in str(p["action_id"]))
    await _resolve(db_session, run_id, {ours: "approve"})

    loaded = await load_run(db_session, run_id)
    target = next(sr for sr in loaded.step_results if sr.step_id == _GATE_STEP)
    await gate_hooks.fire_on_resolved(db_session, run_id, target)

    assert len(await _links(db_session, case_id)) == 1
    assert gate_hooks.failures() == []


async def test_a_proposal_carrying_no_case_produces_no_link(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The demo's routine rows must not manufacture links for cases nobody opened.

    `case_id_of` returning None is the normal answer for a non-case-derived
    proposal, and it has to stay distinguishable from a failure — otherwise the
    fixture starts writing audit rows about repairs that never happened."""
    case_id = await _accepted_case(client_with_db)
    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={})
    run_id = fired.json()["run_id"]
    decisions = {str(p["action_id"]): "approve" for p in fired.json()["proposals"]}
    assert len(decisions) >= 2, "the fixture breach must ride along for this to prove anything"

    await _resolve(db_session, run_id, decisions)

    all_links = list((await db_session.execute(sa.select(RepairCaseRunLink))).scalars())
    linked_cases = {link.case_id for link in all_links}
    # The fixture's own breach DOES carry a case_id (`case-demo-truck03-gearbox`),
    # so it links legitimately; what must not appear is a link for a proposal with
    # no case at all.
    assert case_id in linked_cases
    assert all(link.case_id for link in all_links), "no link may carry an empty case id"
    assert gate_hooks.failures() == []
