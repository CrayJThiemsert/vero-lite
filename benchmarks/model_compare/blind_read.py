"""Blind side-by-side read of two models' prose (FDE program phase 1.5, DECISION.md section 5).

The graded bars in ``compare.py`` score the structured judgment. They say nothing
about the thing a human actually reads before approving: the **prose**. This
module builds a rating sheet where the two models are anonymised and the sides
are shuffled per item, so a rater's preference cannot track a position or a name.

Two honest limits, both load-bearing
------------------------------------
**The rater must not have read the dumps.** Whoever diagnoses a model's failures
knows which side is which, and their "blind" read is not blind. This tool
therefore separates ``prepare`` (which anyone may run) from the rating itself
(which must be done by someone who has not inspected the corpus).

**Language is not scored here.** The procedure-baseline corpus is English, so
DECISION.md section 5's criterion (c) — *reads as Thai a manager would forward* —
is unmeasurable against it and is deliberately absent from the generated sheet.
Everything else is language-agnostic, so the same instrument serves the phase-2
Thai read against a Thai corpus without modification.

Reported as a preference count with its n, never as a percentage accuracy: a
preference is not a correctness measurement and must not be dressed as one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks.model_compare.compare import DumpError, load_dump

#: Verdict tokens a filled sheet may carry. ``TIE`` is explicit so an unfilled
#: item can stay distinguishable from a genuine no-preference.
VERDICTS = ("A", "B", "TIE")

_VERDICT_RE = re.compile(r"^VERDICT:\s*(.*)$", re.MULTILINE)
_ITEM_RE = re.compile(r"^### item\s+(\S+)\s*$", re.MULTILINE)


class SheetError(ValueError):
    """A rating sheet or key could not be read, or disagrees with its key."""


@dataclass(frozen=True)
class Pairing:
    """Which model was shown on which side, for one item."""

    item_id: str
    side_a: str
    side_b: str


def side_for(seed: int, item_id: str) -> bool:
    """Whether the LEFT model is shown as side A for this item.

    Deterministic in ``(seed, item_id)`` so a sheet can be regenerated exactly,
    and unguessable from the sheet alone because the seed lives only in the key.
    """
    digest = hashlib.sha256(f"{seed}:{item_id}".encode()).digest()
    return digest[0] % 2 == 0


def _judgments(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map item id -> judgment blob, skipping items that produced none."""
    out: dict[str, dict[str, Any]] = {}
    for record in records:
        judgment = record.get("judgment")
        if isinstance(judgment, dict):
            out[str(record["item_id"])] = judgment
    return out


def _render_side(judgment: Mapping[str, Any]) -> list[str]:
    """Render one model's prose. The handler is shown BESIDE the prose on purpose.

    A reader cannot judge "could an operator act on this without a follow-up
    question" while blind to the action the record actually carries — and a prose
    that contradicts its own handler is exactly the failure this read exists to
    surface.
    """
    entities = ", ".join(
        str(entity.get("primary_key", "?"))
        for entity in judgment.get("affected_entities", [])
        if isinstance(entity, dict)
    )
    return [
        f"- title: {judgment.get('title', '')}",
        f"- description: {judgment.get('description', '')}",
        f"- rationale: {judgment.get('rationale', '')}",
        f"- entities: {entities}",
        f"- handler: {judgment.get('suggested_handler', '')}",
    ]


def build_sheet(
    left_model: str,
    left: Sequence[Mapping[str, Any]],
    right_model: str,
    right: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> tuple[str, dict[str, Any]]:
    """Build the anonymised sheet and its separate key.

    Only items BOTH models produced a judgment for are included — a pair with one
    empty side is not a comparison, and silently rendering it would invite a
    preference driven by absence.
    """
    left_j, right_j = _judgments(left), _judgments(right)
    shared = sorted(set(left_j) & set(right_j))
    if not shared:
        raise SheetError("the two dumps share no item with a judgment on both sides")

    lines = [
        "# Blind prose read",
        "",
        "Two models, anonymised, sides shuffled per item. Write `VERDICT: A`,",
        "`VERDICT: B`, or `VERDICT: TIE` under each item, then run `blind_read score`.",
        "",
        "Judge on the criteria fixed in DECISION.md section 5, in this order:",
        "",
        "1. does it name the right entity and the right number?",
        "2. could an operator act on it without asking a follow-up question?",
        "3. does the prose state the same action the handler names?",
        "",
        "Do not score writing style beyond those three. Do not look up which model",
        "is which before finishing every item.",
        "",
        "---",
        "",
    ]
    pairings: list[dict[str, str]] = []
    for item_id in shared:
        left_is_a = side_for(seed, item_id)
        side_a_model = left_model if left_is_a else right_model
        side_b_model = right_model if left_is_a else left_model
        a_judgment = left_j[item_id] if left_is_a else right_j[item_id]
        b_judgment = right_j[item_id] if left_is_a else left_j[item_id]
        pairings.append({"item_id": item_id, "side_a": side_a_model, "side_b": side_b_model})
        lines.append(f"### item {item_id}")
        lines.append("")
        lines.append("**A**")
        lines.extend(_render_side(a_judgment))
        lines.append("")
        lines.append("**B**")
        lines.extend(_render_side(b_judgment))
        lines.append("")
        lines.append("VERDICT: ")
        lines.append("")
        lines.append("---")
        lines.append("")

    key = {"seed": seed, "left_model": left_model, "right_model": right_model, "pairings": pairings}
    return "\n".join(lines), key


def parse_sheet(text: str) -> dict[str, str]:
    """Read a filled sheet into ``item_id -> verdict``.

    An item whose verdict line is blank is reported as UNFILLED rather than
    silently dropped or read as a tie; an unrecognised token raises.
    """
    items = _ITEM_RE.findall(text)
    verdicts = [v.strip().upper() for v in _VERDICT_RE.findall(text)]
    if len(items) != len(verdicts):
        raise SheetError(
            f"sheet has {len(items)} items but {len(verdicts)} VERDICT lines — "
            "every item needs exactly one"
        )
    out: dict[str, str] = {}
    for item_id, verdict in zip(items, verdicts, strict=True):
        if not verdict:
            out[item_id] = "UNFILLED"
        elif verdict in VERDICTS:
            out[item_id] = verdict
        else:
            raise SheetError(f"item {item_id}: unrecognised verdict {verdict!r}")
    return out


def score(verdicts: Mapping[str, str], key: Mapping[str, Any]) -> dict[str, Any]:
    """Map side verdicts back to models and count preferences."""
    pairings = {str(p["item_id"]): p for p in key.get("pairings", [])}
    unknown = sorted(set(verdicts) - set(pairings))
    if unknown:
        raise SheetError(f"sheet has items the key does not know: {', '.join(unknown)}")
    counts: dict[str, int] = {str(key["left_model"]): 0, str(key["right_model"]): 0}
    ties = 0
    unfilled: list[str] = []
    for item_id, verdict in sorted(verdicts.items()):
        if verdict == "UNFILLED":
            unfilled.append(item_id)
        elif verdict == "TIE":
            ties += 1
        else:
            winner = pairings[item_id]["side_a" if verdict == "A" else "side_b"]
            counts[str(winner)] += 1
    return {
        "preferences": counts,
        "ties": ties,
        "unfilled": unfilled,
        "scored_n": len(verdicts) - len(unfilled),
        "total_n": len(verdicts),
    }


def render_score(result: Mapping[str, Any]) -> str:
    """Render the preference count — never as a percentage."""
    lines = ["BLIND PROSE READ", ""]
    for model, count in sorted(result["preferences"].items()):
        lines.append(f"  {model}: preferred on {count} of {result['scored_n']} scored items")
    lines.append(f"  ties: {result['ties']}")
    if result["unfilled"]:
        lines.append(f"  UNFILLED ({len(result['unfilled'])}): {', '.join(result['unfilled'])}")
    lines.append("")
    lines.append(
        "A preference count is not an accuracy. Report it as 'preferred on N of M', "
        "never as a percentage."
    )
    return "\n".join(lines)


def _parse_pair(spec: str) -> tuple[str, Path]:
    model, sep, path = spec.partition("=")
    if not sep or not model or not path:
        raise DumpError(f"expected 'model=path', got {spec!r}")
    return model, Path(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Blind prose read between two models.")
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare", help="Build an anonymised sheet plus its key.")
    prep.add_argument("--left", required=True, metavar="MODEL=PATH")
    prep.add_argument("--right", required=True, metavar="MODEL=PATH")
    prep.add_argument("--out", type=Path, required=True, help="Sheet to hand the rater.")
    prep.add_argument("--key", type=Path, required=True, help="Key — do NOT show the rater.")
    prep.add_argument("--seed", type=int, default=20259)

    sc = sub.add_parser("score", help="Score a filled sheet against its key.")
    sc.add_argument("--sheet", type=Path, required=True)
    sc.add_argument("--key", type=Path, required=True)

    args = parser.parse_args(argv)

    if args.command == "prepare":
        left_model, left_path = _parse_pair(args.left)
        right_model, right_path = _parse_pair(args.right)
        sheet, key = build_sheet(
            left_model,
            load_dump(left_path),
            right_model,
            load_dump(right_path),
            seed=args.seed,
        )
        args.out.write_text(sheet, encoding="utf-8")
        args.key.write_text(json.dumps(key, indent=2, sort_keys=True), encoding="utf-8")
        print(f"sheet -> {args.out}")
        print(f"key   -> {args.key}   (do not open this until every verdict is written)")
        return 0

    key_data = json.loads(args.key.read_text(encoding="utf-8"))
    verdicts = parse_sheet(args.sheet.read_text(encoding="utf-8"))
    print(render_score(score(verdicts, key_data)))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
