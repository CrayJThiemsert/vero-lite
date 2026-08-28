"""Offline joiner for the two-model comparison (FDE program phase 1.5).

Reads the JSONL dumps that ``benchmarks.procedure_baseline.run_benchmark
--dump-json`` already writes, groups them by ``(model, repeat)``, and reports
each model on its **majority verdict across repeats** together with the flip
rate that says how stable that verdict was.

No model is called here and no network is touched: this module reads files.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: A run whose items disagree with each other more often than this is reported as
#: too noisy to adjudicate on. It is a REPORTING threshold, not a pass bar — the
#: pass bars live in DECISION.md, fixed before any run.
NOISY_FLIP_RATE = 0.15


class DumpError(ValueError):
    """A dump file could not be read as a procedure-baseline ``--dump-json`` file."""


@dataclass(frozen=True)
class RunRef:
    """One dump file: which model produced it, and which repeat it was."""

    model: str
    repeat: int
    path: Path

    @property
    def label(self) -> str:
        return f"{self.model}#{self.repeat}"


@dataclass
class ItemVerdicts:
    """Every verdict one model produced for one item, across its repeats."""

    item_id: str
    #: ``proposal_correct`` per repeat — the beta headline grade. ``None`` entries
    #: are ungraded items (the non-breach guard), kept so they are never silently
    #: counted as failures.
    proposal: list[bool | None] = field(default_factory=list)
    #: ``probe_tier`` per repeat (canonical / acceptable / forbidden / other).
    probe_tier: list[str | None] = field(default_factory=list)
    #: The judgment-path error string per repeat, or ``None`` when the call
    #: produced a judgment. A non-``None`` entry means the structured-output path
    #: exhausted its retry budget or raised.
    error: list[str | None] = field(default_factory=list)

    def graded_in_every_repeat(self, repeats: int) -> bool:
        """Only items every repeat actually graded can speak to stability."""
        return len(self.proposal) == repeats and all(v is not None for v in self.proposal)

    def majority_proposal(self) -> bool | None:
        """The verdict a majority of repeats reached, or ``None`` if never graded."""
        votes = [v for v in self.proposal if v is not None]
        if not votes:
            return None
        return sum(1 for v in votes if v) * 2 > len(votes)

    def flipped(self) -> bool:
        """Whether this item's graded verdict was not unanimous across repeats."""
        votes = [v for v in self.proposal if v is not None]
        return len(set(votes)) > 1

    def ever_forbidden(self) -> bool:
        """Whether ANY repeat picked a handler classified ``forbidden``.

        Read as a worst-case safety signal on purpose: a model that proposes a
        dangerous handler one run in three is not a model that proposes it
        one-third as dangerously.
        """
        return any(tier == "forbidden" for tier in self.probe_tier)


@dataclass
class ModelReport:
    """One model's aggregate over all its repeats."""

    model: str
    repeats: int
    items_seen: int
    items_stable_basis: int
    majority_correct: int
    majority_accuracy: float | None
    flipped_items: list[str]
    flip_rate: float | None
    error_counts: list[int]
    forbidden_items: list[str]
    probe_tier_totals: dict[str, int]

    @property
    def noisy(self) -> bool:
        return self.flip_rate is not None and self.flip_rate > NOISY_FLIP_RATE


def parse_run_ref(spec: str) -> RunRef:
    """Parse a ``model=path`` or ``model#repeat=path`` CLI argument.

    Without an explicit ``#repeat`` the repeat index is assigned by order of
    appearance for that model, so ``--run gpt-oss:20b=a.jsonl --run
    gpt-oss:20b=b.jsonl`` needs no bookkeeping from the caller.
    """
    name, sep, raw_path = spec.partition("=")
    if not sep or not name or not raw_path:
        raise DumpError(f"run spec must look like 'model=path' or 'model#2=path', got {spec!r}")
    model, hash_sep, repeat_text = name.partition("#")
    if hash_sep:
        try:
            repeat = int(repeat_text)
        except ValueError as exc:
            raise DumpError(f"repeat index must be an integer in {spec!r}") from exc
    else:
        repeat = 0
    return RunRef(model=model, repeat=repeat, path=Path(raw_path))


def assign_repeats(refs: Sequence[RunRef]) -> list[RunRef]:
    """Fill in repeat indices for refs that did not carry an explicit one."""
    seen: Counter[str] = Counter()
    assigned: list[RunRef] = []
    for ref in refs:
        if ref.repeat:
            assigned.append(ref)
            continue
        assigned.append(RunRef(model=ref.model, repeat=seen[ref.model] + 1, path=ref.path))
        seen[ref.model] += 1
    return assigned


def load_dump(path: Path) -> list[dict[str, Any]]:
    """Read one ``--dump-json`` JSONL file into records.

    Raises :class:`DumpError` rather than returning an empty list on a missing or
    malformed file: an empty comparison that silently reports 0/0 is exactly the
    shape of a false pass.
    """
    if not path.is_file():
        raise DumpError(f"dump file not found: {path}")
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DumpError(f"{path}:{lineno} is not valid JSON: {exc}") from exc
        if "item_id" not in record:
            raise DumpError(f"{path}:{lineno} has no 'item_id' — not a procedure-baseline dump")
        records.append(record)
    if not records:
        raise DumpError(f"dump file is empty: {path}")
    return records


def collect_verdicts(
    records_per_repeat: Iterable[Sequence[Mapping[str, Any]]],
) -> dict[str, ItemVerdicts]:
    """Group one model's repeats into per-item verdict lists, in repeat order."""
    verdicts: dict[str, ItemVerdicts] = {}
    for records in records_per_repeat:
        for record in records:
            item_id = str(record["item_id"])
            entry = verdicts.setdefault(item_id, ItemVerdicts(item_id=item_id))
            proposal = record.get("proposal_correct")
            entry.proposal.append(bool(proposal) if proposal is not None else None)
            tier = record.get("probe_tier")
            entry.probe_tier.append(str(tier) if tier is not None else None)
            error = record.get("error")
            entry.error.append(str(error) if error is not None else None)
    return verdicts


def build_model_report(
    model: str, records_per_repeat: Sequence[Sequence[Mapping[str, Any]]]
) -> ModelReport:
    """Aggregate one model's repeats into its majority verdict plus stability."""
    repeats = len(records_per_repeat)
    verdicts = collect_verdicts(records_per_repeat)
    basis = [v for v in verdicts.values() if v.graded_in_every_repeat(repeats)]
    flipped = sorted(v.item_id for v in basis if v.flipped())
    majority_correct = sum(1 for v in basis if v.majority_proposal())
    tier_totals: Counter[str] = Counter()
    for entry in verdicts.values():
        for tier in entry.probe_tier:
            if tier is not None:
                tier_totals[tier] += 1
    errors_per_repeat = [
        sum(1 for record in records if record.get("error") is not None)
        for records in records_per_repeat
    ]
    return ModelReport(
        model=model,
        repeats=repeats,
        items_seen=len(verdicts),
        items_stable_basis=len(basis),
        majority_correct=majority_correct,
        majority_accuracy=(majority_correct / len(basis)) if basis else None,
        flipped_items=flipped,
        # A single repeat is unanimous with itself, so a flip rate computed over one
        # run is 0.0 by construction and says nothing about stability. Found by using
        # this module on a challenger whose run was stopped after one repeat: the
        # report read "flip rate 0.0%" beside a model nothing had measured twice.
        flip_rate=(len(flipped) / len(basis)) if (basis and repeats > 1) else None,
        error_counts=errors_per_repeat,
        forbidden_items=sorted(v.item_id for v in verdicts.values() if v.ever_forbidden()),
        probe_tier_totals=dict(sorted(tier_totals.items())),
    )


def disagreements(reports: Mapping[str, dict[str, ItemVerdicts]]) -> list[dict[str, Any]]:
    """Items where the models' MAJORITY verdicts differ — the whole comparison.

    Ordered by item id so two runs of this joiner produce the same list.
    """
    models = sorted(reports)
    shared = set.intersection(*(set(reports[m]) for m in models)) if models else set()
    rows: list[dict[str, Any]] = []
    for item_id in sorted(shared):
        majorities = {m: reports[m][item_id].majority_proposal() for m in models}
        graded = {m: v for m, v in majorities.items() if v is not None}
        if len(set(graded.values())) > 1:
            rows.append({"item_id": item_id, "majority": majorities})
    return rows


def render(reports: Sequence[ModelReport], diffs: Sequence[Mapping[str, Any]]) -> str:
    """Render the side-by-side report as text."""
    lines: list[str] = ["MODEL COMPARISON — majority verdict over repeats", ""]
    for report in reports:
        accuracy = "n/a" if report.majority_accuracy is None else f"{report.majority_accuracy:.1%}"
        flip = (
            "not measurable (needs 2+ repeats)"
            if report.flip_rate is None
            else f"{report.flip_rate:.1%}"
        )
        lines.append(f"[{report.model}]  repeats={report.repeats}")
        lines.append(
            f"  majority accuracy : {accuracy} "
            f"({report.majority_correct}/{report.items_stable_basis} stable-basis items)"
        )
        lines.append(f"  flip rate        : {flip}" + ("   <-- NOISY" if report.noisy else ""))
        if report.flipped_items:
            lines.append(f"  flipped items    : {', '.join(report.flipped_items)}")
        lines.append(f"  judgment errors  : {report.error_counts} (per repeat)")
        lines.append(f"  probe tiers      : {report.probe_tier_totals}")
        if report.forbidden_items:
            lines.append(f"  FORBIDDEN picks  : {', '.join(report.forbidden_items)}")
        else:
            lines.append("  FORBIDDEN picks  : none")
        lines.append(f"  items seen       : {report.items_seen}")
        lines.append("")
    lines.append(f"majority-verdict disagreements between models: {len(diffs)}")
    for row in diffs:
        lines.append(f"  {row['item_id']}: {row['majority']}")
    lines.append("")
    lines.append(
        "Read the flip rate before the accuracy gap: an accuracy difference "
        "smaller than either model's flip rate is not a difference."
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Join procedure-baseline dumps into a two-model comparison (offline).",
    )
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        metavar="MODEL[#REPEAT]=PATH",
        help="One dump file and the model that produced it; repeat the flag per run.",
    )
    parser.add_argument("--json", type=Path, default=None, help="Also write the report as JSON.")
    args = parser.parse_args(argv)

    refs = assign_repeats([parse_run_ref(spec) for spec in args.run])
    by_model: dict[str, list[RunRef]] = {}
    for ref in refs:
        by_model.setdefault(ref.model, []).append(ref)

    reports: list[ModelReport] = []
    verdicts_by_model: dict[str, dict[str, ItemVerdicts]] = {}
    for model, model_refs in sorted(by_model.items()):
        ordered = sorted(model_refs, key=lambda r: r.repeat)
        records = [load_dump(ref.path) for ref in ordered]
        reports.append(build_model_report(model, records))
        verdicts_by_model[model] = collect_verdicts(records)

    diffs = disagreements(verdicts_by_model)
    print(render(reports, diffs))

    if args.json is not None:
        payload = {
            "models": [
                {
                    "model": r.model,
                    "repeats": r.repeats,
                    "majority_accuracy": r.majority_accuracy,
                    "majority_correct": r.majority_correct,
                    "items_stable_basis": r.items_stable_basis,
                    "flip_rate": r.flip_rate,
                    "flipped_items": r.flipped_items,
                    "error_counts": r.error_counts,
                    "forbidden_items": r.forbidden_items,
                    "probe_tier_totals": r.probe_tier_totals,
                    "items_seen": r.items_seen,
                }
                for r in reports
            ],
            "disagreements": list(diffs),
        }
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
