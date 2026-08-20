#!/usr/bin/env python3
"""Pre-commit guard: a claim declared RETIRED must not survive anywhere live.

The failure this exists to close is **propagation**, not recording. Measured at
session 241 on ``.claude/skills/ms-s1-ollama/``:

* ``SKILL.md`` corrected the claim *"``ms-s1-max`` has no WSL DNS entry"* at
  session 171 — measured, it resolves fine. ``warm.sh:11`` kept asserting it for
  **two more months**, and an operator following the script followed the stale
  copy. It had a real cost: ``services/api/config.py`` defaults ``ollama_host``
  to that hostname, so *"does not resolve"* made a live default read as
  inert-by-default, and a test that reached it ran ``gpt-oss:20b`` twice with no
  ``CLAUDE.md`` §8 go.
* The same file corrected its host-state gate pointer at session 174 and left
  the **footer of the same file** pointing at the old home — 165 lines apart, so
  the file named two different homes for one binding rule.

Both were found by a human reading the file, two months and three sessions late.
Nothing could have found them mechanically, because a correction records *the
new answer* and the repo keeps no account of *the retired one*.

**The convention this enforces** (``docs/conventions/retired-claims.md``): a
correction declares what it killed, on its own line, in any comment syntax::

    <!-- retired: "ms-s1-max has no WSL DNS entry" -->
    # retired: "ms-s1-max has no WSL DNS entry"

The guard then fails if that text appears **anywhere live** except beside a
marker declaring it.

Deliberate scope limits, each of which is a floor rather than a ceiling:

* **Archives are not searched.** ``docs/status-archive/`` and
  ``docs/plans/done/`` preserve superseded text *on purpose*; flagging them
  would make every rotation a violation. A marker declared inside an archive is
  likewise ignored — frozen history declares nothing.
* **Exact text only.** A stale copy reworded, or differently emphasised
  (``*no WSL DNS entry*`` vs ``no WSL DNS entry``), is not caught. Retire the
  plainest wording that a copy would repeat verbatim.
* **A near-marker window is exempt** (``_EXEMPT_WINDOW`` lines either side), because
  the correction narrative almost always quotes the claim it is retiring. The
  window is small on purpose: the session-241 footer case sat 165 lines from its
  correction in the same file and must still be caught.
* **Short strings are refused, not ignored** — a marker under
  ``_MIN_RETIRED_LEN`` characters fails the guard rather than silently matching
  half the repo.

Exit codes: 0 = clean; 1 = a retired claim survives, or a marker is unusable.

``RETIRED_CLAIMS_ROOT`` overrides the scanned repo root for tests (mirrors the
``STATUS_CITATION_ROOT`` / ``STATUS_SIZE_PATH`` / ``ALEMBIC_GUARD_ROOT`` family).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

#: Marker syntax, comment-agnostic: any line declaring ``retired: "<text>"``.
#: Works unchanged in Markdown (``<!-- ... -->``), Python and shell (``# ...``).
_MARKER_RE = re.compile(r'retired:\s*"([^"]+)"')

#: Lines either side of a marker where the retired text may legitimately appear
#: — the correction narrative quotes what it is retiring. Small on purpose.
_EXEMPT_WINDOW = 10

#: Below this length a retired claim is too generic to search for safely.
_MIN_RETIRED_LEN = 20

#: Directories that preserve superseded text by design. Neither searched for
#: survivors nor read for markers.
_ARCHIVE_PREFIXES = (
    "docs/status-archive/",
    "docs/plans/done/",
)

#: Only text-bearing files can carry or repeat a prose claim.
_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".js", ".toml", ".txt"}

#: This guard's own machinery. These files *document* the marker syntax, so their
#: examples are illustrations, not declarations — collecting them would retire a
#: sample claim repo-wide. They are still SEARCHED, so a real stale copy hiding in
#: them is caught like anywhere else; only their marker-declaring power is removed.
_OWN_MACHINERY = frozenset(
    {
        "tools/check_retired_claims.py",
        "tests/tools/test_check_retired_claims.py",
        "docs/conventions/retired-claims.md",
    }
)


@dataclass(frozen=True)
class Marker:
    """One ``retired:`` declaration, with where it was declared.

    ``local_only`` marks an *illustration* rather than a declaration: a marker
    inside :data:`_OWN_MACHINERY`. It exempts its own neighbourhood — so a doc
    may show the syntax, and quote the claim it is documenting, without being
    reported — but it retires nothing for any other file. Found the hard way:
    the guard blocked its own first commit because the convention doc could not
    declare and therefore could not exempt its own worked example either.
    """

    text: str
    path: str
    line: int
    local_only: bool = False


@dataclass(frozen=True)
class Survivor:
    """A retired claim found alive outside any declaring marker's window."""

    text: str
    path: str
    line: int
    declared_at: str


def is_scannable(rel: str) -> bool:
    """Is this path in scope at all — for markers and for survivors alike?

    Kept a pure function of the path so the scope invariant is testable without
    a git repo, and so the two collectors below cannot drift from the
    enumeration in :func:`_tracked_files`.
    """
    return Path(rel).suffix in _SUFFIXES and not rel.startswith(_ARCHIVE_PREFIXES)


def _tracked_files(root: Path) -> list[str]:
    """Every tracked text file, archives excluded.

    ``git ls-files`` is the scope for the same reason R7 uses it: it is the
    literal reading of "tracked artifact", and it keeps gitignored working notes
    (``.claude/handoffs/``) out by construction rather than by an exclude list.
    """
    try:
        # S603: fixed argv, no shell — nothing is interpolated into the command;
        # `root` is a cwd, not an argument. S607: "git" via PATH (the same idiom
        # as tools/check_status_citations.py).
        proc = subprocess.run(  # noqa: S603
            ["git", "ls-files"],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:  # git not on PATH
        raise RuntimeError("git executable not found on PATH") from exc
    out = proc.stdout.splitlines()
    return [p for p in out if is_scannable(p)]


def _read(root: Path, rel: str) -> list[str]:
    try:
        return (root / rel).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def collect_markers(root: Path, files: list[str]) -> tuple[list[Marker], list[str]]:
    """Return every ``retired:`` marker, plus complaints about unusable ones."""
    markers: list[Marker] = []
    problems: list[str] = []
    for rel in files:
        if not is_scannable(rel):
            continue
        local_only = rel in _OWN_MACHINERY
        for i, line in enumerate(_read(root, rel), start=1):
            m = _MARKER_RE.search(line)
            if not m:
                continue
            text = m.group(1).strip()
            # An illustration is never searched, so its length cannot cause a
            # sweeping match — holding it to the minimum would only forbid the
            # short placeholders (`<text>`, `{claim}`) that make the docs legible.
            if len(text) < _MIN_RETIRED_LEN and not local_only:
                problems.append(
                    f"{rel}:{i}: retired claim {text!r} is {len(text)} chars; "
                    f"minimum is {_MIN_RETIRED_LEN}. Too short to search for "
                    f"without matching unrelated prose — retire a longer, "
                    f"distinctive phrasing."
                )
                continue
            markers.append(Marker(text=text, path=rel, line=i, local_only=local_only))
    return markers, problems


def find_survivors(root: Path, files: list[str], markers: list[Marker]) -> list[Survivor]:
    """Every live occurrence of a retired claim outside a declaring window."""
    # Only a real declaration puts a claim under search. An illustration
    # (`local_only`) still builds an exempt window below, but retires nothing.
    by_text: dict[str, list[Marker]] = {}
    for mk in markers:
        if mk.local_only:
            continue
        by_text.setdefault(mk.text, []).append(mk)

    windows: dict[str, list[Marker]] = {}
    for mk in markers:
        windows.setdefault(mk.text, []).append(mk)

    survivors: list[Survivor] = []
    for rel in files:
        if not is_scannable(rel):
            continue
        lines = _read(root, rel)
        for text, decls in by_text.items():
            exempt = {
                ln
                for d in windows.get(text, ())
                if d.path == rel
                for ln in range(d.line - _EXEMPT_WINDOW, d.line + _EXEMPT_WINDOW + 1)
            }
            for i, line in enumerate(lines, start=1):
                if i in exempt or text not in line:
                    continue
                # The marker line itself is a declaration, never a survivor.
                if _MARKER_RE.search(line):
                    continue
                survivors.append(
                    Survivor(
                        text=text,
                        path=rel,
                        line=i,
                        declared_at=f"{decls[0].path}:{decls[0].line}",
                    )
                )
    return survivors


def main() -> int:
    root = Path(os.environ.get("RETIRED_CLAIMS_ROOT") or ".").resolve()
    files = _tracked_files(root)
    markers, problems = collect_markers(root, files)
    survivors = find_survivors(root, files, markers)

    for p in problems:
        print(f"UNUSABLE MARKER: {p}", file=sys.stderr)

    for s in survivors:
        print(
            f"RETIRED CLAIM STILL LIVE: {s.path}:{s.line}\n"
            f"    claim:        {s.text!r}\n"
            f"    retired at:   {s.declared_at}\n"
            f"    fix:          update this occurrence to the corrected wording, "
            f"or delete it. A correction that is not propagated reads as settled "
            f"while the stale copy stays the one an operator follows.",
            file=sys.stderr,
        )

    if problems or survivors:
        print(
            f"\ncheck_retired_claims: {len(survivors)} surviving claim(s), "
            f"{len(problems)} unusable marker(s) "
            f"across {len(files)} tracked files ({len(markers)} marker(s) read).",
            file=sys.stderr,
        )
        return 1

    print(
        f"check_retired_claims: clean — {len(markers)} retired claim(s) "
        f"stayed dead across {len(files)} tracked files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
