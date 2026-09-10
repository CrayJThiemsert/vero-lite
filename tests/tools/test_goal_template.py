"""`tools/goal_template.py` must emit only goals that satisfy R1-R8, and refuse by clause.

🔴 **What this pins.** PLAN-0123 §1.2 catalogues sixteen instrument errors the
Axis-B gate would have caught, across two sessions in which no goal was ever
declared. The diagnosis was cost: a *good* goal is expensive to hand-write, so
the honest path lost to taking the reading and moving on. The renderer is the
intervention, and a renderer that emits a goal violating the very contract it
advertises would be worse than none — it would put the contract's name on
something that does not satisfy it.

So each case below is one clause, and each refusal case is one way a caller can
hand the renderer something that must not become a goal.

Every assertion runs the **real script as a subprocess** and parses the goal
through the **gate's own** ``Goal.from_json`` — not a local copy of the schema.
A test that validated against its own idea of the shape would agree with any
renderer, including one whose output the gate rejects.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / ".claude" / "hooks"))

from _goal_state import Goal  # noqa: E402 — after the sys.path bootstrap

_SUMMARY_RE = re.compile(
    r"checks=(?P<checks>\d+) judges=(?P<judges>\d+) sum_timeout=(?P<sum_timeout>\d+) "
    r"has_dollar=(?P<has_dollar>\w+) has_head_pin=(?P<has_head_pin>\w+) "
    r"control=(?P<control>\S+) evidence_dir=(?P<evidence_dir>\S+) "
    r"falsifier=(?P<falsifier>\w+) declared_head=(?P<declared_head>\S+)"
)

#: Lesson #0056 — the summary parser is an instrument, and an uncontrolled
#: instrument does not fail loudly, it fails confidently.
_PARSER_FIXTURE = (
    "checks=2 judges=1 sum_timeout=60 has_dollar=False has_head_pin=False "
    "control=C0 evidence_dir=/tmp/ev falsifier=True declared_head=abc123"
)


def _summary(stdout: str) -> dict[str, str]:
    match = _SUMMARY_RE.search(stdout)
    if match is None:
        raise AssertionError(f"the renderer printed no summary line:\n{stdout}")
    return match.groupdict()


def _body(stdout: str) -> dict[str, object]:
    """The rendered goal JSON, or a LEGIBLE failure.

    A refusal prints the summary line and no goal body. Letting ``str.index``
    raise ``ValueError`` here makes every refusal-inducing mutation crash instead
    of reddening the assertion it was aimed at — and a probe that crashes credits
    nothing (Lesson #0043: a RED must name what broke). Measured: three probes in
    this module's first battery run died exactly that way.
    """
    start = stdout.find("{")
    if start == -1:
        raise AssertionError(
            "the renderer printed no goal body — it REFUSED. Any assertion about the "
            "body must come after one about the summary line, which is printed either "
            f"way.\n{stdout}"
        )
    obj, _ = json.JSONDecoder().raw_decode(stdout[start:])
    assert isinstance(obj, dict)
    return obj


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


def _log(tmp_path: Path) -> Path:
    path = tmp_path / "log.jsonl"
    path.write_text(
        '{"transport":"ok"}\n{"transport":"timeout"}\n{"transport":"ok"}\n', encoding="utf-8"
    )
    return path


def _args_for(template: str, tmp_path: Path) -> list[str]:
    """Sample parameters for each template — the ones an agent already holds."""
    log = str(_log(tmp_path))
    return {
        "T-COUNT": [template, "--file", log, "--field", "transport", "--expect", "ok,timeout"],
        "T-ABSENT": [template, "--file", log, "--pattern", "ERROR", "--control", "transport"],
        "T-ORACLE": [
            template,
            "--battery",
            "tests/batteries/plan-0123-step2-ac4-absent.json",
            "--claim",
            "test_x|y == 1|#0",
            "--report",
            str(tmp_path / "banked.txt"),
        ],
    }[template]


TEMPLATES = ["T-COUNT", "T-ABSENT", "T-ORACLE"]


def test_the_summary_parser_passes_its_own_control() -> None:
    """Read a known line before trusting the parser on a real one."""
    assert _summary(_PARSER_FIXTURE)["control"] == "C0"


# --- A1-A5: what every rendered goal satisfies --------------------------------


@pytest.mark.parametrize("template", TEMPLATES)
def test_every_template_renders_a_goal_the_gate_itself_accepts(
    template: str, tmp_path: Path
) -> None:
    """A1 + the parse. A goal the gate rejects is a goal that never runs.

    ``Goal.from_json`` is imported from ``.claude/hooks/`` rather than
    re-implemented: the renderer's whole claim is that its output is what the
    Stop hook will read, and only the hook's own parser can settle that.
    """
    code, out = _run([*_args_for(template, tmp_path), "--dry-run"])
    values = _summary(out)
    print(f"{template} exit={code} {values}")

    assert code == 0

    goal = Goal.from_json(_body(out))
    print(f"{template} parsed={goal is not None}")
    assert goal is not None
    assert int(values["checks"]) >= 1
    assert int(values["judges"]) >= 1


@pytest.mark.parametrize("template", TEMPLATES)
def test_the_checks_fit_inside_the_gates_deterministic_budget(
    template: str, tmp_path: Path
) -> None:
    """A2 — the checks sum to <= 100 s against the gate's 120 s ceiling.

    A goal that cannot finish inside the budget reads as a FAILURE at Stop, not
    as "still running": the sixteen-session prose drift that said 600 s was the
    same class of error, and AC-2 pinned it.
    """
    _, out = _run([*_args_for(template, tmp_path), "--dry-run"])
    values = _summary(out)
    print(f"{template} sum_timeout={values['sum_timeout']}")

    assert 0 < int(values["sum_timeout"]) <= 100


@pytest.mark.parametrize("template", TEMPLATES)
def test_no_rendered_command_carries_a_shell_metacharacter(template: str, tmp_path: Path) -> None:
    """A3 — no ``$`` or backtick reaches a cmd, and every check has a timeout.

    Under the gate's transport a metacharacter expands one shell layer early and
    the reading is of something else entirely (CLAUDE.md §8). The rendered cmd is
    argv crossing the Windows -> WSL boundary, which is exactly where that bites.
    """
    _, out = _run([*_args_for(template, tmp_path), "--dry-run"])
    values = _summary(out)
    print(f"{template} has_dollar={values['has_dollar']}")

    # Asserted from the SUMMARY, before any JSON is parsed. The summary line is
    # printed even on a refusal; the goal body is not. Reading the body first
    # would turn every refusal-inducing mutation into a crash in the parser
    # rather than a RED on the assertion it was aimed at — a probe that crashes
    # credits nothing.
    assert values["has_dollar"] == "False"

    checks = [c for c in _body(out)["criteria"] if c["kind"] == "check"]
    timed = sum(1 for c in checks if c.get("timeout_s"))
    print(f"{template} checks_with_timeout={timed}/{len(checks)}")
    assert all(c.get("timeout_s") for c in checks)


@pytest.mark.parametrize("template", TEMPLATES)
def test_no_template_ever_pins_the_basis_to_a_commit(template: str, tmp_path: Path) -> None:
    """A4 — no ``git show <rev>:`` check is ever emitted (R5).

    Measured in s289: a HEAD-pinned check failed at four consecutive Stops after
    its PR merged, teaching that a gate which reliably fails after success is
    noise. The renderer's answer is never to emit one.
    """
    _, out = _run([*_args_for(template, tmp_path), "--dry-run"])
    values = _summary(out)
    print(f"{template} has_head_pin={values['has_head_pin']}")

    assert values["has_head_pin"] == "False"


@pytest.mark.parametrize("template", TEMPLATES)
def test_every_goal_carries_a_control_a_falsifier_and_an_evidence_dir(
    template: str, tmp_path: Path
) -> None:
    """A5 — ``C0``, a non-blank ``FALSIFIER:``, a ``BASIS:``, and a named evidence file.

    These four are the difference between a measurement and a confirmation of
    what the author already believed. The control shows the instrument can fail;
    the falsifier is written before the reading; the basis says what was read;
    the evidence file is the only thing the judge can actually see.
    """
    _, out = _run([*_args_for(template, tmp_path), "--dry-run"])
    values = _summary(out)
    print(f"{template} control={values['control']} falsifier={values['falsifier']}")

    # Summary-derived assertions first — see the note in the metacharacter case
    # for why the JSON parse cannot come before them.
    assert values["control"] == "C0"
    assert values["falsifier"] == "True"

    criteria = _body(out)["criteria"]
    judges = [c for c in criteria if c["kind"] == "judge"]
    checks = [c for c in criteria if c["kind"] == "check"]
    print(
        f"{template} judges_naming_evidence="
        f"{sum(1 for j in judges if values['evidence_dir'] in j['desc'])}/{len(judges)}"
    )
    assert all("BASIS:" in c["desc"] for c in checks)
    assert all(values["evidence_dir"] in j["desc"] for j in judges)


# --- A6: each violation refused, by clause name -------------------------------


@pytest.mark.parametrize(
    ("case", "extra", "clause"),
    [
        ("dollar_in_parameter", ["--pattern", "a$b"], "R6"),
        ("backtick_in_parameter", ["--pattern", "a`b`c"], "R6"),
        ("head_pin_in_parameter", ["--pattern", "git show HEAD:x"], "R5"),
    ],
)
def test_a_caller_supplied_violation_is_refused_by_clause_name(
    case: str, extra: list[str], clause: str, tmp_path: Path
) -> None:
    """A6 — the refusal NAMES the clause, so the message is actionable.

    ``refused=R6`` tells the caller which rule they tripped and therefore what to
    change. A bare non-zero exit would start a hunt — the same argument §8 makes
    about printing measured values rather than a verdict.
    """
    args = ["T-ABSENT", "--file", str(_log(tmp_path)), "--control", "transport", *extra]
    code, out = _run([*args, "--dry-run"])
    named = sorted(set(re.findall(r"refused=(R\d)", out)))
    print(f"{case} exit={code} clauses={named}")

    assert code != 0
    assert clause in named
