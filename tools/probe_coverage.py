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

**One claim, one key** (PLAN-0128). :attr:`Claim.stable_key` is ``@<id>`` when the claim
declares a trailing ``# claim: <id>`` comment on its anchor line, and
``owner|source|#occurrence`` otherwise; a tagged claim is addressable **only** by its
tag. The tag is not derived from the source it names, which is what makes it survive an
edit that a text key cannot: there is no edit that removes the assertion and leaves an
address still resolving to something. Three tag forms are refused at enumeration, loudly
— a duplicate id in one module, a malformed id, and a tag on a line that is not exactly
one claim's anchor (including an interior line of a multi-line claim, and the
comment-on-its-own-line form).
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path


class ClaimTagError(ValueError):
    """A ``# claim:`` tag that enumeration refuses.

    Raised from :func:`enumerate_claims`, so every reader of a claim set meets it: the
    ``always_run`` lint turns it into a Finding at commit time, and the probe driver hits
    it **before its first mutation** rather than midway through a restore.

    A ``ValueError`` subclass on purpose — a caller that already handles bad input
    generically keeps working, while a caller that wants to name tag trouble separately
    can.
    """


#: The one tag form. Narrow by design: ``<id>`` cannot contain ``|``, ``#`` or
#: whitespace, so a tag key (``@<id>``) can never be confused with a text key
#: (``owner|source|#occurrence``).
_TAG_MARKER = "# claim:"

#: ``<id>`` grammar (PLAN-0128 §2.1). Anchored by :meth:`re.Pattern.fullmatch`.
_TAG_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]*")

#: Where :attr:`Claim.source` is cut. A claim longer than this keeps a PREFIX of its
#: expression, which therefore does not parse on its own — anything comparing two
#: sources has to know that (``_tag._equivalent_source`` does). Named here rather than
#: inlined at the two cut sites so there is one derivation of the number, not three.
SOURCE_CUT = 160

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
    cardinality: int = 1
    tag: str | None = None

    @property
    def stable_key(self) -> str:
        """A key that survives edits to the module AND never collides.

        **When the claim declares a tag, the key IS the tag** — ``@<id>``, from a
        trailing ``# claim: <id>`` on the claim's anchor line. The text derivation below
        is what an untagged claim still uses. One field, one lookup, two derivations: a
        tag key and a text key are the same kind of thing, so every refusal that keys on
        ``stable_key`` covers both with no second code path.

        A tag is stronger than any text key can be, because it is not *derived from the
        current source* at all: no edit can delete the assertion and leave an address
        that still resolves. Deleting the statement deletes the line the tag sits on;
        deleting only the assertion's text strands a ``# claim:`` on a line that ends no
        claim, which :func:`enumerate_claims` refuses. The text derivations below can
        only ever narrow the window in which a stale address still resolves — they
        cannot close it.

        ``owner|source`` alone is the obvious line-independent address and it is WRONG:
        a test that asserts ``run_row is not None`` twice would collapse two claims into
        one key, and a coverage report built on it would call the pair covered when only
        the first was ever witnessed — a coverage lie of exactly the kind #0047 is
        about. ``occurrence`` disambiguates repeats within one owner, in source order.

        ``occurrence`` ALONE is also wrong, and for a reason that took until session 310
        to measure: it is a rank re-derived from the current source, and ranks recycle.
        With two identical asserts in one owner, deleting the first leaves the survivor
        at ``#0`` — so the *deleted* claim's key silently addresses it, and the battery
        goes on crediting a claim nobody declared. No rule over the current source can
        refuse that, because the fact which would (that the first assert used to exist)
        is no longer in the source. The same recycling happens to two asserts that
        differ only past the 160-character ``source`` cut.

        So a repeated claim's key carries its group's SIZE beside its rank. Deleting one
        member changes the size, every key in that group stops resolving, and
        ``_validate`` refuses before the first mutation — drift causes re-work, never
        inheritance. A claim alone in its group keys exactly as it did before, so every
        address that was never at risk is byte-identical.

        🔴 **Tagging one claim never moves another claim's key.** ``occurrence`` and
        ``cardinality`` are stamped over *every* claim, tagged or not, so a tagged claim
        still occupies its slot in its text group. Tag the first of two identical asserts
        and the survivor stays ``#1/2`` — it does **not** become ``#0`` or ``#1``. Were it
        otherwise, adding a tag would silently re-point a *different* claim's address,
        which is the whole class of defect tags exist to remove.
        """
        if self.tag is not None:
            return f"@{self.tag}"
        if self.cardinality <= 1:
            return f"{self.owner}|{self.source}|#{self.occurrence}"
        return f"{self.owner}|{self.source}|#{self.occurrence}/{self.cardinality}"

    def render(self) -> str:
        flag = "  ⚠️ CONJUNCTION — one mutation can witness only one operand" if self.multi else ""
        tag = f"  @{self.tag}" if self.tag is not None else ""
        return f"{self.claim_id}{tag}  [{self.kind}]  {self.source}{flag}"


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


def _parse_tag(comment: str, row: int, path: Path) -> str | None:
    """The ``<id>`` a COMMENT token declares, or ``None`` when it declares no tag.

    A COMMENT token may legitimately hold other comments before the tag
    (``# noqa: E501  # claim: E1``), so the marker is looked for *anywhere* in the token
    and whatever precedes it is left alone. Two markers in one token is malformed: which
    one addresses the claim would be a coin flip.
    """
    hits = [i for i in range(len(comment)) if comment.startswith(_TAG_MARKER, i)]
    if not hits:
        return None
    if len(hits) > 1:
        raise ClaimTagError(
            f"{path}:{row}: two '{_TAG_MARKER}' markers in one comment — "
            f"exactly one tag per claim: {comment.strip()!r}"
        )
    rest = comment[hits[0] + len(_TAG_MARKER) :].strip()
    if not rest:
        raise ClaimTagError(f"{path}:{row}: '{_TAG_MARKER}' with an empty id")
    parts = rest.split(None, 1)
    ident, trailing = parts[0], (parts[1] if len(parts) > 1 else "")
    if trailing and not trailing.startswith("#"):
        raise ClaimTagError(
            f"{path}:{row}: text after the claim id that is not a further '#' comment: "
            f"{trailing!r} — an id cannot contain whitespace"
        )
    if not _TAG_ID.fullmatch(ident):
        raise ClaimTagError(
            f"{path}:{row}: malformed claim id {ident!r} — "
            f"must match {_TAG_ID.pattern} (no '|', no '#', no whitespace)"
        )
    return ident


def _anchors_and_tags(source: str, path: Path) -> tuple[list[int], dict[int, str]]:
    """``(anchor rows, {row: tag id})``, both read from ONE token stream.

    The anchor row of a logical line is the row of the NEWLINE token that ends it —
    ``tokenize`` emits NL, not NEWLINE, for the continuation rows inside brackets, so
    this is the statement's last physical line for an ``assert`` and the ``:`` line for
    a ``with`` header, with no per-node special-casing.

    Tags are read from COMMENT **tokens**, never from a regex over raw lines: a
    ``# claim:`` inside a string literal or a docstring is a STRING token and is
    therefore invisible here, which is the point.
    """
    newline_rows: list[int] = []
    tags: dict[int, str] = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NEWLINE:
            newline_rows.append(token.start[0])
        elif token.type == tokenize.COMMENT:
            row = token.start[0]
            ident = _parse_tag(token.string, row, path)
            if ident is not None:
                tags[row] = ident
    return newline_rows, tags


def is_valid_tag_id(ident: str) -> bool:
    """Whether ``ident`` is a well-formed ``# claim:`` id (§2.1).

    Public because the ``tag`` subcommand chooses ids itself and must refuse a bad one
    **in its plan phase**, before writing. Asking the same question of the same pattern
    the enumerator enforces is the point: a tool that invented its own notion of a legal
    id could write a file its own reader then refuses.
    """
    return _TAG_ID.fullmatch(ident) is not None


def anchor_row_for(claim_lineno: int, newline_rows: Sequence[int]) -> int:
    """The row a tag for the claim starting at ``claim_lineno`` must sit on.

    The anchor is the first logical-line end at or after the claim's first row. A claim
    occupies every row between the two, so no other statement can end inside it.

    🔴 **This is the single derivation of "which line is the anchor", and it is public
    for exactly one reason:** the ``tag`` subcommand *writes* a tag onto a line that
    :func:`enumerate_claims` must then *read* it from. Two implementations of this rule
    that agreed today would be free to drift tomorrow, and the failure would be silent —
    a tag written one line off enumerates as ``unattached`` (loud) or, worse, on an
    interior line, where it leaks into the very ``source`` it names. One function,
    both callers.
    """
    later = [row for row in newline_rows if row >= claim_lineno]
    return later[0] if later else claim_lineno


def claims_with_anchor_rows(path: Path) -> list[tuple[Claim, int]]:
    """Every claim in ``path``, paired with the row a tag for it must occupy.

    The writer's entry point, built from the same token stream the reader uses (see
    :func:`anchor_row_for`). Raises whatever :func:`enumerate_claims` raises.
    """
    claims = enumerate_claims(path)
    newline_rows, _ = _anchors_and_tags(path.read_text(encoding="utf-8"), path)
    return [(claim, anchor_row_for(claim.lineno, newline_rows)) for claim in claims]


def _attach_tags(ordered: list[Claim], source: str, path: Path) -> list[Claim]:
    """Attach each declared tag to the one claim its anchor line ends, or refuse.

    Three refusals, all loud (§2.1): a duplicate id inside one module; a tag on a line
    that is not exactly one claim's anchor (**unattached**, which is what the rejected
    line-above form now is, so nobody can write it by habit and silently lose the
    address); and a tag on an **interior** line of a multi-line claim, which would be
    inside the span ``ast.get_source_segment`` slices and so would change the text key of
    the very claim it names.
    """
    newline_rows, tags = _anchors_and_tags(source, path)
    if not tags:
        return ordered

    # One derivation, shared with the `tag` subcommand's writer — see `anchor_row_for`.
    anchor_of = [anchor_row_for(claim.lineno, newline_rows) for claim in ordered]

    by_anchor: dict[int, list[int]] = {}
    for index, row in enumerate(anchor_of):
        by_anchor.setdefault(row, []).append(index)

    seen_ids: dict[str, int] = {}
    for row in sorted(tags):
        ident = tags[row]
        if ident in seen_ids:
            raise ClaimTagError(
                f"{path}: duplicate claim id {ident!r} on lines {seen_ids[ident]} and "
                f"{row} — an id addresses exactly one claim"
            )
        seen_ids[ident] = row

    attached: dict[int, str] = {}
    for row in sorted(tags):
        targets = by_anchor.get(row, [])
        if len(targets) == 1:
            attached[targets[0]] = tags[row]
            continue
        if len(targets) > 1:
            raise ClaimTagError(
                f"{path}:{row}: this line ends {len(targets)} claims, so a tag on it is "
                f"ambiguous — put each claim on its own line"
            )
        inside = next(
            (c for c, a in zip(ordered, anchor_of, strict=True) if c.lineno <= row < a),
            None,
        )
        if inside is not None:
            raise ClaimTagError(
                f"{path}:{row}: tag on an interior line of the claim starting at line "
                f"{inside.lineno} ({inside.source!r}) — it would leak into that claim's "
                f"source text. Put it on the anchor line (the line that ends the "
                f"statement)."
            )
        raise ClaimTagError(
            f"{path}:{row}: unattached tag — this line is no claim's anchor line. A tag "
            f"is a TRAILING comment on the line that ends the claim; a tag on its own "
            f"line, or above the claim, addresses nothing."
        )

    return [
        replace(claim, tag=attached[index]) if index in attached else claim
        for index, claim in enumerate(ordered)
    ]


def enumerate_claims(path: Path) -> list[Claim]:
    """Every claim in ``path``, in source order.

    Raises ``SyntaxError`` on an unparsable module rather than returning an empty list —
    a silent zero here would read as "nothing to cover", which is the false green this
    whole module exists to prevent. Raises :class:`ClaimTagError` on a tag this module
    refuses (§2.1), for the same reason: a tag nobody can resolve must not pass as "no
    tag".
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
                    source=" ".join(text.split())[:SOURCE_CUT],
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
                        source=" ".join(text.split())[:SOURCE_CUT],
                        kind="raises",
                        multi=False,
                    )
                )

    ordered = sorted(claims, key=lambda c: (c.module, c.lineno))
    # Two passes, because a claim's key needs its group's SIZE and that is not known
    # until every member has been seen. One pass could only ever stamp the rank, which
    # is the recycling defect `stable_key` documents.
    totals: dict[tuple[str, str], int] = {}
    for claim in ordered:
        pair = (claim.owner, claim.source)
        totals[pair] = totals.get(pair, 0) + 1
    seen: dict[tuple[str, str], int] = {}
    stamped: list[Claim] = []
    for claim in ordered:
        pair = (claim.owner, claim.source)
        index = seen.get(pair, 0)
        seen[pair] = index + 1
        stamped.append(replace(claim, occurrence=index, cardinality=totals[pair]))
    # Tags are attached AFTER stamping, and stamping runs over every claim regardless:
    # a tagged claim keeps its slot, so tagging one member of a text group cannot move
    # any other member's key (see `stable_key`).
    return _attach_tags(stamped, source, path)


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
