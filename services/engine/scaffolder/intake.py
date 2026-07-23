"""Intake engine — the typed record, the required-slot checklist, the question queue.

PLAN-0091 Step 1 (oracles AC-1 / AC-2). Three responsibilities:

1. :class:`IntakeRecord` — the operator-input-only carrier for every governance
   value the scaffolder will emit. There is no constructor path from an LLM
   emission: this module imports nothing from the generator/LLM layer, and an
   answer can only be built from operator text or a committed fixture.
2. :func:`required_slots` — the deterministic checklist, derived from
   **(AT-2 obligations x ontology judgment slots x fixture value slots)**. The
   AT-2 half is derived by calling the shipped
   :func:`~services.engine.procedures.draft.derive_governance_todo` on the
   spine's steps rather than restating its rules, so the checklist cannot drift
   from what the review gate actually demands.
3. :func:`open_questions` — the queue, with **sub-slot decomposition** (SD-3):
   one customer question decomposes into individually-answerable sub-slots, so
   answering one number never closes the others. They re-surface until each is
   answered on its own.

**Why sub-slots are the load-bearing shape (PLAN-0086's Q2, in-tree).** The
customer's emergency-bypass answer carried three distinct facts: a ฿10,000 cap,
an after-the-fact ratifier, and a ratification window. Only the ratifier maps to
a schema field (``EmergencyWaiverPolicy.escalate_to``); the cap and the window
have **no schema field at all** — see the UNMODELLED note in
``verticals/fleet_maintenance/procedures.yaml`` at the ``approve`` step. A queue
that treated "cap = ฿10,000" as *the* answer to "tell me about the emergency
bypass" would silently drop two customer facts. Here the cap fills exactly one
sub-slot; the other two stay open and re-surface, and the non-schema ones feed
the README's "stated but NOT enforced" register instead of being lost.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from services.engine.procedures.draft import derive_governance_todo
from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    DecisionCondition,
    GateKind,
    Step,
    StepFacet,
    StepKind,
)


class SlotKind(StrEnum):
    """Where a filled slot's value LANDS — which decides how an *unfilled* one is treated.

    A missing ``GOVERNANCE_VALUE`` or ``ONTOLOGY_JUDGMENT`` blocks emission of the
    thing that owes it; a missing ``FIXTURE_VALUE`` is emittable as a marked guess;
    an ``UNMODELLED`` slot is never emitted into YAML at all — it is recorded in the
    README register so the customer's fact survives the schema's silence.
    """

    ONTOLOGY_JUDGMENT = "ontology_judgment"
    GOVERNANCE_VALUE = "governance_value"
    FIXTURE_VALUE = "fixture_value"
    UNMODELLED = "unmodelled"


class Slot(BaseModel):
    """One atomically-answerable unit of the checklist.

    ``slot_id`` is dotted and stable — it is the re-ask key, so a partially
    answered question re-surfaces exactly its unanswered parts.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    slot_id: str = Field(min_length=1, description="stable dotted id; the re-ask key")
    question: str = Field(min_length=1, description="the operator-facing ask")
    kind: SlotKind
    owed_by: str = Field(
        default="",
        description="the spine step_id / ontology object that owes this slot ('' = fixture)",
    )
    schema_field: str | None = Field(
        default=None,
        description="the typed field this value fills; None means UNMODELLED — the value has "
        "no schema home and belongs in the 'stated but NOT enforced' register",
    )


class IntakeAnswer(BaseModel):
    """One operator-supplied value.

    ``confirmed`` is the ADR-0024 D5 gate: an unconfirmed answer never reaches an
    emitter (the ontology stage stops rather than defaulting — AC-3). ``guess``
    marks a value the operator supplied as a placeholder, which the package
    emitter must render with the ``# GUESS — รอแก้`` marker (AC-4).
    """

    model_config = ConfigDict(extra="forbid")

    slot_id: str = Field(min_length=1)
    value: str = Field(description="the operator's answer, verbatim — never model-authored")
    confirmed: bool = True
    guess: bool = False


class IntakeRecord(BaseModel):
    """The typed intake carrier — **operator-input-only by construction**.

    Nothing in this module can populate :attr:`answers` from a model emission:
    there is no LLM import here, and :class:`IntakeAnswer` is built only from
    operator text or a committed fixture. That is what keeps every governance
    value on the human side of ADR-0024's "governed ≠ generated" line at the
    type level rather than by prompt discipline.
    """

    model_config = ConfigDict(extra="forbid")

    namespace: str = Field(min_length=1, description="the vertical namespace being scaffolded")
    narrative: str = Field(default="", description="the raw customer narrative, verbatim")
    answers: list[IntakeAnswer] = Field(default_factory=list)

    def answered(self) -> dict[str, IntakeAnswer]:
        """Answers by slot id. A later answer for the same slot supersedes an earlier one."""
        return {a.slot_id: a for a in self.answers}

    def confirmed_value(self, slot_id: str) -> str | None:
        """The confirmed value for ``slot_id``, or ``None`` if unanswered or unconfirmed.

        Emitters call this rather than reading :attr:`answers` directly, so an
        unconfirmed answer can never leak into an emitted artifact.
        """
        answer = self.answered().get(slot_id)
        if answer is None or not answer.confirmed:
            return None
        return answer.value


# --- the row-11 spine -------------------------------------------------------
#
# The AT-2 money spine's step/gate SEQUENCE, read off the committed golden donor
# `verticals/fleet_maintenance/procedures.yaml` (intake -> judge -> reshape ->
# rule_gate -> approve -> fulfill). PLAN-0091's sequencing note: this sequence is
# all Step 1 needs from Step 4 — the obligations below are derived from
# (gate_kind, kind) alone, never from an ArchetypeTemplate or the REGISTRY.

_SPINE: tuple[tuple[str, StepKind, GateKind], ...] = (
    ("intake", StepKind.QUERY, GateKind.NONE),
    ("judge", StepKind.EVALUATE, GateKind.IN_FILE_BAND),
    ("reshape", StepKind.TRANSFORM, GateKind.NONE),
    ("rule_gate", StepKind.EVALUATE, GateKind.RULE_GATE),
    ("approve", StepKind.ACTION, GateKind.DOA_TIER),
    ("fulfill", StepKind.ACTION, GateKind.NONE),
)


def spine_steps() -> list[Step]:
    """The row-11 spine as minimal :class:`Step` models.

    Minimal on purpose: only the fields ``derive_governance_todo`` reads
    (``kind``, the facet's ``gate_kind``, and ``threshold_field``'s absence) are
    populated, because the checklist depends on the *shape* of the spine, not on
    values a human has not supplied yet.
    """
    steps: list[Step] = []
    for step_id, kind, gate_kind in _SPINE:
        band_source = BandSource.IN_FILE if gate_kind is GateKind.IN_FILE_BAND else None
        steps.append(
            Step(
                step_id=step_id,
                name=step_id,
                kind=kind,
                autonomy=None if kind is not StepKind.ACTION else Autonomy.GATED,
                facet=StepFacet(
                    decision_condition=DecisionCondition(
                        gate_kind=gate_kind,
                        band_source=band_source,
                    )
                ),
            )
        )
    return steps


# --- the three obligation families ------------------------------------------

# The AT-2 governance_content leaf slots, per gate kind. Each entry is
# (sub_slot, schema_field_or_None, question). A None schema_field is the
# UNMODELLED case — a customer fact with nowhere to live in the typed model,
# which is exactly why the register in AC-4 exists.
_GOVERNANCE_LEAVES: dict[GateKind, tuple[tuple[str, str | None, str], ...]] = {
    GateKind.DOA_TIER: (
        ("currency", "currency", "สกุลเงินของเพดานอนุมัติ (ISO เช่น THB)?"),
        (
            "tiers",
            "tiers",
            "ขั้นบันไดอำนาจอนุมัติ — แต่ละขั้นเริ่มที่ยอดเท่าไร และใครเป็นคนอนุมัติ?",
        ),
        (
            "waiver.relaxes",
            "emergency_waiver.relaxes",
            "กรณีฉุกเฉิน ผ่อนปรนกติกาข้อไหนได้บ้าง (three_bid / sole_source)?",
        ),
        (
            "waiver.ratifier",
            "emergency_waiver.escalate_to",
            "กรณีฉุกเฉิน ใครเป็นคนรับรอง/อนุมัติย้อนหลัง?",
        ),
        (
            "waiver.cap",
            None,
            "กรณีฉุกเฉิน มีเพดานยอดเงินไหม (เท่าไร)?",
        ),
        (
            "waiver.window",
            None,
            "กรณีฉุกเฉิน ต้องรับรองย้อนหลังภายในกี่วัน/ชั่วโมง?",
        ),
        # ADR-0025 D5: a doa_tier gate REQUIRES separation of duties. It is a
        # procedure-level field rather than a DoaLadder one, but it is owed by
        # THIS gate, so the operator must be asked here — and it is the gap class
        # PLAN-0086 hit as "an ambiguous requester": the customer names an
        # approver readily and leaves who *files* the claim implicit.
        (
            "sod.requester",
            "separation_of_duties",
            "ใครเป็นคนตั้งเรื่อง/ยื่นขออนุมัติ (ต้องคนละคนกับผู้อนุมัติ)?",
        ),
    ),
    GateKind.RULE_GATE: (
        (
            "criteria",
            "rules",
            "กติกาที่ต้องผ่านก่อนอนุมัติมีอะไรบ้าง (ตั้งชื่อ criterion + เงื่อนไข)?",
        ),
        # The fourth PLAN-0086 gap class — "a threshold-less comparison rule".
        # The customer's rule has two halves ("three competing quotes" AND "above
        # ฿20,000") and only the first is representable: a rule_gate criterion is
        # pass/fail on a supplied signal and carries no threshold field, and
        # ADR-0025 D4 forbids smuggling the amount into its prose. The ฿ half is
        # therefore UNMODELLED by type — see the same finding recorded in
        # `verticals/fleet_maintenance/procedures.yaml` at the `quote_gate` step.
        (
            "criteria.threshold",
            None,
            "กติกานี้เริ่มบังคับใช้ที่ยอดเท่าไร (ถ้ามีเงื่อนไขยอดเงิน)?",
        ),
    ),
    GateKind.IN_FILE_BAND: (),
    GateKind.SCORED_RULE: (("criteria", "criteria", "เกณฑ์ให้คะแนนผู้ขายมีอะไรบ้าง และถ่วงน้ำหนักเท่าไร?"),),
    GateKind.SEVERITY_TIER: (("tiers", "tiers", "ขั้นความรุนแรงแต่ละขั้น ใครเป็นคนตัดสิน?"),),
}

# The band obligations `derive_governance_todo` names for an evaluate step.
_BAND_QUESTIONS: dict[str, str] = {
    "threshold": "เส้นแบ่ง (threshold) ที่ถือว่าผิดปกติคือเท่าไร?",
    "threshold_field": "ใช้คอลัมน์ไหนเป็นเส้นแบ่งรายตัว (per-entity band)?",
    "direction": "ผิดปกติเมื่อค่า 'สูงกว่า' หรือ 'ต่ำกว่า' เส้นแบ่ง?",
    "env_var": "อ่านเส้นแบ่งจาก env var ตัวไหน?",
}

# The three ontology judgment slots (AC-3): the grammar emits the 6-object
# skeleton and all 7 link_types mechanically, but these three are judgment and
# are emitted ONLY from confirmed intake.
_ONTOLOGY_JUDGMENTS: tuple[tuple[str, str, str], ...] = (
    ("asset_noun", "Asset", "หน่วยสินทรัพย์ที่ลูกค้าพูดถึงคืออะไร (เช่น รถบรรทุก, บ่อ, คลัง)?"),
    # DEVIATION from the PLAN's "three judgment slots", surfaced not silent
    # (Step 2 build, session 167). The grammar's Site object is NOT mechanically
    # derivable: the golden donor names it `Depot`, and AC-7 asserts the emitted
    # object SET matches the committed one, so emitting a generic `Site` would
    # fail the diff-oracle by construction. It is the same KIND of judgment as
    # the Asset noun (a customer-vocabulary naming call the ledger simply did not
    # enumerate separately), so it is asked, never guessed.
    ("site_noun", "Site", "สถานที่ที่สินทรัพย์สังกัดอยู่เรียกว่าอะไร (เช่น อู่, ศูนย์, คลัง)?"),
    (
        "band_property",
        "Asset.band_property",
        "เพดาน/เส้นแบ่งรายตัวของสินทรัพย์เก็บเป็น property ชื่ออะไร?",
    ),
    (
        "action_types",
        "RecommendedAction.action_type",
        "การกระทำที่ระบบจะเสนอมีอะไรบ้าง (ชุดปิด — ตั้งชื่อให้ครบ)?",
    ),
)

# The synthetic-fixture value slots (AC-4): every numeric literal in the emitted
# synthetic.py must trace to one of these or carry the GUESS marker.
_FIXTURE_VALUES: tuple[tuple[str, str], ...] = (
    ("asset_count", "จะสร้างสินทรัพย์สังเคราะห์กี่ตัวสำหรับเดโม?"),
    ("breach_value", "ค่าที่ทำให้เกิด breach ในเดโมควรเป็นเท่าไร?"),
    ("normal_value", "ค่าปกติ (ไม่ breach) ควรเป็นเท่าไร?"),
    ("band_value", "เพดานรายตัวของสินทรัพย์ตัวอย่างควรเป็นเท่าไร?"),
)


def required_slots(steps: Sequence[Step] | None = None) -> list[Slot]:
    """The complete required-slot checklist — the AC-2 "derives the question set up front".

    The product of the three families in PLAN-0091's Step 1 definition:

    * **AT-2 obligations** — for each spine step, whatever the shipped
      :func:`derive_governance_todo` says it owes, expanded to the typed model's
      leaf value slots (a ``governance_content`` obligation is not one question,
      it is one per authored leaf).
    * **ontology judgment slots** — the three the grammar refuses to guess.
    * **fixture value slots** — the synthetic-demo numerics.

    Order is deterministic (spine order, then judgments, then fixtures) so the
    queue a re-run shows an operator is the queue they saw last time.
    """
    slots: list[Slot] = []
    for step in steps if steps is not None else spine_steps():
        gate_kind = (
            step.facet.decision_condition.gate_kind
            if step.facet is not None and step.facet.decision_condition is not None
            else GateKind.NONE
        )
        for obligation in derive_governance_todo(step):
            if obligation == "governance_content":
                for sub, schema_field, question in _GOVERNANCE_LEAVES.get(gate_kind, ()):
                    slots.append(
                        Slot(
                            slot_id=f"governance.{step.step_id}.{sub}",
                            question=question,
                            kind=(
                                SlotKind.GOVERNANCE_VALUE
                                if schema_field is not None
                                else SlotKind.UNMODELLED
                            ),
                            owed_by=step.step_id,
                            schema_field=schema_field,
                        )
                    )
            elif obligation in _BAND_QUESTIONS:
                slots.append(
                    Slot(
                        slot_id=f"band.{step.step_id}.{obligation}",
                        question=_BAND_QUESTIONS[obligation],
                        kind=SlotKind.GOVERNANCE_VALUE,
                        owed_by=step.step_id,
                        schema_field=obligation,
                    )
                )
            # `handler` / `autonomy` / `transform` are structural obligations the
            # emitters fill from the spine itself (the archetype fixes the handler
            # name and every AT-2 action is `gated`), so they are not operator
            # questions. They stay derived, never defaulted silently: Step 4 emits
            # them from the template and the review gate re-derives this same list.

    for sub, owner, question in _ONTOLOGY_JUDGMENTS:
        slots.append(
            Slot(
                slot_id=f"ontology.{sub}",
                question=question,
                kind=SlotKind.ONTOLOGY_JUDGMENT,
                owed_by=owner,
                schema_field=sub,
            )
        )

    for sub, question in _FIXTURE_VALUES:
        slots.append(
            Slot(
                slot_id=f"fixture.{sub}",
                question=question,
                kind=SlotKind.FIXTURE_VALUE,
                owed_by="",
                schema_field=sub,
            )
        )

    return slots


def open_questions(record: IntakeRecord, slots: Sequence[Slot] | None = None) -> list[Slot]:
    """The slots still open for ``record`` — the re-ask queue (SD-3).

    A slot is open until it carries its **own** confirmed answer. This is the
    whole point of sub-slot decomposition: an answer to
    ``governance.approve.waiver.cap`` closes that slot and nothing else, so the
    ratifier and window re-surface on the next pass instead of being assumed
    answered because the operator "answered the waiver question".
    """
    checklist = list(slots) if slots is not None else required_slots()
    answered = record.answered()
    return [
        slot
        for slot in checklist
        if slot.slot_id not in answered or not answered[slot.slot_id].confirmed
    ]


def unenforced_register(record: IntakeRecord, slots: Sequence[Slot] | None = None) -> list[Slot]:
    """The "stated but NOT enforced" register feed (AC-4).

    Slots with no schema home, whether answered or not. An **answered** one is
    the sharper case: the customer told us a real rule (a ฿10,000 emergency cap)
    and the typed model has nowhere to put it, so the README must say so out
    loud rather than let the omission read as "the customer never mentioned it".
    """
    checklist = list(slots) if slots is not None else required_slots()
    return [slot for slot in checklist if slot.kind is SlotKind.UNMODELLED]


def format_queue(slots: Iterable[Slot]) -> str:
    """Render the open queue for the operator (``--plan-only`` output, AC-1)."""
    lines = [f"  [{slot.kind.value}] {slot.slot_id}\n      {slot.question}" for slot in slots]
    return "\n".join(lines) if lines else "  (no open questions)"
