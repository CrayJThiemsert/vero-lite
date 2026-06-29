"""Archetype templates — the machine-readable form of the procedure-archetype
catalog (ADR-0024 D2; PLAN-0040 Phase A, Step A1).

The prose catalog (``docs/conventions/procedure-archetypes.md``) is CANONICAL;
this is the DERIVED machine form with *slots to instantiate* (CLAUDE.md §4
canonical→derived — on conflict the catalog wins). v1 models the **AT-1 family
only** — AT-1 plus AT-1b / AT-3 as *variants of an AT-1 base* (ADR-0024 D2 / D7),
not three disjoint shapes; **AT-2 is deferred** (D7).

A template is an ordered list of :class:`StepSlot`. A slot declares the step's
``kind`` and its required ``gate_kind`` (the **archetype-agreement oracle**, D4)
plus the *structure* the generator may emit (G, D3) — step order, the input
fan-out, the typed ``llm_assist`` role. It carries **no governance values** (no
threshold / handler / env_var / tiers) — those are human-author stubs (H, D3).

:func:`instantiate` turns a template into a ``procedures.yaml``-shaped mapping
that round-trips ``load_procedures`` (D6 draft-loadable) with every H field
**absent** — the schema-correct stub (ADR-0024 OQ-C C1: no in-field sentinel; an
absent ``threshold`` is the valid ``None`` state, not a poisoned value). The
result is a SKELETON: it *loads*, but ``validate_governance_complete`` (Step A4)
refuses to *run* it until a human authors the stubs (the D6 two-state property).
"""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    GateKind,
    StepKind,
    Trigger,
)

_BAND_KINDS = (GateKind.ENV_BAND, GateKind.IN_FILE_BAND)
"""The two gate kinds an AT-1-family ``judge`` step may carry — the band-authoring
split (env-overridable vs in-file-authored; the catalog's load-bearing degree of
freedom). The ``judge`` is the only non-``none`` gate in the AT-1 family (D4)."""


class LlmAssist(BaseModel):
    """The typed advisory ``llm_assist`` role on a slot (ADR-0024 D11 / OQ-A3).

    The LLM may only ``draft`` or ``summarise`` a named field/artifact — ``select``
    / ``approve`` / ``set_threshold`` are structurally un-authorable here (governed
    ≠ generated). Typed in the template; emitted as a prose ``str`` on the live
    ``Step.facet.llm_assist`` at instantiate (no live-schema churn, OQ-A3).
    """

    model_config = ConfigDict(extra="forbid")

    role: Literal["draft", "summarise"]
    of: str = Field(description="the field or artifact the LLM drafts/summarises (advisory)")


class SlotInput(BaseModel):
    """A slot's input wiring — pure structure (G, D3): the earlier slot it consumes
    plus an optional field-equality fan-out filter. The template form of
    ``spec.StepInput`` (values-free)."""

    model_config = ConfigDict(extra="forbid")

    from_step: str = Field(description="an EARLIER slot's step_id whose output set feeds this slot")
    where: dict[str, str] | None = Field(
        default=None, description="field-equality fan-out filter, e.g. {verdict: breach}"
    )


class StepSlot(BaseModel):
    """One slot of an archetype template — the step's *shape*, never its governance
    values. ``gate_kind`` is the archetype-agreement oracle (D4); for a ``judge``
    (evaluate) slot it is a band kind whose specific source (env vs in_file) is a
    per-instance G/lean choice resolved at :func:`instantiate`."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    name: str = Field(description="prose label (G)")
    kind: StepKind
    gate_kind: GateKind = Field(
        description="the required decision-condition kind — the archetype-agreement oracle (D4)"
    )
    autonomy: Autonomy | None = Field(
        default=None,
        description="action slots only: the posture the shape dictates (gated breach / auto "
        "terminal). Still a human-CONFIRM obligation at authoring (H) — not a value the "
        "generator owns.",
    )
    input: SlotInput | None = None
    llm_assist: LlmAssist | None = Field(
        default=None, description="typed advisory role (OQ-A3); emitted as prose at instantiate"
    )

    @model_validator(mode="after")
    def _validate_slot(self) -> Self:
        if self.gate_kind in _BAND_KINDS and self.kind is not StepKind.EVALUATE:
            raise ValueError(
                f"slot '{self.step_id}': a band gate_kind belongs to an evaluate (judge) slot"
            )
        if self.autonomy is not None and self.kind is not StepKind.ACTION:
            raise ValueError(f"slot '{self.step_id}': autonomy applies to action slots only")
        return self


class ArchetypeTemplate(BaseModel):
    """A catalogued workflow shape with slots to instantiate (ADR-0024 D2). AT-1b /
    AT-3 declare their AT-1 ``base`` (modelled as base + delta, not disjoint)."""

    model_config = ConfigDict(extra="forbid")

    archetype_id: str = Field(description="catalog id, e.g. 'AT-1' / 'AT-1b' / 'AT-3'")
    title: str
    description: str = Field(
        default="",
        description="one-line classify-prompt hint DERIVED from the canonical catalog "
        "(docs/conventions/procedure-archetypes.md; PLAN-0041 OQ-A) — value-free, names the "
        "single-band nature; default='' keeps bare-template construction back-compatible",
    )
    base: str | None = Field(
        default=None, description="the AT-1 base archetype_id this varies (D2 base+delta)"
    )
    slots: list[StepSlot] = Field(min_length=1)
    terminal_slot: str = Field(description="the step_id of the terminal slot (D-derived)")

    @model_validator(mode="after")
    def _validate_template(self) -> Self:
        ids = [s.step_id for s in self.slots]
        if len(set(ids)) != len(ids):
            raise ValueError(f"archetype '{self.archetype_id}': duplicate slot step_id(s)")
        if self.terminal_slot not in ids:
            raise ValueError(
                f"archetype '{self.archetype_id}': terminal_slot '{self.terminal_slot}' "
                "is not a slot"
            )
        seen: set[str] = set()
        for slot in self.slots:
            if slot.input is not None and slot.input.from_step not in seen:
                raise ValueError(
                    f"archetype '{self.archetype_id}' slot '{slot.step_id}': input.from "
                    f"'{slot.input.from_step}' is not an earlier slot (linear/backward only)"
                )
            seen.add(slot.step_id)
        return self


# --- the AT-1 family (base + variant deltas; D2) --------------------------------


def _at1_base_slots() -> list[StepSlot]:
    """The AT-1 base: read → judge(band) → gated action on the breach set.

    A fresh list each call so the variant builders below can extend/copy it without
    mutating a shared module-level object (the base + delta is built in code, so the
    variants are demonstrably *derived from* the base, not hand-duplicated)."""
    return [
        StepSlot(
            step_id="read", name="Read the signal", kind=StepKind.QUERY, gate_kind=GateKind.NONE
        ),
        StepSlot(
            step_id="judge",
            name="Judge against the band",
            kind=StepKind.EVALUATE,
            # default band kind; instantiate(band_source=ENV) emits env_band instead
            gate_kind=GateKind.IN_FILE_BAND,
        ),
        StepSlot(
            step_id="act",
            name="Act on the breach set",
            kind=StepKind.ACTION,
            gate_kind=GateKind.NONE,
            autonomy=Autonomy.GATED,  # human go/no-go on the irreversible write
            input=SlotInput(from_step="judge", where={"verdict": "breach"}),
            llm_assist=LlmAssist(role="draft", of="action proposal"),
        ),
    ]


def _at1b_slots() -> list[StepSlot]:
    """AT-1b = the AT-1 base + a gated watch-escalation proposal + an auto summary
    terminal (the ADR-0019 watch→gated branch + the no-op echo receipt)."""
    slots = _at1_base_slots()
    slots.append(
        StepSlot(
            step_id="escalate_watch",
            name="Escalate the watch set (gated proposal)",
            kind=StepKind.ACTION,
            gate_kind=GateKind.NONE,
            autonomy=Autonomy.GATED,  # the human decides on the ambiguous band (ADR-0019)
            input=SlotInput(from_step="judge", where={"verdict": "watch"}),
            llm_assist=LlmAssist(role="draft", of="precautionary proposal"),
        )
    )
    slots.append(
        StepSlot(
            step_id="summary",
            name="Round summary",
            kind=StepKind.ACTION,
            gate_kind=GateKind.NONE,
            autonomy=Autonomy.AUTO,  # a no-op echo receipt, not an operational write
            input=SlotInput(from_step="judge"),  # the whole verdict set (no where)
            llm_assist=LlmAssist(role="draft", of="round summary"),
        )
    )
    return slots


def _at3_slots() -> list[StepSlot]:
    """AT-3 = the AT-1 base with the MRO calm-reorder intent (same shape, distinct
    cadence — a steady restock loop, not anomaly remediation; D2). Re-labelled, not
    re-shaped."""
    slots = _at1_base_slots()
    slots[0] = slots[0].model_copy(update={"name": "Read stock levels"})
    slots[1] = slots[1].model_copy(update={"name": "Judge against the reorder point"})
    slots[2] = slots[2].model_copy(update={"name": "Reorder the low-stock set", "llm_assist": None})
    return slots


AT1 = ArchetypeTemplate(
    archetype_id="AT-1",
    title="anomaly→action",
    description=(
        "read a signal, judge it against one deterministic band, then act on the breach "
        "set after a human go/no-go"
    ),
    slots=_at1_base_slots(),
    terminal_slot="act",
)
AT1B = ArchetypeTemplate(
    archetype_id="AT-1b",
    title="anomaly→action + watch escalation + summary",
    description=(
        "the AT-1 loop plus a second band-routed branch for the borderline watch set and "
        "an automatic summary receipt"
    ),
    base="AT-1",
    slots=_at1b_slots(),
    terminal_slot="summary",
)
AT3 = ArchetypeTemplate(
    archetype_id="AT-3",
    title="monitor→reorder",
    description=(
        "read stock levels, judge them against a single reorder-point band, then reorder "
        "the low set after one human approval"
    ),
    base="AT-1",
    slots=_at3_slots(),
    terminal_slot="act",
)

REGISTRY: dict[str, ArchetypeTemplate] = {t.archetype_id: t for t in (AT1, AT1B, AT3)}
"""The v1 archetype-template registry — the AT-1 family only (D7). AT-2 is deferred:
an AT-2-class narrative routes to hand-author (the abstain path, D5), never a
down-classified AT-3 skeleton."""


# --- instantiation --------------------------------------------------------------


def _decision_condition(slot: StepSlot, band_source: BandSource) -> dict[str, Any]:
    """The typed ``decision_condition`` facet for a slot — the G classification only.

    For a band ``judge`` slot, emit ``gate_kind`` + ``band_source`` (G/lean) and
    leave the value binding ABSENT (the H stub): ``env_var`` for an env band,
    ``threshold`` / ``direction`` / ``watch_margin`` for an in-file band. For every
    other slot the gate is ``none``."""
    if slot.gate_kind in _BAND_KINDS:
        if band_source is BandSource.ENV:
            # env_var (the specific binding) is an H stub — absent
            return {"gate_kind": GateKind.ENV_BAND.value, "band_source": BandSource.ENV.value}
        # threshold / direction / watch_margin are H stubs — absent
        return {"gate_kind": GateKind.IN_FILE_BAND.value, "band_source": BandSource.IN_FILE.value}
    return {"gate_kind": slot.gate_kind.value}


def instantiate(
    template: ArchetypeTemplate,
    *,
    procedure_id: str,
    title: str,
    agent_id: str = "author_agent",
    vertical: str = "draft",
    band_source: BandSource = BandSource.IN_FILE,
) -> dict[str, Any]:
    """Instantiate a template into a ``procedures.yaml``-shaped mapping that
    round-trips ``load_procedures`` (D6 draft-loadable).

    Every human-author (H) governance value is ABSENT — the schema-correct stub
    (ADR-0024 OQ-C C1: no in-field sentinel). The judge step carries its band
    *kind* + *source* (G) but no band *value*; action steps carry their autonomy
    posture but no ``handler`` (H); the agent is a placeholder the human binds
    (``run_by`` resolves so the skeleton loads, but ``allowed`` is empty). The
    output is a SKELETON: ``load_procedures`` accepts it; ``validate_governance_complete``
    refuses to run it until the stubs are authored (the two-state property, D6)."""
    steps: list[dict[str, Any]] = []
    for slot in template.slots:
        step: dict[str, Any] = {
            "step_id": slot.step_id,
            "name": slot.name,
            "kind": slot.kind.value,
        }
        if slot.autonomy is not None:
            step["autonomy"] = slot.autonomy.value
        if slot.input is not None:
            inp: dict[str, Any] = {"from": slot.input.from_step}
            if slot.input.where is not None:
                inp["where"] = dict(slot.input.where)
            step["input"] = inp
        facet: dict[str, Any] = {"decision_condition": _decision_condition(slot, band_source)}
        if slot.llm_assist is not None:
            facet["llm_assist"] = f"{slot.llm_assist.role} the {slot.llm_assist.of} (advisory)"
        step["facet"] = facet
        steps.append(step)
    return {
        "namespace": vertical,
        "version": 0,
        "agents": {agent_id: {"name": "<author: name + bind this agent>"}},
        "procedures": {
            procedure_id: {
                "title": title,
                "run_by": agent_id,
                "trigger": Trigger.MANUAL.value,
                "steps": steps,
                "terminal": template.terminal_slot,
            }
        },
    }
