"""The PLAN-0126 story batteries are exactly what their tracked generator produces.

Measured s309, the failure this closes: the generator lived outside git, the copy that
STATUS named was six probes behind the committed page battery, and nothing compared the
two. Regenerating from it would have deleted the AC-11 and AC-3 witnesses silently.

These tests fail in either direction — a spec edited without regenerating, or a JSON file
edited by hand — and the generator's own refusals carry positive controls, because a
refusal that never fires reads exactly like a tree with nothing to refuse.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.batteries.plan_0126_story_generator import (
    BATTERY_DIR,
    REPO_ROOT,
    Spec,
    anchor_error,
    describe_drift,
    render,
    resolve_key,
)
from tools.probe_battery._lint import lint_battery_file

EXPECTED_FILES = [
    "plan-0126-story-drift.json",
    "plan-0126-story-page.json",
    "plan-0126-story-scenario.json",
]
STORY_INDEX = "services/api/static/story/index.html"
PAGE_TESTS = "tests/api/test_story_page.py"


def _committed(name: str) -> str | None:
    path = REPO_ROOT / BATTERY_DIR / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def test_the_committed_story_batteries_equal_their_generator() -> None:
    generated = render(REPO_ROOT)
    assert generated.errors == [], "\n".join(
        [
            "the specs no longer address the tree — edit the generator, then regenerate:",
            *generated.errors,
        ]
    )
    assert sorted(generated.files) == EXPECTED_FILES

    mismatched = sorted(name for name, text in generated.files.items() if _committed(name) != text)
    print(f"files={sorted(generated.counts.items())} mismatched={mismatched}")
    assert mismatched == [], "\n".join(
        line
        for name in mismatched
        for line in describe_drift(name, _committed(name), generated.files[name])
    )


def test_the_generated_batteries_load_and_lint_clean_in_the_real_driver(
    tmp_path: Path,
) -> None:
    """Scenario: the real generator's output, read by the real driver's lint."""
    generated = render(REPO_ROOT)
    loaded: dict[str, int] = {}
    findings: list[str] = []
    for name, text in generated.files.items():
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        report = lint_battery_file(path, REPO_ROOT)
        loaded[name] = report.probes
        findings.extend(str(finding) for finding in report.findings)

    # The expectation is read from the COMMITTED files, not from the generator, so a
    # generator that emits nothing cannot agree with itself here.
    committed_counts = {
        name: len(json.loads(_committed(name) or "{}").get("probes", [])) for name in EXPECTED_FILES
    }
    print(f"loaded={loaded} committed={committed_counts} findings={len(findings)}")
    assert loaded == committed_counts
    assert findings == [], "\n".join(findings)


def _anchor_only(old: str) -> Spec:
    return Spec(name="X", subject=STORY_INDEX, old=old, new="", test="t", prefix="", note="")


def test_the_generator_refuses_an_anchor_that_does_not_occur_exactly_once() -> None:
    absent = anchor_error(REPO_ROOT, _anchor_only("<no-such-anchor-in-the-story-page>"))
    repeated = anchor_error(REPO_ROOT, _anchor_only("<script"))
    print(f"absent={absent!r}\nrepeated={repeated!r}")
    assert absent is not None
    assert repeated is not None


def test_the_generator_refuses_a_claim_that_does_not_resolve_to_exactly_one() -> None:
    missing: list[str] = []
    resolve_key(REPO_ROOT, PAGE_TESTS, "no_such_owner_in_the_page_tests", "", missing)
    ambiguous: list[str] = []
    # An empty prefix matches every claim of an owner that asserts more than once.
    owner = "test_every_story_file_is_admitted_by_a_story_ingress_row"
    resolve_key(REPO_ROOT, PAGE_TESTS, owner, "", ambiguous)
    print(f"missing={missing}\nambiguous={ambiguous}")
    assert missing != []
    assert ambiguous != []
