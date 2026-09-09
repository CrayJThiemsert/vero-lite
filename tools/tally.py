#!/usr/bin/env python
"""Break a record file down by a field, and PROVE the breakdown accounts for every record.

🔴 **The measured failure this replaces.** Session 288 reported the Stop-hook
classifier's transport breakdown into ``docs/STATUS.md`` from two different
instruments in the same table: ``grep -c -i timeout`` (every line containing that
word ANYWHERE — including inside a ``reason`` string) alongside
``grep -c '"transport": "ok"'`` (the actual field). The four buckets summed to
**139** against **140** lines. Nothing in the reading said so; a subagent noticed
the arithmetic by eye, and without that the wrong numbers would have shipped.

A fourth value, ``retry``, existed and was never counted — because a hand-written
breakdown enumerates the values its author already knows about.

**The rule this makes mechanical.** A partition is trustworthy only when

1. the per-value counts **sum to the record count**, and
2. **zero** records lack the key, and
3. **zero** records failed to parse.

All three are computed here and printed as values, never as a bare verdict (§8:
*a verification report prints the values it measured*). Failing any of them exits
non-zero, so a breakdown that does not account for its own input cannot be quoted
as evidence by accident.

**``--expect`` is the falsifier, written down BEFORE the reading.** State the value
set you believe exists and this refuses when reality differs — which is how a value
you did not know about announces itself instead of being silently dropped. That is
the whole difference between a measurement and a confirmation of what you assumed.

**Scope, so a green is not over-read.** This proves a breakdown is arithmetically
complete over the file it read. It does not know whether that file is the right
file, whether the field means what you think, or whether the records are the
population you care about. Those stay yours.

Usage::

    python tools/tally.py .claude/state/stop-classifier-log.jsonl --field transport
    python tools/tally.py LOG --field decision --expect pause,proceed
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Tally:
    """A breakdown plus everything needed to decide whether to believe it."""

    path: Path
    field: str
    counts: Counter[str]
    records: int
    unparseable: int
    missing_field: int

    @property
    def counted(self) -> int:
        return sum(self.counts.values())

    @property
    def exhaustive(self) -> bool:
        """Every record is accounted for by exactly one bucket.

        ⚠️ ``counted == records`` is the WHOLE test, and that is deliberate. Every
        non-blank line increments exactly one of ``counted`` / ``unparseable`` /
        ``missing_field``, so ``records == counted + unparseable + missing`` is an
        identity — which makes ``unparseable == 0 and missing_field == 0`` implied,
        not additional. They were here, and a probe proved they could never fire:
        dead defensive code invites the reader to believe a check is happening
        (CLAUDE.md §8). The two counters stay on the report because they say WHICH
        exclusion happened; that is diagnosis, not verdict.
        """
        return self.counted == self.records


def tally_jsonl(path: Path, field: str) -> Tally:
    """Count records by ``field``, keeping the records that did NOT contribute.

    A line that will not parse, and a record with no such field, are counted
    SEPARATELY rather than skipped. A skipped record is the mechanism by which a
    breakdown quietly stops describing its input — the sum still looks tidy
    because the denominator shrank with it.
    """
    counts: Counter[str] = Counter()
    records = unparseable = missing = 0

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                unparseable += 1
                continue
            if not isinstance(record, dict) or field not in record:
                missing += 1
                continue
            counts[str(record[field])] += 1

    return Tally(path, field, counts, records, unparseable, missing)


def render(tally: Tally, expect: set[str] | None) -> tuple[str, bool]:
    """The report, and whether it may be quoted as evidence."""
    lines = [
        f"file: {tally.path}",
        f"records: {tally.records}   unparseable: {tally.unparseable}   "
        f"missing '{tally.field}': {tally.missing_field}",
        "",
    ]
    width = max((len(v) for v in tally.counts), default=1)
    for value, n in tally.counts.most_common():
        share = (n / tally.records * 100) if tally.records else 0.0
        lines.append(f"  {value:<{width}}  {n:>6}  {share:5.1f}%")

    lines.append("")
    verdict = "==" if tally.counted == tally.records else "!="
    lines.append(
        f"  sum {tally.counted} {verdict} records {tally.records}"
        f"   (unparseable {tally.unparseable}, missing key {tally.missing_field})"
    )

    ok = tally.exhaustive
    if not ok:
        lines.append(
            "🔴 NOT EXHAUSTIVE — this breakdown does not account for every record it "
            "read, so it cannot be quoted as evidence. Records that neither parsed nor "
            "carried the field are shown above; they did not vanish, they were excluded."
        )

    if expect is not None:
        actual = set(tally.counts)
        unexpected = sorted(actual - expect)
        absent = sorted(expect - actual)
        lines.append(f"  expected values: {sorted(expect)}   actual: {sorted(actual)}")
        if unexpected or absent:
            ok = False
            lines.append(
                f"🔴 VALUE SET DIFFERS — unexpected: {unexpected}   absent: {absent}. "
                "A value you did not enumerate is exactly what a hand-written breakdown "
                "drops in silence; an absent one means the population moved."
            )

    lines.append("")
    lines.append(
        f"TALLY: {'EXHAUSTIVE' if ok else 'REFUSED'} "
        f"({tally.records} records, {len(tally.counts)} values)"
    )
    return "\n".join(lines), ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tally",
        description="Break a JSONL file down by a field and prove the breakdown is complete.",
    )
    parser.add_argument("path", type=Path, help="the JSONL file to read")
    parser.add_argument("--field", required=True, help="the record field to break down by")
    parser.add_argument(
        "--expect",
        default=None,
        help=(
            "comma-separated value set you believe exists — the falsifier, written down "
            "BEFORE the reading. Refuses when reality differs."
        ),
    )
    args = parser.parse_args(argv)

    if not args.path.is_file():
        print(f"tally: no such file: {args.path}", file=sys.stderr)
        return 2

    expect = {v.strip() for v in args.expect.split(",") if v.strip()} if args.expect else None
    report, ok = render(tally_jsonl(args.path, args.field), expect)
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
