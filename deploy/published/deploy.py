#!/usr/bin/env python3
"""Redeploy the published OCT demo: build here, ship the image, prove what runs.

Used by ``docs/runbooks/published-demo-redeploy.md``. The bring-up runbook
(``published-demo-bring-up.md``) stands the system up the FIRST time — the
Cloudflare account work, the tunnel, the Access policy, the host secrets. None of
that repeats. This script owns the part that repeats: *something changed on
``main``, make the live demo be that thing, and prove it.*

Why a script and not a list of commands
---------------------------------------
Session 213 lost time to three separate shapes of the same hazard while doing
this by hand — a ``$`` that expanded one shell layer early, inner double quotes
silently stripped by PowerShell, and a ``| head`` that reported the truncator's
exit status. Every command here runs through ``subprocess.run`` with a **list
argv and no shell**, so none of those three can happen: nothing is ever re-parsed
by an intervening shell on this side.

What it actually guarantees
---------------------------
Two different things get confused, so they are separated here:

* ``docker image inspect`` ids equal on both machines proves the **transfer**
  arrived intact. That is what session 213 measured, and it is *not* a claim
  about what is running.
* The running container's ``.Image`` equal to the newly loaded id proves the
  **deploy took effect**. Without it a redeploy can succeed at every visible step
  and still serve the old code, because ``compose up`` decides for itself whether
  a container needs replacing.

Both are asserted. The second is the one that makes a redeploy trustworthy, and
it is the one no prior procedure had.

Safety
------
The default mode is a **plan** — it prints what it would do and touches nothing,
locally or remotely. Executing requires BOTH ``--execute`` and an explicit
``--host``; there is deliberately no default host, so an accidental or
half-written invocation has nothing to aim at. Running against MS-S1 is a
host-state change and needs Cray's explicit go every time (``CLAUDE.md`` §8) —
this script does not and cannot grant it.

Usage
-----
    python3 deploy.py --host <ssh-alias>                    # plan only (default)
    python3 deploy.py --host <ssh-alias> --execute          # deploy
    python3 deploy.py --host <ssh-alias> --execute --rollback
    python3 deploy.py --host <ssh-alias> --execute --smoke-url https://<host>/health

Exit code is 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path
from typing import Any

#: ⚠️ THIS SCRIPT SERVES `oct-energy` ONLY, and every literal below says so.
#:
#: PLAN-0103 Step 4 split `deploy/published/` into one profile directory per
#: published system. The config moved; this script deliberately did NOT (Cray,
#: typed, s219). It stays here, at the parent, because parameterizing it now
#: would mean designing a `--system` interface against a second deployment that
#: has never run — fleet carries a Postgres and will likely owe verification
#: steps energy does not, and guessing their shape is the speculative-generality
#: failure Rule of Three exists to prevent.
#:
#: **The decision is deferred to Step 10**, where procurement's bring-up makes the
#: real requirements observable. Whoever takes it chooses between parameterizing
#: this script by system label and copying it per profile; note that copying
#: triplicates the seven verification checks, which are the only thing standing
#: between a green offline suite and a container that cannot boot (s213 #1071:
#: 3,943 tests green over exactly that).
#:
#: `tests/deploy/test_deploy.py` pins this to oct-energy's compose file, so a
#: second system cannot quietly start riding these energy-shaped literals.

#: Paths on the deploy host. Fixed by Cray's session-213 decision (the checkout
#: location and the staging directory), not discovered — a deploy that guesses
#: where the checkout lives is a deploy that can update the wrong tree.
_HOST_CHECKOUT = r"C:\projects\vero-lite"
_HOST_COMPOSE = r"C:\projects\vero-lite\deploy\published\oct-energy\docker-compose.yml"

#: The same compose file as `_HOST_COMPOSE`, addressed from THIS checkout for the
#: local build. It is a module constant rather than an expression at its use site
#: because the drift guards can only enumerate module constants, and that is
#: exactly how it broke: PLAN-0103 Step 4 moved this file into `oct-energy/` and
#: updated `_HOST_COMPOSE` above, but not the local path, which was composed
#: inline inside `build_and_ship` as
#: `repo_root / "deploy" / "published" / "docker-compose.yml"`. That left `-f`
#: pointing at a file deleted three commits earlier, so Phase 1 would have died on
#: the next `--execute` — and nothing could see it: the scenario suite's fake
#: `docker` never stats its `-f` argument, and an inline expression is invisible to
#: the path guard that already stats `_HOST_READ_PATHS`.
_LOCAL_COMPOSE = "deploy/published/oct-energy/docker-compose.yml"

#: Names that MUST agree with `docker-compose.yml`. They are literals here
#: because this script is stdlib-only by design (an operator runs it outside the
#: venv, exactly like `verify_tunnel_credentials.py`), so there is no YAML parser
#: to read them with. `tests/deploy/test_deploy.py` reads the committed compose
#: file and asserts each one still matches — the drift this cannot prevent, that
#: test catches.
#:
#: Renamed from the `vero-published-*` family in PLAN-0103 Step 4b: the project
#: name is now the profile DIRECTORY name, so that two published systems cannot
#: land in one compose project or on one Docker network (AC-4).
_PROJECT = "oct-energy"
_APP_CONTAINER = "oct-energy-app"
_CLOUDFLARED_CONTAINER = "oct-energy-cloudflared"

#: compose names a built image `<project>-<service>` when the service declares
#: `build:` and no `image:`, which is exactly what the app service does — so this
#: value FOLLOWS `_PROJECT` and is not independently choosable.
_IMAGE = "oct-energy-app"
_PREV_TAG = f"{_IMAGE}:prev"
_LIVE_TAG = f"{_IMAGE}:latest"

#: Repo-relative paths whose change means the HOST checkout must be pulled before
#: `up`, because compose reads them from disk on the host rather than from the
#: image: the compose file itself, the env file it loads, and the ingress
#: allowlist that is bind-mounted into the connector.
_HOST_READ_PATHS = (
    "deploy/published/oct-energy/docker-compose.yml",
    "deploy/published/oct-energy/published.env",
    "deploy/published/oct-energy/cloudflared/config.yml",
)

#: Placeholder values for every `${VAR:?…}` the compose file declares required.
#: They exist only so a LOCAL build can interpolate the file — the app image
#: neither reads nor embeds them, and the real values live on the deploy host.
#: `tests/deploy/test_deploy.py` reads the compose file for required variables and
#: asserts this covers every one, so a new required variable cannot silently
#: reintroduce the failure this closes.
_BUILD_PLACEHOLDERS = {"CLOUDFLARED_CREDENTIALS_FILE": "/nonexistent/build-time-placeholder"}

#: The one whose change ALSO requires recreating the connector. A bind mount
#: shows the new file on disk immediately, but cloudflared reads its config once
#: at start — so `up -d` alone leaves the old ingress map live, with nothing to
#: indicate it.
_CONNECTOR_CONFIG = "deploy/published/oct-energy/cloudflared/config.yml"

_results: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    """Record one check and return its verdict, so callers can early-exit."""
    _results.append((label, ok, detail))
    return ok


class Runner:
    """Runs commands, or prints them when planning.

    The plan/execute split lives here rather than at each call site so that a new
    step cannot forget to honour it — a step that forgets would run for real
    during a plan, which is the failure this class exists to make impossible.
    """

    def __init__(self, *, execute: bool) -> None:
        self.execute = execute
        self.log: list[list[str]] = []

    def run(
        self,
        argv: list[str],
        *,
        stdin_path: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> str:
        """Run `argv` with NO shell. Returns stdout (stripped), or "" when planning."""
        self.log.append(argv)
        if not self.execute:
            suffix = f"  < {stdin_path}" if stdin_path else ""
            if env:
                suffix += f"  (env: {', '.join(sorted(env))})"
            print(f"  would run: {' '.join(argv)}{suffix}")
            return ""
        # S603: every argv this script builds is literals plus the operator's own
        # `--host` / `--smoke-url`, and `shell=False` is the point of the design —
        # it is what removes the quoting-hazard class entirely. Running programs
        # IS the job here; there is no untrusted input to sanitise.
        with stdin_path.open("rb") if stdin_path else nullcontext(None) as source:
            completed = subprocess.run(  # noqa: S603
                argv,
                stdin=source,
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, **env} if env else None,
            )
        if completed.returncode != 0:
            # stderr is merged into the message rather than left on its own
            # stream: through an intervening `wsl bash -lc` an unmerged stderr
            # can overwrite stdout byte-for-byte and erase the very output being
            # read as evidence (docs/lessons/0007).
            raise CommandFailedError(argv, completed.returncode, (completed.stderr or "").strip())
        return (completed.stdout or "").strip()


class CommandFailedError(RuntimeError):
    def __init__(self, argv: list[str], code: int, stderr: str) -> None:
        super().__init__(f"exit {code} from {' '.join(argv)}: {stderr}")
        self.argv = argv
        self.code = code
        self.stderr = stderr


def _ssh(host: str, *remote: str) -> list[str]:
    """An ssh argv. `remote` is passed as separate words, never a joined string.

    ⚠️ The no-shell guarantee stops at THIS process. ssh joins the remaining words
    and the deploy host's shell parses the result — and that shell is **PowerShell**
    (measured 2026-08-08: `echo %COMSPEC%` comes back literal, so it is not cmd).
    Every remote command must therefore be literals a PowerShell would leave alone:
    no quotes, no `$`, no separators, **and no braces**.

    Braces are the one that actually bit. `docker inspect --format={{.Id}}` — the
    form every runbook and every docker doc uses — reaches the host as
    `unknown shorthand flag: 'e' in -encodedCommand`, because PowerShell takes
    `{...}` for a script block. So this script never sends `--format`: it asks for
    plain JSON and parses it here, where no shell is involved at all.

    Anything that genuinely needs more belongs in a `.ps1` piped over stdin (see
    the `ms-s1-admin` skill), not inlined here.
    """
    return ["ssh", host, *remote]


def _first_object(raw: str) -> dict[str, Any]:
    """`docker inspect` always returns a JSON array; take its one element."""
    if not raw:
        return {}
    parsed = json.loads(raw)
    return parsed[0] if isinstance(parsed, list) and parsed else {}


def _local_image_id(run: Runner) -> str:
    return str(_first_object(run.run(["docker", "image", "inspect", _LIVE_TAG])).get("Id", ""))


def _remote_image_id(run: Runner, host: str, tag: str) -> str:
    return str(_first_object(run.run(_ssh(host, "docker", "image", "inspect", tag))).get("Id", ""))


def build_and_ship(run: Runner, host: str, repo_root: Path) -> str:
    """Build here, save, copy, load there. Returns the local image id."""
    print("\n== 1. build on this machine ==")
    compose_file = str(repo_root / _LOCAL_COMPOSE)
    # compose interpolates the WHOLE file before deciding what to build, and the
    # cloudflared service declares CLOUDFLARED_CREDENTIALS_FILE required — so a
    # build fails without it even though building the app touches neither the
    # variable nor the connector. Measured 2026-08-08: `compose config` without it
    # exits 1 with "required variable … is missing a value". Nothing is created at
    # the placeholder path; volumes are materialised at container-create time, not
    # at build.
    run.run(
        [
            "docker",
            "compose",
            "-f",
            compose_file,
            "build",
            "app",
        ],
        env=_BUILD_PLACEHOLDERS,
    )
    local_id = _local_image_id(run)
    print(f"  local image: {local_id or '<planning>'}")

    print("\n== 2. keep a rollback point on the host ==")
    # Tagged BEFORE the load, because the load overwrites `:latest`. If there is
    # no image on the host yet (a first deploy after bring-up) this is a no-op
    # and must not fail the run.
    try:
        run.run(_ssh(host, "docker", "tag", _LIVE_TAG, _PREV_TAG))
        if run.execute:
            check("rollback point tagged", True, _PREV_TAG)
    except CommandFailedError as exc:
        check(
            "rollback point tagged",
            False,
            f"no existing {_LIVE_TAG} on the host to tag ({exc.stderr[:80]}) — "
            "expected only on the very first redeploy; --rollback will not work "
            "until the next one",
        )

    print("\n== 3. ship the image ==")
    # Piped into `docker load` on stdin rather than scp'd to a staging path. That
    # removes a Windows path from the command line, removes the scp step, and
    # removes the dependency on a staging directory existing — which a read-only
    # probe could not even confirm (the `cmd /c if exist` test came back rc=0 and
    # silent, i.e. inconclusive, which is not a pass).
    with tempfile.TemporaryDirectory() as tmp:
        tar = Path(tmp) / "app.tar"
        run.run(["docker", "save", _LIVE_TAG, "-o", str(tar)])
        run.run(_ssh(host, "docker", "load"), stdin_path=tar)

    remote_id = _remote_image_id(run, host, _LIVE_TAG)
    if run.execute:
        check(
            "image transferred intact",
            bool(local_id) and local_id == remote_id,
            f"local {local_id[:19]}… vs host {remote_id[:19]}…",
        )
    return local_id


def sync_host_checkout(run: Runner, host: str) -> bool:
    """Pull the host checkout. Returns True if the connector's config changed.

    compose reads the compose file, the env file and the ingress allowlist from
    the HOST's checkout, not from the image — so an app-only change needs no pull
    but a change to any of those does. Pulling unconditionally is cheaper than
    deciding, and removes the "I forgot to pull" failure entirely; what still has
    to be decided is whether the CONNECTOR needs recreating, which is what this
    returns.
    """
    print("\n== 4. sync the host checkout ==")
    before = run.run(_ssh(host, "git", "-C", _HOST_CHECKOUT, "rev-parse", "HEAD"))
    run.run(_ssh(host, "git", "-C", _HOST_CHECKOUT, "pull", "--ff-only"))
    after = run.run(_ssh(host, "git", "-C", _HOST_CHECKOUT, "rev-parse", "HEAD"))

    if not run.execute:
        print("  would diff the two revisions to decide whether to recreate the connector")
        return False
    if before == after:
        check("host checkout current", True, f"already at {after[:8]}")
        return False

    changed = run.run(
        _ssh(host, "git", "-C", _HOST_CHECKOUT, "diff", "--name-only", before, after)
    ).splitlines()
    check("host checkout updated", True, f"{before[:8]} -> {after[:8]}, {len(changed)} files")
    touched = [p for p in _HOST_READ_PATHS if p in changed]
    if touched:
        print(f"  host-read files changed: {', '.join(touched)}")
    return _CONNECTOR_CONFIG in changed


def bring_up(run: Runner, host: str, *, recreate_connector: bool) -> None:
    print("\n== 5. bring it up ==")
    run.run(_ssh(host, "docker", "compose", "-f", _HOST_COMPOSE, "-p", _PROJECT, "up", "-d"))
    if recreate_connector:
        # The ingress allowlist is bind-mounted, and a bind mount does not make
        # compose consider the container stale — cloudflared would keep serving
        # the map it read at start.
        print("  ingress config changed -> recreating the connector")
        run.run(
            _ssh(
                host,
                "docker",
                "compose",
                "-f",
                _HOST_COMPOSE,
                "-p",
                _PROJECT,
                "up",
                "-d",
                "--force-recreate",
                "cloudflared",
            )
        )


def assert_running_image(run: Runner, host: str, expected_id: str) -> None:
    """THE check. Everything before this proves preparation; this proves effect."""
    print("\n== 6. prove the new image is what is running ==")
    if not run.execute:
        print("  would compare the running container's image against the loaded id")
        return
    running = str(
        _first_object(run.run(_ssh(host, "docker", "inspect", _APP_CONTAINER))).get("Image", "")
    )
    check(
        "running container uses the new image",
        bool(expected_id) and running == expected_id,
        f"container {running[:19]}… vs loaded {expected_id[:19]}…"
        + ("" if running == expected_id else "  <-- THE DEPLOY DID NOT TAKE EFFECT"),
    )


def smoke(run: Runner, host: str, smoke_url: str | None) -> None:
    print("\n== 7. smoke ==")
    ps = run.run(_ssh(host, "docker", "compose", "-f", _HOST_COMPOSE, "-p", _PROJECT, "ps"))
    if run.execute:
        check(
            "both services present",
            _APP_CONTAINER in ps and _CLOUDFLARED_CONTAINER in ps,
            "app + cloudflared in `compose ps`",
        )
        # No published host port on anything is AC-5 and the point of the whole
        # topology; a redeploy that quietly introduced one would be a real
        # regression, and `ps` is where it would show.
        check(
            "no published host port",
            "0.0.0.0:" not in ps and ":::" not in ps,
            "no host-port binding in `compose ps`",
        )

    # Read the image's OWN healthcheck verdict rather than shipping a probe over
    # ssh. The Dockerfile already runs `/health` on a schedule, and that verdict
    # is the one `depends_on: condition: service_healthy` gates the connector on —
    # so this reports the same fact the topology already acts on, instead of a
    # second opinion about it.
    #
    # Read out of plain JSON for the reason `_ssh`'s docstring gives: an inlined
    # `python -c …` carries quotes and a `;`, and `--format={{…}}` carries braces
    # PowerShell reads as a script block. Both are re-parsed on the far side.
    state = _first_object(run.run(_ssh(host, "docker", "inspect", _APP_CONTAINER)))
    verdict = str(state.get("State", {}).get("Health", {}).get("Status", ""))
    if run.execute:
        check("app healthcheck reports healthy", verdict == "healthy", verdict or "<no verdict>")

    if smoke_url is None:
        print("  (no --smoke-url given — skipping the edge check)")
        return
    # Runs from THIS machine, needs no credentials, and is the only check that
    # exercises the public path. 302 means Access is in front of a working
    # origin. A 200 is not a better result — it means the gate is not applied.
    code = run.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "20", smoke_url]
    )
    if run.execute:
        check(
            "edge gate is in front",
            code == "302",
            f"HTTP {code} — 302 expected; 530 means the tunnel is down; "
            "200 would mean Access is NOT applied",
        )


def rollback(run: Runner, host: str) -> None:
    """Put the previous image back and prove that it is the one running."""
    print("\n== rollback ==")
    run.run(_ssh(host, "docker", "tag", _PREV_TAG, _LIVE_TAG))
    prev_id = _remote_image_id(run, host, _LIVE_TAG)
    run.run(
        _ssh(
            host,
            "docker",
            "compose",
            "-f",
            _HOST_COMPOSE,
            "-p",
            _PROJECT,
            "up",
            "-d",
            "--force-recreate",
            "app",
        )
    )
    assert_running_image(run, host, prev_id)


def report() -> int:
    """Print the ledger and return a shell exit code."""
    print()
    if not _results:
        print("=== nothing checked ===")
        return 0
    width = max(len(label) for label, _, _ in _results)
    failed = sum(1 for _, ok, _ in _results if not ok)
    for label, ok, detail in _results:
        suffix = f"  ({detail})" if detail else ""
        print(f"{label.ljust(width)} : {'PASS' if ok else 'FAIL'}{suffix}")
    print()
    print(f"=== {len(_results)} checks, {failed} FAIL ===")
    return 0 if failed == 0 else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="deploy.py",
        description="Redeploy the published OCT demo to the deploy host.",
    )
    # No default host, deliberately: an accidental or half-written invocation
    # must have nothing to aim at.
    parser.add_argument("--host", required=True, help="ssh alias of the deploy host")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually run the commands. Without this the run is a PLAN and touches nothing. "
        "Running against MS-S1 is a host-state change and needs Cray's go (CLAUDE.md §8).",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help=f"retag {_PREV_TAG} back to {_LIVE_TAG} and recreate the app container",
    )
    parser.add_argument(
        "--smoke-url",
        default=None,
        help="public health URL to probe from this machine; expects 302",
    )
    args = parser.parse_args(argv[1:])

    repo_root = Path(__file__).resolve().parents[2]
    run = Runner(execute=args.execute)

    print("=== vero-lite published-demo redeploy ===")
    print(f"mode  : {'EXECUTE' if args.execute else 'PLAN (nothing will run)'}")
    print(f"host  : {args.host}")
    print(f"repo  : {repo_root}")

    try:
        if args.rollback:
            rollback(run, args.host)
        else:
            image_id = build_and_ship(run, args.host, repo_root)
            recreate = sync_host_checkout(run, args.host)
            bring_up(run, args.host, recreate_connector=recreate)
            assert_running_image(run, args.host, image_id)
            smoke(run, args.host, args.smoke_url)
    except CommandFailedError as exc:
        check("command succeeded", False, str(exc)[:200])

    return report()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
