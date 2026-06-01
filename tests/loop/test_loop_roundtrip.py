"""Producer<->consumer round-trip: the live PLAN-0010 loop format contract.

These tests lock the contract between the two scheduled Desktop routines we
stood up in session 29:

- the Cowork-side **producer** (`phase35-smoke-cowork-heartbeat`) Writes
  v3-schema heartbeat messages into ``loop/inbox/``;
- the Code-side **consumer** (`loop-dispatcher`) drains ``loop/inbox/`` ->
  ``loop/processed/`` via ``tools.loop.dispatcher``.

They feed the **verbatim** message format the live producer emits, so a drift
in either side's wire format is caught here in CI rather than only in a live
Desktop run (which fires hourly and is gated on app-open + machine-awake).

They also pin the NONCE-collision data-loss risk found in session 29: the smoke
producer omits the schema's optional ``-<rand>`` filename suffix, so two
same-hour / drifted-clock fires can collide -> the second is deduped and its
distinct body is silently dropped. Benign for interchangeable smoke heartbeats;
data loss for real Step-5 payloads -> ``-<rand>`` is the fix (last test).
"""

from __future__ import annotations

from pathlib import Path

from tools.loop.dispatcher import Dispatcher

# The verbatim message the live Cowork producer writes (its task-prompt
# template; see the `phase35-smoke-cowork-heartbeat` routine Instructions).
# If the producer prompt changes, update this fixture in lockstep — that is the
# whole point: this constant IS the producer<->consumer format contract.
_PRODUCER_MESSAGE = """\
---
producer_id: cowork-smoke-heartbeat
schema_version: 1
message_type: smoke_heartbeat
claimed_time: 2026-06-01T00:00:00Z
time_authority: mtime
---

## Subject

Heartbeat 20260601T000000Z

## Body

Producer alive. Cowork-side scheduled task fired on schedule. Model:
Haiku 4.5. Permission mode: Act without asking. Tool used: Write (no
bash). The claimed_time above is informational only; the consumer uses
filesystem mtime as the authoritative ordering key per PLAN-0010 Step 1
§2.

## Action requested

acknowledge
"""


def _dispatcher(tmp_path: Path) -> Dispatcher:
    inbox = tmp_path / "loop" / "inbox"
    processed = tmp_path / "loop" / "processed"
    inbox.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    return Dispatcher(
        inbox=inbox,
        processed=processed,
        failure_state_path=tmp_path / "loop" / ".failures.json",
    )


def _write(inbox: Path, name: str, text: str) -> Path:
    target = inbox / name
    target.write_text(text, encoding="utf-8")
    return target


def test_live_producer_format_round_trips_through_consumer(tmp_path: Path) -> None:
    """The verbatim producer message parses, dispatches, and archives clean."""
    d = _dispatcher(tmp_path)
    name = "cowork-smoke-heartbeat-20260601T000000Z.msg.md"
    _write(d.inbox, name, _PRODUCER_MESSAGE)

    summary = d.run_once()

    assert summary.ok == 1
    assert summary.parse_failed == 0
    assert summary.dispatch_failed == 0
    assert list(d.inbox.glob("*.msg.md")) == []  # inbox drained
    assert (d.processed / name).exists()  # archived to processed/
    assert list(d.processed.glob("*.log")) == []  # clean dispatch -> no sibling error log


def test_nonce_collision_drops_second_body_silently(tmp_path: Path) -> None:
    """REGRESSION (session-29 finding): same filename + different body -> the
    second message is deduped (skipped_idempotent) and its distinct body is
    silently dropped. Benign for interchangeable smoke heartbeats; data loss
    for real Step-5 payloads -> motivates the ``-<rand>`` fix below."""
    d = _dispatcher(tmp_path)
    name = "cowork-smoke-heartbeat-20260601T120000Z.msg.md"  # no -<rand> suffix

    first = _PRODUCER_MESSAGE.replace("Producer alive.", "FIRST distinct payload.")
    _write(d.inbox, name, first)
    s1 = d.run_once()
    assert s1.ok == 1
    assert (d.processed / name).read_text(encoding="utf-8") == first

    # Producer re-fires the same NONCE with a DIFFERENT body.
    second = _PRODUCER_MESSAGE.replace("Producer alive.", "SECOND distinct payload.")
    _write(d.inbox, name, second)
    s2 = d.run_once()

    assert s2.ok == 0
    assert s2.skipped_idempotent == 1  # deduped, not re-processed
    assert list(d.inbox.glob("*.msg.md")) == []  # inbox copy unlinked
    # Data loss: the archived copy is still the FIRST body; SECOND was dropped.
    archived = (d.processed / name).read_text(encoding="utf-8")
    assert archived == first
    assert "SECOND" not in archived


def test_rand_suffix_prevents_collision(tmp_path: Path) -> None:
    """The fix: same NONCE + distinct ``-<rand>`` suffixes -> two distinct
    files, both processed, no data loss. Real PLAN-0010 Step-5 producers must
    adopt this (AC-2 collision-resistance independent of the producer clock)."""
    d = _dispatcher(tmp_path)
    base = "cowork-smoke-heartbeat-20260601T120000Z"  # identical NONCE
    _write(d.inbox, f"{base}-ab23.msg.md", _PRODUCER_MESSAGE.replace("alive.", "alive A."))
    _write(d.inbox, f"{base}-cd45.msg.md", _PRODUCER_MESSAGE.replace("alive.", "alive B."))

    summary = d.run_once()

    assert summary.ok == 2  # both processed — no collision
    assert summary.skipped_idempotent == 0
    assert len(list(d.processed.glob("*.msg.md"))) == 2
