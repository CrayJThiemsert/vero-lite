"""Accepting a quote fires a governed run — the visitor's case reaches Tab H.

**PLAN-0112 Step 3 / AC-2 + AC-3.** The §8-binding scenario: the REAL Tab I HTTP
intake flow (``POST /api/cases`` → ``/quotes`` → ``/accepted-quote``) drives the REAL
server-side firing seam on realistic simulated data — a breaching THB amount against
a real seeded ``Truck`` ceiling — and the run is read back through the REAL Tab H
surface (``GET /runs``). Nothing on either side of the seam is stubbed.

**The run existing is NOT the claim; the run being ABOUT the visitor's case — and
about NOTHING ELSE — is.** A run can fire, park, and present a perfectly healthy gate
that concerns some other truck entirely, with the visitor's own case absent from every
proposal and no error raised anywhere. Session 244 measured exactly that shape when the
case projection had not caught up (a run whose single proposal resolved to
``case-demo-truck03-gearbox``). So every test here asserts the visitor's ``case_id`` is
the proposal, not merely that the count moved.

**PLAN-0113 Step 3 tightened that from AMONG to ONLY.** ``intake`` used to be a
fleet-wide population scan (G-6); it now carries
``scope_by: {field: case_id, from: trigger.entity_ids}`` + ``when_absent: sweep``
(``verticals/fleet_maintenance/procedures.yaml``), so an event-fired run reads only
its own firing case's rows. The old ``any(case_id in pid ...)`` reading cannot tell
"scoped to one" from "swept the fleet and mine happened to be in it" — it stays green
through the very defect the scoping exists to remove — so :func:`_assert_run_is_about`
now asserts the count and the identity separately.

**SD-2(b) as Cray ruled it, both directions.** Re-accepting the SAME quote is not a
material change and must NOT mint a second run; accepting a DIFFERENT quote must.
That is why ``entity_ids`` carries the quote's identity (G-14) and never
``accepted_id``, which ``accept_quote`` regenerates on every call.

**The demo seed's parked run must not swallow the visitor's.** Fleet's published
profile pins ``OCT_DEMO_SEED_OPERATE=true``, which parks a ``governed_repair_approval``
run at boot; the bridge's SD-P4 backpressure would otherwise skip every visitor
acceptance on that deployment with no error and no visible trace.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.audit_log import AuditLog
from services.db.repair_case_run_link import RepairCaseRunLink
from services.db.repair_spend_export import CSV_ENCODING, load_monthly_export
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.persistence import load_run
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"

#: ต้อม — the one fleet persona holding the SoD ``requester`` role, and therefore the
#: only valid ``event_trigger.owning_person_id`` (G-8). Firing keyed as him is what
#: leaves the run approvable by a distinct human.
_MECHANIC = "req-mechanic-tom"
_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}

#: วิรัช — ผจก.เดินรถ. The partner's ladder (Q9) routes ฿5,001-30,000 to him, so a
#: mid-band repair is what makes "a DECLARED approver can actually resolve it"
#: (AC-4) a live assertion rather than a hypothetical: he holds `ผจก.เดินรถ` and
#: `ช่างใหญ่` cumulatively (PLAN-0075 Policy B) but NOT `เจ้าของกิจการ`, so he can
#: resolve this band and could not resolve the ฿62,000 one above.
_WIRAT = "appr-fleet-manager-wirat"
_WIRAT_KEY = "test-key-appr-fleet-manager-wirat"
_WIRAT_HEADERS = {"Authorization": f"Bearer {_WIRAT_KEY}"}

#: The two amounts the partner's own numbers make meaningful, and neither is round
#: by accident. ฿12,000 is over every truck's ฿5,001 repair ceiling (so the judge
#: bands it `breach` and it reaches the gate) and inside วิรัช's ฿5,001-30,000 rung.
#: ฿4,500 is UNDER the ceiling, so the judge bands it `ok` and `reshape` — which
#: consumes only the breach subset — must drop it before the gate ever sees it.
_MID_BAND_THB = "12000.00"
#: truck-01's registration, the discriminator on the rendered export — the file
#: carries no case_id column, so the plate is how a human finds their own repair.
_PLATE = "80-1234 กรุงเทพมหานคร"
_SUB_CEILING_THB = "4500.00"
_APPROVE, _FULFILL = "approve", "fulfill"


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
    """Register exactly what the API lifespan registers, and make fleet active.

    The executor-factory registration is not optional: the seam resolves executors
    through the registry, and without it ``load_event_resolver`` returns ``None`` and
    the seam becomes a silent no-op — which would make every count assertion below
    pass for the wrong reason.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(
        settings,
        "api_keys",
        {
            _DIGEST: _MECHANIC,
            hashlib.sha256(_WIRAT_KEY.encode("utf-8")).hexdigest(): _WIRAT,
        },
    )


async def _open_case_with_quotes(
    client: AsyncClient,
    *,
    amounts: tuple[tuple[str, str], ...] = (
        ("ส.เจริญยนต์", "58000.00"),
        ("อู่ริมทางปากช่อง", "62000.00"),
        ("อู่ช่างเล็ก", "59500.00"),
    ),
    truck_id: str = "truck-01",
) -> tuple[str, list[str]]:
    """A real axle breakdown with garages compared. Defaults to the ฿62,000 shape."""
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": truck_id,
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทางแถวปากช่อง",
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]
    quote_ids: list[str] = []
    for vendor, amount in amounts:
        quoted = await client.post(
            f"/api/cases/{case_id}/quotes",
            data={"vendor": vendor, "amount_thb": amount},
            headers=_HEADERS,
        )
        assert quoted.status_code == 201, quoted.text
        quote_ids.append(quoted.json()["quote_id"])
    return case_id, quote_ids


async def _accept(client: AsyncClient, case_id: str, quote_id: str) -> None:
    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": quote_id, "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้"},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text


async def _hero_runs(client: AsyncClient) -> list[dict[str, Any]]:
    """The runs Tab H itself would paint, filtered to the hero procedure."""
    listed = await client.get("/runs", headers=_HEADERS)
    assert listed.status_code == 200, listed.text
    return [r for r in listed.json()["runs"] if r["procedure_id"] == _HERO]


async def _proposal_case_ids(client: AsyncClient, run_id: str) -> list[str]:
    got = await client.get(f"/runs/{run_id}", headers=_HEADERS)
    assert got.status_code == 200, got.text
    return [str(p["action_id"]) for p in got.json()["proposals"]]


async def _assert_run_is_about(client: AsyncClient, run_id: str, case_id: str) -> None:
    """The load-bearing half: this run's gate concerns the visitor's OWN case, ALONE.

    **PLAN-0113 AC-3.** Two assertions, in this order, because they fail independently
    and for different reasons:

    1. **exactly one proposal** — the scoping claim. A fleet-wide gate (3 proposals on
       this fixture) is now a defect, not the design.
    2. **and it is the firing case** — the identity claim. A run that fires on a stale
       projection produces exactly one proposal too; it is simply somebody else's.

    Neither subsumes the other, and the old ``any(...)`` reading asserted neither: it
    passed on a 3-proposal fleet-wide gate that happened to include the visitor.
    """
    proposals = await _proposal_case_ids(client, run_id)
    assert len(proposals) == 1, (
        f"run {run_id} proposes {proposals} — a scoped event-fired run gates on its "
        f"firing case ALONE (PLAN-0113 AC-3). More than one means `intake`'s "
        "`scope_by` clause is not narrowing the base read; zero means it narrowed to "
        "nothing at all."
    )
    assert case_id in proposals[0], (
        f"run {run_id} proposes {proposals} — the visitor's case {case_id} is not the "
        "one proposed. The seam must run AFTER _refresh_case_events, or the run gates "
        "on whatever the stale projection still held."
    )


async def test_accepting_a_quote_fires_a_governed_run_about_that_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-3: the whole promise, end to end through the real surfaces."""
    before = len(await _hero_runs(client_with_db))
    case_id, quotes = await _open_case_with_quotes(client_with_db)

    assert len(await _hero_runs(client_with_db)) == before, (
        "opening a case and keying quotes must fire NOTHING — a case with no accepted "
        "quote projects no governable event at all (G-4)"
    )

    await _accept(client_with_db, case_id, quotes[1])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == before + 1, "exactly one governed run per governable acceptance"
    assert runs[0]["status"] == "waiting_human", "the run parks for a human (G-12)"
    await _assert_run_is_about(client_with_db, runs[0]["run_id"], case_id)


async def test_re_accepting_the_same_quote_does_not_mint_a_second_run(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-2(i) — SD-2(b): the same quote re-accepted is not a material change.

    This is the assertion that fails if the key is ever moved to ``accepted_id``:
    ``accept_quote`` mints a fresh ``accepted-{uuid4}`` per call, so a double-click
    would mint a second run.
    """
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    await _accept(client_with_db, case_id, quotes[1])
    after_first = len(await _hero_runs(client_with_db))

    await _accept(client_with_db, case_id, quotes[1])

    assert len(await _hero_runs(client_with_db)) == after_first, (
        "re-accepting the SAME quote minted a second run — entity_ids must carry the "
        "quote's identity, never the per-call accepted_id (G-14)"
    )


async def test_accepting_a_different_quote_mints_one_more_run(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-2(ii) — SD-2(b) as ruled: a materially different acceptance re-fires.

    Load-bearing beyond the key: the first run is parked ``waiting_human`` by the time
    this fires, so this also pins that the bridge's SD-P4 backpressure is opted out of
    for this seam. With the default it returns SKIPPED_IN_FLIGHT and the count stays 1.
    """
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    await _accept(client_with_db, case_id, quotes[1])
    after_first = len(await _hero_runs(client_with_db))

    await _accept(client_with_db, case_id, quotes[2])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == after_first + 1, (
        "accepting a DIFFERENT quote must mint a new run (SD-2(b)); if this reads "
        "equal, either the key lost the quote id or SD-P4 skipped the fire"
    )
    for run in runs:
        await _assert_run_is_about(client_with_db, run["run_id"], case_id)


async def test_the_seeded_demo_run_does_not_swallow_a_visitor_acceptance(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The published-profile shape: a parked demo run must not block the visitor.

    ``OCT_DEMO_SEED_OPERATE=true`` on fleet's published profile
    (``deploy/published/oct-fleet-maintenance/published.env``), and the seed parks a
    ``governed_repair_approval`` run at ``waiting_human`` by construction — the seed
    RAISES if it does not. Under the bridge's stock SD-P4 backpressure that parked run
    makes every visitor acceptance a silent ``SKIPPED_IN_FLIGHT``, which is the whole
    promise of this PLAN failing with nothing to see.
    """
    from verticals.fleet_maintenance.operate_seed import (
        seed_demo_repair_case,
        seed_repair_gate_waiting_human_run,
    )

    await seed_demo_repair_case(db_session)
    await case_projection.refresh(db_session)
    seeded = await seed_repair_gate_waiting_human_run(db_session)
    # Defensive, and measured NON-discriminating (s252): the seed itself fails closed —
    # `seed_repair_gate_waiting_human_run` raises ProcedureError when the gate does not
    # park (operate_seed.py:754) — so any change that would falsify this line kills the
    # test at the CALL above instead. Kept as a readable statement of the premise, not
    # counted as a witnessed claim; see the Step-3 battery's exemption for it.
    assert seeded.run.status == "waiting_human", "the premise: a parked run is in the way"
    before = len(await _hero_runs(client_with_db))

    case_id, quotes = await _open_case_with_quotes(client_with_db)
    await _accept(client_with_db, case_id, quotes[1])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == before + 1, (
        "the visitor's acceptance fired nothing while the seeded demo run was parked — "
        "SD-P4 backpressure swallowed it (PLAN-0112 Step 3, skip_if_in_flight=False)"
    )
    fired = next(r for r in runs if r["run_id"] != seeded.run.run_id)
    await _assert_run_is_about(client_with_db, fired["run_id"], case_id)


# --- Step 4 ------------------------------------------------------------------
# AC-2's remaining clause, AC-3's consumer half, and AC-4's dead-end invariant.
# The seam these exercise shipped in #1248; nothing below re-tests the firing count
# on its own — each asserts something the count cannot see.


async def _resolve(client: AsyncClient, run_id: str, step: str, decisions: dict[str, str]) -> str:
    """Resolve one gate through the REAL route as a keyed approver.

    The deciding principal comes from the bearer key and never from the body
    (`GateResolveRequest`'s own contract), which is what makes this a real SoD check
    rather than a self-declared one.
    """
    got = await client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": step, "decisions": decisions},
        headers=_WIRAT_HEADERS,
    )
    assert got.status_code == 200, got.text
    return str(got.json()["run_status"])


async def _decisions_for(
    client: AsyncClient, run_id: str, verdict: str = "approve"
) -> dict[str, str]:
    got = await client.get(f"/runs/{run_id}", headers=_HEADERS)
    assert got.status_code == 200, got.text
    return {str(p["action_id"]): verdict for p in got.json()["proposals"]}


async def _fire_sub_ceiling_with_a_breaching_control(
    client: AsyncClient, db_session: AsyncSession
) -> str:
    """Seed the demo, fire a BREACHING control run, then fire the sub-ceiling one.

    🔴 The control is not decoration. Every claim below is about a proposal list being
    EMPTY, and an empty list is what a `scope_by` that matches nothing *ever* would
    also produce — the exact defect scoping can introduce. So the same fixtures, the
    same seam and the same principals must first be shown producing a proposal.

    Returns the sub-ceiling run's ``run_id``.
    """
    from verticals.fleet_maintenance.operate_seed import seed_demo_repair_case

    await seed_demo_repair_case(db_session)
    await case_projection.refresh(db_session)

    control_case, control_quotes = await _open_case_with_quotes(
        client, amounts=(("อู่ริมทางปากช่อง", _MID_BAND_THB),)
    )
    await _accept(client, control_case, control_quotes[0])
    control_runs = await _hero_runs(client)
    assert len(control_runs) == 1, "control: one breaching acceptance, one run"
    await _assert_run_is_about(client, control_runs[0]["run_id"], control_case)

    case_id, quotes = await _open_case_with_quotes(client, amounts=(("อู่ช่างเล็ก", _SUB_CEILING_THB),))
    await _accept(client, case_id, quotes[0])
    runs = await _hero_runs(client)
    assert len(runs) == 2, "the sub-ceiling acceptance fires too — the loop DID judge it"
    return str(next(r for r in runs if r["run_id"] != control_runs[0]["run_id"])["run_id"])


async def test_a_sub_ceiling_acceptance_reaches_the_gate_with_no_proposals(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """PLAN-0113 AC-3's sub-ceiling observable — as MEASURED, which is not as predicted.

    AC-3 predicted "a sub-ceiling acceptance fires a run that **completes with no
    gate**". Measured s252 on this very suite, that is FALSE, and the divergence is
    recorded here rather than absorbed: the run fires, `judge` bands the visitor's own
    ฿4,500 case `ok`, `reshape` (`where: {verdict: breach}`) drops it — and the run
    **still parks at `approve` with an EMPTY proposal list**. `_suspends`
    (`orchestrator.py:632-644`) is purely structural: a `gated` action suspends on its
    KIND, never on whether its input set holds anything.

    Before PLAN-0113 this state was unreachable — `intake` swept the fleet and the
    fixture always carried a breaching truck, so every gate had at least one proposal.
    Scoping made the empty gate reachable for the first time. What that costs the
    visitor is asserted separately, in the tripwire test below.

    The claim here is the empty proposal list; its positive control is the breaching
    run fired from the same fixtures by the helper.
    """
    run_id = await _fire_sub_ceiling_with_a_breaching_control(client_with_db, db_session)

    assert await _proposal_case_ids(client_with_db, run_id) == [], (
        f"the ฿{_SUB_CEILING_THB} case is under every truck's ฿5,001 ceiling, so the "
        "judge bands it `ok` and reshape drops it — and under PLAN-0113 scoping no "
        "other truck's breach rides along, so the gate must hold NOTHING"
    )


async def test_the_empty_gate_is_acknowledged_and_the_run_reaches_completed(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """PLAN-0114 AC-1 / AC-2(a) / AC-4's resolve half — the dead end, closed.

    This test was, until PLAN-0114 Step 2, the deliberate tripwire
    `test_an_empty_gate_cannot_be_resolved_so_the_run_is_a_dead_end`: it asserted the
    COST of the empty gate — a sub-ceiling acceptance parking in Tab H with nothing
    anyone could resolve. PLAN-0113 SD-3 was ruled (b) (Cray, typed, s252): such a run
    must reach `completed`, because a completed run recording *"checked — ฿4,500 is
    inside the head mechanic's own authority"* is a better governance artifact than a
    stuck one. The tripwire named this as the site that must change when the ruling
    landed. It landed; this is that change.

    Four claims, in the order they fail independently:

    1. **resolve is UNCHANGED** — `/gate/resolve` on the empty gate still answers the
       same `no proposed actions to resolve`. Continue is a NEW exit, not a changed
       resolve; if this reddens, PLAN-0114's blast radius escaped its bound (AC-4).
    2. **continue is not a resolve bypass** — the breaching control run, whose gate
       holds a REAL proposal, is REFUSED. Asserted on the chokepoint's own detail
       string, never the bare status code: `resume_run` carries an independent second
       guard that refuses the same case with a different message and the same 409, so
       a code-only assertion would stay green with the chokepoint's guard deleted
       (AC-2a — the security boundary of the whole seam, since SD-3 admits any
       authenticated human).
    3. **the run reaches `completed`** — the ruling's actual outcome (AC-1).
    4. **it takes TWO acknowledgments, not one** — MEASURED, not assumed, and
       asserted as a list so the count cannot drift silently. `_suspends`
       (`orchestrator.py:632-644`) is purely structural: the hero spine is
       `request -> approve -> fulfill` and `fulfill` is `autonomy: gated` too, so
       acknowledging `approve` parks the run again on the very next step. This is the
       same G-12 shape :func:`test_the_full_walk_both_gates_the_link_row_and_the_case_surface`
       records for the resolve path — a test that stopped after one continue would
       report a closed dead end while the run sat in the visitor's queue.
    """
    run_id = await _fire_sub_ceiling_with_a_breaching_control(client_with_db, db_session)
    # The helper's breaching control run, recovered by exclusion — its gate holds a real
    # proposal, which is what makes claim 2 a live refusal rather than a hypothetical.
    control_run_id = next(
        r["run_id"] for r in await _hero_runs(client_with_db) if r["run_id"] != run_id
    )

    refused = await client_with_db.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _APPROVE, "decisions": {}},
        headers=_WIRAT_HEADERS,
    )
    # 🔴 The STATUS CODE alone does not discriminate. Measured s252: 409 is also what a
    # gate WITH proposals answers when `decisions` omits one — so `== 409` passes on a
    # perfectly healthy non-empty gate and asserts nothing about emptiness. The detail
    # string names the mechanism (`action_step.py:832`), and that is the claim.
    assert "no proposed actions to resolve" in refused.text, (
        "PLAN-0114 leaves resolve UNTOUCHED — an empty gate must still be unresolvable, "
        f"and the new exit is /continue. Got {refused.status_code} {refused.text}"
    )

    bypass = await client_with_db.post(
        f"/runs/{control_run_id}/continue",
        json={"step_id": _APPROVE},
        headers=_WIRAT_HEADERS,
    )
    assert "holds decidable proposals" in bypass.text, (
        "the continue seam must refuse a gate carrying a REAL proposal with its OWN "
        "message — `resume_run`'s second guard answers the same 409 with a different "
        f"one, so this string IS the claim. Got {bypass.status_code} {bypass.text}"
    )

    acknowledged: list[str] = []
    step, body = _APPROVE, {}
    for _ in range(4):  # bounded: the hero spine carries two gates, never four
        ack = await client_with_db.post(
            f"/runs/{run_id}/continue",
            json={"step_id": step},
            headers=_WIRAT_HEADERS,
        )
        assert ack.status_code == 200, f"acknowledging '{step}': {ack.text}"
        body = ack.json()
        acknowledged.append(step)
        if body["run_status"] != "waiting_human":
            break
        step = body["suspended_step"]
        assert step is not None and step not in acknowledged, (
            f"a waiting_human continuation must name a NEW gate; got {step!r} after "
            f"{acknowledged}"
        )
        # PLAN-0114 SD-4: the walk's stop rule reads THIS field, so it is load-bearing
        # for the UI, not decoration. Positive control for "empty" is shared rather than
        # local: `proposals` is populated by the same `_proposals()` that fills
        # RunProcedureResponse, which `test_runs_endpoints.py::
        # test_http_only_run_suspend_resolve_resume` exercises NON-empty (`== 1`). No
        # shipped spine lands a /continue on a gate that holds a proposal, so the
        # non-empty case is inexpressible here — recorded, not silently skipped.
        assert body["proposals"] == [], (
            "the response must report what the NEW gate holds, so the caller can tell "
            f"an acknowledgment from a decision without a second GET; got {body['proposals']}"
        )
    else:  # pragma: no cover — the bound is a non-termination guard, not a path
        pytest.fail(f"the run never settled after acknowledging {acknowledged}")

    assert body["run_status"] == "completed", (
        "PLAN-0113 SD-3 ruled (b): a gate holding nothing decidable must reach "
        f"completed, not sit unresolvable. Got {body['run_status']}"
    )
    assert acknowledged == [_APPROVE, _FULFILL], (
        "MEASURED: the hero spine's SECOND gate is `autonomy: gated` too and "
        "`_suspends` never inspects the input set, so the empty run parks again at "
        f"`fulfill`. If this list changed, the spine did. Got {acknowledged}"
    )


async def test_the_full_walk_both_gates_the_link_row_and_the_case_surface(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-3's consumer half — and it takes TWO resolves, not one (G-12).

    `governed_repair_approval` is a `request -> approve -> fulfill` spine: resolving
    `approve` does not complete the run, it parks it again at the gated `fulfill`.
    A test that stopped after one resolve would report a delivered promise while the
    run sat in the visitor's queue.

    **The outcome surface is the link row and the month-end export — Cray's ruling
    (a), s244, and it is asserted rather than assumed.** AC-3's wording ("the case
    list / evidence surfaces showing the outcome") pointed at two surfaces that
    deliberately carry no verdict: the case row stops at the accepted quote, and the
    evidence pack is verdict-free BY DESIGN — "a case's sourcing evidence as FACTS —
    deliberately not a verdict", because the sourcing threshold can move and a
    verdict frozen beside the facts would rot into a confident wrong answer. The
    decision therefore lives in the row `link_resolved_cases` writes, and the
    operator-facing surface that renders it is the repair-spend export, which is a
    case list carrying ผู้อนุมัติ and วันที่อนุมัติ. Both are read below — the
    structured export for the case↔run↔approver tie, then the real CSV endpoint,
    because a consumer that cannot render it has not shown the outcome to anyone.

    No `POST /procedures/{id}/run` anywhere — that is the clause separating this
    test from `test_visitor_case_to_monitor_scenario.py`'s older shape.
    """
    case_id, quotes = await _open_case_with_quotes(
        client_with_db, amounts=(("อู่ริมทางปากช่อง", _MID_BAND_THB),)
    )
    await _accept(client_with_db, case_id, quotes[0])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == 1, "one acceptance, one run"
    run_id = runs[0]["run_id"]
    await _assert_run_is_about(client_with_db, run_id, case_id)

    after_approve = await _resolve(
        client_with_db, run_id, _APPROVE, await _decisions_for(client_with_db, run_id)
    )
    assert after_approve == "waiting_human", (
        "resolving `approve` must NOT complete the run — it parks again at the gated "
        "`fulfill` (G-12). A one-resolve test would call this done while it is not"
    )

    after_fulfill = await _resolve(
        client_with_db, run_id, _FULFILL, await _decisions_for(client_with_db, run_id)
    )
    assert after_fulfill == "completed", "the second resolve is what finishes the walk"

    links = list(
        (
            await db_session.execute(
                sa.select(RepairCaseRunLink).where(RepairCaseRunLink.case_id == case_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(links) == 1, f"one decision on this case, one link row — got {len(links)}"
    assert links[0].run_id == run_id
    assert links[0].step_id == _APPROVE
    assert links[0].outcome == "approved"
    assert links[0].three_quote_basis, (
        "the row must carry the sourcing basis the gate ACTUALLY SAW, read from the "
        "engine's own artifact rather than recomputed"
    )
    assert gate_hooks.failures() == [], "the hook is fail-soft; a swallowed error must show here"

    served = await client_with_db.get(f"/api/cases/{case_id}", headers=_HEADERS)
    assert served.status_code == 200, served.text
    assert served.json()["case_id"] == case_id

    # --- the outcome surface (Cray's ruling (a), s244) ------------------------
    now = datetime.now(UTC)
    export = await load_monthly_export(db_session, year=now.year, month=now.month, now=now)
    mine = [r for r in export.rows if r.case_id == case_id]
    assert len(mine) == 1, f"one governed case, one export row — got {len(mine)}"
    assert mine[0].governed is True, "the case must read as GOVERNED, not as escaped money"
    assert mine[0].run_id == run_id, "the row must name the run that actually decided it"
    assert mine[0].outcome == "approved"
    assert mine[0].approver == _WIRAT, (
        "the surface must name the human who resolved the gate, read from the audit "
        f"row rather than the request body — got {mine[0].approver!r}"
    )

    rendered = await client_with_db.get(
        f"/api/exports/repair-spend/{now.year}/{now.month}.csv", headers=_HEADERS
    )
    assert rendered.status_code == 200, rendered.text
    csv_rows = list(csv.DictReader(io.StringIO(rendered.content.decode(CSV_ENCODING))))
    assert len(csv_rows) == len(export.rows), (
        "the rendered file and the structured read must agree on how many repairs the "
        f"month holds — got {len(csv_rows)} vs {len(export.rows)}"
    )
    # Identified by plate, not by count. This was written when the gate was a
    # fleet-wide population scan (G-6, SD-4(a)) and the walk legitimately decided other
    # cases too. PLAN-0113 scoped the run to its firing case, so the population claim
    # would now hold — but the discrimination is kept deliberately: the plate is what a
    # HUMAN uses to find their own repair on this file (the export carries no case_id
    # column), and asserting a count here would test the population instead of testing
    # that this outcome was shown to anyone. The population is asserted at the gate,
    # by `_assert_run_is_about`, which is where it belongs.
    ours = [r for r in csv_rows if r["ทะเบียนรถ"] == _PLATE]
    assert len(ours) == 1, f"this case's repair must appear on the rendered file — got {ours}"
    assert ours[0]["ผู้อนุมัติ"] == _WIRAT, (
        "the rendered row must name the human who resolved the gate — a decision only "
        f"the database knows has not been SHOWN to anyone; got {ours[0]}"
    )


async def test_a_visitor_fired_run_is_never_a_dead_end(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-4: every run a visitor-reachable path can fire has a gate a declared
    approver can actually resolve.

    ⚠️ **Scope note (PLAN-0113, s252; refreshed PLAN-0114 Step 2, s256).** The name
    over-claims: this covers the PRINCIPAL dead end (a run nobody holds the role to
    resolve), on a MID-BAND amount whose gate is never empty. The second dead-end
    route — a sub-ceiling acceptance whose gate holds zero proposals — was OPEN as
    PLAN-0113 SD-3 when this note was written; it is now RULED (b) and **closed** by
    PLAN-0114's acknowledge-and-continue seam, asserted by
    :func:`test_the_empty_gate_is_acknowledged_and_the_run_reaches_completed`.

    G-7 measured the failure this excludes, and it is worse than an ungoverned run:
    a `None`-principal fire mints a run that starts, parks, appears in Tab H, and can
    NEVER be resolved by anyone — `check_principal_sod` raises `UNRESOLVED_PRINCIPAL`
    on every attempt. The ruled SD-5(b) mechanism supplies the shape that prevents it:
    `event_trigger.owning_person_id` is recorded as the SoD requester at fire time.

    Three things are asserted because they fail independently — the requester being
    recorded, the actor being the SERVICE principal (not a human), and the resolve
    actually succeeding for the declared approver of this band.
    """
    case_id, quotes = await _open_case_with_quotes(
        client_with_db, amounts=(("อู่ริมทางปากช่อง", _MID_BAND_THB),)
    )
    await _accept(client_with_db, case_id, quotes[0])
    run_id = (await _hero_runs(client_with_db))[0]["run_id"]

    loaded = await load_run(db_session, run_id)
    assert loaded is not None
    assert loaded.run.step_principals is not None, (
        "a run with no step_principals map never carried SoD — the gate would then "
        "skip the live check instead of enforcing it (ADR-0026 D4)"
    )
    assert loaded.run.step_principals.get("intake") == _MECHANIC, (
        "the declared owning person must be recorded as the SoD requester at fire "
        f"time (G-9 shape) — got {loaded.run.step_principals}"
    )

    rows = list(
        (
            await db_session.execute(
                sa.select(AuditLog).where(
                    AuditLog.run_id == run_id, AuditLog.action == "run_started"
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1, "one run, one run_started row"
    payload = rows[0].payload or {}
    assert payload.get("actor_kind") == "service", (
        "a visitor-fired run acts as the agent's SERVICE principal, never as the "
        f"visitor — got {payload.get('actor_kind')!r}"
    )
    assert (
        payload.get("on_behalf_of", {}).get("owning_person_id") == _MECHANIC
    ), "the SP-5 on-behalf-of lineage names the declared human the service acts for"

    status = await _resolve(
        client_with_db, run_id, _APPROVE, await _decisions_for(client_with_db, run_id)
    )
    assert status == "waiting_human", (
        f"the declared approver for the ฿{_MID_BAND_THB} rung must be able to resolve "
        "this gate — a 403 here is the dead-end G-7 describes"
    )
