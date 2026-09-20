#!/usr/bin/env python3
"""Pre-commit guard: an AC's ledger must agree with itself.

Two checks, both closing failures measured at session 241.

**Check 1 — no PLAN may label two acceptance criteria the same.**
`docs/plans/0108-*.md` shipped **six** AC items wearing **five** labels: two of
them both read ``AC-5`` (a ``[check]`` staleness-guard AC and an ``[evidence]``
retro-classification AC). It survived drafting and review in the one PLAN whose
own subject is **AC-authoring hygiene**, which is the tell that no instrument was
looking. Nothing else can see it: a duplicate label is valid Markdown, passes
every lint, and reads correctly to a human scanning for content rather than
counting labels.

**Check 2 — a closure claimed in STATUS must be ticked in the PLAN.**
``docs/STATUS.md`` recorded ``AC-11 CLOSED s240`` in four places while
``docs/plans/done/0107-*.md`` still carried ``- [ ] **AC-11``. STATUS and the PLAN
disagreed for a full session and the PLAN was the stale one — so the file an
executor opens to pick up work said the work was still open. It was found by a
subagent reading the file for an unrelated reason, not by any check.

The direction matters: STATUS is the reconcile *output*, rewritten every session,
so it is the surface that gets updated. The PLAN is the surface that gets
forgotten. This guard asserts the forgotten one caught up.

## How Check 2 attributes a claim, and why it is built backwards

Measured against every ``CLOSED`` in STATUS at s241 (five real claims, all
correctly attributed, zero ambiguous):

* **Search backwards from ``CLOSED``, not forwards from ``AC-N``.** STATUS
  writes *"Phase B's AC-7 + AC-8 CLOSED s236"* — a forward scan from ``AC-7``
  stops at the first ``CLOSED`` and silently drops ``AC-8``.
* **The governing PLAN is the nearest ``PLAN-NNNN`` earlier on the same line.**
  One real line reads *"PLAN-0107 AC-11 CLOSED and PLAN-0111 drafted"* — a
  line-scoped "any PLAN mentioned" rule would wrongly accuse PLAN-0111.
* **The lookback stops at the previous ``CLOSED``**, so two claims on one line
  cannot bleed into each other.
* **An unattributable claim FAILS.** If an ``AC-N`` sits before a ``CLOSED``
  with no PLAN ahead of it on that line, the guard reports it rather than
  skipping — the alternative is a check that quietly narrows to nothing. Measured
  zero such cases today; if one appears, the fix is to name the PLAN in STATUS.

## Scope limits, stated so this is not read as stronger than it is

* **Check 1 covers ACTIVE plans only** (``docs/plans/*.md``, not ``done/``).
  Archived PLANs are frozen records; a label collision there is a past authoring
  defect, not one this guard can stop being created. One exists and is recorded
  here rather than dropped: ``docs/plans/done/0042-at2-managerial-build.md``
  carries a duplicate ``AC-13`` (16 items). It is deliberately out of scope.
* **Check 2 cannot read a phase-level claim.** *"Phase A CLOSED 6/6"* names no
  individual AC, so no checkbox can be derived from it. Three such claims exist;
  they are invisible to this guard by construction, not by oversight.
* Neither check knows whether an AC *should* be closed. They compare two
  statements of the same fact; a wrong fact stated consistently passes.

## AC lines that carry a status marker (s298), and Check 4

A PLAN may put a status marker between an AC's checkbox and its bold label::

    - [ ] 🔴 **MEASURED s293 — FAILED on clause 2: …** **AC-9 [check-replay] — …

Until s298 the matcher required ``**AC-N`` straight after the box, so such a line was
invisible to every check at once — found when archiving PLAN-0123 (13 ACs) dropped the
active count by 9. Counted across all 125 PLAN files, active and ``done/``, the prefix
took five forms, and the matcher reads exactly those:

* none — 976 of the 1002 checkbox lines carrying an AC token;
* a symbol run, then a bold marker — ``🔴 **MEASURED …**`` (PLAN-0123 AC-9..AC-12);
* two of those stacked — ``⚖️ **RULED s298 …** 🔴 **READ s297 …**`` (PLAN-0123 AC-12);
* an italic tick-note — ``*(ticked 2026-07-11 s118 close — …)*`` (``done/0010``, ``0012``);
* a strikethrough opener — ``~~**AC-5 …`` (``done/0049``).

* **The box state is the checkbox and nothing else.** A marker is prose for a human —
  MEASURED, STRUCK, UNREACHABLE, READ, RULED, ticked — an open vocabulary this guard does
  not interpret. In every measured marker line the author had kept the box consistent.
* **The label is the first bold span opening with ``AC-N``, reached only through
  markers.** An ``AC-N`` inside a marker's or a body's prose is a reference, never a
  label; so is a bold ``**AC-N**`` that follows words, as in a Step checkbox naming the
  AC it closes. A marker may not itself be an AC label, or the label after it would be
  read in its place.

**Check 4 — an active PLAN's AC line the matcher cannot read FAILS.** The marker list is
closed, so the next new shape would reopen this blind spot exactly as silently as the
last one did. Instead, any checkbox line holding a bold-opened ``**AC-N`` that the matcher
does not parse is reported. That also covers the shapes the matcher deliberately leaves
unread — a letter-suffixed ``**AC-1a`` (15 lines, all in ``done/``), a ``[~]`` box (one,
``done/0094``), an indented or non-``-`` checkbox (none) — so none of them can enter an
active PLAN unnoticed. Active PLANs only, like Check 1; in ``done/`` they stay invisible.

Exit codes: 0 = clean; 1 = at least one inconsistency.

``AC_CONSISTENCY_ROOT`` overrides the scanned repo root for tests (mirrors the
``STATUS_CITATION_ROOT`` / ``RETIRED_CLAIMS_ROOT`` family).
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: A code span, which may hold a ``*`` that is not markup (``mcp__vero-bridge__*``).
_CODE_SPAN = r"`[^`\n]*`"

#: One status marker ahead of an AC's label — the four measured shapes, and no others
#: (module docstring): a symbol run, a bold span that is not itself an AC label, an
#: italic span, a strikethrough opener. Atomic, so a line that fails fails in linear time.
_MARKER = (
    r"(?>"
    r"[^\w\s*`~]+"
    rf"|\*\*(?!AC-\d)(?:{_CODE_SPAN}|[^*`\n]|\*(?!\*))+\*\*"
    rf"|\*(?!\*)(?:{_CODE_SPAN}|[^*`\n])+\*"
    r"|~~"
    r")"
)

#: An AC checkbox line: the box, any status markers, then the AC's own bold label.
_AC_BOX = re.compile(rf"^- \[([x ])\] (?:{_MARKER}[ \t]*)*\*\*AC-(\d+)\b", re.M)

#: Any checkbox item holding a bold-opened AC label ANYWHERE — deliberately broader than
#: ``_AC_BOX`` in every dimension (indent, bullet, box character, prefix, label suffix).
#: A line this matches and ``_AC_BOX`` does not is an AC no check can read.
_AC_CANDIDATE = re.compile(r"^[ \t]*[-*+][ \t]+\[[^\]\n]?\][ \t].*\*\*AC-\d")

_CLOSED = re.compile(r"\bCLOSED\b")
_AC_REF = re.compile(r"\bAC-(\d+)\b")
_PLAN_REF = re.compile(r"\bPLAN-(\d{3,4})\b")

#: Characters to search back from a ``CLOSED`` for the ACs it closes. Sized from
#: the real corpus: the longest true claim is "Phase B's AC-7 + AC-8 CLOSED".
_LOOKBACK = 50


@dataclass(frozen=True)
class DuplicateLabel:
    plan: str
    label: int
    count: int


@dataclass(frozen=True)
class Mismatch:
    plan: str
    ac: int
    status_line: int
    reason: str


@dataclass(frozen=True)
class BatteryGap:
    plan: str
    ac: int | None
    reason: str


@dataclass(frozen=True)
class UnparsedLine:
    plan: str
    line: int
    text: str


#: A PLAN's machine-addressable pointer at its committed battery definitions.
_BATTERIES = re.compile(r"^\*\*Batteries:\*\*\s+`([^`]+)`", re.M)

#: The sentence that makes probe evidence binding for a PLAN's ticks. A PLAN that
#: writes it and then names no batteries is the case Check 3 must not sleep through.
#:
#: 🔴 **Matched case-INSENSITIVELY, and that is load-bearing.** Written here in the
#: lower case it takes mid-sentence, but a PLAN quoting the house rule naturally starts
#: a sentence with it — *"No AC box is ticked before its probe."* — and a case-sensitive
#: `in` then reads False on a PLAN that states the rule verbatim. Measured s315:
#: PLAN-0128 wrote it capitalised three times, carried **11 ticked ACs** and three
#: committed batteries, and Check 3 skipped the file entirely; the un-backticked
#: `**Batteries:**` header hid it once, and this comparison hid it again, so neither
#: gap could surface the other. Compare against ``text.lower()``.
_BINDING_SENTENCE = "no ac box is ticked before its probe"

#: The artifact clause of one AC line, up to whatever follows it.
_ARTIFACT_SEG = re.compile(r"\*Artifacts?:\*(.*?)(?:\*Pass read:\*|\*Probe|$)", re.S)

#: An AC that closes on a person's reading rather than on a probe. Check 3 asks
#: "is this ticked AC's artifact inside some battery's denominator of claims?" — a
#: question that only means something when the AC *claims* probe evidence. A docs or
#: ruling AC claims none, names documentation surfaces rather than tests, and is
#: satisfied by a human reading the PR; demanding it appear in a coverage denominator
#: is the same category error the tool-module escape below already recognises, one
#: step further out.
#:
#: 🔴 **`read` and `ruling` are in here because the variety was counted, not guessed.**
#: Measured s315 over every AC in `docs/plans/` and `docs/plans/done/`: PLAN-0128's
#: AC-10 and AC-12 say *"Closes on … review …"*, but PLAN-0125's AC-14 says
#: *"Closes on Cray's read alone; nothing mechanical substitutes"* and names no review
#: at all. A matcher written from the first two would have gone on sleeping through
#: the third the day it was ticked.
_CLOSES_REVIEW = re.compile(r"closes on\b[^.]{0,120}?\b(?:review|read|ruling)\b", re.I)

#: …and a probe-closed AC may still mention a review in passing, so an explicit probe
#: claim wins. An AC saying both is claiming probe evidence and is held to it.
_CLOSES_PROBE = re.compile(r"closes on\b[^.]{0,120}?\bwitnessed probe\b", re.I)

#: A ``path.py`` or ``path.py::test_name`` token inside backticks.
_ARTIFACT_NODE = re.compile(r"`([A-Za-z0-9_./-]+\.py(?:::\w+)?)`")


def _battery_sources(root: Path, pattern: str) -> tuple[set[str], int]:
    """Basenames of every ``claim_sources`` module across the matched batteries.

    Basenames, not paths: PLANs write some artifacts as full paths and some as bare
    filenames, and a raw string comparison reports four false positives on a correct
    tree (measured s278 against PLAN-0120).
    """
    files = sorted((root).glob(pattern))
    sources: set[str] = set()
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        sources.update(s.split("/")[-1] for s in data.get("claim_sources", []))
    return sources, len(files)


def _own_text(text: str, match: re.Match[str]) -> str:
    """One AC's own text: from its bold label to the end of its line, markers excluded.

    Replaces a lookup that re-found the line with ``startswith(f"- [x] **AC-{num} ")`` — a
    second, stricter parser of the same shape, so widening the matcher alone left Check 3
    blind. Measured s298, it also skipped the 14 ticked ``**AC-N**`` / ``**AC-N.**``
    labels in ``done/``, and for a duplicated label it fetched the first copy's line twice.
    """
    start = match.start(2) - len("**AC-")
    end = text.find("\n", start)
    return text[start:] if end == -1 else text[start:end]


def _uncovered_artifacts(plan_name: str, text: str, sources: set[str]) -> list[BatteryGap]:
    """Every ticked AC in ``text`` naming an artifact module outside ``sources``.

    Split out of :func:`find_battery_gaps` to keep that function under the complexity
    ceiling once the implementation-module rule below was added; the two read as one
    check and are only separated for that reason.

    **The rule.** A test module carries claims, so each one an AC names must be in the
    denominator. An IMPLEMENTATION module carries none — ``enumerate_claims`` reads
    assertions, and a tool has zero (measured s283: ``tools/hook_copies_audit.py`` ->
    0 claims) — so demanding it appear in a denominator OF CLAIMS is a category error,
    satisfiable only by adding a module that contributes nothing, which buys a green by
    making the coverage report blind. It is witnessed THROUGH a test module, so it is
    covered when this AC names one that is in the denominator.

    An AC naming NO test module falls back to the original rule, so a tool-only AC
    still cannot slip through unwitnessed — the s278 defect stays caught.
    """
    out: list[BatteryGap] = []
    for match in _AC_BOX.finditer(text):
        flag, num = match.groups()
        if flag != "x":
            continue
        line = _own_text(text, match)
        seg = _ARTIFACT_SEG.search(line)
        if seg is None:
            continue  # an AC with no test artifact (a command-run AC) is not a gap
        if _CLOSES_REVIEW.search(line) and not _CLOSES_PROBE.search(line):
            # A docs/ruling AC claims no probe evidence, so there is no denominator it
            # could be missing from. It is NOT unwitnessed: its witness is the review
            # it names, which the PR carries. The AC must SAY so — an AC that claims a
            # probe, or says nothing about how it closes, is still held to the rule.
            continue
        modules = [t.split("/")[-1].split("::")[0] for t in _ARTIFACT_NODE.findall(seg.group(1))]
        covered_by_a_test = any(m.startswith("test_") and m in sources for m in modules)
        for module in modules:
            if module in sources:
                continue
            if covered_by_a_test and not module.startswith("test_"):
                continue
            out.append(
                BatteryGap(
                    plan=plan_name,
                    ac=int(num),
                    reason=(
                        f"ticked, but its artifact `{module}` is in no battery's "
                        f"claim_sources — so PROBE-COVERAGE was computed over a "
                        f"denominator that excluded it. fix: add a battery covering "
                        f"that module, or untick until one exists."
                    ),
                )
            )
    return out


def find_battery_gaps(root: Path) -> list[BatteryGap]:
    """Check 3 — a ticked AC's named artifact must be inside some battery's denominator.

    A coverage report is scoped to its own ``claim_sources``; that set is **not** the
    obligation set the AC ledger rests on, and nothing joined them until this check.
    Measured s278: four batteries reported ``PROBE-COVERAGE: COMPLETE`` while AC-7's and
    AC-8's artifacts appeared in no denominator at all, and one AC's declared probe had
    never run. Both were ticked on that reading.

    Module-level, deliberately. Joining on the probe's ``node_id`` was measured at 37%
    against real batteries — probe names drift from the PLAN's ids — and a subject-level
    join fires on a legitimately revised mutation. The module join measured 0 false
    positives across PLAN-0120's eleven ACs.

    ⚠️ **That 0-false-positive figure was measured on a population containing none of
    the shape below.** An AC may name an IMPLEMENTATION module as its artifact —
    the tool it delivers — alongside the test module that witnesses it. Measured s283
    across 899 AC lines in ``docs/plans/`` and ``docs/plans/done/``: exactly **four**
    do, all four in PLAN-0122 (``run_eval.py`` twice, ``hook_copies_audit.py``,
    ``stop_classifier_ledger.py``), and PLAN-0122 AC-10 was the first ever ticked.
    So this check met the shape for the first time three sessions after it shipped,
    and accused a correctly-evidenced AC.

    The pairing is NOT by filename — AC-2 and AC-3 pair ``run_eval.py`` with
    ``test_stop_classifier_gold.py``, so a ``test_<stem>.py`` convention would not
    have fixed them. The rule is therefore per-AC, not per-name: the AC's own
    artifact clause is what associates a subject with its witness.

    Deliberately coarse, and consistent with the node_id refusal above: an AC pairing
    an unrelated implementation module with a covered test module passes. What is
    protected is "this ticked AC has witnessed coverage at all", not "every named
    file is individually probed" — the latter is what the 37% measurement rejected.
    """
    out: list[BatteryGap] = []
    for plan in active_plans(root):
        text = plan.read_text(encoding="utf-8")
        ticked = [n for flag, n in _AC_BOX.findall(text) if flag == "x"]
        match = _BATTERIES.search(text)
        if match is None:
            # Scoped to PLANs that have actually TICKED something. A Draft with the
            # binding sentence and nothing ticked yet has no claim resting on absent
            # evidence, and failing it would block work before there is anything to
            # cover — the check exists to catch an unjustified tick, not an unstarted
            # plan. Measured s278: unscoped, this fired on PLAN-0121 at 0 of 8 ticked.
            if _BINDING_SENTENCE in text.lower() and ticked:
                out.append(
                    BatteryGap(
                        plan=plan.name,
                        ac=None,
                        reason=(
                            f"{len(ticked)} AC(s) ticked and this PLAN binds its ticks to "
                            "probe evidence, but it names no batteries. fix: commit the "
                            "definitions under tests/batteries/ and add a `**Batteries:**` "
                            "header line pointing at them."
                        ),
                    )
                )
            continue

        sources, n_files = _battery_sources(root, match.group(1))
        if n_files == 0:
            # A glob matching nothing must ERROR, never skip: a check that quietly
            # passes when its evidence is absent is the thing it exists to prevent.
            out.append(
                BatteryGap(
                    plan=plan.name,
                    ac=None,
                    reason=(
                        f"`**Batteries:**` matches no files ({match.group(1)}). "
                        "fix: commit the battery definitions, or correct the pattern."
                    ),
                )
            )
            continue

        out.extend(_uncovered_artifacts(plan.name, text, sources))
    return out


def _ac_labels(text: str) -> list[int]:
    return [int(n) for _, n in _AC_BOX.findall(text)]


def _ac_state(text: str) -> dict[int, str]:
    """Label -> ``x`` or a space. A duplicate label keeps its LAST state here;
    Check 1 is what makes duplicates visible, so this collapse is safe."""
    return {int(n): flag for flag, n in _AC_BOX.findall(text)}


def active_plans(root: Path) -> list[Path]:
    """Active PLANs only — ``docs/plans/*.md``, never ``done/``."""
    return sorted(p for p in (root / "docs" / "plans").glob("[0-9]*.md") if p.is_file())


def find_duplicate_labels(root: Path) -> list[DuplicateLabel]:
    out: list[DuplicateLabel] = []
    for p in active_plans(root):
        labels = _ac_labels(p.read_text(encoding="utf-8"))
        for label in sorted(set(labels)):
            if labels.count(label) > 1:
                out.append(DuplicateLabel(plan=p.name, label=label, count=labels.count(label)))
    return out


def find_unparsed_ac_lines(root: Path) -> list[UnparsedLine]:
    """Check 4 — an active PLAN's AC line the matcher cannot read is an error, not a skip.

    See the module docstring: the marker grammar is a closed list, and an AC it cannot
    read escapes Checks 1-3 without a word. Failing here turns the next unmeasured shape
    into one visible report on the commit that introduces it.
    """
    out: list[UnparsedLine] = []
    for p in active_plans(root):
        for ln_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if _AC_CANDIDATE.match(line) and not _AC_BOX.match(line):
                out.append(UnparsedLine(plan=p.name, line=ln_no, text=line))
    return out


def _plan_text(root: Path, num: str) -> str | None:
    """A PLAN by number, active or archived — a STATUS claim may name either."""
    for sub in ("plans", "plans/done"):
        for p in (root / "docs" / sub).glob(f"{num}-*.md"):
            return p.read_text(encoding="utf-8")
    return None


def find_status_mismatches(root: Path) -> list[Mismatch]:
    status = root / "docs" / "STATUS.md"
    if not status.is_file():
        return []
    out: list[Mismatch] = []
    for ln_no, line in enumerate(status.read_text(encoding="utf-8").splitlines(), 1):
        for m in _CLOSED.finditer(line):
            start = m.start()
            prev = line.rfind("CLOSED", 0, start)
            lo = max(0, start - _LOOKBACK, (prev + len("CLOSED")) if prev != -1 else 0)
            acs = sorted({int(x) for x in _AC_REF.findall(line[lo:start])})
            if not acs:
                continue
            plans = _PLAN_REF.findall(line[:start])
            if not plans:
                out.append(
                    Mismatch(
                        plan="?",
                        ac=acs[0],
                        status_line=ln_no,
                        reason=(
                            f"claims AC-{acs} CLOSED but names no PLAN earlier on the "
                            f"line, so no checkbox can be checked. Name the PLAN in "
                            f"STATUS, or drop the AC reference."
                        ),
                    )
                )
                continue
            num = plans[-1]
            text = _plan_text(root, num)
            if text is None:
                out.append(
                    Mismatch(
                        plan=num,
                        ac=acs[0],
                        status_line=ln_no,
                        reason=f"names PLAN-{num}, which has no file in docs/plans/.",
                    )
                )
                continue
            state = _ac_state(text)
            for n in acs:
                box = state.get(n)
                if box is None:
                    out.append(
                        Mismatch(
                            plan=num,
                            ac=n,
                            status_line=ln_no,
                            reason=f"PLAN-{num} declares no AC-{n}.",
                        )
                    )
                elif box != "x":
                    out.append(
                        Mismatch(
                            plan=num,
                            ac=n,
                            status_line=ln_no,
                            reason=(
                                f"STATUS says AC-{n} is CLOSED; PLAN-{num} still has "
                                f"it as `- [ ]`. Tick the checkbox, or correct STATUS "
                                f"— the two must not disagree about the same fact."
                            ),
                        )
                    )
    return out


def main() -> int:
    root = Path(os.environ.get("AC_CONSISTENCY_ROOT") or ".").resolve()
    dupes = find_duplicate_labels(root)
    mismatches = find_status_mismatches(root)
    gaps = find_battery_gaps(root)
    unparsed = find_unparsed_ac_lines(root)

    for u in unparsed:
        print(
            f"UNPARSED AC LINE: docs/plans/{u.plan}:{u.line}\n"
            f"    {u.text[:120]}\n"
            f"    no check can read this AC, so a tick, a duplicate label or a STATUS claim "
            f"about it would pass unseen.\n"
            f"    fix: write `- [x] **AC-N`, with any status marker before the label as a "
            f"symbol, a **bold** or *italic* span, or `~~` — or, if the line is not an AC, "
            f"un-bold the reference.",
            file=sys.stderr,
        )

    for d in dupes:
        print(
            f"DUPLICATE AC LABEL: docs/plans/{d.plan}\n"
            f"    AC-{d.label} is used {d.count} times.\n"
            f"    fix: renumber the LATER one so the labels run 1..N in document "
            f"order, and check nothing cites the label you moved.",
            file=sys.stderr,
        )

    for m in mismatches:
        print(
            f"AC LEDGER DISAGREES: docs/STATUS.md:{m.status_line} vs PLAN-{m.plan}\n"
            f"    {m.reason}",
            file=sys.stderr,
        )

    for g in gaps:
        where = f"AC-{g.ac}" if g.ac is not None else "PLAN"
        print(
            f"BATTERY GAP: docs/plans/{g.plan} {where}\n    {g.reason}",
            file=sys.stderr,
        )

    if dupes or mismatches or gaps or unparsed:
        print(
            f"\ncheck_ac_consistency: {len(dupes)} duplicate label(s), "
            f"{len(mismatches)} ledger disagreement(s), {len(gaps)} battery gap(s), "
            f"{len(unparsed)} unparsed AC line(s).",
            file=sys.stderr,
        )
        return 1

    plans = active_plans(root)
    total = sum(len(_ac_labels(p.read_text(encoding="utf-8"))) for p in plans)
    print(
        f"check_ac_consistency: clean — {total} AC(s) across {len(plans)} active "
        f"PLAN(s); every closure STATUS claims is ticked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
