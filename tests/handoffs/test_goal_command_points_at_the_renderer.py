"""PLAN-0123 OQ-3 — the ``/goal`` command points at the renderer, and the pointer cannot rot.

🔴 **The gap this pins, measured s298.** PLAN-0123 §8 OQ-3 ruled that ``goal.md`` *"gains a
pointer"* to ``tools/goal_template.py``. The R-paragraphs landed (Step 1); the pointer never
did. At ``c39f4e3`` the command an agent reads at declaration time named the renderer only
once, in passing — *"the renderer's ``--replace`` does this for you once Step 2 lands"* —
with no invocation and no template names, six sessions after Step 2 landed (#1463, s292).
The other way in, the reading-shape advisory, was struck when AC-9 failed. AC-12 then read
``template_goals=1`` over five sessions, and Cray ruled that NOT MET a failure of **reach**
(s298, typed: ``AC-12 = B``). This file is the reach half of that ruling.

A pointer is two statements of one fact in two files — the same shape as AC-2's budget pin
(``test_goal_command_prose_pins_the_budget.py``) — so it rots the same way unless a test
reads both sides:

- **A1** — the prose carries the exact invocation, so a rewording that drops it is RED.
- **A2** — the template names the prose lists EQUAL the names the real renderer prints, so
  a template added, renamed or removed on either side is RED.
- **A3** — the documented invocation, run as a subprocess against the real renderer, exits
  ``0`` and prints at least one template (the scenario half: the real producer, the real
  command the reader is told to type).

A2 parses the renderer's printed output rather than importing ``TEMPLATES``, and does not
assert the exit code, so a mutation that breaks A3's exit code leaves A2 green and the two
witnesses stay separable (CLAUDE.md §8 — one mutation witnesses one assertion). Both
parsers pass a control on known text before their first real reading (Lesson #0056).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOAL_MD = REPO_ROOT / ".claude" / "commands" / "goal.md"

#: The invocation the prose tells the reader to type, verbatim.
INVOCATION = "python -m tools.goal_template list"
#: The same command as argv, run under the interpreter running this test.
INVOCATION_ARGV = [sys.executable, "-m", "tools.goal_template", "list"]

#: A row of the prose's template table: ``| `T-COUNT` | …``. The table sits inside a
#: numbered list item, so its rows are indented — the anchor allows leading whitespace.
DOC_ROW_RE = re.compile(r"^[ \t]*\|\s*`(T-[A-Z]+)`\s*\|", re.MULTILINE)
#: A template header in ``list`` output: two spaces, the name, end of line.
LIST_NAME_RE = re.compile(r"^  (T-[A-Z]+)$", re.MULTILINE)

#: One flush row and one indented row must both parse; prose that merely mentions a
#: template mid-line must not.
_DOC_CONTROL = (
    "| Template | when |\n|---|---|\n| `T-ONE` | a |\n   | `T-TWO` | b |\nsee | `T-X` | inline\n"
)
_LIST_CONTROL = "Templates:\n\n  T-ONE\n      when : a\n  T-TWO\n      uses : T-NOPE\n"


def doc_template_names(text: str) -> list[str]:
    """Template names from the prose's table rows, in order."""
    return DOC_ROW_RE.findall(text)


def listed_template_names(stdout: str) -> list[str]:
    """Template names from the renderer's ``list`` output, in order."""
    return LIST_NAME_RE.findall(stdout)


def _run_list() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        INVOCATION_ARGV, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60, check=False
    )


def test_the_parsers_pass_their_controls() -> None:
    """An uncontrolled instrument fails confidently, not loudly (Lesson #0056)."""
    doc = doc_template_names(_DOC_CONTROL)
    listed = listed_template_names(_LIST_CONTROL)
    print(f"doc_control={doc} list_control={listed}")
    assert doc == ["T-ONE", "T-TWO"], f"doc_control={doc}"
    assert listed == ["T-ONE", "T-TWO"], f"list_control={listed}"


def test_goal_md_names_the_renderer_invocation() -> None:
    text = GOAL_MD.read_text(encoding="utf-8")
    found = text.count(INVOCATION)
    print(f"invocation={INVOCATION!r} found={found}")
    # A1 — the reader is told exactly what to type.
    assert found >= 1, f"found={found} — goal.md no longer names the renderer invocation"


def test_the_documented_templates_are_the_renderers() -> None:
    doc = doc_template_names(GOAL_MD.read_text(encoding="utf-8"))
    listed = listed_template_names(_run_list().stdout)
    print(f"doc={doc} listed={listed}")
    # A2a — the renderer's side was actually read. Without it an empty prose table would
    # agree with a renderer whose output this parser cannot read.
    assert listed, f"listed={listed} — the renderer's list output parsed to nothing"
    # A2b — the prose and the renderer name the same set.
    assert sorted(doc) == sorted(listed), f"doc={doc} listed={listed}"


def test_the_documented_invocation_runs() -> None:
    """Scenario: the command the prose gives, against the real renderer."""
    proc = _run_list()
    listed = listed_template_names(proc.stdout)
    print(f"rc={proc.returncode} listed={listed} stderr_tail={proc.stderr[-200:]!r}")
    # A3a — it runs.
    assert proc.returncode == 0, f"rc={proc.returncode}"
    # A3b — and what it prints is templates.
    assert len(listed) >= 1, f"listed={listed}"
