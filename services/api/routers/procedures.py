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
from services.engine.procedures.spec import load_procedures, procedures_path
from services.engine.registry import registry

router = APIRouter(tags=["procedures"])

# Catalog-derived (vertical, procedure_id) → archetype map (OQ-5 option a — an
# explicit map, server-side, in one place). Canonical source is
# docs/conventions/procedure-archetypes.md; this is a read-only derived MIRROR
# (CLAUDE.md §4 canonical→derived). A 7th vertical extends this map ADDITIVELY —
# the catalog grows first, the map mirrors it; never the reverse. Twelve shipped
# procedures across the six procedure-bearing verticals (PLAN-0039 fact-pack #1:
# procurement ships two manual; energy / supply_chain / aquaculture one each) plus
# the PLAN-0055 Step 8 schedule-triggered AT-2 variant, the PLAN-0056 Step 8
# event-triggered AT-2 variant, the PLAN-0065 Step 4 schedule-triggered AT-3
# variant (all procurement), the PLAN-0074 supply_chain AT-2 disposition, the
# PLAN-0081 building_materials AT-2 governed-credit hero, the PLAN-0086
# fleet_maintenance AT-2 governed-repair hero, and the PLAN-0089
# fleet_maintenance AT-3 PM calm path.
#
# KEYED ON THE PAIR, NOT THE BARE ID. A `procedure_id` is unique only WITHIN a
# vertical — the spec cross-refs resolve per-vertical, and `ScheduleState` already
# encodes that natural identity as `UniqueConstraint(vertical, procedure_id)`
# (services/engine/procedures/schedules.py:31-33). A bare-id map therefore had a
# latent cross-vertical collision: two verticals shipping the same procedure name
# (a second `low_stock_reorder_round` calm path is the obvious near-miss) would
# silently serve one vertical's archetype label for the other's procedure, with no
# error. The pair key makes that unrepresentable, and matches the canonical
# catalog, which has always written these as `<vertical>.<procedure_id>`.
PROCEDURE_ARCHETYPES: dict[tuple[str, str], str] = {
    ("energy", "substation_health_sweep"): "AT-1",  # anomaly→action
    ("supply_chain", "cold_chain_excursion_sweep"): "AT-1",  # anomaly→action
    ("aquaculture", "morning_pond_health_round"): "AT-1b",  # AT-1 + watch + summary
    ("procurement", "emergency_sourcing_round"): "AT-2",  # request→approve→fulfill (hero)
    ("procurement", "low_stock_reorder_round"): "AT-3",  # monitor→reorder (calm-path)
    ("procurement", "scheduled_emergency_sourcing_round"): "AT-2",  # AT-2 on a nightly clock (S1)
    ("procurement", "scheduled_low_stock_reorder_round"): "AT-3",  # AT-3 on a nightly clock (S1)
    ("procurement", "event_emergency_sourcing_round"): "AT-2",  # AT-2 on an asset-failure event
    # supply_chain — the 2nd AT-2 SIGNATURE (PLAN-0074): a governed cold-chain disposition whose
    # authority quantity is NON-MONEY (severity_tier, not doa_tier). The procurement entries above
    # are trigger variants of ONE signature; this is a second one.
    ("supply_chain", "cold_chain_excursion_disposition"): "AT-2",
    # building_materials — the 3rd AT-2 SIGNATURE (PLAN-0081): a governed credit release. The money
    # doa_tier ladder is REUSED unchanged; only the criterion vocabulary grows ({kyc, overdue_ar,
    # blacklist}). A genuinely third signature, on a fifth vertical.
    ("building_materials", "governed_credit_release"): "AT-2",
    # fleet_maintenance — PLAN-0086 (the timed manual scaffold). The money doa_tier ladder is REUSED
    # unchanged AGAIN (repair spend in THB); no new authority quantity, no new trace kind. Notable
    # not as a new signature but as the first vertical wired with the PLAN-0085 gate advisory ON
    # from day one (L-B: readable on day one).
    ("fleet_maintenance", "governed_repair_approval"): "AT-2",
    # fleet_maintenance — PLAN-0089, the AT-3 calm path. The 2nd vertical to carry AT-3 and the
    # first instance banding a NON-stock measure (odometer km above a service-due point, vs
    # procurement's stock below a reorder point) — which is what showed AT-3's signature is the
    # per-entity band + single human gate, not the stock semantics.
    ("fleet_maintenance", "pm_service_round"): "AT-3",
}

# A procedure absent from the catalog map renders with this sentinel rather than
# failing the read — surfacing "this shipped without a catalogued archetype"
# instead of a 500 (defensive; all twelve shipped procedures are mapped today).
_UNCATALOGUED = "uncatalogued"


def archetype_for(vertical: str, procedure_id: str) -> str:
    """The catalog archetype label for one procedure, scoped to its vertical.

    The single read point of :data:`PROCEDURE_ARCHETYPES`. Scoping is the whole
    contract: `procedure_id` is unique only within a vertical, so the lookup key is
    the pair — never the bare id (see the map comment). An uncatalogued procedure
    gets :data:`_UNCATALOGUED` rather than a 500.
    """
    return PROCEDURE_ARCHETYPES.get((vertical, procedure_id), _UNCATALOGUED)


@router.get("/procedures", response_model=ProceduresResponse)
async def list_procedures() -> ProceduresResponse:
    """Return every discovered vertical's procedures, archetype-annotated.

    A read-only projection of ``load_procedures`` over ``registry.verticals()``;
    no mutation, no DB, no LLM (PLAN-0039 AC-1 / AC-6). A discovered vertical that
    ships NO ``procedures.yaml`` is skipped — see the loop comment.
    """
    verticals: list[VerticalProceduresView] = []
    for vertical in registry.verticals():
        # A discovered vertical need NOT ship a procedures spec: `vero-lite new-vertical`
        # scaffolds a Tier-1 Mirror (ADR-0015 D2) — ontology + adapter + handlers, but no
        # procedures.yaml — and ADR-0023 import-scan discovery registers it regardless. Such
        # a vertical has no procedures to project, so SKIP it rather than 500 this read
        # surface for every OTHER vertical (the whole endpoint used to die on the first
        # spec-less vertical). An EXPLICIT existence check, NOT a swallowed
        # FileNotFoundError, so a genuinely unreadable / malformed spec still raises.
        if not procedures_path(vertical).exists():
            continue
        spec = load_procedures(vertical)
        procedures = [
            ProcedureView.model_validate(
                {
                    **proc.model_dump(),
                    "archetype": archetype_for(spec.vertical, proc.procedure_id),
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
