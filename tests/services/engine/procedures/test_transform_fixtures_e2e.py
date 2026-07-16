"""PLAN-0077 Phase C (AC-6): the transform grammar end-to-end + the marquee value-parity
oracle.

Test-module-embedded procedures + fake adapters (the PLAN-0061 SD-3 pattern — zero
shipped vertical file changes; these procedures double as the authoring examples for the
SD-4 migration PLAN). Two shapes run through the production ``run_procedure`` path over the
REAL shipped ontologies, each threading its enriched rows into a downstream consumer step:

- **fixture A** (procurement-shaped): ``criticality``-copy + ``unit`` default + ``compliance``
  map;
- **fixture B** (supply_chain-shaped): magnitude arithmetic + defaults + ``compliance`` map +
  a Decimal→str coercion.

**Marquee expressibility parity** (the shadow-parity precedent, SD-1 capability-completeness):
a declared transform reproduces — value-identically, without touching the shipped stamp path —
``derive_excursion_severity``'s exact severity + ratio (the ``_DOSE_LADDER``, imported so the
declared bands ARE the shipped constants) and ``scored_rule``'s ``amount = unit_price x qty``
(via the shipped ``select_scored_supplier``). Deterministic, offline, no LLM (L-4).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.orchestrator import RunContext, run_procedure
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.scored_rule import select_scored_supplier
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    ExceptionPolicy,
    Procedure,
    ScoredCriterion,
    ScoredRule,
    SourcePolicy,
    Step,
    StepKind,
)
from services.engine.procedures.transform_step import TransformStepExecutor
from verticals.supply_chain.cold_chain_assess import (
    _DOSE_LADDER,
    _TOP_SEVERITY,
    derive_excursion_severity,
)

# The declared ladder IS the shipped one: build the map_value bands from the vertical's own
# constants, so the parity oracle proves the grammar expresses THE ladder (and tracks it if it
# ever changes) — not a hand-copied coincidence.
_LADDER_BANDS = [{"ceiling": str(ceiling), "value": sev.value} for ceiling, sev in _DOSE_LADDER]
_LADDER_ABOVE = _TOP_SEVERITY.value


class _FakeAdapter:
    """Duck-typed adapter: the executor only calls ``fetch_objects`` (PLAN-0061 SD-3)."""

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


def _ctx() -> RunContext:
    return RunContext(agent=_agent(), vertical="fixture")


def _executors(vertical: str, data: dict[str, list[dict[str, Any]]]) -> dict[StepKind, Any]:
    meta = load_ontology_meta(vertical)  # the REAL shipped ontology, read-only
    return {
        StepKind.QUERY: QueryStepExecutor(
            adapter=_FakeAdapter(vertical, data),  # type: ignore[arg-type]  # duck-typed
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        ),
        StepKind.TRANSFORM: TransformStepExecutor(),
    }


def _transform_step(ops: list[dict[str, Any]]) -> Step:
    return Step.model_validate(
        {"step_id": "enrich", "name": "Enrich", "kind": "transform", "transform": {"ops": ops}}
    )


# A read → transform → downstream-consumer procedure: the query sources the rows, the transform
# enriches them, and the trailing query passthrough (SD-1 identity, no reads) proves the derived
# fields THREAD into a downstream step.
def _procedure(vertical_id: str, read_type: str, ops: list[dict[str, Any]]) -> Procedure:
    return Procedure.model_validate(
        {
            "procedure_id": vertical_id,
            "title": "Transform fixture",
            "goal": "Enrich a threaded row-set via a declared transform (PLAN-0077).",
            "run_by": "fixture_agent",
            "steps": [
                {
                    "step_id": "read",
                    "name": "Read",
                    "kind": "query",
                    "input": {"reads": [read_type]},
                },
                {
                    "step_id": "enrich",
                    "name": "Enrich",
                    "kind": "transform",
                    "input": {"from": "read"},
                    "transform": {"ops": ops},
                },
                {
                    "step_id": "consume",
                    "name": "Downstream consumer",
                    "kind": "query",
                    "input": {"from": "enrich"},
                },
            ],
        }
    )


# ============================ Fixture A — procurement-shaped ============================


_FIXTURE_A_OPS = [
    {"derive": {"target": "criticality", "expr": {"field": "measured_value"}}},  # typed copy
    {"default": {"target": "unit", "value": "each"}},
    {
        "default": {
            "target": "compliance",
            "value": {
                "avl": True,
                "tax": True,
                "cert": True,
                "sanctions": True,
                "single_source": True,
            },
        }
    },
]


async def test_fixture_a_procurement_enrichment_threads_downstream() -> None:
    data = {
        "OperationalEvent": [
            {"event_id": "evt-1", "measured_value": "critical", "part_no": "part-x"},
            {"event_id": "evt-2", "measured_value": "warn", "part_no": "part-y", "unit": "kg"},
        ]
    }
    result = await run_procedure(
        _procedure("transform-fixture-a", "OperationalEvent", _FIXTURE_A_OPS),
        _agent(),
        _executors("procurement", data),
        vertical="procurement",
        run_id="transform-fixture-a",
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    # the downstream consumer received the ENRICHED rows (threading proven)
    rows = result.step_results[-1].artifact["output_set"]  # type: ignore[index]
    by_id = {row["event_id"]: row for row in rows}
    assert by_id["evt-1"]["criticality"] == "critical"  # copied from measured_value
    assert by_id["evt-1"]["measured_value"] == "critical"  # source retained (copy, not move)
    assert by_id["evt-1"]["unit"] == "each"  # defaulted (absent)
    assert by_id["evt-2"]["unit"] == "kg"  # NOT overwritten (present)
    assert by_id["evt-1"]["compliance"]["single_source"] is True


# ============================ Fixture B — supply_chain-shaped ============================


FIXTURE_B_OPS = [
    {
        "derive": {
            "target": "excursion_magnitude_c",
            "expr": {"op": "sub", "args": [{"field": "reading_c"}, {"field": "temp_ceiling"}]},
        }
    },
    {"default": {"target": "excursion_duration_h", "value": 9}},
    {"default": {"target": "stability_budget_ch", "value": 24}},
    {
        "default": {
            "target": "compliance",
            "value": {
                "stability_budget": True,
                "batch_quarantine": True,
                "licensed_disposal_vendor": True,
                "coa_customs": True,
            },
        }
    },
    {"coerce": {"target": "excursion_magnitude_c", "to": "string"}},  # Decimal→str JSONB safety
]


def fixture_b_procedure() -> Procedure:
    return _procedure("transform-fixture-b", "OperationalEvent", FIXTURE_B_OPS)


FIXTURE_B_DATA = {
    "OperationalEvent": [{"event_id": "evt-1", "reading_c": "12", "temp_ceiling": "8"}]
}


async def test_fixture_b_supply_chain_enrichment_threads_downstream() -> None:
    result = await run_procedure(
        fixture_b_procedure(),
        _agent(),
        _executors("supply_chain", FIXTURE_B_DATA),
        vertical="supply_chain",
        run_id="transform-fixture-b",
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    row = result.step_results[-1].artifact["output_set"][0]  # type: ignore[index]
    assert row["excursion_magnitude_c"] == "4"  # 12 - 8, coerced to string
    assert row["excursion_duration_h"] == 9  # defaulted
    assert row["stability_budget_ch"] == 24  # defaulted
    assert row["compliance"]["batch_quarantine"] is True


# ==================== Marquee value-parity oracle (AC-6, SD-1) ====================


class TestMarqueeSeverityParity:
    """A declared transform reproduces ``derive_excursion_severity`` value-identically — the
    grammar can express the F-PIN severity derivation WITHOUT touching the hardened stamp path
    (SD-1). Bands are the shipped ``_DOSE_LADDER`` constants."""

    def _severity_ops(self) -> list[dict[str, Any]]:
        return [
            {
                "derive": {
                    "target": "dose",
                    "expr": {
                        "op": "mul",
                        "args": [
                            {"field": "excursion_magnitude_c"},
                            {"field": "excursion_duration_h"},
                        ],
                    },
                }
            },
            {
                "derive": {
                    "target": "dose_ratio",
                    "expr": {
                        "op": "div",
                        "args": [{"field": "dose"}, {"field": "stability_budget_ch"}],
                    },
                }
            },
            {
                "map_value": {
                    "target": "excursion_severity",
                    "source": {"field": "dose_ratio"},
                    "bands": _LADDER_BANDS,
                    "above": _LADDER_ABOVE,
                }
            },
        ]

    @pytest.mark.parametrize(
        "magnitude,duration,budget",
        [
            ("10", "1", "100"),  # ratio 0.10 → negligible
            ("25", "1", "100"),  # ratio 0.25 → negligible (inclusive edge)
            ("30", "1", "100"),  # ratio 0.30 → minor
            ("50", "1", "100"),  # ratio 0.50 → minor (inclusive edge)
            ("75", "1", "100"),  # ratio 0.75 → major
            ("100", "1", "100"),  # ratio 1.00 → major (inclusive edge)
            ("150", "1", "100"),  # ratio 1.50 → critical (unbounded top)
            ("4", "9", "24"),  # the SD-2 sketch inputs — ratio 1.5 → critical
        ],
    )
    async def test_declared_transform_matches_the_shipped_derivation(
        self, magnitude: str, duration: str, budget: str
    ) -> None:
        entity = {
            "excursion_magnitude_c": magnitude,
            "excursion_duration_h": duration,
            "stability_budget_ch": budget,
        }
        expected = derive_excursion_severity(entity)
        outcome = await TransformStepExecutor().execute(
            _transform_step(self._severity_ops()), [dict(entity)], _ctx()
        )
        row = outcome.output[0]
        assert row["excursion_severity"] == expected.severity.value  # exact severity
        assert Decimal(row["dose_ratio"]) == expected.ratio  # exact ratio


class TestMarqueeAmountParity:
    """A declared ``amount = unit_price x qty`` transform reproduces the spend the shipped
    ``select_scored_supplier`` verdict resolves, value-identically.

    This fixture was authored to prove the shape was FEASIBLE before the migration — "without
    touching the scored_rule stamp path (SD-1)". PLAN-0078 PR-4 has since taken that path: the
    verdict now carries the two FACTORS (``selected_unit_price`` x ``qty``) and the declared
    transform owns the multiplication, so the comparison is against the factors rather than a
    product the verdict no longer computes. Kept as the fixture-level check that the grammar's
    ``mul`` is exact on Decimals; the SHIPPED chain's byte parity is proven over the real
    procedures in ``test_amount_transform_parity.py``."""

    async def test_declared_transform_matches_scored_rule_amount(self) -> None:
        quote = {
            "quote_id": "q1",
            "supplier_id": "s1",
            "unit_price": "1234.56",
            "lead_time_days": "3",
            "on_contract": True,
            "currency": "THB",
        }
        rule = ScoredRule(
            criteria=[ScoredCriterion(name="unit_price", weight=Decimal(1))],
            default_source=SourcePolicy.ON_CONTRACT,
            exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
        )
        verdict = select_scored_supplier(
            rule, [quote], qty=Decimal("5"), event_criticality=Decimal("0.5")
        )
        ops = [
            {
                "derive": {
                    "target": "amount",
                    "expr": {"op": "mul", "args": [{"field": "unit_price"}, {"field": "qty"}]},
                }
            }
        ]
        outcome = await TransformStepExecutor().execute(
            _transform_step(ops), [{"unit_price": "1234.56", "qty": "5"}], _ctx()
        )
        spend = verdict.selected_unit_price * verdict.qty  # the derivation the transform now owns
        assert Decimal(outcome.output[0]["amount"]) == spend
        assert spend == Decimal("1234.56") * Decimal("5")
