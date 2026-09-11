r"""A rendered goal check must hand its instrument the exact bytes the author typed.

🔴 **The measured failure this pins (s295).** ``tools/goal_template.py`` rendered
caller-supplied values into its check scripts with Python ``repr``. That is
Python-literal quoting, not shell quoting, and the two agree often enough to hide
the difference. Inside bash single quotes a doubled backslash stays doubled, so
both T-ABSENT goals rendered on 2026-09-11 (``20260911T074919-5d8c9e87`` and
``-6d1d537c``) carried a broken instrument:

- ``translate \+ phrase prompts …`` reached ``tools/absent.py`` with two
  backslashes and read ``matched=0`` against a file where the author's pattern
  matched once — a vacuous PASS;
- ``internal. for .seq.\)`` arrived as an invalid regex, so the check exited 2 on
  every evaluation and never wrote the evidence file its judge was told to read.

Two siblings came out of the same audit, and both are pinned here. T-COUNT did no
quoting at all (``--field error kind`` reached ``tally`` as two arguments), and
T-ORACLE's claim — a literal ``stable_key`` — reached ``absent.py`` as a regex,
where ``|`` is alternation: a report naming only a different ``…|#0`` claim
satisfied it through the ``#0`` branch.

The earlier suite rendered ``--pattern ERROR`` and never ran a rendered script, so
it agreed with the defect by construction.

**Why every case runs the real script under real bash.** The seam is renderer ->
the one shell layer -> the instrument's argv, and only bash can say what bash
hands over. Each case drives the renderer's real ``main``, reads the goal back
through the GATE's own parser, splits each ``cmd`` with the gate's own
``shlex.split``, runs the script it names, and reads what the real instrument
reports it received — from the evidence file, which is what the judge reads.

**What is relocated, and why that is not a stub.** A rendered script opens with
``cd <REPO_ROOT>`` and ``source .venv/bin/activate``. A Code-tab worktree has no
``.venv`` of its own, so pointed at the checkout this suite would read ``exit 8``
in a worktree and pass only in CI. ``REPO_ROOT`` is therefore a temporary project
whose ``tools`` links to this repo's real ``tools/`` and whose ``.venv`` links to
the venv running the suite: the real activation script and the real instruments,
from a location every checkout has.
"""

from __future__ import annotations

import ast
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / ".claude" / "hooks"))

from _goal_state import load_goal  # noqa: E402 — after the sys.path bootstrap

from tools import goal_template  # noqa: E402
from tools._evidence import EXIT_FAIL, EXIT_PASS, split_evidence, write_evidence  # noqa: E402
from tools.probe_battery._battery import (  # noqa: E402
    Battery,
    ProbeResult,
    _finalize,
    _index_claims,
)
from tools.probe_battery._outcome import Classification, Outcome  # noqa: E402
from tools.probe_coverage import enumerate_claims  # noqa: E402

#: absent.py prints the two values it was handed with ``!r``. repr is injective, so
#: equal reprs mean equal strings: every comparison below is byte for byte.
_ABSENT_ARGV_RE = re.compile(r"^pattern: (?P<pattern>.+)   control: (?P<control>.+)$", re.MULTILINE)

#: tally.py's report names the file, the field and the value set it was handed.
_TALLY_FILE_RE = re.compile(r"^file: (?P<file>.+)$", re.MULTILINE)
_TALLY_FIELD_RE = re.compile(r"   missing '(?P<field>.+)': \d+$", re.MULTILINE)
_TALLY_EXPECT_RE = re.compile(r"^  expected values: (?P<expect>\[.*\])   actual: ", re.MULTILINE)


@dataclass(frozen=True)
class _Reading:
    """One rendered check, run: what the gate keeps and what the judge reads."""

    returncode: int
    #: The evidence file's report body, or "" when the check wrote none.
    evidence: str
    #: Merged stdout+stderr. Printed so a RED names its cause; never asserted on.
    output: str


def _absent_received(report: str) -> tuple[str, str] | None:
    """``(pattern, control)`` as absent.py reports receiving them, or None.

    None rather than an exception: a script that never ran must redden the
    assertion comparing its values. A helper that raised would move the RED off
    that claim, and a probe aimed at the claim would credit nothing.
    """
    match = _ABSENT_ARGV_RE.search(report)
    if match is None:
        return None
    return ast.literal_eval(match["pattern"]), ast.literal_eval(match["control"])


def _tally_received(report: str) -> tuple[str, str, list[str]] | None:
    """``(file, field, expected values)`` as tally.py reports receiving them, or None."""
    file_match = _TALLY_FILE_RE.search(report)
    field_match = _TALLY_FIELD_RE.search(report)
    expect_match = _TALLY_EXPECT_RE.search(report)
    if file_match is None or field_match is None or expect_match is None:
        return None
    return file_match["file"], field_match["field"], ast.literal_eval(expect_match["expect"])


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A ``REPO_ROOT`` any checkout can run a rendered script from (module docstring)."""
    venv = Path(sys.prefix)
    if not (venv / "bin" / "activate").is_file():
        pytest.fail(
            f"the suite is not running inside a venv with bin/activate ({venv}); a rendered "
            "check sources exactly that file, so there is nothing real to run it against"
        )
    root = tmp_path / "project"
    root.mkdir()
    (root / "tools").symlink_to(_ROOT / "tools", target_is_directory=True)
    (root / ".venv").symlink_to(venv, target_is_directory=True)
    monkeypatch.setattr(goal_template, "REPO_ROOT", root)
    monkeypatch.setattr(goal_template, "SCRIPT_ROOT", tmp_path / "goal-checks")
    monkeypatch.setattr(goal_template, "EVIDENCE_ROOT", tmp_path / "goal-evidence")
    return root


def _instrument(project: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """The same instrument, handed its values as argv — no shell anywhere."""
    return subprocess.run(
        [sys.executable, "-m", *argv],
        capture_output=True,
        text=True,
        cwd=str(project),
        check=False,
        timeout=60,
    )


def _declare(tmp_path: Path, name: str, *template_args: str) -> Path:
    """Declare a goal through the renderer's real CLI entry; return its goal file."""
    goal_file = tmp_path / f"{name}-goal.json"
    code = goal_template.main(
        [
            *template_args,
            "--goal-file",
            str(goal_file),
            "--history-root",
            str(tmp_path / f"{name}-history"),
        ]
    )
    if code != EXIT_PASS:
        pytest.fail(f"the renderer refused to declare {name} (exit={code})")
    return goal_file


def _run_check(goal_file: Path, criterion_id: str) -> _Reading:
    """Run one check criterion the way ``_goal_gate._run_one_check`` does.

    ``shlex.split`` is the gate's own split. The rendered ``cmd`` is
    ``wsl.exe --exec bash <script>``, and ``wsl.exe --exec`` runs the rest of that
    argv inside WSL with no shell — so on a Linux host the rest IS the argv.
    """
    goal = load_goal(goal_file)
    if goal is None:
        pytest.fail(f"the gate's own parser rejected {goal_file}")
    [criterion] = [c for c in goal.criteria if c.id == criterion_id]
    argv = shlex.split(criterion.cmd or "")
    if argv[:2] != ["wsl.exe", "--exec"]:
        pytest.fail(f"a cmd shape this suite does not know how to run: {criterion.cmd!r}")
    proc = subprocess.run(argv[2:], capture_output=True, text=True, check=False, timeout=60)
    evidence_file = goal_template.EVIDENCE_ROOT / Path(argv[-1]).parent.name / f"{criterion_id}.txt"
    body = ""
    if evidence_file.is_file():
        body = split_evidence(evidence_file.read_text(encoding="utf-8"))[1]
    return _Reading(proc.returncode, body, proc.stdout + proc.stderr)


# --- T-ABSENT -----------------------------------------------------------------

_ABSENT_CASES = [
    pytest.param(
        r"translate \+ phrase prompts and the D6 prompt log",
        r"RepairCase\w+Quote",
        ("translate + phrase prompts and the D6 prompt log", "RepairCaseAcceptedQuote"),
        id="backslash_plus",
    ),
    pytest.param(
        r"internal. for .seq.\)",
        r"accepted \(quote\)",
        ("internal_ for _seq_)", "accepted (quote)"),
        id="backslash_paren",
    ),
    pytest.param(
        "the operator's queue",
        "Cray's ruling",
        ("the operator's queue", "Cray's ruling"),
        id="single_quote",
    ),
    pytest.param(
        "several  spaced   words",
        "known   control",
        ("several  spaced   words", "known   control"),
        id="spaces",
    ),
    pytest.param(
        'say "it\'s" \\+',
        '"it\'s" known\\.',
        ('say "it\'s" +', '"it\'s" known.'),
        id="both_quotes_and_backslash",
    ),
]


@pytest.mark.parametrize(("pattern", "control", "subject_lines"), _ABSENT_CASES)
def test_a_rendered_absent_goal_hands_absent_py_every_value_byte_for_byte(
    pattern: str,
    control: str,
    subject_lines: tuple[str, str],
    tmp_path: Path,
    project: Path,
) -> None:
    """C0 and C1 receive the pattern, the control and the file exactly as typed.

    The subject's path carries a space and a quote too, so the file argument is
    exercised by every case rather than by one written for it.
    """
    subject = tmp_path / "operator's notes" / "plan text.md"
    subject.parent.mkdir()
    subject.write_text(
        "an unrelated first line\n" + "\n".join(subject_lines) + "\n", encoding="utf-8"
    )

    # Control (Lesson #0056), before any rendered reading is trusted: the same values
    # as argv, no shell, must come back unchanged AND find the planted line. That
    # rules out the parser, absent.py and the subject as the cause of a RED below.
    direct = _instrument(
        project, "tools.absent", "--file", str(subject), "--pattern", pattern, "--control", control
    )
    print(f"sent pattern={pattern!r} control={control!r} file={str(subject)!r}")
    print(f"direct rc={direct.returncode} received={_absent_received(direct.stdout)!r}")
    assert (_absent_received(direct.stdout), direct.returncode) == ((pattern, control), EXIT_FAIL)

    goal_file = _declare(
        tmp_path, "absent", "T-ABSENT", "--file", str(subject), "--pattern", pattern,
        "--control", control,
    )  # fmt: skip
    c0 = _run_check(goal_file, "C0")
    c1 = _run_check(goal_file, "C1")
    print(f"C0 rc={c0.returncode} received={_absent_received(c0.evidence)!r} {c0.output[-400:]!r}")
    print(f"C1 rc={c1.returncode} received={_absent_received(c1.evidence)!r} {c1.output[-400:]!r}")

    assert _absent_received(c0.evidence) == (control, control)
    assert _absent_received(c1.evidence) == (pattern, control)
    # The gate keeps exit codes, never evidence, so this pair is what Stop records.
    # C0 is control mode and must FIND the control; C1 must read what argv read.
    assert (c0.returncode, c1.returncode) == (EXIT_PASS, direct.returncode)


# --- T-ORACLE -----------------------------------------------------------------

#: Two one-test modules. The credited claim's key carries ``(``, ``[`` and ``"`` as
#: well as ``|`` — characters a regex reads as syntax.
_CREDITED_MODULE = (
    'def test_x():\n    values = {"checks": "2"}\n    assert int(values["checks"]) >= 1\n'
)
_OTHER_MODULE = (
    'def test_y():\n    values = {"judges": "1"}\n    assert int(values["judges"]) >= 1\n'
)


def _banked_report(tmp_path: Path, name: str, module_source: str) -> tuple[Path, str]:
    """A banked report crediting one claim, rendered by the driver's own report code.

    ``_finalize`` is what ``python -m tools.probe_battery run`` prints, and
    ``write_evidence`` with the driver's header keys is what its ``--report-to``
    writes. Only the probe's pytest run is skipped: the report is the producer on
    this seam, not a battery.
    """
    module = tmp_path / f"{name}.py"
    module.write_text(module_source, encoding="utf-8")
    [claim] = enumerate_claims(module)
    battery = Battery.from_json(
        {
            "claim_sources": [str(module)],
            "probes": [
                {
                    "name": "P1",
                    "subject": str(module),
                    "old": "values",
                    "new": "vals",
                    "node_id": f"{module}::{claim.owner}",
                    "expect_claim": claim.stable_key,
                }
            ],
        }
    )
    witnessed = ProbeResult(
        battery.probes[0],
        Classification(
            Outcome.WITNESSED,
            f"AssertionError at {module.name}:{claim.lineno} — the declared assertion failed "
            "at its own site.",
        ),
        claim.stable_key,
    )
    result = _finalize(battery, _index_claims(battery), (witnessed,), f"fixture-{name}", False)
    report = tmp_path / "banked reports" / f"{name}.txt"
    write_evidence(
        result.report,
        report,
        {
            "run_id": result.run_id,
            "head": "0" * 40,
            "battery_sha256": "0" * 64,
            "battery": f"tests/batteries/{name}.json",
        },
    )
    return report, claim.stable_key


def test_a_rendered_oracle_goal_reads_the_claim_as_a_literal_not_a_regex(
    tmp_path: Path, project: Path
) -> None:
    """C2 passes on the report crediting the claim and FAILS on one crediting another.

    Unescaped, ``test_x|int(values["checks"]) >= 1|#0`` is three alternatives, and the
    ``#0`` one matches the first-occurrence claim of any report at all.
    """
    credited, claim = _banked_report(tmp_path, "credits-the-claim", _CREDITED_MODULE)
    other, other_claim = _banked_report(tmp_path, "credits-another-claim", _OTHER_MODULE)

    # Control: escaped by the TEST, independently of the renderer, the key tells the
    # two reports apart — so a RED below cannot be a pair of reports no correct
    # pattern could distinguish.
    direct = [
        _instrument(
            project, "tools.absent", "--file", str(report), "--pattern", re.escape(claim),
            "--control", "PROBE-BATTERY:", "--expect-present",
        ).returncode
        for report in (credited, other)
    ]  # fmt: skip
    print(f"claim={claim!r} other={other_claim!r} direct_rc={direct}")
    assert direct == [EXIT_PASS, EXIT_FAIL]

    # Declared and run one at a time. Two T-ORACLE goals differing only in --report
    # share a gid within one second (the goal text omits the report), and the second
    # declaration's scripts would overwrite the first's before it ran.
    on_credited = _run_check(
        _declare(
            tmp_path, "credited", "T-ORACLE", "--battery", "tests/batteries/fixture.json",
            "--claim", claim, "--report", str(credited),
        ),
        "C2",
    )  # fmt: skip
    print(f"C2 on the crediting report rc={on_credited.returncode} {on_credited.output[-400:]!r}")
    assert on_credited.returncode == EXIT_PASS

    on_other = _run_check(
        _declare(
            tmp_path, "other", "T-ORACLE", "--battery", "tests/batteries/fixture.json",
            "--claim", claim, "--report", str(other),
        ),
        "C2",
    )  # fmt: skip
    print(f"C2 on the other claim's report rc={on_other.returncode} {on_other.output[-400:]!r}")
    assert on_other.returncode == EXIT_FAIL


# --- T-COUNT ------------------------------------------------------------------


def test_a_rendered_count_goal_hands_tally_every_value_byte_for_byte(
    tmp_path: Path, project: Path
) -> None:
    """C0 and C1 receive the file, the field and the value set exactly as typed.

    Measured s295 on the pre-fix renderer: ``--field error kind`` reached tally as
    two arguments, and the check exited 2 on ``unrecognized arguments: kind``.
    """
    records = tmp_path / "operator's logs" / "stop classifier.jsonl"
    records.parent.mkdir()
    records.write_text(
        '{"error kind": "time out"}\n{"error kind": "ok"}\n{"error kind": "time out"}\n',
        encoding="utf-8",
    )
    field, expect, values = "error kind", "ok,time out", ["ok", "time out"]

    # Control, as in the T-ABSENT case: argv with no shell reads the values back.
    direct = _instrument(project, "tools.tally", str(records), "--field", field, "--expect", expect)
    print(f"direct rc={direct.returncode} received={_tally_received(direct.stdout)!r}")
    assert (_tally_received(direct.stdout), direct.returncode) == (
        (str(records), field, values),
        EXIT_PASS,
    )

    goal_file = _declare(
        tmp_path, "count", "T-COUNT", "--file", str(records), "--field", field, "--expect", expect
    )
    c0 = _run_check(goal_file, "C0")
    c1 = _run_check(goal_file, "C1")
    print(f"C0 rc={c0.returncode} received={_tally_received(c0.evidence)!r} {c0.output[-400:]!r}")
    print(f"C1 rc={c1.returncode} received={_tally_received(c1.evidence)!r} {c1.output[-400:]!r}")

    # C0 appends a value --expect cannot contain, so it is handed one more value than C1.
    impossible = goal_template._IMPOSSIBLE_VALUE
    assert _tally_received(c0.evidence) == (str(records), field, sorted([*values, impossible]))
    assert _tally_received(c1.evidence) == (str(records), field, values)
    # C0 is control mode (--expect-refusal) and passes only when tally REFUSES.
    assert (c0.returncode, c1.returncode) == (EXIT_PASS, EXIT_PASS)
