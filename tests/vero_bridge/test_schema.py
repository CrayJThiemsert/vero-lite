"""Tests for the vero-bridge wire-format schema.

Covers AC-1 (transport contract is documented + machine-checkable) and
the OQ-T1 / OQ-V2 / OQ-T3 resolutions per PLAN-0012 PR #69:

- **Happy path** — well-formed envelopes parse into typed
  :class:`Envelope` instances.
- **Boundary** — version exactly equal to :data:`PROTOCOL_VERSION`;
  empty payload; long ``claimed_tag``.
- **Fail-closed (OQ-T1)** — every malformed-frame / version-mismatch /
  unknown-type rejection raises the matching :class:`BridgeError`
  subclass with the matching :class:`ErrorCode`. No silent degradation.
- **OQ-V2 version stub** — versions 0 and 2 both rejected
  (forward-compatibility stub is binding, not advisory).
- **OQ-T3 Option I claimed_tag audit-only** — server echoes ``claimed_tag``
  verbatim regardless of value (spoofing always possible per the empirical
  T10/T11 evidence). Validation rejects only structural problems
  (wrong type, empty string), not content.

Full AC-5 cross-client matrix tests live in Step 5
(``tests/vero_bridge/test_server_roundtrip.py`` — not minted yet).
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from tools.vero_bridge import (
    PROTOCOL_VERSION,
    BridgeError,
    ErrorCode,
    MalformedFrameError,
    MessageType,
    PathForbiddenError,
    UnknownTypeError,
    VersionMismatchError,
    format_error_response,
    parse_envelope,
)

# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


def test_protocol_version_is_one() -> None:
    """Phase 1 wire format is v1; bumping is a wire-format breaking change."""
    assert PROTOCOL_VERSION == 1


def test_message_type_members_are_stable() -> None:
    """The enum value strings are wire-format identifiers — stable across
    versions. Any rename would be a wire-format breaking change."""
    assert MessageType.ECHO.value == "echo"
    assert MessageType.SIGNAL.value == "signal"
    assert MessageType.DISPATCH_RECEIVE.value == "dispatch_receive"
    assert {m.value for m in MessageType} == {"echo", "signal", "dispatch_receive"}


def test_error_code_members_are_stable() -> None:
    """Error code strings are wire-format identifiers carried on the
    response payload — they must not drift without a version bump."""
    expected = {
        "connection-drop",
        "timeout",
        "malformed-frame",
        "version-mismatch",
        "unknown-type",
        "tool-not-found",
        "path-forbidden",
    }
    assert {c.value for c in ErrorCode} == expected


# ---------------------------------------------------------------------------
# Happy path — parse_envelope on well-formed input
# ---------------------------------------------------------------------------


def test_parse_minimal_echo_envelope() -> None:
    env = parse_envelope(version=1, claimed_tag="code", message_type="echo")
    assert env.version == 1
    assert env.claimed_tag == "code"
    assert env.message_type is MessageType.ECHO
    assert dict(env.payload) == {}


def test_parse_envelope_with_payload() -> None:
    env = parse_envelope(
        version=1,
        claimed_tag="code",
        message_type="echo",
        payload={"name": "round-trip-1", "n": 42},
    )
    assert env.payload["name"] == "round-trip-1"
    assert env.payload["n"] == 42


def test_parse_envelope_payload_is_defensive_copy() -> None:
    """Mutating the caller's payload dict after parse must not affect
    the parsed envelope (input aliasing would defeat fail-closed)."""
    payload: dict[str, object] = {"key": "value"}
    env = parse_envelope(
        version=1,
        claimed_tag="code",
        message_type="echo",
        payload=payload,
    )
    payload["key"] = "MUTATED"
    payload["new"] = "INJECTED"
    assert env.payload["key"] == "value"
    assert "new" not in env.payload


def test_parsed_envelope_payload_is_read_only() -> None:
    """Downstream code must not be able to mutate a parsed envelope's
    payload — :class:`Envelope` is frozen and the payload view is a
    :class:`MappingProxyType`."""
    env = parse_envelope(
        version=1,
        claimed_tag="code",
        message_type="echo",
        payload={"k": "v"},
    )
    assert isinstance(env.payload, MappingProxyType)
    with pytest.raises(TypeError):
        env.payload["k"] = "MUTATED"  # type: ignore[index]


def test_parse_envelope_payload_none_is_empty() -> None:
    env = parse_envelope(version=1, claimed_tag="code", message_type="echo", payload=None)
    assert dict(env.payload) == {}


def test_envelope_is_frozen() -> None:
    """:class:`Envelope` is ``frozen=True`` — accidental field
    reassignment must fail at runtime."""
    env = parse_envelope(version=1, claimed_tag="code", message_type="echo")
    with pytest.raises(dataclasses.FrozenInstanceError):
        env.version = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Per-tab claimed_tag audit-only — OQ-T3 Option I
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag", ["code", "chat", "cowork", "cray", "anything-else"])
def test_claimed_tag_echoed_verbatim_regardless_of_value(tag: str) -> None:
    """Server echoes ``claimed_tag`` verbatim — no value-based rejection.
    Per OQ-T3 Option I capability-by-tool-design, spoofing is always
    possible; validation rejects only structural problems."""
    env = parse_envelope(version=1, claimed_tag=tag, message_type="echo")
    assert env.claimed_tag == tag


def test_claimed_tag_long_value_accepted() -> None:
    """Long ``claimed_tag`` is structurally valid (server logs it as-is;
    truncation/sanitization is a server-side audit-log concern, not a
    schema concern)."""
    long_tag = "x" * 4096
    env = parse_envelope(version=1, claimed_tag=long_tag, message_type="echo")
    assert env.claimed_tag == long_tag


# ---------------------------------------------------------------------------
# Boundary
# ---------------------------------------------------------------------------


def test_version_exactly_protocol_version_accepted() -> None:
    env = parse_envelope(
        version=PROTOCOL_VERSION,
        claimed_tag="code",
        message_type="echo",
    )
    assert env.version == PROTOCOL_VERSION


@pytest.mark.parametrize("mt", ["echo", "signal", "dispatch_receive"])
def test_all_known_message_types_parse(mt: str) -> None:
    env = parse_envelope(version=1, claimed_tag="code", message_type=mt)
    assert env.message_type is MessageType(mt)


# ---------------------------------------------------------------------------
# Fail-closed — version field (OQ-V2 stub binding)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_version", [0, 2, 99, -1])
def test_version_mismatch_rejected(bad_version: int) -> None:
    """Versions other than 1 are rejected with VERSION_MISMATCH (OQ-V2
    stub is binding — policy decision deferred but acceptance is locked
    to v1 only for Phase 1)."""
    with pytest.raises(VersionMismatchError) as excinfo:
        parse_envelope(version=bad_version, claimed_tag="code", message_type="echo")
    assert excinfo.value.code is ErrorCode.VERSION_MISMATCH
    assert excinfo.value.got == bad_version
    assert excinfo.value.supported == PROTOCOL_VERSION


def test_version_zero_rejected() -> None:
    """Spelled-out 0 case so reviewers see the exact OQ-V2 binding line."""
    with pytest.raises(VersionMismatchError):
        parse_envelope(version=0, claimed_tag="code", message_type="echo")


def test_version_two_rejected() -> None:
    """Spelled-out 2 case so reviewers see the exact OQ-V2 binding line."""
    with pytest.raises(VersionMismatchError):
        parse_envelope(version=2, claimed_tag="code", message_type="echo")


@pytest.mark.parametrize("bad", ["1", 1.0, None, True, False, [1], {"v": 1}])
def test_version_wrong_type_rejected(bad: object) -> None:
    """``version`` must be a plain ``int`` (``bool`` is rejected even though
    ``bool ⊆ int`` in Python — booleans are categorically not version
    numbers)."""
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(version=bad, claimed_tag="code", message_type="echo")
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "version" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# Fail-closed — claimed_tag field
# ---------------------------------------------------------------------------


def test_claimed_tag_empty_rejected() -> None:
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(version=1, claimed_tag="", message_type="echo")
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "claimed_tag" in str(excinfo.value).lower()


@pytest.mark.parametrize("bad", [None, 1, 1.5, True, [], {"x": 1}, b"code"])
def test_claimed_tag_wrong_type_rejected(bad: object) -> None:
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(version=1, claimed_tag=bad, message_type="echo")
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "claimed_tag" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# Fail-closed — message_type field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["", "Echo", "ECHO", "not-a-type", "unknown"])
def test_unknown_message_type_rejected(bad: str) -> None:
    with pytest.raises(UnknownTypeError) as excinfo:
        parse_envelope(version=1, claimed_tag="code", message_type=bad)
    assert excinfo.value.code is ErrorCode.UNKNOWN_TYPE
    assert excinfo.value.got == bad


@pytest.mark.parametrize("bad", [None, 1, 1.5, True, [], {"t": "echo"}])
def test_message_type_wrong_type_rejected(bad: object) -> None:
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(version=1, claimed_tag="code", message_type=bad)
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "message_type" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# Fail-closed — payload field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [1, "string", 1.5, True, [], (), b"payload"])
def test_payload_wrong_type_rejected(bad: object) -> None:
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(
            version=1,
            claimed_tag="code",
            message_type="echo",
            payload=bad,
        )
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "payload" in str(excinfo.value).lower()


def test_payload_non_string_keys_rejected() -> None:
    """JSON payloads only have string keys — anything else is a parser
    upstream-mistake we surface fail-closed rather than coerce."""
    bad_payload = {1: "value"}
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(
            version=1,
            claimed_tag="code",
            message_type="echo",
            payload=bad_payload,
        )
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "payload" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# Validation order — version checked first (OQ-T1: first failure wins)
# ---------------------------------------------------------------------------


def test_version_rejected_before_other_fields() -> None:
    """First-failure-wins: a wrong version is reported even when other
    fields are also malformed. This is the OQ-T1 fail-closed semantics
    — the server stops processing on the first rejection."""
    with pytest.raises(VersionMismatchError):
        parse_envelope(
            version=99,
            claimed_tag="",  # also bad — but version is checked first
            message_type="not-a-type",
            payload="not-a-dict",
        )


def test_claimed_tag_rejected_before_message_type() -> None:
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_envelope(
            version=1,
            claimed_tag="",
            message_type="not-a-type",  # would be UnknownTypeError if reached
        )
    assert excinfo.value.code is ErrorCode.MALFORMED_FRAME
    assert "claimed_tag" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# Error response formatting
# ---------------------------------------------------------------------------


def test_format_error_response_for_version_mismatch() -> None:
    err = VersionMismatchError(got=2, supported=1)
    response = format_error_response(err)
    assert response == {
        "ok": False,
        "error_code": "version-mismatch",
        "error_message": "version 2 unsupported (supported: 1)",
    }


def test_format_error_response_for_malformed_frame() -> None:
    err = MalformedFrameError("payload must be dict or null, got str")
    response = format_error_response(err)
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"
    assert "payload must be dict" in response["error_message"]


def test_format_error_response_for_unknown_type() -> None:
    err = UnknownTypeError("not-a-type")
    response = format_error_response(err)
    assert response["ok"] is False
    assert response["error_code"] == "unknown-type"
    assert "not-a-type" in response["error_message"]


def test_format_error_response_for_path_forbidden() -> None:
    """``PathForbiddenError`` is a tool-policy rejection that still uses the
    uniform §3.1 error envelope so the client sees one consistent shape."""
    err = PathForbiddenError("../../etc/passwd", "parent-directory traversal ('..') is not allowed")
    response = format_error_response(err)
    assert response["ok"] is False
    assert response["error_code"] == "path-forbidden"
    assert "../../etc/passwd" in response["error_message"]
    assert err.requested == "../../etc/passwd"


def test_bridge_error_subclasses_carry_correct_code() -> None:
    """Each subclass binds its :class:`ErrorCode` at construction
    (never None, never wrong) — guard against accidental refactor that
    forgets to wire ``code``."""
    assert MalformedFrameError("x").code is ErrorCode.MALFORMED_FRAME
    assert VersionMismatchError(got=99, supported=1).code is ErrorCode.VERSION_MISMATCH
    assert UnknownTypeError("x").code is ErrorCode.UNKNOWN_TYPE
    assert PathForbiddenError("x", "reason").code is ErrorCode.PATH_FORBIDDEN


def test_bridge_error_is_subclass_of_exception() -> None:
    """:class:`BridgeError` must subclass :class:`Exception` so callers
    can ``except BridgeError`` to handle every wire-format rejection
    uniformly without catching unrelated exceptions."""
    assert issubclass(BridgeError, Exception)
    assert issubclass(MalformedFrameError, BridgeError)
    assert issubclass(VersionMismatchError, BridgeError)
    assert issubclass(UnknownTypeError, BridgeError)
    assert issubclass(PathForbiddenError, BridgeError)
