"""Tests for tools.loop._schema (PLAN-0010 Step 3 parser).

Covers AC-Step1-1 (schema parse) + filename portion of AC-Step1-3
(mtime / filename grammar). Lifecycle / retention / mtime-ordering
tests live with the dispatcher in tests/loop/test_dispatcher.py
(Step 3b).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tools.loop._schema import (
    ActionRequested,
    FilenameParts,
    LoopMessage,
    MessageType,
    Severity,
    ValidationError,
    parse_filename,
    parse_message_file,
    parse_message_text,
)

# --- Helpers ---


def _make_message(
    *,
    filename: str = "cowork-smoke-heartbeat-20260526T085945Z.msg.md",
    producer_id: str = "cowork-smoke-heartbeat",
    schema_version: int = 1,
    message_type: str = "smoke_heartbeat",
    claimed_time: str = "2026-05-26T08:59:45Z",
    time_authority: str = "mtime",
    correlation_id: str | None = None,
    expires_after: str | None = None,
    references: list[str] | None = None,
    subject: str = "Heartbeat 2026-05-26 08:59",
    body: str = "Producer alive.\n\nNo anomalies detected.",
    action_requested: str = "acknowledge",
    citations: list[str] | None = None,
    residual_gaps: str | None = None,
) -> tuple[Path, str]:
    """Build (path, text) for a well-formed loop message; pass kwargs to
    distort individual fields for negative tests."""
    fm_lines = [
        "---",
        f"producer_id: {producer_id}",
        f"schema_version: {schema_version}",
        f"message_type: {message_type}",
        f"claimed_time: {claimed_time}",
        f"time_authority: {time_authority}",
    ]
    if correlation_id is not None:
        fm_lines.append(f"correlation_id: {correlation_id}")
    if expires_after is not None:
        fm_lines.append(f"expires_after: {expires_after}")
    if references is not None:
        fm_lines.append("references:")
        for ref in references:
            fm_lines.append(f"  - {ref}")
    fm_lines.append("---")
    body_lines = [
        "",
        "## Subject",
        "",
        subject,
        "",
        "## Body",
        "",
        body,
        "",
        "## Action requested",
        "",
        action_requested,
    ]
    if citations:
        body_lines.extend(["", "## Citations", ""])
        for cite in citations:
            body_lines.append(f"- {cite}")
    if residual_gaps:
        body_lines.extend(["", "## Residual gaps", "", residual_gaps])
    text = "\n".join(fm_lines + body_lines) + "\n"
    return Path(f"loop/inbox/{filename}"), text


def _parse(**kw: object) -> LoopMessage | list[ValidationError]:
    path, text = _make_message(**kw)  # type: ignore[arg-type]
    return parse_message_text(path, text)


# --- AC-Step1-1 HAPPY: well-formed parses cleanly ---


def test_minimal_well_formed_parses() -> None:
    result = _parse()
    assert isinstance(result, LoopMessage)
    assert result.producer_id == "cowork-smoke-heartbeat"
    assert result.schema_version == 1
    assert result.message_type is MessageType.SMOKE_HEARTBEAT
    assert result.time_authority == "mtime"
    assert result.action_requested is ActionRequested.ACKNOWLEDGE
    assert result.subject == "Heartbeat 2026-05-26 08:59"
    assert result.claimed_time == datetime(2026, 5, 26, 8, 59, 45, tzinfo=UTC)
    assert result.correlation_id is None
    assert result.expires_after is None
    assert result.references == ()
    assert result.citations == ()
    assert result.residual_gaps == ""


def test_all_message_types_parse() -> None:
    for value in (
        "smoke_heartbeat",
        "smoke_receipt",
        "status_digest",
        "governance_reminder",
        "deferred_oq_rotation",
    ):
        result = _parse(message_type=value)
        assert isinstance(result, LoopMessage)
        assert result.message_type.value == value


def test_all_canonical_actions_parse() -> None:
    for value in ("none", "acknowledge", "process-then-archive"):
        result = _parse(action_requested=value)
        assert isinstance(result, LoopMessage)
        assert result.action_requested is ActionRequested(value)
        assert result.action_requested_raw == value


# --- AC-Step1-1 BOUNDARY: optional fields all-absent + all-present ---


def test_all_optional_fields_present() -> None:
    result = _parse(
        correlation_id="smoke-2026-05-26-batch-3",
        expires_after="2026-05-27T00:00:00Z",
        references=["docs/STATUS.md", "https://example.com/dash"],
        citations=["`tools/loop/_schema.py:42` — parser entry point"],
        residual_gaps="None.",
    )
    assert isinstance(result, LoopMessage)
    assert result.correlation_id == "smoke-2026-05-26-batch-3"
    assert result.expires_after == datetime(2026, 5, 27, 0, 0, 0, tzinfo=UTC)
    assert result.references == ("docs/STATUS.md", "https://example.com/dash")
    assert len(result.citations) == 1
    assert result.citations[0].startswith("`tools/loop/_schema.py:42`")
    assert result.residual_gaps == "None."


def test_action_requested_free_form_accepted() -> None:
    """Step 1 §4 permits a free-form imperative beyond the 3 canonical."""
    result = _parse(action_requested="restart-the-loop-detector")
    assert isinstance(result, LoopMessage)
    assert result.action_requested is None  # enum miss → None
    assert result.action_requested_raw == "restart-the-loop-detector"


def test_action_requested_with_backticks_stripped() -> None:
    result = _parse(action_requested="`none`")
    assert isinstance(result, LoopMessage)
    assert result.action_requested is ActionRequested.NONE


def test_section_ordering_insensitive() -> None:
    """Parser uses {heading: content} dict — ordering does not matter.

    Step 1 §4 hints at split('\\n## ').zip as one implementation; this
    parser is order-INsensitive (strictly more robust). Test documents
    the chosen behavior.
    """
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = (
        "---\n"
        "producer_id: cowork-smoke-heartbeat\n"
        "schema_version: 1\n"
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "time_authority: mtime\n"
        "---\n"
        "\n## Action requested\n\nacknowledge\n"
        "\n## Body\n\nbody first\n"
        "\n## Subject\n\nsubject last\n"
    )
    result = parse_message_text(path, text)
    assert isinstance(result, LoopMessage)
    assert result.subject == "subject last"
    assert result.body == "body first"
    assert result.action_requested is ActionRequested.ACKNOWLEDGE


# --- AC-Step1-1 FAIL-CLOSED: required-field / schema-version / unknown enum ---


def _errors(result: LoopMessage | list[ValidationError]) -> list[ValidationError]:
    assert isinstance(result, list), f"expected errors, got LoopMessage: {result}"
    return result


def _has_error_for(errors: list[ValidationError], field_substr: str) -> bool:
    return any(field_substr in e.field and e.is_error() for e in errors)


def test_missing_producer_id_rejected() -> None:
    # Build text manually because the helper requires producer_id.
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = (
        "---\n"
        "schema_version: 1\n"
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "time_authority: mtime\n"
        "---\n"
        "## Subject\n\ns\n## Body\n\nb\n## Action requested\n\nnone\n"
    )
    errors = _errors(parse_message_text(path, text))
    assert _has_error_for(errors, "producer_id")


def test_schema_version_zero_rejected() -> None:
    errors = _errors(_parse(schema_version=0))
    assert _has_error_for(errors, "schema_version")


def test_schema_version_two_rejected() -> None:
    """Producer ahead of consumer → fail-closed reject (Step 1 §3 binding)."""
    errors = _errors(_parse(schema_version=2))
    assert _has_error_for(errors, "schema_version")
    reason = next(
        e.message for e in errors if e.field == "schema_version" and "must ==" in e.message
    )
    assert "1" in reason
    assert "PLAN-0010" in reason


def test_unknown_message_type_rejected() -> None:
    errors = _errors(_parse(message_type="hot_new_workload"))
    assert _has_error_for(errors, "message_type")


def test_time_authority_wrong_literal_rejected() -> None:
    """time_authority must equal the literal 'mtime'; 'clock' is rejected."""
    errors = _errors(_parse(time_authority="clock"))
    assert _has_error_for(errors, "time_authority")
    reason = next(e.message for e in errors if e.field == "time_authority")
    assert "mtime" in reason


def test_time_authority_missing_rejected() -> None:
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = (
        "---\n"
        "producer_id: cowork-smoke-heartbeat\n"
        "schema_version: 1\n"
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "---\n"
        "## Subject\n\ns\n## Body\n\nb\n## Action requested\n\nnone\n"
    )
    errors = _errors(parse_message_text(path, text))
    assert _has_error_for(errors, "time_authority")


def test_claimed_time_without_timezone_rejected() -> None:
    errors = _errors(_parse(claimed_time="2026-05-26T08:59:45"))
    assert _has_error_for(errors, "claimed_time")


def test_claimed_time_malformed_rejected() -> None:
    errors = _errors(_parse(claimed_time="not-a-date"))
    assert _has_error_for(errors, "claimed_time")


def test_expires_after_without_timezone_rejected() -> None:
    errors = _errors(_parse(expires_after="2026-05-27T00:00:00"))
    assert _has_error_for(errors, "expires_after")


def test_missing_body_subject_rejected() -> None:
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = (
        "---\n"
        "producer_id: cowork-smoke-heartbeat\n"
        "schema_version: 1\n"
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "time_authority: mtime\n"
        "---\n"
        "## Body\n\nbody only\n## Action requested\n\nnone\n"
    )
    errors = _errors(parse_message_text(path, text))
    assert _has_error_for(errors, "body:Subject")


def test_missing_body_action_rejected() -> None:
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = (
        "---\n"
        "producer_id: cowork-smoke-heartbeat\n"
        "schema_version: 1\n"
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "time_authority: mtime\n"
        "---\n"
        "## Subject\n\nfoo\n## Body\n\nbar\n"
    )
    errors = _errors(parse_message_text(path, text))
    assert _has_error_for(errors, "body:Action requested")


def test_missing_frontmatter_block_rejected() -> None:
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = "no frontmatter at all\n## Subject\n\nfoo\n"
    errors = _errors(parse_message_text(path, text))
    assert any(e.field == "<frontmatter>" for e in errors)


def test_producer_id_mismatch_with_filename_rejected() -> None:
    """Cross-check: frontmatter producer_id must match filename segment.

    Prevents a producer from renaming the file post-write to forge a
    different producer identity.
    """
    errors = _errors(
        _parse(
            filename="other-producer-20260526T085945Z.msg.md",
            producer_id="cowork-smoke-heartbeat",
        )
    )
    assert _has_error_for(errors, "producer_id")
    reason = next(
        e.message for e in errors if e.field == "producer_id" and "does not match" in e.message
    )
    assert "other-producer" in reason


# --- AC-Step1-1 ADVERSARIAL: extra keys / oversized subject / freeform action ---


def test_extra_frontmatter_keys_warn_only() -> None:
    """Unknown extra keys are tolerated (forward-compat) with a warning."""
    path = Path("loop/inbox/cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    text = (
        "---\n"
        "producer_id: cowork-smoke-heartbeat\n"
        "schema_version: 1\n"
        "message_type: smoke_heartbeat\n"
        "claimed_time: 2026-05-26T08:59:45Z\n"
        "time_authority: mtime\n"
        "future_field_for_v2: experimental\n"
        "---\n"
        "## Subject\n\ns\n## Body\n\nb\n## Action requested\n\nnone\n"
    )
    result = parse_message_text(path, text)
    # Should parse cleanly — warnings are advisory.
    assert isinstance(result, LoopMessage)


def test_oversized_subject_warns_not_errors() -> None:
    """Subject > 120 chars is a WARNING, not a parse failure (lenient)."""
    long_subject = "x" * 121
    result = _parse(subject=long_subject)
    # The parser should still produce a LoopMessage when only warnings exist.
    assert isinstance(result, LoopMessage)
    assert result.subject == long_subject


def test_subject_exactly_120_chars_clean() -> None:
    """Subject ≤ 120 chars passes without warning."""
    boundary_subject = "x" * 120
    result = _parse(subject=boundary_subject)
    assert isinstance(result, LoopMessage)
    assert result.subject == boundary_subject


# --- Filename grammar (portion of AC-Step1-3) ---


def test_filename_well_formed_no_rand() -> None:
    parts = parse_filename("cowork-smoke-heartbeat-20260526T085945Z.msg.md")
    assert isinstance(parts, FilenameParts)
    assert parts.producer_id == "cowork-smoke-heartbeat"
    assert parts.nonce == "20260526T085945Z"
    assert parts.rand is None


def test_filename_with_rand_suffix() -> None:
    parts = parse_filename("cowork-smoke-heartbeat-20260526T085945Z-x7k2.msg.md")
    assert isinstance(parts, FilenameParts)
    assert parts.rand == "x7k2"


def test_filename_short_producer_id_rejected() -> None:
    # Producer-id constraint: ^[a-z][a-z0-9-]{2,63}$ — minimum 3 chars.
    err = parse_filename("ab-20260526T085945Z.msg.md")
    assert isinstance(err, ValidationError)


def test_filename_uppercase_producer_rejected() -> None:
    err = parse_filename("Cowork-Heartbeat-20260526T085945Z.msg.md")
    assert isinstance(err, ValidationError)


def test_filename_underscore_in_producer_rejected() -> None:
    # Grammar is kebab-case only (no underscores in producer-id).
    err = parse_filename("cowork_smoke-20260526T085945Z.msg.md")
    assert isinstance(err, ValidationError)


def test_filename_malformed_nonce_rejected() -> None:
    # Nonce must be UTC ISO basic YYYYMMDDTHHMMSSZ (no separators).
    err = parse_filename("cowork-smoke-2026-05-26T08:59:45Z.msg.md")
    assert isinstance(err, ValidationError)


def test_filename_wrong_extension_rejected() -> None:
    err = parse_filename("cowork-smoke-20260526T085945Z.md")
    assert isinstance(err, ValidationError)


def test_filename_rand_wrong_charset_rejected() -> None:
    # base32 lowercase = [a-z2-7]; '1' and '0' are NOT in the alphabet.
    err = parse_filename("cowork-smoke-20260526T085945Z-x7k1.msg.md")
    assert isinstance(err, ValidationError)


def test_filename_rand_wrong_length_rejected() -> None:
    err = parse_filename("cowork-smoke-20260526T085945Z-x7k.msg.md")
    assert isinstance(err, ValidationError)


def test_filename_gitkeep_does_not_parse_as_message() -> None:
    """The §8 residual-risk-4 case: .gitkeep must not parse as a valid filename."""
    err = parse_filename(".gitkeep")
    assert isinstance(err, ValidationError)


def test_filename_gitkeep_with_msg_md_suffix_does_not_parse() -> None:
    """Even .gitkeep.msg.md must not parse — '.' is not [a-z] start."""
    err = parse_filename(".gitkeep.msg.md")
    assert isinstance(err, ValidationError)


# --- parse_message_file (filesystem path) ---


def test_parse_message_file_missing_file_returns_error(tmp_path: Path) -> None:
    missing = tmp_path / "loop" / "inbox" / "cowork-smoke-20260526T085945Z.msg.md"
    errors = _errors(parse_message_file(missing))
    assert any("cannot read file" in e.message for e in errors)


def test_parse_message_file_roundtrip(tmp_path: Path) -> None:
    inbox = tmp_path / "loop" / "inbox"
    inbox.mkdir(parents=True)
    filename = "cowork-smoke-heartbeat-20260526T085945Z.msg.md"
    _, text = _make_message(filename=filename)
    target = inbox / filename
    target.write_text(text, encoding="utf-8")
    result = parse_message_file(target)
    assert isinstance(result, LoopMessage)
    assert result.source == target
    assert result.producer_id == "cowork-smoke-heartbeat"


# --- ValidationError surface (smoke) ---


def test_validation_error_render() -> None:
    err = ValidationError("producer_id", "bad", "msg")
    assert err.is_error() is True
    assert "producer_id" in err.render()
    assert "error" in err.render()


def test_validation_error_warning_severity() -> None:
    err = ValidationError("x", "y", "z", Severity.WARNING)
    assert err.is_error() is False
    assert "warning" in err.render()
