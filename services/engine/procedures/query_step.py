"""Generic query-step compile seam (PLAN-0048 Step 1; renders ADR-016 Q4).

The **compile** third of the compile / execute / inspect factoring (PLAN-0048
D-N3 — the dbt-MCP ``list/discover + constrained run`` 3-tool shape; MCP
plumbing itself is an explicit non-goal):

- **compile** — :func:`plan_read`: pure, no I/O; turns a query step + agent +
  ontology registry into an executable :class:`ReadPlan` **or** a typed,
  auditable :class:`ReadRefusal`. Out-of-coverage reads refuse loudly — never
  a guess, never a silent ``[]`` masquerading as "no data" (D-N1 / must 1).
- **execute** — the adapter-injected ``QueryStepExecutor`` (PLAN-0048 Step 2)
  runs a compiled plan: exactly ONE ``fetch_objects`` dispatch per plan, no
  retry/repair loop in v1 (D-N2; any future repair loop is a new PLAN and must
  stay deterministic and inside ``reads ∩ object_types`` — no LLM reshaping).
- **inspect** — :func:`readable_object_types`: the agent's read coverage
  (ontology ∩ allowlist; empty allowlist = unconstrained, LOCKED-5/OQ-6).

Deterministic throughout — **no LLM anywhere in the read path** (LOCKED-6,
governed ≠ generated): this module is the deterministic-disposer half of the
CaMeL-shaped "LLM proposes, deterministic policy engine disposes" architecture.
v1 executes SINGLE declared reads only (SD-1, ratified 2026-07-04): multi-read
joins and projections stay with the hand-written per-vertical seeds —
deprecate-in-place, never migrated (SD-3; e.g. the procurement hero-demo
``_SeedQuery`` 3-type join) — until a join grammar is ratified (an ADR-016
amendment, out of scope here).

**Future repair-loop contract (D-N2 — documented, deliberately NOT built).**
v1 has no execute-validate-retry loop: exactly one dispatch, ever. If one is
ever added it MUST (1) carry a FIXED maximum attempt count, (2) keep every
attempt inside ``reads ∩ Agent.allowed.object_types`` — the same shared bound,
re-checked per attempt, and (3) stay fully deterministic — no LLM proposes a
reshaped read or ``where`` (LOCKED-6). Adding such a loop is a NEW PLAN; the
llm-db reliability brief's "bounded execute-validate-retry inside the existing
allowlist" finding (gitignored, 2026-07-03) is its authorizing context.

The ontology/allowlist bound is THE shared predicate
:func:`services.engine.procedures.orchestrator.read_bound_violation` — the same
function the PLAN-0046 load gate uses, so load-time acceptance and run-time
dispatch cannot drift (AC-3).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from services.engine.data_adapter import DataAdapter
from services.engine.procedures.orchestrator import (
    RunContext,
    StepOutcome,
    matches_where,
    read_bound_violation,
)
from services.engine.procedures.spec import Agent, Step, StepKind


class ReadRefusalKind(str, Enum):
    """Why a declared read was refused (PLAN-0048 D-N1 — the typed refusal taxonomy).

    The first two mirror :data:`orchestrator.ReadBoundViolation` (the shared
    ontology/allowlist bound); the last two are compile-seam shape refusals.
    """

    UNKNOWN_OBJECT_TYPE = "unknown_object_type"
    OUTSIDE_ALLOWLIST = "outside_allowlist"
    UNSUPPORTED_READ_SHAPE = "unsupported_read_shape"
    UNBOUND_QUERY = "unbound_query"


class ReadRefusal(Exception):  # noqa: N818 — a refusal is deliberately NOT an *Error (D-N1)
    """A typed, structured, auditable read refusal (PLAN-0048 D-N1 / must 1).

    Refusal ≠ no-data: an in-coverage fetch that finds zero rows COMPLETES the
    step with ``output=[]`` plus provenance (Step 2); this exception is the
    other thing — the engine declining to guess. Carries structured fields
    (``refusal_kind`` / ``step_id`` / ``object_type``) so persisted records and
    audit rows can name the refusal without parsing prose.
    """

    def __init__(
        self,
        refusal_kind: ReadRefusalKind,
        *,
        step_id: str,
        object_type: str | None = None,
        detail: str = "",
    ) -> None:
        self.refusal_kind = refusal_kind
        self.step_id = step_id
        self.object_type = object_type
        self.detail = detail
        target = f" object_type '{object_type}'" if object_type is not None else ""
        message = f"read refused ({refusal_kind.value}) at step '{step_id}'{target}"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)


@dataclass(frozen=True)
class ReadPlan:
    """The compiled, executable read of a single query step (AC-1).

    ``where`` is the OQ-4 engine-side post-fetch field-equality narrowing —
    carried here, applied by the executor over the FETCHED set (never pushed
    down to the adapter's ``filter_expr``).
    """

    step_id: str
    object_type: str
    where: Mapping[str, Any] = field(default_factory=dict)


def plan_read(step: Step, agent: Agent, object_type_names: frozenset[str]) -> ReadPlan:
    """Compile a query step's declared read, or refuse typed (AC-1/AC-2).

    Pure and total: no I/O, no adapter; every ``Step`` shape either returns a
    :class:`ReadPlan` or raises :class:`ReadRefusal` — there is no
    silently-empty path. The v1 executable shape is a SINGLE declared read
    (SD-1): ``reads`` with more than one entry, ``reads`` combined with an
    intra-run ``from`` thread, and a reads-absent entry-point query all refuse.
    A reads-absent step that threads ``from`` a prior step is not a declared
    read at all — identity pass-through belongs to the executor (SD-1), so the
    compile seam refuses it rather than inventing a plan.
    """
    if step.kind is not StepKind.QUERY:
        raise ReadRefusal(
            ReadRefusalKind.UNSUPPORTED_READ_SHAPE,
            step_id=step.step_id,
            detail=(
                f"kind '{step.kind.value}' is not a query step — "
                "the compile seam is a query-step contract"
            ),
        )
    step_input = step.input
    if step_input is None or not step_input.reads:
        from_step = step_input.from_step if step_input is not None else None
        if from_step is not None:
            raise ReadRefusal(
                ReadRefusalKind.UNSUPPORTED_READ_SHAPE,
                step_id=step.step_id,
                detail=(
                    f"no declared read; input threads from step '{from_step}' — identity "
                    "pass-through is the executor's case (SD-1), not a compilable read"
                ),
            )
        raise ReadRefusal(
            ReadRefusalKind.UNBOUND_QUERY,
            step_id=step.step_id,
            detail=(
                "entry-point query step declares no reads — refusing rather than "
                "returning a silent empty set"
            ),
        )
    reads = step_input.reads
    if step_input.from_step is not None:
        raise ReadRefusal(
            ReadRefusalKind.UNSUPPORTED_READ_SHAPE,
            step_id=step.step_id,
            detail=(
                f"reads {reads} + from '{step_input.from_step}' are two competing input "
                "sources (where would double-apply) — declare one"
            ),
        )
    if len(reads) > 1:
        raise ReadRefusal(
            ReadRefusalKind.UNSUPPORTED_READ_SHAPE,
            step_id=step.step_id,
            detail=(
                f"multi-read {reads} — v1 executes single reads only (SD-1); "
                "a join grammar is a future ADR-016 amendment"
            ),
        )
    object_type = reads[0]
    violation = read_bound_violation(object_type, object_type_names, agent.allowed.object_types)
    if violation is not None:
        raise ReadRefusal(ReadRefusalKind(violation), step_id=step.step_id, object_type=object_type)
    where = dict(step_input.where) if step_input.where else {}
    return ReadPlan(step_id=step.step_id, object_type=object_type, where=where)


def readable_object_types(agent: Agent, object_type_names: frozenset[str]) -> frozenset[str]:
    """The inspect half (D-N3): the agent's read coverage.

    ``ontology ∩ allowlist``; an EMPTY ``allowed.object_types`` is
    UNCONSTRAINED (LOCKED-5 / OQ-6, mirroring ``step_kinds``) and yields the
    whole ontology set. Allowlist entries naming unknown object_types simply
    drop out of the intersection — coverage never exceeds the ontology.
    """
    allowed = agent.allowed.object_types
    if not allowed:
        return object_type_names
    return object_type_names & frozenset(allowed)


def _json_safe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """JSON-normalize fetched rows at the adapter boundary (PLAN-0048 Step 3,
    disclosed).

    Real adapters return rows carrying datetimes; the write-ahead path
    (PLAN-0047 Step 4) persists a step's output set as JSONB, which refuses
    them. One ``default=str`` coercion at THE adapter boundary keeps every
    downstream surface — artifact persistence, ``where`` narrowing, the
    judge's numeric reads — consistent. Keys and dict shape are unchanged, so
    SD-2's raw-dict threading stands; only non-JSON scalar TYPES coerce (a
    datetime becomes its ``str``), which is what landing in a JSONB column
    would force anyway.
    """
    return cast(list[dict[str, Any]], json.loads(json.dumps(rows, default=str)))


@dataclass(frozen=True)
class QueryStepExecutor:
    """The generic, deterministic ``query`` StepExecutor — the execute half
    (PLAN-0048 Step 2; AC-4..AC-7).

    Constructor-injected (the PLAN-0046 SD-1 purity rationale; the
    ``ActionStepExecutor(client_factory=...)`` shape): the composing factory
    supplies ``registry.get_adapter(vertical)`` and the vertical's ontology
    object-type names — the executor itself performs no registry or filesystem
    I/O. Per execution it makes **exactly ONE** ``fetch_objects`` dispatch
    (D-N2 — the bound is a tested property, and an adapter raise propagates to
    D4 fail-and-divert with no re-fetch); ``where`` narrows the FETCHED set
    engine-side via the shared :func:`orchestrator.matches_where` predicate
    (LOCKED-3 — the adapter's ``filter_expr`` is never used). A reads-absent
    step that threads ``from`` a prior step is the SD-1 identity pass-through
    (no dispatch); every other shape compiles-or-refuses via
    :func:`plan_read`, which raises BEFORE any dispatch.
    """

    adapter: DataAdapter
    object_type_names: frozenset[str]

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        """Run the step's declared read (or the SD-1 pass-through), or refuse typed."""
        step_input = step.input
        if (
            (step_input is None or not step_input.reads)
            and step_input is not None
            and step_input.from_step is not None
        ):
            trace: list[dict[str, Any]] = [
                {
                    "kind": "read_passthrough",
                    "summary": (
                        f"step '{step.step_id}': no declared read; passing through "
                        f"{len(input_set)} entities threaded from '{step_input.from_step}' (SD-1)"
                    ),
                }
            ]
            audit: dict[str, Any] = {
                "actor": ctx.agent.agent_id,
                "actor_kind": "engine",
                "deterministic": True,
                "passthrough": True,
            }
            return StepOutcome(output=list(input_set), reasoning_trace=trace, audit=audit)
        plan = plan_read(step, ctx.agent, self.object_type_names)
        fetched = _json_safe(await self.adapter.fetch_objects(plan.object_type))
        output = (
            [entity for entity in fetched if matches_where(entity, plan.where)]
            if plan.where
            else list(fetched)
        )
        provenance: list[dict[str, Any]] = [
            {
                "kind": "read_provenance",
                "summary": (
                    f"read '{plan.object_type}': fetched {len(fetched)}, "
                    f"{len(output)} after where"
                ),
                "object_type": plan.object_type,
                "fetched_count": len(fetched),
                "post_where_count": len(output),
            }
        ]
        read_audit: dict[str, Any] = {
            "actor": ctx.agent.agent_id,
            "actor_kind": "engine",
            "deterministic": True,
            "object_type": plan.object_type,
        }
        return StepOutcome(output=output, reasoning_trace=provenance, audit=read_audit)
