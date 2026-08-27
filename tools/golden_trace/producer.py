"""Golden-trace producer — the mechanism PLAN-0107 AC-9 found missing.

Before this module the golden-trace corpus
(``tests/services/engine/eval/golden_traces/``) had **no producer at all**:
``grep -l golden_trace --include='*.py'`` returned exactly one file, the test
module that consumes it (measured s241, re-verified s258). Traces were
hand-placed JSON, and the five harness tests validated each file against
*itself* — schema-validity, confidence range, handler resolution, envelope
composition. None of that compares the file to the system, so per CLAUDE.md §8
(*"an expected-value set … is not an oracle of the system until the system's
own output is scored against it"*) the corpus was not yet an oracle.

This module closes that gap from both ends:

1. it **produces** ``expected_envelope`` for a trace by running the trace's
   recorded ``event`` + ``model_output`` through the real composition path
   (``recommender._compose_llm_record``); and
2. the eval harness **scores** the system against that recorded value — a
   fresh composition must equal the envelope on disk.

The scoring direction is what makes it an oracle: the recorded value is read
from the file, the compared value is computed live, so a regression in
composition diverges from the corpus and reddens. The producer is only ever
run deliberately (``python -m tools.golden_trace refresh``) — never from the
test, which would compare fresh output to fresh output and be vacuous by
construction.

**Why exactly one field is excluded.** The composed envelope carries 16
top-level keys. Composing the same trace twice and diffing (s258 feasibility
probe) leaves exactly one differing key: ``created_at``, stamped
``datetime.now(UTC)`` at ``recommender.py:190``. Every other field —
including the whole hybrid reasoning trace and the audit metadata — is
deterministic. The exclusion list is therefore minimal and stated, not a
convenience: widening it is how a golden snapshot goes quietly vacuous.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.engine.llm.structured import JudgmentResult, LlmJudgment
from services.engine.recommender import _compose_llm_record

TRACE_DIR = (
    Path(__file__).resolve().parents[2] / "tests" / "services" / "engine" / "eval" / "golden_traces"
)

#: The only envelope field that is not reproducible. See the module docstring —
#: this set is deliberately tiny and must not grow without a fresh measurement.
VOLATILE_ENVELOPE_FIELDS = frozenset({"created_at"})

#: Traces 01-03 predate the ``vertical`` field; they were all composed as energy.
DEFAULT_VERTICAL = "energy"

#: Traces 01-03 predate the ``judgment_context`` block. These are the constants
#: the harness passed before this module existed, kept so backfilling those three
#: traces records what they already meant rather than silently restating them.
DEFAULT_JUDGMENT_CONTEXT: dict[str, Any] = {
    "thinking": "recorded reasoning narrative",
    "draft": "recorded draft",
    "model": "gpt-oss:20b",
    "attempts": 1,
}


def trace_paths() -> list[Path]:
    """Every golden-trace file, sorted by filename (the harness's own order)."""
    return sorted(TRACE_DIR.glob("*.json"))


def load_trace(path: Path) -> dict[str, Any]:
    """Read one golden trace from disk."""
    parsed: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return parsed


def judgment_context(trace: dict[str, Any]) -> dict[str, Any]:
    """The ``JudgmentResult`` inputs for this trace, defaults filled in.

    ``thinking``, ``draft``, ``model`` and ``attempts`` all reach the composed
    envelope through ``_llm_inference_step``'s detail block, so a trace that
    does not carry them would have its expected value depend on a constant
    invented here rather than on anything recorded.
    """
    context = dict(DEFAULT_JUDGMENT_CONTEXT)
    context.update(trace.get("judgment_context", {}))
    return context


def compose_envelope(trace: dict[str, Any]) -> dict[str, Any]:
    """Run a trace through the REAL composition path and dump the envelope.

    This is the single calling convention shared by the producer and the eval
    harness, so the two cannot drift apart on *how* the system is invoked. It
    does not carry the expected value — that lives on disk.
    """
    judgment = LlmJudgment.model_validate(trace["model_output"])
    context = judgment_context(trace)
    result = JudgmentResult(
        judgment=judgment,
        thinking=context["thinking"],
        draft=context["draft"],
        model=context["model"],
        attempts=context["attempts"],
    )
    record = _compose_llm_record(
        trace["event"],
        trace.get("vertical", DEFAULT_VERTICAL),
        result,
        judgment.affected_entities,
        [],
        [],
        [],
    )
    dumped: dict[str, Any] = record.action.model_dump(mode="json")
    return dumped


def stable_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Drop the non-reproducible fields, leaving what a snapshot can pin."""
    return {key: value for key, value in envelope.items() if key not in VOLATILE_ENVELOPE_FIELDS}


def expected_envelope_for(trace: dict[str, Any]) -> dict[str, Any]:
    """The envelope the system produces for ``trace`` today, minus volatiles."""
    return stable_envelope(compose_envelope(trace))


def envelope_diff(recorded: dict[str, Any], produced: dict[str, Any]) -> list[str]:
    """Keys where the recorded envelope and a fresh composition disagree.

    Reports keys missing from either side as well as differing values, so a
    field the system stops emitting is as visible as one whose value drifts.
    """
    keys = sorted(set(recorded) | set(produced))
    sentinel = object()
    return [key for key in keys if recorded.get(key, sentinel) != produced.get(key, sentinel)]


def refresh(path: Path) -> bool:
    """Recompute ``expected_envelope`` for one trace; True when the file changed.

    Writing is the deliberate act of accepting the system's current output as
    the new expectation — run it when a composition change is intended, and
    review the resulting diff as part of that change.
    """
    trace = load_trace(path)
    produced = expected_envelope_for(trace)
    if trace.get("expected_envelope") == produced:
        return False
    trace["expected_envelope"] = produced
    path.write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def check(path: Path) -> list[str]:
    """Keys where the trace on disk disagrees with a fresh composition.

    An empty list means the corpus still describes the system. A trace with no
    ``expected_envelope`` at all reports every key as differing, rather than
    passing quietly — an unrecorded expectation is a gap, not an agreement.
    """
    trace = load_trace(path)
    recorded = trace.get("expected_envelope")
    produced = expected_envelope_for(trace)
    if recorded is None:
        return sorted(produced)
    return envelope_diff(recorded, produced)
