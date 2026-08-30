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
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def classify(runs: list[dict[str, Any]], *, deadline_exceeded: bool = False) -> Verdict:
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


class ShaResolutionError(ValueError):
    """The argument could not be turned into one full commit sha."""


#: A full git object name. GitHub's `gh run list --commit` matches ONLY this form.
_FULL_SHA = re.compile(r"\A[0-9a-f]{40}\Z")

#: An abbreviated one. Bounded below at 7 because git's own default abbreviation
#: is 7 and anything shorter is far more likely to be a typo than an intent.
_SHORT_SHA = re.compile(r"\A[0-9a-f]{7,39}\Z")


def resolve_sha(raw: str) -> str:
    """Turn an accepted argument into the full 40-character sha, or refuse.

    Exists because a short sha used to reach the API unchanged, come back with
    zero runs, and be reported as NO-RUN — a verdict that means "CI has not run
    here", stated about a commit where it had run and passed. Measured at s262 on
    a sha whose full form returned PASS. The failure is safe in direction (this
    tool can still never report a green it did not measure) but it is a false
    reading all the same, and a tool whose exit 0 means "measured pass" becomes
    one that simply cannot pass.

    Deliberately accepts hex prefixes ONLY — never ``HEAD``, a branch, or a tag.
    Resolving a moving ref would reintroduce the very thing the ``--sha`` flag is
    required for: a green is a claim about ONE commit, and a ref answers with
    whatever it points at when asked, which is not necessarily what the caller
    was looking at.

    Raises :class:`ShaResolutionError` rather than returning anything the caller
    could mistake for an answer. The one outcome this must never produce is a
    value that flows on to be reported as NO-RUN.
    """
    candidate = raw.strip().lower()
    if _FULL_SHA.match(candidate):
        return candidate
    if not _SHORT_SHA.match(candidate):
        raise ShaResolutionError(
            f"{raw!r} is not a commit sha. Pass the full 40-character sha, or an "
            f"abbreviation of at least 7 hex characters — a branch name, a tag or "
            f"HEAD is refused on purpose, because a green is a claim about one "
            f"commit and a moving ref is not one."
        )
    # `^{commit}` forces a commit rather than a tag object, and git fails loudly on
    # an ambiguous or unknown prefix — which is the behaviour wanted here, since
    # guessing between two candidates would put the verdict on the wrong commit.
    proc = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    resolved = proc.stdout.strip()
    if proc.returncode != 0 or not _FULL_SHA.match(resolved):
        raise ShaResolutionError(
            f"{raw!r} does not resolve to a commit in this repository "
            f"(git rev-parse exit {proc.returncode}). A sha this clone has never "
            f"seen cannot be the one CI ran on."
        )
    return resolved


def _gh_runs(sha: str) -> list[dict[str, Any]]:
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

    # Resolved FIRST, so nothing downstream ever sees an abbreviation. A short sha
    # reaching the API returns zero runs, and zero runs is reported as NO-RUN —
    # the one verdict a caller reads as a fact about CI rather than about their
    # own argument. ERROR (2) instead: the tool could not answer, which is true.
    try:
        sha = resolve_sha(args.sha)
    except ShaResolutionError as exc:
        print(f"CI_WAIT: ERROR       {exc}", file=sys.stderr)
        return 2
    if sha != args.sha.strip().lower():
        # Said out loud, on stderr so it cannot be mistaken for the verdict line.
        # A step that silently changes which commit is queried is exactly the kind
        # of invisible substitution this tool exists to make impossible.
        print(f"CI_WAIT: resolved {args.sha} -> {sha}", file=sys.stderr)

    if args.mode == "wait":
        stale = SENTINEL_DIR / f"{sha}.done"
        # A previous run's answer would otherwise read as this one's.
        stale.unlink(missing_ok=True)
        verdict = _wait(sha, args.deadline_min)
    else:
        try:
            verdict = classify(_gh_runs(sha))
        except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
            print(f"CI_WAIT: ERROR       gh call failed: {exc}", file=sys.stderr)
            return 2

    _emit(verdict, sha)
    return verdict.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
