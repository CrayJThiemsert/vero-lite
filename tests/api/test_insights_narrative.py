"""AC-5 — the deterministic A2 narrative (PLAN-0088 Step 2).

``render_impact_narrative`` is a pure template over the report, so these run
without a database. Two properties are asserted:

* **Every ฿ figure the prose cites is a value on the report** — the narrative
  cannot drift from the numbers it claims to summarise, and cannot invent one.
* **No ADR-0032 D5 forbidden vocabulary** appears in any reader-facing string.

The forbidden phrases are defined HERE, not in the modules under scan, so the
grep-style guard cannot match its own documentation. ADR-0032 D5 names exactly
these two and no more (see that ADR's D5 section, lines 224-226); extending this
tuple without an ADR that names the addition would be invention.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from services.api.models.insights import ImpactBucket
from services.api.routers.insights import render_impact_narrative

_FORBIDDEN_VOCABULARY = ("agi-ready", "self-modifying")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INSIGHTS_MODULES = (
    _REPO_ROOT / "services" / "api" / "routers" / "insights.py",
    _REPO_ROOT / "services" / "api" / "models" / "insights.py",
)

_MONEY = re.compile(r"~฿([\d,]+(?:\.\d+)?)")


def _buckets() -> list[ImpactBucket]:
    return [
        ImpactBucket(
            currency="THB",
            procedure_id="emergency_sourcing",
            facet_kind="avoided_outage",
            period="2026-06-01",
            run_count=3,
            facet_count=4,
            figures_missing=1,
            net_benefit_sum=Decimal("3600000"),
            net_benefit_avg=Decimal("1200000"),
        ),
        ImpactBucket(
            currency="USD",
            procedure_id="emergency_sourcing",
            facet_kind="avoided_outage",
            period="2026-06-02",
            run_count=2,
            facet_count=2,
            figures_missing=0,
            net_benefit_sum=Decimal("50000"),
            net_benefit_avg=Decimal("25000"),
        ),
    ]


def test_every_money_figure_cited_is_a_report_value() -> None:
    buckets = _buckets()
    text = render_impact_narrative("energy", buckets, ["seeded synthetic corpus"], 1)
    cited = {Decimal(m.replace(",", "")) for m in _MONEY.findall(text)}
    allowed = {b.net_benefit_sum for b in buckets} | {b.net_benefit_avg for b in buckets}
    assert cited, "the narrative must actually cite figures (guard against a vacuous pass)"
    assert cited <= allowed, f"narrative cites figures absent from the report: {cited - allowed}"
    # and it must not silently drop a bucket's headline figure
    assert {b.net_benefit_sum for b in buckets} <= cited


def test_narrative_labels_every_figure_provisional() -> None:
    text = render_impact_narrative("energy", _buckets(), [], 0)
    assert "provisional" in text.lower(), "ADR-0030 D5: the report is never authoritative"


def test_narrative_discloses_missing_figures_and_assumptions() -> None:
    text = render_impact_narrative("energy", _buckets(), ["fuel price held flat"], 7)
    assert "7 facet(s)" in text, "unreadable figures must be disclosed, not hidden"
    assert "fuel price held flat" in text, "ADR-0030 D3: assumptions travel with the figure"


def test_narrative_is_deterministic() -> None:
    a = render_impact_narrative("energy", _buckets(), ["x"], 2)
    b = render_impact_narrative("energy", _buckets(), ["x"], 2)
    assert a == b, "no LLM, no ambient state — the same report renders the same prose"


def test_empty_report_renders_without_inventing_a_figure() -> None:
    text = render_impact_narrative("energy", [], [], 0)
    assert _MONEY.findall(text) == [], "no buckets -> no ฿ claim"
    assert "provisional" in text.lower()


def test_no_forbidden_vocabulary_in_insights_modules() -> None:
    """ADR-0032 D5, held as a grep over the reader-facing modules."""
    for path in _INSIGHTS_MODULES:
        source = path.read_text(encoding="utf-8").lower()
        for phrase in _FORBIDDEN_VOCABULARY:
            assert phrase not in source, (
                f"{path.relative_to(_REPO_ROOT).as_posix()} contains ADR-0032 D5 "
                f"forbidden vocabulary: {phrase!r}"
            )


def test_no_forbidden_vocabulary_in_the_rendered_narrative() -> None:
    text = render_impact_narrative("energy", _buckets(), ["assumption"], 1).lower()
    for phrase in _FORBIDDEN_VOCABULARY:
        assert phrase not in text


def test_the_vocabulary_guard_fires_on_the_phrases_it_forbids() -> None:
    """Non-vacuity: a guard that matches nothing is worse than none."""
    offending = "our platform is AGI-ready and self-modifying".lower()
    assert [p for p in _FORBIDDEN_VOCABULARY if p in offending] == list(_FORBIDDEN_VOCABULARY)
    clean = "governed runs, audited end to end".lower()
    assert not [p for p in _FORBIDDEN_VOCABULARY if p in clean]
