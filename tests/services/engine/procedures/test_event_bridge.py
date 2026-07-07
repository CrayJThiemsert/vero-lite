"""PLAN-0056 Step 3 (ADR-0029 SD-2 / SD-P1) — the event dedup key + run-id helpers.

Pure/offline: proves the idempotency semantics (AC-5) — a re-detected event inside the
same detection window collapses to ONE key (=> one governed run), a later window fires a
fresh key, and the key is order-independent + machine-independent (naive datetime = UTC).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import pytest

from services.engine.procedures.event_bridge import (
    EventBridgeError,
    EventRunRequest,
    build_event_resolver,
    event_key,
    event_run_id,
)
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.spec import (
    Agent,
    EventTrigger,
    Person,
    Procedure,
    ServicePrincipal,
    Step,
    StepKind,
    Trigger,
    VerticalProcedures,
)

_T0 = datetime(2026, 7, 7, 6, 0, 0, tzinfo=UTC)


def _key(
    *,
    vertical: str = "procurement",
    event_kind: str = "asset_failure",
    entity_ids: list[str] | None = None,
    detected_at: datetime = _T0,
    window_seconds: int = 3600,
) -> str:
    return event_key(
        vertical=vertical,
        event_kind=event_kind,
        entity_ids=entity_ids if entity_ids is not None else ["pump-7"],
        detected_at=detected_at,
        window_seconds=window_seconds,
    )


def test_event_key_is_deterministic() -> None:
    assert _key() == _key()


def test_event_key_re_detect_same_window_collapses() -> None:
    # AC-5: the same event re-detected 30 min later (same 1h window) yields the SAME key —
    # so the write-ahead run_id insert is an idempotent no-op (no duplicate governed run).
    later = _T0 + timedelta(minutes=30)
    assert _key() == _key(detected_at=later)


def test_event_key_distinct_window_fires_fresh() -> None:
    # The same condition recurring in a LATER window yields a fresh key (a new run).
    next_window = _T0 + timedelta(hours=1, minutes=1)
    assert _key() != _key(detected_at=next_window)


def test_event_key_entity_order_independent() -> None:
    # Entity ordering never splits the key (ids are sorted before hashing).
    assert _key(entity_ids=["a", "b"]) == _key(entity_ids=["b", "a"])


def test_event_key_distinguishes_vertical() -> None:
    assert _key() != _key(vertical="energy")


def test_event_key_distinguishes_event_kind() -> None:
    assert _key() != _key(event_kind="low_stock")


def test_event_key_distinguishes_entity() -> None:
    assert _key() != _key(entity_ids=["pump-8"])


def test_event_key_no_field_boundary_collision() -> None:
    # The unit-separator join means a split shift cannot collide.
    assert _key(vertical="a", event_kind="bc") != _key(vertical="ab", event_kind="c")


def test_event_key_naive_datetime_treated_as_utc() -> None:
    # A naive detected_at is read as UTC — the bucket is machine-independent (not host-local).
    naive = _T0.replace(tzinfo=None)
    assert _key(detected_at=naive) == _key(detected_at=_T0)


def test_event_key_rejects_nonpositive_window() -> None:
    with pytest.raises(ValueError, match="window_seconds must be > 0"):
        _key(window_seconds=0)


def test_event_run_id_format() -> None:
    key = _key()
    assert event_run_id("event_emergency_sourcing_round", key) == (
        f"event_emergency_sourcing_round@{key}"
    )


# --- Step 4: the event resolver (event -> EventRunRequest) ---------------------------------


def _no_executors() -> Mapping[StepKind, StepExecutor]:
    return {}


def _event_spec(
    *,
    event_kind: str = "asset_failure",
    owning: str | None = "alice",
    sp_ids: tuple[str, ...] = ("svc-1",),
    window: int = 3600,
) -> VerticalProcedures:
    return VerticalProcedures(
        vertical="procurement",
        agents=[Agent(agent_id="a1", name="A1", service_principal_ids=list(sp_ids))],
        service_principals=[ServicePrincipal(service_principal_id="svc-1", name="Buyer Bot")],
        principals=[Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))],
        procedures=[
            Procedure(
                procedure_id="event_emergency_sourcing_round",
                title="Event Emergency Sourcing",
                run_by="a1",
                trigger=Trigger.EVENT,
                event_trigger=EventTrigger(
                    event_kind=event_kind, owning_person_id=owning, dedup_window_seconds=window
                ),
                steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY)],
            )
        ],
    )


def _resolve(
    spec: VerticalProcedures,
    *,
    event_kind: str = "asset_failure",
    entity_ids: list[str] | None = None,
    detected_at: datetime = _T0,
) -> EventRunRequest:
    resolver = build_event_resolver(spec, _no_executors)
    return resolver(
        event_kind=event_kind,
        entity_ids=entity_ids if entity_ids is not None else ["pump-7"],
        detected_at=detected_at,
    )


def test_resolve_maps_event_kind_to_procedure() -> None:
    req = _resolve(_event_spec())
    assert req.procedure.procedure_id == "event_emergency_sourcing_round"
    assert req.agent.agent_id == "a1"
    assert req.service_principal.service_principal_id == "svc-1"
    assert req.owning_person is not None and req.owning_person.person_id == "alice"
    assert req.vertical == "procurement"


def test_resolve_run_id_is_event_keyed() -> None:
    req = _resolve(_event_spec())
    key = event_key(
        vertical="procurement",
        event_kind="asset_failure",
        entity_ids=["pump-7"],
        detected_at=_T0,
        window_seconds=3600,
    )
    assert req.run_id == event_run_id("event_emergency_sourcing_round", key)


def test_resolve_stamps_trigger_context() -> None:
    tc = _resolve(_event_spec()).trigger_context
    assert tc["trigger"] == "event"
    assert tc["event_kind"] == "asset_failure"
    assert tc["entity_ids"] == ["pump-7"]
    assert "event_key" in tc
    assert "detected_at" in tc


def test_resolve_uses_per_mapping_window() -> None:
    # The descriptor's dedup_window_seconds drives the key — a wide (1-day) window collapses a
    # 2h-later re-detect that the 1h default would have split into a fresh run.
    resolver = build_event_resolver(_event_spec(window=86_400), _no_executors)
    first = resolver(event_kind="asset_failure", entity_ids=["pump-7"], detected_at=_T0)
    later = resolver(
        event_kind="asset_failure", entity_ids=["pump-7"], detected_at=_T0 + timedelta(hours=2)
    )
    assert first.run_id == later.run_id


def test_resolve_unmapped_event_kind_raises() -> None:
    with pytest.raises(EventBridgeError, match="maps event_kind 'flood'"):
        _resolve(_event_spec(), event_kind="flood")


def test_resolve_agent_without_service_principal_raises() -> None:
    with pytest.raises(EventBridgeError, match="declares no service_principal_ids"):
        _resolve(_event_spec(sp_ids=()))


def test_resolve_headless_owning_person_is_none() -> None:
    assert _resolve(_event_spec(owning=None)).owning_person is None
