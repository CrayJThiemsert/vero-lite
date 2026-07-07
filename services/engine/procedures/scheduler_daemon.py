"""The long-lived scheduler daemon (ADR-0028 SD-1; PLAN-0055 Step 5, AC-11).

The net-new operational surface Phase B adds: a deployment entrypoint + a run loop that
periodically drives the pure :func:`fire_due_schedules` (Step 4) with ``now = wall-clock``,
a graceful SIGTERM shutdown (finish the in-flight tick, then exit — no torn writes), and
structured logging. It holds **NO scheduling logic** — the daemon is a thin loop; all policy
(due/skip/missed, SD-P2..P6) lives in the Step-4 function it calls.

Collaborators are INJECTED (a session factory, a schedule loader, a resolver, a clock, the
tick interval) so the daemon is unit-testable without real infra and stays MS-S1-independent
(the executor wiring lives behind the injected ``resolve``). :func:`load_all_schedules` is
the default DB loader; :func:`run_scheduler_daemon` is the programmatic entrypoint.
"""

from __future__ import annotations

import asyncio
import signal
from collections.abc import Awaitable, Callable, Sequence
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.scheduler import (
    FireOutcome,
    FireResult,
    ScheduleResolver,
    fire_due_schedules,
)
from services.engine.procedures.schedules import ScheduleState

SessionFactory = Callable[[], AsyncSession]
"""Opens a fresh :class:`AsyncSession` (used as an ``async with``) per tick — e.g. an
``async_sessionmaker`` instance."""

ScheduleLoader = Callable[[AsyncSession], Awaitable[Sequence[ScheduleState]]]
"""Loads the schedule set the daemon drives this tick (default :func:`load_all_schedules`)."""

Clock = Callable[[], datetime]
"""Returns the current instant — the ONLY wall-clock read in the whole scheduler; injectable
so a test drives the loop with a fixed clock."""

_log: structlog.stdlib.BoundLogger = structlog.get_logger("scheduler_daemon")


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def load_all_schedules(session: AsyncSession) -> Sequence[ScheduleState]:
    """The default loader: every persisted :class:`ScheduleState` (Step-6 recovery reads the
    same table). Ordered by ``schedule_id`` for a stable, testable fire order."""
    rows = await session.execute(sa.select(ScheduleState).order_by(ScheduleState.schedule_id))
    return list(rows.scalars().all())


class SchedulerDaemon:
    """A run loop that ticks :func:`fire_due_schedules` until asked to stop.

    Graceful shutdown: a SIGTERM/SIGINT (or :meth:`request_stop`) sets an event; the loop
    finishes the CURRENT tick and exits before the next one. A tick never fires mid-write —
    :func:`fire_due_schedules` commits per schedule — so a stop between fires loses nothing.
    A tick that raises is logged and swallowed, never killing the loop.
    """

    def __init__(
        self,
        *,
        session_factory: SessionFactory,
        load_schedules: ScheduleLoader = load_all_schedules,
        resolve: ScheduleResolver,
        interval_seconds: float = 60.0,
        clock: Clock = _utcnow,
        logger: Any = None,
    ) -> None:
        self._session_factory = session_factory
        self._load_schedules = load_schedules
        self._resolve = resolve
        self._interval = interval_seconds
        self._clock = clock
        self._log = logger if logger is not None else _log
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        """Ask the loop to exit after the current tick (idempotent)."""
        self._stop.set()

    async def tick(self) -> list[FireOutcome]:
        """One iteration: open a session, load the schedules, fire the due ones, log."""
        now = self._clock()
        async with self._session_factory() as session:
            schedules = await self._load_schedules(session)
            outcomes = await fire_due_schedules(session, schedules, now=now, resolve=self._resolve)
        fired = sum(1 for o in outcomes if o.result is FireResult.FIRED)
        skipped = sum(1 for o in outcomes if o.result is FireResult.SKIPPED_IN_FLIGHT)
        self._log.info(
            "scheduler.tick",
            now=now.isoformat(),
            evaluated=len(outcomes),
            fired=fired,
            skipped=skipped,
        )
        for o in outcomes:
            if o.result is FireResult.FIRED:
                self._log.info(
                    "scheduler.fired",
                    schedule_id=o.schedule_id,
                    run_id=o.run_id,
                    run_status=o.run_status,
                    missed=o.missed,
                )
            elif o.result is FireResult.SKIPPED_IN_FLIGHT:
                self._log.warning("scheduler.skipped_in_flight", schedule_id=o.schedule_id)
        return outcomes

    async def run(self) -> None:
        """Loop :meth:`tick` every ``interval_seconds`` until stopped (the entrypoint's body)."""
        self._install_signal_handlers()
        self._log.info("scheduler.start", interval_seconds=self._interval)
        try:
            while not self._stop.is_set():
                try:
                    await self.tick()
                except Exception:
                    # A single bad tick (a transient DB error, a malformed schedule) must
                    # never kill the daemon — log it and keep the loop alive.
                    self._log.exception("scheduler.tick_failed")
                await self._wait_next()
        finally:
            self._log.info("scheduler.stop")

    async def _wait_next(self) -> None:
        """Sleep the interval, waking immediately on a stop request (graceful between ticks)."""
        with suppress(TimeoutError):
            await asyncio.wait_for(self._stop.wait(), timeout=self._interval)

    def _install_signal_handlers(self) -> None:
        """Wire SIGTERM/SIGINT → :meth:`request_stop`. Best-effort: a platform/loop without
        signal support (Windows proactor, a non-main thread) is tolerated — the daemon is
        still stoppable via :meth:`request_stop` (the injected/test path)."""
        with suppress(NotImplementedError, RuntimeError, ValueError):
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self.request_stop)


async def run_scheduler_daemon(
    *,
    session_factory: SessionFactory,
    resolve: ScheduleResolver,
    load_schedules: ScheduleLoader = load_all_schedules,
    interval_seconds: float = 60.0,
) -> None:
    """Programmatic entrypoint (AC-11): construct + run a :class:`SchedulerDaemon` until it is
    signalled to stop. The deployment/CLI wiring (real vertical spec + executor factory behind
    ``resolve``) is the Step-7 ops posture."""
    daemon = SchedulerDaemon(
        session_factory=session_factory,
        load_schedules=load_schedules,
        resolve=resolve,
        interval_seconds=interval_seconds,
    )
    await daemon.run()
