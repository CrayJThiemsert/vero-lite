#!/usr/bin/env python
"""Run any command and turn its output into a goal evidence file.

**Why this exists.** PLAN-0123 clause R2 binds *every* ``check`` to leave an
evidence file the ``goal-evaluator`` can read — a check's stdout never reaches
the judge, only its exit code becomes a state. The purpose-built instruments
(``tools/tally.py``, ``tools/absent.py``, the probe-battery driver) each carry
``--report-to`` for that. But a legitimate check may invoke something that is
**not** an instrument: a ``tools/check_*.py`` guard, a pytest node, a one-off
script. Those have no ``--report-to`` and should not grow one — a pre-commit
guard's interface is not the place to encode a goal-file convention.

So the wrapper, rather than a flag on every callee. One convention for the
evidence format (``tools/_evidence.py``), one place that knows it, and any
command at all can produce a conforming file.

**The two things it refuses to get wrong.**

1. **The exit status is the child's, unmodified**, and the ``VERDICT:`` line is
   rendered from that same value. A wrapper that computed its own verdict would
   be error #13 with an extra process in the middle.
2. **stdout and stderr are merged**, in order, into one capture. CLAUDE.md §8
   records the measured failure: unmerged ``stderr`` **overwrites** ``stdout``
   byte-for-byte, and one stderr line can erase an entire reading. A traceback
   that vanished from the evidence file is worse than no evidence file, because
   the file still looks like a measurement.

Usage::

    python -m tools.stamp_evidence \\
        --to .claude/state/goal-evidence/<gid>/C0.txt --gid <gid> \\
        --label check_battery_definitions \\
        -- python tools/check_battery_definitions.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if __package__ in (None, ""):  # pragma: no cover - path-form invocation
    sys.path.insert(0, str(REPO_ROOT))

from tools._evidence import head_sha, verdict_line, write_evidence  # noqa: E402


def run_and_capture(argv: list[str], *, cwd: Path, timeout_s: int) -> tuple[int, str]:
    """The child's ``(exit status, merged output)``.

    ``stderr=STDOUT`` rather than two pipes: the point is one stream in the order
    it was written. Reassembling two captures afterwards guesses at interleaving,
    and a guessed order in an evidence file is a fact nobody measured.
    """
    try:
        proc = subprocess.run(  # noqa: S603 — argv supplied by the caller, no shell
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(cwd),
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, f"stamp_evidence: {argv!r} exceeded {timeout_s}s and was killed"
    except (OSError, subprocess.SubprocessError) as exc:
        return 125, f"stamp_evidence: could not run {argv!r}: {exc}"
    return proc.returncode, proc.stdout


def build_report(argv: list[str], status: int, captured: str) -> str:
    """The evidence body: what ran, what it said, and the verdict — as values."""
    return "\n".join(
        [
            f"command: {' '.join(argv)}",
            f"child_exit: {status}   output_bytes: {len(captured)}",
            "",
            captured.rstrip("\n"),
            "",
            verdict_line(status),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stamp_evidence",
        description="Run a command and write its output as a goal evidence file.",
    )
    parser.add_argument("--to", type=Path, required=True, help="the evidence file to write")
    parser.add_argument("--gid", default="", help="goal id for the R7 header")
    parser.add_argument("--label", default="", help="what produced this reading")
    parser.add_argument("--timeout", type=int, default=90, help="kill the child after N seconds")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to run, after a bare --",
    )
    args = parser.parse_args(argv)

    command = [c for c in args.command if c != "--"]
    if not command:
        print("stamp_evidence: no command given after --", file=sys.stderr)
        print(verdict_line(2))
        return 2

    status, captured = run_and_capture(command, cwd=REPO_ROOT, timeout_s=args.timeout)
    report = build_report(command, status, captured)
    print(report)
    write_evidence(
        report,
        args.to,
        {
            "gid": args.gid or "unset",
            "head": head_sha(REPO_ROOT),
            "instrument": args.label or "stamp_evidence",
        },
    )
    # The child's status, unmodified — the same value `verdict_line` rendered.
    return status


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
