"""UI contract for Tab I's accept control — PLAN-0112 Step 5 (AC-5's UI half).

There is no build step and no frontend test runner, so a CI tripwire for the UI must be
a Python test (``docs/conventions/ui.md`` §5). These are lexical checks over the shipped
asset: deliberately the weakest thing that is still an oracle, each stating what it
cannot prove.

**Why this module exists rather than leaning on the AC-3 scenario.**
``test_case_acceptance_fires_governed_run_scenario.py`` drives the real API walk and is
the stronger test by far — but it drives ``httpx``, not the browser. It would stay fully
green with the accept BUTTON deleted from ``view-case.js``, while
``deploy/published/oct-fleet-maintenance/card-copy.md`` goes on promising a published
visitor they can *press "accept this one"*. That gap is the whole subject here: the
published copy makes a claim about a control, so something has to pin the control.

**The rule this module protects is a SEAM, not a value.** ``accept_quote`` refuses a
non-lowest acceptance without a written reason (422). The view must not re-derive that
rule by comparing amounts client-side: a second copy drifts, and a drifted copy either
nags for a reason nobody owes or stays silent where the server would have demanded one
and hands the operator an unexplained 422. The view's own quote panel already refuses
exactly this for the three-quote verdict ("inventing a verdict here would be a second,
drifting copy of it"), so the property is house style, not a preference invented here.

**Honest limits.** These are static lexical checks over source text. They prove the
control and its 422 path are present in the SOURCE; they cannot prove the button renders,
that it is reachable on a phone, or that the reason box is legible. Rendering is verified
in the browser preview — evidence, never the gate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.api.js_source import strip_js_comments

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VIEW_CASE = _REPO_ROOT / "services" / "api" / "static" / "assets" / "view-case.js"
_INDEX_HTML = _REPO_ROOT / "services" / "api" / "static" / "index.html"

#: The tokens ``view-case.js`` and ``views.css`` carried BEFORE PLAN-0112 Step 5 edited
#: them. Compared for INEQUALITY, never pinned to the new value: pinning would turn every
#: future legitimate bump into a false RED, and the property worth protecting is "it moved
#: when the asset moved", not "it equals c46".
_PRE_STEP5_TOKENS = {"view-case.js": "c45", "views.css": "c47"}

#: A DIRECT comparison of a quote amount against a lowest/cheapest figure.
_DIRECT_COMPARISON = re.compile(
    r"amount_thb\s*[<>]|[<>]=?\s*[\w.]*(?:lowest|amount_thb)|(?:lowest|cheapest)\w*\s*[<>]"
)
#: Ways to AGGREGATE a list down to a minimum. Deliberately broad in shape, because the
#: first version of this guard enumerated `Math\.min\s*\(` and was proven vacuous against
#: a planted ``Math.min.apply(...)`` — it passed 7/7 with the forbidden rule present.
_AGGREGATOR = re.compile(r"Math\.(?:min|max)\b|\.sort\s*\(|\.reduce\s*\(")
#: ...but an aggregator only offends when it is working on a quote amount. A bare
#: ``.sort(`` ban would redden the day someone sorts the CASE LIST by date — unrelated
#: work — and a tripwire that fires on unrelated work is one that gets weakened by
#: whoever hits it. Verified before adoption: fires on all six realistic ways to compute
#: the lowest client-side, silent on three benign aggregations, 0 hits on the clean file.
_AMOUNTISH = re.compile(r"amount_thb|lowest|cheapest")
_NEAR = 120


def _client_side_comparisons(source: str) -> list[str]:
    """Every place the view computes or compares a lowest quote figure itself."""
    hits = [m.group(0) for m in _DIRECT_COMPARISON.finditer(source)]
    hits += [
        m.group(0)
        for m in _AGGREGATOR.finditer(source)
        if _AMOUNTISH.search(source[max(0, m.start() - _NEAR) : m.end() + _NEAR])
    ]
    return hits


@pytest.fixture
def source() -> str:
    """``view-case.js`` with comments stripped.

    Stripped deliberately: this module asserts what the view DOES. A claim that survives
    only in a comment is not a control, and an absence satisfied only by commenting the
    offending line out is not an absence.
    """
    return strip_js_comments(_VIEW_CASE.read_text(encoding="utf-8"))


def test_the_source_slice_is_substantial(source: str) -> None:
    """The anti-vacuity floor, before any presence or absence below is claimed.

    ``strip_js_comments`` on an unreadable or restructured file could return something
    tiny, and every assertion in this module would then pass or fail for a reason that
    has nothing to do with the accept control.
    """
    assert len(source) > 4000, (
        f"view-case.js stripped to {len(source)} chars — too small to be the shipped "
        "view. Every other assertion here would be reading the wrong thing."
    )


def test_tab_i_posts_to_the_accepted_quote_route(source: str) -> None:
    """The control calls the route Step 5 put on the published allowlist.

    Asserted on the ROUTE and the METHOD together. The route string alone would also be
    satisfied by the read side, and Tab I has never had one.
    """
    assert "/accepted-quote" in source, (
        "view-case.js no longer references /accepted-quote. The ingress row admitting it "
        "and the card copy promising it both survive this deletion silently."
    )
    assert re.search(r"method:\s*'POST'", source), "no POST in view-case.js at all"


def test_the_accept_control_is_present_and_labelled(source: str) -> None:
    """A visitor has something to PRESS — not merely a function that exists.

    🔴 Both assertions here were rewritten after a probe defeated the first pair.
    Deleting the button's wiring and blanking its label left the module reporting
    **16 passed**, because ``"acceptQuote(" in source`` is satisfied by the function's
    own ``async function acceptQuote(`` definition and by ``submitReason``'s call, and
    ``"ตกลงใบนี้" in source`` is satisfied by the SUBSTRING inside the reason form's
    ``'ยืนยันตกลงใบนี้'``. Neither could tell a rendered control from dead code.

    So: the call is pinned at its RENDER site (``acceptQuote(q.quote_id``, the only site
    that a visitor's press reaches), and the label as a whole quoted literal.
    """
    assert "acceptQuote(q.quote_id" in source, (
        "nothing in the quote list calls acceptQuote(q.quote_id, …). The handler may "
        "still exist, but no rendered control reaches it — which is dead code wearing "
        "the shape of a feature, and card-copy.md promises a button."
    )
    assert re.search(r"class:\s*'pack-accept'", source), (
        "the accept button element is gone from the render. Its CSS rule gives it the "
        "44px touch target this phone-first view needs; without the element there is "
        "nothing to give it to."
    )
    assert re.search(r"'ตกลงใบนี้'", source), (
        "the accept control's Thai label is gone as a standalone literal. card-copy.md "
        'quotes it verbatim (TH กด "ตกลงใบนี้" / EN press "accept this one"), so the '
        "published copy and the screen have drifted apart. NOTE: a bare substring check "
        "passes on 'ยืนยันตกลงใบนี้' — the quotes in this pattern are load-bearing."
    )


def test_the_non_lowest_reason_is_demanded_by_the_server_not_recomputed(source: str) -> None:
    """The 422 path is what opens the reason box — the seam, not a second copy of a rule.

    🔴 The absence carries its own positive control. "No client-side amount comparison"
    is vacuously true of a file that does not mention amounts at all, which is exactly
    what a gutted view would look like — so the amounts the quote panel legitimately
    READS must be found first, before the absence of a COMPARISON means anything.
    """
    assert "422" in source, (
        "nothing in view-case.js reacts to a 422. The server refuses a non-lowest "
        "acceptance without a reason, so without this branch the visitor gets a dead "
        "button and no way to answer the one question the audit actually asks."
    )
    assert "reasonFor" in source, "the reason box is not scoped to the refused quote"

    # Positive control: the view genuinely handles quote amounts, so the negative below
    # is a statement about this file rather than about an empty one.
    assert "amount_thb" in source, (
        "positive control FAILED: view-case.js does not mention amount_thb, so the "
        "'no client-side comparison' assertion below would pass vacuously"
    )

    # The absence itself: no comparison of a quote amount against a lowest/min figure.
    forbidden = _client_side_comparisons(source)
    assert not forbidden, (
        f"view-case.js compares quote amounts client-side ({forbidden}) — that is a "
        "second copy of `accept_quote`'s non-lowest rule. Post and let the server's 422 "
        "open the reason box; a drifting copy nags for reasons nobody owes, or stays "
        "silent where the server would have demanded one."
    )


@pytest.mark.parametrize(
    "planted",
    [
        # The exact shape that proved v1 of this matcher vacuous. Written with its
        # amount reference intact, as real code would have it: the scoping rule below
        # requires an aggregator to be NEAR a quote amount, so a sample that drops the
        # amount is testing the sample, not the guard.
        pytest.param(
            "const lo = Math.min.apply(null, qs.map(q => Number(q.amount_thb)));",
            id="min-apply",
        ),
        pytest.param("const lo = Math.min(...qs.map(q => Number(q.amount_thb)));", id="min-spread"),
        pytest.param("const lo = qs.sort((a,b)=>a.amount_thb-b.amount_thb)[0];", id="sort-head"),
        pytest.param(
            "const lo = qs.reduce((m,q) => q.amount_thb < m ? q.amount_thb : m, 9);",
            id="reduce",
        ),
        pytest.param("if (q.amount_thb > lowest) { showReason(); }", id="direct"),
        pytest.param("if (lowest < q.amount_thb) { showReason(); }", id="reversed"),
    ],
)
def test_the_comparison_matcher_fires_on_a_planted_sample(planted: str) -> None:
    """🔴 The absence above is only as good as this matcher, and v1 was VACUOUS.

    The first version enumerated ``Math\\.min\\s*\\(`` and friends. A probe planted
    ``Math.min.apply(null, …)`` into the shipped view — an ordinary way to compute the
    lowest quote — and the whole module still reported **7 passed**: the forbidden rule
    was present and the guard could not see it.

    So the matcher is exercised against six realistic shapes here, in the same file that
    relies on it. An absence asserted by a matcher nobody proved can fire is not an
    absence; it is a green light with no bulb.
    """
    assert _client_side_comparisons(planted), (
        f"the matcher missed {planted!r} — a client-side lowest computation it must "
        "catch. Widen it; do NOT relax the assertion that depends on it."
    )


@pytest.mark.parametrize(
    "benign",
    [
        pytest.param(
            "state.cases.sort((a,b) => a.opened_at < b.opened_at ? 1 : -1);",
            id="sort-cases",
        ),
        pytest.param(
            "const n = cs.reduce((t,c) => t + (c.photos||[]).length, 0);",
            id="count-photos",
        ),
        pytest.param("const w = Math.max(labelLen, valueLen);", id="max-widths"),
    ],
)
def test_the_comparison_matcher_stays_quiet_on_unrelated_aggregation(benign: str) -> None:
    """The other half of a usable tripwire: it must not fire on work it does not govern.

    A guard that reddens when someone sorts the case list by date is a guard that gets
    weakened by whoever hits it next — which is how a tripwire dies quietly. The
    aggregation shapes only count when they occur near a quote amount, and this pins
    that scoping so a future widening cannot silently drop it.
    """
    assert not _client_side_comparisons(benign), (
        f"the matcher fired on {benign!r}, which has nothing to do with the non-lowest "
        "rule. Scope the aggregator check to quote amounts rather than banning sort()."
    )


def test_a_failed_accept_never_reports_success(source: str) -> None:
    """The unauthenticated case is named, because on the published profile it is likely.

    ``accept_quote`` resolves ``get_current_principal``, which is fail-closed under this
    system's ``API_AUTH_ENABLED=true``. A visitor who has not picked a persona gets a 401,
    and "pick a persona" is a fixable situation that must not read as a system fault.
    """
    assert "401" in source and "403" in source, (
        "view-case.js does not distinguish the fail-closed auth refusal on the accept "
        "path. On the published profile an anonymous accept is the COMMON first attempt."
    )


@pytest.mark.parametrize(("asset", "pre_token"), sorted(_PRE_STEP5_TOKENS.items()))
def test_each_step5_edited_asset_carries_a_bumped_cache_token(asset: str, pre_token: str) -> None:
    """A stale ``?v=`` serves the pre-Step-5 file, so a browser check would verify nothing.

    Both assets are covered because they were both edited and they fail independently:
    shipping the JS without the CSS gives an unstyled control with no touch target, which
    on the phone this view is built for is indistinguishable from no control at all.
    """
    html = _INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(rf"assets/{re.escape(asset)}\?v=([A-Za-z0-9._-]+)", html)
    assert match is not None, (
        f"index.html no longer references assets/{asset} with a ?v= token — the "
        "cache-bust convention is what makes a normal reload pick up an asset edit."
    )
    assert match.group(1) != pre_token, (
        f"{asset} still carries ?v={pre_token}, the token it had before PLAN-0112 Step 5 "
        "edited it. A reviewer reloading the demo would be served the pre-accept-control "
        "file and would report on a screen this PLAN did not build."
    )
