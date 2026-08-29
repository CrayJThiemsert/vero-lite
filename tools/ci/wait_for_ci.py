"""Answer "did CI pass at THIS sha" without ever inferring a pass from silence.

Replaces the hand-rolled CI wait. Session 261 wrote that wait four times in one
hour and got four different wrong answers: a break condition that read "no checks
registered yet" as "settled green"; a redirect placed outside the ``wsl bash -lc``
quoted argument, so the output landed on the Windows filesystem and a later WSL
``cat`` reported it missing; an exit code asserted from memory rather than measured;
and a ``$(...)`` inside an ``until`` condition expanded one shell layer early, which
froze the condition to a literal and produced a loop that could not terminate and
had to be killed by hand.

**Two independent defect classes, and only one of them is about quoting.**

*Layer-boundary theft* — a token written for the inner shell is claimed by an outer
layer. This file is the whole remedy: a script has exactly one shell layer, so the
class is not mitigated here, it is impossible. That fix was already discovered in
this repo on 2026-06-12 and written down in
``.claude/skills/ms-s1-ollama/_run_detached_body.sh``, where it stayed, scoped to
MS-S1, until it was re-derived badly eleven weeks later.

*A non-terminal state read as terminal* — the domain has THREE states (settled
green, settled red, **not yet known**) and hand-rolled waits model two. No script
file prevents that, so it is prevented here by construction: every verdict requires
a POSITIVE terminal token, and absence is its own verdict. That fix, too, already
existed — as an untracked ``.git/ci_wait.sh`` dated 2026-08-15, carrying the comment
"Never infers PASS from the absence of a failure word", where no grep of tracked
files could ever find it. This module is that script, promoted somewhere a reader
can reach and a test can drive.

**Why the run at a sha, and not ``gh pr checks``.** ``gh pr checks`` has no
``--json`` on the pinned gh (2.45), so its output must be parsed as text, and the
question it answers is about a PR rather than about the commit whose green is being
claimed. A green must be pinned to the sha it was measured at or it is a claim about
a tree that has since moved.

:func:`classify` is pure — the parsed run list in, a verdict out — so every outcome,
including the empty list that started all this, is driven by fixtures with no
network and no ``gh``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

#: Repo root, resolved from THIS FILE rather than the CWD. A sentinel addressed
#: relative to the working directory is one `cd` away from being written somewhere
#: nobody looks — which is the same defect as the Windows-side redirect above.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Where a `wait` run leaves its answer. `.claude/state/` is already gitignored.
SENTINEL_DIR = REPO_ROOT / ".claude" / "state" / "ci_wait"

#: Seconds between polls. Remote API — deliberately not tight.
POLL_INTERVAL_S = 30


@dataclass(frozen=True)
class Verdict:
    """One terminal-or-not answer about the runs at a sha."""

    name: str
    exit_code: int
    detail: str
    run_id: int | None = None

    @property
    def is_terminal(self) -> bool:
        """True when polling again cannot change the answer.

        ``PENDING`` is the ONLY non-terminal verdict. ``NO-RUN`` is deliberately
        terminal for a single ``status`` call but is treated as still-waiting by
        ``wait``, because a run that has not been registered yet is exactly what a
        freshly pushed sha looks like — see :func:`_wait`.
        """
        return self.name != "PENDING"


def classify(runs: list[dict], *, deadline_exceeded: bool = False) -> Verdict:
    """Decide the verdict for the runs at one sha. Pure.

    ``runs`` is the parsed ``gh run list --json databaseId,status,conclusion`` payload.
    """
    if deadline_exceeded:
        return Verdict(
            "TIMEOUT",
            6,
            "no terminal conclusion before the deadline — a timeout is NOT a pass",
        )
    if not runs:
        # The defect that started this. `gh run list -c <sha>` returns `[]` with exit
        # status 0 (measured session 261), so a loop that breaks on "nothing is
        # pending" declares victory instantly against a sha that never even ran.
        return Verdict("NO-RUN", 5, "0 runs at this sha — absence is NOT a pass")

    # Newest by databaseId — a COUNTER, never a clock. WSL2's wall clock steps
    # backwards, so ordering by a timestamp can pick the older run of a re-run pair.
    newest = max(runs, key=lambda r: r["databaseId"])
    run_id = newest["databaseId"]
    extra = f" ({len(runs)} runs at this sha; newest by id wins)" if len(runs) > 1 else ""

    if newest.get("status") != "completed":
        return Verdict("PENDING", 3, f"status={newest.get('status')}{extra}", run_id)

    conclusion = newest.get("conclusion")
    if conclusion == "success":
        return Verdict("PASS", 0, f"conclusion=success{extra}", run_id)
    if conclusion == "cancelled":
        # `cancel-in-progress: true` is set on this repo's workflow, so a cancelled
        # run is the ROUTINE consequence of pushing again — the sha is stale, the
        # code is not broken. Collapsing it into FAIL sends a reader debugging a
        # green branch; collapsing it into PASS ships an untested tree.
        return Verdict(
            "SUPERSEDED",
            4,
            f"conclusion=cancelled — a newer push superseded this sha{extra}",
            run_id,
        )
    return Verdict("FAIL", 1, f"conclusion={conclusion}{extra}", run_id)


def _gh_runs(sha: str) -> list[dict]:
    """The runs GitHub has for one sha. Fixed argv, no shell — there is no layer to eat."""
    proc = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "gh",
            "run",
            "list",
            "--commit",
            sha,
            "--json",
            "databaseId,status,conclusion,headSha,workflowName",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    parsed = json.loads(proc.stdout)
    if not isinstance(parsed, list):
        raise ValueError(f"expected a JSON list from gh, got {type(parsed).__name__}")
    return parsed


def _emit(verdict: Verdict, sha: str) -> None:
    """One verdict line. Non-PASS goes to stderr so a caller cannot miss it."""
    line = f"CI_WAIT: {verdict.name:<11} sha={sha[:7]}"
    if verdict.run_id is not None:
        line += f" run={verdict.run_id}"
    line += f" — {verdict.detail}"
    print(line, file=sys.stdout if verdict.name == "PASS" else sys.stderr)


def _wait(sha: str, deadline_min: int) -> Verdict:
    """Poll until terminal or the deadline. Returns the verdict; also writes a sentinel.

    The deadline is counted in POLLS, not elapsed wall-clock, because WSL2's clock is
    not monotonic and a backwards step would extend or truncate the budget silently.
    """
    max_polls = max(1, (deadline_min * 60) // POLL_INTERVAL_S)
    verdict = Verdict("NO-RUN", 5, "never polled")
    for poll in range(1, max_polls + 1):
        try:
            verdict = classify(_gh_runs(sha))
        except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
            # One transient gh failure must not end the watch, but it must not be
            # mistaken for progress either — keep the last real verdict and retry.
            verdict = Verdict("ERROR", 2, f"gh call failed on poll {poll}: {exc}")
        else:
            # NO-RUN is terminal for `status` but NOT here: a freshly pushed sha has
            # no run registered for a few seconds, and treating that as an answer is
            # precisely the bug this tool exists to prevent.
            if verdict.is_terminal and verdict.name != "NO-RUN":
                break
        if poll < max_polls:
            time.sleep(POLL_INTERVAL_S)
    else:
        if not verdict.is_terminal or verdict.name == "NO-RUN":
            verdict = classify([], deadline_exceeded=True)

    SENTINEL_DIR.mkdir(parents=True, exist_ok=True)
    # Written as the LAST act, so its existence means the answer is complete —
    # the `run_detached.sh` contract. Harness task status is not trusted.
    (SENTINEL_DIR / f"{sha}.done").write_text(
        f"{verdict.name} {verdict.exit_code} {sha} {verdict.run_id} {verdict.detail}\n",
        encoding="utf-8",
    )
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wait_for_ci", description=__doc__)
    parser.add_argument("mode", choices=["status", "wait"])
    # Required, and never defaulted to HEAD: a green is a claim about ONE commit,
    # and a tool that guesses which one will happily report a green for a tree that
    # moved under the caller.
    parser.add_argument("--sha", required=True, help="the commit the claim is about")
    parser.add_argument(
        "--deadline-min",
        type=int,
        default=35,
        help="wait mode: give up after this many minutes (CI's own cap is 30)",
    )
    args = parser.parse_args(argv)

    if args.mode == "wait":
        stale = SENTINEL_DIR / f"{args.sha}.done"
        # A previous run's answer would otherwise read as this one's.
        stale.unlink(missing_ok=True)
        verdict = _wait(args.sha, args.deadline_min)
    else:
        try:
            verdict = classify(_gh_runs(args.sha))
        except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
            print(f"CI_WAIT: ERROR       gh call failed: {exc}", file=sys.stderr)
            return 2

    _emit(verdict, args.sha)
    return verdict.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
