"""Scenario suite for `tools/probe_battery/` — the real driver, killed for real.

CLAUDE.md §8: every build ships a scenario test that drives the **real producer into the
real consumer on realistic simulated data**. Here that means the driver runs as its own
child process, against a self-contained fixture project on disk, spawning a real pytest,
and is then actually signalled — never the live tree, never a stubbed runner, never a
mocked signal.

This is the half the unit suite structurally cannot reach. `try/finally` restore is
trivially testable in-process; **surviving SIGTERM is not**, because Python's default
disposition for that signal kills the interpreter without running a single `finally`. A
test that called the restore path directly would agree with itself and prove nothing about
the case that actually loses work.

POSIX-only by design (PLAN-0115 Step 1 item 3): the driver runs WSL-side and CI is Linux.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools.probe_battery import STATE_ENV, VERDICT_PASS, find_unrestored
from tools.probe_battery._lock import LOCK_ENV

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX signals — the driver runs WSL-side, CI is Linux"
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_SUBJECT = """
def classify(n):
    return "high" if n > 10 else "low"
"""

_SLOW_TEST = """
import time

from subject import classify


def test_slow_claim():
    time.sleep(30)
    assert classify(20) == "high"
"""

_FAST_TEST = """
from subject import classify


def test_fast_claim():
    assert classify(20) == "high"
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_project(tmp_path: Path, test_body: str, test_name: str, node: str) -> Path:
    (tmp_path / "subject.py").write_text(_SUBJECT, encoding="utf-8")
    (tmp_path / test_name).write_text(test_body, encoding="utf-8")
    (tmp_path / "state").mkdir(exist_ok=True)
    battery = {
        "claim_sources": [test_name],
        "probes": [
            {
                "name": "P1",
                "subject": "subject.py",
                "old": "n > 10",
                "new": "n > 1000",
                "node_id": f"{test_name}::{node}",
                "expect_claim": 'test_slow_claim|classify(20) == "high"|#0'
                if node == "test_slow_claim"
                else 'test_fast_claim|classify(20) == "high"|#0',
            }
        ],
    }
    (tmp_path / "battery.json").write_text(json.dumps(battery, indent=2), encoding="utf-8")
    return tmp_path


def _spawn(project: Path, stdout: int | None = subprocess.DEVNULL) -> subprocess.Popen[bytes]:
    env = dict(os.environ)
    env[STATE_ENV] = str(project / "state")
    # Explicit, though `--project-root` already scopes it: a battery that wrote the REAL
    # lock would stand the live goal gate down for its whole staleness window.
    env[LOCK_ENV] = str(project / "probe_battery.lock")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(project),
            "run",
            "--battery",
            str(project / "battery.json"),
            "--timeout",
            "120",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=stdout,
        stderr=subprocess.DEVNULL,
    )


CHILD_PATTERN = "[t]est_slow.py::test_slow_claim"


def _wait_for_mutation(subject: Path, pristine: str, timeout: float = 60.0) -> bool:
    """Poll until the subject's bytes differ from pristine. Returns whether they did.

    🟢 One of the two positive controls AC-1 asks for. Signalling the driver before the
    mutation reached disk would make the restore assertion vacuous — nothing was broken, so
    of course nothing needed fixing. The caller asserts the return value.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if subject.exists() and _sha(subject) != pristine:
            return True
        time.sleep(0.05)
    return False


def _pytest_children() -> list[str]:
    proc = subprocess.run(
        ["pgrep", "-f", CHILD_PATTERN],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in proc.stdout.split() if line.strip()]


def _wait_for_pytest_child(timeout: float = 60.0) -> bool:
    """Poll until the driver's pytest subprocess is genuinely running.

    🟢 The SECOND positive control, and it was not obvious. Measured 2026-08-25: waiting
    only for the mutation returns in ~0.15 s — while the driver is still *between* writing
    the mutation and spawning pytest. A SIGTERM landing in that window is not the case
    under test at all, and "no orphan survived" would pass because no child ever existed.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _pytest_children():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture(autouse=True)
def _no_stray_children() -> Iterator[None]:
    """Fail loudly rather than let one test's orphan be read as another's evidence.

    Without this, the SIGKILL cases below leak a pytest into the next test's `pgrep`, and
    the orphan assertion reddens against a survivor it did not create.
    """
    subprocess.run(["pkill", "-f", CHILD_PATTERN], capture_output=True, check=False)  # noqa: S607
    yield
    subprocess.run(["pkill", "-f", CHILD_PATTERN], capture_output=True, check=False)  # noqa: S607


@pytest.fixture
def slow_project(tmp_path: Path) -> Path:
    return _make_project(tmp_path, _SLOW_TEST, "test_slow.py", "test_slow_claim")


# ======================================================================================
# AC-1, first assertion — restore survives SIGTERM
# ======================================================================================


def _armed(project: Path) -> subprocess.Popen[bytes]:
    """Spawn the driver and return only once a battery is genuinely in flight.

    Both preconditions are asserted here so no caller can forget one: the mutation is on
    disk, and the pytest child is running. Signalling before either would test a window
    that is not the one under test.
    """
    subject = project / "subject.py"
    pristine = _sha(subject)
    proc = _spawn(project)
    assert _wait_for_mutation(subject, pristine) is True, "mutation never reached disk"
    assert _wait_for_pytest_child() is True, "pytest child never started"
    return proc


def test_the_mutation_reaches_disk_before_the_signal(slow_project: Path) -> None:
    """🟢 POSITIVE CONTROL, asserted on its own so it cannot silently degrade. If this
    reddens, every SIGTERM-restore claim below is about a file that was never mutated."""
    subject = slow_project / "subject.py"
    pristine = _sha(subject)
    proc = _spawn(slow_project)
    try:
        assert _wait_for_mutation(subject, pristine) is True
    finally:
        proc.kill()
        proc.wait(timeout=30)


def test_the_pytest_child_is_running_when_the_signal_lands(slow_project: Path) -> None:
    """🟢 The second POSITIVE CONTROL. Measured: waiting only for the mutation returns while
    the driver is still between the write and the spawn — so this pins the window."""
    proc = _spawn(slow_project)
    try:
        assert _wait_for_pytest_child() is True
    finally:
        proc.kill()
        proc.wait(timeout=30)


def test_the_subject_is_restored_byte_identically_after_sigterm(slow_project: Path) -> None:
    """🔴 The assertion this whole file exists for. Python's default SIGTERM handling would
    kill the driver mid-battery with the mutation still on disk."""
    subject = slow_project / "subject.py"
    pristine = _sha(subject)
    proc = _armed(slow_project)
    proc.terminate()
    proc.wait(timeout=60)
    assert _sha(subject) == pristine


def test_the_pytest_child_does_not_outlive_the_sigtermed_driver(slow_project: Path) -> None:
    """🔴 A 30-second sleep still running after the driver exits is an orphan holding
    whatever the test held — the shape behind the 67-minute hang. The driver's
    kill-on-any-exception path is what prevents it.

    **The check is immediate, and that is deliberate — do not add a grace period here.**
    This went flaky in CI (s265: run 33361773136 red at 5d679ae, the identical sha green on
    re-run), and a bounded poll for the child to disappear is the obvious repair. It would
    have been the wrong one. The driver kills its child with ``proc.kill()`` followed by
    ``proc.communicate()``, and ``communicate()`` waits — so the child is always reaped
    *before* the driver itself exits. Once ``proc.wait()`` above has returned there is no
    reaping still in flight, and anything ``pgrep`` can still see is a genuine orphan.

    What was actually broken was the driver. A SIGTERM landing inside ``Popen.__init__`` —
    child already forked and exec'd, ``proc`` not yet bound — escaped the kill path
    entirely, because no ``except`` can reach a name that was never assigned. Measured under
    single-CPU contention: 9 failures in 12 runs, and every survivor lived out its full
    30-second body rather than dying milliseconds late. A grace period would not have caught
    one of them; it would only have made each failure 35 seconds slower to report.
    ``_DeferredInterrupts`` in ``_battery.py`` closes that window, and this assertion stays
    immediate so it keeps reddening promptly when a child really does outlive its driver."""
    proc = _armed(slow_project)
    proc.terminate()
    proc.wait(timeout=60)
    assert _pytest_children() == []


# ======================================================================================
# AC-1, second assertion — SIGKILL leaves a manifest, and the manifest is the guarantee
# ======================================================================================


def _sigkill_a_running_battery(project: Path) -> None:
    proc = _armed(project)
    proc.kill()
    proc.wait(timeout=30)


def _run_restore(project: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env[STATE_ENV] = str(project / "state")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(project),
            "restore",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_killed_driver_leaves_the_mutation_on_disk(slow_project: Path) -> None:
    """🟢 The premise of the recovery tests below, asserted rather than assumed. SIGKILL runs
    no Python, so there is genuinely damage to recover — if this reddens, every restore
    assertion here is recovering a file that was already clean."""
    subject = slow_project / "subject.py"
    pristine = _sha(subject)
    _sigkill_a_running_battery(slow_project)
    assert _sha(subject) != pristine


def test_a_killed_driver_orphans_its_pytest_child(slow_project: Path) -> None:
    """🟢 The premise of the reaping test, likewise asserted. Nothing a SIGKILLed process
    does can prevent this — which is exactly why the cleanup has to live in the manifest
    and run from the recovery path."""
    _sigkill_a_running_battery(slow_project)
    assert _pytest_children() != []


def test_restore_reaps_the_orphaned_pytest_child(slow_project: Path) -> None:
    """🔴 The orphan is still executing the code `restore` is about to put back — and this
    repo has already paid 67 minutes for a leaked test session holding locks."""
    _sigkill_a_running_battery(slow_project)
    assert _pytest_children() != [], "no orphan to reap — vacuous"
    _run_restore(slow_project)
    assert _pytest_children() == []


def test_a_new_battery_refuses_to_start_while_a_manifest_is_unrestored(
    slow_project: Path,
) -> None:
    """🔴 The load-bearing half. Starting anyway would snapshot the MUTATED file as pristine
    and make the damage permanent — no later restore could recover it."""
    _sigkill_a_running_battery(slow_project)
    second = _spawn(slow_project)
    assert second.wait(timeout=60) == 3


def test_the_restore_subcommand_recovers_byte_identically_after_a_kill(
    slow_project: Path,
) -> None:
    """The persisted manifest is the entire guarantee once no handler can run."""
    subject = slow_project / "subject.py"
    pristine = _sha(subject)
    _sigkill_a_running_battery(slow_project)
    restore = _run_restore(slow_project)
    assert restore.returncode == 0 and _sha(subject) == pristine


def test_a_battery_may_start_again_once_the_run_is_restored(slow_project: Path) -> None:
    """🟢 POSITIVE CONTROL for the refusal: the block clears, so `run` is not simply refusing
    forever once a state directory exists."""
    _sigkill_a_running_battery(slow_project)
    _run_restore(slow_project)
    assert find_unrestored(slow_project / "state") == []


# ======================================================================================
# The whole seam, end to end: CLI -> driver -> real pytest -> real report
# ======================================================================================


def test_a_clean_battery_run_through_the_cli_reports_pass(tmp_path: Path) -> None:
    """Driver → real pytest subprocess → real junit → real coverage report → exit 0. If
    any link in that chain is wrong, no unit test in this package would notice."""
    project = _make_project(tmp_path, _FAST_TEST, "test_fast.py", "test_fast_claim")
    env = dict(os.environ)
    env[STATE_ENV] = str(project / "state")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(project),
            "run",
            "--battery",
            str(project / "battery.json"),
            "--timeout",
            "120",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_the_clean_run_prints_the_pass_verdict_token(tmp_path: Path) -> None:
    """An echoed exit code is corruptible; a printed verdict is not (#0047's rule)."""
    project = _make_project(tmp_path, _FAST_TEST, "test_fast.py", "test_fast_claim")
    env = dict(os.environ)
    env[STATE_ENV] = str(project / "state")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(project),
            "run",
            "--battery",
            str(project / "battery.json"),
            "--timeout",
            "120",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert VERDICT_PASS in proc.stdout


def test_the_clean_run_leaves_the_tree_untouched(tmp_path: Path) -> None:
    """The happy path restores too — not only the interrupted one."""
    project = _make_project(tmp_path, _FAST_TEST, "test_fast.py", "test_fast_claim")
    subject = project / "subject.py"
    pristine = _sha(subject)
    env = dict(os.environ)
    env[STATE_ENV] = str(project / "state")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(project),
            "run",
            "--battery",
            str(project / "battery.json"),
            "--timeout",
            "120",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        check=False,
    )
    assert _sha(subject) == pristine


def test_the_keys_subcommand_prints_the_address_a_probe_must_declare(tmp_path: Path) -> None:
    """The driver mandates `stable_key` addressing, so it has to be able to hand you one —
    otherwise a battery author derives it by hand, which is how s253 hand-rolled a
    colliding key beside the one it had imported."""
    project = _make_project(tmp_path, _FAST_TEST, "test_fast.py", "test_fast_claim")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "keys",
            str(project / "test_fast.py"),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert 'test_fast_claim|classify(20) == "high"|#0' in proc.stdout


# ======================================================================================
# PLAN-0121 — a cut-off child, through the CLI
# ======================================================================================

#: The token PLAN-0120's DB guard will print. Mimicked in SHAPE only: `tests/db_guard.py`
#: does not exist, and PLAN-0121 must stay executable without it.
_CONTENTION_REASON = "TEST-DB-GUARD outcome=CONTENDED holder_pid=424242 db=vero_lite_test_s279"

_ABORTING_TEST = f"""import pytest

from subject import classify


def test_fast_claim():
    pytest.exit({_CONTENTION_REASON!r}, returncode=75)
    assert classify(20) == "high"
"""


def _run_cli(project: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env[STATE_ENV] = str(project / "state")
    env[LOCK_ENV] = str(project / "probe_battery.lock")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(project),
            "run",
            "--battery",
            str(project / "battery.json"),
            "--timeout",
            "120",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _expect_aborted(project: Path) -> None:
    """Rewrite the generated battery so its probe declares `expect: ABORTED`."""
    path = project / "battery.json"
    battery = json.loads(path.read_text(encoding="utf-8"))
    battery["probes"][0]["expect"] = "ABORTED"
    path.write_text(json.dumps(battery, indent=2), encoding="utf-8")


def test_an_aborting_child_is_reported_aborted_through_the_cli(tmp_path: Path) -> None:
    """🔴 The ONLY shape that witnesses a `_battery.py` mutation (PLAN-0121 §2.4).

    The driver's parent process imports `_battery` once, before the first mutation, so a
    probe that mutates the runner is invisible to the judge running in that parent. Here a
    **fresh driver process** is spawned, loads the mutated module from disk, and misreports
    — which this assertion, running in the child, can see.

    Before PLAN-0121 this run printed GREEN: the same reading a real green produces.
    """
    project = _make_project(tmp_path, _ABORTING_TEST, "test_fast.py", "test_fast_claim")
    proc = _run_cli(project)
    print(proc.stdout)
    assert "ABORTED" in proc.stdout


def test_an_aborting_child_fails_a_battery_that_declared_witnessed(tmp_path: Path) -> None:
    """Sibling claim: the declared `WITNESSED` is unmet, so the run FAILS and credits none.

    A cut-off child must not be able to satisfy a probe that predicted a reddened
    assertion — that is the whole crediting rule, seen from the outside.
    """
    project = _make_project(tmp_path, _ABORTING_TEST, "test_fast.py", "test_fast_claim")
    proc = _run_cli(project)
    print(proc.stdout)
    assert proc.returncode == 1


def test_a_battery_declaring_expect_aborted_satisfies_its_probe(tmp_path: Path) -> None:
    """🟢 POSITIVE CONTROL: `ABORTED` is reachable through the DATA path, not just in-process.

    Without this, the two assertions above would be satisfied by a driver that had simply
    become unable to pass anything. It also pins that the new member is declarable in a
    battery file — `Probe.from_json` accepts any `Outcome` value, so no parser change was
    needed, and this is what would notice if that stopped being true.

    🔴 **The read is the PROBE's verdict, not the battery's** — measured, s279. PLAN-0121
    AC-4(d) predicted `PROBE-BATTERY: PASS` here; the battery still reports FAIL, and
    rightly so: its verdict also carries the coverage report, and a claim that was never
    witnessed RED is a `GAPS: 1` whatever the probe declared. Making the whole battery green
    would mean adding an exemption for that claim purely to satisfy this assertion — bending
    the subject to fit the instrument, and inflating the coverage denominator on the way.
    The claim under test is "the data path honours `expect: ABORTED`", and the probe line
    states exactly that.
    """
    project = _make_project(tmp_path, _ABORTING_TEST, "test_fast.py", "test_fast_claim")
    _expect_aborted(project)
    proc = _run_cli(project)
    print(proc.stdout)
    assert "ABORTED  (declared ABORTED)" in proc.stdout
