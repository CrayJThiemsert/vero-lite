"""Tab F's origin-narrative panel: the path the JS asks for is the path the app serves.

The repo has no build step and no JS test runner (``docs/conventions/ui.md`` §5), so a
CI tripwire for the UI has to be a Python test that reads the shipped source. This
module reads ``services/api/static/assets/view-procedures.js`` — the ARTIFACT, never a
restatement of it — following ``test_map_run_filter_contract``'s precedent.

**The seam this exists for.** The panel is the only place in the console that fetches a
file the browser must resolve by *string*: ``fetch('assets/narratives/…')``. Nothing
else links the JS constant to the file on disk. Rename the file, move the directory, or
retype the constant, and the console keeps booting, Tab F keeps rendering, and the
button opens onto an error state that only a human clicking it would ever see. So the
load-bearing assertion here is not "the file exists" — it is a real HTTP GET through the
real StaticFiles mount, at exactly the path parsed out of the JS.

That is also why the served bytes are compared to the on-disk bytes rather than merely
asserted non-empty: the published deployment ships this file *inside the image*
(``Dockerfile`` COPYs ``services/``, and pointedly not ``docs/``), so "it is on my disk"
and "the container serves it" are different claims.

**The content anchor is deliberate, not decorative.** The narrative's whole job in the
demo is to be the raw form of what Tab F states formally, so the test pins the one
sentence that carries that: the owner's own separation-of-duties rule. Swap the file for
some other document and the panel would still open, still render, and still be wrong —
a green that this assertion turns red.

**What this cannot prove.** It is a source-and-serving contract, not a rendering test.
That the button paints, that the overlay traps focus, and that Thai prose wraps legibly
are browser observations — evidence, not the gate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api import main
from tests.api.js_source import strip_js_comments

_STATIC = Path(main.__file__).resolve().parent / "static"
_VIEW_PROCEDURES = _STATIC / "assets" / "view-procedures.js"

#: ``fleet_maintenance: { file: 'assets/narratives/fleet_maintenance.md', … }``
_ENTRY = re.compile(r"(\w+)\s*:\s*\{[^{}]*?file\s*:\s*'([^']+)'", re.DOTALL)


def _source() -> str:
    return strip_js_comments(_VIEW_PROCEDURES.read_text(encoding="utf-8"))


def _registry() -> dict[str, str]:
    """``{vertical: relative asset path}`` as the shipped JS declares it."""
    src = _source()
    start = src.find("const NARRATIVES")
    assert start != -1, (
        "view-procedures.js no longer declares `const NARRATIVES` — the panel's "
        "registry was renamed or removed, and every assertion below would parse "
        "nothing and pass vacuously"
    )
    # Bound the scan to the registry literal so an unrelated `file:` elsewhere in
    # the module cannot be mistaken for an entry.
    end = src.find("\n  };", start)
    assert end != -1, "could not find the end of the NARRATIVES literal"
    return dict(_ENTRY.findall(src[start:end]))


def test_the_registry_parse_is_not_vacuous() -> None:
    """Positive control: the instrument reads the artifact at all.

    Every other test in this module iterates over the registry, so an empty parse
    would turn all of them green while the feature was gone.
    """
    registry = _registry()
    assert registry, (
        "parsed zero narrative entries out of view-procedures.js — either the "
        "registry is empty or the parse broke; both make this module vacuous"
    )
    assert (
        "fleet_maintenance" in registry
    ), f"fleet_maintenance has no narrative registered; parsed: {sorted(registry)}"


def test_every_registered_narrative_exists_on_disk() -> None:
    for vertical, rel in _registry().items():
        assert rel.startswith("assets/"), (
            f"{vertical}'s narrative path {rel!r} is not under assets/ — the "
            "published allowlist admits `^/assets/.+$` and nothing else, so a "
            "path outside it would 404 behind Cloudflare Access while working locally"
        )
        target = _STATIC / rel
        assert target.is_file(), f"{vertical} declares {rel!r}, which is not a file at {target}"
        assert target.stat().st_size > 0, f"{vertical}'s narrative {rel!r} is empty"


@pytest.mark.anyio
async def test_the_declared_path_is_the_path_the_server_serves(client: AsyncClient) -> None:
    """The seam: a real GET through the real static mount, at the JS's own string.

    This is the assertion that would redden on a rename, a moved directory, or a
    retyped constant — none of which any other test in the suite can see.

    Self-guarded rather than leaning on ``test_the_registry_parse_is_not_vacuous``:
    measured, an emptied registry turns this loop vacuously green, and the most
    load-bearing assertion in the module should not depend on a sibling test being
    collected to stay honest.
    """
    registry = _registry()
    assert registry, "empty registry — this test would otherwise pass by iterating nothing"
    for vertical, rel in registry.items():
        response = await client.get("/" + rel)
        assert response.status_code == 200, (
            f"{vertical}'s narrative is declared at {rel!r} but the app served "
            f"HTTP {response.status_code} for it — the panel's fetch would fail"
        )
        on_disk = (_STATIC / rel).read_bytes()
        assert response.content == on_disk, (
            f"the bytes served at /{rel} differ from the file on disk — the "
            "container would ship something other than the reviewed narrative"
        )


@pytest.mark.anyio
async def test_the_fleet_narrative_carries_the_sod_rule_the_gate_formalises(
    client: AsyncClient,
) -> None:
    """The content anchor — see the module docstring.

    ``คนทำเรื่องเบิกห้ามเป็นคนอนุมัติเอง`` is the owner stating, in his own words, the
    rule Tab H's gate renders as *"the requester cannot approve their own
    requisition"*. It is the single line that makes this document the origin of
    THIS vertical rather than a generic story, so it is what the test pins.
    """
    rel = _registry()["fleet_maintenance"]
    text = (await client.get("/" + rel)).text
    assert "คนทำเรื่องเบิกห้ามเป็นคนอนุมัติเอง" in text, (
        "the fleet narrative no longer contains the owner's separation-of-duties "
        "sentence — either the file was replaced, or the demo's before/after "
        "pairing with Tab H's gate silently stopped being true"
    )
    for name in ("ต้อม", "วิรัช"):
        assert name in text, (
            f"{name} is missing from the narrative — the personas the demo logs in "
            "as are supposed to be the people in this story"
        )


def test_the_panel_is_reachable_from_the_procedure_card() -> None:
    """A registry nobody calls is a feature nobody can open."""
    src = _source()
    assert "originNarrativeLink(vEntry.vertical, vEntry)" in src, (
        "procedureCard no longer builds the origin-narrative link — the registry "
        "would still parse and the file would still serve, with no way in"
    )
    assert "openNarrative(entry, vEntry)" in src, (
        "the button is no longer wired to open the panel with its vertical entry — "
        "without vEntry the legend cannot be built from the live procedure"
    )


# --- the highlight mapping (session 239) ------------------------------------
#
# Each anchor is an exact substring of the narrative. A near-miss — one wrong Thai
# character, a normalised space — is a SILENT no-op: the panel opens, the prose
# renders, and nothing is marked. Only a human reading closely would catch it, and
# only if they knew what to expect. These two tests are that reader.

_HIGHLIGHT = re.compile(r"\{\s*step_id\s*:\s*'([^']+)'\s*,\s*match\s*:\s*'([^']+)'\s*\}")


def _anchors() -> list[tuple[str, str]]:
    src = _source()
    start = src.find("highlights: [")
    assert start != -1, "the highlights list is gone from the registry"
    end = src.find("]", start)
    return _HIGHLIGHT.findall(src[start:end])


@pytest.mark.anyio
async def test_every_highlight_anchor_occurs_exactly_once(client: AsyncClient) -> None:
    """An anchor that matches nothing highlights nothing, loudly here instead of never."""
    anchors = _anchors()
    assert anchors, "parsed zero highlight anchors — this test would pass on an empty list"
    text = (await client.get("/" + _registry()["fleet_maintenance"])).text
    for step_id, match in anchors:
        assert text.count(match) == 1, (
            f"the anchor for step {step_id!r} occurs {text.count(match)} times in the "
            f"narrative, expected exactly 1 — 0 highlights nothing at all, and >1 "
            f"marks a passage the mapping did not mean: {match[:60]!r}"
        )


def test_every_anchored_step_exists_in_the_shipped_procedure() -> None:
    """Step ids are checked against the SPEC, imported rather than copied.

    ``procedures.yaml`` is the source of truth for what steps exist. A copied list
    here would agree with itself while a renamed or deleted step left its anchor
    pointing at nothing — and the legend, which is built from the live steps, would
    silently stop marking that passage.
    """
    from services.engine.procedures.spec import load_procedures

    spec = load_procedures("fleet_maintenance")
    procedure = next(
        (p for p in spec.procedures if p.procedure_id == "governed_repair_approval"), None
    )
    assert procedure is not None, "governed_repair_approval is no longer in the fleet spec"
    shipped = {step.step_id for step in procedure.steps}
    assert shipped, "the procedure declares no steps — the check below would be vacuous"

    anchored = {step_id for step_id, _ in _anchors()}
    assert anchored, "no anchors parsed"
    unknown = sorted(anchored - shipped)
    assert not unknown, (
        f"the narrative maps sentences to step id(s) {unknown} that the shipped "
        f"procedure does not declare; it has {sorted(shipped)}"
    )


def test_reshape_is_declared_unmapped_rather_than_forced() -> None:
    """The honest gap, pinned so nobody 'fixes' it by inventing a source sentence.

    ``reshape`` bridges quote-as-a-reading to quote-as-a-governed-spend. That is
    machinery the platform needs, not a rule the business owner stated, so the
    panel shows it as having no origin. The claim the demo makes is 'these
    sentences became these steps' — attaching a sentence here would make that claim
    false in the one place a careful viewer would check.
    """
    from services.engine.procedures.spec import load_procedures

    spec = load_procedures("fleet_maintenance")
    procedure = next(p for p in spec.procedures if p.procedure_id == "governed_repair_approval")
    assert "reshape" in {step.step_id for step in procedure.steps}, (
        "reshape is no longer a step — this test's premise is stale; re-derive the "
        "mapping rather than deleting the test"
    )
    assert "reshape" not in {step_id for step_id, _ in _anchors()}, (
        "reshape acquired a narrative anchor. If that is deliberate, the owner "
        "really did describe the transform and this test should be updated — but "
        "check the sentence actually says it, because the panel now claims it does"
    )
    assert "unmappedNote" in _source(), (
        "the legend no longer carries an unmapped note, so a step with no anchor "
        "would render as a bare number with no explanation"
    )


def test_the_narrative_renderer_never_uses_innerhtml() -> None:
    """The renderer builds nodes; it must not interpolate served text as markup.

    The content is ours today. This pins that it stays safe by CONSTRUCTION rather
    than by the content staying trusted — a future narrative is a plain file that
    anyone editing would not think of as code.
    """
    src = _source()
    assert "innerHTML" not in src, (
        "view-procedures.js now contains innerHTML — the narrative renderer must "
        "build DOM nodes via h()/textContent so served text can never become markup"
    )
