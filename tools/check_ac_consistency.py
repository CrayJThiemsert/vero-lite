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

Exit codes: 0 = clean; 1 = at least one inconsistency.

``AC_CONSISTENCY_ROOT`` overrides the scanned repo root for tests (mirrors the
``STATUS_CITATION_ROOT`` / ``RETIRED_CLAIMS_ROOT`` family).
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: An AC checkbox line, the form every PLAN uses.
_AC_BOX = re.compile(r"^- \[([x ])\] \*\*AC-(\d+)\b", re.M)

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

    if dupes or mismatches:
        print(
            f"\ncheck_ac_consistency: {len(dupes)} duplicate label(s), "
            f"{len(mismatches)} ledger disagreement(s).",
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
