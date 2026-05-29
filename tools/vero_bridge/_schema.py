"""vero-bridge wire-format schema: envelope parsing + validation (stdlib-only).

This is the machine-checkable counterpart to
``docs/conventions/vero-bridge-wire-format.md`` and codifies AC-1 of
PLAN-0012 (`vero-bridge`) under the OQ-T1 / OQ-T4 / OQ-V2 resolutions
ratified 2026-05-28 PM late (PR #69):

- **OQ-T1 fail-closed.** Any rejection raises a :class:`BridgeError`
  subclass with a typed :class:`ErrorCode` — no silent degradation, no
  retry, no fallback. The server reports the error via
  :func:`format_error_response` and returns to idle.
- **OQ-T4 serial-per-instance.** This module is concurrency-agnostic by
  design: it owns no state across calls. Concurrency discipline is
  enforced one layer up (the stdio-MCP server's per-instance call queue
  in Step 2).
- **OQ-V2 ``version: int`` field, v1 only.** :data:`PROTOCOL_VERSION` is
  the single supported wire format version for Phase 1. Frames with a
  different ``version`` are rejected with :class:`VersionMismatchError`
  (``ErrorCode.VERSION_MISMATCH``). Version negotiation policy
  (per-session vs per-call vs per-tab) is deferred per OQ-V2.

Dependency-free (stdlib only). Mirrors the
``tools/handoffs/_schema.py`` discipline (dataclass-typed, fail-closed,
enum-driven closed sets) — adapted for runtime wire-format validation
(raise-on-reject) rather than file-frontmatter validation (collect
findings).

Under A1 stdio-MCP (OQ-A RATIFIED), MCP/JSON-RPC handles transport
framing; this schema validates the *payload envelope* carried inside
each MCP tool-call's arguments. Every bridge tool's call shape is::

    tool(version=1, claimed_tag="<tag>", **type_specific_kwargs)

The shared ``version`` + ``claimed_tag`` pair is the envelope; the
remaining kwargs are the per-tool payload (validated by the tool, not
by this module — the envelope concerns are decoupled from the payload).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

#: The single wire-format version supported in Phase 1. Per OQ-V2
#: DEFERRED, the server accepts only this value; any other version
#: raises :class:`VersionMismatchError`.
PROTOCOL_VERSION: int = 1


class MessageType(Enum):
    """Closed set of envelope message types.

    Phase 1 ships ``ECHO`` only (AC-3). ``SIGNAL`` and
    ``DISPATCH_RECEIVE`` are reserved placeholders for Phase 2+ — the
    enum carries them so that future wire format extensions do not
    require a wire-format-breaking change to the type field.
    """

    ECHO = "echo"
    SIGNAL = "signal"
    DISPATCH_RECEIVE = "dispatch_receive"


class ErrorCode(Enum):
    """Closed set of wire-format error codes (OQ-T1 fail-closed contract).

    Every :class:`BridgeError` carries exactly one of these. The
    ``ErrorCode.value`` strings are the canonical wire-format error
    identifiers and are stable across versions for a given code (a
    rename would be a wire-format breaking change requiring a version
    bump).

    Most codes are *envelope/transport* level (raised by
    :func:`parse_envelope`). ``PATH_FORBIDDEN`` is the one *tool-policy*
    code in Phase 1 — raised by the ``read_repo_path`` sandbox
    (:mod:`tools.vero_bridge._repo_read`) so that a payload-level rejection
    reuses the same uniform error envelope as an envelope rejection.
    """

    CONNECTION_DROP = "connection-drop"
    TIMEOUT = "timeout"
    MALFORMED_FRAME = "malformed-frame"
    VERSION_MISMATCH = "version-mismatch"
    UNKNOWN_TYPE = "unknown-type"
    TOOL_NOT_FOUND = "tool-not-found"
    PATH_FORBIDDEN = "path-forbidden"


class BridgeError(Exception):
    """Base for every wire-format / transport validation failure.

    All instances carry a :class:`ErrorCode` accessible via the
    ``code`` attribute; the exception ``args[0]`` is the human-readable
    message rendered by :func:`format_error_response` into the wire
    error payload.
    """

    code: ErrorCode

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class MalformedFrameError(BridgeError):
    """Envelope structure is wrong (missing field, wrong type, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.MALFORMED_FRAME, message)


class VersionMismatchError(BridgeError):
    """``version`` field does not match :data:`PROTOCOL_VERSION`."""

    got: int
    supported: int

    def __init__(self, got: int, supported: int) -> None:
        super().__init__(
            ErrorCode.VERSION_MISMATCH,
            f"version {got} unsupported (supported: {supported})",
        )
        self.got = got
        self.supported = supported


class UnknownTypeError(BridgeError):
    """``message_type`` field does not match any :class:`MessageType`."""

    got: str

    def __init__(self, got: str) -> None:
        allowed = ", ".join(member.value for member in MessageType)
        super().__init__(
            ErrorCode.UNKNOWN_TYPE,
            f"unknown message_type: {got!r}; allowed: {allowed}",
        )
        self.got = got


class PathForbiddenError(BridgeError):
    """A tool payload requested a path outside the Phase-1 read sandbox.

    Unlike the other :class:`BridgeError` subclasses (which are *envelope*
    rejections raised by :func:`parse_envelope`), this is a **tool-level
    policy** rejection raised by the ``read_repo_path`` sandbox
    (:mod:`tools.vero_bridge._repo_read`) — e.g. ``..`` traversal, an
    out-of-tree symlink target, a ``.git/`` path, a non-git-tracked path,
    a non-regular file, an oversize file, or non-UTF-8 content. It reuses
    the uniform transport-error envelope (``ErrorCode.PATH_FORBIDDEN`` →
    :func:`format_error_response`) so the client sees one consistent error
    shape regardless of which layer rejected the call.
    """

    requested: str

    def __init__(self, requested: str, reason: str) -> None:
        super().__init__(
            ErrorCode.PATH_FORBIDDEN,
            f"path {requested!r} rejected: {reason}",
        )
        self.requested = requested


@dataclass(frozen=True)
class Envelope:
    """A fully parsed + typed wire-format envelope.

    Every bridge tool call carries one of these (decomposed across the
    tool's kwargs). The envelope is immutable; payload is wrapped in a
    read-only mapping to prevent accidental downstream mutation of the
    parsed-as-validated state.

    Fields:

    - ``version``: The wire format version. Always equal to
      :data:`PROTOCOL_VERSION` for any envelope this module produces
      (mismatches raise before construction).
    - ``claimed_tag``: The caller's self-asserted tab identity. **Audit-only
      per OQ-T3 Option I** — the server does NOT verify this against any
      observable signal; spoofing is always possible. Server-side
      handlers log this alongside observable transport facts (PID,
      ppid, stdin_fd, stdout_fd, ts_ns) for the AC-4 (b) audit log and
      AC-4 (c) anti-spoof matrix.
    - ``message_type``: The envelope's declared type. Drives dispatch
      inside the server's per-tool handler.
    - ``payload``: The per-tool payload (read-only mapping). Empty by
      default; tool-specific validation lives in the tool's handler,
      not in this module.
    """

    version: int
    claimed_tag: str
    message_type: MessageType
    payload: MappingProxyType[str, Any] = field(
        default_factory=lambda: MappingProxyType({}),
    )


def _validate_version(value: Any) -> int:
    """Validate the envelope ``version`` field. See :func:`parse_envelope`."""
    # Strict int (bool is rejected even though bool ⊆ int in Python — booleans
    # are categorically not version numbers).
    if not isinstance(value, int) or isinstance(value, bool):
        raise MalformedFrameError(f"version must be int, got {type(value).__name__}")
    if value != PROTOCOL_VERSION:
        raise VersionMismatchError(got=value, supported=PROTOCOL_VERSION)
    return value


def _validate_claimed_tag(value: Any) -> str:
    """Validate the envelope ``claimed_tag`` field. See :func:`parse_envelope`."""
    if not isinstance(value, str):
        raise MalformedFrameError(f"claimed_tag must be str, got {type(value).__name__}")
    if not value:
        raise MalformedFrameError("claimed_tag must be non-empty")
    return value


def _validate_message_type(value: Any) -> MessageType:
    """Validate the envelope ``message_type`` field. See :func:`parse_envelope`."""
    if not isinstance(value, str):
        raise MalformedFrameError(f"message_type must be str, got {type(value).__name__}")
    try:
        return MessageType(value)
    except ValueError:
        raise UnknownTypeError(value) from None


def _validate_payload(value: Any) -> MappingProxyType[str, Any]:
    """Validate the envelope ``payload`` field. See :func:`parse_envelope`."""
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise MalformedFrameError(f"payload must be dict or null, got {type(value).__name__}")
    # Keys are validated as strings — JSON-shaped payloads only carry
    # string keys; anything else is an upstream parser mistake we
    # surface fail-closed rather than coerce silently.
    for key in value:
        if not isinstance(key, str):
            raise MalformedFrameError(f"payload keys must be str, got {type(key).__name__}")
    # Defensive copy: parsed envelope must not alias caller state.
    return MappingProxyType(dict(value))


def parse_envelope(
    *,
    version: Any,
    claimed_tag: Any,
    message_type: Any,
    payload: Any = None,
) -> Envelope:
    """Parse + validate an inbound envelope; raise on any rejection.

    All four envelope fields are validated in declaration order:
    ``version`` → ``claimed_tag`` → ``message_type`` → ``payload``. The
    first failure raises immediately (fail-closed — OQ-T1); subsequent
    fields are not validated.

    Args:
        version: Must be a plain ``int`` (not ``bool``) and equal to
            :data:`PROTOCOL_VERSION`.
        claimed_tag: Must be a non-empty ``str``. Content is opaque to
            this module — the server logs it as-is.
        message_type: Must be a ``str`` matching one of
            :class:`MessageType` ``.value`` strings.
        payload: Must be a ``dict[str, Any]`` or ``None`` (treated as
            empty). Tool-specific schema lives in the tool handler.

    Returns:
        A frozen :class:`Envelope` instance.

    Raises:
        MalformedFrameError: When a field has the wrong type or shape.
        VersionMismatchError: When ``version`` is the wrong int.
        UnknownTypeError: When ``message_type`` is not a known enum value.
    """
    return Envelope(
        version=_validate_version(version),
        claimed_tag=_validate_claimed_tag(claimed_tag),
        message_type=_validate_message_type(message_type),
        payload=_validate_payload(payload),
    )


def format_error_response(error: BridgeError) -> dict[str, Any]:
    """Build the wire-format error response for a :class:`BridgeError`.

    Returned dict shape is the canonical error response that bridge
    tools serialize back to the client::

        {
          "ok": False,
          "error_code": "<ErrorCode value>",
          "error_message": "<human-readable detail>",
        }

    This is the *only* path a server-side handler should use to surface
    a :class:`BridgeError` to the client — direct exception propagation
    across the MCP boundary is not allowed (would leak Python tracebacks
    + bypass the OQ-T1 fail-closed contract).
    """
    return {
        "ok": False,
        "error_code": error.code.value,
        "error_message": str(error),
    }
