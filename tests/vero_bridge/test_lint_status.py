"""Tests for ``lint_status`` — PLAN-0012 Step 2b (tool 3/4).

``lint_status`` reports whether ``docs/STATUS.md`` is fresh vs the local
``main`` branch. Unlike the first two tools it depends on real commit history,
so these tests build throwaway git repos with controlled histories and run the
real ``git log`` queries against them (faithful to the merge-commit /
``docs(status):`` behaviour that the freshness logic must handle).

Coverage:

- **Freshness logic** (``tools.vero_bridge._status_lint``): fresh; stale (with
  the drift list); ``docs(status):`` commits excluded (``--invert-grep``);
  merge commits excluded (``--no-merges`` — the false-drift-after-reconcile
  case this repo's PR workflow would otherwise hit); missing ``head_commit``
  and bogus ``head_commit`` both fail closed to ``fresh=False``.
- **Server handler** (``_handle_lint_status``): response shape, envelope
  fail-closed, audit side-effects, AC-7 parity.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.vero_bridge import _audit_log, _status_lint
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge._status_lint import compute_status_freshness
from tools.vero_bridge.server import _handle_lint_status

_GIT = shutil.which("git") or "git"


def _git(repo: Path, *args: str) -> str:
    """Run a git command in ``repo`` (check=True for setup); return stdout."""
    result = subprocess.run(
        [_GIT, *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _init(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")


def _commit(repo: Path, relpath: str, content: str, msg: str) -> str:
    """Write + commit a file; return the short SHA of the new commit."""
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", relpath)
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "--short", "HEAD")


def _status_body(head_commit: str | None) -> str:
    head_line = f"head_commit: {head_commit}\n" if head_commit is not None else ""
    return f"---\nlast_updated: 2026-05-29T00:00:00+07:00\nsession: 1\n{head_line}---\n\n# Status\n"


def _commit_status(
    repo: Path, head_commit: str | None, msg: str = "docs(status): reconcile"
) -> str:
    """Commit docs/STATUS.md (a ``docs(status):`` commit) with the given head."""
    return _commit(repo, "docs/STATUS.md", _status_body(head_commit), msg)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    _init(r)
    return r


@pytest.fixture
def audit_log_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reset_counter_for_test()
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", path)
    return path


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# Freshness logic — compute_status_freshness
# ---------------------------------------------------------------------------


def test_fresh_when_status_points_at_newest_substantive(repo: Path) -> None:
    _commit(repo, "a.txt", "1", "feat: a")
    c2 = _commit(repo, "b.txt", "2", "feat: b")
    _commit_status(repo, c2)  # STATUS reconciled up to the newest substantive

    result = compute_status_freshness(repo_root=repo)
    assert result["fresh"] is True
    assert result["status_head_commit"] == c2
    assert result["newest_substantive_sha"] == c2
    assert result["drift_commits"] == []


def test_stale_when_substantive_commit_landed_after_head(repo: Path) -> None:
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    c2 = _commit(repo, "b.txt", "2", "feat: b")
    _commit_status(repo, c1)  # STATUS only reconciled up to c1 — c2 has drifted

    result = compute_status_freshness(repo_root=repo)
    assert result["fresh"] is False
    assert result["status_head_commit"] == c1
    assert result["newest_substantive_sha"] == c2
    assert result["drift_commits"] == [c2]


def test_docs_status_commits_after_head_do_not_count(repo: Path) -> None:
    """``--invert-grep``: STATUS-reconcile commits after head are not drift."""
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    _commit_status(repo, c1, msg="docs(status): first reconcile")
    # A second, distinct docs(status): commit after head (different file).
    _commit(repo, "docs/notes.md", "ledger tweak\n", "docs(status): second tweak")

    result = compute_status_freshness(repo_root=repo)
    assert result["fresh"] is True
    assert result["drift_commits"] == []


def test_merge_commit_after_head_does_not_count(repo: Path) -> None:
    """``--no-merges``: a STATUS-reconcile merged via a merge commit must not
    read as drift (its merge subject 'Merge pull request …' would otherwise
    survive ``--invert-grep``). This is the real merge-commit-workflow case."""
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    # Reconcile STATUS to c1 on a branch, then merge with a merge commit.
    _git(repo, "checkout", "-q", "-b", "status-branch")
    _commit_status(repo, c1, msg="docs(status): reconcile up to c1")
    _git(repo, "checkout", "-q", "main")
    _git(
        repo,
        "merge",
        "--no-ff",
        "-q",
        "-m",
        "Merge pull request #1 from status-branch",
        "status-branch",
    )

    result = compute_status_freshness(repo_root=repo)
    assert result["fresh"] is True  # without --no-merges the merge commit = false drift
    assert result["drift_commits"] == []


def test_missing_head_commit_fails_closed(repo: Path) -> None:
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    _commit(repo, "docs/STATUS.md", _status_body(None), "docs(status): no head field")

    result = compute_status_freshness(repo_root=repo)
    assert result["fresh"] is False
    assert result["status_head_commit"] is None
    assert result["newest_substantive_sha"] == c1
    assert result["drift_commits"] == []


def test_bogus_head_commit_fails_closed(repo: Path) -> None:
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    _commit_status(repo, "deadbeef")  # not a resolvable object → range query fails

    result = compute_status_freshness(repo_root=repo)
    assert result["fresh"] is False
    assert result["status_head_commit"] == "deadbeef"
    assert result["newest_substantive_sha"] == c1
    assert result["drift_commits"] == []


def test_missing_status_file_fails_closed(tmp_path: Path) -> None:
    """A repo with no docs/STATUS.md at all → fresh=False, head=None."""
    empty = tmp_path / "empty"
    _init(empty)
    _commit(empty, "a.txt", "1", "feat: a")
    result = compute_status_freshness(repo_root=empty)
    assert result["fresh"] is False
    assert result["status_head_commit"] is None


# ---------------------------------------------------------------------------
# Server handler
# ---------------------------------------------------------------------------


def test_handler_returns_documented_shape(
    repo: Path, audit_log_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    _commit_status(repo, c1)
    monkeypatch.setattr(_status_lint, "REPO_ROOT", repo)

    response = _handle_lint_status(version=1, claimed_tag="cowork")
    assert response["ok"] is True
    assert set(response) == {
        "ok",
        "fresh",
        "status_head_commit",
        "newest_substantive_sha",
        "drift_commits",
    }
    assert response["fresh"] is True


def test_handler_writes_ok_audit_record(
    repo: Path, audit_log_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    _commit_status(repo, c1)
    monkeypatch.setattr(_status_lint, "REPO_ROOT", repo)

    _handle_lint_status(version=1, claimed_tag="cowork")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "lint_status"
    assert records[0]["claimed_tag"] == "cowork"
    assert records[0]["outcome"] == "ok"
    assert records[0]["error_code"] is None


def test_handler_version_mismatch_returns_error(audit_log_path: Path) -> None:
    response = _handle_lint_status(version=99, claimed_tag="cowork")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"


def test_handler_empty_claimed_tag_returns_malformed_frame(audit_log_path: Path) -> None:
    response = _handle_lint_status(version=1, claimed_tag="")
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"


def test_handler_ac7_parity_across_clients(
    repo: Path, audit_log_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    c1 = _commit(repo, "a.txt", "1", "feat: a")
    _commit_status(repo, c1)
    monkeypatch.setattr(_status_lint, "REPO_ROOT", repo)

    chat = _handle_lint_status(version=1, claimed_tag="chat")
    cowork = _handle_lint_status(version=1, claimed_tag="cowork")
    assert chat == cowork
    records = _read_audit_lines(audit_log_path)
    assert [r["claimed_tag"] for r in records] == ["chat", "cowork"]
