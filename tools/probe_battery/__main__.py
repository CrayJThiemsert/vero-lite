"""CLI for the probe-battery driver: ``run``, ``restore``, ``status``.

``restore`` is not a convenience. SIGKILL runs no Python, so the only recovery path after
one is the persisted manifest — and ``run`` refuses to start while an unrestored manifest
exists, precisely so the recovery happens deliberately instead of being papered over by
the next battery snapshotting a mutated file as pristine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.probe_battery._battery import (
    Battery,
    BatteryDefinitionError,
    BatteryInterruptedError,
    run_battery,
)
from tools.probe_battery._snapshot import (
    RunStore,
    UnrestoredSnapshotError,
    find_unrestored,
    restore_pending,
    state_root,
)
from tools.probe_coverage import enumerate_claims


def _cmd_run(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    battery_path = Path(args.battery)
    try:
        data = json.loads(battery_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read battery file {battery_path}: {exc}", file=sys.stderr)
        return 2
    try:
        battery = Battery.from_json(data, base=project_root)
        result = run_battery(
            battery,
            project_root=project_root,
            state_base=state_root(project_root),
            timeout_s=args.timeout,
        )
    except BatteryDefinitionError as exc:
        print(f"battery definition error: {exc}", file=sys.stderr)
        return 2
    except UnrestoredSnapshotError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except BatteryInterruptedError as exc:
        # The tree is already restored — the driver's `finally` ran because the signal was
        # turned into an exception, and it printed the partial report on the way out. Say
        # so, so nobody hand-restores over a clean tree.
        print(f"\n{exc} — the tree was restored before exiting.", file=sys.stderr)
        return 130
    # `run_battery` already echoed the report (AC-6); printing it again here would
    # double every battery's output.
    return 0 if result.passed else 1


def _cmd_restore(args: argparse.Namespace) -> int:
    base = state_root(Path(args.project_root).resolve())
    try:
        recovered = restore_pending(base)
    except UnrestoredSnapshotError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not recovered:
        print(f"nothing to restore — no unrestored runs under {base}")
        return 0
    for run_dir in recovered:
        print(f"restored {run_dir.name}")
    print(f"\n{len(recovered)} run(s) restored byte-identically.")
    return 0


def _cmd_keys(args: argparse.Namespace) -> int:
    """List each module's claims by ``stable_key`` — the address a probe must declare.

    This exists because the driver *mandates* ``stable_key`` addressing (AC-5) while the
    only other listing path, ``python -m tools.probe_coverage``, prints the line-numbered
    ``claim_id``. Making a battery author derive one form from the other by hand is how
    s253 ended up hand-rolling its own key beside the one it had imported.
    """
    total = 0
    for raw in args.paths:
        path = Path(raw)
        claims = enumerate_claims(path)
        total += len(claims)
        print(f"--- {path} ({len(claims)} claims) ---")
        for claim in claims:
            flag = "  ⚠️ CONJUNCTION" if claim.multi else ""
            print(f"  {claim.stable_key}")
            print(f"      L{claim.lineno}  [{claim.kind}]  {claim.source}{flag}")
    print(f"\ntotal claims: {total}")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    base = state_root(Path(args.project_root).resolve())
    pending = find_unrestored(base)
    print(f"state directory: {base}")
    if not pending:
        print("no unrestored runs — a battery may start.")
        return 0
    print(f"🔴 {len(pending)} unrestored run(s) — `run` will refuse until these are restored:")
    for run_dir in pending:
        try:
            manifest = RunStore.load(run_dir).manifest
        except (OSError, json.JSONDecodeError, TypeError):
            print(f"  {run_dir.name}: manifest unreadable — restore by hand")
            continue
        subjects = ", ".join(Path(e.subject).name for e in manifest.entries) or "<none>"
        print(f"  {run_dir.name}: pid={manifest.pid} head={manifest.head_sha[:8]} → {subjects}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="probe_battery", description=__doc__)
    parser.add_argument(
        "--project-root", default=".", help="repository root the battery runs against"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run a battery file")
    run_parser.add_argument("--battery", required=True, help="path to the battery JSON file")
    run_parser.add_argument(
        "--timeout", type=int, default=600, help="per-probe pytest timeout in seconds"
    )
    run_parser.set_defaults(func=_cmd_run)

    restore_parser = sub.add_parser("restore", help="restore snapshots left by a killed run")
    restore_parser.set_defaults(func=_cmd_restore)

    keys_parser = sub.add_parser("keys", help="list a module's claims by stable_key")
    keys_parser.add_argument("paths", nargs="+", help="test modules to enumerate")
    keys_parser.set_defaults(func=_cmd_keys)

    status_parser = sub.add_parser("status", help="show unrestored runs")
    status_parser.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
