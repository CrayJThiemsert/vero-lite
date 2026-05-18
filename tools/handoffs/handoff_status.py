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
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _schema import SessionSummary, summarize_paths

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
    return parser


def _session_dir(root: Path, selector: str) -> Path:
    candidate = Path(selector)
    if candidate.is_dir():
        return candidate
    if selector.startswith("session-"):
        return root / selector
    return root / f"session-{selector}"


def _summaries(args: argparse.Namespace) -> list[SessionSummary]:
    if args.all:
        dirs = sorted(p for p in args.root.glob("session-*") if p.is_dir())
        return [summarize_paths(list(d.glob("*.md")), d.name) for d in dirs]
    target = _session_dir(args.root, args.session)
    return [summarize_paths(list(target.glob("*.md")), target.name)]


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

    summaries = _summaries(args)

    if args.json:
        print(json.dumps([asdict(s) for s in summaries], ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(_render_text(s) for s in summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
