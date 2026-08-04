"""PLAN-0101 Step 1.3 / AC-4 — ``tenant_id`` must never reach the governance pin.

ADR-0035 D7 states the tenant key is "a plain settings field, **not** part of the
governance pin — it must never enter the resolved-procedures hash". That sentence is
a *claim about behaviour*, and this module is its oracle.

**Why this module exists even though a top-level tripwire already does.**
``test_derivation_pin.py::test_every_snapshot_carries_exactly_the_declared_surface``
already asserts ``set(build_governance_snapshot(procedure)) == {"procedure_id",
"separation_of_duties", "steps"}`` across every vertical, so a **top-level**
``tenant_id`` key would already redden. What that guard cannot see is a tenant value
reaching the hash through a **nested** path (a per-step key) or through a live read of
``settings`` at hash time — which is exactly the shape SD-1's stamping mechanism could
introduce by accident. This module covers that hole and deliberately does not restate
the top-level assertion.

**The three legs.** Two are behavioural — the hash must not move with the tenant value,
and the value must not appear in the snapshot. The third is structural: no
tenant-shaped KEY at any depth, which is the only one that catches a constant
tenant-flavoured key (``"tenant_scoped": True``) whose value never equals the slug.
Measured: a step-level leak reddens all three here while ``test_derivation_pin.py``
stays fully green, so the hole this module fills is real, not assumed.

**Why the monkeypatch targets the settings OBJECT, not the environment.**
``settings`` is a module-level singleton constructed at import. Setting ``TENANT_ID``
in ``os.environ`` after import changes nothing the running code reads, so an
env-var-based test would pass *whether or not* the coupling exists — vacuous by
construction. ``monkeypatch.setattr(settings, "tenant_id", ...)`` mutates what any
caller of ``settings.tenant_id`` actually sees (the repo-wide idiom, e.g.
``tests/conftest.py:85``).

Pure + offline (CLAUDE.md §8 — the offline oracle is the gate): no DB, no LLM, no MS-S1.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from services.api.config import settings
from services.engine.procedures.governance_pin import governance_pin_for
from services.engine.procedures.spec import load_procedures

_VERTICALS_DIR = Path(__file__).parents[4] / "verticals"

# Discovered, not hardcoded: a vertical added later is covered automatically rather
# than silently escaping the guard. Underscore-prefixed dirs (`_template`) are
# scaffolding, not shipped verticals.
_ALL_VERTICALS = sorted(
    p.parent.name
    for p in _VERTICALS_DIR.glob("*/procedures.yaml")
    if not p.parent.name.startswith("_")
)

# Two values that share no substring, so a partial leak (e.g. a truncated or hashed
# fragment landing in the snapshot) still changes the digest.
_TENANT_A = "default"
_TENANT_B = "acme-industrial"


def test_the_vertical_census_is_not_empty() -> None:
    """Fixture guard: an empty census would make every test below vacuously pass."""
    assert _ALL_VERTICALS, f"no verticals discovered under {_VERTICALS_DIR} — the glob moved"


@pytest.mark.parametrize("vertical", _ALL_VERTICALS)
def test_tenant_id_never_changes_the_governance_hash(
    vertical: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADR-0035 D7, at FULL depth: the resolved-procedures hash is byte-identical
    under two different tenant values.

    This is the leg the top-level surface tripwire cannot cover — it catches a
    ``tenant_id`` folded in at ANY nesting depth, and a live ``settings`` read at hash
    time, because both would make the digest move with the value.
    """
    spec = load_procedures(vertical)
    assert spec.procedures, f"{vertical} declares no procedures — the fixture moved"

    monkeypatch.setattr(settings, "tenant_id", _TENANT_A)
    hashes_a = {p.procedure_id: governance_pin_for(p)[1] for p in spec.procedures}

    monkeypatch.setattr(settings, "tenant_id", _TENANT_B)
    hashes_b = {p.procedure_id: governance_pin_for(p)[1] for p in spec.procedures}

    assert hashes_a == hashes_b, (
        f"{vertical}: the governance hash moved when tenant_id changed "
        f"{_TENANT_A!r} -> {_TENANT_B!r} — the tenant key has leaked into the "
        "resolved-procedures pin (ADR-0035 D7 forbids it)"
    )


@pytest.mark.parametrize("vertical", _ALL_VERTICALS)
def test_no_snapshot_value_anywhere_carries_the_tenant_value(
    vertical: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Belt-and-braces on the same claim, by SUBSTRING rather than by digest.

    A value can reach the snapshot without moving the hash if it is folded in
    constantly (e.g. a hardcoded ``"default"``). Serialising the whole snapshot and
    searching for the distinctive tenant value catches that shape too.
    """
    monkeypatch.setattr(settings, "tenant_id", _TENANT_B)
    spec = load_procedures(vertical)

    for procedure in spec.procedures:
        snapshot, _ = governance_pin_for(procedure)
        assert _TENANT_B not in repr(snapshot), (
            f"{vertical}/{procedure.procedure_id}: the tenant value appears inside the "
            "governance snapshot (ADR-0035 D7 forbids it)"
        )


# ---------------------------------------------------------------------------
# The structural leg — no tenant-SHAPED key, at any depth
# ---------------------------------------------------------------------------

_TENANT_SHAPED = re.compile(r"tenant", re.IGNORECASE)


def _all_keys(node: Any) -> set[str]:
    """Every mapping key anywhere in a nested JSON-ish structure."""
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(str(key))
            keys |= _all_keys(value)
    elif isinstance(node, list):
        for item in node:
            keys |= _all_keys(item)
    return keys


@pytest.mark.parametrize("vertical", _ALL_VERTICALS)
def test_no_snapshot_key_anywhere_is_tenant_shaped(vertical: str) -> None:
    """The leg the two behavioural tests above cannot cover.

    Both of those key off the tenant VALUE — one via the digest, one via substring.
    A *constant* tenant-flavoured key whose value never equals the slug slips past
    both: a step gaining ``"tenant_scoped": True`` moves the hash exactly once, then
    sits still forever, so "change the tenant, the hash must not move" stays green.

    That single silent move is the damage: every in-flight run refuses at resume
    (``assert_governance_pin`` fails closed). It happened deliberately once, at
    PLAN-0078 PR-5, and was made explicit by
    ``test_derivation_pin.py::test_every_snapshot_carries_exactly_the_declared_surface``
    — but that guard only watches the TOP level, so a nested tenant key still moves
    the hash unwatched.

    Scoped to tenant-shaped NAMES rather than to the snapshot's whole shape (Cray's
    call, PLAN-0101 Step 1.3): a step-level set-equality assertion would catch more,
    but it would be guarding "the snapshot must not grow silently" — a broader,
    different concern that belongs beside the top-level tripwire, not inside a module
    named for the tenant key. Here, a legitimate new key (as ``transform`` was in
    PLAN-0077) costs this test nothing.
    """
    spec = load_procedures(vertical)
    assert spec.procedures, f"{vertical} declares no procedures — the fixture moved"

    for procedure in spec.procedures:
        snapshot, _ = governance_pin_for(procedure)
        offenders = sorted(k for k in _all_keys(snapshot) if _TENANT_SHAPED.search(k))
        assert not offenders, (
            f"{vertical}/{procedure.procedure_id}: tenant-shaped key(s) {offenders} in the "
            "governance snapshot — ADR-0035 D7 keeps the tenant key out of the "
            "resolved-procedures pin entirely"
        )
