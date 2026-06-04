#!/usr/bin/env python3
"""CLI: handoff dashboard reader (PLAN-004 Phase A).

Walks ``.claude/handoffs/session-NN/`` and emits a session snapshot:
counts by phase / status / actor, pause-and-redispatch chains, open
NEEDS_INPUT items, and parse failures.

Usage
-----
    python tools/handoffs/handoff_status.py 10            # session-10
    python tools/handoffs/handoff_status.py session-10
    python tools/handoffs/handoff_status.py --all
    python tools/handoffs/handoff_status.py 10 --json

Exit codes
----------
    0  summary produced
    2  invocation error (session dir not found, no selector)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _schema import (
    SessionSummary,
    session_md_files,
    summarize_paths,
    write_index,
)

DEFAULT_ROOT = Path(".claude/handoffs")


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="handoff_status.py",
        description="Summarize handoff session state (PLAN-004 dashboard reader).",
    )
    parser.add_argument(
        "session",
        nargs="?",
        help="Session selector: '10', 'session-10', or a directory path.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=f"Summarize every session-* dir under {DEFAULT_ROOT}/.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Handoffs root (default: {DEFAULT_ROOT}).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--index",
        action="store_true",
        help="Write/refresh INDEX.md for the selected session(s) instead of printing.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Re-render the summary on an interval until interrupted (Ctrl-C).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between refreshes in --watch mode (default: 5.0).",
    )
    return parser


def _session_dir(root: Path, selector: str) -> Path:
    candidate = Path(selector)
    if candidate.is_dir():
        return candidate
    if selector.startswith("session-"):
        return root / selector
    return root / f"session-{selector}"


def _selected_dirs(args: argparse.Namespace) -> list[Path]:
    """Resolve the session directories the invocation targets."""
    if args.all:
        return sorted(p for p in args.root.glob("session-*") if p.is_dir())
    return [_session_dir(args.root, args.session)]


def _summaries(args: argparse.Namespace) -> list[SessionSummary]:
    # session_md_files() excludes the generated INDEX.md so it is never counted.
    return [summarize_paths(session_md_files(d), d.name) for d in _selected_dirs(args)]


def _render_text(summary: SessionSummary) -> str:
    def _kv(mapping: dict[str, int]) -> str:
        return ", ".join(f"{k}={v}" for k, v in mapping.items()) or "—"

    lines = [
        f"{summary.session}:",
        f"  Total handoffs: {summary.total}",
        f"  By phase: {_kv(summary.by_phase)}",
        f"  By status: {_kv(summary.by_status)}",
        f"  By actor: {_kv(summary.by_actor)}",
        f"  Pause-and-redispatch chains: {len(summary.chains)}",
    ]
    lines.extend(f"    - {chain}" for chain in summary.chains)
    lines.append(f"  Open NEEDS_INPUT: {len(summary.needs_input)}")
    lines.extend(f"    - {name}" for name in summary.needs_input)
    if summary.parse_failures:
        lines.append(f"  Parse failures: {len(summary.parse_failures)}")
        lines.extend(f"    - {name}" for name in summary.parse_failures)
    return "\n".join(lines)


def _write_indexes(args: argparse.Namespace) -> int:
    """Write/refresh INDEX.md for each selected, existing session dir."""
    exit_code = 0
    for session_dir in _selected_dirs(args):
        if not session_dir.is_dir():
            print(f"error: session dir not found: {session_dir}", file=sys.stderr)
            exit_code = 2
            continue
        target = write_index(session_dir)
        print(f"wrote {target}")
    return exit_code


def run_watch(
    args: argparse.Namespace,
    *,
    ticks: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    out: TextIO | None = None,
) -> int:
    """Re-render the summary every ``args.interval`` seconds until Ctrl-C.

    ``ticks`` bounds the loop for tests; ``sleep_fn`` / ``out`` are
    injectable so a test can run a fixed number of frames against a buffer
    without a real terminal or a wall-clock wait.
    """
    stream = out if out is not None else sys.stdout
    count = 0
    try:
        while ticks is None or count < ticks:
            stream.write("\033[2J\033[H")  # clear screen + cursor home
            stream.write("\n\n".join(_render_text(s) for s in _summaries(args)))
            stream.write("\n")
            stream.flush()
            count += 1
            if ticks is not None and count >= ticks:
                break
            sleep_fn(args.interval)
    except KeyboardInterrupt:
        pass
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not args.all and not args.session:
        print("error: provide a session selector or --all", file=sys.stderr)
        return 2
    if not args.root.is_dir():
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 2

    if args.index:
        return _write_indexes(args)
    if args.watch:
        return run_watch(args)

    summaries = _summaries(args)

    if args.json:
        print(json.dumps([asdict(s) for s in summaries], ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(_render_text(s) for s in summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
