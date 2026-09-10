#!/usr/bin/env python3
"""Guard: ``docs/STATUS.md``'s ``head_commit`` must resolve — and its drift is PRINTED.

🔴 **The measured failure this makes visible.** At session 291's open, STATUS's
frontmatter read ``head_commit: 793b9d9`` while ``main`` stood at ``f65f7ea`` — nine
substantive commits behind, four merged PRs (#1453-#1456) recorded nowhere in the
file every session reads first. Nothing said so. A re-deriver for exactly this field
already existed — ``tools/vero_bridge/_status_lint.py::compute_status_freshness``,
fail-closed — but it ran only when a human called the ``lint_status`` MCP tool, which
nobody did. The number was there to be measured and was not being looked at.

**What this guard gates, and what it deliberately does NOT.** It exits non-zero on
exactly one condition: STATUS is unreadable, has no ``head_commit``, or names a sha
that does not resolve on the baseline — a *broken* pointer, not a *stale* one. Drift
itself is **printed, never gated**: ``fresh`` in the underlying function is
zero-tolerance, and STATUS is reconciled *after* PRs merge, so a zero-tolerance gate
would redden every PR that lands between reconciles — including ``main`` on the day
this shipped. That is the over-refusing shape ``tests/tools/test_guards_hold_on_the_real_tree.py``
exists to prevent: a guard that cries wolf gets routed around, and the real finding
goes with it. The threshold above which drift *should* gate is a decision, not a
constant — it is PLAN-0125 SD-1, Cray's to rule.

**Why the value is printed every run.** A verification report that prints only
PASS/FAIL withholds the evidence it just collected (CLAUDE.md §8). ``drift=9`` is the
whole diagnosis; ``OK`` is a hunt. Wired ``always_run`` + ``verbose: true`` in
pre-commit so the committer sees the number on every commit, not on the day someone
is surprised.

**Baseline unavailable is reported, not hidden.** In a shallow CI checkout ``main``
may not exist locally. The guard then prints ``baseline=main UNAVAILABLE`` and exits 0
— a *visible* skip, not a pass. The RED witness for the hard assertion lives in this
guard's own test module, which builds a repository where ``main`` does exist.

Exit codes: 0 = ``head_commit`` resolves (drift printed) or baseline unavailable
(printed); 1 = STATUS unreadable / ``head_commit`` missing / sha does not resolve.
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

    print(f"{PREFIX} head={head} newest={newest} drift={len(drift)} fresh={fresh}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
