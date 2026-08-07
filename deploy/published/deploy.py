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
import subprocess
import sys
import tempfile
from pathlib import Path

#: Paths on the deploy host. Fixed by Cray's session-213 decision (the checkout
#: location and the staging directory), not discovered — a deploy that guesses
#: where the checkout lives is a deploy that can update the wrong tree.
_HOST_CHECKOUT = r"C:\projects\vero-lite"
_HOST_COMPOSE = r"C:\projects\vero-lite\deploy\published\docker-compose.yml"
_HOST_STAGING = r"C:\vero-staging\app.tar"

#: Names that MUST agree with `docker-compose.yml`. They are literals here
#: because this script is stdlib-only by design (an operator runs it outside the
#: venv, exactly like `verify_tunnel_credentials.py`), so there is no YAML parser
#: to read them with. `tests/deploy/test_deploy.py` reads the committed compose
#: file and asserts each one still matches — the drift this cannot prevent, that
#: test catches.
_PROJECT = "vero-published"
_APP_CONTAINER = "vero-published-app"
_CLOUDFLARED_CONTAINER = "vero-published-cloudflared"

#: compose names a built image `<project>-<service>` when the service declares
#: `build:` and no `image:`, which is exactly what the app service does.
_IMAGE = "vero-published-app"
_PREV_TAG = f"{_IMAGE}:prev"
_LIVE_TAG = f"{_IMAGE}:latest"

#: Repo-relative paths whose change means the HOST checkout must be pulled before
#: `up`, because compose reads them from disk on the host rather than from the
#: image: the compose file itself, the env file it loads, and the ingress
#: allowlist that is bind-mounted into the connector.
_HOST_READ_PATHS = (
    "deploy/published/docker-compose.yml",
    "deploy/published/published.env",
    "deploy/published/cloudflared/config.yml",
)

#: The one whose change ALSO requires recreating the connector. A bind mount
#: shows the new file on disk immediately, but cloudflared reads its config once
#: at start — so `up -d` alone leaves the old ingress map live, with nothing to
#: indicate it.
_CONNECTOR_CONFIG = "deploy/published/cloudflared/config.yml"

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

    def run(self, argv: list[str], *, capture: bool = True) -> str:
        """Run `argv` with NO shell. Returns stdout (stripped), or "" when planning."""
        self.log.append(argv)
        if not self.execute:
            print(f"  would run: {' '.join(argv)}")
            return ""
        # S603: every argv this script builds is literals plus the operator's own
        # `--host` / `--smoke-url`, and `shell=False` is the point of the design —
        # it is what removes the quoting-hazard class entirely. Running programs
        # IS the job here; there is no untrusted input to sanitise.
        completed = subprocess.run(  # noqa: S603
            argv,
            capture_output=capture,
            text=True,
            check=False,
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

    Nothing here is quoted for a remote shell on purpose: every remote command
    this script issues is built from literals with no `$`, no inner quotes and no
    pipes, which is what keeps it safe to send. A step that needs more than that
    belongs in a `.ps1` piped over stdin (see the `ms-s1-admin` skill), not
    inlined here.
    """
    return ["ssh", host, *remote]


def _local_image_id(run: Runner) -> str:
    return run.run(["docker", "image", "inspect", _LIVE_TAG, "--format={{.Id}}"])


def _remote_image_id(run: Runner, host: str, tag: str) -> str:
    return run.run(_ssh(host, "docker", "image", "inspect", tag, "--format={{.Id}}"))


def build_and_ship(run: Runner, host: str, repo_root: Path) -> str:
    """Build here, save, copy, load there. Returns the local image id."""
    print("\n== 1. build on this machine ==")
    compose_file = str(repo_root / "deploy" / "published" / "docker-compose.yml")
    # compose interpolates the WHOLE file before deciding what to build, and the
    # cloudflared service declares CLOUDFLARED_CREDENTIALS_FILE required — so a
    # build fails without it even though building the app touches neither the
    # variable nor the connector. Nothing is created at this path: volumes are
    # materialised at container-create time, not at build.
    run.run(
        [
            "docker",
            "compose",
            "-f",
            compose_file,
            "build",
            "app",
        ],
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
    with tempfile.TemporaryDirectory() as tmp:
        tar = str(Path(tmp) / "app.tar")
        run.run(["docker", "save", _LIVE_TAG, "-o", tar])
        run.run(["scp", tar, f"{host}:{_HOST_STAGING}"])
    run.run(_ssh(host, "docker", "load", "-i", _HOST_STAGING))

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
    running = run.run(_ssh(host, "docker", "inspect", _APP_CONTAINER, "--format={{.Image}}"))
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
    # so this reports the same fact the topology already acts on.
    #
    # It is also the only form that is SAFE to send: an inlined `python -c …`
    # carries inner quotes and a `;`, and ssh hands the remote shell one joined
    # string to re-parse. The no-shell guarantee holds on THIS side of the
    # connection only; a remote command must therefore be literals with no
    # quotes, no `$` and no separators, which `--format=` satisfies and a
    # one-liner does not.
    health = run.run(
        _ssh(host, "docker", "inspect", _APP_CONTAINER, "--format={{.State.Health.Status}}")
    )
    if run.execute:
        check("app healthcheck reports healthy", health == "healthy", health or "<no verdict>")

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
