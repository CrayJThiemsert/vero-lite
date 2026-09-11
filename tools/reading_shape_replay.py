#!/usr/bin/env python3
"""Replay the reading-shape detector over a transcript corpus (PLAN-0123 AC-9).

**Why this tool exists before the hook it justifies.** PLAN-0123 §4.5 proposes a
third advisory in ``posttooluse_progress_observer._handle_bash``: when a Bash
command has the shape of *taking a reading* and no goal is active, print a nudge
carrying a pre-filled ``tools/goal_template.py`` command. An advisory that fires
on ordinary work is noise that trains the agent to ignore it, so §4.5 fixes a
kill criterion **before** any replay is run and this module measures it. The
numbers are read against §4.5 as written. **Failing the read is a finding, not a
reason to edit the read** — a fail strikes AC-10 and the advisory does not ship.

The classification rubric, quoted from §4.5
-------------------------------------------
Replay corpus: the main-session transcripts of **s287, s288 and s289**, of which
s287 and s289 are out of sample for a predicate written from s288. The report
prints ``corpus_calls=N raw_matches=M (p %) deduped_fires=F valid=V misfire=X
reachable=k/3``. **Ship iff all three hold:**

1. ``k == 3`` — positive control, credits nothing;
2. **raw predicate match rate ``p < 5 %``** of all Bash calls — measured *before*
   dedup, because once-per-session-per-shape would make any ceiling on deduped
   fires near-vacuous (three sessions x seven shapes bounds ``F`` at 21
   regardless of how noisy the predicate is);
3. **``X <= V``** on the deduped fires, hand-classified from the transcript with
   the class fixed here: a fire is *valid* iff the command's output was quoted as
   a number or an absence claim in the same or the next assistant turn, else a
   *misfire*.

Decisions this module pre-commits, so the numbers cannot be tuned after the fact
-------------------------------------------------------------------------------
*The detector reads the WHOLE command string.* The real hook receives
``tool_input["command"]`` entire, so a 671-character compound one-liner whose
tenth clause counts something is one match, not zero. This is the faithful
mirror and it is the single choice that most inflates ``p``; it is made here,
before any corpus number is known, precisely because it is the tempting one to
revisit afterwards.

*The denominator is every ``Bash`` tool_use in the corpus transcripts.* Measured
rather than assumed: all three transcripts carry ``isSidechain=False`` on every
record, so no subagent call is in or out by judgment — there are none. This
matters because :func:`_loop_counter.main_session_id` returns ``None`` for a
subagent payload, which would otherwise have made the dedup key ambiguous.

*Dedup fires on the FIRST unseen shape and marks only that one seen.* The hook
prints one JSON object per Bash call and its reason names one shape; a command
matching three shapes cannot honestly be counted as three nudges the agent saw.
The shapes it did not name stay unseen and may fire later.

*``reachable`` is measured on a planted fixture, never on the corpus.* §4.5 is
explicit that a detector written from three commands matches them in sample and
that this **credits nothing**. It is here to prove the detector is not dead.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct-script bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._evidence import (
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_REFUSED,
    head_sha,
    verdict_line,
    write_evidence,
)

# --------------------------------------------------------------------------
# The predicate. Seven shapes, exactly the seven §4.5 names.
# --------------------------------------------------------------------------

#: A ``grep`` invocation and its argument run, stopping at the first shell
#: separator so a later clause's flags are not attributed to this one. ``git
#: grep`` and ``zgrep`` are the same reading.
_GREP_SEGMENT_RE = re.compile(r"\b(?:git\s+)?z?grep\b([^|;&><\n]*)")

#: ``wc`` carrying a short ``-l``. Covers ``wc -l file`` and ``wc -l < file``.
_WC_L_RE = re.compile(r"\bwc\b[^|;&><\n]*?\s-[A-Za-z]*l\b")

#: Any ``pgrep`` — census error #10 is the whole shape.
_PGREP_RE = re.compile(r"\bpgrep\b")

#: ``sed -n`` piped directly into a grep: census error #8's shape. The window
#: must not cross a pipe, so the ``sed`` and the ``grep`` are the same stage.
_SED_N_GREP_RE = re.compile(r"\bsed\s+-n\b[^|\n]*\|\s*(?:git\s+)?z?grep\b")

#: A pipe into a truncator. Deliberately the same shape the shell-hygiene
#: advisory already matches on (``_PIPE_TO_TRUNCATOR_RE``): §4.5 measures this
#: predicate's ceiling against that advisory's own 30.8 % firing rate.
_PIPE_HEAD_RE = re.compile(r"\|\s*head\b")
_PIPE_TAIL_RE = re.compile(r"\|\s*tail\b")

#: Order matters: it fixes which shape a multi-shape command fires on.
SHAPE_ORDER: tuple[str, ...] = (
    "grep_c",
    "grep_L",
    "sed_n_grep",
    "wc_l",
    "pgrep",
    "pipe_head",
    "pipe_tail",
)


def _grep_carries_short_flag(command: str, flag: str) -> bool:
    """Does any ``grep`` in *command* carry short option *flag*?

    Flags are read per-token so that ``grep -c -i``, ``grep -rc`` and
    ``grep -ci`` all count, while ``--color`` (a long option that happens to
    contain the letter) does not. Case matters: ``-c`` counts lines, ``-L``
    lists files without a match, and they are separate shapes.
    """
    for match in _GREP_SEGMENT_RE.finditer(command):
        for token in match.group(1).split():
            if token.startswith("--") or not token.startswith("-"):
                continue
            if flag in token[1:]:
                return True
    return False


def reading_shapes(command: str) -> tuple[str, ...]:
    """The detector, as a pure function: which reading shapes *command* matches.

    Pure by construction — no clock, no filesystem, no goal lookup. The second
    conjunct of §4.5's predicate ("and no goal is active") is deliberately NOT
    here: no goal existed anywhere in the replay corpus, so applying it would
    filter nothing while making the function untestable in isolation. §4.5's
    correction (i) is explicit that a fire during goal-less PLAN work is a real
    fire, counted valid or misfire on the rubric, never excluded.
    """
    matched: list[str] = []
    if _grep_carries_short_flag(command, "c"):
        matched.append("grep_c")
    if _grep_carries_short_flag(command, "L"):
        matched.append("grep_L")
    if _SED_N_GREP_RE.search(command):
        matched.append("sed_n_grep")
    if _WC_L_RE.search(command):
        matched.append("wc_l")
    if _PGREP_RE.search(command):
        matched.append("pgrep")
    if _PIPE_HEAD_RE.search(command):
        matched.append("pipe_head")
    if _PIPE_TAIL_RE.search(command):
        matched.append("pipe_tail")
    return tuple(sorted(matched, key=SHAPE_ORDER.index))


# --------------------------------------------------------------------------
# The positive control (in-sample; credits nothing).
# --------------------------------------------------------------------------

#: Census error #1, recovered VERBATIM from the s288 transcript
#: (``4f48b22d-...``, one occurrence, 2026-09-09T04:43:21.745Z). §1.2: *counted
#: the word inside a different field's free text; buckets summed 139 vs 140.*
CONTROL_1_VERBATIM = (
    "wsl bash -lc 'cd ~/work/vero-lite && L=.claude/state/stop-classifier-log.jsonl; "
    'echo "===CLASSIFIER-LOG==="; ls -la "\\$L" 2>&1; echo "LINES=\\$(wc -l < "\\$L")"; '
    'echo "TIMEOUT=\\$(grep -c -i "timeout" "\\$L") MALFORMED=\\$(grep -c -i "malformed" "\\$L")"\''
)

#: Census errors #8 and #10, RECONSTRUCTED from §1.2's locked description.
#: Stated plainly because it weakens the control: neither is a ``Bash``
#: tool_use anywhere in the s287-s289 corpus (measured — 0 occurrences in all
#: three transcripts), so these two prove the regexes match the PLAN's prose,
#: not that they match what actually ran. Only #1 is verbatim.
CONTROL_8_RECONSTRUCTED = "sed -n '1,20p' .claude/settings.json | grep '^model:'"
CONTROL_10_RECONSTRUCTED = "pgrep -af run_benchmark"

CONTROL_COMMANDS: tuple[tuple[str, str], ...] = (
    ("#1", CONTROL_1_VERBATIM),
    ("#8", CONTROL_8_RECONSTRUCTED),
    ("#10", CONTROL_10_RECONSTRUCTED),
)


def reachable(commands: Sequence[tuple[str, str]] = CONTROL_COMMANDS) -> int:
    """How many of the three census commands the detector still matches."""
    return sum(1 for _label, cmd in commands if reading_shapes(cmd))


# --------------------------------------------------------------------------
# Corpus parsing.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BashCall:
    """One ``Bash`` tool_use, with the assistant prose that followed it."""

    session: str
    index: int
    command: str
    following_text: str


def _content_blocks(record: Mapping[str, Any]) -> list[Any]:
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    return content if isinstance(content, list) else []


def _transcript_events(path: Path) -> list[tuple[str, str]]:
    """Flatten a transcript into an ordered ``("bash"|"text", payload)`` list.

    Split out from :func:`iter_bash_calls` so that parsing and windowing are two
    readable passes rather than one nest deep enough for ruff to flag; a malformed
    line is skipped rather than fatal, because one truncated record at the tail of
    a live transcript must not cost the other 1,900.
    """
    events: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            for block in _content_blocks(record):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = str(block.get("text", "")).strip()
                    if text:
                        events.append(("text", text))
                elif block.get("type") == "tool_use" and block.get("name") == "Bash":
                    events.append(("bash", str((block.get("input") or {}).get("command", ""))))
    return events


def iter_bash_calls(path: Path, session: str, context_chars: int = 1200) -> Iterator[BashCall]:
    """Yield every ``Bash`` tool_use in a transcript, in order.

    ``following_text`` collects the assistant prose the agent wrote next — the
    window §4.5's rubric reads to decide whether the output was quoted. It is
    bounded so one verbose turn cannot swamp a report.
    """
    events = _transcript_events(path)

    # The window is the next TURNS_AHEAD assistant text blocks after the call —
    # deliberately NOT "up to the next Bash call". §4.5's rubric reads "the same
    # or the next assistant turn", and a turn routinely batches several Bash
    # calls before any prose; closing the window at the next call reported "no
    # text" for a fire whose number was quoted two calls later, which would
    # under-count V and inflate X. Windows may overlap; a fire is judged on what
    # the agent actually said next, not on an exclusive slice.
    turns_ahead = 2
    index = 0
    for position, (kind, payload) in enumerate(events):
        if kind != "bash":
            continue
        index += 1
        ahead: list[str] = []
        for later_kind, later_payload in events[position + 1 :]:
            if later_kind == "text":
                ahead.append(later_payload)
                if len(ahead) >= turns_ahead:
                    break
        yield BashCall(
            session=session,
            index=index,
            command=payload,
            following_text="\n".join(ahead)[:context_chars],
        )


# --------------------------------------------------------------------------
# The replay.
# --------------------------------------------------------------------------


@dataclass
class Fire:
    """A deduped advisory fire, awaiting the §4.5 hand classification."""

    session: str
    shape: str
    index: int
    command: str
    following_text: str
    verdict: str = "unclassified"


@dataclass
class ReplayResult:
    corpus_calls: int = 0
    raw_matches: int = 0
    fires: list[Fire] = field(default_factory=list)
    reachable_k: int = 0
    per_session: dict[str, dict[str, int]] = field(default_factory=dict)
    shape_hits: dict[str, int] = field(default_factory=dict)

    @property
    def match_rate(self) -> float:
        if self.corpus_calls == 0:
            return 0.0
        return 100.0 * self.raw_matches / self.corpus_calls

    @property
    def valid(self) -> int:
        return sum(1 for f in self.fires if f.verdict == "valid")

    @property
    def misfire(self) -> int:
        return sum(1 for f in self.fires if f.verdict == "misfire")

    @property
    def unclassified(self) -> int:
        return sum(1 for f in self.fires if f.verdict == "unclassified")

    def headline(self) -> str:
        """The one line AC-9 pre-committed, with every value printed."""
        return (
            f"corpus_calls={self.corpus_calls} "
            f"raw_matches={self.raw_matches} ({self.match_rate:.1f} %) "
            f"deduped_fires={len(self.fires)} "
            f"valid={self.valid} misfire={self.misfire} "
            f"reachable={self.reachable_k}/3"
        )


def replay(corpus: Mapping[str, Path], dedup: bool = True) -> ReplayResult:
    """Run the detector over the corpus and dedup once per session per shape."""
    result = ReplayResult(reachable_k=reachable())
    for session, path in corpus.items():
        seen: set[str] = set()
        counts = {"calls": 0, "matches": 0, "fires": 0}
        for call in iter_bash_calls(path, session):
            counts["calls"] += 1
            result.corpus_calls += 1
            shapes = reading_shapes(call.command)
            if not shapes:
                continue
            counts["matches"] += 1
            result.raw_matches += 1
            for shape in shapes:
                result.shape_hits[shape] = result.shape_hits.get(shape, 0) + 1
            fresh = [s for s in shapes if s not in seen] if dedup else list(shapes)
            if not fresh:
                continue
            shape = fresh[0]
            seen.add(shape)
            counts["fires"] += 1
            result.fires.append(
                Fire(
                    session=session,
                    shape=shape,
                    index=call.index,
                    command=call.command,
                    following_text=call.following_text,
                )
            )
        result.per_session[session] = counts
    return result


P_CEILING = 5.0
REQUIRED_REACHABLE = 3


def decide(result: ReplayResult) -> tuple[int, list[str]]:
    """Apply §4.5's three clauses. Returns ``(exit_status, reasons)``.

    ``EXIT_REFUSED`` is reserved for "the reading was never taken" — an empty
    corpus, or fires nobody classified. A refusal is not a fail: it says the
    instrument has no verdict to give, which is the distinction §4.6 makes so a
    provenance problem is never banked as a result.
    """
    reasons: list[str] = []
    if result.corpus_calls == 0:
        return EXIT_REFUSED, ["REFUSED: corpus is empty — no reading was taken"]

    # An unmeasured clause blocks a PASS; it must never swallow a FAIL. Clauses
    # 1 and 2 do not depend on the hand classification, so a breach of either is
    # a result in its own right and is reported as one. Returning REFUSED here
    # because clause 3 has no labels yet would file a decisive 27 %-vs-5 %
    # finding as "no reading taken".
    ok = True
    if result.reachable_k != REQUIRED_REACHABLE:
        reasons.append(f"FAIL clause 1: reachable={result.reachable_k}/3, required 3/3")
        ok = False
    else:
        reasons.append("pass clause 1: reachable=3/3 (in-sample; credits nothing)")

    if result.match_rate >= P_CEILING:
        reasons.append(
            f"FAIL clause 2: p={result.match_rate:.1f} % >= {P_CEILING:.0f} % "
            f"({result.raw_matches} of {result.corpus_calls} Bash calls)"
        )
        ok = False
    else:
        reasons.append(
            f"pass clause 2: p={result.match_rate:.1f} % < {P_CEILING:.0f} % "
            f"({result.raw_matches} of {result.corpus_calls} Bash calls)"
        )

    if result.unclassified:
        reasons.append(
            f"NOT MEASURED clause 3: {result.unclassified} of {len(result.fires)} fires carry "
            "no hand classification — V and X are not measured (§4.5 requires one)"
        )
        # Blocks a pass, never a fail.
        return (EXIT_REFUSED if ok else EXIT_FAIL), reasons

    if result.misfire > result.valid:
        reasons.append(f"FAIL clause 3: misfire={result.misfire} > valid={result.valid}")
        ok = False
    else:
        reasons.append(f"pass clause 3: misfire={result.misfire} <= valid={result.valid}")

    return (EXIT_PASS if ok else EXIT_FAIL), reasons


def render_report(result: ReplayResult, reasons: Sequence[str], status: int) -> str:
    """The full report. Prints the values it measured, never a bare PASS/FAIL."""
    lines = [
        "PLAN-0123 AC-9 — reading-shape replay",
        "",
        result.headline(),
        "",
        "per session:",
    ]
    for session, counts in result.per_session.items():
        lines.append(
            f"  {session}: calls={counts['calls']} matches={counts['matches']} "
            f"fires={counts['fires']}"
        )
    lines.append("")
    lines.append("raw matches by shape (a command may match several):")
    for shape in SHAPE_ORDER:
        lines.append(f"  {shape}: {result.shape_hits.get(shape, 0)}")
    lines.append("")
    lines.append("deduped fires:")
    for fire in result.fires:
        lines.append(f"  [{fire.verdict}] {fire.session} {fire.shape} call#{fire.index}")
        lines.append(f"      cmd: {fire.command[:200]}")
    lines.append("")
    lines.append("kill criterion (§4.5, fixed before the replay):")
    for reason in reasons:
        lines.append(f"  {reason}")
    lines.append("")
    lines.append(verdict_line(status))
    return "\n".join(lines)


def load_classification(path: Path, result: ReplayResult) -> int:
    """Apply a hand classification file. Returns how many fires it labelled."""
    data = json.loads(path.read_text(encoding="utf-8"))
    labels = {(str(e["session"]), str(e["shape"])): str(e["verdict"]) for e in data["fires"]}
    applied = 0
    for fire in result.fires:
        verdict = labels.get((fire.session, fire.shape))
        if verdict in ("valid", "misfire"):
            fire.verdict = verdict
            applied += 1
    return applied


def _parse_corpus(specs: Sequence[str]) -> dict[str, Path]:
    corpus: dict[str, Path] = {}
    for spec in specs:
        name, sep, raw = spec.partition("=")
        if not sep:
            raise SystemExit(f"--corpus expects NAME=PATH, got {spec!r}")
        corpus[name] = Path(raw)
    return corpus


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--corpus", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--classification", type=Path, default=None)
    parser.add_argument("--report-to", type=Path, default=None)
    parser.add_argument("--goal-id", default="ac9-replay")
    parser.add_argument(
        "--emit-fires",
        type=Path,
        default=None,
        help="write the deduped fires, with their following prose, for hand classification",
    )
    args = parser.parse_args(argv)

    if not args.corpus:
        print("REFUSED: no --corpus given")
        print(verdict_line(EXIT_REFUSED))
        return EXIT_REFUSED

    result = replay(_parse_corpus(args.corpus))

    if args.emit_fires is not None:
        payload = {
            "fires": [
                {
                    "session": f.session,
                    "shape": f.shape,
                    "index": f.index,
                    "command": f.command,
                    "following_text": f.following_text,
                    "verdict": "unclassified",
                }
                for f in result.fires
            ]
        }
        args.emit_fires.parent.mkdir(parents=True, exist_ok=True)
        args.emit_fires.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.classification is not None:
        load_classification(args.classification, result)

    status, reasons = decide(result)
    report = render_report(result, reasons, status)
    print(report)

    if args.report_to is not None:
        write_evidence(
            report,
            args.report_to,
            {"goal_id": args.goal_id, "head": head_sha(), "instrument": "reading_shape_replay"},
        )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
