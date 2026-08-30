"""Offline rationale re-grade of a procedure-baseline ``--dump-json`` file
(session 264, route B1 — no live model, no host-state, no MS-S1).

**Why this exists.** Under the corrected ``fleet_maintenance`` goal (``0a1061f``)
both compared models score 100% / 100% / 14-of-14 on the three existing lanes
(β headline, α handler probe, consistency), so the benchmark can no longer
separate them — the ceiling became a blocker rather than a limit. Every lane
grades *which* answer the model gave; none grades whether the model's
``rationale`` carries the facts a human approver needs to act on it. This module
measures that fourth thing **from dumps already on disk**, so an existing run's
cost is not paid twice.

It deliberately does **not** modify :mod:`benchmarks.procedure_baseline.grader`.
Promoting a rationale signal into a scored grader lane is a separate, ratifiable
decision (route B2); keeping B1 read-only means every β / α figure ever published
stays byte-comparable.

**Objectivity.** ``grader.py``'s standing discipline is "all objective — no
fuzzy/semantic scoring", and this module holds to it: every signal is a literal
substring or numeric match. In particular the role vocabulary is **not** a
hand-authored word list applied to the model — it is the intersection of a
candidate phrase set with **the procedure goal's own prose**, so a role phrase can
only ever be required of a model that was handed that phrase in its prompt. Edit
the goal and the check follows; a phrase the goal never supplies is never demanded.

**Signals** (reported separately — this module deliberately publishes no verdict;
see ``OPEN DESIGN DECISION`` below):

* ``names_amount`` — the rationale states the item's ``measured_value``
* ``names_threshold`` — the rationale states the item's ``threshold``
* ``roles_named`` — goal-supplied human-role phrases the rationale actually uses

Usage (offline)::

    uv run python -m benchmarks.procedure_baseline.rationale_regrade \\
        --goal-source verticals/fleet_maintenance/procedures.yaml \\
        --dump .claude/benchmark-results/s263-2f-gptoss-goalfix.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

# Candidate human-role phrases, superset across verticals. A phrase here is inert
# until a procedure goal actually contains it — `role_vocabulary` filters this set
# by the goal text, which is what keeps the check fair (see module docstring).
CANDIDATE_ROLE_PHRASES: tuple[str, ...] = (
    "head mechanic",
    "fleet manager",
    "owner",
    "shift supervisor",
    "operations manager",
    "duty engineer",
    "site manager",
    "controller",
)

# A bare integer/decimal, tolerating thousands separators ("5,001" / "5001.0").
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

# Relative tolerance for "the rationale states this value". Models restate a quote
# as 5001, 5001.0 or 5,001 — all the same fact — but must not earn the signal by
# naming a merely nearby number.
_VALUE_RTOL = 1e-6


def role_vocabulary(goal: str) -> tuple[str, ...]:
    """The role phrases this goal actually supplies to the model.

    The fairness guarantee: a model is only ever measured against vocabulary its
    own prompt handed it, so a 0-of-N result is a failure to use supplied words,
    never a vocabulary mismatch invented by the grader.
    """
    lowered = goal.lower()
    return tuple(phrase for phrase in CANDIDATE_ROLE_PHRASES if phrase in lowered)


def _numbers_in(text: str) -> list[float]:
    """Every numeric literal in ``text``, thousands separators folded away."""
    found: list[float] = []
    for raw in _NUMBER_RE.findall(text):
        try:
            found.append(float(raw.replace(",", "")))
        except ValueError:  # pragma: no cover - regex cannot produce this
            continue
    return found


def _states_value(text: str, value: float) -> bool:
    """Whether ``text`` states ``value`` as a number (separator-insensitive)."""
    return any(
        abs(candidate - value) <= _VALUE_RTOL * max(abs(value), 1.0)
        for candidate in _numbers_in(text)
    )


@dataclass(frozen=True)
class RationaleSignals:
    """The objective content signals of one item's rationale.

    ``amount_threshold_ambiguous`` marks the case where the item's
    ``measured_value`` and ``threshold`` are the SAME number (an
    exactly-at-the-ceiling item such as ``fleet-001``). There, one numeral
    satisfies both signals and the two cannot be told apart — reported rather
    than silently double-counted.
    """

    item_id: str
    length: int
    names_amount: bool
    names_threshold: bool
    roles_named: tuple[str, ...]
    amount_threshold_ambiguous: bool

    @property
    def names_role(self) -> bool:
        """Whether the rationale names at least one goal-supplied human role."""
        return bool(self.roles_named)

    @property
    def carries_content(self) -> bool:
        """The minimum bar: does the rationale name **who** must decide?

        **Role-naming alone — Cray-ratified 2026-08-31.** Deliberately the
        weakest of the three candidate rules, and the reason is a property of the
        system rather than of the models: the richer criteria a human approver
        would actually want — is this the right supplier, does their delivery
        history support accepting this quote, how does it compare with the
        alternatives — rest on facts **the ontology does not yet carry**. A pass
        rule may only demand what the run supplies, which is the same fairness
        principle :func:`role_vocabulary` applies to the vocabulary: the goal
        supplies the three role phrases, so naming one is answerable today;
        supplier history is not, so requiring it would fail every model for the
        ontology's silence.

        Raising this bar is therefore an **ontology** move before it is a grader
        move. As supplier-evaluation facts enter the ontology and the goal, each
        one makes a stricter rule answerable, and the bar can rise toward the
        standing target — an approver who can act on the rationale without
        reopening the event.

        Measured consequence on the two ceiling-tied cells (14 breach items,
        corrected goal): ``gpt-oss:20b`` 0/14, ``qwen3.8:27b-mtp-q8_0`` 8/14.
        Requiring the amount as well would have scored 0/14 against ~3/14 —
        rejected as unmeasurable, not as undesirable.
        """
        return self.names_role


def score_rationale(
    rationale: str,
    *,
    item_id: str,
    measured_value: float,
    threshold: float,
    vocabulary: tuple[str, ...],
) -> RationaleSignals:
    """Score one rationale against its own item's facts and the goal vocabulary."""
    lowered = rationale.lower()
    return RationaleSignals(
        item_id=item_id,
        length=len(rationale),
        names_amount=_states_value(rationale, measured_value),
        names_threshold=_states_value(rationale, threshold),
        roles_named=tuple(phrase for phrase in vocabulary if phrase in lowered),
        amount_threshold_ambiguous=abs(measured_value - threshold)
        <= _VALUE_RTOL * max(abs(threshold), 1.0),
    )


def score_dump(dump: Path, vocabulary: tuple[str, ...]) -> list[RationaleSignals]:
    """Score every **breach** record of a dump file.

    Non-breach records are skipped: the rationale question is about routing a
    breach to a human, and watch/ok items have no spend to justify.
    """
    signals: list[RationaleSignals] = []
    for line in dump.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("expected", {}).get("disposition") != "breach":
            continue
        scenario = record["scenario"]
        judgment = record.get("judgment") or {}
        signals.append(
            score_rationale(
                judgment.get("rationale") or "",
                item_id=record["item_id"],
                measured_value=scenario["measured_value"],
                threshold=scenario["threshold"],
                vocabulary=vocabulary,
            )
        )
    return signals


def extract_goal(goal_source: Path, procedure: str | None = None) -> str:
    """The goal prose a model was shown, read from a vertical's ``procedures.yaml``.

    Uses the runtime spine's own loader so the text is exactly what
    ``build_reasoning_messages`` would render — never a re-parse that could drift.
    """
    from services.engine.procedures.spec import load_procedures

    spec = load_procedures(goal_source.parent.name)
    by_id = {item.procedure_id: item for item in spec.procedures}
    if procedure is not None:
        if procedure not in by_id:
            raise SystemExit(
                f"{goal_source} declares no procedure {procedure!r}; have {sorted(by_id)}"
            )
        return by_id[procedure].goal
    if len(by_id) == 1:
        return next(iter(by_id.values())).goal
    raise SystemExit(
        f"{goal_source} declares {len(by_id)} procedures "
        f"({sorted(by_id)}); pass --procedure to pick one."
    )


def format_report(label: str, signals: list[RationaleSignals]) -> str:
    """A per-cell tally plus the per-item detail, as printable text."""
    total = len(signals)
    if not total:
        return f"--- {label}\n    (no breach records)\n"
    lengths = [s.length for s in signals]
    lines = [
        f"--- {label}  breach items={total}",
        f"    rationale chars: mean={sum(lengths) // total} "
        f"min={min(lengths)} max={max(lengths)}",
        f"    names_amount    : {sum(s.names_amount for s in signals)}/{total}",
        f"    names_threshold : {sum(s.names_threshold for s in signals)}/{total}",
        f"    names_role      : {sum(s.names_role for s in signals)}/{total}",
        f"    CARRIES_CONTENT : {sum(s.carries_content for s in signals)}/{total}"
        "   (bar: names a role — Cray-ratified 2026-08-31)",
    ]
    ambiguous = [s.item_id for s in signals if s.amount_threshold_ambiguous]
    if ambiguous:
        lines.append(f"    ⚠ amount==threshold (signals indistinguishable): {ambiguous}")
    lines.append("    per-item:")
    for signal in signals:
        roles = ",".join(signal.roles_named) or "-"
        lines.append(
            f"      {signal.item_id:<14} chars={signal.length:<5} "
            f"amount={'Y' if signal.names_amount else 'n'} "
            f"threshold={'Y' if signal.names_threshold else 'n'} "
            f"roles={roles}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline rationale re-grade of a procedure-baseline dump (B1)."
    )
    parser.add_argument(
        "--goal-source",
        type=Path,
        required=True,
        help="Path to a vertical's procedures.yaml — supplies the role vocabulary.",
    )
    parser.add_argument("--procedure", default=None, help="Procedure name, if the spec has many.")
    parser.add_argument(
        "--dump",
        type=Path,
        action="append",
        required=True,
        help="A run dump (.jsonl). Repeat to compare cells side by side.",
    )
    args = parser.parse_args()

    goal = extract_goal(args.goal_source, args.procedure)
    vocabulary = role_vocabulary(goal)
    print(f"role vocabulary supplied by the goal: {list(vocabulary)}\n")
    for dump in args.dump:
        print(format_report(dump.stem, score_dump(dump, vocabulary)))


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
