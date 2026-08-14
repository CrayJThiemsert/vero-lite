"""The periodic case-retention task (PLAN-0105 Steps 2-3).

Drives :func:`services.db.repair_case_retention.sweep` on a schedule from inside
the application process.

**Why in-app and not a host scheduler** (PLAN-0105 LOCKED-3, Cray typed
2026-08-14). A Windows Task Scheduler entry or a cron line on MS-S1 is a
host-state change (CLAUDE.md §8), lives outside the repo, and does not follow a
redeploy — the retention control would silently stop existing the first time the
box is rebuilt. An in-app task ships with the image. It is the same conclusion
``prompt_log`` reached from the same premise ("there is no cron on the published
box") and solved a different way, on the write path; a retention sweep has no
write path to ride, so it takes a task instead.

**Boot-anchored, then periodic.** One sweep runs immediately at startup and then
every :data:`CASE_RETENTION_SWEEP_HOURS`. The boot sweep is not belt-and-braces:
a box that restarts more often than the interval would otherwise never complete
a cycle, and the published demo is exactly such a box.

**Both gates live HERE, so the call site spends no branch at all** — the
``_seed_fleet_operate_demo`` shape (`services/api/main.py:245`, `:258-262`).
``lifespan`` sits exactly at the C901 complexity ceiling, so an ``if`` at the
call site reddens ruff. This is a real constraint, not a style preference.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from services.api.config import settings
from services.db.repair_case_retention import RetentionReport, sweep
from services.db.session import async_session

logger = logging.getLogger(__name__)

#: How often the sweep repeats after the boot-anchored first pass. Retention is
#: a 90-day rule, so the interval only has to be small relative to a day —
#: daily keeps the deletion within a day of its due date without making the
#: published box do meaningless work.
CASE_RETENTION_SWEEP_HOURS = 24

#: The vertical whose published system carries a database, and the only one with
#: visitor-writable case rows to retain (PLAN-0103 LOCKED-1 / ADR-0037).
_RETENTION_VERTICAL = "fleet_maintenance"


def _photo_root() -> Path:
    """Resolve the upload directory the sweep must clear.

    Lazily imported from the router that WRITES those files, rather than
    re-deriving the path from settings here. Two derivations of one path are two
    chances to disagree, and disagreeing here means the sweep confidently
    deletes an empty directory while the real bytes stay on disk.
    """
    from services.api.routers.cases import photo_root

    return photo_root()


async def _sweep_once() -> RetentionReport:
    """One pass, on its own session."""
    async with async_session() as session:
        return await sweep(session, photo_root=_photo_root())


async def _retention_loop() -> None:
    """Sweep at boot, then every :data:`CASE_RETENTION_SWEEP_HOURS`.

    Fail-soft per iteration, including an unreachable database — the published
    demo must keep serving when Postgres is down (the DB-less boot contract,
    `services/api/main.py:460-463`), and a retention pass that raised into the
    task would kill the loop and take every FUTURE pass with it. That is the
    failure this shape exists to prevent: not one missed deletion, but a control
    that stops running while everything else looks healthy.

    ``asyncio.CancelledError`` inherits ``BaseException``, so ``except
    Exception`` below does NOT swallow it — cancellation still stops the loop
    promptly, which is what :func:`stop_case_retention` depends on.
    """
    while True:
        try:
            report = await _sweep_once()
            logger.info(
                "case-retention sweep: %d expired, %d deleted, %d failed",
                report.expired_found,
                report.deleted,
                len(report.failed_case_ids),
            )
        except Exception as exc:  # fail-soft — see the docstring
            logger.warning("case-retention sweep skipped (error): %s", exc)
        await asyncio.sleep(CASE_RETENTION_SWEEP_HOURS * 3600)


def start_case_retention(vertical: str) -> asyncio.Task[None] | None:
    """Start the retention loop, or return ``None`` when it does not apply.

    Inert by CONSTRUCTION off fleet, not by an unreachable database: energy and
    procurement are DB-less, so a sweep there would fail rather than no-op, and
    "it errors harmlessly" is not the same guarantee as "it never runs".
    """
    if vertical != _RETENTION_VERTICAL or not settings.case_retention_enabled:
        return None
    logger.info("case retention ARMED: sweeping at boot and every %d h", CASE_RETENTION_SWEEP_HOURS)
    return asyncio.create_task(_retention_loop())


async def stop_case_retention(handle: asyncio.Task[None] | None) -> None:
    """Cancel the loop and wait for it to finish unwinding.

    Awaiting the cancellation rather than firing and forgetting: a task still
    holding a DB session while the engine disposes at shutdown produces a
    confusing error on a perfectly healthy shutdown path.
    """
    if handle is None:
        return
    handle.cancel()
    try:
        await handle
    except asyncio.CancelledError:
        pass
