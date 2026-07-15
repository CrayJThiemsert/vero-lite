"""Generic transform-step compile + execute seam (PLAN-0077 Step 2 / Phase B).

Renders ADR-0031 D3 row-1 + the ADR-016 Q4 OQ-3 downstream-transform home. The
**compile** and **execute** halves of the transform grammar, mirroring
``query_step.py`` 1:1 (PLAN-0061 the direct template):

- **compile** — :func:`plan_transform`: pure, total, no I/O. Turns a ``transform``
  step into a frozen :class:`TransformPlan` **or** a typed, auditable
  :class:`TransformRefusal`. It re-runs the SAME structural predicate the load
  gate runs (:func:`spec.validate_transform_spec` — PLAN-0077 L-6), so load-time
  acceptance and run-time compile cannot drift (the ``_validate_join_project``
  no-drift property, extended). Every step shape either compiles or refuses —
  there is no silently-empty path (**refusal ≠ no-op**: a transform never passes
  rows through unchanged while claiming to derive).
- **execute** — :class:`TransformStepExecutor`: a ``@dataclass(frozen=True)`` with
  **no adapter, no I/O, no LLM, no registry** (it is engine-generic — OQ-3
  settled: adapter-free, so every composing factory can register ONE shared
  instance uniformly). It applies the compiled row-local ops to each
  ``from``-threaded input row.

Deterministic throughout — **no LLM anywhere in the derivation path** (L-4,
governed ≠ generated): same inputs → same derived fields; no clock, no
randomness. Transform is ontology-INDEPENDENT (row-local, SD-8), so — unlike the
join/project grammar — the compile takes no ``meta`` and resolves nothing against
the ontology.

The failure posture is **fail-closed** (SD-7): a missing / non-coercible source
field, a division by zero, and a non-finite (NaN / ±Inf) result each refuse the
whole step typed — transform outputs feed governance gates, and a silently
dropped or silently-nulled row upstream of a gate fails DANGEROUS, not closed.
The ``default`` op is the *authored* escape hatch: if absence is legal the author
declares the default; the engine never invents one.
"""

from __future__ import annotations

import operator
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from functools import reduce
from typing import Any

from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.query_step import _json_safe
from services.engine.procedures.spec import (
    CoerceBody,
    CoerceOp,
    DefaultOp,
    DeriveOp,
    Expr,
    ExprConst,
    ExprField,
    MapValueBody,
    RenameOp,
    Step,
    StepKind,
    TransformOp,
    validate_transform_spec,
)

# The provisional compare operators (SD-2/SD-3) — binary, yield a bool. Keyed by the
# SAME strings the closed ``TransformCompareOp`` enum uses, so the evaluator and the
# schema cannot disagree on the vocabulary.
_COMPARE_FUNCS: dict[str, Callable[[Decimal, Decimal], bool]] = {
    "le": operator.le,
    "lt": operator.lt,
    "ge": operator.ge,
    "gt": operator.gt,
    "eq": operator.eq,
}


class TransformRefusalKind(str, Enum):
    """Why a transform step was refused (PLAN-0077 OQ-1 — the typed refusal taxonomy).

    One enum spanning both phases (the :class:`~query_step.ReadRefusalKind` grain):
    the first three are **compile-time** refusals raised by :func:`plan_transform`;
    the rest are **execute-time** fail-closed refusals raised by
    :class:`TransformStepExecutor` on a per-row derivation that cannot honestly
    complete (SD-7 — never a silent drop / null upstream of a governance gate).
    """

    # compile-time (plan_transform)
    NOT_A_TRANSFORM_STEP = "not_a_transform_step"
    MISSING_DECLARATION = "missing_declaration"
    INVALID_SPEC = "invalid_spec"
    # execute-time (fail-closed, SD-7)
    MISSING_INPUT_FIELD = "missing_input_field"
    NON_MAPPING_ROW = "non_mapping_row"
    NON_NUMERIC_OPERAND = "non_numeric_operand"
    NON_FINITE_RESULT = "non_finite_result"


class TransformRefusal(Exception):  # noqa: N818 — a refusal is deliberately NOT an *Error (OQ-1)
    """A typed, structured, auditable transform refusal (PLAN-0077 AC-4 / SD-7).

    Refusal ≠ no-op: a compiled transform either derives every declared field or
    declines the whole step — it never silently passes rows through while claiming
    to derive. Carries structured fields (``refusal_kind`` / ``step_id`` /
    ``detail``) so persisted records and audit rows can name the refusal without
    parsing prose (the :class:`~query_step.ReadRefusal` grain). Raised at compile
    (:func:`plan_transform`) and at execute (fail-closed per-row); an executor
    raise propagates to the orchestrator's D4 fail-and-divert, exactly like a
    join ``fuse`` refusal.
    """

    def __init__(
        self, refusal_kind: TransformRefusalKind, *, step_id: str, detail: str = ""
    ) -> None:
        self.refusal_kind = refusal_kind
        self.step_id = step_id
        self.detail = detail
        message = f"transform refused ({refusal_kind.value}) at step '{step_id}'"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)


@dataclass(frozen=True)
class TransformPlan:
    """The compiled, executable transform of a single ``transform`` step (AC-4).

    The sibling of :class:`~query_step.ReadPlan`. The ops are already typed,
    validated Pydantic models (arity / depth / ascending-band invariants enforced
    at construction; the cross-op dead-write invariant enforced by
    :func:`~spec.validate_transform_spec`, re-run at compile) — so the plan just
    carries them as an immutable tuple. Row-local (SD-8): each op reads and writes
    the threaded row's own flat fields.
    """

    step_id: str
    ops: tuple[TransformOp, ...]


def plan_transform(step: Step) -> TransformPlan:
    """Compile a transform step's declared derivation, or refuse typed (AC-4).

    Pure and total: no I/O, no adapter, no registry, no ontology ``meta`` (unlike
    :func:`~query_step.plan_read` — transform is ontology-independent, SD-8). Every
    ``Step`` shape either returns a :class:`TransformPlan` or raises a typed
    :class:`TransformRefusal`:

    - a non-transform step → ``NOT_A_TRANSFORM_STEP`` (the compile seam is a
      transform-step contract, mirroring ``plan_read``'s kind guard);
    - a transform step with **no** declaration → ``MISSING_DECLARATION`` (an
      unfilled governance stub that the run never reaches — ``validate_runnable``
      → ``validate_governance_complete`` rejects it first — but the compile still
      refuses loudly rather than pass rows through, refusal ≠ no-op);
    - a structurally-invalid declaration → ``INVALID_SPEC``, via the SAME
      :func:`~spec.validate_transform_spec` the load gate runs (L-6, one decision
      surface — so load-acceptance and run-compile cannot drift).
    """
    if step.kind is not StepKind.TRANSFORM:
        raise TransformRefusal(
            TransformRefusalKind.NOT_A_TRANSFORM_STEP,
            step_id=step.step_id,
            detail=(
                f"kind '{step.kind.value}' is not a transform step — the transform compile "
                "seam is a transform-step contract"
            ),
        )
    transform = step.transform
    if transform is None:
        raise TransformRefusal(
            TransformRefusalKind.MISSING_DECLARATION,
            step_id=step.step_id,
            detail=(
                "transform step declares no transform — an unfilled governance stub "
                "(derive_governance_todo), not a runnable derivation"
            ),
        )
    try:
        validate_transform_spec(transform)  # the shared structural predicate (L-6)
    except ValueError as exc:
        raise TransformRefusal(
            TransformRefusalKind.INVALID_SPEC, step_id=step.step_id, detail=str(exc)
        ) from exc
    return TransformPlan(step_id=step.step_id, ops=tuple(transform.ops))


def _op_summary(op: TransformOp) -> tuple[str, str]:
    """``(op_name, target)`` for a provenance entry — a display concern only."""
    if isinstance(op, DeriveOp):
        return "derive", op.derive.target
    if isinstance(op, DefaultOp):
        return "default", op.default.target
    if isinstance(op, CoerceOp):
        return "coerce", op.coerce.target
    if isinstance(op, RenameOp):
        return "rename", op.rename.target
    return "map_value", op.map_value.target


@dataclass(frozen=True)
class TransformStepExecutor:
    """The generic, deterministic ``transform`` StepExecutor — the execute half
    (PLAN-0077 Phase B; AC-5).

    Engine-generic (OQ-3): **no adapter, no I/O, no LLM, no registry** — nothing to
    inject, so it is a fieldless frozen dataclass and every composing factory can
    register one shared instance uniformly. It consumes the ``from``-threaded input
    set and applies the compiled ops **row-local** (SD-8): each op reads and writes
    the row's own flat fields; one input row → the same row enriched.

    Arithmetic is exact ``Decimal`` — never binary float on an authority quantity
    (the ``_spend`` / ``_positive_decimal`` house discipline). Failure is
    fail-closed (SD-7): a missing / non-coercible source field, a division by zero,
    and a non-finite result each raise a typed :class:`TransformRefusal` for the
    whole step (caught by D4 fail-and-divert), never a silent per-row drop. Outputs
    are JSONB-safe via the shared ``_json_safe`` boundary (the derived ``Decimal``s
    a run persists as JSONB coerce to their exact string form, exactly as the
    supply_chain seed's ``Decimal→str`` coercions do). Every op emits a provenance
    trace entry (targets written, per-op row counts — the ``read_provenance``
    grain).
    """

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        """Compile-or-refuse, then apply the ops row-local to each threaded row."""
        plan = plan_transform(step)  # raises TransformRefusal → D4 fail-and-divert
        op_write_counts = [0] * len(plan.ops)
        out_rows: list[dict[str, Any]] = []
        for raw_row in input_set:
            if not isinstance(raw_row, Mapping):
                raise TransformRefusal(
                    TransformRefusalKind.NON_MAPPING_ROW,
                    step_id=plan.step_id,
                    detail=(
                        "transform is row-local (SD-8) but the threaded input row is a "
                        f"{type(raw_row).__name__}, not a field mapping"
                    ),
                )
            working: dict[str, Any] = dict(raw_row)
            for i, op in enumerate(plan.ops):
                if self._apply_op(op, working, plan.step_id):
                    op_write_counts[i] += 1
            out_rows.append(working)

        safe_rows = _json_safe(out_rows)
        provenance: list[dict[str, Any]] = []
        for i, op in enumerate(plan.ops):
            name, target = _op_summary(op)
            provenance.append(
                {
                    "kind": "transform_provenance",
                    "op": name,
                    "target": target,
                    "rows_written": op_write_counts[i],
                    "summary": (
                        f"{name} '{target}': wrote {op_write_counts[i]}/{len(input_set)} rows"
                    ),
                }
            )
        audit: dict[str, Any] = {
            "actor": ctx.agent.agent_id,
            "actor_kind": "engine",
            "deterministic": True,
            "transform": True,
            "op_count": len(plan.ops),
            "row_count": len(input_set),
        }
        return StepOutcome(output=safe_rows, reasoning_trace=provenance, audit=audit)

    def _apply_op(self, op: TransformOp, row: dict[str, Any], step_id: str) -> bool:
        """Apply ONE op in place to ``row``; return whether it wrote its target.

        (``default`` writes only when the target is absent — a present target is a
        no-write, so its provenance count reflects real fills. Every other op
        writes when it does not refuse.)
        """
        if isinstance(op, DeriveOp):
            row[op.derive.target] = self._eval_expr(op.derive.expr, row, step_id)
            return True
        if isinstance(op, DefaultOp):
            if op.default.target in row:
                return False
            row[op.default.target] = op.default.value
            return True
        if isinstance(op, CoerceOp):
            return self._apply_coerce(op.coerce, row, step_id)
        if isinstance(op, RenameOp):
            source = op.rename.source
            if source not in row:
                raise TransformRefusal(
                    TransformRefusalKind.MISSING_INPUT_FIELD,
                    step_id=step_id,
                    detail=f"rename source '{source}' is absent on the row (fail closed, SD-7)",
                )
            # COPY semantics (non-destructive): target ← source, source retained.
            # v1 has no field-drop op (out of scope) and dropping a field upstream
            # of a gate risks the SD-7 fail-dangerous shape; a move is a follow-on.
            row[op.rename.target] = row[source]
            return True
        # MapValueOp — band a numeric source (SD-2; the case-2 _DOSE_LADDER shape)
        body = op.map_value
        source_value = self._eval_expr(body.source, row, step_id)
        banded = self._to_decimal(source_value, step_id, detail=f"map_value '{body.target}' source")
        row[body.target] = self._band(banded, body)
        return True

    def _apply_coerce(self, body: CoerceBody, row: dict[str, Any], step_id: str) -> bool:
        """``coerce``: convert an existing field to a v1 target type in place (SD-2)."""
        if body.target not in row:
            raise TransformRefusal(
                TransformRefusalKind.MISSING_INPUT_FIELD,
                step_id=step_id,
                detail=f"coerce target '{body.target}' is absent on the row (fail closed, SD-7)",
            )
        value = row[body.target]
        if body.to == "string":
            row[body.target] = str(value)
        else:  # decimal — exact, validated (a non-numeric value fails closed)
            row[body.target] = self._to_decimal(
                value, step_id, detail=f"coerce '{body.target}' to decimal"
            )
        return True

    @staticmethod
    def _band(value: Decimal, body: MapValueBody) -> str:
        """Inclusive-ceiling, unbounded-top banding (reproduces ``derive_excursion_severity``).

        Bands are strictly-ascending by ceiling (schema-enforced); the first band
        whose inclusive ceiling covers ``value`` wins, else the mandatory ``above``
        top band — cover is TOTAL, a value above every ceiling always bands (never
        falls through, the fail-dangerous shape PLAN-0074 fixed)."""
        for band in body.bands:
            if value <= Decimal(band.ceiling):
                return band.value
        return body.above

    def _eval_expr(self, expr: Expr, row: dict[str, Any], step_id: str) -> Any:
        """Evaluate a ``derive`` expression tree over the row (SD-3).

        A field leaf reads the row's flat field (a bare-leaf derive is the typed
        copy); a const leaf is its authored literal; an op node coerces each
        evaluated operand to exact ``Decimal`` and applies the closed operator. The
        only node types are field / const / op — there is no call, attribute, or
        string-of-code node, so arbitrary evaluation is unrepresentable (the schema
        already guarantees this; the evaluator never introduces one)."""
        if isinstance(expr, ExprField):
            if expr.field not in row:
                raise TransformRefusal(
                    TransformRefusalKind.MISSING_INPUT_FIELD,
                    step_id=step_id,
                    detail=f"derive reads absent field '{expr.field}' (fail closed, SD-7)",
                )
            return row[expr.field]
        if isinstance(expr, ExprConst):
            return expr.const
        # ExprOp — evaluate operands, coerce each to exact Decimal, apply the operator
        operands = [
            self._to_decimal(
                self._eval_expr(arg, row, step_id), step_id, detail=f"operator '{expr.op}' operand"
            )
            for arg in expr.args
        ]
        return self._apply_operator(expr.op, operands, step_id)

    def _to_decimal(self, value: Any, step_id: str, *, detail: str) -> Decimal:
        """Coerce a value to exact ``Decimal(str(value))`` — never binary float on an
        authority quantity — or refuse typed (SD-7).

        A bool is rejected as a non-numeric operand (a flag is not a quantity); a
        non-numeric value refuses ``NON_NUMERIC_OPERAND``; a non-finite (NaN / ±Inf)
        input refuses ``NON_FINITE_RESULT`` — a non-finite scalar must never band or
        arithmetic-combine (the ``cold_chain_assess`` fail-closed lesson)."""
        if isinstance(value, bool):
            raise TransformRefusal(
                TransformRefusalKind.NON_NUMERIC_OPERAND,
                step_id=step_id,
                detail=f"{detail}: a boolean is not a numeric quantity",
            )
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise TransformRefusal(
                TransformRefusalKind.NON_NUMERIC_OPERAND,
                step_id=step_id,
                detail=f"{detail}: {value!r} is not numeric",
            ) from exc
        if not result.is_finite():
            raise TransformRefusal(
                TransformRefusalKind.NON_FINITE_RESULT,
                step_id=step_id,
                detail=f"{detail}: non-finite value {value!r}",
            )
        return result

    def _apply_operator(self, op: str, operands: list[Decimal], step_id: str) -> Decimal | bool:
        """Apply a closed arithmetic / compare operator to exact-``Decimal`` operands.

        Compare (``le`` / ``lt`` / ``ge`` / ``gt`` / ``eq``) is provisional, binary,
        and yields a bool (dispatched via :data:`_COMPARE_FUNCS`); arithmetic yields
        a ``Decimal`` (:meth:`_apply_arithmetic`). Arity is guaranteed by the schema
        (``ExprOp._validate_arity``), so the binary unpackings are safe."""
        compare = _COMPARE_FUNCS.get(op)
        if compare is not None:
            left, right = operands
            return compare(left, right)
        return self._apply_arithmetic(op, operands, step_id)

    def _apply_arithmetic(self, op: str, operands: list[Decimal], step_id: str) -> Decimal:
        """Exact-``Decimal`` arithmetic; a non-finite result (e.g. overflow) or a
        division by zero fails closed BEFORE it can leak (SD-7)."""
        if op == "add":
            return self._finite(reduce(operator.add, operands), step_id, op)
        if op == "mul":
            return self._finite(reduce(operator.mul, operands), step_id, op)
        if op == "sub":
            return self._finite(operands[0] - operands[1], step_id, op)
        if op == "min":
            return min(operands)
        if op == "max":
            return max(operands)
        # div — refuse BEFORE dividing so a DivisionByZero never leaks
        if operands[1] == 0:
            raise TransformRefusal(
                TransformRefusalKind.NON_FINITE_RESULT,
                step_id=step_id,
                detail="division by zero (fail closed, SD-7)",
            )
        return self._finite(operands[0] / operands[1], step_id, op)

    @staticmethod
    def _finite(value: Decimal, step_id: str, op: str) -> Decimal:
        """An arithmetic result must be finite (fail closed on NaN / ±Inf, SD-7)."""
        if not value.is_finite():
            raise TransformRefusal(
                TransformRefusalKind.NON_FINITE_RESULT,
                step_id=step_id,
                detail=f"operator '{op}' produced a non-finite result",
            )
        return value
