"""PLAN-0079 AC-2 (half i) — the governed-credit HERO tracker is load-bearing by MECHANISM.

PLAN-0079 is a STANDING TRACKING PLAN (it builds nothing). It exists because the
building_materials governed-credit hero lived ONLY in volatile, rotated surfaces (a STATUS
``next_action`` + a Current Focus block) with **no durable home** — no Active TODO, no PLAN,
no ADR build item — and because the session-137 handoff mis-scoped it as a *cheap follow-on*,
a claim resting on a stale ``N=1`` comment that PR #767 had to kill. A tracker's mere presence
in a directory is a PASSIVE tripwire (the s133 panel finding, Cray-ratified: "location !=
tripwire; failing tests are the real anti-rot"). This guard converts PLAN-0079's location
anchor into a FAILING BUILD:

  (i) the PLAN lives in ACTIVE ``docs/plans/`` (never ``docs/plans/done/``) while the hero is
      neither built nor Cray-declined — a premature archive-to-``done/`` mislabels an open,
      un-commissioned item as *resolved*, turning this RED.

AC-2's SECOND half — ``docs/STATUS.md`` carries a pointer naming ``PLAN-0079`` — is
**deliberately not here yet**: #769 (the session-138 STATUS reconcile) is open, so STATUS is a
blocked file and the pointer lands in the first post-#769 STATUS PR (PLAN-0079 AC-4 / SD-3).
That assertion arms in THAT PR, alongside the pointer it guards. A guard born RED is a broken
tripwire, not a safeguard.

Retiring the tracker is Step T3: when the hero is **built** (its build PLAN merged) or Cray
**explicitly declines** it, PLAN-0079 moves to ``done/`` AND this guard is deleted in that SAME
PLAN/PR — its RED on a premature archive is the intended forcing function, not a regression to
route around.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8): reads one repo path, anchored on
``__file__`` (not the CWD). Mirrors the exemplar
``tests/services/engine/procedures/test_at2_followon_tracking_guard.py`` (PLAN-0076 AC-6).
"""

from __future__ import annotations

from pathlib import Path

# tests/services/engine/procedures/<this file> -> parents[4] is the repo root (CWD-independent).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_PLAN_REL = "docs/plans/0079-building-materials-governed-credit-hero-tracking.md"


def test_plan_0079_lives_in_active_plans_not_done() -> None:
    """The tracker is in ACTIVE ``docs/plans/``, never ``done/``, while the governed-credit hero
    is neither built nor declined. A premature ``git mv`` to ``done/`` mislabels an
    un-commissioned item as resolved — the exact rot PLAN-0079 was filed to prevent — and buries
    its honest cost with it; this turns the build RED so the archive is a conscious act
    (Step T3)."""
    active = _REPO_ROOT / _PLAN_REL
    archived = _REPO_ROOT / "docs" / "plans" / "done" / Path(_PLAN_REL).name
    assert active.is_file(), (
        f"PLAN-0079 tracking stub is missing from active '{_PLAN_REL}'. If it was archived to "
        "docs/plans/done/ while the building_materials governed-credit hero is neither built nor "
        "explicitly declined by Cray, that mislabels open work as resolved AND buries the hero's "
        "honest cost (it is AT-2 signature #3 -> re-arms test_at2_signature_retrigger.py -> "
        "obligates the ADR-0025 D7 re-evaluation; it is never a config-cost item, ADR-0032 D6). "
        "Retire the tracker only via PLAN-0079 Step T3, deleting THIS guard in the same PLAN/PR."
    )
    assert not archived.is_file(), (
        "PLAN-0079 appears under docs/plans/done/ — a tracking stub in done/ reads as 'resolved' "
        "while the hero is un-commissioned. See PLAN-0079 Step T3 + this guard's docstring."
    )
