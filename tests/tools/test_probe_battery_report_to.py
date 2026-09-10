"""`probe_battery run --report-to` must bank a provenance-stamped copy of its report.

🔴 **What this pins.** A battery's verdict is the strongest evidence this repo
produces — it is the only thing that turns a green into a witnessed RED — and
until now it existed only in a terminal. PLAN-0123 clause R2 says a check's
stdout never reaches the ``goal-evaluator``, so a T-ORACLE goal's judge has
nothing to read but a remembered ``PROBE-BATTERY: PASS``. Clause R7 adds the
stamp: a report that does not say which tree it ran against is
indistinguishable from one taken before the fix it is being quoted to justify.

The three header keys are not decoration. ``run_id`` ties the report to the
snapshot manifest that proves the tree was restored; ``head`` is what the judge
compares to the goal's ``declared_head``; ``battery_sha256`` is what makes
"these probes" a checkable claim rather than a filename.

The battery driven here is a real two-probe battery over a real fixture module,
run through the real driver — the seam is driver → pytest → junit → report →
file, per CLAUDE.md §8's scenario rule.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from tools._evidence import split_evidence

_ROOT = Path(__file__).resolve().parents[2]

#: The fixture project is a real git repository, not a bare directory. The
#: driver stamps ``head`` from ``git rev-parse HEAD`` in the project root and
#: falls back to an empty string outside a checkout — so a fixture with no repo
#: would let the "non-empty stamp" assertion pass or fail for reasons that have
#: nothing to do with the code under test.
_GIT_IDENTITY = (
    "-c",
    "user.email=fixture@example.invalid",
    "-c",
    "user.name=fixture",
)


def _git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *_GIT_IDENTITY, *args],  # noqa: S607 — PATH-resolved git intended
        cwd=str(project),
        capture_output=True,
        text=True,
        check=True,
    )


def _fixture_module(tmp_path: Path) -> Path:
    """A tiny module with two independently reddenable claims."""
    module = tmp_path / "test_reportto_fixture.py"
    module.write_text(
        "GREETING = 'hello'\n"
        "COUNT = 2\n"
        "\n"
        "\n"
        "def test_greeting_is_hello() -> None:\n"
        "    assert GREETING == 'hello'\n"
        "\n"
        "\n"
        "def test_count_is_two() -> None:\n"
        "    assert COUNT == 2\n",
        encoding="utf-8",
    )
    return module


def _battery_file(tmp_path: Path, module: Path) -> Path:
    rel = module.relative_to(tmp_path).as_posix()
    definition = {
        "claim_sources": [rel],
        "probes": [
            {
                "name": "F1",
                "subject": rel,
                "old": "GREETING = 'hello'",
                "new": "GREETING = 'goodbye'",
                "node_id": f"{rel}::test_greeting_is_hello",
                "expect_claim": "test_greeting_is_hello|GREETING == 'hello'|#0",
                "note": "fixture probe",
            },
            {
                "name": "F2",
                "subject": rel,
                "old": "COUNT = 2",
                "new": "COUNT = 3",
                "node_id": f"{rel}::test_count_is_two",
                "expect_claim": "test_count_is_two|COUNT == 2|#0",
                "note": "fixture probe",
            },
        ],
        "exemptions": {},
    }
    path = tmp_path / "battery.json"
    path.write_text(json.dumps(definition, indent=2), encoding="utf-8")
    return path


def _project(tmp_path: Path) -> tuple[Path, Path, str]:
    """Build the fixture project, commit it, and return ``(battery, report_to, head)``.

    Every test here needs all three and needs them built the same way; assembling
    them in one place is what stops the four cases from silently testing four
    slightly different fixtures.
    """
    module = _fixture_module(tmp_path)
    battery = _battery_file(tmp_path, module)
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "--quiet", "-m", "fixture")
    head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    return battery, tmp_path / "banked.txt", head


def _run(tmp_path: Path, battery: Path, report_to: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.probe_battery",
            "--project-root",
            str(tmp_path),
            "run",
            "--battery",
            str(battery),
            "--report-to",
            str(report_to),
        ],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        env={**os.environ, "PYTHONPATH": str(_ROOT)},
        check=False,
    )
    return proc.returncode, proc.stdout


def test_the_banked_report_is_byte_identical_to_what_was_printed(tmp_path: Path) -> None:
    """A1 — the file's body equals stdout, verbatim.

    Not "equivalent", not "contains the verdict": byte-equal. A banked report
    that trims, re-wraps or summarises is a second rendering of the run, and a
    second rendering is a thing that can disagree with the first.
    """
    battery, destination, _ = _project(tmp_path)
    code, stdout = _run(tmp_path, battery, destination)

    header, body = split_evidence(destination.read_text(encoding="utf-8"))
    print(
        f"exit={code} stdout_bytes={len(stdout)} file_body_bytes={len(body)} "
        f"header_keys={sorted(header)}"
    )

    assert "PROBE-BATTERY:" in stdout
    assert body == stdout


def test_the_header_carries_the_three_provenance_keys(tmp_path: Path) -> None:
    """A2 — ``run_id``, ``head`` and ``battery_sha256``, all present and non-empty.

    Non-empty is asserted separately from present because a stamp written as an
    empty string is the shape that passes a key check and tells the judge
    nothing.
    """
    battery, destination, _ = _project(tmp_path)
    _run(tmp_path, battery, destination)

    header, _ = split_evidence(destination.read_text(encoding="utf-8"))
    print(f"header={header}")

    assert sorted(k for k in ("run_id", "head", "battery_sha256") if header.get(k)) == [
        "battery_sha256",
        "head",
        "run_id",
    ]


def test_the_stamped_head_is_the_tree_the_probes_actually_ran_on(tmp_path: Path) -> None:
    """A3 — ``head`` equals the HEAD this test reads for itself.

    Read independently rather than taken from the report: a stamp that agrees
    with itself is not provenance. This is the assertion a hard-coded sha
    reddens while A2 stays perfectly green.
    """
    battery, destination, head = _project(tmp_path)
    _run(tmp_path, battery, destination)

    header, _ = split_evidence(destination.read_text(encoding="utf-8"))
    print(f"stamped={header.get('head')} observed={head}")

    assert len(head) == 40
    assert header.get("head") == head


def test_the_battery_digest_is_the_digest_of_the_battery_file(tmp_path: Path) -> None:
    """The third stamp, checked against a digest this test computes itself.

    ``battery_sha256`` is what makes "these probes ran" checkable after the file
    has been edited — a report naming a battery by path says nothing about which
    version of it produced the verdict.
    """
    battery, destination, _ = _project(tmp_path)
    _run(tmp_path, battery, destination)

    header, _ = split_evidence(destination.read_text(encoding="utf-8"))
    expected = hashlib.sha256(battery.read_bytes()).hexdigest()
    print(f"stamped={header.get('battery_sha256')} computed={expected}")

    assert header.get("battery_sha256") == expected
