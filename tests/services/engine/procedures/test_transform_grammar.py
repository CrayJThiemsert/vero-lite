"""PLAN-0077 Phase A — the transform grammar: schema + H-governance + load gate.

Covers AC-1 (the typed `extra="forbid"` spec surface + the anti-eval property), AC-2
(H-governed + pinned, no-transform byte-identical), and AC-3 (one decision surface: the
load gate and the run-compile share `validate_transform_spec`, so they cannot drift —
the compile half lands in Phase B). Everything here is offline and deterministic.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from services.engine.procedures.draft import (
    STEP_GOVERNANCE_FIELDS,
    StepDraft,
    derive_governance_todo,
    unfilled_governance,
)
from services.engine.procedures.governance_pin import governance_pin_for
from services.engine.procedures.orchestrator import ProcedureError, validate_read_bindings
from services.engine.procedures.spec import (
    Agent,
    DefaultBody,
    DefaultOp,
    Procedure,
    Step,
    StepKind,
    TransformSpec,
    validate_transform_spec,
)

_AGENT = Agent.model_validate({"agent_id": "a", "name": "A"})


def _transform_step(ops: list[dict[str, Any]]) -> dict[str, Any]:
    return {"step_id": "enrich", "name": "Enrich", "kind": "transform", "transform": {"ops": ops}}


def _procedure(steps: list[dict[str, Any]]) -> Procedure:
    return Procedure.model_validate(
        {
            "procedure_id": "p",
            "title": "P",
            "run_by": "a",
            "trigger": "manual",
            "steps": steps,
        }
    )


# ============================ AC-1: the typed spec surface ============================


class TestAC1TypedSurface:
    def test_transform_stepkind_is_additive(self) -> None:
        assert StepKind.TRANSFORM.value == "transform"
        # the four existing members are untouched (additive closed-enum growth, L-3)
        assert {"query", "evaluate", "action", "human_task"} <= {k.value for k in StepKind}

    def test_valid_transform_constructs(self) -> None:
        ts = TransformSpec.model_validate(
            {
                "ops": [
                    {
                        "derive": {
                            "target": "amount",
                            "expr": {
                                "op": "mul",
                                "args": [{"field": "unit_price"}, {"field": "qty"}],
                            },
                        }
                    },
                    {"default": {"target": "unit", "value": "criticality"}},
                    {"coerce": {"target": "amount", "to": "string"}},
                    {
                        "map_value": {
                            "target": "sev",
                            "source": {"field": "ratio"},
                            "bands": [
                                {"ceiling": "0.25", "value": "negligible"},
                                {"ceiling": "0.50", "value": "minor"},
                            ],
                            "above": "critical",
                        }
                    },
                ]
            }
        )
        assert len(ts.ops) == 4

    def test_marquee_shapes_are_schema_expressible(self) -> None:
        """SD-1 capability-completeness (schema level): the grammar CAN express the two
        marquee derivations — `amount = unit_price * qty` and the `_DOSE_LADDER` severity.
        (Runtime value-parity is AC-6, Phase C; this is the authorability proof.)"""
        # amount = unit_price * qty
        TransformSpec.model_validate(
            {
                "ops": [
                    {
                        "derive": {
                            "target": "amount",
                            "expr": {
                                "op": "mul",
                                "args": [{"field": "unit_price"}, {"field": "qty"}],
                            },
                        }
                    }
                ]
            }
        )
        # _DOSE_LADDER: dose = magnitude * duration; ratio = dose / budget; band by ratio
        TransformSpec.model_validate(
            {
                "ops": [
                    {
                        "derive": {
                            "target": "dose_ratio",
                            "expr": {
                                "op": "div",
                                "args": [
                                    {
                                        "op": "mul",
                                        "args": [
                                            {"field": "excursion_magnitude_c"},
                                            {"field": "excursion_duration_h"},
                                        ],
                                    },
                                    {"field": "stability_budget_ch"},
                                ],
                            },
                        }
                    },
                    {
                        "map_value": {
                            "target": "excursion_severity",
                            "source": {"field": "dose_ratio"},
                            "bands": [
                                {"ceiling": "0.25", "value": "negligible"},
                                {"ceiling": "0.50", "value": "minor"},
                                {"ceiling": "1.00", "value": "major"},
                            ],
                            "above": "critical",
                        }
                    },
                ]
            }
        )

    def test_empty_ops_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransformSpec.model_validate({"ops": []})

    @pytest.mark.parametrize(
        "bad_expr",
        [
            {"call": "foo"},
            {"eval": "unit*qty"},
            {"lambda": "x"},
            {"field": "x", "extra": 1},  # extra="forbid" on the leaf
            {"op": "exec", "args": [{"field": "x"}]},  # op outside the closed enum
            {"op": "system", "args": [{"field": "x"}]},
            {"attr": "obj.method"},  # no attribute-access node exists
            "unit_price * qty",  # a raw string is not an Expr node
            {"op": "add"},  # op with no args
        ],
    )
    def test_anti_eval_unrepresentable(self, bad_expr: object) -> None:
        """L-2 / SD-3: arbitrary evaluation is UNREPRESENTABLE by construction (D2 tripwire
        1). There is no call / attribute / string-of-code node — the union rejects them."""
        with pytest.raises(ValidationError):
            TransformSpec.model_validate({"ops": [{"derive": {"target": "t", "expr": bad_expr}}]})

    def test_op_body_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            TransformSpec.model_validate(
                {"ops": [{"default": {"target": "t", "value": 1, "bogus": 2}}]}
            )

    def test_deferred_op_is_not_a_member(self) -> None:
        # unit_convert / extract / normalize / concat / discrete map_value are deferred (L-7)
        with pytest.raises(ValidationError):
            TransformSpec.model_validate({"ops": [{"unit_convert": {"target": "t", "to": "usd"}}]})

    @pytest.mark.parametrize(
        "op,n_args",
        [("sub", 3), ("div", 1), ("le", 3), ("eq", 1), ("add", 1), ("mul", 1), ("min", 1)],
    )
    def test_operator_arity(self, op: str, n_args: int) -> None:
        args = [{"field": f"f{i}"} for i in range(n_args)]
        with pytest.raises(ValidationError):
            TransformSpec.model_validate(
                {"ops": [{"derive": {"target": "t", "expr": {"op": op, "args": args}}}]}
            )

    def test_expr_depth_bound(self) -> None:
        expr: dict[str, Any] = {"field": "x"}
        for _ in range(10):  # nest well past the depth-8 bound
            expr = {"op": "add", "args": [expr, {"const": "1"}]}
        with pytest.raises(ValidationError):
            TransformSpec.model_validate({"ops": [{"derive": {"target": "t", "expr": expr}}]})

    def test_map_value_requires_unbounded_top_band(self) -> None:
        with pytest.raises(ValidationError):  # missing `above` — cover would not be total
            TransformSpec.model_validate(
                {
                    "ops": [
                        {
                            "map_value": {
                                "target": "s",
                                "source": {"field": "r"},
                                "bands": [{"ceiling": "0.5", "value": "a"}],
                            }
                        }
                    ]
                }
            )

    def test_map_value_bands_strictly_ascending(self) -> None:
        with pytest.raises(ValidationError):
            TransformSpec.model_validate(
                {
                    "ops": [
                        {
                            "map_value": {
                                "target": "s",
                                "source": {"field": "r"},
                                "bands": [
                                    {"ceiling": "0.5", "value": "a"},
                                    {"ceiling": "0.25", "value": "b"},
                                ],
                                "above": "c",
                            }
                        }
                    ]
                }
            )

    def test_duplicate_produced_target_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransformSpec.model_validate(
                {
                    "ops": [
                        {"default": {"target": "x", "value": 1}},
                        {"derive": {"target": "x", "expr": {"field": "y"}}},
                    ]
                }
            )

    def test_coerce_after_derive_same_target_is_allowed(self) -> None:
        # coerce/rename over an earlier PRODUCED target is the legitimate pipeline shape
        TransformSpec.model_validate(
            {
                "ops": [
                    {"derive": {"target": "amount", "expr": {"field": "raw"}}},
                    {"coerce": {"target": "amount", "to": "string"}},
                ]
            }
        )

    def test_transform_only_on_transform_step(self) -> None:
        with pytest.raises(ValidationError):
            Step.model_validate(
                {
                    "step_id": "a",
                    "name": "A",
                    "kind": "query",
                    "transform": {"ops": [{"default": {"target": "x", "value": 1}}]},
                }
            )

    def test_transform_step_without_declaration_is_a_loadable_stub(self) -> None:
        s = Step.model_validate({"step_id": "e", "name": "E", "kind": "transform"})
        assert s.transform is None


# ============================ AC-2: H-governed + pinned ============================


class TestAC2Governance:
    def test_transform_is_a_governance_field(self) -> None:
        assert "transform" in STEP_GOVERNANCE_FIELDS

    def test_stepdraft_cannot_carry_transform(self) -> None:
        # the generator's draft type has no transform field — a leak would be a type error
        assert "transform" not in StepDraft.model_fields
        with pytest.raises(ValidationError):  # extra="forbid"
            StepDraft.model_validate(
                {
                    "step_id": "e",
                    "name": "E",
                    "kind": "transform",
                    "transform": {"ops": [{"default": {"target": "x", "value": 1}}]},
                }
            )

    def test_transform_step_owes_its_declaration(self) -> None:
        stub = Step.model_validate({"step_id": "e", "name": "E", "kind": "transform"})
        assert derive_governance_todo(stub) == ["transform"]
        assert unfilled_governance(stub) == ["transform"]

    def test_authored_transform_satisfies_the_obligation(self) -> None:
        filled = Step.model_validate(_transform_step([{"default": {"target": "x", "value": 1}}]))
        assert unfilled_governance(filled) == []

    def test_no_transform_procedure_pins_byte_identically(self) -> None:
        p = _procedure(
            [{"step_id": "read", "name": "R", "kind": "query", "input": {"reads": ["Asset"]}}]
        )
        snap, _ = governance_pin_for(p)
        # AC-13 only-when-supplied precedent: no `transform` key anywhere → config hash unchanged
        assert all("transform" not in step for step in snap["steps"])

    def test_transform_step_pins_its_declaration(self) -> None:
        p = _procedure([_transform_step([{"default": {"target": "x", "value": 1}}])])
        snap, _ = governance_pin_for(p)
        assert snap["steps"][0]["transform"]["ops"][0]["default"]["target"] == "x"

    def test_midflight_transform_edit_changes_the_hash(self) -> None:
        # a changed derivation → a different config hash → resume fails CLOSED, like a ladder edit
        _, h1 = governance_pin_for(
            _procedure([_transform_step([{"default": {"target": "x", "value": 1}}])])
        )
        _, h2 = governance_pin_for(
            _procedure([_transform_step([{"default": {"target": "x", "value": 2}}])])
        )
        assert h1 != h2

    def test_rename_pins_from_by_alias(self) -> None:
        p = _procedure([_transform_step([{"rename": {"from": "src", "target": "dst"}}])])
        snap, _ = governance_pin_for(p)
        assert snap["steps"][0]["transform"]["ops"][0]["rename"] == {"from": "src", "target": "dst"}


# ============================ AC-3: one decision surface ============================


class TestAC3OneSurface:
    def test_load_gate_accepts_a_valid_transform(self) -> None:
        p = _procedure(
            [
                _transform_step(
                    [
                        {
                            "derive": {
                                "target": "amt",
                                "expr": {"op": "mul", "args": [{"field": "p"}, {"field": "q"}]},
                            }
                        }
                    ]
                )
            ]
        )
        validate_read_bindings(p, _AGENT, frozenset({"Asset"}))  # no raise

    def test_load_gate_ignores_an_unfilled_transform_stub(self) -> None:
        # a transform step with no declaration is the governance gate's job, not the load gate's
        p = _procedure([{"step_id": "e", "name": "E", "kind": "transform"}])
        validate_read_bindings(p, _AGENT, frozenset({"Asset"}))  # no raise

    def test_load_gate_independently_rejects_an_invalid_transform(self) -> None:
        # inject a dup-target spec bypassing construction validation (model_construct) so the
        # LOAD GATE is what rejects — proving it calls validate_transform_spec itself (no drift).
        p = _procedure([_transform_step([{"default": {"target": "x", "value": 1}}])])
        p.steps[0].transform = TransformSpec.model_construct(
            ops=[
                DefaultOp(default=DefaultBody(target="x", value=1)),
                DefaultOp(default=DefaultBody(target="x", value=2)),
            ]
        )
        with pytest.raises(ProcedureError, match="invalid transform declaration"):
            validate_read_bindings(p, _AGENT, frozenset({"Asset"}))

    def test_the_predicate_is_one_surface(self) -> None:
        """The SAME rule decides at construction AND at the load gate (compile = Phase B):
        a dup-target spec is rejected at construction (ValidationError) and, when the model
        validator is bypassed, by validate_transform_spec directly (ValueError) — one rule."""
        with pytest.raises(ValidationError):
            TransformSpec.model_validate(
                {
                    "ops": [
                        {"default": {"target": "x", "value": 1}},
                        {"derive": {"target": "x", "expr": {"field": "y"}}},
                    ]
                }
            )
        bypassed = TransformSpec.model_construct(
            ops=[
                DefaultOp(default=DefaultBody(target="x", value=1)),
                DefaultOp(default=DefaultBody(target="x", value=2)),
            ]
        )
        with pytest.raises(ValueError, match="dead write"):
            validate_transform_spec(bypassed)
