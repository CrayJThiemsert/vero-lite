"""Tests for the energy synthetic DataAdapter (PLAN-0005 §6.2 / §7.2).

Lesson #7 §3: in-process probes — Protocol conformance, behavioral
assertions on returned data, generated-model validation, and an
in-process PD-5 wording scan.
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
from verticals.energy.data_adapter import EnergySyntheticAdapter, register_energy_adapter

_ENERGY_YAML = Path("verticals/energy/ontology/energy_v0.yaml")
_ADAPTER_DIR = Path("verticals/energy/data_adapter")

# PD-5 denylist (PLAN-003 §9.4). The design-partner candidate names are
# assembled from fragments so the literal identifiers never appear verbatim
# in the repo — the very wording discipline this test enforces.
_DESIGN_PARTNER_TERMS = ("ban" + "pu", "fast" + "enal")


def _load_generated_models(tmp_path: Path) -> ModuleType:
    """Generate the energy Pydantic models and import them in isolation."""
    models_path = tmp_path / "energy_models.py"
    emit_pydantic(load_doc(_ENERGY_YAML), models_path)
    spec = importlib.util.spec_from_file_location("energy_generated", models_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_adapter_conforms_to_protocol() -> None:
    assert isinstance(EnergySyntheticAdapter(), DataAdapter)


async def test_health_check_reports_ok() -> None:
    result = await EnergySyntheticAdapter().health_check()
    assert result["status"] == "ok"
    assert result["vertical"] == "energy"


async def test_fetch_objects_asset_non_empty() -> None:
    objects = await EnergySyntheticAdapter().fetch_objects("Asset")
    assert objects
    assert all(isinstance(obj, dict) for obj in objects)


async def test_fetch_objects_unknown_type_is_empty() -> None:
    assert await EnergySyntheticAdapter().fetch_objects("Nonexistent") == []


async def test_fetch_objects_respects_limit() -> None:
    objects = await EnergySyntheticAdapter().fetch_objects("Asset", limit=2)
    assert len(objects) == 2


async def test_fetch_objects_asset_validates_against_generated_model(tmp_path: Path) -> None:
    """§7.2: every fetched Asset dict constructs the generated Asset model."""
    models = _load_generated_models(tmp_path)
    objects = await EnergySyntheticAdapter().fetch_objects("Asset")
    assert objects
    for raw in objects:
        models.Asset(**raw)


async def test_stream_events_reading_yields_threshold_crossing() -> None:
    """§7.2: stream_events('reading') yields >=1 event suitable for an Alert."""
    adapter = EnergySyntheticAdapter()
    events = [event async for event in adapter.stream_events("reading")]
    assert events
    assert all(event["event_type"] == "reading" for event in events)
    assert any(event["measured_value"] >= 90.0 for event in events)


async def test_stream_events_filters_by_type() -> None:
    adapter = EnergySyntheticAdapter()
    alarms = [event async for event in adapter.stream_events("alarm")]
    assert alarms
    assert {event["event_type"] for event in alarms} == {"alarm"}


def test_register_energy_adapter_registers_on_registry() -> None:
    register_energy_adapter()
    assert isinstance(registry.get_adapter("energy"), EnergySyntheticAdapter)


def test_no_design_partner_identifiers() -> None:
    """PD-5: the adapter + synthetic fixtures carry no design-partner names."""
    pattern = re.compile(r"\b(" + "|".join(_DESIGN_PARTNER_TERMS) + r")\b", re.IGNORECASE)
    hits: list[str] = []
    for path in sorted(_ADAPTER_DIR.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{path}:{lineno}")
    assert hits == []
