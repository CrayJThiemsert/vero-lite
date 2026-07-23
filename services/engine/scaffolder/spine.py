"""The AT-2 spine template + the procedures emitter (Step 4, oracle AC-5).

**SD-5 (a), Cray-ratified 2026-07-23 — the binding constraint on this module.**
:data:`AT2_SPINE` is owned *here*, in the scaffolder, and **never enters the
shared** ``services.engine.procedures.archetypes.template.REGISTRY``. That is
not a style preference; it is what keeps the API classify path byte-unchanged:
``generator/pipeline.py`` builds its classify catalog from ``REGISTRY.values()``
and routes by label through the same dict, so registering AT-2 centrally would
silently turn an "AT-2" label from an abstain into a hit. Because nothing is
registered, ``test_archetype_templates.py``'s ``set(REGISTRY) == set(AT1_FAMILY)``
never fires and its family-invariant framing stays accurate.

**The tripwire is armed.** If a valid AT-2 spine ever turns out to be impossible
without central registration, STOP and re-open SD-5 — do not register, and do
not edit that test. A diff to it means the tripwire is firing.

The ``ArchetypeTemplate`` *type* is reused as-is; only the registration is
avoided. That is the whole of SD-5 (a): it constrains where the template lives,
not what it is built from.

**What the emitter guarantees.** Structure comes from the template; every
governance VALUE comes from confirmed intake. An unanswered value is emitted as
an **absent** field — the shipped stub form — so the procedure stays
draft-loadable while ``derive_governance_todo`` still lists it as owed and the
runnable gate refuses it (ADR-0024 D6). Free text is run through the shipped
``prose_lint`` **before** writing, so a lint violation is a refusal to emit
rather than a parse round-trip after the fact.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from services.engine.procedures.archetypes.template import (
    ArchetypeTemplate,
    SlotInput,
    StepSlot,
)
from services.engine.procedures.prose_lint import governance_prose_lint
from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    ComplianceGate,
    ComplianceRule,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    GateKind,
    RelaxableConstraint,
    StepKind,
)
from services.engine.scaffolder.intake import IntakeRecord


def _at2_spine_slots() -> list[StepSlot]:
    """Row 11's fixed spine: intake -> judge -> reshape -> rule_gate -> approve -> fulfill.

    A fresh list per call, mirroring the AT-1 family's builders, so a caller that
    mutates the slots cannot corrupt the module-level template.
    """
    return [
        StepSlot(
            step_id="intake",
            name="Read the latest signal per asset",
            kind=StepKind.QUERY,
            gate_kind=GateKind.NONE,
        ),
        StepSlot(
            step_id="judge",
            name="Judge against the asset's own band",
            kind=StepKind.EVALUATE,
            gate_kind=GateKind.IN_FILE_BAND,
            input=SlotInput(from_step="intake"),
        ),
        StepSlot(
            step_id="reshape",
            name="Reshape the breach into a governed spend",
            kind=StepKind.TRANSFORM,
            gate_kind=GateKind.NONE,
            input=SlotInput(from_step="judge", where={"verdict": "breach"}),
        ),
        StepSlot(
            step_id="rule_gate",
            name="Check the compliance gate",
            kind=StepKind.EVALUATE,
            gate_kind=GateKind.RULE_GATE,
            input=SlotInput(from_step="reshape"),
        ),
        StepSlot(
            step_id="approve",
            name="Tiered authority approval (human gate)",
            kind=StepKind.ACTION,
            gate_kind=GateKind.DOA_TIER,
            autonomy=Autonomy.GATED,
            input=SlotInput(from_step="rule_gate", where={"compliant": "true"}),
        ),
        StepSlot(
            step_id="fulfill",
            name="Execute the approved decision",
            kind=StepKind.ACTION,
            gate_kind=GateKind.NONE,
            autonomy=Autonomy.GATED,
            input=SlotInput(from_step="approve"),
        ),
    ]


AT2_SPINE = ArchetypeTemplate(
    archetype_id="AT-2",
    title="governed money spine",
    description=(
        "read a signal per asset, judge it against that asset's own band, reshape the breach "
        "into a governed spend, check a compliance gate, then route it to tiered human "
        "authority with separation of duties"
    ),
    slots=_at2_spine_slots(),
    terminal_slot="fulfill",
)
"""The AT-2 spine — **scaffolder-owned, deliberately NOT in the shared REGISTRY** (SD-5 (a))."""


def gate_signature(template: ArchetypeTemplate = AT2_SPINE) -> tuple[tuple[str, str], ...]:
    """The template's ``(step_id, gate_kind)`` signature — the D4 agreement oracle."""
    return tuple((slot.step_id, slot.gate_kind.value) for slot in template.slots)


class SpineAgreementError(RuntimeError):
    """Raised when an emitted spine contradicts the template's gate signature (D4).

    A contradicting ``gate_kind`` is a HARD failure, never a warning: the gate
    kind is what decides which governance content a step owes, so a spine that
    disagrees with its own archetype owes the wrong things.
    """


class ProseLintError(RuntimeError):
    """Raised when emitted free text would smuggle a governance value into prose.

    ADR-0025 D4: an amount, weight or role token in a note is not documentation,
    it is an ungoverned second copy of a governed value.
    """

    def __init__(self, findings: list[str]) -> None:
        self.findings = findings
        super().__init__("prose lint refused the emission: " + "; ".join(findings))


def _lint(text: str, *, roles: frozenset[str]) -> list[str]:
    """The SCOPED AT-2 lint — the same one the loader runs (ADR-0025 D4).

    Deliberately not the broad :func:`prose_lint`: that variant also flags
    decision verbs and handler names, and it exists for text the MODEL wrote
    (``generator/pipeline.py`` lints drafts with it). This emitter's prose is
    human-authored template text, where "execute the approved decision" is
    legitimate — the shipped donor says exactly that. Using the broad lint here
    would refuse to emit language the repo already ships.
    """
    return [f"{v.kind}: {v.match} — {v.message}" for v in governance_prose_lint(text, roles=roles)]


def emit_procedures(record: IntakeRecord, ontology_doc: dict[str, Any]) -> dict[str, Any]:
    """Emit the vertical's ``procedures.yaml`` document.

    Structure from :data:`AT2_SPINE`; values from confirmed intake only. Anything
    unanswered is left ABSENT — the shipped unfilled-stub form, which keeps the
    document draft-loadable while the review gate still lists the obligation.
    """
    ns = record.namespace
    asset = str(record.confirmed_value("ontology.asset_noun") or "Asset")
    band_property = str(record.confirmed_value("ontology.band_property") or "")

    criteria = _criteria(record)
    steps = [
        _emit_step(slot, record, criteria, band_property, ontology_doc) for slot in AT2_SPINE.slots
    ]

    procedure: dict[str, Any] = {
        "title": f"Governed {asset} Approval",
        "goal": (
            f"Read the latest signal per {asset}, judge it against that {asset}'s own band, "
            "reshape the breach into a governed spend, check the compliance gate, then route "
            "the compliant spend to the human authority its size demands. The LLM drafts; it "
            "decides nothing."
        ),
        "run_by": f"{ns}_agent",
        "trigger": "manual",
        "steps": steps,
        "terminal": AT2_SPINE.terminal_slot,
    }

    requester = record.confirmed_value("governance.approve.sod.requester")
    if requester:
        # ADR-0025 D5: a doa_tier gate REQUIRES separation of duties. Author-time
        # form is the STRUCTURAL distinct-steps pair; the resolved-principal check
        # is the live run check (ADR-0026 D4).
        procedure["separation_of_duties"] = [
            {
                "distinct_steps": ["intake", "approve"],
                "required_roles": {"intake": "requester", "approve": "approver"},
            }
        ]

    doc: dict[str, Any] = {
        "version": 0,
        "namespace": ns,
        # The agent `run_by` points at. Emitted because the loader cross-checks
        # the reference — a procedures document whose `run_by` names no declared
        # agent does not load, so omitting this would make the whole emission
        # unusable rather than merely incomplete. `autonomy_ceiling: gated` is
        # structural for this spine: both action slots are gated, so the ceiling
        # never needs to reach `auto`.
        "agents": {
            f"{ns}_agent": {
                "name": f"Governed {asset} Agent",
                "llm_model": "gpt-oss:20b",
                "autonomy_ceiling": "gated",
            }
        },
    }
    if criteria:
        # PLAN-0087: the vertical DECLARES its own vocabulary — zero engine diff.
        doc["compliance_criteria"] = criteria
    doc["procedures"] = {f"governed_{_snake(asset)}_approval": procedure}

    _assert_agreement(steps)
    _assert_prose_clean(doc, record)
    return doc


def write_procedures(record: IntakeRecord, ontology_doc: dict[str, Any], root: Path) -> Path:
    """Write the emitted ``procedures.yaml`` under ``root`` and return its path.

    A sibling of ``write_ontology`` / ``write_package`` so no caller has to re-implement
    the dump: the CLI doing its own ``YAML().dump`` is how a settings drift (width,
    unicode, flow style) between the tool and its own tests starts.
    """
    from services.engine.scaffolder.ontology import dump_yaml

    path = root / "verticals" / record.namespace / "procedures.yaml"
    return dump_yaml(emit_procedures(record, ontology_doc), path)


def _gate_fields(
    slot: StepSlot,
    record: IntakeRecord,
    criteria: list[str],
    band_property: str,
) -> dict[str, Any]:
    """The gate-kind-specific half of a step: the facet plus whatever it owes.

    One branch per gate kind, so "what does THIS gate owe" is readable on its
    own. Every branch emits its facet; the governance CONTENT is emitted only
    when confirmed intake supplies it, and is otherwise left absent as the
    shipped unfilled-stub form.
    """
    if slot.gate_kind is GateKind.IN_FILE_BAND:
        fields: dict[str, Any] = {
            "facet": {
                "decision_condition": {
                    "gate_kind": GateKind.IN_FILE_BAND.value,
                    "band_source": BandSource.IN_FILE.value,
                }
            }
        }
        # The per-entity band: emitted only when the operator named the property.
        if band_property:
            fields["threshold_field"] = band_property
        direction = record.confirmed_value("band.judge.direction")
        if direction:
            fields["direction"] = direction
        return fields

    if slot.gate_kind is GateKind.RULE_GATE:
        fields = {"facet": {"decision_condition": {"gate_kind": GateKind.RULE_GATE.value}}}
        if criteria:
            gate = ComplianceGate(
                rules=[
                    ComplianceRule(criterion=c, spec=f"TODO - the customer's own rule for {c}")
                    for c in criteria
                ]
            )
            fields["governance_content"] = gate.model_dump(mode="json")
        return fields

    if slot.gate_kind is GateKind.DOA_TIER:
        fields = {
            "facet": {"decision_condition": {"gate_kind": GateKind.DOA_TIER.value}},
            "handler": "escalate",
        }
        ladder = _doa_ladder(record)
        if ladder is not None:
            fields["governance_content"] = ladder
        return fields

    return {"facet": {"decision_condition": {"gate_kind": GateKind.NONE.value}}}


def _emit_step(
    slot: StepSlot,
    record: IntakeRecord,
    criteria: list[str],
    band_property: str,
    ontology_doc: dict[str, Any],
) -> dict[str, Any]:
    """One emitted step: SHAPE from the slot, VALUES from confirmed intake only.

    Split out of :func:`emit_procedures` so the per-gate-kind branches stay
    readable — the branch a reader cares about is "what does THIS gate kind owe",
    not the document assembly around it.
    """
    step: dict[str, Any] = {
        "step_id": slot.step_id,
        "name": slot.name,
        "kind": slot.kind.value,
    }
    if slot.input is not None:
        step["input"] = {"from": slot.input.from_step}
        if slot.input.where:
            step["input"]["where"] = dict(slot.input.where)
    if slot.autonomy is not None:
        step["autonomy"] = slot.autonomy.value

    step.update(_gate_fields(slot, record, criteria, band_property))

    if slot.step_id == "fulfill":
        step["handler"] = _terminal_handler(ontology_doc)
    return step


def _criteria(record: IntakeRecord) -> list[str]:
    raw = record.confirmed_value("governance.rule_gate.criteria")
    if not raw:
        return []
    return [part.strip() for part in raw.replace("\n", ",").split(",") if part.strip()]


def _doa_ladder(record: IntakeRecord) -> dict[str, Any] | None:
    """The DoaLadder content — built through the TYPED model, not as a raw dict.

    Two reasons it is typed rather than a dict literal:

    * **Validation at emit time.** ``DoaLadder`` enforces the first floor at 0
      and strictly-increasing floors, and REQUIRES an ``emergency_waiver``
      (ADR-0025 D3 — not optional). A raw dict would happily emit a ladder that
      only fails much later, at load, in a file the operator has already been
      handed.
    * A ``{"kind": "doa_tier"}`` dict literal is indistinguishable, to the
      trace-kind guard that scans ``services/engine``, from a ReasoningStep
      emission — and these are governance-content discriminators, not trace
      kinds. Building through the model keeps that guard honest instead of
      teaching it an exception.

    A ladder that cannot be built validly is emitted as NOTHING: a
    half-authored authority ladder that loads is more dangerous than one the
    review gate refuses, because it looks governed and routes on fiction.
    """
    currency = record.confirmed_value("governance.approve.currency")
    tiers_raw = record.confirmed_value("governance.approve.tiers")
    relaxes = record.confirmed_value("governance.approve.waiver.relaxes")
    ratifier = record.confirmed_value("governance.approve.waiver.ratifier")
    if not currency or not tiers_raw or not relaxes or not ratifier:
        return None

    tiers: list[DoaTier] = []
    for entry in tiers_raw.split(","):
        if ":" not in entry:
            continue
        amount, role = entry.split(":", 1)
        try:
            tiers.append(DoaTier(min_amount=Decimal(amount.strip()), approver_role=role.strip()))
        except (InvalidOperation, ValidationError):
            return None
    if not tiers:
        return None

    try:
        ladder = DoaLadder(
            currency=currency,
            tiers=tiers,
            emergency_waiver=EmergencyWaiverPolicy(
                relaxes=[RelaxableConstraint(r.strip()) for r in relaxes.split(",") if r.strip()],
                escalate_to=ratifier,
            ),
        )
    except (ValidationError, ValueError):
        return None
    return ladder.model_dump(mode="json")


def _terminal_handler(ontology_doc: dict[str, Any]) -> str:
    values = ontology_doc["object_types"]["RecommendedAction"]["properties"]["action_type"][
        "values"
    ]
    return str(values[0])


def _snake(noun: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(noun):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _assert_agreement(steps: list[dict[str, Any]]) -> None:
    """D4 agreement: the emitted spine's gate signature MUST equal the template's."""
    emitted = tuple(
        (
            str(step["step_id"]),
            str(step.get("facet", {}).get("decision_condition", {}).get("gate_kind", "none")),
        )
        for step in steps
    )
    expected = gate_signature()
    if emitted != expected:
        raise SpineAgreementError(
            f"emitted spine contradicts AT-2: {emitted!r} != template {expected!r}"
        )


def _assert_prose_clean(doc: dict[str, Any], record: IntakeRecord) -> None:
    """Run the shipped lint BEFORE writing (AC-5's "lint pre-paid")."""
    roles = frozenset(
        tier["approver_role"]
        for procedure in doc["procedures"].values()
        for step in procedure["steps"]
        for tier in step.get("governance_content", {}).get("tiers", [])
    )
    findings: list[str] = []
    for procedure in doc["procedures"].values():
        findings.extend(_lint(str(procedure["goal"]), roles=roles))
        findings.extend(_lint(str(procedure["title"]), roles=roles))
        for step in procedure["steps"]:
            findings.extend(_lint(str(step["name"]), roles=roles))
    if findings:
        raise ProseLintError(findings)
