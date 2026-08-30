"""Consistency: do items the governing rule treats as the SAME case get the same answer?

This is not reproducibility, and the difference is the point.

**Reproducibility** asks: run the same item twice, is the answer the same? It is a
property of the INSTRUMENT. Session 262 measured it at 20/20 — two runs of
``fleet`` x ``qwen/full`` produced drafts identical character for character, while
judgment latency differed on 17 of 20, so they were genuinely two runs.

**Consistency** asks: do items that the governing rule says are the same case get
the same CLASS of answer? It is a property of the JUDGMENT, and it is what a user
has to be able to trust. A model can be perfect on the first and poor on the
second — and on this dataset it is. Same session, same runs: 9 of 14.

Grouping is by the rule's own structure, not by similarity of prose. For fleet
that is the DOA ladder: two repairs in the same authority band differ only in an
amount the rule has already decided is irrelevant, so a different class of answer
between them is a divergence the rule never licensed. Measured, mid band
(THB 5,001-30,000), ten items under one rule: ``escalate`` x5, ``echo`` x2 (one of
them on a THB 22,800 repair — a no-op), ``dispatch_replacement_truck`` x2,
``tow_to_partner_garage`` x1. No pattern by amount: THB 30,000 escalates while
THB 22,800 does not. The owner band above it was 4/4.

### Cray's ruling, 2026-08-30 (typed) — the STRICT reading

A handler the grader tiers as *acceptable* still counts as a **different class of
answer**. Specifically ``dispatch_replacement_truck`` does NOT agree with
``escalate``: the question is *who has authority to approve this spend*, and
dispatching a replacement truck answers a different question, however sensible it
is as a parallel action.

So this module scores against the rule's own canonical handler, never against
whatever the model returned most often. The lenient reading (counting acceptable
as agreement) puts the same run at 11/14 rather than 9/14, and the gap between
those two numbers is exactly the judgement Cray settled. It is recorded in code
rather than in prose because a definition that has to be re-derived is a
definition that will be re-derived differently.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: The fleet DOA ladder, as authored in
#: ``verticals/fleet_maintenance/procedures.yaml``: 0 -> chang yai,
#: 5,001 -> fleet manager, 30,001 -> owner. Lower bounds, ascending.
FLEET_DOA_BANDS: tuple[tuple[float, str], ...] = (
    (30_001.0, "owner (>=30,001)"),
    (5_001.0, "fleet-manager (5,001-30,000)"),
    (0.0, "chang-yai (<5,001)"),
)


def band_of(amount: float, bands: Iterable[tuple[float, str]] = FLEET_DOA_BANDS) -> str:
    """The authority band an amount falls in.

    Bands are given as descending lower bounds, so the first one the amount clears
    is its band. Written this way rather than as a chain of comparisons because the
    ladder is data in the vertical's YAML, and a caller for another vertical passes
    its own.
    """
    for floor, name in bands:
        if amount >= floor:
            return name
    return "<below all bands>"


@dataclass(frozen=True)
class BandResult:
    """One authority band's agreement with the rule."""

    band: str
    canonical: str | None
    total: int
    agreed: int
    #: handler -> the item ids that proposed it, so a reader can see WHICH items
    #: diverged rather than only how many. A bare count cannot be acted on.
    by_handler: dict[str, list[str]]


@dataclass(frozen=True)
class ConsistencyReport:
    """Agreement with the governing rule, per band and overall."""

    bands: tuple[BandResult, ...]

    @property
    def total(self) -> int:
        return sum(band.total for band in self.bands)

    @property
    def agreed(self) -> int:
        return sum(band.agreed for band in self.bands)


def score(
    records: Iterable[Mapping[str, Any]],
    *,
    bands: Iterable[tuple[float, str]] = FLEET_DOA_BANDS,
) -> ConsistencyReport:
    """Score a ``--dump-json`` record set against each band's canonical handler.

    Only breach items are scored: watch items carry no adjudicated ground truth
    (the PLAN-0022 M-2=b calibration state) and ok items run no model call, so
    including either would move the number without measuring anything.

    A record whose exchange errored counts toward ``total`` and never toward
    ``agreed``. Dropping it instead would let a run improve its consistency by
    failing more often, which is the wrong direction for a trust metric.
    """
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    order: list[str] = []
    for record in records:
        expected = record.get("expected") or {}
        if expected.get("disposition") != "breach":
            continue
        scenario = record.get("scenario") or {}
        band = band_of(float(scenario.get("measured_value") or 0.0), bands)
        if band not in grouped:
            grouped[band] = []
            order.append(band)
        grouped[band].append(record)

    results: list[BandResult] = []
    for band in sorted(order):
        items = grouped[band]
        by_handler: dict[str, list[str]] = {}
        canonical: str | None = None
        agreed = 0
        for record in items:
            canonical = canonical or (record.get("expected") or {}).get("canonical_handler")
            judgment = record.get("judgment") or {}
            handler = judgment.get("suggested_handler") or "<no judgment>"
            by_handler.setdefault(handler, []).append(str(record.get("item_id")))
        for record in items:
            judgment = record.get("judgment") or {}
            if canonical is not None and judgment.get("suggested_handler") == canonical:
                agreed += 1
        results.append(
            BandResult(
                band=band,
                canonical=canonical,
                total=len(items),
                agreed=agreed,
                by_handler=by_handler,
            )
        )
    return ConsistencyReport(bands=tuple(results))


def render(report: ConsistencyReport) -> str:
    """A human-readable rendering that names the diverging items, not just a ratio."""
    lines: list[str] = []
    for band in report.bands:
        lines.append(f"  {band.band}  —  {band.total} items, canonical {band.canonical!r}")
        for handler, ids in sorted(band.by_handler.items(), key=lambda kv: -len(kv[1])):
            mark = "  " if handler == band.canonical else "<-"
            lines.append(f"    {mark} {handler:<28} {len(ids):>2}  {', '.join(ids)}")
        lines.append("")
    lines.append(
        f"CONSISTENCY (agrees with the rule's canonical handler): {report.agreed}/{report.total}"
    )
    lines.append(
        "Strict reading (Cray, 2026-08-30): an 'acceptable' handler is a DIFFERENT "
        "class of answer, not agreement."
    )
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, required=True, help="A --dump-json JSONL file.")
    args = parser.parse_args()
    records = [
        json.loads(line) for line in args.dump.read_text(encoding="utf-8").splitlines() if line
    ]
    print(f"DUMP: {args.dump}")
    print(render(score(records)))


if __name__ == "__main__":
    main()
