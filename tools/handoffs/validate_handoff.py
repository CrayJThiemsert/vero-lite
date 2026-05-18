#!/usr/bin/env python3
"""CLI: validate handoff frontmatter against the PLAN-004 schema.

Usage
-----
    python tools/handoffs/validate_handoff.py PATH [PATH ...]
    python tools/handoffs/validate_handoff.py --all      # walk .claude/handoffs/
    python tools/handoffs/validate_handoff.py --all --quiet   # exit code only

Exit codes
----------
    0  all files valid (warnings allowed)
    1  at least one error-severity finding
    2  invocation error (no inputs, missing path, ...)
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _schema import (
    ValidationError,
    validate_directory,
    validate_file,
)

DEFAULT_ROOT = Path(".claude/handoffs")


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="validate_handoff.py",
        description="Validate handoff frontmatter against the PLAN-004 schema.",
    )
    parser.add_argument("paths", nargs="*", type=Path, help="Handoff files to validate.")
    parser.add_argument(
        "--all",
        action="store_true",
        help=f"Walk {DEFAULT_ROOT}/ instead of explicit paths.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Root for --all (default: {DEFAULT_ROOT}).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-finding output; communicate via exit code only.",
    )
    return parser


def _gather(args: argparse.Namespace) -> dict[Path, list[ValidationError]]:
    if args.all:
        return validate_directory(args.root)
    return {path: validate_file(path) for path in args.paths}


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not args.all and not args.paths:
        print("error: provide one or more PATHs, or --all", file=sys.stderr)
        return 2
    if args.all and not args.root.is_dir():
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 2

    findings = _gather(args)
    error_count = 0
    for path in sorted(findings):
        for finding in findings[path]:
            if finding.is_error():
                error_count += 1
            if not args.quiet:
                print(f"{path}:{finding.render()}")

    if error_count:
        if not args.quiet:
            print(f"\n{error_count} error(s) across {len(findings)} file(s)", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"OK: {len(findings)} file(s) valid", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
