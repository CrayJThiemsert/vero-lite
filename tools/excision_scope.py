#!/usr/bin/env python3
"""Enumerate the blast radius of deleting a set of symbols.

**The gap this closes.** PLAN-0102 retired the L1 loop-detect guard, and its
scope was reviewed carefully — by walking the call graph *backwards* from the
marker symbol (``LoopType.FILE_EDIT``) to every site that touched it. That pass
worked: it found three sites whose names carry no ``L1`` token at all. Nobody
walked the graph *forwards*, from the functions being deleted to the things only
those functions call. So every callee reachable **only** from a doomed entry
point stayed invisible, three separate times — see the archived PLAN's
"Corrections found by executing this PLAN".

⚠️ **A linter does not close this.** ruff reports an unused *import* but not an
unused *private function* or module constant, so an acceptance criterion reading
"ruff + mypy are clean" passes straight over the dead function. Measured, not
assumed: that is exactly what PLAN-0102's AC-9 did.

**What this tool does.** Given the symbols you intend to delete, it computes to a
fixpoint every other symbol whose *only* referencers are inside that set — the
transitively-exclusive callees — plus the imports that go unused with them and,
separately, any symbol you named that still has a surviving caller.

**Symbols are module-qualified** (``module::name``), and imports are graph nodes
that depend on their origin. That is load-bearing rather than tidy: a first
version keyed symbols by bare name and therefore collapsed the three separate
``_state_path`` definitions in the hooks tree into one node. Because one of them
kept a live caller, the whole set read as alive — and the tool missed the very
example its own docstring led with. Historical validation against the real
pre-excision tree is what caught that; see ``tests/tools/test_excision_scope.py``.

**What it is NOT.** Read :data:`BLIND_SPOTS`, which the tool prints on every run.
This is static AST analysis: a reference through ``getattr``, a string lookup, a
settings entry point or a plugin registry is invisible to it. Its output is a
**list to verify**, never a verdict — a tool whose predicate is "what its author
thought of", presented as complete, is precisely the failure shape in
``docs/lessons/0039-a-self-authored-guard-inherits-the-authors-blind-spot.md``,
and this tool is not exempt from its own lesson.

Usage::

    python tools/excision_scope.py --root .claude/hooks \\
        --delete _apply_commit_reset _handle_write_or_edit LoopType.FILE_EDIT
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

MODULE_SCOPE = "<module>"

BLIND_SPOTS = (
    "getattr / setattr and any attribute name built at runtime",
    "references from a string: registries, settings.json commands, entry points, "
    "pytest fixture names, decorators that resolve by name",
    "dynamic import (importlib), __getattr__, and star-imports",
    "anything outside --root: a caller in another tree keeps a symbol alive and "
    "this run cannot see it",
    "non-Python callers entirely (shell, CI yaml, Dockerfiles)",
)


@dataclass
class Definition:
    """One top-level definition in one module, and the names its body reads."""

    module: str
    name: str
    kind: str
    lineno: int
    reads: set[str] = field(default_factory=set)
    #: For an ``import`` node: the ``module::name`` it aliases, when resolvable.
    origin: str | None = None

    @property
    def node_id(self) -> str:
        return f"{self.module}::{self.name}"


class _Collector(ast.NodeVisitor):
    """Attribute every name-read to the top-level definition enclosing it.

    Module-level statements are attributed to :data:`MODULE_SCOPE`, which is
    never deletable — so a symbol used at import time keeps a live referencer.
    The one exception is a single-target module-level assignment, whose reads
    are charged to the name it defines (see :meth:`visit_Assign`).
    """

    def __init__(self, module: str) -> None:
        self.module = module
        self.defs: dict[str, Definition] = {}
        self._scope: str = MODULE_SCOPE
        self.defs[MODULE_SCOPE] = Definition(module, MODULE_SCOPE, "module", 0)

    def _define(self, name: str, kind: str, lineno: int, origin: str | None = None) -> Definition:
        d = self.defs.get(name)
        if d is None:
            d = Definition(self.module, name, kind, lineno, origin=origin)
            self.defs[name] = d
        return d

    def _visit_def(self, node: ast.AST, name: str, kind: str, lineno: int) -> None:
        outer = self._scope
        # Only TOP-LEVEL definitions get their own scope: a nested def's reads
        # belong to the enclosing top-level symbol, which is the unit a person
        # actually deletes.
        if outer == MODULE_SCOPE:
            self._define(name, kind, lineno)
            self._scope = name
        self.generic_visit(node)
        self._scope = outer

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_def(node, node.name, "function", node.lineno)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_def(node, node.name, "function", node.lineno)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        # Class members are recorded as ``Class.member`` so an enum member such
        # as ``LoopType.FILE_EDIT`` can be named on the command line.
        if self._scope == MODULE_SCOPE:
            self._define(node.name, "class", node.lineno)
            for stmt in node.body:
                targets: list[ast.expr] = []
                if isinstance(stmt, ast.Assign):
                    targets = list(stmt.targets)
                elif isinstance(stmt, ast.AnnAssign):
                    targets = [stmt.target]
                for t in targets:
                    if isinstance(t, ast.Name):
                        self._define(f"{node.name}.{t.id}", "class-attr", stmt.lineno)
        self._visit_def(node, node.name, "class", node.lineno)

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        """Charge a module-level initializer's reads to the name it defines.

        ``_GIT = shutil.which("git")`` reads ``shutil`` at import time, so the
        naive attribution is to :data:`MODULE_SCOPE` — never deletable, which
        would keep ``shutil`` alive forever. But the read exists *because*
        ``_GIT`` exists: delete ``_GIT`` and the import goes with it.
        """
        if self._scope == MODULE_SCOPE:
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            for n in names:
                self._define(n, "constant", node.lineno)
            # Single, unambiguous target only: ``a = b = expr`` has no one owner.
            if len(names) == 1:
                outer = self._scope
                self._scope = names[0]
                self.visit(node.value)
                self._scope = outer
                return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            self._define(local, "import", node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        for alias in node.names:
            local = alias.asname or alias.name
            origin = f"{node.module}::{alias.name}" if node.module else None
            self._define(local, "import", node.lineno, origin=origin)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, ast.Load):
            self.defs[self._scope].reads.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        if isinstance(node.value, ast.Name):
            self.defs[self._scope].reads.add(f"{node.value.id}.{node.attr}")
        self.generic_visit(node)


def collect(paths: list[Path]) -> dict[str, _Collector]:
    """Parse every ``*.py`` under ``paths``; return module-name -> collector."""
    out: dict[str, _Collector] = {}
    for path in paths:
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for f in files:
            if "__pycache__" in f.parts:
                continue
            c = _Collector(f.stem)
            c.visit(ast.parse(f.read_text(encoding="utf-8"), filename=str(f)))
            out[f.stem] = c
    return out


def _resolve(read: str, module: str, collectors: dict[str, _Collector]) -> str | None:
    """Map a name read inside ``module`` to the ``module::name`` node it hits.

    Resolution is LOCAL FIRST — that is the whole point of qualifying nodes. A
    bare ``_state_path`` inside ``stop_continuation`` must resolve to
    ``stop_continuation::_state_path`` and not to the identically-named function
    in a sibling hook, or three distinct definitions collapse into one and a
    single live caller keeps all of them alive.
    """
    local = collectors[module].defs
    if read in local:
        return f"{module}::{read}"

    # ``Base.attr`` where Base is imported: follow the alias to the origin.
    if "." in read:
        base, attr = read.split(".", 1)
        base_def = local.get(base)
        if base_def is not None and base_def.origin:
            origin_mod = base_def.origin.split("::")[0]
            if origin_mod in collectors and f"{base}.{attr}" in collectors[origin_mod].defs:
                return f"{origin_mod}::{base}.{attr}"
    return None


def _nodes_of(collectors: dict[str, _Collector]) -> dict[str, Definition]:
    """Every top-level definition in every module, keyed ``module::name``."""
    nodes: dict[str, Definition] = {}
    for c in collectors.values():
        for name, d in c.defs.items():
            if name != MODULE_SCOPE:
                nodes[d.node_id] = d
    return nodes


def _read_edges(collectors: dict[str, _Collector]) -> dict[str, set[str]]:
    """target node -> the nodes whose bodies read it.

    ``MODULE_SCOPE`` participates as a referencer and is never a target: it can
    never be deleted, so anything it reads keeps a live referencer forever.
    """
    refs: dict[str, set[str]] = {}
    for mod, c in collectors.items():
        for name, d in c.defs.items():
            referencer = f"{mod}::{name}"
            for read in d.reads:
                target = _resolve(read, mod, collectors)
                if target is not None and target != referencer:
                    refs.setdefault(target, set()).add(referencer)
    return refs


def _link_imports(
    nodes: dict[str, Definition],
    collectors: dict[str, _Collector],
    refs: dict[str, set[str]],
) -> None:
    """Make each ``from X import y`` node a referencer of ``X::y``.

    Without this edge the origin definition looks unreferenced whenever its only
    users are in other modules, and the importing name looks alive whenever the
    origin dies. Both directions matter to the fixpoint.
    """
    for node_id, d in nodes.items():
        if d.kind != "import" or not d.origin:
            continue
        origin_mod, origin_name = d.origin.split("::", 1)
        if origin_mod in collectors and origin_name in collectors[origin_mod].defs:
            refs.setdefault(f"{origin_mod}::{origin_name}", set()).add(node_id)


def build_graph(
    collectors: dict[str, _Collector],
) -> tuple[dict[str, Definition], dict[str, set[str]]]:
    """Return (node_id -> Definition, node_id -> referencing node_ids)."""
    nodes = _nodes_of(collectors)
    refs = _read_edges(collectors)
    _link_imports(nodes, collectors, refs)
    return nodes, refs


def expand(names: set[str], nodes: dict[str, Definition]) -> set[str]:
    """Turn user-supplied names into node ids.

    A bare name marks EVERY module that defines it — deliberately: the caller
    said "delete this symbol", and asking them to know which modules define it
    is asking for the enumeration this tool exists to produce. Pass an explicit
    ``module::name`` to narrow.
    """
    out: set[str] = set()
    for n in names:
        if "::" in n:
            if n in nodes:
                out.add(n)
            continue
        out |= {nid for nid, d in nodes.items() if d.name == n}
    return out


def compute(collectors: dict[str, _Collector], deleting: set[str]) -> dict[str, list[str]]:
    """Grow ``deleting`` to a fixpoint over exclusively-owned symbols."""
    nodes, refs = build_graph(collectors)
    doomed = expand(deleting, nodes)
    unknown = sorted(
        n for n in deleting if "::" not in n and not any(d.name == n for d in nodes.values())
    )

    orphaned: list[str] = []
    changed = True
    while changed:
        changed = False
        for node_id, d in sorted(nodes.items()):
            if node_id in doomed:
                continue
            who = refs.get(node_id, set())
            if not who:
                continue  # already unreferenced — reported separately
            if all(r in doomed for r in who):
                doomed.add(node_id)
                orphaned.append(f"{node_id}  ({d.kind}, line {d.lineno})")
                changed = True

    never_referenced = [
        f"{nid}  ({d.kind}, line {d.lineno})"
        for nid, d in sorted(nodes.items())
        if nid not in refs and d.kind != "import"
    ]

    still_used: list[str] = []
    for node_id in sorted(expand(deleting, nodes)):
        survivors = sorted(r for r in refs.get(node_id, set()) if r not in doomed)
        if survivors:
            still_used.append(f"{node_id}  <- still referenced by {', '.join(survivors)}")

    return {
        "orphaned": orphaned,
        "never_referenced": never_referenced,
        "still_used": still_used,
        "unknown": unknown,
    }


def render(result: dict[str, list[str]], deleting: set[str]) -> str:
    lines: list[str] = [f"Deleting ({len(deleting)}): {', '.join(sorted(deleting))}", ""]

    if result.get("unknown"):
        lines.append(f"== ⚠️ NAME NOT FOUND IN THE ANALYSED TREE ({len(result['unknown'])}) ==")
        lines.append("   A typo here silently shrinks the answer — nothing orphans off a")
        lines.append("   symbol that does not exist. Check the spelling and --root.")
        lines.extend(f"   {x}" for x in result["unknown"])
        lines.append("")

    lines.append(f"== Transitively orphaned by that deletion ({len(result['orphaned'])}) ==")
    lines.append("   Referenced ONLY from inside the deletion set. ruff will flag the")
    lines.append("   imports among them and NOT the functions or constants.")
    lines.extend(f"   {x}" for x in result["orphaned"] or ["(none)"])
    lines.append("")

    if result["still_used"]:
        lines.append(f"== ⚠️ NAMED FOR DELETION BUT STILL USED ({len(result['still_used'])}) ==")
        lines.extend(f"   {x}" for x in result["still_used"])
        lines.append("")

    if result["never_referenced"]:
        n = len(result["never_referenced"])
        lines.append(f"== Already unreferenced before this deletion ({n}) ==")
        lines.append("   Pre-existing, not caused by your change. Entry points live here too.")
        lines.extend(f"   {x}" for x in result["never_referenced"])
        lines.append("")

    lines.append("== ⚠️ THIS OUTPUT IS A LIST TO VERIFY, NOT A VERDICT ==")
    lines.append("   Static AST analysis cannot see:")
    lines.extend(f"     - {b}" for b in BLIND_SPOTS)
    lines.append("   Confirm each candidate before deleting it. A symbol this tool calls")
    lines.append("   orphaned may be the one thing a config file names.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Enumerate the blast radius of deleting a set of symbols.",
        epilog="Output is a list to VERIFY, not a verdict. See the module docstring.",
    )
    p.add_argument("--root", action="append", required=True, help="file or directory to analyse")
    p.add_argument("--delete", nargs="+", required=True, help="symbols you intend to delete")
    args = p.parse_args(argv)

    roots = [Path(r) for r in args.root]
    missing = [r for r in roots if not r.exists()]
    if missing:
        print(f"error: no such path: {', '.join(str(m) for m in missing)}", file=sys.stderr)
        return 2

    collectors = collect(roots)
    if not collectors:
        print("error: no Python files found under the given roots", file=sys.stderr)
        return 2

    print(render(compute(collectors, set(args.delete)), set(args.delete)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
