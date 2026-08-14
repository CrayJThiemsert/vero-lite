"""PLAN-0103 Steps 4b/5 — the CROSS-PROFILE invariants of `deploy/published/`.

Closes AC-4 (per-system network + project isolation), AC-5 (no shadow registry),
and the per-instance half of Step 5 (each system's allowlist gets its OWN
set-equality + anchoring guard — ADR-0036 D5: "the guard extends per instance").

**Why a second module rather than parametrizing `test_published_compose.py`.**
That module is energy's DEEP single-system suite and says so in its own `_DEPLOY`
comment. What is new here is not "the same assertions, three times" — it is a
different class of claim: statements about the profiles *as a set* (no two share a
project, no file outside them lists two of them). Those have no single-system form.

**The failure this module exists to prevent is silent.** Two compose projects on
one Docker network let each system's connector reach the other's `app:8000` and
skip that system's allowlist entirely — and every allowlist assertion would stay
green throughout, because they read a committed file and cannot see who else is on
the wire. ADR-0035 (`0035:490-493`) names a shared network as grounds for
reopening the whole hosting arrangement.

**Vacuity is the live risk here, not correctness.** Every test below is driven by
a glob, and an empty glob makes a parametrized test vanish rather than fail. Two
assertions exist purely to stop that: ``test_discovery_is_not_vacuous`` (the glob
found the profiles at all) and ``test_every_discovered_profile_has_an_expected_
allow_set`` (a NEW profile cannot ride along uncovered — it must be given a table
here or it reddens). Without the second, adding `oct-fleet-maintenance/` would
silently receive zero assertions while the suite reported green.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

_DEPLOY_ROOT = Path("deploy/published")
_RUNBOOKS = sorted(Path("docs/runbooks").glob("published-demo-*.md"))

#: The label convention (`0036:142-147`). A profile directory is `oct-<system>`.
_PROFILE_GLOB = "oct-*"

#: The host checkout path the runbooks use in `ssh <host> …` commands. Stripped so
#: a Windows host path can be resolved against this repo (PLAN-0103 Step 4b — two
#: such paths went stale in Step 4a precisely because they are not repo-relative
#: and a POSIX-shaped search never saw them).
_HOST_CHECKOUT_PREFIX = r"C:\projects\vero-lite"


def _profiles() -> list[Path]:
    """Every committed per-system profile directory, sorted."""
    return sorted(p for p in _DEPLOY_ROOT.glob(_PROFILE_GLOB) if p.is_dir())


def _profile_ids() -> list[str]:
    return [p.name for p in _profiles()]


def _compose(profile: Path) -> dict:
    return yaml.safe_load((profile / "docker-compose.yml").read_text(encoding="utf-8"))


def _ingress_paths(profile: Path) -> list[str]:
    """The `path:` patterns of a profile's allowlist, in file order."""
    doc = yaml.safe_load((profile / "cloudflared" / "config.yml").read_text(encoding="utf-8"))
    return [rule["path"] for rule in doc["ingress"] if "path" in rule]


#: Each system's published allow set — the set-equality target Step 5 requires
#: "per instance". These are DELIBERATELY written out per system rather than
#: derived from the files: a table computed from the thing it checks asserts
#: nothing. Editing a `config.yml` without editing its row here is exactly the
#: drift these tests exist to catch.
_EXPECTED_ALLOW: dict[str, set[str]] = {
    "oct-energy": {
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
    },
    # `G,F`, default G, no personas (SD-3/SD-4 joint ruling, Cray, typed s218).
    # Adds the two hero reads; drops /objects, /recommendations{,/…/approve},
    # /query and — the load-bearing one — /whoami. The reasoning for each drop is
    # in that file's header; the reasoning for /whoami is that Tab G's Approve
    # button calls H-family routes this system does not admit, so a login would
    # lead to a control that 404s.
    "oct-procurement": {
        r"^/$",
        r"^/assets/.+$",
        r"^/health$",
        r"^/meta$",
        r"^/procedures$",
        r"^/demo/hero/governance$",
        r"^/demo/hero/impact$",
    },
    # `A,C,F,H,I,J`, default A (SD-3, Cray typed s218). The ONLY profile that
    # re-admits routes PLAN-0100 excluded, and the only one with personas and a
    # database — which is why H, I and J appear here and nowhere else.
    #
    # The two re-admission bases differ and are NOT interchangeable:
    #   * I/J were excluded on SD-1(a) DB-less grounds — a basis that DISSOLVES
    #     here, because LOCKED-1 grants this system a Postgres;
    #   * H's five routes were excluded by default-deny + SD-1's C-3, which is not
    #     a storage fact, so each is admitted on its own written basis instead.
    # Both are spelled out per row in that system's config.yml header.
    "oct-fleet-maintenance": {
        r"^/$",
        r"^/assets/.+$",
        r"^/health$",
        r"^/meta$",
        # ON here and OFF procurement: this is the system with personas (LOCKED-5),
        # and without login the refused-then-granted beat is unreachable.
        r"^/whoami$",
        # Tab A — the landing view
        r"^/objects/[^/]+$",
        r"^/recommendations$",
        r"^/recommendations/[^/]+/approve$",
        # Tab C — the assisted route
        r"^/query$",
        # Tab F
        r"^/procedures$",
        # Tab H — five routes, five separate decisions
        r"^/runs$",
        r"^/runs/[^/]+$",
        r"^/runs/[^/]+/gate/resolve$",
        r"^/runs/[^/]+/cancel$",
        r"^/audit/verify$",
        # Tab I — visitor-writable; the surface AC-11's RoPA must cover
        r"^/api/cases$",
        r"^/api/cases/[^/]+/photos$",
        r"^/api/cases/[^/]+/evidence$",
        r"^/api/cases/[^/]+/quotes$",
        # Tab J — the COVER only; the `.csv` sibling stays off (Cray declined it
        # at s192, and the `/cover$` anchor is what keeps that ruling in force)
        r"^/api/exports/repair-spend/[^/]+/[^/]+/cover$",
    },
}

#: Routes that must NOT be admitted by ANY published system, whatever its tab set.
#: A per-system table would let a future profile quietly reopen one of these; a
#: shared floor cannot be lowered by adding a directory.
_UNIVERSALLY_DENIED = {
    "/warm": "D5(2) — warms MS-S1; never anonymous",
    "/sleep": "D5(2)",
    "/intake/generate": "D5(2) — authoring surface",
    "/intake/extract": "D5(2)",
    "/intake/defaults": "D5(2)",
    "/procedures/draft/classify": "SD-2 — authoring surface",
    "/procedures/draft/build": "SD-2",
    "/procedures/draft/instantiate": "SD-2",
    "/demo/hero/event": "D5(2) F4 — an UNAUTHENTICATED DB write",
    "/insights/query": "SD-1 — DB-backed; unhandled 500 under a DB-less posture",
}


# --------------------------------------------------------------------------- #
# Discovery — the anti-vacuity floor
# --------------------------------------------------------------------------- #


def test_discovery_is_not_vacuous() -> None:
    """The glob finds real profiles.

    Without this, an empty or mistyped glob would make every parametrized test
    below silently collect ZERO cases and the module would report green while
    asserting nothing at all.
    """
    found = _profiles()
    assert len(found) >= 2, (
        f"expected at least energy + procurement under {_DEPLOY_ROOT}/{_PROFILE_GLOB}, "
        f"found {[p.name for p in found]} — if this is right, the glob is wrong"
    )
    assert (_DEPLOY_ROOT / "oct-energy") in found


def test_every_discovered_profile_has_an_expected_allow_set() -> None:
    """A NEW profile directory cannot ride along uncovered.

    This is the test that makes the parametrization honest: adding a profile
    without giving it a row in `_EXPECTED_ALLOW` reddens HERE, rather than
    silently receiving zero allowlist assertions.
    """
    missing = [p.name for p in _profiles() if p.name not in _EXPECTED_ALLOW]
    assert not missing, (
        f"profile(s) {missing} have no `_EXPECTED_ALLOW` entry — every published "
        "system needs its own set-equality target (PLAN-0103 Step 5, ADR-0036 D5)"
    )


#: AC-3's committed artifact list, per profile. The card copy is the FIFTH and was
#: added by Step 8a — before it existed this tuple had four entries and the test
#: said so in its name, which is why AC-3 could not be ticked.
_REQUIRED_ARTIFACTS = (
    "docker-compose.yml",
    "published.env",
    "cloudflared/config.yml",
    "README.md",
    "card-copy.md",
)


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_a_profile_carries_every_committed_artifact(profile: Path) -> None:
    """AC-3: all five committed artifacts exist for every published system."""
    for rel in _REQUIRED_ARTIFACTS:
        assert (profile / rel).is_file(), f"{profile.name} is missing {rel}"


#: AC-9 asserts SECTION PRESENCE, never copy quality — "which has no oracle" is the
#: AC's own wording. These are the English headings because they are stable; the
#: Thai side is held to structural PARITY instead, so its wording stays free.
_CARD_SECTIONS_EN = ("Card name", "What you'll see", "First 90 seconds", "Call to action")


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_ac9_the_card_copy_is_bilingual_and_structurally_complete(profile: Path) -> None:
    """AC-9: both language sections present, and neither is a stub.

    The failure this actually catches is **one language drifting behind the
    other** — someone edits the English, ships, and the Thai card silently keeps
    describing an older demo. Rather than pin Thai wording (which would make every
    copy edit a test edit, and which AC-9 explicitly does not ask for), the Thai
    section is required to carry at least as many subsections as the English one.
    """
    text = (profile / "card-copy.md").read_text(encoding="utf-8")

    assert text.count("\n## TH") == 1, f"{profile.name}: expected exactly one `## TH` section"
    assert text.count("\n## EN") == 1, f"{profile.name}: expected exactly one `## EN` section"

    th_body, _, en_body = text.partition("\n## EN")
    _, _, th_body = th_body.partition("\n## TH")

    for heading in _CARD_SECTIONS_EN:
        assert f"### {heading}" in en_body, f"{profile.name}: EN section lacks `### {heading}`"

    th_sections = th_body.count("\n### ")
    en_sections = en_body.count("\n### ")
    assert th_sections >= en_sections, (
        f"{profile.name}: the Thai card has {th_sections} subsections against the "
        f"English card's {en_sections} — the two languages have drifted apart"
    )

    # A heading with nothing under it satisfies every check above, so the copy has
    # to actually be there. Deliberately a low bar: this is a stub detector, not a
    # quality judgement.
    for label, body in (("TH", th_body), ("EN", en_body)):
        prose = [
            line
            for line in body.splitlines()
            if line.strip() and not line.startswith("#") and not line.startswith("---")
        ]
        assert len(prose) >= len(_CARD_SECTIONS_EN), (
            f"{profile.name}: the {label} card has headings but almost no copy "
            f"({len(prose)} non-heading lines) — an empty stub would pass a "
            "presence-only check"
        )


# --------------------------------------------------------------------------- #
# AC-4 — per-system project + network isolation
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_ac4_the_project_name_is_the_directory_name(profile: Path) -> None:
    """The convention that makes a copied profile safe.

    A per-system literal is exactly what a copy-paste forgets, so the name is not
    freely chosen — it is DERIVED from the directory and checked here. A fourth
    system that inherits `oct-energy` by copying the file reddens instead of
    joining energy's project.
    """
    declared = _compose(profile).get("name")
    assert declared == profile.name, (
        f"{profile.name}/docker-compose.yml declares `name: {declared}` but must "
        f"declare `name: {profile.name}` — see deploy/published/README.md"
    )


def test_ac4_no_two_profiles_share_a_project_name() -> None:
    """Pairwise-distinct project names.

    Implied by the directory convention above, asserted independently anyway: this
    is the property ADR-0035 actually cares about, and it should not depend on the
    convention test still existing.
    """
    names = [_compose(p).get("name") for p in _profiles()]
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, f"two published systems share a compose project name: {duplicates}"


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_ac4_no_profile_declares_a_fixed_network_name(profile: Path) -> None:
    """The ANTI-BYPASS boundary, stated as an absence.

    Compose scopes an unnamed network under the project, so dropping the key makes
    collision structurally impossible rather than conventionally avoided. A fixed
    `name:` reintroduced in ANY profile puts two systems one copy-paste away from
    sharing a network — and every allowlist test would stay green through it.
    """
    for net_name, body in (_compose(profile).get("networks") or {}).items():
        declared = (body or {}).get("name")
        assert declared is None, (
            f"{profile.name} pins network `{net_name}` to the fixed name "
            f"`{declared}`. Drop the `name:` key: compose then scopes it as "
            f"`{profile.name}_{net_name}`, which cannot collide with another system."
        )


def test_ac4_no_two_profiles_share_a_container_or_volume_name() -> None:
    """Container and volume names are GLOBAL on the Docker daemon.

    Not covered by project scoping: two systems declaring `container_name:
    vero-published-app` collide on `up` even in different projects, and a shared
    volume name would have two systems writing ONE prompt log — which is a
    compliance artifact with a per-system retention story.
    """
    seen: dict[str, str] = {}
    for profile in _profiles():
        doc = _compose(profile)
        names = [
            svc["container_name"]
            for svc in (doc.get("services") or {}).values()
            if isinstance(svc, dict) and "container_name" in svc
        ]
        names += [
            (body or {}).get("name")
            for body in (doc.get("volumes") or {}).values()
            if (body or {}).get("name")
        ]
        for name in names:
            assert name not in seen, (
                f"`{name}` is declared by both {seen[name]} and {profile.name}; "
                "container and volume names are global on the daemon"
            )
            seen[name] = profile.name


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_the_build_context_resolves_to_a_real_dockerfile(profile: Path) -> None:
    """A build context is a relative path, and relative paths do not follow a move.

    ⚠️ This guard exists because its absence shipped a compose file that CANNOT
    BUILD. PLAN-0103 Step 4a moved each compose from `deploy/published/` down into
    `deploy/published/<system>/` and left `context: ../..` untouched — which now
    resolves to `deploy/`, a directory with no Dockerfile. Every profile authored
    by copying that one inherited it.

    It survived two sessions because nothing offline exercised it:
    `docker compose config --quiet` returns 0 on a context that does not exist, so
    the "all three composes validate" check reported clean over it. Only an actual
    `build` failed — with `failed to read dockerfile`, at the moment an operator
    would be mid-deploy.

    Asserting the resolved directory contains a Dockerfile is the cheap offline
    form of the check that only a real build otherwise makes.
    """
    build = ((_compose(profile).get("services") or {}).get("app") or {}).get("build") or {}
    context = build.get("context")
    assert context, f"{profile.name}'s app service declares no build context"

    resolved = (profile / context).resolve()
    assert resolved.is_dir(), (
        f"{profile.name}: build context `{context}` resolves to {resolved}, "
        "which is not a directory"
    )
    dockerfile = resolved / build.get("dockerfile", "Dockerfile")
    assert dockerfile.is_file(), (
        f"{profile.name}: build context `{context}` resolves to {resolved}, which "
        f"contains no {build.get('dockerfile', 'Dockerfile')}. `docker compose "
        "config` will NOT catch this — only a real build will, mid-deploy."
    )


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_ac3_no_service_publishes_a_host_port(profile: Path) -> None:
    """PLAN-0100 AC-5's property, preserved PER SYSTEM (PLAN-0103 AC-3).

    The whole topology depends on it: with no `ports:`, a host firewall mistake
    cannot expose `app` directly, because the only route in is the tunnel.
    """
    for svc_name, svc in (_compose(profile).get("services") or {}).items():
        assert "ports" not in svc, (
            f"{profile.name}'s `{svc_name}` publishes a host port — the published "
            "topology's only ingress is the tunnel"
        )


# --------------------------------------------------------------------------- #
# LOCKED-1 / ADR-0037 — the per-system database grant is a GRANT, not a default
# --------------------------------------------------------------------------- #

#: The one profile ADR-0037 grants a database to. A set rather than a string so a
#: second grant is a visible, deliberate edit here — which is the point: LOCKED-1
#: ruled the DB posture per system, and the ADR attached compliance obligations
#: (RoPA, retention, DSR path) to the grant. A profile that acquires a `postgres`
#: service by copy-paste would take the storage without the obligations.
_DB_GRANTED = {"oct-fleet-maintenance"}


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_only_a_granted_profile_declares_a_database(profile: Path) -> None:
    """DB-less is the default and the grant is per system (LOCKED-1, ADR-0037).

    Both directions are asserted. A profile that gains a database it was not
    granted takes on a personal-data store with no RoPA entry behind it; a granted
    profile that LOSES its database silently breaks the approve beat that is the
    whole reason the grant exists.
    """
    services = _compose(profile).get("services") or {}
    has_db = "postgres" in services
    if profile.name in _DB_GRANTED:
        assert has_db, (
            f"{profile.name} is the ADR-0037-granted system but declares no "
            "`postgres` service — Tabs H/I/J have nothing behind them"
        )
    else:
        assert not has_db, (
            f"{profile.name} declares a `postgres` service without a grant. "
            "LOCKED-1 keeps every other published system DB-less, and ADR-0037 "
            "attaches RoPA/retention/DSR obligations to any grant."
        )


def _env_items(service: dict) -> dict[str, str]:
    """Normalise a compose `environment:` block to a dict.

    Compose accepts BOTH a mapping (`KEY: value`) and a sequence
    (`- KEY=value`, or a bare `- KEY` host pass-through), and a real profile uses
    both in different services. A guard that understood only one form would read
    an empty dict for the other and pass over whatever it contained.
    """
    env = service.get("environment") or {}
    if isinstance(env, dict):
        return {k: "" if v is None else str(v) for k, v in env.items()}
    out: dict[str, str] = {}
    for entry in env:
        key, sep, value = str(entry).partition("=")
        out[key] = value if sep else ""
    return out


#: Env values that carry a credential: an explicit password, or a connection
#: string (CLAUDE.md §8 names both — "passwords" AND "connection strings with
#: credentials").
_CREDENTIAL_BEARING = ("PASSWORD", "DATABASE_URL")


def test_no_profile_commits_a_database_credential() -> None:
    """Every credential-bearing env value is a REQUIRED host-env pass-through.

    This repo is public (CLAUDE.md §8) and the granted database stores
    visitor-typed personal data, so a password may be neither a literal nor a
    DEFAULTED interpolation — a default lets the system boot on a value that is
    committed in all but name.

    ⚠️ Scans EVERY service and both env forms, not just `postgres.POSTGRES_PASSWORD`.
    A non-vacuity probe found the narrower version green while the credential in
    the app service's `DATABASE_URL` connection string had been switched to a
    default: the assertion was reading a field the violation never touched.
    """
    for profile in _profiles():
        if profile.name not in _DB_GRANTED:
            continue
        for svc_name, svc in (_compose(profile).get("services") or {}).items():
            for key, value in _env_items(svc).items():
                if not any(marker in key.upper() for marker in _CREDENTIAL_BEARING):
                    continue
                assert "${" in value and ":?" in value, (
                    f"{profile.name}'s `{svc_name}.{key}` must take its credential "
                    f"from a REQUIRED host-env pass-through (`${{VAR:?message}}`), "
                    f"got {value!r}. A literal commits a secret to a public repo; "
                    "a `:-` default lets the system boot on a known one."
                )


#: AC-6's named secrets, per profile. `API_KEYS` maps sha256(raw key) -> person_id;
#: `UI_DEMO_PERSONA_KEYS` maps person_id -> the RAW key. Both are credentials and
#: neither may be ASSIGNED A VALUE in a committed file (CLAUDE.md §8).
#:
#: ⚠️ Naming them is not the violation, and a guard that treated it as one would
#: redden against correct files: fleet's `published.env` carries ~20 lines of
#: comment explaining exactly why each is absent, its `docker-compose.yml` must
#: DECLARE both bare for the host pass-through to work at all, and its README
#: documents the generation recipe. The violation is a committed VALUE.
_SECRET_ENV_NAMES = ("API_KEYS", "UI_DEMO_PERSONA_KEYS")


def _read_env_file(profile: Path) -> dict[str, str]:
    """`published.env`'s real assignments, comments and blanks discarded.

    Returns only lines that actually bind a name to a value, so a commented-out
    `# API_KEYS=...` cannot register as an assignment — and, in the other
    direction, cannot hide one either.
    """
    out: dict[str, str] = {}
    for raw in (profile / "published.env").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep:
            out[key.strip()] = value.strip()
    return out


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_ac6_no_profile_commits_a_key_credential(profile: Path) -> None:
    """AC-6: neither named secret carries a committed VALUE, on ANY profile.

    This closes the half of AC-6 that its own wording asks for and that nothing
    enforced until now: "the per-system env-parse tests assert each committed env
    file's key set excludes `API_KEYS` (and the persona-key variable if SD-4
    introduces one)". SD-4 introduced one — `UI_DEMO_PERSONA_KEYS` — and the s224
    credential ruling made it a store of RAW keys.

    ⚠️ Why this lives here and not in `test_published_compose.py`, where the
    energy-only `test_ac4_no_secret_is_committed` already sits: that module pins
    `_DEPLOY` to `oct-energy` and says so deliberately, on a reason that has since
    expired ("procurement's and fleet's are authored in the next step" — they
    shipped in #1114/#1116). This module is parametrized over every discovered
    profile, and `test_every_discovered_profile_has_an_expected_allow_set` makes a
    NEW profile redden rather than ride along uncovered. Fleet is precisely the
    profile that introduced the raw-key variable, so per-profile coverage is the
    property AC-6 actually needs.

    Two carriers, and they have OPPOSITE correct shapes — which is the whole
    difficulty:

    * `published.env` is loaded wholesale by `env_file:`, so a secret name
      appearing there as an assignment at all is the violation.
    * `docker-compose.yml` MUST list both names under `environment:` — a BARE
      entry (`- API_KEYS`, no `=`) is what makes the host value reach the
      container, and its absence is its own bug (`test_published_compose.py::
      test_the_app_can_actually_receive_api_keys_from_the_host`). Here the
      violation is the same name carrying a value.

    `_env_items` already normalizes both compose forms: a bare entry yields `""`,
    an assignment yields its value.
    """
    committed_env = _read_env_file(profile)
    compose_env = {
        key: value
        for svc in (_compose(profile).get("services") or {}).values()
        for key, value in _env_items(svc).items()
    }

    # RULED (Cray, typed, s225): a REQUIRED interpolation (`${API_KEYS:?...}`) is
    # NOT accepted here, even though the sibling guard just above DEMANDS that
    # shape for database credentials. The two differ on purpose. A `:?` default
    # still names the variable in a committed file and reads as provisioning
    # guidance; the compose file argues against that form for `API_KEYS` in its
    # own comment, and a guard accepting a shape the file itself rejects is a
    # guard that has stopped enforcing the file's design. Bare or absent, nothing
    # else. Recorded because it is a decision, not an oversight — if the compose
    # file's posture ever changes, this line is what has to change with it.
    for name in _SECRET_ENV_NAMES:
        assert name not in committed_env, (
            f"{profile.name}/published.env ASSIGNS {name}={committed_env[name]!r}. "
            f"That file is committed AND loaded wholesale by `env_file:`, so the "
            f"value ships in a public repo (CLAUDE.md §8, AC-6). Naming {name} in a "
            f"comment is fine and expected; provision the value host-env-local per "
            f"that profile's README."
        )
        if name in compose_env:
            assert compose_env[name] == "", (
                f"{profile.name}/docker-compose.yml gives {name} the value "
                f"{compose_env[name]!r}. The only accepted form is a BARE "
                f"pass-through (`- {name}`), which takes the value from the host "
                f"environment without committing it. An interpolation such as "
                f"`${{{name}:?...}}` is deliberately refused here (s225 ruling) — "
                f"see the comment above this loop."
            )


# --------------------------------------------------------------------------- #
# Step 5 — each system's allowlist, per instance
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_the_allow_set_equals_this_systems_expected_table(profile: Path) -> None:
    """Set-equality against THIS system's table (Step 5, per instance)."""
    expected = _EXPECTED_ALLOW.get(profile.name)
    assert expected is not None, f"no expected allow set for {profile.name}"
    assert set(_ingress_paths(profile)) == expected


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_every_pattern_is_anchored_at_both_ends(profile: Path) -> None:
    """cloudflared matches Path as an UNANCHORED regex.

    So an unanchored `/procedures` would also admit `/procedures/draft/build`, and
    an unanchored `/recommendations` would admit `/recommendations/{id}/execute`.
    Membership alone is not enough; anchoring is part of the claim.
    """
    for pattern in _ingress_paths(profile):
        assert pattern.startswith("^") and pattern.endswith(
            "$"
        ), f"{profile.name} admits `{pattern}`, which is not anchored at both ends"


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_the_last_rule_is_the_catch_all_404(profile: Path) -> None:
    """The catch-all IS the deny-by-default rule, and only works LAST."""
    doc = yaml.safe_load((profile / "cloudflared" / "config.yml").read_text(encoding="utf-8"))
    last = doc["ingress"][-1]
    assert "path" not in last, f"{profile.name}'s final ingress rule is not a catch-all"
    assert last["service"] == "http_status:404"


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
@pytest.mark.parametrize("route", sorted(_UNIVERSALLY_DENIED), ids=lambda r: r)
def test_no_system_admits_a_universally_denied_route(profile: Path, route: str) -> None:
    """A floor no profile may lower, whatever its tab set.

    Matched with `re.search` and never `re.fullmatch` — cloudflared's semantics.
    With `fullmatch` a pattern that lost its `^` would still pass here while
    leaking in production, i.e. the test would agree with a broken file.
    """
    why = _UNIVERSALLY_DENIED[route]
    for pattern in _ingress_paths(profile):
        assert not re.search(
            pattern, route
        ), f"{profile.name} admits `{route}` via `{pattern}` — excluded: {why}"


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_the_tunnel_is_locally_managed_and_names_this_system(profile: Path) -> None:
    """A locally-managed tunnel keeps the ingress map in this repo.

    Also asserts each system names its OWN tunnel: two systems sharing one tunnel
    would put both behind one connector, which is the arrangement the per-system
    compose project exists to prevent.
    """
    doc = yaml.safe_load((profile / "cloudflared" / "config.yml").read_text(encoding="utf-8"))
    assert doc.get("credentials-file"), f"{profile.name} declares no credentials-file"
    assert doc.get("tunnel"), f"{profile.name} declares no tunnel name"


def test_no_two_profiles_share_a_tunnel_name() -> None:
    tunnels = [
        yaml.safe_load((p / "cloudflared" / "config.yml").read_text(encoding="utf-8"))["tunnel"]
        for p in _profiles()
    ]
    duplicates = {t for t in tunnels if tunnels.count(t) > 1}
    assert not duplicates, f"two published systems share a tunnel name: {duplicates}"


# --------------------------------------------------------------------------- #
# AC-5 — no shadow registry
# --------------------------------------------------------------------------- #


#: Tiers whose job is to REASON ABOUT the set of systems, exempt by construction.
#: The hazard AC-5 names is an *operational* artifact that enumerates the published
#: systems — a shadow ingress map. A governance record that discusses which systems
#: exist is the opposite: it is where that reasoning is SUPPOSED to live, and
#: `docs/status-archive/` additionally must not be rewritten at all, because
#: editing an append-only historical record to satisfy a guard falsifies it.
_AC5_EXEMPT_TIERS = (
    Path("docs/adr"),  # ADR-0036 DEFINES the label convention; it must name labels
    Path("docs/plans"),  # PLAN-0103 ordered the split
    Path("docs/plans/done"),
    Path("docs/status-archive"),  # append-only; rewriting it would falsify the record
    Path("docs/lessons"),
    Path("docs/logs"),
)

_AC5_EXEMPT_FILES = {
    # A guard over the set has to name the set.
    Path("tests/deploy/test_published_profiles.py"),
    # ⚠️ ADDED AFTER THIS GUARD FAILED IN CI ON ITS OWN SESSION'S STATUS RECONCILE.
    # The omission was an inconsistency, not a finding: `docs/status-archive/` was
    # already exempt above, and the archive is nothing but rotated STATUS content —
    # so exempting the archive while STATUS itself bit treated one tier two ways.
    # STATUS is the state/reasoning tier: its job is to record WHAT SHIPPED, which
    # cannot be done without naming the systems that shipped. It is also rotating,
    # so it never accumulates into the durable roster AC-5 is aimed at.
    #
    # Worth knowing for the next guard of this shape: a full local `pytest tests/`
    # cannot catch this, because the STATUS text that trips it is written AFTER the
    # code change it describes — and pre-commit runs ruff/mypy, not pytest. CI was
    # the first place the two ever coexisted.
    Path("docs/STATUS.md"),
}


def _committed_text_files() -> list[Path]:
    """Every **tracked** text file that could plausibly carry a system label.

    ⚠️ `git ls-files`, deliberately, not an `rglob`. AC-5 speaks about *committed*
    files, and an rglob reads the working tree — so any untracked local scratch
    file can redden this guard, and the result stops being a property of the
    checkout. Measured, not hypothetical: the first run of this guard failed on
    `docs/strategy/private/…`, a **gitignored** file a parallel session had just
    written. That is a false RED on code that is correct in every clone.
    """
    out = subprocess.run(
        ["git", "ls-files", "--", "deploy", "docs", "services", "tests", "verticals"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    tracked = [Path(line) for line in out.stdout.splitlines() if line.strip()]
    # A worktree/permissions failure makes `git ls-files` return nothing, which
    # would make every AC-5 assertion below pass over an EMPTY set. Fail loudly
    # instead of silently: a vacuous guard is worse than an absent one.
    assert tracked, (
        "`git ls-files` returned no files — this guard cannot run, and passing "
        f"would be vacuous. stderr: {out.stderr.strip()!r}"
    )
    return [
        p
        for p in tracked
        if p.suffix in {".md", ".yml", ".yaml", ".py", ".env", ".js"} and "generated" not in p.parts
    ]


def test_ac5_no_file_outside_a_profile_lists_two_system_labels() -> None:
    """A vero-lite file enumerating the published systems is a shadow ingress map.

    ADR-0036 D2 puts the cross-system map in the portal repo. One label is a
    reference; two or more is a registry. `ls deploy/published/` is the filesystem
    answering the question, which is not the same as a committed list.

    ⚠️ This module is itself the deliberate exception — a guard over the set has to
    name the set — and so is the PLAN that ordered the split.
    """
    labels = {p.name for p in _profiles()}
    assert len(labels) >= 2, "need ≥2 profiles for this guard to mean anything"

    offenders: list[str] = []
    for path in _committed_text_files():
        if path in _AC5_EXEMPT_FILES or _DEPLOY_ROOT in path.parents:
            continue
        if any(tier in path.parents for tier in _AC5_EXEMPT_TIERS):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        mentioned = {label for label in labels if label in text}
        if len(mentioned) >= 2:
            offenders.append(f"{path} names {sorted(mentioned)}")
    assert not offenders, "shadow registry — files naming two or more systems:\n" + "\n".join(
        offenders
    )


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_ac5_a_profile_mentions_only_its_own_label(profile: Path) -> None:
    """Each profile directory is ignorant of its siblings.

    A profile that names another system is a registry entry by another route, and
    it is also how a copied file's stale references survive review.
    """
    others = {p.name for p in _profiles()} - {profile.name}
    for path in sorted(profile.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        named = sorted(label for label in others if label in text)
        assert not named, f"{path} (in {profile.name}) names another system: {named}"


# --------------------------------------------------------------------------- #
# Operator paths — the guard whose ABSENCE let Step 4a ship six broken commands
# --------------------------------------------------------------------------- #

#: `docker compose -f <path>` and `cloudflared … --config <path>`, as an operator
#: would copy them out of a runbook or a profile README.
_OPERATOR_PATH = re.compile(
    r"(?:-f|--config)\s+((?:[A-Za-z]:\\|/)?[\w./\\-]*deploy[/\\]published[/\\][\w./\\-]+)"
)


def _resolve(raw: str) -> Path:
    """Map a documented path — Windows host or repo-relative — onto this checkout."""
    cleaned = raw.replace(_HOST_CHECKOUT_PREFIX, "").replace("\\", "/").lstrip("/")
    return Path(cleaned)


def test_every_documented_operator_path_resolves() -> None:
    """A path in a runbook is a command someone will paste at 2am.

    ⚠️ This guard exists because its absence had a measured cost. PLAN-0103 Step 4a
    moved energy's artifacts into a profile directory and updated the references it
    could see; SIX survived — `published-demo-redeploy.md:187,198` (Windows host
    paths, invisible to a POSIX-shaped replace) and four in `oct-energy/README.md`.
    Every one of them sat in a fallback or verification procedure, i.e. exactly the
    path an operator reaches for when the normal one has already failed. Nothing in
    the suite noticed, because no test read the runbooks as instructions.
    """
    sources = [*_RUNBOOKS, *(p / "README.md" for p in _profiles()), _DEPLOY_ROOT / "README.md"]
    broken: list[str] = []
    checked = 0
    for source in sources:
        if not source.is_file():
            continue
        for line_no, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            for raw in _OPERATOR_PATH.findall(line):
                checked += 1
                if not _resolve(raw).exists():
                    broken.append(f"{source}:{line_no} → {raw}")
    assert checked >= 5, (
        f"only {checked} operator paths found across {len(sources)} documents — the "
        "regex has stopped matching and this guard would pass vacuously"
    )
    assert not broken, "documented operator paths that do not exist:\n" + "\n".join(broken)


# --------------------------------------------------------------------------- #
# PLAN-0105 Step 5 / AC-8 — the retention sweep is armed on exactly one profile
# --------------------------------------------------------------------------- #

#: The one profile PLAN-0105 arms the retention sweep on. A set rather than a
#: string, the ``_DB_GRANTED`` shape (`:406`) and for the same reason: arming a
#: second system must be a visible, deliberate edit HERE, because this flag
#: DELETES data. Fleet is the only published system with a database, and the only
#: one whose visitors can write something that persists.
_RETENTION_ARMED = {"oct-fleet-maintenance"}

#: What pydantic-settings reads as True for a bool field. Spelled out rather than
#: compared against the literal ``"true"``: a profile pinning ``=1`` or ``=yes``
#: would arm the sweep for real while a string comparison called it disarmed, and
#: this guard would then certify a DB-less system as safe while it deleted on a
#: timer.
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _flag_is_on(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUTHY


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_only_the_armed_profile_enables_case_retention(profile: Path) -> None:
    """Both directions, and they fail in opposite ways.

    ARMED but off: the RoPA promises a 90-day retention control that never runs.
    The promise is false while every status line stays green — the worse of the
    two, because a compliance claim nobody can watch fail is not a claim.

    NOT armed but on: a DB-less system starts a sweep that can only error, and a
    pilot deployment would delete an operator's real cases on an engine default.

    The negative side asserts "not truthy" rather than "absent". An explicit
    ``CASE_RETENTION_ENABLED=false`` is a legitimate and louder way to write the
    same posture, and a guard that reddened against a correct file is a guard
    somebody deletes the first time it gets in the way.
    """
    value = _read_env_file(profile).get("CASE_RETENTION_ENABLED")
    if profile.name in _RETENTION_ARMED:
        assert _flag_is_on(value), (
            f"{profile.name} is the retention-armed profile but its published.env "
            f"reads CASE_RETENTION_ENABLED={value!r}. The sweep would never run, and "
            "the RoPA's 90-day promise would name a control that does not fire."
        )
    else:
        assert not _flag_is_on(value), (
            f"{profile.name} has no database and is not retention-armed, but its "
            f"published.env reads CASE_RETENTION_ENABLED={value!r}. Arming a second "
            "system is a deliberate edit to _RETENTION_ARMED, never a copied env line."
        )
