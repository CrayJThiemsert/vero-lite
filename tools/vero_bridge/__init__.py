"""vero-bridge — MCP transport between Code (server) ↔ (Chat + Cowork) clients.

Phase 1 surface = wire-format schema + capability inventory + (later)
the stdio-MCP server itself.

This package codifies the wire-format contract documented in
``docs/conventions/vero-bridge-wire-format.md``. The contract is the
machine-checkable counterpart to the document; the document is the
human-readable counterpart to this code. They are kept in sync by
review.

Public re-exports below are the only stable surface; everything else
under this package is implementation detail.
"""

from __future__ import annotations

from tools.vero_bridge._schema import (
    PROTOCOL_VERSION,
    BridgeError,
    Envelope,
    ErrorCode,
    MalformedFrameError,
    MessageType,
    PathForbiddenError,
    UnknownTypeError,
    VersionMismatchError,
    format_error_response,
    parse_envelope,
)

__all__ = [
    "PROTOCOL_VERSION",
    "BridgeError",
    "Envelope",
    "ErrorCode",
    "MalformedFrameError",
    "MessageType",
    "PathForbiddenError",
    "UnknownTypeError",
    "VersionMismatchError",
    "format_error_response",
    "parse_envelope",
]
