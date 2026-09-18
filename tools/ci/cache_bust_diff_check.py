"""Fail CI when a changed static asset ships behind an unchanged ``?v=`` token.

Replaces ``test_every_edited_asset_got_a_cache_bust`` (PLAN-0107 AC-14), which is
deleted in the same commit rather than kept alongside. That guard froze a per-file
*minimum* token for **9 of 21 JS files and 0 of 4 CSS files**, so it passed today and
would still have passed with the thing it protects broken: editing ``views.css``
without bumping its token in ``index.html`` was invisible to it, and that exact shape
happened — PR #1190's ``c43 → c44`` bump was hand-made and unguarded. A guard that
cannot fail for the reason it exists is retired, not supplemented.

**Why a diff instead of a floor.** The token is a per-file counter, not a build
number (differing values across files are normal, not drift), so there is no global
invariant to assert. The only true statement is relational: *if the bytes changed,
the token must have changed too.* That needs the PR's two revisions, which is why the
CI step wants ``fetch-depth: 2`` — at depth 1 ``HEAD^1`` does not exist and the check
cannot run at all.

**Three outcomes, deliberately distinct.** A stale token is a violation. A changed
asset carrying **no** ``?v=`` reference is *not* — ``favicon.svg`` is on disk,
referenced by convention rather than by a versioned tag, so treating "absent from the
HTML" as a failure would redden CI on a favicon edit with no fix available. It is
reported instead, so the silence is visible rather than assumed. Everything else
passes.

**Why the scope is discovered, not listed** (s310). The original check hard-coded one
pair — ``static/assets/`` against ``static/index.html`` — and that is precisely how it
came to be wrong: the story page (PLAN-0126) shipped at ``static/story/`` with its own
``index.html``, and a measured s309 run over a PR that changed ``story.js`` and
``story-data.js`` printed ``0 bumped, 0 unversioned, 0 stale``. The page was outside
the gate and nothing said so. A list would have fixed *that* page and left the next one
to repeat it, so the surfaces are found by walking :data:`STATIC_ROOT` for
``index.html`` — and :mod:`tests.tools.test_cache_bust_diff_check` locks the discovered
set against a committed expectation, so widening the gate's reach still arrives as a
reviewable diff rather than as a silent change of scope.

**Why references are resolved to repo paths.** ``story.css`` exists **twice** —
``static/assets/story.css`` (the console's story view, ``?v=c25``) and
``static/story/story.css`` (the story page, ``?v=c1``). Keying on a bare filename
resolves the story page's asset against the *console's* token, which is a guard that
reads the wrong number and reports green. So every reference is resolved against its
own index's directory into a repo-relative path: bare ``story.css`` in the story index
becomes ``services/api/static/story/story.css`` and can never collide with the
console's. That join is the whole defence, and it is what the unit suite mutates.

A left-boundary lookbehind was drafted alongside it and then **measured redundant** —
identical output on both shipped indexes and on seven adversarial strings, because
greedy leftmost matching already captures the maximal path. It was dropped rather than
shipped with a test that could never redden (§8, vacuous oracle).

:func:`check` is pure — changed files and both revisions of every index in, findings
out — so the unit suite drives every verdict, including the PR #1190 shape and the
``story.css`` collision, without git.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

#: The tree walked for cache-bust surfaces. Every ``index.html`` under it is one.
STATIC_ROOT = "services/api/static"

#: The filename that marks a directory as a cache-bust surface.
INDEX_NAME = "index.html"

#: Every ``<href-as-written>?v=<token>`` pair in a document. The href class excludes
#: whitespace and quotes, so the prose in the console index's own comments — which
#: contains both ``assets/*`` and a bare ``?v=`` — cannot be mistaken for a reference
#: (measured: 25 matches in a file with 3 such comment lines, zero phantoms). It is
#: deliberately not anchored to a tag, so a future ``<img src="assets/…?v=…">`` is
#: covered without an edit here.
_REFERENCE_RE = re.compile(r"([A-Za-z0-9._/-]+)\?v=([A-Za-z0-9._-]+)")


def discover_indexes(repo_root: Path) -> list[str]:
    """Every cache-bust surface under :data:`STATIC_ROOT`, as repo-relative paths.

    Sorted, so the merge order in :func:`check` is deterministic rather than
    filesystem-dependent.
    """
    static = repo_root / STATIC_ROOT
    return sorted(p.relative_to(repo_root).as_posix() for p in static.rglob(INDEX_NAME))


def references(index_path: str, html: str) -> dict[str, str]:
    """Map every versioned reference in ``html`` to its repo-relative asset path.

    The href is resolved against the *index's own* directory, which is what makes one
    implementation serve both layouts: the console index at ``static/`` writes
    ``assets/app.js``, the story index at ``static/story/`` writes bare ``story.js``,
    and both land on the path git reports in a diff.
    """
    index_dir = posixpath.dirname(index_path)
    return {
        posixpath.normpath(posixpath.join(index_dir, href)): token
        for href, token in _REFERENCE_RE.findall(html)
    }


@dataclass(frozen=True)
class Findings:
    """What one comparison produced. Three lists, never collapsed into a count.

    ``stale`` and ``unversioned`` are opposite conditions with the same cardinality
    when a run is quiet, and a single number could not tell them apart — the donor
    sweep in ``services/db/repair_case_retention.py`` makes the same point about its
    own counters.

    Entries are full repo-relative paths, not bare filenames: with two surfaces in
    scope a bare ``story.css`` names two different files, so the report would be
    ambiguous exactly where the collision it must survive lives.
    """

    stale: list[str] = field(default_factory=list)
    unversioned: list[str] = field(default_factory=list)
    bumped: list[str] = field(default_factory=list)


def check(
    changed_files: Iterable[str],
    revisions: Mapping[str, tuple[str, str]],
) -> Findings:
    """Compare each changed asset's token across both revisions of every surface.

    ``revisions`` maps an index's repo-relative path to its ``(old_html, new_html)``.
    A newly added asset has no token in the old revision; ``None != "c24"`` so it counts
    as bumped, which is correct — its first token is its first bump.

    A changed file is only *reported* as unversioned when it sits in a directory some
    index already versions something from. That keeps ``assets/fonts/``,
    ``assets/brand/`` and ``assets/narratives/`` silent, as they are today, while
    ``static/story/three.module.min.js`` — a real asset in a versioned directory that
    carries no token — becomes visible instead of assumed.
    """
    new_refs: dict[str, str] = {}
    old_refs: dict[str, str] = {}
    for index_path in sorted(revisions):
        old_html, new_html = revisions[index_path]
        # setdefault, not update: if two surfaces ever version the same asset with
        # different tokens, first-sorted-index wins DETERMINISTICALLY rather than
        # last-iterated. The sets are disjoint today (measured) and a test locks that.
        for path, token in references(index_path, new_html).items():
            new_refs.setdefault(path, token)
        for path, token in references(index_path, old_html).items():
            old_refs.setdefault(path, token)

    versioned_dirs = {posixpath.dirname(path) for path in new_refs}

    findings = Findings()
    for path in sorted(set(changed_files)):
        if path in revisions:
            continue  # the versioning surface itself is not a versioned asset
        new_token = new_refs.get(path)
        if new_token is None:
            if posixpath.dirname(path) in versioned_dirs:
                findings.unversioned.append(path)
            continue
        if old_refs.get(path) == new_token:
            findings.stale.append(f"{path} (still ?v={new_token})")
        else:
            findings.bumped.append(path)
    return findings


def _git(*args: str) -> str:
    # S603/S607: fixed `git` argv, no shell. The only caller-supplied value is
    # `--base`, which reaches git as a revision argument and never as a command.
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _git_show_or_absent(base: str, path: str) -> str:
    """``base:path``, or ``""`` when the path did not exist at ``base``.

    Not an error: a surface added by this very PR has no old revision, and every one of
    its references is then a first bump. The caller has already run a diff against
    ``base``, so a failure here means "absent at base" and not "unresolvable rev" —
    and a mistyped path still fails loudly, on the new-side read that follows.
    """
    completed = subprocess.run(  # noqa: S603
        ["git", "show", f"{base}:{path}"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cache_bust_diff_check", description=__doc__)
    parser.add_argument(
        "--base",
        default="HEAD^1",
        help="revision to compare against (default HEAD^1 — needs fetch-depth: 2)",
    )
    args = parser.parse_args(argv)

    try:
        changed = [p for p in _git("diff", "--name-only", args.base, "HEAD").splitlines() if p]
    except subprocess.CalledProcessError as exc:
        # Loud, and it names WHICH half failed: a shallow clone fails on the rev-parse
        # of HEAD^1, which is the fetch-depth mistake this check is most likely to hit.
        print(f"CACHE_BUST: ERROR — git failed ({exc.cmd}): {exc.stderr.strip()}", file=sys.stderr)
        return 2

    indexes = discover_indexes(Path.cwd())
    if not indexes:
        # An empty scope would otherwise print a serene "0 stale" — the exact shape of
        # silence this check exists to remove.
        print(
            f"CACHE_BUST: ERROR — no {INDEX_NAME} found under {STATIC_ROOT}/; "
            "the gate has no surface to check",
            file=sys.stderr,
        )
        return 2

    revisions = {
        index_path: (
            _git_show_or_absent(args.base, index_path),
            Path(index_path).read_text(encoding="utf-8"),
        )
        for index_path in indexes
    }

    findings = check(changed, revisions)

    # Print the measured scope, not just the verdict: a surface that silently dropped
    # out of the walk is invisible in a bare "0 stale" (CLAUDE.md §8).
    versioned = sum(len(references(path, new)) for path, (_, new) in revisions.items())
    print(f"  scope       {len(indexes)} surface(s), {versioned} versioned reference(s)")
    for index_path in indexes:
        print(f"              {index_path}")
    for name in findings.bumped:
        print(f"  bumped      {name}")
    for name in findings.unversioned:
        print(f"  unversioned {name} — changed but carries no ?v= reference (not a failure)")
    for entry in findings.stale:
        print(f"  STALE       {entry}", file=sys.stderr)

    if findings.stale:
        print(
            f"CACHE_BUST: FAIL — {len(findings.stale)} changed asset(s) ship behind an "
            "unchanged ?v= token; a browser keeps serving the pre-edit file",
            file=sys.stderr,
        )
        return 1
    print(
        f"CACHE_BUST: OK — {len(indexes)} surface(s), {len(findings.bumped)} bumped, "
        f"{len(findings.unversioned)} unversioned, 0 stale"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
