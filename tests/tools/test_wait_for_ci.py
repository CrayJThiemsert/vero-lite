"""The verdict table for :mod:`tools.ci.wait_for_ci`.

Every case here is one of the four ways session 261 got this wrong by hand. The
first — an empty run list read as a pass — is the one that cost the most, because
it fails in the direction that looks like success.

The payload shapes are the ones ``gh run list --json databaseId,status,conclusion``
actually emits on this repo, captured live rather than invented, so the grammar
asserted is the grammar gh produces and not one this test agreed with itself about.
"""

from __future__ import annotations

import pytest

from tools.ci.wait_for_ci import classify


def _run(run_id: int, status: str, conclusion: str | None) -> dict:
    return {
        "databaseId": run_id,
        "status": status,
        "conclusion": conclusion,
        # A real, public commit sha from this repo — detect-secrets reads any 40-char
        # hex as high-entropy, which every git sha is. pragma: allowlist secret
        "headSha": "e9e5f72f50295a89247df03bad23c8042b20c570",  # pragma: allowlist secret
        "workflowName": "CI",
    }


def test_no_runs_is_never_a_pass() -> None:
    """THE defect. `gh run list -c <sha>` returns `[]` with exit status 0 (measured),
    so a wait that breaks on "nothing pending" reports green against a sha that never
    ran. Absence of evidence gets its own verdict and its own exit code."""
    verdict = classify([])
    assert verdict.name == "NO-RUN"
    assert verdict.exit_code == 5
    assert verdict.exit_code != 0


def test_in_progress_is_pending_and_not_terminal() -> None:
    verdict = classify([_run(100, "in_progress", None)])
    assert verdict.name == "PENDING"
    assert verdict.is_terminal is False


def test_success_is_the_only_pass() -> None:
    verdict = classify([_run(100, "completed", "success")])
    assert verdict.name == "PASS"
    assert verdict.exit_code == 0
    assert verdict.run_id == 100


def test_failure_is_a_fail() -> None:
    verdict = classify([_run(100, "completed", "failure")])
    assert verdict.name == "FAIL"
    assert verdict.exit_code == 1


def test_cancelled_is_superseded_not_failure() -> None:
    """`cancel-in-progress: true` makes a cancelled run the ROUTINE result of pushing
    again — 1 of 12 sampled runs. Read as FAIL it sends a reader debugging a branch
    that is fine; read as PASS it ships a tree nothing tested."""
    verdict = classify([_run(100, "completed", "cancelled")])
    assert verdict.name == "SUPERSEDED"
    assert verdict.exit_code == 4
    assert verdict.exit_code != 0


def test_newest_run_wins_and_is_chosen_by_id_not_order() -> None:
    """A re-run leaves two runs at one sha. The newer is authoritative — and it is
    found by max(databaseId), a COUNTER, because WSL2's wall clock steps backwards
    and a timestamp sort can pick the older one.

    The older run here is green and listed FIRST, so a reader that latched onto the
    first entry, or onto any green it found, would report PASS.
    """
    verdict = classify([_run(99, "completed", "success"), _run(100, "in_progress", None)])
    assert verdict.name == "PENDING"
    assert verdict.run_id == 100


def test_deadline_exceeded_is_never_a_pass() -> None:
    """A wait that gives up has learned nothing, which is not the same as a green."""
    verdict = classify([_run(100, "in_progress", None)], deadline_exceeded=True)
    assert verdict.name == "TIMEOUT"
    assert verdict.exit_code == 6


@pytest.mark.parametrize(
    ("runs", "deadline"),
    [
        ([], False),
        ([_run(1, "in_progress", None)], False),
        ([_run(1, "completed", "failure")], False),
        ([_run(1, "completed", "cancelled")], False),
        ([_run(1, "completed", "timed_out")], False),
        ([_run(1, "completed", None)], False),
        ([_run(1, "in_progress", None)], True),
    ],
)
def test_exit_code_zero_is_reserved_for_a_measured_success(
    runs: list[dict], deadline: bool
) -> None:
    """The single invariant the whole module exists to hold.

    Enumerated as a table rather than asserted per-case so that a NEW verdict added
    later without a deliberate exit code cannot default its way to 0. Every non-green
    state — including the two that look like nothing happened — must be non-zero.
    """
    assert classify(runs, deadline_exceeded=deadline).exit_code != 0
