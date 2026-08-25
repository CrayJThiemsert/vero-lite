"""Snapshot, mutate and restore the source files a battery deliberately breaks.

**The guarantee, and its limit.** A battery edits real tracked source. If it dies
mid-run, the tree is left broken — and the next thing to read that tree may be a test
suite, a commit, or the Axis-B goal gate. So restore is defended twice:

- **SIGTERM** is handled and ``try/finally`` runs, which covers an interrupt, a timeout
  kill, and an ordinary exception.
- **SIGKILL runs no Python at all**, so no handler can help. The guarantee there is the
  *persisted manifest*: every snapshot is on disk with its sha256 **before** the
  corresponding mutation is written, so a later ``restore`` invocation recovers
  byte-identically, and a battery refuses to start while an unrestored manifest exists.
  Refusing is the load-bearing half — a driver that silently started over a broken tree
  would snapshot the *mutated* file as the original and make the damage permanent.

**Writes are atomic** (tmpfile + :func:`os.replace`, the ``_goal_state.save_goal``
posture): a reader sees old-or-new, never a truncated subject. This matters because the
readers here include a pytest subprocess we started on purpose.

⚠️ **Freshness is a counter, not a clock.** WSL2's wall clock steps backwards, so the
manifest carries a monotonic ``heartbeat`` integer alongside its timestamp and nothing in
this module orders runs by time.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

#: Overrides where run state lives. Part of the ``CLAUDE_*`` testability family already
#: used by ``.claude/hooks/_goal_state.py`` — a test must never be able to trip over, or
#: clobber, a real battery's snapshots.
STATE_ENV = "CLAUDE_PROBE_BATTERY_STATE"

MANIFEST_NAME = "manifest.json"

STATUS_ACTIVE = "active"
STATUS_RESTORED = "restored"


class UnrestoredSnapshotError(RuntimeError):
    """Raised when a battery would start on a tree a dead run may still have mutated."""


class MutationError(RuntimeError):
    """Raised when a probe's ``old`` text is not present exactly once in its subject."""


def state_root(project_root: Path) -> Path:
    """Where run directories live: ``$CLAUDE_PROBE_BATTERY_STATE`` or the repo default."""
    override = os.environ.get(STATE_ENV)
    if override:
        return Path(override)
    return project_root / ".claude" / "state" / "probe_battery"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head_sha(project_root: Path) -> str:
    """Best-effort ``git rev-parse HEAD`` — recorded so a recovered snapshot can be
    matched to the commit it was taken against. Never fatal: a battery is still valid in
    a tree that is not a git checkout."""
    try:
        proc = subprocess.run(  # noqa: S603 — fixed git argv, no shell
            ["git", "rev-parse", "HEAD"],  # noqa: S607 — PATH-resolved git intended
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _as_int(value: object, default: int = 0) -> int:
    """Tolerant int coercion for manifest fields — a hand-edited manifest must degrade to
    a default rather than crash the recovery path that is trying to read it."""
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return default


@dataclass
class SnapshotEntry:
    """One subject file's pristine bytes, addressed by content hash."""

    subject: str
    backup: str
    original_sha256: str
    mutated_sha256: str | None = None


@dataclass
class Manifest:
    """The crash-recovery record. Written before the first mutation, not after."""

    run_id: str
    project_root: str
    pid: int
    head_sha: str
    created: str
    status: str = STATUS_ACTIVE
    heartbeat: int = 0
    heartbeat_ts: str = ""
    #: The pytest subprocess currently in flight, recorded so a SIGKILLed driver's orphan
    #: can be reaped by the recovery path. Nothing a dying process does can prevent the
    #: orphan — but the manifest outlives the process, and `restore` reads it.
    child_pid: int | None = None
    child_cmdline: str = ""
    entries: list[SnapshotEntry] = field(default_factory=list)

    def to_json(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, object]) -> Manifest:
        raw_entries = data.get("entries")
        entries = (
            [SnapshotEntry(**e) for e in raw_entries if isinstance(e, dict)]
            if isinstance(raw_entries, list)
            else []
        )
        return cls(
            run_id=str(data.get("run_id", "")),
            project_root=str(data.get("project_root", "")),
            pid=_as_int(data.get("pid")),
            head_sha=str(data.get("head_sha", "")),
            created=str(data.get("created", "")),
            status=str(data.get("status", STATUS_ACTIVE)),
            heartbeat=_as_int(data.get("heartbeat")),
            heartbeat_ts=str(data.get("heartbeat_ts", "")),
            child_pid=_as_int(data.get("child_pid")) or None,
            child_cmdline=str(data.get("child_cmdline", "")),
            entries=entries,
        )


def invalidate_bytecode(subject: Path) -> list[Path]:
    """Delete any cached bytecode for ``subject``. Returns what was removed.

    🔴 **Reaching disk is not the same as reaching the interpreter.** CPython validates a
    ``.pyc`` against its source by *(mtime-in-whole-seconds, size)*. A mutation that does
    not change the file's length — ``return "even"`` → ``return "EVEN"`` — and lands in the
    same wall-clock second as the previous compile is therefore judged *unchanged*, and the
    child process imports the **stale** bytecode. The battery then reports ``GREEN``: "the
    mutation reached disk and nothing reddened, the guard may be vacuous" — when in truth
    the guard was never exercised at all. That is a false negative of exactly the kind this
    package exists to prevent, and it is invisible on a slow machine.

    Measured 2026-08-25: CI reddened on this while the same commit passed locally.

    Called on every mutate **and** every restore, because the restore writes a same-size
    file too — leaving a probe's bytecode cached for the *next* probe's run.
    """
    cache = subject.parent / "__pycache__"
    if not cache.is_dir():
        return []
    removed: list[Path] = []
    for stale in cache.glob(f"{subject.stem}.*.pyc"):
        with suppress(OSError):
            stale.unlink()
            removed.append(stale)
    return removed


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """tmpfile in the target directory + :func:`os.replace` — atomic on one filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=str(path.parent), delete=False, prefix=path.name + ".", suffix=".tmp"
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


class RunStore:
    """One battery run's snapshot directory, manifest, and restore obligation."""

    def __init__(self, run_dir: Path, manifest: Manifest) -> None:
        self.run_dir = run_dir
        self.manifest = manifest

    # -- lifecycle ---------------------------------------------------------------

    @classmethod
    def begin(cls, project_root: Path, root: Path | None = None) -> RunStore:
        base = root if root is not None else state_root(project_root)
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        run_dir = base / run_id
        (run_dir / "snapshots").mkdir(parents=True, exist_ok=True)
        manifest = Manifest(
            run_id=run_id,
            project_root=str(project_root.resolve()),
            pid=os.getpid(),
            head_sha=_head_sha(project_root),
            created=datetime.now(UTC).isoformat(),
        )
        store = cls(run_dir, manifest)
        store._flush()
        return store

    @classmethod
    def load(cls, run_dir: Path) -> RunStore:
        data = json.loads((run_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
        return cls(run_dir, Manifest.from_json(data))

    def _flush(self) -> None:
        payload = json.dumps(self.manifest.to_json(), indent=2, sort_keys=True)
        _atomic_write_bytes(self.run_dir / MANIFEST_NAME, payload.encode("utf-8"))

    def heartbeat(self) -> None:
        """Bump the monotonic counter (and stamp a time, which is advisory only)."""
        self.manifest.heartbeat += 1
        self.manifest.heartbeat_ts = datetime.now(UTC).isoformat()
        self._flush()

    def set_child(self, pid: int, cmdline: str) -> None:
        """Record the pytest subprocess in flight, so a kill leaves a reapable trail."""
        self.manifest.child_pid = pid
        self.manifest.child_cmdline = cmdline
        self._flush()

    def clear_child(self) -> None:
        self.manifest.child_pid = None
        self.manifest.child_cmdline = ""
        self._flush()

    # -- mutate / restore --------------------------------------------------------

    def _entry_for(self, subject: Path) -> SnapshotEntry | None:
        key = str(subject.resolve())
        for entry in self.manifest.entries:
            if str(Path(entry.subject).resolve()) == key:
                return entry
        return None

    def snapshot(self, subject: Path) -> SnapshotEntry:
        """Copy ``subject``'s pristine bytes aside. Idempotent per subject.

        Re-snapshotting a file the run has already mutated would record the mutation as
        the original — so the first snapshot always wins.
        """
        existing = self._entry_for(subject)
        if existing is not None:
            return existing
        backup = self.run_dir / "snapshots" / f"{len(self.manifest.entries):02d}-{subject.name}"
        shutil.copyfile(subject, backup)
        entry = SnapshotEntry(
            subject=str(subject.resolve()),
            backup=str(backup.resolve()),
            original_sha256=sha256_of(subject),
        )
        self.manifest.entries.append(entry)
        self._flush()
        return entry

    def apply(self, subject: Path, old: str, new: str) -> str:
        """Snapshot, then replace ``old`` with ``new`` — and prove the write reached disk.

        ``old`` must appear **exactly once**. Zero occurrences means the probe is a no-op
        and any green it produces is meaningless; more than one means the mutation's blast
        radius is not what the author declared. Both refuse rather than proceed.

        Returns the sha256 of the file **re-read from disk**, so a silent no-op cannot be
        reported as a mutation that ran.
        """
        entry = self.snapshot(subject)
        source = subject.read_text(encoding="utf-8")
        hits = source.count(old)
        if hits != 1:
            raise MutationError(
                f"{subject.name}: the mutation's `old` text occurs {hits} times, expected "
                f"exactly 1. A zero-occurrence mutation is a no-op whose GREEN proves "
                f"nothing; a repeated one edits more than the probe declared. Text: {old!r}"
            )
        mutated = source.replace(old, new, 1)
        _atomic_write_bytes(subject, mutated.encode("utf-8"))

        on_disk = subject.read_text(encoding="utf-8")
        if on_disk != mutated:  # pragma: no cover - a filesystem that lied to us
            raise MutationError(f"{subject.name}: the mutation did not survive the write")
        digest = sha256_of(subject)
        if digest == entry.original_sha256:
            raise MutationError(
                f"{subject.name}: the file is byte-identical after the mutation — the "
                f"probe changed nothing, so any outcome it reports is about the "
                f"unmutated code"
            )
        invalidate_bytecode(subject)
        entry.mutated_sha256 = digest
        self._flush()
        return digest

    def restore(self, subject: Path) -> bool:
        """Put one subject's pristine bytes back. Returns whether a snapshot existed."""
        entry = self._entry_for(subject)
        if entry is None:
            return False
        self._restore_entry(entry)
        return True

    def _restore_entry(self, entry: SnapshotEntry) -> None:
        backup = Path(entry.backup)
        target = Path(entry.subject)
        _atomic_write_bytes(target, backup.read_bytes())
        invalidate_bytecode(target)
        restored = sha256_of(target)
        if restored != entry.original_sha256:  # pragma: no cover - defended, never seen
            raise RuntimeError(
                f"restore of {target} is NOT byte-identical: {restored} != "
                f"{entry.original_sha256}. The pristine bytes are still at {backup}."
            )
        entry.mutated_sha256 = None

    def restore_all(self) -> None:
        """Restore every snapshot and discharge the run's obligation."""
        for entry in self.manifest.entries:
            self._restore_entry(entry)
        self.manifest.status = STATUS_RESTORED
        self._flush()


def find_unrestored(base: Path) -> list[Path]:
    """Every run directory whose manifest still claims an outstanding mutation.

    A manifest we cannot parse counts as unrestored. Treating unreadable state as "fine"
    is how a driver talks itself into starting on a broken tree.
    """
    if not base.exists():
        return []
    out: list[Path] = []
    for manifest_path in sorted(base.glob(f"*/{MANIFEST_NAME}")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            status = str(data.get("status", STATUS_ACTIVE))
        except (OSError, json.JSONDecodeError):
            out.append(manifest_path.parent)
            continue
        if status != STATUS_RESTORED:
            out.append(manifest_path.parent)
    return out


def refuse_if_unrestored(base: Path) -> None:
    """The AC-1 refusal: never begin a battery over a tree a dead run may hold."""
    stale = find_unrestored(base)
    if not stale:
        return
    names = ", ".join(p.name for p in stale)
    raise UnrestoredSnapshotError(
        f"{len(stale)} unrestored probe-battery run(s) present ({names}). A previous "
        f"battery died without restoring, so this tree may still carry its mutations — "
        f"snapshotting it now would record a mutated file as the original and make the "
        f"damage permanent. Recover first:\n"
        f"    python -m tools.probe_battery restore\n"
        f"State directory: {base}"
    )


def reap_child(manifest: Manifest, grace_s: float = 2.0) -> bool:
    """Kill the pytest subprocess a SIGKILLed driver left behind. Returns whether one died.

    **Why this is here and not in the driver.** SIGKILL runs no Python, so a killed driver
    cannot take its child down with it — the pytest process keeps running, holding whatever
    the test held. This repo has already paid for that shape once: a leaked session at the
    head of a three-deep lock chain hung a suite for 67 minutes. The manifest outlives the
    driver, so the recovery path is the one place that can still clean up.

    **The pid-reuse guard is the exact cmdline**, not "is a pid alive": between the kill and
    the recovery the OS may have handed that number to something else, and this function
    sends signals. Linux-only (it reads ``/proc``); a no-op elsewhere.
    """
    pid = manifest.child_pid
    if not pid or not manifest.child_cmdline:
        return False
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False  # already gone, or no /proc on this platform
    live = raw.replace(b"\0", b" ").decode("utf-8", errors="replace").strip()
    if live != manifest.child_cmdline.strip():
        return False  # the pid was recycled — signalling it would hit a bystander
    try:
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + grace_s
        while time.monotonic() < deadline:
            if not Path(f"/proc/{pid}").exists():
                return True
            time.sleep(0.05)
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return False
    return True


def restore_pending(base: Path) -> list[Path]:
    """Restore every unrestored run, reaping any orphaned pytest child on the way.

    Returns the run directories that were recovered.
    """
    recovered: list[Path] = []
    for run_dir in find_unrestored(base):
        try:
            store = RunStore.load(run_dir)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            raise UnrestoredSnapshotError(
                f"{run_dir.name}: manifest is unreadable ({exc}). The pristine bytes are "
                f"still under {run_dir / 'snapshots'} — restore by hand, then delete the "
                f"run directory."
            ) from exc
        # Reap first: the orphan is still executing the code we are about to put back, and
        # a test mid-flight against a file that changes underneath it reports nonsense.
        reap_child(store.manifest)
        store.clear_child()
        store.restore_all()
        recovered.append(run_dir)
    return recovered
