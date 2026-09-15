#!/usr/bin/env python
"""Guard: every ``measure`` block still says something true — and every count is PRINTED.

🔴 **The gap this closes (PLAN-0125 Step 2; ADR-0038 OQ-5).** ``tools/measure.py`` seals
a number together with the tree it was taken against (``against_sha``), the paths it read
(``declared_paths``) and the procedure that produced it. Until this guard nothing read
those fields: a block kept its ✔ after its paths moved, and a wrong value re-sealed by
hand passed every check that compares two statements. ADR-0038 ratified this guard as
*"owed work, not an option"* (``0038:758-764``).

**It supplies no oracle of its own (PLAN-0125 §3.1).** Every fact it acts on was declared
by the block. Every fact it checks against comes from git, or from re-running the block's
own procedure through ``tools.measure.run_procedure`` — the emitter's function, so no
second interpreter ever sees an argv.

**Per block, in order (§3.2)** — the first finding wins:

1. the seal recomputes and the fields have the ``measure/v1`` shape, else ``hash_bad``;
2. ``against_sha`` resolves to a commit, else ``unavailable`` in a shallow clone (a
   visible skip) or ``unresolvable`` in a full one (a broken pointer);
3. a path block's declared paths are unchanged since ``against_sha``, else ``stale``;
4. a ``rerun: true`` block's procedure still reduces to its recorded value, else
   ``mismatch`` — a number on unchanged paths that was never true.

Then every ``measure:<16hex>`` token in the live surfaces must name a parsed block
(``dangling``), and a live — not ``:historical`` — token on a stale block is
``stale_cited``. ``⚠️ asserted-not-verified`` is counted and never gated (§6 E6).

**Two readings beyond §3.2's letter, both typed by Cray in session 303:**

* **D1 = a — ``rerun_failed``.** Under the emitter's option-(a) policy a re-run that exits
  non-zero or writes any stderr raises ``ProcedureError``: neither a mismatch (no value
  came back) nor an unresolvable pointer. In a full repository it gates — a block the
  guard can no longer re-derive is a block it cannot defend. In a shallow clone it counts
  as ``unavailable``, because a depth-2 CI checkout cannot see the commits a history
  block names (measured s303: ``git log A..B`` exits 128 there, and 0 in the full
  worktree). A block whose argv the emitter's own R6/R7 would refuse is never executed;
  it is ``rerun_failed`` in any clone.
* **D2 = b — staleness also reads what is not yet committed.** ADR-0038's check is
  ``git diff --name-only <against_sha>..HEAD -- <paths>``, and it runs here verbatim. The
  re-run, though, reads the working tree. At pre-commit the commit being built is not in
  ``HEAD`` yet, so an edit to a declared path would pass the ADR's diff and then fail the
  re-run as a ``mismatch`` — the wrong diagnosis, on a block nobody may cite. The second
  diff, ``git diff --name-only HEAD -- <paths>``, closes that gap.

Exit: 1 on ``blocks == 0``, ``hash_bad``, ``unresolvable``, ``mismatch``, ``rerun_failed``,
``dangling``, or ``stale_cited`` (``GATE_STALE_CITED``, SD-7 = b); otherwise 0. The values
line comes first, the findings next, the verdict last (CLAUDE.md §8).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - `python tools/check_measure_staleness.py`
    # Both invocation forms work (the measure.py idiom): pre-commit runs the file by path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._evidence import EXIT_FAIL, EXIT_PASS, verdict_line
from tools.measure import (
    SCHEMA,
    ProcedureError,
    parse_blocks,
    rerun_refusal,
    run_procedure,
    shell_refusal,
    verify_hash,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The line prefix every run prints.
PREFIX = "MEASURE-STALENESS:"

#: ADR-0038 D3's ratified home — the only place a block is parsed from.
BLOCK_GLOB = "docs/logs/*.md"

#: The live surfaces whose ``measure:<16hex>`` tokens must resolve (not ``done/``).
CITATION_GLOBS = ("docs/plans/*.md", "docs/STATUS.md", "docs/adr/*.md")

#: Where the honest marker is counted — active PLANs only.
ASSERTED_GLOB = CITATION_GLOBS[0]

#: SD-7 = (b), Cray typed s299: a live citation of a stale block gates. A named constant so
#: the ruling is legible in the source, not so it can be quietly flipped.
GATE_STALE_CITED = True

GIT_TIMEOUT_S = 30

HASH_BAD = "hash_bad"
UNRESOLVABLE = "unresolvable"
UNAVAILABLE = "unavailable"
STALE = "stale"
MISMATCH = "mismatch"
RERUN_FAILED = "rerun_failed"
FRESH = "fresh"

_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_CITATION = re.compile(r"(?<![0-9A-Za-z_])measure:([0-9a-f]{16})(:historical)?(?![0-9A-Za-z_])")
_ASSERTED = re.compile("⚠️?\\s*\\**asserted-not-verified")

#: The namespace ``rerun_refusal`` reads, so the guard applies the emitter's R7 verbatim
#: instead of a second copy of the allowlist rule that could drift from the first.
_RERUN_ARGS = argparse.Namespace(rerun=True, file=None)


@dataclass
class Counts:
    """Every number the values line prints, in print order."""

    files: int = 0
    blocks: int = 0
    hash_bad: int = 0
    unresolvable: int = 0
    unavailable: int = 0
    stale: int = 0
    rerun: int = 0
    mismatch: int = 0
    rerun_failed: int = 0
    cites: int = 0
    dangling: int = 0
    stale_cited: int = 0
    historical: int = 0
    asserted: int = 0


@dataclass(frozen=True)
class Verdict:
    """One block's classification. ``rederived`` is True when a re-run returned a value."""

    state: str
    detail: str = ""
    rederived: bool = False


# --- git ---------------------------------------------------------------------------------


def _git(root: Path, *args: str) -> tuple[int, str]:
    """One git query at ``root``: ``(returncode, stdout)``. 127 when git cannot start.

    The environment is inherited, never scrubbed: under ``git commit -a`` pre-commit's
    hooks see a temporary ``GIT_INDEX_FILE`` (PLAN-0125 §9), and a minimal ``env`` would
    hide it.
    """
    try:
        proc = subprocess.run(  # noqa: S603 — a fixed git argv, never a shell
            ["git", *args],  # noqa: S607 — "git" via PATH, the house idiom
            cwd=root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, str(exc)
    return proc.returncode, proc.stdout


def _is_shallow(root: Path) -> bool:
    rc, out = _git(root, "rev-parse", "--is-shallow-repository")
    return rc == 0 and out.strip() == "true"


def _resolves(root: Path, sha: str) -> bool:
    rc, _ = _git(root, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
    return rc == 0


def moved_paths(root: Path, sha: str, paths: Sequence[str]) -> list[str] | None:
    """Declared paths that differ from ``sha`` — committed since, or not yet committed.

    ``None`` when either diff fails. The first diff is ADR-0038's own (``0038:582``); the
    second is D2 = b (see the module docstring).
    """
    committed_rc, committed = _git(root, "diff", "--name-only", "-z", f"{sha}..HEAD", "--", *paths)
    pending_rc, pending = _git(root, "diff", "--name-only", "-z", "HEAD", "--", *paths)
    if committed_rc != 0 or pending_rc != 0:
        return None
    return sorted({name for name in (committed + "\0" + pending).split("\0") if name})


# --- one block ---------------------------------------------------------------------------


def shape_problem(data: Mapping[str, Any]) -> str | None:
    """Why a sealed block cannot be read as ``measure/v1``, or ``None``.

    Counted with the bad seals: a block the guard cannot read is one it cannot defend,
    and skipping it would let the count stop describing the input (the ``tally.py`` rule).
    """
    paths = data.get("declared_paths")
    sha = data.get("against_sha")
    if data.get("schema") != SCHEMA:
        return f"schema={data.get('schema')!r}, expected {SCHEMA!r}"
    if not isinstance(sha, str) or not _FULL_SHA.fullmatch(sha):
        return f"against_sha={sha!r} is not a full 40-hex SHA"
    if not isinstance(data.get("history"), bool) or not isinstance(data.get("rerun"), bool):
        return "history and rerun must both be booleans"
    if not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
        return "declared_paths must be a list of path strings"
    if not data["history"] and not paths:
        return "a path block declares no paths — there is nothing to diff"
    if not isinstance(data.get("value"), str):
        return "value must be a string"
    return _procedure_problem(data.get("procedure"))


def _procedure_problem(procedure: object) -> str | None:
    if not isinstance(procedure, dict) or not isinstance(procedure.get("reduce"), str):
        return "procedure must be an object with a reduce"
    if ("file" in procedure) == ("argv" in procedure):
        return "procedure must name exactly one of file / argv"
    if "file" in procedure:
        return None if isinstance(procedure["file"], str) else "procedure.file must be a string"
    argv = procedure["argv"]
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        return "procedure.argv must be a non-empty list of strings"
    return None


def _rederive(root: Path, data: Mapping[str, Any], *, shallow_clone: bool) -> Verdict:
    """Step 4: re-run the block's own procedure and compare it with the recorded value."""
    procedure = data["procedure"]
    if "argv" in procedure:
        argv = [str(element) for element in procedure["argv"]]
        refusal = shell_refusal(argv) or rerun_refusal(_RERUN_ARGS, argv)
        if refusal is not None:
            return Verdict(
                RERUN_FAILED,
                f"not re-executed — the emitter's own {refusal.rule} refuses it: "
                f"{refusal.reason}",
            )
    try:
        got = run_procedure(procedure, root)
    except (ProcedureError, re.error) as exc:
        if shallow_clone:
            return Verdict(UNAVAILABLE, f"re-run cannot see its commits in a shallow clone: {exc}")
        return Verdict(RERUN_FAILED, f"re-run failed: {exc}")
    if got != data["value"]:
        return Verdict(
            MISMATCH, f"recorded value={data['value']!r}, re-derived={got!r}", rederived=True
        )
    return Verdict(FRESH, rederived=True)


def classify(root: Path, data: Mapping[str, Any] | None, *, shallow: bool, rerun: bool) -> Verdict:
    """One block through §3.2's steps 2 to 5. The first finding wins."""
    if data is None:
        return Verdict(HASH_BAD, "the marker has no ```json fence holding a JSON object")
    if not verify_hash(data):
        return Verdict(HASH_BAD, f"the seal {data.get('hash')!r} does not recompute")
    problem = shape_problem(data)
    if problem is not None:
        return Verdict(HASH_BAD, problem)
    sha = str(data["against_sha"])
    if not _resolves(root, sha):
        if shallow:
            return Verdict(UNAVAILABLE, f"against_sha {sha} is not in this shallow clone")
        return Verdict(UNRESOLVABLE, f"against_sha {sha} does not resolve to a commit")
    if not data["history"]:
        moved = moved_paths(root, sha, data["declared_paths"])
        if moved is None:
            return Verdict(UNRESOLVABLE, f"git diff against {sha} failed")
        if moved:
            return Verdict(STALE, f"declared path(s) {moved} differ from {sha[:12]}")
    if not data["rerun"] or not rerun:
        return Verdict(FRESH)
    return _rederive(root, data, shallow_clone=shallow)


# --- the surface -------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _where(root: Path, path: Path, text: str, offset: int) -> str:
    return f"{path.relative_to(root).as_posix()}:{text.count(chr(10), 0, offset) + 1}"


def run(root: Path, *, rerun: bool) -> tuple[Counts, list[str]]:
    """Walk the blocks, then the citations, then the honest marker. Nothing is gated here."""
    counts = Counts()
    findings: list[str] = []
    states = _walk_blocks(root, counts, findings, rerun=rerun)
    _walk_citations(root, counts, findings, states)
    for path in sorted(root.glob(ASSERTED_GLOB)):
        counts.asserted += len(_ASSERTED.findall(_read(path)))
    return counts, findings


def _walk_blocks(root: Path, counts: Counts, findings: list[str], *, rerun: bool) -> dict[str, str]:
    """Classify every block; return each readable block's state keyed by its 16-hex hash."""
    shallow = _is_shallow(root)
    states: dict[str, str] = {}
    for path in sorted(root.glob(BLOCK_GLOB)):
        parsed = parse_blocks(_read(path))
        counts.files += 1 if parsed else 0
        for block in parsed:
            counts.blocks += 1
            verdict = classify(root, block.data, shallow=shallow, rerun=rerun)
            if verdict.state != FRESH:
                setattr(counts, verdict.state, getattr(counts, verdict.state) + 1)
            if verdict.rederived:
                counts.rerun += 1
            if verdict.state != HASH_BAD and block.data is not None:
                states[str(block.data["hash"]).removeprefix("sha256:")] = verdict.state
            if verdict.detail:
                where = f"{path.relative_to(root).as_posix()}:{block.line}"
                findings.append(f"{PREFIX} {verdict.state} {where} — {verdict.detail}")
    return states


def _walk_citations(
    root: Path, counts: Counts, findings: list[str], states: Mapping[str, str]
) -> None:
    """Resolve every ``measure:<16hex>`` token in the live surfaces against ``states``."""
    for pattern in CITATION_GLOBS:
        for path in sorted(root.glob(pattern)):
            text = _read(path)
            for match in _CITATION.finditer(text):
                counts.cites += 1
                if match.group(2) is not None:
                    counts.historical += 1
                state = states.get(match.group(1))
                where = _where(root, path, text, match.start())
                if state is None:
                    counts.dangling += 1
                    findings.append(f"{PREFIX} dangling {where} — no block is sealed {match[0]}")
                elif match.group(2) is None and state == STALE:
                    counts.stale_cited += 1
                    findings.append(
                        f"{PREFIX} stale_cited {where} — {match[0]} names a stale block"
                    )


def gating(counts: Counts) -> list[str]:
    """The counters that fail the commit, as ``name=value`` — empty means exit 0."""
    gates: list[str] = []
    if not counts.blocks:
        gates.append("blocks=0")
    if counts.hash_bad:
        gates.append(f"hash_bad={counts.hash_bad}")
    if counts.unresolvable:
        gates.append(f"unresolvable={counts.unresolvable}")
    if counts.mismatch:
        gates.append(f"mismatch={counts.mismatch}")
    if counts.rerun_failed:
        gates.append(f"rerun_failed={counts.rerun_failed}")
    if counts.dangling:
        gates.append(f"dangling={counts.dangling}")
    if GATE_STALE_CITED and counts.stale_cited:
        gates.append(f"stale_cited={counts.stale_cited}")
    return gates


def values_line(counts: Counts, elapsed_ms: int) -> str:
    body = " ".join(f"{field.name}={getattr(counts, field.name)}" for field in fields(counts))
    return f"{PREFIX} {body} elapsed_ms={elapsed_ms}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_measure_staleness",
        description="Re-derive every measure block under docs/logs/ and resolve its citations.",
    )
    parser.add_argument(
        "root", nargs="?", type=Path, default=REPO_ROOT, help="repository root (default: this one)"
    )
    parser.add_argument(
        "--no-rerun",
        action="store_true",
        help="skip re-derivation — PLAN-0125 AC-11's timing control, never a pass",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    started = time.monotonic()  # a duration, so never the wall clock (WSL2 steps it back)
    counts, findings = run(args.root.resolve(), rerun=not args.no_rerun)
    elapsed_ms = round((time.monotonic() - started) * 1000)
    print(values_line(counts, elapsed_ms))
    for finding in findings:
        print(finding)
    if counts.blocks == 0:
        print(f"{PREFIX} blocks=0 — EMPTY SURFACE, NOT a pass")
    if counts.unavailable:
        print(
            f"{PREFIX} unavailable={counts.unavailable} — those blocks were NOT checked in "
            "this shallow clone, NOT a pass"
        )
    if args.no_rerun:
        print(f"{PREFIX} --no-rerun — re-derivation SKIPPED, a timing control, NOT a pass")
    gates = gating(counts)
    status = EXIT_FAIL if gates else EXIT_PASS
    if gates:
        print(f"{PREFIX} gated on {' '.join(gates)} — exit {status}")
    print(verdict_line(status))
    return status


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
