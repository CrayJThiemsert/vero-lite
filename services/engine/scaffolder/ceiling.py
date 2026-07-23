"""Governance-ceiling detector — stop before the wire, not after (Step 6, AC-8).

Any new AT-2-bearing vertical **is** a candidate 5th signature, so the scaffolder
does not get to decide whether the census baseline should move. It predicts the
signature it is about to emit, compares it against the shipped baseline, and —
when the baseline would extend — **STOPS before writing any wire edit**, handing
the operator a comparison table naming the exact test that will go red.

**The tool never modifies ``_BASELINE_SIGNATURES`` and has no flag that does.**
That list is the record of an argument a human made; moving it is that human's
call, and a scaffolder that could quietly extend it would convert a governance
tripwire into a formality. Detect → stop → hand over is the ceiling by design,
not a missing feature.

The prediction uses :mod:`services.engine.procedures.at2_signature` — the same
fingerprint the census keys on — so "the tool says 5th signature" and "the census
says the baseline moved" cannot disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from services.engine.procedures.at2_signature import (
    Signature,
    at2_gate_kinds,
    content_enum_surface,
    distinct_at2_signatures,
)
from services.engine.procedures.spec import load_procedures_file

CENSUS_TEST = "tests/services/engine/procedures/test_at2_signature_retrigger.py"
CENSUS_ASSERTION = "assert signatures == _BASELINE_SIGNATURES"
CENSUS_INSTRUCTION = "Re-argue it (do not just update this list)."


@dataclass(frozen=True)
class AxisDelta:
    """How the candidate differs from ONE baseline row, per axis."""

    vertical: str
    gate_composition: str
    authority_quantity: str
    enum_surface: str


@dataclass(frozen=True)
class CeilingReport:
    """The comparison table the operator receives instead of a wired vertical."""

    candidate: Signature
    baseline: list[Signature]
    deltas: list[AxisDelta]

    def render(self) -> str:
        lines = [
            "GOVERNANCE CEILING — stopping BEFORE any wire edit.",
            "",
            f"The vertical you are scaffolding would add a {len(self.baseline) + 1}th AT-2 "
            "signature to the census baseline:",
            f"  candidate: {self.candidate}",
            "",
            "Per-axis delta against each shipped signature:",
        ]
        for delta in self.deltas:
            lines += [
                f"  vs {delta.vertical}:",
                f"      gate composition   : {delta.gate_composition}",
                f"      authority quantity : {delta.authority_quantity}",
                f"      enum surface       : {delta.enum_surface}",
            ]
        lines += [
            "",
            f"The test that will go RED is {CENSUS_TEST}:",
            f"    {CENSUS_ASSERTION}",
            f"and its own instruction is: {CENSUS_INSTRUCTION}",
            "",
            "This tool did NOT write any wire edit and did NOT touch the baseline.",
            "Moving the baseline is a human argument, not a scaffolding step.",
        ]
        return "\n".join(lines)


class GovernanceCeilingError(RuntimeError):
    """Raised when emitting would extend the AT-2 census baseline."""

    def __init__(self, report: CeilingReport) -> None:
        self.report = report
        super().__init__(report.render())


def _authority(signature: Signature) -> str:
    """The authority gate — the last AT-2 gate in step order, or '(none)'."""
    kinds = signature[1]
    return kinds[-1] if kinds else "(none)"


def predict_signature(namespace: str, procedures_doc: dict[str, Any], scratch: Path) -> Signature:
    """Fingerprint the spine about to be emitted, via the shipped loader.

    The document is staged into ``scratch`` and loaded rather than fingerprinted
    from the raw dict: the loader is what turns prose into typed
    ``governance_content``, and the fingerprint reads the TYPED field. Predicting
    from the dict would fingerprint a shape the loader might reject.
    """
    path = scratch / "verticals" / namespace / "procedures.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        YAML().dump(procedures_doc, stream)

    spec = load_procedures_file(path, vertical=namespace)
    procedure = spec.procedures[0]
    return (namespace, at2_gate_kinds(procedure), content_enum_surface(procedure))


def build_report(candidate: Signature, baseline: list[Signature]) -> CeilingReport:
    deltas = [
        AxisDelta(
            vertical=row[0],
            gate_composition=(
                "same" if candidate[1] == row[1] else f"{list(row[1])} -> {list(candidate[1])}"
            ),
            authority_quantity=(
                "same"
                if _authority(candidate) == _authority(row)
                else f"{_authority(row)} -> {_authority(candidate)}"
            ),
            enum_surface=("same" if candidate[2] == row[2] else f"{row[2]} -> {candidate[2]}"),
        )
        for row in baseline
    ]
    return CeilingReport(candidate=candidate, baseline=baseline, deltas=deltas)


def check_ceiling(
    namespace: str,
    procedures_doc: dict[str, Any],
    *,
    repo_root: Path,
    scratch: Path,
) -> CeilingReport | None:
    """Predict, compare, and STOP if the baseline would extend.

    Returns ``None`` when the candidate is already a baseline member (the fleet
    golden fixture regenerates without firing); raises
    :class:`GovernanceCeilingError` otherwise. The baseline is read from
    ``repo_root``'s shipped verticals — the same source the census test scans.
    """
    candidate = predict_signature(namespace, procedures_doc, scratch)
    baseline = distinct_at2_signatures(repo_root)

    # A candidate matches when some shipped signature has the same SHAPE — the
    # vertical name differs by construction (it is the new namespace), so
    # comparing the full tuple would fire on every scaffold, including a
    # regeneration of a vertical already in the baseline.
    shape = (candidate[1], candidate[2])
    if any((row[1], row[2]) == shape for row in baseline):
        return None

    raise GovernanceCeilingError(build_report(candidate, baseline))
