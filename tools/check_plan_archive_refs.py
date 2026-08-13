#!/usr/bin/env python3
"""Pre-commit guard: no tracked artifact may cite a PLAN by its pre-archive path
(rotation policy R8).

Completing a PLAN ends in ``git mv docs/plans/NNNN-slug.md docs/plans/done/``.
That single move silently kills every reference to the old path across the repo,
and the rot is invisible: nothing errors, the prose still reads correctly, and a
reader only discovers it by following the link and landing on nothing.

Same failure shape as R7 -- "the anchor rots by construction" -- but the other
direction. R7 stops artifacts citing STATUS by a line number that a reconcile
will move; R8 stops artifacts citing a PLAN by a path that archival will move.

**The predicate is deliberately narrow: MOVED, not MISSING.** A violation is a
reference to ``docs/plans/<slug>`` where that file is absent *and*
``docs/plans/done/<slug>`` exists. Measured on the tree at 2026-07-28 (s183):

* "path does not resolve" flags **89 files** -- overwhelmingly placeholders
  (``NNNN-*.md``, ``0011-xxx.md``, ``x.md``) and forward references to files that
  were never written. Unusable as a fail-closed gate.
* "moved to done/" flags **29 files, every one a real dead pointer.** Placeholders
  cannot trip it: ``NNNN-name.md`` has no twin under ``done/``.

References are matched in both their full-slug and **glob** (``0100-*.md``)
forms. The glob shape is what registries and closeout notes actually write, and
it rots identically -- but the original slug class admitted no ``*``, so those
citations never matched and the guard stayed silent on them from R8's landing
until this change. Measured cost of the blindspot: the ``stream-status`` skill's
stream-1 row went dead when PLAN-0100 was archived at s216 and was never once
reported, including by the very commit that updated the stream-2 row beside it
for the same reason one session later.

Widening the class does not soften the predicate: a glob is a violation only
when it matches nothing under ``docs/plans/`` **and** something under
``docs/plans/done/``, so placeholders and forward references still cannot trip
it.

Exit codes: 0 = clean; 1 = at least one pre-archive citation found.

``PLAN_REF_ROOT`` overrides the scanned repo root for tests (mirrors the
``STATUS_CITATION_ROOT`` / ``STATUS_SIZE_PATH`` override family).
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

# `docs/plans/0094-loop-detect-...md`, the legacy `docs/plans/PLAN-001-...md`,
# and the GLOB form (a `0094-*.md` slug) that registries and closeout notes use.
# The slug is captured so it can be re-tested under `done/`.
#
# The glob example above is deliberately written WITHOUT its `docs/plans/`
# prefix: spelled in full it is a live citation of an archived PLAN, and this
# guard would flag its own source. That is the narration trap the failure
# message at the bottom of this file describes -- prose about a dead pointer
# that contains one re-breaks the check it is describing.
#
# `*` belongs in the slug class: a glob citation rots exactly like a full-slug
# one, but matched nothing here, so the guard passed over it in silence. It
# does NOT widen the predicate toward "path does not resolve" -- `has_moved`
# still demands a twin under `done/`, and a placeholder (`NNNN-*.md`) has none.
PLAN_REF_RE = re.compile(r"docs/plans/((?:\d{4}|PLAN-\d+)-[A-Za-z0-9._*-]+\.md)")

# Paths where a `docs/plans/...` string is DATA, not navigation -- exempt on
# principle, not convenience.
EXEMPT_PREFIXES = (
    # Test fixtures: the path is an argument fed to a hook, not a link. Several
    # rows assert the ALLOW side of a write gate ("plan-drafter may write
    # docs/plans/<x>.md"), so rewriting them to `done/` would silently change
    # what the test tests. Tests must also be free to name paths that never
    # exist (`9999-ghost.md`) -- that is their input space.
    "tests/",
    # Tier-3 frozen history. Same mandatory reasoning as R7's archive carve-out:
    # archives are move-only and never rewritten (R4), so a path frozen inside an
    # archived block must stay exactly as written.
    "docs/status-archive/",
    # An archived PLAN narrating its own pre-archive path is describing its own
    # history, not pointing at a live file. ~40 files do this by construction.
    "docs/plans/done/",
    # TEMPORARY, and tracked as such -- NOT a judgement that ADRs may rot.
    # 8 Accepted ADRs carry pre-archive PLAN references, and CLAUDE.md's G1 gate
    # blocks Code from editing an Accepted ADR's body, so they cannot be repaired
    # from here. They are queued to ride the parked CLAUDE.md Cowork dispatch.
    # Remove this prefix in the same change that lands those fixes.
    "docs/adr/",
    # The stop-classifier GOLD SET: a corpus of SIMULATED assistant turns fed to
    # the classifier and scored, so a path inside one is benchmark INPUT, not
    # navigation -- the `tests/` reasoning exactly. Its `pause-plan-status-flip`
    # case has an assistant announcing it is about to `git mv` the PLAN-0028
    # reference into `done/`; re-pointing that reference at `done/` makes the
    # sentence self-contradictory and silently changes what the benchmark
    # measures. (Named descriptively, not as a literal path, for the reason
    # given beside PLAN_REF_RE.)
    #
    # FILE-scoped, not directory-scoped, and that is the whole point: the
    # RESULTS.md beside it is a genuine navigation surface, and a benchmark
    # RESULTS.md is exactly where this rot shows up.
    "benchmarks/stop_classifier/gold.yaml",
)


def is_exempt(rel_path: str) -> bool:
    """True if `rel_path` (POSIX, repo-relative) is outside R8's scope."""
    return rel_path.startswith(EXEMPT_PREFIXES)


class EnumerationError(RuntimeError):
    """`git ls-files` could not enumerate the tree.

    Fatal by design, mirroring the R7 guard: a guard that cannot enumerate
    cannot certify the tree clean, and "no files found" is indistinguishable
    from "the scan silently failed" -- the fail-OPEN shape these guards exist to
    prevent.
    """


def tracked_files(root: Path) -> list[Path]:
    """Repo-relative paths of every git-tracked file under `root`.

    Raises `EnumerationError` if git is unavailable or errors (fail-closed).
    """
    try:
        # S603: fixed argv, no shell. S607: "git" via PATH -- the same idiom as
        # tools/check_status_citations.py.
        proc = subprocess.run(  # noqa: S603
            ["git", "ls-files", "-z"],  # noqa: S607
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        )
    except FileNotFoundError as exc:  # git not on PATH
        raise EnumerationError("git executable not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"exit {exc.returncode}"
        raise EnumerationError(f"git ls-files failed in {root}: {detail}") from exc
    return [Path(p) for p in proc.stdout.split("\0") if p]


def _dir_has_match(directory: Path, slug: str) -> bool:
    """True iff a regular file DIRECTLY in `directory` matches the glob `slug`.

    Deliberately not `Path.glob`: `slug` is untrusted text scraped out of prose,
    and `glob` assigns extra meaning to `**` and to path separators. Matching
    names from a single flat `iterdir()` keeps the lookup one level deep, which
    is what stops the live-side probe from descending into `done/` and reporting
    every archived PLAN as still-live -- a fail-OPEN inversion of the guard.
    """
    if not directory.is_dir():
        return False
    return any(fnmatch.fnmatch(e.name, slug) and e.is_file() for e in directory.iterdir())


def has_moved(root: Path, slug: str) -> bool:
    """True iff `docs/plans/<slug>` is gone AND `docs/plans/done/<slug>` exists.

    Both halves are load-bearing. Without the first, a live PLAN's own path
    reports as a violation; without the second, every placeholder and every
    never-written forward reference does.

    `slug` may be a glob (`0094-*.md`). The predicate is unchanged in kind --
    still MOVED, not MISSING -- it just asks the two questions of a pattern:
    does it match nothing live, and something archived?
    """
    plans = root / "docs" / "plans"
    if "*" in slug:
        return not _dir_has_match(plans, slug) and _dir_has_match(plans / "done", slug)
    return not (plans / slug).is_file() and (plans / "done" / slug).is_file()


FENCE_RE = re.compile(r"^\s*(```|~~~)")


def find_violations(root: Path, files: list[Path]) -> list[tuple[str, int, str, str]]:
    """Scan `files` (repo-relative) under `root`; return (path, lineno, slug, line).

    Fenced code blocks are skipped. A path inside a fence is DATA, not
    navigation -- the same principle that exempts `tests/`. Measured cases this
    protects: a lesson quoting the literal L1 counter key
    (``counter["counters"].pop("L1:docs/plans/0010-...md")``) and a lesson
    quoting verbatim hook output. Rewriting either to `done/` would falsify the
    historical record rather than repair a link.
    """
    violations: list[tuple[str, int, str, str]] = []
    for rel in files:
        rel_posix = rel.as_posix()
        if is_exempt(rel_posix):
            continue
        target = root / rel
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Binary or unreadable (e.g. a deleted-but-staged path) -- not a
            # citation surface.
            continue
        in_fence = False
        for lineno, line in enumerate(text.splitlines(), start=1):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for slug in PLAN_REF_RE.findall(line):
                if has_moved(root, slug):
                    violations.append((rel_posix, lineno, slug, line.strip()))
    return violations


def main() -> int:
    root = Path(os.environ.get("PLAN_REF_ROOT") or ".").resolve()
    try:
        files = tracked_files(root)
    except EnumerationError as exc:
        print(
            f"plan-archive-ref-guard (R8): cannot enumerate tracked files — "
            f"{exc}. Failing closed: an un-enumerable tree is not a clean tree.",
            file=sys.stderr,
        )
        return 1
    violations = find_violations(root, files)
    if not violations:
        return 0
    print(
        f"plan-archive-ref-guard (R8): {len(violations)} reference(s) to a PLAN "
        f"by its PRE-ARCHIVE path (the file now lives under docs/plans/done/):",
        file=sys.stderr,
    )
    for rel_posix, lineno, slug, line in violations:
        print(f"  {rel_posix}:{lineno}: {line}", file=sys.stderr)
        print(f"      -> docs/plans/{slug}  lives at  docs/plans/done/{slug}", file=sys.stderr)
    print(
        "\nCompleting a PLAN ends in `git mv docs/plans/NNNN-*.md docs/plans/done/`, "
        "which kills every reference to the old path at once — silently, because "
        "nothing errors and the prose still reads correctly. Re-point the "
        "reference at docs/plans/done/<slug>.\n\n"
        "If you are NARRATING a stale pointer rather than citing one (a "
        "correction note, a lesson about the rot), name it descriptively — "
        "'the PLAN-0095 reference' — never as a literal path. This guard cannot "
        "tell narration from assertion, and prose about a dead pointer that "
        "contains one re-breaks the check it is describing.\n\n"
        "Policy: docs/runbooks/memory-architecture.md §'R8'.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
