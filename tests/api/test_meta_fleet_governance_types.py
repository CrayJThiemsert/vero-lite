"""PLAN-0109 AC-2 — fleet's ``GET /meta`` advertises the three ruled governance types.

The types are ``RepairCase``, ``RepairCaseQuote`` and ``RepairCaseAcceptedQuote`` (SD-B,
RULED — Cray, typed 2026-08-18). Declaring them in the ontology YAML is what makes
``/meta`` advertise them and what gives the NL-query translator their names; nothing
else contributes to that vocabulary (PLAN-0109 F4).

**Witnessed RED before the YAML edit.** At baseline this module fails on the missing
type names — the same read, pointed at an ontology that does not declare them. That
failure is the evidence the assertions below can fail at all.

**What this does NOT prove.** Declared is not served: until the fleet adapter reads the
tables (PLAN-0109 Step 3), a question about these types gets the honest no-records
answer. That half is AC-6/AC-8's, not this file's.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.db.repair_case import CASE_STATUSES, WORK_TYPES

_VERTICAL = "fleet_maintenance"

#: The ruled set, each with the primary key its table is keyed on.
_RULED_PRIMARY_KEYS = {
    "RepairCase": "case_id",
    "RepairCaseQuote": "quote_id",
    "RepairCaseAcceptedQuote": "accepted_id",
}

#: The refs that make "the screens are related" machine-readable (AC-1). A ref is what
#: ``_describe_ontology`` renders as ``(ref->Target)`` in the translate prompt.
_RULED_REFS = {
    ("RepairCase", "truck_id"): "Truck",
    ("RepairCaseQuote", "case_id"): "RepairCase",
    ("RepairCaseAcceptedQuote", "case_id"): "RepairCase",
    ("RepairCaseAcceptedQuote", "quote_id"): "RepairCaseQuote",
}


async def _fleet_types(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> dict[str, dict[str, Any]]:
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    response = await client.get("/meta")
    assert response.status_code == 200
    body = response.json()
    # Control: the monkeypatch reached the route. Without it every assertion below
    # would be reading the default vertical's ontology and failing for the wrong reason.
    assert body["vertical"] == _VERTICAL
    return {obj["name"]: obj for obj in body["object_types"]}


def _property(obj: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next((p for p in obj["properties"] if p["name"] == name), None)


async def test_meta_advertises_each_ruled_type_with_its_primary_key(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    types = await _fleet_types(client, monkeypatch)

    # Positive control: the same read finds a type that has always been declared, so
    # a missing ruled type below is about the ontology, not about the reader.
    assert types["Truck"]["primary_key"] == "truck_id"

    missing = sorted(set(_RULED_PRIMARY_KEYS) - set(types))
    assert not missing, f"/meta does not advertise {missing}; it advertises {sorted(types)}"

    wrong = {
        name: types[name]["primary_key"]
        for name, key in _RULED_PRIMARY_KEYS.items()
        if types[name]["primary_key"] != key
    }
    assert not wrong, f"primary keys differ from the tables': {wrong}"


async def test_meta_carries_the_relational_refs(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    types = await _fleet_types(client, monkeypatch)
    found: dict[tuple[str, str], str | None] = {}
    for type_name, prop_name in _RULED_REFS:
        prop = _property(types[type_name], prop_name) if type_name in types else None
        found[(type_name, prop_name)] = prop["target"] if prop else None
    assert found == _RULED_REFS, f"ref targets advertised on /meta: {found}"


async def test_declared_enums_equal_the_values_the_code_writes(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The YAML's enum values and the tuples the write path validates against stay equal.

    An enum makes a filter like ``status == open`` reliable for the translator — and it
    is also a second statement of a fact the code already owns. This test is what keeps
    the two from drifting: a status added in ``services/db/repair_case.py`` and not in
    the ontology would make every question about it come back empty.
    """
    types = await _fleet_types(client, monkeypatch)
    assert "RepairCase" in types, f"RepairCase is not advertised; /meta has {sorted(types)}"
    case = types["RepairCase"]
    status = _property(case, "status")
    work_type = _property(case, "work_type")
    declared = {
        "status": sorted(status["enum"] or []) if status else None,
        "work_type": sorted(work_type["enum"] or []) if work_type else None,
    }
    written = {"status": sorted(CASE_STATUSES), "work_type": sorted(WORK_TYPES)}
    assert declared == written, f"ontology enums {declared} != code tuples {written}"
