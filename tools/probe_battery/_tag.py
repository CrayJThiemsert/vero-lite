"""``probe_battery tag`` — give every claim a battery addresses a tag of its own.

A text key (``owner|source|#occurrence``) is *derived from the assertion's current
text*, so editing the assertion silently re-points or strands the address. A tag is
declared by the author on the claim's anchor line and survives every edit that does not
delete the statement. This subcommand performs that migration for a whole battery at
once, and it is the only supported way to do it: the hand transplant the PLAN's §9
measured is refused by the coverage denominator, not by the classifier, and only
*conditionally* (see that section) — so nothing here relies on a human getting it right.

**Plan first, write second, and refuse in between.** The whole plan is computed before a
byte is written (:func:`plan_tags`); a single unaddressable key, a colliding id, or a
line that would exceed the project's ``ruff`` ``line-length`` aborts the run with **every
file untouched**. This matters more than it looks: the alternative — writing as you go —
leaves a half-tagged module whose battery addresses neither the old text keys nor the
new tags, which is a worse state than either end.

**Append, never insert.** A tag is appended to the claim's existing anchor line, so the
line *count* never changes and no line number shifts. Files may therefore be written in
any order, each rewritten once, with every line other than its anchor lines
byte-identical.

**The equivalence line is the leak detector, not decoration.** After writing, every
touched module is re-enumerated and each newly-tagged key is resolved again; the printed
``resolved_same`` counts keys whose ``(owner, source, occurrence)`` is unchanged. A tag
that leaked into the claim's ``source`` — because it landed on an interior line of a
multi-line statement — changes that tuple, ``resolved_differ`` counts it, and the tool
**restores every file from the in-memory originals and exits 2**. A leaking tag cannot be
committed by this tool. Under trailing placement the leak is already impossible by
construction (:func:`tools.probe_coverage.anchor_row_for` is shared with the reader); the
check is what keeps that true if either side ever moves.

Why the tool does not let ``ruff format`` reflow an over-long tagged line for it: a
Black-compatible formatter puts the trailing comment after the closing bracket of the
exploded statement — still a valid anchor — but that is asserted, not measured here, and
a tool depending on it would be writing a tree it cannot lint. It refuses and prints the
width instead, and the author shortens the id or explodes the statement by hand.
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.probe_battery._battery import Battery, BatteryDefinitionError
from tools.probe_battery._lint import lint_battery_file
from tools.probe_coverage import (
    Claim,
    ClaimTagError,
    claims_with_anchor_rows,
    enumerate_claims,
    is_valid_tag_id,
)

#: What a tag costs on the line it joins: two separating spaces plus the marker.
TAG_PREFIX = "  # claim: "

#: ``ruff``'s own default, used only when the project states no ``line-length``.
_RUFF_DEFAULT_LINE_LENGTH = 88


class TagPlanError(ValueError):
    """The plan phase refused. Carries every reason at once, never just the first.

    Reporting one refusal per run would make migrating a battery an iterative guessing
    game; the author wants the whole list so one edit pass fixes it.
    """

    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = tuple(reasons)
        super().__init__("; ".join(reasons))


@dataclass(frozen=True)
class PlannedTag:
    """One addressed key and what the tool intends to do about it."""

    key: str
    ident: str
    path: Path
    #: The claim's ANCHOR row — the line the tag is appended to, and the only correct
    #: target. Carried beside ``lineno`` so a diagnostic can show both: for a
    #: single-line claim they are equal, and for a multi-line one the gap between them
    #: is exactly the interior region a tag must never land in.
    row: int
    lineno: int
    adopted: bool
    width: int
    #: ``(owner, source, occurrence)`` as resolved BEFORE any write — the equivalence
    #: baseline the post-write re-resolution is compared against.
    identity: tuple[str, str, int]


@dataclass(frozen=True)
class TagPlan:
    battery_name: str
    planned: tuple[PlannedTag, ...]
    #: Lines the append would push past the limit. Fatal when applying; in ``--dry-run``
    #: they are the SD-e measurement and are reported rather than refused.
    overlong: tuple[str, ...]
    limit: int

    @property
    def addressed(self) -> int:
        return len(self.planned)

    @property
    def adopted(self) -> int:
        return sum(1 for p in self.planned if p.adopted)

    @property
    def to_append(self) -> int:
        return sum(1 for p in self.planned if not p.adopted)


def line_length_limit(project_root: Path) -> int:
    """The project's ``ruff`` ``line-length``, or ruff's default when unstated.

    Read rather than hard-coded: a tool that assumed 88 would refuse legal lines in this
    repository (which sets 100) and, worse, would *accept* over-long ones in a project
    that sets less.
    """
    try:
        data = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return _RUFF_DEFAULT_LINE_LENGTH
    tool = data.get("tool")
    ruff = tool.get("ruff") if isinstance(tool, dict) else None
    value = ruff.get("line-length") if isinstance(ruff, dict) else None
    return value if isinstance(value, int) else _RUFF_DEFAULT_LINE_LENGTH


def _addressed_keys(battery: Battery) -> list[tuple[str, str]]:
    """``(key, proposed id suffix)`` for every key the battery addresses, in order.

    Probe keys first, in battery order; the **first** probe declaring a key names it, so
    two probes on one claim do not fight over the id. Exemptions follow, numbered over
    the whole exemption mapping so a later adoption cannot renumber the others.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for probe in battery.probes:
        if probe.expect_claim in seen:
            continue
        seen.add(probe.expect_claim)
        out.append((probe.expect_claim, probe.name))
    for index, key in enumerate(battery.exemptions, start=1):
        if key in seen:
            continue
        seen.add(key)
        out.append((key, f"exempt-{index}"))
    return out


def _index(battery: Battery) -> tuple[dict[str, tuple[Claim, Path, int]], dict[Path, set[str]]]:
    """``{stable_key: (claim, path, anchor row)}`` plus each module's tag ids in use."""
    index: dict[str, tuple[Claim, Path, int]] = {}
    tags_in_module: dict[Path, set[str]] = {}
    for source in battery.claim_sources:
        used: set[str] = set()
        for claim, row in claims_with_anchor_rows(source):
            index[claim.stable_key] = (claim, source, row)
            if claim.tag is not None:
                used.add(claim.tag)
        tags_in_module[source] = used
    return index, tags_in_module


def plan_tags(battery: Battery, battery_path: Path, project_root: Path) -> TagPlan:
    """Compute the whole migration, or raise :class:`TagPlanError` having written nothing.

    ``overlong`` is returned rather than raised: the caller decides, because ``--dry-run``
    exists precisely to *measure* how often the default id scheme overruns (PLAN-0128
    SD-e's binding measurement) and a refusal there would destroy the reading.
    """
    stem = battery_path.stem
    limit = line_length_limit(project_root)
    index, tags_in_module = _index(battery)

    reasons: list[str] = []
    planned: list[PlannedTag] = []
    overlong: list[str] = []
    # Ids this plan intends to add, per module, so two planned ids cannot collide with
    # each other — the in-file set alone would miss that.
    claimed: dict[Path, set[str]] = {path: set(used) for path, used in tags_in_module.items()}

    for key, suffix in _addressed_keys(battery):
        entry = index.get(key)
        if entry is None:
            reasons.append(f"unaddressable key {key!r} — it resolves to no claim in claim_sources")
            continue
        claim, path, row = entry
        identity = (claim.owner, claim.source, claim.occurrence)

        if claim.tag is not None:
            planned.append(PlannedTag(key, claim.tag, path, row, claim.lineno, True, 0, identity))
            continue

        ident = f"{stem}/{suffix}"
        if not is_valid_tag_id(ident):
            reasons.append(
                f"key {key!r}: the default id {ident!r} is not a legal tag id — "
                f"rename the probe, or tag that claim by hand and re-run"
            )
            continue
        if ident in claimed.get(path, set()):
            reasons.append(
                f"key {key!r}: id {ident!r} is already used in {path} — "
                f"ids address exactly one claim per module"
            )
            continue
        claimed.setdefault(path, set()).add(ident)

        source_lines = path.read_text(encoding="utf-8").split("\n")
        width = len(source_lines[row - 1]) + len(TAG_PREFIX) + len(ident)
        if width > limit:
            overlong.append(f"overlong: {path}:{row} width={width} limit={limit}")
        planned.append(PlannedTag(key, ident, path, row, claim.lineno, False, width, identity))

    if reasons:
        raise TagPlanError(reasons)
    return TagPlan(battery_path.name, tuple(planned), tuple(overlong), limit)


def _apply_appends(plan: TagPlan) -> dict[Path, str]:
    """Write every planned append. Returns the pre-write text of each touched file.

    An append changes no line count, so the rows computed in the plan phase stay valid
    while this runs and the write order is irrelevant.
    """
    by_path: dict[Path, list[PlannedTag]] = {}
    for item in plan.planned:
        if not item.adopted:
            by_path.setdefault(item.path, []).append(item)

    originals: dict[Path, str] = {}
    for path, items in by_path.items():
        text = path.read_text(encoding="utf-8")
        originals[path] = text
        lines = text.split("\n")
        for item in items:
            lines[item.row - 1] = f"{lines[item.row - 1]}{TAG_PREFIX}{item.ident}"
        path.write_text("\n".join(lines), encoding="utf-8")
    return originals


def _rewrite_battery(battery_path: Path, plan: TagPlan) -> str:
    """Point every addressed key at its tag. Returns the battery's pre-write text."""
    original = battery_path.read_text(encoding="utf-8")
    data = json.loads(original)
    new_key = {item.key: f"@{item.ident}" for item in plan.planned}

    for probe in data.get("probes", []):
        current = probe.get("expect_claim")
        if current in new_key:
            probe["expect_claim"] = new_key[current]
    exemptions = data.get("exemptions")
    if isinstance(exemptions, dict):
        data["exemptions"] = {new_key.get(k, k): v for k, v in exemptions.items()}

    battery_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return original


def _restore(originals: Mapping[Path, str], battery_path: Path, battery_text: str | None) -> None:
    for path, text in originals.items():
        path.write_text(text, encoding="utf-8")
    if battery_text is not None:
        battery_path.write_text(battery_text, encoding="utf-8")


def _resolved_same(plan: TagPlan) -> tuple[int, int]:
    """``(same, differ)`` over the post-write resolution of every tagged key.

    The claim behind ``@<id>`` must still be the claim the text key named — same owner,
    same ``source``, same occurrence. A tag that entered ``source`` changes the tuple,
    which is how a leak is caught without trusting placement.
    """
    live: dict[Path, dict[str, Claim]] = {}
    same = differ = 0
    for item in plan.planned:
        if item.path not in live:
            live[item.path] = {c.stable_key: c for c in enumerate_claims(item.path)}
        claim = live[item.path].get(f"@{item.ident}")
        if claim is not None and (claim.owner, claim.source, claim.occurrence) == item.identity:
            same += 1
        else:
            differ += 1
    return same, differ


def proof_line(plan: TagPlan, same: int, differ: int) -> str:
    """The printed evidence. Values, never a bare PASS (CLAUDE.md §8).

    ``keys_equal`` would be meaningless here — with tags every key string changes by
    construction — so the equivalence proved is claim identity, printed per battery.
    """
    return (
        f"battery={plan.battery_name} addressed={plan.addressed} tagged={plan.to_append} "
        f"adopted={plan.adopted} resolved_same={same} resolved_differ={differ}"
    )


def tag_battery(battery_path: Path, project_root: Path, dry_run: bool = False) -> tuple[int, str]:
    """``(exit code, report)``. Writes nothing when ``dry_run`` or when anything refuses."""
    try:
        data = json.loads(battery_path.read_text(encoding="utf-8"))
        battery = Battery.from_json(data, base=project_root)
    except (OSError, json.JSONDecodeError) as exc:
        return 2, f"cannot read battery file {battery_path}: {exc}"
    except BatteryDefinitionError as exc:
        return 2, f"battery definition error: {exc}"

    try:
        plan = plan_tags(battery, battery_path, project_root)
    except TagPlanError as exc:
        return 2, "refused, nothing written:\n  " + "\n  ".join(exc.reasons)
    except (ClaimTagError, SyntaxError, OSError) as exc:
        return 2, f"refused, nothing written: {exc}"

    if dry_run:
        lines = list(plan.overlong)
        # SD-e's binding measurement. Printed even at zero: a missing line and a zero
        # line are the same reading to anyone grepping for it, and only one is true.
        lines.append(f"overlong={len(plan.overlong)} of addressed={plan.addressed}")
        lines.append(
            f"battery={plan.battery_name} addressed={plan.addressed} "
            f"would_tag={plan.to_append} would_adopt={plan.adopted} (dry run, nothing written)"
        )
        return 0, "\n".join(lines)

    if plan.overlong:
        return 2, (
            "refused, nothing written — an append would exceed the line limit:\n  "
            + "\n  ".join(plan.overlong)
            + "\n  Shorten the id by tagging that claim by hand, or explode the statement "
            "so its anchor line is shorter, then re-run."
        )

    originals = _apply_appends(plan)
    battery_text: str | None = None
    try:
        battery_text = _rewrite_battery(battery_path, plan)
        same, differ = _resolved_same(plan)
        if differ:
            _restore(originals, battery_path, battery_text)
            return 2, (
                f"refused and RESTORED — {differ} key(s) resolve to a different claim after "
                f"tagging, which means a tag entered a claim's source text.\n"
                f"  {proof_line(plan, same, differ)}"
            )
        report = lint_battery_file(battery_path, project_root)
        if report.findings:
            _restore(originals, battery_path, battery_text)
            named = "\n  ".join(str(f) for f in report.findings)
            return 2, f"refused and RESTORED — the tagged battery does not lint:\n  {named}"
    except (ClaimTagError, SyntaxError, OSError, json.JSONDecodeError) as exc:
        _restore(originals, battery_path, battery_text)
        return 2, f"refused and RESTORED — re-enumeration failed after writing: {exc}"

    return 0, proof_line(plan, same, differ)
