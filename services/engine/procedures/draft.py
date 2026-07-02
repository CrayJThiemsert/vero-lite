"""Restricted draft types + the lift to the runtime spec (ADR-0024 D3; PLAN-0040
Phase A, Step A2).

**"governed ≠ generated" made MECHANICAL** (D3 mechanism 1): the generator's
output is a RESTRICTED draft type with **no governance fields**, so a leak is a
TYPE ERROR at the boundary — not a model behaviour we hope for. A draft carries
only what the generator may emit (G, D3): prose, the closed-enum classifications
(``kind`` / ``gate_kind`` / ``band_source``), and workflow structure (step order,
the input fan-out). It carries **zero governance values** — no ``threshold`` /
``direction`` / ``watch_margin`` / ``handler`` / ``tiers`` / ``autonomy`` /
``env_var``; on the agent side no ``llm_model`` / ``autonomy_ceiling`` /
``allowed``; on the procedure no ``run_by``.

:func:`lift_to_step` / :func:`lift_to_procedure` deterministically lift a draft to
the runtime ``spec`` model, INJECTING every governance field as an **absent stub**
(ADR-0024 OQ-C C1: the field is ``None`` / left to its safe default — never an
in-field sentinel). :func:`derive_governance_todo` re-derives, from
``(gate_kind, kind)``, exactly which gates a human still owes — the worklist the
review gate shows and ``validate_governance_complete`` (orchestrator, Step A4)
re-checks (it never trusts a stored worklist; it recomputes).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    DecisionCondition,
    GateKind,
    Procedure,
    Step,
    StepFacet,
    StepInput,
    StepKind,
    Trigger,
)

# --- the H partition: the governance fields a draft must NEVER carry (D3) --------

STEP_GOVERNANCE_FIELDS = frozenset(
    {
        "autonomy",
        "handler",
        "threshold",
        "direction",
        "watch_margin",
        "tiers",
        "env_var",
        "governance_content",
        "reads",
    }
)
"""``Step``-level human-author (H) fields. ``env_var`` lives on the nested
``DecisionCondition`` (not a top-level ``Step`` field), but it is named here so the
disjointness test (AC-A4) also fails CI if someone adds it to a draft type.
``governance_content`` is the AT-2 typed managerial content (ADR-0025 D2/D4) — the
highest-consequence governance value in the system; never model-emitted.
``reads`` (ADR-016 Q3 OQ-A) lives on the nested ``StepInput`` — which ``StepDraft``
REUSES for the G fan-out structure — so unlike ``env_var`` it CAN physically ride a
draft; :func:`lift_to_step` therefore strips it to an ABSENT stub (a generated
skeleton may never self-declare its own read blast-radius)."""

PROCEDURE_GOVERNANCE_FIELDS = frozenset({"run_by", "separation_of_duties"})
"""``Procedure``-level H fields: ``run_by`` binds the Agent (a blast-radius choice);
``separation_of_duties`` is the AT-2 SoD constraint set (ADR-0025 D2/D4) — human-authored,
never generated."""

AGENT_GOVERNANCE_FIELDS = frozenset({"llm_model", "autonomy_ceiling", "allowed"})
"""``Agent``-level H fields: the residency binding + the blast-radius bounds."""

PRINCIPAL_GOVERNANCE_FIELDS = frozenset({"principals", "principal_aliases", "required_roles"})
"""ADR-0026 D1/D4 principal-identity H fields: ``principals`` / ``principal_aliases`` (the
``VerticalProcedures`` human-identity records the SoD run-check resolves against) and
``required_roles`` (the ``SoDConstraint`` step->required-role map). Human-authored — a
principal, an alias group, or a role binding is never model-emitted (ADR-0024 D3). There is
no ``VerticalProceduresDraft`` (principals are not a generated surface), so these are guarded
by the recursive TYPE-disjointness test (``Person`` / ``PrincipalAlias`` unreachable from any
draft type) rather than a per-draft field check."""

GOVERNANCE_FIELDS = (
    STEP_GOVERNANCE_FIELDS
    | PROCEDURE_GOVERNANCE_FIELDS
    | AGENT_GOVERNANCE_FIELDS
    | PRINCIPAL_GOVERNANCE_FIELDS
)
"""The full never-generate (H) field set across Step / Procedure / Agent / principal (D3)."""


# --- the restricted draft types (G fields only) ---------------------------------


class StepDraft(BaseModel):
    """A generated step DRAFT — only the fields the generator may emit (G, D3).

    No governance value can be carried: the model has no ``handler`` / ``threshold``
    / ``direction`` / ``watch_margin`` / ``tiers`` / ``autonomy`` / ``env_var``
    field at all, so a leak is a *type error*. ``input`` reuses the runtime
    :class:`StepInput` (the fan-out is structure, G). The facet's typed
    classification (``gate_kind`` / ``band_source``) and advisory prose are carried
    flat and assembled into a ``StepFacet`` by :func:`lift_to_step`."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    name: str = Field(description="prose label (G)")
    description: str = Field(
        default="", description="prose (G); un-trusted for values (prose-lint)"
    )
    kind: StepKind
    output: str | None = Field(default=None, description="produced artifact name (G prose)")
    input: StepInput | None = Field(
        default=None,
        description="input fan-out structure (G); a carried `reads` is an H value "
        "(ADR-016 Q3 OQ-A) and is stripped to an absent stub at lift",
    )
    gate_kind: GateKind = Field(
        default=GateKind.NONE, description="closed-enum decision-condition classification (G, D4)"
    )
    band_source: BandSource | None = Field(
        default=None, description="band mechanism class for a band gate_kind (G, lean)"
    )
    llm_assist: str | None = Field(default=None, description="advisory role prose (G)")
    input_note: str | None = Field(default=None, description="non-authoritative facet note (G)")
    output_note: str | None = Field(default=None, description="non-authoritative facet note (G)")
    governance_note: str | None = Field(
        default=None, description="non-authoritative facet note (G)"
    )


class AgentDraft(BaseModel):
    """A generated agent DRAFT — name only (G). No ``llm_model`` / ``autonomy_ceiling``
    / ``allowed`` (the H blast-radius bounds the human authors)."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(description="slug (D)")
    name: str = Field(description="prose label (G)")


class ProcedureDraft(BaseModel):
    """A generated procedure DRAFT — title / goal / steps (G) only. No ``run_by``
    (H: binds the agent) and no governance posture."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="slug (D)")
    title: str = Field(description="prose (G)")
    goal: str = Field(
        default="", description="runtime LLM directive (G prose; un-trusted for values)"
    )
    steps: list[StepDraft] = Field(min_length=1)
    terminal: str | None = Field(default=None, description="terminal step_id (D-derived)")


class GovernanceStub(BaseModel):
    """One unfilled governance obligation, for the review gate's "YOU must author"
    zone (ADR-0024 OQ-C C1 / D8). Lives ONLY in the draft layer — never on a typed
    ``Step`` (an in-field sentinel is incompatible with the typed schema, finding #7)."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(description="the governance field the human must author, e.g. 'threshold'")
    reason: str = Field(description="why it is the human's to own (governed ≠ generated)")
    archetype_expectation: str = Field(description="the oracle's expectation for this gate (D4/D8)")


# --- the deterministic lift (inject governance as absent stubs; OQ-C C1) ---------


def _strip_read_binding(input_: StepInput | None) -> StepInput | None:
    """Inject ``reads`` as an ABSENT stub (H, ADR-016 Q3 OQ-A; OQ-C C1 pattern).

    ``StepDraft`` reuses the runtime :class:`StepInput` for the G fan-out
    structure (``from``/``where``), so — unlike ``env_var``, which a draft cannot
    physically carry — a generated draft CAN arrive with ``reads`` set. The lift
    drops it, exactly as it injects ``handler``/``threshold``/``env_var`` absent:
    a generated skeleton may never self-declare its own read blast-radius; the
    human authors ``reads`` (+ the agent's ``allowed.object_types``) later.
    """
    if input_ is None or input_.reads is None:
        return input_
    return input_.model_copy(update={"reads": None})


def lift_to_step(draft: StepDraft, *, autonomy: Autonomy | None = None) -> Step:
    """Lift a :class:`StepDraft` to a runtime :class:`Step`, injecting every
    governance value as an ABSENT stub (OQ-C C1: ``None`` / safe default, never a
    sentinel). The result round-trips ``load_procedures`` (D6 draft-loadable) but
    carries unfilled gates that ``validate_governance_complete`` refuses to run.

    ``autonomy`` is the archetype-supplied posture for an ``action`` slot (the
    template's, never the LLM's — the draft cannot carry it). ``None`` lets the
    ``Step`` default to ``gated`` (safe-by-default)."""
    facet = StepFacet(
        decision_condition=DecisionCondition(
            gate_kind=draft.gate_kind,
            band_source=draft.band_source,
            # env_var is an H stub — injected absent
        ),
        llm_assist=draft.llm_assist,
        input=draft.input_note,
        output=draft.output_note,
        governance=draft.governance_note,
    )
    return Step(
        step_id=draft.step_id,
        name=draft.name,
        description=draft.description,
        kind=draft.kind,
        output=draft.output,
        input=_strip_read_binding(draft.input),
        autonomy=autonomy if draft.kind is StepKind.ACTION else None,
        # handler / threshold / direction / watch_margin / tiers / input.reads: ABSENT stubs (H)
        facet=facet,
    )


def lift_to_procedure(
    draft: ProcedureDraft,
    *,
    run_by: str,
    autonomies: dict[str, Autonomy] | None = None,
) -> Procedure:
    """Lift a :class:`ProcedureDraft` to a runtime :class:`Procedure`. ``run_by`` is
    a placeholder the human binds (H stub); per-step ``autonomies`` carry the
    archetype postures. The result is a load_procedures-valid SKELETON that is not
    run-loadable until the stubs are authored (D6 two-state)."""
    postures = autonomies or {}
    steps = [lift_to_step(s, autonomy=postures.get(s.step_id)) for s in draft.steps]
    return Procedure(
        procedure_id=draft.procedure_id,
        title=draft.title,
        goal=draft.goal,
        run_by=run_by,
        trigger=Trigger.MANUAL,
        steps=steps,
        terminal=draft.terminal,
    )


# --- the obligation worklist (re-derived; never trusted as stored state) ---------


def _step_gate_kind(step: Step) -> GateKind:
    if step.facet is not None and step.facet.decision_condition is not None:
        return step.facet.decision_condition.gate_kind
    return GateKind.NONE


_AT2_GATE_KINDS = frozenset({GateKind.SCORED_RULE, GateKind.RULE_GATE, GateKind.DOA_TIER})
"""The AT-2 (managerial) gate kinds whose step owes typed ``governance_content`` (ADR-0025
D5): a ``scored_rule`` action owes a ``ScoredRule``, a ``rule_gate`` evaluate owes a
``ComplianceGate``, a ``doa_tier`` action owes a ``DoaLadder``. (Distinct from the
generator's classify-time AT-2 abstain guard in ``generator/pipeline.py``.)"""


def derive_governance_todo(step: Step) -> list[str]:
    """The governance gates a human still owes on ``step``, derived deterministically
    from ``(gate_kind, kind)`` (ADR-0024 OQ-C / AC-A7; extended for AT-2 by ADR-0025 D5).
    A ``judge`` (evaluate) owes its band value (threshold+direction for an in-file band;
    env_var for an env band); an ``action`` owes a ``handler`` and an autonomy confirm; and
    a step on an **AT-2 gate kind** (``scored_rule`` / ``rule_gate`` / ``doa_tier``) also
    owes its typed ``governance_content`` (the matching DoaLadder / ScoredRule /
    ComplianceGate — D5). The list is the review gate's "YOU must author" worklist;
    ``validate_governance_complete`` re-derives it (it never trusts a stored copy)."""
    gate_kind = _step_gate_kind(step)
    owes_at2 = ["governance_content"] if gate_kind in _AT2_GATE_KINDS else []
    if step.kind is StepKind.EVALUATE:
        if gate_kind is GateKind.IN_FILE_BAND:
            return ["threshold", "direction"]  # watch_margin stays optional
        if gate_kind is GateKind.ENV_BAND:
            return ["env_var"]
        return owes_at2  # rule_gate owes its ComplianceGate; none owes nothing
    if step.kind is StepKind.ACTION:
        return ["handler", "autonomy", *owes_at2]  # scored_rule/doa_tier add the content
    return owes_at2


def _is_filled(step: Step, field: str) -> bool:
    """Whether a derived obligation ``field`` is authored on ``step`` (presence test).
    ``autonomy`` is always present (defaulted ``gated`` = safe), so it never blocks a
    run — it stays in the worklist as a human CONFIRM, not a hard gate.

    ``governance_content`` (AT-2, ADR-0025 D5) is filled iff it is present AND its
    discriminator ``kind`` matches the step's ``gate_kind`` — the D4 correspondence check,
    so a ``DoaLadder`` mistakenly placed on a ``scored_rule`` step counts as unfilled
    (wrong content), not filled. (Semantic validity — non-empty tiers, monotone floors,
    etc. — is already guaranteed by the model validators at construction, so a *present,
    matching* content is a *valid* content.)"""
    if field == "env_var":
        dc = step.facet.decision_condition if step.facet is not None else None
        return dc is not None and dc.env_var is not None
    if field == "governance_content":
        content = step.governance_content
        return content is not None and content.kind == _step_gate_kind(step).value
    return getattr(step, field, None) is not None


def unfilled_governance(step: Step) -> list[str]:
    """The subset of :func:`derive_governance_todo` not yet authored on ``step`` —
    what ``validate_governance_complete`` raises on. Empty ⇒ the step's gates are
    authored (run-loadable)."""
    return [field for field in derive_governance_todo(step) if not _is_filled(step, field)]


# --- procedure-level governance obligations (AT-2 SoD; ADR-0025 D5) --------------


def derive_procedure_governance_todo(procedure: Procedure) -> list[str]:
    """The procedure-level governance obligations, derived from the procedure's steps
    (ADR-0025 D5). A procedure containing a ``doa_tier`` action owes >=1
    ``separation_of_duties`` constraint — SoD spans steps, so it is procedure-scoped, not
    step-scoped. The author-time gate enforces this STRUCTURAL form (a constraint exists,
    naming >=2 distinct real steps — see the ``Procedure`` validators); the
    resolved-PRINCIPAL distinctness (fail-closed on alias-collapse) is the deferred A2 run
    check (ADR-0025 OQ-A=A1; AC-13-ALT)."""
    if any(_step_gate_kind(s) is GateKind.DOA_TIER for s in procedure.steps):
        return ["separation_of_duties"]
    return []


def unfilled_procedure_governance(procedure: Procedure) -> list[str]:
    """The procedure-level obligations not yet authored (ADR-0025 D5). Empty ⇒ the
    procedure's SoD obligation (if any) is satisfied. Re-derived; never a stored copy."""
    out: list[str] = []
    for field in derive_procedure_governance_todo(procedure):
        if field == "separation_of_duties" and not procedure.separation_of_duties:
            out.append(field)
    return out
