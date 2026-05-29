"""Tests for ``read_repo_path`` — PLAN-0012 Step 2b (first integration tool).

The tool's whole design surface is the **path sandbox**, so the bulk of
this file is the AC-5 negative matrix: every way a path can be outside the
Phase-1 read sandbox must be rejected with ``ErrorCode.PATH_FORBIDDEN``.

Coverage mirrors ``test_server.py`` (happy / fail-closed / audit
side-effects) and adds the sandbox-specific dimensions:

- **Sandbox unit** (``tools.vero_bridge._repo_read``): happy reads of
  git-tracked files; AC-5 rejection of absolute / ``..`` traversal /
  out-of-tree symlink / ``.git/`` / gitignored / untracked / directory /
  oversize / non-UTF-8 paths. Each runs against a real temporary git repo
  (built once per module) so symlink + tracked-status behaviour is faithful.
- **Server handler** (``_handle_read_repo_path``): envelope fail-closed,
  tool-policy rejection, and one audit record per call (accepted *and*
  rejected), with ``claimed_tag`` logged verbatim (OQ-T3 Option I).
- **AC-7 parity**: the Chat path and Cowork path return identical content
  for the same tracked file (the surface has no per-tab branch).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.vero_bridge import _audit_log, _repo_read
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge._repo_read import read_repo_file, resolve_repo_path
from tools.vero_bridge._schema import ErrorCode, PathForbiddenError
from tools.vero_bridge.server import _handle_read_repo_path

# Tracked file contents (ASCII, so byte length == character length).
_README = "# vero-lite fake repo\nhello world\n"
_STATUS = "status: fresh\nfresh: true\n"
_APP = "print('hi from app')\n"


def _git(repo: Path, *args: str) -> None:
    """Run a git command in ``repo``; raise loudly if it fails (fixture setup)."""
    subprocess.run(
        [shutil.which("git") or "git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture(scope="module")
def fake_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a real temporary git repo with a known tracked/untracked layout.

    Only ``git add`` is run (no commit) — ``git ls-files --error-unmatch``
    reads the index, so staging is enough to make a path "tracked".
    """
    base = tmp_path_factory.mktemp("vero_bridge_sandbox")
    repo = base / "repo"
    repo.mkdir()

    # A file OUTSIDE the repo — the escape-symlink target.
    (base / "outside.txt").write_text("outside the repo (never read)\n", encoding="utf-8")

    # Tracked files.
    (repo / "README.md").write_text(_README, encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "STATUS.md").write_text(_STATUS, encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text(_APP, encoding="utf-8")
    (repo / ".gitignore").write_text("secret.txt\n.env\nprivate/\n", encoding="utf-8")
    (repo / "binary.bin").write_bytes(b"\xff\xfe\x00\x01\x02")
    (repo / "big.txt").write_text("A" * 4096, encoding="utf-8")
    os.symlink("../outside.txt", repo / "escape_link")  # tracked symlink, escapes tree

    # Untracked: gitignored sensitive paths + one stray non-ignored file.
    # Contents are deliberately innocuous — these paths are always *rejected*,
    # so their bytes are never returned; only their tracked-status matters.
    (repo / "secret.txt").write_text("ignored file (never read)\n", encoding="utf-8")
    (repo / ".env").write_text("ignored file (never read)\n", encoding="utf-8")
    (repo / "private").mkdir()
    (repo / "private" / "audit.jsonl").write_text("{}\n", encoding="utf-8")
    (repo / "untracked.md").write_text("stray file\n", encoding="utf-8")

    _git(repo, "init", "-q")
    _git(
        repo,
        "add",
        "README.md",
        "docs/STATUS.md",
        "src/app.py",
        ".gitignore",
        "binary.bin",
        "big.txt",
        "escape_link",
    )
    return repo


@pytest.fixture(autouse=True)
def _sandbox_env(
    fake_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Point the sandbox at the fake repo + redirect the audit log so no
    test touches the real working tree or ``docs/research/private/``."""
    reset_counter_for_test()
    monkeypatch.setattr(_repo_read, "REPO_ROOT", fake_repo)
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", tmp_path / "audit.jsonl")


@pytest.fixture
def audit_log_path(tmp_path: Path) -> Path:
    """The same temp path the autouse fixture redirected the audit log to."""
    return tmp_path / "audit.jsonl"


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# Sandbox — happy reads of git-tracked files
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("README.md", _README),
        ("docs/STATUS.md", _STATUS),
        ("src/app.py", _APP),
    ],
)
def test_read_tracked_file_returns_content(path: str, expected: str) -> None:
    rel, size, content = read_repo_file(path)
    assert rel == path
    assert content == expected
    assert size == len(expected.encode("utf-8"))


def test_resolve_returns_in_tree_path(fake_repo: Path) -> None:
    resolved = resolve_repo_path("README.md")
    assert resolved == (fake_repo / "README.md").resolve()
    assert resolved.is_file()


# ---------------------------------------------------------------------------
# Sandbox — AC-5 negative matrix (every rejection is PATH_FORBIDDEN)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",  # absolute
        "../outside.txt",  # traversal (one level)
        "../../etc/passwd",  # traversal (multi level)
        "docs/../../etc/passwd",  # traversal hidden mid-path
        ".git/config",  # sensitive prefix (.git/)
        "secret.txt",  # gitignored (named in .gitignore)
        ".env",  # gitignored (secrets)
        "private/audit.jsonl",  # gitignored directory
        "untracked.md",  # present + NOT ignored, but never `git add`ed
        "does/not/exist.md",  # non-existent
        "src",  # directory (tracked pathspec, not a regular file)
        "docs",  # directory
        "escape_link",  # tracked symlink whose target escapes the tree
    ],
)
def test_out_of_sandbox_path_is_forbidden(path: str) -> None:
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file(path)
    assert excinfo.value.code is ErrorCode.PATH_FORBIDDEN
    assert excinfo.value.requested == path


def test_traversal_reason_names_dotdot() -> None:
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("../outside.txt")
    assert ".." in str(excinfo.value)


def test_symlink_escape_reason_names_escape() -> None:
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("escape_link")
    assert "escapes" in str(excinfo.value)


def test_untracked_reason_names_tracked() -> None:
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("untracked.md")
    assert "tracked" in str(excinfo.value)


def test_directory_reason_names_regular_file() -> None:
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("src")
    assert "regular file" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Sandbox — read-time guards (size + encoding)
# ---------------------------------------------------------------------------


def test_oversize_file_is_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_repo_read, "MAX_READ_BYTES", 10)
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("big.txt")  # 4096 bytes > 10
    assert excinfo.value.code is ErrorCode.PATH_FORBIDDEN
    assert "max read size" in str(excinfo.value)


def test_binary_file_is_forbidden() -> None:
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("binary.bin")
    assert excinfo.value.code is ErrorCode.PATH_FORBIDDEN
    assert "UTF-8" in str(excinfo.value)


def test_nul_byte_path_is_forbidden() -> None:
    """Fail-closed (wire-format §3.1): a NUL byte would raise ValueError
    from the os layer downstream — caught structurally as PATH_FORBIDDEN
    rather than leaked as a raw exception across the MCP boundary."""
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("READ\x00ME.md")
    assert excinfo.value.code is ErrorCode.PATH_FORBIDDEN
    assert "NUL" in str(excinfo.value)


def test_unreadable_file_is_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail-closed: an OSError during the read (perms / vanished mid-call)
    on an otherwise-valid tracked file becomes PATH_FORBIDDEN, never a raw
    exception across the boundary."""

    def _boom(*_args: object, **_kwargs: object) -> str:
        raise PermissionError("simulated unreadable file")

    monkeypatch.setattr(Path, "read_text", _boom)
    with pytest.raises(PathForbiddenError) as excinfo:
        read_repo_file("README.md")
    assert excinfo.value.code is ErrorCode.PATH_FORBIDDEN
    assert "could not be read" in str(excinfo.value)


def test_rejected_read_creates_no_file(fake_repo: Path) -> None:
    """No-write guarantee: a forbidden read never materializes the path."""
    with pytest.raises(PathForbiddenError):
        read_repo_file("does/not/exist.md")
    assert not (fake_repo / "does" / "not" / "exist.md").exists()


# ---------------------------------------------------------------------------
# Server handler — happy path
# ---------------------------------------------------------------------------


def test_handler_happy_returns_documented_shape(audit_log_path: Path) -> None:
    response = _handle_read_repo_path(version=1, claimed_tag="cowork", path="README.md")
    assert response == {
        "ok": True,
        "path": "README.md",
        "size": len(_README.encode("utf-8")),
        "content": _README,
    }


def test_handler_happy_writes_one_ok_audit_record(audit_log_path: Path) -> None:
    _handle_read_repo_path(version=1, claimed_tag="cowork", path="src/app.py")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "read_repo_path"
    assert records[0]["claimed_tag"] == "cowork"
    assert records[0]["outcome"] == "ok"
    assert records[0]["error_code"] is None


# ---------------------------------------------------------------------------
# Server handler — fail-closed (envelope + tool policy)
# ---------------------------------------------------------------------------


def test_handler_version_mismatch_returns_error(audit_log_path: Path) -> None:
    response = _handle_read_repo_path(version=99, claimed_tag="cowork", path="README.md")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"


def test_handler_empty_claimed_tag_returns_malformed_frame(audit_log_path: Path) -> None:
    response = _handle_read_repo_path(version=1, claimed_tag="", path="README.md")
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"


def test_handler_empty_path_returns_malformed_frame(audit_log_path: Path) -> None:
    """An empty ``path`` is a *payload* malformation (not a policy rejection)."""
    response = _handle_read_repo_path(version=1, claimed_tag="cowork", path="")
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "malformed-frame"


@pytest.mark.parametrize("path", ["../outside.txt", "untracked.md", ".env", ".git/config"])
def test_handler_forbidden_path_returns_path_forbidden(audit_log_path: Path, path: str) -> None:
    response = _handle_read_repo_path(version=1, claimed_tag="cowork", path=path)
    assert response["ok"] is False
    assert response["error_code"] == "path-forbidden"
    assert set(response) == {"ok", "error_code", "error_message"}
    records = _read_audit_lines(audit_log_path)
    assert records[0]["tool_name"] == "read_repo_path"
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "path-forbidden"


def test_handler_logs_claimed_tag_verbatim_even_when_spoofed(audit_log_path: Path) -> None:
    """OQ-T3 Option I: the claimed_tag is logged verbatim regardless of value
    — a forbidden read from a spoofed tag still records the spoof."""
    _handle_read_repo_path(version=1, claimed_tag="chat", path="secret.txt")
    records = _read_audit_lines(audit_log_path)
    assert records[0]["claimed_tag"] == "chat"
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "path-forbidden"


def test_handler_mixed_outcomes_all_audited(audit_log_path: Path) -> None:
    _handle_read_repo_path(version=1, claimed_tag="cowork", path="README.md")  # ok
    _handle_read_repo_path(version=1, claimed_tag="cowork", path="../x")  # path-forbidden
    _handle_read_repo_path(version=1, claimed_tag="cowork", path="")  # malformed-frame
    records = _read_audit_lines(audit_log_path)
    outcomes = [(r["tool_name"], r["outcome"], r["error_code"]) for r in records]
    assert outcomes == [
        ("read_repo_path", "ok", None),
        ("read_repo_path", "error", "path-forbidden"),
        ("read_repo_path", "error", "malformed-frame"),
    ]


# ---------------------------------------------------------------------------
# AC-7 cross-client parity
# ---------------------------------------------------------------------------


def test_ac7_read_repo_path_parity_across_clients(audit_log_path: Path) -> None:
    """The same tracked file read from the Chat path vs the Cowork path
    yields an identical response — the surface has no per-tab branch. Only
    the audit-only ``claimed_tag`` differs (and it is not in the response)."""
    chat = _handle_read_repo_path(version=1, claimed_tag="chat", path="README.md")
    cowork = _handle_read_repo_path(version=1, claimed_tag="cowork", path="README.md")
    assert chat == cowork
    records = _read_audit_lines(audit_log_path)
    assert [r["claimed_tag"] for r in records] == ["chat", "cowork"]
