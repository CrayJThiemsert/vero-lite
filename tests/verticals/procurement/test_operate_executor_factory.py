"""PLAN-0054 Step 6b / AC-10 — the deterministic procurement executor-factory registration.

The Control-leg operate demo resolves a ``waiting_human`` gate over HTTP, which resumes the
run via ``registry.get_procedure_executors("procurement")``. That lookup 409s ("no
procedure-executor factory") until a factory is registered -- the gap this Step closes. These
tests prove the demo-registration path (:func:`register_procurement_procedure_executors`)
registers a ``procurement`` factory so the resolve endpoint's ``_executor_factory("procurement")``
no longer 409s, AND that the factory is DETERMINISTIC (the deterministic advisory stub, NOT a
live ``OllamaClient``) so the operate demo needs no MS-S1 call (host-state, CLAUDE.md #8).

The autouse ``_reset_registry`` fixture (tests/conftest.py) leaves ``procurement`` unregistered
at the start of every case, so each test asserts against a clean registry.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from services.api.routers.runs import _executor_factory
from services.engine.discovery import discover_and_register
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.governance_step import GovernanceActionExecutor
from services.engine.procedures.spec import StepKind
from services.engine.registry import RegistryError, registry
from verticals.procurement.hero_demo.run import (
    _AdvisoryStubClient,
    advisory_stub_factory,
    register_procurement_procedure_executors,
)


@pytest.fixture(autouse=True)
def _discover() -> None:
    """PLAN-0064: registration now binds the declared-read leg to the REGISTRY-registered
    adapter (SD-5), so the adapter must be discovered first — exactly the API-lifespan
    ordering (`discover_and_register()` before the registrar table) and the
    energy-factory-test precedent. `_reset_registry` (tests/conftest.py) still leaves the
    executor FACTORY unregistered at every test start, which is what these tests assert."""
    discover_and_register()


async def test_registration_resolves_the_procurement_factory() -> None:
    """After the demo-registration path, get_procedure_executors('procurement') resolves to a
    zero-arg factory yielding the three per-kind executors the run/resume path dispatches on."""
    with pytest.raises(RegistryError):
        registry.get_procedure_executors("procurement")  # unregistered by default

    await register_procurement_procedure_executors()

    execs = registry.get_procedure_executors("procurement")()
    # PLAN-0078 Step 1: TRANSFORM joins the exact key set (shared fieldless executor, all 4
    # factories, pure-additive — the PR-1 intake flip adds the first declared transform).
    assert set(execs) == {
        StepKind.QUERY,
        StepKind.EVALUATE,
        StepKind.ACTION,
        StepKind.TRANSFORM,
    }


async def test_resolve_endpoint_factory_no_longer_409s() -> None:
    """AC-10: the resolve endpoint's ``_executor_factory('procurement')`` 409s ("no
    procedure-executor factory") until the demo path registers a factory, then resolves."""
    with pytest.raises(HTTPException) as unregistered:
        _executor_factory("procurement")
    assert unregistered.value.status_code == 409

    await register_procurement_procedure_executors()

    # The exact 409 that blocked the live operate demo is now closed.
    assert _executor_factory("procurement") is registry.get_procedure_executors("procurement")


async def test_factory_is_deterministic_no_ollama() -> None:
    """AC-10: the ACTION executor reuses the deterministic advisory stub -- NO ``OllamaClient``
    in the resolve path (the ``source`` auto step + post-``approve`` ``issue_po`` ACTION would
    otherwise fire a live LLM on resume)."""
    await register_procurement_procedure_executors()

    action = registry.get_procedure_executors("procurement")()[StepKind.ACTION]
    assert isinstance(action, GovernanceActionExecutor)
    base = action.base
    assert isinstance(base, ActionStepExecutor)
    # The ACTION executor's LLM seam is the deterministic advisory stub, not Ollama.
    assert base.client_factory is advisory_stub_factory
    assert isinstance(advisory_stub_factory("gpt-oss:20b"), _AdvisoryStubClient)


async def test_registration_is_idempotent() -> None:
    """A second registration is a no-op -- NOT a duplicate-registration ``RegistryError``."""
    await register_procurement_procedure_executors()
    await register_procurement_procedure_executors()  # must not raise

    assert _executor_factory("procurement") is registry.get_procedure_executors("procurement")
