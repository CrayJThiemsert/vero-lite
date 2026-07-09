"""PLAN-0061 Step 2 (the ADR-016 Q4 amendment): the join/projection grammar's
schema + H-governance + load gate (AC-2, AC-3).

Covers the SD-1 lean two-construct schema's Pydantic invariants, the
``validate_read_bindings`` structural extension (declared-link joins resolve
typed keys / refuse typed; ``on``/``fuse`` overrides WARN-first per OQ-4; the
SD-5 latest-per-group checks; the SD-1 collision rule; OQ-3 rename-target
refusal), the H-governance strip at lift, and the governance-pin participation
(a ``join``/``project`` edit changes the pinned hash → fails CLOSED at resume
via the PLAN-0047/0048 mechanism already proven in
``tests/services/db/test_governance_pin.py``).

Execution stays Phase C — nothing here dispatches an adapter.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.engine.ontology_meta import (
    JoinKeyMeta,
    LinkTypeMeta,
    ObjectTypeMeta,
    OntologyMeta,
    PropertyMeta,
)
from services.engine.procedures.draft import (
    STEP_GOVERNANCE_FIELDS,
    StepDraft,
    lift_to_step,
)
from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
)
from services.engine.procedures.orchestrator import (
    ProcedureError,
    ProcedureWarning,
    validate_read_bindings,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    JoinOn,
    JoinSpec,
    Procedure,
    ProjectSpec,
    Step,
    StepInput,
    StepKind,
)

# --------------------------------------------------------------------------- #
# Fixture ontology meta (pure objects — no YAML, no I/O)
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
        # PurchaseOrder + Quotation deliberately SHARE the declared 'status'
        # property (the collision-rule case) beside the shared join key.
        _obj("PurchaseOrder", "po_id", "po_id", "quote_id", "status"),
        _obj("Quotation", "quote_id", "quote_id", "part_id", "status"),
        _obj("NoPk", None, "x", "occurred_at"),
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
        LinkTypeMeta(
            name="unkeyed_link",
            from_type="PurchaseOrder",
            to_type="Quotation",
            foreign_key=None,  # declared but not parseable — the SD-D refusal case
        ),
        LinkTypeMeta(
            name="event_for_nopk",
            from_type="NoPk",
            to_type="Asset",
            foreign_key=JoinKeyMeta(from_property="x", to_property="asset_id"),
        ),
    ],
)

_NAMES = frozenset(t.name for t in _META.object_types)


def _agent() -> Agent:
    return Agent(
        agent_id="a",
        name="A",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),  # empty = unconstrained reads (OQ-6)
    )


def _proc(input_: StepInput) -> Procedure:
    return Procedure(
        procedure_id="p",
        title="P",
        goal="g",
        run_by="a",
        steps=[Step(step_id="q", name="Q", kind=StepKind.QUERY, input=input_)],
    )


def _gate(input_: StepInput) -> None:
    validate_read_bindings(_proc(input_), _agent(), _NAMES, meta=_META)


# --------------------------------------------------------------------------- #
# SD-1 schema invariants (pure Pydantic — no gate)
# --------------------------------------------------------------------------- #


def test_joinspec_requires_exactly_one_form() -> None:
    with pytest.raises(ValidationError, match="exactly one of link/on/fuse"):
        JoinSpec.model_validate({"with": "Quotation"})
    with pytest.raises(ValidationError, match="exactly one of link/on/fuse"):
        JoinSpec.model_validate({"with": "Quotation", "link": "po_from_quotation", "fuse": True})


def test_joinspec_fuse_false_is_refused() -> None:
    with pytest.raises(ValidationError, match="fuse must be true"):
        JoinSpec.model_validate({"with": "Quotation", "fuse": False})


def test_joinspec_accepts_the_with_alias() -> None:
    spec = JoinSpec.model_validate({"with": "Quotation", "on": {"left": "a", "right": "b"}})
    assert spec.with_read == "Quotation"
    assert spec.on == JoinOn(left="a", right="b")


def test_projectspec_latest_requires_order_by() -> None:
    with pytest.raises(ValidationError, match="requires an explicit project.order_by"):
        ProjectSpec(latest_per="event_emitted_by_asset")
    with pytest.raises(ValidationError, match="only meaningful with"):
        ProjectSpec(order_by="occurred_at")
    with pytest.raises(ValidationError, match="declares nothing"):
        ProjectSpec()


def test_stepinput_join_requires_reads() -> None:
    with pytest.raises(ValidationError, match="require a declared reads"):
        StepInput.model_validate(
            {"join": [{"with": "Quotation", "fuse": True}]}  # no reads
        )
    with pytest.raises(ValidationError, match="require a declared reads"):
        StepInput.model_validate({"project": {"latest_per": "l", "order_by": "occurred_at"}})


def test_stepinput_join_with_must_be_a_declared_non_base_read() -> None:
    with pytest.raises(ValidationError, match="not a declared read"):
        StepInput.model_validate(
            {"reads": ["PurchaseOrder"], "join": [{"with": "Ghost", "fuse": True}]}
        )
    with pytest.raises(ValidationError, match="names the base read"):
        StepInput.model_validate(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "PurchaseOrder", "fuse": True}],
            }
        )
    with pytest.raises(ValidationError, match="duplicate join"):
        StepInput.model_validate(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [
                    {"with": "Quotation", "fuse": True},
                    {"with": "Quotation", "on": {"left": "quote_id", "right": "quote_id"}},
                ],
            }
        )


# --------------------------------------------------------------------------- #
# AC-3: the load gate's structural checks (ontology-dependent)
# --------------------------------------------------------------------------- #


def test_gate_requires_meta_for_a_declaring_step() -> None:
    """Fail-loud, never silently skipped: join/project without meta refuses."""
    input_ = StepInput.model_validate(
        {"reads": ["PurchaseOrder", "Quotation"], "join": [{"with": "Quotation", "fuse": True}]}
    )
    with pytest.raises(ProcedureError, match="no ontology meta"):
        validate_read_bindings(_proc(input_), _agent(), _NAMES)  # meta omitted


def test_declared_link_join_passes_with_rename() -> None:
    """The governed default: keys resolve from the promoted typed foreign_key;
    the shared non-key 'status' property is renamed away (SD-1 collision rule)."""
    _gate(
        StepInput.model_validate(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            }
        )
    )  # no raise, no warn expected


def test_unknown_link_refuses() -> None:
    with pytest.raises(ProcedureError, match="not a declared link_type"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["PurchaseOrder", "Quotation"],
                    "join": [{"with": "Quotation", "link": "ghost_link"}],
                    "project": {"fields": {"status": "quote_status"}},
                }
            )
        )


def test_link_outside_declared_reads_refuses() -> None:
    with pytest.raises(ProcedureError, match="not within the declared"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["OperationalEvent", "Quotation"],
                    # po_from_quotation connects PurchaseOrder->Quotation; PO not read
                    "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                }
            )
        )


def test_link_without_parseable_fk_refuses_typed() -> None:
    with pytest.raises(ProcedureError, match="no parseable typed foreign_key"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["PurchaseOrder", "Quotation"],
                    "join": [{"with": "Quotation", "link": "unkeyed_link"}],
                    "project": {"fields": {"status": "quote_status"}},
                }
            )
        )


def test_on_override_warns_when_unbacked() -> None:
    """OQ-4 resolved: an explicit override with NO declared relationship between
    the pair WARNS (ProcedureWarning) — and still loads."""
    input_ = StepInput.model_validate(
        {
            "reads": ["OperationalEvent", "Quotation"],
            "join": [{"with": "Quotation", "on": {"left": "asset_id", "right": "part_id"}}],
        }
    )
    with pytest.warns(ProcedureWarning, match="not backed by any declared"):
        _gate(input_)


def test_fuse_override_warns_when_unbacked() -> None:
    input_ = StepInput.model_validate(
        {
            "reads": ["OperationalEvent", "Quotation"],
            "join": [{"with": "Quotation", "fuse": True}],
        }
    )
    with pytest.warns(ProcedureWarning, match="not backed by any declared"):
        _gate(input_)


def test_on_override_backed_by_a_declared_pair_does_not_warn(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """An override between a pair the ontology DOES declare stays warn-free —
    the author overrode the keys, not the relationship."""
    _gate(
        StepInput.model_validate(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "on": {"left": "quote_id", "right": "quote_id"}}],
                "project": {"fields": {"status": "quote_status"}},
            }
        )
    )
    assert not [w for w in recwarn if issubclass(w.category, ProcedureWarning)]


def test_declared_collision_refuses_without_rename() -> None:
    """SD-1: PurchaseOrder.status vs Quotation.status collide; the equal-named
    join key (quote_id) is exempt (values equal by the join predicate)."""
    with pytest.raises(ProcedureError, match=r"collision.*status"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["PurchaseOrder", "Quotation"],
                    "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                }
            )
        )


def test_latest_per_group_passes_on_the_declared_link() -> None:
    """Shape 1's gate: group key from the typed FK, explicit order_by, PK present."""
    _gate(
        StepInput.model_validate(
            {
                "reads": ["OperationalEvent"],
                "project": {"latest_per": "event_emitted_by_asset", "order_by": "occurred_at"},
            }
        )
    )


def test_latest_per_wrong_direction_refuses() -> None:
    """The link's from_type must equal the read it groups (SD-5)."""
    with pytest.raises(ProcedureError, match="from_type"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["Asset"],
                    "project": {
                        "latest_per": "event_emitted_by_asset",
                        "order_by": "name",
                    },
                }
            )
        )


def test_latest_per_undeclared_order_by_refuses() -> None:
    with pytest.raises(ProcedureError, match="not a declared property"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["OperationalEvent"],
                    "project": {"latest_per": "event_emitted_by_asset", "order_by": "ghost"},
                }
            )
        )


def test_latest_per_without_primary_key_refuses() -> None:
    """SD-5's deterministic tie-break requires a declared primary_key."""
    with pytest.raises(ProcedureError, match="declares no primary_key"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["NoPk"],
                    "project": {"latest_per": "event_for_nopk", "order_by": "occurred_at"},
                }
            )
        )


def test_rename_target_collision_refuses() -> None:
    """OQ-3 resolved: a rename may not TARGET an existing kept field."""
    with pytest.raises(ProcedureError, match="rename target"):
        _gate(
            StepInput.model_validate(
                {
                    "reads": ["OperationalEvent"],
                    "project": {"fields": {"value": "occurred_at"}},  # occurred_at is kept
                }
            )
        )


def test_reads_only_step_is_byte_compatible_without_meta() -> None:
    """AC-7 guard: the existing 3-arg call shape still works for reads-only steps."""
    validate_read_bindings(
        _proc(StepInput.model_validate({"reads": ["Asset"]})), _agent(), _NAMES
    )  # no meta, no raise


# --------------------------------------------------------------------------- #
# AC-2: H-governance — strip at lift + pin participation
# --------------------------------------------------------------------------- #


def test_join_project_are_h_governed_fields() -> None:
    assert {"join", "project"} <= STEP_GOVERNANCE_FIELDS


def test_lift_strips_join_and_project_from_draft_input() -> None:
    """A generated skeleton may never self-declare its join surface (OQ-A rule)."""
    draft = StepDraft(
        step_id="q",
        name="Q",
        kind=StepKind.QUERY,
        input=StepInput.model_validate(
            {
                "reads": ["PurchaseOrder", "Quotation"],
                "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                "project": {"fields": {"status": "quote_status"}},
            }
        ),
    )
    step = lift_to_step(draft)
    assert step.input is not None
    assert step.input.reads is None
    assert step.input.join is None
    assert step.input.project is None


def _pinned_procedure(join: bool) -> Procedure:
    input_ = StepInput.model_validate(
        {
            "reads": ["PurchaseOrder", "Quotation"],
            "join": [
                {"with": "Quotation", "link": "po_from_quotation"}
                if join
                else {"with": "Quotation", "fuse": True}
            ],
            "project": {"fields": {"status": "quote_status"}},
        }
    )
    return _proc(input_)


def test_snapshot_pins_join_and_project() -> None:
    snapshot = build_governance_snapshot(_pinned_procedure(join=True))
    step_pin = snapshot["steps"][0]
    assert step_pin["join"] == [
        {
            "with": "Quotation",
            "link": "po_from_quotation",
            "on": None,
            "fuse": None,
            "where": None,
        }
    ]
    assert step_pin["project"] == {
        "latest_per": None,
        "order_by": None,
        "fields": {"status": "quote_status"},
    }


def test_join_edit_changes_the_governance_hash() -> None:
    """The fail-closed teeth: a mid-flight join/project edit trips the SAME pin
    mismatch the DB-backed test_governance_pin proves refuses at gate + resume."""
    pinned = compute_governance_hash(build_governance_snapshot(_pinned_procedure(join=True)))
    edited = compute_governance_hash(build_governance_snapshot(_pinned_procedure(join=False)))
    assert pinned != edited


def test_join_absent_step_pins_none() -> None:
    """Backward compat: a reads-only step pins join/project as None — pre-0061
    snapshots of join-absent procedures are unchanged in meaning."""
    snapshot = build_governance_snapshot(_proc(StepInput.model_validate({"reads": ["Asset"]})))
    step_pin = snapshot["steps"][0]
    assert step_pin["join"] is None
    assert step_pin["project"] is None
