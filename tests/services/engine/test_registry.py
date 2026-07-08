"""Tests for the vertical registry (PLAN-0005 §6.4, OQ-6, R5/C-4).

The autouse ``_reset_registry`` fixture (tests/conftest.py) gives every
test a clean registry; these cases exercise registration, lookup,
duplicate rejection, and explicit reset in-process.
"""

from typing import Any, cast

import pytest

from services.engine.actions import RecommendedAction
from services.engine.data_adapter import DataAdapter
from services.engine.registry import RegistryError, VerticalRegistry, registry


class _StubAdapter:
    """Minimal adapter stub — the registry only reads ``vertical_name``."""

    def __init__(self, vertical_name: str) -> None:
        self.vertical_name = vertical_name


def _stub(name: str) -> DataAdapter:
    """Duck-typed stub cast to satisfy mypy; registry only touches vertical_name."""
    return cast(DataAdapter, _StubAdapter(name))


async def _noop_handler(action: RecommendedAction) -> dict[str, Any]:
    return {"handled": action.id}


def test_register_and_get_adapter() -> None:
    adapter = _stub("energy")
    registry.register_adapter(adapter)
    assert registry.get_adapter("energy") is adapter


def test_duplicate_adapter_raises() -> None:
    registry.register_adapter(_stub("energy"))
    with pytest.raises(RegistryError):
        registry.register_adapter(_stub("energy"))


def test_get_unknown_adapter_raises() -> None:
    with pytest.raises(RegistryError):
        registry.get_adapter("nonexistent")


def test_register_and_get_handler() -> None:
    registry.register_handler("energy", "echo", _noop_handler)
    assert registry.get_handler("energy", "echo") is _noop_handler


def test_duplicate_handler_raises() -> None:
    registry.register_handler("energy", "echo", _noop_handler)
    with pytest.raises(RegistryError):
        registry.register_handler("energy", "echo", _noop_handler)


def test_get_unknown_handler_raises() -> None:
    with pytest.raises(RegistryError):
        registry.get_handler("energy", "missing")


def test_verticals_lists_registered_sorted() -> None:
    registry.register_handler("supply_chain", "noop", _noop_handler)
    registry.register_adapter(_stub("energy"))
    assert registry.verticals() == ["energy", "supply_chain"]


def test_handler_names_lists_registered_sorted() -> None:
    registry.register_handler("energy", "notify", _noop_handler)
    registry.register_handler("energy", "echo", _noop_handler)
    assert registry.handler_names("energy") == ["echo", "notify"]


def test_handler_names_empty_for_unknown_vertical() -> None:
    assert registry.handler_names("nonexistent") == []


# --- PLAN-0060: optional per-handler descriptions + handler_catalog accessor ---


def test_handler_catalog_returns_name_description_pairs_sorted() -> None:
    """A registered description surfaces in the catalog; ordering matches handler_names."""
    registry.register_handler("energy", "restart", _noop_handler, description="Controlled restart.")
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    assert registry.handler_catalog("energy") == [
        ("echo", "Diagnostic no-op."),
        ("restart", "Controlled restart."),
    ]


def test_handler_catalog_description_defaults_to_none() -> None:
    """A handler registered without a description yields None (renders name-only)."""
    registry.register_handler("energy", "echo", _noop_handler)
    assert registry.handler_catalog("energy") == [("echo", None)]


def test_handler_catalog_mixes_described_and_undescribed() -> None:
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    registry.register_handler("energy", "notify", _noop_handler)
    assert registry.handler_catalog("energy") == [
        ("echo", "Diagnostic no-op."),
        ("notify", None),
    ]


def test_handler_catalog_empty_for_unknown_vertical() -> None:
    assert registry.handler_catalog("nonexistent") == []


def test_description_does_not_change_handler_lookup() -> None:
    """A description is metadata only — get_handler / handler_names are unaffected."""
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    assert registry.get_handler("energy", "echo") is _noop_handler
    assert registry.handler_names("energy") == ["echo"]


def test_duplicate_handler_with_description_still_raises() -> None:
    registry.register_handler("energy", "echo", _noop_handler, description="first")
    with pytest.raises(RegistryError):
        registry.register_handler("energy", "echo", _noop_handler, description="second")


def test_reset_clears_descriptions() -> None:
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    registry.reset()
    assert registry.handler_catalog("energy") == []


def test_reset_clears_registry() -> None:
    registry.register_adapter(_stub("energy"))
    registry.reset()
    assert registry.verticals() == []


def test_isolated_instance_independent_of_singleton() -> None:
    local = VerticalRegistry()
    local.register_adapter(_stub("energy"))
    assert local.verticals() == ["energy"]
    assert registry.verticals() == []
