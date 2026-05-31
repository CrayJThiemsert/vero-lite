"""Tests for the supply_chain synthetic DataAdapter (PLAN-0013 AC-template).

Mirrors ``tests/verticals/energy/test_energy_adapter.py`` — Protocol
conformance, behavioural assertions on returned data, generated-model
validation, and the PD-5 wording scan — for the second concrete vertical.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

from services.engine.code_generator import emit_pydantic, load_doc
from services.engine.data_adapter import DataAdapter
from services.engine.registry import registry
from verticals.supply_chain.data_adapter import (
    SupplyChainSyntheticAdapter,
    register_supply_chain_adapter,
)

_SUPPLY_CHAIN_YAML = Path("verticals/supply_chain/ontology/supply_chain_v0.yaml")
_ADAPTER_DIR = Path("verticals/supply_chain/data_adapter")

# PD-5 denylist (PLAN-003 §9.4) — same discipline as the energy adapter test.
_DESIGN_PARTNER_TERMS = ("ban" + "pu", "fast" + "enal")


def _load_generated_models(tmp_path: Path) -> ModuleType:
    """Generate the supply_chain Pydantic models and import them in isolation."""
    models_path = tmp_path / "supply_chain_models.py"
    emit_pydantic(load_doc(_SUPPLY_CHAIN_YAML), models_path)
    spec = importlib.util.spec_from_file_location("supply_chain_generated", models_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_adapter_conforms_to_protocol() -> None:
    assert isinstance(SupplyChainSyntheticAdapter(), DataAdapter)


async def test_health_check_reports_ok() -> None:
    result = await SupplyChainSyntheticAdapter().health_check()
    assert result["status"] == "ok"
    assert result["vertical"] == "supply_chain"


async def test_fetch_objects_shipment_non_empty() -> None:
    objects = await SupplyChainSyntheticAdapter().fetch_objects("Shipment")
    assert objects
    assert all(isinstance(obj, dict) for obj in objects)


async def test_fetch_objects_facility_has_coordinates() -> None:
    """AC-template: the map needs a geo-bearing type — Facility carries lat/lng."""
    facilities = await SupplyChainSyntheticAdapter().fetch_objects("Facility")
    assert facilities
    assert all("lat" in f and "lng" in f for f in facilities)


async def test_fetch_objects_unknown_type_is_empty() -> None:
    assert await SupplyChainSyntheticAdapter().fetch_objects("Nonexistent") == []


async def test_fetch_objects_respects_limit() -> None:
    objects = await SupplyChainSyntheticAdapter().fetch_objects("Shipment", limit=2)
    assert len(objects) == 2


async def test_fetch_objects_validate_against_generated_models(tmp_path: Path) -> None:
    """Every fetched Shipment/Facility dict constructs its generated model."""
    models = _load_generated_models(tmp_path)
    for shipment in await SupplyChainSyntheticAdapter().fetch_objects("Shipment"):
        models.Shipment(**shipment)
    for facility in await SupplyChainSyntheticAdapter().fetch_objects("Facility"):
        models.Facility(**facility)


async def test_stream_events_reading_yields_cold_chain_breach() -> None:
    """stream_events('reading') yields >=1 cold-chain excursion suitable for an Alert."""
    adapter = SupplyChainSyntheticAdapter()
    events = [event async for event in adapter.stream_events("reading")]
    assert events
    assert all(event["event_type"] == "reading" for event in events)
    # one pharma reading breaches the 2-8 °C cold-chain limit (well above 8)
    assert any(event["measured_value"] >= 14.0 for event in events)


async def test_stream_events_filters_by_type() -> None:
    adapter = SupplyChainSyntheticAdapter()
    alarms = [event async for event in adapter.stream_events("alarm")]
    assert alarms
    assert {event["event_type"] for event in alarms} == {"alarm"}


def test_register_supply_chain_adapter_registers_on_registry() -> None:
    register_supply_chain_adapter()
    assert isinstance(registry.get_adapter("supply_chain"), SupplyChainSyntheticAdapter)


def test_no_design_partner_identifiers() -> None:
    """PD-5: the adapter + synthetic fixtures carry no design-partner names."""
    pattern = re.compile(r"\b(" + "|".join(_DESIGN_PARTNER_TERMS) + r")\b", re.IGNORECASE)
    hits: list[str] = []
    for path in sorted(_ADAPTER_DIR.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{path}:{lineno}")
    assert hits == []
