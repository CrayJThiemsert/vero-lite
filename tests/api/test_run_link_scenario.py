"""The case ↔ run link, end to end (PLAN-0096 Step 8, build-order item 3).

This is the seam AC-9's two approval columns — วันที่อนุมัติ and ผู้อนุมัติ — will
be filled from. Before it, the only path from a repair case to the run that
approved it was a full JSONB scan matching a `case_id` buried in an action's
reasoning trace, with a string-vs-string amount join as the fallback.

Nothing is stubbed on either side of the seam. The producer is the real HTTP
capture surface plus the real shipped procedure fired through the real run
endpoint; the consumer is the real `resolve_gated_step` AND `ratify_gated_step`
drivers, which fire the real registered hook. A test that called
`link_resolved_cases` directly would prove the writer works and say nothing about
whether the engine ever calls it — and "the engine never calls it" is the entire
failure this build exists to fix.

**Both drivers are covered, and that is the point of the module.** ADR-0034's E-2
path resolves provisionally and settles days later through `ratify_gated_step`; a
suite that exercised only the first driver would pass completely while every
emergency approval stayed frozen at `provisional` forever. Measured s192: deleting
the second `fire_on_resolved` call reddens exactly the two ratification tests and
nothing else.

**Every test here also asserts the hook recorded no failure.** That is not
belt-and-braces: the hook is fail-soft by design, because an audit convenience
must never roll back a human's approval. Session 191 measured what a fail-soft
handler does to an oracle — it swallowed an exception so completely that the test
asserting the resulting absence stayed green. `gate_hooks.failures()` exists so
"the hook wrote nothing" and "the hook exploded" cannot be read as the same result.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.repair_case_run_link import RepairCaseRunLink
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.action_step import (
    WaiverInvocation,
    ratify_gated_step,
    resolve_gated_step,
)
from services.engine.procedures.persistence import load_run
from services.engine.procedures.spec import load_procedures
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"
#: The owner tier is what a ฿62,000 repair routes to under the partner's real ladder.
_OWNER = "appr-owner"
#: ต้อม, the mechanic who opens the case and fires the round. He is the REQUESTER half
#: of the hero's separation-of-duties constraint, and the run endpoint records him from
#: the authenticated identity — never from the request body (`runs.py:391`).
_MECHANIC = "req-mechanic-tom"

#: Authn is ON for this module, and that is load-bearing rather than incidental.
#: `POST /procedures/{id}/run` persists `step_principals` from `auth.person`
#: (`runs.py:405`); with authn off that is None, so the run records no requester and
#: `_enforce_principal_sod` correctly refuses the later approval with "no principal
#: resolved for constrained step 'intake'". Firing the round as a real authenticated
#: ต้อม is what makes the SoD check pass on its MERITS — two distinct humans — instead
#: of being skipped. `req-mechanic-tom` is a declared fleet principal, so the bearer
#: resolves against the real spec with no `_principal_index` monkeypatch.
_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}


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
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


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


async def _resolve_provisionally(
    session: AsyncSession, run_id: str, decisions: dict[str, str]
) -> Any:
    """Resolve under the emergency waiver — ต้อม RECORDS a decision เฮีย gave by phone.

    The recorder is the mechanic, not the owner: that is the whole shape of E-2. The
    approval happened on the shoulder of a road, so the person at a keyboard is
    recording someone else's authority, and the `governed_decision` tie is WITHHELD
    until that someone signs (ADR-0034 D3). Mirrors `test_ratification_matrix`.
    """
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    return await resolve_gated_step(
        session,
        run_id,
        _GATE_STEP,
        decisions,
        _person(_MECHANIC),
        procedure=procedure,
        principals=list(spec.principals),
        waiver_invocation=WaiverInvocation(
            justification="รถเสียกลางทาง โทรหาเฮียแล้วเคาะมาว่าให้ซ่อมเลย"
        ),
    )


async def _ratify(session: AsyncSession, run_id: str, *, decision: str = "ratify") -> Any:
    """เฮีย signs (or refuses) afterwards — the ONLY path to `ratify_gated_step`.

    There is no HTTP route for this; `services/api/routers/` has no ratify endpoint
    at all, so the driver is the production surface and calling it directly is the
    real consumer, not a shortcut around one.
    """
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    return await ratify_gated_step(
        session,
        run_id,
        _GATE_STEP,
        _person(_OWNER),
        decision=decision,  # type: ignore[arg-type]
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
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]
    assert opened.json()["opened_by"] == _MECHANIC, "the case must be attributed to ต้อม"
    chosen = ""
    for vendor, amount in (
        ("ส.เจริญยนต์", "58000.00"),
        ("อู่ริมทางปากช่อง", "62000.00"),
        ("อู่ช่างเล็ก", "59500.00"),
    ):
        quoted = await client.post(
            f"/api/cases/{case_id}/quotes",
            data={"vendor": vendor, "amount_thb": amount},
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
    return case_id


async def _fire(client: AsyncClient) -> dict[str, Any]:
    """Fire the hero from the production entry point, as the authenticated ต้อม.

    The bearer is the whole point: this endpoint persists ``step_principals`` from
    the SERVER-resolved principal, and that recorded requester is what the approval
    below is checked against. An unauthenticated fire returns 200 and a run that
    can never be approved.
    """
    fired = await client.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    body: dict[str, Any] = fired.json()
    assert body["triggered_by"] == _MECHANIC, "the requester half must be server-resolved"
    return body


def _action_for(body: dict[str, Any], case_id: str) -> str:
    return next(str(p["action_id"]) for p in body["proposals"] if case_id in str(p["action_id"]))


def _decide(body: dict[str, Any], case_id: str, verdict: str) -> dict[str, str]:
    """Give ``case_id`` the verdict under test and every other proposal a reject.

    The gate refuses a partial resolution — an undecided proposed action raises
    rather than being skipped, because silence about a proposed spend is exactly
    what an audit trail must not contain. So a test cannot decide only its own case
    and ignore the fixture rows riding along in the same round.

    Rejecting the rest is not padding. It puts one approval and one rejection in a
    SINGLE gate resolution, which is the second of the three measured reasons this
    table is a join table rather than a ``run_id`` column on ``repair_case``: a run
    pointer cannot say that run R approved case A and refused case B.
    """
    ours = _action_for(body, case_id)
    return {
        str(p["action_id"]): (verdict if str(p["action_id"]) == ours else "reject")
        for p in body["proposals"]
    }


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

    body = await _fire(client_with_db)
    run_id = body["run_id"]

    await _resolve(db_session, run_id, _decide(body, case_id, "approve"))

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
    body = await _fire(client_with_db)
    run_id = body["run_id"]

    await _resolve(db_session, run_id, _decide(body, case_id, "reject"))

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
    body = await _fire(client_with_db)
    run_id = body["run_id"]
    await _resolve(db_session, run_id, _decide(body, case_id, "approve"))

    loaded = await load_run(db_session, run_id)
    target = next(sr for sr in loaded.step_results if sr.step_id == _GATE_STEP)
    await gate_hooks.fire_on_resolved(db_session, run_id, target)

    assert len(await _links(db_session, case_id)) == 1
    assert gate_hooks.failures() == []


async def test_ratifying_adds_a_second_row_beside_the_provisional_one(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """THE test this build exists for: `ratify_gated_step` fires the hook too.

    Hooking only `resolve_gated_step` would leave every deferred-ratification case
    frozen at `provisional` forever — the export would report a repair as unsigned
    after เฮีย had signed for it, which is worse than reporting nothing, because it
    is a confident false statement about who stands behind the spend.

    The second row lands BESIDE the first, never over it. That is the deferred
    mechanism's entire value as evidence: the trail has to be able to show that a
    repair was authorised on the shoulder of a road on Saturday and signed for on
    Tuesday. An UPDATE would collapse those two facts into one and lose the gap.
    """
    case_id = await _accepted_case(client_with_db)
    body = await _fire(client_with_db)
    run_id = body["run_id"]

    await _resolve_provisionally(db_session, run_id, _decide(body, case_id, "approve"))

    provisional = await _links(db_session, case_id)
    assert [link.outcome for link in provisional] == [
        "provisional"
    ], "an unsigned emergency approval must not read as a settled one"
    assert gate_hooks.failures() == []

    await _ratify(db_session, run_id)

    after = await _links(db_session, case_id)
    assert {link.outcome for link in after} == {
        "provisional",
        "ratified",
    }, "the ratify call site did not fire the hook — the E-2 path drops silently"
    assert len(after) == 2, "append-only: the ratification must not overwrite its provisional"
    assert gate_hooks.failures() == []


async def test_a_refused_ratification_is_recorded_as_refused(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """เฮีย declines to stand behind what was done in his name.

    A refusal is a governed outcome, not a missing signature, and it must be
    distinguishable from `provisional` — "nobody has signed yet" and "the authority
    looked at it and refused" are opposite facts about the same baht."""
    case_id = await _accepted_case(client_with_db)
    body = await _fire(client_with_db)
    run_id = body["run_id"]
    await _resolve_provisionally(db_session, run_id, _decide(body, case_id, "approve"))

    await _ratify(db_session, run_id, decision="refuse")

    outcomes = {link.outcome for link in await _links(db_session, case_id)}
    assert outcomes == {"provisional", "refused"}
    assert gate_hooks.failures() == []


async def test_a_case_rejected_under_a_waiver_is_rejected_not_provisional(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Cray, typed s192: a refusal is checked BEFORE the ratification state.

    The obligation belongs to the run, so it rides along on every case that gate
    touched — including the ones turned down. Reading it as the case's own status
    would stamp a declined repair `provisional` and the export would chase เฮีย for
    a signature on spend that never happened. There is nothing to ratify: the answer
    was no, and that answer is already complete.

    This is only observable because the hook reads the full decision record; while
    it read `output_set` the rejected case was absent entirely and the mis-labelling
    could not be seen.
    """
    case_id = await _accepted_case(client_with_db)
    body = await _fire(client_with_db)
    run_id = body["run_id"]

    # The waiver is invoked for the ROUND; this case is still refused inside it.
    await _resolve_provisionally(db_session, run_id, _decide(body, case_id, "reject"))

    assert [link.outcome for link in await _links(db_session, case_id)] == ["rejected"]
    assert gate_hooks.failures() == []


async def test_a_proposal_carrying_no_case_produces_no_link(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The demo's routine rows must not manufacture links for cases nobody opened.

    `case_id_of` returning None is the normal answer for a non-case-derived
    proposal, and it has to stay distinguishable from a failure — otherwise the
    fixture starts writing audit rows about repairs that never happened."""
    case_id = await _accepted_case(client_with_db)
    body = await _fire(client_with_db)
    run_id = body["run_id"]
    decisions = {str(p["action_id"]): "approve" for p in body["proposals"]}
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
