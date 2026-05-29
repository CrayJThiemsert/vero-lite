"""Path-sandboxed, read-only repo file access for the ``read_repo_path`` tool.

PLAN-0012 Step 2b. ``read_repo_path`` (capability inventory §2.4) lets the
Chat + Cowork tabs read the same repo-tracked state Code reads — closing the
Lesson #8 K-2 read-block for contract reasoning + governance review. The
*whole design surface* of the tool is the **path sandbox**: this module is
the load-bearing safety boundary that keeps a read tool from degrading into
an arbitrary-file-read primitive.

Phase-1 conservative allowlist (AC-5). A path is readable iff **all** hold:

1. It is relative (not absolute) and contains no ``..`` component —
   rejected *before* any filesystem touch.
2. It is not under a sensitive prefix (``.git/``) — defense in depth even
   though git internals are never tracked.
3. After symlink resolution it stays inside :data:`REPO_ROOT` (a tracked
   symlink whose target is outside the tree is still rejected).
4. It is **tracked by git** (``git ls-files``). This is the load-bearing
   rule: every gitignored sensitive path (``.env``, ``.claude/state/``,
   ``docs/research/private/`` audit logs, ``docs/strategy/private/``) is
   untracked and therefore refused by construction — without maintaining a
   hand-curated denylist that could drift.
5. It resolves to a regular file no larger than :data:`MAX_READ_BYTES`
   whose bytes decode as UTF-8 text.

Any violation raises :class:`PathForbiddenError`
(``ErrorCode.PATH_FORBIDDEN``); the server surfaces it through
:func:`tools.vero_bridge.format_error_response`, identically to an envelope
rejection. There is **no write path** in this module — by design
(AC-8 / ADR-013 D2): the bridge never acquires repo-write authority.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tools.vero_bridge._schema import PathForbiddenError

#: Repo root, anchored to this file's location (``tools/vero_bridge/`` →
#: ``parents[2]``). Anchored to the source tree rather than the process CWD
#: so the sandbox boundary is stable regardless of how the server was
#: spawned. Tests monkeypatch this to a temporary git repo.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: Largest file the tool will return. Generous for governance/source text;
#: a guard against returning a pathological blob over the transport.
MAX_READ_BYTES: int = 2 * 1024 * 1024

#: First-component path prefixes refused even if (accidentally) tracked.
#: The git-tracked allowlist already excludes gitignored sensitive paths;
#: this is belt-and-suspenders for git's own internals.
_SENSITIVE_PREFIXES: tuple[str, ...] = (".git",)

#: Resolved ``git`` executable (absolute path; avoids a partial-path argv).
#: Falls back to the bare name — a missing git then surfaces as an OSError
#: in :func:`_is_tracked`, which fails closed (treats the path as untracked).
_GIT: str = shutil.which("git") or "git"


def _is_tracked(repo_root: Path, rel: str) -> bool:
    """Return ``True`` iff ``rel`` is a git-tracked path under ``repo_root``.

    Uses ``git ls-files --error-unmatch`` (exit 0 ⇔ the pathspec matches at
    least one tracked index entry). Any failure to run git (missing binary,
    not a repository, timeout) is treated as *not tracked* — fail-closed.
    """
    try:
        # S603: fixed argv, no shell; ``rel`` is passed as data after ``--``
        # so it can never be interpreted as a git option or shell token.
        result = subprocess.run(  # noqa: S603
            [_GIT, "ls-files", "--error-unmatch", "--", rel],
            cwd=repo_root,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def resolve_repo_path(path: str, repo_root: Path | None = None) -> Path:
    """Validate ``path`` against the Phase-1 read sandbox.

    Returns the resolved absolute :class:`Path` that is safe to read. Raises
    :class:`PathForbiddenError` on any sandbox violation. Pure policy +
    filesystem inspection: performs no read and never writes.
    """
    root = (repo_root if repo_root is not None else REPO_ROOT).resolve()

    # 1. Structural — reject before touching the filesystem.
    if Path(path).is_absolute() or path.startswith("/"):
        raise PathForbiddenError(path, "absolute paths are not allowed")
    parts = Path(path).parts
    if ".." in parts:
        raise PathForbiddenError(path, "parent-directory traversal ('..') is not allowed")

    # 2. Sensitive-prefix denylist (defense in depth).
    if parts and parts[0] in _SENSITIVE_PREFIXES:
        raise PathForbiddenError(path, f"path under a sensitive prefix ({parts[0]}/)")

    # 3. Containment — resolve symlinks; the real target must stay in-tree.
    candidate = (root / path).resolve()
    if candidate != root and root not in candidate.parents:
        raise PathForbiddenError(path, "path escapes the repository root")

    # 4. Allowlist — must be git-tracked (excludes every gitignored path).
    if not _is_tracked(root, path):
        raise PathForbiddenError(path, "path is not tracked by git (Phase-1 allowlist)")

    # 5a. Regular file only (a directory pathspec also matches ls-files).
    if not candidate.is_file():
        raise PathForbiddenError(path, "path is not a regular file")

    return candidate


def read_repo_file(path: str, repo_root: Path | None = None) -> tuple[str, int, str]:
    """Resolve + read a sandboxed repo path.

    Returns ``(path, size, content)`` where ``size`` is the file's byte
    length and ``content`` is its UTF-8 text. Raises
    :class:`PathForbiddenError` on any sandbox violation, an oversize file,
    or non-UTF-8 content.
    """
    candidate = resolve_repo_path(path, repo_root=repo_root)

    # 5b. Size guard — stat before read so a huge file never hits memory.
    size = candidate.stat().st_size
    if size > MAX_READ_BYTES:
        raise PathForbiddenError(path, f"file exceeds max read size ({MAX_READ_BYTES} bytes)")

    # 5c. UTF-8 text only — a binary file is refused, not returned mangled.
    try:
        content = candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise PathForbiddenError(path, "file is not valid UTF-8 text") from None

    return path, size, content
