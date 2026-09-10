"""The one writer for the evidence files a goal's ``check`` leaves behind.

**Why this is a shared module and not a helper copied into each instrument.**
PLAN-0123 clause R2 says a check's stdout never reaches the ``goal-evaluator`` —
only its exit code becomes a state — so the numbers a check measured have to be
written to a file the judge reads. That file's shape is therefore a *contract
between programs*: the instrument writes it, a subagent parses it, and neither
can see the other. Two instruments each carrying their own copy of the format is
precisely how the two halves drift apart while both keep passing their own tests
— the s288 defect in miniature, where one table was filled from two instruments
that disagreed about what they were counting.

**The format**, stable and deliberately dull::

    key=value            <- header, one per line, in the order given
    key=value
    ---                  <- the separator; everything after it is the report
    <the report, byte-identical to what the instrument printed>

Clause R7 requires the header to carry the goal id and the HEAD sha at the time
of writing; the judge compares that sha to the goal's ``declared_head`` and
reports a mismatch as a finding rather than a pass. Which keys beyond those an
instrument adds is its own business — the driver stamps ``run_id`` and
``battery_sha256``, an instrument stamps its own name — so the header is passed
in rather than assembled here.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from pathlib import Path

#: Everything after this line is the report body, byte-for-byte as printed.
#: A judge splits on the FIRST occurrence, so a report that happens to contain
#: the separator cannot truncate its own evidence.
SEPARATOR = "---"

#: The verdict vocabulary, shared so that no two instruments can disagree about
#: what a number means. PLAN-0123 §4.6: *a verdict computed twice drifts once* —
#: error #13 was a shell ``!`` inversion that made a report's printed verdict and
#: its exit status say opposite things. There is therefore exactly one mapping
#: from exit status to token, and :func:`verdict_line` is the only thing that
#: renders it.
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_REFUSED = 2

VERDICT_BY_EXIT = {EXIT_PASS: "PASS", EXIT_FAIL: "FAIL", EXIT_REFUSED: "REFUSED"}


def verdict_line(status: int) -> str:
    """The final line every instrument prints, derived from the exit status.

    The status is the ONE value: pass it here and return it from ``main``, and
    the printed verdict cannot disagree with what the caller's ``$?`` sees. An
    unmapped status renders as ``REFUSED`` rather than raising — an instrument
    that has already taken its measurement should report an unexpected status,
    not lose the reading to a KeyError.
    """
    return f"VERDICT: {VERDICT_BY_EXIT.get(status, 'REFUSED')} exit={status}"


#: What ``head_sha`` returns when it cannot ask git. Deliberately a value and
#: not an empty string or a missing line: the judge can see and report
#: ``head=unknown``, whereas an absent header line is indistinguishable from an
#: older writer that never stamped one.
UNKNOWN_HEAD = "unknown"


def head_sha(cwd: Path | None = None) -> str:
    """Best-effort ``git rev-parse HEAD``; :data:`UNKNOWN_HEAD` if git cannot answer.

    Best-effort rather than fatal because an instrument's job is to take the
    measurement. A reading that refused because the provenance stamp was
    unavailable would trade a diagnosable finding for no reading at all.
    """
    try:
        proc = subprocess.run(  # noqa: S603 — fixed git argv, no shell
            ["git", "rev-parse", "HEAD"],  # noqa: S607 — PATH-resolved git intended
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(cwd) if cwd is not None else None,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return UNKNOWN_HEAD
    sha = proc.stdout.strip()
    return sha if proc.returncode == 0 and sha else UNKNOWN_HEAD


def render_evidence(report: str, header: Mapping[str, str]) -> str:
    """The full evidence-file text: header, separator, then the report verbatim.

    ``report`` is not reformatted, re-wrapped or trimmed. The file and the
    terminal telling two stories is how a number nobody took becomes a number
    somebody quoted, so the body is exactly what was printed.
    """
    lines = [f"{key}={value}" for key, value in header.items()]
    lines.append(SEPARATOR)
    return "\n".join(lines) + "\n" + report.rstrip("\n") + "\n"


def write_evidence(report: str, destination: Path, header: Mapping[str, str]) -> None:
    """Write the evidence file, creating its ``goal-evidence/<gid>/`` directory."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_evidence(report, header), encoding="utf-8")


def split_evidence(text: str) -> tuple[dict[str, str], str]:
    """Parse an evidence file back into ``(header, body)``.

    Shipped beside the writer on purpose: a reader living somewhere else is a
    second implementation of the format, which is the thing this module exists
    to prevent. A file with no separator yields an empty header and the whole
    text as the body — the shape a judge should report as unstamped, not the
    shape it should crash on.
    """
    head, sep, body = text.partition("\n" + SEPARATOR + "\n")
    if not sep:
        return {}, text
    header: dict[str, str] = {}
    for line in head.splitlines():
        key, eq, value = line.partition("=")
        if eq:
            header[key.strip()] = value.strip()
    return header, body
