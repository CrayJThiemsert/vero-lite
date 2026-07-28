"""PLAN-0096 AC-2 — the cross-vertical governance-drift tripwire.

PLAN-0096 edits ONE vertical (fleet_maintenance) but reaches shared surfaces: the
authored spec grammar in Step 1, and — from Step 5 — the ``EmergencyWaiverPolicy``
model itself. The measured failure class this guards is not hypothetical: a new
governance field that serializes ALWAYS (even as ``None``) changes the resolved
governance snapshot of EVERY vertical, which flips every ``PipelineRun`` config hash,
which makes every in-flight run refuse at resume (``governance_pin.py`` fails CLOSED on
a mismatch — by design). ADR-0034 D6 therefore requires new pins to be
only-when-supplied, and this module is the test that notices when one is not.

**What it pins.** The resolved governance snapshot hash of every procedure in the five
non-fleet verticals, against a committed fixture. Nothing here re-implements the
snapshot — it calls the SAME ``governance_pin_for`` the orchestrator pins runs with, so
a change in what governance MEANS is caught, not just a change in this file's idea of it.

**Why fleet_maintenance is excluded.** Its hash SHOULD change — Step 1 rewrites its
ladder on purpose. Pinning it here would either block the intended work or, worse,
train whoever hits the failure to regenerate the fixture reflexively, which is exactly
the habit that would make the other five pins worthless. Fleet's own numbers are pinned
by ``test_partner_ladder_boundaries.py`` and the hero suite instead.

**On regenerating the fixture.** If a diff legitimately changes a guarded vertical's
governance, the fixture is updated in the SAME commit as that change, with the reason in
the commit body. Regenerating it to make a red test green is the failure mode this file
exists to prevent — the pin is worth exactly as much as the discipline behind it.

Offline + deterministic (CLAUDE.md §8): YAML load + sha256, no DB, no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.engine.procedures.governance_pin import governance_pin_for
from services.engine.procedures.spec import load_procedures

_FIXTURE = Path(__file__).parent / "fixtures" / "governance_config_hashes.json"
_VERTICALS_DIR = Path("verticals")

# The five AC-2 names. fleet_maintenance is deliberately absent — see the module docstring.
_GUARDED = ("aquaculture", "building_materials", "energy", "procurement", "supply_chain")


def _hashes(vertical: str) -> dict[str, str]:
    """``{procedure_id: governance_hash}`` for one vertical, via the engine's own pin."""
    spec = load_procedures(vertical)
    return {p.procedure_id: governance_pin_for(p)[1] for p in spec.procedures}


def _expected() -> dict[str, dict[str, str]]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("vertical", _GUARDED)
def test_guarded_vertical_governance_hash_is_unchanged(vertical: str) -> None:
    """AC-2: byte-identical resolved governance for every untouched vertical.

    Parametrized per vertical rather than asserted as one dict so a failure NAMES the
    vertical that drifted — the first question on a red pin is always "which one", and a
    single whole-dict assertion answers it with a wall of sha256."""
    assert _hashes(vertical) == _expected()[vertical]


def test_the_guard_covers_every_non_fleet_vertical_that_has_procedures() -> None:
    """The set-equality tripwire — without it this whole module rots quietly.

    A pin that lists five names by hand protects five verticals forever, including the
    day a SIXTH ships and silently escapes the guard. Deriving the expected set from the
    filesystem means a new vertical fails HERE, at a test whose message says what to do,
    instead of shipping an unnoticed governance-hash change months later."""
    on_disk = {
        path.parent.name
        for path in _VERTICALS_DIR.glob("*/procedures.yaml")
        if not path.parent.name.startswith("_")
    }
    assert on_disk - {"fleet_maintenance"} == set(_GUARDED)


def test_the_fixture_names_exactly_the_guarded_verticals() -> None:
    """A fixture carrying a stale vertical (or missing a guarded one) would make the
    parametrized test above pass vacuously for whatever it happens to contain."""
    assert set(_expected()) == set(_GUARDED)
    for vertical in _GUARDED:
        assert _expected()[vertical], f"{vertical} pins no procedure at all"
