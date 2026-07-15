"""PLAN-0077 Phase B — compile + execute the transform grammar (AC-4, AC-5).

Drives :func:`plan_transform` (pure/total → a frozen ``TransformPlan`` or a typed
``TransformRefusal``, re-running the load gate's ``validate_transform_spec`` — one
decision surface, AC-3 compile half) and :class:`TransformStepExecutor` (the per-op
determinism matrix: exact-``Decimal`` arithmetic, fail-closed
division/non-finite/missing-input per SD-7, inclusive-ceiling + unbounded-top
banding, ``default`` fills only absent, ``coerce`` round-trips, JSONB-safe output,
per-op provenance). Also OQ-4: the ``from``-thread linearity check applies
kind-agnostically to a transform step. Deterministic, offline, no LLM (L-4).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    _validate_transform_load,
    validate_read_bindings,
    validate_runnable,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    DefaultBody,
    DefaultOp,
    Procedure,
    Step,
    TransformSpec,
    validate_transform_spec,
)
from services.engine.procedures.transform_step import (
    TransformPlan,
    TransformRefusal,
    TransformRefusalKind,
    TransformStepExecutor,
    plan_transform,
)

_AGENT_ID = "a"


def _agent() -> Agent:
    return Agent(
        agent_id=_AGENT_ID, name="A", autonomy_ceiling=Autonomy.GATED, allowed=AgentAllowed()
    )


def _ctx() -> RunContext:
    return RunContext(agent=_agent(), vertical="fixture")


def _transform_step(ops: list[dict[str, Any]], *, step_id: str = "enrich") -> Step:
    return Step.model_validate(
        {"step_id": step_id, "name": "Enrich", "kind": "transform", "transform": {"ops": ops}}
    )


async def _run(ops: list[dict[str, Any]], rows: list[Any]) -> Any:
    """Execute a transform over ``rows`` and return the StepOutcome."""
    return await TransformStepExecutor().execute(_transform_step(ops), rows, _ctx())


def _dup_target_spec() -> TransformSpec:
    """A dead-write spec (two producing ops write ``x``) built via ``model_construct`` so it
    bypasses the model validator — the ONLY way to feed an invalid spec to a surface
    (a normally-constructed ``TransformSpec`` rejects it at construction)."""
    return TransformSpec.model_construct(
        ops=[
            DefaultOp(default=DefaultBody(target="x", value=1)),
            DefaultOp(default=DefaultBody(target="x", value=2)),
        ]
    )


# ============================ AC-4: compile is pure + total ============================


class TestAC4Compile:
    def test_valid_transform_compiles_to_a_frozen_plan(self) -> None:
        step = _transform_step(
            [
                {
                    "derive": {
                        "target": "amt",
                        "expr": {"op": "mul", "args": [{"field": "p"}, {"field": "q"}]},
                    }
                }
            ]
        )
        plan = plan_transform(step)
        assert isinstance(plan, TransformPlan)
        assert plan.step_id == "enrich"
        assert isinstance(plan.ops, tuple) and len(plan.ops) == 1
        with pytest.raises((AttributeError, TypeError)):  # frozen dataclass
            plan.step_id = "other"  # type: ignore[misc]

    def test_non_transform_step_refuses(self) -> None:
        step = Step.model_validate({"step_id": "q", "name": "Q", "kind": "query"})
        with pytest.raises(TransformRefusal) as exc:
            plan_transform(step)
        assert exc.value.refusal_kind is TransformRefusalKind.NOT_A_TRANSFORM_STEP
        assert exc.value.step_id == "q"

    def test_transform_step_without_declaration_refuses_not_no_op(self) -> None:
        # refusal ≠ no-op: an unfilled transform stub refuses loudly, never passes rows through
        step = Step.model_validate({"step_id": "e", "name": "E", "kind": "transform"})
        with pytest.raises(TransformRefusal) as exc:
            plan_transform(step)
        assert exc.value.refusal_kind is TransformRefusalKind.MISSING_DECLARATION

    def test_structurally_invalid_spec_refuses_via_the_shared_predicate(self) -> None:
        step = _transform_step([{"default": {"target": "x", "value": 1}}])
        step.transform = _dup_target_spec()  # inject the bypassed dead-write spec
        with pytest.raises(TransformRefusal) as exc:
            plan_transform(step)
        assert exc.value.refusal_kind is TransformRefusalKind.INVALID_SPEC
        assert "dead write" in exc.value.detail


# ============================ AC-5: each op executes deterministically ============================


class TestAC5Execute:
    async def test_derive_arithmetic_is_exact_decimal(self) -> None:
        # amount = unit_price * qty, exact (never binary float: 0.1 * 3 == 0.3, not 0.30000000004)
        outcome = await _run(
            [
                {
                    "derive": {
                        "target": "amount",
                        "expr": {"op": "mul", "args": [{"field": "up"}, {"field": "qty"}]},
                    }
                }
            ],
            [{"up": "0.1", "qty": "3"}],
        )
        assert Decimal(outcome.output[0]["amount"]) == Decimal("0.3")

    @pytest.mark.parametrize(
        "op,args,expected",
        [
            ("add", ["2", "3", "5"], "10"),
            ("sub", ["10", "4"], "6"),
            ("mul", ["3", "4"], "12"),
            ("div", ["10", "4"], "2.5"),
            ("min", ["5", "2", "9"], "2"),
            ("max", ["5", "2", "9"], "9"),
        ],
    )
    async def test_each_arithmetic_operator(self, op: str, args: list[str], expected: str) -> None:
        expr = {"op": op, "args": [{"const": a} for a in args]}
        outcome = await _run([{"derive": {"target": "r", "expr": expr}}], [{}])
        assert Decimal(outcome.output[0]["r"]) == Decimal(expected)

    async def test_derive_bare_field_leaf_is_a_copy(self) -> None:
        # criticality = copy of measured_value; the SOURCE field is retained (not moved)
        outcome = await _run(
            [{"derive": {"target": "criticality", "expr": {"field": "measured_value"}}}],
            [{"measured_value": "warn"}],
        )
        assert outcome.output[0]["criticality"] == "warn"
        assert outcome.output[0]["measured_value"] == "warn"

    async def test_compare_operator_yields_bool(self) -> None:
        outcome = await _run(
            [
                {
                    "derive": {
                        "target": "hot",
                        "expr": {"op": "ge", "args": [{"field": "t"}, {"const": "8"}]},
                    }
                }
            ],
            [{"t": "9"}],
        )
        assert outcome.output[0]["hot"] is True

    async def test_division_by_zero_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run(
                [
                    {
                        "derive": {
                            "target": "r",
                            "expr": {"op": "div", "args": [{"field": "a"}, {"const": "0"}]},
                        }
                    }
                ],
                [{"a": "5"}],
            )
        assert exc.value.refusal_kind is TransformRefusalKind.NON_FINITE_RESULT

    async def test_non_finite_input_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run(
                [
                    {
                        "derive": {
                            "target": "r",
                            "expr": {"op": "mul", "args": [{"field": "a"}, {"const": "2"}]},
                        }
                    }
                ],
                [{"a": "NaN"}],
            )
        assert exc.value.refusal_kind is TransformRefusalKind.NON_FINITE_RESULT

    async def test_missing_source_field_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run(
                [{"derive": {"target": "r", "expr": {"field": "absent"}}}],
                [{"present": "1"}],
            )
        assert exc.value.refusal_kind is TransformRefusalKind.MISSING_INPUT_FIELD

    async def test_non_numeric_operand_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run(
                [
                    {
                        "derive": {
                            "target": "r",
                            "expr": {"op": "add", "args": [{"field": "a"}, {"const": "1"}]},
                        }
                    }
                ],
                [{"a": "not-a-number"}],
            )
        assert exc.value.refusal_kind is TransformRefusalKind.NON_NUMERIC_OPERAND

    async def test_non_mapping_row_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run([{"default": {"target": "x", "value": 1}}], [42])
        assert exc.value.refusal_kind is TransformRefusalKind.NON_MAPPING_ROW

    @pytest.mark.parametrize(
        "ratio,expected",
        [
            ("0.10", "negligible"),
            ("0.25", "negligible"),  # inclusive ceiling edge
            ("0.2500001", "minor"),  # just over the first ceiling
            ("0.50", "minor"),  # inclusive edge
            ("1.00", "major"),  # inclusive edge
            ("1.0001", "critical"),  # above every ceiling → the unbounded top band
            ("9999", "critical"),
        ],
    )
    async def test_map_value_banding_inclusive_ceiling_and_top(
        self, ratio: str, expected: str
    ) -> None:
        outcome = await _run(
            [
                {
                    "map_value": {
                        "target": "sev",
                        "source": {"field": "ratio"},
                        "bands": [
                            {"ceiling": "0.25", "value": "negligible"},
                            {"ceiling": "0.50", "value": "minor"},
                            {"ceiling": "1.00", "value": "major"},
                        ],
                        "above": "critical",
                    }
                }
            ],
            [{"ratio": ratio}],
        )
        assert outcome.output[0]["sev"] == expected

    async def test_default_fills_only_absent_fields(self) -> None:
        outcome = await _run(
            [{"default": {"target": "unit", "value": "each"}}],
            [{"unit": "kg"}, {}],  # first present (keep), second absent (fill)
        )
        assert outcome.output[0]["unit"] == "kg"
        assert outcome.output[1]["unit"] == "each"
        # provenance records ONLY the real fill (1 of 2 rows written)
        assert outcome.reasoning_trace[0]["rows_written"] == 1

    async def test_coerce_string_and_decimal_round_trip(self) -> None:
        outcome = await _run(
            [
                {
                    "derive": {
                        "target": "amount",
                        "expr": {"op": "mul", "args": [{"field": "p"}, {"field": "q"}]},
                    }
                },
                {"coerce": {"target": "amount", "to": "string"}},  # Decimal→str JSONB safety
                {"coerce": {"target": "raw", "to": "decimal"}},  # normalize a string quantity
            ],
            [{"p": "12", "q": "5", "raw": "7.50"}],
        )
        assert outcome.output[0]["amount"] == "60"
        assert Decimal(outcome.output[0]["raw"]) == Decimal("7.50")

    async def test_coerce_missing_target_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run([{"coerce": {"target": "absent", "to": "string"}}], [{}])
        assert exc.value.refusal_kind is TransformRefusalKind.MISSING_INPUT_FIELD

    async def test_rename_copies_and_retains_source(self) -> None:
        outcome = await _run(
            [{"rename": {"from": "reference", "target": "batch_id"}}],
            [{"reference": "R-99"}],
        )
        assert outcome.output[0]["batch_id"] == "R-99"
        assert outcome.output[0]["reference"] == "R-99"  # COPY semantics (non-destructive)

    async def test_rename_missing_source_fails_closed(self) -> None:
        with pytest.raises(TransformRefusal) as exc:
            await _run([{"rename": {"from": "absent", "target": "t"}}], [{}])
        assert exc.value.refusal_kind is TransformRefusalKind.MISSING_INPUT_FIELD

    async def test_output_is_jsonb_safe(self) -> None:
        # a derived Decimal must not survive as a Python Decimal (JSONB refuses it) —
        # it coerces to its exact string at the _json_safe boundary
        outcome = await _run(
            [
                {
                    "derive": {
                        "target": "amount",
                        "expr": {"op": "mul", "args": [{"field": "p"}, {"field": "q"}]},
                    }
                }
            ],
            [{"p": "3", "q": "4"}],
        )
        assert outcome.output[0]["amount"] == "12"
        assert not isinstance(outcome.output[0]["amount"], Decimal)

    async def test_pipeline_order_and_per_op_provenance(self) -> None:
        # ops apply in order; each emits one provenance entry with its op name + target
        outcome = await _run(
            [
                {
                    "derive": {
                        "target": "dose",
                        "expr": {"op": "mul", "args": [{"field": "mag"}, {"field": "dur"}]},
                    }
                },
                {
                    "derive": {
                        "target": "ratio",
                        "expr": {"op": "div", "args": [{"field": "dose"}, {"field": "budget"}]},
                    }
                },
                {
                    "map_value": {
                        "target": "sev",
                        "source": {"field": "ratio"},
                        "bands": [
                            {"ceiling": "0.50", "value": "minor"},
                            {"ceiling": "1.00", "value": "major"},
                        ],
                        "above": "critical",
                    }
                },
            ],
            [{"mag": "2", "dur": "9", "budget": "24"}],
        )
        row = outcome.output[0]
        assert Decimal(row["dose"]) == Decimal("18")  # 2 * 9
        assert Decimal(row["ratio"]) == Decimal("18") / Decimal("24")  # 0.75
        assert row["sev"] == "major"  # 0.75 > 0.50 ceiling, <= 1.00 ceiling → the major band
        names = [(e["op"], e["target"]) for e in outcome.reasoning_trace]
        assert names == [("derive", "dose"), ("derive", "ratio"), ("map_value", "sev")]
        assert all(e["kind"] == "transform_provenance" for e in outcome.reasoning_trace)
        assert all(e["rows_written"] == 1 for e in outcome.reasoning_trace)

    async def test_empty_input_set_yields_empty_output(self) -> None:
        outcome = await _run([{"default": {"target": "x", "value": 1}}], [])
        assert outcome.output == []
        assert outcome.reasoning_trace[0]["rows_written"] == 0

    async def test_input_row_is_not_mutated(self) -> None:
        source_row = {"p": "3", "q": "4"}
        await _run(
            [
                {
                    "derive": {
                        "target": "amount",
                        "expr": {"op": "mul", "args": [{"field": "p"}, {"field": "q"}]},
                    }
                }
            ],
            [source_row],
        )
        assert "amount" not in source_row  # the executor works on a copy


# ==================== AC-3: one decision surface (the compile half) ====================


class TestAC3OneSurfaceCompileHalf:
    """The load gate (:func:`validate_read_bindings` → ``_validate_transform_load``) and the
    run-compile (:func:`plan_transform`) share ONE structural predicate
    (:func:`validate_transform_spec`) — so they cannot drift (L-6). A shared matrix drives
    the SAME specs through both and asserts identical accept/refuse."""

    def _procedure_with(self, spec: TransformSpec) -> Procedure:
        step = _transform_step([{"default": {"target": "x", "value": 1}}])
        step.transform = spec
        return Procedure.model_validate(
            {
                "procedure_id": "p",
                "title": "P",
                "run_by": _AGENT_ID,
                "trigger": "manual",
                "steps": [step],
            }
        )

    def _load_gate_accepts(self, spec: TransformSpec) -> bool:
        try:
            validate_read_bindings(self._procedure_with(spec), _agent(), frozenset({"Asset"}))
            return True
        except ProcedureError:
            return False

    def _compile_accepts(self, spec: TransformSpec) -> bool:
        step = _transform_step([{"default": {"target": "x", "value": 1}}])
        step.transform = spec
        try:
            plan_transform(step)
            return True
        except TransformRefusal:
            return False

    def test_valid_spec_accepted_by_both_surfaces(self) -> None:
        spec = TransformSpec.model_validate(
            {
                "ops": [
                    {
                        "derive": {
                            "target": "amt",
                            "expr": {"op": "mul", "args": [{"field": "p"}, {"field": "q"}]},
                        }
                    }
                ]
            }
        )
        assert self._load_gate_accepts(spec) is True
        assert self._compile_accepts(spec) is True

    def test_invalid_spec_rejected_by_both_surfaces(self) -> None:
        spec = _dup_target_spec()  # model_construct dead-write bypass
        assert self._load_gate_accepts(spec) is False
        assert self._compile_accepts(spec) is False

    def test_the_two_surfaces_agree_across_the_matrix(self) -> None:
        valid = TransformSpec.model_validate(
            {"ops": [{"default": {"target": "u", "value": "each"}}]}
        )
        matrix = [(valid, True), (_dup_target_spec(), False)]
        for spec, expected in matrix:
            assert self._load_gate_accepts(spec) is expected
            assert self._compile_accepts(spec) is expected
            # both surfaces route through the same predicate — belt and braces
            raised = False
            try:
                validate_transform_spec(spec)
            except ValueError:
                raised = True
            assert raised is (not expected)

    def test_load_gate_and_compile_share_validate_transform_load(self) -> None:
        # _validate_transform_load (the gate's internal) is the same predicate wrapper
        step = _transform_step([{"default": {"target": "x", "value": 1}}])
        step.transform = _dup_target_spec()
        with pytest.raises(ProcedureError, match="invalid transform declaration"):
            _validate_transform_load(step)
        with pytest.raises(TransformRefusal):
            plan_transform(step)


# ============================ OQ-4: from-thread linearity ============================


class TestOQ4FromLinearity:
    """OQ-4: the pre-flight ``from`` linearity check (:func:`validate_runnable`) applies
    kind-agnostically — a transform step with a forward / unknown ``from`` fails at LOAD,
    not at run."""

    def test_transform_with_forward_from_refuses_at_load(self) -> None:
        step = Step.model_validate(
            {
                "step_id": "enrich",
                "name": "E",
                "kind": "transform",
                "input": {"from": "ghost"},  # names no earlier step
                "transform": {"ops": [{"default": {"target": "x", "value": 1}}]},
            }
        )
        proc = Procedure.model_validate(
            {
                "procedure_id": "p",
                "title": "P",
                "run_by": _AGENT_ID,
                "trigger": "manual",
                "steps": [step],
            }
        )
        with pytest.raises(ProcedureError, match="linear"):
            validate_runnable(proc, _agent())

    def test_transform_with_backward_from_is_runnable(self) -> None:
        read = {"step_id": "read", "name": "R", "kind": "query"}
        enrich = {
            "step_id": "enrich",
            "name": "E",
            "kind": "transform",
            "input": {"from": "read"},  # a real earlier step
            "transform": {"ops": [{"default": {"target": "x", "value": 1}}]},
        }
        proc = Procedure.model_validate(
            {
                "procedure_id": "p",
                "title": "P",
                "run_by": _AGENT_ID,
                "trigger": "manual",
                "steps": [read, enrich],
            }
        )
        validate_runnable(proc, _agent())  # no raise
