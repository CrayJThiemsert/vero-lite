"""Offline gate for the read-only ``GET /procedures`` viewer endpoint (PLAN-0039).

The offline test is the GATE (CLAUDE.md §8): ``GET /procedures`` returns every
discovered vertical's procedures, each round-trips ``load_procedures``, and the
catalog archetype label is attached for all shipped procedures across the six
procedure-bearing verticals (fact-pack #1: procurement ships five; supply_chain
ships two; energy / aquaculture one each; building_materials ships one — the
PLAN-0081 governed-credit hero; fleet_maintenance ships two — the PLAN-0086
governed-repair hero and the PLAN-0089 PM calm path). No LLM, no DB, no mutation. A live preview is
*evidence* (Step 5), not the gate.

The archetype label is looked up on the ``(vertical, procedure_id)`` PAIR, never
the bare id — a bare id is unique only within a vertical. See
``test_same_procedure_id_in_two_verticals_keeps_its_own_archetype``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.main import app
from services.api.routers import procedures as procedures_router
from services.engine.discovery import discover_and_register
from services.engine.procedures.spec import VerticalProcedures, load_procedures, procedures_path
from services.engine.registry import registry

# The twelve shipped procedures, vertical → {procedure_id: archetype} (fact-pack
# #1 / docs/conventions/procedure-archetypes.md). procurement ships five:
# two manual + the PLAN-0055 Step 8 schedule-triggered AT-2 variant + the
# PLAN-0056 Step 8 event-triggered AT-2 variant + the PLAN-0065 Step 4
# schedule-triggered AT-3 calm-path variant.
#
# Vertical-keyed, and now load-bearing twice: the per-procedure archetype assertion
# below AND the `(vertical, procedure_id)` set-equality pin on PROCEDURE_ARCHETYPES
# (`test_archetype_map_is_keyed_by_vertical_procedure_pair`). A bare `procedure_id`
# is NOT a unique key across verticals — see that test's docstring.
_EXPECTED: dict[str, dict[str, str]] = {
    "energy": {"substation_health_sweep": "AT-1"},
    "supply_chain": {
        "cold_chain_excursion_sweep": "AT-1",
        # PLAN-0074 — the 2nd AT-2 SIGNATURE (non-money authority: severity_tier, not doa_tier).
        "cold_chain_excursion_disposition": "AT-2",
    },
    "aquaculture": {"morning_pond_health_round": "AT-1b"},
    "procurement": {
        "emergency_sourcing_round": "AT-2",
        "low_stock_reorder_round": "AT-3",
        # PLAN-0055 Step 8 — the schedule-triggered AT-2 variant (nightly, headless).
        "scheduled_emergency_sourcing_round": "AT-2",
        # PLAN-0065 Step 4 — the schedule-triggered AT-3 calm-path variant (nightly, headless).
        "scheduled_low_stock_reorder_round": "AT-3",
        # PLAN-0056 Step 8 — the event-triggered AT-2 variant (asset-failure auto-fire).
        "event_emergency_sourcing_round": "AT-2",
    },
    "building_materials": {
        # PLAN-0081 — the 3rd AT-2 SIGNATURE (governed credit release; the money doa_tier ladder
        # reused unchanged, the criterion vocabulary grown by {kyc, overdue_ar, blacklist}).
        "governed_credit_release": "AT-2",
    },
    "fleet_maintenance": {
        # PLAN-0086 — the timed manual scaffold (6th vertical). The money doa_tier ladder is reused
        # unchanged again (repair spend, THB); notable as the first vertical wired with the
        # PLAN-0085 gate advisory ON from day one, not as a new AT-2 signature.
        "governed_repair_approval": "AT-2",
        # PLAN-0089 — the AT-3 PM calm path: the 2nd vertical to carry AT-3, and the first instance
        # banding a NON-stock measure (odometer km ABOVE a service-due point, vs procurement's stock
        # BELOW a reorder point). The inverted direction is the point: AT-3's signature is the
        # per-entity band + single human gate, not the stock semantics.
        "pm_service_round": "AT-3",
    },
}

# The gate_kinds with a LIVE shipped consumer across the four verticals, with zero
# fixtures (PLAN-0039 finding #4 / AC-5). PLAN-0070 re-themed energy's judge — the
# last env_band consumer — to a per-feeder `threshold_field` band, so `env_band` (a
# valid GateKind) now has NO shipped YAML consumer; the engine path stays test-covered
# (test_env_band_evaluate.py). PLAN-0074 adds `severity_tier` — the 4th AT-2 gate kind,
# whose first (and only) shipped consumer is supply_chain's disposition `approve` step.
_LIVE_GATE_KINDS = {
    "in_file_band",
    "rule_gate",
    "scored_rule",
    "doa_tier",
    "severity_tier",
    "none",
}


@pytest.fixture
async def all_verticals_client() -> AsyncIterator[AsyncClient]:
    """A client with EVERY discovered vertical registered.

    The app lifespan (which calls ``discover_and_register``) does not run under
    httpx.ASGITransport — so we discover explicitly here. The autouse
    ``_reset_registry`` fixture (tests/conftest.py) wipes the registry first, so
    this re-discovers deterministically.
    """
    discover_and_register()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def test_procedures_returns_all_discovered_verticals_and_archetypes(
    all_verticals_client: AsyncClient,
) -> None:
    """Every discovered vertical's procedures round-trip load_procedures, each
    carrying the correct catalog archetype — all twelve across the six procedure-bearing
    verticals (procurement ships five: two manual + scheduled AT-2 + event AT-2 + scheduled AT-3;
    supply_chain ships two: the AT-1 sweep + the PLAN-0074 AT-2 disposition; energy + aquaculture
    one each; building_materials ships one: the PLAN-0081 AT-2 governed-credit hero;
    fleet_maintenance ships two: the PLAN-0086 AT-2 governed-repair hero + the
    PLAN-0089 AT-3 PM calm path)."""
    response = await all_verticals_client.get("/procedures")
    assert response.status_code == 200
    payload = response.json()

    returned = {v["vertical"] for v in payload["verticals"]}
    # The endpoint loops registry.verticals() (ADR-0023 discovery), not OCT_VERTICAL —
    # but SKIPS any discovered vertical shipping no procedures.yaml (a Tier-1 Mirror
    # scaffold, ADR-0015 D2), which has no procedures to project. So `returned` is the
    # spec-BEARING subset of the discovered set, never a superset.
    assert returned <= set(registry.verticals())
    assert returned == set(_EXPECTED)

    total = 0
    for ventry in payload["verticals"]:
        vname = ventry["vertical"]
        spec = load_procedures(vname)
        # the payload round-trips load_procedures: same procedure ids, in order
        assert [p["procedure_id"] for p in ventry["procedures"]] == [
            p.procedure_id for p in spec.procedures
        ]
        for proc in ventry["procedures"]:
            assert proc["archetype"] == _EXPECTED[vname][proc["procedure_id"]]
            total += 1
    # twelve procedures across six verticals: the eleven prior (fact-pack #1's five + the
    # PLAN-0055 scheduled AT-2 + the PLAN-0056 event AT-2 + the PLAN-0065 scheduled AT-3
    # + the PLAN-0074 supply_chain disposition + the PLAN-0081 building_materials
    # governed-credit hero + the PLAN-0086 fleet_maintenance governed-repair hero) + the
    # PLAN-0089 fleet_maintenance PM calm path (the SECOND procedure on an existing
    # vertical — no new vertical, and AT-3's first non-stock band)
    assert total == 12


class _SpecLessFixtureAdapter:
    """A minimal discovered-but-spec-less vertical: a registered adapter with NO
    ``procedures.yaml``. The endpoint skips it at the ``procedures_path(...).exists()``
    check before touching the adapter, so only ``vertical_name`` is load-bearing."""

    vertical_name = "z_spec_less_fixture"

    async def fetch_objects(self, *args: object, **kwargs: object) -> list[dict[str, object]]:
        return []

    async def fetch_links(self, *args: object, **kwargs: object) -> list[dict[str, object]]:
        return []

    async def stream_events(
        self, *args: object, **kwargs: object
    ) -> AsyncIterator[dict[str, object]]:
        return
        yield  # pragma: no cover - never reached; makes this an async generator

    async def health_check(self) -> dict[str, object]:
        return {"status": "ok", "vertical": self.vertical_name, "synthetic": True}


async def test_procedures_skips_discovered_vertical_without_a_spec(
    all_verticals_client: AsyncClient,
) -> None:
    """A discovered vertical shipping NO procedures.yaml is SKIPPED, not a 500.

    Regression guard: ``vero-lite new-vertical`` scaffolds a Tier-1 Mirror (ADR-0015
    D2) — ontology + adapter + handlers, no spec — and ADR-0023 import-scan discovery
    registers it regardless. Before this fix ``GET /procedures`` called
    ``load_procedures`` unconditionally and died with FileNotFoundError on the first
    such vertical, breaking the read surface for every OTHER vertical.

    RE-POINTED (PLAN-0081 AC-8): building_materials WAS the shipped spec-less vertical
    that exercised this path, but the governed-credit hero gave it a ``procedures.yaml``.
    No real discovered vertical is spec-less now (vet_clinic is a README-only parked dir
    ``discover_and_register`` cannot import — no data_adapter/handlers). So the skip path
    is exercised via a FIXTURE spec-less vertical (an adapter, no spec) registered here —
    the guard's own ``:131`` alternative. Do NOT delete it: the skip path it protects
    stays live code the moment a new Tier-1 Mirror is scaffolded.
    """
    registry.register_adapter(_SpecLessFixtureAdapter())  # type: ignore[arg-type]  # duck-typed
    discovered = set(registry.verticals())
    spec_less = {v for v in discovered if not procedures_path(v).exists()}
    assert (
        "z_spec_less_fixture" in spec_less
    ), "the fixture spec-less vertical must exercise the skip path"

    response = await all_verticals_client.get("/procedures")
    assert response.status_code == 200
    returned = {v["vertical"] for v in response.json()["verticals"]}
    assert not (spec_less & returned)  # skipped, never projected
    assert (discovered - spec_less) == returned  # every spec-BEARING vertical still shows


async def test_procedures_all_live_gate_kinds_present(
    all_verticals_client: AsyncClient,
) -> None:
    """The typed facet decomposition serializes through, and every gate_kind with a live
    shipped consumer appears in the real data with zero fixtures (AC-5 / finding #4).
    Post-PLAN-0070 that is five kinds — `env_band` retired its last YAML consumer (energy)."""
    payload = (await all_verticals_client.get("/procedures")).json()
    gate_kinds = {
        step["facet"]["decision_condition"]["gate_kind"]
        for ventry in payload["verticals"]
        for proc in ventry["procedures"]
        for step in proc["steps"]
        if (step.get("facet") or {}).get("decision_condition")
    }
    assert gate_kinds == _LIVE_GATE_KINDS


async def test_procedures_typed_authoritative_band_passes_through(
    all_verticals_client: AsyncClient,
) -> None:
    """The authoritative typed band (the source of truth, AC-4) is rendered as
    loaded — in-file bands carry their threshold/direction/watch_margin, env
    bands carry their env_var — distinct from the non-authoritative facet prose."""
    payload = (await all_verticals_client.get("/procedures")).json()
    by_vertical = {v["vertical"]: v for v in payload["verticals"]}

    # aquaculture judge: in-file authored band (the source of truth on the Step).
    # PLAN-0068: the band is now per-entity (`threshold_field: do_floor`), so the
    # rendered scalar `threshold` is None; `direction`/`watch_margin` stay authored.
    aqua = by_vertical["aquaculture"]["procedures"][0]
    aqua_judge = next(s for s in aqua["steps"] if s["step_id"] == "judge")
    assert aqua_judge["threshold"] is None
    # PLAN-0068: the scalar threshold is None but the per-entity band column IS surfaced in
    # the payload — the view-procedures decision facet renders it (do not silently drop it).
    assert aqua_judge["threshold_field"] == "do_floor"
    assert aqua_judge["direction"] == "below"
    assert aqua_judge["watch_margin"] == 1.0
    assert aqua_judge["facet"]["decision_condition"]["gate_kind"] == "in_file_band"

    # energy judge: PLAN-0070 — per-feeder in-file band (`threshold_field: rated_current_a`),
    # so the rendered scalar `threshold` is None; the band column + direction stay authored.
    energy_judge = next(
        s for s in by_vertical["energy"]["procedures"][0]["steps"] if s["step_id"] == "judge"
    )
    assert energy_judge["threshold"] is None
    assert energy_judge["threshold_field"] == "rated_current_a"
    assert energy_judge["direction"] == "above"
    energy_dc = energy_judge["facet"]["decision_condition"]
    assert energy_dc["gate_kind"] == "in_file_band"


async def test_archetype_map_is_keyed_by_vertical_procedure_pair() -> None:
    """The catalog mirror is keyed on ``(vertical, procedure_id)`` — a set-equality
    tripwire against BOTH the shipped specs and this module's ``_EXPECTED`` pin.

    A bare-``procedure_id`` key is unrepresentable here by construction: the assertion
    compares against pairs, so a map that drops the vertical fails outright. The set
    equality (not a subset check) is the anti-rot half — a procedure that ships without
    a catalog entry, and a map entry naming a vertical/procedure that no longer ships,
    both go RED instead of silently rendering ``uncatalogued`` in the console.
    """
    discover_and_register()
    shipped = {
        (vertical, proc.procedure_id)
        for vertical in registry.verticals()
        if procedures_path(vertical).exists()
        for proc in load_procedures(vertical).procedures
    }
    assert set(procedures_router.PROCEDURE_ARCHETYPES) == shipped
    assert procedures_router.PROCEDURE_ARCHETYPES == {
        (vertical, pid): archetype
        for vertical, procs in _EXPECTED.items()
        for pid, archetype in procs.items()
    }


async def test_same_procedure_id_in_two_verticals_keeps_its_own_archetype(
    all_verticals_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two verticals shipping the SAME bare ``procedure_id`` each get their OWN archetype.

    Regression guard for a latent cross-vertical collision. ``procedure_id`` is unique
    only WITHIN a vertical (``services/engine/procedures/schedules.py:31-33``, whose
    ``ScheduleState`` already encodes the pair as its ``UniqueConstraint``), but the
    archetype mirror used to be a ``dict[str, str]`` keyed on the bare id, GLOBALLY across
    verticals. Two verticals naming a procedure identically — e.g. both shipping a calm
    path called ``low_stock_reorder_round`` — would silently collide: one vertical's label
    served for the other's procedure, no error, no 500, just a wrong badge in the console.

    Built end-to-end through the real ``list_procedures`` handler (not just the lookup
    helper) on a synthetic two-vertical registry whose specs deliberately COLLIDE on
    ``_SHARED_ID`` while carrying different archetypes. Under bare-id keying the map
    cannot even express both entries, so this goes RED.
    """
    shared_id = "colliding_round"
    donor = load_procedures("procurement")
    proc = next(p for p in donor.procedures if p.procedure_id == "low_stock_reorder_round")
    # model_copy, not re-validation: we are re-labelling an ALREADY-VALID procedure, and
    # the spec's cross-ref validators are not what is under test here.
    collided = proc.model_copy(update={"procedure_id": shared_id})
    specs: dict[str, VerticalProcedures] = {
        "v_alpha": donor.model_copy(update={"vertical": "v_alpha", "procedures": [collided]}),
        "v_beta": donor.model_copy(update={"vertical": "v_beta", "procedures": [collided]}),
    }

    monkeypatch.setattr(registry, "verticals", lambda: sorted(specs))
    monkeypatch.setattr(procedures_router, "load_procedures", lambda v: specs[v])
    # every synthetic vertical is spec-BEARING, so none is skipped at the existence check
    monkeypatch.setattr(procedures_router, "procedures_path", lambda v: procedures_path("energy"))
    monkeypatch.setattr(
        procedures_router,
        "PROCEDURE_ARCHETYPES",
        {("v_alpha", shared_id): "AT-3", ("v_beta", shared_id): "AT-1"},
    )

    payload = (await all_verticals_client.get("/procedures")).json()
    rendered = {
        (ventry["vertical"], proc["procedure_id"]): proc["archetype"]
        for ventry in payload["verticals"]
        for proc in ventry["procedures"]
    }
    assert rendered == {("v_alpha", shared_id): "AT-3", ("v_beta", shared_id): "AT-1"}


def test_archetype_for_is_vertical_scoped() -> None:
    """The lookup helper never answers from the bare id alone.

    The same ``procedure_id`` under a DIFFERENT vertical is a miss (``uncatalogued``),
    not a silent hit on some other vertical's label — the unit-level statement of the
    end-to-end guard above.
    """
    assert procedures_router.archetype_for("procurement", "low_stock_reorder_round") == "AT-3"
    assert procedures_router.archetype_for("energy", "substation_health_sweep") == "AT-1"
    # a real procedure_id, asked for under a vertical that does not ship it
    assert (
        procedures_router.archetype_for("energy", "low_stock_reorder_round")
        == procedures_router._UNCATALOGUED
    )
    assert procedures_router.archetype_for("procurement", "no_such_procedure") == "uncatalogued"


async def test_procedures_advertised_in_openapi(all_verticals_client: AsyncClient) -> None:
    """GET /openapi.json advertises the new read-only /procedures route."""
    paths = (await all_verticals_client.get("/openapi.json")).json()["paths"]
    assert "/procedures" in paths
