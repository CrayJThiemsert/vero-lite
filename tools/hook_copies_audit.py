#!/usr/bin/env python3
"""Audit which copy of the Stop-arm hooks each worktree is running (PLAN-0122 AC-10).

**Read-only, by ruling.** SD-6 was ruled IN SCOPE, AUDIT-ONLY (Cray, typed, s280):
this delivers the tool and the list and nothing else. *No file inside another
worktree is touched.* Pruning, syncing or deleting a stale copy is a separate,
Cray-gated action.

The gap it records: a hook change on ``main`` does not reach a worktree that was
checked out before it. A session started in that worktree keeps the old
behaviour — including, historically, the shipped 32,708-char prompt that the
PLAN measured at 16/49, below an always-pause bot.

**Enumeration is by FILESYSTEM, not by ``git worktree list``, and that is a
measured decision, not a preference.** On this machine at s282 the porcelain
reported **6** worktrees where **19** exist on disk, and marked all six
``prunable`` although every one of their directories was present — their gitdirs
are UNC paths (``//wsl.localhost/...``) that git cannot resolve from the WSL
side. A tool that walked the porcelain would have read 6 of 19 copies, or 0 if
it honoured ``prunable``, and reported a single hash: a clean bill of health
produced by reading almost nothing.

**Why zero worktrees is NOT the vacuity control.** A fresh clone legitimately has
none — CI checks out exactly that, so an assertion on the worktree count would be
environment-dependent and would redden in CI for the wrong reason. The control
that *does* discriminate is the MAIN tree's own hook copy: it must always exist,
so failing to find it means the path logic is broken rather than the tree clean.
That is what this tool fails closed on.

Exit codes: 0 = every copy is on the same bytes; 1 = divergence found, or the
main tree's own copy could not be read.

``HOOK_AUDIT_ROOT`` overrides the scanned repo root for tests (mirrors the
``PLAN_REF_ROOT`` / ``STATUS_CITATION_ROOT`` override family).
"""

from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# The two files that decide what a Stop event does. `_sonnet_classifier.py`
# builds the prompt and talks to the model; `stop_continuation.py` owns the
# arms (proceed / demoted / pause / dispatch) and the chain counter.
SUBJECTS = ("_sonnet_classifier.py", "stop_continuation.py")

HOOKS_REL = Path(".claude") / "hooks"
WORKTREES_REL = Path(".claude") / "worktrees"


def _sha256(path: Path) -> str | None:
    """Hex digest of `path`, or None if it cannot be read."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


@dataclass(frozen=True)
class Copy:
    """One checkout's copy of the Stop-arm hooks.

    `name` is "main" for the root tree, else the worktree directory name.
    A subject missing from a copy maps to None rather than being dropped: a
    worktree that predates a hook is a real state, and silently omitting it
    would understate the divergence.
    """

    name: str
    hashes: dict[str, str | None]


def _copy_at(root: Path, name: str) -> Copy:
    hooks = root / HOOKS_REL
    return Copy(name=name, hashes={s: _sha256(hooks / s) for s in SUBJECTS})


def collect(root: Path) -> tuple[Copy, list[Copy]]:
    """`(main_copy, worktree_copies)` — every on-disk checkout under `root`.

    Worktrees are found by globbing `.claude/worktrees/*/`, deliberately: see
    the module docstring on why the git porcelain undercounts here. Directories
    without a `.claude/hooks/` at all are skipped — they are not checkouts of
    this repo's hook surface and would only add noise.
    """
    main = _copy_at(root, "main")
    worktrees: list[Copy] = []
    wt_root = root / WORKTREES_REL
    if wt_root.is_dir():
        for entry in sorted(wt_root.iterdir()):
            if not (entry / HOOKS_REL).is_dir():
                continue
            worktrees.append(_copy_at(entry, entry.name))
    return main, worktrees


@dataclass(frozen=True)
class Report:
    worktrees: int
    distinct: dict[str, int]
    stale: list[str]
    main_readable: bool


def audit(root: Path) -> Report:
    """Hash every copy and diff each worktree against the shipped (main) bytes."""
    main, worktrees = collect(root)
    distinct = {
        subject: len({c.hashes[subject] for c in [main, *worktrees]}) for subject in SUBJECTS
    }
    stale = [c.name for c in worktrees if any(c.hashes[s] != main.hashes[s] for s in SUBJECTS)]
    return Report(
        worktrees=len(worktrees),
        distinct=distinct,
        stale=stale,
        main_readable=all(main.hashes[s] is not None for s in SUBJECTS),
    )


def main() -> int:
    root = Path(os.environ.get("HOOK_AUDIT_ROOT") or ".").resolve()
    report = audit(root)

    # Print the values measured, never a bare verdict (CLAUDE.md §8).
    print(
        f"hook-copies-audit (AC-10): worktrees={report.worktrees} "
        f"distinct_classifier_hashes={report.distinct['_sonnet_classifier.py']} "
        f"distinct_stop_hook_hashes={report.distinct['stop_continuation.py']} "
        f"stale={report.stale}"
    )

    if not report.main_readable:
        print(
            f"hook-copies-audit (AC-10): the MAIN tree's own hook copy is "
            f"unreadable under {root / HOOKS_REL}. Failing closed — an enumerator "
            f"that cannot find the one copy guaranteed to exist is broken, not "
            f"looking at a clean tree. (Zero WORKTREES is not this error: a fresh "
            f"clone has none, which is why the main copy is the control.)",
            file=sys.stderr,
        )
        return 1

    if all(k == 1 for k in report.distinct.values()):
        return 0

    print(
        f"\nhook-copies-audit (AC-10): {len(report.stale)} worktree(s) are NOT on "
        f"the shipped bytes. A session started in any of them runs that copy's "
        f"Stop arm, not main's.\n\n"
        f"This tool is AUDIT-ONLY by ruling (PLAN-0122 SD-6, Cray, typed, s280): "
        f"it reports and does not repair. Pruning or syncing a worktree is a "
        f"separate, Cray-gated action. Record the disposition of each entry in "
        f"the PLAN's closeout rather than fixing it here.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
