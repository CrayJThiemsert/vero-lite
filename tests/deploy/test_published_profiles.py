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
        r"^/llm/status$",
        r"^/procedures$",
        r"^/demo/hero/governance$",
        r"^/demo/hero/impact$",
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


@pytest.mark.parametrize("profile", _profiles(), ids=_profile_ids())
def test_a_profile_carries_all_four_committed_artifacts(profile: Path) -> None:
    """AC-3: `{docker-compose.yml, published.env, cloudflared/config.yml, README}`."""
    for rel in ("docker-compose.yml", "published.env", "cloudflared/config.yml", "README.md"):
        assert (profile / rel).is_file(), f"{profile.name} is missing {rel}"


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
