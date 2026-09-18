"""The cache-bust gate driven end to end: real git, real CLI, real exit code.

The unit suite beside this one drives :func:`check`, which is pure — changed files and
both HTML revisions in, findings out. That is the right shape for the verdict logic and
the wrong shape for the s309 failure, because **nothing in it was wrong**. The check
computed a correct answer about the assets it was handed; the defect was that `main`
never handed it the story page at all. A suite that supplies its own `revisions` mapping
agrees with itself about scope by construction and cannot see that (CLAUDE.md §8).

So these cases stub neither side of the seam. Each one builds a throwaway repository
with the real two-surface layout, commits it, edits an asset, commits again, and runs
``python -m tools.ci.cache_bust_diff_check`` as a subprocess exactly as ``ci.yml`` does
— including the ``HEAD^1`` base that needs ``fetch-depth: 2``. The assertion is the
process's own exit code and output.

:func:`test_a_changed_story_asset_behind_an_unchanged_token_fails_ci` is the s309 shape
end to end: on ``fix/story-v2a`` (e0d1d041) this exact edit printed
``CACHE_BUST: OK — 0 bumped, 0 unversioned, 0 stale`` and exited 0.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

_CONSOLE_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Asset cache-busting: bump the ?v= token on ANY assets/* edit so a NORMAL
       browser reload picks up the change. The cached ?v=<token> URL is reused. -->
  <link rel="stylesheet" href="assets/theme.css?v=c51" />
  <link rel="stylesheet" href="assets/story.css?v=c25" />
</head>
<body>
  <div id="app"></div>
  <script src="assets/app.js?v=c52"></script>
</body>
</html>
"""

_STORY_INDEX = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="utf-8" />
  <title>เพลาขาดที่ปากช่อง</title>
  <link rel="stylesheet" href="story.css?v=c1" />
</head>
<body>
<div class="stage" id="stage"></div>
<script src="story-data.js?v=c1"></script>
<script type="module" src="story.js?v=c1"></script>
</body>
</html>
"""

#: The shipped layout, including the two files that share the name ``story.css`` and
#: the untokenised ``three.module.min.js``. Both are load-bearing: the first is the
#: collision, the second the reported-not-failed outcome.
_TREE = {
    "services/api/static/index.html": _CONSOLE_INDEX,
    "services/api/static/assets/theme.css": ":root { --bg: #0b0d10; }\n",
    "services/api/static/assets/story.css": ".story-view { display: grid; }\n",
    "services/api/static/assets/app.js": "export const boot = () => {};\n",
    "services/api/static/assets/favicon.svg": "<svg xmlns='http://www.w3.org/2000/svg'/>\n",
    "services/api/static/assets/fonts/LICENSE.txt": "SIL OFL 1.1\n",
    "services/api/static/story/index.html": _STORY_INDEX,
    "services/api/static/story/story.css": ".stage { position: fixed; }\n",
    "services/api/static/story/story.js": "export const acts = [];\n",
    "services/api/static/story/story-data.js": "window.STORY = { acts: [] };\n",
    "services/api/static/story/three.module.min.js": "// vendored three.js\n",
}


def _git(repo: Path, *args: str) -> None:
    # S603/S607: fixed argv, no shell, `git` via PATH — the same idiom as
    # tools/check_plan_archive_refs.py. Identity is passed with -c so the run never
    # depends on (or writes) a global git config.
    subprocess.run(
        ["git", "-c", "user.email=t@t.invalid", "-c", "user.name=T", *args],  # noqa: S607
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _write(repo: Path, rel: str, body: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway repo holding the real two-surface layout at one commit."""
    _git(tmp_path, "init", "-q", "-b", "main")
    for rel, body in _TREE.items():
        _write(tmp_path, rel, body)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "baseline")
    return tmp_path


def _run_check(repo: Path) -> subprocess.CompletedProcess[str]:
    """Run the CI step's exact command line against ``repo``.

    ``PYTHONPATH`` points at the real repository so the module is importable while
    ``cwd`` — which is what the check resolves its paths against — is the fixture.
    """
    env = {**os.environ, "PYTHONPATH": str(_REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "tools.ci.cache_bust_diff_check"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_changed_story_asset_behind_an_unchanged_token_fails_ci(repo: Path) -> None:
    """🔴 The s309 shape, end to end. This is the case the gate did not have.

    ``story.js`` gains a line and its ``?v=c1`` is left alone — the edit that shipped
    green on fix/story-v2a. The gate must now exit 1 and name the file.
    """
    _write(repo, "services/api/static/story/story.js", "export const acts = [1, 2, 3];\n")
    _git(repo, "commit", "-q", "-am", "story: v2a")

    result = _run_check(repo)

    assert result.returncode == 1, (
        "a changed story asset behind an unchanged token must FAIL CI; got "
        f"rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert (
        "services/api/static/story/story.js (still ?v=c1)" in result.stderr
    ), f"the failure must name the story file and its token; stderr:\n{result.stderr}"


def test_the_same_story_edit_with_the_token_bumped_passes(repo: Path) -> None:
    """The positive control: identical edit, ``?v=c1`` → ``?v=c2``, and CI goes green.

    Without it, the failure above could come from a gate that reddens on any story
    edit at all — red for the wrong reason, and unusable.
    """
    _write(repo, "services/api/static/story/story.js", "export const acts = [1, 2, 3];\n")
    bumped = _STORY_INDEX.replace("story.js?v=c1", "story.js?v=c2")
    _write(repo, "services/api/static/story/index.html", bumped)
    _git(repo, "commit", "-q", "-am", "story: v2a, token bumped")

    result = _run_check(repo)

    assert (
        result.returncode == 0
    ), f"a bumped token must pass; stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "1 bumped" in result.stdout, f"the bump must be counted; stdout:\n{result.stdout}"


def test_the_console_surface_still_fails_on_a_stale_token(repo: Path) -> None:
    """The pre-existing console guard, re-driven end to end after the rewrite.

    PR #1190's shape. Widening the scope must not have cost the surface that already
    worked — a regression here would trade one blind spot for another.
    """
    _write(repo, "services/api/static/assets/theme.css", ":root { --bg: #111; }\n")
    _git(repo, "commit", "-q", "-am", "theme tweak")

    result = _run_check(repo)

    assert (
        result.returncode == 1
    ), f"console assets must still be guarded; stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "services/api/static/assets/theme.css (still ?v=c51)" in result.stderr


def test_both_surfaces_are_reported_as_in_scope(repo: Path) -> None:
    """The scope line is printed, and it names both pages.

    s309's gate said ``0 bumped, 0 unversioned, 0 stale`` — a serene verdict that was
    true of the one page it looked at. Printing the surfaces is what makes the
    difference between "nothing is wrong" and "nothing was examined" readable at a
    glance (CLAUDE.md §8: a report prints the values it measured).
    """
    _write(repo, "docs/note.md", "unrelated\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs only")

    result = _run_check(repo)

    assert result.returncode == 0, f"stderr:\n{result.stderr}"
    assert "2 surface(s)" in result.stdout, f"stdout:\n{result.stdout}"
    assert "services/api/static/index.html" in result.stdout
    assert "services/api/static/story/index.html" in result.stdout


def test_an_untokenised_asset_in_a_versioned_dir_is_reported_not_failed(repo: Path) -> None:
    """``three.module.min.js`` changes: reported, exit 0 — the favicon precedent.

    It is imported by ``story.js`` rather than referenced from the page, so there is
    no token to bump and failing would block a legitimate commit with no fix available.
    """
    _write(repo, "services/api/static/story/three.module.min.js", "// vendored three.js r160\n")
    _git(repo, "commit", "-q", "-am", "bump vendored three")

    result = _run_check(repo)

    assert (
        result.returncode == 0
    ), f"an untokenised asset must not fail CI; stderr:\n{result.stderr}"
    assert "unversioned services/api/static/story/three.module.min.js" in result.stdout
    assert "1 unversioned" in result.stdout


def test_a_story_page_added_in_this_commit_counts_as_all_bumped(repo: Path) -> None:
    """A surface with no revision at ``base``: every reference is a first bump.

    ``git show HEAD^1:…/story/index.html`` fails for a page that did not exist yet.
    Treating that as an error would make the gate refuse the very commit that adds a
    page — which is the first moment it has anything to say.
    """
    for rel in list(_TREE):
        if rel.startswith("services/api/static/story/"):
            (repo / rel).unlink()
    _git(repo, "commit", "-q", "-am", "remove the story page")
    for rel, body in _TREE.items():
        if rel.startswith("services/api/static/story/"):
            _write(repo, rel, body)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "add the story page")

    result = _run_check(repo)

    assert result.returncode == 0, f"adding a page must not fail the gate; stderr:\n{result.stderr}"
    assert (
        "3 bumped" in result.stdout
    ), f"the new page's three versioned assets are all first bumps; stdout:\n{result.stdout}"
