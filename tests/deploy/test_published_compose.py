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
_RUNBOOKS = sorted(Path("docs/runbooks").glob("published-demo-*.md"))

#: Registrable domains the published-deploy docs are allowed to name. Anything
#: else is treated as a leak of the real domain, which ADR-0035 D1(3) forbids
#: this repo from carrying. Extending this set is a deliberate act — add the
#: vendor or reference domain you mean, never the deployment's own.
_ALLOWED_DOMAINS = frozenset(
    {
        "cloudflare.com",
        "cloudflareaccess.com",
        "cfargotunnel.com",
        "github.com",
        # The registry the Dockerfile pulls `uv` from. Added when the bring-up
        # runbook started naming the base images a build has to fetch — a vendor
        # domain, added on purpose, which is the only way this set should grow.
        "ghcr.io",
        "example.com",
    }
)

#: Trailing labels treated as a real TLD. An allowlist rather than a denylist of
#: file extensions, because the dotted-token shape is shared by far more than
#: filenames: `sys.argv`, `cert.pem` and `rule.go` all look like hostnames to a
#: pattern, and no denylist of extensions excludes them. Deliberately omits the
#: ccTLDs that collide with extensions this repo uses (`.sh`, `.py`, `.md`,
#: `.ts`) — a domain under one of those would slip, which the test's docstring
#: states rather than hides.
_TLDS = frozenset(
    {
        "ai",
        "app",
        "biz",
        "cloud",
        "co",
        "com",
        "dev",
        "info",
        "io",
        "link",
        "net",
        "online",
        "org",
        "page",
        "site",
        "systems",
        "tech",
        "th",
        "tools",
        "uk",
        "us",
        "xyz",
    }
)

#: A dotted, all-lowercase token — the shape a hostname takes in prose, a URL or
#: a shell command. Case-sensitive on purpose: `r.Path.Regexp.MatchString` is not
#: a hostname, and requiring lowercase is what tells them apart without a list.
_DOTTED = re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+\b")

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


def _app_environment_names() -> set[str]:
    """The env-var NAMES the app service declares under `environment:`.

    Compose accepts both the list form (``- API_KEYS``) and the map form
    (``API_KEYS: ${API_KEYS}``). Reading only one of them would make the caller
    quietly vacuous the day someone reformats the file — the assertion would keep
    passing against an `environment:` block it can no longer see.
    """
    env = _compose()["services"]["app"].get("environment", [])
    if isinstance(env, dict):
        return set(env)
    return {str(item).split("=", 1)[0] for item in env}


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


def test_the_app_can_actually_receive_api_keys_from_the_host() -> None:
    """The other half of `test_ac4_no_secret_is_committed`, and it was missing.

    Keeping API_KEYS out of published.env is only half a design: the container
    still has to be able to RECEIVE it. `env_file` loads published.env and nothing
    else, and compose does not forward the host environment on its own — so
    without a pass-through the demo is unloginable no matter what the operator
    exports, and Step 9 case 1's positive control (keyed ``/whoami`` -> 200, the
    only evidence the demo is loginable at all) can never pass.

    Asserted as a NAME, never a value: the point is that the plumbing exists, and
    `test_no_api_key_digest_is_committed_in_the_compose_file` guards the other
    direction.
    """
    assert "API_KEYS" in _app_environment_names(), (
        "the app service must declare API_KEYS under `environment:` so the host's "
        "value reaches the container. README.md documents provisioning it "
        "env-local, but env_file only loads published.env — without this entry the "
        "variable is silently dropped and every keyed route stays 401 forever"
    )


def test_no_api_key_digest_is_committed_in_the_compose_file() -> None:
    """The pass-through must stay a NAME — a value here would be a committed secret.

    `test_ac4_no_secret_is_committed` reads published.env; nothing read the compose
    file, which is the other place an operator in a hurry would paste the map.
    A SHA-256 digest is 64 hex characters, so the shape is greppable without this
    test needing to know any real key.
    """
    text = _COMPOSE.read_text(encoding="utf-8")
    digests = re.findall(r"\b[0-9a-fA-F]{64}\b", text)
    assert not digests, (
        f"{_COMPOSE} contains {len(digests)} SHA-256-shaped literal(s) — API_KEYS "
        "maps sha256(raw-key) -> person_id and is a SECRET (CLAUDE.md §8). The "
        "compose file may name the variable, never carry its value"
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


def _deploy_docs() -> list[Path]:
    """Every committed file the published deployment is described by."""
    return [p for p in sorted(_DEPLOY.rglob("*")) if p.is_file()] + list(_RUNBOOKS)


def _registrable_domains(text: str) -> set[str]:
    """The last two labels of every hostname-shaped token in `text`."""
    found: set[str] = set()
    for token in _DOTTED.findall(text):
        labels = token.split(".")
        if len(labels) < 2:
            continue
        # Only a recognised TLD counts. This is what separates `cloudflare.com`
        # from `sys.argv`, `cert.pem`, `app.js` and `2025.8.1` — all of which have
        # the same dotted shape and none of which end in a TLD.
        if labels[-1] not in _TLDS:
            continue
        found.add(".".join(labels[-2:]))
    return found


def test_no_unknown_domain_appears_in_the_deploy_docs() -> None:
    """ADR-0035 D1(3), widened from `config.yml` to everything that describes the deploy.

    `test_no_ingress_rule_binds_a_hostname` guards the ingress file. It cannot see
    a runbook, a README or an env file — and a bring-up runbook is exactly where a
    real hostname wants to be pasted, because that is the value the operator is
    holding while writing it.

    Written as an ALLOWLIST of registrable domains rather than a search for the
    real one, which is the only form that is committable in a public repo: the
    test never has to know the domain in order to reject it, and it keeps working
    across a rename.

    Honest limit: this is a tripwire, not a proof. A hostname split across lines,
    written in mixed case, or ending in a TLD outside `_TLDS` slips through. It
    catches the realistic accident — a pasted URL or command — which is the
    failure mode that actually happens.

    RED when: any file under `deploy/` or a `published-demo-*` runbook names a
    registrable domain outside `_ALLOWED_DOMAINS`.
    """
    leaks: dict[str, set[str]] = {}
    for path in _deploy_docs():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # pragma: no cover — no binaries live here today
            continue
        unknown = _registrable_domains(text) - _ALLOWED_DOMAINS
        if unknown:
            leaks[str(path)] = unknown
    assert not leaks, (
        f"unexpected domain(s) in the published-deploy docs: {leaks}. ADR-0035 D1(3) "
        "keeps the domain out of this repo entirely — it belongs in DNS and the portal "
        "repo's ingress map, and nowhere else. Use a placeholder such as <DOMAIN>. If "
        "the name is a legitimate vendor or reference domain, add it to _ALLOWED_DOMAINS "
        "deliberately"
    )


def test_the_runbooks_name_the_compose_project_the_compose_file_declares() -> None:
    """A `docker compose -p <name>` that matches nothing fails by doing nothing.

    Found the hard way: the operations runbook drove all three of its PDPA
    prompt-log deletion paths through `-p vero-oct`, while the compose file
    declares `name: vero-published` (`vero_oct` is the NETWORK). Every one of
    those commands would have selected no project — and `docker compose exec`
    against a project that does not exist is an error the operator sees, but
    `find -delete` inside it never runs, which is the deletion silently not
    happening.

    Reads the project name from the COMPOSE FILE, never from a constant here, so
    renaming the project reddens this instead of leaving the runbooks stale.

    RED when: a runbook names a project the compose file does not declare, or the
    compose file's `name:` changes without the runbooks following.
    """
    declared = _compose().get("name")
    assert declared, "docker-compose.yml must declare a top-level `name:`"

    wrong: dict[str, set[str]] = {}
    for path in _RUNBOOKS:
        used = set(re.findall(r"docker compose -p (\S+)", path.read_text(encoding="utf-8")))
        if used - {declared}:
            wrong[str(path)] = used - {declared}
    assert not wrong, (
        f"runbook(s) name a compose project the compose file does not declare: {wrong}. "
        f"docker-compose.yml declares name: {declared!r}. A `-p` that matches nothing "
        "selects no services, so the command reports success at having done nothing"
    )


def test_no_ingress_rule_binds_a_hostname() -> None:
    """ADR-0035 D1(3)/L6 domain-ignorance, asserted rather than left to discipline.

    The domain lives in exactly one layer — DNS at the vendor plus the portal
    repo's cross-system ingress map — and *"nothing in this repo may reference the
    portal domain"* (0035:280-285). That is what makes a domain change cost a DNS
    re-point and no application change at all (L6, 0035:231).

    ``config.yml`` implements it by carrying no ``hostname:`` key, and until now
    only a comment said so. This test asserts the SHAPE that would let a domain in,
    never a domain value — so it is committable in a public repo and stays correct
    across any rename. A rule without ``hostname`` matches any host, which is
    right here: the tunnel only ever receives traffic for the hostname its own DNS
    route points at.

    RED when: any ingress rule gains a ``hostname:`` key.
    """
    bound = [rule for rule in _ingress_rules() if "hostname" in rule]
    assert not bound, (
        f"{_INGRESS} binds a hostname on {len(bound)} rule(s): {bound!r}. "
        "ADR-0035 D1(3) keeps the domain out of this repo entirely — a hostname "
        "here pins the deployment to one domain, so moving domains stops being a "
        "DNS re-point and becomes a code change, and the value itself leaks the "
        "domain into a public repo"
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
