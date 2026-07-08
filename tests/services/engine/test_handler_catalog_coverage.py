"""PLAN-0060 AC-2: every handler-registering vertical describes every handler.

Each of the four verticals with a ``handlers.py`` (procurement / energy /
supply_chain / aquaculture — ``vet_clinic`` registers none, Phase-2 parked) declares
an ``ACTION_DESCRIPTIONS`` map beside its ``ACTION_TYPES`` tuple. After registration
the ``handler_catalog`` must describe every registered handler with no orphan (a
description for an unregistered name) and no gap (a registered handler with no
description). The procurement ``emergency_source`` vs ``reorder`` pair is the
load-bearing distinction the session-114 live smoke found the model getting wrong
from bare names alone.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from services.engine.registry import registry
from verticals.aquaculture import handlers as aquaculture_handlers
from verticals.energy import handlers as energy_handlers
from verticals.procurement import handlers as procurement_handlers
from verticals.supply_chain import handlers as supply_chain_handlers

_Case = tuple[str, Callable[[], None], tuple[str, ...], dict[str, str]]

_VERTICALS: list[_Case] = [
    (
        "procurement",
        procurement_handlers.register_procurement_handlers,
        procurement_handlers.ACTION_TYPES,
        procurement_handlers.ACTION_DESCRIPTIONS,
    ),
    (
        "energy",
        energy_handlers.register_energy_handlers,
        energy_handlers.ACTION_TYPES,
        energy_handlers.ACTION_DESCRIPTIONS,
    ),
    (
        "supply_chain",
        supply_chain_handlers.register_supply_chain_handlers,
        supply_chain_handlers.ACTION_TYPES,
        supply_chain_handlers.ACTION_DESCRIPTIONS,
    ),
    (
        "aquaculture",
        aquaculture_handlers.register_aquaculture_handlers,
        aquaculture_handlers.ACTION_TYPES,
        aquaculture_handlers.ACTION_DESCRIPTIONS,
    ),
]

_IDS = [case[0] for case in _VERTICALS]


@pytest.mark.parametrize("vertical,register,action_types,descriptions", _VERTICALS, ids=_IDS)
def test_action_descriptions_cover_exactly_echo_plus_action_types(
    vertical: str,
    register: Callable[[], None],
    action_types: tuple[str, ...],
    descriptions: dict[str, str],
) -> None:
    """The authored map keys == echo + every ACTION_TYPES entry — no orphan, no gap."""
    assert set(descriptions) == set(action_types) | {"echo"}
    assert all(text.strip() for text in descriptions.values()), "every description is non-empty"


@pytest.mark.parametrize("vertical,register,action_types,descriptions", _VERTICALS, ids=_IDS)
def test_registered_catalog_describes_every_handler(
    vertical: str,
    register: Callable[[], None],
    action_types: tuple[str, ...],
    descriptions: dict[str, str],
) -> None:
    """After registration every catalog entry carries a non-None description and the
    catalog's key set matches handler_names (the registered universe)."""
    register()
    catalog = dict(registry.handler_catalog(vertical))
    assert set(catalog) == set(registry.handler_names(vertical))
    assert all(desc is not None for desc in catalog.values())
    assert set(catalog) == set(action_types) | {"echo"}


def test_procurement_emergency_source_vs_reorder_are_distinguished() -> None:
    """The load-bearing pair encodes urgent-critical-failure vs routine-restock (AC-2)."""
    descriptions = procurement_handlers.ACTION_DESCRIPTIONS
    emergency = descriptions["emergency_source"].lower()
    reorder = descriptions["reorder"].lower()
    assert emergency != reorder
    # emergency_source reads urgent / critical-failure; reorder reads routine / calm.
    assert any(word in emergency for word in ("urgent", "critical", "line-down"))
    assert any(word in reorder for word in ("routine", "calm", "normal lead time"))
    assert "urgent" not in reorder
