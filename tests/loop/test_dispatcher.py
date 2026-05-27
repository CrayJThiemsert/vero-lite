"""Tests for tools.loop.dispatcher (PLAN-0010 Step 3b consumer poller).

Covers AC-Step1-2 (lifecycle), AC-Step1-3 (mtime ordering + idempotency),
AC-Step1-4 (retention), and the poison-detection extension that mirrors
the spirit of PLAN-0008 L1-L4 loop-detect.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tools.loop._schema import LoopMessage, MessageType
from tools.loop.dispatcher import (
    DEFAULT_POISON_THRESHOLD,
    DEFAULT_RETENTION_AGE_DAYS,
    DEFAULT_RETENTION_FLOOR,
    DEFAULT_RETENTION_SIZE_BYTES,
    Dispatcher,
    DispatchResult,
    FailureState,
    ScanCycleSummary,
    check_same_filesystem,
    iter_inbox_filenames,
    load_failure_state,
    prune_processed,
    save_failure_state,
    scan_inbox_mtime_ordered,
    stderr_alert,
)

# --- Helpers ---


def _well_formed_text(
    *,
    producer_id: str = "cowork-smoke-heartbeat",
    message_type: str = "smoke_heartbeat",
    claimed_time: str = "2026-05-26T08:59:45Z",
    expires_after: str | None = None,
    action: str = "acknowledge",
    subject: str = "Heartbeat 2026-05-26 08:59",
) -> str:
    lines = [
        "---",
        f"producer_id: {producer_id}",
        "schema_version: 1",
        f"message_type: {message_type}",
        f"claimed_time: {claimed_time}",
        "time_authority: mtime",
    ]
    if expires_after is not None:
        lines.append(f"expires_after: {expires_after}")
    lines.extend(
        [
            "---",
            "",
            "## Subject",
            "",
            subject,
            "",
            "## Body",
            "",
            "Producer alive.",
            "",
            "## Action requested",
            "",
            action,
        ]
    )
    return "\n".join(lines) + "\n"


def _make_inbox_message(
    inbox: Path,
    *,
    filename: str = "cowork-smoke-heartbeat-20260526T085945Z.msg.md",
    mtime_offset_s: float = 0.0,
    text: str | None = None,
    **kw: object,
) -> Path:
    """Create a well-formed message in ``inbox/`` with a specific mtime."""
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / filename
    target.write_text(text if text is not None else _well_formed_text(**kw), encoding="utf-8")  # type: ignore[arg-type]
    if mtime_offset_s:
        stat = target.stat()
        os.utime(target, (stat.st_atime, stat.st_mtime + mtime_offset_s))
    return target


def _new_dispatcher(tmp_path: Path, **kw: object) -> Dispatcher:
    inbox = tmp_path / "loop" / "inbox"
    processed = tmp_path / "loop" / "processed"
    failures = tmp_path / "loop" / ".failures.json"
    inbox.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    return Dispatcher(
        inbox=inbox,
        processed=processed,
        failure_state_path=failures,
        **kw,  # type: ignore[arg-type]
    )


# --- AC-Step1-2 LIFECYCLE: happy / idempotent / parse-fail / expired ---


def test_happy_message_archived(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path)
    _make_inbox_message(d.inbox)
    summary = d.run_once()
    assert summary.ok == 1
    assert summary.parse_failed == 0
    assert list(d.inbox.glob("*.msg.md")) == []
    assert len(list(d.processed.glob("*.msg.md"))) == 1


def test_empty_inbox_noop(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path)
    summary = d.run_once()
    assert summary.ok == 0
    assert summary.dispatch_failed == 0
    assert summary.parse_failed == 0
    assert summary.pruned == 0


def test_idempotent_skips_when_processed_exists(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path)
    msg = _make_inbox_message(d.inbox)
    # Pre-stage the archived copy (simulating a crashed earlier cycle
    # that completed the mv but left an inbox copy behind somehow).
    (d.processed / msg.name).write_text(msg.read_text(encoding="utf-8"), encoding="utf-8")
    summary = d.run_once()
    assert summary.skipped_idempotent == 1
    assert summary.ok == 0
    assert list(d.inbox.glob("*.msg.md")) == []  # leftover cleaned up


def test_parse_failure_archives_with_sibling_log(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path)
    bad_text = (
        "---\n"
        "producer_id: cowork-smoke-heartbeat\n"
        "schema_version: 2\n"  # fail-closed: schema_version != 1
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "time_authority: mtime\n"
        "---\n"
        "## Subject\n\ns\n## Body\n\nb\n## Action requested\n\nnone\n"
    )
    _make_inbox_message(d.inbox, text=bad_text)
    summary = d.run_once()
    assert summary.parse_failed == 1
    assert summary.ok == 0
    archived = list(d.processed.glob("*.msg.md"))
    assert len(archived) == 1
    error_log = archived[0].with_suffix(archived[0].suffix + ".parse-error.log")
    assert error_log.exists()
    assert "schema_version" in error_log.read_text(encoding="utf-8")


def test_expired_message_archives_with_sibling_log(tmp_path: Path) -> None:
    # Set now > expires_after.
    fixed_now = datetime(2026, 5, 28, 0, 0, 0, tzinfo=UTC)
    d = _new_dispatcher(tmp_path, now_fn=lambda: fixed_now)
    _make_inbox_message(
        d.inbox,
        expires_after="2026-05-27T00:00:00Z",  # before fixed_now
    )
    summary = d.run_once()
    assert summary.expired == 1
    archived = list(d.processed.glob("*.msg.md"))
    assert len(archived) == 1
    expired_log = archived[0].with_suffix(archived[0].suffix + ".expired.log")
    assert expired_log.exists()
    assert "2026-05-27T00:00:00" in expired_log.read_text(encoding="utf-8")


def test_not_yet_expired_dispatches_normally(tmp_path: Path) -> None:
    fixed_now = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)
    d = _new_dispatcher(tmp_path, now_fn=lambda: fixed_now)
    _make_inbox_message(d.inbox, expires_after="2026-05-27T00:00:00Z")
    summary = d.run_once()
    assert summary.ok == 1
    assert summary.expired == 0


# --- AC-Step1-2 dispatch failure + poison detection ---


def _raising_handler(_: LoopMessage) -> None:
    raise RuntimeError("downstream handler busted")


def test_dispatch_failure_leaves_in_inbox_first_time(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path)
    d.handlers[MessageType.SMOKE_HEARTBEAT] = _raising_handler
    _make_inbox_message(d.inbox)
    summary = d.run_once()
    assert summary.dispatch_failed == 1
    assert summary.poison == 0
    assert len(list(d.inbox.glob("*.msg.md"))) == 1
    assert len(list(d.processed.glob("*.msg.md"))) == 0
    state = load_failure_state(d.failure_state_path)
    assert sum(state.counts.values()) == 1


def test_poison_threshold_archives_and_alerts(tmp_path: Path) -> None:
    alerts: list[tuple[str, dict[str, Any]]] = []

    def capture_alert(reason: str, payload: dict[str, Any]) -> None:
        alerts.append((reason, payload))

    d = _new_dispatcher(tmp_path, alert_callback=capture_alert, poison_threshold=3)
    d.handlers[MessageType.SMOKE_HEARTBEAT] = _raising_handler
    _make_inbox_message(d.inbox)

    # Run 3 cycles; on the 3rd the threshold trips.
    for cycle in range(1, 4):
        # Re-create the inbox file each cycle since failure does not move it,
        # but the previous cycle is a fresh "scan" — same file remains.
        summary = d.run_once()
        if cycle < 3:
            assert summary.poison == 0
            assert summary.dispatch_failed == 1
            assert len(list(d.inbox.glob("*.msg.md"))) == 1
        else:
            assert summary.poison == 1
            assert summary.dispatch_failed == 0
            assert len(list(d.inbox.glob("*.msg.md"))) == 0  # archived as poison
            assert len(list(d.processed.glob("*.msg.md"))) == 1
            poison_log = next(d.processed.glob("*.poison.log"))
            assert "poison_threshold=3" in poison_log.read_text(encoding="utf-8")
            assert "RuntimeError" in poison_log.read_text(encoding="utf-8")

    assert len(alerts) == 1
    reason, payload = alerts[0]
    assert reason == "poison_message"
    assert payload["count"] == 3


def test_recover_after_partial_failures_clears_state(tmp_path: Path) -> None:
    """A handler that succeeds after a prior failure clears the count."""
    call_count = {"n": 0}

    def flaky(_: LoopMessage) -> None:
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise RuntimeError("first time fails")

    d = _new_dispatcher(tmp_path, poison_threshold=5)
    d.handlers[MessageType.SMOKE_HEARTBEAT] = flaky
    _make_inbox_message(d.inbox)

    s1 = d.run_once()
    assert s1.dispatch_failed == 1
    assert load_failure_state(d.failure_state_path).counts != {}

    s2 = d.run_once()
    assert s2.ok == 1
    assert load_failure_state(d.failure_state_path).counts == {}


# --- AC-Step1-3 MTIME ORDERING ---


def test_mtime_order_three_messages(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path)
    order_seen: list[str] = []

    def record(msg: LoopMessage) -> None:
        order_seen.append(msg.source.name)

    d.handlers[MessageType.SMOKE_HEARTBEAT] = record

    # Write 3 messages, then adjust mtimes so 'second' < 'first' < 'third'.
    p_first = _make_inbox_message(
        d.inbox, filename="cowork-smoke-heartbeat-20260526T080000Z.msg.md"
    )
    p_second = _make_inbox_message(
        d.inbox, filename="cowork-smoke-heartbeat-20260526T090000Z.msg.md"
    )
    p_third = _make_inbox_message(
        d.inbox, filename="cowork-smoke-heartbeat-20260526T100000Z.msg.md"
    )
    base = p_first.stat().st_mtime
    os.utime(p_second, (base, base + 1))  # second-earliest
    os.utime(p_first, (base, base + 2))  # middle
    os.utime(p_third, (base, base + 3))  # latest

    # Re-sort: second(b+1) < first(b+2) < third(b+3)
    os.utime(p_second, (base, base + 0))
    os.utime(p_first, (base, base + 1))
    os.utime(p_third, (base, base + 2))

    d.run_once()
    assert order_seen == [p_second.name, p_first.name, p_third.name]


def test_mtime_tiebreak_by_filename_lex(tmp_path: Path) -> None:
    """When two messages share st_mtime, tiebreak by filename lex order."""
    d = _new_dispatcher(tmp_path)
    seen: list[str] = []
    d.handlers[MessageType.SMOKE_HEARTBEAT] = lambda m: seen.append(m.source.name)
    # Construct two filenames with same mtime; lex order: a-... < b-...
    a = _make_inbox_message(d.inbox, filename="aaa-producer-20260526T085945Z.msg.md")
    b = _make_inbox_message(d.inbox, filename="bbb-producer-20260526T085945Z.msg.md")
    # The frontmatter producer_id must match the filename; rewrite both.
    a.write_text(_well_formed_text(producer_id="aaa-producer"), encoding="utf-8")
    b.write_text(_well_formed_text(producer_id="bbb-producer"), encoding="utf-8")
    same = time.time()
    os.utime(a, (same, same))
    os.utime(b, (same, same))
    d.run_once()
    assert seen == [a.name, b.name]


def test_scan_inbox_skips_non_msg_md(tmp_path: Path) -> None:
    inbox = tmp_path / "loop" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / ".gitkeep").write_text("", encoding="utf-8")
    (inbox / "ignored.md").write_text("not a message", encoding="utf-8")
    valid = _make_inbox_message(inbox)
    paths = scan_inbox_mtime_ordered(inbox)
    assert paths == [valid]


def test_scan_inbox_missing_dir_returns_empty(tmp_path: Path) -> None:
    paths = scan_inbox_mtime_ordered(tmp_path / "nonexistent")
    assert paths == []


def test_iter_inbox_filenames_helper(tmp_path: Path) -> None:
    inbox = tmp_path / "loop" / "inbox"
    inbox.mkdir(parents=True)
    msg = _make_inbox_message(inbox)
    assert list(iter_inbox_filenames(inbox)) == [msg.name]


# --- AC-Step1-4 RETENTION (Step 1 §6) ---


def _make_processed_file(processed: Path, name: str, age_days: float, size: int = 1024) -> Path:
    processed.mkdir(parents=True, exist_ok=True)
    target = processed / name
    target.write_text("x" * size, encoding="utf-8")
    mtime = (datetime.now(UTC) - timedelta(days=age_days)).timestamp()
    os.utime(target, (mtime, mtime))
    return target


def test_retention_no_op_when_all_fresh(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    for i in range(5):
        _make_processed_file(processed, f"msg-{i}.msg.md", age_days=1)
    pruned, freed, oldest = prune_processed(processed)
    assert pruned == 0
    assert freed == 0
    assert oldest == ""


def test_retention_prunes_old_entries_by_age(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    for i in range(220):  # over floor=200
        _make_processed_file(processed, f"old-{i:03d}.msg.md", age_days=45)
    pruned, freed, oldest = prune_processed(processed, age_days=30, floor=200)
    assert pruned == 20  # 220 - 200 floor
    assert freed > 0
    assert oldest != ""


def test_retention_floor_preserves_recent(tmp_path: Path) -> None:
    """N=200 floor — never prune below floor even when over age."""
    processed = tmp_path / "processed"
    for i in range(150):
        _make_processed_file(processed, f"old-{i:03d}.msg.md", age_days=45)
    pruned, _, _ = prune_processed(processed, age_days=30, floor=200)
    assert pruned == 0  # 150 ≤ 200 floor


def test_retention_size_threshold_prunes_oldest(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    # Make ~250 entries x 1MB so total > 100 MB threshold.
    for i in range(250):
        _make_processed_file(processed, f"big-{i:03d}.msg.md", age_days=1, size=1024 * 1024)
    pruned, freed, _ = prune_processed(
        processed,
        age_days=30,
        size_bytes=100 * 1024 * 1024,
        floor=50,  # allow more pruning for the test
    )
    assert pruned > 0
    assert freed > 0
    # After prune, remaining entries should be at most the floor count
    # (plus any size-driven margin since the prune stops when under).
    remaining = len(list(processed.iterdir()))
    assert remaining >= 50  # floor honored


def test_retention_missing_dir_no_op(tmp_path: Path) -> None:
    pruned, freed, oldest = prune_processed(tmp_path / "nonexistent")
    assert (pruned, freed, oldest) == (0, 0, "")


def test_retention_integrated_into_run_once(tmp_path: Path) -> None:
    d = _new_dispatcher(tmp_path, retention_age_days=30, retention_floor=10)
    for i in range(15):  # over floor=10
        _make_processed_file(d.processed, f"old-{i:02d}.msg.md", age_days=45)
    summary = d.run_once()
    assert summary.pruned == 5  # 15 - 10 floor


# --- Same-fs check ---


def test_same_filesystem_true_when_both_under_tmp(tmp_path: Path) -> None:
    inbox = tmp_path / "loop" / "inbox"
    processed = tmp_path / "loop" / "processed"
    inbox.mkdir(parents=True)
    processed.mkdir(parents=True)
    assert check_same_filesystem(inbox, processed) is True


def test_same_filesystem_false_when_inbox_missing(tmp_path: Path) -> None:
    inbox = tmp_path / "loop" / "inbox"
    processed = tmp_path / "loop" / "processed"
    processed.mkdir(parents=True)
    assert check_same_filesystem(inbox, processed) is False


def test_run_once_aborts_when_same_fs_check_fails(tmp_path: Path) -> None:
    inbox = tmp_path / "loop" / "inbox"
    processed = tmp_path / "loop" / "processed"
    # Don't create inbox — same-fs check will fail.
    processed.mkdir(parents=True)
    d = Dispatcher(inbox=inbox, processed=processed, failure_state_path=tmp_path / ".failures.json")
    with pytest.raises(RuntimeError) as exc_info:
        d.run_once()
    assert "atomic-mv lifecycle invariant" in str(exc_info.value)


# --- Failure state persistence ---


def test_failure_state_load_missing_returns_empty(tmp_path: Path) -> None:
    state = load_failure_state(tmp_path / "missing.json")
    assert state.counts == {}


def test_failure_state_load_corrupt_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.json"
    path.write_text("not json", encoding="utf-8")
    state = load_failure_state(path)
    assert state.counts == {}


def test_failure_state_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "fs.json"
    state = FailureState()
    state.increment("foo.msg.md", "TypeError: boom")
    state.increment("foo.msg.md", "TypeError: boom")
    save_failure_state(path, state)
    loaded = load_failure_state(path)
    assert loaded.counts == {"foo.msg.md": 2}
    assert loaded.last_error_signatures == {"foo.msg.md": "TypeError: boom"}


def test_failure_state_clear(tmp_path: Path) -> None:
    state = FailureState()
    state.increment("foo.msg.md", "err")
    state.clear("foo.msg.md")
    assert state.counts == {}
    assert state.last_error_signatures == {}


# --- PLAN-0010 Phase 4 Fix 1: _archive FileNotFoundError recovery ---


def test_archive_returns_none_when_race_loser(tmp_path: Path) -> None:
    """Simulate the cross-process race: another dispatcher already moved
    ``source → processed/<name>`` and removed ``source``. The race
    loser's ``_archive`` call must return ``None`` (idempotent skip)
    instead of crashing with ``FileNotFoundError``.

    PLAN-0010 Phase 4 Fix 1 regression guard.
    """
    from tools.loop.dispatcher import _archive

    inbox = tmp_path / "inbox"
    processed = tmp_path / "processed"
    inbox.mkdir()
    processed.mkdir()

    source = inbox / "cowork-smoke-heartbeat-20260527T120000Z.msg.md"
    source.write_text("body", encoding="utf-8")

    # Simulate "winner already moved it": target exists, source is gone.
    (processed / source.name).write_text("body", encoding="utf-8")
    source.unlink()

    result = _archive(source, processed)
    assert result is None, (
        f"expected None (idempotent skip), got {result!r} — " "race-loser handling regressed"
    )
    # Filesystem invariant: target still exists, source still gone
    assert (processed / "cowork-smoke-heartbeat-20260527T120000Z.msg.md").exists()
    assert not source.exists()


def test_archive_reraises_when_source_missing_and_no_target(tmp_path: Path) -> None:
    """If source is gone AND target does not exist, the FileNotFoundError
    is genuine (something other than a race ate the source) and must
    bubble up loud — do not swallow real errors under the race-recovery
    branch."""
    from tools.loop.dispatcher import _archive

    inbox = tmp_path / "inbox"
    processed = tmp_path / "processed"
    inbox.mkdir()
    processed.mkdir()

    source = inbox / "ghost.msg.md"  # never created
    with pytest.raises(FileNotFoundError):
        _archive(source, processed)


def test_archive_returns_target_on_normal_path(tmp_path: Path) -> None:
    """Sanity: _archive still returns the target Path on the happy path
    (no race, source exists, target does not). Guards against the
    Fix-1 refactor accidentally changing the OK return type."""
    from tools.loop.dispatcher import _archive

    inbox = tmp_path / "inbox"
    processed = tmp_path / "processed"
    inbox.mkdir()
    processed.mkdir()

    source = inbox / "msg.msg.md"
    source.write_text("body", encoding="utf-8")

    result = _archive(source, processed)
    assert result == processed / "msg.msg.md"
    assert result is not None and result.exists()
    assert not source.exists()


def test_process_one_race_loser_reports_skipped_idempotent(tmp_path: Path) -> None:
    """End-to-end: when ``_archive`` returns None inside ``_process_one``
    (because a parallel process won the rename), the dispatcher reports
    ``SKIPPED_IDEMPOTENT`` and does NOT crash, double-archive, or write
    a sibling log on top of the winner's."""
    from tools.loop.dispatcher import DispatchResult, FailureState

    disp = _new_dispatcher(tmp_path)

    # Set up: an inbox message that would normally trigger a parse-error
    # path, but mid-way through (between idempotency-check and _archive),
    # a parallel process moves source → processed and removes source.
    source = _make_inbox_message(
        disp.inbox,
        filename="cowork-smoke-heartbeat-20260527T130000Z.msg.md",
        text="not a valid YAML/markdown message body",
    )

    # Simulate the parallel-win race AFTER the idempotency-check at the
    # top of _process_one passes (target does not yet exist), but
    # BEFORE _archive's source.replace runs (target gets created +
    # source removed by the parallel process).
    parallel_target = disp.processed / source.name
    parallel_target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    source.unlink()

    failures = FailureState()
    result = disp._process_one(source, failures)
    assert result == DispatchResult.SKIPPED_IDEMPOTENT
    # No sibling parse-error.log on top of the winner's archive
    sibling = parallel_target.with_suffix(parallel_target.suffix + ".parse-error.log")
    assert (
        not sibling.exists()
    ), "race loser must not write a sibling log on top of the winner's archive"


# --- PLAN-0010 Phase 4 Fix 2: save_failure_state per-process unique tmp path ---


def test_save_failure_state_uses_pid_unique_tmp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tmp path used by ``save_failure_state`` must include the
    process pid so concurrent dispatchers don't race on a shared tmp
    name. Spy on ``Path.write_text`` to capture the tmp path used.

    PLAN-0010 Phase 4 Fix 2 regression guard.
    """
    from tools.loop.dispatcher import FailureState, save_failure_state

    written_paths: list[str] = []
    real_write_text = Path.write_text

    def spy_write_text(self: Path, *args: object, **kwargs: object) -> int:
        written_paths.append(str(self))
        return real_write_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "write_text", spy_write_text)

    target = tmp_path / "loop" / ".failures.json"
    save_failure_state(target, FailureState())

    pid_str = str(os.getpid())
    tmp_writes = [p for p in written_paths if p.endswith(".tmp")]
    assert tmp_writes, f"expected a *.tmp write, got {written_paths}"
    assert all(
        pid_str in p for p in tmp_writes
    ), f"expected pid {pid_str} in every tmp path; got {tmp_writes}"
    # And the final file still lands at the canonical target.
    assert target.exists()


def _save_failure_worker(
    path_str: str,
    msg_id: str,
    ready_path: str,
    go_path: str,
    error_path: str,
) -> None:
    """Module-level worker for ``test_save_failure_state_cross_process_no_crash``.

    Uses filesystem signals instead of multiprocessing primitives so the
    test is portable across fork/spawn start methods.
    """
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, "/home/crayj/work/vero-lite")
    from tools.loop.dispatcher import FailureState, save_failure_state

    try:
        state = FailureState()
        for i in range(20):
            state.increment(f"{msg_id}-{i}.msg.md", "TypeError: boom")
        # Signal readiness
        _Path(ready_path).write_text("ready", encoding="utf-8")
        # Wait for "go"
        for _ in range(100):
            if _Path(go_path).exists():
                break
            time.sleep(0.05)
        for _ in range(15):
            save_failure_state(_Path(path_str), state)
    except Exception as exc:
        _Path(error_path).write_text(f"{type(exc).__name__}: {exc}", encoding="utf-8")


def test_save_failure_state_cross_process_no_crash(tmp_path: Path) -> None:
    """Two real subprocesses race on ``save_failure_state``; neither must
    crash with FileNotFoundError under the pid-unique tmp scheme.

    Authentic reproduction of the session-14 Phase 2 §3b live finding.
    """
    import multiprocessing as mp

    state_path = tmp_path / "loop" / ".failures.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    ready_a = tmp_path / "ready_a"
    ready_b = tmp_path / "ready_b"
    go = tmp_path / "go"
    err_a = tmp_path / "err_a"
    err_b = tmp_path / "err_b"

    ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    pa = ctx.Process(
        target=_save_failure_worker,
        args=(str(state_path), "alpha", str(ready_a), str(go), str(err_a)),
    )
    pb = ctx.Process(
        target=_save_failure_worker,
        args=(str(state_path), "beta", str(ready_b), str(go), str(err_b)),
    )
    pa.start()
    pb.start()

    # Wait for both workers to be ready
    for _ in range(100):
        if ready_a.exists() and ready_b.exists():
            break
        time.sleep(0.05)
    assert ready_a.exists() and ready_b.exists(), "workers did not signal ready in time"

    # Fire the starting gun
    go.write_text("go", encoding="utf-8")

    pa.join(timeout=20)
    pb.join(timeout=20)

    err_a_text = err_a.read_text(encoding="utf-8") if err_a.exists() else "<no err file>"
    err_b_text = err_b.read_text(encoding="utf-8") if err_b.exists() else "<no err file>"
    assert pa.exitcode == 0, f"worker A crashed (exit {pa.exitcode}); error: {err_a_text}"
    assert pb.exitcode == 0, f"worker B crashed (exit {pb.exitcode}); error: {err_b_text}"
    assert not err_a.exists(), f"worker A reported error: {err_a.read_text(encoding='utf-8')}"
    assert not err_b.exists(), f"worker B reported error: {err_b.read_text(encoding='utf-8')}"

    # Final state file must exist and parse cleanly (last writer wins;
    # we don't assert specific contents).
    assert state_path.exists()
    final = load_failure_state(state_path)
    assert isinstance(final.counts, dict)

    # No leftover tmp files from either worker.
    leftovers = list(state_path.parent.glob("*.tmp"))
    assert not leftovers, f"leftover tmp files after race: {leftovers}"


# --- Alert callbacks ---


def test_stderr_alert_emits_json(capsys: pytest.CaptureFixture[str]) -> None:
    stderr_alert("test_reason", {"foo": "bar"})
    captured = capsys.readouterr()
    payload = json.loads(captured.err.strip())
    assert payload["alert"] == "test_reason"
    assert payload["foo"] == "bar"
    assert "ts" in payload


# --- Scan cycle summary ---


def test_scan_cycle_summary_log_line() -> None:
    s = ScanCycleSummary(
        ok=3,
        parse_failed=1,
        pruned=2,
        pruned_freed_bytes=4096,
        pruned_oldest="2026-04-01T00:00:00+00:00",
    )
    line = s.to_log_line()
    assert "ok=3" in line
    assert "parse_failed=1" in line
    assert "pruned=2" in line
    assert "freed=4096B" in line
    assert "2026-04-01" in line


def test_scan_cycle_summary_no_prune_omits_freed() -> None:
    s = ScanCycleSummary(ok=1)
    line = s.to_log_line()
    assert "freed=" not in line
    assert "pruned=0" in line


# --- DispatchResult enum surface ---


def test_dispatch_result_string_values() -> None:
    assert DispatchResult.OK.value == "ok"
    assert DispatchResult.POISON.value == "poison"


# --- Constants surface (regression guard) ---


def test_defaults_are_sensible() -> None:
    assert DEFAULT_RETENTION_AGE_DAYS == 30
    assert DEFAULT_RETENTION_SIZE_BYTES == 100 * 1024 * 1024
    assert DEFAULT_RETENTION_FLOOR == 200
    assert DEFAULT_POISON_THRESHOLD == 3


# --- CLI smoke ---


def test_cli_with_empty_inbox_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from tools.loop.dispatcher import main

    inbox = tmp_path / "loop" / "inbox"
    processed = tmp_path / "loop" / "processed"
    inbox.mkdir(parents=True)
    processed.mkdir(parents=True)
    monkeypatch.setenv("LOOP_INBOX", str(inbox))
    monkeypatch.setenv("LOOP_PROCESSED", str(processed))
    monkeypatch.setenv("LOOP_FAILURES_STATE", str(tmp_path / ".failures.json"))
    rc = main(["--quiet"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "scan_cycle:" in captured.out


def test_cli_aborts_when_same_fs_check_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.loop.dispatcher import main

    inbox = tmp_path / "loop" / "inbox"  # not created
    processed = tmp_path / "loop" / "processed"
    processed.mkdir(parents=True)
    monkeypatch.setenv("LOOP_INBOX", str(inbox))
    monkeypatch.setenv("LOOP_PROCESSED", str(processed))
    monkeypatch.setenv("LOOP_FAILURES_STATE", str(tmp_path / ".failures.json"))
    rc = main(["--quiet"])
    assert rc == 2
