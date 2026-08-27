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
referenced by convention rather than by a versioned tag (measured: 26 assets on
disk, 25 versioned), so treating "absent from the HTML" as a failure would redden
CI on a favicon edit with no fix available. It is reported instead, so the silence
is visible rather than assumed. Everything else passes.

:func:`check` is pure — changed files and both HTML revisions in, findings out — so
the unit suite drives both verdicts, including the PR #1190 shape, without git.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field

#: Only assets under this prefix carry a cache-bust token.
ASSET_PREFIX = "services/api/static/assets/"

#: The document whose ``?v=`` tokens are the cache-bust surface.
INDEX_PATH = "services/api/static/index.html"


def token_for(html: str, asset_name: str) -> str | None:
    """The ``?v=`` token ``html`` serves ``asset_name`` at, or ``None`` if unversioned.

    Matches the reference form used by both the stylesheet links and the script
    tags — ``assets/<name>?v=<token>`` — and is deliberately not anchored to a tag,
    so a future ``<img src="assets/…?v=…">`` is covered without an edit here.
    """
    match = re.search(rf"assets/{re.escape(asset_name)}\?v=([A-Za-z0-9._-]+)", html)
    return match.group(1) if match else None


@dataclass(frozen=True)
class Findings:
    """What one comparison produced. Three lists, never collapsed into a count.

    ``stale`` and ``unversioned`` are opposite conditions with the same cardinality
    when a run is quiet, and a single number could not tell them apart — the donor
    sweep in ``services/db/repair_case_retention.py`` makes the same point about its
    own counters.
    """

    stale: list[str] = field(default_factory=list)
    unversioned: list[str] = field(default_factory=list)
    bumped: list[str] = field(default_factory=list)


def check(changed_files: list[str], old_html: str, new_html: str) -> Findings:
    """Compare each changed asset's token across the two HTML revisions.

    A newly added asset has no token in ``old_html``; ``None != "c24"`` so it counts
    as bumped, which is correct — its first token is its first bump.
    """
    findings = Findings()
    for path in sorted(set(changed_files)):
        if not path.startswith(ASSET_PREFIX):
            continue
        name = path[len(ASSET_PREFIX) :]
        if "/" in name:  # a nested asset dir is not part of the flat token surface
            continue
        new_token = token_for(new_html, name)
        if new_token is None:
            findings.unversioned.append(name)
            continue
        if token_for(old_html, name) == new_token:
            findings.stale.append(f"{name} (still ?v={new_token})")
        else:
            findings.bumped.append(name)
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
        old_html = _git("show", f"{args.base}:{INDEX_PATH}")
    except subprocess.CalledProcessError as exc:
        # Loud, and it names WHICH half failed: a shallow clone fails on the rev-parse
        # of HEAD^1, which is the fetch-depth mistake this check is most likely to hit.
        print(f"CACHE_BUST: ERROR — git failed ({exc.cmd}): {exc.stderr.strip()}", file=sys.stderr)
        return 2

    with open(INDEX_PATH, encoding="utf-8") as fh:
        new_html = fh.read()

    findings = check(changed, old_html, new_html)

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
        f"CACHE_BUST: OK — {len(findings.bumped)} bumped, "
        f"{len(findings.unversioned)} unversioned, 0 stale"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
