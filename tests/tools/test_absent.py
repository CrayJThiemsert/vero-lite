"""`tools/absent.py` must measure an absence with a control that could have failed.

🔴 **What each case pins.** An empty result is the one reading that looks identical
whether the instrument worked or not — ``grep -c`` prints ``0`` for *"the pattern is
absent"* and ``0`` for *"I was pointed at the wrong file"*. PLAN-0123 §1.2 catalogues
three instrument errors of exactly that shape, so each test below is one way an
absence reading can be wrong while still printing a tidy zero:

* the scan stopped early and described a **window**, not the subject (#10);
* the **control** found nothing, so ``matched=0`` carried no information (#8);
* the instrument matched **itself** — a ``pgrep`` whose own command line satisfied
  the pattern, reporting a process running when nothing but the check was (#8).

Every assertion here is reached through the **real script as a subprocess** on a
planted fixture (PLAN-0123 §5: *a test that stubs the thing under test does not
satisfy any AC here*), so the seam under test is argv → scan → printed values →
exit status, the same seam a goal's ``check`` drives.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "absent.py"

#: The claim under test: this string is ABSENT from the subject. Chosen so it
#: cannot appear in the filler by accident.
_PATTERN = "ERROR: disk full"
#: The positive control: something the author knows IS there. A reading whose
#: control goes to zero is refused rather than reported as an absence.
_CONTROL = "level=info"

_VALUES_RE = re.compile(
    r"lines=(?P<lines>\d+) consumed=(?P<consumed>\d+) matched=(?P<matched>\d+) "
    r"control_hits=(?P<control_hits>\d+) self_excluded=(?P<self_excluded>\d+)"
)

#: Lesson #0056: an instrument whose reading you will act on passes a control on
#: known content before its first real reading is trusted. ``_values`` is an
#: instrument — it is the only thing standing between the tool's output and every
#: number asserted below, and an uncontrolled parser does not fail loudly, it
#: fails confidently.
_PARSER_FIXTURE = "  lines=40 consumed=40 matched=1 control_hits=1 self_excluded=0"
_PARSER_EXPECT = {"lines": 40, "consumed": 40, "matched": 1, "control_hits": 1, "self_excluded": 0}


def _values(stdout: str) -> dict[str, int]:
    """The five numbers the report printed, or a hard failure naming the output.

    A report that printed no values is INSUFFICIENT — never an implied zero.
    """
    match = _VALUES_RE.search(stdout)
    if match is None:
        raise AssertionError(
            "the report printed no values line — nothing below can be trusted.\n"
            f"stdout was:\n{stdout}"
        )
    return {k: int(v) for k, v in match.groupdict().items()}


def _planted(tmp_path: Path, *, with_pattern: bool = True, with_control: bool = True) -> Path:
    """AC-4's fixture: 40 lines, the pattern at line 33, the control at line 38."""
    lines = [f"line {i:02d} filler payload" for i in range(1, 41)]
    if with_pattern:
        lines[32] = f"line 33 {_PATTERN}"
    if with_control:
        lines[37] = f"line 38 {_CONTROL}"
    path = tmp_path / "subject.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _table(tmp_path: Path) -> Path:
    """A planted process table containing the instrument's own command line.

    The real ``/proc`` cannot have entries planted in it, and a ``--proc`` mode
    exercisable only against the live table is a mode no probe could redden.
    """
    rows = [
        "111\tpython tools/absent.py --proc --pattern ollama --control pytest",
        "222\tollama serve",
        "333\tpython -m pytest tests/tools",
    ]
    path = tmp_path / "proctable.tsv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(_TOOL), *args],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


# --- the parser's own control -------------------------------------------------


def test_the_values_parser_passes_its_own_control() -> None:
    """Read a known line before trusting the parser on a real one (Lesson #0056)."""
    assert _values(_PARSER_FIXTURE) == _PARSER_EXPECT


# --- A1: the scan consumed the whole subject ----------------------------------


def test_the_reading_consumes_every_line_of_its_subject(tmp_path: Path) -> None:
    """A1 — ``consumed == lines``, the two counted by separate passes.

    The non-vacuity assertion comes first on purpose: ``consumed == lines`` is
    satisfied by ``0 == 0``, so an instrument pointed at an empty file would pass
    this test while measuring nothing. Pinning ``lines == 40`` means the equality
    below is a statement about a subject that actually had content.
    """
    code, out = _run(
        ["--file", str(_planted(tmp_path)), "--pattern", _PATTERN, "--control", _CONTROL]
    )
    values = _values(out)
    print(f"exit={code} {values}")

    assert values["lines"] == 40
    assert values["consumed"] == values["lines"]


# --- A2: exit 0 is reserved for a controlled absence --------------------------


def test_an_absent_pattern_under_a_live_control_is_the_only_route_to_exit_zero(
    tmp_path: Path,
) -> None:
    """A2 — ``exit == 0`` iff ``matched == 0 and control_hits >= 1``.

    Both cases carry a live control, so this test says nothing about the failed
    control (that is A3's, and keeping them apart is what lets one probe redden
    one of them).
    """
    absent_code, absent_out = _run(
        [
            "--file",
            str(_planted(tmp_path, with_pattern=False)),
            "--pattern",
            _PATTERN,
            "--control",
            _CONTROL,
        ]
    )
    present_code, present_out = _run(
        ["--file", str(_planted(tmp_path)), "--pattern", _PATTERN, "--control", _CONTROL]
    )
    absent_values, present_values = _values(absent_out), _values(present_out)
    print(f"absent: exit={absent_code} {absent_values}")
    print(f"present: exit={present_code} {present_values}")

    assert (absent_values["matched"], absent_values["control_hits"], absent_code) == (0, 1, 0)
    assert (present_values["matched"], present_values["control_hits"], present_code) == (1, 1, 1)


# --- A3: a control that finds nothing invalidates the reading -----------------


def test_a_control_that_finds_nothing_refuses_rather_than_reporting_absence(
    tmp_path: Path,
) -> None:
    """A3 — ``exit == 2`` iff ``control_hits == 0``, and 2 is neither absent nor present.

    This is the whole reason the tool exists. With the control token gone the
    instrument has not shown it could find anything, so ``matched=0`` is not
    evidence of absence — and returning ``0`` here is the failure CLAUDE.md §8
    names: *a zero or absence needs a positive control that finds a known one.*
    """
    code, out = _run(
        [
            "--file",
            str(_planted(tmp_path, with_pattern=False, with_control=False)),
            "--pattern",
            _PATTERN,
            "--control",
            _CONTROL,
        ]
    )
    values = _values(out)
    print(f"exit={code} {values}")

    assert values["control_hits"] == 0
    assert code == 2


# --- A4: the instrument cannot match itself -----------------------------------


def test_the_instrument_excludes_its_own_command_line(tmp_path: Path) -> None:
    """A4 — a process whose argv names ``absent.py`` is withheld and counted.

    The planted table holds three rows: the instrument's own invocation (which
    contains the pattern, in its own arguments), one real match, and one
    control match. Without the exclusion the tool reports two matches and
    declares a process running on the strength of having been asked about it.
    """
    code, out = _run(
        [
            "--proc",
            "--proc-source",
            str(_table(tmp_path)),
            "--pattern",
            "ollama",
            "--control",
            "pytest",
        ]
    )
    values = _values(out)
    print(f"exit={code} {values}")

    assert values["self_excluded"] == 1
    assert (values["lines"], values["consumed"]) == (3, 3)
    assert values["matched"] == 1


def test_a_missing_file_refuses_instead_of_reporting_zero(tmp_path: Path) -> None:
    """A missing subject is a refusal, never an empty reading.

    ``exit 0`` on an unreadable subject is the same defect as an uncontrolled
    zero, reached by a different road: nothing was scanned, so nothing was
    shown to be absent.
    """
    code, _ = _run(
        ["--file", str(tmp_path / "nope.log"), "--pattern", _PATTERN, "--control", _CONTROL]
    )
    print(f"exit={code}")

    assert code == 2


def test_a_missing_process_table_refuses_instead_of_reporting_zero(tmp_path: Path) -> None:
    """The ``--proc`` half of the same rule, kept separate so one probe reddens one claim.

    This is the branch that matters most in practice: an empty process table is
    the shape a Windows-side interpreter produces for ``/proc``, and it makes
    every process look absent.
    """
    code, _ = _run(
        [
            "--proc",
            "--proc-source",
            str(tmp_path / "nope.tsv"),
            "--pattern",
            _PATTERN,
            "--control",
            _CONTROL,
        ]
    )
    print(f"exit={code}")

    assert code == 2


def test_the_report_is_written_to_the_evidence_file_with_its_provenance_header(
    tmp_path: Path,
) -> None:
    """Clause R2 + R7 — stdout never reaches the judge, so the values go to a file.

    The body below the header is byte-identical to what was printed: a file and
    a terminal telling two stories is how a number nobody took becomes a number
    somebody quoted.
    """
    destination = tmp_path / "evidence" / "C1.txt"
    code, out = _run(
        [
            "--file",
            str(_planted(tmp_path, with_pattern=False)),
            "--pattern",
            _PATTERN,
            "--control",
            _CONTROL,
            "--report-to",
            str(destination),
            "--gid",
            "s292test",
        ]
    )
    written = destination.read_text(encoding="utf-8")
    header, _, body = written.partition("---\n")
    print(f"exit={code} file_bytes={len(written)} header={header!r}")

    assert "gid=s292test" in header
    assert re.search(r"head=([0-9a-f]{40}|unknown)", header) is not None
    assert body.strip() == out.strip()
