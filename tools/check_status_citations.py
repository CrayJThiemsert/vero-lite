#!/usr/bin/env python3
"""Pre-commit citation guard for ``docs/STATUS.md`` (rotation policy R7).

A tracked artifact must never cite ``docs/STATUS.md`` by line number. Two
independent reasons (``docs/runbooks/memory-architecture.md`` §"R7"):

* It inverts ``CLAUDE.md`` §1 precedence — STATUS is *state* and "never wins a
  rule conflict", so an ADR/PLAN citing it as authority inverts the hierarchy.
* The anchor rots by construction — R2/R6 re-prune STATUS every reconcile. The
  2026-07-17 prune (65,061 -> 48,420 B) invalidated every pre-existing line-ref
  in the repo at once: 10 citations across 5 files, all silently wrong.

Cite the tracked artifact that holds the fact; if a STATUS reference is truly
unavoidable, cite it by **section name** (``docs/STATUS.md`` §"Active TODOs") —
section names survive a prune, line numbers do not.

Scope is ``git ls-files`` — the literal reading of "tracked artifact", and it
keeps gitignored working notes (``.claude/handoffs/``) out by construction.

Exit codes: 0 = clean; 1 = at least one line-number citation found.

``STATUS_CITATION_ROOT`` overrides the scanned repo root for tests (mirrors the
``STATUS_SIZE_PATH`` / ``CLAUDE_*`` override family pattern).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# Matches `STATUS.md:132` and `STATUS.md:264-286`, with or without a path
# prefix. Deliberately the same shape as the `grep -rn 'STATUS\.md:[0-9]'`
# sweep that found the original rot.
CITATION_RE = re.compile(r"STATUS\.md:\d+")

# Narrative *about* STATUS, or the rule's own machinery — never citations *of*
# STATUS. See the R7 allowlist table in the runbook.
ALLOWLISTED_FILES = frozenset(
    {
        # STATUS narrating its own rotation history.
        "docs/STATUS.md",
        # This policy — it must state the forbidden pattern in order to forbid it.
        "docs/runbooks/memory-architecture.md",
        # The rule's own machinery: this guard must spell the pattern to match
        # it, and its tests must spell it to have anything to catch. Without
        # these two the guard reports itself, which is noise, not a citation.
        "tools/check_status_citations.py",
        "tests/tools/test_check_status_citations.py",
    }
)

# Tier-3 frozen history. R4 makes this exemption MANDATORY, not a convenience:
# archives are move-only and never rewritten, so a line-ref frozen inside an
# archived block must stay exactly as it was written.
ALLOWLISTED_PREFIXES = ("docs/status-archive/",)


def is_allowlisted(rel_path: str) -> bool:
    """True if `rel_path` (POSIX, repo-relative) is exempt from R7."""
    if rel_path in ALLOWLISTED_FILES:
        return True
    return rel_path.startswith(ALLOWLISTED_PREFIXES)


class EnumerationError(RuntimeError):
    """`git ls-files` could not enumerate the tree.

    Deliberately fatal rather than an empty list. A guard that cannot enumerate
    cannot certify the tree clean, and "no files found" is indistinguishable
    from "the scan silently failed" — the exact fail-OPEN shape this guard
    exists to prevent. Caught in development: this worktree's `.git` file points
    at a UNC gitdir (`//wsl.localhost/...`) that WSL's git cannot resolve, so
    `git ls-files` exits non-zero; swallowing that made the guard report a clean
    tree while 10 known violations sat on disk.
    """


def tracked_files(root: Path) -> list[Path]:
    """Repo-relative paths of every git-tracked file under `root`.

    Raises `EnumerationError` if git is unavailable or errors (fail-closed).
    """
    try:
        # S603: fixed argv, no shell — nothing is interpolated into the command;
        # `root` is a cwd, not an argument. S607: "git" via PATH (the same idiom
        # as tools/loop/_status_digest.py).
        proc = subprocess.run(  # noqa: S603
            ["git", "ls-files", "-z"],  # noqa: S607
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        )
    except FileNotFoundError as exc:  # git not on PATH
        raise EnumerationError("git executable not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"exit {exc.returncode}"
        raise EnumerationError(f"git ls-files failed in {root}: {detail}") from exc
    return [Path(p) for p in proc.stdout.split("\0") if p]


def find_violations(root: Path, files: list[Path]) -> list[tuple[str, int, str]]:
    """Scan `files` (repo-relative) under `root`; return (path, lineno, line)."""
    violations: list[tuple[str, int, str]] = []
    for rel in files:
        rel_posix = rel.as_posix()
        if is_allowlisted(rel_posix):
            continue
        target = root / rel
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Binary or unreadable (e.g. a deleted-but-staged path) — not a
            # citation surface.
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if CITATION_RE.search(line):
                violations.append((rel_posix, lineno, line.strip()))
    return violations


def main() -> int:
    root = Path(os.environ.get("STATUS_CITATION_ROOT") or ".").resolve()
    try:
        files = tracked_files(root)
    except EnumerationError as exc:
        print(
            f"status-citation-guard (R7): cannot enumerate tracked files — "
            f"{exc}. Failing closed: an un-enumerable tree is not a clean tree.",
            file=sys.stderr,
        )
        return 1
    violations = find_violations(root, files)
    if not violations:
        return 0
    print(
        f"status-citation-guard (R7): {len(violations)} line-number citation(s) "
        f"of docs/STATUS.md in tracked artifacts:",
        file=sys.stderr,
    )
    for rel_posix, lineno, line in violations:
        print(f"  {rel_posix}:{lineno}: {line}", file=sys.stderr)
    print(
        "\nSTATUS is volatile state — R2/R6 re-prune it every reconcile, so a "
        "line number rots by construction, and citing STATUS as authority "
        "inverts CLAUDE.md §1 (STATUS never wins a rule conflict). Cite the "
        "tracked artifact that holds the fact; if a STATUS reference is truly "
        "unavoidable, cite it by section name (docs/STATUS.md §'Active TODOs'). "
        "Policy: docs/runbooks/memory-architecture.md §'R7'.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
