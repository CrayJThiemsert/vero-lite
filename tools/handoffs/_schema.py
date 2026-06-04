#!/usr/bin/env python3
"""Handoff frontmatter schema: parsing + validation (stdlib-only).

This is the machine-checkable counterpart to
``docs/conventions/handoff-frontmatter-schema.md`` and codifies D1-D5 of
PLAN-004 v2 (``docs/plans/0004-handoff-frontmatter-and-dashboard.md``).

Handoff files live under ``.claude/handoffs/session-NN/`` and are
gitignored by design (Lesson #5 §4). This module and the two CLIs that
import it (``validate_handoff.py``, ``handoff_status.py``) are
git-tracked.

Dependency-free (stdlib only). The frontmatter is a small, flat YAML
subset (scalars + simple ``- item`` lists), so a hand-rolled parser is
used rather than pulling in PyYAML.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TypeVar

_E = TypeVar("_E", bound=Enum)

REQUIRED_FIELDS: tuple[str, ...] = (
    "from",
    "to",
    "actor",
    "session",
    "batch",
    "phase",
    "status",
    "created",
    "title",
)

OPTIONAL_FIELDS: tuple[str, ...] = (
    "suffix",
    "references_predecessor_handoffs",
    "references_session_batches_completed",
    "references_commits",
)

_KEY_RE = re.compile(r"^(?P<key>[A-Za-z_][\w-]*):[ \t]?(?P<val>.*)$")
_ITEM_RE = re.compile(r"^[ \t]+-[ \t]+(?P<item>.*\S)[ \t]*$")
_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-(?P<actor>[a-z]+)-")
_SESSION_DIR_RE = re.compile(r"^session-(?P<num>\d+)$")

# The generated per-session index (PLAN-004 Phase B). It carries no
# frontmatter by design, so it is excluded from every handoff walk to
# avoid being mis-parsed as a malformed handoff.
INDEX_FILENAME = "INDEX.md"


class Actor(Enum):
    """Authoring tier (D2). Drives the filename prefix discipline."""

    CHAT = "chat"
    CODE = "code"
    COWORK = "cowork"
    CRAY = "cray"


class Phase(Enum):
    """Lifecycle role of the handoff (D3)."""

    KICKOFF = "kickoff"
    DISPATCH = "dispatch"
    MIDFLIGHT = "midflight"
    CLOSEOUT = "closeout"
    HANDOFF = "handoff"
    DISCUSSION = "discussion"


class Status(Enum):
    """Work state (D5)."""

    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    DONE = "DONE"
    NEEDS_INPUT = "NEEDS_INPUT"


class Suffix(Enum):
    """Content-type token (D4). Core members are locked; the
    extensible members are registered here and adding more requires a
    PLAN-004 D4 amendment."""

    CLOSEOUT = "closeout"
    MIDFLIGHT = "midflight"
    KICKOFF = "kickoff"
    ERRATA = "errata"
    AMENDMENT = "amendment"
    ADDENDUM = "addendum"
    TRANSCRIPT = "transcript"
    SYNC = "sync"
    RESTART_BRIDGE = "restart-bridge"
    DISPATCH = "dispatch"
    COMPLETION = "completion"
    CONSULTATION = "consultation"


class Severity(Enum):
    """Whether a finding fails validation (error) or is advisory."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationError:
    """A single schema finding for one field of one file."""

    field: str
    value: str
    message: str
    severity: Severity = Severity.ERROR

    def is_error(self) -> bool:
        """True when this finding fails validation."""
        return self.severity is Severity.ERROR

    def render(self) -> str:
        """One-line ``<field>: <severity>: <message>`` form."""
        return f"{self.field}: {self.severity.value}: {self.message}"


@dataclass(frozen=True)
class Frontmatter:
    """A fully parsed + typed handoff frontmatter block."""

    source: Path
    from_: str
    to: str
    actor: Actor
    session: int
    batch: str
    phase: Phase
    status: Status
    created: datetime
    title: str
    suffix: Suffix | None = None
    references_predecessor_handoffs: tuple[str, ...] = ()
    references_session_batches_completed: tuple[str, ...] = ()
    references_commits: tuple[str, ...] = ()


@dataclass(frozen=True)
class SessionSummary:
    """Aggregated dashboard view over one session's handoff files."""

    session: str
    total: int
    by_phase: dict[str, int]
    by_status: dict[str, int]
    by_actor: dict[str, int]
    chains: list[str]
    needs_input: list[str]
    parse_failures: list[str]


def _strip_quotes(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def _scalar(value: str) -> str:
    return _strip_quotes(value.strip())


def _as_str(value: object) -> str:
    return value if isinstance(value, str) else repr(value)


def _split_frontmatter(text: str) -> str | None:
    """Return the body between the leading ``---`` fence and the next
    ``---`` line, or None when there is no frontmatter block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx])
    return None


def _collect_list(lines: list[str], start: int) -> tuple[list[str], int]:
    """Consume contiguous ``- item`` lines beginning at ``start``.

    Returns the collected items and the index of the first
    non-list, non-blank line.
    """
    items: list[str] = []
    idx = start
    while idx < len(lines):
        match = _ITEM_RE.match(lines[idx])
        if match is not None:
            items.append(_strip_quotes(match.group("item").strip()))
            idx += 1
            continue
        if not lines[idx].strip():
            idx += 1
            continue
        break
    return items, idx


def _parse_block(block: str) -> dict[str, object]:
    """Parse the flat YAML subset used by handoff frontmatter."""
    data: dict[str, object] = {}
    lines = block.splitlines()
    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        if not raw.strip() or raw.lstrip().startswith("#"):
            idx += 1
            continue
        match = _KEY_RE.match(raw)
        if match is None:
            idx += 1
            continue
        key = match.group("key")
        val = match.group("val").strip()
        if val:
            data[key] = _scalar(val)
            idx += 1
            continue
        items, idx = _collect_list(lines, idx + 1)
        data[key] = items if items else ""
    return data


def _coerce_enum(
    enum_cls: type[_E],
    value: object,
    name: str,
    errors: list[ValidationError],
) -> _E | None:
    if not isinstance(value, str) or not value:
        errors.append(ValidationError(name, _as_str(value), f"required field {name} missing"))
        return None
    try:
        return enum_cls(value)
    except ValueError:
        allowed = ", ".join(str(member.value) for member in enum_cls)
        errors.append(ValidationError(name, value, f"invalid {name}; allowed: {allowed}"))
        return None


def _coerce_int(value: object, name: str, errors: list[ValidationError]) -> int:
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    errors.append(ValidationError(name, _as_str(value), f"{name} must be an integer"))
    return -1


def _coerce_dt(value: object, name: str, errors: list[ValidationError]) -> datetime:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            parsed = None
        if parsed is not None and parsed.tzinfo is not None:
            return parsed
    errors.append(ValidationError(name, _as_str(value), f"{name} must be ISO8601 with timezone"))
    return datetime.min


def _as_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _check_required(raw: dict[str, object], errors: list[ValidationError]) -> None:
    for name in REQUIRED_FIELDS:
        if name not in raw or raw[name] == "":
            errors.append(ValidationError(name, "", f"required field {name} missing"))


def _check_unknown(raw: dict[str, object], errors: list[ValidationError]) -> None:
    known = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for key in raw:
        if key not in known:
            errors.append(
                ValidationError(key, _as_str(raw[key]), "unknown field", Severity.WARNING)
            )


def _build(path: Path, raw: dict[str, object]) -> Frontmatter | list[ValidationError]:
    errors: list[ValidationError] = []
    _check_required(raw, errors)
    _check_unknown(raw, errors)

    actor = _coerce_enum(Actor, raw.get("actor"), "actor", errors)
    phase = _coerce_enum(Phase, raw.get("phase"), "phase", errors)
    status = _coerce_enum(Status, raw.get("status"), "status", errors)
    suffix: Suffix | None = None
    if raw.get("suffix"):
        suffix = _coerce_enum(Suffix, raw.get("suffix"), "suffix", errors)
    session = _coerce_int(raw.get("session"), "session", errors)
    created = _coerce_dt(raw.get("created"), "created", errors)

    if any(err.is_error() for err in errors) or actor is None or phase is None:
        return errors
    assert status is not None  # narrowed: a None status added an error above

    return Frontmatter(
        source=path,
        from_=_as_str(raw.get("from", "")),
        to=_as_str(raw.get("to", "")),
        actor=actor,
        session=session,
        batch=_as_str(raw.get("batch", "")),
        phase=phase,
        status=status,
        created=created,
        title=_as_str(raw.get("title", "")),
        suffix=suffix,
        references_predecessor_handoffs=_as_tuple(raw.get("references_predecessor_handoffs")),
        references_session_batches_completed=_as_tuple(
            raw.get("references_session_batches_completed")
        ),
        references_commits=_as_tuple(raw.get("references_commits")),
    )


def parse_frontmatter_text(
    content: str, source: Path | None = None
) -> Frontmatter | list[ValidationError]:
    """Parse + type a handoff frontmatter block from raw *text*.

    Identical to :func:`parse_frontmatter` but takes the file content
    directly instead of reading from disk — for in-process callers that
    hold the text but no file path (e.g. the vero-bridge
    ``validate_handoff_frontmatter`` tool, which receives the handoff body
    over the wire). ``source`` is recorded on the resulting
    :class:`Frontmatter` (a ``<text>`` placeholder by default); it does not
    affect validation. No filesystem access.

    Returns a :class:`Frontmatter` on success, or a non-empty list of
    :class:`ValidationError` describing every schema violation.
    """
    block = _split_frontmatter(content)
    if block is None:
        return [ValidationError("<frontmatter>", "", "missing '---' frontmatter block")]
    return _build(source if source is not None else Path("<text>"), _parse_block(block))


def parse_frontmatter(path: Path) -> Frontmatter | list[ValidationError]:
    """Parse + type one handoff file.

    Returns a :class:`Frontmatter` on success, or a non-empty list of
    :class:`ValidationError` describing every schema violation.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [ValidationError("<file>", str(path), f"cannot read file: {exc}")]
    return parse_frontmatter_text(text, source=path)


def validate_filename_prefix(path: Path, actor: Actor) -> ValidationError | None:
    """Enforce the ``actor:`` ↔ filename-prefix discipline (D2)."""
    name = path.name
    match = _FILENAME_RE.match(name)
    if match is None:
        return ValidationError(
            "filename", name, "filename must be <date>-<HHMM>-<actor>-<topic>.md"
        )
    found = match.group("actor")
    if found != actor.value:
        return ValidationError(
            "filename",
            name,
            f"filename actor prefix '{found}-' does not match actor: {actor.value}",
        )
    return None


def validate_file(path: Path) -> list[ValidationError]:
    """Full validation of one file: schema + filename + suffix coherence.

    An empty list means the file is valid (warnings, if any, are
    included but do not by themselves indicate invalidity — callers
    decide via :meth:`ValidationError.is_error`).
    """
    result = parse_frontmatter(path)
    if isinstance(result, list):
        return result
    errors: list[ValidationError] = []
    prefix_error = validate_filename_prefix(path, result.actor)
    if prefix_error is not None:
        errors.append(prefix_error)
    if result.suffix is not None and f"-{result.suffix.value}" not in path.stem:
        errors.append(
            ValidationError(
                "suffix",
                result.suffix.value,
                f"suffix '{result.suffix.value}' not reflected in filename",
                Severity.WARNING,
            )
        )
    return errors


def validate_directory(root: Path) -> dict[Path, list[ValidationError]]:
    """Validate every ``*.md`` under ``root`` (skipping any ``archive``
    path component). Returns a mapping of file → findings."""
    out: dict[Path, list[ValidationError]] = {}
    for path in sorted(root.rglob("*.md")):
        if "archive" in path.parts:
            continue
        if path.name == INDEX_FILENAME:
            continue
        out[path] = validate_file(path)
    return out


def _detect_chains(frontmatters: Sequence[Frontmatter]) -> list[str]:
    """A pause-and-redispatch chain is a batch with ≥2 files where at
    least one is PAUSED; rendered as the status trail ordered by
    ``created`` (Lesson #6 pattern, D5)."""
    by_batch: dict[str, list[Frontmatter]] = defaultdict(list)
    for fmatter in frontmatters:
        by_batch[fmatter.batch].append(fmatter)
    chains: list[str] = []
    for batch, items in sorted(by_batch.items()):
        if len(items) < 2:
            continue
        ordered = sorted(items, key=lambda f: f.created)
        if not any(f.status is Status.PAUSED for f in ordered):
            continue
        trail = " → ".join(f.status.value for f in ordered)
        chains.append(f"{batch}: {trail}")
    return chains


def summarize_paths(paths: Sequence[Path], session: str) -> SessionSummary:
    """Build the dashboard summary for one session's handoff files."""
    frontmatters: list[Frontmatter] = []
    parse_failures: list[str] = []
    for path in sorted(paths):
        result = parse_frontmatter(path)
        if isinstance(result, list):
            if any(err.is_error() for err in result):
                parse_failures.append(path.name)
            continue
        frontmatters.append(result)

    by_phase = Counter(f.phase.value for f in frontmatters)
    by_status = Counter(f.status.value for f in frontmatters)
    by_actor = Counter(f.actor.value for f in frontmatters)
    needs_input = sorted(f.source.name for f in frontmatters if f.status is Status.NEEDS_INPUT)
    return SessionSummary(
        session=session,
        total=len(frontmatters),
        by_phase=dict(sorted(by_phase.items())),
        by_status=dict(sorted(by_status.items())),
        by_actor=dict(sorted(by_actor.items())),
        chains=_detect_chains(frontmatters),
        needs_input=needs_input,
        parse_failures=sorted(parse_failures),
    )


# --- Session discovery + INDEX.md generation (PLAN-004 Phase B) ---


def session_md_files(session_dir: Path) -> list[Path]:
    """Return a session dir's handoff ``*.md`` files, sorted by name.

    Excludes the generated :data:`INDEX_FILENAME` so it is never counted
    or parsed as a handoff.
    """
    return sorted(p for p in session_dir.glob("*.md") if p.name != INDEX_FILENAME)


def latest_session_dir(root: Path) -> Path | None:
    """Return the highest-numbered ``session-NN`` directory under *root*.

    Sorts **numerically** (``session-9`` < ``session-10``), not
    lexicographically. Returns ``None`` when *root* is missing or holds no
    ``session-NN`` directory.
    """
    if not root.is_dir():
        return None
    best: tuple[int, Path] | None = None
    for entry in root.glob("session-*"):
        if not entry.is_dir():
            continue
        match = _SESSION_DIR_RE.match(entry.name)
        if match is None:
            continue
        num = int(match.group("num"))
        if best is None or num > best[0]:
            best = (num, entry)
    return best[1] if best is not None else None


def _index_cell(text: str, limit: int = 60) -> str:
    """Sanitize one cell for a markdown table (escape pipes, collapse, clip)."""
    cleaned = text.replace("|", r"\|").replace("\n", " ").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def render_index(session_dir: Path) -> str:
    """Render a deterministic markdown index of one session's handoffs.

    The output is a header (session name + aggregate counts) plus a table
    of handoffs ordered by ``created`` then filename, plus an
    ``⚠ Unparseable`` list for any parse-failure files. **No
    generation timestamp is emitted**, so repeated renders over an
    unchanged directory are byte-identical (idempotent regeneration, the
    Phase B acceptance property).
    """
    paths = session_md_files(session_dir)
    summary = summarize_paths(paths, session_dir.name)

    rows: list[tuple[datetime, str, str]] = []
    for path in paths:
        result = parse_frontmatter(path)
        if isinstance(result, list):
            continue  # parse failures are surfaced via summary.parse_failures
        suffix = result.suffix.value if result.suffix is not None else "—"
        cells = (
            result.created.strftime("%Y-%m-%d %H:%M"),
            result.actor.value,
            result.phase.value,
            result.status.value,
            suffix,
            _index_cell(result.title),
            path.name,
        )
        rows.append((result.created, path.name, "| " + " | ".join(cells) + " |"))
    rows.sort(key=lambda r: (r[0], r[1]))

    def _counts(mapping: dict[str, int]) -> str:
        return ", ".join(f"{k}={v}" for k, v in mapping.items()) or "—"

    lines = [
        f"# {session_dir.name} — handoff index",
        "",
        "> Auto-generated by `tools/handoffs/precommit_handoffs.py`. Do not edit by hand.",
        "> Regenerated on each commit; gitignored output.",
        "",
        (
            f"**Total:** {summary.total} · "
            f"**phase:** {_counts(summary.by_phase)} · "
            f"**status:** {_counts(summary.by_status)} · "
            f"**actor:** {_counts(summary.by_actor)}"
        ),
        "",
        "| Created | Actor | Phase | Status | Suffix | Title | File |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(row[2] for row in rows)
    if summary.parse_failures:
        lines.append("")
        lines.append("## ⚠ Unparseable")
        lines.extend(f"- `{name}`" for name in summary.parse_failures)
    return "\n".join(lines) + "\n"


def write_index(session_dir: Path) -> Path:
    """Write :func:`render_index` to ``session_dir/INDEX.md``; return its path."""
    target = session_dir / INDEX_FILENAME
    target.write_text(render_index(session_dir), encoding="utf-8")
    return target
