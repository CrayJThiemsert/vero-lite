#!/usr/bin/env python3
"""Pre-commit size guard for ``docs/status-archive/*.md`` (rotation policy R4).

R4's "archive size escape" sets the only two numbers this guard enforces
(``docs/runbooks/memory-architecture.md`` §"R4 — Archive, don't drop"):

    archives are Tier-3 (grep + windowed reads only, never whole-file Read),
    but stay under the 256 KB byte cap for sanity: if a half-year file would
    exceed ~192 KB, start a `-b` continuation file.

**Why this guard exists.** R4 was the one size-bearing rotation rule with no
mechanism — its responsibility-matrix row read ``—`` where R1 and R7 both read
``fail``. It rotted accordingly: by session 144 the recent-window file stood at
~592 KB, **3x its split trigger and 2.3x the cap**, growing ~7.5 KB per
reconcile because "move, never drop" sends rotated content here and nothing
ever pushed back. Convention is not a tripwire; only a failing check is
(PLAN-0076 AC-6's reasoning, applied to R4).

**Scope note (deliberate).** The hook is ``files:``-scoped to the archive
directory, so this runs only on commits that actually touch an archive — which
is the only way an archive can grow. It is NOT ``always_run``: R7's citation
guard scans the whole tree because a violation can be authored anywhere, but a
byte cap can only be breached by writing to the file it caps.

**This guard is the local half.** Pre-commit is skippable (``--no-verify``) and
CI does not run pre-commit at all, so the binding check on the live archives is
``tests/tools/test_check_archive_size.py::test_live_archives_are_within_cap``,
which runs in CI on every PR. This guard's job is to fail *early* — at the
commit that would grow the breach — rather than after a push.

Exit codes: 0 = every archive within the cap (a file over the split trigger
prints a warning but passes); 1 = at least one archive over the hard cap (split
it per R4 before committing).

``ARCHIVE_SIZE_DIR`` overrides the checked directory for tests (mirrors the
``STATUS_SIZE_PATH`` / ``CLAUDE_*`` override family).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

SPLIT_TRIGGER_BYTES = 192 * 1024  # R4 "start a continuation file" bar
HARD_CAP_BYTES = 256 * 1024  # R4 "stay under ... for sanity" cap
DEFAULT_DIR = "docs/status-archive"


def main() -> int:
    directory = Path(os.environ.get("ARCHIVE_SIZE_DIR") or DEFAULT_DIR)
    if not directory.is_dir():
        # Nothing to guard (e.g. a checkout without the archive) — not a failure.
        return 0

    over_cap: list[tuple[Path, int]] = []
    over_trigger: list[tuple[Path, int]] = []
    for path in sorted(directory.glob("*.md")):
        size = path.stat().st_size
        if size > HARD_CAP_BYTES:
            over_cap.append((path, size))
        elif size > SPLIT_TRIGGER_BYTES:
            over_trigger.append((path, size))

    for path, size in over_trigger:
        print(
            f"archive-size-guard (R4): {path} is {size:,} bytes — over the "
            f"{SPLIT_TRIGGER_BYTES:,}-byte split trigger (hard cap "
            f"{HARD_CAP_BYTES:,}). Passing, but start a continuation file "
            f"before it reaches the cap."
        )

    if over_cap:
        for path, size in over_cap:
            print(
                f"archive-size-guard (R4): {path} is {size:,} bytes — over the "
                f"{HARD_CAP_BYTES:,}-byte HARD cap ({size / HARD_CAP_BYTES:.1f}x). "
                f"Split it into a continuation file before committing: letters "
                f"ascend with time, so the base file keeps the RECENT window and "
                f"older content spills into the next letter (Cray-ratified, "
                f"session 144). Policy: docs/runbooks/memory-architecture.md "
                f"§'R4 — Archive, don't drop'.",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
