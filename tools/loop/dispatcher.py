#!/usr/bin/env python3
"""PLAN-0010 loop dispatcher: consumer poller (Step 3b).

Reads ``loop/inbox/*.msg.md`` in filesystem-mtime order, parses each
message via :mod:`tools.loop._schema`, dispatches to a message-type
handler, and atomically archives the message to ``loop/processed/``.

Lifecycle invariants (binding per PLAN-0010 Step 1 §5):

* Either ``loop/inbox/<name>`` exists or ``loop/processed/<name>``
  exists — never both, never neither (POSIX atomic rename on same fs;
  same-fs check enforced at startup per §8 residual risk #1)
* Filename-keyed idempotency: a re-scan of an already-processed
  message is a no-op (covers consumer crash mid-mv recovery)
* Parse failure → archive immediately with ``.parse-error.log``
  sibling; do NOT retry (Step 1 §5 binding — content cannot change
  on retry)
* Expired (``now > expires_after``) → archive with ``.expired.log``;
  do not dispatch
* Dispatch handler raises → leave in inbox, increment per-message
  failure count; when failures reach ``poison_threshold`` (default
  3), archive as poison + emit alert + remove from inbox so it does
  not retry (a poison-detection analog of PLAN-0008 L3/L4 — same
  spirit, dispatcher-local state because the dispatcher is a
  standalone process tree separate from the Code harness counter)

Retention (binding per PLAN-0010 Step 1 §6):

* Prune at end of each scan cycle
* Eligible if older than ``retention_age_days`` (default 30) OR if
  total ``processed/`` size exceeds ``retention_size_bytes``
  (default 100 MB)
* Preserve at least ``retention_floor`` (default 200) most-recent
  entries even when otherwise eligible
* One-line summary logged to stdout

Stdlib-only. Telegram integration is via the same
``tools/notify/telegram.sh`` script used by Phase 1
``notification_telegram.py`` + Phase 2
``pretooluse_loop_detect.py``; graceful no-op when the env vars
``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_CHAT_ID`` are unset.

CLI: ``python -m tools.loop.dispatcher`` runs one scan cycle then
exits — scheduling is delegated to the host (Code Desktop scheduled
task per PLAN-0010 §Step 3 + Lesson #9 Sonnet 4.6 + Auto floor).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from tools.loop._schema import (
    LoopMessage,
    MessageType,
    ValidationError,
    parse_message_file,
)

LOGGER = logging.getLogger("tools.loop.dispatcher")

DEFAULT_INBOX = Path("loop/inbox")
DEFAULT_PROCESSED = Path("loop/processed")
DEFAULT_FAILURES_STATE = Path("loop/.failures.json")

DEFAULT_RETENTION_AGE_DAYS = 30
DEFAULT_RETENTION_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
DEFAULT_RETENTION_FLOOR = 200
DEFAULT_POISON_THRESHOLD = 3  # consecutive failures on the same message

DEFAULT_TELEGRAM_SCRIPT = Path("tools/notify/telegram.sh")
TELEGRAM_TIMEOUT_SEC = 5


class DispatchResult(str, Enum):
    """Per-message outcome of a single scan iteration."""

    OK = "ok"
    PARSE_FAILED = "parse_failed"
    EXPIRED = "expired"
    DISPATCH_FAILED = "dispatch_failed"
    POISON = "poison"
    SKIPPED_IDEMPOTENT = "skipped_idempotent"


# Handler signature: (message) -> Any. Raise on failure (the
# dispatcher catches + tracks per-message failures + escalates to
# poison archival when threshold met).
Handler = Callable[[LoopMessage], None]


def _default_smoke_heartbeat_handler(message: LoopMessage) -> None:
    """Default smoke_heartbeat handler: log + acknowledge.

    The smoke regression workload (PLAN-0010 §Step 5) extends this
    with a daily rollup that emits a smoke_receipt back into the loop;
    that extension lives outside the dispatcher core (Step 5 work).
    """
    LOGGER.info(
        "smoke_heartbeat: producer=%s claimed=%s subject=%s",
        message.producer_id,
        message.claimed_time.isoformat(),
        message.subject,
    )


def _default_noop_handler(message: LoopMessage) -> None:
    """Default no-op handler for message types without a registered handler.

    Logs the receipt + archives (the dispatcher does the archive after
    the handler returns); the no-op is intentional so that a producer
    emitting a future ``message_type`` does not crash a consumer that
    has not been upgraded yet.
    """
    LOGGER.info(
        "no-handler-registered: producer=%s type=%s — archiving as no-op",
        message.producer_id,
        message.message_type.value,
    )


DEFAULT_HANDLERS: dict[MessageType, Handler] = {
    MessageType.SMOKE_HEARTBEAT: _default_smoke_heartbeat_handler,
    MessageType.SMOKE_RECEIPT: _default_noop_handler,
    MessageType.STATUS_DIGEST: _default_noop_handler,
    MessageType.GOVERNANCE_REMINDER: _default_noop_handler,
    MessageType.DEFERRED_OQ_ROTATION: _default_noop_handler,
}


# --- Same-filesystem check (Step 1 §8 residual risk #1) ---


def check_same_filesystem(inbox: Path, processed: Path) -> bool:
    """Confirm inbox + processed live on the same filesystem.

    POSIX guarantees ``rename(2)`` is atomic only within one
    filesystem; the lifecycle invariant ("either inbox or processed,
    never both, never neither") depends on this. The dispatcher
    refuses to start if the assumption fails.
    """
    try:
        return inbox.stat().st_dev == processed.stat().st_dev
    except OSError:
        return False


# --- Per-message failure tracking (poison detection) ---


@dataclass
class FailureState:
    """In-memory + persistent per-message failure counts.

    Keyed by filename (not full path); a re-scan that finds the same
    filename in inbox after the dispatcher restarts will pick up the
    prior count from the persistent file.
    """

    counts: dict[str, int] = field(default_factory=dict)
    last_error_signatures: dict[str, str] = field(default_factory=dict)

    def increment(self, filename: str, error_signature: str) -> int:
        new_count = self.counts.get(filename, 0) + 1
        self.counts[filename] = new_count
        self.last_error_signatures[filename] = error_signature
        return new_count

    def clear(self, filename: str) -> None:
        self.counts.pop(filename, None)
        self.last_error_signatures.pop(filename, None)

    def to_json(self) -> dict[str, Any]:
        return {
            "counts": dict(self.counts),
            "last_error_signatures": dict(self.last_error_signatures),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> FailureState:
        return cls(
            counts={str(k): int(v) for k, v in (data.get("counts") or {}).items()},
            last_error_signatures={
                str(k): str(v) for k, v in (data.get("last_error_signatures") or {}).items()
            },
        )


def load_failure_state(path: Path) -> FailureState:
    """Read failure state from disk; return empty state if missing/corrupt."""
    if not path.exists():
        return FailureState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return FailureState()
    if not isinstance(data, dict):
        return FailureState()
    return FailureState.from_json(data)


def save_failure_state(path: Path, state: FailureState) -> None:
    """Persist failure state atomically (write to tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state.to_json(), indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


# --- Alert callback (Telegram + stderr fallback) ---


def _now_utc() -> datetime:
    """Wall-clock UTC. Indirected for tests."""
    return datetime.now(UTC)


def stderr_alert(reason: str, payload: dict[str, Any]) -> None:
    """Default alert callback: write a one-line JSON record to stderr."""
    record = {"alert": reason, **payload, "ts": _now_utc().isoformat()}
    print(json.dumps(record), file=sys.stderr)


def make_telegram_alert(script_path: Path) -> Callable[[str, dict[str, Any]], None]:
    """Build an alert callback that fires ``tools/notify/telegram.sh``.

    Graceful no-op if the script does not exist or fails; the consumer
    still archives the poison message + logs to stderr. The Phase 1
    telegram.sh itself no-ops when ``$TELEGRAM_BOT_TOKEN`` /
    ``$TELEGRAM_CHAT_ID`` are unset, so tests do not need to stub it.
    """

    def alert(reason: str, payload: dict[str, Any]) -> None:
        stderr_alert(reason, payload)  # always log to stderr too
        if not script_path.exists():
            return
        body = json.dumps({"reason": reason, **payload})
        try:
            # S603: argv elements are a hook-controlled script path + a JSON
            # payload we built; no shell interpolation. S607: "bash" relies on
            # PATH (same idiom as pretooluse_loop_detect.py).
            subprocess.run(  # noqa: S603
                ["bash", str(script_path)],  # noqa: S607
                input=body,
                text=True,
                capture_output=True,
                check=False,
                timeout=TELEGRAM_TIMEOUT_SEC,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

    return alert


# --- Scan cycle summary ---


@dataclass
class ScanCycleSummary:
    """End-of-cycle summary; one line to stdout per Step 1 §6 spec."""

    ok: int = 0
    parse_failed: int = 0
    expired: int = 0
    dispatch_failed: int = 0
    poison: int = 0
    skipped_idempotent: int = 0
    pruned: int = 0
    pruned_freed_bytes: int = 0
    pruned_oldest: str = ""

    def to_log_line(self) -> str:
        bits = [
            f"ok={self.ok}",
            f"parse_failed={self.parse_failed}",
            f"expired={self.expired}",
            f"dispatch_failed={self.dispatch_failed}",
            f"poison={self.poison}",
            f"skipped_idempotent={self.skipped_idempotent}",
            f"pruned={self.pruned}",
        ]
        if self.pruned:
            bits.append(f"pruned_oldest={self.pruned_oldest}")
            bits.append(f"freed={self.pruned_freed_bytes}B")
        return "scan_cycle: " + " ".join(bits)


# --- Inbox iteration (mtime-ordered) ---


def scan_inbox_mtime_ordered(inbox: Path) -> list[Path]:
    """Return ``inbox/*.msg.md`` sorted ascending by ``st_mtime_ns``.

    Tiebreak: filename lexicographic — covers the AC-Step1-3 boundary
    case where two messages share the same ``mtime_ns``. Defensive
    against missing inbox dir (returns empty list).
    """
    if not inbox.is_dir():
        return []
    entries: list[tuple[int, str, Path]] = []
    for entry in inbox.iterdir():
        if not entry.is_file() or not entry.name.endswith(".msg.md"):
            continue
        try:
            mtime_ns = entry.stat().st_mtime_ns
        except OSError:
            continue
        entries.append((mtime_ns, entry.name, entry))
    entries.sort()
    return [path for (_, __, path) in entries]


# --- Retention prune (Step 1 §6) ---


_Entry = tuple[float, int, Path]  # (mtime, size, path)


def _scan_processed_entries(processed: Path) -> tuple[list[_Entry], int]:
    """Return ``(entries-oldest-first, total_size)`` for files under processed/."""
    entries: list[_Entry] = []
    total_size = 0
    for entry in processed.iterdir():
        if not entry.is_file():
            continue
        try:
            stat = entry.stat()
        except OSError:
            continue
        entries.append((stat.st_mtime, stat.st_size, entry))
        total_size += stat.st_size
    entries.sort()  # oldest first
    return entries, total_size


def _select_size_driven_prune(
    entries: list[_Entry], total_size: int, size_bytes: int, max_prunable: int
) -> list[_Entry]:
    """Pick oldest entries to prune until under size threshold."""
    to_prune: list[_Entry] = []
    running = total_size
    for triple in entries:
        if len(to_prune) >= max_prunable or running <= size_bytes:
            break
        to_prune.append(triple)
        running -= triple[1]
    return to_prune


def prune_processed(
    processed: Path,
    *,
    age_days: int = DEFAULT_RETENTION_AGE_DAYS,
    size_bytes: int = DEFAULT_RETENTION_SIZE_BYTES,
    floor: int = DEFAULT_RETENTION_FLOOR,
    now: datetime | None = None,
) -> tuple[int, int, str]:
    """Apply the Step 1 §6 retention policy.

    Returns ``(pruned_count, freed_bytes, oldest_pruned_iso)``. The
    oldest-pruned ISO string is empty when nothing was pruned.

    Policy:
        1. Eligible if older than ``age_days`` OR total size > ``size_bytes``
        2. Preserve at least ``floor`` most-recent entries regardless
        3. Within the eligible set, oldest first
    """
    if not processed.is_dir():
        return (0, 0, "")
    now = now or _now_utc()
    age_threshold = now.timestamp() - age_days * 86400.0

    entries, total_size = _scan_processed_entries(processed)
    if len(entries) <= floor:
        return (0, 0, "")  # floor preserves everything

    max_prunable = len(entries) - floor
    size_over = total_size > size_bytes
    eligible_by_age = [(m, s, p) for (m, s, p) in entries if m < age_threshold]

    if not size_over and not eligible_by_age:
        return (0, 0, "")

    if size_over:
        to_prune = _select_size_driven_prune(entries, total_size, size_bytes, max_prunable)
    else:
        to_prune = eligible_by_age[:max_prunable]

    pruned_count = 0
    freed_bytes = 0
    oldest_iso = ""
    for mtime, size, path in to_prune:
        try:
            path.unlink()
        except OSError:
            continue
        pruned_count += 1
        freed_bytes += size
        iso = datetime.fromtimestamp(mtime, UTC).isoformat()
        if not oldest_iso or iso < oldest_iso:
            oldest_iso = iso

    return (pruned_count, freed_bytes, oldest_iso)


# --- Per-message processing ---


def _archive(source: Path, processed: Path) -> Path:
    """Atomically move a message from inbox/ to processed/."""
    processed.mkdir(parents=True, exist_ok=True)
    target = processed / source.name
    source.replace(target)  # POSIX atomic on same fs
    return target


def _write_sibling_log(archived: Path, suffix: str, content: str) -> None:
    """Write a ``<name>.<suffix>.log`` sibling next to an archived message."""
    sibling = archived.with_suffix(archived.suffix + f".{suffix}.log")
    sibling.write_text(content, encoding="utf-8")


def _format_validation_errors(errors: list[ValidationError]) -> str:
    return "\n".join(e.render() for e in errors) + "\n"


# --- Dispatcher (Step 3b core) ---


@dataclass
class Dispatcher:
    """Loop consumer poller.

    Construct once, call :meth:`run_once` per scan cycle. The CLI
    entrypoint at the bottom of this module wraps a single call;
    scheduling is delegated to the host (Code Desktop scheduled task).
    """

    inbox: Path = DEFAULT_INBOX
    processed: Path = DEFAULT_PROCESSED
    failure_state_path: Path = DEFAULT_FAILURES_STATE
    handlers: dict[MessageType, Handler] = field(default_factory=lambda: dict(DEFAULT_HANDLERS))
    alert_callback: Callable[[str, dict[str, Any]], None] = stderr_alert
    poison_threshold: int = DEFAULT_POISON_THRESHOLD
    retention_age_days: int = DEFAULT_RETENTION_AGE_DAYS
    retention_size_bytes: int = DEFAULT_RETENTION_SIZE_BYTES
    retention_floor: int = DEFAULT_RETENTION_FLOOR
    now_fn: Callable[[], datetime] = _now_utc

    def _process_one(self, path: Path, failures: FailureState) -> DispatchResult:
        # Idempotency check first — Step 1 §5 binding.
        archived_target = self.processed / path.name
        if archived_target.exists():
            # The mv was already done in a prior cycle; clean up the
            # leftover inbox file if it somehow lingers.
            try:
                path.unlink()
            except OSError:
                pass
            return DispatchResult.SKIPPED_IDEMPOTENT

        parsed = parse_message_file(path)
        if isinstance(parsed, list):
            archived = _archive(path, self.processed)
            _write_sibling_log(archived, "parse-error", _format_validation_errors(parsed))
            failures.clear(path.name)
            return DispatchResult.PARSE_FAILED

        if parsed.expires_after is not None and self.now_fn() > parsed.expires_after:
            archived = _archive(path, self.processed)
            _write_sibling_log(
                archived,
                "expired",
                f"expires_after={parsed.expires_after.isoformat()} "
                f"now={self.now_fn().isoformat()}\n",
            )
            failures.clear(path.name)
            return DispatchResult.EXPIRED

        handler = self.handlers.get(parsed.message_type, _default_noop_handler)
        try:
            handler(parsed)
        except Exception as exc:
            signature = f"{type(exc).__name__}: {exc}"
            count = failures.increment(path.name, signature)
            if count >= self.poison_threshold:
                archived = _archive(path, self.processed)
                _write_sibling_log(
                    archived,
                    "poison",
                    f"poison_threshold={self.poison_threshold} reached after {count} attempts.\n"
                    f"last_error_signature={signature}\n",
                )
                self.alert_callback(
                    "poison_message",
                    {
                        "message": path.name,
                        "count": count,
                        "last_error_signature": signature,
                    },
                )
                failures.clear(path.name)
                return DispatchResult.POISON
            LOGGER.warning(
                "dispatch_failed (count=%d / threshold=%d): %s — %s",
                count,
                self.poison_threshold,
                path.name,
                signature,
            )
            return DispatchResult.DISPATCH_FAILED

        _archive(path, self.processed)
        failures.clear(path.name)
        return DispatchResult.OK

    def run_once(self) -> ScanCycleSummary:
        """One scan cycle: process inbox in mtime order, then prune."""
        if not check_same_filesystem(self.inbox, self.processed):
            self.alert_callback(
                "same_fs_check_failed",
                {"inbox": str(self.inbox), "processed": str(self.processed)},
            )
            raise RuntimeError(
                "loop inbox and processed are on different filesystems; "
                "the atomic-mv lifecycle invariant cannot hold. Aborting "
                "scan per Step 1 §8 residual risk #1."
            )

        summary = ScanCycleSummary()
        failures = load_failure_state(self.failure_state_path)
        try:
            for path in scan_inbox_mtime_ordered(self.inbox):
                result = self._process_one(path, failures)
                if result is DispatchResult.OK:
                    summary.ok += 1
                elif result is DispatchResult.PARSE_FAILED:
                    summary.parse_failed += 1
                elif result is DispatchResult.EXPIRED:
                    summary.expired += 1
                elif result is DispatchResult.DISPATCH_FAILED:
                    summary.dispatch_failed += 1
                elif result is DispatchResult.POISON:
                    summary.poison += 1
                elif result is DispatchResult.SKIPPED_IDEMPOTENT:
                    summary.skipped_idempotent += 1
        finally:
            save_failure_state(self.failure_state_path, failures)

        pruned, freed, oldest = prune_processed(
            self.processed,
            age_days=self.retention_age_days,
            size_bytes=self.retention_size_bytes,
            floor=self.retention_floor,
            now=self.now_fn(),
        )
        summary.pruned = pruned
        summary.pruned_freed_bytes = freed
        summary.pruned_oldest = oldest

        return summary


# --- Iterator helpers (exposed for tests) ---


def iter_inbox_filenames(inbox: Path) -> Iterator[str]:
    """Yield message filenames in mtime order."""
    for path in scan_inbox_mtime_ordered(inbox):
        yield path.name


# --- CLI ---


def _build_default_dispatcher() -> Dispatcher:
    """Build a Dispatcher from env-overridable defaults."""
    inbox_env = os.environ.get("LOOP_INBOX")
    processed_env = os.environ.get("LOOP_PROCESSED")
    failures_env = os.environ.get("LOOP_FAILURES_STATE")
    telegram_env = os.environ.get("LOOP_TELEGRAM_SCRIPT")

    inbox = Path(inbox_env) if inbox_env else DEFAULT_INBOX
    processed = Path(processed_env) if processed_env else DEFAULT_PROCESSED
    failure_state_path = Path(failures_env) if failures_env else DEFAULT_FAILURES_STATE

    telegram_script = Path(telegram_env) if telegram_env else DEFAULT_TELEGRAM_SCRIPT
    alert_callback = (
        make_telegram_alert(telegram_script) if telegram_script.exists() else stderr_alert
    )

    return Dispatcher(
        inbox=inbox,
        processed=processed,
        failure_state_path=failure_state_path,
        alert_callback=alert_callback,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PLAN-0010 loop dispatcher (single scan cycle).")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-message INFO logs.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    start = time.monotonic()
    dispatcher = _build_default_dispatcher()
    try:
        summary = dispatcher.run_once()
    except RuntimeError as exc:
        LOGGER.error("scan_cycle aborted: %s", exc)
        return 2

    elapsed_ms = int((time.monotonic() - start) * 1000)
    print(f"{summary.to_log_line()} elapsed_ms={elapsed_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
