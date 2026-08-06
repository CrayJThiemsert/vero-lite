"""PLAN-0100 Step 8 — the published deployment's COMMITTED configuration.

Closes AC-4 (every pinned value is pinned), AC-5 (no service publishes a port) and
AC-6(a)/(b) (the allowlist is enforced at the edge and the UI fetches nothing off
the two tables). AC-6(c) is the live compose smoke and belongs to Step 9.

**Why these tests read FILES rather than a running stack.** The published surface
is enforced by configuration, and configuration fails silently: a missing `^`
still parses, a `ports:` key still starts, a remotely-managed tunnel still serves.
None of those raise. So the oracle has to be the committed bytes.

**What that oracle CANNOT see, stated so a closeout cannot overstate it:**

* whether the running container's env matches this file (`API_AUTH_ENABLED=false`
  set at `docker run` time would leave every keyed route open and every test here
  would still pass — Step 9 case 1's keyless ``/whoami`` → **401** is the only
  thing that catches it);
* whether a SECOND connector joined `vero_oct` and reaches `app:8000` around the
  ingress entirely — that produces byte-identical output here (review finding 3);
* the per-IP rate cap, which is a Cloudflare **zone** rule with no file in this
  repo at all.

**The regex semantics modelled here are cloudflared's, not Python's convenience.**
cloudflared evaluates `r.Path.Regexp.MatchString(req.URL.Path)` — an UNANCHORED
search. Every match below therefore uses ``re.search`` and never ``re.fullmatch``.
That is load-bearing: with ``fullmatch`` a pattern that lost its ``^`` would still
pass here while leaking in production, so the test would agree with a broken file.
``test_the_anchors_are_load_bearing`` proves the distinction is real rather than
asserted. (Go's RE2 and Python's ``re`` differ on backtracking, not on any
construct these patterns use.)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tests.api.js_source import strip_js_comments

_DEPLOY = Path("deploy/published")
_COMPOSE = _DEPLOY / "docker-compose.yml"
_ENV = _DEPLOY / "published.env"
_INGRESS = _DEPLOY / "cloudflared" / "config.yml"
_ASSETS = Path("services/api/static/assets")

#: AC-6(a)'s set-equality target — PLAN-0100's published allow table expressed as
#: the anchored cloudflared patterns that implement it. Editing this set without
#: editing the PLAN (or the reverse) is exactly the drift this test exists to catch.
_ALLOW_PATTERNS = {
    r"^/$",
    r"^/assets/.+$",
    r"^/health$",
    r"^/meta$",
    r"^/objects/[^/]+$",
    r"^/procedures$",
    r"^/llm/status$",
    r"^/recommendations$",
    r"^/whoami$",
    r"^/recommendations/[^/]+/approve$",
    r"^/query$",
}

#: AC-4 — §Pinned values, plus the two Step 8 owed on its own (`OCT_VERTICAL`,
#: which was UNPINNED until Cray's typed ruling on 2026-08-06, and
#: `LLM_MAX_INFLIGHT`, whose "1" existed only as PLAN prose because the setting
#: defaults to 0 = unlimited and no committed file set it).
_PINNED_ENV = {
    "UI_PROFILE": "published",
    "OCT_VERTICAL": "energy",
    "API_AUTH_ENABLED": "true",
    "OLLAMA_HOST": "http://host.docker.internal:11434",
    "LLM_REQUEST_TIMEOUT_S": "25",
    "LLM_RETRY_BUDGET": "1",
    "LLM_MAX_INFLIGHT": "1",
    "PROMPT_LOG_ENABLED": "true",
    "PROMPT_LOG_DIR": "/var/log/vero/prompt-log",
    "TENANT_ID": "demo",
    "OCT_DEMO_SEED_OPERATE": "false",
}

#: Concrete URLs the published edge MUST serve. One per allow-table row, written
#: as a real path rather than a pattern so a mis-built regex fails here.
_MUST_SERVE = (
    "/",
    "/assets/app.js",
    "/health",
    "/meta",
    "/objects/Asset",
    "/procedures",
    "/llm/status",
    "/recommendations",
    "/whoami",
    "/recommendations/act-0001/approve",
    "/query",
)

#: Concrete URLs the published edge MUST deny (fall through to the catch-all 404).
#: Each carries the ruling that excluded it, because "why is this off" is the
#: question a future reader will actually have.
_MUST_DENY = {
    "/insights/query": "SD-1 — DB-backed; unhandled 500 under the DB-less posture",
    "/recommendations/act-0001/execute": "SD-1 — DB-backed, split off the approve row",
    "/runs": "default-deny (finding C-2 — a Tab A caller the drafting census missed)",
    "/runs/run-0001": "SD-1's C-3 disposition",
    "/runs/run-0001/gate/resolve": "SD-1's C-3 disposition",
    "/runs/run-0001/cancel": "default-deny",
    "/demo/hero/event": "D5(2) F4 — event mode excluded",
    "/demo/hero/governance": "Step 8 (Cray, 2026-08-06) — hero is bespoke per design partner",
    "/demo/hero/impact": "Step 8 (Cray, 2026-08-06) — hero is bespoke per design partner",
    "/warm": "D5(2)",
    "/sleep": "D5(2)",
    "/intake/generate": "D5(2)",
    "/intake/extract": "D5(2)",
    "/intake/defaults": "D5(2)",
    "/procedures/draft/classify": "SD-2",
    "/procedures/draft/build": "SD-2",
    "/procedures/draft/instantiate": "SD-2",
    "/audit/verify": "default-deny",
    "/api/cases": "SD-1(a) — DB-backed",
    "/api/exports/repair-spend/2026-06": "SD-1(a) — DB-backed",
}

#: AC-6(b) — every route-looking string the SPA assets contain, classified. A NEW
#: fetch to an unlisted route reddens `test_ac6b_...` because the scan finds a
#: string in none of these three sets.
_UI_ALLOWED = {
    "/meta",
    "/objects/",
    "/objects/Truck",
    "/procedures",
    "/query",
    "/recommendations",
    "/recommendations/",
    "/whoami",
    "/llm/status",
}
_UI_EXCLUDED = {
    "/api/cases",
    "/api/exports/repair-spend/",
    "/audit/verify",
    "/demo/hero/event",
    "/demo/hero/governance",
    "/demo/hero/impact",
    "/intake/defaults",
    "/intake/extract",
    "/intake/generate",
    "/procedures/draft/build",
    "/procedures/draft/classify",
    "/procedures/draft/instantiate",
    "/runs",
    "/runs/",
    "/sleep",
    "/warm",
}
#: Strings the scan matches that are NOT routes. Listed rather than filtered by a
#: cleverer regex, because every one of them is a judgement a reader should be able
#: to audit — a silent filter is where a real route would go to hide.
_UI_NOT_ROUTES = {
    "/approve": "URL SUFFIX concatenated onto '/recommendations/' + id",
    "/execute": "URL SUFFIX concatenated onto '/recommendations/' + id",
    "/gate/resolve": "URL SUFFIX concatenated onto '/runs/' + id",
    "/cancel": "URL SUFFIX concatenated onto '/runs/' + id",
    "/cover": "URL SUFFIX concatenated onto the exports base",
    "/ontology/": "a FILESYSTEM path built for display, view-story.js:1246 — never fetched",
}


def _read_env() -> dict[str, str]:
    """Parse the committed env file the way `docker compose --env-file` does."""
    values: dict[str, str] = {}
    for line in _ENV.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def _compose() -> dict:
    return yaml.safe_load(_COMPOSE.read_text(encoding="utf-8"))


def _ingress_rules() -> list[dict]:
    return yaml.safe_load(_INGRESS.read_text(encoding="utf-8"))["ingress"]


def _committed_patterns() -> set[str]:
    """The patterns the DEPLOYED edge will actually evaluate.

    ⚠️ Every assertion ABOUT ENFORCEMENT must read this, never `_ALLOW_PATTERNS`.
    The distinction is not pedantic — a non-vacuity probe caught it here: stripping
    the anchors off `^/query$` in config.yml reddened ONLY the set-equality test,
    because the anchoring and deny assertions were parametrized over the module's
    own constant, which is anchored by construction and therefore could never fail.
    `_ALLOW_PATTERNS` is the *table*, and its only legitimate use is the drift check
    that compares the table to the file.
    """
    return {rule["path"] for rule in _ingress_rules() if "path" in rule}


def _ui_route_strings() -> dict[str, set[str]]:
    """Every quoted route-looking string in the assets, comments stripped.

    The query string is stripped AFTER matching, never before: `/warm?wait=false`
    (api.js:177) is the live proof that a character class stopping at `?` makes a
    real excluded route invisible to the census.
    """
    found: dict[str, set[str]] = {}
    for js in sorted(_ASSETS.glob("*.js")):
        source = strip_js_comments(js.read_text(encoding="utf-8"))
        for match in re.finditer(r"['\"](/[a-z][A-Za-z0-9_/{}.=&?-]*)['\"]", source):
            found.setdefault(match.group(1).split("?", 1)[0], set()).add(js.name)
    return found


def _served_by(url: str, patterns: set[str]) -> bool:
    """True when any pattern admits `url` under cloudflared's own semantics."""
    return any(re.search(pattern, url) for pattern in patterns)


# --------------------------------------------------------------------------- #
# AC-4 — the published env profile
# --------------------------------------------------------------------------- #


def test_ac4_every_pinned_value_is_pinned() -> None:
    """Set-equality on §Pinned values: a missing key and a wrong value both fail."""
    env = _read_env()
    for key, expected in _PINNED_ENV.items():
        assert key in env, f"{key} is not pinned in {_ENV} — §Pinned values requires it"
        assert env[key] == expected, f"{key} is {env[key]!r}, §Pinned values pins {expected!r}"


def test_ac4_the_compose_file_reads_the_committed_env_file() -> None:
    """A pinned file nothing loads pins nothing."""
    app = _compose()["services"]["app"]
    assert _ENV.name in app.get("env_file", []), (
        f"the app service must load {_ENV.name}; otherwise every AC-4 assertion "
        "above is about a file the container never reads"
    )


def test_ac4_no_secret_is_committed() -> None:
    """CLAUDE.md §8. API_KEYS provisioning stays env-local, documented in README."""
    env = _read_env()
    for forbidden in ("API_KEYS", "TELEGRAM_BOT_TOKEN", "LINE_CHANNEL_ACCESS_TOKEN"):
        assert forbidden not in env, (
            f"{forbidden} is a SECRET and must never enter a committed file "
            "(CLAUDE.md §8) — provision it env-local on the host"
        )


# --------------------------------------------------------------------------- #
# AC-5 — no published ports
# --------------------------------------------------------------------------- #


def test_ac5_no_service_publishes_a_host_port() -> None:
    """D1(1): the tunnel is the only way in, so a host firewall slip cannot expose app."""
    for name, service in _compose()["services"].items():
        assert "ports" not in service, (
            f"service {name!r} declares a ports: key — the published project must "
            "publish nothing (ADR-0035 D1(1), 0035:266-274). The dev compose at the "
            "repo root keeps its ports and is unaffected (ADR-0003)."
        )


def test_the_project_is_exactly_app_plus_cloudflared_and_no_database() -> None:
    """SD-1 (no postgres) and SD-3 (no nginx), asserted as the service set itself."""
    services = set(_compose()["services"])
    assert services == {"app", "cloudflared"}, (
        f"the published project must be exactly app + cloudflared, found {sorted(services)} "
        "— no postgres (SD-1's DB-less ruling), no nginx (SD-3: the rate cap is a "
        "Cloudflare zone rule, not a limit_req)"
    )


def test_the_app_joins_only_the_one_network() -> None:
    """Review finding 3's boundary, as far as a file can carry it."""
    app = _compose()["services"]["app"]
    assert app.get("networks") == ["vero_oct"], (
        "app must join vero_oct and nothing else — a second network is a second "
        "way to reach app:8000 around the ingress allowlist"
    )


# --------------------------------------------------------------------------- #
# AC-6(a) — the allowlist is enforced at the edge
# --------------------------------------------------------------------------- #


def test_ac6a_the_ingress_allow_set_equals_the_allow_table() -> None:
    rules = _ingress_rules()
    committed = {rule["path"] for rule in rules if "path" in rule}
    assert committed == _ALLOW_PATTERNS, (
        f"ingress drifted from PLAN-0100's allow table.\n"
        f"  only in config.yml: {sorted(committed - _ALLOW_PATTERNS)}\n"
        f"  only in the table:  {sorted(_ALLOW_PATTERNS - committed)}"
    )


@pytest.mark.parametrize("pattern", sorted(_committed_patterns()))
def test_ac6a_every_pattern_is_anchored_at_both_ends(pattern: str) -> None:
    """Set-equality alone passes for an UNANCHORED allowlist that admits excluded routes."""
    assert pattern.startswith("^") and pattern.endswith("$"), (
        f"{pattern!r} is not anchored at both ends. cloudflared matches Path as an "
        "unanchored regex (r.Path.Regexp.MatchString), so an unanchored /query also "
        "admits the SD-1-excluded /insights/query"
    )


def test_ac6a_the_last_rule_is_the_catch_all_404() -> None:
    """The catch-all IS the deny-by-default enforcement (D5(2)), not decoration."""
    last = _ingress_rules()[-1]
    assert last == {"service": "http_status:404"}, (
        f"the final ingress rule must be the bare catch-all, found {last!r} — "
        "without it cloudflared has no deny arm and the allowlist enforces nothing"
    )
    assert all("path" in rule for rule in _ingress_rules()[:-1]), (
        "a rule without a path before the catch-all matches everything and shadows "
        "every rule below it"
    )


def test_ac6a_the_tunnel_is_locally_managed() -> None:
    """A token-only remote tunnel moves the ingress map out of the repo, voiding this AC."""
    config = yaml.safe_load(_INGRESS.read_text(encoding="utf-8"))
    assert "credentials-file" in config and "tunnel" in config, (
        "config.yml must declare a locally-managed tunnel (tunnel + credentials-file). "
        "A remotely-managed TUNNEL_TOKEN tunnel keeps the ingress map in the Cloudflare "
        "dashboard, where this test cannot see it and would keep passing regardless"
    )


@pytest.mark.parametrize("url", _MUST_SERVE)
def test_ac6a_the_allowed_routes_are_admitted(url: str) -> None:
    assert _served_by(
        url, _committed_patterns()
    ), f"{url} is on the allow table but no COMMITTED pattern admits it"


@pytest.mark.parametrize("url,why", sorted(_MUST_DENY.items()))
def test_ac6a_the_excluded_routes_are_denied(url: str, why: str) -> None:
    assert not _served_by(
        url, _committed_patterns()
    ), f"{url} LEAKS through the COMMITTED allowlist — excluded by {why}"


def test_the_anchors_are_load_bearing() -> None:
    """Positive control: prove this suite can tell an anchored allowlist from a leaky one.

    Strip the anchors off the SAME patterns and the SAME assertions must break. If
    this test ever passes trivially — because the unanchored set denies just as much
    — then `test_ac6a_the_excluded_routes_are_denied` is proving nothing about the
    anchors and the whole anchoring argument would be unfalsifiable here.
    """
    committed = _committed_patterns()
    unanchored = {pattern.lstrip("^").rstrip("$") for pattern in committed}
    leaks = {url for url in _MUST_DENY if _served_by(url, unanchored)}
    assert "/insights/query" in leaks, (
        "the unanchored allowlist did NOT admit /insights/query, so this suite cannot "
        "distinguish anchored from unanchored patterns and its anchoring assertions "
        "are vacuous"
    )
    assert "/recommendations/act-0001/execute" in leaks
    assert not any(
        _served_by(url, committed) for url in leaks
    ), "a URL that leaks unanchored must be denied by the real, committed set"


# --------------------------------------------------------------------------- #
# AC-6(b) — the census tripwire
# --------------------------------------------------------------------------- #


def test_ac6b_every_route_the_ui_references_is_classified() -> None:
    """A new UI fetch to an unlisted route reddens here — that is the whole tripwire.

    The three sets are deliberately exhaustive rather than "allowed plus a filter":
    a string that is neither allowed, excluded, nor explicitly declared a non-route
    is a route nobody has ruled on, and that is precisely the state AC-6(b) exists to
    make impossible to reach silently.
    """
    scanned = _ui_route_strings()
    classified = _UI_ALLOWED | _UI_EXCLUDED | set(_UI_NOT_ROUTES)
    unclassified = {
        route: sorted(files) for route, files in scanned.items() if route not in classified
    }
    assert not unclassified, (
        "the SPA references route strings that are on NEITHER published table and are "
        f"not declared non-routes: {unclassified}. Add each to the allow table, the "
        "excluded table, or _UI_NOT_ROUTES with the reason it is not a route."
    )
    stale = classified - set(scanned)
    assert not stale, (
        f"these are classified but no longer appear in any asset: {sorted(stale)} — "
        "a census that keeps dead entries stops describing the UI it guards"
    )


@pytest.mark.parametrize("route", sorted(_UI_EXCLUDED))
def test_ac6b_the_ui_excluded_routes_are_actually_denied_at_the_edge(route: str) -> None:
    """Classification is a claim about the edge; this drives it through the real patterns."""
    probe = route if not route.endswith("/") else route + "x"
    assert not _served_by(probe, _committed_patterns()), (
        f"{route} is classified EXCLUDED for the published UI but the committed "
        f"ingress admits {probe} — the classification and the enforcement disagree"
    )
