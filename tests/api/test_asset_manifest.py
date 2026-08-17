"""The asset manifest bijection (PLAN-0107 AC-2, Phase A / ① instruments).

Today a renamed or deleted asset 404s **silently**: the page half-boots, and only
3 of the 21 shipped scripts are string-checked anywhere
(``test_static_ui.py``, ``test_export_cover_ui_contract.py``,
``test_view_hero_fleet_ui_contract.py``). Nothing reads the other eighteen, and
nothing notices a file on disk that no page references.

**The bijection IS the anti-vacuity control — deliberately, instead of a floor
constant.** Measured 2026-08-17: ``index.html`` carries 21 ``<script src>``
references and 4 stylesheet links; ``assets/`` holds exactly 21 ``.js`` and 4
``.css`` files, a perfect bijection with zero orphans. A floor
(``assert len(refs) >= 20``) would pass over a dropped reference and its misfire
remedy is editing the number — the guard-erosion ratchet PLAN-0107 exists to
stop. A bijection has no number to erode: a dropped reference reddens the
reverse direction and an orphaned file reddens it too, each on its own.

Two null-selector traps are closed explicitly, because an empty match set makes
every ``for``-loop assertion below vacuously true (the PLAN-0100 trap,
``docs/plans/done/0100-exposure-published-demo-surface.md``):

* the reference parse asserts it matched at least one of each kind, so an
  emptied or unparseable ``index.html`` cannot pass by matching nothing;
* the disk enumeration asserts it is non-empty, so a moved ``assets/``
  directory cannot pass by enumerating nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

from services.api import main

#: Assets deliberately shipped without an ``index.html`` reference. Each entry
#: needs a written reason — an unexplained orphan is the defect this test exists
#: to surface, so the dict must never become a dumping ground.
#:
#: Empty today, and that is the measured truth rather than an untested default:
#: every one of the 21 JS and 4 CSS files on disk is referenced, including
#: ``mock.js`` and ``gate-fixture.js`` (both are loaded by ``index.html``, not
#: dead demo scaffolding as their names suggest).
_UNREFERENCED_ASSETS: dict[str, str] = {}

_STATIC = Path(main.__file__).resolve().parent / "static"
_INDEX = _STATIC / "index.html"
_ASSETS = _STATIC / "assets"

#: ``src="assets/app.js?v=c50"`` / ``href="assets/theme.css?v=c50"`` — the
#: ``?v=`` cache-busting token is stripped, it is not part of the filename.
_REF = re.compile(r"""(?:src|href)=["']assets/([^"'?]+)(?:\?[^"']*)?["']""")


def _referenced() -> set[str]:
    """Every ``assets/`` filename ``index.html`` references, ``?v=`` stripped."""
    return set(_REF.findall(_INDEX.read_text(encoding="utf-8")))


def _on_disk(suffix: str) -> set[str]:
    return {p.name for p in _ASSETS.glob(f"*{suffix}")}


def test_the_parse_finds_references_of_both_kinds() -> None:
    """Anti-vacuity: an emptied index.html must not pass by matching nothing.

    Every other assertion in this module iterates over one of these sets, so an
    empty parse would turn all of them green. This is the positive control that
    the instrument reads the artifact at all.
    """
    assert _INDEX.exists(), f"index.html is missing at {_INDEX}"
    refs = _referenced()
    assert any(name.endswith(".js") for name in refs), (
        "index.html referenced no assets/*.js at all — the parse matched nothing, "
        "so every downstream assertion in this module would be vacuously true"
    )
    assert any(
        name.endswith(".css") for name in refs
    ), "index.html referenced no assets/*.css at all — see above"


def test_the_asset_directory_is_not_empty() -> None:
    """Anti-vacuity for the reverse direction: a moved assets/ must go RED."""
    assert _ASSETS.is_dir(), f"assets/ is missing at {_ASSETS}"
    assert _on_disk(".js"), "assets/ holds no .js files — the reverse check would be vacuous"
    assert _on_disk(".css"), "assets/ holds no .css files — see above"


def test_every_reference_resolves_to_a_file_on_disk() -> None:
    """Forward direction: a renamed or deleted asset must not 404 silently."""
    dangling = sorted(name for name in _referenced() if not (_ASSETS / name).is_file())
    assert not dangling, (
        f"index.html references {len(dangling)} asset(s) that do not exist on disk: "
        f"{dangling}. The browser 404s these silently and the page half-boots. "
        "Fix the reference, or restore the file."
    )


def test_every_asset_on_disk_is_referenced_or_exempt() -> None:
    """Reverse direction: an orphaned asset is dead weight shipped to every visitor.

    An orphan is not automatically a bug — but it must be a DECISION, recorded in
    ``_UNREFERENCED_ASSETS`` with its reason, not a silent leftover.
    """
    referenced = _referenced()
    orphans = sorted(
        name
        for name in _on_disk(".js") | _on_disk(".css")
        if name not in referenced and name not in _UNREFERENCED_ASSETS
    )
    assert not orphans, (
        f"{len(orphans)} asset(s) on disk are referenced by nothing: {orphans}. "
        "Either reference them from index.html, delete them, or add an entry to "
        "_UNREFERENCED_ASSETS with the reason they ship unreferenced."
    )


def test_the_exemption_dict_carries_no_stale_entry() -> None:
    """An exemption for an asset that is gone, or now referenced, is a lie.

    Without this the dict silently accumulates entries that describe nothing —
    exactly how an allowlist stops meaning anything.
    """
    referenced = _referenced()
    on_disk = _on_disk(".js") | _on_disk(".css")
    stale = sorted(
        name for name in _UNREFERENCED_ASSETS if name not in on_disk or name in referenced
    )
    assert not stale, (
        f"_UNREFERENCED_ASSETS holds {len(stale)} entry/entries that no longer "
        f"describe an unreferenced on-disk asset: {stale}. Remove them."
    )
