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

    A tenth was added by PLAN-0121, under the same rule and for the same reason:

    - :attr:`ABORTED` — the child pytest ended **before reaching a verdict** for the
      selected node, so its report is not an account of what ran. Measured (s277): a
      session calling ``pytest.exit(reason, returncode=75)`` from a test *body* emits one
      childless, **unnamed** ``<testcase>`` while ``testsuite@tests`` still reads ``"0"``,
      and the pre-0121 classifier read that as :attr:`GREEN` **with the same reason string
      as a real green** — i.e. it published an infrastructure event as *"the guard may be
      vacuous"*, sending a reader to strengthen a guard that is fine. From an autouse
      *fixture* the same call emits no ``<testcase>`` at all and read as :attr:`NO_TESTS`.
      Folding either into :attr:`SETUP_ERROR` would say "collection or fixture error",
      which a reader chases in the test module, and would conflate a legible ``<error>``
      record with the *absence* of one. The outcome names only what the instrument can
      see — "ended without a verdict" — never *why*; the cause travels in the reason, as
      the child's own last line.
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
    ABORTED = "ABORTED"


#: The only outcome that may credit a claim (PLAN-0115 defect 2 — "one reddened test
#: marked ALL its claims witnessed"). Kept as a set rather than an ``== WITNESSED``
#: comparison scattered through the driver so the crediting rule has exactly one home.
#: :attr:`Outcome.ABORTED` is deliberately **not** here: a cut-off child proves nothing
#: about the guard, so it must never credit. PLAN-0121 §2.2 depends on this line not
#: changing.
CREDITING_OUTCOMES = frozenset({Outcome.WITNESSED})

#: The exit codes under which pytest's report is a **complete account of what ran**: all
#: passed, some failed, nothing collected. Every other code — ``2`` interrupted, ``3``
#: internal error, ``4`` usage error, any user-supplied ``pytest.exit(returncode=N)``, a
#: negative code from a signal — means the session ended before the report can be trusted.
#:
#: 🔴 **The asymmetry that keeps this inside PLAN-0115's founding refusal.** That refusal
#: is *"outcome comes from pytest's junit failure record, never an exit code"*, and it
#: exists because s253 keyed on ``returncode`` and counted a crash as a witnessed RED. The
#: code is consulted here in exactly one situation — when the record would **otherwise
#: read clean** — and its only power is to *downgrade* that reading. An exit code can
#: withhold evidence; it can never supply it. The s253 channel stays closed.
#:
#: Kept as integer literals rather than importing ``pytest.ExitCode`` so ``tools/`` takes
#: no test-framework dependency; ``tests/tools/test_probe_battery_contention.py`` pins the
#: set against ``pytest.ExitCode`` from the test side (PLAN-0121 AC-2b).
VERDICT_EXIT_CODES = frozenset({0, 1, 5})

#: How much of the child's merged stdout+stderr :class:`RunRecord` carries. The cause of a
#: cut-off run is in its **last** line (measured, s277), so the tail is what matters.
#: Consumed by ``_battery._run`` (PLAN-0121 Step 2), which does the truncation; it is
#: declared here because it is part of :class:`RunRecord`'s contract, not the spawner's.
STDOUT_TAIL_BYTES = 4096

#: The name :func:`parse_junit` gives a ``<testcase>`` that carries no ``name`` attribute.
UNNAMED_CASE = "<unnamed>"

#: The opening clause of an :attr:`Outcome.ABORTED` reason, one per defence layer. They
#: differ so a reader — and a probe — can tell **which** layer decided; see
#: :func:`_abort_reason` for why that is a correctness requirement and not a nicety.
ABORT_LEAD_EXIT_CODE = "pytest exited without reaching a verdict"
ABORT_LEAD_SHAPE = (
    "the report carries an unnamed, childless <testcase> — the shape pytest leaves when a "
    "session is cut off, and no exit code contradicts it — so no verdict was reached"
)

#: Exception types that mean "an assertion failed", as opposed to "something blew up".
#: ``Failed`` covers both ``pytest.fail()`` and a ``pytest.raises`` block that did not
#: raise (measured: ``DID NOT RAISE`` reports as ``Failed`` at the ``with`` line, which
#: is where ``enumerate_claims`` puts the ``raises`` claim — so the sites agree).
ASSERTION_FAMILY = frozenset({"AssertionError", "Failed"})

#: ``test_shapes.py:7: AssertionError`` — the last non-empty line of a failure body.
_SITE_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?P<exc>[A-Za-z_][A-Za-z0-9_.]*)$")


@dataclass(frozen=True)
class RunRecord:
    """Everything one probe's child pytest left behind — the classifier's raw input.

    Before PLAN-0121 the runner returned the junit text alone and dropped both
    ``proc.returncode`` and the captured output (``_battery.py:391``), so a session that
    was cut off before reaching a verdict was indistinguishable from one that ran clean.
    The cause of the s277 contention existed in exactly one place — the child's stdout —
    and that was the value being discarded.

    ``xml_text is None`` means pytest produced no report at all; ``returncode is None``
    means there was no code to read (the child was killed at the timeout).
    """

    xml_text: str | None
    returncode: int | None
    stdout_tail: str


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

    ``tag`` is ``"failure"`` / ``"error"`` / ``"skipped"`` straight from the child element,
    ``"passed"`` for a childless **named** case, and ``"unreported"`` for a childless case
    with **no name** — the shape a cut-off session leaves behind (PLAN-0121).
    """
    # S314: the XML is produced by our own pytest subprocess into a path we chose, never
    # untrusted input. defusedxml is not a project dependency and adding one for a
    # first-party artifact would be cargo.
    root = ET.fromstring(xml_text)  # noqa: S314
    records: list[CaseRecord] = []
    for case in root.iter("testcase"):
        children = list(case)
        if not children:
            name = case.get("name")
            records.append(
                CaseRecord(
                    # A childless ``<testcase>`` normally means "this test passed". One
                    # with **no name** does not: measured (s277), that is the element
                    # pytest emits for a session cut off mid-body, and calling it
                    # ``"passed"`` is what let a contended run publish as GREEN. The tag
                    # is the rc-independent half of PLAN-0121's defence — it catches a
                    # ``pytest.exit(returncode=0)`` and an injected runner that carries
                    # no exit code at all.
                    name=name or UNNAMED_CASE,
                    tag="passed" if name else "unreported",
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
                    name=case.get("name") or UNNAMED_CASE,
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


def last_nonempty_line(text: str) -> str:
    """The child's own last word — the one place a cut-off run says why it stopped.

    Measured (s277): a ``pytest.exit(reason, returncode=75)`` prints
    ``! _pytest.outcomes.Exit: <reason> !`` as the final line of stdout and puts it
    **nowhere** in the junit XML. Shared by the :attr:`Outcome.ABORTED` reason and, from
    :mod:`tools.probe_battery._battery`, by the no-report :attr:`Outcome.SETUP_ERROR`
    reason, so both name their cause the same way.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _abort_reason(
    cases: list[CaseRecord],
    declared: Claim,
    returncode: int | None,
    stdout_tail: str,
    lead: str,
) -> str:
    """The one reason shape both abort layers produce — values first, then the cause.

    ``lead`` names **which layer decided**, and that is load-bearing rather than
    cosmetic. Both layers return :attr:`Outcome.ABORTED` and both print the same measured
    values, so without a distinguishing lead a probe that disables layer 1 on a body-phase
    abort would still read ``ABORTED`` — layer 2 catches the same report — and the probe
    would report a green for a mutation that did reach disk and did change behaviour. An
    instrument whose two paths are indistinguishable in its own output cannot be probed
    one claim at a time (CLAUDE.md §8).
    """
    rc = returncode if returncode is not None else "-"
    unnamed = sum(1 for case in cases if case.name == UNNAMED_CASE)
    tail = last_nonempty_line(stdout_tail)
    said = f" Child said: {tail!r}" if tail else " The child left nothing on stdout."
    return (
        f"{lead} for {declared.stable_key!r} — "
        f"rc={rc}, {len(cases)} testcase(s) in the report, {unnamed} without a name; the "
        f"run was cut off, so nothing here is evidence about the guard.{said}"
    )


def _classify_abort(
    cases: list[CaseRecord],
    declared: Claim,
    returncode: int | None,
    stdout_tail: str,
) -> Classification | None:
    """Whether a would-be-clean report came from a session that never reached a verdict.

    Two layers, in this order, because they are not equally trustworthy:

    1. **The exit code** — the verdict source. General: it catches an interrupt, an
       internal error, a usage error and any ``pytest.exit(returncode=N)`` alike.
    2. **The report's shape** — a childless ``<testcase>`` with no ``name``. This is a
       pytest implementation detail and therefore the weaker signal, so it never outranks
       layer 1; it exists for the two cases layer 1 cannot see: a
       ``pytest.exit(returncode=0)`` and an injected runner that carries no code at all.
       ``tests/tools/test_probe_battery_contention.py``'s drift detector is what makes it
       loud if a future pytest starts naming these.

    Returns ``None`` when the report is a real account of what ran.
    """
    if returncode is not None and returncode not in VERDICT_EXIT_CODES:
        return Classification(
            Outcome.ABORTED,
            _abort_reason(cases, declared, returncode, stdout_tail, ABORT_LEAD_EXIT_CODE),
        )
    if any(case.tag == "unreported" for case in cases):
        return Classification(
            Outcome.ABORTED,
            _abort_reason(cases, declared, returncode, stdout_tail, ABORT_LEAD_SHAPE),
        )
    return None


def _classify_clean(
    cases: list[CaseRecord],
    declared: Claim,
    returncode: int | None,
    stdout_tail: str,
) -> Classification:
    """Every reading available when the report carries no failure and no error record.

    🔴 **This is the only caller of :func:`_classify_abort`, and that is the point.**
    PLAN-0121 §4.1 permits the exit code to be consulted *solely* where the report would
    otherwise read clean; routing it through this function makes that rule structural
    rather than a comment someone can drift away from. A legible ``<failure>`` or
    ``<error>`` never reaches here, so no exit code can override one.
    """
    # Asked before "nothing ran", because the fixture-phase abort measured in s277
    # produces an empty report — and answering NO-TESTS for it names the node id as the
    # problem, which is the misdiagnosis this arm exists to remove.
    aborted = _classify_abort(cases, declared, returncode, stdout_tail)
    if aborted is not None:
        return aborted

    if not cases:
        return Classification(
            Outcome.NO_TESTS,
            "the node id selected no tests — nothing ran, so nothing was witnessed",
        )

    skipped = [c for c in cases if c.tag == "skipped"]
    if skipped and len(skipped) == len(cases):
        return Classification(
            Outcome.SKIPPED,
            f"every selected test was skipped: {skipped[0].message}",
            skipped[0],
        )

    # The values are part of the reading, not decoration: before PLAN-0121 this string was
    # byte-identical for a real green and for a session cut off mid-body, and a reader had
    # no way to tell them apart (measured, s277).
    unnamed = sum(1 for case in cases if case.name == UNNAMED_CASE)
    rc = returncode if returncode is not None else "-"
    return Classification(
        Outcome.GREEN,
        "the mutation reached disk and nothing reddened — the claim is NOT witnessed, "
        f"and the guard may be vacuous (rc={rc}; {len(cases)} testcase(s), "
        f"{unnamed} without a name)",
    )


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
    *,
    returncode: int | None = None,
    stdout_tail: str = "",
) -> Classification:
    """Decide what a probe run proved about its **declared** claim.

    The order below is load-bearing. A non-assertion exception is a crash wherever it
    lands, so it is tested before the site: reporting "reddened the wrong assertion"
    about an ``AttributeError`` would name the wrong defect for the author to fix.

    ``returncode`` and ``stdout_tail`` are keyword-only and optional so every caller that
    predates PLAN-0121 stays valid. They are read on **one** path — where the report would
    otherwise read clean — and can only downgrade that reading to :attr:`Outcome.ABORTED`.
    A legible ``<failure>`` or ``<error>`` record is never overridden by an exit code: a
    RED that failed at its own site stays a witness even if the session then exited oddly.
    """
    problems = [c for c in cases if c.is_problem]
    if not problems:
        return _classify_clean(cases, declared, returncode, stdout_tail)

    errors = [c for c in cases if c.tag == "error"]
    if errors:
        first = errors[0]
        return Classification(
            Outcome.SETUP_ERROR,
            f"collection/setup/teardown error in {first.name}: {first.message} "
            f"({first.render_site()})",
            first,
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
