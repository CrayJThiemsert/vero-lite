"""Row retention for fleet's visitor-opened repair cases (PLAN-0105 Step 1).

The row-side counterpart to ``services/engine/llm/prompt_log.rotate``. That one
deletes prompt-log day *files*; this one deletes case *rows*, their FK children,
and the case's upload directory on disk.

**Why a separate 90 rather than the prompt log's.** ADR-0035 D6's retention
regime is defined per request to a published LLM route and **does not reach case
text** (`docs/compliance/ropa-change-statement-fleet.md` §4(a)). PLAN-0105
LOCKED-1: this is an independent decision that happens to choose the same
number. A future D6 change changes nothing here, and vice versa — which is why
this module deliberately imports nothing from ``prompt_log`` and AC-9 guards
that absence rather than trusting it.

**Why the age anchor is ``opened_at``.** The row analogue of ``_file_date``
reading the day from the file NAME rather than its mtime: ``opened_at`` is
written once at case creation, carried inside the row, never updated by any code
path, and preserved byte-for-byte by a dump/restore. An mtime-shaped anchor
would let a volume remount silently resurrect an expired case's clock.

**Why files are deleted before rows** (PLAN-0105 SD-2, ruled (a)). If the row
went first and the unlink then failed, the bytes would be **unreachable AND
undeleted**: nothing points at ``stored_path`` any more, and no retry can find
them either, because the sweep finds expired cases *by row*. Files-first makes
that state unconstructible — a partial failure leaves the row intact, still
discoverable, and retried on the next pass.

**Never raises out of a case.** A retention pass that died on case #3 would
silently stop deleting cases #4 onward — the failure mode where the control
looks healthy and has simply stopped working. Per-case failures are recorded and
retried next pass (the ``rotate()`` contract).
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case import RepairCase
from services.db.repair_case_closeout import RepairCaseCloseout, RepairCaseOrderNumber
from services.db.repair_case_evidence import (
    RepairCaseAcceptedQuote,
    RepairCaseJustification,
    RepairCaseQuote,
)
from services.db.repair_case_run_link import RepairCaseRunLink
from services.db.repair_case_task import RepairCaseTaskEvent
from verticals.fleet_maintenance import case_projection

logger = logging.getLogger(__name__)

#: Rolling retention for visitor-opened case data. **Independent of ADR-0035 D6**
#: — see the module docstring (PLAN-0105 LOCKED-1). The coincidence with
#: ``prompt_log.RETENTION_DAYS`` is a coincidence, not an inheritance.
CASE_RETENTION_DAYS = 90

#: The six children holding a real ForeignKey to ``repair_case.case_id``, in
#: DELETION ORDER — children before the parent. Not one of them declares
#: ``ondelete`` (zero ``ondelete`` declarations exist in ``services/db/``), so a
#: bare parent delete raises ForeignKeyViolation rather than cascading. That
#: loud failure is a safety property PLAN-0105 SD-1 (ruled (b)) deliberately
#: keeps: a stray delete from some future code path still fails closed.
#:
#: 🔴 **The order is not cosmetic, and child-to-parent is not the only edge.**
#: ``repair_case_accepted_quote`` holds a composite FK to ``repair_case_quote``
#: (``tenant_id, case_id, quote_id``) as well as one to the root, so the accepted
#: quote MUST be deleted before the quote it points at. Deleting the quote first
#: raises ``ForeignKeyViolation`` on any case that ever accepted one — which is
#: every case that reached a gate. Found by the Step-6 scenario test on a real
#: intake; the Step-1 unit test could not see it, because it inserted a task event
#: and no quote pack. The child-to-child edges are asserted against the live
#: metadata by ``test_the_declared_order_respects_every_child_to_child_dependency``,
#: so a seventh child arriving with its own inter-child FK reddens rather than
#: waiting ninety days to raise in production.
_FK_CHILD_MODELS = (
    RepairCaseOrderNumber,
    RepairCaseCloseout,
    RepairCaseTaskEvent,
    RepairCaseJustification,
    RepairCaseAcceptedQuote,
    RepairCaseQuote,
)

#: The same six as an ORDERED tuple. Exported separately from the set below
#: because the two are checked against different things: membership against the
#: FKs pointing at the root, and ORDER against the FKs pointing between children.
#: A frozenset cannot carry the second property, and the day that mattered it
#: failed in production-shaped data rather than in a guard.
FK_CHILD_DELETION_ORDER: tuple[str, ...] = tuple(m.__tablename__ for m in _FK_CHILD_MODELS)

#: Table names of the above — the declared list AC-5's completeness guard reads
#: and asserts EQUAL to the FKs the live metadata actually declares.
FK_CHILD_TABLES: frozenset[str] = frozenset(FK_CHILD_DELETION_ORDER)

#: Tables referencing ``case_id`` with **no ForeignKey at all**, each with an
#: explicit policy. ``repair_case_run_link`` dropped its FK on purpose (s191 —
#: see that module's docstring), so deleting a case orphans its link rows
#: SILENTLY: no error, no cascade, nothing reddens. PLAN-0105 SD-4 ruled (a) —
#: RETAIN: no visitor free text rides that table, it is a governance-decision
#: record, and a missing referent lands in its already-measured degrade mode.
NO_FK_REFERENCERS: dict[str, str] = {
    RepairCaseRunLink.__tablename__: "RETAIN",
}

#: The root the sweep deletes from.
ROOT_TABLE: str = RepairCase.__tablename__


@dataclass(frozen=True)
class RetentionReport:
    """What one retention pass did — returned so a caller can log or assert on it.

    Three numbers rather than one: a pass where every case FAILED and a pass with
    nothing to delete both report zero deletions, and for a compliance control
    those are opposite conditions. The donor sweep makes the same point about its
    own counters — collapsing them would make a disarmed channel look like a
    quiet week (`services/db/task_chain_sweep.py:38-45`).

    ``failed_case_ids`` names cases; ``deleted`` only counts them. The asymmetry
    is deliberate — a failed case still EXISTS, so naming it is the pointer an
    operator needs. A deleted case does not, and a list of what we erased would
    be a residual record of exactly what the erasure was meant to remove.
    """

    cutoff: datetime
    expired_found: int = 0
    deleted: int = 0
    failed_case_ids: tuple[str, ...] = ()


def _remove_case_directory(photo_root: Path, case_id: str) -> None:
    """Delete a case's upload directory — photos AND quote attachments.

    ``_store_upload`` keys every upload under ``photo_root/<case_id>/``
    (`services/api/routers/cases.py:149-150`), and it is shared by the
    case-photo and quote-attachment routes, so the per-case directory is the
    case's COMPLETE disk footprint.

    A case that never carried an upload has no directory, and that is success,
    not failure — but any other OSError propagates. ``ignore_errors=True`` would
    swallow a real permission failure and let the caller delete the row anyway,
    manufacturing exactly the unreachable-and-undeleted state SD-2 exists to
    prevent.
    """
    target = photo_root / case_id
    try:
        shutil.rmtree(target)
    except FileNotFoundError:
        return


async def _refresh_projection(session: AsyncSession) -> None:
    """Re-read the in-memory case view after a deletion, fail-soft.

    ``case_projection`` serves from RAM, so rows deleted from Postgres keep
    being served until something refreshes it — a retention leak in memory that
    no DB assertion would catch. Same fail-soft contract the router uses
    (`services/api/routers/cases.py:105-108`): a projection hiccup must not turn
    a completed deletion into a raised error.
    """
    try:
        await case_projection.refresh(session)
    except Exception as exc:  # fail-soft — see the docstring
        case_projection.record_unavailable(str(exc))


async def delete_case(
    session: AsyncSession,
    case_id: str,
    *,
    photo_root: Path,
) -> None:
    """Erase ONE named case completely — uploads, then its six FK children, then the row.

    The per-case unit of work, callable on its own. :func:`sweep` selects its
    work set by AGE and can express nothing else; a DSR-on-request path needs
    the opposite — one named case, whatever its age — and this is the seam it
    calls. PLAN-0105's Out of Scope claimed that factoring already existed; until
    s232 it did not (the unit was inline in :func:`sweep`'s loop and reachable
    from nowhere), which that PLAN now records as `was an error`.

    **The ordering is load-bearing twice.** Files before rows (SD-2, ruled (a)):
    a row deleted first would leave bytes unreachable AND undeleted, because the
    sweep finds expired cases *by row*. Then, within the rows, children before
    the parent **and** ``repair_case_accepted_quote`` before the
    ``repair_case_quote`` it holds a composite FK to — see
    :data:`_FK_CHILD_MODELS`, where that edge and the production failure it
    caused are recorded.

    **Leaves the session CLEAN on failure** (Cray, typed, s232): a partial
    deletion is rolled back here and the exception re-raised. The alternative —
    propagating and letting the caller clean up — makes the extraction true in
    letter while leaving the exact trap it was meant to remove: a DSR caller
    holding a session in a failed transaction it never knew it had to reset.
    :func:`sweep` relies on this and no longer rolls back itself.

    **Does NOT refresh the projection.** A batch caller refreshes once per pass
    rather than once per case, so the refresh belongs to the caller (see
    :func:`sweep`). ⚠️ A DSR path deleting a single case must call
    :func:`_refresh_projection` itself, or ``case_projection`` keeps serving the
    erased case from RAM — a retention leak in memory that no DB assertion sees.
    """
    try:
        # Files FIRST (SD-2 ruling (a)) — see the module docstring.
        _remove_case_directory(photo_root, case_id)
        for model in _FK_CHILD_MODELS:
            # Table-level rather than ORM-level so one loop covers all six:
            # the models share no common base declaring ``case_id``, and the
            # column name is identical across them (verified per model).
            table = cast(sa.Table, model.__table__)
            await session.execute(sa.delete(table).where(table.c.case_id == case_id))
        await session.execute(sa.delete(RepairCase).where(RepairCase.case_id == case_id))
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def sweep(
    session: AsyncSession,
    *,
    photo_root: Path,
    now: datetime | None = None,
) -> RetentionReport:
    """Delete every case older than :data:`CASE_RETENTION_DAYS`, files first.

    One :func:`delete_case` per expired case, committed per case so a failure on
    one cannot roll back the cases already deleted. This function owns only the
    AGE selection, the per-case error accounting, and the single projection
    refresh; the erasure itself — and its ordering, its files-first rule and its
    rollback — belongs to :func:`delete_case`. Run-link rows are left standing
    (:data:`NO_FK_REFERENCERS`).
    """
    moment = now or datetime.now(UTC)
    cutoff = moment - timedelta(days=CASE_RETENTION_DAYS)

    expired: list[str] = list(
        (
            await session.execute(
                sa.select(RepairCase.case_id).where(RepairCase.opened_at < cutoff)
            )
        ).scalars()
    )

    deleted: list[str] = []
    failed: list[str] = []
    for case_id in expired:
        try:
            await delete_case(session, case_id, photo_root=photo_root)
        except Exception:
            # Never raises out of a case: the next case still gets its turn, and
            # this one is retried on the next pass. No rollback here — the unit
            # rolls back its own partial work (Cray, typed s232), so the session
            # handed to the NEXT iteration is already clean.
            logger.exception("case retention: case %s could not be deleted", case_id)
            failed.append(case_id)
            continue
        deleted.append(case_id)

    if deleted:
        await _refresh_projection(session)

    logger.info(
        "case retention: %d expired, %d deleted, %d failed (cutoff %s)",
        len(expired),
        len(deleted),
        len(failed),
        cutoff.isoformat(),
    )
    return RetentionReport(
        cutoff=cutoff,
        expired_found=len(expired),
        deleted=len(deleted),
        failed_case_ids=tuple(failed),
    )
