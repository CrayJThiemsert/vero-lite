"""Generate the PLAN-0126 story probe batteries — the tracked home of their generator.

The three files it writes (``plan-0126-story-{page,drift,scenario}.json``) are OUTPUT.
Edit the specs below and regenerate; never hand-edit the JSON.

🔴 **Why this file is tracked (s309).** Session 304 wrote the generator into a gitignored
handoff directory; session 305 extended it (P11a to P11d for AC-11, P3a2 and P3b2 for
AC-3) in a session scratchpad and regenerated twice. STATUS and two handoffs then named the
handoff copy as "the only copy". Measured on ``main`` ``d71f3cd7``: that copy produced a
page battery of **35** probes against the committed **41** — running it for the next
``story.js?v=`` bump would have deleted six witnesses without a word. The current copy
survived only in a Windows temp scratchpad.

``tests/api/test_story_battery_generator.py`` fails CI when this generator and the
committed JSON disagree, in either direction.

**Interim by ruling (Cray, s309).** A load-time claim-reference design that would make a
generator unnecessary is being dispatched as a PLAN; it reopens PLAN-0115 AC-5
("``Claim.stable_key`` addressing, mandatory"). If it lands, this file and its guard
retire together.

Every ``expect_claim`` is resolved from :func:`tools.probe_coverage.enumerate_claims`
(never hand-typed); a claim that resolves to zero or several claims, and an ``old`` that
does not occur exactly once in its subject, are refused before anything is written.

Run from anywhere::

    python -m tests.batteries.plan_0126_story_generator          # regenerate
    python -m tests.batteries.plan_0126_story_generator --check  # compare only
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # path-script invocation, not `-m`
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.probe_coverage import enumerate_claims

REPO_ROOT = Path(__file__).resolve().parents[2]
BATTERY_DIR = Path("tests/batteries")

PAGE = "tests/api/test_story_page.py"
DRIFT = "tests/api/test_story_drift.py"
SCEN = "tests/api/test_story_scenario.py"
S = "services/api/static/story/"
DATA = S + "story-data.js"
CFG = "deploy/published/oct-fleet-maintenance/cloudflared/config.yml"
APP_JS = "services/api/static/assets/app.js"
MAIN = "services/api/main.py"
STORY_SOURCE = "tests/api/story_source.py"


@dataclass(frozen=True)
class Spec:
    """One probe before its claim is resolved.

    ``prefix`` selects the claim by the start of its asserted source text; ``owner`` is
    the function that holds the assert, and defaults to ``test`` (a helper's assert is
    owned by the helper, not by the test that calls it).
    """

    name: str
    subject: str
    old: str
    new: str
    test: str
    prefix: str
    note: str
    owner: str | None = None


@dataclass(frozen=True)
class Exemption:
    """A claim no text mutation can reach, with the written reason."""

    owner: str
    prefix: str
    reason: str


@dataclass(frozen=True)
class BatterySpec:
    filename: str
    module: str
    probes: tuple[Spec, ...]
    exemptions: tuple[Exemption, ...] = ()


@dataclass
class Generated:
    """What one generation produced: file name -> JSON text, plus every refusal."""

    files: dict[str, str] = field(default_factory=dict)
    counts: dict[str, tuple[int, int]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def anchor_error(root: Path, spec: Spec) -> str | None:
    """Refuse an ``old`` that does not occur exactly once in its subject."""
    n = (root / spec.subject).read_text(encoding="utf-8").count(spec.old)
    if n != 1:
        return f"{spec.name}: `old` occurs {n}x in {spec.subject}: {spec.old[:70]!r}"
    return None


def resolve_key(root: Path, module: str, owner: str, prefix: str, errors: list[str]) -> str:
    """The one claim ``owner`` asserts starting with ``prefix``, by its stable_key."""
    hits = [
        c
        for c in enumerate_claims(root / module)
        if c.owner == owner and c.source.startswith(prefix)
    ]
    if len(hits) != 1:
        errors.append(f"claim {owner}|{prefix!r} in {module}: {len(hits)} matches")
    return hits[0].stable_key if len(hits) == 1 else f"UNRESOLVED:{owner}"


def render(root: Path = REPO_ROOT) -> Generated:
    """Resolve every battery against the tree at ``root``; write nothing."""
    out = Generated()
    for battery in BATTERIES:
        probes: list[dict[str, str]] = []
        for spec in battery.probes:
            error = anchor_error(root, spec)
            if error is not None:
                out.errors.append(error)
            owner = spec.owner if spec.owner is not None else spec.test
            probes.append(
                {
                    "name": spec.name,
                    "subject": spec.subject,
                    "old": spec.old,
                    "new": spec.new,
                    "node_id": f"{battery.module}::{spec.test}",
                    "expect_claim": resolve_key(
                        root, battery.module, owner, spec.prefix, out.errors
                    ),
                    "note": spec.note,
                }
            )
        exemptions = {
            resolve_key(root, battery.module, e.owner, e.prefix, out.errors): e.reason
            for e in battery.exemptions
        }
        doc = {"claim_sources": [battery.module], "probes": probes, "exemptions": exemptions}
        out.files[battery.filename] = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
        out.counts[battery.filename] = (len(probes), len(exemptions))
    return out


def describe_drift(name: str, committed: str | None, generated: str) -> list[str]:
    """Name what differs between a committed battery file and what the specs generate.

    One line per difference, so a failing guard says *what* drifted without a diff tool
    (lesson #0043). ``committed`` is ``None`` when the file does not exist.
    """
    if committed is None:
        return [f"{name}: not committed — the generator would create it"]
    if committed == generated:
        return []
    try:
        old_doc, new_doc = json.loads(committed), json.loads(generated)
    except json.JSONDecodeError as exc:
        return [f"{name}: committed file is not valid JSON ({exc}) — regenerate it"]
    if not isinstance(old_doc, dict):
        return [f"{name}: committed file is not a battery document — regenerate it"]
    old, new = _probes_by_name(old_doc), _probes_by_name(new_doc)

    # The s305 shape first: a probe only the committed file has is a witness that
    # regenerating from these specs would delete without a word.
    lines = [
        f"{name}: {probe} is committed but not in the specs — regenerating would DELETE it"
        for probe in old
        if probe not in new
    ]
    lines += [
        f"{name}: {probe} is in the specs but not committed" for probe in new if probe not in old
    ]
    for probe in (p for p in old if p in new and old[p] != new[p]):
        fields = sorted(
            k
            for k in old[probe].keys() | new[probe].keys()
            if old[probe].get(k) != new[probe].get(k)
        )
        lines.append(f"{name}: {probe} differs in {fields}")
    for key in ("claim_sources", "exemptions"):
        if _field(old_doc, key) != _field(new_doc, key):
            lines.append(f"{name}: `{key}` differs")
    return lines or [
        f"{name}: same probes, sources and exemptions, but the bytes differ — regenerate it"
    ]


def _field(doc: object, key: str) -> object:
    return doc.get(key) if isinstance(doc, dict) else None


def _probes_by_name(doc: object) -> dict[str, dict[str, Any]]:
    """A battery document's probes keyed by name; anything malformed reads as no probes."""
    probes = _field(doc, "probes")
    if not isinstance(probes, list):
        return {}
    return {str(p.get("name")): p for p in probes if isinstance(p, dict)}


PAGE_PROBES: tuple[Spec, ...] = (
    Spec(
        name="P-A1",
        subject=STORY_SOURCE,
        old='AUTHORED_FILES = ("index.html", "story.css", "story-data.js", "story.js")',
        new='AUTHORED_FILES = ("index.html", "story.scss", "story-data.js", "story.js")',
        test="test_story_files_reference_no_external_origin",
        owner="_authored_texts",
        prefix="not missing",
        note=(
            "an authored file the scan expects is missing: the helper's presence assert "
            "reddens before any scan"
        ),
    ),
    Spec(
        name="P1a",
        subject=S + "story.js",
        old="import * as THREE from './three.module.min.js?v=160';",
        new=(
            "import * as THREE from "
            "'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';"
        ),
        test="test_story_files_reference_no_external_origin",
        prefix="not any(external",
        note=(
            "reinserts the stage-1 CDN import; the external-origin assert reddens, the ref "
            "count stays >= 4"
        ),
    ),
    Spec(
        name="P1c",
        subject=STORY_SOURCE,
        old="    return _REFERENCE_PATTERNS[kind].findall(text)",
        new="    return []",
        test="test_story_files_reference_no_external_origin",
        prefix="total >= 4",
        note=(
            "the parser reads nothing: no external refs (green) and a zero count — the "
            "anti-vacuity assert reddens"
        ),
    ),
    Spec(
        name="P1b",
        subject=STORY_SOURCE,
        old='_SCHEME = r"(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)"',
        new='_SCHEME = r"(?:never-a-scheme:)"',
        test="test_the_origin_checker_flags_a_known_cdn_import",
        prefix="flagged ==",
        note=(
            "the checker stops recognising a scheme; the positive control on the known CDN "
            "import reddens"
        ),
    ),
    Spec(
        name="P2a",
        subject=MAIN,
        old="        if isinstance(response, FileResponse) and self._is_root_index(response):",
        new=(
            "        if isinstance(response, FileResponse) and "
            'str(response.path).endswith("index.html"):'
        ),
        test="test_story_index_is_served_unprofiled_on_the_published_profile",
        prefix="response.status_code == 200",
        note=(
            "restores PLAN-0100's endswith match: the story index is profiled, lacks the "
            "anchor, raises -> 500"
        ),
    ),
    Spec(
        name="P2b",
        subject=MAIN,
        old='        response.headers["Content-Security-Policy"] = _OCT_CSP',
        new="        pass",
        test="test_story_index_is_served_unprofiled_on_the_published_profile",
        prefix="csp",
        note="the CSP stamp is dropped; status stays 200, the csp assert reddens",
    ),
    Spec(
        name="P2d",
        subject=S + "index.html",
        old='<script type="module" src="story.js?v=c1"></script>',
        new='<script type="module" src="scene.js?v=c1"></script>',
        test="test_story_index_is_served_unprofiled_on_the_published_profile",
        prefix='\'type="module" src="story.js\' in',
        note=(
            "the served page no longer loads story.js as a module; 200 and CSP hold, the "
            "module-tag assert reddens"
        ),
    ),
    Spec(
        name="P2e",
        subject=S + "index.html",
        old='  <meta charset="utf-8" />',
        new='  <meta charset="utf-8" />\n  <meta name="ui-profile" content="dev" />',
        test="test_story_index_is_served_unprofiled_on_the_published_profile",
        prefix="not profile_meta",
        note=(
            "a profile tag appears in the story page (served plain); only the "
            "no-profile-meta assert reddens"
        ),
    ),
    Spec(
        name="P2f",
        subject=MAIN,
        old='        response.headers["Content-Security-Policy"] = _OCT_CSP',
        new=(
            '        response.headers["Content-Security-Policy"] = _OCT_CSP\n'
            '        response.headers["Cache-Control"] = "no-store"'
        ),
        test="test_story_index_is_served_unprofiled_on_the_published_profile",
        prefix='cache != "no-store"',
        note=(
            "every static response is marked no-store; status, CSP, module tag and meta "
            "hold — the cache assert reddens"
        ),
    ),
    Spec(
        name="P2g",
        subject="services/api/static/index.html",
        old='<meta name="ui-profile" content="dev" />',
        new='<meta name="ui-profile" content="dev-anchor-removed" />',
        test="test_root_index_is_still_profiled",
        prefix="response.status_code == 200",
        note=(
            "the console index loses its anchor; PLAN-0100's fail-loud raise turns GET / "
            "into 500"
        ),
    ),
    Spec(
        name="P2h",
        subject=MAIN,
        old="        return Path(response.path).resolve() == root_index",
        new="        return False",
        test="test_root_index_is_still_profiled",
        prefix="published_tag",
        note=(
            "nothing is profiled, not even the root: 200 with the dev tag — the "
            "published-tag assert reddens"
        ),
    ),
    Spec(
        name="P2c",
        subject=MAIN,
        old="        if _UI_PROFILE_META_DEV not in html:",
        new="        if False:",
        test="test_profiled_index_still_raises_without_the_anchor",
        prefix="pytest.raises(RuntimeError",
        note="the fail-loud raise is disabled; DID NOT RAISE at the with-line",
    ),
    Spec(
        name="P3d",
        subject=CFG,
        old="  - path: ^/story/$\n    service: http://app:8000\n",
        new="",
        test="test_every_story_file_is_admitted_by_a_story_ingress_row",
        prefix="len(rows) == 2",
        note="one story row removed: the row-count assert reddens first",
    ),
    Spec(
        name="P3c",
        subject=CFG,
        old="  - path: ^/story/[^/]+$",
        new="  - path: ^/story/[a-z]+$",
        test="test_every_story_file_is_admitted_by_a_story_ingress_row",
        prefix="sorted(admitted) == sorted(files)",
        note=("the sibling row rejects dotted filenames: two rows, flat dir, admitted != files"),
    ),
    Spec(
        name="P3e",
        subject=CFG,
        old="  - path: ^/story/$",
        new="  - path: ^/story/x$",
        test="test_every_story_file_is_admitted_by_a_story_ingress_row",
        prefix="page_admitted",
        note=(
            "the page row no longer admits /story/; files still admitted — the page assert "
            "reddens"
        ),
    ),
    Spec(
        name="P3f",
        subject=CFG,
        old="  - path: ^/story/[^/]+$",
        new="  - path: ^/story/.+$",
        test="test_every_story_file_is_admitted_by_a_story_ingress_row",
        prefix="control_admitted == 0",
        note=(
            "the sibling row admits nested paths; everything real passes, the "
            "/story/sub/x.js control reddens"
        ),
    ),
    Spec(
        name="P3b2",
        subject=CFG,
        old="  - path: ^/story/[^/]+$",
        new="  - path: /story/[^/]+$",
        test="test_the_story_rows_are_anchored_and_the_expected_table_carries_them",
        prefix="unanchored == []",
        note=(
            "PLAN-0126 P3b\N{PRIME} (C): the sibling row loses its LEADING ^ — every story "
            "file is still admitted and /story/sub/x.js still refused (the admission test "
            "stays green), but the anchoring assert reddens"
        ),
    ),
    Spec(
        name="P3a2",
        subject="tests/deploy/test_published_profiles.py",
        old='        r"^/story/$",\n',
        new="",
        test="test_the_story_rows_are_anchored_and_the_expected_table_carries_them",
        prefix="table_rows == config_rows",
        note=(
            "PLAN-0126 P3a\N{PRIME} (C): _EXPECTED_ALLOW loses the page row while "
            "config.yml keeps it — the anchoring assert (first) stays green, the table "
            "comparison reddens"
        ),
    ),
    Spec(
        name="P5a",
        subject=S + "story.js",
        old="'ทุกขั้นถูกบันทึกแบบ tamper-evident'",
        new="'ทุกขั้นถูกบันทึกแบบ tamper-evident ฿30,001'",
        test="test_story_text_carries_no_ruled_out_literal",
        prefix="not found",
        note="a band numeral enters a caption; the absence assert (first) reddens",
    ),
    Spec(
        name="P5d",
        subject=S + "story.js",
        old="'ทุกขั้นถูกบันทึกแบบ tamper-evident'",
        new="'ทุกขั้นถูกบันทึกแบบ tamper-evident 30001'",
        test="test_story_text_carries_no_ruled_out_literal",
        prefix="band_numeral ==",
        note=(
            "the bare band numeral leaks into a caption (not a listed literal): the "
            "numeral-count assert reddens"
        ),
    ),
    Spec(
        name="P5e",
        subject=S + "story.js",
        old="'ทุกขั้นถูกบันทึกแบบ tamper-evident'",
        new="'ทุกขั้นถูกบันทึกแบบ tamper-evident AI AI'",
        test="test_story_text_carries_no_ruled_out_literal",
        prefix="ai_tokens <= 1",
        note="two AI tokens enter a caption; literals and numeral hold, the R3 count reddens",
    ),
    Spec(
        name="P5c",
        subject=STORY_SOURCE,
        old='AUTHORED_FILES = ("index.html", "story.css", "story-data.js", "story.js")',
        new='AUTHORED_FILES = ("index.html", "story.css", "story-data.js")',
        test="test_story_text_carries_no_ruled_out_literal",
        prefix='"tamper-evident" in',
        note=(
            "the scan stops reading story.js (where the captions live): the presence control "
            "is what notices"
        ),
    ),
    Spec(
        name="P5b",
        subject=PAGE,
        old='    "฿30,001",\n',
        new="",
        test="test_the_literal_checker_flags_a_known_numeral",
        prefix='"฿30,001" in flagged',
        note="the baht-prefixed literal is dropped from the list; the positive control reddens",
    ),
    Spec(
        name="P6a",
        subject=S + "index.html",
        old='<script src="story-data.js?v=c1"></script>',
        new='<script src="ghost.js"></script>\n<script src="story-data.js?v=c1"></script>',
        test="test_every_story_reference_resolves",
        prefix="dangling == []",
        note="a reference to a file that does not exist; nothing escapes static/",
    ),
    Spec(
        name="P6c",
        subject=S + "story.css",
        old="url('../assets/fonts/IBMPlexMono-Medium.woff2')",
        new="url('../../main.py')",
        test="test_every_story_reference_resolves",
        prefix="escaping == []",
        note="a reference that resolves to a REAL file outside static/: not dangling, escaping",
    ),
    Spec(
        name="P6b",
        subject=S + "index.html",
        old='  <link rel="stylesheet" href="story.css?v=c1" />\n',
        new="",
        test="test_every_story_file_is_referenced_or_exempt",
        prefix="orphans == []",
        note="story.css is no longer loaded: an orphan, no stale exemption",
    ),
    Spec(
        name="P6d",
        subject=PAGE,
        old="_UNREFERENCED_STORY_FILES: dict[str, str] = {}",
        new='_UNREFERENCED_STORY_FILES: dict[str, str] = {"story.js": "probe"}',
        test="test_every_story_file_is_referenced_or_exempt",
        prefix="stale == []",
        note="an exemption for a file that IS referenced: no orphan, a stale exemption",
    ),
    Spec(
        name="P6e",
        subject=PAGE,
        old='    for name in ("index.html", "story.js", "story.css"):',
        new='    for name in ("story.css",):',
        test="test_the_story_parse_is_not_vacuous",
        prefix="refs_js >= 1",
        note="the reference scan reads only the stylesheet: zero .js references",
    ),
    Spec(
        name="P6f",
        subject=PAGE,
        old='    for name in ("index.html", "story.js", "story.css"):',
        new='    for name in ("story.js",):',
        test="test_the_story_parse_is_not_vacuous",
        prefix="refs_css >= 1",
        note="the reference scan reads only story.js: .js references remain, zero .css references",
    ),
    Spec(
        name="P7b",
        subject=APP_JS,
        old="href: '/story/'",
        new="href: '/story'",
        test="test_console_offers_the_story_link_in_a_new_tab",
        prefix="len(anchors) == 1",
        note="the link loses its trailing slash (an edge 404 by design): no anchor found",
    ),
    Spec(
        name="P7c",
        subject=APP_JS,
        old="        h('a', {\n          class: 'iconbtn', href: '/story/'",
        new="        h('button', {\n          class: 'iconbtn', href: '/story/'",
        test="test_console_offers_the_story_link_in_a_new_tab",
        prefix='re.search(r"h\\(',
        note="the link is rendered as a button, not an anchor",
    ),
    Spec(
        name="P7a",
        subject=APP_JS,
        old="href: '/story/', target: '_blank', rel: 'noopener',",
        new="href: '/story/', rel: 'noopener',",
        test="test_console_offers_the_story_link_in_a_new_tab",
        prefix='re.search(r"target',
        note="the link no longer opens a new tab",
    ),
    Spec(
        name="P7d",
        subject=APP_JS,
        old="target: '_blank', rel: 'noopener',",
        new="target: '_blank',",
        test="test_console_offers_the_story_link_in_a_new_tab",
        prefix='re.search(r"rel',
        note="the new tab keeps an opener reference",
    ),
    Spec(
        name="P7e",
        subject=APP_JS,
        old=(
            "if (Object.prototype.hasOwnProperty.call(VIEWS, 'I') && "
            "Object.prototype.hasOwnProperty.call(VIEWS, 'H')) {"
        ),
        new="if (true) {",
        test="test_console_offers_the_story_link_in_a_new_tab",
        prefix="gated",
        note="the I+H gate is removed: energy and procurement would link to an edge 404",
    ),
    Spec(
        name="P7f",
        subject=APP_JS,
        old="key: 'J'",
        new="key: 'K'",
        test="test_the_story_link_added_no_tab",
        prefix="registered == MEASURED_TAB_CENSUS",
        note="the tab census changes: the no-tab control reddens",
    ),
    Spec(
        name="P7g",
        subject="deploy/published/oct-fleet-maintenance/published.env",
        old="UI_PUBLISHED_VIEWS=A,C,F,H,I,J",
        new="UI_PUBLISHED_VIEWS=A,C,F,I,J",
        test="test_the_link_and_the_edge_agree_on_every_published_system",
        prefix="any(",
        note=(
            "no published system declares both I and H: the pairing's anti-vacuity assert "
            "(first) reddens"
        ),
    ),
    Spec(
        name="P7h",
        subject=CFG,
        old="  - path: ^/story/$",
        new="  - path: ^/storyX/$",
        test="test_the_link_and_the_edge_agree_on_every_published_system",
        prefix="[row for row",
        note=(
            "fleet declares I and H but its edge stops admitting /story/: link and edge " "disagree"
        ),
    ),
    Spec(
        name="P11a",
        subject=S + "story.css",
        old="url('../assets/fonts/IBMPlexSans-Regular.woff2')",
        new="url('/assets/fonts/IBMPlexSans-Regular.woff2')",
        test="test_every_story_reference_is_relative_and_in_bounds",
        prefix="not_relative == []",
        note=(
            "a root-relative font URL (still same-origin, so AC-1 stays green): the relative "
            "assert reddens first"
        ),
    ),
    Spec(
        name="P11c",
        subject=S + "story.css",
        old="url('../assets/fonts/IBMPlexMono-Medium.woff2')",
        new="url('../assets/app.js')",
        test="test_every_story_reference_is_relative_and_in_bounds",
        prefix="out_of_bounds == []",
        note=(
            "a relative reference to a REAL file outside story/ and assets/fonts/: relative "
            "holds, the bounds assert reddens"
        ),
    ),
    Spec(
        name="P11d",
        subject=STORY_SOURCE,
        old="    return _REFERENCE_PATTERNS[kind].findall(text)",
        new="    return []",
        test="test_every_story_reference_is_relative_and_in_bounds",
        prefix="set(owners)",
        note=(
            "the parser reads nothing: no bad reference is found, the owners anti-vacuity "
            "assert reddens"
        ),
    ),
    Spec(
        name="P11b",
        subject=PAGE,
        old='if ref in external or ref.startswith("/")]',
        new="if ref in external]",
        test="test_the_relative_checker_flags_a_root_relative_url",
        prefix="flagged ==",
        note=(
            "the checker stops recognising a leading slash; the positive control on a "
            "root-relative font URL reddens"
        ),
    ),
)

PAGE_EXEMPTIONS: tuple[Exemption, ...] = (
    Exemption(
        owner="test_every_story_file_is_admitted_by_a_story_ingress_row",
        prefix="not subdirs",
        reason=(
            "needs a DIRECTORY inside story/; the driver mutates file bytes and cannot "
            "create a directory entry"
        ),
    ),
    Exemption(
        owner="test_the_story_parse_is_not_vacuous",
        prefix="files",
        reason=(
            "needs story/ to hold no files; the driver mutates file bytes and cannot delete "
            "directory entries (the sibling asserts in this test are witnessed by P6e/P6f)"
        ),
    ),
)

DRIFT_PROBES: tuple[Spec, ...] = (
    Spec(
        name="P4-proc",
        subject=DRIFT,
        old='_PROCEDURE_ID = "governed_repair_approval"',
        new='_PROCEDURE_ID = "governed_repair_approval_x"',
        test="test_steps_and_gates_equal_the_loaded_procedure",
        owner="_procedure",
        prefix="len(matches) == 1",
        note="the procedure lookup finds nothing: the helper's uniqueness assert reddens",
    ),
    Spec(
        name="P4-ceil",
        subject="verticals/fleet_maintenance/data_adapter/synthetic.py",
        old=(
            '            "odometer_km": 254_300.0,\n'
            '            "minor_repair_ceiling_thb": 5001.0,'
        ),
        new=(
            '            "odometer_km": 254_300.0,\n'
            '            "minor_repair_ceiling_thb": 5000.0,'
        ),
        test="test_rule_constants_equal_sourcing_and_the_seed",
        owner="_real_ceiling",
        prefix="len(ceilings) == 1",
        note="truck-03's seed ceiling diverges: the one-ceiling helper assert reddens",
    ),
    Spec(
        name="P4a",
        subject=DATA,
        old='["Truck", "Vendor", "Depot",',
        new='["Truck", "Depot",',
        test="test_object_types_equal_the_ontology",
        prefix="(sorted(pinned)",
        note="the block drops Vendor",
    ),
    Spec(
        name="P4b",
        subject=DATA,
        old='["truck_at_depot", "Truck", "Depot"]',
        new='["truck_at_depot", "Truck", "Vendor"]',
        test="test_link_types_equal_the_ontology",
        prefix="pinned == real",
        note="a link type points at the wrong object",
    ),
    Spec(
        name="P4c0",
        subject=DRIFT,
        old='if prop.get("type") == "ref" and prop.get("target") in types',
        new='if prop.get("type") == "reference" and prop.get("target") in types',
        test="test_undeclared_refs_equal_the_refs_the_ontology_leaves_undeclared",
        prefix="real",
        note="the ref reading matches nothing: the non-empty control (first) reddens",
    ),
    Spec(
        name="P4c",
        subject=DATA,
        old='        ["RepairCase", "Truck"],\n',
        new="",
        test="test_undeclared_refs_equal_the_refs_the_ontology_leaves_undeclared",
        prefix="pinned == real",
        note="the block drops an undeclared ref; the reading still finds refs",
    ),
    Spec(
        name="P4d",
        subject=DATA,
        old=(
            '{"id": "judge", "th": "เทียบเพดานซ่อมของคันนี้"},\n'
            '        {"id": "reshape", "th": "แปลงเป็นยอดใช้จ่าย"},'
        ),
        new=(
            '{"id": "reshape", "th": "แปลงเป็นยอดใช้จ่าย"},\n'
            '        {"id": "judge", "th": "เทียบเพดานซ่อมของคันนี้"},'
        ),
        test="test_steps_and_gates_equal_the_loaded_procedure",
        prefix="(",
        note="judge and reshape swap order",
    ),
    Spec(
        name="P4e",
        subject=DATA,
        old='{"min_amount": 5001, "role": "ผจก.เดินรถ"}',
        new='{"min_amount": 5000, "role": "ผจก.เดินรถ"}',
        test="test_tiers_equal_the_loaded_doa_ladder",
        prefix="pinned == real",
        note="a tier floor moves by one baht",
    ),
    Spec(
        name="P4f",
        subject=DATA,
        old='"sod": {"distinct_steps": ["intake", "approve"]}',
        new='"sod": {"distinct_steps": ["intake", "fulfill"]}',
        test="test_sod_and_event_kind_equal_the_loaded_procedure",
        prefix="(",
        note="the separation-of-duties pair names the wrong step",
    ),
    Spec(
        name="P4g",
        subject=DATA,
        old='"three_quote_threshold_thb": 30000,',
        new='"three_quote_threshold_thb": 29000,',
        test="test_rule_constants_equal_sourcing_and_the_seed",
        prefix="(",
        note="the pinned threshold drifts from sourcing.py",
    ),
    Spec(
        name="P4h",
        subject=DATA,
        old='"basis": "quotes_required"',
        new='"basis": "three_quotes"',
        test="test_every_case_outcome_is_the_real_rules_outcome",
        prefix="mismatches == []",
        note="case 1's pinned basis is no longer what the real rule returns",
    ),
    Spec(
        name="P4l",
        subject="verticals/fleet_maintenance/sourcing.py",
        old='THREE_QUOTE_THRESHOLD_THB = Decimal("30000")',
        new='THREE_QUOTE_THRESHOLD_THB = Decimal("50000")',
        test="test_every_case_outcome_is_the_real_rules_outcome",
        prefix="mismatches == []",
        note="mutates the PRODUCER, not the block: proves (h) reads the real function",
    ),
    Spec(
        name="P4i",
        subject=DATA,
        old='"distinct_vendors": 3, "sole_source": false,\n       "illustrative": false,',
        new='"distinct_vendors": 3, "sole_source": false,\n       "illustrative": true,',
        test="test_non_illustrative_cases_are_seeded_and_the_illustrative_one_is_not",
        prefix="(seed_matches",
        note=(
            "a seeded case is marked illustrative: it matches the seed, so "
            "illustrative_matches becomes 1"
        ),
    ),
    Spec(
        name="P4j",
        subject=DATA,
        old='"context_pack": "context pack"',
        new='"context": "context pack"',
        test="test_emitter_keys_equal_generate_all",
        prefix="(",
        note="an emitter key no longer names a generate_all output",
    ),
    Spec(
        name="P4k",
        subject=DATA,
        old=(
            '    "emitters": {\n      "pydantic": "Pydantic",\n      "orm": "ORM",\n'
            '      "sql": "SQL DDL",\n'
            '      "jsonschema": "JSON Schema",\n      "mcp": "MCP tools",\n'
            '      "typescript": "TypeScript",\n'
            '      "context_pack": "context pack"\n    },'
        ),
        new='    "emitters": {},',
        test="test_the_block_is_well_formed",
        prefix="(counts",
        note="the emitters map is emptied (still valid JSON): the well-formedness assert reddens",
    ),
)

_VISITOR = "test_a_published_visitor_reaches_the_story_and_its_data_is_the_real_rules"

SCEN_PROBES: tuple[Spec, ...] = (
    Spec(
        name="P8-root",
        subject="services/api/static/index.html",
        old='<meta name="ui-profile" content="dev" />',
        new='<meta name="ui-profile" content="dev-anchor-removed" />',
        test=_VISITOR,
        prefix="console.status_code == 200",
        note=(
            "the console index fails loud on the published profile: the visitor's first GET "
            "is a 500"
        ),
    ),
    Spec(
        name="P8-appjs",
        subject="services/api/static/index.html",
        old='<script src="assets/app.js?v=c52"></script>',
        new='<script src="assets/app-main.js?v=c52"></script>',
        test=_VISITOR,
        prefix='"assets/app.js" in console.text',
        note="the console stops loading app.js",
    ),
    Spec(
        name="P8-link",
        subject=APP_JS,
        old="href: '/story/'",
        new="href: '/explainer/'",
        test=_VISITOR,
        prefix="\"href: '/story/'\" in",
        note="the console no longer carries the link the visitor clicks",
    ),
    Spec(
        name="P8-page",
        subject=MAIN,
        old="        if isinstance(response, FileResponse) and self._is_root_index(response):",
        new=(
            "        if isinstance(response, FileResponse) and "
            'str(response.path).endswith("index.html"):'
        ),
        test=_VISITOR,
        prefix="page.status_code == 200",
        note="Trap 1 returns: the console loads, the story page is a 500",
    ),
    Spec(
        name="P8-csp",
        subject=MAIN,
        old='        response.headers["Content-Security-Policy"] = _OCT_CSP',
        new="        pass",
        test=_VISITOR,
        prefix='page.headers.get("content-security-policy")',
        note="the page is served without the console CSP",
    ),
    Spec(
        name="P8b",
        subject=S + "index.html",
        old='<script type="module" src="story.js?v=c1"></script>',
        new='<script type="module" src="stori.js?v=c1"></script>',
        test=_VISITOR,
        prefix="failed == {}",
        note="the served page references a file that 404s",
    ),
    Spec(
        name="P8-set",
        subject=S + "index.html",
        old='  <link rel="stylesheet" href="story.css?v=c1" />\n',
        new="",
        test=_VISITOR,
        prefix="{",
        note=(
            "the served page never requests story.css: nothing fails, the required-file set "
            "is incomplete"
        ),
    ),
    Spec(
        name="P8-three",
        subject=SCEN,
        old=(
            "    assert len(three.encode()) > 100_000, "
            '"the served Three.js is not a real library build"'
        ),
        new=(
            "    assert len(three.encode()) > 1_000_000, "
            '"the served Three.js is not a real library build"'
        ),
        test=_VISITOR,
        prefix="len(three.encode())",
        note=(
            "floor raised above the vendored build's measured 670,681 bytes: proves the size "
            "assert reads the served body (a same-size substitute cannot be written as a text "
            "mutation of a 655 KB minified file)"
        ),
    ),
    Spec(
        name="P8a",
        subject=DATA,
        old='"basis": "under_threshold"',
        new='"basis": "three_quotes"',
        test=_VISITOR,
        prefix='case["expected"] == real',
        note="case 3's served basis disagrees with the real rule",
    ),
    Spec(
        name="P8-count",
        subject=DATA,
        old=(
            '"outcome": "approved"}},\n'
            '      {"truck": "truck-03", "what": "เกียร์เสียงดัง", "amount_thb": 15000, '
            '"distinct_vendors": 1, "sole_source": false,\n'
            '       "illustrative": false,\n'
            '       "expected": '
            '{"breach": true, "sourcing_pass": true, "basis": "under_threshold", '
            '"tier_role": "ผจก.เดินรถ", "outcome": "approved"}}'
        ),
        new='"outcome": "approved"}}',
        test=_VISITOR,
        prefix="checked >= 3",
        note="the served block carries two cases (both still correct): only the count reddens",
    ),
)

SCEN_EXEMPTIONS: tuple[Exemption, ...] = (
    Exemption(
        owner="_ladder",
        prefix="approve.governance_content is not None",
        reason=(
            "type narrowing for Step.governance_content (Optional); removing the approve "
            "step's governance content from procedures.yaml fails load_procedures validation "
            "before this line is reached"
        ),
    ),
)

BATTERIES: tuple[BatterySpec, ...] = (
    BatterySpec("plan-0126-story-page.json", PAGE, PAGE_PROBES, PAGE_EXEMPTIONS),
    BatterySpec("plan-0126-story-drift.json", DRIFT, DRIFT_PROBES),
    BatterySpec("plan-0126-story-scenario.json", SCEN, SCEN_PROBES, SCEN_EXEMPTIONS),
)


def _committed(root: Path, name: str) -> str | None:
    path = root / BATTERY_DIR / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the generated JSON with the committed files; write nothing",
    )
    args = parser.parse_args(argv)

    generated = render(REPO_ROOT)
    if generated.errors:
        print("GENERATION ERRORS:")
        for error in generated.errors:
            print("  " + error)
        print("VERDICT: NOT-GENERATED")
        return 2

    drifted = 0
    for name, text in generated.files.items():
        probes, exemptions = generated.counts[name]
        if args.check:
            committed = _committed(REPO_ROOT, name)
            same = committed == text
            drifted += not same
            print(f"{'SAME' if same else 'DIFF'} {name}: probes={probes} exemptions={exemptions}")
            for line in [] if same else describe_drift(name, committed, text):
                print("  " + line)
        else:
            (REPO_ROOT / BATTERY_DIR / name).write_text(text, encoding="utf-8")
            print(f"wrote {name}: probes={probes} exemptions={exemptions}")

    if not args.check:
        print("VERDICT: GENERATED")
        return 0
    print(f"drifted={drifted} of {len(generated.files)}")
    print("VERDICT: IN-SYNC" if drifted == 0 else "VERDICT: DRIFT")
    return 0 if drifted == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
