"""Seed ONE persisted ``waiting_human`` repair-approval run for fleet's operate demo.

PLAN-0103 Step 7, under SD-5's ruling (a) (Cray, typed, s218): **seed one at boot AND
keep the visitor path.** Fleet's published set lands on Tab A but publishes Tab H
(Monitor), and until a visitor files a case at Tab I that Monitor opens EMPTY — the
first paint of the system whose whole pitch is "watch a decision get governed" showed
nothing being governed. This closes that, without removing the visitor path: the seed
supplies the first paint, the visitor still gets to watch their *own* case enter the
loop (AC-8's second clause).

**Why this is not a copy of procurement's seeder, and the difference is the point.**
``verticals.procurement.hero_demo.run.seed_operate_waiting_human_run`` must hand-build
an intake seed dict, because procurement's ``intake`` step declares no ``reads`` — its
QUERY slot is a hand-written ``_SeedQuery`` holding a cardinality-changing nest the v1
grammar cannot express. Fleet's ``intake`` **declares** ``input.reads`` + ``join`` +
``project`` (latest ``OperationalEvent`` per ``Truck`` with that truck's own
``minor_repair_ceiling_thb`` joined on), so it runs through the shipped
:class:`~services.engine.procedures.query_step.QueryStepExecutor` over the registry's
adapter. There is therefore **no seed to write here at all** — and no seam where a
hand-built fixture could disagree with what the procedure actually reads in production.
A declared procedure earns a shorter seeder, and it earns it without trading away the
truth of the data.

Contract, mirroring procurement's block by intent rather than by copy:

* **env-gated** — the caller checks ``settings.oct_demo_seed_operate``; this module is
  a plain coroutine and gates nothing itself;
* **idempotent** — a fixed ``run_id``; the caller skips when ``load_run`` already finds
  it, so a restart never piles up demo runs;
* **fail-soft at the call site** — a seed error must log and never block the demo boot;
  the Monitor then simply shows no run, which is the pre-Step-7 behaviour;
* **the SAME executors that resolve the gate** — taken from the registry rather than
  constructed here, so the run that parks and the resume that clears it cannot drift
  apart. The factory is registered immediately before this runs in the API lifespan.

The requester half of the SoD map (``{intake: req-mechanic-tom}``) is recorded on the
run by passing ``principal``, so a DISTINCT approver keeps SoD **governed** when the
gate is resolved — which is exactly the refused-then-granted moment fleet's card copy
promises a visitor.

Deterministic and host-state-free: the synthetic adapter, pure band math, pure AT-2
resolution, and the stubbed advisory prose the factory already wires (CLAUDE.md §8).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.orchestrator import ProcedureError, RunResult
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.runs import StepResultStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry

_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"
_APPROVE_STEP = "approve"

#: The head mechanic — fleet's authored requester (``procedures.yaml`` principals).
#: He holds no approver role, which is what makes the seeded gate refusable by him
#: and grantable by the fleet manager or the owner.
_REQUESTER_ID = "req-mechanic-tom"

#: The fixed demo run id. A constant, not a parameter default that callers vary:
#: idempotency is the whole point, and two ids would mean two demo runs.
DEMO_RUN_ID = "run-fleet-operate-demo"


async def seed_repair_gate_waiting_human_run(
    session: AsyncSession,
    *,
    run_id: str = DEMO_RUN_ID,
) -> RunResult:
    """Run ``governed_repair_approval`` to its ``approve`` gate and persist it parked.

    Returns the persisted :class:`RunResult` — reachable by ``GET /runs/{run_id}`` and
    counted by ``GET /runs``'s ``waiting_human_count``, which is what Tab H reads.

    Raises :class:`ProcedureError` if the run does **not** park at ``waiting_human``.
    That is deliberate and is not defensive noise: a run that completed instead of
    parking would leave the Monitor with nothing to act on while every status line
    still said "seeded", which is precisely the silent-success shape this PLAN keeps
    catching. The caller wraps this fail-soft, so the loud failure lands in the boot
    log rather than in a visitor's browser.
    """
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)
    requester = next(p for p in spec.principals if p.person_id == _REQUESTER_ID)

    # The registry's factory, not a local construction (see module docstring): the API
    # lifespan registers it one statement earlier, and every test that drives this must
    # do the same. A missing factory raises loudly here rather than silently seeding a
    # run the resolve endpoint would then 409 on.
    executors = registry.get_procedure_executors(_VERTICAL)()

    result = await run_procedure_persisted(
        session,
        procedure,
        agent,
        executors,
        vertical=_VERTICAL,
        run_id=run_id,
        trigger_context={
            "source": "operate-demo-seed",
            "triggered_by": requester.person_id,
            # NOTE: no ``subject`` ref, unlike procurement's seed. Procurement can name
            # its asset because it hand-builds the intake seed; fleet's breaching truck
            # is chosen by the declared query DURING the run, so it is not knowable
            # before it. The Monitor row simply carries no subject — ``_resolve_subject``
            # already handles that — and inventing one here would mean asserting an
            # asset the run had not yet picked.
        },
        principal=requester,
    )

    approve = next((s for s in result.step_results if s.step_id == _APPROVE_STEP), None)
    if approve is None or approve.status != StepResultStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"fleet operate-demo seed {run_id!r}: the {_APPROVE_STEP!r} gate did not park at "
            f"waiting_human (status {approve.status if approve else None!r}) — Tab H would "
            "open empty while the boot log reported a seeded run"
        )
    return result
