"""Check a battery's DEFINITION without mutating anything or running one test.

🔴 **Why this exists: a battery can be silently DEAD, and nothing caught it.**
Session 287 re-ran PLAN-0119's six batteries before ticking their ACs and found
**two** had been aborting on a *definition error* — not a red probe — since s286:

- AC-1's: ``ruff format`` reflowed the asserted literal, and ``stable_key`` is
  built from those bytes, so the declared claim key no longer addressed anything.
- AC-2's: the claim key **and** probe R17's mutation anchor both still named
  ``settings.llm_max_output_tokens``, which #1433 had replaced. **The test was
  updated with the code; the battery was not.** R17 had been a no-op whose green
  proved nothing for a whole session.

The driver already refuses both — ``_validate`` rejects an unaddressable
``expect_claim``, and ``RunStore.apply`` rejects an anchor that does not occur
exactly once. The gap was never the checks. It was **when they run**: only when
somebody runs that battery, and *batteries do not run in CI*.

⚠️ **The rot is authored on the OTHER side.** Both s287 deaths came from editing
the code a battery points at, never the battery file. So a check scoped to
``tests/batteries/*.json`` would not have fired for either — which is why the
pre-commit hook that calls this is ``always_run``.

**What this deliberately does NOT do.** It never mutates, never spawns pytest,
and never claims a probe would redden — that is the battery run's job and cannot
be answered offline. It answers only the cheap question: *can every probe still
address what it says it addresses?* A battery passing this lint can still fail
its run; a battery failing this lint cannot produce meaningful evidence at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from tools.probe_battery._battery import (
    Battery,
    BatteryDefinitionError,
    _index_claims,
    _overlaps,
    _validate,
)
from tools.probe_coverage import Claim


@dataclass(frozen=True)
class Finding:
    """One reason a battery cannot produce evidence, addressed to its author."""

    battery: Path
    probe: str
    detail: str

    def __str__(self) -> str:
        where = f"{self.battery.name}" + (f" [{self.probe}]" if self.probe else "")
        return f"{where}: {self.detail}"


@dataclass(frozen=True)
class BatteryLintReport:
    """What one battery measured — counts first, so a disagreement is one step to read."""

    battery: Path
    probes: int
    claim_sources: int
    findings: tuple[Finding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings


def _claim_findings(battery: Battery, path: Path) -> list[Finding]:
    """The two address classes that live in the CLAIM index, not in the subject.

    Split out of :func:`lint_battery_file` to keep it under the complexity ceiling
    once the exemption rule landed; the two read as one pass and are separated only
    for that reason.
    """
    findings: list[Finding] = []
    index: dict[str, tuple[Claim, Path]] | None = None

    # --- the s287 AC-1 / AC-2 killer: a claim key that addresses nothing ----------
    # `_index_claims` re-derives every stable_key from the CURRENT source, so a
    # reflowed literal or a renamed symbol shows up here rather than mid-run.
    try:
        index = _index_claims(battery)
        _validate(battery, index)
    except BatteryDefinitionError as exc:
        findings.append(Finding(path, "", f"claims: {exc}"))
    except (OSError, SyntaxError) as exc:
        findings.append(Finding(path, "", f"claim source unparseable: {exc}"))

    # --- the THIRD address that rots: an exemption naming a claim that is gone ----
    # `_validate` checks `expect_claim` and the driver's report counts these as
    # "stale ids", but only once a battery is actually RUN — the same too-late
    # timing this lint exists to fix. An exemption is a written promise that a
    # specific claim cannot be reached by any probe; when that claim disappears the
    # promise still reads as deliberate coverage while covering nothing.
    if index is not None:
        orphan = sorted(set(battery.exemptions) - set(index))
        if orphan:
            findings.append(
                Finding(
                    path,
                    "",
                    f"{len(orphan)} exemption(s) name a claim that no longer exists, so "
                    f"they excuse nothing while still reading as deliberate coverage: "
                    f"{orphan}",
                )
            )

    overlapping = _overlaps(battery)
    if overlapping:
        findings.append(
            Finding(
                path,
                "",
                f"{len(overlapping)} claim(s) are BOTH declared by a probe and exempted, "
                f"which is a contradiction — a claim cannot be unreachable and reddened "
                f"by the same battery: {list(overlapping)}",
            )
        )
    return findings


def _anchor_findings(battery: Battery, path: Path, project_root: Path) -> list[Finding]:
    """The s287 R17 killer: an anchor that no longer resolves in its subject."""
    findings: list[Finding] = []
    sources: dict[Path, str] = {}
    for probe in battery.probes:
        subject = probe.subject if probe.subject.is_absolute() else project_root / probe.subject
        if subject not in sources:
            try:
                sources[subject] = subject.read_text(encoding="utf-8")
            except OSError as exc:
                findings.append(Finding(path, probe.name, f"subject unreadable: {exc}"))
                continue
        text = sources[subject]

        hits = text.count(probe.old)
        if hits != 1:
            findings.append(
                Finding(
                    path,
                    probe.name,
                    f"anchor occurs {hits} times in {probe.subject}, expected exactly 1. "
                    f"A zero-occurrence anchor is a no-op whose GREEN proves nothing; a "
                    f"repeated one edits more than the probe declared. Text: {probe.old!r}",
                )
            )

        # A substitution of a string by ITSELF is the only offline-decidable no-op.
        #
        # 🔴 This check was written wrong first, and the wrong version is worth
        # recording because it is a tempting mistake: it flagged `new` being present
        # anywhere in the subject as "the mutation changes nothing". That is false.
        # A probe rewriting `return "plain"` to `return "reasoning"` in a file that
        # already has a legitimate `return "reasoning"` branch is a perfectly good
        # mutation — collapsing two shapes into one is exactly what it means to test.
        # The wrong version called SIX healthy batteries dead on its first run.
        # A guard that over-refuses is not a stricter guard; it is a broken one.
        #
        # The genuine no-op — a mutation whose write leaves the bytes unchanged — is
        # already caught by the driver, and caught properly: `RunStore.apply` compares
        # the sha256 of the re-read file against the snapshot and refuses when they
        # match. Nothing offline needs to, or can, do better than that.
        if probe.old == probe.new:
            findings.append(
                Finding(
                    path,
                    probe.name,
                    f"`old` and `new` are byte-identical, so applying the mutation "
                    f"changes nothing and the probe cannot redden. Text: {probe.old!r}",
                )
            )

        node_file = project_root / probe.node_id.split("::", 1)[0]
        if not node_file.is_file():
            findings.append(
                Finding(
                    path,
                    probe.name,
                    f"node_id names a module that does not exist: {node_file}. (Only the "
                    f"FILE is checked here — resolving the test itself needs collection.)",
                )
            )
    return findings


def lint_battery_file(path: Path, project_root: Path) -> BatteryLintReport:
    """Every definitional check the driver would make, made before the first mutation.

    Ordered cheapest-first and short-circuiting: a battery whose JSON will not parse
    has no probes to report anchor counts for, and printing a cascade of derived
    complaints about a file that never loaded buries the one that matters.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return BatteryLintReport(path, 0, 0, (Finding(path, "", f"unreadable: {exc}"),))

    try:
        battery = Battery.from_json(data, base=project_root)
    except ValueError as exc:
        # ValueError, not BatteryDefinitionError: the latter subclasses it, but an
        # invalid `expect` value reaches `Outcome(...)` and raises a BARE ValueError.
        # Found by dogfooding — a battery written in this same session with a
        # lower-case outcome name took the whole 22-battery run down with a
        # traceback instead of being reported as one broken battery. A lint that
        # crashes on the input it exists to inspect is not a lint.
        return BatteryLintReport(path, 0, 0, (Finding(path, "", f"schema: {exc}"),))

    n_probes = len(battery.probes)
    n_sources = len(battery.claim_sources)

    missing_sources = [s for s in battery.claim_sources if not s.is_file()]
    if missing_sources:
        named = ", ".join(str(s) for s in missing_sources)
        return BatteryLintReport(
            path,
            n_probes,
            n_sources,
            (Finding(path, "", f"claim_sources missing from disk: {named}"),),
        )

    findings = _claim_findings(battery, path)
    findings.extend(_anchor_findings(battery, path, project_root))

    return BatteryLintReport(path, n_probes, n_sources, tuple(findings))


def lint_batteries(paths: list[Path], project_root: Path) -> list[BatteryLintReport]:
    """Lint each battery in ``paths``, in a stable order so output diffs are readable."""
    return [lint_battery_file(p, project_root) for p in sorted(paths)]
