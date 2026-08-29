"""Render a benchmark dump as a per-item question-and-answer report.

A pass/fail column says a model was wrong; it never says whether the thing it
produced would be usable by the person who has to act on it. That judgement needs
the item's own question, the model's own prose, and the grader's own reason, side
by side — which is what this renders.

Reads a ``--dump-json`` JSONL and writes Markdown. Deliberately a separate reader
rather than a flag on the run, for three reasons: it re-runs on an existing dump
without spending another live run, it can be tested offline against a fixture,
and it keeps report formatting from riding along on the code that does the
measuring.

Dumps written before the record carried its own ``scenario``/``expected`` have no
question in them. Pass ``--dataset-dir`` to backfill from the dataset files; every
backfilled item is MARKED as such, because a question reconstructed from a file
that may have changed since the run is not the same evidence as one the run wrote
down.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.procedure_baseline.loader import DATASET_DIR, load_all

#: Long drafts are folded, not dropped. A reasoning pass on this dataset ran to
#: ~7,500 characters; twenty of those is a wall nobody reads, and a report nobody
#: reads answers the usability question no better than the pass/fail column it
#: replaced.
DEFAULT_MAX_DRAFT_CHARS = 1_500

#: Tilde fences, not backticks: model prose regularly contains ``` and would end
#: a backtick fence early, silently swallowing the rest of the draft into the
#: surrounding document.
_FENCE = "~~~"


def _fmt_reading(scenario: dict[str, Any]) -> str:
    """The measured value against its threshold, in one line."""
    direction = scenario.get("direction", "above")
    unit = scenario.get("unit", "")
    value = scenario.get("measured_value")
    threshold = scenario.get("threshold")
    band = scenario.get("watch_margin")
    band_note = f" · watch band {band:g}" if isinstance(band, int | float) else ""
    return f"**{value:g}** {unit} against a {threshold:g} {unit} `{direction}` line{band_note}"


def _verdict_label(record: dict[str, Any]) -> str:
    """One short verdict token — present, but never the point of the report."""
    if record.get("error"):
        return "UNSCORED (errored)"
    if record.get("proposal_correct") is True:
        return "PASS"
    if record.get("proposal_correct") is False:
        return "FAIL"
    if record.get("watch_graded"):
        return "WATCH (calibration, unscored)"
    return "not graded"


def _render_question(record: dict[str, Any], backfilled: bool) -> list[str]:
    scenario = record.get("scenario")
    expected = record.get("expected")
    if scenario is None:
        return [
            "**Question:** _not recorded in this dump, and no dataset was supplied "
            "to backfill it._",
            "",
        ]
    mark = " _(backfilled from the dataset — not written by the run)_" if backfilled else ""
    out = [f"### The question{mark}", "", f"> {scenario.get('description', '—')}", ""]
    out += [
        "| | |",
        "|---|---|",
        f"| entity | {scenario.get('entity_type', '—')} `{scenario.get('primary_key', '—')}` |",
        f"| reading | {_fmt_reading(scenario)} |",
    ]
    distractors = scenario.get("distractors") or []
    if distractors:
        pretty = ", ".join(f"`{d['primary_key']}`={d['measured_value']:g}" for d in distractors)
        out.append(f"| decoys | {pretty} |")
    context = scenario.get("context") or {}
    if context:
        pretty_ctx = ", ".join(f"`{k}`={v}" for k, v in context.items())
        out.append(f"| context | {pretty_ctx} |")
    if expected:
        canonical = expected.get("canonical_handler")
        acceptable = expected.get("acceptable_handlers") or []
        forbidden_kw = expected.get("forbidden_keywords") or []
        out.append(f"| expected disposition | `{expected.get('disposition', '—')}` |")
        if canonical:
            out.append(f"| canonical handler | `{canonical}` |")
        if acceptable:
            out.append(f"| acceptable | {', '.join(f'`{h}`' for h in acceptable)} |")
        if forbidden_kw:
            out.append(f"| forbidden keywords | {', '.join(f'`{k}`' for k in forbidden_kw)} |")
    out.append("")
    return out


def _render_answer(record: dict[str, Any], max_draft_chars: int) -> list[str]:
    out = ["### What the model produced", ""]
    judgment = record.get("judgment")
    if judgment is None:
        out += [
            f"_No judgment. The exchange errored:_ `{record.get('error', 'unknown')}`",
            "",
        ]
    else:
        handler = judgment.get("suggested_handler", "—")
        tier = record.get("probe_tier")
        tier_note = f" — graded **{tier}**" if tier else ""
        out += [
            f"**Proposed handler:** `{handler}`{tier_note}",
            "",
            f"**Title:** {judgment.get('title', '—')}",
            "",
            f"**Confidence:** {judgment.get('confidence', '—')}",
            "",
            "**Rationale** — the prose an operator would actually be handed:",
            "",
            f"> {judgment.get('rationale', '—')}",
            "",
        ]
        entities = judgment.get("affected_entities") or []
        if entities:
            pretty = ", ".join(f"`{e.get('primary_key')}`" for e in entities)
            out += [f"**Named entities:** {pretty}", ""]
        payload = judgment.get("handler_payload")
        if payload:
            out += [f"**Payload:** `{json.dumps(payload, ensure_ascii=False)}`", ""]

    draft = record.get("draft")
    if draft:
        shown = draft if max_draft_chars <= 0 else draft[:max_draft_chars]
        elided = len(draft) - len(shown)
        tail = f"\n\n[... {elided:,} more characters elided]" if elided > 0 else ""
        out += [
            f"<details><summary>Reasoning draft — {len(draft):,} characters</summary>",
            "",
            _FENCE,
            f"{shown}{tail}",
            _FENCE,
            "",
            "</details>",
            "",
        ]
    return out


def _render_grading(record: dict[str, Any]) -> list[str]:
    checks = record.get("checks")
    if not checks:
        return []
    out = ["### Why it graded that way", "", "| check | | detail |", "|---|---|---|"]
    for check in checks:
        mark = "✅" if check.get("passed") else "❌"
        lane = " _(advisory)_" if check.get("advisory") else ""
        detail = str(check.get("detail", "")).replace("|", "\\|")
        out.append(f"| `{check.get('name')}`{lane} | {mark} | {detail} |")
    out.append("")
    return out


def _render_generation(record: dict[str, Any]) -> list[str]:
    """Token accounting and wall-clock.

    Latency is rendered even when no per-call metrics exist. It is independent
    evidence and it is present in dumps written before the metrics were carried;
    gating it behind ``calls`` would hide a number the run did write down.
    """
    calls = record.get("calls") or []
    latency = record.get("judgment_latency_s")
    if not calls:
        if not isinstance(latency, int | float):
            return []
        return [f"_Generation: {latency:.1f}s end-to-end (no per-call metrics in this dump)._", ""]
    parts = []
    for call in calls:
        tokens = call.get("eval_count")
        reason = call.get("done_reason")
        # An absent reason is spelled out rather than shown as a clean stop: a
        # blank there would read as "measured and fine" when it means "not
        # measured at all".
        reason_note = reason if reason is not None else "no done_reason reported"
        flag = " ⚠️ **TRUNCATED**" if call.get("truncated") else ""
        count = f"{tokens:,}" if isinstance(tokens, int) else "?"
        parts.append(f"{call.get('role')} {count} tok ({reason_note}){flag}")
    latency_note = f" · {latency:.1f}s end-to-end" if isinstance(latency, int | float) else ""
    return [f"_Generation: {' · '.join(parts)}{latency_note}_", ""]


def render_report(
    records: list[dict[str, Any]],
    *,
    backfilled_ids: frozenset[str] = frozenset(),
    max_draft_chars: int = DEFAULT_MAX_DRAFT_CHARS,
) -> str:
    """Render every record as question -> answer -> grading -> generation."""
    out: list[str] = ["# Benchmark items — question and answer", ""]
    truncated = sum(1 for r in records for c in (r.get("calls") or []) if c.get("truncated"))
    out += [
        f"{len(records)} item(s). "
        + (
            f"⚠️ **{truncated} call(s) hit the generation cap** — the affected items' "
            "reasoning was cut, so read them as evidence about the cap, not about "
            "the model."
            if truncated
            else "No call hit the generation cap."
        ),
        "",
        "## At a glance",
        "",
        "| item | verdict | proposed handler | tier |",
        "|---|---|---|---|",
    ]
    for record in records:
        judgment = record.get("judgment") or {}
        out.append(
            f"| `{record.get('item_id')}` | {_verdict_label(record)} "
            f"| `{judgment.get('suggested_handler', '—')}` "
            f"| {record.get('probe_tier') or '—'} |"
        )
    out.append("")

    for record in records:
        item_id = str(record.get("item_id"))
        out += ["---", "", f"## `{item_id}` — {_verdict_label(record)}", ""]
        out += _render_question(record, item_id in backfilled_ids)
        out += _render_answer(record, max_draft_chars)
        out += _render_grading(record)
        out += _render_generation(record)
    return "\n".join(out).rstrip() + "\n"


def _backfill(records: list[dict[str, Any]], dataset_dir: Path) -> frozenset[str]:
    """Fill in the question for records that predate the self-contained dump.

    Mutates in place and returns the ids it touched, so the renderer can mark
    them. A record that already carries its own scenario is never overwritten —
    what the run wrote down outranks what the dataset says now.
    """
    by_id = {item.id: item for dataset in load_all(dataset_dir) for item in dataset.items}
    touched: set[str] = set()
    for record in records:
        if record.get("scenario") is not None:
            continue
        item = by_id.get(str(record.get("item_id")))
        if item is None:
            continue
        record["scenario"] = {
            "description": item.description,
            "entity_type": item.scenario.entity_type,
            "primary_key": item.scenario.primary_key,
            "measured_value": item.scenario.measured_value,
            "unit": item.scenario.unit,
            "threshold": item.scenario.threshold,
            "direction": item.scenario.direction,
            "watch_margin": item.scenario.watch_margin,
            "distractors": [
                {"primary_key": d.primary_key, "measured_value": d.measured_value}
                for d in item.scenario.distractors
            ],
            "context": item.scenario.context,
        }
        record["expected"] = item.expected.model_dump(mode="json")
        touched.add(item.id)
    return frozenset(touched)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, required=True, help="A --dump-json JSONL file.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help=(
            f"Backfill the question for dumps that predate it (default dataset dir is "
            f"{DATASET_DIR}). Backfilled items are marked in the report."
        ),
    )
    parser.add_argument("--out", type=Path, default=None, help="Write Markdown here (default: -).")
    parser.add_argument(
        "--max-draft-chars",
        type=int,
        default=DEFAULT_MAX_DRAFT_CHARS,
        help="Fold reasoning drafts past this length; 0 shows them whole.",
    )
    args = parser.parse_args()

    records = [
        json.loads(line) for line in args.dump.read_text(encoding="utf-8").splitlines() if line
    ]
    backfilled = (
        _backfill(records, args.dataset_dir) if args.dataset_dir is not None else frozenset()
    )
    report = render_report(records, backfilled_ids=backfilled, max_draft_chars=args.max_draft_chars)
    if args.out is None:
        print(report)
    else:
        args.out.write_text(report, encoding="utf-8")
        print(f"REPORT: {len(records)} item(s) -> {args.out}")


if __name__ == "__main__":
    main()
