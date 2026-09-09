"""Every `tools/check_*.py` guard must stay GREEN on a healthy tree, and own a test.

🔴 **The failure this exists for: a guard that OVER-refuses.** Session 288 shipped a
first draft of ``check_battery_definitions`` whose no-op rule was wrong — it flagged a
mutation's ``new`` text appearing anywhere in the subject as "this changes nothing".
It reported **8 of 21 batteries dead**. The real number was **2**. Six healthy
batteries were accused, and the only thing that caught it was the author finding the
number surprising enough to go read the artifact.

That is not a process. A guard that over-refuses is not a stricter guard — it is a
broken one, and it is more dangerous than a guard that under-refuses, because people
start routing around a guard that cries wolf and then the real finding goes with it.

**This is the control that makes "no findings" mean something.** Every guard here is
run against the REAL repository, which is a tree we assert is healthy. A guard that
begins accusing that tree reddens immediately, on the commit that broke it, instead of
waiting for someone to be surprised by a number.

**It encodes a convention the repo already follows rather than inventing a rule.**
Measured at s288: 7 of the 7 guards that existed had a test module and 6 ran against
``REPO_ROOT``. The convention was real and unenforced — `check_plan_archive_refs` had
drifted to zero live-tree references, and the eighth guard (this session's) had no test
module at all. Making it mechanical is what stops the next one from drifting silently.

⚠️ **Scope, so a green is not over-read.** This says every guard *accepts* the current
tree. It says nothing about whether a guard would *catch* anything — that is each
guard's own test module's job, which is why the pairing assertion below is not
decoration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_DIR = REPO_ROOT / "tools"
GUARD_TEST_DIR = REPO_ROOT / "tests" / "tools"

#: Measured at s288. A floor, not an expectation of the exact count: guards get added,
#: and a test that pins the number would fail on every addition for no reason. What it
#: refuses is the glob quietly matching NOTHING — an empty parametrize is a green that
#: ran no checks at all, which is the vacuity this whole module exists to prevent.
_GUARD_FLOOR = 8


def _guards() -> list[Path]:
    return sorted(GUARD_DIR.glob("check_*.py"))


GUARDS = _guards()


def test_the_guard_glob_still_matches_something() -> None:
    """Non-vacuity for every parametrized test below.

    If ``tools/check_*.py`` stops matching — a rename, a move, a directory change —
    every parametrization below collects zero cases and the suite goes green having
    verified nothing. This is the assertion that turns that silence into a failure.
    """
    assert len(GUARDS) >= _GUARD_FLOOR, (
        f"found {len(GUARDS)} guards under {GUARD_DIR}/check_*.py, expected at least "
        f"{_GUARD_FLOOR}. Either the glob stopped matching (fix the glob) or guards were "
        f"deliberately removed (lower the floor, in the same commit, with the reason)."
    )


@pytest.mark.parametrize("guard", GUARDS, ids=lambda p: p.stem)
def test_every_guard_owns_a_test_module(guard: Path) -> None:
    """The pairing, made mechanical.

    A guard with no test module is a guard nobody has shown can FAIL. The live-tree
    check below proves only that it accepts a healthy tree — which a guard that always
    returns 0 also does. The two assertions are complementary and neither substitutes
    for the other.
    """
    expected = GUARD_TEST_DIR / f"test_{guard.stem}.py"
    assert expected.is_file(), (
        f"{guard.relative_to(REPO_ROOT)} has no test module at "
        f"{expected.relative_to(REPO_ROOT)}. A guard whose only evidence is that it "
        f"passes on a healthy tree is indistinguishable from `return 0`."
    )


def test_a_failing_subprocess_is_actually_visible_to_this_harness() -> None:
    """Positive control for the negative assertion below.

    ``every guard exits 0`` is satisfied by a runner that cannot observe a non-zero exit
    at all. Before any guard's 0 is trusted, prove the harness can SEE a 1 — on known
    content, deliberately failing.
    """
    proc = subprocess.run(
        [sys.executable, "-c", "raise SystemExit(3)"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 3, (
        "this harness cannot observe a non-zero exit, so every 'guard exited 0' below "
        f"would prove nothing. Got {proc.returncode}."
    )


@pytest.mark.parametrize("guard", GUARDS, ids=lambda p: p.stem)
def test_no_guard_accuses_the_real_tree(guard: Path) -> None:
    """The over-refusal control: a healthy tree must satisfy every guard.

    Run as a subprocess rather than by importing ``main()``: that is how pre-commit and
    CI invoke them, and an import-time difference (``sys.path`` bootstrap, a module-level
    read) is exactly the kind of thing that makes a guard behave one way under pytest and
    another in the hook that actually gates the commit.
    """
    proc = subprocess.run(
        [sys.executable, str(guard)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-25:]
    assert proc.returncode == 0, (
        f"{guard.relative_to(REPO_ROOT)} exited {proc.returncode} against the real tree.\n"
        f"Either the tree genuinely violates it — fix the tree — or the guard has begun "
        f"OVER-REFUSING, which is a defect in the guard and must be fixed there.\n"
        + "\n".join(tail)
    )
