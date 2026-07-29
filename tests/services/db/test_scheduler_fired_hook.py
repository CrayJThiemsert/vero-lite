"""The daemon's post-fire hook — the seam that keeps ``pm_due`` wired (AC-8, amended).

A producer nothing calls is a producer that does not exist. ``pm_due`` reads a fired
round and pushes to กลุ่มช่าง, but the thing that has to invoke it every morning is
the scheduler daemon — and the daemon is deliberately vertical-agnostic ("holds NO
scheduling logic"), so it cannot import fleet code to do it.

These cases pin both halves of the resolution: the daemon calls an INJECTED hook for
each fired schedule, and the CLI resolves the fleet producer as that hook. Without
the second half the seam looks correct in every daemon test and does nothing in
production — the shape of bug PLAN-0090 already paid for once, when the daemon's
factory dispatch was procurement-hardcoded and fleet raised at startup.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from services.engine.procedures.scheduler import FireOutcome, FireResult
from services.engine.procedures.scheduler_daemon import SchedulerDaemon


class _StubSession:
    async def __aenter__(self) -> _StubSession:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None


def _outcome(result: FireResult, *, run_id: str, schedule_id: str) -> FireOutcome:
    return FireOutcome(
        schedule_id=schedule_id,
        result=result,
        run_id=run_id,
        run_status="waiting_human",
        scheduled_for=datetime(2026, 7, 7, 6, 0, tzinfo=UTC),
        missed=False,
    )


async def _noop_schedules(_session: Any) -> list[Any]:
    return []


async def _never_notify(**_: object) -> bool:  # pragma: no cover - guard, not behaviour
    raise AssertionError("the missed-round notifier must not fire in these cases")


@pytest.fixture
def daemon_firing(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build a daemon whose tick yields exactly the outcomes a case declares.

    ``fire_due_schedules`` is stubbed through ``monkeypatch`` so it is restored
    even when a case fails — these cases are about the HOOK, and a real fire would
    drag a database and a vertical spec into a question that is neither.
    """

    def _build(outcomes: list[FireOutcome], hook: Any) -> SchedulerDaemon:
        async def _fire(*_: object, **__: object) -> list[FireOutcome]:
            return outcomes

        monkeypatch.setattr("services.engine.procedures.scheduler_daemon.fire_due_schedules", _fire)
        return SchedulerDaemon(
            session_factory=_StubSession,  # type: ignore[arg-type]
            load_schedules=_noop_schedules,  # type: ignore[arg-type]
            resolve=lambda *_a, **_k: None,  # type: ignore[arg-type,return-value]
            on_fired=hook,
            notify=_never_notify,
        )

    return _build


# --------------------------------------------------------------------------- #


async def test_a_fired_schedule_reaches_the_hook_with_its_run_id(daemon_firing: Any) -> None:
    """The morning round's run id is what the producer needs; nothing else is."""
    seen: list[str] = []

    async def hook(_session: Any, outcome: FireOutcome) -> None:
        seen.append(str(outcome.run_id))

    daemon = daemon_firing(
        [_outcome(FireResult.FIRED, run_id="run-morning", schedule_id="fleet:pm")], hook
    )
    await daemon.tick()

    assert seen == ["run-morning"]


async def test_a_schedule_that_did_not_fire_never_reaches_the_hook(daemon_firing: Any) -> None:
    """A skipped-in-flight or recovered outcome produced no NEW round.

    Reacting to one would announce trucks twice — the second push naming a set
    somebody already acted on, which is how a group learns the channel repeats
    itself and stops reading it.
    """
    seen: list[str] = []

    async def hook(_session: Any, outcome: FireOutcome) -> None:
        seen.append(str(outcome.run_id))

    daemon = daemon_firing(
        [
            _outcome(FireResult.SKIPPED_IN_FLIGHT, run_id="run-a", schedule_id="fleet:pm"),
            _outcome(FireResult.ALREADY_FIRED, run_id="run-b", schedule_id="fleet:pm"),
        ],
        hook,
    )
    await daemon.tick()

    assert seen == []


async def test_a_hook_that_raises_does_not_lose_the_tick_s_outcomes(daemon_firing: Any) -> None:
    """The run is already recorded before the hook runs.

    If a notification failure could unwind or hide it, a LINE outage would look
    like the scheduler stopped working — turning a cosmetic problem into an
    operational one.
    """

    async def hook(_session: Any, _outcome: FireOutcome) -> None:
        raise RuntimeError("LINE is down")

    daemon = daemon_firing(
        [_outcome(FireResult.FIRED, run_id="run-morning", schedule_id="fleet:pm")], hook
    )
    outcomes = await daemon.tick()

    assert [o.run_id for o in outcomes] == ["run-morning"]


async def test_one_failing_hook_does_not_starve_the_next_schedule(daemon_firing: Any) -> None:
    """Two verticals fire in the same tick; the second must still be reacted to."""
    seen: list[str] = []

    async def hook(_session: Any, outcome: FireOutcome) -> None:
        if outcome.run_id == "run-first":
            raise RuntimeError("boom")
        seen.append(str(outcome.run_id))

    daemon = daemon_firing(
        [
            _outcome(FireResult.FIRED, run_id="run-first", schedule_id="a:one"),
            _outcome(FireResult.FIRED, run_id="run-second", schedule_id="b:two"),
        ],
        hook,
    )
    await daemon.tick()

    assert seen == ["run-second"]


async def test_a_daemon_with_no_hook_still_ticks(daemon_firing: Any) -> None:
    """Most verticals have no reaction; the absence must be free, not a special case."""
    daemon = daemon_firing(
        [_outcome(FireResult.FIRED, run_id="run-morning", schedule_id="x:one")], None
    )
    outcomes = await daemon.tick()

    assert [o.result for o in outcomes] == [FireResult.FIRED]


# --------------------------------------------------------------------------- #
# The wiring half — what makes the seam real in production
# --------------------------------------------------------------------------- #


def test_the_fleet_vertical_resolves_to_the_pm_due_producer() -> None:
    """The CLI must actually hand the fleet producer to the daemon.

    This is the assertion that would have caught an unwired seam. Everything above
    passes with ``_FIRED_HOOKS`` empty — the daemon would faithfully call a hook
    that production never supplies, and the 06:00 push would simply never happen.
    """
    from services.engine.cli import _FIRED_HOOKS, _fired_hook_for

    assert _FIRED_HOOKS["fleet_maintenance"] == (
        "services.db.pm_due_notify",
        "notify_pm_due_for_run",
    )
    assert _fired_hook_for("fleet_maintenance") is not None


def test_a_vertical_with_no_reaction_resolves_to_nothing() -> None:
    """Procurement and the rest get no hook — the correct default, asserted so a
    future blanket hook is a deliberate act."""
    from services.engine.cli import _fired_hook_for

    assert _fired_hook_for("procurement") is None
