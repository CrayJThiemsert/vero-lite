"""PLAN-0061 Step 4 (AC-6): both v1 shapes end-to-end through ``run_procedure``
over REAL shipped ontologies (SD-3 — test-module fixtures; zero vertical-file
changes; these procedures double as the authoring examples for the Phase-3
migration PLAN).

Shape 1 (latest-per-group) runs over the REAL energy ontology's
``event_emitted_by_asset`` link; shape 2 (equi-join enrichment + ``on`` override
+ ``fuse``) over the REAL procurement ontology's ``po_from_quotation`` link —
read-only ontology loads, fake adapters, the production ``run_procedure`` path.
Deterministic, offline, no LLM (LOCKED-6).
"""

from __future__ import annotations

from typing import Any

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
)


class _FakeAdapter:
    """Duck-typed adapter: the executor only calls ``fetch_objects``."""

    def __init__(self, vertical: str, data: dict[str, list[dict[str, Any]]]) -> None:
        self.vertical_name = vertical
        self._data = data

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._data.get(object_type, [])]


def _agent() -> Agent:
    return Agent(
        agent_id="fixture_agent",
        name="Fixture Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),
    )


def _procedure(input_: dict[str, Any]) -> Procedure:
    return Procedure(
        procedure_id="join-fixture-round",
        title="Join fixture round",
        goal="Exercise the Q4 declared join/projection grammar end-to-end.",
        run_by="fixture_agent",
        steps=[
            Step(
                step_id="read_joined",
                name="Declared multi-read",
                kind=StepKind.QUERY,
                input=StepInput.model_validate(input_),
            )
        ],
    )


def _executors(vertical: str, data: dict[str, list[dict[str, Any]]]) -> dict[StepKind, Any]:
    meta = load_ontology_meta(vertical)  # the REAL shipped ontology, read-only
    return {
        StepKind.QUERY: QueryStepExecutor(
            adapter=_FakeAdapter(vertical, data),
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        )
    }


# --------------------------------------------------------------------------- #
# Shape 1 — latest-per-group over the REAL energy ontology
# --------------------------------------------------------------------------- #


async def test_shape1_latest_per_group_end_to_end_on_energy() -> None:
    data = {
        "OperationalEvent": [
            {
                "event_id": "evt-1",
                "event_type": "reading",
                "measured_value": 88.0,
                "occurred_at": "2026-07-08T06:00:00Z",
                "asset_id": "asset-battery-01",
            },
            {
                "event_id": "evt-2",
                "event_type": "reading",
                "measured_value": 96.5,
                "occurred_at": "2026-07-09T06:00:00Z",
                "asset_id": "asset-battery-01",
            },
            {
                "event_id": "evt-3",
                "event_type": "reading",
                "measured_value": 42.0,
                "occurred_at": "2026-07-09T06:00:00Z",
                "asset_id": "asset-inverter-02",
            },
            # missing asset_id — excluded + counted, never guessed
            {"event_id": "evt-4", "occurred_at": "2026-07-09T09:00:00Z", "measured_value": 1.0},
        ]
    }
    result = await run_procedure(
        _procedure(
            {
                "reads": ["OperationalEvent"],
                "project": {
                    "latest_per": "event_emitted_by_asset",
                    "order_by": "occurred_at",
                    "fields": {"measured_value": "latest_reading"},
                },
            }
        ),
        _agent(),
        _executors("energy", data),
        vertical="energy",
        run_id="fixture-shape1",
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    artifact = result.step_results[-1].artifact
    assert artifact is not None
    rows = artifact["output_set"]
    by_asset = {row["asset_id"]: row for row in rows}
    assert set(by_asset) == {"asset-battery-01", "asset-inverter-02"}
    assert by_asset["asset-battery-01"]["event_id"] == "evt-2"  # the latest reading
    assert by_asset["asset-battery-01"]["latest_reading"] == 96.5  # renamed
    assert all("measured_value" not in row for row in rows)


# --------------------------------------------------------------------------- #
# Shape 2 — equi-join enrichment over the REAL procurement ontology
# --------------------------------------------------------------------------- #

# The REAL declared PO∩Quotation property collisions are currency / part_no /
# supplier_id (quote_id is the exempt equal-named join key) — the rename map
# must cover exactly these for the load gate to accept the join (SD-1 rule).
_QUOTE_RENAMES = {
    "currency": "quote_currency",
    "part_no": "quote_part_no",
    "supplier_id": "quote_supplier_id",
}

_PROCUREMENT_DATA = {
    "PurchaseOrder": [
        {
            "po_id": "po-spindle-01",
            "part_no": "part-spindle-01",
            "supplier_id": "sup-rfq-01",
            "quote_id": "quote-spindle-rfq",
            "amount": 2150000.0,
            "currency": "THB",
            "status": "pending_approval",
        },
        {
            "po_id": "po-filter-02",
            "part_no": "part-filter-02",
            "supplier_id": "sup-contract-01",
            "quote_id": "quote-filter-contract",
            "amount": 45000.0,
            "currency": "THB",
            "status": "pending_approval",
        },
    ],
    "Quotation": [
        {
            "quote_id": "quote-spindle-rfq",
            "part_no": "part-spindle-01",
            "supplier_id": "sup-rfq-01",
            "price": 2150000.0,
            "currency": "THB",
            "lead_time": 3,
            "on_contract": False,
        },
        {
            "quote_id": "quote-filter-contract",
            "part_no": "part-filter-02",
            "supplier_id": "sup-contract-01",
            "price": 45000.0,
            "currency": "THB",
            "lead_time": 14,
            "on_contract": True,
        },
    ],
}


async def test_shape2_declared_link_join_end_to_end_on_procurement() -> None:
    result = await run_procedure(
        _procedure(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": _QUOTE_RENAMES},
            }
        ),
        _agent(),
        _executors("procurement", _PROCUREMENT_DATA),
        vertical="procurement",
        run_id="fixture-shape2",
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    artifact = result.step_results[-1].artifact
    assert artifact is not None
    rows = artifact["output_set"]
    assert len(rows) == 2
    spindle = next(row for row in rows if row["po_id"] == "po-spindle-01")
    # enriched from the quote via the declared link's typed FK
    assert spindle["price"] == 2150000.0
    assert spindle["on_contract"] is False
    # base keeps its names; the quote side's collisions renamed
    assert spindle["part_no"] == "part-spindle-01"
    assert spindle["quote_part_no"] == "part-spindle-01"
    assert spindle["supplier_id"] == "sup-rfq-01"


async def test_shape2_on_override_and_fuse_end_to_end() -> None:
    """The intake decomposition's other two forms: an explicit ``on`` override
    (part_no) + the positional singleton ``fuse`` of the failure event."""
    data = dict(_PROCUREMENT_DATA)
    data["OperationalEvent"] = [
        {
            "event_id": "EVT-CNC-014-FAIL",
            "event_type": "failure",
            "measured_value": 0.92,
            "occurred_at": "2026-06-30T09:15:00Z",
            "equipment_id": "AST-CNC-014",
        },
        {
            "event_id": "EVT-CNC-014-BASE",
            "event_type": "reading",
            "measured_value": 0.30,
            "occurred_at": "2026-06-30T06:00:00Z",
            "equipment_id": "AST-CNC-014",
        },
    ]
    import warnings

    from services.engine.procedures.orchestrator import ProcedureWarning

    with warnings.catch_warnings():
        # the OperationalEvent<->PurchaseOrder fuse is the ontology-undeclarable
        # shape — the OQ-4 warn-first advisory fires by design; not a failure.
        warnings.simplefilter("ignore", ProcedureWarning)
        result = await run_procedure(
            _procedure(
                {
                    "reads": ["OperationalEvent", "PurchaseOrder", "Quotation"],
                    "where": {"event_type": "failure"},  # narrows the event to the singleton
                    "join": [
                        {
                            "with": "PurchaseOrder",
                            "fuse": True,
                            "where": {"po_id": "po-spindle-01"},
                        },
                        {
                            "with": "Quotation",
                            "on": {"left": "quote_id", "right": "quote_id"},
                        },
                    ],
                    "project": {"fields": _QUOTE_RENAMES},
                }
            ),
            _agent(),
            _executors("procurement", data),
            vertical="procurement",
            run_id="fixture-shape2-fuse",
        )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    artifact = result.step_results[-1].artifact
    assert artifact is not None
    rows = artifact["output_set"]
    assert len(rows) == 1
    requisition = rows[0]
    # one flat enriched requisition: event + PO + quote fused/joined
    assert requisition["event_id"] == "EVT-CNC-014-FAIL"
    assert requisition["po_id"] == "po-spindle-01"
    assert requisition["price"] == 2150000.0
