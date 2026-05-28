"""vero-bridge audit log writer (AC-4 (b); stdlib-only).

Append-only JSONL audit log for every server-accepted *and* server-rejected
call. Captured signals per PLAN-0012 AC-4 (b) +
`docs/conventions/vero-bridge-wire-format.md` §5.2:

- ``ts_ns`` — high-res monotonic timestamp (the OQ-T4 serial-per-instance
  ordering primary key)
- ``ts_iso`` — ISO-8601 wall-clock timestamp (human-readable secondary)
- ``monotonic_counter`` — per-server-process call counter (resolves ts_ns
  ties; survives across calls within one server process)
- ``tool_name`` — the bridge tool that received the call
- ``claimed_tag`` — caller's self-asserted identity (verbatim or ``repr``
  if malformed); audit-only per OQ-T3 Option I
- ``pid`` / ``ppid`` — server process ids (per-spawn identifiers under
  the tab-group routing model — Lesson #0017 §3.1 corrected)
- ``stdin_fd`` / ``stdout_fd`` — readlinks of ``/proc/self/fd/{0,1}``
  (per-connection pipe inodes; useful for the AC-4 (c) anti-spoof matrix)
- ``env_keys_seen`` — sorted list of ``CLAUDE_*`` / ``MCP_*`` /
  ``ANTHROPIC_*`` keys visible to the server (empirically ``[]`` per
  ``bridge_whoami`` probe — Desktop strips env)
- ``version`` — wire-format version asserted in the envelope (echoed even
  on mismatch reject so the audit log captures the spoof attempt)
- ``outcome`` — ``"ok"`` when the envelope parsed and the tool ran;
  ``"error"`` otherwise
- ``error_code`` — present (and matches one of :class:`ErrorCode`) only
  when ``outcome == "error"``; ``null`` otherwise

The default Phase 1 log path is
``docs/research/private/vero-bridge-audit.jsonl`` (gitignored). The
directory is created if missing. Records are appended one per line in
strict JSON (no trailing comma, no pretty-printing, sorted keys for
diff stability).

Phase 2+ may relocate the audit channel to a tracked-but-redacted
destination once authority operations land on the bridge; the writer
API stays the same (caller injects the path).
"""

from __future__ import annotations

import datetime as _dt
import itertools
import json
import os
import time
from pathlib import Path
from threading import Lock
from typing import Any

#: Phase 1 default log path. Resolved relative to the repo root at
#: import time (the server's working directory is set by the Desktop
#: spawn command — see `mcpServers.vero-bridge` entry).
DEFAULT_LOG_PATH: Path = Path("docs/research/private/vero-bridge-audit.jsonl")

#: Env var prefixes captured into ``env_keys_seen``. Matches the probe's
#: filter for consistency across audit + empirical-probe outputs.
_OBSERVABLE_ENV_PREFIXES: tuple[str, ...] = ("CLAUDE_", "MCP_", "ANTHROPIC_")

#: Per-process monotonic call counter. Cycles indefinitely; rolls over
#: only on process restart.
_counter = itertools.count(start=1)

#: Guard against concurrent writes from the same process. The OQ-T4
#: serial-per-instance discipline is enforced at the server layer, but
#: this lock is belt-and-braces — if a future change adds threaded
#: handlers, the audit log line atomicity still holds.
_write_lock = Lock()


def _read_proc_fd(fd: int) -> str:
    """Best-effort readlink of ``/proc/self/fd/<fd>``. Returns a sentinel
    on platforms where ``/proc`` is unavailable (Windows, macOS) so the
    audit log degrades gracefully rather than crashing."""
    try:
        return os.readlink(f"/proc/self/fd/{fd}")
    except OSError as exc:
        return f"<unavailable: {type(exc).__name__}>"


def _safe_claimed_tag(value: Any) -> str:
    """Best-effort rendering of the caller's ``claimed_tag``.

    Audit-log records the *claimed* tag even when the envelope rejected
    it (so spoof-with-malformed-tag attempts are visible). When the value
    isn't a string, ``repr`` it so the JSON record stays well-formed —
    don't silently coerce non-str to str.
    """
    if isinstance(value, str):
        return value
    return repr(value)


def _safe_version(value: Any) -> Any:
    """Echo the caller's version even on mismatch reject — but only when
    it's JSON-serializable as-is. Otherwise ``repr`` it."""
    if isinstance(value, bool):
        # bool is JSON-serializable but it's almost certainly a spoof — render verbatim
        # but with a label so the reviewer notices the type confusion.
        return f"<bool:{value!r}>"
    if isinstance(value, int | str | float) or value is None:
        return value
    return repr(value)


def _observable_signals() -> dict[str, Any]:
    """Snapshot the server-side observable signals at the moment of the
    call. The schema-level OQ-T3 Option I selection rationale leans on
    these — they are what the server CAN see, regardless of what the
    client CLAIMS."""
    return {
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "stdin_fd": _read_proc_fd(0),
        "stdout_fd": _read_proc_fd(1),
        "env_keys_seen": sorted(k for k in os.environ if k.startswith(_OBSERVABLE_ENV_PREFIXES)),
    }


def build_record(
    *,
    tool_name: str,
    claimed_tag: Any,
    version: Any,
    outcome: str,
    error_code: str | None = None,
) -> dict[str, Any]:
    """Build one audit record dict. Pure function (no I/O); callers pass
    the result to :func:`write_record` to persist.

    Returned dict is JSON-serializable. The shape is the canonical
    audit record for AC-4 (b); test fixtures may assert against this
    shape directly.
    """
    now = _dt.datetime.now(_dt.UTC)
    return {
        "ts_ns": time.time_ns(),
        "ts_iso": now.isoformat(timespec="microseconds"),
        "monotonic_counter": next(_counter),
        "tool_name": tool_name,
        "claimed_tag": _safe_claimed_tag(claimed_tag),
        "version": _safe_version(version),
        "outcome": outcome,
        "error_code": error_code,
        **_observable_signals(),
    }


def write_record(record: dict[str, Any], log_path: Path | None = None) -> None:
    """Append one record to the audit log, atomically.

    The default destination is :data:`DEFAULT_LOG_PATH`; callers may
    override via ``log_path`` (used by tests + by callers that route
    audit output elsewhere — Phase 2+ tracked-but-redacted destination).

    Atomicity contract: the record is serialized to a single JSON line +
    written under a process-level lock + flushed before release. Other
    server processes writing to the same file rely on OS-level append
    atomicity (``O_APPEND`` + small write < PIPE_BUF on Linux).
    """
    path = log_path if log_path is not None else DEFAULT_LOG_PATH
    line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    with _write_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        # O_APPEND ensures write is atomic at OS level for small records;
        # CPython open() in text 'a' mode uses O_APPEND on POSIX.
        with path.open("a", encoding="utf-8") as fp:
            fp.write(line)
            fp.flush()


def log_call(
    *,
    tool_name: str,
    claimed_tag: Any,
    version: Any,
    outcome: str,
    error_code: str | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Convenience: build + persist one audit record in one call.

    Returns the persisted record (for caller-side debugging or
    test-side assertion). Always returns a dict — never raises (audit
    failures are swallowed and surfaced via the returned record's
    ``audit_io_error`` key when present, so a write failure cannot
    take down the call path)."""
    record = build_record(
        tool_name=tool_name,
        claimed_tag=claimed_tag,
        version=version,
        outcome=outcome,
        error_code=error_code,
    )
    try:
        write_record(record, log_path=log_path)
    except OSError as exc:
        # Audit log I/O failure must not take down the call — but it
        # must surface somewhere. Attach the error class to the
        # returned record so the caller sees the failure in test
        # output / server stderr.
        record["audit_io_error"] = type(exc).__name__
    return record


def reset_counter_for_test() -> None:
    """Reset the per-process monotonic counter. **Test-only.**

    Production code MUST NOT call this — the counter's monotonicity
    across a server process is part of the AC-4 (b) audit contract."""
    global _counter
    _counter = itertools.count(start=1)
