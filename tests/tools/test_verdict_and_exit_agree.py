"""Every instrument's printed verdict and its exit status must be one value.

🔴 **The measured failure this guards.** PLAN-0123 §1.2 error #13: a check
inverted its own result with a shell ``!``, so the line it printed and the status
it exited with were computed by two different expressions — and they disagreed.
Nothing failed. The report said one thing, the gate read the other, and the only
reason anybody noticed was that a human happened to read both.

§4.6 makes it structural: each instrument derives its verdict token and its exit
status from a **single** variable. This module is that rule as a guard, run
across every instrument a rendered goal can call.

**Instrument-specific verdict tokens, and why they are not unified.** ``tally``
and ``absent`` print the shared ``VERDICT: <token> exit=<n>`` line from
:func:`tools._evidence.verdict_line`. The probe-battery driver's terminal line
has been ``PROBE-BATTERY: PASS|FAIL`` since PLAN-0115 and is asserted by name in
several places, so it keeps its own token; what matters for #13 is not that the
words match across tools but that within each tool there is one variable behind
both halves. The table below records each instrument's form explicitly rather
than assuming a common one — assuming one is how a fourth instrument gets added
whose line nobody actually checks.

All four of AC-5's instruments are covered: ``tally``, ``absent``, the
probe-battery driver, and the renderer's refusal path. The renderer's row is the
one that matters most — it is the place the whole contract is supposed to be
enforced, and a renderer that refused a goal while printing ``PASS`` would be
error #13 sitting at the enforcement point itself.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

_VERDICT_RE = re.compile(
    r"^VERDICT: (?P<token>PASS|FAIL|REFUSED) exit=(?P<exit>\d+)$", re.MULTILINE
)
_BATTERY_RE = re.compile(r"^PROBE-BATTERY: (?P<token>PASS|FAIL)$", re.MULTILINE)

#: Which token an instrument is allowed to print for which exit status. Written
#: out rather than derived from the code under test — a table generated from the
#: implementation would agree with any implementation, including a broken one.
_ALLOWED = {"PASS": 0, "FAIL": 1, "REFUSED": 2}

#: Lesson #0056 — the extractors below are instruments too, and an uncontrolled
#: instrument does not fail loudly, it fails confidently.
_VERDICT_CONTROL = ("some report\nVERDICT: REFUSED exit=2\n", ("REFUSED", 2))
_BATTERY_CONTROL = ("outcomes...\nPROBE-BATTERY: FAIL\n", ("FAIL", 1))


def _read_verdict_line(stdout: str) -> tuple[str, int]:
    match = _VERDICT_RE.search(stdout)
    if match is None:
        raise AssertionError(f"no VERDICT line in output:\n{stdout}")
    return match.group("token"), int(match.group("exit"))


def _read_battery_line(stdout: str) -> tuple[str, int]:
    match = _BATTERY_RE.search(stdout)
    if match is None:
        raise AssertionError(f"no PROBE-BATTERY line in output:\n{stdout}")
    token = match.group("token")
    return token, _ALLOWED[token]


@dataclass(frozen=True)
class Case:
    """One instrument, one fixture, and the outcome the fixture was built to force."""

    instrument: str
    should_pass: bool
    argv: Callable[[Path], list[str]]
    extract: Callable[[str], tuple[str, int]]


def _jsonl(tmp_path: Path, *, exhaustive: bool) -> Path:
    path = tmp_path / "log.jsonl"
    records = [{"transport": "ok"}, {"transport": "timeout"}]
    if not exhaustive:
        # A record with no such field: counted, never skipped, so the buckets no
        # longer account for the input and `tally` must refuse.
        records.append({"other": "x"})
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


def _subject(tmp_path: Path, *, pattern_present: bool) -> Path:
    path = tmp_path / "subject.log"
    body = ["level=info start"]
    if pattern_present:
        body.append("FATAL boom")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


def _fixture_battery(tmp_path: Path, *, probe_fires: bool) -> Path:
    module = tmp_path / "test_vx_fixture.py"
    module.write_text("VALUE = 1\n\n\ndef test_value() -> None:\n    assert VALUE == 1\n", "utf-8")
    definition = {
        "claim_sources": ["test_vx_fixture.py"],
        "probes": [
            {
                "name": "F1",
                "subject": "test_vx_fixture.py",
                # A mutation that changes the value reddens the assertion (WITNESSED);
                # one that only touches a comment cannot, so the driver reports a
                # MISFIRE and the battery fails. Two real outcomes, one knob.
                "old": "VALUE = 1" if probe_fires else "def test_value",
                "new": "VALUE = 2" if probe_fires else "def  test_value",
                "node_id": "test_vx_fixture.py::test_value",
                "expect_claim": "test_value|VALUE == 1|#0",
                "note": "verdict/exit agreement fixture",
            }
        ],
        "exemptions": {},
    }
    path = tmp_path / "battery.json"
    path.write_text(json.dumps(definition, indent=2), encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=str(tmp_path), check=True)  # noqa: S607
    return path


_CASES = [
    Case(
        "tally.py",
        True,
        lambda p: ["-m", "tools.tally", str(_jsonl(p, exhaustive=True)), "--field", "transport"],
        _read_verdict_line,
    ),
    Case(
        "tally.py",
        False,
        lambda p: ["-m", "tools.tally", str(_jsonl(p, exhaustive=False)), "--field", "transport"],
        _read_verdict_line,
    ),
    Case(
        "absent.py",
        True,
        lambda p: [
            "-m",
            "tools.absent",
            "--file",
            str(_subject(p, pattern_present=False)),
            "--pattern",
            "FATAL",
            "--control",
            "level=info",
        ],
        _read_verdict_line,
    ),
    Case(
        "absent.py",
        False,
        lambda p: [
            "-m",
            "tools.absent",
            "--file",
            str(_subject(p, pattern_present=True)),
            "--pattern",
            "FATAL",
            "--control",
            "level=info",
        ],
        _read_verdict_line,
    ),
    Case(
        "probe_battery",
        True,
        lambda p: [
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(p),
            "run",
            "--battery",
            str(_fixture_battery(p, probe_fires=True)),
        ],
        _read_battery_line,
    ),
    Case(
        "goal_template",
        True,
        lambda p: [
            "-m",
            "tools.goal_template",
            "T-COUNT",
            "--file",
            str(_jsonl(p, exhaustive=True)),
            "--field",
            "transport",
            "--expect",
            "ok,timeout",
            "--dry-run",
        ],
        _read_verdict_line,
    ),
    Case(
        "goal_template",
        False,
        # A `$` in a caller parameter — clause R6's refusal, the renderer's own
        # control path. It must exit non-zero AND say so in the same breath.
        lambda p: [
            "-m",
            "tools.goal_template",
            "T-ABSENT",
            "--file",
            str(_jsonl(p, exhaustive=True)),
            "--pattern",
            "a$b",
            "--control",
            "transport",
            "--dry-run",
        ],
        _read_verdict_line,
    ),
    Case(
        "probe_battery",
        False,
        lambda p: [
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(p),
            "run",
            "--battery",
            str(_fixture_battery(p, probe_fires=False)),
        ],
        _read_battery_line,
    ),
]


def test_the_verdict_extractors_pass_their_own_controls() -> None:
    """Both parsers read a known line correctly before any real reading is trusted."""
    assert _read_verdict_line(_VERDICT_CONTROL[0]) == _VERDICT_CONTROL[1]
    assert _read_battery_line(_BATTERY_CONTROL[0]) == _BATTERY_CONTROL[1]


@pytest.mark.parametrize(
    "case", _CASES, ids=[f"{c.instrument}-{'pass' if c.should_pass else 'fail'}" for c in _CASES]
)
def test_the_printed_verdict_and_the_exit_status_are_one_value(case: Case, tmp_path: Path) -> None:
    """A1 — for every instrument, on a fixture built to pass and one built to fail.

    The fixtures are asserted to have actually forced the intended outcome
    (``should_pass``) before the agreement is checked. Without that, an
    instrument that always exited 0 and always printed PASS would satisfy
    "the two agree" perfectly.
    """
    proc = subprocess.run(
        [sys.executable, *case.argv(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        env={**os.environ, "PYTHONPATH": str(_ROOT)},
        check=False,
    )
    token, printed_exit = case.extract(proc.stdout)
    agree = printed_exit == proc.returncode and _ALLOWED[token] == proc.returncode
    print(
        f"instrument={case.instrument} printed={token} printed_exit={printed_exit} "
        f"process_exit={proc.returncode} agree={agree}"
    )

    assert (proc.returncode == 0) is case.should_pass
    assert agree
