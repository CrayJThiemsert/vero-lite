"""Declaring a second goal must be a RECORD, never a silent overwrite (R8 / AC-8).

🔴 **The loophole this closes.** PLAN-0123 names two ways a goal gate stops
meaning anything. The first is the hollow goal — no criteria, so it can never
fail; Step 1 closed that. The second is subtler and lives here: declare a hard
goal, find it inconvenient, declare an easy one over the top. The gate goes
green, the trail says nothing happened, and nobody can tell the difference
between a goal that passed and a goal that was abandoned.

R8's answer is not to forbid the replacement — sometimes the goal really has
moved — but to make the abandonment **a record**. An unpassed goal is appended
to, under a fresh ``T<n>-`` prefix that keeps every prior id readable; replacing
it on purpose costs an archived copy in ``goal-history/`` stamped
``replaced-unpassed``; a goal that actually passed archives as ``passed``. The
three dispositions are what a later reader uses to tell the cases apart.

Every case drives the real renderer as a subprocess against an isolated goal
file and an isolated history root — the archive is the artifact under test, so
it cannot be shared with the live one.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / ".claude" / "hooks"))

from _goal_state import Criterion, Goal, save_goal  # noqa: E402 — sys.path bootstrap above

_LIFECYCLE_RE = re.compile(
    r"pre_ids=(?P<pre_ids>\[[^\]]*\]) post_ids=(?P<post_ids>\[[^\]]*\]) "
    r"archived=(?P<archived>\S+) disposition=(?P<disposition>\S+)"
)

#: Lesson #0056 — control the parser on known content first.
_PARSER_FIXTURE = (
    "pre_ids=['C0', 'C1'] post_ids=['C0', 'C1', 'T1-C0'] archived=none disposition=appended"
)


def _lifecycle(stdout: str) -> dict[str, str]:
    match = _LIFECYCLE_RE.search(stdout)
    if match is None:
        raise AssertionError(f"the renderer printed no lifecycle line:\n{stdout}")
    return match.groupdict()


def _ids(rendered: str) -> list[str]:
    return re.findall(r"'([^']+)'", rendered)


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.goal_template", *args],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        env={**os.environ, "PYTHONPATH": str(_ROOT)},
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _existing(tmp_path: Path, status: str) -> Path:
    """A goal already on disk, in the state the case is about."""
    goal_file = tmp_path / "goal.json"
    save_goal(
        Goal(
            goal="the prior goal, whose trail must not vanish",
            status=status,
            session=291,
            created="2026-09-10T00:00:00+0000",
            declared_head="0" * 40,
            criteria=[
                Criterion(id="C0", kind="check", desc="BASIS: tree.", cmd="true", timeout_s=10),
                Criterion(id="C1", kind="check", desc="BASIS: tree.", cmd="true", timeout_s=10),
                Criterion(id="J1", kind="judge", desc="FALSIFIER: something."),
            ],
        ),
        goal_file,
    )
    return goal_file


def _render(tmp_path: Path, goal_file: Path, *extra: str) -> tuple[int, str]:
    log = tmp_path / "log.jsonl"
    log.write_text('{"transport":"ok"}\n', encoding="utf-8")
    return _run(
        [
            "T-COUNT",
            "--file",
            str(log),
            "--field",
            "transport",
            "--expect",
            "ok",
            "--goal-file",
            str(goal_file),
            "--history-root",
            str(tmp_path / "goal-history"),
            *extra,
        ]
    )


def test_the_lifecycle_parser_passes_its_own_control() -> None:
    """Read a known line before trusting the parser on a real one."""
    values = _lifecycle(_PARSER_FIXTURE)
    assert (values["disposition"], _ids(values["post_ids"])) == (
        "appended",
        ["C0", "C1", "T1-C0"],
    )


def test_declaring_over_an_unpassed_goal_appends_and_keeps_every_prior_id(
    tmp_path: Path,
) -> None:
    """A1 — append, never overwrite. Every id that was there is still there.

    Overwriting erases the trail that says what the earlier goal found, which is
    the whole abandonment loophole. The new criteria arrive under a ``T1-``
    prefix so a reader can see there were two rounds.
    """
    goal_file = _existing(tmp_path, "active")
    code, out = _render(tmp_path, goal_file)
    values = _lifecycle(out)
    pre, post = _ids(values["pre_ids"]), _ids(values["post_ids"])
    print(f"exit={code} pre={pre} post={post} disposition={values['disposition']}")

    assert set(pre) <= set(post)
    assert any(i.startswith("T1-") for i in post)


def test_replacing_an_unpassed_goal_archives_it_as_abandoned(tmp_path: Path) -> None:
    """A2 — ``--replace`` costs an archived copy stamped ``replaced-unpassed``.

    The disposition is the point. Anyone reading ``goal-history/`` later can tell
    a goal that was met from a goal that was walked away from, and the second is
    exactly what a green gate would otherwise hide.
    """
    goal_file = _existing(tmp_path, "active")
    code, out = _render(tmp_path, goal_file, "--replace")
    values = _lifecycle(out)
    archived = Path(values["archived"])
    payload = json.loads(archived.read_text(encoding="utf-8")) if archived.is_file() else {}
    kept = len(payload.get("criteria", []))
    print(
        f"exit={code} archived={archived.name if archived.is_file() else 'MISSING'} "
        f"disposition={payload.get('disposition')} archived_criteria={kept}"
    )

    assert archived.is_file()
    assert payload.get("disposition") == "replaced-unpassed"
    assert len(payload.get("criteria", [])) == 3


def test_replacing_a_passed_goal_archives_it_as_passed(tmp_path: Path) -> None:
    """A3 — a goal that was actually met archives under a different word.

    Same mechanism, opposite meaning. Collapsing the two dispositions into one
    would make the archive unable to answer the only question anyone asks of it.
    """
    goal_file = _existing(tmp_path, "passed")
    code, out = _render(tmp_path, goal_file)
    values = _lifecycle(out)
    archived = Path(values["archived"])
    payload = json.loads(archived.read_text(encoding="utf-8")) if archived.is_file() else {}
    print(
        f"exit={code} archived={archived.name if archived.is_file() else 'MISSING'} "
        f"disposition={payload.get('disposition')}"
    )

    assert archived.is_file()
    assert payload.get("disposition") == "passed"


def test_a_first_declaration_archives_nothing(tmp_path: Path) -> None:
    """The base case, and the non-vacuity control for the two archive assertions.

    Without it, a renderer that archived on EVERY run would satisfy A2 and A3
    perfectly while making the archive meaningless.
    """
    goal_file = tmp_path / "goal.json"
    code, out = _render(tmp_path, goal_file)
    values = _lifecycle(out)
    print(f"exit={code} pre={values['pre_ids']} archived={values['archived']}")

    assert values["archived"] == "none"
    assert _ids(values["pre_ids"]) == []
