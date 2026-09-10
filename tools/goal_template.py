#!/usr/bin/env python
"""Render a goal that satisfies the PLAN-0123 contract, so declaring is cheaper than not.

🔴 **The problem this exists for.** PLAN-0123 §1.2 catalogues sixteen instrument
errors across two sessions. The Axis-B goal gate would have caught most of them,
and it was not used — because writing a *good* goal by hand costs more than
taking the reading and moving on. A contract alone makes that worse: it raises
the price of the honest path without lowering it. Only a renderer lowers it.

So: one command, at most four parameters the agent already holds at the moment
of the trigger, and the output is a goal that satisfies clauses R1-R8 by
construction.

**What the renderer refuses, by clause name.** A goal is emitted only if it
passes every clause; a violation exits non-zero printing ``refused=<clause>``
and what was wrong. The clauses are separate functions on purpose — each is one
failure class from §1.2, and a probe can disable exactly one.

- **R1** — not hollow: at least one ``check`` and at least one ``judge``.
- **R2** — every check writes an evidence FILE; a check's stdout never reaches
  the ``goal-evaluator``, so a number that lived only in stdout is a number
  nobody took. The judge's ``desc`` names the file it must read.
- **R3** — a ``C0`` control that could have failed, expressed as an INSTRUMENT
  MODE (``tally --expect-refusal``, ``absent --expect-present``) rather than a
  shell ``!`` inversion. An inversion outside the process flips the exit and
  leaves the printed verdict saying the opposite — error #13 by construction.
- **R4** — the falsifier is written down BEFORE the reading, as a ``FALSIFIER:``
  line in the judge's ``desc``. A blank one is refused.
- **R5** — each check names its basis (``BASIS: tree``); a ``git show <rev>:``
  check is never emitted, because a merge moves that basis out from under it.
- **R6** — transport-safe: no ``$``, backtick or ``$(`` anywhere in a rendered
  command OR in a caller-supplied parameter; every check has a ``timeout_s``;
  the checks sum to ≤ 100 s against the gate's 120 s budget.
- **R7** — provenance: ``declared_head`` is recorded, and each instrument stamps
  the HEAD it measured at into its evidence file for the judge to compare.
- **R8** — one goal file, no silent replacement: an unpassed ``active`` goal is
  APPENDED to with ``T<n>-`` prefixed ids; ``--replace`` archives it to
  ``goal-history/`` with ``disposition: replaced-unpassed`` first, so abandoning
  a hard goal is a record rather than a disappearance.

**Why every check is a generated bash script and not an inline command.**
Measured in s291: a goal whose ``cmd`` was ``python -m pytest …`` read
``C1=C2=C3=fail`` while every test was green — the Stop hook runs **Windows-side**
and that interpreter has no pytest. The shape that worked, and the shape rendered
here, is ``wsl.exe --exec bash <WSL-side script>``: argv with no shell on the
Windows side, exactly one shell layer inside the file, and therefore no way for a
``$`` to be eaten by an outer layer (CLAUDE.md §8).

⚠️ **This departs from PLAN-0123 R6's illustrative text**, which shows
``wsl bash -lc "cd ~/work/vero-lite && ./.venv/bin/python …"``. That form
contradicts ``.claude/commands/goal.md`` ("Commands run argv-without-shell from
the repo root: no ``&&``, no pipes — one command per criterion") and carries the
quoting hazard the §8 rule exists for. The measured shape wins; R6's example
text is a documentation defect to correct, recorded here rather than silently
diverged from.

Usage::

    python -m tools.goal_template list
    python -m tools.goal_template T-COUNT  --file LOG --field transport --expect ok,timeout
    python -m tools.goal_template T-ABSENT --file LOG --pattern PAT --control KNOWN
    python -m tools.goal_template T-ORACLE --battery tests/batteries/x.json \\
        --claim 'test_x|y == 1|#0' --report .claude/state/banked.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if __package__ in (None, ""):  # pragma: no cover - path-form invocation
    sys.path.insert(0, str(REPO_ROOT))
# The gate's own schema module, so a rendered goal is parsed by exactly the code
# that will read it at Stop. Re-declaring the shape here would be a second
# implementation of the schema, and the two would drift the first time either moved.
sys.path.insert(0, str(REPO_ROOT / ".claude" / "hooks"))

from _goal_state import (  # noqa: E402 — after the sys.path bootstrap above
    KIND_CHECK,
    KIND_JUDGE,
    STATUS_ACTIVE,
    STATUS_PASSED,
    Criterion,
    Goal,
    load_goal,
    save_goal,
)

from tools._evidence import (  # noqa: E402 — same reason
    EXIT_PASS,
    EXIT_REFUSED,
    head_sha,
    verdict_line,
)

STATE_DIR = REPO_ROOT / ".claude" / "state"
EVIDENCE_ROOT = STATE_DIR / "goal-evidence"
SCRIPT_ROOT = STATE_DIR / "goal-checks"
HISTORY_ROOT = STATE_DIR / "goal-history"

#: R6. The gate's deterministic budget is 120 s (``DEFAULT_CHECK_BUDGET_S``);
#: rendered goals stay under 100 so a hand-added criterion still fits.
BUDGET_S = 100

#: R6. Characters that mean something to a shell. None of them may appear in a
#: rendered command or in a caller-supplied parameter — not because the rendered
#: shape would mis-handle them, but because a parameter carrying one is a sign
#: the author is thinking in shell, and the next thing they write by hand will
#: not have this file's protection.
_SHELL_METACHARS = ("$", "`")

#: R5. A basis a merge can move out from under the goal.
_HEAD_PIN_RE = re.compile(r"git\s+show\s+\S+:")

#: R3. The control criterion's id. Fixed rather than free so a judge, a human and
#: a probe all point at the same thing.
CONTROL_ID = "C0"

#: T-COUNT's control is derived, never typed: a value the author's own ``--expect``
#: cannot contain, appended to make the falsifier provably capable of refusing.
_IMPOSSIBLE_VALUE = "__control_value_that_cannot_exist__"


@dataclass(frozen=True)
class Refusal:
    """One clause violation, named by the clause so the message is actionable."""

    clause: str
    detail: str

    def __str__(self) -> str:
        return f"refused={self.clause}  {self.detail}"


@dataclass
class Draft:
    """A rendered goal plus the scripts its checks invoke."""

    goal_text: str
    criteria: list[Criterion]
    scripts: dict[str, str] = field(default_factory=dict)
    params: list[str] = field(default_factory=list)
    gid: str = ""

    @property
    def evidence_dir(self) -> Path:
        return EVIDENCE_ROOT / self.gid

    @property
    def script_dir(self) -> Path:
        return SCRIPT_ROOT / self.gid

    def checks(self) -> list[Criterion]:
        return [c for c in self.criteria if c.kind == KIND_CHECK]

    def judges(self) -> list[Criterion]:
        return [c for c in self.criteria if c.kind == KIND_JUDGE]


def make_gid(goal_text: str, *, now: datetime | None = None) -> str:
    """``<compact timestamp>-<first 8 hex of sha256(goal text)>``.

    Time alone would collide across two goals declared in the same second; the
    digest alone would make two runs of the same goal indistinguishable in
    ``goal-history/``. Both halves earn their place.
    """
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%S")
    digest = hashlib.sha256(goal_text.encode("utf-8")).hexdigest()[:8]
    return f"{stamp}-{digest}"


def render_script(criterion_id: str, purpose: str, command: str) -> str:
    """One check, as a WSL-side bash script — see the module docstring for why.

    Deliberately contains no shell metacharacter — not even inside a comment.
    The file is the only shell layer, and keeping it metachar-free lets R6's scan
    treat the script and the command as one surface instead of reasoning about
    which layer would expand what.

    ⚠️ This is not hypothetical tidiness: the first version of this template
    quoted the s291 symptom with backticks in that comment line, and R6 refused
    every one of the three templates. The clause was right and the template was
    wrong — which is the direction a freshly-written instrument's disagreement
    usually does NOT go, and worth the note.
    """
    return (
        "#!/usr/bin/env bash\n"
        f"# {criterion_id}: {purpose}\n"
        "# Rendered by tools/goal_template.py (PLAN-0123 Step 2). Runs WSL-side under\n"
        "# the project venv because the Stop hook is Windows-side and its interpreter\n"
        "# has no pytest (measured s291: every check read fail while all tests were\n"
        "# green). The hook invokes this as argv -- no shell on the Windows side -- so\n"
        "# this file is the one and only shell layer.\n"
        f"cd {REPO_ROOT} || exit 9\n"
        "source .venv/bin/activate || exit 8\n"
        f"exec {command}\n"
    )


def _cmd_for(gid: str, criterion_id: str) -> str:
    return f"wsl.exe --exec bash {SCRIPT_ROOT / gid / (criterion_id + '.sh')}"


def _evidence_arg(gid: str, criterion_id: str) -> str:
    return f"--report-to {EVIDENCE_ROOT / gid / (criterion_id + '.txt')} --gid {gid}"


# --- the three templates ------------------------------------------------------


def template_count(args: argparse.Namespace) -> Draft:
    """T-COUNT — a breakdown that accounts for every record it read.

    Trigger: about to type ``grep -c``, ``wc -l``, or hand-add buckets.
    """
    expect = ",".join(v.strip() for v in args.expect.split(",") if v.strip())
    goal_text = (
        f"the breakdown of {args.file} by '{args.field}' accounts for every record "
        f"and its value set is exactly [{expect}]"
    )
    gid = make_gid(goal_text)
    draft = Draft(goal_text, [], gid=gid, params=[args.file, args.field, args.expect])

    draft.scripts[CONTROL_ID] = render_script(
        CONTROL_ID,
        "R3 control -- can this falsifier fail at all?",
        f"python -m tools.tally {args.file} --field {args.field} "
        f"--expect {expect},{_IMPOSSIBLE_VALUE} --expect-refusal "
        f"{_evidence_arg(gid, CONTROL_ID)}",
    )
    draft.scripts["C1"] = render_script(
        "C1",
        "the reading itself",
        f"python -m tools.tally {args.file} --field {args.field} --expect {expect} "
        f"{_evidence_arg(gid, 'C1')}",
    )
    draft.criteria = [
        Criterion(
            id=CONTROL_ID,
            kind=KIND_CHECK,
            desc=(
                "BASIS: tree. R3 control: the same instrument, same file, with a value "
                f"appended that cannot exist. It must REFUSE. If it accepts, the "
                f"--expect in {'C1'} could not have failed and C1's green means nothing."
            ),
            cmd=_cmd_for(gid, CONTROL_ID),
            timeout_s=30,
        ),
        Criterion(
            id="C1",
            kind=KIND_CHECK,
            desc=(
                f"BASIS: tree. The breakdown of {args.file} by '{args.field}' is "
                f"exhaustive and its value set is exactly [{expect}]."
            ),
            cmd=_cmd_for(gid, "C1"),
            timeout_s=30,
        ),
        Criterion(
            id="J1",
            kind=KIND_JUDGE,
            desc=(
                f"FALSIFIER: the value set is exactly [{expect}] -- written before the "
                "reading; any other value present, or any of these absent, refutes it.\n"
                "BASIS: tree.\n"
                f"Read the evidence files {EVIDENCE_ROOT / gid / (CONTROL_ID + '.txt')} "
                f"and {EVIDENCE_ROOT / gid / 'C1.txt'}. Each prints the values it "
                "measured; an absent file, or one carrying only a bare verdict, is "
                "INSUFFICIENT-EVIDENCE, never a pass. Check the head= stamp against the "
                "goal's declared_head and report a mismatch as a finding. Refuse the "
                "falsifier if it could not have failed on the file as it stands."
            ),
        ),
    ]
    return draft


def template_absent(args: argparse.Namespace) -> Draft:
    """T-ABSENT — an absence measured with a control that could have failed.

    Trigger: about to report ``0`` / "no hits" / "not running", or a value read
    through a window.
    """
    goal_text = (
        f"'{args.pattern}' is absent from {args.file}, measured with a control "
        f"('{args.control}') that finds a known one"
    )
    gid = make_gid(goal_text)
    draft = Draft(goal_text, [], gid=gid, params=[args.file, args.pattern, args.control])

    draft.scripts[CONTROL_ID] = render_script(
        CONTROL_ID,
        "R3 control -- can this instrument find anything at all?",
        f"python -m tools.absent --file {args.file} --pattern {args.control!r} "
        f"--control {args.control!r} --expect-present {_evidence_arg(gid, CONTROL_ID)}",
    )
    draft.scripts["C1"] = render_script(
        "C1",
        "the absence itself",
        f"python -m tools.absent --file {args.file} --pattern {args.pattern!r} "
        f"--control {args.control!r} {_evidence_arg(gid, 'C1')}",
    )
    draft.criteria = [
        Criterion(
            id=CONTROL_ID,
            kind=KIND_CHECK,
            desc=(
                "BASIS: tree. R3 control: the same instrument pointed at something known "
                f"to be present ('{args.control}'). It must FIND it. A zero from C1 is "
                "meaningless unless this passes."
            ),
            cmd=_cmd_for(gid, CONTROL_ID),
            timeout_s=30,
        ),
        Criterion(
            id="C1",
            kind=KIND_CHECK,
            desc=(
                f"BASIS: tree. '{args.pattern}' does not occur in {args.file}, over a "
                "scan that consumed every line (consumed == lines is printed)."
            ),
            cmd=_cmd_for(gid, "C1"),
            timeout_s=30,
        ),
        Criterion(
            id="J1",
            kind=KIND_JUDGE,
            desc=(
                f"FALSIFIER: any occurrence of '{args.pattern}' in {args.file} refutes "
                "this -- written before the reading.\n"
                "BASIS: tree.\n"
                f"Read {EVIDENCE_ROOT / gid / (CONTROL_ID + '.txt')} and "
                f"{EVIDENCE_ROOT / gid / 'C1.txt'}. REFUSE the reading if consumed != "
                "lines (the scan described a window, not the subject), if control_hits "
                "is 0, or if the control pattern sits INSIDE the same window the "
                "original ad-hoc reading used -- a control that could not have missed "
                "is not a control. An absent or bare-verdict file is "
                "INSUFFICIENT-EVIDENCE. Compare head= to the goal's declared_head."
            ),
        ),
    ]
    return draft


def template_oracle(args: argparse.Namespace) -> Draft:
    """T-ORACLE — a new or changed assertion an AC will cite.

    The battery itself is NOT a check: it takes the gate lock and mutates the
    tree, so it runs BEFORE the goal with ``--report-to``, and the goal reads the
    banked report.
    """
    goal_text = (
        f"the assertion '{args.claim}' has been witnessed RED by a probe in "
        f"{args.battery}, and the banked report says so"
    )
    gid = make_gid(goal_text)
    draft = Draft(goal_text, [], gid=gid, params=[args.battery, args.claim, args.report])

    draft.scripts[CONTROL_ID] = render_script(
        CONTROL_ID,
        "R3 control -- can the battery still address what it declares?",
        # The control is a GUARD, not one of the purpose-built instruments, so it
        # has no --report-to of its own and should not grow one: a pre-commit
        # guard's interface is not the place to encode a goal-file convention.
        # tools/stamp_evidence.py wraps any command into the R2/R7 format while
        # passing the child's exit status through unmodified.
        f"python -m tools.stamp_evidence --to {EVIDENCE_ROOT / gid / (CONTROL_ID + '.txt')} "
        f"--gid {gid} --label check_battery_definitions "
        "-- python tools/check_battery_definitions.py",
    )
    draft.scripts["C1"] = render_script(
        "C1",
        "the banked report carries no failure verdict",
        f"python -m tools.absent --file {args.report} --pattern 'PROBE-BATTERY: FAIL' "
        f"--control 'PROBE-BATTERY:' {_evidence_arg(gid, 'C1')}",
    )
    draft.scripts["C2"] = render_script(
        "C2",
        "the claim under test was actually credited",
        f"python -m tools.absent --file {args.report} --pattern {args.claim!r} "
        f"--control 'PROBE-BATTERY:' --expect-present {_evidence_arg(gid, 'C2')}",
    )
    draft.criteria = [
        Criterion(
            id=CONTROL_ID,
            kind=KIND_CHECK,
            desc=(
                "BASIS: tree. R3 control: every probe's anchor still occurs exactly once "
                "in its subject. A zero-occurrence anchor is a no-op whose GREEN proves "
                "nothing, so a report from a dead battery is not evidence."
            ),
            cmd=_cmd_for(gid, CONTROL_ID),
            timeout_s=30,
        ),
        Criterion(
            id="C1",
            kind=KIND_CHECK,
            desc=(
                f"BASIS: artifact:{args.report}. The banked report contains no "
                "'PROBE-BATTERY: FAIL', measured with 'PROBE-BATTERY:' as the control so "
                "a missing or truncated report cannot read as a pass."
            ),
            cmd=_cmd_for(gid, "C1"),
            timeout_s=30,
        ),
        Criterion(
            id="C2",
            kind=KIND_CHECK,
            desc=(
                f"BASIS: artifact:{args.report}. The report names the claim under test, "
                "so a battery that passed while crediting something else is caught."
            ),
            cmd=_cmd_for(gid, "C2"),
            timeout_s=30,
        ),
        Criterion(
            id="J1",
            kind=KIND_JUDGE,
            desc=(
                f"FALSIFIER: the claim '{args.claim}' is credited by a probe whose "
                "mutation could not have reddened it -- written before the reading.\n"
                f"BASIS: artifact:{args.report}.\n"
                f"Read {EVIDENCE_ROOT / gid / 'C1.txt'} and "
                f"{EVIDENCE_ROOT / gid / 'C2.txt'}, and the banked report itself. Grep "
                "the probe's entry_module for a SECOND emission site that could satisfy "
                "the same substring -- a probe crediting the wrong site passes every "
                "check above. Verify the report's head= and battery_sha256= stamps: a "
                "report banked against a different tree, or a battery edited since, is a "
                "finding and not a pass."
            ),
        ),
    ]
    return draft


TEMPLATES: dict[str, tuple[str, str, Callable[[argparse.Namespace], Draft]]] = {
    "T-COUNT": (
        "about to type grep -c / wc -l / hand-add buckets",
        "tools/tally.py -- --expect is the falsifier",
        template_count,
    ),
    "T-ABSENT": (
        "about to report 0 / 'no hits' / 'not running', or a value read through a window",
        "tools/absent.py -- the control must find a known one",
        template_absent,
    ),
    "T-ORACLE": (
        "a new or changed assertion an AC will cite",
        "tools/probe_battery/ -- run BEFORE the goal, with --report-to",
        template_oracle,
    ),
}


# --- the R1-R8 validator ------------------------------------------------------
#
# One function per clause, so a probe can disable exactly one and see exactly one
# refusal case go missing.


def _clause_r1(draft: Draft) -> list[Refusal]:
    out: list[Refusal] = []
    if not draft.checks():
        out.append(Refusal("R1", "a goal with no check is hollow — it can never fail"))
    if not draft.judges():
        out.append(Refusal("R1", "a goal with no judge has no residue anyone reads — add one"))
    return out


def _clause_r2(draft: Draft) -> list[Refusal]:
    out: list[Refusal] = []
    for check in draft.checks():
        body = draft.scripts.get(check.id, "")
        # Its OWN evidence file, by path — not merely "a --report-to appears
        # somewhere". Two checks pointed at one file is a report that overwrites
        # itself, and the judge would read whichever ran last while believing it
        # had both.
        if str(draft.evidence_dir / f"{check.id}.txt") not in body:
            out.append(
                Refusal(
                    "R2",
                    f"check {check.id} does not write {check.id}.txt into the evidence "
                    "dir; a check's stdout never reaches the judge, so the numbers "
                    "would be unreadable",
                )
            )
    for judge in draft.judges():
        if str(draft.evidence_dir) not in judge.desc:
            out.append(Refusal("R2", f"judge {judge.id} does not name the evidence file to read"))
    return out


def _clause_r3(draft: Draft) -> list[Refusal]:
    if not any(c.id == CONTROL_ID for c in draft.checks()):
        return [
            Refusal(
                "R3",
                f"no {CONTROL_ID} control — a reading from an instrument never shown "
                "capable of failing is not evidence",
            )
        ]
    return []


def _clause_r4(draft: Draft) -> list[Refusal]:
    out: list[Refusal] = []
    for judge in draft.judges():
        match = re.search(r"FALSIFIER:(.*)", judge.desc)
        if match is None:
            out.append(Refusal("R4", f"judge {judge.id} carries no FALSIFIER: line"))
        elif not match.group(1).strip():
            out.append(
                Refusal(
                    "R4",
                    f"judge {judge.id} has a blank FALSIFIER — a falsifier nobody wrote "
                    "down before the reading is a confirmation, not a measurement",
                )
            )
    return out


def _clause_r5(draft: Draft) -> list[Refusal]:
    out: list[Refusal] = []
    surfaces = [c.cmd for c in draft.checks()] + list(draft.scripts.values()) + draft.params
    for surface in surfaces:
        if _HEAD_PIN_RE.search(surface):
            out.append(
                Refusal(
                    "R5",
                    "a `git show <rev>:` basis is pinned to a commit a merge can move "
                    "out from under the goal; use a tree basis",
                )
            )
            break
    for check in draft.checks():
        if "BASIS:" not in check.desc:
            out.append(Refusal("R5", f"check {check.id} does not name its BASIS"))
    return out


def _clause_r6(draft: Draft) -> list[Refusal]:
    """Transport safety: metacharacters in the ``cmd`` and in caller parameters.

    ⚠️ **Reach correction, recorded because it was wrong the first time.** This
    scan originally also covered the rendered SCRIPT bodies, and it refused all
    three templates over a backtick inside a generated comment. Two different
    findings came out of that, and only one of them was the instrument's fault:
    the comment really did carry a metacharacter and was fixed, but scanning the
    script at all contradicts the design — the script file is *the one shell
    layer*, the place where a ``$`` is finally safe, which is the entire reason
    the check is a file instead of an inline command (CLAUDE.md §8: *write the
    script to a file*). AC-7 A3/A6 bind the ``cmd`` and the caller's parameters,
    which is what crosses the Windows -> WSL boundary and what an author might
    paste into a hand-written goal later. Those two surfaces are the reach.

    A parameter carrying a metacharacter is still refused even though it is
    interpolated into a script, because the author who typed it is thinking in
    shell and the next thing they write will not have this file's protection.
    """
    out: list[Refusal] = []
    surfaces = [c.cmd for c in draft.checks()] + draft.params
    for surface in surfaces:
        for meta in _SHELL_METACHARS:
            if meta in surface:
                out.append(
                    Refusal(
                        "R6",
                        f"shell metacharacter {meta!r} reaches a rendered command or "
                        "parameter; under the gate's transport it would expand one "
                        "layer early and the reading would be of something else",
                    )
                )
                break
        if out:
            break
    total = 0
    for check in draft.checks():
        if not check.timeout_s or check.timeout_s <= 0:
            out.append(Refusal("R6", f"check {check.id} has no timeout_s"))
        else:
            total += check.timeout_s
    if total > BUDGET_S:
        out.append(
            Refusal(
                "R6",
                f"checks sum to {total} s against a {BUDGET_S} s ceiling (the gate's own "
                "budget is 120 s); a goal that cannot finish reads as a failure",
            )
        )
    return out


CLAUSES: tuple[Callable[[Draft], list[Refusal]], ...] = (
    _clause_r1,
    _clause_r2,
    _clause_r3,
    _clause_r4,
    _clause_r5,
    _clause_r6,
)


def validate(draft: Draft) -> list[Refusal]:
    """Every clause violation, so one run names all of them rather than the first."""
    found: list[Refusal] = []
    for clause in CLAUSES:
        found.extend(clause(draft))
    return found


def summarize(draft: Draft, declared_head: str) -> str:
    """The one-line reading AC-7 asserts against. Values, never a bare verdict."""
    checks = draft.checks()
    surfaces = [c.cmd for c in checks] + list(draft.scripts.values()) + draft.params
    has_dollar = any(m in s for s in surfaces for m in _SHELL_METACHARS)
    has_head_pin = any(_HEAD_PIN_RE.search(s) for s in surfaces)
    falsifier = all(
        (m := re.search(r"FALSIFIER:(.*)", j.desc)) is not None and bool(m.group(1).strip())
        for j in draft.judges()
    )
    return (
        f"checks={len(checks)} judges={len(draft.judges())} "
        f"sum_timeout={sum(c.timeout_s or 0 for c in checks)} "
        f"has_dollar={has_dollar} has_head_pin={has_head_pin} "
        f"control={CONTROL_ID if any(c.id == CONTROL_ID for c in checks) else 'none'} "
        f"evidence_dir={draft.evidence_dir} falsifier={falsifier} "
        f"declared_head={declared_head or 'unknown'}"
    )


# --- R8: append, or archive-then-replace, never a silent overwrite -------------


def build_goal(draft: Draft, *, declared_head: str, session: int, source: str) -> Goal:
    """The Goal a fresh declaration writes — built here so ``--dry-run`` prints
    exactly what a real run would write, rather than a summary of it. A dry run
    that shows something other than the artifact is a rehearsal of a different
    performance.
    """
    return Goal(
        goal=draft.goal_text,
        status=STATUS_ACTIVE,
        source=source,
        session=session,
        created=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z"),
        enforce=False,
        declared_head=declared_head,
        criteria=draft.criteria,
    )


def _archive(existing: Goal, disposition: str, history_root: Path) -> Path:
    """Write the outgoing goal to ``goal-history/`` with WHY it left.

    The disposition is the point. Replacing a hard goal with an easy one is the
    second hollow-goal loophole, and it is closed not by forbidding the
    replacement but by making the abandonment a record somebody can read.
    """
    history_root.mkdir(parents=True, exist_ok=True)
    gid = make_gid(existing.goal)
    payload = existing.to_json()
    payload["disposition"] = disposition
    destination = history_root / f"{gid}.json"
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def _next_prefix(existing: Goal) -> str:
    rounds = {int(m.group(1)) for c in existing.criteria if (m := re.match(r"T(\d+)-", c.id))}
    return f"T{max(rounds, default=0) + 1}-"


def apply_lifecycle(
    draft: Draft,
    *,
    goal_file: Path,
    history_root: Path,
    replace: bool,
    declared_head: str,
    session: int,
    source: str,
) -> tuple[Path | None, str, list[str], list[str]]:
    """Write the goal per R8. Returns ``(archived, disposition, pre_ids, post_ids)``."""
    existing = load_goal(goal_file)
    pre_ids = [c.id for c in existing.criteria] if existing else []

    if existing is not None and existing.status != STATUS_PASSED and not replace:
        # APPEND. Overwriting erases the trail that says what the earlier goal
        # found, so a second declaration adds to the first under a fresh prefix.
        prefix = _next_prefix(existing)
        for criterion in draft.criteria:
            criterion.id = prefix + criterion.id
        for old_id in list(draft.scripts):
            draft.scripts[prefix + old_id] = draft.scripts.pop(old_id)
        existing.criteria.extend(draft.criteria)
        existing.goal = f"{existing.goal}  ||  {draft.goal_text}"
        save_goal(existing, goal_file)
        return None, "appended", pre_ids, [c.id for c in existing.criteria]

    archived: Path | None = None
    disposition = "none"
    if existing is not None:
        disposition = "passed" if existing.status == STATUS_PASSED else "replaced-unpassed"
        archived = _archive(existing, disposition, history_root)

    goal = build_goal(draft, declared_head=declared_head, session=session, source=source)
    save_goal(goal, goal_file)
    return archived, disposition, pre_ids, [c.id for c in goal.criteria]


def write_scripts(draft: Draft, script_root: Path) -> None:
    target = script_root / draft.gid
    target.mkdir(parents=True, exist_ok=True)
    for criterion_id, body in draft.scripts.items():
        (target / f"{criterion_id}.sh").write_text(body, encoding="utf-8")


def _cmd_list() -> int:
    print("Templates — one command, the parameters you already hold at the trigger:\n")
    for name, (trigger, instrument, _) in TEMPLATES.items():
        print(f"  {name}")
        print(f"      when : {trigger}")
        print(f"      uses : {instrument}")
    print("\nEvery rendered goal satisfies R1-R8 or is refused by clause name.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="goal_template", description=__doc__)
    sub = parser.add_subparsers(dest="template", required=True)
    sub.add_parser("list", help="show the templates and their triggers")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="print, write nothing")
    common.add_argument("--replace", action="store_true", help="archive the active goal first")
    common.add_argument("--session", type=int, default=0)
    common.add_argument("--source", default="")
    common.add_argument("--goal-file", type=Path, default=None, help="override for tests")
    common.add_argument(
        "--history-root",
        type=Path,
        default=None,
        help="override the goal-history/ archive dir (tests; R8's record must be isolatable)",
    )

    count = sub.add_parser("T-COUNT", parents=[common])
    count.add_argument("--file", required=True)
    count.add_argument("--field", required=True)
    count.add_argument("--expect", required=True, help="the falsifier — the value set you believe")

    absent = sub.add_parser("T-ABSENT", parents=[common])
    absent.add_argument("--file", required=True)
    absent.add_argument("--pattern", required=True, help="what you claim is ABSENT")
    absent.add_argument("--control", required=True, help="something you know IS there")

    oracle = sub.add_parser("T-ORACLE", parents=[common])
    oracle.add_argument("--battery", required=True)
    oracle.add_argument("--claim", required=True, help="the stable_key the probe must credit")
    oracle.add_argument("--report", required=True, help="the banked --report-to file")

    args = parser.parse_args(argv)
    if args.template == "list":
        return _cmd_list()

    draft = TEMPLATES[args.template][2](args)
    declared_head = head_sha(REPO_ROOT)

    refusals = validate(draft)
    print(summarize(draft, declared_head))
    if refusals:
        for refusal in refusals:
            print(str(refusal), file=sys.stderr)
        print(
            f"\nREFUSED - {len(refusals)} clause violation(s). Nothing was written.",
            file=sys.stderr,
        )
        # §4.6: the printed verdict and the exit status come from one value, here
        # as in every other instrument a goal can call. A renderer that refused
        # while printing PASS would be error #13 at the one place the whole
        # contract is supposed to be enforced.
        print(verdict_line(EXIT_REFUSED))
        return EXIT_REFUSED

    if args.dry_run:
        goal = build_goal(
            draft, declared_head=declared_head, session=args.session, source=args.source
        )
        print(json.dumps(goal.to_json(), indent=2, sort_keys=True))
        for criterion_id, body in sorted(draft.scripts.items()):
            print(f"\n--- {criterion_id}.sh ---\n{body}")
        print(f"gid={draft.gid}")
        print("DRY RUN - nothing written.")
        print(verdict_line(EXIT_PASS))
        return EXIT_PASS

    goal_file = args.goal_file if args.goal_file is not None else STATE_DIR / "goal.json"
    write_scripts(draft, SCRIPT_ROOT)
    draft.evidence_dir.mkdir(parents=True, exist_ok=True)
    archived, disposition, pre_ids, post_ids = apply_lifecycle(
        draft,
        goal_file=goal_file,
        history_root=args.history_root if args.history_root is not None else HISTORY_ROOT,
        replace=args.replace,
        declared_head=declared_head,
        session=args.session,
        source=args.source,
    )
    print(
        f"pre_ids={pre_ids} post_ids={post_ids} "
        f"archived={archived or 'none'} disposition={disposition}"
    )
    print(verdict_line(EXIT_PASS))
    return EXIT_PASS


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
