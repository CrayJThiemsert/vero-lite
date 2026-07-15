"""PLAN-0076 AC-6 (s133 panel — the anti-rot review, Cray-ratified enhancement) — the
tracking stub is load-bearing by MECHANISM, not by convention.

PLAN-0076 is a STANDING TRACKING PLAN (it builds nothing). The s133 specialist review found
that a PLAN's mere presence in a directory is a PASSIVE tripwire — read, never executed —
exactly the shape that let the ADR-0031 OQ-4 marker rot (a promise nothing FAILED on, caught
only by a lucky manual grep). This guard converts two of PLAN-0076's anti-rot anchors into a
FAILING BUILD:

  (i)  the PLAN lives in ACTIVE ``docs/plans/`` (never ``docs/plans/done/``) while its tracked
       deferrals are open — a premature archive-to-``done/`` (which would mislabel open work as
       *resolved*) turns this RED;
  (ii) ``docs/STATUS.md`` still carries the Active-TODO pointer naming ``PLAN-0076`` (AC-5) —
       pruning that pointer (STATUS is volatile + window-rotated, the softest tripwire) turns
       this RED.

Retiring the tracker is Step T3: when BOTH deferrals are built (each via its own PLAN) or Cray
re-adjudicates, the PLAN moves to ``done/`` AND this guard is deleted in that SAME PLAN — its
RED on a premature archive is the intended forcing function, not a regression to route around.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8): reads two repo files, anchored on
``__file__`` (not the CWD). The static-guard sibling is
``tests/services/db/test_load_run_ordering_guard.py``.
"""

from __future__ import annotations

from pathlib import Path

# tests/services/engine/procedures/<this file> -> parents[4] is the repo root (CWD-independent).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_PLAN_REL = "docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md"


def test_plan_0076_lives_in_active_plans_not_done() -> None:
    """The tracker is in ACTIVE ``docs/plans/``, never ``done/``, while its deferrals are open.
    A premature ``git mv`` to ``done/`` mislabels open work as resolved (the OQ-4 failure in a
    new costume); this turns the build RED so the archive is a conscious act (Step T3)."""
    active = _REPO_ROOT / _PLAN_REL
    archived = _REPO_ROOT / "docs" / "plans" / "done" / Path(_PLAN_REL).name
    assert active.is_file(), (
        f"PLAN-0076 tracking stub is missing from active '{_PLAN_REL}'. If it was archived to "
        "docs/plans/done/ while F-FACTORY (the ADR-0031 D3 gate-plugin seam) or F-PIN's "
        "remainder is still open, that mislabels open work as resolved. Retire the tracker only "
        "via Step T3 (both deferrals built / Cray re-adjudicates), deleting THIS guard in the "
        "same PLAN."
    )
    assert not archived.is_file(), (
        "PLAN-0076 appears under docs/plans/done/ — a tracking stub in done/ reads as 'resolved' "
        "while its deferrals are open. See PLAN-0076 Step T3 + this guard's docstring."
    )


def test_status_still_points_at_plan_0076() -> None:
    """The STATUS Active-TODO pointer (AC-5) still names PLAN-0076. STATUS is volatile +
    window-rotated (the softest of the three tripwires), so a scribe pass could silently drop
    the line — this makes the pointer load-bearing."""
    status = (_REPO_ROOT / "docs" / "STATUS.md").read_text(encoding="utf-8")
    assert "PLAN-0076" in status, (
        "docs/STATUS.md no longer references PLAN-0076 — the Active-TODO pointer to the F-PIN / "
        "gate-seam tracker (AC-5) was pruned. Restore it, or retire the tracker via PLAN-0076 "
        "Step T3 (and delete this guard in that same PLAN)."
    )
