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
from services.engine.ontology_meta import OntologyMeta
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepOutcome,
    _validate_join_project,
    matches_where,
    read_bound_violation,
)
from services.engine.procedures.spec import Agent, Step, StepKind


class ReadRefusalKind(str, Enum):
    """Why a declared read was refused (PLAN-0048 D-N1 — the typed refusal taxonomy).

    The first two mirror :data:`orchestrator.ReadBoundViolation` (the shared
    ontology/allowlist bound); the next two are compile-seam shape refusals.
    ``JOIN_SHAPE_VIOLATION`` (PLAN-0061 Step 3; the PLAN's OQ-1 settled at step
    review as ONE additive member) covers every join/project violation — a
    structural check failing at compile (mirroring the load gate) or the runtime
    ``fuse`` non-singleton refusal. Existing members untouched (AC-7).
    """

    UNKNOWN_OBJECT_TYPE = "unknown_object_type"
    OUTSIDE_ALLOWLIST = "outside_allowlist"
    UNSUPPORTED_READ_SHAPE = "unsupported_read_shape"
    UNBOUND_QUERY = "unbound_query"
    JOIN_SHAPE_VIOLATION = "join_shape_violation"


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


@dataclass(frozen=True)
class CompiledJoin:
    """One resolved join of a :class:`JoinReadPlan` (PLAN-0061 Step 3).

    Keys are RESOLVED at compile — from the declared link's promoted typed
    ``foreign_key`` (the SD-A governed default) or the explicit ``on`` override;
    a ``fuse`` join carries no keys (both sides must be exactly one row
    post-narrowing, refused typed otherwise at execution). ``left`` reads from
    the accumulated/base side, ``right`` from the joined side. ``where``
    narrows the JOINED side post-fetch, pre-join (the single ``matches_where``
    predicate — LOCKED-3).
    """

    with_type: str
    left: str | None
    right: str | None
    fuse: bool
    where: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JoinReadPlan:
    """The compiled multi-read join/projection plan (PLAN-0061 Step 3; Q4 SD-B).

    The sibling of :class:`ReadPlan` for a ``join``/``project``-declaring step:
    exactly one ``fetch_objects`` dispatch per entry of ``reads`` (the D-N2
    bound extended), the SD-1 pinned pipeline order (base ``where`` → per-join
    ``where`` → joins in declaration order → latest-per-group → field renames),
    and the SD-5 determinism contract (argmax ``order_by`` per ``group_by``,
    ties broken by max ``tie_break`` — the base type's declared primary_key;
    rows missing either field are excluded + counted in provenance).
    """

    step_id: str
    reads: tuple[str, ...]
    where: Mapping[str, Any] = field(default_factory=dict)
    joins: tuple[CompiledJoin, ...] = ()
    group_by: str | None = None
    order_by: str | None = None
    tie_break: str | None = None
    fields: Mapping[str, str] = field(default_factory=dict)


def _compile_join_plan(
    step: Step, agent: Agent, object_type_names: frozenset[str], meta: OntologyMeta
) -> JoinReadPlan:
    """Compile a join/project-declaring step into a :class:`JoinReadPlan`.

    Re-runs the SAME structural validation the load gate runs
    (:func:`orchestrator._validate_join_project` — one decision surface, so
    load-acceptance and run-compile cannot drift, the PLAN-0048 AC-3 property
    extended), converting a structural violation into the typed
    ``JOIN_SHAPE_VIOLATION`` refusal. Every declared read is bound-checked via
    the single shared :func:`read_bound_violation` predicate (closing the
    fact-3 reads[0]-only note).
    """
    step_input = step.input
    assert step_input is not None and step_input.reads  # guarded by plan_read
    for object_type in step_input.reads:
        violation = read_bound_violation(object_type, object_type_names, agent.allowed.object_types)
        if violation is not None:
            raise ReadRefusal(
                ReadRefusalKind(violation), step_id=step.step_id, object_type=object_type
            )
    try:
        _validate_join_project(step, meta)
    except ProcedureError as exc:
        raise ReadRefusal(
            ReadRefusalKind.JOIN_SHAPE_VIOLATION, step_id=step.step_id, detail=str(exc)
        ) from exc

    links = {link.name: link for link in meta.link_types}
    base = step_input.reads[0]
    joins: list[CompiledJoin] = []
    for spec in step_input.join or []:
        if spec.link is not None:
            link = links[spec.link]
            fk = link.foreign_key
            assert fk is not None  # _validate_join_project refused a keyless link
            # the link may point either direction; `left` always reads the
            # accumulated/base side, `right` the joined (`with`) side.
            if link.from_type == spec.with_read:
                left, right = fk.to_property, fk.from_property
            else:
                left, right = fk.from_property, fk.to_property
            joins.append(
                CompiledJoin(
                    with_type=spec.with_read,
                    left=left,
                    right=right,
                    fuse=False,
                    where=dict(spec.where) if spec.where else {},
                )
            )
        elif spec.on is not None:
            joins.append(
                CompiledJoin(
                    with_type=spec.with_read,
                    left=spec.on.left,
                    right=spec.on.right,
                    fuse=False,
                    where=dict(spec.where) if spec.where else {},
                )
            )
        else:  # fuse — validated exactly-one-of by the schema
            joins.append(
                CompiledJoin(
                    with_type=spec.with_read,
                    left=None,
                    right=None,
                    fuse=True,
                    where=dict(spec.where) if spec.where else {},
                )
            )

    group_by: str | None = None
    order_by: str | None = None
    tie_break: str | None = None
    project = step_input.project
    if project is not None and project.latest_per is not None:
        link = links[project.latest_per]
        assert link.foreign_key is not None  # refused above otherwise
        group_by = link.foreign_key.from_property
        order_by = project.order_by
        base_obj = next(t for t in meta.object_types if t.name == base)
        tie_break = base_obj.primary_key

    return JoinReadPlan(
        step_id=step.step_id,
        reads=tuple(step_input.reads),
        where=dict(step_input.where) if step_input.where else {},
        joins=tuple(joins),
        group_by=group_by,
        order_by=order_by,
        tie_break=tie_break,
        fields=dict(project.fields) if project is not None and project.fields else {},
    )


def plan_read(
    step: Step,
    agent: Agent,
    object_type_names: frozenset[str],
    *,
    meta: OntologyMeta | None = None,
) -> ReadPlan | JoinReadPlan:
    """Compile a query step's declared read, or refuse typed (AC-1/AC-2).

    Pure and total: no I/O, no adapter; every ``Step`` shape either returns a
    plan or raises :class:`ReadRefusal` — there is no silently-empty path.
    A SINGLE declared read compiles to :class:`ReadPlan` exactly as PLAN-0048
    shipped it (byte-identical path, AC-7). A step declaring the PLAN-0061
    ``join``/``project`` grammar compiles to :class:`JoinReadPlan` — this
    REQUIRES ``meta`` (the typed join keys live there; refused typed when
    absent, mirroring the load gate's fail-loud posture). Multi-read WITHOUT
    the grammar still refuses (the SD-1 refusal narrowed, not vanished), as do
    ``reads``+``from`` competition and reads-absent entry-point queries.
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
    if step_input.join or step_input.project:
        if meta is None:
            raise ReadRefusal(
                ReadRefusalKind.JOIN_SHAPE_VIOLATION,
                step_id=step.step_id,
                detail=(
                    "join/project declared but the executor holds no ontology meta — "
                    "construct QueryStepExecutor with meta=... (PLAN-0061)"
                ),
            )
        return _compile_join_plan(step, agent, object_type_names, meta)
    if len(reads) > 1:
        raise ReadRefusal(
            ReadRefusalKind.UNSUPPORTED_READ_SHAPE,
            step_id=step.step_id,
            detail=(
                f"multi-read {reads} without a declared join/project grammar — declare "
                "join/project (PLAN-0061, the ADR-016 Q4 amendment) or use a single read"
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
    # PLAN-0061 Step 3 (additive): the ontology meta the join/project grammar
    # resolves typed keys against. None = single-read-only (a declaring step
    # refuses typed) — every existing construction is unchanged.
    meta: OntologyMeta | None = None

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
        plan = plan_read(step, ctx.agent, self.object_type_names, meta=self.meta)
        if isinstance(plan, JoinReadPlan):
            return await self._execute_join(plan, ctx)
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

    async def _execute_join(self, plan: JoinReadPlan, ctx: RunContext) -> StepOutcome:
        """Run a compiled join/projection plan — the SD-1 pinned pipeline order.

        Exactly ONE ``fetch_objects`` per declared read (the D-N2 bound extended
        to ``len(reads)`` dispatches, still no retry/repair loop, still no LLM);
        every fetch passes :func:`_json_safe` at the adapter boundary. Pipeline:
        base ``where`` → per-join ``where`` (joined side, pre-join) → joins in
        declaration order (flat merged rows; base value wins a runtime-only key
        collision, counted in provenance) → latest-per-group (SD-5 argmax +
        primary-key tie-break; rows missing the group key or ``order_by`` are
        excluded + counted) → field renames.
        """
        provenance: list[dict[str, Any]] = []
        fetched_by_type: dict[str, list[dict[str, Any]]] = {}
        for object_type in plan.reads:  # exactly len(reads) dispatches
            rows = _json_safe(await self.adapter.fetch_objects(object_type))
            fetched_by_type[object_type] = rows
            provenance.append(
                {
                    "kind": "read_provenance",
                    "summary": f"read '{object_type}': fetched {len(rows)}",
                    "object_type": object_type,
                    "fetched_count": len(rows),
                }
            )

        base_type = plan.reads[0]
        accumulated = [
            row
            for row in fetched_by_type[base_type]
            if not plan.where or matches_where(row, plan.where)
        ]
        provenance.append(
            {
                "kind": "join_pipeline",
                "summary": f"base '{base_type}': {len(accumulated)} after where",
                "object_type": base_type,
                "post_where_count": len(accumulated),
            }
        )

        for join in plan.joins:
            side = [
                row
                for row in fetched_by_type[join.with_type]
                if not join.where or matches_where(row, join.where)
            ]
            accumulated = self._apply_join(plan, join, accumulated, side, provenance)

        if plan.group_by is not None and plan.order_by is not None:
            accumulated = self._latest_per_group(plan, accumulated, provenance)

        if plan.fields:
            accumulated = [self._rename(row, plan.fields) for row in accumulated]

        audit: dict[str, Any] = {
            "actor": ctx.agent.agent_id,
            "actor_kind": "engine",
            "deterministic": True,
            "object_types": list(plan.reads),
            "join_grammar": True,
        }
        return StepOutcome(output=accumulated, reasoning_trace=provenance, audit=audit)

    def _apply_join(
        self,
        plan: JoinReadPlan,
        join: CompiledJoin,
        accumulated: list[dict[str, Any]],
        side: list[dict[str, Any]],
        provenance: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """One join in declaration order — keyed (inner) or fuse (singletons)."""
        if join.fuse:
            if len(accumulated) != 1 or len(side) != 1:
                raise ReadRefusal(
                    ReadRefusalKind.JOIN_SHAPE_VIOLATION,
                    step_id=plan.step_id,
                    object_type=join.with_type,
                    detail=(
                        f"fuse with '{join.with_type}' requires exactly one row on each "
                        f"side post-narrowing (got {len(accumulated)} base, {len(side)} "
                        "joined) — a fuse is a positional singleton fusion, never a guess"
                    ),
                )
            merged, collisions = self._merge(accumulated[0], side[0], plan.fields)
            provenance.append(
                {
                    "kind": "join_pipeline",
                    "summary": f"fuse '{join.with_type}': 1 row fused",
                    "object_type": join.with_type,
                    "matched": 1,
                    "unmatched_base": 0,
                    "runtime_key_collisions": collisions,
                }
            )
            return [merged]
        assert join.left is not None and join.right is not None
        out: list[dict[str, Any]] = []
        unmatched = 0
        collisions_total = 0
        for row in accumulated:
            matches = [s for s in side if s.get(join.right) == row.get(join.left)]
            if not matches:
                unmatched += 1
                continue
            for match in matches:
                merged, collisions = self._merge(row, match, plan.fields)
                collisions_total += collisions
                out.append(merged)
        provenance.append(
            {
                "kind": "join_pipeline",
                "summary": (
                    f"join '{join.with_type}' on {join.left}=={join.right}: "
                    f"{len(out)} merged, {unmatched} base rows unmatched (excluded)"
                ),
                "object_type": join.with_type,
                "matched": len(out),
                "unmatched_base": unmatched,
                "runtime_key_collisions": collisions_total,
            }
        )
        return out

    @staticmethod
    def _merge(
        base_row: dict[str, Any], side_row: dict[str, Any], fields: Mapping[str, str]
    ) -> tuple[dict[str, Any], int]:
        """Flat-merge one pair. A side key colliding with a base key is renamed
        when ``project.fields`` maps it (the SD-1 collision-resolution rename
        applies to the JOINED side at merge, exactly once); an unmapped runtime
        collision keeps the BASE value and is counted (never a silent clobber).
        Equal-named join keys hold equal values by the join predicate, so
        base-wins is value-neutral for them."""
        merged = dict(base_row)
        collisions = 0
        for key, value in side_row.items():
            if key in merged:
                if key in fields:
                    merged[fields[key]] = value
                elif merged[key] != value:
                    collisions += 1
            else:
                merged[key] = value
        return merged, collisions

    def _latest_per_group(
        self,
        plan: JoinReadPlan,
        rows: list[dict[str, Any]],
        provenance: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """SD-5: argmax(``order_by``) per ``group_by``, ties broken by max
        ``tie_break`` (the declared primary_key, lexicographic) — deterministic
        across adapter orderings; rows missing either field are excluded and
        counted, never guessed."""
        assert plan.group_by is not None and plan.order_by is not None
        groups: dict[Any, dict[str, Any]] = {}
        excluded = 0
        for row in rows:
            group_key = row.get(plan.group_by)
            order_value = row.get(plan.order_by)
            if group_key is None or order_value is None:
                excluded += 1
                continue
            current = groups.get(group_key)
            if current is None:
                groups[group_key] = row
                continue
            current_order = current[plan.order_by]
            if order_value > current_order:
                groups[group_key] = row
            elif order_value == current_order and plan.tie_break is not None:
                if str(row.get(plan.tie_break, "")) > str(current.get(plan.tie_break, "")):
                    groups[group_key] = row
        kept = [groups[k] for k in sorted(groups, key=str)]
        provenance.append(
            {
                "kind": "join_pipeline",
                "summary": (
                    f"latest_per '{plan.group_by}' by '{plan.order_by}': {len(kept)} "
                    f"groups kept, {excluded} rows excluded (missing key/order)"
                ),
                "groups_kept": len(kept),
                "rows_excluded_missing_key": excluded,
            }
        )
        return kept

    @staticmethod
    def _rename(row: dict[str, Any], fields: Mapping[str, str]) -> dict[str, Any]:
        """The final select/rename pass.

        A mapping whose TARGET already exists on the row was consumed by the
        merge-side collision resolution (the joined side's occurrence became
        ``target``; the base keeps its original name) — skipping it here is what
        makes each rename apply exactly ONCE and never clobber. Any other
        mapping renames normally (the shape-1 single-read case)."""
        out: dict[str, Any] = {}
        for key, value in row.items():
            target = fields.get(key, key)
            if target != key and target in row:
                out[key] = value  # collision already resolved at merge — keep the base name
            else:
                out[target] = value
        return out
