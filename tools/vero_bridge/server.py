"""vero-bridge stdio-MCP server (production) — Phase 1 Steps 2 + 2b.

Implements the AC-2 lifecycle + AC-4 (b) audit log + the three
introspection tools (``echo`` / ``bridge_status`` / ``bridge_whoami``,
Step 2) and the first integration tool (``read_repo_path``, Step 2b) from
the Phase 1
:doc:`capability inventory <docs/conventions/vero-bridge-capability-inventory>`.

Under OQ-A RATIFIED A1 stdio-MCP, this server is spawned by Claude
Desktop via the ``mcpServers.vero-bridge`` entry in
``claude_desktop_config.json`` (UWP path per
:doc:`Lesson #0016 <docs/lessons/0016-claude-desktop-uwp-sandbox-config-path>`).
The server is long-lived for the Desktop session (per Lesson #0017 §3:
**stateless discipline mandatory**; no per-tab state accumulation across
the Desktop session).

Wire format + envelope validation: every tool invocation routes through
:func:`tools.vero_bridge.parse_envelope`. Any rejection (malformed
frame, version mismatch, unknown type) raises a :class:`BridgeError`
subclass; the tool wraps it via :func:`format_error_response` (the only
allowed ``BridgeError`` → client path per
:doc:`docs/conventions/vero-bridge-wire-format` §3.1).

Audit log: every accepted *and* rejected call appends one JSONL record
to :data:`tools.vero_bridge._audit_log.DEFAULT_LOG_PATH` per AC-4 (b).
The record captures ``claimed_tag`` (audit-only per OQ-T3 Option I)
alongside observable server-process signals (PID, ppid, stdin_fd,
stdout_fd, env_keys_seen, ts_ns, monotonic counter).

Safety boundaries preserved:

- **ADR-013 D2** — no path exposed to git operations (AC-4 (a)). The
  three tools shipped in this PR are pure introspection + echo; none
  invoke ``Bash``, ``Edit``, or any state-changing primitive.
- **OQ-T3 Option I** — ``claimed_tag`` is logged but NEVER used for
  authorization. The bridge surface is restricted to tab-tier-safe
  operations per the capability inventory; dangerous operations
  remain not-on-bridge.
- **OQ-T4 serial-per-instance** — sync tool handlers + single FastMCP
  event-loop dispatch. Concurrency-related state is deliberately
  absent (would constrain Phase 2 reconsideration).

Step 2b adds the integration tools. Shipped: ``read_repo_path`` (a
path-sandboxed, read-only repo-file reader; git-tracked allowlist, see
:mod:`tools.vero_bridge._repo_read`) and ``validate_handoff_frontmatter``
(in-process handoff-frontmatter validation via
:mod:`tools.vero_bridge._handoff_validate`). Still deferred to follow-ons:

- ``lint_status`` — needs git subprocess + STATUS frontmatter parse
  (Step 2b).
- ``dispatch_receive`` — needs gitignored receive-queue path (Step 2b
  or Step 5 alongside the dispatch flow integration).

Run via Desktop spawn (see ``mcpServers.vero-bridge`` config) or
manually for local testing::

    uv run --extra dev python -m tools.vero_bridge.server
"""

from __future__ import annotations

import os
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from tools.vero_bridge._audit_log import (
    _OBSERVABLE_ENV_PREFIXES,
    DEFAULT_LOG_PATH,
    _read_proc_fd,
    log_call,
)
from tools.vero_bridge._handoff_validate import validate_frontmatter_content
from tools.vero_bridge._repo_read import read_repo_file
from tools.vero_bridge._schema import (
    BridgeError,
    MalformedFrameError,
    MessageType,
    format_error_response,
    parse_envelope,
)

#: Server start timestamp (epoch seconds, integer). Used by
#: :func:`bridge_status` to report uptime. Captured at module import
#: time so the value is stable for the lifetime of the server process.
SERVER_START_TS: float = time.time()

#: Track the most recent successful call's ``ts_ns`` for the
#: :func:`bridge_status` ``last_call_ts_ns`` field. ``None`` until a
#: call lands; updated on every accepted (``outcome == "ok"``) call.
_last_call_ts_ns: int | None = None

#: The FastMCP application. Decorators below register each tool against
#: this instance; ``mcp.run()`` at module ``__main__`` starts the
#: stdio-MCP event loop.
mcp: FastMCP = FastMCP("vero-bridge")


def _update_last_call_ts(record: dict[str, Any]) -> None:
    """Record the most recent successful call timestamp.

    Only updates on ``outcome == "ok"`` so rejected calls (which still
    flow through the audit log) do not advance the "last successful
    call" pointer.
    """
    global _last_call_ts_ns
    if record.get("outcome") == "ok":
        _last_call_ts_ns = record["ts_ns"]


# ---------------------------------------------------------------------------
# Tool: echo
# ---------------------------------------------------------------------------


def _handle_echo(version: int, claimed_tag: str, name: str) -> dict[str, Any]:
    """Plain-function implementation of :func:`echo` (decoupled from
    FastMCP's decorator so unit tests can invoke it directly without
    going through stdio framing)."""
    try:
        env = parse_envelope(
            version=version,
            claimed_tag=claimed_tag,
            message_type=MessageType.ECHO.value,
            payload={"name": name},
        )
    except BridgeError as err:
        record = log_call(
            tool_name="echo",
            claimed_tag=claimed_tag,
            version=version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    record = log_call(
        tool_name="echo",
        claimed_tag=env.claimed_tag,
        version=env.version,
        outcome="ok",
    )
    _update_last_call_ts(record)
    return {
        "ok": True,
        "echoed": env.payload["name"],
        # ts_ns is an int64 nanosecond stamp (~1.78e18) that exceeds 2^53,
        # so it cannot survive a JSON-number-as-IEEE-754-double client
        # (FINDING-2, Step 4 live evidence). Returned as a decimal STRING so
        # every client — text-content *and* structuredContent consumers —
        # round-trips it losslessly. The audit log keeps the int (source of
        # truth; Python-read, no double).
        "ts_ns": str(record["ts_ns"]),
    }


@mcp.tool()
def echo(version: int, claimed_tag: str, name: str) -> dict[str, Any]:
    """AC-3 round-trip echo carrier. Returns the caller's ``name`` plus
    the server-side ``ts_ns`` of the call.

    Wire format: per
    :doc:`docs/conventions/vero-bridge-wire-format` §2. Fail-closed
    per OQ-T1. Audit-logged per AC-4 (b).
    """
    return _handle_echo(version=version, claimed_tag=claimed_tag, name=name)


# ---------------------------------------------------------------------------
# Tool: bridge_status
# ---------------------------------------------------------------------------


def _handle_bridge_status(version: int, claimed_tag: str) -> dict[str, Any]:
    """Plain-function implementation of :func:`bridge_status`."""
    try:
        env = parse_envelope(
            version=version,
            claimed_tag=claimed_tag,
            message_type=MessageType.SIGNAL.value,
        )
    except BridgeError as err:
        record = log_call(
            tool_name="bridge_status",
            claimed_tag=claimed_tag,
            version=version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    record = log_call(
        tool_name="bridge_status",
        claimed_tag=env.claimed_tag,
        version=env.version,
        outcome="ok",
    )
    _update_last_call_ts(record)
    uptime_s = int(time.time() - SERVER_START_TS)
    return {
        "ok": True,
        "protocol_version": env.version,
        "uptime_s": uptime_s,
        "pid": os.getpid(),
        "ppid": os.getppid(),
        # int64 ns → decimal string (or None when no call has landed yet).
        # Same 2^53 / JSON-double rationale as echo's ts_ns (FINDING-2).
        "last_call_ts_ns": str(_last_call_ts_ns) if _last_call_ts_ns is not None else None,
    }


@mcp.tool()
def bridge_status(version: int, claimed_tag: str) -> dict[str, Any]:
    """Report server operational state (version / uptime / pid /
    last-call timestamp).

    Useful for client-side liveness checks and the AC-3 cross-client
    smoke matrix. Read-only — no repo state surfaced.
    """
    return _handle_bridge_status(version=version, claimed_tag=claimed_tag)


# ---------------------------------------------------------------------------
# Tool: bridge_whoami
# ---------------------------------------------------------------------------


def _handle_bridge_whoami(version: int, claimed_tag: str) -> dict[str, Any]:
    """Plain-function implementation of :func:`bridge_whoami`."""
    try:
        env = parse_envelope(
            version=version,
            claimed_tag=claimed_tag,
            message_type=MessageType.SIGNAL.value,
        )
    except BridgeError as err:
        record = log_call(
            tool_name="bridge_whoami",
            claimed_tag=claimed_tag,
            version=version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    record = log_call(
        tool_name="bridge_whoami",
        claimed_tag=env.claimed_tag,
        version=env.version,
        outcome="ok",
    )
    _update_last_call_ts(record)
    return {
        "ok": True,
        "claimed_tag": env.claimed_tag,
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "stdin_fd": _read_proc_fd(0),
        "stdout_fd": _read_proc_fd(1),
        # int64 ns → decimal string (FINDING-2; same rationale as echo).
        "ts_ns": str(record["ts_ns"]),
        "env_keys_seen": sorted(k for k in os.environ if k.startswith(_OBSERVABLE_ENV_PREFIXES)),
    }


@mcp.tool()
def bridge_whoami(version: int, claimed_tag: str) -> dict[str, Any]:
    """Return the audit-log fingerprint for the current call.

    Echoes ``claimed_tag`` verbatim (audit-only per OQ-T3 Option I)
    alongside observable server-process signals (PID, ppid, stdin_fd,
    stdout_fd, ts_ns, env_keys_seen). Used by clients to self-audit how
    the server saw them, and by AC-4 (c) cross-tab anti-spoof tests to
    assert the per-call observable fingerprint.
    """
    return _handle_bridge_whoami(version=version, claimed_tag=claimed_tag)


# ---------------------------------------------------------------------------
# Tool: read_repo_path
# ---------------------------------------------------------------------------


def _handle_read_repo_path(version: int, claimed_tag: str, path: str) -> dict[str, Any]:
    """Plain-function implementation of :func:`read_repo_path`.

    Two rejection layers, both surfaced via :func:`format_error_response`
    and both audit-logged:

    - **Envelope** (``parse_envelope``) — version / claimed_tag / type.
    - **Tool policy** — an empty/non-str ``path`` is ``MALFORMED_FRAME``; a
      sandbox violation is ``PATH_FORBIDDEN`` (raised by
      :func:`tools.vero_bridge._repo_read.read_repo_file`).
    """
    try:
        env = parse_envelope(
            version=version,
            claimed_tag=claimed_tag,
            message_type=MessageType.SIGNAL.value,
            payload={"path": path},
        )
    except BridgeError as err:
        record = log_call(
            tool_name="read_repo_path",
            claimed_tag=claimed_tag,
            version=version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    try:
        requested = env.payload["path"]
        if not isinstance(requested, str) or not requested:
            raise MalformedFrameError("path must be a non-empty str")
        rel, size, content = read_repo_file(requested)
    except BridgeError as err:
        record = log_call(
            tool_name="read_repo_path",
            claimed_tag=env.claimed_tag,
            version=env.version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    record = log_call(
        tool_name="read_repo_path",
        claimed_tag=env.claimed_tag,
        version=env.version,
        outcome="ok",
    )
    _update_last_call_ts(record)
    return {"ok": True, "path": rel, "size": size, "content": content}


@mcp.tool()
def read_repo_path(version: int, claimed_tag: str, path: str) -> dict[str, Any]:
    """Read a repo-tracked file under the repo root and return its content.

    Phase-1 read-only sandbox (capability inventory §2.4): ``path`` must be
    relative, free of ``..``, inside the repo after symlink resolution, not
    under ``.git/``, **git-tracked**, a regular file, ≤2 MiB, and valid
    UTF-8. Any violation returns a ``path-forbidden`` error envelope (AC-5).
    No write path exists — this tool cannot mutate repo state (AC-8 /
    ADR-013 D2).
    """
    return _handle_read_repo_path(version=version, claimed_tag=claimed_tag, path=path)


# ---------------------------------------------------------------------------
# Tool: validate_handoff_frontmatter
# ---------------------------------------------------------------------------


def _handle_validate_handoff_frontmatter(
    version: int, claimed_tag: str, content: str
) -> dict[str, Any]:
    """Plain-function implementation of :func:`validate_handoff_frontmatter`.

    Note the two distinct success notions: ``ok`` is *transport* success
    (the call was well-formed and ran); ``valid`` is *content* validity (the
    frontmatter passed the schema). An invalid handoff is ``ok=True,
    valid=False`` — validation findings are a successful result, not an error.
    A non-str ``content`` is the only payload-level malformation
    (``MALFORMED_FRAME``); an *empty* string is a valid input that simply
    reports ``valid=False`` (missing frontmatter block).
    """
    try:
        env = parse_envelope(
            version=version,
            claimed_tag=claimed_tag,
            message_type=MessageType.SIGNAL.value,
            payload={"content": content},
        )
    except BridgeError as err:
        record = log_call(
            tool_name="validate_handoff_frontmatter",
            claimed_tag=claimed_tag,
            version=version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    try:
        received = env.payload["content"]
        if not isinstance(received, str):
            raise MalformedFrameError("content must be a str")
    except BridgeError as err:
        record = log_call(
            tool_name="validate_handoff_frontmatter",
            claimed_tag=env.claimed_tag,
            version=env.version,
            outcome="error",
            error_code=err.code.value,
        )
        _update_last_call_ts(record)
        return format_error_response(err)

    valid, errors = validate_frontmatter_content(received)
    record = log_call(
        tool_name="validate_handoff_frontmatter",
        claimed_tag=env.claimed_tag,
        version=env.version,
        outcome="ok",
    )
    _update_last_call_ts(record)
    return {"ok": True, "valid": valid, "errors": errors}


@mcp.tool()
def validate_handoff_frontmatter(version: int, claimed_tag: str, content: str) -> dict[str, Any]:
    """Validate a handoff frontmatter body against the committed schema.

    Runs ``tools/handoffs/_schema.py`` validation **in-process** (capability
    inventory §2.5) — the same logic the ``validate_handoff.py`` CLI uses —
    so Cowork can validate handoffs it authors without Code brokering the run
    (Lesson #8 K-1). Pure validation: no filesystem write, no state mutation.

    Returns ``{"ok": True, "valid": <bool>, "errors": [{field, value,
    message, severity}, ...]}``. ``ok`` is transport success; ``valid`` is
    content validity (no error-severity finding). An invalid handoff is
    ``ok=True, valid=False`` with the findings.
    """
    return _handle_validate_handoff_frontmatter(
        version=version, claimed_tag=claimed_tag, content=content
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the stdio-MCP server event loop.

    Invoked by Claude Desktop via the ``mcpServers.vero-bridge.command +
    args`` entry in ``claude_desktop_config.json``. May also be run
    manually for local testing::

        uv run --extra dev python -m tools.vero_bridge.server

    The audit log is initialized lazily on the first call — no
    pre-flight I/O at server-process spawn time (a missing parent dir
    would otherwise block startup; instead the audit module creates
    parents on first write).
    """
    # Touch DEFAULT_LOG_PATH to surface configuration mistakes early
    # (the import would have failed if the path was unconstructable),
    # but do NOT create it pre-flight — see docstring.
    _ = DEFAULT_LOG_PATH  # reference to keep the import in __main__ scope
    mcp.run()


if __name__ == "__main__":
    main()
