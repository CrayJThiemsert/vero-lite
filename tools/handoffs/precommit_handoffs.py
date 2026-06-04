#!/usr/bin/env python3
"""Pre-commit entry: validate the latest session's handoffs + refresh INDEX.md.

PLAN-004 Phase B. Wired as a ``repo: local`` hook (``always_run: true``,
``pass_filenames: false``) because handoff files are gitignored
(``.claude/handoffs/.gitignore`` = ``*``) and are therefore never staged — a
normal staged-files hook would never see them. This runs against the
**working tree** instead.

Scope = the **latest** ``session-NN`` directory only (highest N). This catches
schema drift in the session being actively authored at commit time, without
letting a malformed handoff in an old session block unrelated commits (the
"no legacy drag" design decision, Cray-ratified session 35).

Behaviour:

* No ``.claude/handoffs/`` root or no ``session-NN`` dir → exit 0 (no-op).
* Always regenerate the latest session's ``INDEX.md`` (idempotent; gitignored
  output, never staged).
* Validate every ``*.md`` in that session (excluding the generated
  ``INDEX.md``); print error-severity findings to stderr; exit 1 if any.

Warnings (e.g. unknown field, suffix-not-in-filename) do not block — only
error-severity findings fail the commit.

Exit codes
----------
    0  clean, or nothing to check
    1  at least one error-severity schema finding in the latest session
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _schema import (
    latest_session_dir,
    session_md_files,
    validate_file,
    write_index,
)

DEFAULT_ROOT = Path(".claude/handoffs")


def main(argv: list[str] | None = None) -> int:
    """Hook entry point. Optional ``argv[0]`` overrides the handoffs root."""
    root = Path(argv[0]) if argv else DEFAULT_ROOT
    session_dir = latest_session_dir(root)
    if session_dir is None:
        return 0  # no handoffs root / no session dir — nothing to check

    write_index(session_dir)  # idempotent refresh of the latest session's index

    error_count = 0
    for path in session_md_files(session_dir):
        for finding in validate_file(path):
            if finding.is_error():
                error_count += 1
                print(f"{path}:{finding.render()}", file=sys.stderr)

    if error_count:
        print(
            f"\n{error_count} handoff schema error(s) in {session_dir.name} "
            "— refusing commit; fix the frontmatter "
            "(run: uv run python tools/handoffs/validate_handoff.py <file>)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
