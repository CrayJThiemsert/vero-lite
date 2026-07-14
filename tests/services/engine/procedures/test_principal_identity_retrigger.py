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

**IT FIRED — and this is the honest record of the answer (PLAN-0074 AC-12 / SD-4, session 131).**
``supply_chain`` shipped ``principals`` with the 2nd AT-2 signature (the cold-chain disposition's
severity-tier gate needs an SoD-resolvable requester + approver), taking N from one vertical to
TWO. Per the marker's own instruction the deferral was RE-EVALUATED rather than silently re-armed:

* **Resolution: re-confirm the per-vertical ``Person`` shape; file the shared/core extraction as a
  FOLLOW-ON** (PLAN-0074 SD-4). The two rosters are genuinely independent (procurement's DOA roles
  vs supply_chain's quality roles) and nothing yet reads a Person ACROSS verticals — so extraction
  buys no correctness today, while doing it inside a gate-kind PLAN would couple an identity-model
  refactor to an unrelated blast radius. The evidence FOR extraction (two hand-copied Person
  blocks, two SoD wirings) is now recorded, not lost.
* The trip-wire is therefore **re-armed at the next threshold** (below), where a THIRD copy would
  make the per-vertical shape indefensible under Rule-of-Three (ADR-006 D4).

The baseline below is the state that re-evaluation was performed against — it is not a rubber stamp:
if a vertical is added or dropped, the count assertion fails and the question is asked again.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.engine.procedures.spec import load_procedures_file, procedures_path

_RETRIGGER_N = 3
"""The N at which the shared/core ``Person`` extraction deferral self-cancels AGAIN (ADR-0026
OQ-6=(b) / PLAN-0044 AC-10; re-armed by PLAN-0074 AC-12 after the N=2 firing was answered — see
the module docstring). At a THIRD principal-bearing vertical the per-vertical copy is a
Rule-of-Three violation and the shared/core extraction is due, not deferrable."""

_PRINCIPAL_VERTICALS = ["procurement", "supply_chain"]
"""The N=2 baseline the re-evaluation was performed against (PLAN-0074 AC-12): procurement (the 1st
AT-2 signature, DOA/money authority) and supply_chain (the 2nd, severity/non-money authority)."""


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


def test_the_principal_bearing_verticals_are_the_reevaluated_baseline() -> None:
    """The N=2 state the RE-EVALUATED deferral rests on (PLAN-0074 AC-12): procurement (money
    authority) and supply_chain (severity authority) are the two principal-bearing verticals, and
    the shared/core ``Person`` extraction was answered against exactly that pair (module docstring).
    A third vertical — or a dropped one — invalidates that answer and must re-open the question."""
    assert _verticals_shipping_principals() == _PRINCIPAL_VERTICALS


def test_person_extraction_deferral_retrigger() -> None:
    """AC-10 (mirroring ADR-0025 D7): the OQ-6 re-trigger, RE-ARMED at N=3 (PLAN-0074 AC-12 — the
    N=2 firing was answered: per-vertical shape re-confirmed, shared extraction filed as a
    follow-on). FAILS the moment a THIRD vertical ships principals — at which point a per-vertical
    copy is a Rule-of-Three violation (ADR-006 D4) and the extraction is due, not deferrable."""
    shipping = _verticals_shipping_principals()
    assert len(shipping) < _RETRIGGER_N, (
        f"OQ-6 N>={_RETRIGGER_N} RE-TRIGGER FIRED: {len(shipping)} verticals now ship principals "
        f"({shipping}) — the shared/core Person extraction deferral was already re-evaluated ONCE "
        f"at N=2 (PLAN-0074 AC-12: per-vertical shape re-confirmed, extraction filed as a "
        "follow-on). A THIRD copy exhausts that answer: extract the shared Person model (ADR-006 "
        "D4 Rule of Three), then update this marker. This failure is the deferral SELF-CANCELLING, "
        "not a test bug."
    )


@pytest.mark.parametrize("vertical", _PRINCIPAL_VERTICALS)
def test_principals_actually_load(vertical: str) -> None:
    """Guard the counter itself: each counted vertical's principals are real, resolvable identities
    (so the trip-wire counts genuine identity-bearing verticals, not an empty ``principals:`` key).
    The SoD floor is a requester + at least one approver — both AT-2 signatures resolve their gate
    against these rosters."""
    spec = load_procedures_file(procedures_path(vertical), vertical=vertical)
    assert len(spec.principals) >= 2  # a requester + at least one approver (the SoD floor)
    assert all(p.person_id and p.roles for p in spec.principals)
