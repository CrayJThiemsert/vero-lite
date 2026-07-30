"""A real repair case, as an OperationalEvent (PLAN-0096 Step 8, build-order item 2).

Pure and deterministic: no DB, no clock, no network. Everything it needs is passed
in, which is what makes the event contract testable without standing up Postgres and
the whole engine — the shape this row must satisfy is governance-critical, and an
oracle that could only run end-to-end would not be run often enough.

**Why the vertical owns this and the engine does not.** What counts as a governed
spend reading, which ฿ figure the ladder routes on, and how a Thai description reads
on the operator's timeline are all this operator's answers. An engine-side builder
would make them every vertical's answers (ADR-006).

**The compliance block is load-bearing and fails CLOSED.** Step 4 deleted the
fail-open ``default: {compliance: {three_quote: true}}``, so a row reaching
``rule_gate`` without the map raises rather than passing. This module therefore runs
the REAL :func:`compute_three_quote` through the REAL :func:`compliance_signal_map`
— the same two functions the synthetic fixture calls — so a live case and a demo row
can never disagree about the same numbers.
"""

from __future__ import annotations

from typing import Any

from services.db.case_events import CaseFacts
from verticals.fleet_maintenance.sourcing import compliance_signal_map, compute_three_quote

#: Prefix for the generated ``event_id``. Derived from the case id rather than
#: random, so a refresh that reloads the same case produces the same event and the
#: projection's change detection is not defeated by a fresh uuid every read.
EVENT_ID_PREFIX = "event-case"


def event_id_for(case_id: str) -> str:
    """The stable event id for one case — one function so nothing spells it twice."""
    return f"{EVENT_ID_PREFIX}-{case_id}"


def _severity(*, breaches_ceiling: bool, work_type: str) -> str:
    """Triage colour for the timeline. **Nothing routes on this.**

    Stated plainly because the opposite is easy to assume: a ``severity_tier`` gate
    reads ``excursion_severity``, a DIFFERENT field, and ``governance_step.py``
    warns in its own docstring that reading the ontology's ``severity`` there would
    silently route an event-triage string as an authority quantity. Fleet routes on
    ``doa_tier`` — money — so this value is for the human reading the map.
    """
    if not breaches_ceiling:
        return "info"
    return "critical" if work_type == "breakdown" else "warn"


def _description(facts: CaseFacts, *, breaches_ceiling: bool, ceiling_thb: float) -> str:
    """The line a human reads on the timeline, in the operator's own language.

    The case's own text leads when เมย์ wrote one — it is what ต้อม phoned in, and it
    says more than any template. The generated tail states only what is recorded: the
    agreed garage, the agreed figure, and whether it clears the truck's own ceiling.
    """
    head = (facts.description or "").strip() or "แจ้งซ่อม (ไม่ได้ระบุรายละเอียด)"
    tail = f"{facts.accepted_vendor} เสนอราคา {facts.accepted_amount_thb:,.2f} บาท (ใบที่ตกลง)"
    if breaches_ceiling:
        tail += f" — เกินเพดาน {ceiling_thb:,.0f} บาท ต้องเข้าสายอนุมัติ"
    else:
        tail += f" — ต่ำกว่าเพดาน {ceiling_thb:,.0f} บาท ช่างใหญ่เคาะเองได้"
    if facts.accepted_reason:
        tail += f" (เหตุผลที่ไม่เอาใบถูกสุด: {facts.accepted_reason})"
    return f"{head} — {tail}"


def build_event(facts: CaseFacts, *, site_id: str, ceiling_thb: float) -> dict[str, Any]:
    """One real case as an OperationalEvent dict, shaped like the synthetic fixture.

    ``measured_value`` is a float while the stored amount is ``Numeric(14, 2)``, and
    that conversion is deliberate rather than sloppy. The ontology's
    ``OperationalEvent.measured_value`` is a numeric reading across every vertical,
    ``demo_events`` skips any row whose value is not ``int | float`` when it anchors
    the timeline, and the ``judge`` step compares it against a float ceiling. The
    governance DECISION is not taken on the float: :func:`compute_three_quote` below
    receives the exact ``Decimal``. THB amounts in this fleet are far inside the
    range a float represents exactly to the satang, so the conversion is lossless
    here — it would not be for arbitrary precision, which is why the Decimal is what
    the schema stores and what the rule reads.
    """
    breaches_ceiling = float(facts.accepted_amount_thb) >= ceiling_thb
    basis_signal = compute_three_quote(
        amount_thb=facts.accepted_amount_thb,
        distinct_vendor_count=facts.distinct_vendor_count,
        has_sole_source_justification=facts.has_sole_source_justification,
    )
    _, basis = basis_signal
    return {
        "event_id": event_id_for(facts.case_id),
        "event_type": "reading",
        "severity": _severity(breaches_ceiling=breaches_ceiling, work_type=facts.work_type),
        "measured_value": float(facts.accepted_amount_thb),
        "unit": "THB",
        "case_id": facts.case_id,
        "compliance": compliance_signal_map(basis_signal),
        "three_quote_basis": basis,
        "description": _description(
            facts, breaches_ceiling=breaches_ceiling, ceiling_thb=ceiling_thb
        ),
        # The moment the governed figure became true — not when the case was opened
        # (there was no number yet) and not "now" (which would make the timeline
        # jump on every refresh and defeat the projection's change detection).
        "occurred_at": facts.accepted_at,
        "truck_id": facts.truck_id,
        "site_id": site_id,
    }
