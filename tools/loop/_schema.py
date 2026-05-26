#!/usr/bin/env python3
"""PLAN-0010 loop message schema: parsing + validation (stdlib-only).

This is the machine-checkable counterpart to
``docs/plans/0010-step1-message-schema.md`` and codifies §2 (filename
pattern), §3 (frontmatter), §4 (body sections), and the
schema-version-1 fail-closed rule (§3 "Schema-version compatibility").

Loop messages live under ``loop/inbox/`` + ``loop/processed/`` at the
repo top (PLAN-0010 Step 1 §1; SD-3 ratified). The ``*.msg.md`` files
themselves are gitignored; this module + downstream consumer code are
git-tracked.

Dependency-free (stdlib only). The frontmatter is a small, flat YAML
subset (scalars + simple ``- item`` lists), so a hand-rolled parser is
used rather than pulling in PyYAML — mirrors
:mod:`tools.handoffs._schema`.

Fail-closed discipline (binding for Step 3 dispatcher integration):

* Unknown ``message_type`` → reject (archive to ``processed/`` with
  ``.parse-error.log`` sibling; do NOT retry)
* ``schema_version != 1`` → reject (same archive path)
* Missing required field → reject
* ``time_authority != "mtime"`` → reject (the literal encodes the §2
  mtime-authority rule into every message)
* Filename ``producer_id`` segment ≠ frontmatter ``producer_id`` →
  reject (cross-check; prevents a producer renaming the file
  post-write to look like a different producer)
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TypeVar

_E = TypeVar("_E", bound=Enum)

REQUIRED_FRONTMATTER_FIELDS: tuple[str, ...] = (
    "producer_id",
    "schema_version",
    "message_type",
    "claimed_time",
    "time_authority",
)

OPTIONAL_FRONTMATTER_FIELDS: tuple[str, ...] = (
    "correlation_id",
    "expires_after",
    "references",
)

REQUIRED_BODY_SECTIONS: tuple[str, ...] = (
    "Subject",
    "Body",
    "Action requested",
)

OPTIONAL_BODY_SECTIONS: tuple[str, ...] = (
    "Citations",
    "Residual gaps",
)

SCHEMA_VERSION = 1
TIME_AUTHORITY_LITERAL = "mtime"
SUBJECT_MAX_CHARS = 120

# Filename grammar per PLAN-0010 Step 1 §2.
#   <producer-id>-<mtime-nonce>[-<rand>].msg.md
#   producer-id: ^[a-z][a-z0-9-]{2,63}$
#   nonce:       UTC ISO basic, YYYYMMDDTHHMMSSZ
#   rand:        4 chars base32 lowercase ([a-z2-7])
_FILENAME_RE = re.compile(
    r"^(?P<producer>[a-z][a-z0-9-]{2,63})"
    r"-(?P<nonce>\d{8}T\d{6}Z)"
    r"(?:-(?P<rand>[a-z2-7]{4}))?"
    r"\.msg\.md$"
)

# YAML-subset parsers (same as handoffs/_schema.py).
_KEY_RE = re.compile(r"^(?P<key>[A-Za-z_][\w-]*):[ \t]?(?P<val>.*)$")
_ITEM_RE = re.compile(r"^[ \t]+-[ \t]+(?P<item>.*\S)[ \t]*$")


class MessageType(Enum):
    """Vocabulary per PLAN-0010 Step 1 §3.1.

    ``smoke_heartbeat`` + ``smoke_receipt`` ship in Phase 3.5 (Cray-ratified
    SD-1 (b) smoke regression). The other three are reserved for deferred
    Step 4 use cases (a/c/d); consumer accepts them at parse time so that
    the producer + consumer can evolve independently, but a dispatcher
    that has no handler for one should treat it as a no-op + archive.
    """

    SMOKE_HEARTBEAT = "smoke_heartbeat"
    SMOKE_RECEIPT = "smoke_receipt"
    STATUS_DIGEST = "status_digest"
    GOVERNANCE_REMINDER = "governance_reminder"
    DEFERRED_OQ_ROTATION = "deferred_oq_rotation"


class ActionRequested(Enum):
    """The three canonical action verbs per PLAN-0010 Step 1 §4.

    The spec also permits a free-form imperative ("if ``message_type``
    allows it per §3.1 future vocabulary"); free-form values bypass this
    enum and surface as the raw ``action_requested_raw`` field on
    :class:`LoopMessage`. The dispatcher decides what to do with a
    free-form action based on ``message_type``.
    """

    NONE = "none"
    ACKNOWLEDGE = "acknowledge"
    PROCESS_THEN_ARCHIVE = "process-then-archive"


class Severity(Enum):
    """Whether a finding fails parse (error) or is advisory."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationError:
    """A single schema finding for one field of one message file."""

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
class FilenameParts:
    """Parsed components of a loop message filename."""

    producer_id: str
    nonce: str  # UTC ISO basic, YYYYMMDDTHHMMSSZ
    rand: str | None  # 4-char base32 lowercase, optional


@dataclass(frozen=True)
class LoopMessage:
    """A fully parsed + typed loop message (frontmatter + body sections).

    ``mtime_ns`` is populated by the dispatcher (it is the authoritative
    ordering key per Step 1 §2); the parser does not stat the file
    because tests + idempotency checks may parse synthetic input from
    in-memory strings. The dispatcher fills it in before any ordering
    decisions.
    """

    source: Path
    filename_parts: FilenameParts
    producer_id: str
    schema_version: int
    message_type: MessageType
    claimed_time: datetime
    time_authority: str  # always == TIME_AUTHORITY_LITERAL after validation
    action_requested: ActionRequested | None  # None when free-form (see action_requested_raw)
    action_requested_raw: str
    subject: str
    body: str
    correlation_id: str | None = None
    expires_after: datetime | None = None
    references: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    residual_gaps: str = ""


# --- YAML-subset parsing (mirror of handoffs/_schema.py helpers) ---


def _strip_quotes(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def _scalar(value: str) -> str:
    return _strip_quotes(value.strip())


def _as_str(value: object) -> str:
    return value if isinstance(value, str) else repr(value)


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return ``(frontmatter_block, body_text)``.

    ``frontmatter_block`` is the YAML between the leading ``---`` fence
    and the next ``---`` line (None if no frontmatter). ``body_text`` is
    everything after the closing fence (or the whole text if no
    frontmatter).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            block = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return block, body
    return None, text


def _collect_list(lines: list[str], start: int) -> tuple[list[str], int]:
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
    """Parse the flat YAML subset used by loop message frontmatter."""
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


# --- Body section parsing ---


def _parse_body_sections(body_text: str) -> dict[str, str]:
    """Split a markdown body into ``{heading: content}`` for each H2
    section. Returns an empty dict if no H2 sections are found.

    Heading match is exact text after ``## ``; trailing/leading whitespace
    in the content is trimmed. Sections beyond H2 (e.g., H3 inside a
    section) are kept verbatim as part of the parent H2 content.
    """
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []
    for raw in body_text.splitlines():
        if raw.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = raw[3:].strip()
            current_lines = []
            continue
        current_lines.append(raw)
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()
    return sections


def _parse_citation_items(citations_section: str) -> tuple[str, ...]:
    """Parse the ``## Citations`` section into a tuple of item strings."""
    items: list[str] = []
    for raw in citations_section.splitlines():
        match = _ITEM_RE.match("  " + raw) if raw.startswith("-") else _ITEM_RE.match(raw)
        if match is not None:
            items.append(_strip_quotes(match.group("item").strip()))
    return tuple(items)


# --- Coercion helpers (mirror handoffs/_schema.py) ---


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
    errors.append(ValidationError(name, _as_str(value), f"{name} must be ISO 8601 with timezone"))
    return datetime.min


def _coerce_optional_dt(value: object, name: str, errors: list[ValidationError]) -> datetime | None:
    if value is None or value == "":
        return None
    return _coerce_dt(value, name, errors)


def _as_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, str) and value:
        return (value,)
    return ()


# --- Filename parsing ---


def parse_filename(name: str) -> FilenameParts | ValidationError:
    """Parse a loop message filename per Step 1 §2 grammar."""
    match = _FILENAME_RE.match(name)
    if match is None:
        return ValidationError(
            "filename",
            name,
            "filename must match <producer-id>-<YYYYMMDDTHHMMSSZ>[-<rand>].msg.md "
            "where producer-id is ^[a-z][a-z0-9-]{2,63}$ and rand is 4 chars base32 lowercase",
        )
    return FilenameParts(
        producer_id=match.group("producer"),
        nonce=match.group("nonce"),
        rand=match.group("rand"),
    )


# --- Validation orchestration ---


def _check_required_frontmatter(raw: Mapping[str, object], errors: list[ValidationError]) -> None:
    for name in REQUIRED_FRONTMATTER_FIELDS:
        if name not in raw or raw[name] == "":
            errors.append(ValidationError(name, "", f"required field {name} missing"))


def _check_unknown_frontmatter(raw: Mapping[str, object], errors: list[ValidationError]) -> None:
    known = set(REQUIRED_FRONTMATTER_FIELDS) | set(OPTIONAL_FRONTMATTER_FIELDS)
    for key in raw:
        if key not in known:
            errors.append(
                ValidationError(
                    key, _as_str(raw[key]), "unknown frontmatter field", Severity.WARNING
                )
            )


def _check_schema_version(raw: Mapping[str, object], errors: list[ValidationError]) -> int:
    version = _coerce_int(raw.get("schema_version"), "schema_version", errors)
    if version != -1 and version != SCHEMA_VERSION:
        errors.append(
            ValidationError(
                "schema_version",
                str(version),
                f"schema_version must == {SCHEMA_VERSION}; "
                f"fail-closed reject per PLAN-0010 Step 1 §3 schema-version-compatibility rule",
            )
        )
    return version


def _check_time_authority(raw: Mapping[str, object], errors: list[ValidationError]) -> str:
    value = raw.get("time_authority", "")
    if isinstance(value, str) and value == TIME_AUTHORITY_LITERAL:
        return value
    errors.append(
        ValidationError(
            "time_authority",
            _as_str(value),
            f"time_authority must == '{TIME_AUTHORITY_LITERAL}' literally "
            f"(encodes Step 1 §2 mtime-authority rule into every message)",
        )
    )
    return ""


def _check_producer_id_matches_filename(
    frontmatter_producer_id: str,
    filename_producer_id: str,
    errors: list[ValidationError],
) -> None:
    if frontmatter_producer_id != filename_producer_id:
        errors.append(
            ValidationError(
                "producer_id",
                frontmatter_producer_id,
                f"frontmatter producer_id '{frontmatter_producer_id}' does not match "
                f"filename producer-id segment '{filename_producer_id}' "
                f"(cross-check per Step 1 §3 — prevents post-write rename to forge identity)",
            )
        )


def _check_body_sections(sections: Mapping[str, str], errors: list[ValidationError]) -> None:
    for name in REQUIRED_BODY_SECTIONS:
        if name not in sections or not sections[name]:
            errors.append(
                ValidationError(f"body:{name}", "", f"required body section '## {name}' missing")
            )


def _parse_action(
    raw_action: str, errors: list[ValidationError]
) -> tuple[ActionRequested | None, str]:
    """Parse the body's ``Action requested`` section.

    Returns ``(enum_value, raw_string)``. enum_value is None when the
    action is free-form (not in the canonical 3). The raw string is
    always populated for the dispatcher's free-form handling.
    """
    cleaned = raw_action.strip().strip("`").strip()
    if not cleaned:
        errors.append(
            ValidationError(
                "body:Action requested",
                "",
                "action requested must be one of: none / acknowledge / process-then-archive, "
                "or a free-form imperative per Step 1 §4",
            )
        )
        return None, ""
    try:
        return ActionRequested(cleaned), cleaned
    except ValueError:
        return None, cleaned


def _check_subject_length(subject: str, errors: list[ValidationError]) -> None:
    if len(subject) > SUBJECT_MAX_CHARS:
        errors.append(
            ValidationError(
                "body:Subject",
                f"len={len(subject)}",
                f"subject exceeds {SUBJECT_MAX_CHARS} chars "
                f"per Step 1 §4 'one-line plain-text subject'",
                Severity.WARNING,
            )
        )


# --- Top-level parse + validate ---


def parse_message_text(path: Path, text: str) -> LoopMessage | list[ValidationError]:
    """Parse + validate a loop message from its filename + raw text.

    The path is used for ``source`` and for the filename cross-check;
    the text is the raw file contents (separated for testability — tests
    can synthesize text without touching the filesystem).
    """
    errors: list[ValidationError] = []

    # Filename first — if the filename is malformed, the cross-check
    # cannot run and we surface that as the primary error.
    filename_result = parse_filename(path.name)
    if isinstance(filename_result, ValidationError):
        return [filename_result]

    block, body_text = _split_frontmatter(text)
    if block is None:
        return [ValidationError("<frontmatter>", "", "missing '---' frontmatter block")]

    raw = _parse_block(block)
    _check_required_frontmatter(raw, errors)
    _check_unknown_frontmatter(raw, errors)

    schema_version = _check_schema_version(raw, errors)
    time_authority = _check_time_authority(raw, errors)

    message_type = _coerce_enum(MessageType, raw.get("message_type"), "message_type", errors)
    claimed_time = _coerce_dt(raw.get("claimed_time"), "claimed_time", errors)
    expires_after = _coerce_optional_dt(raw.get("expires_after"), "expires_after", errors)

    producer_id = _as_str(raw.get("producer_id", ""))
    if producer_id:
        _check_producer_id_matches_filename(producer_id, filename_result.producer_id, errors)

    sections = _parse_body_sections(body_text)
    _check_body_sections(sections, errors)

    subject = sections.get("Subject", "").strip()
    _check_subject_length(subject, errors)

    body = sections.get("Body", "").strip()
    action_raw = sections.get("Action requested", "")
    action_enum, action_raw_clean = _parse_action(action_raw, errors)

    citations = _parse_citation_items(sections["Citations"]) if "Citations" in sections else ()
    residual_gaps = sections.get("Residual gaps", "").strip()

    correlation_id_raw = raw.get("correlation_id")
    correlation_id: str | None = (
        correlation_id_raw if isinstance(correlation_id_raw, str) and correlation_id_raw else None
    )

    if any(err.is_error() for err in errors) or message_type is None:
        return errors

    return LoopMessage(
        source=path,
        filename_parts=filename_result,
        producer_id=producer_id,
        schema_version=schema_version,
        message_type=message_type,
        claimed_time=claimed_time,
        time_authority=time_authority,
        action_requested=action_enum,
        action_requested_raw=action_raw_clean,
        subject=subject,
        body=body,
        correlation_id=correlation_id,
        expires_after=expires_after,
        references=_as_tuple(raw.get("references")),
        citations=citations,
        residual_gaps=residual_gaps,
    )


def parse_message_file(path: Path) -> LoopMessage | list[ValidationError]:
    """Parse + validate a loop message file from disk."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [ValidationError("<file>", str(path), f"cannot read file: {exc}")]
    return parse_message_text(path, text)
