"""End-to-end tests for the aquaculture vertical (PLAN-0016 Step 5, AC-1).

The aquaculture pick (ADR-0015 D4) is the first vertical whose breach is a
*crash*: a dissolved-oxygen reading of 3.2 mg/L falls BELOW the 4 mg/L safe
threshold (``OCT_RECOMMEND_DIRECTION=below``). These tests prove the scaffolded
vertical end-to-end — the ontology is OCT-shaped and role-detects to Pond/Farm;
the synthetic adapter serves the DO-crash timeline; and the deterministic rule
path (MS-S1 off, ADR-010 IN-4 — the clean-render demo path) fires on the crash,
proposes, and completes approve -> echo-execute (AC-1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from services.api.config import settings
from services.engine import code_generator, scaffold
from services.engine.recommender import ActionStatus, _rule_recommend, approve, execute
from verticals.aquaculture.data_adapter import register_aquaculture_adapter, synthetic
from verticals.aquaculture.handlers import register_aquaculture_handlers

_ONTOLOGY = Path("verticals/aquaculture/ontology/aquaculture_v0.yaml")


def _set_aquaculture_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply the aquaculture OCT_RECOMMEND_* policy (the env block new-vertical
    emitted) to the global settings for the duration of one test."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 4.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "below")
    monkeypatch.setattr(settings, "oct_recommend_entity_type", "Pond")
    monkeypatch.setattr(settings, "oct_recommend_entity_id_field", "pond_id")
    monkeypatch.setattr(settings, "oct_recommend_label", "dissolved-oxygen crash")


def _do_crash_event() -> dict[str, Any]:
    return synthetic.operational_events()[-1]


def test_aquaculture_ontology_roles() -> None:
    """The ontology is OCT-shaped and role-detects to the domain-renamed Pond/Farm."""
    roles = scaffold.detect_roles(code_generator.load_doc(_ONTOLOGY))
    assert roles.namespace == "aquaculture"
    assert roles.asset_type == "Pond"
    assert roles.site_type == "Farm"
    assert roles.event_asset_ref == "pond_id"
    assert roles.event_site_ref == "site_id"


def test_synthetic_do_crash_is_the_final_beat() -> None:
    events = synthetic.operational_events()
    crash = events[-1]
    assert crash["event_id"] == "event-reading-do-crash"
    assert crash["measured_value"] == 3.2
    assert crash["severity"] == "critical"
    assert crash["pond_id"] == "pond-07"
    # every non-breach reading stays strictly above the 4 mg/L threshold, so only
    # the crash escalates on the below-direction rule path.
    readings = [e for e in events[:-1] if e["event_type"] == "reading"]
    assert readings and all(e["measured_value"] > 4 for e in readings)


def test_synthetic_dataset_shape() -> None:
    assert len(synthetic.farms()) == 2
    assert len(synthetic.ponds()) == 4
    assert set(synthetic.OBJECT_SOURCES) == {"Farm", "Pond"}
    # the fallow pond exercises a non-active status enum on the map.
    assert any(p["status"] == "fallow" for p in synthetic.ponds())


def test_ac1_rule_path_fires_on_do_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1 (rule path, MS-S1 off): the DO crash escalates with a below-direction
    trace naming pond-07; a nominal reading does not escalate."""
    _set_aquaculture_settings(monkeypatch)
    record = _rule_recommend(_do_crash_event(), "aquaculture")
    assert record is not None
    assert record.status is ActionStatus.PROPOSED
    action = record.action
    assert action.affected_entities[0].object_type == "Pond"
    assert action.affected_entities[0].primary_key == "pond-07"
    assert "fell below" in action.description
    assert "<=" in action.reasoning_trace[0].summary
    # the dusk-nominal reading (6.8 mg/L > 4) stays silent.
    assert _rule_recommend(synthetic.operational_events()[2], "aquaculture") is None


async def test_ac1_approve_execute_completes(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1 lifecycle: propose -> approve -> execute (echo) completes."""
    _set_aquaculture_settings(monkeypatch)
    register_aquaculture_adapter()
    register_aquaculture_handlers()
    record = _rule_recommend(_do_crash_event(), "aquaculture")
    assert record is not None
    approve(record)
    receipt = await execute(record)
    assert receipt["executed"] is True
    assert receipt["vertical"] == "aquaculture"
    assert record.status is ActionStatus.EXECUTED
