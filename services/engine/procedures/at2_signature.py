"""The AT-2 signature fingerprint — one implementation, two consumers.

Extracted from ``tests/services/engine/procedures/test_at2_signature_retrigger.py``
by PLAN-0091 Step 6 so the census test and the scaffolder's governance-ceiling
detector cannot drift. If the tool predicted a signature with its own copy of
this logic, "the tool says this is a 5th signature" and "the census test says
the baseline moved" could disagree — and the whole point of the ceiling detector
is to warn about the test that is *about* to go red.

**What did NOT move.** ``_BASELINE_SIGNATURES`` and both of the census test's
assertions stay in that test, byte-identical. This module is the fingerprint
FUNCTION only; the baseline it is compared against, and the decision to fail,
remain where a reader looking for the tripwire will find them.

**The one deliberate change: an explicit root.** The test's private version
globbed ``Path("verticals")`` relative to the CWD. The scaffolder fingerprints a
spine it is about to write into a SCRATCH tree, so inheriting the CWD would
fingerprint the repo instead and make the detector vacuous — it would compare
the repo against itself and never fire. :func:`distinct_at2_signatures`
therefore takes the root it should scan.
"""

from __future__ import annotations

from pathlib import Path

from services.engine.procedures.orchestrator import _is_at2_procedure
from services.engine.procedures.spec import Procedure, load_procedures_file

Signature = tuple[str, tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...]]
"""``(vertical, gate_kinds, enum_surface)`` — the fingerprint the census keys on."""


def at2_gate_kinds(procedure: Procedure) -> tuple[str, ...]:
    """The AT-2 gate kinds this procedure composes, in step order — the shape half of its
    signature. Read off the TYPED ``governance_content`` (the authoritative field), never the
    non-authoritative facet prose."""
    return tuple(
        step.governance_content.kind
        for step in procedure.steps
        if step.governance_content is not None
    )


def content_enum_surface(procedure: Procedure) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """The GOVERNED-ENUM SURFACE each AT-2 content presses, per step — its kind plus the sorted
    closed-enum member VALUES it names (the reviewer-F4 discriminator). This is the D2 type-system
    footprint Rule-of-Three actually cares about: two procedures sharing a gate composition but
    naming different criteria / policies / severity floors are DIFFERENT signatures. Deliberately
    excludes free instance detail (weights, Thai role strings, tier count) so trigger variants of
    ONE signature — identical content — collapse to an identical surface and never over-split."""
    surface: list[tuple[str, tuple[str, ...]]] = []
    for step in procedure.steps:
        gc = step.governance_content
        if gc is None:
            continue
        if gc.kind == "rule_gate":
            # PLAN-0087: `criterion` is a declared CriterionId (plain str) since the vocabulary
            # left engine code — no `.value` to unwrap. The FINGERPRINT is unchanged: the same
            # ids in the same sorted order, so `_BASELINE_SIGNATURES` stays byte-identical
            # and the census pin still fires on a genuine 5th signature.
            members = tuple(sorted(rule.criterion for rule in gc.rules))
        elif gc.kind == "scored_rule":
            members = tuple(sorted((gc.default_source.value, gc.exception_policy.value)))
        elif gc.kind == "doa_tier":
            members = (gc.currency,)  # the money surface; a new currency = new pressure
        elif gc.kind == "severity_tier":
            members = tuple(sorted(tier.min_severity.value for tier in gc.tiers))
        else:
            members = ()
        surface.append((gc.kind, members))
    return tuple(surface)


def distinct_at2_signatures(root: Path) -> list[Signature]:
    """Every distinct AT-2 signature under ``root``, sorted.

    ``root`` is explicit (see the module docstring): the scaffolder scans a
    scratch tree, the census test scans the checkout. Globs only
    ``verticals/*`` (never the ``.claude/worktrees`` copies), and dedups trigger
    variants of one signature.
    """
    signatures: set[Signature] = set()
    for path in sorted((root / "verticals").glob("*/procedures.yaml")):
        vertical = path.parent.name
        spec = load_procedures_file(path, vertical=vertical)
        for procedure in spec.procedures:
            if _is_at2_procedure(procedure):
                signatures.add(
                    (vertical, at2_gate_kinds(procedure), content_enum_surface(procedure))
                )
    return sorted(signatures)
