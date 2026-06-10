#!/usr/bin/env python3
"""Pre-commit size guard for ``docs/STATUS.md`` (rotation policy R1).

STATUS.md is Tier-1 volatile state — always-read, never an archive. After it
grew to 393 KB and broke the Read tool's 25k-token whole-file cap (Lesson #23,
PR #243), the rotation policy (``docs/runbooks/memory-architecture.md``
§"STATUS.md Rotation Policy") set a **hard ceiling of 64 KB** with a **48 KB
soft target**. This guard is the R1 responsibility-matrix "authoritative
check": deterministic, fail-closed at the commit boundary, immune to agent
drift.

Exit codes: 0 = within budget (a soft-target overrun prints a warning but
passes); 1 = hard ceiling exceeded (fix per R2/R3 before committing).

``STATUS_SIZE_PATH`` overrides the checked path for tests (mirrors the
``CLAUDE_*`` override family pattern).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HARD_CEILING_BYTES = 64 * 1024  # R1 hard ceiling
SOFT_TARGET_BYTES = 48 * 1024  # R1 soft target
DEFAULT_PATH = "docs/STATUS.md"


def main() -> int:
    path = Path(os.environ.get("STATUS_SIZE_PATH") or DEFAULT_PATH)
    if not path.exists():
        # Nothing to guard (e.g. a checkout without STATUS) — not a failure.
        return 0
    size = path.stat().st_size
    if size > HARD_CEILING_BYTES:
        print(
            f"status-size-guard (R1): {path} is {size:,} bytes — over the "
            f"{HARD_CEILING_BYTES:,}-byte HARD ceiling. Prune to the rotation "
            f"window (R2) / rotate to docs/status-archive/ (R4) before "
            f"committing. Policy: docs/runbooks/memory-architecture.md "
            f"§'STATUS.md Rotation Policy' (Lesson #23).",
            file=sys.stderr,
        )
        return 1
    if size > SOFT_TARGET_BYTES:
        print(
            f"status-size-guard (R1): {path} is {size:,} bytes — over the "
            f"{SOFT_TARGET_BYTES:,}-byte soft target (hard ceiling "
            f"{HARD_CEILING_BYTES:,}). Passing, but prune harder next "
            f"reconcile (R2/R6)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
