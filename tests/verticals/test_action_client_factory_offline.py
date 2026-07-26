"""Every shipped vertical's ACTION executor must carry an OFFLINE client factory.

``ActionStepExecutor.client_factory`` defaults to ``_default_client_factory``
(``services/engine/procedures/action_step.py:285`` -> ``:151-162``), which builds a live
``OllamaClient`` pointed at MS-S1. Deleting one kwarg from any vertical's executor factory
is therefore a SILENT conversion to a live model call: no type error, no ``mypy`` complaint,
and no test failure on any path that does not actually execute an ACTION step. That is a
CLAUDE.md §8 host-state change hiding in a default argument.

The hazard is not hypothetical. Wiring the AC-9b translate seam turned a deliberately
unstubbed case into a live call and ran ``gpt-oss:20b`` on MS-S1 twice before anyone
noticed -- the incident recorded in ``tests/conftest.py::_no_outbound_network``.

**What this module adds, measured rather than assumed.** Dropping the kwarg was mutation-
tested across all six verticals before this file was written, and the pre-existing suite
does NOT stay green: aquaculture 3 failures, building_materials 1, energy 2,
fleet_maintenance 6, supply_chain 7, procurement pinned directly by
``tests/verticals/procurement/test_operate_executor_factory.py::test_factory_is_deterministic_no_ollama``.
So the claim "the other five were unguarded" -- which this docstring asserted in draft --
is false, and is recorded here because the correction is the point. What is actually wrong
with that coverage is three things:

1. **The signal is opaque.** Those failures surface as
   ``BaseExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)`` -- the socket
   guard firing deep inside an async run. It names neither the vertical, nor the kwarg,
   nor the network. This module fails with a sentence saying exactly what regressed.
2. **The coverage is incidental, not maintained.** It exists only where a vertical happens
   to own an end-to-end test that executes an ACTION step, and building_materials rests on
   a single case. Nothing keeps that property true. A newly scaffolded vertical
   (``services/engine/scaffolder/package.py:369`` emits the kwarg) ships with no end-to-end
   test at all, and would be genuinely unguarded until someone wrote one.
3. **It only fires under pytest.** ``_no_outbound_network`` is a pytest fixture; the
   production registrations in ``services/api/main.py`` and ``services/engine/cli.py`` run
   under neither it nor any e2e test. This module asserts at *registration* -- the same
   operation those two files perform -- rather than at execution.

**The assertion is "not the live default", never "is <a specific stub>".** Five verticals
inject ``services.engine.procedures.advisory_stub.advisory_stub_factory``; procurement
injects its OWN, same-named, PO-shaped stub (``verticals/procurement/hero_demo/run.py:123``),
kept byte-unchanged per PLAN-0062 AC-6. Pinning identity would either miss procurement or
require a stub allowlist that goes stale the moment a sixth stub is legitimately added.
What must never regress is the *property* -- no vertical's ACTION step reaches the network
-- so that is what is asserted.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

from services.engine.cli import _PROCEDURE_EXECUTOR_REGISTRARS as CLI_REGISTRARS
from services.engine.discovery import discover_and_register
from services.engine.llm.client import OllamaClient
from services.engine.procedures.action_step import (
    ActionStepExecutor,
    _default_client_factory,
)
from services.engine.procedures.spec import StepKind
from services.engine.registry import registry

VERTICALS = sorted(CLI_REGISTRARS)
"""Enumerated from the CLI registrar map, NOT hardcoded, so a 7th vertical is guarded the
day it is wired. The CLI map is pinned set-equal to the API lifespan map by
``tests/services/engine/test_cli_registrars.py`` (PLAN-0090 AC-4), and it addresses its
registrars lazily by ``(module, attr)`` strings -- so importing it here does not drag
FastAPI in, and cannot import one vertical's harness while guarding another's."""


@pytest.fixture(autouse=True)
def _discover() -> None:
    """Registration binds the declared-read leg to the REGISTRY-registered adapter
    (PLAN-0064 SD-5), so adapters must be discovered first -- the API-lifespan ordering."""
    discover_and_register()


async def _register(vertical: str) -> None:
    module_name, attr = CLI_REGISTRARS[vertical]
    registrar = getattr(importlib.import_module(module_name), attr)
    result = registrar()
    if inspect.isawaitable(result):
        await result


_WRAPPER_ATTRS = ("base", "inner")
"""The decorator seams an ACTION executor can hide behind. Walked, not indexed, because
the nesting DEPTH varies per vertical: aquaculture and energy register a bare
``ActionStepExecutor``; building_materials, fleet_maintenance and procurement wrap it once
as ``GovernanceActionExecutor(base=...)``; supply_chain wraps twice --
``ColdChainAssessExecutor(inner=GovernanceActionExecutor(base=...))``. A fixed one-level
unwrap silently mistook that third shape for an un-unwrappable executor."""


def _action_base(vertical: str) -> ActionStepExecutor:
    """The ``ActionStepExecutor`` carrying the LLM seam, unwrapped through any decorators."""
    executor = registry.get_procedure_executors(vertical)()[StepKind.ACTION]

    for _ in range(len(_WRAPPER_ATTRS) * 4):  # bounded: a cycle must not hang the suite
        if isinstance(executor, ActionStepExecutor):
            return executor
        nxt = next((getattr(executor, a) for a in _WRAPPER_ATTRS if hasattr(executor, a)), None)
        if nxt is None:
            break
        executor = nxt

    pytest.fail(
        f"{vertical}: could not reach an ActionStepExecutor from "
        f"{type(executor).__name__} by walking {_WRAPPER_ATTRS}. A new decorator seam was "
        f"added -- extend _WRAPPER_ATTRS, do NOT drop the vertical from the guard."
    )


def test_the_guarded_set_is_every_procedure_shipping_vertical() -> None:
    """Non-vacuity: the parametrization must not silently shrink to zero.

    A guard that enumerates its own subjects can be defeated by the enumeration going
    empty (a renamed map, a failed import swallowed upstream) -- and every parametrized
    case would then PASS by not existing. Pinning the count makes that shape RED.
    """
    assert VERTICALS == [
        "aquaculture",
        "building_materials",
        "energy",
        "fleet_maintenance",
        "procurement",
        "supply_chain",
    ]


@pytest.mark.parametrize("vertical", VERTICALS)
async def test_action_client_factory_is_not_the_live_default(vertical: str) -> None:
    """The registered ACTION executor must not be riding ``_default_client_factory``.

    This is the assertion that catches the actual regression shape -- a dropped
    ``client_factory=`` kwarg -- at the point of registration, before any step runs.
    """
    await _register(vertical)

    assert _action_base(vertical).client_factory is not _default_client_factory, (
        f"{vertical}: the ACTION executor is riding _default_client_factory, which builds a "
        f"live OllamaClient against MS-S1. A vertical factory almost certainly lost its "
        f"'client_factory=' kwarg. Running it is a host-state action (CLAUDE.md §8)."
    )


@pytest.mark.parametrize("vertical", VERTICALS)
async def test_action_client_factory_yields_no_ollama_client(vertical: str) -> None:
    """Belt-and-braces: the factory must not PRODUCE a live client either.

    Distinct from the identity check above, and not redundant with it: a vertical could
    inject a bespoke factory (procurement already does) that nonetheless constructs an
    ``OllamaClient`` internally. Identity would pass; this fails.
    """
    await _register(vertical)

    client = _action_base(vertical).client_factory("gpt-oss:20b")

    assert not isinstance(client, OllamaClient), (
        f"{vertical}: the ACTION client factory produced a live OllamaClient "
        f"({type(client).__name__}). The offline arm must stay opt-in (CLAUDE.md §8)."
    )
