"""PLAN-0105 Steps 2-3 — the periodic retention task's lifecycle (AC-6, AC-7, AC-8).

⚠️ **Scope boundary, stated so nothing here is mistaken for AC-10.** The seam under
test is the TASK: its gating, its boot-anchored first pass, its fail-soft loop, and
its cancellation. ``_sweep_once`` is substituted in the lifecycle cases because the
sweep is not what these assert — it has its own DB-backed tests
(`tests/services/db/test_case_retention.py`), and the real producer driven into the
real consumer on realistic data is Step 6's scenario test (CLAUDE.md §8). A lifecycle
test that also drove Postgres would prove neither thing more strongly.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from services.api import case_retention_task
from services.api.case_retention_task import start_case_retention, stop_case_retention
from services.api.config import settings
from services.db.repair_case_retention import RetentionReport

_NOW = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)


@pytest.fixture
def armed(monkeypatch: pytest.MonkeyPatch) -> None:
    """The flag on. The vertical is still the caller's to pass — the two gates are
    independent and every test below turns exactly one of them off at a time."""
    monkeypatch.setattr(settings, "case_retention_enabled", True)


def test_ac8_the_flag_is_off_by_default() -> None:
    """The default is the whole safety story: this task DELETES data, so a dev box, a
    CI run, or a pilot deployment must never acquire it by inheriting an engine
    default. Only fleet's published profile opts in."""
    assert settings.case_retention_enabled is False


async def test_ac8_inert_when_the_flag_is_off() -> None:
    """⚠️ ``async`` deliberately, though nothing here awaits — see the sibling below."""
    assert start_case_retention("fleet_maintenance") is None


async def test_ac8_inert_on_a_db_less_vertical_even_with_the_flag_on(armed: None) -> None:
    """Inert by CONSTRUCTION, not by an unreachable database.

    energy and procurement are DB-less, so a sweep there would ERROR rather than
    no-op — and "it fails harmlessly" is a different guarantee from "it never runs".
    Asserted for both, because a gate that happened to match only one vertical name
    would pass a single-vertical check.

    ⚠️ **``async`` on purpose, and the reason is a probe finding.** As a sync test
    this still caught a removed gate — but by CRASHING on ``asyncio.create_task``
    with ``RuntimeError: no running event loop``, which tells a future reader
    nothing about retention. With a loop running, the gate's removal surfaces as
    this test's own assertion instead. A guard that fails for an incidental reason
    is a guard whose RED nobody can act on.
    """
    assert start_case_retention("energy") is None
    assert start_case_retention("procurement") is None


async def test_ac6_the_boot_sweep_runs_without_waiting_for_the_interval(
    armed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A box that restarts more often than the interval must still enforce retention.

    Waited on an Event rather than a sleep: a poll would pass on a slow machine for
    the wrong reason, and the property under test is "before the interval", not
    "within N milliseconds".
    """
    swept = asyncio.Event()

    async def _fake_sweep() -> RetentionReport:
        swept.set()
        return RetentionReport(cutoff=_NOW, expired_found=3, deleted=3)

    monkeypatch.setattr(case_retention_task, "_sweep_once", _fake_sweep)

    handle = start_case_retention("fleet_maintenance")
    assert handle is not None, "both gates open — the task must exist"
    try:
        await asyncio.wait_for(swept.wait(), timeout=5)
    finally:
        await stop_case_retention(handle)


async def test_ac6_a_failing_sweep_does_not_kill_the_loop(
    armed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The failure this shape exists to prevent is not one missed deletion — it is a
    control that stops running while everything else looks healthy. If the raise
    escaped, the task would die and every FUTURE pass would be lost silently."""
    raised = asyncio.Event()

    async def _exploding_sweep() -> RetentionReport:
        raised.set()
        raise RuntimeError("simulated: the database is unreachable")

    monkeypatch.setattr(case_retention_task, "_sweep_once", _exploding_sweep)

    handle = start_case_retention("fleet_maintenance")
    assert handle is not None
    try:
        await asyncio.wait_for(raised.wait(), timeout=5)
        # Hand the loop enough turns to die if it were going to.
        for _ in range(5):
            await asyncio.sleep(0)
        assert not handle.done(), "the loop survived the error and is waiting for the next pass"
    finally:
        await stop_case_retention(handle)


async def test_stop_cancels_the_loop_and_waits_for_it(
    armed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Awaited cancellation, not fire-and-forget: a task still holding a session while
    the engine disposes turns a healthy shutdown into a confusing error."""
    swept = asyncio.Event()

    async def _fake_sweep() -> RetentionReport:
        swept.set()
        return RetentionReport(cutoff=_NOW)

    monkeypatch.setattr(case_retention_task, "_sweep_once", _fake_sweep)

    handle = start_case_retention("fleet_maintenance")
    assert handle is not None
    await asyncio.wait_for(swept.wait(), timeout=5)

    await stop_case_retention(handle)
    assert handle.done(), "stop() returns only once the loop has actually unwound"


async def test_stop_on_a_disarmed_start_is_a_no_op() -> None:
    """``start`` returns None wherever retention does not apply, so the unconditional
    call site in ``lifespan`` hands None straight back to ``stop``. If that raised, the
    zero-branch wiring (AC-7) would be impossible and the shutdown path would break on
    every non-fleet deployment."""
    await stop_case_retention(None)


def test_ac7_lifespan_gained_no_branch_for_retention() -> None:
    """AC-7, asserted against the ARTIFACT rather than trusting review.

    Reads ``lifespan``'s own source and requires both retention calls to sit at
    statement level — not nested inside an ``if``. ``lifespan`` sits exactly at the
    C901 ceiling (its own comments say so), so a branch added here reddens ruff for a
    reason that has nothing to do with retention, and the fix would be to gate inside
    the helper, never to raise the ceiling.
    """
    import ast
    import inspect

    from services.api import main

    source = inspect.getsource(main.lifespan.__wrapped__)  # type: ignore[attr-defined]
    tree = ast.parse(source.lstrip())
    func = tree.body[0]
    assert isinstance(func, ast.AsyncFunctionDef)

    called_at_top_level = {
        node.value.func.id
        for node in func.body
        if isinstance(node, ast.Assign | ast.Expr)
        for value in [node.value]
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
    } | {
        node.value.value.func.id
        for node in func.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Await)
        and isinstance(node.value.value, ast.Call)
        and isinstance(node.value.value.func, ast.Name)
    }
    assert "start_case_retention" in called_at_top_level, (
        "start_case_retention must be called unconditionally at lifespan's statement "
        "level — both gates belong inside the helper (AC-7 / C901)"
    )
    assert (
        "stop_case_retention" in called_at_top_level
    ), "stop_case_retention must be awaited unconditionally after the yield"
