"""Extract Step 4b's four latency terms per arm, and refuse a reading it cannot account for.

Step 4b exists so `load` and `prefill` stop being unmeasured terms in AC-4's rule
`cap / decode_rate + load + prefill < timeout`. This reads the per-case artifacts
`run_benchmark.py` writes and reports the terms — with the accounting that makes the
numbers quotable:

* every attempt is counted, and any attempt missing any of the four duration fields
  is counted SEPARATELY rather than skipped (a skipped attempt shrinks the
  denominator with it, so the aggregate still looks tidy);
* raw per-case values are printed before any aggregate, so a percentile can be
  checked by hand against the list it came from;
* the pre-committed pass/fail read (Cray, typed, s288) is applied: an arm needs
  >= 6 of 11 cases with a completed attempt, else INSUFFICIENT-EVIDENCE — which is
  NOT a failure of the model and must never be quoted as one.

CONTROL, run before any reading here is trusted: the derived decode rate must
reproduce PLAN-0118's published figure for gpt-oss@4096 (~85 s) to within a stated
band. An instrument that cannot re-derive a number already on the record has not
earned the right to produce new ones.

Rehomed s289 from an untracked `/tmp` script — `/tmp` does not survive a reboot, and
this file carries the only control that ties Step 4b's new numbers back to a
published one. CI does not type-check `benchmarks/`, so `mypy --strict` on this
module is run by hand (CLAUDE.md §8 / the `code-operational-policy` skill).

Usage:
    python -m benchmarks.intake_extraction.extract_terms <arm-dir> [<arm-dir> ...]
"""

from __future__ import annotations

import json
import pathlib
import statistics
import sys
from dataclasses import dataclass

NS = 1_000_000_000
FIELDS = (
    "total_duration_ns",
    "load_duration_ns",
    "prompt_eval_duration_ns",
    "eval_duration_ns",
)
MIN_CASES = 6  # the pre-committed floor (Cray, typed, s288)

# PLAN-0118's published gpt-oss@4096 figure is ~85 s. The band is deliberately wide:
# it is a control on the INSTRUMENT (does the derived rate land in the right order of
# magnitude), not a re-measurement of the model.
#
# 🔴 The control is MODEL-SCOPED, and s289 measured why that matters. The first
# rehomed version applied the gpt-oss band to every arm; all three gpt-oss arms read
# OK (89.7 / 90.3 / 86.4 s, reproducing the published figure three times over) while
# all four qwen arms read OUT OF BAND — because qwen decodes at ~19 tok/s against
# gpt-oss's ~46, so 4096 tokens legitimately predicts ~215 s. Nothing was wrong with
# the instrument's arithmetic or with the qwen artifacts: the CONTROL'S APPLICABILITY
# was wrong. A control asserted against a model it does not describe is not a control
# — it is either ignored (which teaches the reader to ignore controls) or read as a
# defect that does not exist. So a model with no published figure gets the derived
# prediction printed and NO verdict, said in as many words.
CONTROL_CAP = 4096
PUBLISHED_BANDS: dict[str, tuple[float, float]] = {
    # model tag -> (lo, hi) seconds for CONTROL_CAP tokens, from PLAN-0118's RESULTS
    "gpt-oss:20b": (60.0, 110.0),
}


@dataclass(frozen=True)
class Row:
    """One usable attempt — every duration field present, none inferred."""

    case: str
    idx: int
    total: float
    load: float
    prefill: float
    decode: float
    out_tok: int
    in_tok: int
    done: str | None
    trunc: bool | None
    model: str


def _collect(files: list[pathlib.Path]) -> tuple[list[Row], int, int]:
    """Return (usable rows, attempts seen, attempts missing a duration field).

    An attempt missing any of FIELDS is counted, never dropped: dropping it would
    shrink the denominator along with the numerator and leave the aggregate looking
    tidy about data it never saw.
    """
    rows: list[Row] = []
    attempts_total = 0
    attempts_missing = 0
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        for att in rec.get("attempts", []):
            attempts_total += 1
            if any(att.get(k) is None for k in FIELDS):
                attempts_missing += 1
                continue
            rows.append(
                Row(
                    case=rec["case_id"],
                    idx=att["index"],
                    total=att["total_duration_ns"] / NS,
                    load=att["load_duration_ns"] / NS,
                    prefill=att["prompt_eval_duration_ns"] / NS,
                    decode=att["eval_duration_ns"] / NS,
                    out_tok=att.get("eval_count") or 0,
                    in_tok=att.get("prompt_eval_count") or 0,
                    done=att.get("done_reason"),
                    trunc=att.get("truncated"),
                    model=att.get("model") or rec.get("model") or "",
                )
            )
    return rows, attempts_total, attempts_missing


def report_arm(arm_dir: str) -> int:
    """Print one arm's terms. Returns 0 if USABLE, 1 if INSUFFICIENT-EVIDENCE, 2 if empty."""
    d = pathlib.Path(arm_dir)
    files = sorted(d.glob("*.json"))
    if not files:
        print(f"REFUSED: no artifacts under {d} — an empty arm is not an exhaustive one")
        return 2

    rows, attempts_total, attempts_missing = _collect(files)
    if not rows:
        print(
            f"REFUSED: {d.name} — {attempts_total} attempts, none carrying all four "
            f"duration fields; there is nothing here to average"
        )
        return 2

    print(f"arm: {d.name}")
    print(
        f"cases: {len(files)}   attempts: {attempts_total}   "
        f"missing a duration field: {attempts_missing}   usable: {len(rows)}"
    )
    print()
    print(
        f"  {'case':<8} {'#':<3} {'total':>8} {'load':>7} {'prefill':>8} {'decode':>8} "
        f"{'out':>6} {'in':>6}  done      trunc"
    )
    for r in sorted(rows, key=lambda r: (r.case, r.idx)):
        print(
            f"  {r.case:<8} {r.idx:<3} {r.total:>8.2f} {r.load:>7.3f} "
            f"{r.prefill:>8.3f} {r.decode:>8.2f} {r.out_tok:>6} {r.in_tok:>6}  "
            f"{r.done!s:<9} {r.trunc}"
        )

    cases_ok = len({r.case for r in rows})
    totals = sorted(r.total for r in rows)
    out_tok = sum(r.out_tok for r in rows)
    dec_s = sum(r.decode for r in rows)

    accounted = len(rows) + attempts_missing
    print()
    print(
        f"  attempts accounted for: {len(rows)} + {attempts_missing} missing = "
        f"{accounted}  vs attempts seen {attempts_total}  "
        f"{'OK' if accounted == attempts_total else 'MISMATCH'}"
    )
    print(f"  cases with a usable attempt: {cases_ok} / {len(files)}  (floor {MIN_CASES})")
    print()
    print(
        f"  total_duration  p50={statistics.median(totals):.2f}s  "
        f"p95={totals[max(0, round(0.95 * (len(totals) - 1)))]:.2f}s  "
        f"max={totals[-1]:.2f}s   n={len(totals)}"
    )
    print(
        f"  load     mean={statistics.mean(r.load for r in rows):.3f}s  "
        f"max={max(r.load for r in rows):.3f}s"
    )
    print(
        f"  prefill  mean={statistics.mean(r.prefill for r in rows):.3f}s  "
        f"max={max(r.prefill for r in rows):.3f}s"
    )
    rate = out_tok / dec_s if dec_s else 0.0
    print(f"  decode rate = {out_tok} tok / {dec_s:.2f}s = {rate:.1f} tok/s")
    print(
        f"  truncated: {sum(1 for r in rows if r.trunc)}   "
        f"done_reason != stop: {sum(1 for r in rows if r.done != 'stop')}"
    )

    models = sorted({r.model for r in rows})
    print()
    print(f"  model tag(s) in this arm: {', '.join(models) or '(none recorded)'}")
    print("  CONTROL — does this rate re-derive the published figure FOR THIS MODEL?")
    if not rate:
        print("    no decode time recorded — no rate, so no control")
    elif len(models) != 1:
        print(
            f"    {len(models)} model tags in one arm — REFUSED: a mixed arm has no "
            f"single published figure to check against"
        )
    elif models[0] not in PUBLISHED_BANDS:
        pred = CONTROL_CAP / rate
        print(
            f"    {CONTROL_CAP} / {rate:.1f} tok/s = {pred:.1f} s   "
            f"NO PUBLISHED FIGURE for {models[0]} — not a control, no verdict"
        )
    else:
        pred = CONTROL_CAP / rate
        lo, hi = PUBLISHED_BANDS[models[0]]
        band = lo <= pred <= hi
        print(
            f"    {CONTROL_CAP} / {rate:.1f} tok/s = {pred:.1f} s   "
            f"published band {lo:.0f}-{hi:.0f} s   "
            f"{'OK' if band else 'OUT OF BAND — suspect the instrument before the artifact'}"
        )
    print()
    print(
        f"STEP4B-ARM: {'USABLE' if cases_ok >= MIN_CASES else 'INSUFFICIENT-EVIDENCE'} "
        f"({cases_ok}/{len(files)} cases, floor {MIN_CASES})"
    )
    return 0 if cases_ok >= MIN_CASES else 1


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    worst = 0
    for i, arm in enumerate(argv):
        if i:
            print("\n" + "=" * 78 + "\n")
        worst = max(worst, report_arm(arm))
    if len(argv) > 1:
        print(
            f"\nSTEP4B-ARMS: {len(argv)} read, worst status "
            f"{'USABLE' if worst == 0 else 'INSUFFICIENT-EVIDENCE' if worst == 1 else 'REFUSED'}"
        )
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
