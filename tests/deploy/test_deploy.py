"""The shipped redeploy orchestrator — guarded against drift, and driven for real.

`deploy/published/deploy.py` is the procedure that makes the live demo be
whatever `main` currently says. Two failure classes matter, and they need
different kinds of test:

**Drift.** The script is stdlib-only by design (an operator runs it outside the
venv, like `verify_tunnel_credentials.py`), so it cannot parse the compose file
to learn the project, container and image names — it carries them as literals.
The guard tests below read the **committed compose file** and assert each literal
still matches. They deliberately do not restate the names as their own constants:
a guard that compares one copy to another copy proves only that the copy is
self-consistent.

**Silent no-op.** A redeploy can succeed at every visible step and still serve the
old code, because `compose up` decides for itself whether a container needs
replacing. The scenario cases drive `main()` for real against fake `docker` /
`ssh` / `scp` / `curl` on `PATH`, and the load-bearing one asserts that when the
running container's image does NOT match what was just loaded, the run **fails**.

The fakes are executables on `PATH`, not a patched `subprocess.run`: that keeps
the argv construction, the no-shell invocation and the exit-code handling all
real, and only the far side of the process boundary simulated. Every scenario
asserts the fake log is non-empty before reading it — if a fake were not wired,
the script would reach the real `docker`/`ssh` and the test must fail loudly
rather than quietly pass on a live call.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import stat
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path("deploy/published/deploy.py")
_COMPOSE = Path("deploy/published/docker-compose.yml")
_RUNBOOK = Path("docs/runbooks/published-demo-redeploy.md")

_LOCAL_ID = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_OTHER_ID = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

_HEAD_BEFORE = "1111111111111111111111111111111111111111"
_HEAD_AFTER = "2222222222222222222222222222222222222222"

#: One fake for every external program the script shells out to. It dispatches on
#: its own basename, logs each invocation, and answers from a JSON control file —
#: so a scenario is expressed as data, not as another copy of the script's logic.
_FAKE = """#!/usr/bin/env python3
import json, os, sys
name = os.path.basename(sys.argv[0])
args = sys.argv[1:]
ctl = json.loads(open(os.environ["FAKE_CTL"]).read())
with open(os.environ["FAKE_LOG"], "a") as fh:
    fh.write(json.dumps([name, *args]) + "\\n")

def out(text, code=0):
    sys.stdout.write(text)
    sys.exit(code)

if name == "docker":
    if args[:2] == ["image", "inspect"]:
        out(ctl["local_id"])
    out("")

if name == "scp":
    out("")

if name == "curl":
    out(ctl.get("http_code", "302"))

if name == "ssh":
    rest = args[1:]          # drop the host alias
    if rest[:1] == ["git"]:
        if "rev-parse" in rest:
            n = ctl["_state"] = ctl.get("_state", 0) + 1
            open(os.environ["FAKE_CTL"], "w").write(json.dumps(ctl))
            out(ctl["head_before"] if n == 1 else ctl["head_after"])
        if "diff" in rest:
            out("\\n".join(ctl.get("changed", [])))
        out("")
    if rest[:2] == ["docker", "tag"]:
        if ctl.get("no_prev_image"):
            sys.stderr.write("Error: No such image")
            sys.exit(1)
        out("")
    if rest[:3] == ["docker", "image", "inspect"]:
        out(ctl["remote_id"])
    if rest[:2] == ["docker", "inspect"]:
        if any("Health" in a for a in rest):
            out(ctl.get("health", "healthy"))
        out(ctl["running_id"])
    if rest[:2] == ["docker", "compose"] and "ps" in rest:
        out(ctl.get("ps", "vero-published-app  running\\nvero-published-cloudflared  running\\n"))
    if rest[:2] == ["docker", "compose"] and "exec" in rest:
        out(ctl.get("health", '{"status": "ok"}'))
    out("")

out("")
"""


@pytest.fixture(scope="module")
def deploy() -> ModuleType:
    """The script, loaded from its committed path (`deploy/` is not importable)."""
    assert _SCRIPT.is_file(), f"{_SCRIPT} is missing — the redeploy runbook drives it"
    spec = importlib.util.spec_from_file_location("published_deploy", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def compose_text() -> str:
    assert _COMPOSE.is_file(), f"{_COMPOSE} is missing"
    return _COMPOSE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Drift guards — every assertion reads the COMMITTED compose file.
# --------------------------------------------------------------------------- #


def test_the_project_name_matches_the_compose_file(deploy: ModuleType, compose_text: str) -> None:
    """`-p vero-published` on every remote compose call has to be the real project."""
    match = re.search(r"^name:\s*(\S+)\s*$", compose_text, re.MULTILINE)
    assert match is not None, "docker-compose.yml declares no top-level `name:`"
    assert deploy._PROJECT == match.group(1), (
        f"deploy.py drives `-p {deploy._PROJECT}` but the compose project is "
        f"{match.group(1)!r}. A wrong -p addresses a DIFFERENT project: compose "
        "reports 'no containers' and every downstream check reads an empty world"
    )


@pytest.mark.parametrize("attr", ["_APP_CONTAINER", "_CLOUDFLARED_CONTAINER"])
def test_each_container_name_is_declared_in_the_compose_file(
    deploy: ModuleType, compose_text: str, attr: str
) -> None:
    """`docker inspect <container>` names them directly, so a rename must redden."""
    declared = set(re.findall(r"^\s*container_name:\s*(\S+)\s*$", compose_text, re.MULTILINE))
    assert getattr(deploy, attr) in declared, (
        f"deploy.py {attr} = {getattr(deploy, attr)!r} is not a container_name in "
        f"the compose file (declared: {sorted(declared)})"
    )


def test_every_host_read_path_exists_and_the_compose_really_reads_it(
    deploy: ModuleType, compose_text: str
) -> None:
    """The pull-before-up rule is only correct if these are the files compose reads.

    Each of the three has a distinct mechanism — the compose file is itself the
    `-f` target, `published.env` arrives via `env_file:`, and the ingress config is
    a bind mount. Asserting the mechanism, not just the filename, is what makes
    this guard mean something.
    """
    for rel in deploy._HOST_READ_PATHS:
        assert Path(rel).is_file(), f"{rel} is listed as host-read but does not exist"

    assert "deploy/published/docker-compose.yml" in deploy._HOST_READ_PATHS
    assert re.search(r"^\s*-\s*published\.env\s*$", compose_text, re.MULTILINE), (
        "published.env is listed as host-read but the compose file no longer "
        "loads it via env_file"
    )
    assert (
        "./cloudflared/config.yml:" in compose_text
    ), "the ingress config is listed as host-read but is no longer bind-mounted"


def test_the_connector_config_is_one_of_the_host_read_paths(deploy: ModuleType) -> None:
    """It gets special treatment (force-recreate), so it must be in the base set."""
    assert deploy._CONNECTOR_CONFIG in deploy._HOST_READ_PATHS


def test_the_script_names_no_domain(deploy: ModuleType) -> None:
    """Domain-ignorance (ADR-0035 D1(3)) — the host is an argument, never a literal.

    A TLD allowlist rather than a filename denylist: the dotted shape is shared by
    attribute access and filenames, and a denylist of extensions cannot separate
    `cert.pem` from `demo.example.com`. This is the s213 finding, applied here.
    """
    tlds = r"(?:com|net|org|io|dev|app|co|th|ai|cloud)"
    hits = re.findall(rf"\b[a-z0-9][a-z0-9-]*\.[a-z0-9-]+\.{tlds}\b", _SCRIPT.read_text("utf-8"))
    assert not hits, f"deploy.py names a hostname: {hits}. Pass --host / --smoke-url instead"


def test_the_effect_assertion_is_wired_into_the_deploy_path(deploy: ModuleType) -> None:
    """The one check the whole script exists for cannot be quietly dropped.

    `assert_running_image` is what separates "the commands ran" from "the new code
    is serving". A refactor that leaves the function defined but stops calling it
    would pass every other test in this file.
    """
    source = _SCRIPT.read_text(encoding="utf-8")
    for caller in ("def main(", "def rollback("):
        body = source.split(caller, 1)[1].split("\ndef ", 1)[0]
        assert "assert_running_image(" in body, (
            f"{caller.removeprefix('def ')}) no longer calls assert_running_image — "
            "without it the run can report success while the old container keeps "
            "serving, which is the single failure this script exists to prevent"
        )


def test_the_runbook_exists_and_drives_this_script() -> None:
    assert _RUNBOOK.is_file(), f"{_RUNBOOK} is missing — deploy.py's docstring points at it"
    assert "deploy.py" in _RUNBOOK.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Scenario cases — the real entry point, real subprocesses, fake far side.
# --------------------------------------------------------------------------- #

posix_only = pytest.mark.skipif(
    os.name != "posix", reason="the fakes are exec-bit shell programs on PATH"
)


@pytest.fixture
def stage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Put fake `docker`/`ssh`/`scp`/`curl` on PATH; return a runner for one scenario."""
    binder = tmp_path / "bin"
    binder.mkdir()
    for name in ("docker", "ssh", "scp", "curl"):
        exe = binder / name
        exe.write_text(_FAKE, encoding="utf-8")
        exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    log = tmp_path / "calls.log"
    ctl = tmp_path / "ctl.json"
    monkeypatch.setenv("PATH", f"{binder}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("FAKE_CTL", str(ctl))

    def _run(deploy: ModuleType, argv: list[str], **control: object) -> tuple[int, list[list[str]]]:
        settings: dict[str, object] = {
            "local_id": _LOCAL_ID,
            "remote_id": _LOCAL_ID,
            "running_id": _LOCAL_ID,
            "head_before": _HEAD_BEFORE,
            "head_after": _HEAD_BEFORE,
            "changed": [],
        }
        settings.update(control)
        ctl.write_text(json.dumps(settings), encoding="utf-8")
        log.write_text("", encoding="utf-8")

        deploy._results.clear()
        code = deploy.main(["deploy.py", *argv])
        calls = [json.loads(line) for line in log.read_text("utf-8").splitlines() if line.strip()]
        return code, calls

    return _run


@posix_only
def test_a_clean_redeploy_passes_every_check(deploy: ModuleType, stage) -> None:
    code, calls = stage(deploy, ["--host", "fake-host", "--execute"])
    assert calls, (
        "no fake was invoked — the script did not shell out at all, which means "
        "this scenario proved nothing (and a real docker/ssh may have been reached)"
    )
    verdicts = {label: ok for label, ok, _ in deploy._results}
    assert code == 0, f"a clean redeploy failed on {[k for k, v in verdicts.items() if not v]}"
    assert verdicts["running container uses the new image"] is True


@posix_only
def test_a_deploy_that_did_not_take_effect_fails(deploy: ModuleType, stage) -> None:
    """The load-bearing case: every command succeeds, the old container keeps serving.

    This is the exact shape that has no visible symptom — `up -d` prints nothing
    alarming, `compose ps` is healthy, the edge answers. Without this assertion the
    operator concludes the deploy worked.
    """
    code, calls = stage(deploy, ["--host", "fake-host", "--execute"], running_id=_OTHER_ID)
    assert calls, "no fake was invoked — the scenario is vacuous"
    verdicts = {label: ok for label, ok, _ in deploy._results}
    assert verdicts["running container uses the new image"] is False
    assert code != 0, "a deploy that did not take effect must not exit 0"


@posix_only
def test_a_corrupted_transfer_fails(deploy: ModuleType, stage) -> None:
    """Ids differing across machines means the image that arrived is not the one built."""
    code, _ = stage(deploy, ["--host", "fake-host", "--execute"], remote_id=_OTHER_ID)
    verdicts = {label: ok for label, ok, _ in deploy._results}
    assert verdicts["image transferred intact"] is False
    assert code != 0


@posix_only
def test_the_connector_is_recreated_only_when_its_config_changed(deploy: ModuleType, stage) -> None:
    """A bind mount does not make compose replace the container — this must be explicit."""
    _, unchanged = stage(deploy, ["--host", "fake-host", "--execute"])
    assert not any(
        "--force-recreate" in c for c in unchanged
    ), "the connector was recreated although its config did not change"

    _, changed = stage(
        deploy,
        ["--host", "fake-host", "--execute"],
        head_after=_HEAD_AFTER,
        changed=[deploy._CONNECTOR_CONFIG],
    )
    recreated = [c for c in changed if "--force-recreate" in c and "cloudflared" in c]
    assert recreated, (
        "the ingress config changed and the connector was NOT recreated — it would "
        "keep serving the allowlist it read at start, with nothing to indicate it"
    )


@posix_only
def test_an_app_only_change_does_not_recreate_the_connector(deploy: ModuleType, stage) -> None:
    """The common case: new app code, untouched ingress. Recreating would be churn."""
    _, calls = stage(
        deploy,
        ["--host", "fake-host", "--execute"],
        head_after=_HEAD_AFTER,
        changed=["services/api/main.py", "services/api/static/assets/app.js"],
    )
    assert not any("--force-recreate" in c for c in calls)


@posix_only
def test_a_non_302_from_the_edge_fails(deploy: ModuleType, stage) -> None:
    """200 is not a better answer than 302 — it means the gate is not applied."""
    code, _ = stage(
        deploy,
        ["--host", "fake-host", "--execute", "--smoke-url", "https://example.invalid/health"],
        http_code="200",
    )
    verdicts = {label: ok for label, ok, _ in deploy._results}
    assert verdicts["edge gate is in front"] is False
    assert code != 0


@posix_only
def test_a_first_redeploy_with_no_previous_image_still_completes(deploy: ModuleType, stage) -> None:
    """Tagging the rollback point fails when there is nothing to tag yet.

    That is expected once — right after bring-up — and must be reported rather
    than abort the deploy. But it must NOT pass silently: rollback is unavailable
    until the next run, and the operator has to know.
    """
    code, _ = stage(deploy, ["--host", "fake-host", "--execute"], no_prev_image=True)
    verdicts = {label: ok for label, ok, _ in deploy._results}
    assert verdicts["rollback point tagged"] is False
    assert (
        verdicts["running container uses the new image"] is True
    ), "a missing rollback point must not stop the deploy itself"
    assert code != 0, "an unavailable rollback path is surfaced, not swallowed"


@posix_only
def test_rollback_proves_which_image_it_left_running(deploy: ModuleType, stage) -> None:
    code, calls = stage(
        deploy, ["--host", "fake-host", "--execute", "--rollback"], running_id=_LOCAL_ID
    )
    assert any(c[:3] == ["ssh", "fake-host", "docker"] and "tag" in c for c in calls)
    verdicts = {label: ok for label, ok, _ in deploy._results}
    assert verdicts["running container uses the new image"] is True
    assert code == 0


# --------------------------------------------------------------------------- #
# The safety property, tested rather than assumed.
# --------------------------------------------------------------------------- #


@posix_only
def test_without_execute_nothing_runs_at_all(deploy: ModuleType, stage) -> None:
    """The default mode must be inert.

    This is the structural guard on a script whose job is to mutate a host Cray
    has to authorise per CLAUDE.md §8: a forgotten flag, a copied command or a
    half-written invocation produces a printed plan, never a deploy.
    """
    code, calls = stage(deploy, ["--host", "fake-host"])
    assert calls == [], f"planning invoked real programs: {calls}"
    assert code == 0


@posix_only
def test_a_plan_records_no_verdicts_at_all(deploy: ModuleType, stage) -> None:
    """A plan checked nothing, so it must not be able to report a PASS.

    The first draft recorded `rollback point tagged: PASS` during a plan and
    closed with "2 checks, 0 FAIL" at exit 0 — a run that proved nothing reading
    exactly like a run that proved something. Found by reading the plan's real
    output, not by review.
    """
    stage(deploy, ["--host", "fake-host"])
    assert deploy._results == [], f"planning recorded verdicts it never earned: {deploy._results}"


@posix_only
def test_no_remote_command_carries_anything_a_shell_would_reparse(
    deploy: ModuleType, stage
) -> None:
    """The no-shell guarantee holds on THIS side only — ssh hands over a string.

    `subprocess.run` with a list argv means nothing is re-parsed locally, but ssh
    joins the remaining words and the REMOTE shell parses the result. So every
    remote command has to survive that: literals, no quotes, no `$`, no
    separators. An inlined `python -c "…;…"` does not, and one shipped in the
    first draft.

    This guards the class rather than that one command: any future step that
    inlines a script, a pipe or a variable reddens here.
    """
    _, calls = stage(
        deploy,
        ["--host", "fake-host", "--execute"],
        head_after=_HEAD_AFTER,
        changed=[deploy._CONNECTOR_CONFIG],
    )
    remote = [c for c in calls if c[0] == "ssh"]
    assert remote, "no ssh call was made — the scenario is vacuous"
    hazards = set("\"'$;|&`<>()")
    for call in remote:
        for word in call[2:]:  # skip "ssh" and the host alias
            bad = hazards & set(word)
            assert not bad, (
                f"remote word {word!r} contains {sorted(bad)}, which the host's "
                "shell will re-parse. Build it from literals, or pipe a .ps1 over "
                "stdin (see the ms-s1-admin skill) — do not inline it here"
            )


def test_execute_cannot_run_without_an_explicit_host(deploy: ModuleType) -> None:
    """No default host — an accidental invocation has nothing to aim at."""
    with pytest.raises(SystemExit) as exc:
        deploy.main(["deploy.py", "--execute"])
    assert exc.value.code != 0
