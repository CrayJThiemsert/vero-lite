"""Return fleet's published demo to its pristine two-run state (PLAN-0110 Steps 3-4).

**The defect this exists for.** ``services/api/main.py:307`` skips the operate seed
whenever the run row EXISTS, in any state. The gate-resolve route is on the published
system's ingress allowlist and personas ship with keys, so a visitor resolving the gate
is the *designed* interaction — and it is consumable exactly once per deployment. The
first visitor who plays the refused-then-granted beat consumes it for every visitor
after them, and the seed never re-arms. This module makes the seed able to REBUILD;
it does not invent a new end state. The target is precisely what a fresh boot already
produces since PR #1209: one run parked at ``approve``, one completed through both
gates.

**Where it runs (SD-C, RULED AGAINST the drafter's recommendation — Cray, typed,
2026-08-18 s237).** Not at boot. A container crash-restart would then also reset, and a
visitor mid-beat at that moment would lose the half-played run — Cray ruled that a
deletion on a public system happens only under a human's explicit action. The priced
cost is real and is not hidden: a beat consumed on day 1 with the next deploy three
weeks out means **three degraded weeks**, and nothing self-heals. The two mitigations
are (1) :func:`read_demo_state`'s ``DEMO-STATE:`` token, so the degraded state is
observable any day without deploying, and (2) the operator procedure in this system's
own profile directory (``DEMO-RESET.md``), which the shared redeploy runbook points at
generically. ⚠️ It lives with the profile rather than in the runbook because a
vero-lite file naming two published systems is a shadow ingress map (ADR-0036 D2,
enforced by ``tests/deploy/test_published_profiles.py``) and the commands must carry a
literal compose path to be runnable — measured here: writing them into the runbook
reddened that guard.

**Where it does NOT attach, and why that is a constraint rather than a preference
(G11).** ``deploy/published/deploy.py`` serves ``oct-energy`` ONLY, by Cray's typed
s219 decision recorded in that module's own header, with ``--system`` parameterization
explicitly deferred and ``tests/deploy/test_deploy.py:44-47`` pinning it. Adding a
fleet step there would force the deferred decision as a side effect and widen a
deliberate test pin. So the operator entry point is the ``__main__`` guard at the
bottom of THIS module, baked into the app image and invoked via ``compose exec`` — on
the container's own ``DATABASE_URL`` and ``OCT_VERTICAL``, so it aims at the right
database by construction and no credential leaves the deployed system.

🔴 **Transaction scope — a deliberate, stated divergence from the PLAN's wording.**
PLAN-0110 Step 3 says "in one transaction" and reuses ``repair_case_retention.
delete_case`` for the two demo cases. Those two are **incompatible**: ``delete_case``
owns its own commit and its own rollback by design (PLAN-0105 s232 made that its
contract — "leaves the session CLEAN on failure"), so calling it can never be enclosed
in an outer transaction. Re-implementing its six-child ordering here to get one commit
was rejected — that ordering already cost PLAN-0105 a production-shaped failure, and a
second copy is a second chance to disagree about it. What ships instead:

* the RUN-side deletion (step results, link rows, run rows) is one transaction that
  this module owns, rolling back whole on any error;
* the CASE erasure is ``delete_case``'s own unit, one per case, each atomic in itself;
* **runs are deleted BEFORE cases**, which is the ordering under which a failure
  between the units leaves a state the seeds can still act on; and
* the whole reset is **idempotent** — deleting absent rows is a no-op — so the
  recovery from any partial failure is to run it again, and
  :func:`read_demo_state` says whether that is still needed.

The guarantee is therefore "each unit is atomic, and a partial failure is re-runnable
and observable", NOT "one global transaction". Stated here because a reader who
believed the stronger claim would skip the re-check that actually makes this safe.

**The audit chain is never touched.** ``audit_log.run_id`` is a plain nullable ``Text``
with **no ForeignKey**, and ``verify_chain`` walks only audit rows by ``audit_id`` — it
never reads runs. Deleting a run leaves the chain intact and leaves the audit record of
that run standing. One sentence for the demo: *the demo resets; the audit log
remembers.*
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy import CursorResult, Delete
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case_run_link import RepairCaseRunLink
from services.engine.procedures.persistence import load_run
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from verticals.fleet_maintenance.operate_seed import (
    DEMO_CASE_ID,
    DEMO_HISTORY_CASE_ID,
    DEMO_HISTORY_RUN_ID,
    DEMO_RUN_ID,
)

#: The vertical this reset is allowed to run against. A deployment serving any other
#: vertical refuses — the fixed ids below are fleet's, and a hand-typed invocation on
#: the wrong host is exactly the failure an operator-invoked step can produce.
DEMO_VERTICAL = "fleet_maintenance"

#: The gate the pristine live run must be parked at. Status alone is NOT sufficient:
#: a run parked at ``fulfill`` is also ``waiting_human`` (``governed_repair_approval``
#: is a ``request -> approve -> fulfill`` spine whose TERMINAL step is itself gated),
#: and that state is a CONSUMED beat, not a pristine one.
PRISTINE_SUSPENDED_STEP = "approve"

#: CONSTANTS, never parameters. Idempotency and scope are the whole point: a
#: parameterized id set would let one mistyped argument aim this at a visitor's row.
DEMO_RUN_IDS: tuple[str, ...] = (DEMO_RUN_ID, DEMO_HISTORY_RUN_ID)
DEMO_CASE_IDS: tuple[str, ...] = (DEMO_CASE_ID, DEMO_HISTORY_CASE_ID)

#: The tables holding a real ForeignKey to ``pipeline_runs.run_id``, in DELETION
#: ORDER — children before the parent. ``step_results.run_id`` declares no
#: ``ondelete`` (``runs.py:133``), so a bare parent delete raises ForeignKeyViolation
#: rather than cascading, and that loud failure is kept as the backstop exactly as
#: PLAN-0105 SD-1 kept it for cases.
_FK_CHILD_MODELS = (StepResult,)

#: Read by the AC-6 completeness guard, which compares it against the FKs the LIVE
#: SQLAlchemy metadata declares — never against a copy of this list. A future second
#: child of ``pipeline_runs`` added without updating this reddens the guard instead
#: of leaving rows behind and then failing on the parent delete in production.
FK_CHILD_DELETION_ORDER: tuple[str, ...] = tuple(m.__tablename__ for m in _FK_CHILD_MODELS)
FK_CHILD_TABLES: frozenset[str] = frozenset(FK_CHILD_DELETION_ORDER)

#: The root this reset deletes from.
ROOT_TABLE: str = PipelineRun.__tablename__

#: Tables referencing ``run_id`` with **no ForeignKey at all**, each with an explicit
#: policy — the shape that fails SILENTLY and so cannot be found by walking FK
#: declarations backwards (PLAN-0105 AC-5's lesson, applied to the run graph).
#:
#: 🔴 ``repair_case_run_link`` is DELETED here, which is a surfaced divergence from
#: PLAN-0105 SD-4's ratified RETAIN — granted by Cray (typed, s237) for this sub-case
#: only. SD-4 governed the retention SWEEP, where a deleted case id never returns and
#: the orphan lands in a measured silent-degrade mode. This reset **reuses** ids, and
#: id reuse is precisely the condition under which RETAIN stops being safe: a prior
#: deployment's visitor decisions would otherwise re-attach to the rebuilt case as
#: decisions nobody in this deployment made, and land on the month-end report as
#: audit answers with no author.
#:
#: ``audit_log`` also references ``run_id`` with no FK and is **never** deleted (see
#: the module docstring).
NO_FK_REFERENCERS: dict[str, str] = {
    RepairCaseRunLink.__tablename__: "DELETE (SD-D, id-reuse sub-case)",
    "audit_log": "RETAIN — never deleted; the chain outlives every reset",
}

#: The two literals the operator (or a runbook check) reads. Constants rather than
#: inline f-string fragments so the scenario test asserts the SAME strings the module
#: prints — a token the test spells out itself could drift from the one that ships.
STATE_PRISTINE = "PRISTINE"
STATE_CONSUMED = "CONSUMED"
VERDICT_PREFIX = "DEMO-STATE:"


@dataclass(frozen=True)
class DemoResetReport:
    """What one invocation did — returned so a caller can assert on it, printed so an
    operator can read it.

    ``state_before`` and ``executed`` are separate fields rather than one status,
    because "already pristine, nothing to do" and "plan mode, refused to act" are
    opposite conditions that both delete zero rows.
    """

    state_before: str
    executed: bool
    refused: str | None = None
    deleted: dict[str, int] = field(default_factory=dict)

    @property
    def verdict_line(self) -> str:
        """The AC-11 token. An echoed exit code is corruptible through a shell chain;
        a printed token the reader greps for is not — and its ABSENCE means the module
        never ran, which makes the ``python -m`` silent-no-op hazard detectable by
        construction."""
        return f"{VERDICT_PREFIX} {self.state_before}"


async def read_demo_state(session: AsyncSession) -> str:
    """``PRISTINE`` when both demo runs match the boot-fresh shape, else ``CONSUMED``.

    The pristine read is deliberately STRICTER than a status comparison:

    * ``run-fleet-operate-demo`` must be ``waiting_human`` **and suspended at
      ``approve``**. A run whose ``approve`` gate a visitor already resolved parks
      again at ``fulfill`` — still ``waiting_human``, still in the visitor's queue,
      and no longer offering the beat. Status alone cannot tell those apart.
    * ``run-fleet-demo-history`` must be ``completed``.

    A MISSING run reads ``CONSUMED``, not pristine: an empty demo is not a ready one,
    and the honest answer to "can a visitor play the beat" is no.
    """
    live = await load_run(session, DEMO_RUN_ID)
    if live is None or live.run.status != PipelineRunStatus.WAITING_HUMAN.value:
        return STATE_CONSUMED
    waiting = [s for s in live.step_results if s.status == StepResultStatus.WAITING_HUMAN.value]
    if len(waiting) != 1 or waiting[0].step_id != PRISTINE_SUSPENDED_STEP:
        return STATE_CONSUMED
    if not (waiting[0].artifact or {}).get("output_set"):
        return STATE_CONSUMED

    history = await load_run(session, DEMO_HISTORY_RUN_ID)
    if history is None or history.run.status != PipelineRunStatus.COMPLETED.value:
        return STATE_CONSUMED
    return STATE_PRISTINE


async def _delete_run_side(session: AsyncSession) -> dict[str, int]:
    """The one transaction this module owns: step results, link rows, then the runs.

    Children before the parent (the FK has no ``ondelete``), and the link rows are
    cleared on BOTH keys — by ``run_id`` for this deployment's decisions and by
    ``case_id`` so a row written against a rebuilt case id cannot survive into the
    next generation of the demo.
    """
    deleted: dict[str, int] = {}

    async def _count(statement: Delete) -> int:
        # ``AsyncSession.execute`` is typed ``Result[Any]``, which declares no
        # ``rowcount``; a DML statement always returns a ``CursorResult``, which does.
        # Narrowed here once rather than at each of the three call sites.
        result = cast("CursorResult[Any]", await session.execute(statement))
        return result.rowcount or 0

    try:
        for model in _FK_CHILD_MODELS:
            table = cast(sa.Table, model.__table__)
            deleted[table.name] = await _count(
                sa.delete(table).where(table.c.run_id.in_(DEMO_RUN_IDS))
            )

        link = cast(sa.Table, RepairCaseRunLink.__table__)
        deleted[link.name] = await _count(
            sa.delete(link).where(
                sa.or_(
                    link.c.run_id.in_(DEMO_RUN_IDS),
                    link.c.case_id.in_(DEMO_CASE_IDS),
                )
            )
        )

        runs = cast(sa.Table, PipelineRun.__table__)
        deleted[runs.name] = await _count(sa.delete(runs).where(runs.c.run_id.in_(DEMO_RUN_IDS)))

        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return deleted


async def reset_demo_runs(
    session: AsyncSession,
    *,
    photo_root: Path,
    execute: bool = False,
    vertical: str | None = None,
) -> DemoResetReport:
    """The entry point. PLAN mode by DEFAULT — it deletes nothing unless asked.

    Copied from ``deploy/published/deploy.py``'s own safety pattern (`:36-41`): the
    default invocation reads and reports, and deletion requires an explicit
    ``execute=True``. That default matters more here than it does there, because this
    is invoked by hand against a live public system where a mistyped target is a
    realistic failure.

    Two guards, both fail-closed, both returning a report rather than raising — a
    refusal an operator can read beats a traceback they have to interpret:

    * ``execute`` unset → nothing is deleted, the token is printed, done.
    * ``vertical`` (defaulting to the deployment's own ``OCT_VERTICAL``) is not
      ``fleet_maintenance`` → refuse. The ids below are fleet's; running them
      against another system's database would be a delete aimed at nothing in the
      best case and at a collision in the worst.

    ``photo_root`` is a required parameter rather than resolved here: this module sits
    in ``services/db/`` and must not import the API's router layer to learn a path.
    The ``__main__`` block below resolves it and passes it in.
    """
    state = await read_demo_state(session)
    if not execute:
        return DemoResetReport(state_before=state, executed=False)

    # Imported lazily: ``settings`` is the API's config object and this module is
    # importable by DB-side callers that have no reason to construct it.
    from services.api.config import settings

    active = vertical if vertical is not None else settings.oct_vertical
    if active != DEMO_VERTICAL:
        return DemoResetReport(
            state_before=state,
            executed=False,
            refused=(
                f"refusing: this reset owns {DEMO_VERTICAL!r}'s fixed demo ids and the "
                f"deployment serves {active!r}"
            ),
        )

    # Runs FIRST, then cases — see the module docstring on why this ordering is the
    # one under which a failure between the two units stays re-runnable.
    deleted = await _delete_run_side(session)

    from services.db.repair_case_retention import delete_case

    for case_id in DEMO_CASE_IDS:
        await delete_case(session, case_id, photo_root=photo_root)
    deleted["repair_case"] = len(DEMO_CASE_IDS)

    return DemoResetReport(state_before=state, executed=True, deleted=deleted)


async def _main(execute: bool) -> int:
    """The operator path. Resolves the app's own session + photo root, prints, exits."""
    from services.api.routers.cases import photo_root
    from services.db.session import async_session

    async with async_session() as session:
        report = await reset_demo_runs(session, photo_root=photo_root(), execute=execute)

    print(report.verdict_line)
    if report.refused is not None:
        print(report.refused)
        return 2
    if not report.executed:
        print("plan mode — nothing deleted. Re-run with --execute to reset.")
        return 0
    for table, count in sorted(report.deleted.items()):
        print(f"deleted {count} row(s) from {table}")
    print(
        "reset complete. The seeds rebuild only in the app's BOOT lifespan — "
        "recreate or restart the app now, or the demo stays empty until it next boots."
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m services.db.demo_run_reset",
        description=(
            "Reset fleet's published demo to its pristine two-run state. "
            "Plan mode by default: prints DEMO-STATE: PRISTINE|CONSUMED and deletes "
            "nothing. Run inside the app container so it uses that container's own "
            "DATABASE_URL and OCT_VERTICAL."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually delete the demo runs and cases (default: plan only)",
    )
    raise SystemExit(asyncio.run(_main(parser.parse_args().execute)))
