"""Classify one probe run from pytest's machine-readable failure record.

**Why this module exists (ADR-0038 C6).** A probe's RED is not a witness until the
failure record shows *the declared assertion failing at its own site*. Session 253's
hand-rolled driver keyed on ``returncode == 0`` and discarded the captured output, so an
``AttributeError`` from a disabled ``None`` guard and a ``KeyError`` raised one line
*before* the tracked assertion both counted as witnessed, and the battery published
13/13. C6 promoted that failure class to a binding rule; this module is its form-(c)
enforcer, named by the ADR (PLAN-0115 Step 1, AC-2 + AC-4).

**Measured, not assumed** (probe run 2026-08-25 against the project's pinned pytest, 15
outcome shapes). The two findings that shape every line below:

1. 🔴 ``<failure type="...">`` is **absent** — ``type`` reads ``None`` on every failure.
   A classifier reading that attribute cannot tell an ``AssertionError`` from a
   ``ModuleNotFoundError``, which is s253's defect wearing different clothes. The
   exception type lives **only** in the body's last line.
2. The body's last non-empty line is ``<file>:<line>: <ExcType>`` and this invariant
   held across every shape probed: a plain assert, an assert inside a helper (the line
   is the *helper's*, which is also where :func:`tools.probe_coverage.enumerate_claims`
   attributes the claim), a parametrized case, a multi-line exception message, a
   multi-line assertion repr, and setup/teardown errors. It is the one machine-readable
   record that carries **both** the failing site and the exception type.

**The witness rule is a conjunction, and it has to be.** ``assert obj.thing == 1`` where
``obj is None`` fails at the declared assertion's *own line* with an ``AttributeError``:
site matches, kind does not. Site alone would credit it. So a RED is a witness only when
the site matches **and** the failure is assertion-family. Identity is still never decided
by exception type *alone* — a ``KeyError`` one line above a tracked assert *about* a
``KeyError`` has the right type and the wrong site, and is rejected on the site.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from tools.probe_coverage import Claim


class Outcome(StrEnum):
    """What one probe run actually did — never inferred from an exit code.

    The first seven are PLAN-0115 Step 1's contract. Two more are additions the same
    contract *requires* but did not name, each recorded here rather than folded silently
    into a neighbour:

    - :attr:`MUTATION_ERROR` — Step 1 contract item 2 demands the mutation be "verified
      reached disk". Without an outcome for "it did not", a no-op mutation would be
      reported as :attr:`GREEN`, i.e. as evidence that the guard is live, which is the
      exact inversion.
    - :attr:`UNREADABLE` — C6's *second* conjunct ("the declared assertion did fail but
      its message could not tell a reader what broke") made mechanical for the one case a
      machine can judge: a failure record naming no site at all. Folding it into
      :attr:`CRASHED` would report "a non-assertion exception" about a run where the
      exception is precisely what could not be read.
    """

    WITNESSED = "WITNESSED"
    MISFIRE = "MISFIRE"
    CRASHED = "CRASHED"
    UNREADABLE = "UNREADABLE"
    GREEN = "GREEN"
    SETUP_ERROR = "SETUP/COLLECT-ERROR"
    SKIPPED = "SKIPPED"
    NO_TESTS = "NO-TESTS"
    MUTATION_ERROR = "MUTATION-ERROR"


#: The only outcome that may credit a claim (PLAN-0115 defect 2 — "one reddened test
#: marked ALL its claims witnessed"). Kept as a set rather than an ``== WITNESSED``
#: comparison scattered through the driver so the crediting rule has exactly one home.
CREDITING_OUTCOMES = frozenset({Outcome.WITNESSED})

#: Exception types that mean "an assertion failed", as opposed to "something blew up".
#: ``Failed`` covers both ``pytest.fail()`` and a ``pytest.raises`` block that did not
#: raise (measured: ``DID NOT RAISE`` reports as ``Failed`` at the ``with`` line, which
#: is where ``enumerate_claims`` puts the ``raises`` claim — so the sites agree).
ASSERTION_FAMILY = frozenset({"AssertionError", "Failed"})

#: ``test_shapes.py:7: AssertionError`` — the last non-empty line of a failure body.
_SITE_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?P<exc>[A-Za-z_][A-Za-z0-9_.]*)$")


@dataclass(frozen=True)
class CaseRecord:
    """One ``<testcase>`` from a junit XML report, with its failure record extracted."""

    name: str
    tag: str
    message: str
    body: str
    site_file: str | None
    site_line: int | None
    exc_type: str | None

    @property
    def is_problem(self) -> bool:
        """Whether this case failed or errored (a skip is neither a pass nor a problem)."""
        return self.tag in {"failure", "error"}

    def render_site(self) -> str:
        if self.site_file is None or self.site_line is None:
            return "<no site in the failure record>"
        return f"{self.site_file}:{self.site_line}"


@dataclass(frozen=True)
class Classification:
    """A probe's outcome plus the text that makes the RED readable.

    ``reason`` is not decoration. C6's binding rule has two halves and only the first is
    mechanical; the second — "a RED recorded as evidence must carry failure text a reader
    could act on" — is discharged by carrying the failure message and site into the
    report, which is exactly what the s253 driver threw away.
    """

    outcome: Outcome
    reason: str
    record: CaseRecord | None = None


def parse_junit(xml_text: str) -> list[CaseRecord]:
    """Every ``<testcase>`` in a junit XML report, failure record already extracted.

    Raises ``ET.ParseError`` on unparsable XML rather than returning an empty list: an
    empty list means :attr:`Outcome.NO_TESTS` ("your node id selected nothing"), and
    silently reporting that for a corrupt report would be a false negative of the kind
    this package exists to stop.
    """
    # S314: the XML is produced by our own pytest subprocess into a path we chose, never
    # untrusted input. defusedxml is not a project dependency and adding one for a
    # first-party artifact would be cargo.
    root = ET.fromstring(xml_text)  # noqa: S314
    records: list[CaseRecord] = []
    for case in root.iter("testcase"):
        children = list(case)
        if not children:
            records.append(
                CaseRecord(
                    name=case.get("name") or "<unnamed>",
                    tag="passed",
                    message="",
                    body="",
                    site_file=None,
                    site_line=None,
                    exc_type=None,
                )
            )
            continue
        for child in children:
            body = (child.text or "").strip()
            site_file, site_line, exc_type = _parse_site(body)
            records.append(
                CaseRecord(
                    name=case.get("name") or "<unnamed>",
                    tag=child.tag,
                    message=child.get("message") or "",
                    body=body,
                    site_file=site_file,
                    site_line=site_line,
                    exc_type=exc_type,
                )
            )
    return records


def _parse_site(body: str) -> tuple[str | None, int | None, str | None]:
    """Pull ``(file, line, exception type)`` out of a failure body's last non-empty line."""
    lines = [line for line in body.splitlines() if line.strip()]
    if not lines:
        return None, None, None
    match = _SITE_RE.match(lines[-1].strip())
    if match is None:
        return None, None, None
    return match["file"], int(match["line"]), match["exc"]


def _same_file(site_file: str, claim_path: Path, project_root: Path) -> bool:
    """Whether a failure record's file refers to ``claim_path``.

    pytest reports the path relative to its rootdir, so resolve against the project root
    first. Falls back to comparing file names, which is what a battery run from a
    different working directory leaves us with.
    """
    try:
        resolved = (project_root / site_file).resolve()
        if resolved == claim_path.resolve():
            return True
    except OSError:  # pragma: no cover - resolve() on a hostile path
        pass
    return Path(site_file).name == claim_path.name


def classify(
    cases: list[CaseRecord],
    declared: Claim,
    claim_path: Path,
    project_root: Path,
) -> Classification:
    """Decide what a probe run proved about its **declared** claim.

    The order below is load-bearing. A non-assertion exception is a crash wherever it
    lands, so it is tested before the site: reporting "reddened the wrong assertion"
    about an ``AttributeError`` would name the wrong defect for the author to fix.
    """
    if not cases:
        return Classification(
            Outcome.NO_TESTS,
            "the node id selected no tests — nothing ran, so nothing was witnessed",
        )

    errors = [c for c in cases if c.tag == "error"]
    if errors:
        first = errors[0]
        return Classification(
            Outcome.SETUP_ERROR,
            f"collection/setup/teardown error in {first.name}: {first.message} "
            f"({first.render_site()})",
            first,
        )

    problems = [c for c in cases if c.is_problem]
    if not problems:
        skipped = [c for c in cases if c.tag == "skipped"]
        if skipped and len(skipped) == len(cases):
            return Classification(
                Outcome.SKIPPED,
                f"every selected test was skipped: {skipped[0].message}",
                skipped[0],
            )
        return Classification(
            Outcome.GREEN,
            "the mutation reached disk and nothing reddened — the claim is NOT witnessed, "
            "and the guard may be vacuous",
        )

    if len(problems) > 1:
        sites = ", ".join(f"{c.name} @ {c.render_site()}" for c in problems)
        return Classification(
            Outcome.MISFIRE,
            f"{len(problems)} tests failed, so this mutation's blast radius is wider than "
            f"one assertion; a probe credits a claim only when exactly one reddened "
            f"(one-mutation-one-assertion). Failing: {sites}",
            problems[0],
        )

    failure = problems[0]

    if failure.exc_type is None or failure.site_line is None or failure.site_file is None:
        return Classification(
            Outcome.UNREADABLE,
            "the failure record names no site, so it cannot show the declared assertion "
            f"failing at its own site (C6). Raw message: {failure.message!r}",
            failure,
        )

    if failure.exc_type not in ASSERTION_FAMILY:
        return Classification(
            Outcome.CRASHED,
            f"{failure.exc_type} at {failure.render_site()} is not an assertion failing — "
            f"it is the mutation breaking something else. Message: {failure.message!r}",
            failure,
        )

    if not _same_file(failure.site_file, claim_path, project_root):
        return Classification(
            Outcome.MISFIRE,
            f"the assertion that failed lives in {failure.site_file}, but the declared "
            f"claim is in {claim_path.name}",
            failure,
        )

    if failure.site_line != declared.lineno:
        return Classification(
            Outcome.MISFIRE,
            f"an assertion failed at line {failure.site_line}, but the declared claim "
            f"{declared.stable_key!r} is at line {declared.lineno}. Crediting it would let "
            f"the result rewrite the prediction. Message: {failure.message!r}",
            failure,
        )

    return Classification(
        Outcome.WITNESSED,
        f"{failure.exc_type} at {failure.render_site()} — the declared assertion failed at "
        f"its own site. Message: {failure.message!r}",
        failure,
    )
