"""CLI for the golden-trace producer.

``check``   — report every trace whose recorded envelope no longer matches a
              fresh composition. Exit 0 clean, 1 on drift, 2 on error.
``refresh`` — recompute and write ``expected_envelope`` for every trace. This
              ACCEPTS the system's current output as the new expectation, so
              run it deliberately and review the diff it produces.
"""

from __future__ import annotations

import argparse
import sys

from tools.golden_trace.producer import check, refresh, trace_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.golden_trace")
    parser.add_argument("command", choices=("check", "refresh"))
    args = parser.parse_args(argv)

    paths = trace_paths()
    if not paths:
        print("ERROR: no golden traces found — the corpus is empty", file=sys.stderr)
        return 2

    if args.command == "refresh":
        changed = [path.name for path in paths if refresh(path)]
        for name in changed:
            print(f"refreshed: {name}")
        print(f"GOLDEN-TRACE-REFRESH: {len(changed)} of {len(paths)} trace(s) rewritten")
        return 0

    drifted = {path.name: check(path) for path in paths}
    drifted = {name: keys for name, keys in drifted.items() if keys}
    for name, keys in drifted.items():
        print(f"DRIFT {name}: {', '.join(keys)}", file=sys.stderr)
    if drifted:
        print(f"GOLDEN-TRACE-CHECK: FAIL ({len(drifted)} of {len(paths)} drifted)", file=sys.stderr)
        return 1
    print(f"GOLDEN-TRACE-CHECK: OK ({len(paths)} trace(s) match the system)")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
