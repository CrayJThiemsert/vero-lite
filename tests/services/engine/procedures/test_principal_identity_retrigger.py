"""OQ-6 shared-``Person`` marker — the deferral is RESOLVED (PLAN-0082, s150), TRANSFORMED
from an N-count re-trigger into a shared-type invariant (AC-6).

LINEAGE (the honest record — preserved, not dropped):

* ADR-0026 OQ-6=(b) kept a **per-vertical** ``Person`` while only ONE vertical needed principal
  identity (N=1); genericizing it to a shared/core object was DEFERRED behind a CI trip-wire that
  FAILED the moment a 2nd vertical shipped ``principals`` — so a second per-vertical copy could
  not accrete silently.
* **IT FIRED at N=2** (PLAN-0074 AC-12, s131): ``supply_chain`` shipped ``principals`` (the 2nd
  AT-2 signature — the cold-chain disposition's severity-tier gate needs an SoD-resolvable
  requester + approver). Per the marker's own instruction the deferral was RE-EVALUATED, not
  silently re-armed — resolution: re-confirm the per-vertical shape, file the shared/core
  extraction as a FOLLOW-ON (PLAN-0074 SD-4), and re-arm the trip-wire at N=3.
* **AT N=3 THE EXTRACTION WAS PERFORMED — by PLAN-0082 (this arc), not deferred again.** Step 5
  (#809) shipped the shared generated ``core.Person`` (``ontology/core_v0.yaml`` ->
  ``services/engine/procedures/person_model.py``, re-exported as ``spec.Person``, SD-H=(a));
  procurement + supply_chain migrated onto it HERE (Step 6 — a type re-unification, not a roster
  merge: the two per-org rosters stay distinct DATA); PLAN-0081 lands the 3rd principal-bearing
  vertical (``building_materials``) on the SAME shared home.

So the marker's job **inverts**. The question is no longer "has a 2nd/3rd per-vertical copy
appeared?" — a per-vertical copy can no longer appear: there is exactly ONE generated ``Person``
definition (guarded by
``test_shared_ontology_mechanism.test_exactly_one_pydantic_person_definition``). It is now the
INVARIANT that every principal-bearing vertical's roster parses into that ONE shared type. A
future vertical adding ``principals`` on the shared home is the INTENDED end state — **NOT** a
re-trigger (no re-arm at N=4). A regression that reintroduced a per-vertical ``Person`` fails the
AC-4 grep guard; one that made a vertical's principals a DIFFERENT type fails here.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.engine.procedures import person_model
from services.engine.procedures.spec import Person, load_procedures_file, procedures_path


def _verticals_shipping_principals() -> list[str]:
    """Every top-level vertical whose ``procedures.yaml`` ships human principals (Person identity),
    sorted. Globs only ``verticals/*`` (never the ``.claude/worktrees`` copies)."""
    shipping: list[str] = []
    for path in sorted(Path("verticals").glob("*/procedures.yaml")):
        vertical = path.parent.name
        spec = load_procedures_file(path, vertical=vertical)
        if spec.principals:
            shipping.append(vertical)
    return shipping


def test_spec_person_is_the_shared_generated_type() -> None:
    """PLAN-0082 Step 5/6 (SD-H=(a)): the ``Person`` every roster parses into IS the ONE generated
    shared ``core.Person`` (``person_model.Person``) — the extraction the OQ-6 deferral was
    RESOLVED BY, not a per-vertical convenience type. The single-definition half is guarded by
    ``test_shared_ontology_mechanism.test_exactly_one_pydantic_person_definition``; this pins that
    the spec-layer re-export resolves to it."""
    assert Person is person_model.Person


def test_every_principal_bearing_vertical_parses_into_the_shared_person() -> None:
    """AC-6 (the transformed marker — this REPLACES the N-count re-trigger): every
    principal-bearing vertical's roster parses into the ONE shared generated ``Person``. A future
    vertical adding ``principals`` on the shared home is the INTENDED state (no re-arm at N=4); a
    regression that made a vertical's principals a different type would fail here."""
    shipping = _verticals_shipping_principals()
    assert shipping, "expected at least one principal-bearing vertical"
    for vertical in shipping:
        spec = load_procedures_file(procedures_path(vertical), vertical=vertical)
        assert spec.principals  # the counter matched a non-empty roster
        types = {type(p).__name__ for p in spec.principals}
        assert all(type(p) is person_model.Person for p in spec.principals), (
            f"vertical '{vertical}' parses principals into {sorted(types)} — expected the shared "
            "core.Person (person_model.Person); a per-vertical Person type has regressed"
        )


@pytest.mark.parametrize("vertical", _verticals_shipping_principals())
def test_principals_actually_load(vertical: str) -> None:
    """Guard the rosters themselves: each principal-bearing vertical's principals are real,
    resolvable identities — a requester + at least one approver (the SoD floor), each with a
    ``person_id`` + ``roles``. Both AT-2 signatures resolve their gate against these rosters.
    Parametrized over the discovered set, so a future principal-bearing vertical is covered
    automatically (the INTENDED end state — no marker edit needed)."""
    spec = load_procedures_file(procedures_path(vertical), vertical=vertical)
    assert len(spec.principals) >= 2  # a requester + at least one approver (the SoD floor)
    assert all(p.person_id and p.roles for p in spec.principals)
