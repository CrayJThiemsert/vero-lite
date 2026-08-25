"""Report which of a test module's claims no probe ever reddened.

**Why this exists (lesson #0047).** A probe battery answers exactly one question —
"did my probes behave as I predicted?" — and is structurally *silent* about the
question that matters as much: "what did I never probe?" In session 251 a battery
printed PASS while 12 of 33 items had never been reddened by any mutation, and two of
those gaps were load-bearing. The repair named in `docs/lessons/0047-*.md` §6 is that a
battery's pass rule needs a fourth clause beside reach / named-red / no-extra:
**every item not reddened by some probe is named, with a reason.**

This module is that clause, computed **mechanically from the AST** rather than by hand.
A regex over ``assert `` matches prose inside docstrings and misses ``pytest.raises``;
a hand-written list is short by exactly the number of cases its author cannot see.

**What counts as a claim** (lesson #0047 §6, verbatim rules):

- every ``assert`` statement is one claim;
- every ``pytest.raises`` (and ``pytest.warns``) context manager is one claim — the
  block asserts that something raised;
- a conjunction (``assert a and b``) is counted as the ONE claim it behaves as: the
  run stops at the first failing operand either way, so a single mutation can only
  ever witness one of them. Such claims are FLAGGED rather than split, because the
  honest repair is to split the test, not to inflate the denominator.

**Scoping the denominator.** The caller supplies the module(s) under test, and #0047's
own finding applies: a denominator wider than the instrument's reach forces junk
exemptions, and a junk-filled exemption list destroys the check faster than having none.
So exemptions are not free-form — each carries a written reason, and the report prints
them where a reviewer meets them rather than hiding them behind a count. If narrowing
the denominator feels convenient, that is the moment to have someone else check.

**Usage is driver-first** (PLAN-0115 R-A, correcting this docstring's original framing).
It used to say "a session's battery imports :func:`enumerate_claims` and
:func:`render_report`" — i.e. that each session writes its own battery *script* around
this library. Session 253 measured what that costs: a from-scratch driver re-made four
retired defect classes at once, and **none of them is visible from here** by construction,
because :func:`render_report` sees claim keys and credit maps and never *how* credit was
earned. So the seam moved. The machinery — mutate, restore, classify, credit, report —
ships in ``tools/probe_battery/``; what stays per-session is the probe *definitions*
(which mutation, which declared claim, which expected outcome), fed to that driver as
data. This module remains the coverage half it always was, and the driver calls it.

The ``__main__`` path lists a module's claims by ``claim_id`` so a battery author can see
the denominator before running anything; ``python -m tools.probe_battery keys <module>``
lists the same claims by :attr:`Claim.stable_key`, which is the address a probe must
declare.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path

#: Printed verbatim when every claim is either reddened by a probe or exempted with a
#: reason. A caller greps for this token — an echoed exit code is corruptible, a printed
#: verdict is not.
VERDICT_COMPLETE = "PROBE-COVERAGE: COMPLETE"

#: Printed verbatim when at least one claim is neither reddened nor exempted. This is
#: the s251 shape: a battery that would otherwise have printed PASS.
VERDICT_GAPS = "PROBE-COVERAGE: GAPS"


@dataclass(frozen=True)
class Claim:
    """One load-bearing assertion, addressed by a stable id.

    ``claim_id`` is ``<module stem>::<owner>::L<lineno>``. The line number is part of
    the identity on purpose: two assertions in one function are two claims, and a
    battery that cannot tell them apart is the instrument #0047 describes.
    """

    claim_id: str
    module: str
    owner: str
    lineno: int
    source: str
    kind: str
    multi: bool
    occurrence: int = 0

    @property
    def stable_key(self) -> str:
        """A key that survives edits to the module AND never collides.

        ``owner|source`` alone is the obvious line-independent address and it is WRONG:
        a test that asserts ``run_row is not None`` twice would collapse two claims into
        one key, and a coverage report built on it would call the pair covered when only
        the first was ever witnessed — a coverage lie of exactly the kind #0047 is
        about. ``occurrence`` disambiguates repeats within one owner, in source order.
        """
        return f"{self.owner}|{self.source}|#{self.occurrence}"

    def render(self) -> str:
        flag = "  ⚠️ CONJUNCTION — one mutation can witness only one operand" if self.multi else ""
        return f"{self.claim_id}  [{self.kind}]  {self.source}{flag}"


def _owner_of(tree: ast.Module) -> dict[int, str]:
    """Map every line to its innermost enclosing function name.

    Built by walking function bodies rather than by comparing line ranges, so a claim
    inside a nested helper is attributed to the helper and not to the test around it.
    """
    owners: dict[int, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        end = node.end_lineno or node.lineno
        for line in range(node.lineno, end + 1):
            # Inner definitions are walked too; the narrowest span wins because a nested
            # function's own pass overwrites the outer one for exactly its own lines.
            existing = owners.get(line)
            if existing is None or _span_of(tree, existing) > (end - node.lineno):
                owners[line] = node.name
    return owners


def _span_of(tree: ast.Module, name: str) -> int:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return (node.end_lineno or node.lineno) - node.lineno
    return 1 << 30


def _is_raises_call(node: ast.expr) -> bool:
    """Whether ``node`` is a ``pytest.raises(...)`` / ``pytest.warns(...)`` call."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr in {"raises", "warns"}
    return isinstance(func, ast.Name) and func.id in {"raises", "warns"}


def enumerate_claims(path: Path) -> list[Claim]:
    """Every claim in ``path``, in source order.

    Raises ``SyntaxError`` on an unparsable module rather than returning an empty list —
    a silent zero here would read as "nothing to cover", which is the false green this
    whole module exists to prevent.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    owners = _owner_of(tree)
    stem = path.stem
    claims: list[Claim] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            text = ast.get_source_segment(source, node.test) or "<unrendered>"
            claims.append(
                Claim(
                    claim_id=f"{stem}::{owners.get(node.lineno, '<module>')}::L{node.lineno}",
                    module=stem,
                    owner=owners.get(node.lineno, "<module>"),
                    lineno=node.lineno,
                    source=" ".join(text.split())[:160],
                    kind="assert",
                    multi=isinstance(node.test, ast.BoolOp) and isinstance(node.test.op, ast.And),
                )
            )
        elif isinstance(node, ast.With | ast.AsyncWith):
            for item in node.items:
                if not _is_raises_call(item.context_expr):
                    continue
                text = ast.get_source_segment(source, item.context_expr) or "<unrendered>"
                claims.append(
                    Claim(
                        claim_id=f"{stem}::{owners.get(node.lineno, '<module>')}::L{node.lineno}",
                        module=stem,
                        owner=owners.get(node.lineno, "<module>"),
                        lineno=node.lineno,
                        source=" ".join(text.split())[:160],
                        kind="raises",
                        multi=False,
                    )
                )

    ordered = sorted(claims, key=lambda c: (c.module, c.lineno))
    seen: dict[tuple[str, str], int] = {}
    stamped: list[Claim] = []
    for claim in ordered:
        pair = (claim.owner, claim.source)
        index = seen.get(pair, 0)
        seen[pair] = index + 1
        stamped.append(replace(claim, occurrence=index))
    return stamped


def render_report(
    claims: Iterable[Claim],
    reddened: Mapping[str, str],
    exemptions: Mapping[str, str],
    key_of: Callable[[Claim], str] | None = None,
) -> tuple[str, bool]:
    """Render the coverage report and its verdict.

    ``reddened`` maps a claim key to the probe that witnessed it RED; ``exemptions``
    maps a claim key to the written reason no probe can reach it. A claim in neither
    map is a GAP — the thing #0047 says a battery must stop being silent about.

    ``key_of`` chooses how a claim is ADDRESSED, and defaults to :attr:`Claim.claim_id`.
    A battery that must survive edits to the module under test should pass a key built
    from ``owner`` + ``source`` instead: a line-numbered key silently re-points at a
    different assertion the moment a line is inserted above it, which turns an exemption
    into an unnoticed blanket over the wrong claim.

    Returns ``(report, complete)``. A key in ``reddened`` or ``exemptions`` that matches
    no claim is reported as STALE and fails the verdict: it means the battery is
    addressing an assertion that no longer exists, which is how a coverage check quietly
    rots into agreement with itself.
    """
    resolve = key_of if key_of is not None else (lambda c: c.claim_id)
    ordered = list(claims)
    known = {resolve(c) for c in ordered}
    lines: list[str] = []

    covered = [c for c in ordered if resolve(c) in reddened]
    exempt = [c for c in ordered if resolve(c) not in reddened and resolve(c) in exemptions]
    gaps = [c for c in ordered if resolve(c) not in reddened and resolve(c) not in exemptions]
    stale = sorted((set(reddened) | set(exemptions)) - known)
    conjunctions = [c for c in ordered if c.multi]

    lines.append("=" * 78)
    lines.append("PROBE COVERAGE (lesson #0047 §6 — the fourth clause)")
    lines.append("=" * 78)
    lines.append(
        f"claims: {len(ordered)}   witnessed RED: {len(covered)}   "
        f"exempted: {len(exempt)}   GAPS: {len(gaps)}   stale ids: {len(stale)}"
    )
    lines.append("")

    lines.append(f"-- witnessed RED ({len(covered)}) " + "-" * 40)
    for claim in covered:
        lines.append(f"  [{reddened[resolve(claim)]}] {claim.render()}")

    lines.append("")
    lines.append(f"-- NOT reddened, exempted with a reason ({len(exempt)}) " + "-" * 16)
    for claim in exempt:
        lines.append(f"  {claim.render()}")
        lines.append(f"      reason: {exemptions[resolve(claim)]}")

    if conjunctions:
        lines.append("")
        lines.append(f"-- conjunctions: one mutation witnesses ONE operand ({len(conjunctions)})")
        for claim in conjunctions:
            lines.append(f"  {claim.render()}")

    if stale:
        lines.append("")
        lines.append(f"-- 🔴 STALE ids (addressed, but no such claim) ({len(stale)}) " + "-" * 8)
        for claim_id in stale:
            lines.append(f"  {claim_id}")

    if gaps:
        lines.append("")
        lines.append(f"-- 🔴 GAPS: neither reddened nor exempted ({len(gaps)}) " + "-" * 14)
        for claim in gaps:
            lines.append(f"  {claim.render()}")

    complete = not gaps and not stale
    lines.append("")
    lines.append(VERDICT_COMPLETE if complete else VERDICT_GAPS)
    return "\n".join(lines), complete


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="+", type=Path, help="test modules to enumerate")
    args = parser.parse_args(argv)

    total = 0
    for path in args.paths:
        claims = enumerate_claims(path)
        total += len(claims)
        print(f"--- {path} ({len(claims)} claims) ---")
        for claim in claims:
            print(f"  {claim.render()}")
    print(f"\ntotal claims: {total}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())
