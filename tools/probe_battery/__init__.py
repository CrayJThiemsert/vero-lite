"""The shipped probe-battery driver (PLAN-0115 Step 1).

A probe battery answers "did my mutations redden the assertions I predicted?" — the
witnessed-RED discipline CLAUDE.md §8 makes binding. Before this package, every session
rebuilt that driver from scratch in ``/tmp``, and session 253 measured what a fresh one
does by default: it re-makes four defect classes an earlier session had already fixed.

Two names in ``tools/`` sound alike and are unrelated:

- **``tools/probe_battery/``** (here) — the *mutation* battery driver: break a line on
  purpose, run one test, decide whether the declared assertion is what failed.
- **``tools/probes/``** — live *liveness* probes (e.g. the vero-bridge reachability
  check). Nothing to do with mutation testing.

Library entry point::

    from tools.probe_battery import Battery, Probe, run_battery

    result = run_battery(battery, project_root=Path.cwd())
    print(result.report)          # always rendered, including on failure
    assert result.passed

CLI::

    python -m tools.probe_battery run --battery battery.json
    python -m tools.probe_battery restore     # after a SIGKILL
    python -m tools.probe_battery status

Full mechanics, the battery-file schema, and the measured pytest facts the classifier
rests on: ``tools/probe_battery/README.md``.
"""

from tools.probe_battery._battery import (
    DEFAULT_TIMEOUT_S,
    VERDICT_FAIL,
    VERDICT_PASS,
    Battery,
    BatteryDefinitionError,
    BatteryInterruptedError,
    BatteryResult,
    Probe,
    ProbeResult,
    run_battery,
)
from tools.probe_battery._lock import (
    LOCK_ENV,
    STALE_AFTER_S,
    BatteryLock,
    LockHandle,
    defers_path,
    lock_path,
)
from tools.probe_battery._outcome import (
    ASSERTION_FAMILY,
    CREDITING_OUTCOMES,
    CaseRecord,
    Classification,
    Outcome,
    classify,
    parse_junit,
)
from tools.probe_battery._snapshot import (
    STATE_ENV,
    MutationError,
    RunStore,
    UnrestoredSnapshotError,
    find_unrestored,
    refuse_if_unrestored,
    restore_pending,
    state_root,
)

__all__ = [
    "ASSERTION_FAMILY",
    "CREDITING_OUTCOMES",
    "DEFAULT_TIMEOUT_S",
    "LOCK_ENV",
    "STALE_AFTER_S",
    "STATE_ENV",
    "VERDICT_FAIL",
    "VERDICT_PASS",
    "Battery",
    "BatteryDefinitionError",
    "BatteryInterruptedError",
    "BatteryLock",
    "BatteryResult",
    "CaseRecord",
    "Classification",
    "LockHandle",
    "MutationError",
    "Outcome",
    "Probe",
    "ProbeResult",
    "RunStore",
    "UnrestoredSnapshotError",
    "classify",
    "defers_path",
    "find_unrestored",
    "lock_path",
    "parse_junit",
    "refuse_if_unrestored",
    "restore_pending",
    "run_battery",
    "state_root",
]
