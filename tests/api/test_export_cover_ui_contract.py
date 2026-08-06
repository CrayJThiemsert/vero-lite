"""The Month-End KPI view reads exactly the fields the cover response declares.

PLAN-0096 Step 8 shipped the month-end export with no UI, so the KPI a pilot
charter is bound to was a JSON endpoint you had to type a URL to reach. The view
that renders it (``services/api/static/assets/view-export.js``) binds field names
by string, and JavaScript has no compiler to notice when one of those strings
stops matching the Pydantic model on the other side: a renamed field does not
crash, it silently renders ``undefined`` — a blank tile where a governance number
used to be, on the screen most likely to be believed without checking.

So the guard is set EQUALITY in both directions, the same shape as
``test_trace_kind_labels.py``:

* a cover field the UI does not read → RED. Either the view should show it, or
  the omission is deliberate and belongs in ``_UNREAD_COVER_FIELDS`` with a
  reason. EMPTY by construction today — the view reads all eleven.
* a field the UI reads that the response does not declare → RED. That is the
  blank-tile bug, caught at CI time instead of in a demo.

Scope + limits, stated honestly:

* This is a **string-contract** test, not a rendering test. It proves the view
  asks for fields that exist; it cannot prove the number is placed in the right
  tile or formatted correctly. The repo ships no JS test harness, and this test
  does not pretend to be one — end-to-end rendering is verified in the browser
  preview against the live endpoint, and the endpoint's own producer→consumer
  coverage lives in ``tests/api/test_repair_spend_export_scenario.py``.
* The declared-field list is read from the JS asset itself, through the same
  delimiters the browser reads the literal through. There is no second copy to
  drift.
* The CSV guard below is a **structural** guard on a typed Cray decision, not a
  reminder to be careful.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from services.api.models.exports import ExportCoverResponse, ExportExceptionResponse
from tests.api.js_source import strip_js_comments

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSETS = _REPO_ROOT / "services" / "api" / "static" / "assets"
_VIEW_JS = _ASSETS / "view-export.js"
_API_JS = _ASSETS / "api.js"
_INDEX_HTML = _REPO_ROOT / "services" / "api" / "static" / "index.html"

_JSON_BEGIN = "/* EXPORT_COVER_FIELDS_JSON_BEGIN */"
_JSON_END = "/* EXPORT_COVER_FIELDS_JSON_END */"

#: Cover fields the view deliberately does not render. EMPTY by construction: the
#: panel shows all eleven, so a new field on the response forces a conscious call
#: rather than being silently dropped from the one screen that reports the KPI.
_UNREAD_COVER_FIELDS: frozenset[str] = frozenset()

#: Same, for the per-exception rows. Also EMPTY.
_UNREAD_EXCEPTION_FIELDS: frozenset[str] = frozenset()

#: A scan that matches nothing must not pass vacuously. Eleven cover fields and
#: seven exception fields exist today; the floors sit below both so adding one
#: does not require editing these numbers.
_COVER_FLOOR = 9
_EXCEPTION_FLOOR = 6


@lru_cache(maxsize=1)
def _contract() -> dict[str, list[str]]:
    """The {cover, exception} field lists, read from the JS asset's JSON block."""
    src = _VIEW_JS.read_text(encoding="utf-8")
    try:
        start = src.index(_JSON_BEGIN) + len(_JSON_BEGIN)
        end = src.index(_JSON_END)
    except ValueError as exc:  # pragma: no cover - only on a broken asset
        raise AssertionError(
            f"{_VIEW_JS.name} lost its {_JSON_BEGIN} / {_JSON_END} delimiters — the "
            "browser and this test read the SAME literal through them. Restore them."
        ) from exc
    return json.loads(src[start:end])


#: Comment stripping is shared — ``tests.api.js_source``. This module used to keep
#: its own copy, which stripped block comments before line comments and so read a
#: ``/*`` inside a ``//`` comment as a real block opener. ``api.js`` is scanned by
#: the CSV guard below and contains exactly that shape at line 87, which put lines
#: 87-105 of it beyond the guard's reach. ``test_the_comment_stripper_is_not_vacuous``
#: is what keeps the shared version honest here — if it ever eats real code, this
#: module goes RED rather than making the CSV guard silently unfalsifiable.


def test_cover_contract_block_is_not_vacuous() -> None:
    """A broken delimiter or an emptied list must fail, not silently find nothing."""
    contract = _contract()
    assert set(contract) == {"cover", "exception"}, (
        f"{_VIEW_JS.name}'s contract block must declare exactly 'cover' and "
        f"'exception'; found {sorted(contract)}"
    )
    assert len(contract["cover"]) >= _COVER_FLOOR, (
        f"only {len(contract['cover'])} cover fields declared (floor {_COVER_FLOOR}) — "
        "the block is probably broken, not the model. A pass here would be vacuous."
    )
    assert len(contract["exception"]) >= _EXCEPTION_FLOOR, (
        f"only {len(contract['exception'])} exception fields declared (floor "
        f"{_EXCEPTION_FLOOR}) — the block is probably broken. A pass would be vacuous."
    )


def test_the_view_reads_exactly_the_cover_response_fields() -> None:
    """Set equality with ExportCoverResponse — both directions are bugs."""
    declared = set(_contract()["cover"])
    actual = set(ExportCoverResponse.model_fields)

    invented = declared - actual
    assert not invented, (
        f"{_VIEW_JS.name} reads cover fields ExportCoverResponse does not declare: "
        f"{sorted(invented)}\n\nIn the browser these render as `undefined` — a blank "
        "tile where a governance number belongs, with no error anywhere."
    )
    unread = actual - declared - _UNREAD_COVER_FIELDS
    assert not unread, (
        f"ExportCoverResponse declares fields the Month-End KPI view never shows: "
        f"{sorted(unread)}\n\nEither render them, or add each to "
        "_UNREAD_COVER_FIELDS with the reason it is deliberately not on the screen "
        "that reports the KPI."
    )


def test_the_view_reads_exactly_the_exception_response_fields() -> None:
    """Same equality for the per-row E-2 exception report on the cover."""
    declared = set(_contract()["exception"])
    actual = set(ExportExceptionResponse.model_fields)

    invented = declared - actual
    assert not invented, (
        f"{_VIEW_JS.name} reads exception fields ExportExceptionResponse does not "
        f"declare: {sorted(invented)}"
    )
    unread = actual - declared - _UNREAD_EXCEPTION_FIELDS
    assert not unread, (
        f"ExportExceptionResponse declares fields the exception list never shows: "
        f"{sorted(unread)}\n\nThe E-2 list is the emergency-path report; a field "
        "dropped from it is a repair whose story is told incompletely."
    )


def _property_accesses(receiver: str) -> set[str]:
    """Every ``<receiver>.<name>`` read in the view, manifest block excluded.

    The manifest is cut out first so the scan sees the RENDER CODE only —
    otherwise a field would satisfy the "is it read?" check merely by being
    declared, which is the vacuity this pair of tests exists to prevent.
    """
    src = _VIEW_JS.read_text(encoding="utf-8")
    start = src.index(_JSON_BEGIN)
    end = src.index(_JSON_END) + len(_JSON_END)
    code = strip_js_comments(src[:start] + src[end:])
    return set(re.findall(rf"\b{re.escape(receiver)}\.([a-z_][a-z0-9_]*)\b", code))


def test_every_declared_field_is_read_by_the_render_code() -> None:
    """The manifest must describe the code, not replace it.

    Without this, the contract block could be edited into agreement with the model
    while the render function reads something else entirely — the manifest would
    pass and the screen would still be blank.
    """
    contract = _contract()
    cover_read = _property_accesses("cover")
    exc_read = _property_accesses("exc")

    # `year` and `month` are threaded as function parameters rather than read off
    # the payload object, so they are legitimately absent from `cover.<name>`.
    unread = (set(contract["cover"]) - cover_read) - {"year", "month"}
    assert not unread, (
        f"declared in {_VIEW_JS.name}'s contract block but never read as "
        f"`cover.<name>` by the render code: {sorted(unread)}\n\nThe manifest "
        "describes what the view reads. A name only in the manifest means the block "
        "was edited to satisfy this test instead of the view being fixed."
    )
    unread_exc = set(contract["exception"]) - exc_read
    assert not unread_exc, (
        f"declared but never read as `exc.<name>` in the exception list: " f"{sorted(unread_exc)}"
    )


def test_every_property_access_is_a_field_the_response_declares() -> None:
    """The reverse direction — and the one a manifest edit cannot satisfy.

    Added after a non-vacuity probe caught the first version of this guard passing
    vacuously: it counted name occurrences, so renaming ONE of two reads of
    ``cover.outstanding_ratification_count`` left the count above the floor and the
    test stayed green while the rendered row silently became ``undefined``. Counting
    cannot see a partial mis-read; scanning the accesses themselves can.
    """
    cover_fields = set(ExportCoverResponse.model_fields)
    exc_fields = set(ExportExceptionResponse.model_fields)

    stray_cover = _property_accesses("cover") - cover_fields
    assert not stray_cover, (
        f"{_VIEW_JS.name} reads `cover.<name>` for names ExportCoverResponse does "
        f"not declare: {sorted(stray_cover)}\n\nEach renders as `undefined` — a blank "
        "value where a governance number belongs, with no error anywhere."
    )
    stray_exc = _property_accesses("exc") - exc_fields
    assert not stray_exc, (
        f"{_VIEW_JS.name} reads `exc.<name>` for names ExportExceptionResponse does "
        f"not declare: {sorted(stray_exc)}"
    )


def test_the_spa_actually_loads_the_view() -> None:
    """An unreferenced view asset is dead code, and the tab would render nothing."""
    html = _INDEX_HTML.read_text(encoding="utf-8")
    assert "assets/view-export.js" in html, (
        f"{_INDEX_HTML.name} does not load view-export.js — the Month-End KPI tab "
        "would mount an undefined module. Add the script tag (before app.js, with a "
        "?v= cache-bust token)."
    )
    app_js = strip_js_comments((_ASSETS / "app.js").read_text(encoding="utf-8"))
    assert "O.ViewExport" in app_js, (
        "app.js does not register the Month-End KPI view in its VIEWS map, so the "
        "asset loads but no tab reaches it."
    )


def test_the_export_ui_never_reaches_the_csv_route() -> None:
    """Cray declined a UI button (and a CLI) for the CSV at s192 — guard it structurally.

    That decision is recorded in ``services/api/routers/exports.py``'s module
    docstring, where nothing enforces it. A later session adding a download button
    would be reversing a typed decision, and a comment asking it not to is not a
    control. This is: the moment either asset references the ``.csv`` route, the
    build goes red and whoever wrote it has to reverse the decision on purpose.
    """
    for path in (_VIEW_JS, _API_JS):
        code = strip_js_comments(path.read_text(encoding="utf-8"))
        assert ".csv" not in code, (
            f"{path.name} references the .csv export route in CODE (not a comment).\n\n"
            "Cray declined a UI download button for the month-end file at s192 (see "
            "services/api/routers/exports.py). If that is being reversed deliberately, "
            "record the new decision and delete this test in the same change — do not "
            "route around it."
        )


@lru_cache(maxsize=1)
def _defined_css_classes() -> frozenset[str]:
    """Every class selector defined by the stylesheets index.html loads."""
    html = _INDEX_HTML.read_text(encoding="utf-8")
    sheets = re.findall(r'<link rel="stylesheet" href="assets/([^"?]+)', html)
    names: set[str] = set()
    for sheet in sheets:
        css = (_ASSETS / sheet).read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)
        names |= set(re.findall(r"\.(-?[_a-zA-Z][\w-]*)", css))
    return frozenset(names)


def test_every_css_class_the_view_uses_is_actually_defined() -> None:
    """A class no stylesheet defines renders unstyled — and can break the layout.

    Not hypothetical, and not a style nit. The first version of this view used
    ``.hero-sub``, which existed in no stylesheet. The element therefore inherited
    ``white-space: nowrap`` from its ancestor with nothing to override it, and the
    subtitle rendered as ONE unwrapped line — measured at 1121px inside a 980px
    column, pushing the whole document into horizontal scroll. Nothing errored;
    the console was clean. A browser measurement caught it, and this test is what
    makes the next one cheap.
    """
    src = strip_js_comments(_VIEW_JS.read_text(encoding="utf-8"))
    used: set[str] = set()
    # `class: 'a b'` and the literal half of `class: 'a ' + dynamic`.
    for literal in re.findall(r"class:\s*'([^']*)'", src):
        used |= {tok for tok in literal.split() if tok}
    # Class names this view RETURNS for a caller to concatenate (kpiClass).
    used |= set(re.findall(r"return\s+'(s-[a-z]+)'", src))

    assert used, (
        f"no class literals found in {_VIEW_JS.name} — the scan is broken, not the "
        "view. A pass here would be vacuous."
    )
    undefined = used - _defined_css_classes()
    assert not undefined, (
        f"{_VIEW_JS.name} uses CSS classes no loaded stylesheet defines: "
        f"{sorted(undefined)}\n\nThese render unstyled and silently inherit whatever "
        "the ancestors set — the failure mode is a broken layout with a clean "
        "console, not an error. Define the class or use one that exists."
    )


def test_the_css_class_scan_sees_the_real_stylesheets() -> None:
    """Guard the guard: an empty class registry would make the check above vacuous."""
    defined = _defined_css_classes()
    assert len(defined) > 100, (
        f"only {len(defined)} CSS classes parsed from the linked stylesheets — the "
        "parser or the <link> scan is broken. A pass above would prove nothing."
    )
    # Anchors from three different sheets: if any is missing, a sheet was skipped.
    for anchor in ("hero-kpi-tile", "hero-sub", "faint"):
        assert anchor in defined, (
            f"'{anchor}' was not found in the parsed stylesheets — at least one sheet "
            "linked by index.html is not being read."
        )


def test_the_comment_stripper_is_not_vacuous() -> None:
    """If the stripper ate the code, the CSV guard above would pass unfalsifiably."""
    stripped = strip_js_comments(_VIEW_JS.read_text(encoding="utf-8"))
    assert "O.Exports.cover" in stripped, (
        "the comment stripper removed the view's own fetch call — every guard built "
        "on it is now vacuous. Fix the stripper before trusting this module."
    )
    assert "/*" not in stripped and "*/" not in stripped, (
        "block comments survived the stripper, so a prose mention of a route could "
        "satisfy or trip the CSV guard for the wrong reason."
    )
