"""The ``load_run`` ordering invariant, enforced statically across the tree.

``load_run`` orders step results by ``created_at`` — a WALL-CLOCK column. This box's
``datetime.now(UTC)`` was measured stepping BACKWARDS (2 backward steps per 20 s sample,
worst -555 ms), so a later step can sort before an earlier one and ``step_results[-1]``
then names a *completed* step rather than the one the run is suspended at.

#678 taught the production consumers (``resume_run``, ``GET /runs/{id}``) to select by
STATUS via ``suspended_step_result``, but the DB tests kept reading by position — which
surfaced as an intermittent, full-suite-only failure of the procurement demo tests. This
guard closes the gap for good: indexing a ``load_run`` result's ``step_results`` is now a
static error anywhere under ``services/``, ``tests/`` or ``verticals/``.

Select by STATUS — ``suspended_step_result(loaded.step_results)`` — when the intent is "the
step this run is suspended at", or by IDENTITY — ``next(sr for sr in loaded.step_results if
sr.step_id == "approve")`` — when the intent is a particular step (and especially when the
test then asserts that step's *status*, which selecting by status would make circular).

Scope + limits, stated honestly:

* Only names bound directly to a ``load_run(...)`` call are tracked, scoped to the function
  that binds them.
* Only *subscripts* are flagged. An order-sensitive comparison such as
  ``[sr.step_id for sr in loaded.step_results] == ["read", "aerate"]`` is unsafe for exactly
  the same reason and is **not** detected — compare those ``sorted``.
* An in-memory ``RunResult`` is unaffected: the orchestrator appends ``step_results`` in
  execution order, so ``result.step_results[-1]`` is legitimate and is not scanned.

Why this guards the hazard instead of removing it — the deferral, and why it STANDS:

A monotonic per-run ``sequence`` column on ``step_results`` would remove this hazard at its
ROOT rather than guard against it, and that remains the right fix. It needs a DB migration,
so it deserves its own PLAN (PLAN-0062-independent) — none is drafted. Until one is,
``load_run``'s wall-clock ``ORDER BY created_at`` is **unchanged by design**: the deferral
STANDS, and this guard is what holds the line in the meantime.

What makes the deferral tolerable rather than urgent is that both surviving wall-clock
orderings are **DISPLAY-ONLY**. #678 moved the production consumers (``resume_run``,
``GET /runs/{id}``) off list position and onto STATUS selection; what still sorts on a
wall clock is:

* ``load_run`` itself — ``order_by(StepResult.created_at, ...)`` in
  ``services/engine/procedures/persistence.py`` (the ordering this guard covers).
* the run list — ``order_by(PipelineRun.started_at.desc())`` in
  ``services/api/routers/runs.py`` (a newest-first read-only projection).

Both render rows a human reads; neither decides what a run does next. That is the whole
of the deferral's safety margin — if a correctness path ever starts depending on either
ordering, the sequence-column PLAN stops being optional.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCANNED_PACKAGES = ("services", "tests", "verticals")


def _is_load_run_call(value: ast.expr | None) -> bool:
    """``load_run(...)`` or ``await load_run(...)``."""
    if isinstance(value, ast.Await):
        value = value.value
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "load_run"
    )


def _load_run_names(scope: ast.AST) -> set[str]:
    """Names bound to a ``load_run`` result within ``scope``."""
    names: set[str] = set()
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and _is_load_run_call(node.value):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return names


def _positional_reads(scope: ast.AST, names: set[str]) -> set[int]:
    """Lines subscripting ``<tracked name>.step_results`` within ``scope``."""
    lines: set[int] = set()
    for node in ast.walk(scope):
        if not isinstance(node, ast.Subscript):
            continue
        attribute = node.value
        if not isinstance(attribute, ast.Attribute) or attribute.attr != "step_results":
            continue
        owner = attribute.value
        if isinstance(owner, ast.Name) and owner.id in names:
            lines.add(node.lineno)
    return lines


def offending_lines(tree: ast.Module) -> set[int]:
    """Lines that read a ``load_run`` result's ``step_results`` by list position.

    Tracked per enclosing function, so a name like ``result`` bound to an in-memory
    ``RunResult`` in one test never inherits ``load_run`` provenance from another.
    """
    lines: set[int] = set()
    for scope in ast.walk(tree):
        if not isinstance(scope, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        names = _load_run_names(scope)
        if names:
            lines |= _positional_reads(scope, names)
    return lines


def test_no_load_run_result_is_read_by_list_position() -> None:
    offenders: list[str] = []
    for package in _SCANNED_PACKAGES:
        for path in sorted((_REPO_ROOT / package).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            offenders += [
                f"{path.relative_to(_REPO_ROOT).as_posix()}:{line}"
                for line in sorted(offending_lines(tree))
            ]

    assert not offenders, (
        "a load_run() result's step_results is read by list position at "
        + ", ".join(offenders)
        + " — load_run orders on `created_at`, a wall clock that steps backwards, so list "
        "position does not mean execution order. Select by status "
        "(suspended_step_result) or by identity (next(sr for sr in ... if sr.step_id == ...))."
    )


def test_the_guard_fires_on_the_pattern_it_forbids() -> None:
    """A guard that matches nothing is worse than none — pin what it does and does not catch."""
    unsafe = ast.parse(
        "async def f(s):\n"
        "    loaded = await load_run(s, 'r')\n"
        "    return loaded.step_results[-1]\n"
    )
    assert offending_lines(unsafe) == {3}

    by_status = ast.parse(
        "async def f(s):\n"
        "    loaded = await load_run(s, 'r')\n"
        "    return suspended_step_result(loaded.step_results)\n"
    )
    assert offending_lines(by_status) == set()

    by_identity = ast.parse(
        "async def f(s):\n"
        "    loaded = await load_run(s, 'r')\n"
        "    return next(sr for sr in loaded.step_results if sr.step_id == 'approve')\n"
    )
    assert offending_lines(by_identity) == set()

    in_memory = ast.parse(
        "async def f():\n"
        "    result = await run_procedure()\n"
        "    return result.step_results[-1]\n"
    )
    assert offending_lines(in_memory) == set(), "an in-memory RunResult is append-ordered"

    # provenance does not leak across functions sharing a variable name
    scoped = ast.parse(
        "async def a(s):\n"
        "    loaded = await load_run(s, 'r')\n"
        "    return loaded.run\n"
        "async def b():\n"
        "    loaded = await run_procedure()\n"
        "    return loaded.step_results[-1]\n"
    )
    assert offending_lines(scoped) == set()
