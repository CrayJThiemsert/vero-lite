#!/usr/bin/env python
"""Emit a sealed ``measure`` block — a number a TOOL took, in a shape a model cannot forge.

🔴 **The gap this closes (PLAN-0125; ADR-0038 D3 and OQ-5).** Every shipped guard checks
that two statements agree or that a reference resolves; none re-derives a fact after it
is written — ``tools/check_ac_consistency.py`` says so in its own docstring: *"a wrong
fact stated consistently passes."* The two writers that put the most SHAs, counts and
byte sizes into tracked files (``status-scribe``, ``plan-drafter``) have no shell, so
every such number they write was transcribed from prose. A ``measure`` block makes the
number travel with the procedure that produced it, the tree it was taken against, a
predicate fixed before it was taken, a control that could have failed, and a seal.

**What the seal is, and is not.** ``hash`` is ``sha256:`` plus the first 16 hex of
SHA-256 over the canonical JSON of every other field. A model cannot compute it and a
hand edit breaks it — those are the two actors it defends against. It is not a
signature: anyone with a shell can re-seal (PLAN-0125 §2.2).

**One invocation, one block, no shell ever.** The procedure is an argv list or a file
reduction. Every process this module starts goes through :func:`_spawn`, its one
process call site (AC-3 reads that site by symbol). The one exception to *one block* is
``--recipe`` (PLAN-0125 §4.2), which runs a fixed set of invocations back through the
same entry point — so every refusal below applies to each of them, unchanged and
unexempted.

**Refusals** — exit 2, no block, the reason printed (PLAN-0125 §2.3):

* ``R1`` nothing declared — neither ``--paths`` nor ``--history``, both, or a ``--file``
  outside ``--paths`` (the guard would diff the wrong paths)
* ``R2`` a declared path is not tracked, or differs from HEAD
* ``R3`` no predicate, or one outside the grammar — parsed by hand, never ``eval``
* ``R4`` no control, or a control that reads the same value as the measurement
* ``R5`` ``--history`` whose endpoints are not immutable SHAs
* ``R6`` a shell anywhere in an argv, or a pasted one-element command line
* ``R7`` ``--rerun`` outside the read-only allowlist
* ``R8`` the tree cannot be resolved to a full HEAD SHA

plus two mechanical ones: ``usage`` (the command line does not parse) and ``procedure``
(the procedure produced nothing that may be reduced into a value).

**Order.** Checks that need no git run first, in R-number order. Then ``R8`` asks
whether git can answer at all, and only then the two that need its answer (``R2``, and
``R5``'s endpoint half). ``R8`` sits ahead of them on purpose: outside a repository
``R2`` would otherwise fire and blame the path for what is really a missing tree — a
refusal whose reason names the wrong cause (Lesson #0043). ``R4``'s second half can
only be known once the procedure and its control have both run.

⚠️ **Residual, stated (s299 note in the #1487 PR body).** ``R6`` scans every argv
element's basename, so a literal argument that happens to be a shell's name —
``git grep -e bash`` — is refused. The shell is the hazard; that false refusal is the
price of a rule a wrapper (``env bash -c …``) cannot walk around.

**Printed, every run** (CLAUDE.md §8 — values, never a bare verdict): the ``MEASURE:``
values line first, then the block (stdout, or appended to ``--out``), then ``VERDICT:``
last, rendered from the same status ``main`` returns. ``when`` is wall-clock UTC and is
provenance only — WSL2's clock steps backwards, so nothing orders blocks by it.

Usage::

    python tools/measure.py --metric status_head_drift --units commits \\
        --history --rerun --predicate "value == 3" --who code-s302 \\
        --control-argv "git log --format=%h 793b9d9..793b9d9" --control-reduce lines \\
        --reduce lines -- git log --no-merges --format=%h 793b9d9..f65f7ea

    python tools/measure.py --metric template_measure_tokens --units occurrences \\
        --paths docs/plans/0000-template.md --file docs/plans/0000-template.md \\
        --reduce count:measure --predicate "value == 0" --who code-s302 \\
        --control-file docs/plans/0000-template.md --control-reduce count:Goal \\
        --out docs/logs/2026-09-15-plan0125-fact-pack-measures.md

    python tools/measure.py --recipe status-reconcile --who code-s304
"""

from __future__ import annotations

import argparse
import hashlib
import json
import operator
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

if __package__ in (None, ""):  # pragma: no cover - `python tools/measure.py`, not `-m`
    # Both invocation forms have to work (the absent.py / tally.py idiom): a block's
    # procedure is re-run by hand as often as by a tool.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._evidence import EXIT_FAIL, EXIT_PASS, EXIT_REFUSED, verdict_line

SCHEMA = "measure/v1"
MARKER = "<!-- measure:v1 -->"

#: R6's shell set, compared against every argv element's basename (lower-cased, ``.exe``
#: stripped). A module constant so widening it is one edit.
SHELL_BASENAMES = frozenset(
    {"sh", "bash", "dash", "zsh", "ksh", "fish", "cmd", "powershell", "pwsh"}
)

#: R7: the git subcommands a ``rerun: true`` block may name. Read-only, deterministic and
#: host-state-free, so a guard can afford to re-execute them at pre-commit.
RERUN_ALLOWLIST = frozenset({"log", "rev-parse", "rev-list", "diff", "ls-files", "show"})

#: ``--recipe`` names a fixed set of invocations instead of one hand-written procedure, so
#: the two facts ``status-scribe`` transcribes arrive as blocks it cannot type (PLAN-0125 §4.2).
RECIPES = frozenset({"status-reconcile"})

#: The ref ``status-reconcile`` measures. The recipe resolves it to an immutable SHA before
#: it measures anything — :func:`_recipe_invocations` records why that is not optional.
RECIPE_REF = "main"

PROCEDURE_TIMEOUT_S = 30

_TEXT_REDUCERS = frozenset({"raw", "lines", "first", "int"})
_HEX_REV = re.compile(r"[0-9a-f]{7,40}")
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_INT = re.compile(r"-?\d+")
_GIT_VALUE_OPTIONS = frozenset({"-c", "-C", "--git-dir", "--work-tree", "--namespace"})
_COMPARE = re.compile(r'\s*value\s*(==|!=|<=|>=|<|>)\s*(-?\d+|"[^"\\]*")\s*')
_RANGE = re.compile(r"\s*(-?\d+)\s*<=\s*value\s*<=\s*(-?\d+)\s*")
_OPS: dict[str, Callable[[int, int], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}
_MARKER_LINE = re.compile(r"^" + re.escape(MARKER) + r"[ \t]*$", re.M)
_FENCE = re.compile(r"\n```json\n(.*?)\n```", re.S)


@dataclass(frozen=True)
class Refusal:
    """Why no block was emitted.

    ``rule`` is ``R1``…``R8``, or one of the mechanical ``usage`` / ``procedure`` / ``recipe``.
    """

    rule: str
    reason: str


class ProcedureError(Exception):
    """A procedure, or its control, produced nothing the emitter may reduce into a value."""


class _UsageError(Exception):
    """argparse's complaint, raised instead of printed so it becomes a ``usage`` refusal."""


@dataclass(frozen=True)
class Spawned:
    """A finished process: exit status, raw stdout, decoded stderr."""

    returncode: int
    stdout: bytes
    stderr: str


@dataclass(frozen=True)
class Tree:
    """The repository root and the full HEAD SHA every block is sealed against."""

    root: Path
    sha: str


@dataclass(frozen=True)
class ParsedBlock:
    """One marker found in a text. ``data`` is ``None`` when its fence did not parse."""

    line: int
    data: dict[str, Any] | None


@dataclass(frozen=True)
class Predicate:
    """``value <op> <int|"string">``, or ``<int> <= value <= <int>`` (``op == "range"``)."""

    op: str
    operand: int | str
    upper: int = 0

    def holds(self, value: str) -> bool:
        if isinstance(self.operand, str):
            return (value == self.operand) is (self.op == "==")
        if not _INT.fullmatch(value):
            return False
        number = int(value)
        if self.op == "range":
            return self.operand <= number <= self.upper
        return _OPS[self.op](number, self.operand)


# --- processes ---------------------------------------------------------------------------


def _spawn(argv: Sequence[str], cwd: Path) -> Spawned:
    """Start one process and wait for it — the ONLY process call site in this module.

    Kept singular so AC-3 can read it by symbol: an argv list, no shell, a timeout. A
    second call site would be a second place for a shell to creep back in.
    """
    try:
        proc = subprocess.run(  # noqa: S603 — an argv list, never a shell (R6)
            list(argv),
            cwd=cwd,
            capture_output=True,
            timeout=PROCEDURE_TIMEOUT_S,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProcedureError(f"{argv[0]!r} could not run: {exc}") from exc
    return Spawned(proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace"))


def _git(cwd: Path, *args: str) -> Spawned:
    return _spawn(["git", *args], cwd)


def procedure_output(argv: Sequence[str], spawned: Spawned) -> bytes:
    """What a finished procedure contributes to the value — or a refusal.

    Returns the bytes the reducer will consume. Raises :class:`ProcedureError` with a
    one-line reason to refuse: exit 2, no block, the reason printed after
    ``MEASURE: REFUSED procedure —``.

    This is the Lesson #0007 seam. A failed ``git log <bad-ref>`` exits 128 and writes
    one line to stderr; if that line reaches a ``lines`` reducer the emitter seals a
    confident ``value=1`` that nobody measured. ``spawned.stderr`` is already decoded;
    ``spawned.stdout`` is raw bytes (the ``bytes`` reducer counts them as-is).

    **Policy (Cray, typed, s302 — option a): refuse on a non-zero exit OR any stderr;
    reduce stdout alone.** PLAN-0125 Step 1.1 wrote "merged as ``stdout + stderr``"; a
    merge would count a success-path warning (git's ``refname is ambiguous``) as one more
    line — the fake value the merge was meant to prevent. Reading stdout alone while
    refusing on stderr keeps #0007's intent both ways: stderr is never counted, and never
    lost, because its first line becomes the refusal's reason. Cost, accepted: a procedure
    that succeeds but warns is refused, and one whose non-zero exit carries meaning
    (``git diff --quiet``) cannot be measured by its exit code.
    """
    stderr = spawned.stderr.strip()
    if spawned.returncode != 0 or stderr:
        first = stderr.splitlines()[0] if stderr else "(no stderr)"
        raise ProcedureError(
            f"{argv[0]!r} exited {spawned.returncode} with stderr {first!r} — "
            "a failed or warning run is not a measurement"
        )
    return spawned.stdout


def _read_repo_file(root: Path, rel: str) -> bytes:
    target = (root / rel).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ProcedureError(f"{rel!r} resolves outside the repository")
    try:
        return target.read_bytes()
    except OSError as exc:
        raise ProcedureError(f"cannot read {rel!r}: {exc}") from exc


def run_procedure(proc: Mapping[str, Any], root: Path) -> str:
    """Execute one declared procedure at ``root`` and reduce it to the value string.

    Public because the staleness guard (PLAN-0125 Step 2) re-runs a block's procedure
    through this same function — so no second interpreter ever sees the argv.
    """
    if "file" in proc:
        data = _read_repo_file(root, str(proc["file"]))
    else:
        argv = [str(element) for element in proc["argv"]]
        data = procedure_output(argv, _spawn(argv, root))
    return reduce_output(str(proc["reduce"]), data)


# --- reducers and the predicate ----------------------------------------------------------


def reduce_output(reducer: str, data: bytes) -> str:
    """The pipes a shell would need, as named reducers whose UNIT is part of the name.

    ``count:<regex>`` counts occurrences, not matching lines — the G16 lines-vs-occurrences
    slip (PLAN-0125 §1) cannot recur silently when the unit is spelled in the reducer.
    """
    if reducer == "bytes":
        return str(len(data))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProcedureError(f"reducer {reducer!r} needs UTF-8 text: {exc}") from exc
    if reducer.startswith("count:"):
        pattern = reducer[len("count:") :]
        return str(len(re.findall(pattern, text)))
    if reducer == "lines":
        return str(sum(1 for line in text.splitlines() if line.strip()))
    if reducer == "first":
        lines = text.splitlines()
        return lines[0].rstrip() if lines else ""
    if reducer == "int":
        stripped = text.strip()
        if not _INT.fullmatch(stripped):
            raise ProcedureError(f"reducer 'int' needs exactly one integer, got {stripped[:60]!r}")
        return str(int(stripped))
    return text.strip()  # "raw" — every other spec was refused as `usage` before any run


def _reducer_problem(spec: str) -> str | None:
    if spec == "bytes" or spec in _TEXT_REDUCERS:
        return None
    if not spec.startswith("count:"):
        return f"unknown reducer {spec!r} (raw | lines | bytes | first | int | count:<regex>)"
    try:
        pattern = re.compile(spec[len("count:") :])
    except re.error as exc:
        return f"reducer {spec!r} is not a valid regex: {exc}"
    if pattern.search("") is not None:
        return f"reducer {spec!r} matches the empty string — it would count gaps, not needles"
    return None


def parse_predicate(text: str) -> Predicate | None:
    """The predicate grammar, parsed by hand. ``None`` means outside it (R3).

    Never ``eval``: ``value == 9 or True`` and ``__import__('os')`` are strings a model
    can type, and an evaluator would accept both as predicates that "pass".
    """
    ranged = _RANGE.fullmatch(text)
    if ranged is not None:
        return Predicate("range", int(ranged.group(1)), int(ranged.group(2)))
    compared = _COMPARE.fullmatch(text)
    if compared is None:
        return None
    op, literal = compared.groups()
    if literal.startswith('"'):
        return Predicate(op, literal[1:-1]) if op in ("==", "!=") else None
    return Predicate(op, int(literal))


# --- git argv shape ----------------------------------------------------------------------


def _basename(element: str) -> str:
    return re.split(r"[\\/]", element)[-1].lower().removesuffix(".exe")


def _split_git(argv: Sequence[str]) -> tuple[str | None, list[str]]:
    """``(subcommand, the tokens after it)`` for a git argv, global options skipped."""
    rest = list(argv[1:])
    while rest and rest[0].startswith("-"):
        if rest.pop(0) in _GIT_VALUE_OPTIONS and rest:
            rest.pop(0)
    if not rest:
        return None, []
    return rest[0], rest[1:]


def revision_candidates(argv: Sequence[str]) -> list[str]:
    """Every revision a git argv names: positionals after the subcommand, before ``--``.

    ``A..B`` and ``A...B`` contribute both ends (an open end is an empty string, which is
    git's implicit ``HEAD``); ``<rev>:<path>`` contributes the rev. An option's value must
    be attached (``--grep=x``, ``--max-count=10``): a detached value reads as a revision
    and is refused, which is the safe side of that ambiguity.
    """
    _, parts = _split_git(argv)
    candidates: list[str] = []
    for part in parts:
        if part == "--":
            break
        if part.startswith("-"):
            continue
        if ".." in part:
            candidates.extend(re.split(r"\.{2,3}", part))
        else:
            candidates.append(part.split(":", 1)[0])
    return candidates


# --- refusals ----------------------------------------------------------------------------


def declaration_refusal(args: argparse.Namespace) -> Refusal | None:
    """R1 — a block with nothing declared is one the guard cannot defend (0038:580-582)."""
    if args.history and args.paths is not None:
        return Refusal("R1", "declare --paths OR --history, not both")
    if not args.history and not args.paths:
        return Refusal("R1", "nothing declared: give --paths <tracked files> or --history")
    if args.file is not None and not args.history and args.file not in args.paths:
        return Refusal(
            "R1",
            f"--file {args.file} is not among --paths — the guard would diff " "the wrong paths",
        )
    return None


def predicate_refusal(args: argparse.Namespace) -> Refusal | None:
    """R3 — the predicate must exist before the number does (PLAN-0108:89)."""
    if args.predicate is None:
        return Refusal(
            "R3",
            "no --predicate: a predicate written after the number is a "
            "confirmation, not a check",
        )
    if parse_predicate(args.predicate) is None:
        return Refusal(
            "R3",
            f"--predicate {args.predicate!r} is outside the grammar: "
            'value <op> <int|"string"> or <int> <= value <= <int>',
        )
    return None


def control_refusal(args: argparse.Namespace) -> Refusal | None:
    """R4, first half — a measurement with no control cannot show it could have failed."""
    if args.control_file is None and args.control_argv is None:
        return Refusal("R4", "no control: give --control-file or --control-argv")
    return None


def history_shape_refusal(args: argparse.Namespace, argv: Sequence[str]) -> Refusal | None:
    """R5, the half that needs no git: a history block names commits, and only SHAs stay put."""
    if not args.history:
        return None
    if args.file is not None or not argv or _basename(argv[0]) != "git":
        return Refusal(
            "R5",
            "--history measures commits and needs a git argv — a file "
            "reduction reads the working tree, which no SHA pins",
        )
    candidates = revision_candidates(argv)
    bad = [c for c in candidates if not _HEX_REV.fullmatch(c)]
    if bad:
        return Refusal(
            "R5",
            f"history endpoint(s) {bad} are not immutable SHAs — a ref "
            "(HEAD, main, origin/…, ~, ^) or an open range moves",
        )
    if not candidates:
        return Refusal("R5", "no endpoint named — git defaults to HEAD, which moves")
    return None


def shell_refusal(argv: Sequence[str]) -> Refusal | None:
    """R6 — the emitter is the instrument; an instrument that runs a shell inherits its lies."""
    for element in argv:
        if _basename(element) in SHELL_BASENAMES:
            return Refusal("R6", f"argv element {element!r} is a shell ({sorted(SHELL_BASENAMES)})")
    if len(argv) == 1 and any(ch.isspace() for ch in argv[0]):
        return Refusal(
            "R6",
            f"one argv element holding whitespace ({argv[0]!r}) is a pasted "
            "command line — only a shell could run it",
        )
    return None


def rerun_refusal(args: argparse.Namespace, argv: Sequence[str]) -> Refusal | None:
    """R7 — a guard re-executes a ``rerun`` procedure at pre-commit: it must be cheap and inert."""
    if not args.rerun or args.file is not None:
        return None
    subcommand, parts = _split_git(argv)
    if not argv or _basename(argv[0]) != "git" or subcommand not in RERUN_ALLOWLIST:
        return Refusal(
            "R7",
            f"--rerun allows a file reduction or git {sorted(RERUN_ALLOWLIST)}; "
            f"got {list(argv)[:3]!r}",
        )
    if any(part.startswith("--output") for part in parts):
        return Refusal("R7", "--output writes a file; a re-runnable procedure must be read-only")
    return None


def resolve_tree(cwd: Path) -> Tree | Refusal:
    """R8 — the full HEAD SHA, from the emitter's OWN git call.

    Deliberately not ``tools/_evidence.head_sha()``: that falls back to ``"unknown"`` so an
    evidence stamp never loses a reading, which is right there and wrong here. A block
    carrying ``"unknown"`` is a well-formed pointer to nothing, and nothing downstream
    would report it as anything but a SHA. Git's own stderr becomes the reason.
    """
    try:
        top = _git(cwd, "rev-parse", "--show-toplevel")
        head = _git(cwd, "rev-parse", "HEAD")
    except ProcedureError as exc:
        return Refusal("R8", f"git cannot answer: {exc}")
    sha = head.stdout.decode("utf-8", "replace").strip()
    if top.returncode != 0 or head.returncode != 0 or not _FULL_SHA.fullmatch(sha):
        detail = (top.stderr or head.stderr).strip() or f"HEAD read {sha!r}"
        return Refusal("R8", f"against_sha cannot be resolved — {detail}")
    return Tree(Path(top.stdout.decode("utf-8").strip()), sha)


def path_refusal(tree: Tree, paths: Sequence[str]) -> Refusal | None:
    """R2 — an against-SHA cannot describe a file git does not see, or one that differs from it."""
    for path in paths:
        tracked = _git(tree.root, "ls-files", "--error-unmatch", "--", path)
        if tracked.returncode != 0:
            return Refusal(
                "R2",
                f"{path!r} is not tracked by git — no against-SHA describes it "
                "(a gitignored surface stays [evidence])",
            )
        dirty = _git(tree.root, "status", "--porcelain", "--", path)
        if dirty.stdout.strip():
            return Refusal(
                "R2",
                f"{path!r} differs from HEAD "
                f"({dirty.stdout.decode('utf-8', 'replace').strip()!r}) — commit it first",
            )
    return None


def endpoint_refusal(tree: Tree, args: argparse.Namespace, argv: Sequence[str]) -> Refusal | None:
    """R5, the half that asks git: every endpoint must resolve to a commit in this tree."""
    if not args.history:
        return None
    for candidate in revision_candidates(argv):
        check = _git(tree.root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if check.returncode != 0:
            return Refusal("R5", f"history endpoint {candidate!r} does not resolve to a commit")
    return None


def _first_refusal(checks: Iterable[Callable[[], Refusal | None]]) -> Refusal | None:
    for check in checks:
        refusal = check()
        if refusal is not None:
            return refusal
    return None


def _usage_refusal(args: argparse.Namespace, argv: Sequence[str]) -> Refusal | None:
    if (args.file is None) == (not argv):
        return Refusal("usage", "give exactly one procedure: --file <path>, or an argv after --")
    if args.control_file is not None and args.control_argv is not None:
        return Refusal("usage", "give at most one control: --control-file or --control-argv")
    if not args.who.strip():
        return Refusal("usage", "--who is empty")
    for spec in (args.reduce, args.control_reduce):
        problem = None if spec is None else _reducer_problem(spec)
        if problem is not None:
            return Refusal("usage", problem)
    return None


# --- the block ---------------------------------------------------------------------------


def canonical(block: Mapping[str, Any]) -> bytes:
    """The one byte form the seal is computed over: every field except ``hash``."""
    body = {key: value for key, value in block.items() if key != "hash"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def seal(block: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(block)).hexdigest()[:16]


def verify_hash(block: Mapping[str, Any]) -> bool:
    return block.get("hash") == seal(block)


def render_block(block: Mapping[str, Any]) -> str:
    return f"{MARKER}\n```json\n{json.dumps(block, indent=2, ensure_ascii=False)}\n```\n"


def parse_blocks(text: str) -> list[ParsedBlock]:
    """Every marker in ``text`` is a block — one whose fence does not parse is kept, not skipped.

    ``data is None`` for a marker with no ``json`` fence after it, or a fence that is not a
    JSON object. A reader that skipped those would stop describing its input while its
    count still looked tidy (the ``tally.py`` rule), so the caller counts them as bad seals.
    """
    blocks: list[ParsedBlock] = []
    for marker in _MARKER_LINE.finditer(text):
        line = text.count("\n", 0, marker.start()) + 1
        fence = _FENCE.match(text, marker.end())
        data: Any = None
        if fence is not None:
            try:
                data = json.loads(fence.group(1))
            except json.JSONDecodeError:
                data = None
        blocks.append(ParsedBlock(line, data if isinstance(data, dict) else None))
    return blocks


def _token(value: object) -> str:
    text = str(value)
    return text if re.fullmatch(r"\S+", text) else json.dumps(text, ensure_ascii=False)


def values_line(block: Mapping[str, Any]) -> str:
    paths = "history" if block["history"] else str(len(block["declared_paths"]))
    return (
        f"MEASURE: metric={block['metric']} value={_token(block['value'])} "
        f"units={block['units']} against={block['against_sha']} paths={paths} "
        f"pass={block['pass']} control={_token(block['control']['value'])} "
        f"hash={str(block['hash']).removeprefix('sha256:')}"
    )


def append_block(out: Path, block: Mapping[str, Any]) -> str | None:
    """Append ``block`` to ``out`` and read it back; the reason the read-back failed, or None."""
    existing = out.read_text(encoding="utf-8") if out.is_file() else ""
    gap = "\n\n"
    if not existing or existing.endswith("\n\n"):
        gap = ""
    elif existing.endswith("\n"):
        gap = "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as handle:
        handle.write(gap + render_block(block))
    found = [
        b.data
        for b in parse_blocks(out.read_text(encoding="utf-8"))
        if b.data is not None and b.data.get("hash") == block["hash"]
    ]
    if len(found) != 1 or not verify_hash(found[0]):
        return f"read-back found {len(found)} block(s) sealed {block['hash']} in {out}, expected 1"
    return None


def _take(
    args: argparse.Namespace, tree: Tree, argv: Sequence[str], control_argv: list[str] | None
) -> dict[str, Any] | Refusal:
    """Run the procedure and its control, then assemble and seal the block."""
    reduce = args.reduce
    control_reduce = args.control_reduce or reduce
    procedure: dict[str, Any] = (
        {"file": args.file, "reduce": reduce}
        if args.file is not None
        else {"argv": list(argv), "reduce": reduce}
    )
    control: dict[str, Any] = (
        {"file": args.control_file, "reduce": control_reduce}
        if args.control_file is not None
        else {"argv": control_argv, "reduce": control_reduce}
    )
    value = run_procedure(procedure, tree.root)
    control_value = run_procedure(control, tree.root)
    if control_value == value:
        return Refusal(
            "R4",
            f"the control reads the measured value ({value!r}) — a control "
            "that cannot differ cannot discriminate (0038:568-570)",
        )
    predicate = parse_predicate(args.predicate)
    if predicate is None:  # unreachable after R3; kept so the type is honest
        return Refusal("R3", f"--predicate {args.predicate!r} is outside the grammar")
    block: dict[str, Any] = {
        "schema": SCHEMA,
        "metric": args.metric,
        "value": value,
        "units": args.units,
        "procedure": procedure,
        "against_sha": tree.sha,
        "declared_paths": [] if args.history else list(args.paths),
        "history": bool(args.history),
        "who": args.who,
        "when": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "predicate": args.predicate,
        "pass": predicate.holds(value),
        "control": {**control, "value": control_value},
        "rerun": bool(args.rerun),
    }
    block["hash"] = seal(block)
    return block


# --- command line ------------------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="measure",
        description="Emit one sealed measure/v1 block, or refuse and say why.",
        allow_abbrev=False,
    )
    parser.add_argument("--metric", required=True)
    parser.add_argument("--units", required=True)
    parser.add_argument(
        "--who", required=True, help="required — a default is how a field " "becomes decoration"
    )
    parser.add_argument(
        "--predicate",
        default=None,
        help='value <op> <int|"string">, or '
        "<int> <= value <= <int>; fixed before the number is taken",
    )
    parser.add_argument("--paths", nargs="*", default=None, help="tracked, clean paths measured")
    parser.add_argument("--history", action="store_true", help="a measurement over immutable SHAs")
    parser.add_argument("--rerun", action="store_true", help="a guard may re-execute this offline")
    parser.add_argument("--file", default=None, help="reduce this repo file instead of an argv")
    parser.add_argument(
        "--reduce", required=True, help="raw | lines | bytes | first | int | " "count:<regex>"
    )
    parser.add_argument("--control-file", default=None)
    parser.add_argument("--control-argv", default=None, help="one string, split without a shell")
    parser.add_argument("--control-reduce", default=None, help="defaults to --reduce")
    parser.add_argument("--out", type=Path, default=None, help="append the block here")
    return parser


def _measure(raw: list[str]) -> tuple[dict[str, Any], Path | None] | Refusal:
    options, procedure_argv = _split_raw(raw)
    if "--shell" in options:
        return Refusal("R6", "there is no --shell: the emitter runs an argv list and nothing else")
    try:
        args = _parser().parse_args(options)
        control_argv = None if args.control_argv is None else shlex.split(args.control_argv)
    except (_UsageError, ValueError) as exc:
        return Refusal("usage", str(exc))
    refusal = _usage_refusal(args, procedure_argv) or _first_refusal(
        [
            lambda: declaration_refusal(args),
            lambda: predicate_refusal(args),
            lambda: control_refusal(args),
            lambda: history_shape_refusal(args, procedure_argv),
            lambda: shell_refusal(procedure_argv),
            lambda: shell_refusal(control_argv or []),
            lambda: rerun_refusal(args, procedure_argv),
        ]
    )
    if refusal is not None:
        return refusal
    tree = resolve_tree(Path.cwd())
    if isinstance(tree, Refusal):
        return tree
    try:
        refusal = path_refusal(tree, args.paths or []) or endpoint_refusal(
            tree, args, procedure_argv
        )
        if refusal is not None:
            return refusal
        taken = _take(args, tree, procedure_argv, control_argv)
    except ProcedureError as exc:
        return Refusal("procedure", str(exc))
    out: Path | None = args.out
    return taken if isinstance(taken, Refusal) else (taken, out)


def _split_raw(raw: list[str]) -> tuple[list[str], list[str]]:
    """Options before the first ``--``, and the procedure argv after it, split by hand.

    argparse's own ``--`` handling with a ``nargs="*"`` positional interleaved among
    options is the kind of parser quirk that silently moves an element across the line.
    """
    if "--" not in raw:
        return raw, []
    cut = raw.index("--")
    return raw[:cut], raw[cut + 1 :]


def _emit(block: dict[str, Any], out: Path | None) -> int:
    """Print the values, then the block (or append it), and return the one status."""
    print(values_line(block))
    if out is None:
        print(render_block(block), end="")
        return EXIT_PASS if block["pass"] else EXIT_FAIL
    problem = append_block(out, block)
    if problem is not None:
        print(f"MEASURE: REFUSED write — {problem}")
        return EXIT_REFUSED
    print(f"MEASURE: appended {block['hash']} to {out}")
    return EXIT_PASS if block["pass"] else EXIT_FAIL


def _refused(refusal: Refusal) -> int:
    """Print one refusal in the shape every reader parses, and return the one status."""
    print(f"MEASURE: REFUSED {refusal.rule} — {refusal.reason}")
    return EXIT_REFUSED


def _recipe_invocations(sha: str, who: str) -> list[list[str]]:
    """``status-reconcile``'s two invocations, over an already-resolved immutable SHA.

    PLAN-0125 §4.2: ``status-scribe`` receives ``head_commit`` and ``recent_commits`` as
    blocks and transcribes each ``value`` into STATUS's frontmatter, so each *value* is the
    short form STATUS carries while each ``against_sha`` is the full SHA every block carries
    (§2.2). Each control re-runs the same query without the one formatting flag the value
    depends on — full SHAs against short ones — so a procedure that lost ``--short=7`` or
    ``--format=%h`` reads its own control and R4 refuses it.

    ✎ **s304 — the ref is resolved here because the PLAN's own recipe does not run.** §2.3
    names ``main`` itself as the endpoint and calls the blocks ``rerun: false`` *"by
    construction"*. Measured at ``06df94d7``: R5 refuses a symbolic endpoint outright
    (``history endpoint(s) ['main'] are not immutable SHAs``), and §2.3's ``-n 10`` leaks
    its detached ``10`` in as a second endpoint — ``revision_candidates``' own docstring
    predicts that one. Resolving the ref first satisfies R5 honestly and keeps §2.3's
    stated outcome: these invocations still do not pass ``--rerun``, so the blocks are
    still ``rerun: false``. No refusal changes, so AC-2's nine witnesses are untouched.
    """
    return [
        [
            *("--metric", "status_head_commit", "--units", "sha", "--who", who),
            *("--history", "--predicate", 'value != ""'),
            *("--control-argv", f"git rev-parse {sha}", "--control-reduce", "raw"),
            *("--reduce", "raw", "--"),
            *("git", "rev-parse", "--short=7", sha),
        ],
        [
            *("--metric", "status_recent_commits", "--units", "shas", "--who", who),
            *("--history", "--predicate", 'value != ""'),
            *("--control-argv", f"git log --format=%H --max-count=10 {sha}"),
            *("--control-reduce", "raw"),
            *("--reduce", "raw", "--"),
            *("git", "log", "--format=%h", "--max-count=10", sha),
        ],
    ]


def _recipe(raw: list[str]) -> int:
    """``--recipe <name>`` — several blocks from one run, each through the normal path.

    Every invocation the recipe builds goes back through :func:`_measure`, so R1…R8 run
    over it exactly as they would over a hand-typed command line. The recipe adds a
    precondition of its own and no exemption.
    """
    parser = _Parser(prog="measure", allow_abbrev=False)
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--who", required=True)
    parser.add_argument("--out", type=Path, default=None)
    try:
        args = parser.parse_args(raw)
    except (_UsageError, ValueError) as exc:
        return _refused(Refusal("usage", str(exc)))
    if args.recipe not in RECIPES:
        known = sorted(RECIPES)
        return _refused(Refusal("recipe", f"unknown recipe {args.recipe!r} — known: {known}"))
    if args.out is not None:
        return _refused(
            Refusal(
                "recipe",
                "--out: a recipe block is payload provenance for one dispatch and is "
                "never persisted (PLAN-0125 §6 E1 — ④-lite re-derives head_commit itself)",
            )
        )
    if not args.who.strip():
        return _refused(Refusal("usage", "--who is empty"))
    tree = resolve_tree(Path.cwd())
    if isinstance(tree, Refusal):
        return _refused(tree)
    resolved = _git(tree.root, "rev-parse", "--verify", "--quiet", f"{RECIPE_REF}^{{commit}}")
    sha = resolved.stdout.decode("utf-8", "replace").strip()
    if resolved.returncode != 0 or not _FULL_SHA.fullmatch(sha):
        return _refused(
            Refusal("recipe", f"{RECIPE_REF!r} does not resolve to a commit — nothing to measure")
        )
    status = EXIT_PASS
    for invocation in _recipe_invocations(sha, args.who):
        outcome = _measure(invocation)
        if isinstance(outcome, Refusal):
            return _refused(outcome)
        emitted = _emit(*outcome)
        if emitted != EXIT_PASS:
            status = emitted
    return status


def main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--recipe" in raw:
        status = _recipe(raw)
    else:
        outcome = _measure(raw)
        status = _refused(outcome) if isinstance(outcome, Refusal) else _emit(*outcome)
    print(verdict_line(status))
    return status


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
