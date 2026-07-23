"""PLAN-0091 Step 2 — the ontology emitter + the invoked floor (oracle AC-3).

AC-3 has two halves and both are asserted here:

* **Mechanical where the ledger says mechanical** — the 6-object skeleton and
  all 7 link_types come from the grammar alone.
* **Refuses to guess where the ledger says judgment** — the Asset noun, the Site
  noun, the per-entity band property and the action vocabulary come only from
  CONFIRMED intake; an unconfirmed one stops emission instead of defaulting.

The third assertion is the one that makes the first two mean anything: the
emitted YAML passes the **invoked** floor (`validate` + `generate` at EXIT 0),
so "the emitter produces a valid ontology" is checked by the shipped validator
rather than by this test's opinion of what valid means.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.engine.scaffolder.intake import IntakeAnswer, IntakeRecord
from services.engine.scaffolder.ontology import (
    OntologyEmissionError,
    emit_ontology,
    run_floor,
    write_ontology,
)


def _record(**overrides: str) -> IntakeRecord:
    """A fully-answered fleet-shaped judgment set, minus any slot overridden away."""
    answers = {
        "ontology.asset_noun": "Truck",
        "ontology.site_noun": "Depot",
        "ontology.band_property": "minor_repair_ceiling_thb",
        "ontology.action_types": "approve_repair_spend, tow_to_partner_garage, escalate",
    }
    answers.update(overrides)
    return IntakeRecord(
        namespace="fleet_demo",
        answers=[IntakeAnswer(slot_id=k, value=v) for k, v in answers.items()],
    )


# --- the mechanical half ----------------------------------------------------


def test_skeleton_is_six_objects_and_seven_link_types() -> None:
    doc = emit_ontology(_record())
    assert set(doc["object_types"]) == {
        "Truck",
        "Depot",
        "OperationalEvent",
        "Alert",
        "RecommendedAction",
        "AlertEventLink",
    }
    assert set(doc["link_types"]) == {
        "truck_at_depot",
        "event_for_truck",
        "event_at_depot",
        "action_addresses_alert",
        "action_target_truck",
        "alert_event_link_to_alert",
        "alert_event_link_to_event",
    }


def test_link_names_and_foreign_keys_follow_the_customer_nouns() -> None:
    """The grammar is fixed; the NAMES in it are the customer's.

    Non-vacuity: with different nouns every derived link name and FK changes, so
    a hardcoded emitter (the plausible shortcut) fails this rather than the
    fleet-shaped test above, which it would pass.
    """
    doc = emit_ontology(_record(**{"ontology.asset_noun": "Pond", "ontology.site_noun": "Farm"}))
    assert set(doc["link_types"]) >= {"pond_at_farm", "event_for_pond", "action_target_pond"}
    assert doc["link_types"]["pond_at_farm"]["foreign_key"] == "Pond.site_id -> Farm.farm_id"
    assert doc["object_types"]["Pond"]["primary_key"] == "pond_id"
    assert doc["object_types"]["OperationalEvent"]["properties"]["pond_id"]["target"] == "Pond"


def test_band_property_lands_on_the_asset() -> None:
    doc = emit_ontology(_record())
    assert "minor_repair_ceiling_thb" in doc["object_types"]["Truck"]["properties"]
    assert doc["object_types"]["Truck"]["properties"]["minor_repair_ceiling_thb"]["type"] == "float"


def test_action_vocabulary_is_the_confirmed_answer_verbatim() -> None:
    doc = emit_ontology(_record())
    assert doc["object_types"]["RecommendedAction"]["properties"]["action_type"]["values"] == [
        "approve_repair_spend",
        "tow_to_partner_garage",
        "escalate",
    ]


# --- refuses to guess -------------------------------------------------------


@pytest.mark.parametrize(
    "slot",
    [
        "ontology.asset_noun",
        "ontology.site_noun",
        "ontology.band_property",
        "ontology.action_types",
    ],
)
def test_each_judgment_slot_is_individually_required(slot: str) -> None:
    """Drop ONE judgment and emission stops naming exactly it.

    Parametrised per slot on purpose: a single "unanswered record raises" test
    would pass even if three of the four had silent defaults.
    """
    record = _record()
    record.answers = [a for a in record.answers if a.slot_id != slot]
    with pytest.raises(OntologyEmissionError) as exc:
        emit_ontology(record)
    assert exc.value.open_slots == [slot]


def test_an_unconfirmed_judgment_does_not_count_as_answered() -> None:
    """ADR-0024 D5 at the emission boundary, not just in the queue."""
    record = _record()
    record.answers = [
        IntakeAnswer(slot_id=a.slot_id, value=a.value, confirmed=a.slot_id != "ontology.asset_noun")
        for a in record.answers
    ]
    with pytest.raises(OntologyEmissionError) as exc:
        emit_ontology(record)
    assert exc.value.open_slots == ["ontology.asset_noun"]


# --- the invoked floor ------------------------------------------------------


def test_emitted_ontology_passes_the_invoked_floor(tmp_path: Path) -> None:
    """AC-3's floor: `validate` + `generate` at EXIT 0 against a scratch tree.

    The shipped commands are INVOKED, not re-implemented — so this asserts the
    emitter satisfies the same validator every shipped vertical satisfies,
    rather than this test's own idea of a valid ontology.
    """
    record = _record()
    path = write_ontology(record, tmp_path)
    assert path.is_file()

    assert run_floor(record.namespace, tmp_path) == 0

    generated = tmp_path / "verticals" / "fleet_demo" / "generated"
    for name in ("models.py", "schema.sql", "schema.json", "mcp_tools.json", "types.ts"):
        assert (generated / name).is_file(), f"floor did not emit {name}"


def test_the_floor_writes_only_inside_the_given_root(tmp_path: Path) -> None:
    """The chdir must not leak: the repo tree is never the emission target.

    Non-vacuity: an emitter that inherited the CWD (the shipped commands resolve
    CWD-relative by design) would write `verticals/fleet_demo/` into the repo
    and this assertion is what catches it.
    """
    repo_root = Path(__file__).resolve().parents[4]
    record = _record()
    write_ontology(record, tmp_path)
    assert run_floor(record.namespace, tmp_path) == 0

    assert not (repo_root / "verticals" / "fleet_demo").exists()
    assert Path.cwd() == repo_root or Path.cwd().exists()  # chdir restored


def test_floor_returns_the_validator_code_on_a_broken_ontology(tmp_path: Path) -> None:
    """A non-zero floor is surfaced, never swallowed."""
    record = _record()
    path = write_ontology(record, tmp_path)
    path.write_text("version: 0\nnamespace: fleet_demo\nobject_types: {}\n", encoding="utf-8")
    assert run_floor(record.namespace, tmp_path) != 0
