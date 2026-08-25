"""The cross-process battery lock: "a deliberately-broken tree is in flight, stand down".

**The problem** (PLAN-0115 safety hole 1). A battery mutates real tracked source. The
Axis-B Stop-hook goal gate runs `check` criteria as subprocesses against that same tree and
fingerprints it as `sha256(HEAD + porcelain status)` — so while a battery runs, every Stop
event both (a) records **false** `fail` entries into `goal.json`'s **append-only** trail,
which no one can remove afterwards, and (b) reads the mutation as "new work", eligible to
dispatch the `goal-evaluator` against a tree that is broken on purpose.

**Why a file and not a real lock.** The driver runs WSL-side, where pytest runs; the Stop
hook runs Windows-side (`settings.json` invokes `python .claude/hooks/…`). An `fcntl` lock
is invisible across that boundary, so the protocol is a JSON file on the shared filesystem
that each side parses independently — no shared imports, no shared runtime.

⚠️ **Freshness is judged generously, and never by ordering two clocks.** WSL2's wall clock
steps backwards, so a lock that looks *younger* than it should is treated as **fresh**, not
as evidence of anything. Only a clearly-old positive age makes a lock stale. A dead driver
must not silence the gate forever — but nor may a clock hiccup un-silence it mid-battery.

**Where the gate lives** (CLAUDE.md §4, and PLAN-0115 R-C): the gate's *logic* is in the
tracked `.claude/hooks/_goal_gate.py`. This lock file, under gitignored `.claude/state/`, is
the ephemeral **state** that tracked gate reads — never the gate itself.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

#: Overrides the lock path. Part of the ``CLAUDE_*`` testability family the goal gate
#: already uses, so a test can never collide with — or be silenced by — a real battery.
LOCK_ENV = "CLAUDE_PROBE_BATTERY_LOCK"

DEFAULT_LOCK_RELPATH = Path(".claude") / "state" / "probe_battery.lock"

#: Suffix of the sidecar the GATE appends to, one line per stand-down. Separate from the
#: lock so the two writers never touch the same bytes: the driver owns the lock, the gate
#: owns the tally.
DEFERS_SUFFIX = ".defers"

#: Generous on purpose (R-D). The cost of being too generous is that a crashed driver
#: silences the gate for this long; the cost of being too strict is that the gate wakes up
#: mid-battery and evaluates a deliberately-broken tree — which is the failure this exists
#: to prevent. Tens of minutes, not minutes.
STALE_AFTER_S = 45 * 60

TELEGRAM_TIMEOUT_S = 5


def lock_path(project_root: Path) -> Path:
    override = os.environ.get(LOCK_ENV)
    return Path(override) if override else project_root / DEFAULT_LOCK_RELPATH


def defers_path(lock: Path) -> Path:
    return lock.with_name(lock.name + DEFERS_SUFFIX)


@dataclass
class BatteryLock:
    """The on-disk protocol. Read by the gate; written only by the driver."""

    run_id: str
    pid: int
    head_sha: str
    acquired: str
    heartbeat: int = 0
    heartbeat_ts: str = ""
    writer: str = "tools.probe_battery"


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(path.parent), delete=False, suffix=".tmp"
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


class LockHandle:
    """A held battery lock. Acquire before the first mutation, release after restore."""

    def __init__(self, path: Path, state: BatteryLock) -> None:
        self.path = path
        self.state = state

    @classmethod
    def acquire(cls, project_root: Path, run_id: str, head_sha: str) -> LockHandle:
        path = lock_path(project_root)
        state = BatteryLock(
            run_id=run_id,
            pid=os.getpid(),
            head_sha=head_sha,
            acquired=datetime.now(UTC).isoformat(),
            heartbeat_ts=datetime.now(UTC).isoformat(),
        )
        handle = cls(path, state)
        handle._flush()
        # A stale tally from a previous run would make this run think it deferred Stops it
        # never saw, so the counter starts from zero with the lock.
        defers_path(path).unlink(missing_ok=True)
        return handle

    def _flush(self) -> None:
        _atomic_write(self.path, json.dumps(asdict(self.state), indent=2, sort_keys=True))

    def heartbeat(self) -> None:
        """Refresh liveness. Called per probe — the gate reads this, not the pid."""
        self.state.heartbeat += 1
        self.state.heartbeat_ts = datetime.now(UTC).isoformat()
        self._flush()

    def defer_count(self) -> int:
        """How many Stop events the gate stood down for while this lock was held."""
        tally = defers_path(self.path)
        if not tally.exists():
            return 0
        try:
            return len([ln for ln in tally.read_text(encoding="utf-8").splitlines() if ln.strip()])
        except OSError:
            return 0

    def release(self) -> int:
        """Drop the lock. Returns the defer count so the caller can report it once."""
        deferred = self.defer_count()
        self.path.unlink(missing_ok=True)
        defers_path(self.path).unlink(missing_ok=True)
        return deferred


def ping_telegram(project_root: Path, event: str, detail: str) -> bool:
    """Best-effort Telegram note. Returns whether the notifier was actually invoked.

    **Telegram rather than stderr, and this is not a preference** (PLAN-0115 SD-2, ruled).
    Claude Code's contract is that stderr from a hook exiting 0 goes to the debug log only —
    never the transcript, never to Claude — and the repo already carries four exit-0 stderr
    notes in that invisible class, none of them asserted by any test. ADR-0018 VX-1 names
    Telegram *"D5's warn channel of record"*, and per §1 precedence an Accepted ADR outranks
    a PLAN, which is why the PLAN's unsourced `no Telegram` clause was struck.

    **Keyed to the lock, not to each defer**: the lock is held once per battery while Stop
    fires every turn, so a per-defer ping would emit several per battery — the only spam
    shape anyone could reasonably have been guarding against.
    """
    script = project_root / "tools" / "notify" / "telegram.sh"
    if not script.exists():
        return False
    body = f"[vero-lite/probe_battery_{event}]\n{detail}"
    try:
        subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["bash", str(script), body],  # noqa: S607 — PATH-resolved bash intended
            capture_output=True,
            text=True,
            check=False,
            timeout=TELEGRAM_TIMEOUT_S,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return True
