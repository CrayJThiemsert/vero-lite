"""PLAN-0062 Step 4 (PR4) — procurement ``intake``: the join half proven under SHADOW parity (AC-6).

The other three OCT verticals MIGRATED their seed's read to the declared query grammar.
procurement's ``intake`` KEEPS its relational read as a shadow (this module proves the join
half is grammar-expressible without flipping it), while PLAN-0078 PR-1 separately migrated the
seed's flat DERIVED fields (``criticality`` / ``unit`` / ``compliance``) into a declared
``enrich`` TRANSFORM step — a different grammar from this query-join half.

**Shadow, not migration (SD-C / OQ-3).** Production ``intake`` keeps ``_SeedQuery`` — the
co-existing hand-written seed. Nothing in the hero YAML, the hero audit contract, the
production factory, or the scheduled-demo path changes. What these tests prove is a
narrower, checkable claim: **the JOIN HALF of that seed is expressible in the ratified
grammar, and over the REAL ``FastenalCsvAdapter`` it carries the same information.**

**What the query-join grammar cannot do — asserted, not hand-waved.** A relational join emits
**three flat rows** and **no derived fields** — it cannot produce the seed's nested
``candidate_quotes`` reshape, nor the flat derived fields. PLAN-0078 PR-1 closed the FLAT half
of that gap with the ``enrich`` TRANSFORM grammar (``criticality`` / ``unit`` / ``compliance``
are now execution-bound ✔), so what a JOIN alone still cannot invent is the nested
``candidate_quotes`` (the cardinality-changing reshape — PLAN-0077 SD-8 wall) plus the
harness-owned envelope metadata (``object_type`` / ``primary_key``, the
``required_tier_id``→``declared_tier_id`` relabel). Those facts are pinned below: the
``candidate_quotes`` nest keeps ``intake`` **execution-bound ✖** for that residue (LOCKED-9,
L-3 partial).

**A drift this test also pins.** The procurement ontology declares
``PurchaseOrder.part_no`` / ``Quotation.price`` / ``OperationalEvent.equipment_id``,
while the real CSVs emit ``part_id`` / ``price_thb`` / ``asset_id``. The load gate checks
**declared** properties; the executor merges **runtime** keys. So the declaration must
rename the four ontology-declared ``PurchaseOrder``∩``Quotation`` collisions
(``currency`` · ``part_no`` · ``quote_id`` · ``supplier_id``) even though only
``supplier_id`` collides at runtime — and renaming it is what keeps each quote's own
supplier instead of letting the PO's supplier win all three rows.

Deterministic, offline, no LLM, no DB (SD-6 / LOCKED-6): the real CSV adapter, the real
ontology, no MS-S1.
"""

from __future__ import annotations

import warnings
from decimal import Decimal
from typing import Any

import pytest

from services.engine.discovery import discover_and_register
from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.orchestrator import (
    ProcedureWarning,
    RunContext,
    run_procedure,
    validate_read_bindings_for_vertical,
)
from services.engine.procedures.query_router import QueryStepRouter
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
    load_procedures,
)
from services.engine.registry import registry
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.hero_demo.run import (
    _HERO_PO,
    _intake_seed,
    _SeedQuery,
    register_procurement_procedure_executors,
)

_VERTICAL = "procurement"

# The declared JOIN HALF of `_intake_seed`, in the ratified PLAN-0061 grammar.
#   * base    = the singleton failure event (`where` narrows it to one row)
#   * fuse    = the hero PO — the ontology-undeclarable positional fusion (OQ-4 warns)
#   * on      = quotes keyed on part_id (the PO CSV carries NO quote_id — PLAN fact 5)
#   * fields  = the four ontology-declared PO∩Quotation collisions, renamed away as the
#               load gate requires; `part_no` never appears at runtime (ontology drift),
#               so its rename is a declared no-op.
_INTAKE_JOIN_INPUT: dict[str, Any] = {
    "reads": ["OperationalEvent", "PurchaseOrder", "Quotation"],
    "where": {"event_type": "failure"},
    "join": [
        {"with": "PurchaseOrder", "fuse": True, "where": {"po_id": _HERO_PO}},
        {"with": "Quotation", "on": {"left": "part_id", "right": "part_id"}},
    ],
    "project": {
        "fields": {
            "supplier_id": "quote_supplier_id",
            "quote_id": "quotation_id",
            "currency": "quote_currency",
            "part_no": "quote_part_no",
        }
    },
}

# grammar row key -> `_intake_seed` key, for the fields the JOIN HALF is responsible for.
# PLAN-0078 PR-1 removed `unit` here: it is no longer a seed-emitted field (the `enrich`
# transform now DEFAULTS it), so there is no seed counterpart to compare the join row against.
_BASE_FIELD_MAP = {
    "event_id": "event_id",
    "po_id": "primary_key",
    "asset_id": "asset_id",
    "part_id": "part_id",
    "qty": "qty",
    "measured_value": "measured_value",
    "order_type": "order_type",
    "is_off_avl_override": "is_off_avl_override",
    "required_tier_id": "declared_tier_id",
}

# grammar row key -> the seed's `candidate_quotes` entry key (per-quote half).
_QUOTE_FIELD_MAP = {
    "quotation_id": "quote_id",
    "quote_supplier_id": "supplier_id",
    "quote_currency": "currency",
    "lead_time_days": "lead_time_days",
    "on_contract": "on_contract",
}

# The seed's DERIVED fields — the OQ-3 boundary. A relational join cannot produce them.
_DERIVED_FIELDS = (
    "compliance",  # the rule_gate per-criterion signal (data-access = (a))
    "candidate_quotes",  # the flat-rows -> nested reshape
    "criticality",  # the scored_rule amplification (a duplicate of measured_value)
    "object_type",  # harness-owned envelope metadata
    "primary_key",  # harness-owned envelope metadata
    "declared_tier_id",  # a relabel of required_tier_id
)


def _agent() -> Agent:
    return Agent(
        agent_id="shadow_parity_agent",
        name="Shadow Parity Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),  # unconstrained reads (OQ-6)
    )


def _procedure() -> Procedure:
    return Procedure(
        procedure_id="intake-shadow-parity",
        title="Intake shadow parity",
        goal="Prove the intake join half is grammar-expressible over the real CSVs.",
        run_by="shadow_parity_agent",
        steps=[
            Step(
                step_id="intake_join",
                name="Declared intake join half",
                kind=StepKind.QUERY,
                input=StepInput.model_validate(_INTAKE_JOIN_INPUT),
            )
        ],
    )


async def _grammar_rows() -> list[dict[str, Any]]:
    """Run the declared join half through the production ``run_procedure`` path over the
    REAL ``FastenalCsvAdapter`` + the REAL procurement ontology."""
    meta = load_ontology_meta(_VERTICAL)
    executors = {
        StepKind.QUERY: QueryStepExecutor(
            adapter=FastenalCsvAdapter(),
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        )
    }
    with warnings.catch_warnings():
        # The OperationalEvent<->PurchaseOrder fuse is the ontology-undeclarable shape;
        # the OQ-4 warn-first advisory fires BY DESIGN (test_join_fixtures_e2e precedent).
        warnings.simplefilter("ignore", ProcedureWarning)
        result = await run_procedure(
            _procedure(), _agent(), executors, vertical=_VERTICAL, run_id="intake-shadow-parity"
        )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    artifact = result.step_results[-1].artifact
    assert artifact is not None
    rows: list[dict[str, Any]] = artifact["output_set"]
    return rows


def test_the_declared_intake_join_passes_the_load_gate() -> None:
    """The declaration resolves against the REAL ontology — the fuse warns (OQ-4
    warn-first, never rejects), the four declared PO∩Quotation collisions are renamed
    away, and nothing raises."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validate_read_bindings_for_vertical(_procedure(), _agent(), _VERTICAL)

    fuse_warnings = [w for w in caught if issubclass(w.category, ProcedureWarning)]
    assert len(fuse_warnings) == 1
    assert "PurchaseOrder" in str(fuse_warnings[0].message)
    assert "fuse" in str(fuse_warnings[0].message)


async def test_join_half_is_information_parity_with_the_seed() -> None:
    """AC-6, the positive half: every join-half field the seed derives from the CSVs is
    reproduced by the grammar, over the REAL adapter — base fields on every row, and the
    three quotes matched by id. ``price_thb`` (str, coerced from ``Decimal`` at the
    adapter boundary by ``_json_safe``) equals ``unit_price`` (``Decimal``) exactly —
    the normalization ``_normalize_quotes`` performs by hand."""
    rows = await _grammar_rows()
    seed = await _intake_seed(FastenalCsvAdapter())

    assert len(rows) == len(seed["candidate_quotes"]) == 3

    # base half: identical on every flat row (the fused event + PO)
    for row in rows:
        for grammar_key, seed_key in _BASE_FIELD_MAP.items():
            assert row[grammar_key] == seed[seed_key], grammar_key

    # per-quote half: match by quote id, then compare field by field
    by_id = {q["quote_id"]: q for q in seed["candidate_quotes"]}
    assert {row["quotation_id"] for row in rows} == set(by_id)
    for row in rows:
        quote = by_id[row["quotation_id"]]
        for grammar_key, seed_key in _QUOTE_FIELD_MAP.items():
            assert row[grammar_key] == quote[seed_key], grammar_key
        # price_thb -> unit_price: exact, no float round-trip
        assert Decimal(row["price_thb"]) == quote["unit_price"]

    # the join kept EACH quote's supplier — the PO's supplier did not win all three rows
    assert {row["quote_supplier_id"] for row in rows} == {
        q["supplier_id"] for q in seed["candidate_quotes"]
    }
    assert all(row["supplier_id"] == "SUP-RAPIDMRO" for row in rows), "base PO supplier intact"


async def test_derived_fields_are_absent_from_the_grammar_output() -> None:
    """AC-6, the honest half — the OQ-3 boundary made executable. The grammar emits THREE
    flat rows and none of the seed's derived fields; ``_SeedQuery`` co-exists because of
    exactly this, not because migration was never attempted. intake stays
    execution-bound ✖ for these fields (LOCKED-9)."""
    rows = await _grammar_rows()

    assert len(rows) == 3, "a relational join emits one row per quote, never the nested reshape"
    for row in rows:
        for derived in _DERIVED_FIELDS:
            assert derived not in row, f"{derived!r} is derived — the grammar must not invent it"
        # the seed's normalized quote key never appears; the raw CSV column does
        assert "unit_price" not in row
        assert "price_thb" in row


@pytest.mark.parametrize("required", ["candidate_quotes"])
async def test_the_seed_still_supplies_what_the_grammar_cannot(required: str) -> None:
    """The complement of the assertion above, NARROWED by PLAN-0078 PR-1. The two flat derived
    fields the seed used to owe here — ``criticality`` (a typed copy) and the ``compliance`` map
    (plus the ``unit`` default) — the transform grammar CAN express, and PR-1 migrated them into
    the declared ``enrich`` step (execution-bound ✔). What remains genuinely un-migratable
    without a cardinality-changing reshape is the nested ``candidate_quotes`` (the PLAN-0077 SD-8
    wall, L-3 partial): it exists in the seed and has no flat relational source."""
    seed = await _intake_seed(FastenalCsvAdapter())
    assert required in seed
    # the migrated flat fields are NO LONGER seed-emitted (they are the enrich transform's data)
    assert "criticality" not in seed
    assert "compliance" not in seed
    assert "unit" not in seed


# --------------------------------------------------------------------------- #
# AC-7 — the `read_stock` deferral, with the PLAN's stated reason CORRECTED
# --------------------------------------------------------------------------- #


async def test_read_stock_substrate_exists_the_plan_fact_7_erratum() -> None:
    """PLAN-0062 SD-1/fact 7 says ``read_stock`` is deferred because there is "no
    substrate". **That is false**, and Cray ratified SD-1 on it — so the reason is
    corrected here rather than quietly repeated.

    The ontology DECLARES ``Part.stock_qty`` + ``Part.reorder_point``, and the
    registry-registered ``ProcurementSyntheticAdapter`` EMITS both. (The hero
    ``FastenalCsvAdapter`` does not — but it is not the vertical's registered adapter.)
    A ``reads: [Part]`` declaration would resolve at the load gate today."""
    discover_and_register()
    meta = load_ontology_meta(_VERTICAL)
    part = next(t for t in meta.object_types if t.name == "Part")
    declared = {p.name for p in part.properties}
    assert {"stock_qty", "reorder_point"} <= declared, "the ontology declares the substrate"

    rows = await registry.get_adapter(_VERTICAL).fetch_objects("Part")
    assert rows, "the registered adapter emits Part rows"
    assert all(
        {"stock_qty", "reorder_point"} <= set(row) for row in rows
    ), "the registered adapter emits the stock substrate"


async def test_read_stock_routes_to_the_shipped_executor_not_the_seed() -> None:
    """PLAN-0064: the per-step QUERY router SHIPPED — the PLAN-0062 AC-7 deferral fell due
    and is discharged. Same lineage, rewritten in place (PLAN-0064 SD-4): this replaces the
    ERRATUM-2 tripwire ``test_read_stock_is_blocked_by_per_kind_executor_routing_not_by_data``,
    whose docstring promised exactly this rewrite when routing shipped. The history it
    pinned stands: the substrate was never the blocker (the companion test above);
    per-``StepKind`` routing was.

    The NEW contract, pinned three ways against the PRODUCTION factory:
      * the QUERY slot is the declaration-presence router (SD-1/SD-2) — declared leg the
        SHIPPED ``QueryStepExecutor``, fallback leg the co-existing ``_SeedQuery``;
      * the REAL declared ``read_stock`` step receives the REGISTRY-registered adapter's
        Part rows (SD-5) — never the intake requisition (the ERRATUM-2 hazard is now
        structurally impossible, and asserted so);
      * the REAL undeclared ``intake`` step still receives the seed byte-identically
        (PLAN-0062 SD-C carried — PLAN-0064 AC-4)."""
    discover_and_register()
    await register_procurement_procedure_executors()
    executors = registry.get_procedure_executors(_VERTICAL)()

    # PLAN-0078 Step 1: TRANSFORM joins the exact key set (shared fieldless executor, all 4
    # factories, pure-additive — the PR-1 intake flip adds the first declared transform).
    assert set(executors) == {
        StepKind.QUERY,
        StepKind.EVALUATE,
        StepKind.ACTION,
        StepKind.TRANSFORM,
    }
    query = executors[StepKind.QUERY]
    assert isinstance(query, QueryStepRouter), "the production QUERY slot is the router"
    assert isinstance(query.declared, QueryStepExecutor), "declared leg = the shipped executor"
    assert isinstance(query.fallback, _SeedQuery), "fallback leg = the co-existing seed"

    procedures = load_procedures(_VERTICAL).procedures
    read_stock = next(s for p in procedures for s in p.steps if s.step_id == "read_stock")
    assert read_stock.input is not None and read_stock.input.reads == ["Part"]
    intake = next(s for p in procedures for s in p.steps if s.step_id == "intake")
    assert intake.input is None or not intake.input.reads, "intake stays undeclared (SD-C)"

    ctx = RunContext(agent=_agent(), vertical=_VERTICAL)
    stock = await query.execute(read_stock, [], ctx)
    # PLAN-0065 (AC-5): read_stock now rename-projects stock_qty -> measured_value so the
    # shipped judge_stock can band the rows. Routing is unchanged (declared leg = the shipped
    # QueryStepExecutor over the registered adapter); the OUTPUT is that adapter's Part rows
    # with the one field renamed (stock_qty MOVED to measured_value, reorder_point kept).
    raw = await registry.get_adapter(_VERTICAL).fetch_objects("Part")
    expected = [
        {**{k: v for k, v in row.items() if k != "stock_qty"}, "measured_value": row["stock_qty"]}
        for row in raw
    ]
    assert (
        stock.output == expected
    ), "declared read_stock = the registered adapter's Part rows, projected"
    assert all(
        {"measured_value", "reorder_point"} <= set(row) and "stock_qty" not in row
        for row in stock.output
    )

    seeded = await query.execute(intake, [], ctx)
    assert len(seeded.output) == 1, "intake still gets the single enriched requisition seed"
    assert "candidate_quotes" in seeded.output[0], "the seed's derived shape, not Part rows"
    assert seeded.output == query.fallback.seed, "byte-identical to the fallback seed (AC-4)"
