"""Record which governed run decided which repair case (PLAN-0096 Step 8, item 3).

The fleet's `on_resolved` hook. The engine says *"this gate was resolved, here is
the durable result"*; deciding that this means a row in `repair_case_run_link` is
the vertical's job (ADR-006), so all of the case-shaped knowledge lives here.

**Where the case id actually is** — measured s191 against a real persisted run,
not inferred. Each entry in the resolved step's `decisions` list carries a full
`action`, whose `reasoning_trace` holds a step with `kind == "ontology_query"`
whose `detail["event"]` is the WHOLE event dict the engine ingested, `case_id`
included (`services/engine/llm/trace.py`). Keying on `kind` rather than on a trace
index is deliberate: the trace grows steps over time and a positional read would
break quietly the first time one is inserted ahead of it.

**Why not read the case id off `action_id`.** It is there — an action id is
`action-{event_id}` and a live case's event id is `event-case-{case_id}` — and
parsing it would be shorter. It would also silently couple the audit trail to two
independent id FORMATS, so a future change to either would produce link rows for
cases that do not exist rather than an error. The trace carries the event itself;
read the data, not the name.

**The outcome comes from the canonical reader.** `ratification_state()` is what
the month-end export will use to describe the same decision, so the hook calls it
rather than re-deriving the distinction from `target.status` and audit keys. Two
readers of one fact are two chances to disagree about a repair someone signed for.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case_run_link import (
    LINK_OUTCOME_APPROVED,
    LINK_OUTCOME_PROVISIONAL,
    LINK_OUTCOME_RATIFIED,
    LINK_OUTCOME_REFUSED,
    LINK_OUTCOME_REJECTED,
    RepairCaseRunLink,
)
from services.engine.procedures.gate_hooks import decided_entries, register_on_resolved
from services.engine.procedures.ratification import ratification_state
from services.engine.procedures.runs import StepResult

_VERTICAL = "fleet_maintenance"

#: The proposal status the gate writes when a human approved AND the handler ran.
#: Anything else on a non-ratification path is a reject: the gate's own vocabulary
#: is binary at this point, and inventing a third reading here would put this
#: module's guess into an audit row.
_EXECUTED = "executed"


def _ingested_event(proposal: dict[str, Any]) -> dict[str, Any] | None:
    """The event dict the engine ingested for one proposal, or None.

    One walk of the trace, so the case id and the sourcing basis are read from the
    SAME event rather than from two independent traversals that could, after a
    future trace change, disagree about which event a link row describes.

    Keyed on ``kind`` rather than on a trace index: the trace grows steps over time
    and a positional read would break quietly the first time one is inserted ahead
    of this one.
    """
    action = proposal.get("action")
    if not isinstance(action, dict):
        return None
    for step in action.get("reasoning_trace") or []:
        if not isinstance(step, dict) or step.get("kind") != "ontology_query":
            continue
        detail = step.get("detail")
        if not isinstance(detail, dict):
            continue
        event = detail.get("event")
        if isinstance(event, dict):
            return event
    return None


def case_id_of(proposal: dict[str, Any]) -> str | None:
    """The repair case one proposal is about, or None if it is not case-derived.

    None is the normal answer for the synthetic demo rows — they carry no case —
    and must stay distinguishable from an error, or the fixture would start
    manufacturing link rows for cases that do not exist.
    """
    event = _ingested_event(proposal)
    if event is None:
        return None
    case_id = event.get("case_id")
    return case_id if isinstance(case_id, str) and case_id else None


def basis_of(proposal: dict[str, Any]) -> str | None:
    """The ``three_quote_basis`` the gate saw for this proposal, or None.

    Read from the ingested event rather than recomputed from today's evidence pack
    — the distinction ``compute_three_quote`` exists to preserve. Recomputing at
    report time would answer the audit question against whatever the threshold has
    become, not the one the approval was actually made under.

    Deliberately NOT validated against the known basis vocabulary here. This is an
    audit trail: if the engine ever writes an unrecognised basis, the honest record
    is the value it wrote, and coercing it to None would erase the only evidence
    that something upstream changed.
    """
    event = _ingested_event(proposal)
    if event is None:
        return None
    basis = event.get("three_quote_basis")
    return basis if isinstance(basis, str) and basis else None


def _outcome(proposal: dict[str, Any], *, ratification: str) -> str:
    """What this case got out of this decision.

    **A refusal is checked FIRST, before any ratification state** (Cray, typed
    s192). A ratification obligation is created by the run, not by the proposal, so
    it rides along on every case the same gate touched — including the ones the
    approver turned down. Letting the run-level state win would stamp a rejected
    repair `provisional`, and the month-end export would report it as awaiting a
    signature that nobody will ever give, because there is nothing to sign for: the
    spend was declined. A rejection is already a complete, traceable decision.

    Above that line the ratification states DO dominate the per-proposal status:
    once an obligation exists over work that actually happened, "the handler ran" is
    no longer the interesting fact — whether anyone has signed for it is.
    """
    if proposal.get("status") != _EXECUTED:
        return LINK_OUTCOME_REJECTED
    if ratification == "ratified":
        return LINK_OUTCOME_RATIFIED
    if ratification == "refused":
        return LINK_OUTCOME_REFUSED
    if ratification in ("pending", "overdue"):
        return LINK_OUTCOME_PROVISIONAL
    return LINK_OUTCOME_APPROVED


async def link_resolved_cases(session: AsyncSession, run_id: str, target: StepResult) -> None:
    """Write one link row per case this gate resolution decided.

    Idempotent against a re-fire by the schema, not by care: the
    `(case_id, run_id, step_id, outcome)` unique constraint rejects a duplicate,
    and this checks for the existing row first so a legitimate re-entry is a no-op
    rather than an IntegrityError the engine's fail-soft path would then have to
    swallow. A RATIFICATION is a different `outcome` on the same three keys, so it
    still lands beside the provisional row it supersedes.
    """
    now = datetime.now(UTC)
    state = ratification_state(target.audit, now).state
    seen: set[tuple[str, str]] = set()

    # `decided_entries`, never `artifact["output_set"]`: the gate threads only the
    # EXECUTED effects forward, so a resolution that rejected this case would leave
    # it out entirely and the case would present as never decided. That is the exact
    # failure `LINK_OUTCOME_REJECTED` exists to prevent, and reading the executed
    # subset would have made that constant permanently unreachable.
    for proposal in decided_entries(target):
        case_id = case_id_of(proposal)
        if case_id is None:
            continue
        outcome = _outcome(proposal, ratification=state)
        if (case_id, outcome) in seen:
            continue
        seen.add((case_id, outcome))

        existing = await session.execute(
            RepairCaseRunLink.__table__.select().where(
                RepairCaseRunLink.case_id == case_id,
                RepairCaseRunLink.run_id == run_id,
                RepairCaseRunLink.step_id == target.step_id,
                RepairCaseRunLink.outcome == outcome,
            )
        )
        if existing.first() is not None:
            continue

        session.add(
            RepairCaseRunLink(
                link_id=f"link-{uuid.uuid4().hex[:12]}",
                case_id=case_id,
                run_id=run_id,
                step_id=target.step_id,
                outcome=outcome,
                three_quote_basis=basis_of(proposal),
                linked_at=now,
            )
        )
    await session.commit()


def register_fleet_run_link_hook() -> None:
    """Arm the hook. Called wherever the fleet's executors are registered."""
    register_on_resolved(_VERTICAL, link_resolved_cases)
