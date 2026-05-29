"""STATUS.md freshness check for the ``lint_status`` bridge tool.

PLAN-0012 Step 2b (capability inventory §2.6). Reports whether
``docs/STATUS.md`` is stale — i.e. whether substantive commits have landed on
the integration branch since STATUS last reconciled. Useful as drafting
context for Cowork (check before authoring a session-reconcile). Read-only:
one file read + read-only ``git log`` queries; no write, no state mutation.

**Baseline ref = local ``main`` (not ``origin/main``, not ``HEAD``).** Rationale
(real-operation smoothness): "fresh" means "STATUS reflects what has *landed*",
and the landed line is the ``main`` integration branch. ``HEAD`` is wrong — Code
usually works on a feature branch, so it would count not-yet-merged WIP as
drift. ``origin/main`` is fragile — the bridge server runs in WSL local to the
repo with no guaranteed network; ``origin/main`` is a remote-tracking ref that
only updates on ``git fetch`` (stale or unqueryable offline), whereas local
``main`` is refreshed by ``gh``'s pull on every PR merge from this machine and
is queryable as a ref regardless of the checked-out branch. Caveat: if a PR is
ever merged from the GitHub web UI rather than ``gh`` on this machine, local
``main`` lags until the next ``git pull`` — a Phase-2 opt-in ``fetch`` could
close that, gated on network + fail-closed.

**``docs(status):`` and merge commits are excluded** when computing drift:
``--invert-grep --grep='^docs(status):'`` drops STATUS-reconcile commits (they
do not themselves need reconciling), and ``--no-merges`` drops the
"Merge pull request #N …" commits — *essential* under this repo's merge-commit
PR workflow, since a STATUS-reconcile PR's merge commit subject does **not**
match ``^docs(status):`` and would otherwise be counted as false drift right
after a reconcile.

Fail-closed: if STATUS is unreadable / has no ``head_commit`` / the baseline
ref or range query fails, the check reports ``fresh=False`` (cannot confirm
fresh ⇒ assume needs-attention) rather than raising.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

#: Repo root, anchored to this file's location (``tools/vero_bridge/`` →
#: ``parents[2]``). Stable regardless of the process CWD. Tests monkeypatch it.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: STATUS ledger path, relative to the repo root.
STATUS_REL_PATH: str = "docs/STATUS.md"

#: The integration branch the freshness check is measured against. A single
#: constant so a policy change (e.g. to ``origin/main``) is a one-line edit.
BASELINE_REF: str = "main"

#: Resolved ``git`` executable (absolute path; avoids a partial-path argv).
_GIT: str = shutil.which("git") or "git"

#: Frontmatter ``head_commit: <sha>`` line in ``docs/STATUS.md``.
_HEAD_COMMIT_RE = re.compile(r"^head_commit:[ \t]*(?P<sha>\S+)")

#: Commit-message prefix that marks a STATUS-reconcile commit (excluded from
#: drift via ``--invert-grep``). BRE-literal — parens are literal in git's
#: default basic-regex grep.
_STATUS_COMMIT_GREP: str = "^docs(status):"


def _read_status_head_commit(repo_root: Path) -> str | None:
    """Extract ``head_commit`` from the ``docs/STATUS.md`` frontmatter block.

    Returns the short SHA string, or ``None`` if STATUS is unreadable, has no
    ``---`` frontmatter fence, or has no ``head_commit`` field.
    """
    try:
        text = (repo_root / STATUS_REL_PATH).read_text(encoding="utf-8")
    except OSError:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _HEAD_COMMIT_RE.match(line)
        if match is not None:
            sha = match.group("sha").strip()
            return sha or None
    return None


def _git_substantive_shas(repo_root: Path, revrange: str | None) -> list[str] | None:
    """Short SHAs of substantive commits (non-merge, non-``docs(status):``).

    ``revrange`` is a git revision range (e.g. ``"<sha>..main"``); when
    ``None`` the whole baseline branch is listed (newest first). Returns the
    SHA list, or ``None`` if git cannot be run or the query fails (bad ref,
    not a repo, timeout) — the caller treats ``None`` as fail-closed.
    """
    cmd = [
        _GIT,
        "log",
        "--no-merges",
        "--invert-grep",
        f"--grep={_STATUS_COMMIT_GREP}",
        "--format=%h",
        revrange if revrange is not None else BASELINE_REF,
    ]
    try:
        # S603: fixed argv, no shell; the only interpolated value is a git
        # revision range built from a STATUS-sourced short SHA + a constant ref.
        result = subprocess.run(  # noqa: S603
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def compute_status_freshness(repo_root: Path | None = None) -> dict[str, Any]:
    """Compute the ``docs/STATUS.md`` freshness result.

    Returns ``{"fresh", "status_head_commit", "newest_substantive_sha",
    "drift_commits"}``. ``fresh`` is ``True`` iff no substantive
    (non-merge, non-``docs(status):``) commit has landed on the baseline ref
    since ``status_head_commit``. Fail-closed: any unreadable STATUS / missing
    ``head_commit`` / git failure reports ``fresh=False``.
    """
    root = (repo_root if repo_root is not None else REPO_ROOT).resolve()
    head = _read_status_head_commit(root)
    newest_list = _git_substantive_shas(root, None)
    newest = newest_list[0] if newest_list else None

    if head is None or newest_list is None:
        return {
            "fresh": False,
            "status_head_commit": head,
            "newest_substantive_sha": newest,
            "drift_commits": [],
        }

    drift = _git_substantive_shas(root, f"{head}..{BASELINE_REF}")
    if drift is None:
        # Range query failed — e.g. head_commit is not a resolvable object.
        return {
            "fresh": False,
            "status_head_commit": head,
            "newest_substantive_sha": newest,
            "drift_commits": [],
        }

    return {
        "fresh": len(drift) == 0,
        "status_head_commit": head,
        "newest_substantive_sha": newest,
        "drift_commits": drift,
    }
