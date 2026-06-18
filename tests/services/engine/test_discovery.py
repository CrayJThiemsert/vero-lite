"""Tests for registry auto-discovery (ADR-0023 / PLAN-0032, B2).

Offline + deterministic. Exercises the import-scan over the real ``verticals/*``
packages against the process-global registry (the autouse ``_reset_registry`` fixture
wipes it between tests). Asserts the CONTRACT: discovery registers the active verticals
(AC-1), is idempotent with explicit registration + when re-run (AC-2), is
failure-isolated (AC-3), and is re-runnable after a reset (AC-4).
"""

from __future__ import annotations

import pytest

from services.engine import discovery
from services.engine.registry import registry
from verticals.energy.data_adapter import register_energy_adapter

# The three active verticals (Rule-of-Three). Assertions use subset (<=) so a parked /
# additional vertical package does not break them.
_ACTIVE = {"energy", "supply_chain", "aquaculture"}


def test_discovery_registers_all_active_verticals() -> None:
    """AC-1: import-scan registers every conforming vertical; ``_template`` is skipped."""
    newly = discovery.discover_and_register()
    assert _ACTIVE <= set(registry.verticals())
    assert "_template" not in registry.verticals()
    assert newly == sorted(newly)  # deterministic order


def test_discovery_is_idempotent_with_explicit_registration() -> None:
    """AC-2: discovery after an explicit register skips that vertical — no duplicate
    RegistryError; the rest still register."""
    register_energy_adapter()  # explicit, before discovery
    newly = discovery.discover_and_register()
    assert "energy" not in newly  # already registered -> skipped
    assert _ACTIVE <= set(registry.verticals())


def test_discovery_run_twice_registers_nothing_new() -> None:
    """AC-2: a second discovery is a no-op (registers nothing new, does not raise)."""
    first = discovery.discover_and_register()
    second = discovery.discover_and_register()
    assert _ACTIVE <= set(first)
    assert second == []


def test_discovery_isolates_a_failing_vertical(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-3: a vertical whose registration raises is skipped + logged; the rest register."""
    real = discovery._register_vertical

    def _boom(ns: str) -> None:
        if ns == "energy":
            raise RuntimeError("boom")
        real(ns)

    monkeypatch.setattr(discovery, "_register_vertical", _boom)
    newly = discovery.discover_and_register()
    assert "energy" not in newly  # the broken one is skipped, not raised
    assert {"supply_chain", "aquaculture"} <= set(registry.verticals())  # the rest survive


def test_discovery_is_rerunnable_after_reset() -> None:
    """AC-4: discovery is re-runnable after ``registry.reset()`` (no import-time-only
    side effect that survives a reset — PLAN-0005 R5)."""
    discovery.discover_and_register()
    assert _ACTIVE <= set(registry.verticals())
    registry.reset()
    assert registry.verticals() == []
    discovery.discover_and_register()
    assert _ACTIVE <= set(registry.verticals())
