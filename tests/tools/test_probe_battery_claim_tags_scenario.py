"""PLAN-0128 AC-8 — a TAGGED claim through the REAL driver, as its own child process.

The unit suite proves the enumerator reads a tag. It cannot prove the driver ADDRESSES one
end to end: `_resolve_declared` re-enumerates the module while the mutation is still on
disk, and whether a tag survives that is a property of a real run, not of a fixture.

Also here: the two fixtures that settle PLAN-0128 §9's open question — how the driver
classifies a tag that was moved by hand from one claim's anchor line onto another's.

🔴 **Its own module, for the denominator** — see `test_probe_coverage_claim_tags.py`.

POSIX-only by design: the driver runs WSL-side and CI is Linux.

NOTE — no comment here spells the tag marker out; see the sibling module's note.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.probe_battery import STATE_ENV, VERDICT_PASS
from tools.probe_battery._lock import LOCK_ENV

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="the driver runs WSL-side, CI is Linux"
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_SUBJECT = """
def classify(n):
    return "high" if n > 10 else "low"
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


_TAGGED_TEST = """from subject import classify


def test_fast_claim():
    assert classify(20) == "high"  # claim: fast
"""


def _make_tagged_project(tmp_path: Path, probe: dict[str, object]) -> Path:
    """The `_make_project` shape, with the claim TAGGED and the probe supplied whole."""
    (tmp_path / "subject.py").write_text(_SUBJECT, encoding="utf-8")
    (tmp_path / "test_fast.py").write_text(_TAGGED_TEST, encoding="utf-8")
    (tmp_path / "state").mkdir(exist_ok=True)
    battery = {"claim_sources": ["test_fast.py"], "probes": [probe]}
    (tmp_path / "battery.json").write_text(json.dumps(battery, indent=2), encoding="utf-8")
    return tmp_path


def test_a_tagged_claim_is_witnessed_through_the_real_driver(tmp_path: Path) -> None:
    """The whole path, once: real driver, real pytest, real junit, a tag as the address.

    `witnessed RED: 1` is the read that matters — it is the coverage report crediting the
    tag key, which is the thing the unit suite can only assert about `stable_key` in
    isolation.
    """
    project = _make_tagged_project(
        tmp_path,
        {
            "name": "P1",
            "subject": "subject.py",
            "old": "n > 10",
            "new": "n > 1000",
            "node_id": "test_fast.py::test_fast_claim",
            "expect_claim": "@fast",
        },
    )
    proc = _run_cli(project)
    print(proc.stdout)

    assert VERDICT_PASS in proc.stdout  # claim: pr1/scenario-tag-passes
    assert "claim : @fast" in proc.stdout  # claim: pr1/scenario-tag-is-the-address
    assert "witnessed RED: 1" in proc.stdout  # claim: pr1/scenario-tag-credited


def test_a_tagged_claim_survives_a_line_shift_in_its_own_module(tmp_path: Path) -> None:
    """🔴 The case a text key handles only by accident, and a line-numbered key not at all.

    The probe's subject is the TEST MODULE, and its mutation inserts two lines above the
    tagged assert while breaking it — the `_battery.py:512-517` measured shape. The
    assert's text changes too, so a text key would stop resolving and the run would fall
    back to the pre-run claim and report MISFIRE. `@fast` is not derived from that text,
    so the live lookup still finds the claim at the line the failure actually names.

    `MISFIRE` being absent is the negative half; `PROBE-BATTERY: PASS` with
    `witnessed RED: 1` is its positive control — a MISFIRE would fail the probe's
    declared expectation and take the verdict with it.
    """
    project = _make_tagged_project(
        tmp_path,
        {
            "name": "P1",
            "subject": "test_fast.py",
            "old": '    assert classify(20) == "high"  # claim: fast',
            "new": (
                "    filler_one = 1\n"
                "    filler_two = 2\n"
                '    assert classify(20) == "low"  # claim: fast'
            ),
            "node_id": "test_fast.py::test_fast_claim",
            "expect_claim": "@fast",
        },
    )
    proc = _run_cli(project)
    print(proc.stdout)

    assert VERDICT_PASS in proc.stdout  # claim: pr1/shift-still-passes
    assert "witnessed RED: 1" in proc.stdout  # claim: pr1/shift-still-credited
    assert "MISFIRE" not in proc.stdout  # claim: pr1/shift-is-not-a-misfire


def test_a_hand_transplanted_tag_is_classified_by_the_real_driver(tmp_path: Path) -> None:
    """🔴 PLAN-0128 §9's one open question, settled by running it rather than reading it.

    §2.3 records the residual narrowly: a tag CUT from one anchor line and PASTED onto
    another claim's is the one edit tags do not refuse, and the draft could not say how
    the driver classifies it. A specialist read of `_outcome.py:462-492` (relayed by the
    s310 dispatch, never run) said `GREEN` or `WITNESSED`; the drafter's read of the
    site-line comparison at `:478-485` said it depends on which assertion reddens.

    This is the fixture §9 asks for: two claims in one owner, `# claim: fast` moved from
    the first onto the SECOND, and a mutation that reddens **both**. Whatever it prints is
    the answer — the assertion below records the outcome rather than predicting it, and no
    AC closes on which one it is. The printed value goes in the PR body.
    """
    (tmp_path / "subject.py").write_text(_SUBJECT, encoding="utf-8")
    # The tag sits on the SECOND assert; the FIRST is the one it used to name.
    # (The marker is not spelled in this comment: a prose comment carrying a live
    #  marker is parsed as a tag and refused, which is how this line was found.)
    (tmp_path / "test_fast.py").write_text(
        "from subject import classify\n"
        "\n"
        "\n"
        "def test_fast_claim():\n"
        '    assert classify(20) == "high"\n'
        '    assert classify(30) == "high"  # claim: fast\n',
        encoding="utf-8",
    )
    (tmp_path / "state").mkdir(exist_ok=True)
    battery = {
        "claim_sources": ["test_fast.py"],
        "probes": [
            {
                "name": "P1",
                "subject": "subject.py",
                # reddens BOTH asserts, so the site comparison has a real choice to make
                "old": "n > 10",
                "new": "n > 1000",
                "node_id": "test_fast.py::test_fast_claim",
                "expect_claim": "@fast",
            }
        ],
    }
    (tmp_path / "battery.json").write_text(json.dumps(battery, indent=2), encoding="utf-8")

    proc = _run_cli(tmp_path)
    print(proc.stdout)

    outcomes = [o for o in ("WITNESSED", "MISFIRE", "GREEN", "CRASHED") if o in proc.stdout]
    assert outcomes == ["MISFIRE"]  # claim: pr1/transplant-both-red-is-a-misfire


def test_a_transplanted_tag_is_credited_silently_but_strands_its_old_claim_as_a_gap(
    tmp_path: Path,
) -> None:
    """🔴 The OTHER branch — and it answers §9 better than either reading in the PLAN.

    The test above reddens both asserts, so pytest stops at the first, which is the
    DE-TAGGED original: the site comparison disagrees with the declared line and the run
    refuses loudly. That is the favourable branch, and it is not the whole answer.

    Here the mutation narrows `classify` so that only the SECOND assert reddens — the one
    the tag was transplanted onto. Measured, 2026-09-20:

    * the **classifier** is fooled exactly as §2.3 feared: `✅ P1  WITNESSED`, credited at
      `test_fast.py:6`, because the declared claim really is at that site now;
    * the **coverage report** is not: the de-tagged original at line 5 is addressed by
      nothing, so it lands in `GAPS: 1` and the run ends `PROBE-BATTERY: FAIL`.

    So a hand transplant is **not** silent end to end. What catches it is lesson #0047's
    fourth clause — name every claim no probe reddened — and not the site comparison at
    all. Neither reading recorded in §2.3 considered the coverage half; both were arguing
    about the classifier alone.

    ⚠️ The catch is conditional and the condition is worth stating: it holds because the
    transplanted-FROM claim is in `claim_sources` and nothing else addresses it. A
    transplant onto a claim whose original is covered by some other probe would still be
    silent. Recorded, not repaired — no AC closes on it.
    """
    (tmp_path / "subject.py").write_text(_SUBJECT, encoding="utf-8")
    (tmp_path / "test_fast.py").write_text(
        "from subject import classify\n"
        "\n"
        "\n"
        "def test_fast_claim():\n"
        '    assert classify(20) == "high"\n'
        '    assert classify(30) == "high"  # claim: fast\n',
        encoding="utf-8",
    )
    (tmp_path / "state").mkdir(exist_ok=True)
    battery = {
        "claim_sources": ["test_fast.py"],
        "probes": [
            {
                "name": "P1",
                "subject": "subject.py",
                # 20 still classifies high, 30 no longer does: ONLY the tagged line reddens
                "old": "n > 10",
                "new": "10 < n < 25",
                "node_id": "test_fast.py::test_fast_claim",
                "expect_claim": "@fast",
            }
        ],
    }
    (tmp_path / "battery.json").write_text(json.dumps(battery, indent=2), encoding="utf-8")

    proc = _run_cli(tmp_path)
    print(proc.stdout)

    # The classifier IS fooled — this is the residual, witnessed.
    assert "✅ P1  WITNESSED" in proc.stdout  # claim: pr1/transplant-credited-at-new-site

    # …and the coverage half is what refuses anyway. Asserted together so a future change
    # that makes the battery pass here cannot slip by as "the classifier got stricter".
    assert ("GAPS: 1" in proc.stdout, VERDICT_PASS in proc.stdout) == (
        True,
        False,
    )  # claim: pr1/transplant-stranded-claim-is-a-gap
