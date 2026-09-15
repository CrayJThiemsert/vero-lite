#!/usr/bin/env python3
"""Guard: ``docs/STATUS.md``'s ``head_commit`` must resolve — and its drift is PRINTED.

🔴 **The measured failure this makes visible.** At session 291's open, STATUS's
frontmatter read ``head_commit: 793b9d9`` while ``main`` stood at ``f65f7ea`` — nine
commits (three substantive) behind, four merged PRs (#1453-#1456) recorded nowhere in
the file every session reads first. Nothing said so. A re-deriver for exactly this field
already existed — ``tools/vero_bridge/_status_lint.py::compute_status_freshness``,
fail-closed — but it ran only when a human called the ``lint_status`` MCP tool, which
nobody did. The number was there to be measured and was not being looked at.

**What this guard gates, and what it deliberately does NOT.** It exits non-zero when
STATUS is unreadable, has no ``head_commit``, or names a sha that does not resolve on
the baseline — a *broken* pointer — and when ``docs/STATUS.md`` is in the commit's
staged set while drift is non-zero. On every other commit drift is **printed, never
gated**: STATUS is reconciled *after* PRs merge, so gating every commit would redden
each PR that lands between reconciles — the over-refusing shape
``tests/tools/test_guards_hold_on_the_real_tree.py`` exists to prevent. The commit that
edits STATUS is the one claiming to describe ``main``, so that is where the pointer
must be current: drift gates only when ``docs/STATUS.md`` is staged
(PLAN-0125 SD-1 = c, Cray, typed, s299); on every other commit it is printed.

**Why the value is printed every run.** A verification report that prints only
PASS/FAIL withholds the evidence it just collected (CLAUDE.md §8). ``drift=9`` is the
whole diagnosis; ``OK`` is a hunt. Wired ``always_run`` + ``verbose: true`` in
pre-commit so the committer sees the number on every commit, not on the day someone
is surprised.

**Baseline unavailable is reported, not hidden.** In a shallow CI checkout ``main``
may not exist locally. The guard then prints ``baseline=main UNAVAILABLE`` and exits 0
— a *visible* skip, not a pass. The RED witness for the hard assertion lives in this
guard's own test module, which builds a repository where ``main`` does exist.

Exit codes: 0 = ``head_commit`` resolves and STATUS is unstaged or at drift 0, or baseline
unavailable (printed); 1 = a broken pointer, or STATUS staged while drift > 0.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.vero_bridge._status_lint import (  # noqa: E402  (path insert above)
    BASELINE_REF,
    STATUS_REL_PATH,
    compute_status_freshness,
)

#: The line prefix every run prints. Named PREFIX, not TOKEN — ruff S105 reads any
#: identifier containing "token" as a possible credential.
PREFIX = "STATUS-FRESHNESS:"


def _baseline_resolves(root: Path) -> bool:
    """True iff ``BASELINE_REF`` names a commit in ``root``. Fail-closed on no git."""
    git = shutil.which("git")
    if git is None:
        return False
    # S603: fixed argv, no shell; the only interpolated value is BASELINE_REF, a
    # module constant — the same idiom as tools/ci/wait_for_ci.py:175.
    proc = subprocess.run(  # noqa: S603
        [git, "rev-parse", "--verify", "--quiet", f"{BASELINE_REF}^{{commit}}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _status_is_staged(root: Path) -> bool:
    """True iff ``docs/STATUS.md`` is in the staged set — the index against ``HEAD``.

    That set is what a pre-commit hook's commit will carry: pre-commit stashes unstaged
    changes before its hooks run. The query lists the **whole** staged set and then
    looks for STATUS in it, rather than asking git with a pathspec, so "nothing staged"
    and "something else staged" stay two distinguishable readings.

    🔴 **The environment is inherited, never scrubbed.** ``git commit -a`` and
    ``git commit -- <paths>`` run hooks with ``GIT_INDEX_FILE`` naming a *temporary*
    index that holds the commit's real staged set (probed s299, PLAN-0125 §9). A git
    child handed a minimal ``env`` would read the default index instead — empty under
    ``-a`` — and pass every such reconcile in print mode, silently. ``cwd`` stays at the
    repository root because a plain commit sets that variable to the relative
    ``.git/index``.

    A git that cannot read its index prints nothing, which reads as an empty set: print
    mode, the pre-gate behaviour. A commit cannot be built from an unreadable index, so
    that is never the commit this gate exists for.
    """
    git = shutil.which("git")
    if git is None:
        return False
    # S603: fixed argv, no shell, nothing interpolated.
    proc = subprocess.run(  # noqa: S603
        [git, "diff", "--cached", "--name-only", "-z"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    names = [name for name in proc.stdout.split("\0") if name]
    if not names:
        # The `--all-files` / CI shape: the ruling's "every other commit" arm.
        return False
    return STATUS_REL_PATH in names


def _baseline_lag(root: Path) -> int | None:
    """Commits ``origin/main`` holds that local ``main`` does not — PRINTED, never gated.

    ``BASELINE_REF`` is a local ref and this guard never fetches: a hook whose reading
    moves with connectivity would red on the network, not on the record. A lagging
    local ``main`` under-counts drift, so the failure direction is a miss, never a false
    red — and printing the lag is what keeps that miss visible. ``None`` when
    ``origin/main`` does not resolve (a fresh clone, every throwaway test repository).
    """
    git = shutil.which("git")
    if git is None:
        return None
    # S603: fixed argv, no shell; the only interpolated value is BASELINE_REF, a constant.
    proc = subprocess.run(  # noqa: S603
        [git, "rev-list", "--count", f"{BASELINE_REF}..origin/{BASELINE_REF}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    text = proc.stdout.strip()
    if proc.returncode != 0 or not text.isdigit():
        return None
    return int(text)


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else REPO_ROOT

    if not _baseline_resolves(root):
        print(f"{PREFIX} baseline={BASELINE_REF} UNAVAILABLE — skipped, NOT a pass")
        return 0

    result = compute_status_freshness(root)
    head = result["status_head_commit"]
    newest = result["newest_substantive_sha"]
    drift = result["drift_commits"]
    fresh = result["fresh"]

    if head is None:
        print(f"{PREFIX} head_commit MISSING or STATUS unreadable — exit 1")
        return 1
    if newest is None:
        print(f"{PREFIX} head={head} baseline={BASELINE_REF} has no substantive commit — exit 1")
        return 1
    if not fresh and not drift:
        # The range query failed: head_commit is not a resolvable object on the baseline.
        print(f"{PREFIX} head={head} does NOT resolve on {BASELINE_REF} — exit 1")
        return 1

    staged = _status_is_staged(root)
    mode = "gate" if staged else "print"
    lag = _baseline_lag(root)
    lag_text = "n/a" if lag is None else str(lag)
    print(
        f"{PREFIX} head={head} newest={newest} drift={len(drift)} fresh={fresh} "
        f"staged={staged} mode={mode} baseline_lag={lag_text}"
    )
    if staged and drift:
        print(
            f"{PREFIX} {STATUS_REL_PATH} is STAGED with drift={len(drift)} — point "
            f"head_commit at main's tip before committing (PLAN-0125 SD-1 = c, Cray s299) "
            f"— exit 1"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
