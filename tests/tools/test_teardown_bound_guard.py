"""Guard: no `drop_all` teardown in `tests/` may bypass the bounded helper.

**Why a guard and not just a helper** (PLAN-0115 SD-1, ruled (b) — the two ship together
and neither is severable). A helper without a guard is *safety-feeling without safety*: a
**new** module simply never calls it, which is precisely how the module that hung for 67
minutes came to exist. The helper fixes the 54 sites that exist today; the guard is what
makes the 55th impossible.

**Rule, not roster.** The guard states a property — *every* `Base.metadata.drop_all` call
in `tests/` lives in `db_support.py` — rather than listing today's known offenders. A
roster passes forever once written; a rule fails the moment someone adds a site.

**It walks the tree on disk, not the git index.** A guard that enumerates committed files
is blind to the new, uncommitted one — which is the file most likely to be wrong, and the
only one a pre-commit run could still catch.

**AST, not grep.** `drop_all` appears in ~10 docstrings and comments under `tests/`
(including this module). A regex flags every one of them, and an author who has to
whitelist prose will whitelist a real call by accident. The AST sees calls only.
"""

from __future__ import annotations

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]

#: The one file allowed to call it — the helper's own body.
HELPER_MODULE = "db_support.py"

HELPER_NAME = "drop_all_bounded"


def _is_drop_all_ref(node: ast.AST) -> bool:
    """Whether ``node`` is the attribute chain ``<anything>.metadata.drop_all``.

    Matched on the tail of the chain rather than on the literal text ``Base.metadata``, so
    aliasing the declarative base on import cannot slip a site past the guard.
    """
    if not isinstance(node, ast.Attribute) or node.attr != "drop_all":
        return False
    return isinstance(node.value, ast.Attribute) and node.value.attr == "metadata"


def _unbounded_sites() -> list[str]:
    """Every `metadata.drop_all` reference under `tests/`, outside the helper module."""
    found: list[str] = []
    for path in sorted(TESTS_ROOT.rglob("*.py")):
        if path.name == HELPER_MODULE:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:  # pragma: no cover - a broken test file fails elsewhere
            continue
        for node in ast.walk(tree):
            if _is_drop_all_ref(node):
                rel = path.relative_to(TESTS_ROOT.parent)
                found.append(f"{rel}:{node.lineno}")
    return found


def test_no_test_module_calls_drop_all_outside_the_bounded_helper() -> None:
    """🔴 The rule. A teardown that bypasses the helper is unbounded, and an unbounded
    `drop_all` does not fail — it **waits forever** on a lock another test leaked, which
    is a failure the test system cannot see."""
    sites = _unbounded_sites()
    assert sites == [], (
        f"{len(sites)} unbounded drop_all teardown(s) — route them through "
        f"`tests.db_support.{HELPER_NAME}`: {sites}"
    )


def test_the_guard_finds_a_planted_violation(tmp_path: Path) -> None:
    """🟢 POSITIVE CONTROL, and the load-bearing half of this file.

    The rule above asserts an **empty list**, which an inert guard satisfies perfectly —
    a `_is_drop_all_ref` that always returned False, or an `rglob` matching nothing, would
    make it green forever. So the matcher is pointed at a module that genuinely contains
    the offending call and must report it.
    """
    planted = tmp_path / "test_planted.py"
    planted.write_text(
        "async def teardown(conn):\n    await conn.run_sync(Base.metadata.drop_all)\n",
        encoding="utf-8",
    )
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    assert any(_is_drop_all_ref(node) for node in ast.walk(tree))


def test_the_guard_ignores_the_word_in_prose(tmp_path: Path) -> None:
    """🟢 The other half of the control: the matcher must NOT fire on the ~10 docstrings
    and comments under `tests/` that mention `drop_all`. If it did, the rule would be
    unsatisfiable and someone would weaken it rather than fix a real site."""
    prose = tmp_path / "test_prose.py"
    prose.write_text(
        '"""A docstring mentioning Base.metadata.drop_all in passing."""\n'
        "# and a comment about conn.run_sync(Base.metadata.drop_all)\n"
        "x = 1\n",
        encoding="utf-8",
    )
    tree = ast.parse(prose.read_text(encoding="utf-8"))
    assert not any(_is_drop_all_ref(node) for node in ast.walk(tree))


def test_the_helper_module_is_where_the_call_actually_lives() -> None:
    """🟢 Proves the exemption is doing real work rather than naming an empty file: the
    single permitted call site genuinely exists, so `_unbounded_sites()` returning `[]`
    means "all routed through the helper" and not "nobody calls drop_all at all"."""
    helper = TESTS_ROOT / HELPER_MODULE
    tree = ast.parse(helper.read_text(encoding="utf-8"), filename=str(helper))
    assert any(_is_drop_all_ref(node) for node in ast.walk(tree))
