#!/usr/bin/env python
"""Guard: every probe battery can still ADDRESS what it declares (s288).

🔴 **The defect this exists for.** A probe battery can be silently DEAD, and until
s288 nothing caught it. Session 287 re-ran PLAN-0119's six batteries before ticking
their ACs and found **two** had been aborting on a *definition error* — not a red
probe — since s286: one had its asserted literal reflowed by ``ruff format``
(``stable_key`` is built from those bytes), the other had both its claim key and a
probe's mutation anchor still naming a setting #1433 had replaced. **The tests were
updated with the code; the batteries were not.**

**Batteries do not run in CI** — they mutate the tree and spawn one pytest per probe,
which is not a thing a shared runner should do — and ``check_ac_consistency`` reports
clean because it does not run them either. So the *definitional* half is lifted out
here: it needs no mutation and no pytest, and it is exactly the half that rotted.

⚠️ **always_run, and that is the whole point.** Both s287 deaths were authored by
editing the code a battery points at, never the battery file. A hook scoped to
``tests/batteries/*.json`` would have stayed silent through both. This is the same
one-side-of-a-pair reasoning the alembic-registration and retired-claim guards carry.

**One claim, one key** (PLAN-0128). What a probe must address is
``tools.probe_coverage.Claim.stable_key``, which is ``@<id>`` when a trailing
``# claim: <id>`` is declared on the claim's anchor line and ``owner|source|#occurrence``
otherwise; a tagged claim is addressable **only** by its tag. That distinction is this
guard's whole subject: a *text* key is derived from the assertion's current bytes, which
is why ``ruff format`` could kill one silently in s287, while a *tag* is declared by the
author and survives any edit short of deleting the statement. So a battery that still
carries text keys is the one this guard will red first — and the repair is
``python -m tools.probe_battery tag <battery.json>``, never a hand-typed key.

**Scope, stated so a green is not over-read.** Passing here means every probe can
address its claim and its anchor resolves. It does **not** mean any probe would
redden — that needs the real run, and no offline check can answer it.

🔴 **Reach: every COMMITTED battery, wherever it sits.** The first cut read only
``tests/batteries/*.json``. Two tracked batteries lived beside their subject in
``benchmarks/intake_extraction/`` instead, so this guard never opened them, and one was
DEAD: probe S3's anchor had occurred 0 times since 2a112187 turned the one-line append it
named into a multi-line constructor. The guard printed OK throughout. (Measured s317;
both files now live in ``tests/batteries/``.) A location is a convention. What makes a
file a battery is its content. So this guard lints the home glob **plus** every
git-tracked ``*.json`` elsewhere whose text carries :data:`BATTERY_MARKER`, each file
once. It fails closed when git cannot enumerate: "no stray battery" must never mean the
same thing as "the guard did not look".
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import bootstrap
    sys.path.insert(0, str(REPO_ROOT))

from tools.probe_battery._lint import BatteryLintReport, lint_batteries  # noqa: E402

#: The HOME. Everything here is linted whatever it contains: a file here that will not
#: parse is a broken battery, not a non-battery.
BATTERY_GLOB = "tests/batteries/*.json"

#: What makes a JSON file a battery anywhere else: the key every battery carries. It is
#: matched on the raw TEXT, never on a parsed object, so a battery with broken JSON is
#: still FOUND and the lint then reports it unreadable. A parsed check would drop it
#: silently, and a silent drop is the failure this reach exists to close. The cost: a
#: non-battery JSON that spells this key gets linted and refused. That is loud, and it
#: names the file.
BATTERY_MARKER = '"claim_sources"'


class EnumerationError(RuntimeError):
    """``git ls-files`` could not enumerate the tree.

    This is fatal. It never becomes an empty list, for the reason ``check_status_citations``
    gives: a guard that cannot enumerate cannot certify anything. Scoping to tracked files
    is also what keeps ``.claude/worktrees/`` out. Every directory there is a full copy of
    this repo, batteries included, and a filesystem walk would lint all of them.
    """


def tracked_json(root: Path) -> list[Path]:
    """Repo-relative paths of every git-tracked ``*.json`` under ``root``.

    Raises :class:`EnumerationError` if git is unavailable or errors (fail-closed). A
    pathspec ``*`` matches across ``/``, so this reaches every depth.
    """
    try:
        # S603: fixed argv, no shell; `root` is a cwd, not an argument. S607: "git" via
        # PATH, the same idiom as tools/check_status_citations.py.
        proc = subprocess.run(  # noqa: S603
            ["git", "ls-files", "-z", "--", "*.json"],  # noqa: S607
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        )
    except FileNotFoundError as exc:  # git not on PATH
        raise EnumerationError("git executable not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"exit {exc.returncode}"
        raise EnumerationError(f"git ls-files failed in {root}: {detail}") from exc
    return [Path(p) for p in proc.stdout.split("\0") if p]


def carries_marker(text: str) -> bool:
    """True if ``text`` is shaped like a battery definition (see :data:`BATTERY_MARKER`)."""
    return BATTERY_MARKER in text


def find_batteries(root: Path, tracked: list[Path]) -> list[Path]:
    """Every battery definition in the repo, sorted, each exactly once.

    ``tracked`` (repo-relative) is a parameter so the selection is testable without git.
    """
    home = set(root.glob(BATTERY_GLOB))
    elsewhere: set[Path] = set()
    for rel in tracked:
        candidate = root / rel
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # A staged-but-deleted path is enumerated by git yet absent on disk.
            continue
        if carries_marker(text):
            elsewhere.add(candidate)
    # A union, never a concatenation. A home battery is tracked too, so both sources name
    # it, and a battery counted twice is linted twice and inflates every printed count.
    return sorted(home | elsewhere)


def render(reports: list[BatteryLintReport], root: Path) -> str:
    """A report that prints the values it measured, never a bare PASS/FAIL (§8)."""
    lines: list[str] = []
    probes = sum(r.probes for r in reports)
    broken = [r for r in reports if not r.ok]
    findings = sum(len(r.findings) for r in reports)
    home = root / Path(BATTERY_GLOB).parent
    outside = sum(1 for r in reports if r.battery.parent != home)

    lines.append("BATTERY DEFINITION LINT — can every probe still address what it declares?")
    lines.append(
        f"batteries: {len(reports)} (outside {Path(BATTERY_GLOB).parent.as_posix()}/: "
        f"{outside})   probes: {probes}   "
        f"broken batteries: {len(broken)}   findings: {findings}"
    )
    lines.append("")

    for report in reports:
        mark = "  ok " if report.ok else "🔴 DEAD"
        rel = (
            report.battery.relative_to(root)
            if report.battery.is_relative_to(root)
            else report.battery
        )
        lines.append(f"{mark} {rel}  probes={report.probes} claim_sources={report.claim_sources}")
        for finding in report.findings:
            lines.append(f"        - {finding.probe or '(battery)'}: {finding.detail}")

    lines.append("")
    if broken:
        lines.append(
            f"BATTERY-DEFINITIONS: BROKEN ({len(broken)} of {len(reports)} batteries cannot "
            f"produce evidence until repaired)"
        )
    else:
        lines.append(f"BATTERY-DEFINITIONS: OK ({len(reports)} batteries, {probes} probes)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]).resolve() if argv else REPO_ROOT
    try:
        tracked = tracked_json(root)
    except EnumerationError as exc:
        print(
            f"BATTERY-DEFINITIONS: CANNOT ENUMERATE tracked files ({exc}). Failing closed: "
            f"a battery outside {BATTERY_GLOB} would go unlinted, and a clean report would "
            "then say nothing.",
            file=sys.stderr,
        )
        return 2  # fail closed: an unenumerated tree certifies nothing
    batteries = find_batteries(root, tracked)
    if not batteries:
        # A zero-battery run must not read as a pass: the repo HAS batteries, so an
        # empty set means the glob stopped matching, not that everything is healthy.
        print(
            f"BATTERY-DEFINITIONS: NO BATTERIES FOUND under {root / BATTERY_GLOB} — "
            "the glob matched nothing, which is a broken guard, not a clean tree.",
            file=sys.stderr,
        )
        return 2
    reports = lint_batteries(batteries, root)
    print(render(reports, root))
    return 1 if any(not r.ok for r in reports) else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
