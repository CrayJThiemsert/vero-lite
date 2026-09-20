"""PLAN-0126 AC-8 — scenario: a published visitor reaches the explainer, and what they are
served is the real rules' data (CLAUDE.md §8).

This drives the REAL producer into the REAL consumer with nothing stubbed:

* producer — the app's static mount, under the published profile, serving the files
  that ship in the image;
* consumer — a visitor's browser, played here by following every reference the SERVED
  page makes (not the files on disk) and reading the data block out of the SERVED
  ``story-data.js`` body.

The last leg checks that served block against ``sourcing.compute_three_quote`` and the
loaded DOA ladder. A green here therefore means: a visitor who opens ``/story/`` on the
published profile gets a page whose every file loads under the console CSP, and whose
Act-4 outcomes are the outcomes the governed repair procedure would actually produce.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal
from urllib.parse import urljoin, urlsplit

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.config import settings
from services.api.main import _OCT_CSP, app
from services.engine.procedures.spec import load_procedures
from tests.api.story_source import AUTHORED_FILES, authored_text, extract_block, references
from verticals.fleet_maintenance import sourcing
from verticals.fleet_maintenance.data_adapter import synthetic

_BASE = "http://test"


@pytest.fixture
async def visitor() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url=_BASE) as http:
        yield http


def _ladder() -> list[tuple[int, str]]:
    procedure = next(
        p
        for p in load_procedures("fleet_maintenance").procedures
        if p.procedure_id == "governed_repair_approval"
    )
    approve = next(step for step in procedure.steps if step.step_id == "approve")
    assert approve.governance_content is not None  # claim: plan-0126-story-scenario/exempt-1
    return [(int(t.min_amount), str(t.approver_role)) for t in approve.governance_content.tiers]


async def test_a_published_visitor_reaches_the_story_and_its_data_is_the_real_rules(
    visitor: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "ui_profile", "published")

    # 1. The console loads, and it carries the link the visitor clicks.
    console = await visitor.get("/")
    assert console.status_code == 200  # claim: plan-0126-story-scenario/P8-root
    assert "assets/app.js" in console.text  # claim: plan-0126-story-scenario/P8-appjs
    app_js = await visitor.get("/assets/app.js")
    assert "href: '/story/'" in app_js.text  # claim: plan-0126-story-scenario/P8-link

    # 2. The explainer page itself, under the console CSP.
    page = await visitor.get("/story/")
    assert page.status_code == 200  # claim: plan-0126-story-scenario/P8-page
    assert (
        page.headers.get("content-security-policy") == _OCT_CSP
    )  # claim: plan-0126-story-scenario/P8-csp

    # 3. Every reference the SERVED page makes loads from the same mount.
    served: dict[str, str] = {"/story/": page.text}
    queue = [(f"{_BASE}/story/", "index.html", page.text)]
    statuses: dict[str, int] = {}
    while queue:
        base_url, name, text = queue.pop()
        for ref in references(name, authored_text(name, text)):
            url = urljoin(base_url, ref)
            path = urlsplit(url).path
            if path in statuses:
                continue
            response = await visitor.get(url)
            statuses[path] = response.status_code
            if path.endswith((".js", ".css")) and response.status_code == 200:
                served[path] = response.text
                file_name = path.rsplit("/", 1)[-1]
                # Follow the page's OWN files; the vendored library is a leaf, never parsed.
                if path.startswith("/story/") and file_name in AUTHORED_FILES:
                    queue.append((url, file_name, response.text))
    failed = {path: status for path, status in statuses.items() if status != 200}
    three = served.get("/story/three.module.min.js", "")
    print(f"served_refs={len(statuses)} failed={failed} three_bytes={len(three.encode())}")
    assert failed == {}  # claim: plan-0126-story-scenario/P8b
    assert (
        {
            "/story/story.css",
            "/story/story-data.js",
            "/story/story.js",
            "/story/three.module.min.js",
        }
        <= set(statuses)
    ), (
        f"the served page never referenced a file it needs: {sorted(statuses)}"
    )  # claim: plan-0126-story-scenario/P8-set
    assert (
        len(three.encode()) > 100_000
    ), "the served Three.js is not a real library build"  # claim: plan-0126-story-scenario/P8-three

    # 4. The data the visitor received is the real rules' data.
    block = extract_block(served["/story/story-data.js"])
    ladder = _ladder()
    ceiling = {truck["minor_repair_ceiling_thb"] for truck in synthetic.truck_records()}.pop()
    checked = 0
    for case in block["cases"]:
        passed, basis = sourcing.compute_three_quote(
            amount_thb=Decimal(case["amount_thb"]),
            distinct_vendor_count=case["distinct_vendors"],
            has_sole_source_justification=case["sole_source"],
        )
        breach = case["amount_thb"] >= ceiling
        role = [r for floor, r in ladder if case["amount_thb"] >= floor][-1]
        outcome = "ok" if not breach else ("approved" if passed else "fail")
        real = {
            "breach": breach,
            "sourcing_pass": passed,
            "basis": basis,
            "tier_role": role,
            "outcome": outcome,
        }
        assert (
            case["expected"] == real
        ), (
            f"served case {case['truck']} {case['amount_thb']}: {case['expected']} != {real}"
        )  # claim: plan-0126-story-scenario/P8a
        checked += 1
    print(f"cases_checked={checked}")
    assert checked >= 3  # claim: plan-0126-story-scenario/P8-count
