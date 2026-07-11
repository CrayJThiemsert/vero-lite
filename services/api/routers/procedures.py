"""Read-only procedure viewer API (PLAN-0039 Step 1; ADR-0024 D8 read surface).

Exposes ``GET /procedures`` — every shipped procedure across **all discovered
verticals**, loaded via ``load_procedures`` and decomposed exactly as the engine
validates it (ADR-016 D2 typed spec + the typed ``facet:`` amendment), annotated
with the catalog **archetype** label per procedure (OQ-5).

Read-only by construction: it iterates ``registry.verticals()`` (the ADR-0023
discovery registry — NOT the single ``OCT_VERTICAL`` the rest of the console
keys off) and performs NO mutation, NO DB access, and NO LLM call (PLAN-0039
AC-1 / AC-6). It is the **read-mode of the one review surface** PLAN-0040
extends to an edit-mode generator gate (ADR-0024 D8).
"""

from fastapi import APIRouter

from services.api.models.procedures import (
    ProceduresResponse,
    ProcedureView,
    VerticalProceduresView,
)
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry

router = APIRouter(tags=["procedures"])

# Catalog-derived procedure_id → archetype map (OQ-5 option a — an explicit map,
# server-side, in one place). Canonical source is
# docs/conventions/procedure-archetypes.md; this is a read-only derived MIRROR
# (CLAUDE.md §4 canonical→derived). A 5th vertical extends this map ADDITIVELY —
# the catalog grows first, the map mirrors it; never the reverse. Eight shipped
# procedures across the four instrumented verticals (PLAN-0039 fact-pack #1:
# procurement ships two manual; energy / supply_chain / aquaculture one each) plus
# the PLAN-0055 Step 8 schedule-triggered AT-2 variant, the PLAN-0056 Step 8
# event-triggered AT-2 variant, and the PLAN-0065 Step 4 schedule-triggered AT-3
# variant (all procurement).
PROCEDURE_ARCHETYPES: dict[str, str] = {
    "substation_health_sweep": "AT-1",  # energy — anomaly→action
    "cold_chain_excursion_sweep": "AT-1",  # supply_chain — anomaly→action
    "morning_pond_health_round": "AT-1b",  # aquaculture — AT-1 + watch + summary
    "emergency_sourcing_round": "AT-2",  # procurement — request→approve→fulfill (hero)
    "low_stock_reorder_round": "AT-3",  # procurement — monitor→reorder (calm-path)
    "scheduled_emergency_sourcing_round": "AT-2",  # procurement — AT-2 on a nightly clock (S1)
    "scheduled_low_stock_reorder_round": "AT-3",  # procurement — AT-3 on a nightly clock (S1)
    "event_emergency_sourcing_round": "AT-2",  # procurement — AT-2 on an asset-failure event
}

# A procedure absent from the catalog map renders with this sentinel rather than
# failing the read — surfacing "this shipped without a catalogued archetype"
# instead of a 500 (defensive; all seven shipped procedures are mapped today).
_UNCATALOGUED = "uncatalogued"


@router.get("/procedures", response_model=ProceduresResponse)
async def list_procedures() -> ProceduresResponse:
    """Return every discovered vertical's procedures, archetype-annotated.

    A read-only projection of ``load_procedures`` over ``registry.verticals()``;
    no mutation, no DB, no LLM (PLAN-0039 AC-1 / AC-6).
    """
    verticals: list[VerticalProceduresView] = []
    for vertical in registry.verticals():
        spec = load_procedures(vertical)
        procedures = [
            ProcedureView.model_validate(
                {
                    **proc.model_dump(),
                    "archetype": PROCEDURE_ARCHETYPES.get(proc.procedure_id, _UNCATALOGUED),
                }
            )
            for proc in spec.procedures
        ]
        verticals.append(
            VerticalProceduresView(
                vertical=spec.vertical,
                namespace=spec.namespace,
                version=spec.version,
                agents=spec.agents,
                procedures=procedures,
            )
        )
    return ProceduresResponse(verticals=verticals)
