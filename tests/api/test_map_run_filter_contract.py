"""Tab A's three-mode run-marker filter matches its ruled buckets (PLAN-0110 AC-2/3/9).

The repo has no build step and no JS test runner (``docs/conventions/ui.md`` §5), so a
CI tripwire for the UI has to be a Python test that reads the shipped source. This
module reads ``services/api/static/assets/view-map.js`` — the ARTIFACT, never a
restatement of it — following ``test_css_class_contract``'s precedent.

**What is under guard here, and why each half needs guarding.**

*The default* (AC-2) is a ratified ruling that this PLAN deliberately did NOT reopen.
PLAN-0084 SD-C (Cray, typed, 2026-07-20 s155) fixed the in-flight marker at
``{waiting_human, running}`` and said "never terminal states". PLAN-0110 layers two
opt-in modes on top; the thing that must not move is the view a visitor lands on. A
widened default would change what the demo says at first paint without anyone deciding
to — which is the exact shape this guard exists to catch.

*The buckets* (AC-3) are checked against the **Python enum**, imported rather than
copied. ``PipelineRunStatus`` is the source of truth for what statuses exist; a copied
list here would agree with itself while the JS silently stopped covering a sixth
status. With the import, a new status reddens this guard instead of landing in no
bucket at all and vanishing from the "all" mode that promises to show everything.

**What this cannot prove.** It is a source contract, not a rendering test: it shows the
JS declares these buckets and wires them to these modes. That the ring actually paints,
that the mode tabs are clickable, and that a marker lands on the right node are browser
observations — evidence, not the gate.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pytest

from services.engine.procedures.runs import PipelineRunStatus
from tests.api.js_source import strip_js_comments

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATIC = _REPO_ROOT / "services" / "api" / "static"
_VIEW_MAP = _STATIC / "assets" / "view-map.js"
_INDEX_HTML = _STATIC / "index.html"

#: The ``?v=`` counter ``view-map.js`` carried BEFORE PLAN-0110 Step 2, measured on
#: disk at authoring time. A per-FILE counter, not a build number — differing values
#: across assets are normal and expected (``index.html`` ships several).
_CACHE_BUST_BASELINE = 39

#: The mode the map must open on. Named here as the ruled OUTCOME (PLAN-0084 SD-C),
#: so the assertion below reads as "the default is the in-flight mode" rather than as
#: "the default is whatever the file says".
_DEFAULT_MODE = "inflight"


@lru_cache(maxsize=1)
def _source() -> str:
    """``view-map.js`` with comment CONTENT blanked.

    Load-bearing: this module's own rationale prose names every status and bucket it
    guards. Scanning raw source would let a bucket that exists only in a comment
    satisfy the assertions — the guard would then pass on a file whose code had been
    gutted, which is worse than no guard.
    """
    return strip_js_comments(_VIEW_MAP.read_text(encoding="utf-8"))


def _object_literal_keys(name: str) -> set[str]:
    """The KEY set of a top-level ``const <name> = { a: 1, b: 1 };`` declaration."""
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*\{{([^}}]*)\}}", _source())
    assert match is not None, f"view-map.js declares no `const {name} = {{...}}`"
    return set(re.findall(r"(\w+)\s*:", match.group(1)))


def _mode_to_bucket_const() -> dict[str, str]:
    """``RUN_BUCKETS``' mode -> bucket-constant-name wiring.

    Read separately from the buckets themselves so the WIRING is under guard too: a
    file could declare three perfect buckets and point every mode at the same one.
    """
    match = re.search(r"const\s+RUN_BUCKETS\s*=\s*\{([^}]*)\}", _source())
    assert match is not None, "view-map.js declares no `const RUN_BUCKETS`"
    return dict(re.findall(r"(\w+)\s*:\s*(\w+)", match.group(1)))


def _bucket_for_mode(mode: str) -> set[str]:
    wiring = _mode_to_bucket_const()
    assert mode in wiring, f"RUN_BUCKETS has no {mode!r} mode (has {sorted(wiring)})"
    return _object_literal_keys(wiring[mode])


def _declared_default_mode() -> str:
    match = re.search(r"const\s+RUN_MODE_DEFAULT\s*=\s*'([^']+)'", _source())
    assert match is not None, "view-map.js declares no `const RUN_MODE_DEFAULT`"
    return match.group(1)


# --------------------------------------------------------------------------- #
# AC-2 — the default is untouched (REJECT-IF-grade)
# --------------------------------------------------------------------------- #
def test_the_default_mode_is_in_flight_and_its_bucket_is_unchanged() -> None:
    """PLAN-0084 SD-C, not reopened by PLAN-0110.

    Both halves matter and they fail differently. A changed DEFAULT means a visitor's
    first paint shows runs SD-C ruled it must not; a widened in-flight BUCKET means the
    in-flight marker itself starts lighting terminal states, which is the ruling's own
    words ("never terminal states") broken while the default still reads 'inflight'.
    """
    assert _declared_default_mode() == _DEFAULT_MODE, (
        "the map must open on the in-flight mode — PLAN-0084 SD-C governs first paint "
        "and PLAN-0110 layered opt-in modes on top of it, deliberately not over it"
    )
    assert _bucket_for_mode(_DEFAULT_MODE) == {"waiting_human", "running"}, (
        "the in-flight bucket is SD-C's ratified pair; widening it would light a "
        "terminal state on the default view"
    )


# --------------------------------------------------------------------------- #
# AC-3 — bucket membership is exactly SD-B's ratified sets
# --------------------------------------------------------------------------- #
def test_completed_means_completed_exactly() -> None:
    """SD-B (Cray, typed, s237): ``completed`` = ``{completed}``.

    The rejected alternative was "all terminal states", which flattens *gave up* into
    *done*. A cancelled run wearing the settled marker would report abandoned spend as
    a decision somebody made.
    """
    assert _bucket_for_mode("completed") == {"completed"}


def test_all_means_every_status_the_enum_declares() -> None:
    """A mode named "all" that hides a status is a mode that lies about its name.

    The expected set is IMPORTED from ``PipelineRunStatus``, never copied: when a sixth
    status is added, this reddens here — instead of the new status silently belonging
    to no bucket and disappearing from the one view that promises to show everything.
    """
    expected = {s.value for s in PipelineRunStatus}
    assert len(expected) == 5, "PipelineRunStatus changed shape — re-read SD-B before widening"
    assert _bucket_for_mode("all") == expected


@pytest.mark.parametrize("status", ["failed", "cancelled"])
def test_failed_and_cancelled_appear_under_all_and_nowhere_else(status: str) -> None:
    """SD-B put these two in no NAMED mode. Asserted per-mode rather than as a summary
    so a failure names which mode admitted them."""
    assert status in _bucket_for_mode("all")
    assert status not in _bucket_for_mode("inflight")
    assert status not in _bucket_for_mode("completed")


def test_every_mode_the_toggle_offers_has_a_bucket() -> None:
    """The tabs are built from a literal list; a tab whose mode is missing from
    ``RUN_BUCKETS`` would fall back to the in-flight bucket and silently show the
    default view under another name."""
    tabs = re.search(r"\[\s*'inflight'\s*,\s*'completed'\s*,\s*'all'\s*\]\.map\(tab\)", _source())
    assert tabs is not None, "the three-tab toggle literal is not where this guard reads it"
    assert set(_mode_to_bucket_const()) == {"inflight", "completed", "all"}


# --------------------------------------------------------------------------- #
# AC-9 — cache-bust for the shipped JS
# --------------------------------------------------------------------------- #
def test_view_map_cache_bust_is_bumped() -> None:
    """A published visitor holds the previous ``view-map.js`` in cache; without a bumped
    ``?v=`` they keep the pre-filter file and the deploy is invisible to them.

    Per-FILE counter (``?v=cNN``): a value differing from other assets' is normal.
    """
    html = _INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(r"assets/view-map\.js\?v=c(\d+)", html)
    assert match is not None, "index.html no longer cache-busts view-map.js"
    assert int(match.group(1)) > _CACHE_BUST_BASELINE, (
        f"view-map.js changed in PLAN-0110 Step 2 but its ?v= counter is still "
        f"c{match.group(1)} (baseline c{_CACHE_BUST_BASELINE})"
    )
