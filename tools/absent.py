#!/usr/bin/env python
"""Measure an ABSENCE with a control that could have failed, and print the values.

🔴 **The measured failure this replaces.** CLAUDE.md §8 states the rule plainly —
*a zero or absence needs a positive control that finds a known one* — and three of
the sixteen instrument errors PLAN-0123 §1.2 catalogues are absence or window
readings that had no such control:

* a ``grep`` whose needle could not have matched anything, reported as *"not
  present"* rather than as *"this instrument found nothing, including things I
  know are there"*;
* a ``pgrep`` that matched **its own command line**, so the process was reported
  running when nothing but the check itself was;
* a reading taken through a **window** (a tail, a date range, a single directory)
  and then quoted as a statement about the whole population.

An empty result is the one reading that looks identical whether the instrument
worked or not. ``grep -c`` prints ``0`` for *"the pattern is absent"* and ``0``
for *"I was pointed at the wrong file"*, and nothing in the output distinguishes
them.

**The rule this makes mechanical.** An absence reading may be quoted only when

1. every line of the subject was **consumed** — ``consumed == lines``, the two
   counted independently, so a truncated scan cannot masquerade as a complete one;
2. the **control** pattern — something the author knows IS there — was found
   (``control_hits >= 1``); a control that finds nothing invalidates the reading
   and exits ``2``, which is neither *absent* nor *present*; and
3. the instrument **cannot match itself** — its own pid and any process whose
   command line names this file are excluded and counted separately.

All four numbers are printed as values, never as a bare verdict (§8: *a
verification report prints the values it measured*), and the final ``VERDICT:``
token and the exit status are derived from **one** variable (PLAN-0123 §4.6 —
a verdict computed twice drifts once).

**Scope, so a green is not over-read.** This proves the pattern is absent from
the bytes it read, with an instrument shown to be capable of finding something.
It does not know whether the subject is the right subject, whether the pattern
expresses the claim, or whether the control sits **outside** the window the
original ad-hoc reading used (contract clause R3 — that placement is the goal
author's, and the judge's to refuse). Those stay yours.

Usage::

    python tools/absent.py --file .claude/state/stop-classifier-log.jsonl \\
        --pattern '"decision": "block"' --control '"decision":'

    python tools/absent.py --proc --pattern 'ollama serve' --control 'python'

    python tools/absent.py --file LOG --pattern PAT --control PAT \\
        --report-to .claude/state/goal-evidence/<gid>/C1.txt --gid <gid>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - `python tools/absent.py`, not `-m`
    # Both invocation forms have to work. A goal's `check` cmd is written by
    # hand as often as it is rendered, and an instrument that only runs one way
    # is an instrument someone will invoke the other way and read the
    # ImportError as "no hits".
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._evidence import (
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_REFUSED,
    head_sha,
    verdict_line,
    write_evidence,
)

#: Exit status is the ONE value the verdict token is derived from (§4.6). The
#: numbers come from the shared vocabulary so that ``0`` means the same thing
#: here as it does in every other instrument a goal can call; the local names
#: exist because ``EXIT_ABSENT`` says what the reading found and ``EXIT_PASS``
#: only says how it scored.
EXIT_ABSENT = EXIT_PASS
EXIT_PRESENT = EXIT_FAIL
EXIT_CONTROL_FAILED = EXIT_REFUSED

#: Any process whose command line names this file is the instrument observing
#: itself. Kept as a module constant so the self-exclusion has one definition
#: and a probe that removes it removes it everywhere (AC-4 P4c).
_SELF_MARKER = "absent.py"


@dataclass(frozen=True)
class Reading:
    """An absence measurement plus everything needed to decide whether to believe it."""

    subject: str
    pattern: str
    control: str
    lines: int
    consumed: int
    matched: int
    control_hits: int
    self_excluded: int

    @property
    def complete(self) -> bool:
        """Every line of the subject was examined.

        ``lines`` and ``consumed`` are derived by **two separate passes over the
        subject**, and that is the entire point. Were both incremented by the
        same loop the equality would be an identity — a scan that stopped early
        would decrement both, the assertion could never fail, and dead defensive
        code invites the reader to believe a check is happening (§8; the
        ``tally.py`` docstring makes the same argument about its own counters).

        Two passes can genuinely disagree, and each way it happens is worth
        knowing: a scan bounded to a window (error #10 — a value read through a
        tail and then quoted about the whole population), or a subject that
        **changed under the instrument** between the passes. The second is not
        hypothetical for this repo: ``.claude/state/*.jsonl`` are appended to by
        hooks while a reading is being taken, and an absence measured against a
        moving target is not an absence.
        """
        return self.consumed == self.lines

    @property
    def control_held(self) -> bool:
        """The instrument found something it was told is there.

        A negative measurement with no positive control is vacuous — *"absent
        from the list"* is satisfied by an empty list (CLAUDE.md §8).
        """
        return self.control_hits >= 1


def _exit_status(reading: Reading) -> int:
    """The single value both the verdict token and the process exit derive from.

    Precedence is deliberate and matches AC-4: a failed control outranks the
    absence question entirely. When the instrument cannot demonstrate it could
    have found anything, ``matched`` carries no information — reporting
    ``PASS`` there would be the exact failure this tool exists to prevent, and
    reporting ``FAIL`` would invent a presence nobody measured.

    ⚠️ **An incomplete scan is reported but does NOT change the exit status**,
    because AC-4 fixes ``exit == 2`` **iff** ``control_hits == 0``: the exit
    codes stay a one-to-one map onto the control question, and completeness is
    asserted separately (AC-4 A1, witnessed by probe P4a). Folding it in here
    would make two distinct defects share one code and would break the ``iff``
    the acceptance criterion was pre-committed on. **This leaves a real hole** —
    a windowed scan whose control happens to sit inside the window reads
    ``PASS`` — and it is recorded as a finding against AC-4 rather than closed
    by widening the criterion after the fact.
    """
    if not reading.control_held:
        return EXIT_CONTROL_FAILED
    return EXIT_ABSENT if reading.matched == 0 else EXIT_PRESENT


def scan_file(path: Path, pattern: str, control: str) -> Reading:
    """Scan every line of ``path`` for ``pattern`` and for the ``control``.

    Both counts come from the same pass, so the control is exposed to exactly
    the failure the reading is (clause R3): if the file is the wrong file,
    unreadable in this encoding, or shorter than the author believed, the
    control goes to zero and the reading refuses instead of returning a
    confident ``0``.
    """
    # Pass 1 — how many lines the subject HAS. Deliberately not the same
    # iteration the scan uses; see ``Reading.complete`` for why one loop
    # counting both would make the completeness assertion unfailable.
    with path.open(encoding="utf-8", errors="replace") as handle:
        lines = sum(1 for _ in handle)

    # Pass 2 — the scan. Both counts come from this one pass, so the control is
    # exposed to exactly the failure the reading is (clause R3).
    pattern_re = re.compile(pattern)
    control_re = re.compile(control)
    consumed = matched = control_hits = 0

    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            consumed += 1
            if pattern_re.search(line):
                matched += 1
            if control_re.search(line):
                control_hits += 1

    return Reading(
        subject=str(path),
        pattern=pattern,
        control=control,
        lines=lines,
        consumed=consumed,
        matched=matched,
        control_hits=control_hits,
        self_excluded=0,
    )


def read_process_table() -> list[tuple[int, str]]:
    """``(pid, cmdline)`` for every process, read from ``/proc``.

    ``/proc`` rather than ``ps`` because the repo already reads command lines
    this way (``tools/probe_battery/_snapshot.py``) and because shelling out to
    ``ps`` would put a second exit status between the reading and the verdict.

    ⚠️ On a host with no ``/proc`` — a Windows-side interpreter, most obviously —
    this returns an **empty list**, and an empty table is exactly the shape that
    makes every process look absent. Nothing here tries to detect that: the
    control does. A control naming a process the author knows is running reads
    ``control_hits=0`` on an empty table and the reading REFUSES.
    """
    entries: list[tuple[int, str]] = []
    proc = Path("/proc")
    if not proc.is_dir():
        return entries
    for child in sorted(proc.iterdir()):
        if not child.name.isdigit():
            continue
        try:
            raw = (child / "cmdline").read_bytes()
        except OSError:
            # The process exited between listing and reading. Not an error, and
            # not silently dropped either — it is simply no longer in the table
            # the reading describes.
            continue
        cmdline = raw.replace(b"\0", b" ").decode("utf-8", "replace").strip()
        entries.append((int(child.name), cmdline))
    return entries


def parse_process_table(text: str) -> list[tuple[int, str]]:
    """Parse a planted process table: one ``<pid>\\t<cmdline>`` per line.

    This is what ``--proc-source`` reads. A test cannot plant entries in the
    real ``/proc``, and a ``--proc`` mode that could only ever be exercised
    against the live table would be a mode no probe could redden.
    """
    entries: list[tuple[int, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        pid_text, _, cmdline = line.partition("\t")
        try:
            pid = int(pid_text.strip())
        except ValueError:
            continue
        entries.append((pid, cmdline.strip()))
    return entries


def scan_processes(
    entries: list[tuple[int, str]], pattern: str, control: str, *, own_pid: int
) -> Reading:
    """Scan a process table, excluding the instrument's own footprint.

    A self-match is counted, not skipped — ``self_excluded`` says how many
    entries were withheld and why the totals differ. A skipped record is the
    mechanism by which a reading quietly stops describing its input (the
    ``tally.py`` lesson): the sum still looks tidy because the denominator
    shrank with it.

    Exclusion covers **both** the pattern and the control. A control satisfied
    only by this process would be a control that cannot fail, which is clause
    R3's whole prohibition.
    """
    lines = len(entries)
    pattern_re = re.compile(pattern)
    control_re = re.compile(control)
    consumed = matched = control_hits = self_excluded = 0

    for pid, cmdline in entries:
        consumed += 1
        if pid == own_pid or _SELF_MARKER in cmdline:
            self_excluded += 1
            continue
        if pattern_re.search(cmdline):
            matched += 1
        if control_re.search(cmdline):
            control_hits += 1

    return Reading(
        subject="<process table>",
        pattern=pattern,
        control=control,
        lines=lines,
        consumed=consumed,
        matched=matched,
        control_hits=control_hits,
        self_excluded=self_excluded,
    )


def render(reading: Reading) -> tuple[str, int]:
    """The report, and the exit status. Both derive from ``_exit_status``."""
    status = _exit_status(reading)
    lines = [
        f"subject: {reading.subject}",
        f"pattern: {reading.pattern!r}   control: {reading.control!r}",
        "",
        f"  lines={reading.lines} consumed={reading.consumed} "
        f"matched={reading.matched} control_hits={reading.control_hits} "
        f"self_excluded={reading.self_excluded}",
        "",
    ]

    if not reading.complete:
        lines.append(
            f"🔴 INCOMPLETE SCAN — consumed {reading.consumed} of {reading.lines} lines. "
            "This reading describes a window, not the subject, and an absence measured "
            "through a window is not an absence."
        )
    if not reading.control_held:
        lines.append(
            "🔴 CONTROL FOUND NOTHING — the instrument cannot demonstrate it would have "
            "found the pattern had the pattern been there, so `matched=0` carries no "
            "information. Point the control at something you know is present, OUTSIDE "
            "any window the original reading used."
        )
    if status == EXIT_PRESENT:
        lines.append(
            f"the pattern is PRESENT ({reading.matched} match(es)) — the absence claim "
            "is refuted, which is the instrument working."
        )

    lines.append("")
    lines.append(verdict_line(status))
    return "\n".join(lines), status


def write_report(report: str, destination: Path, gid: str) -> None:
    """Write the evidence file clause R2 requires, with clause R7's header.

    stdout never reaches the ``goal-evaluator`` — only a check's exit code
    becomes a state — so a number that existed only in a captured stdout is a
    number nobody took. The body below the header is byte-identical to what was
    printed, so the file and the terminal cannot tell two stories.
    """
    write_evidence(
        report,
        destination,
        {
            "gid": gid or "unset",
            "head": head_sha(),
            "instrument": _SELF_MARKER,
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="absent",
        description="Measure an absence with a control that could have failed.",
    )
    subject = parser.add_mutually_exclusive_group(required=True)
    subject.add_argument("--file", type=Path, help="the file the pattern should be absent from")
    subject.add_argument(
        "--proc", action="store_true", help="read the process table instead of a file"
    )
    parser.add_argument(
        "--proc-source",
        type=Path,
        default=None,
        help="read the process table from this file (`<pid>\\t<cmdline>` per line) "
        "instead of /proc — how a test plants a table",
    )
    parser.add_argument("--pattern", required=True, help="the pattern claimed to be ABSENT")
    parser.add_argument(
        "--control",
        required=True,
        help=(
            "a pattern you know IS present — the positive control. Required, not "
            "optional: an absence reading without one is vacuous (CLAUDE.md §8), and "
            "an optional control is a control nobody supplies under time pressure."
        ),
    )
    parser.add_argument(
        "--report-to",
        type=Path,
        default=None,
        help="write the evidence file here (clause R2) as well as to stdout",
    )
    parser.add_argument("--gid", default="", help="goal id stamped into the report header (R7)")
    args = parser.parse_args(argv)

    # Compile both patterns before touching the subject. A bad regex must refuse
    # up front, never surface as an exception mid-scan whose traceback a caller
    # could read as "found nothing".
    for label, expression in (("pattern", args.pattern), ("control", args.control)):
        try:
            re.compile(expression)
        except re.error as exc:
            print(f"absent: --{label} is not a valid regex: {exc}", file=sys.stderr)
            return EXIT_CONTROL_FAILED

    if args.proc:
        if args.proc_source is not None:
            if not args.proc_source.is_file():
                print(f"absent: no such process table: {args.proc_source}", file=sys.stderr)
                return EXIT_CONTROL_FAILED
            entries = parse_process_table(
                args.proc_source.read_text(encoding="utf-8", errors="replace")
            )
        else:
            entries = read_process_table()
        reading = scan_processes(entries, args.pattern, args.control, own_pid=os.getpid())
    else:
        if not args.file.is_file():
            print(f"absent: no such file: {args.file}", file=sys.stderr)
            return EXIT_CONTROL_FAILED
        reading = scan_file(args.file, args.pattern, args.control)

    report, status = render(reading)
    print(report)
    if args.report_to is not None:
        write_report(report, args.report_to, args.gid)
    return status


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main(sys.argv[1:]))
