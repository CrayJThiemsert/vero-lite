"""AC-11 — the read-only guard for the Group-A substrate (PLAN-0088 Step 1).

Holds L1 mechanically: the substrate + its readers only READ. A static AST scan
over ``run_analytics.py`` (and ``insights.py`` / ``run_query.py`` once they
exist) asserts:

  (i)   no write primitive — ``session.add`` / ``add_all`` / ``delete`` /
        ``merge``, or an ``insert(`` / ``update(`` / ``delete(`` construct;
  (ii)  no import of the proposal / write-path deny-list — ``RecommendedAction``,
        ``resolve_gated_step``, ``persist_run``, ``resume_run``;
  (iii) ``run_query.py`` imports no ``sqlalchemy`` symbol at all (S1 layering —
        engine-side owns no SQL).

If a reader ever acquires a write primitive, the build fails here — Group A is
reads-and-reports, never a proposal / governance-feedback loop.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TARGETS = (
    _REPO_ROOT / "services" / "db" / "run_analytics.py",
    _REPO_ROOT / "services" / "api" / "routers" / "insights.py",
    _REPO_ROOT / "services" / "engine" / "run_query.py",
)

_WRITE_METHODS = {"add", "add_all", "delete", "merge"}
_WRITE_CTORS = {"insert", "update", "delete"}
_DENY_LIST = {"RecommendedAction", "resolve_gated_step", "persist_run", "resume_run"}


def write_primitive_lines(tree: ast.Module) -> set[int]:
    """Lines that call a write primitive (``session.add`` / ``insert(`` / …)."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and (
            func.attr in _WRITE_METHODS or func.attr in _WRITE_CTORS
        ):
            lines.add(node.lineno)
        elif isinstance(func, ast.Name) and func.id in _WRITE_CTORS:
            lines.add(node.lineno)
    return lines


def denied_imports(tree: ast.Module) -> set[str]:
    """Deny-list symbols imported anywhere in the module."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            found |= {alias.name for alias in node.names if alias.name in _DENY_LIST}
        elif isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names if alias.name in _DENY_LIST}
    return found


def imports_sqlalchemy(tree: ast.Module) -> bool:
    """True if the module imports any ``sqlalchemy`` symbol (S1 layering check)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("sqlalchemy"):
            return True
        if isinstance(node, ast.Import):
            if any(alias.name.startswith("sqlalchemy") for alias in node.names):
                return True
    return False


def test_substrate_and_readers_are_read_only() -> None:
    scanned = 0
    for path in _TARGETS:
        if not path.exists():
            continue  # insights.py / run_query.py land in later steps
        scanned += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(_REPO_ROOT).as_posix()

        writes = sorted(write_primitive_lines(tree))
        assert (
            not writes
        ), f"{rel} calls a write primitive at lines {writes} — Group A reads only (AC-11)"

        denied = denied_imports(tree)
        assert (
            not denied
        ), f"{rel} imports the write-path deny-list {sorted(denied)} — Group A reads only (AC-11)"

        if path.name == "run_query.py":
            assert not imports_sqlalchemy(
                tree
            ), f"{rel} imports sqlalchemy — the engine-side reader owns no SQL (S1 layering)"
    assert scanned >= 1, "the guard scanned no target file — run_analytics.py must exist by Step 1"


def test_the_guard_fires_on_the_pattern_it_forbids() -> None:
    """Non-vacuity: the detectors must catch the exact patterns they forbid."""
    session_add = ast.parse("def f(session, x):\n    session.add(x)\n")
    assert write_primitive_lines(session_add) == {2}

    sa_insert = ast.parse("def f():\n    return insert(T).values(a=1)\n")
    assert write_primitive_lines(sa_insert) == {2}

    read_only = ast.parse("def f(session):\n    return session.execute(select(T))\n")
    assert write_primitive_lines(read_only) == set(), "session.execute (a read) must not be flagged"

    denied = ast.parse("from services.engine.procedures.persistence import persist_run\n")
    assert denied_imports(denied) == {"persist_run"}

    clean = ast.parse("from services.engine.procedures.runs import PipelineRun\n")
    assert denied_imports(clean) == set()

    has_sa = ast.parse("import sqlalchemy as sa\n")
    assert imports_sqlalchemy(has_sa) is True
    no_sa = ast.parse("from services.engine.nl_query import translate\n")
    assert imports_sqlalchemy(no_sa) is False
