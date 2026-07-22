"""AC-2 (PLAN-0090) — the scheduled AT-3 calm path loads, cross-refs resolve, and its spine is
byte-identical to the manual path's.

The central claim of PLAN-0090 is that **cadence is a trigger property, not a governance one**:
`scheduled_pm_service_round` and `pm_service_round` differ ONLY in how a run starts. That claim
is cheap to state and easy to let rot, so it is asserted structurally here rather than described
in a comment — if anyone edits one procedure's steps without the other, this module goes RED.

Offline: no DB, no daemon, no LLM.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.engine.procedures.spec import Procedure, Schedule, Trigger, load_procedures

_VERTICAL = "fleet_maintenance"
_MANUAL = "pm_service_round"
_SCHEDULED = "scheduled_pm_service_round"
_SP_ID = "svc-fleet-scheduler"


def _proc(procedure_id: str) -> Procedure:
    spec = load_procedures(_VERTICAL)
    return next(p for p in spec.procedures if p.procedure_id == procedure_id)


def test_scheduled_procedure_loads_with_its_schedule_descriptor() -> None:
    """L1/L2 as ratified: 06:00 daily Asia/Bangkok, owned by the head mechanic."""
    p = _proc(_SCHEDULED)
    assert p.trigger is Trigger.SCHEDULE
    assert p.schedule is not None
    assert p.schedule.cron == "0 6 * * *"
    assert p.schedule.timezone == "Asia/Bangkok"
    assert p.schedule.owning_person_id == "req-mechanic-tom"


def test_service_principal_cross_refs_resolve() -> None:
    """SP-4: a scheduled fire needs a declared service actor, and the agent must reference one
    that actually exists in the vertical's `service_principals` block."""
    spec = load_procedures(_VERTICAL)
    declared = {sp.service_principal_id for sp in spec.service_principals}
    assert declared == {_SP_ID}

    agent = next(a for a in spec.agents if a.agent_id == _proc(_SCHEDULED).run_by)
    assert agent.service_principal_ids == [_SP_ID]
    assert set(agent.service_principal_ids) <= declared

    # L2's owning person must be a real human principal of this vertical.
    people = {person.person_id for person in spec.principals}
    assert _proc(_SCHEDULED).schedule is not None
    assert _proc(_SCHEDULED).schedule.owning_person_id in people  # type: ignore[union-attr]


def test_scheduled_path_keeps_the_at3_shape() -> None:
    """AT-3 absence properties: no DOA ladder, no SoD, no criteria.

    Asserted against the MANUAL path rather than against literals, so the two can never drift
    apart on governance shape — which is the property the archetype claim rests on.
    """
    manual, scheduled = _proc(_MANUAL), _proc(_SCHEDULED)
    assert scheduled.separation_of_duties == manual.separation_of_duties == []
    assert [s.governance_content for s in scheduled.steps] == [
        s.governance_content for s in manual.steps
    ]
    assert all(s.governance_content is None for s in scheduled.steps)


def test_spine_is_byte_identical_to_the_manual_path() -> None:
    """The whole point of the procedure: only the TRIGGER differs.

    A dumped-model comparison, not a step-id comparison — it catches a changed projection,
    threshold_field, direction, handler, autonomy or facet, any of which would silently make the
    scheduled run a different governed thing from the one the demo narrates.
    """
    manual, scheduled = _proc(_MANUAL), _proc(_SCHEDULED)
    assert [s.model_dump(mode="json") for s in scheduled.steps] == [
        s.model_dump(mode="json") for s in manual.steps
    ]
    assert scheduled.terminal == manual.terminal
    assert scheduled.run_by == manual.run_by

    # ...and the manual path is STILL manual: a distinct procedure_id, never a trigger flip.
    assert manual.trigger is Trigger.MANUAL
    assert manual.schedule is None


def test_schedule_descriptor_is_required_when_the_trigger_is_schedule() -> None:
    """Negative control: strip the descriptor and the spec must fail LOUDLY at load.

    Built from the shipped procedure so the control cannot drift from the real shape.
    """
    payload = _proc(_SCHEDULED).model_dump(mode="json")
    payload.pop("schedule")
    with pytest.raises(ValidationError):
        Procedure.model_validate(payload)


def test_a_bogus_timezone_fails_loudly_at_load() -> None:
    """SD-P1: the tz is resolved against the system tz database at LOAD, so a typo is a loud
    error rather than a schedule that silently never fires."""
    with pytest.raises(ValidationError):
        Schedule(cron="0 6 * * *", timezone="Asia/Bangkonk")
