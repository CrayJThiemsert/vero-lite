"""AC-3 — the ordering tripwire for the cross-run substrate (PLAN-0088 Step 1).

Same doctrine as ``test_load_run_ordering_guard.py``: this box's wall clock steps
BACKWARDS, so ``services/db/run_analytics.py`` must never ``ORDER BY`` a raw
wall-clock column (``started_at`` / ``created_at`` / ``updated_at``). Ordering a
``date_trunc`` bucket label — or a non-wall-clock grouping column, or in Python —
is allowed; ordering the raw column is a static error here.

The guard also asserts the module documents its own ±1 s skew tolerance +
day-or-coarser bucketing rule, and pins that it fires on the pattern it forbids.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = _REPO_ROOT / "services" / "db" / "run_analytics.py"

_WALL_CLOCK = {"started_at", "created_at", "updated_at"}
_ORDER_WRAPPERS = {"desc", "asc", "nullsfirst", "nullslast"}


def _unwrap(node: ast.expr) -> ast.expr:
    """Strip ``.desc()`` / ``.asc()`` / ``.nulls*()`` wrappers to the core sort key."""
    while (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _ORDER_WRAPPERS
    ):
        node = node.func.value
    return node


def _orders_by_wall_clock(arg: ast.expr) -> bool:
    """True if this ``order_by`` argument sorts on a RAW wall-clock column.

    ``PipelineRun.started_at`` / ``…started_at.desc()`` → True (the raw value is
    the sort key). ``func.date_trunc('day', started_at)`` → False (the wall clock
    is an *argument* to a bucketing function, not the sort key). ``sa.text('…
    started_at …')`` → True (raw column named in raw SQL).
    """
    core = _unwrap(arg)
    if isinstance(core, ast.Attribute) and core.attr in _WALL_CLOCK:
        return True
    if isinstance(core, ast.Name) and core.id in _WALL_CLOCK:
        return True
    if isinstance(core, ast.Call):
        for a in core.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                if any(w in a.value for w in _WALL_CLOCK):
                    return True
    return False


def offending_lines(tree: ast.Module) -> set[int]:
    """Lines with an ``order_by(...)`` sorting on a raw wall-clock column."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "order_by"
        ):
            if any(_orders_by_wall_clock(arg) for arg in node.args):
                lines.add(node.lineno)
    return lines


def test_run_analytics_never_orders_by_a_wall_clock() -> None:
    tree = ast.parse(_MODULE.read_text(encoding="utf-8"), filename=str(_MODULE))
    offenders = sorted(offending_lines(tree))
    assert not offenders, (
        "services/db/run_analytics.py orders by a raw wall-clock column at lines "
        + ", ".join(map(str, offenders))
        + " — this box's wall clock steps backwards. Order by a date_trunc bucket label, "
        "a non-wall-clock column, or in Python (AC-3 / S4)."
    )


def test_module_documents_the_skew_and_bucketing_rule() -> None:
    doc = ast.get_docstring(ast.parse(_MODULE.read_text(encoding="utf-8"))) or ""
    assert "±1 s" in doc, "AC-3: the ±1 s skew tolerance must be documented in the module docstring"
    assert (
        "day or coarser" in doc
    ), "AC-3: the day-or-coarser bucketing rule must be documented in the module docstring"


def test_the_guard_fires_on_the_pattern_it_forbids() -> None:
    """A guard that matches nothing is worse than none — pin what it does and does not catch."""
    forbidden_plain = ast.parse("q = select(X).order_by(PipelineRun.started_at)\n")
    assert offending_lines(forbidden_plain) == {1}

    forbidden_desc = ast.parse("q = select(X).order_by(PipelineRun.started_at.desc())\n")
    assert offending_lines(forbidden_desc) == {1}

    forbidden_text = ast.parse("q = select(X).order_by(sa.text('started_at DESC'))\n")
    assert offending_lines(forbidden_text) == {1}

    allowed_bucket = ast.parse(
        "q = select(X).order_by(func.date_trunc('day', PipelineRun.started_at))\n"
    )
    assert offending_lines(allowed_bucket) == set(), "ordering a date_trunc bucket label is allowed"

    allowed_label = ast.parse("q = select(X).order_by(PipelineRun.status)\n")
    assert offending_lines(allowed_label) == set(), "ordering a non-wall-clock column is allowed"
