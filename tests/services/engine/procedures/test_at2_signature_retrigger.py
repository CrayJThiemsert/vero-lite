"""PLAN-0074 AC-11 — the ADR-0025 D7 AT-2-generator re-trigger (this PLAN owns the marker).

ADR-0025 D7 defers the **AT-2 generator** (the generator ships AT-1 only and ABSTAINS on
AT-2-class narratives) on an explicit Rule-of-Three argument: at N=1 there was exactly ONE
governance-heavy instance to generalise from, and a generator extracted from a single instance
generalises that instance's accidents (procurement's money authority, its vendor-hygiene criteria,
its emergency waiver) into the engine. The deferral is not a silent ``# TODO`` that rots under
delivery pressure — ADR-0031 OQ-4 assigned this marker to the PLAN that adds the 2nd signature.
This module is it:

* it counts **distinct AT-2 SIGNATURES** shipped across ``verticals/*/procedures.yaml``, and
* it **FAILS when a THIRD appears** — forcing the AT-2-generator deferral to be re-argued rather
  than accreting a third hand-authored copy in silence.

**Signatures, not procedure entries (the counting trap this marker exists to avoid).** Procurement
ships THREE AT-2 procedure entries — ``emergency_sourcing_round`` plus its schedule- and
event-triggered variants — but they are the SAME governance signature fired three ways (the
archetype catalog says so explicitly: "the schedule-triggered variant is the same archetype, not a
second instance", ``docs/conventions/procedure-archetypes.md``). A naive per-entry count would read
N>=3 today and fire this marker on a vertical that taught us nothing new about AT-2. The dedup key
(Code judgment, PLAN-0074 AC-11 — veto-open) is therefore:

    (vertical, the ordered tuple of the procedure's AT-2 gate kinds)

— the vertical (a signature is a vertical's governance shape) and WHICH gates it composes, in step
order. Procurement's three entries all key to ``("procurement", ("scored_rule", "rule_gate",
"doa_tier"))``; supply_chain's disposition keys to ``("supply_chain", ("scored_rule", "rule_gate",
"severity_tier"))`` — genuinely different, because its authority gate is NON-MONEY.

**N=2 REACHED — and the re-evaluation was performed, not deferred again (PLAN-0074 SD-3).** The
D7 re-trigger's whole point is that N>=2 forces the question. It was asked at this PLAN's review:

* **Resolution: the AT-2 generator STAYS deferred and abstaining; the D2 content types stay
  instance-scoped.** N>=2 *permits* genericization, it does not mandate it. What the second
  signature actually revealed is that the parts a generator would have to emit are still
  per-instance — the authority QUANTITY (baht spend vs excursion severity; ``DoaLadder`` cannot
  represent the latter, which is why a 4th gate kind exists at all), the compliance CRITERION
  vocabulary (vendor hygiene vs GDP/GxP), and even the scored-rule provenance policy
  (``SourcePolicy`` turned out NOT to be freely extensible — the run executor keys on the member
  itself, so a third member would invert a vertical's provenance). What DID
  generalise, unchanged, is the GATE SHAPE: a scored rule selects, a rule gate blocks, a tiered
  human gate authorises, SoD holds. That is a real finding, and it is the input to the follow-on
  genericization/gate-plugin-seam PLAN (ADR-0031 D3) — not something to bolt into a gate-kind PLAN.
* The generator's abstain guard grew to cover the new kind instead (``generator/pipeline.py``
  ``_AT2_ONLY_KINDS``, PLAN-0074 Step 3) — proven by ``test_generator_pipeline.py``.

So the marker re-arms at **N=3**: a third distinct signature would mean three hand-authored
governance shapes and no extraction, which Rule-of-Three (ADR-006 D4) does not permit.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8). The failing assertion is the deferral
SELF-CANCELLING, not a test bug.
"""

from __future__ import annotations

from pathlib import Path

from services.engine.procedures.orchestrator import _is_at2_procedure
from services.engine.procedures.spec import Procedure, load_procedures_file

_RETRIGGER_N = 3
"""The distinct-signature count at which the AT-2-generator deferral self-cancels (ADR-0025 D7;
re-armed here by PLAN-0074 after the N=2 firing was answered — see the module docstring). At a
THIRD signature the per-instance types are a Rule-of-Three violation and the extraction is due."""

_BASELINE_SIGNATURES = [
    ("procurement", ("scored_rule", "rule_gate", "doa_tier")),
    ("supply_chain", ("scored_rule", "rule_gate", "severity_tier")),
]
"""The N=2 baseline the D7 re-evaluation was performed against (PLAN-0074 SD-3): the same three
gates composed twice, but on a MONEY authority and a NON-MONEY one. Sorted by vertical."""


def _at2_gate_kinds(procedure: Procedure) -> tuple[str, ...]:
    """The AT-2 gate kinds this procedure composes, in step order — the shape half of its
    signature. Read off the TYPED ``governance_content`` (the authoritative field), never the
    non-authoritative facet prose."""
    return tuple(
        step.governance_content.kind
        for step in procedure.steps
        if step.governance_content is not None
    )


def _distinct_at2_signatures() -> list[tuple[str, tuple[str, ...]]]:
    """Every distinct AT-2 signature shipped, sorted. Globs only ``verticals/*`` (never the
    ``.claude/worktrees`` copies), and dedups trigger variants of one signature (see module
    docstring). A procedure that :func:`_is_at2_procedure` calls AT-2 but that carries no typed
    governance content (an SoD-only procedure) keys to an empty gate tuple — counted, but never
    silently merged with a gate-bearing one."""
    signatures: set[tuple[str, tuple[str, ...]]] = set()
    for path in sorted(Path("verticals").glob("*/procedures.yaml")):
        vertical = path.parent.name
        spec = load_procedures_file(path, vertical=vertical)
        for procedure in spec.procedures:
            if _is_at2_procedure(procedure):
                signatures.add((vertical, _at2_gate_kinds(procedure)))
    return sorted(signatures)


def test_trigger_variants_are_one_signature_not_three() -> None:
    """The counting trap, pinned: procurement ships THREE AT-2 procedure ENTRIES (manual +
    schedule- + event-triggered) that are ONE governance signature. A per-entry count would read
    N>=3 and false-fire the re-trigger below on a vertical that added no new AT-2 knowledge."""
    spec = load_procedures_file(
        Path("verticals/procurement/procedures.yaml"), vertical="procurement"
    )
    at2_entries = [p for p in spec.procedures if _is_at2_procedure(p)]
    assert len(at2_entries) == 3, "procurement's three AT-2 entries (manual / schedule / event)"

    signatures = {("procurement", _at2_gate_kinds(p)) for p in at2_entries}
    assert signatures == {("procurement", ("scored_rule", "rule_gate", "doa_tier"))}


def test_the_two_signatures_differ_in_their_authority_gate() -> None:
    """WHY N=2 is a real second data point (and not a copy): both signatures compose the same three
    gates, but the AUTHORITY gate differs — ``doa_tier`` (a Decimal spend) vs ``severity_tier`` (an
    ordinal excursion severity). That difference is the whole Rule-of-Three argument: a generator
    extracted from procurement alone would have baked "authority means money" into the engine."""
    by_vertical = dict(_distinct_at2_signatures())

    assert by_vertical["procurement"][-1] == "doa_tier"
    assert by_vertical["supply_chain"][-1] == "severity_tier"
    # everything upstream of the authority gate generalised unchanged
    assert by_vertical["procurement"][:-1] == by_vertical["supply_chain"][:-1]


def test_at2_generator_deferral_retrigger() -> None:
    """AC-11 (ADR-0025 D7 / ADR-0031 OQ-4): the AT-2-generator re-trigger, RE-ARMED at N=3 after
    PLAN-0074 answered the N=2 firing (module docstring: generator stays deferred + abstaining, D2
    types stay instance-scoped, the triangulation findings feed the follow-on extraction PLAN).
    FAILS the moment a THIRD distinct signature ships."""
    signatures = _distinct_at2_signatures()
    assert signatures == _BASELINE_SIGNATURES, (
        "the AT-2 signature baseline moved — the D7 re-evaluation recorded in this module's "
        f"docstring was performed against {_BASELINE_SIGNATURES}, so it no longer holds. Re-argue "
        "it (do not just update this list)."
    )
    assert len(signatures) < _RETRIGGER_N, (
        f"ADR-0025 D7 N>={_RETRIGGER_N} RE-TRIGGER FIRED: {len(signatures)} distinct AT-2 "
        f"signatures now ship ({signatures}) — the AT-2-generator deferral was already "
        "re-evaluated "
        "ONCE at N=2 (PLAN-0074 SD-3: generator stays deferred + abstaining because the authority "
        "quantity, the criterion vocabulary and the provenance policy all proved per-instance). A "
        "THIRD hand-authored signature exhausts that answer under Rule-of-Three (ADR-006 D4): "
        "extract the generic AT-2 framework / the ADR-0031 D3 gate-plugin seam, or re-argue the "
        "deferral in a follow-on ADR — then update this marker. This failure is the deferral "
        "SELF-CANCELLING, not a test bug."
    )
