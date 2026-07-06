"""PLAN-0053 Phase B — the typed ``ServicePrincipal`` actor model (spec layer).

Covers AC-5 (distinct type, never a Person / never an approver), AC-6 (the
vertical-level ``service_principals`` registry + unique-id validator), and AC-7
(the ``Agent`` -> service reference + dangling cross-ref). RunContext threading
(AC-8) + the audit path (AC-9/10/11) land in the runtime/audit PRs.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.engine.procedures.spec import (
    Agent,
    Person,
    ServicePrincipal,
    VerticalProcedures,
    parse_procedures,
)

# --- AC-5: ServicePrincipal is a DISTINCT, approver-incapable type ---------------


def test_service_principal_is_not_a_person_subtype() -> None:
    """RF-3 / SP-2: the service identity is a DISTINCT Pydantic model, never substitutable for a
    Person in the SoD comparison set."""
    assert not issubclass(ServicePrincipal, Person)
    sp = ServicePrincipal(service_principal_id="svc-scheduler", name="Nightly Scheduler")
    assert not isinstance(sp, Person)
    assert sp.service_principal_id == "svc-scheduler"


def test_service_principal_has_no_approver_field() -> None:
    """SP-1: no ``roles`` (or any approver) field exists — the approver seam cannot be reused."""
    assert "roles" not in ServicePrincipal.model_fields
    assert set(ServicePrincipal.model_fields) == {"service_principal_id", "name"}


def test_service_principal_forbids_extra_fields() -> None:
    """AC-13 / AC-5: ``extra='forbid'`` — a smuggled ``roles`` (or any extra) is rejected, so a
    service identity can never grow an approver capability by accident."""
    with pytest.raises(ValidationError):
        ServicePrincipal(service_principal_id="svc-x", name="X", roles=frozenset({"dept_head"}))  # type: ignore[call-arg]


# --- AC-6: the vertical-level service_principals registry ------------------------


def test_vertical_service_principals_default_empty_backward_compatible() -> None:
    """Absent key => empty; every existing vertical loads unchanged (additive)."""
    vp = VerticalProcedures(vertical="v", agents=[], procedures=[])
    assert vp.service_principals == []


def test_parse_procedures_reads_service_principals() -> None:
    vp = parse_procedures(
        {
            "agents": {},
            "procedures": {},
            "service_principals": [{"service_principal_id": "svc-1", "name": "Scheduler"}],
        },
        vertical="v",
    )
    assert [sp.service_principal_id for sp in vp.service_principals] == ["svc-1"]


def test_parse_procedures_absent_service_principals_is_empty() -> None:
    vp = parse_procedures({"agents": {}, "procedures": {}}, vertical="v")
    assert vp.service_principals == []


def test_vertical_rejects_duplicate_service_principal_id() -> None:
    with pytest.raises(ValidationError, match="duplicate service_principal_id"):
        VerticalProcedures(
            vertical="v",
            agents=[],
            procedures=[],
            service_principals=[
                ServicePrincipal(service_principal_id="svc-1", name="A"),
                ServicePrincipal(service_principal_id="svc-1", name="B"),
            ],
        )


# --- AC-7: Agent -> service-principal reference + dangling cross-ref -------------


def test_agent_service_principal_ids_default_empty() -> None:
    assert Agent(agent_id="a", name="A").service_principal_ids == []


def test_vertical_rejects_dangling_agent_service_reference() -> None:
    """SD-3: a dangling Agent->service reference is an authoring error (mirrors run_by)."""
    with pytest.raises(ValidationError, match="unknown service_principal_id"):
        VerticalProcedures(
            vertical="v",
            agents=[Agent(agent_id="a", name="A", service_principal_ids=["svc-ghost"])],
            procedures=[],
            service_principals=[],
        )


def test_vertical_accepts_valid_agent_service_reference() -> None:
    vp = VerticalProcedures(
        vertical="v",
        agents=[Agent(agent_id="a", name="A", service_principal_ids=["svc-1"])],
        procedures=[],
        service_principals=[ServicePrincipal(service_principal_id="svc-1", name="Scheduler")],
    )
    assert vp.agents[0].service_principal_ids == ["svc-1"]
