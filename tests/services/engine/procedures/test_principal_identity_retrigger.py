"""AC-10 (re-trigger half; PLAN-0044 A1b Step 2) — the OQ-6 N>=2 shared-``Person`` re-trigger.

The **enforceable, self-cancelling deferral** marker (mirroring ADR-0025 D7's AT-2-generator
re-trigger). ADR-0026 OQ-6=(b) keeps a **per-vertical** ``Person`` while only ONE vertical needs
principal identity (N=1); genericizing it to a shared/core object is DEFERRED — but the deferral is
not a silent ``# TODO`` that rots under delivery pressure. This module is the CI trip-wire:

* it counts the verticals whose ``procedures.yaml`` ships human ``principals`` (Person identity),
  and
* it **FAILS when a SECOND vertical ships principals (N>=2)** — forcing a re-evaluation of the
  shared/core ``Person`` extraction rather than letting a second per-vertical copy accrete silently.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8). The failing assertion is the deferral
self-cancelling, NOT a test bug: when it fires, extract the shared ``Person`` model (or re-confirm
the per-vertical shape in a follow-on ADR) and update this marker to the new N.
"""

from __future__ import annotations

from pathlib import Path

from services.engine.procedures.spec import load_procedures_file, procedures_path

_RETRIGGER_N = 2
"""The N at which the shared/core ``Person`` extraction deferral self-cancels (ADR-0026 OQ-6=(b) /
PLAN-0044 AC-10). While fewer than this many verticals ship principals, the per-vertical shape
stands; at N>=2 the trip-wire fires."""


def _verticals_shipping_principals() -> list[str]:
    """Every top-level vertical whose ``procedures.yaml`` ships human principals (Person identity),
    sorted. Globs only ``verticals/*`` (never the ``.claude/worktrees`` copies)."""
    shipping: list[str] = []
    for path in sorted(Path("verticals").glob("*/procedures.yaml")):
        vertical = path.parent.name
        spec = load_procedures_file(path, vertical=vertical)
        if spec.principals:
            shipping.append(vertical)
    return shipping


def test_procurement_is_the_sole_principal_vertical_today() -> None:
    """The N=1 state the deferral rests on: procurement is the only vertical shipping principals
    (its emergency-sourcing SoD run-check resolves against them). This documents the baseline the
    re-trigger guards — if another vertical adds principals, this and the trip-wire below both
    move."""
    assert _verticals_shipping_principals() == ["procurement"]


def test_person_extraction_deferral_retrigger() -> None:
    """AC-10 (mirroring ADR-0025 D7): the OQ-6 N>=2 re-trigger. FAILS the moment a SECOND vertical
    ships principals — the enforceable trip-wire that makes the shared/core ``Person`` extraction
    deferral self-cancelling (ADR-0026 OQ-6=(b) / PLAN-0044 AC-10)."""
    shipping = _verticals_shipping_principals()
    assert len(shipping) < _RETRIGGER_N, (
        f"OQ-6 N>={_RETRIGGER_N} RE-TRIGGER FIRED: {len(shipping)} verticals now ship principals "
        f"({shipping}) — re-evaluate the shared/core Person extraction deferral (ADR-0026 OQ-6=(b) "
        f"/ PLAN-0044 AC-10). A per-vertical Person was the N=1 shape; at N>={_RETRIGGER_N} the "
        "core/shared extraction is due. This failure is the deferral SELF-CANCELLING, not a test "
        "bug: extract the shared Person model (or re-confirm the per-vertical shape in a follow-on "
        "ADR), then update this marker to the new N."
    )


def test_procurement_principals_actually_load() -> None:
    """Guard the counter itself: procurement's principals are real, resolvable identities (so the
    trip-wire counts a genuine identity-bearing vertical, not an empty ``principals:`` key)."""
    spec = load_procedures_file(procedures_path("procurement"), vertical="procurement")
    assert len(spec.principals) >= 2  # a requester + at least one approver (the SoD floor)
    assert all(p.person_id and p.roles for p in spec.principals)
