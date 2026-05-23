"""PostToolUse hook — run validate_handoff.py on writes/edits under .claude/handoffs/**.

PLAN-0007 Step 5 / AC-3 / ADR-013 D2 (handoff frontmatter auto-validation).

Settings.json matcher narrows to ``Write|Edit``; this script narrows further
to ``.claude/handoffs/**`` paths and ignores everything else. Hard-error
(non-zero exit from the validator) is treated as a blocking PostToolUse
``decision: block`` per the Claude Code hooks reference. Warnings (currently
suppressed by the PLAN-004 Phase B ``_schema.py:_build()`` warning-swallow
bug — see STATUS Active TODOs) are deliberately NOT coupled to this hook;
when the Phase B fix lands, this script will start surfacing warnings via
``additionalContext`` without code changes.

Per PostToolUse semantics: "tool already ran" — we cannot prevent the write,
only block the model from proceeding until the user / model acknowledges.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HANDOFFS_SEGMENT = (".claude", "handoffs")
VALIDATOR = REPO_ROOT / "tools" / "handoffs" / "validate_handoff.py"


def _normalize(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = (REPO_ROOT / p).resolve()
    try:
        return p.resolve()
    except OSError:
        return p


def _is_handoff(path: Path) -> bool:
    parts = path.parts
    # Find the .claude/handoffs/ segment anywhere in the path
    for i in range(len(parts) - 1):
        if parts[i] == HANDOFFS_SEGMENT[0] and parts[i + 1] == HANDOFFS_SEGMENT[1]:
            return True
    # Also handle the Windows UNC form (\\wsl.localhost\... -> drive-less)
    return ".claude/handoffs" in path.as_posix()


def _block(reason: str) -> None:
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": reason,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                },
            }
        )
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name")
    if tool_name not in ("Write", "Edit"):
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = _normalize(tool_input.get("file_path"))
    if file_path is None or not _is_handoff(file_path):
        return 0

    if not file_path.exists():
        # The tool already ran; if the file is missing something else is wrong.
        return 0

    if not VALIDATOR.exists():
        print(
            f"posttooluse_validate_handoff: validator missing at {VALIDATOR}; skipping",
            file=sys.stderr,
        )
        return 0

    try:
        # S603: argv is sys.executable + REPO_ROOT-derived validator path + a file_path
        # already verified to live under .claude/handoffs/ (no shell). Safe by construction.
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(VALIDATOR), str(file_path)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
            env=os.environ.copy(),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"posttooluse_validate_handoff: invocation failed: {exc}", file=sys.stderr)
        return 0

    if result.returncode == 0:
        return 0

    # Hard error from validator → block.
    detail = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    parts = [
        f"validate_handoff.py FAILED on {file_path.name}",
        f"  detail: {detail}" if detail else "",
        f"  stderr: {err}" if err else "",
        "  fix the frontmatter and re-write, or revert the change.",
    ]
    _block("\n".join(p for p in parts if p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
