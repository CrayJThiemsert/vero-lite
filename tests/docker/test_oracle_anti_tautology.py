"""Guards PLAN-0095 AC-3 + AC-6 on the oracle module itself.

Lives in a **separate module** on purpose: AC-3 forbids the oracle module from
containing the name of the plugin package it must nonetheless cover, so the check
cannot live inside the thing it checks. Scoping AC-3 to
``test_dockerfile_oracle.py`` is what lets this file spell the name freely.

Cray ruled this shape (session 177) over the PLAN's literal "one-line greppable
check any reviewer can run": a reviewer's grep is a habit, a test is a gate --
and AC-3 is exactly the invariant a future edit would quietly kill.
"""

from __future__ import annotations

import ast
from pathlib import Path

ORACLE = Path(__file__).resolve().parent / "test_dockerfile_oracle.py"

# The plugin package root the oracle must discover by DERIVATION, never by name.
BANNED_NAME = "verticals"

# AC-6: no acceptance criterion may require a Docker daemon. A substring grep for
# "docker" would false-positive on the module's own prose, so the check is on
# what it actually IMPORTS -- the only way it could reach a daemon or the network.
BANNED_IMPORTS = frozenset(
    {"subprocess", "socket", "requests", "httpx", "docker", "urllib.request"}
)


def _imported_names(tree: ast.Module) -> set[str]:
    """Every module name the source imports, dotted form preserved."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names |= {f"{node.module}.{alias.name}" for alias in node.names}
    return names


def test_ac3_oracle_never_names_the_plugin_package() -> None:
    """The oracle's coverage must fall out of derivation, not enumeration."""
    source = ORACLE.read_text(encoding="utf-8")
    hits = [
        f"{number}: {line.strip()}"
        for number, line in enumerate(source.splitlines(), start=1)
        if BANNED_NAME in line
    ]
    assert not hits, (
        f"{ORACLE.name} names {BANNED_NAME!r} in {len(hits)} line(s), so its coverage "
        "of that root is enumerated rather than derived -- a hardcoded expectation "
        "passes tautologically forever and stops catching new runtime-resolved "
        f"roots. Offending line(s): {hits}"
    )


def test_ac6_oracle_cannot_reach_a_daemon_or_the_network() -> None:
    """Every acceptance criterion must be evaluable with Docker absent."""
    tree = ast.parse(ORACLE.read_text(encoding="utf-8"))
    imported = _imported_names(tree)
    offending = sorted(
        name
        for name in imported
        if name in BANNED_IMPORTS or name.split(".")[0] in {"subprocess", "docker"}
    )
    assert not offending, (
        f"{ORACLE.name} imports {offending}, which can reach a daemon, a shell or the "
        "network. The oracle is the offline gate: daemon actions belong only in the "
        "optional, Cray-gated live-evidence step."
    )
