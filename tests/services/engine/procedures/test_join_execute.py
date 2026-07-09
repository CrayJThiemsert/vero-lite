"""PLAN-0061 Step 3 (the ADR-016 Q4 amendment): compile + execute the two shapes
(AC-4, AC-5, AC-7).

Drives the extended ``plan_read`` (a declaring step compiles to ``JoinReadPlan``,
re-using the load gate's structural validation — one decision surface) and the
``QueryStepExecutor`` join pipeline: exactly one ``fetch_objects`` per declared
read (a counting fake adapter — the D-N2 bound extended), the SD-1 pinned
pipeline order, the SD-5 argmax + primary-key tie-break + excluded-row
provenance, fuse singleton refusal, runtime-collision counting, and renames.
Deterministic, offline, no LLM (LOCKED-6).
"""

from __future__ import annotations

from typing import Any

import pytest

from services.engine.ontology_meta import (
    JoinKeyMeta,
    LinkTypeMeta,
    ObjectTypeMeta,
    OntologyMeta,
    PropertyMeta,
)
from services.engine.procedures.orchestrator import RunContext, validate_read_bindings
from services.engine.procedures.query_step import (
    JoinReadPlan,
    QueryStepExecutor,
    ReadRefusal,
    ReadRefusalKind,
    plan_read,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
)

# --------------------------------------------------------------------------- #
# Fixture meta (mirrors test_join_grammar's) + a counting fake adapter
# --------------------------------------------------------------------------- #


def _obj(name: str, pk: str | None, *props: str) -> ObjectTypeMeta:
    return ObjectTypeMeta(
        name=name,
        primary_key=pk,
        properties=[PropertyMeta(name=p, type="string") for p in props],
    )


_META = OntologyMeta(
    vertical="fixture",
    object_types=[
        _obj("OperationalEvent", "event_id", "event_id", "asset_id", "occurred_at", "value"),
        _obj("Asset", "asset_id", "asset_id", "name"),
        _obj("PurchaseOrder", "po_id", "po_id", "quote_id", "status", "event_kind"),
        _obj("Quotation", "quote_id", "quote_id", "part_id", "status"),
    ],
    link_types=[
        LinkTypeMeta(
            name="event_emitted_by_asset",
            from_type="OperationalEvent",
            to_type="Asset",
            foreign_key=JoinKeyMeta(from_property="asset_id", to_property="asset_id"),
        ),
        LinkTypeMeta(
            name="po_from_quotation",
            from_type="PurchaseOrder",
            to_type="Quotation",
            foreign_key=JoinKeyMeta(from_property="quote_id", to_property="quote_id"),
        ),
    ],
)

_NAMES = frozenset(t.name for t in _META.object_types)


class _CountingAdapter:
    """A DataAdapter stand-in that counts fetch_objects dispatches per type."""

    vertical_name = "fixture"

    def __init__(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self._data = data
        self.fetch_counts: dict[str, int] = {}

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        self.fetch_counts[object_type] = self.fetch_counts.get(object_type, 0) + 1
        return [dict(row) for row in self._data.get(object_type, [])]


def _adapter(data: dict[str, list[dict[str, Any]]]) -> Any:
    return _CountingAdapter(data)


def _agent() -> Agent:
    return Agent(
        agent_id="a",
        name="A",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),
    )


def _step(input_: dict[str, Any]) -> Step:
    return Step(
        step_id="q",
        name="Q",
        kind=StepKind.QUERY,
        input=StepInput.model_validate(input_),
    )


def _ctx() -> RunContext:
    return RunContext(agent=_agent(), vertical="fixture")


def _executor(adapter: Any) -> QueryStepExecutor:
    return QueryStepExecutor(
        adapter=adapter,  # duck-typed; the executor only calls fetch_objects
        object_type_names=_NAMES,
        meta=_META,
    )


# --------------------------------------------------------------------------- #
# Compile (plan_read → JoinReadPlan)
# --------------------------------------------------------------------------- #


def test_declaring_step_compiles_to_a_join_plan_with_resolved_keys() -> None:
    plan = plan_read(
        _step(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            }
        ),
        _agent(),
        _NAMES,
        meta=_META,
    )
    assert isinstance(plan, JoinReadPlan)
    assert plan.reads == ("PurchaseOrder", "Quotation")
    join = plan.joins[0]
    # the declared link's typed FK resolved: PurchaseOrder.quote_id == Quotation.quote_id
    assert (join.left, join.right, join.fuse) == ("quote_id", "quote_id", False)
    assert plan.fields == {"status": "quote_status"}


def test_latest_per_compiles_group_and_tie_break() -> None:
    plan = plan_read(
        _step(
            {
                "reads": ["OperationalEvent"],
                "project": {"latest_per": "event_emitted_by_asset", "order_by": "occurred_at"},
            }
        ),
        _agent(),
        _NAMES,
        meta=_META,
    )
    assert isinstance(plan, JoinReadPlan)
    assert plan.group_by == "asset_id"  # the link's typed foreign_key.from_property
    assert plan.order_by == "occurred_at"
    assert plan.tie_break == "event_id"  # the base type's declared primary_key


def test_declaring_step_without_meta_refuses_typed() -> None:
    with pytest.raises(ReadRefusal) as exc:
        plan_read(
            _step(
                {
                    "reads": ["PurchaseOrder", "Quotation"],
                    "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                    "project": {"fields": {"status": "quote_status"}},
                }
            ),
            _agent(),
            _NAMES,
        )
    assert exc.value.refusal_kind is ReadRefusalKind.JOIN_SHAPE_VIOLATION


def test_structural_violation_maps_to_the_typed_refusal() -> None:
    """AC-3 one-decision-surface: the same violation the load gate refuses
    (unknown link) compiles to a JOIN_SHAPE_VIOLATION refusal here."""
    step = _step(
        {
            "reads": ["PurchaseOrder", "Quotation"],
            "join": [{"with": "Quotation", "link": "ghost_link"}],
        }
    )
    with pytest.raises(ReadRefusal) as exc:
        plan_read(step, _agent(), _NAMES, meta=_META)
    assert exc.value.refusal_kind is ReadRefusalKind.JOIN_SHAPE_VIOLATION
    assert "not a declared link_type" in exc.value.detail


def test_multi_read_without_grammar_still_refuses() -> None:
    """AC-7: the SD-1 refusal narrowed, not vanished."""
    with pytest.raises(ReadRefusal) as exc:
        plan_read(_step({"reads": ["PurchaseOrder", "Quotation"]}), _agent(), _NAMES, meta=_META)
    assert exc.value.refusal_kind is ReadRefusalKind.UNSUPPORTED_READ_SHAPE


def test_gate_and_compile_agree_on_the_same_matrix() -> None:
    """AC-3 extended: the same declaring inputs accept/refuse identically at the
    load gate and the compile seam (one shared validation surface)."""
    cases: list[tuple[dict[str, Any], bool]] = [
        (
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            },
            True,
        ),
        (
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "ghost_link"}],
            },
            False,
        ),
        (
            {
                "reads": ["OperationalEvent"],
                "project": {"latest_per": "event_emitted_by_asset", "order_by": "ghost"},
            },
            False,
        ),
    ]
    for input_, ok in cases:
        step = _step(input_)
        procedure = Procedure(procedure_id="p", title="P", goal="g", run_by="a", steps=[step])
        gate_ok = True
        try:
            validate_read_bindings(procedure, _agent(), _NAMES, meta=_META)
        except Exception:
            gate_ok = False
        compile_ok = True
        try:
            plan_read(step, _agent(), _NAMES, meta=_META)
        except ReadRefusal:
            compile_ok = False
        assert gate_ok == compile_ok == ok, f"gate/compile disagree on {input_}"


# --------------------------------------------------------------------------- #
# Execute — shape 2: equi-join enrichment (AC-5)
# --------------------------------------------------------------------------- #

_PO_ROWS = [
    {"po_id": "po-1", "quote_id": "qt-1", "status": "draft", "event_kind": "failure"},
    {"po_id": "po-2", "quote_id": "qt-2", "status": "open", "event_kind": "restock"},
    {"po_id": "po-3", "quote_id": "qt-9", "status": "open", "event_kind": "restock"},  # no match
]
_QUOTE_ROWS = [
    {"quote_id": "qt-1", "part_id": "part-a", "status": "quoted"},
    {"quote_id": "qt-2", "part_id": "part-b", "status": "expired"},
]


async def test_keyed_join_merges_flat_and_dispatches_once_per_read() -> None:
    adapter = _adapter({"PurchaseOrder": _PO_ROWS, "Quotation": _QUOTE_ROWS})
    outcome = await _executor(adapter).execute(
        _step(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            }
        ),
        [],
        _ctx(),
    )
    # D-N2 extended: exactly one dispatch per declared read
    assert adapter.fetch_counts == {"PurchaseOrder": 1, "Quotation": 1}
    # po-3 has no matching quote -> excluded (inner join); 2 merged flat rows
    assert [row["po_id"] for row in outcome.output] == ["po-1", "po-2"]
    merged = outcome.output[0]
    assert merged["part_id"] == "part-a"  # enriched from the quote
    assert merged["status"] == "draft"  # base keeps its name
    assert merged["quote_status"] == "quoted"  # the side's collision renamed
    join_trace = next(t for t in outcome.reasoning_trace if t["kind"] == "join_pipeline")
    assert outcome.audit is not None and outcome.audit["join_grammar"] is True
    assert join_trace is not None


async def test_unmatched_base_rows_are_counted_in_provenance() -> None:
    adapter = _adapter({"PurchaseOrder": _PO_ROWS, "Quotation": _QUOTE_ROWS})
    outcome = await _executor(adapter).execute(
        _step(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            }
        ),
        [],
        _ctx(),
    )
    join_trace = next(
        t for t in outcome.reasoning_trace if t["kind"] == "join_pipeline" and "unmatched_base" in t
    )
    assert join_trace["unmatched_base"] == 1  # po-3


async def test_base_where_and_join_where_narrow_before_joining() -> None:
    adapter = _adapter({"PurchaseOrder": _PO_ROWS, "Quotation": _QUOTE_ROWS})
    outcome = await _executor(adapter).execute(
        _step(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "where": {"event_kind": "failure"},  # narrows the BASE
                "join": [
                    {
                        "with": "Quotation",
                        "link": "po_from_quotation",
                        "where": {"status": "quoted"},  # narrows the JOINED side
                    }
                ],
                "project": {"fields": {"status": "quote_status"}},
            }
        ),
        [],
        _ctx(),
    )
    assert [row["po_id"] for row in outcome.output] == ["po-1"]


async def test_fuse_merges_singletons_and_refuses_non_singleton() -> None:
    data = {
        "OperationalEvent": [
            {"event_id": "e1", "asset_id": "a1", "occurred_at": "t1", "value": "9"},
            {"event_id": "e2", "asset_id": "a2", "occurred_at": "t2", "value": "3"},
        ],
        "PurchaseOrder": [_PO_ROWS[0]],
    }
    step = _step(
        {
            "reads": ["OperationalEvent", "PurchaseOrder"],
            "where": {"event_id": "e1"},  # narrows the base to a singleton
            "join": [{"with": "PurchaseOrder", "fuse": True}],
        }
    )
    adapter = _adapter(data)
    with pytest.warns(UserWarning):  # the unbacked-fuse load warning re-fires at compile
        outcome = await _executor(adapter).execute(step, [], _ctx())
    fused = outcome.output[0]
    assert fused["event_id"] == "e1" and fused["po_id"] == "po-1"

    # non-singleton base (no where) -> typed refusal, never a guess
    step_bad = _step(
        {
            "reads": ["OperationalEvent", "PurchaseOrder"],
            "join": [{"with": "PurchaseOrder", "fuse": True}],
        }
    )
    with pytest.warns(UserWarning), pytest.raises(ReadRefusal) as exc:
        await _executor(_adapter(data)).execute(step_bad, [], _ctx())
    assert exc.value.refusal_kind is ReadRefusalKind.JOIN_SHAPE_VIOLATION


async def test_runtime_only_collision_keeps_base_value_and_counts() -> None:
    """An adapter-extra key (undeclared) colliding at merge keeps the BASE value
    and is counted — never a silent clobber."""
    data = {
        "PurchaseOrder": [
            {"po_id": "po-1", "quote_id": "qt-1", "status": "draft", "extra": "base-wins"}
        ],
        "Quotation": [
            {"quote_id": "qt-1", "part_id": "part-a", "status": "quoted", "extra": "side-loses"}
        ],
    }
    adapter = _adapter(data)
    outcome = await _executor(adapter).execute(
        _step(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            }
        ),
        [],
        _ctx(),
    )
    row = outcome.output[0]
    assert row["extra"] == "base-wins"
    join_trace = next(
        t
        for t in outcome.reasoning_trace
        if t["kind"] == "join_pipeline" and "runtime_key_collisions" in t
    )
    assert join_trace["runtime_key_collisions"] == 1


# --------------------------------------------------------------------------- #
# Execute — shape 1: latest-per-group projection (AC-4)
# --------------------------------------------------------------------------- #

_EVENT_ROWS = [
    {"event_id": "e1", "asset_id": "a1", "occurred_at": "2026-07-01T06:00:00Z", "value": "1"},
    {"event_id": "e2", "asset_id": "a1", "occurred_at": "2026-07-02T06:00:00Z", "value": "2"},
    {"event_id": "e3", "asset_id": "a2", "occurred_at": "2026-07-01T09:00:00Z", "value": "3"},
    # tie on occurred_at within a2 — the higher event_id (SD-5 PK tie-break) wins
    {"event_id": "e4", "asset_id": "a2", "occurred_at": "2026-07-01T09:00:00Z", "value": "4"},
    # missing group key / order value — excluded + counted, never guessed
    {"event_id": "e5", "occurred_at": "2026-07-03T06:00:00Z", "value": "5"},
    {"event_id": "e6", "asset_id": "a3", "value": "6"},
]


async def test_latest_per_group_keeps_argmax_with_pk_tie_break() -> None:
    adapter = _adapter({"OperationalEvent": _EVENT_ROWS})
    outcome = await _executor(adapter).execute(
        _step(
            {
                "reads": ["OperationalEvent"],
                "project": {"latest_per": "event_emitted_by_asset", "order_by": "occurred_at"},
            }
        ),
        [],
        _ctx(),
    )
    assert adapter.fetch_counts == {"OperationalEvent": 1}
    by_asset = {row["asset_id"]: row for row in outcome.output}
    assert by_asset["a1"]["event_id"] == "e2"  # the later reading
    assert by_asset["a2"]["event_id"] == "e4"  # tie -> max primary_key
    assert set(by_asset) == {"a1", "a2"}  # a3 excluded (no order value)
    latest_trace = next(t for t in outcome.reasoning_trace if "rows_excluded_missing_key" in t)
    assert latest_trace["rows_excluded_missing_key"] == 2  # e5 + e6


async def test_latest_per_group_rename_applies() -> None:
    adapter = _adapter({"OperationalEvent": _EVENT_ROWS[:3]})
    outcome = await _executor(adapter).execute(
        _step(
            {
                "reads": ["OperationalEvent"],
                "project": {
                    "latest_per": "event_emitted_by_asset",
                    "order_by": "occurred_at",
                    "fields": {"value": "latest_value"},
                },
            }
        ),
        [],
        _ctx(),
    )
    for row in outcome.output:
        assert "latest_value" in row and "value" not in row


async def test_deterministic_across_adapter_orderings() -> None:
    """SD-5: the same rows in reverse adapter order produce the same output."""
    step_input = {
        "reads": ["OperationalEvent"],
        "project": {"latest_per": "event_emitted_by_asset", "order_by": "occurred_at"},
    }
    fwd = await _executor(_adapter({"OperationalEvent": _EVENT_ROWS})).execute(
        _step(step_input), [], _ctx()
    )
    rev = await _executor(_adapter({"OperationalEvent": list(reversed(_EVENT_ROWS))})).execute(
        _step(step_input), [], _ctx()
    )
    assert fwd.output == rev.output


# --------------------------------------------------------------------------- #
# AC-7: the single-read path is byte-identical (no meta, no grammar)
# --------------------------------------------------------------------------- #


async def test_single_read_without_grammar_is_unchanged() -> None:
    adapter = _adapter({"Asset": [{"asset_id": "a1", "name": "N1"}]})
    executor = QueryStepExecutor(adapter=adapter, object_type_names=_NAMES)  # no meta
    outcome = await executor.execute(_step({"reads": ["Asset"]}), [], _ctx())
    assert outcome.output == [{"asset_id": "a1", "name": "N1"}]
    assert outcome.reasoning_trace[0]["kind"] == "read_provenance"
    assert outcome.audit is not None and "join_grammar" not in outcome.audit
