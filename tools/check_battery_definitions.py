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

**Scope, stated so a green is not over-read.** Passing here means every probe can
address its claim and its anchor resolves. It does **not** mean any probe would
redden — that needs the real run, and no offline check can answer it.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import bootstrap
    sys.path.insert(0, str(REPO_ROOT))

from tools.probe_battery._lint import BatteryLintReport, lint_batteries  # noqa: E402

BATTERY_GLOB = "tests/batteries/*.json"


def find_batteries(root: Path) -> list[Path]:
    """Every battery definition in the repo, sorted."""
    return sorted(root.glob(BATTERY_GLOB))


def render(reports: list[BatteryLintReport], root: Path) -> str:
    """A report that prints the values it measured, never a bare PASS/FAIL (§8)."""
    lines: list[str] = []
    probes = sum(r.probes for r in reports)
    broken = [r for r in reports if not r.ok]
    findings = sum(len(r.findings) for r in reports)

    lines.append("BATTERY DEFINITION LINT — can every probe still address what it declares?")
    lines.append(
        f"batteries: {len(reports)}   probes: {probes}   "
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
    batteries = find_batteries(root)
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
