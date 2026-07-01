"""The Fastenal hero procedure for the LIVE run (PLAN-0045 Step 4b / C-2).

Reuses the **shipped, validated** ``emergency_sourcing_round`` procedure shape
(intake→judge→source→compliance→approve→issue_po→audit) and swaps **only** the approve step's
DOA ladder to the Fastenal ladder (English roles, ฿200,000 Manager ceiling) — so the live run
resolves the Fastenal ฿288,000 → ``CONTROLLER`` governance moment on real Fastenal data.

Built **in-code** (NOT a ``procedures.yaml`` entry): it does not pollute the procurement vertical's
procedure list (the read-only viewer test asserts exactly the two shipped procedures), it does not
touch ``services/engine/procedures/*``, and it reuses the shipped procedure's validated
steps / SoD / facets verbatim — only the authored ฿ ladder differs. The shipped procedure's SoD
(``intake`` requester ≠ ``approve`` approver) is unchanged; the Fastenal ladder's ``CONTROLLER``
role is what ``resolve_doa_tier`` picks, and the Fastenal principals bind both ``approver`` and
``CONTROLLER`` to the same Person (``appr-controller``), so the two resolve consistently.
"""

from __future__ import annotations

from decimal import Decimal

from services.engine.procedures.spec import (
    Agent,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    Person,
    Procedure,
    load_procedures,
)
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter

_APPROVE_STEP = "approve"
_PROCEDURE_ID = "fastenal_emergency_sourcing"


def fastenal_doa_ladder() -> DoaLadder:
    """The Fastenal DOA ladder (from ``approval_tier.csv``): THB, floors 0 / 15001 / 200001 /
    1000001 → SUPERVISOR / MANAGER / CONTROLLER / VP_OPERATIONS. The hero ฿288,000 crosses the
    ฿200,000 Manager ceiling into the CONTROLLER band."""
    return DoaLadder(
        currency="THB",
        tiers=[
            DoaTier(min_amount=Decimal("0"), approver_role="SUPERVISOR"),
            DoaTier(min_amount=Decimal("15001"), approver_role="MANAGER"),
            DoaTier(min_amount=Decimal("200001"), approver_role="CONTROLLER"),
            DoaTier(min_amount=Decimal("1000001"), approver_role="VP_OPERATIONS"),
        ],
        emergency_waiver=EmergencyWaiverPolicy(relaxes=["three_bid"], escalate_to="CONTROLLER"),
    )


def fastenal_hero_procedure() -> tuple[Procedure, Agent]:
    """Return the shipped ``emergency_sourcing_round`` with the Fastenal DOA ladder swapped into
    its approve step, plus its agent. Reuses the loaded (validated) procedure; ``model_copy``
    substitutes the approve step's ``governance_content`` and re-ids the procedure."""
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    ladder = fastenal_doa_ladder()
    new_steps = [
        step.model_copy(update={"governance_content": ladder})
        if step.step_id == _APPROVE_STEP
        else step
        for step in proc.steps
    ]
    fastenal = proc.model_copy(update={"procedure_id": _PROCEDURE_ID, "steps": new_steps})
    return fastenal, agent


async def load_fastenal_principals(adapter: FastenalCsvAdapter | None = None) -> list[Person]:
    """The Fastenal principals from ``person.csv`` (the SoD / DOA-approver identities)."""
    adapter = adapter or FastenalCsvAdapter()
    return [
        Person(person_id=row["person_id"], name=row["name"], roles=frozenset(row["roles"]))
        for row in await adapter.fetch_objects("Person")
    ]
