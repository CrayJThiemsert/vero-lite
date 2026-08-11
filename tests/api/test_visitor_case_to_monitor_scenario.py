"""Tab I → Tab H with the seed present, and what the tamper-evident chain holds.

PLAN-0103 **AC-8 clause 2** — *"the visitor path still closes end-to-end: a case
opened via Tab I's backend appears in H's list"* — plus the **empirical** half of
ADR-0037 **D2.7**: *does visitor-typed case text reach the tamper-evident audit
chain?*

**Why a third module beside two that already look like this one.** Neither sibling
covers what clause 2 actually claims:

* ``test_case_event_path_scenario.py`` drives the case onto the event stream and into
  a parked run — but it asserts on the *fire* response and never on ``GET /runs``,
  which is what Tab H reads; and it runs with **no seed present**.
* ``test_run_link_scenario.py`` drives the *resolution* and the link row — it never
  reads the Monitor either, and never touches ``audit_log``.

**The trap this module is shaped around (PLAN-0103 Step 7, PR #1122).** Fleet now
seeds ONE ``waiting_human`` run at boot, so Tab H is non-empty *before any visitor
arrives*. "Open a case, then assert H has a run" would therefore pass **with the case
removed entirely** — the seed alone satisfies it. Every assertion here is a DELTA
against a baseline measured after the seed and before the visitor, and the new run is
identified by the visitor's own ``case_id`` read through ``run_link.case_id_of``, the
same function production uses.

**D2.7, measured rather than read.** Session 221 answered D2.7 by reading two of the
fourteen ``append_audit`` call sites and concluded the chain holds no case text. This
module upgrades that code read to a measurement: it asserts over EVERY ``audit_log``
row the run produced, so a write site nobody thought to read is covered — and so is
one that does not exist yet. Two independent oracles (Cray, typed, s222):

1. a **sentinel** buried in the visitor's own typed description, asserted absent from
   every payload — this survives a leak that truncated or reshaped the text, which a
   whole-string search would not;
2. a **structural allowlist** of the top-level payload keys each audit action may
   carry, where an unknown action OR an unknown key is a loud failure — this catches
   a NEW carrier of text at the moment it is introduced, rather than when someone
   next thinks to look.

The sentinel is **positively controlled**: it is asserted PRESENT in the ingested
event first. Without that, "absent from the chain" would also pass in the world where
the visitor's text never reached the run at all — which is the same green for the
opposite reason, and is exactly the vacuity this PLAN keeps catching.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.audit_log import AuditLog
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.action_step import (
    WaiverInvocation,
    ratify_gated_step,
    resolve_gated_step,
)
from services.engine.procedures.persistence import load_run
from services.engine.procedures.spec import Person, load_procedures
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.case_events import event_id_for
from verticals.fleet_maintenance.operate_seed import (
    DEMO_RUN_ID,
    seed_repair_gate_waiting_human_run,
)
from verticals.fleet_maintenance.run_link import case_id_of

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"

#: ต้อม opens the case and fires the round — the REQUESTER half of the hero's
#: separation-of-duties constraint, recorded by the endpoint from the authenticated
#: identity and never from the request body.
_MECHANIC = "req-mechanic-tom"
#: เฮีย approves. ฿62,000 routes to the owner tier under the partner's real ladder —
#: established by ``test_run_link_scenario`` against this same case shape, not assumed
#: here. A DISTINCT human from the requester is what keeps SoD satisfied on its merits.
_OWNER = "appr-owner"

_MECHANIC_KEY = "test-key-req-mechanic-tom"
_OWNER_KEY = "test-key-appr-owner"
_HEADERS = {"Authorization": f"Bearer {_MECHANIC_KEY}"}
_OWNER_HEADERS = {"Authorization": f"Bearer {_OWNER_KEY}"}


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


#: Buried inside what the visitor types. Distinctive enough that finding it anywhere
#: downstream is proof of provenance rather than coincidence, and short enough to
#: survive a truncation that a whole-description search would miss.
#: TWO of them, at opposite ends, and the position is the point. A single tail
#: sentinel is blind to a leak that keeps the HEAD of the description and drops the
#: rest — a truncating carrier ("first 80 chars of the trace") would evade it while
#: putting the visitor's opening words in the immutable record. Bracketing catches a
#: truncation from either end, and any payload holding the description VERBATIM.
#:
#: The hole it does NOT close, named rather than argued away: a **middle-slice**
#: carrier — one that drops both bracketed ends and keeps the Thai in between — lands
#: inside an already-allowed key and is invisible to BOTH oracles. That is a real leak
#: of the visitor's text, not a degenerate case. It is left open because closing it
#: needs a different instrument (a similarity check, or a payload schema that forbids
#: free-form strings outright), not a third sentinel — n sentinels are always evaded
#: by a slice that misses all n. Whether the residual risk is acceptable is a
#: controller judgment; recorded here so it is a decision rather than an oversight.
#: (An earlier revision of this comment claimed such a leak "is no longer a leak of
#: the visitor's text". That was false, and is corrected in place: a test that argues
#: its own blind spot out of existence is worse than one that has the blind spot.)
_SENTINEL_HEAD = "ZQ7"
_SENTINEL_TAIL = "WM8"
_SENTINELS = (_SENTINEL_HEAD, _SENTINEL_TAIL)
_VISITOR_TEXT = (
    f"({_SENTINEL_HEAD}) เพลาขาดกลางทางแถวปากช่อง "
    f"มีเสียงดังใต้ท้องรถมาหลายวันก่อนหน้านี้ ({_SENTINEL_TAIL})"
)

#: Two more sentinels for the emergency path, which is the one place a HUMAN's free
#: text is DESIGNED to land in the chain: ``WaiverInvocation.justification``'s own
#: docstring says "It is stored in the durable audit chain", and the ratification row
#: carries an optional ``note``. Distinct tokens so the third test can tell apart
#: "the recorder's words are in there" (true, and intended) from "the visitor's words
#: are in there" (the thing D2.7 asks about, and false on every path measured here).
_WAIVER_SENTINEL = "RC4"
_NOTE_SENTINEL = "SG2"
_WAIVER_TEXT = f"รถจอดขวางทางหลวงอยู่ โทรหาเฮียแล้วเคาะมาว่าให้ซ่อมเลย ({_WAIVER_SENTINEL})"
_RATIFY_NOTE = f"เซ็นย้อนหลังตามที่เคาะทางโทรศัพท์เมื่อวันเสาร์ ({_NOTE_SENTINEL})"

#: What each audit action is allowed to carry at the TOP LEVEL of its payload, read
#: off the write sites rather than guessed:
#: ``persistence.py`` (``run_started``, ``run_resumed``) and ``action_step.py``
#: (``gate_decision`` — including the six extra keys the provisional/waiver branch
#: adds — and ``handler_receipt``).
#:
#: This is the tripwire half of the D2.7 oracle. A new key here means a new thing the
#: immutable record carries, and the RoPA has to be able to describe it; reddening at
#: the moment it is added is the whole point, so WIDEN THIS DELIBERATELY — never to
#: make a red test green.
_ALLOWED_PAYLOAD_KEYS: dict[str, frozenset[str]] = {
    "run_started": frozenset({"procedure_id", "agent_id", "actor_kind", "on_behalf_of"}),
    "gate_decision": frozenset(
        {
            "decisions",
            "actor_kind",
            "kind",
            "justification",
            "attested_approver_id",
            "recorded_by",
            "ratify_by_role",
            "ratification_window_days",
        }
    ),
    "handler_receipt": frozenset({"action_id", "receipt", "actor_kind"}),
    "run_resumed": frozenset({"final_status", "actor_kind"}),
    "gate_ratified": frozenset(
        {
            "actor_kind",
            "attested_approver_id",
            "recorded_by",
            "ratify_by_role",
            "due_at",
            "was_overdue",
            "justification_ref",
            "note",
        }
    ),
}


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    """Both caches and the hook registry are process-global; a leak makes a later test lie."""
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register EXACTLY what the API lifespan registers, with authn ON.

    Authn is load-bearing rather than incidental: ``POST /procedures/{id}/run``
    persists ``step_principals`` from the server-resolved principal, so an
    unauthenticated fire produces a run whose gate can never be approved — a 200 that
    leads nowhere. Two keys are registered because the SoD constraint needs two
    distinct humans, and both are declared fleet principals, so they resolve against
    the real spec with no ``_principal_index`` monkeypatch.
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
        {_digest(_MECHANIC_KEY): _MECHANIC, _digest(_OWNER_KEY): _OWNER},
    )


async def _monitor(client: AsyncClient) -> dict[str, Any]:
    """Tab H's backing read, through the real route.

    ``GET /runs`` and not the fire response: the claim under test is that the case
    appears in the MONITOR, and a run object returned by the endpoint that created it
    proves only that the endpoint returned it.
    """
    response = await client.get("/runs", headers=_HEADERS)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def _visitor_opens_a_case(client: AsyncClient) -> str:
    """Tab I's backend, exactly as a visitor drives it — open, quote, agree."""
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": _VISITOR_TEXT,
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]

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


async def _parked_proposals(session: AsyncSession, run_id: str) -> list[dict[str, Any]]:
    """The proposals sitting at the parked gate, read off the persisted run."""
    loaded = await load_run(session, run_id)
    target = next(sr for sr in loaded.step_results if sr.step_id == _GATE_STEP)
    artifact = target.artifact
    assert artifact is not None, "the parked gate must have produced an artifact"
    return list(artifact["output_set"])


def _ingested_event(proposal: dict[str, Any], case_id: str) -> dict[str, Any] | None:
    """The event dict the engine ingested for ``case_id``, walked from the trace.

    Walked here rather than imported from ``run_link``'s private helper so the test
    reads the same structure production reads without depending on its internals —
    and so a change to that structure surfaces HERE as a failed walk rather than as a
    silently-None answer.
    """
    action = proposal.get("action")
    if not isinstance(action, dict):
        return None
    for step in action.get("reasoning_trace") or []:
        if not isinstance(step, dict) or step.get("kind") != "ontology_query":
            continue
        detail = step.get("detail")
        if not isinstance(detail, dict):
            continue
        event = detail.get("event")
        if isinstance(event, dict) and event.get("case_id") == case_id:
            return event
    return None


async def _audit_rows(session: AsyncSession, run_id: str) -> list[AuditLog]:
    rows = await session.execute(
        sa.select(AuditLog).where(AuditLog.run_id == run_id).order_by(AuditLog.audit_id)
    )
    return list(rows.scalars())


def _dumped(payload: dict[str, Any] | None) -> str:
    """The whole payload as text — nested values included, at any depth.

    ``ensure_ascii=False`` is for the failure OUTPUT, not for the oracle: the
    sentinels are ASCII and would survive escaping either way, but a leak's failure
    message has to show the Thai a human can recognise rather than a wall of ``\\uXXXX``.
    (An earlier version of this docstring claimed the flag was load-bearing for the
    assertion itself. It is not — corrected rather than quietly dropped, because a
    test that overstates why it works invites the next reader to trust the wrong part.)
    """
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def _leaked(payload: dict[str, Any] | None) -> list[str]:
    """Which of the visitor's sentinels this payload carries — [] when none.

    Returns rather than asserts so the caller can name WHICH end of the description
    escaped, which is the difference between "a carrier folded the whole trace in" and
    "a carrier truncated it" — different bugs with different erasure consequences.
    """
    dumped = _dumped(payload)
    return [s for s in _SENTINELS if s in dumped]


async def test_a_visitor_case_lands_in_the_monitor_beside_the_seed_not_instead_of_it(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-8 clause 2, asserted as a delta so the seed cannot answer for the visitor.

    The order is the whole design: seed first, MEASURE the Monitor, then let the
    visitor in. A baseline taken before the seed would let the seed's own run satisfy
    the increase; a baseline taken after the visitor would measure nothing at all.

    What makes the new row provably the visitor's, rather than merely new: its parked
    proposal's grounding trace carries the visitor's ``case_id``, read with
    ``run_link.case_id_of`` — the same function the production hook uses to decide
    which case a decision belongs to.
    """
    seeded = await seed_repair_gate_waiting_human_run(db_session)
    assert seeded.run.run_id == DEMO_RUN_ID

    baseline = await _monitor(client_with_db)
    assert baseline["waiting_human_count"] == 1, (
        "Step 7's seed must be the ONLY thing parked before the visitor arrives — if "
        "this is 0 the seed did not land and the delta below would prove nothing; if "
        "it is >1 something else is parked and the delta is not attributable"
    )
    baseline_ids = {r["run_id"] for r in baseline["runs"]}
    assert DEMO_RUN_ID in baseline_ids

    case_id = await _visitor_opens_a_case(client_with_db)

    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    run_id: str = fired.json()["run_id"]

    after = await _monitor(client_with_db)
    assert after["waiting_human_count"] == baseline["waiting_human_count"] + 1, (
        "the visitor's case must ADD a waiting run — an assertion that H is merely "
        "non-empty passes with the visitor removed entirely, because the seed is there"
    )
    new_ids = {r["run_id"] for r in after["runs"]} - baseline_ids
    assert new_ids == {run_id}, "exactly one new run, and it is the one the visitor fired"
    assert DEMO_RUN_ID in {r["run_id"] for r in after["runs"]}, (
        "beside the seed, not instead of it — a visitor run that displaced the seed "
        "would leave the next visitor's first paint empty again"
    )

    # --- the TIE: this parked run is provably THIS case's ----------------------
    proposals = await _parked_proposals(db_session, run_id)
    linked = {case_id_of(p) for p in proposals}
    assert case_id in linked, (
        "the parked gate must be about the REAL case — a run that merely appeared "
        "alongside it is not the visitor watching their own case get governed"
    )
    ours = next(p for p in proposals if case_id_of(p) == case_id)
    assert ours["action_id"] == f"action-{event_id_for(case_id)}", (
        "the action id is derived from the case's own event id — this is the same "
        "derivation the audit chain relies on to name the case (D2.7)"
    )


async def test_the_chain_names_the_case_without_holding_what_the_visitor_typed(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """ADR-0037 D2.7, empirical: erasing case text breaks no hash, because the chain
    never held it — but the ``case_id`` is in there and cannot be erased.

    This is the assertion the RoPA needs, and it is a permanent tripwire rather than a
    one-off reading: if anyone later folds the reasoning trace, the event dict, or the
    case description into an audit payload, the sentinel scan reddens; if anyone adds
    a NEW field or a new audit action to a payload this run produces, the allowlist
    reddens. Both fire at the moment of the change, not at the next compliance review.

    Both halves are asserted over EVERY row the run produced — not over a chosen
    subset of write sites, which is what made the session-221 code read a claim about
    two of fourteen call sites rather than a measurement.
    """
    await seed_repair_gate_waiting_human_run(db_session)
    case_id = await _visitor_opens_a_case(client_with_db)

    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    run_id: str = fired.json()["run_id"]

    # --- positive control: the sentinel DID travel this far --------------------
    proposals = await _parked_proposals(db_session, run_id)
    ours = next(p for p in proposals if case_id_of(p) == case_id)
    event = _ingested_event(ours, case_id)
    assert event is not None, "the grounding trace must carry the case's ingested event"
    assert [s for s in _SENTINELS if s in str(event["description"])] == list(_SENTINELS), (
        "BOTH of the visitor's sentinels must be IN the run's reasoning trace — without "
        "this the absence asserted below would also hold in the world where the text "
        "never arrived, which is the same green for the opposite reason; and a control "
        "that checked only one end would leave that end's oracle unproven"
    )

    # --- the human decides, through the real route -----------------------------
    decisions = {
        str(p["action_id"]): ("approve" if case_id_of(p) == case_id else "reject")
        for p in proposals
    }
    assert len(decisions) >= 2, (
        "the fixture's own breach must ride along — the gate refuses a partial "
        "resolution, and a single-proposal round would not exercise that"
    )
    resolved = await client_with_db.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATE_STEP, "decisions": decisions},
        headers=_OWNER_HEADERS,
    )
    assert resolved.status_code == 200, resolved.text

    # --- the measurement -------------------------------------------------------
    rows = await _audit_rows(db_session, run_id)
    assert rows, "no audit rows means the absence assertions below are vacuous"
    actions = {row.action for row in rows}
    assert actions == {"run_started", "gate_decision", "handler_receipt", "run_resumed"}, (
        f"unexpected audit actions for a resolved run: {sorted(actions)} — a new kind "
        "of row is a new thing the immutable record carries, and D2.7's answer does "
        "not automatically extend to it"
    )

    for row in rows:
        assert _leaked(row.payload) == [], (
            f"the visitor's typed text reached the tamper-evident chain via the "
            f"{row.action!r} payload (sentinels seen: {_leaked(row.payload)}) — this "
            f"INVERTS D2.7's answer, and the DSR path for a repair case is no longer "
            f"the same shape as the prompt log's"
        )
        allowed = _ALLOWED_PAYLOAD_KEYS.get(row.action)
        assert allowed is not None, f"no allowlist declared for audit action {row.action!r}"
        assert set(row.payload or {}) <= allowed, (
            f"{row.action!r} payload grew a key the RoPA has not described: "
            f"{sorted(set(row.payload or {}) - allowed)}"
        )

    # --- and the other half: the case IS named, permanently --------------------
    naming = [row for row in rows if case_id in _dumped(row.payload)]
    assert naming, (
        "the chain must identify WHICH case was decided — if it does not, the audit "
        "trail cannot answer the partner's per-baht question at all"
    )
    assert {row.action for row in naming} >= {"gate_decision"}, (
        "the gate decision is where the case is named: its `decisions` map is keyed by "
        f"action ids of the form action-{event_id_for('<case-id>')}"
    )
    assert all(_leaked(row.payload) == [] for row in naming), (
        "naming the case must not mean quoting it — this is the exact residue D2.7 "
        "leaves the controller: an opaque case id in an immutable record, and nothing "
        "the visitor wrote"
    )


def _person(person_id: str) -> Person:
    spec = load_procedures(_VERTICAL)
    return next(p for p in spec.principals if p.person_id == person_id)


async def test_the_emergency_path_stores_the_recorders_own_words_but_still_not_the_visitors(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """D2.7 on the path that DOES put human free text in the immutable record.

    The test above measures the ordinary approval. This one measures the emergency
    one, and the two answers are different in a way the RoPA has to state:

    * ``WaiverInvocation.justification`` — the roadside "ทำไมถึงเคาะไปก่อน" — lands in
      the ``gate_decision`` payload, and the ratification row can carry a ``note``.
      Both are free text a human typed, in a hash-chained row that cannot be edited or
      deleted. This is **designed, not leaked**: ``WaiverInvocation``'s own docstring
      says it is stored in the durable audit chain so the obligation and its stated
      reason cannot drift apart. Asserting it here pins it as a known fact rather than
      leaving it to be rediscovered by whoever next writes the erasure procedure.
    * The VISITOR's text still is not there — which is what D2.7 actually asks, and it
      now holds on both paths rather than only on the one that was measured first.

    The distinction that matters to the controller: the waiver text is typed by a
    NAMED INTERNAL PRINCIPAL about their own act (``recorded_by`` sits in the same
    payload), not by a member of the public describing their vehicle. Whether that
    difference is decisive is a controller judgment, not a code fact — this test only
    establishes which is true.

    There is no HTTP surface for either driver (the resolve route takes no waiver, and
    ``services/api/routers/`` has no ratify endpoint at all), so the drivers ARE the
    production surface here — calling them is the real consumer, not a shortcut.
    """
    await seed_repair_gate_waiting_human_run(db_session)
    case_id = await _visitor_opens_a_case(client_with_db)

    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    run_id: str = fired.json()["run_id"]

    proposals = await _parked_proposals(db_session, run_id)
    decisions = {
        str(p["action_id"]): ("approve" if case_id_of(p) == case_id else "reject")
        for p in proposals
    }
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)

    # ต้อม RECORDS a decision เฮีย gave by phone — the recorder is the mechanic, which
    # is the whole shape of ADR-0034's E-2 path.
    await resolve_gated_step(
        db_session,
        run_id,
        _GATE_STEP,
        decisions,
        _person(_MECHANIC),
        procedure=procedure,
        principals=list(spec.principals),
        waiver_invocation=WaiverInvocation(justification=_WAIVER_TEXT),
    )
    # ...and เฮีย signs for it afterwards, with a note.
    await ratify_gated_step(
        db_session,
        run_id,
        _GATE_STEP,
        _person(_OWNER),
        decision="ratify",
        procedure=procedure,
        principals=list(spec.principals),
        note=_RATIFY_NOTE,
    )
    assert gate_hooks.failures() == [], "the hook is fail-soft; a swallowed error must show here"

    rows = await _audit_rows(db_session, run_id)
    assert rows, "no audit rows means every assertion below is vacuous"
    actions = {row.action for row in rows}
    assert actions == {
        "run_started",
        "gate_decision",
        "handler_receipt",
        "gate_ratified",
    }, f"unexpected audit actions for a provisional-then-ratified run: {sorted(actions)}"

    for row in rows:
        allowed = _ALLOWED_PAYLOAD_KEYS.get(row.action)
        assert allowed is not None, f"no allowlist declared for audit action {row.action!r}"
        assert set(row.payload or {}) <= allowed, (
            f"{row.action!r} payload grew a key the RoPA has not described: "
            f"{sorted(set(row.payload or {}) - allowed)}"
        )
        assert _leaked(row.payload) == [], (
            f"the VISITOR's typed text reached the tamper-evident chain via the "
            f"{row.action!r} payload (sentinels seen: {_leaked(row.payload)}) — D2.7's "
            f"answer does not survive the emergency path"
        )

    # --- the recorder's words ARE in there, and that is the finding ------------
    by_action = {row.action: row for row in rows}
    assert _WAIVER_SENTINEL in _dumped(by_action["gate_decision"].payload), (
        "the waiver justification must be IN the chain — if this stops being true the "
        "obligation and its stated reason can drift apart, which is the property "
        "ADR-0034 D3(2) put it there for"
    )
    assert _NOTE_SENTINEL in _dumped(by_action["gate_ratified"].payload), (
        "the ratifier's note is the second human free-text field the immutable record "
        "carries; the erasure procedure has to know about both, not one"
    )
    assert by_action["gate_decision"].payload is not None
    assert by_action["gate_decision"].payload["recorded_by"] == _MECHANIC, (
        "the free text sits beside the NAMED principal who typed it — that pairing is "
        "what makes it personal data about an identified internal person rather than "
        "an anonymous string, and it is why this row needs its own RoPA line"
    )
