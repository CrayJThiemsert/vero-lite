# vero-bridge wire format (v1)

> **Status:** Phase 1, frozen.
> **Codified in:** [`tools/vero_bridge/_schema.py`](../../tools/vero_bridge/_schema.py)
> **Plan:** [PLAN-0012 §AC-1](../plans/0012-vero-bridge.md) — "Transport contract is documented"
> **OQs resolved here:** OQ-T1 (fail-closed), OQ-T4 (serial-per-instance), OQ-V2 (`version: int` stub, v1-only)

This file is the **human-readable counterpart** to
[`tools/vero_bridge/_schema.py`](../../tools/vero_bridge/_schema.py).
The schema module is the **machine-checkable counterpart** to this
file. If they disagree, **the schema wins** (it is what the running
server enforces); update this file to match in the same PR.

## 1. Transport assumptions

Under **OQ-A RATIFIED A1 = stdio-MCP** (PLAN-0012 §Open Questions OQ-A;
session 21 PR #67), the vero-bridge server is a stdio-MCP server
spawned by Claude Desktop via the `mcpServers` entry in
`claude_desktop_config.json` (UWP path per
[Lesson #0016](../lessons/0016-claude-desktop-uwp-sandbox-config-path.md)).

The wire format documented here lives **inside** MCP's native JSON-RPC
framing — MCP/JSON-RPC handles the byte-level transport (delimiters,
request/response correlation via `id`); vero-bridge's wire format
defines the **payload envelope** carried inside each tool-call's
arguments.

**Tab-group routing (empirical, Lesson #0017 §3.1 corrected).** Under A1
stdio-MCP, Claude Desktop spawns 2 server instance pairs per
`mcpServers` entry on fresh launch:

- **Instance A** — Chat alone (PID varies per spawn cycle).
- **Instance B** — Code + Cowork share (PID varies per spawn cycle).

The server **cannot** discriminate Code from Cowork via transport-level
signals (they share PID, ppid, stdin_fd, stdout_fd, env). It **can**
discriminate Chat-vs-(Code∪Cowork) via PID. This shapes
[`claimed_tag`](#23-claimed_tag-string-non-empty-audit-only) and the
[AC-4 audit log](#52-audit-log-discipline-ac-4-b) design.

## 2. Envelope

Every bridge tool call carries a four-field envelope, decomposed across
the tool's keyword arguments:

```python
tool(
    version=1,                # required, int, MUST equal PROTOCOL_VERSION
    claimed_tag="<tag>",      # required, non-empty str, audit-only
    message_type="<type>",    # required, str matching MessageType
    payload={...},            # optional, dict[str, Any] or None
)
```

`version` + `claimed_tag` + `message_type` are envelope fields; the
remaining kwargs are the per-tool payload. Tools may split the payload
across named kwargs for ergonomics; the schema treats the full
remainder as a single dict.

### 2.1 `version` (int, required)

The wire format version. **Phase 1 server accepts only
`version: 1`.** Any other value raises `VersionMismatchError` with
`ErrorCode.VERSION_MISMATCH`.

`bool` is **not accepted** as `int` here even though `bool ⊆ int` in
Python — booleans are categorically not version numbers, and silently
coercing `True → 1` would defeat the OQ-V2 stub's intent (the field
must be a deliberate version assertion, not an accidental truthy
value).

**OQ-V2 deferral.** The `version: int` field is the
forward-compatibility stub for the deferred version-negotiation policy
(per-session vs per-call vs per-tab). Full policy is pinned when client
codepaths diverge or when a wire format v2 lands; until then, the field
is mandatory and v1-only.

### 2.2 `claimed_tag` (str, non-empty, audit-only)

The caller's self-asserted tab identity (typical values: `code`,
`chat`, `cowork`, `cray`, or any string the operator wants logged).
**Audit-only per OQ-T3 Option I** — the server does NOT verify this
against any observable signal; spoofing is always possible (empirical
T10/T11/T12 in the OQ-B probe research note §8.4).

The schema rejects only **structural** problems:

- Non-string types → `MalformedFrameError`.
- Empty string → `MalformedFrameError`.

It does **not** reject any value-based pattern. Server-side handlers
log the value as-is alongside observable transport facts (PID, ppid,
stdin_fd, stdout_fd, ts_ns) for the
[AC-4 (b) audit log](#52-audit-log-discipline-ac-4-b).

### 2.3 `message_type` (str, MessageType member)

The envelope's declared type, drives dispatch inside the server's
per-tool handler. The closed set is defined by the `MessageType` enum:

| `MessageType` | `.value` | Phase 1 status |
|---|---|---|
| `MessageType.ECHO` | `"echo"` | **Active** — required for AC-3 cross-client live evidence. |
| `MessageType.SIGNAL` | `"signal"` | **Reserved placeholder** for Phase 2+ ADR-013 D1 autonomy signal carriers. |
| `MessageType.DISPATCH_RECEIVE` | `"dispatch_receive"` | **Reserved placeholder** for Phase 2+ dispatch-without-authority handoff carriers. |

Unknown values raise `UnknownTypeError` with `ErrorCode.UNKNOWN_TYPE`.
The enum carries placeholders so that adding `signal` or
`dispatch_receive` in Phase 2 is a server-side handler change, not a
wire-format-breaking change.

### 2.4 `payload` (dict or None, optional)

Per-tool payload data. Empty dict by default. The schema validates:

- Type must be `dict` (or `None`, which is coerced to empty dict).
- All keys must be strings (JSON-shaped — non-string keys are an
  upstream parser mistake we surface fail-closed rather than coerce).

The schema does **not** validate payload contents — per-tool schema
lives in the tool handler (per the
[capability inventory](vero-bridge-capability-inventory.md) Phase 1
seven safe-for-all tools). Parsed envelopes carry the payload as a
`MappingProxyType` read-only view of a **defensive copy**, so input
aliasing is impossible.

## 3. Validation order and failure semantics (OQ-T1)

`parse_envelope()` validates fields in declaration order:

```
1. version       →  MalformedFrameError | VersionMismatchError
2. claimed_tag   →  MalformedFrameError
3. message_type  →  MalformedFrameError | UnknownTypeError
4. payload       →  MalformedFrameError
```

The **first failure raises immediately** — subsequent fields are not
validated (fail-closed per OQ-T1). This is observable in tests:

- `test_version_rejected_before_other_fields` — bad version + bad
  `claimed_tag` + bad `message_type` + bad `payload` all in one call;
  only `VersionMismatchError` is raised.
- `test_claimed_tag_rejected_before_message_type` — empty
  `claimed_tag` + unknown `message_type`; only `MalformedFrameError`
  (claimed_tag) is raised.

This ordering is part of the wire-format contract: clients can rely on
the first-error semantics to debug rejected calls. If the server
silently accumulated multiple errors and reported them as a batch, a
malicious client could probe the server's validation logic by counting
errors — instead, the server reports exactly one and stops.

### 3.1 Error response shape

`format_error_response(error)` produces the canonical wire-format error
payload returned to the client when a `BridgeError` is raised:

```python
{
    "ok": False,
    "error_code": "<ErrorCode value>",   # e.g. "version-mismatch"
    "error_message": "<human detail>",   # e.g. "version 2 unsupported (supported: 1)"
}
```

This is the **only** path a server-side handler should use to surface a
`BridgeError` to the client. Direct exception propagation across the
MCP boundary is **not allowed** — it would leak Python tracebacks into
the response and bypass the OQ-T1 fail-closed contract.

### 3.2 Error code catalog (OQ-T1)

| `ErrorCode` | Wire value | Raised when |
|---|---|---|
| `MALFORMED_FRAME` | `"malformed-frame"` | Field has wrong type or shape (missing, wrong primitive, non-string payload keys, etc.). |
| `VERSION_MISMATCH` | `"version-mismatch"` | `version` is the wrong int (any value ≠ `PROTOCOL_VERSION`). |
| `UNKNOWN_TYPE` | `"unknown-type"` | `message_type` is a `str` but does not match any `MessageType` member. |
| `CONNECTION_DROP` | `"connection-drop"` | Reserved for server-side transport layer (lost connection, peer hung up before response). Raised by the server in Step 2, not by `parse_envelope()`. |
| `TIMEOUT` | `"timeout"` | Reserved for server-side transport layer (call exceeded the bounded latency budget). Raised by the server in Step 2, not by `parse_envelope()`. |
| `TOOL_NOT_FOUND` | `"tool-not-found"` | The tool name on the call is not in the [AC-8 capability inventory](vero-bridge-capability-inventory.md). **Reserved** — Phase 1 enforces not-on-bridge structurally (an unregistered tool raises a FastMCP `ToolError` before any handler runs; see [inventory §4 FINDING-3](vero-bridge-capability-inventory.md#4-ac-8-negative-test-asserted-by-step-5)), so no server code emits this code yet; it is held for a hypothetical future generic-dispatcher surface. |
| `PATH_FORBIDDEN` | `"path-forbidden"` | A `read_repo_path` payload targets a path outside the Phase-1 read sandbox (absolute / `..` traversal / out-of-tree symlink / `.git/` / not git-tracked / not a regular file / oversize / non-UTF-8). The **one tool-policy code** — raised by the `read_repo_path` sandbox ([capability inventory §2.4](vero-bridge-capability-inventory.md#24-read_repo_path)), not by `parse_envelope()`; it reuses the §3.1 error envelope so payload rejections look identical to envelope rejections. |

Wire-value strings are stable across versions for a given
`ErrorCode` — a rename would be a wire-format breaking change
requiring a `version` bump.

## 4. Concurrency (OQ-T4)

The schema module is **concurrency-agnostic by design** — it owns no
state across calls; `parse_envelope()` is a pure function of its
kwargs. Concurrency discipline is enforced one layer up, in the
stdio-MCP server's per-instance call queue (Step 2 implementation):

- **Serial-per-instance.** The server queues incoming calls and
  processes one-at-a-time per instance (per Cray's OQ-T4 resolution
  2026-05-28 PM late, PR #69). Code + Cowork sharing instance B get
  serialized handling; within that instance the audit-log ordering is
  deterministic via the per-process `monotonic_counter` (§5.2) — not
  `ts_ns`, which is wall-clock.
- **No per-call parallelism in Phase 1.** Even pure-function tools
  (`echo`, `bridge_status`, `bridge_whoami`) are processed serially.
  The MCP/JSON-RPC protocol permits concurrent in-flight requests via
  `id` correlation, but the server does not exploit that in Phase 1.
- **Phase 2 reconsideration.** Concurrent-per-call becomes an option
  when evidence of contention pressure exists. Pre-Phase-2, no
  concurrency-related state is stored (deliberately — adding it would
  be premature optimization that constrains future design).

## 5. Implementation discipline

### 5.1 Stateless + stdlib-only

The schema module imports nothing outside the stdlib (`dataclasses`,
`enum`, `types`, `typing`). It owns no module-level state beyond the
`PROTOCOL_VERSION` constant. This mirrors the
[`tools/handoffs/_schema.py`](../../tools/handoffs/_schema.py)
discipline (Lesson #5 §4, PLAN-004 D1).

### 5.2 Audit log discipline (AC-4 (b))

The schema does not write audit logs — that is the **server's**
responsibility (Step 2). Per AC-4 (b), the server MUST log every
accepted call's `claimed_tag` alongside observable transport facts:

- `pid` — server process id
- `ppid` — parent process id (the `uv run` wrapper)
- `stdin_fd` — `readlink /proc/self/fd/0` (per-connection pipe inode)
- `stdout_fd` — `readlink /proc/self/fd/1`
- `ts_ns` — **epoch / wall-clock** nanoseconds (`time.time_ns()`).
  **Not monotonic** (FINDING-1, Step 4): it tracks wall time (can skew on
  NTP adjustment), correlates with `ts_iso`, and is **not** the ordering
  key. In the audit log it is an int (full precision); in client-facing
  responses it is a decimal string (§7.2, FINDING-2).
- `ts_iso` — ISO-8601 wall-clock timestamp (human-readable secondary).
- `monotonic_counter` — **per-process** call counter; the *actual*
  OQ-T4 serial-per-instance ordering key. It increments per call within
  one server process and **resets to 1 on each (re)spawn**, so it orders
  calls *within* an instance, not across the shared audit file. Step 4
  live evidence: Chat→instance-A and Cowork→instance-B each logged
  `monotonic_counter: 1` for their first call (independent per-process
  counters); a later Code+Cowork pair landing on the *same* re-spawned
  instance logged `1` then `2`.
- `env_keys_seen` — list of `CLAUDE_*` keys visible to the server
  (empirically `[]` per `bridge_whoami` probe — Desktop strips env)

Phase 1 audit log destination = appended JSONL under
`docs/research/private/` (gitignored). Phase 2+ may relocate this to a
tracked-but-redacted destination when authority operations land on the
bridge.

### 5.3 What this schema does NOT validate

- **Per-tool payload contracts.** Each tool in the
  [capability inventory](vero-bridge-capability-inventory.md) defines
  its own arg/return schema. The envelope is decoupled from payload.
- **Authority / authorization.** `claimed_tag` is audit-only. The
  bridge surface is restricted to tab-tier-safe operations per AC-8;
  authority-bearing operations are not on the bridge at all (they live
  under Code's internal mechanisms + ADR-013 D2 deterministic deny
  hook for the commit boundary).
- **JSON-RPC framing.** That is MCP's responsibility. If a frame is
  malformed at the JSON-RPC level, MCP rejects it before
  `parse_envelope()` ever sees it.

## 6. Versioning policy (OQ-V2)

Per OQ-V2 DEFERRED (Cray ratified 2026-05-28 PM late, PR #69), the
**negotiation policy** (per-session vs per-call vs per-tab) is decided
when client codepaths diverge. Until then, Phase 1 binds:

- Every wire frame carries `version: int` (mandatory; not optional).
- Phase 1 server accepts only `version: 1` (PROTOCOL_VERSION).
- Frames with any other value are rejected per the OQ-T1 fail-closed
  contract (`VersionMismatchError` → wire `error_code: "version-mismatch"`).

The `version` field is the **forward-compatibility stub** that lets
us defer the policy decision without baking in a wire-format breaking
change later. Adding `version: 2` support (whether as a
per-session-pinned upgrade, per-call permissive accept, or per-tab
divergence) is a Phase 2 design decision — at which point this section
gets a follow-up subsection.

## 7. Client invocation from Chat tab

> **Scope:** PLAN-0012 §Phase 1 Step 3a (Chat) — and, byte-for-byte
> identical, Step 3b (Cowork). The invocation pattern below applies to
> **any** tab (Chat, Cowork, Code); §7.4 records why no per-tab client
> wrapper exists.

### 7.1 How a tab reaches the bridge

A tab does not import any Python module to call the bridge. It invokes
the bridge tools **directly as MCP tools** from its own deferred-tool
list. Under A1 stdio-MCP (§1), the `mcpServers.vero-bridge` entry makes
the server's tools available to every connected tab; each tab loads
their schemas on demand via `ToolSearch`:

```
ToolSearch query: select:mcp__vero-bridge__echo,mcp__vero-bridge__bridge_status,mcp__vero-bridge__bridge_whoami,mcp__vero-bridge__read_repo_path
```

After the schemas load, the tab calls them like any other tool.

### 7.2 The Phase 1 invocation surface

The Phase 1 tools are invoked with these exact keyword arguments (the
authoritative source is the registered FastMCP tool surface in
[`tools/vero_bridge/server.py`](../../tools/vero_bridge/server.py); the
[contract test](../../tests/vero_bridge/test_chat_client.py) fails if this
table and that surface diverge):

| Tool (MCP name) | Required kwargs | Returns (shape — see [capability inventory](vero-bridge-capability-inventory.md) §2) |
|---|---|---|
| `mcp__vero-bridge__echo` | `version: int`, `claimed_tag: str`, `name: str` | `{"ok": True, "echoed": <name>, "ts_ns": <decimal str>}` |
| `mcp__vero-bridge__bridge_status` | `version: int`, `claimed_tag: str` | `{"ok": True, "protocol_version": 1, "uptime_s": <int>, "pid": <int>, "ppid": <int>, "last_call_ts_ns": <decimal str \| None>}` |
| `mcp__vero-bridge__bridge_whoami` | `version: int`, `claimed_tag: str` | `{"ok": True, "claimed_tag": <verbatim>, "pid": <int>, "ppid": <int>, "stdin_fd": <str>, "stdout_fd": <str>, "ts_ns": <decimal str>, "env_keys_seen": [<str>, ...]}` |
| `mcp__vero-bridge__read_repo_path` | `version: int`, `claimed_tag: str`, `path: str` | `{"ok": True, "path": <str>, "size": <int>, "content": <str>}` — or a `path-forbidden` error envelope (§3.1) when the path is outside the §2.4 read sandbox |

**`ts_ns` / `last_call_ts_ns` are decimal strings, not numbers (FINDING-2).**
These are int64 nanosecond stamps (~1.78×10¹⁸) that exceed `2**53`, the
largest integer an IEEE-754 double represents exactly. A client that
parses JSON numbers as doubles (most JS-based MCP clients — empirically
Cowork + the Code harness in the Step 4 live matrix) would silently
round them; only a big-int-aware client (empirically the Chat tab, which
surfaces FastMCP's text-content channel) preserved the exact value. To
make the round-trip lossless for **every** client, the server emits these
fields as decimal strings (`"1780022667682239521"`), so neither FastMCP
content channel (text *or* `structuredContent`) carries a JSON number for
them. The audit log keeps the int form (source of truth; §5.2).

A Chat-tab call looks like:

```
mcp__vero-bridge__echo(version=1, claimed_tag="chat", name="<round-trip token>")
mcp__vero-bridge__bridge_status(version=1, claimed_tag="chat")
mcp__vero-bridge__bridge_whoami(version=1, claimed_tag="chat")
```

### 7.3 `message_type` is supplied server-side, not by the tab

The §2 envelope carries four fields, but a tab passes only **three of
them as kwargs**: `version`, `claimed_tag`, and the per-tool payload
kwargs (`name` for `echo`; `path` for `read_repo_path`; none for
`bridge_status` / `bridge_whoami`). The fourth envelope field,
`message_type`, is **fixed by the tool the tab chose to call** — the
server's handler supplies it before `parse_envelope` runs (`echo` →
`MessageType.ECHO`; `bridge_status` / `bridge_whoami` / `read_repo_path`
→ `MessageType.SIGNAL`). A tab therefore selects a `message_type`
implicitly, by choosing a tool name; it never passes a `message_type`
kwarg. Doing so would be a wrong-arity call rejected by MCP before the
envelope is parsed.

`claimed_tag` is the tab's own self-asserted identity (`"chat"` from the
Chat tab, `"cowork"` from Cowork). It is **audit-only** (§2.2, OQ-T3
Option I): the server logs it verbatim but never authorizes against it.

### 7.4 Why raw invocation, not a Python client wrapper

Step 3a ships **no** `tools/vero_bridge/clients/` module. A wrapper
would have exactly one real caller — Code's own smoke tests — because
Chat and Cowork tabs cannot import a Python module into their context;
they can only call `mcp__vero-bridge__*` directly. A one-caller wrapper
is a premature abstraction (CLAUDE.md "Rule of Three"), and a transform
layer between the tab and the server would weaken the AC-7 byte-for-byte
cross-client parity guarantee (there would be something to drift). Raw
invocation keeps the surface minimal, keeps `server.py` the single
source of truth, and makes AC-7 parity trivially provable.

Raw invocation's one weakness — this doc rotting out of sync with
`server.py` — is closed by the contract test in
[`tests/vero_bridge/test_chat_client.py`](../../tests/vero_bridge/test_chat_client.py):
it asserts the §7.2 table matches the live registered tool surface and
that every documented tool + kwarg name appears in this section, so a
`server.py` signature change turns the test red until this doc is
updated to match.

A Python wrapper is deferred until a real multi-tool-sequence need
appears (the "third instance" under the Rule of Three) — at which point
it would be a Code-internal convenience, still leaving the tab-facing
surface as raw `mcp__vero-bridge__*` calls.

### 7.5 Cowork tab (Step 3b)

The Cowork tab invokes the bridge **identically** to the Chat tab
(§7.1–§7.3) — the only intended difference is `claimed_tag="cowork"`:

```
mcp__vero-bridge__echo(version=1, claimed_tag="cowork", name="<round-trip token>")
mcp__vero-bridge__bridge_status(version=1, claimed_tag="cowork")
mcp__vero-bridge__bridge_whoami(version=1, claimed_tag="cowork")
```

This identical surface **is** the AC-7 cross-client parity guarantee, and
it is exactly what the Raw-over-wrapper choice (§7.4) protects: with no
per-tab transform layer, there is nothing that could drift one client's
wire format away from the other's. Parity is asserted in
[`tests/vero_bridge/test_cowork_client.py`](../../tests/vero_bridge/test_cowork_client.py),
which compares the Chat-path and Cowork-path responses for the same
logical call and requires them to be identical except for fields that
are *meant* to vary — the echoed `claimed_tag` (reflects the caller) and
per-call / per-process observables (`ts_ns`, `uptime_s`,
`last_call_ts_ns`, `pid`, `ppid`, `stdin_fd`, `stdout_fd`).

Two Cowork-specific facts worth recording:

- **Why the bridge matters for Cowork.** Cowork cannot run repo tooling
  locally (Lesson #8 §1/§3 — UNC abort on `mcp__workspace__bash`; no
  local `pytest`). The bridge is the one execution channel Cowork has;
  OQ-B T6+T7 confirmed Cowork reaches `mcp__vero-bridge__*` end-to-end.
- **Cowork is transport-indistinguishable from Code.** Under tab-group
  routing (§1; Lesson #0017 §3.1), Cowork shares **instance B** with
  Code — same PID, ppid, stdin_fd, stdout_fd, env. The server cannot
  tell a Cowork call from a Code call at the transport layer; only the
  audit-only `claimed_tag` separates them, and that is spoofable (§2.2).
  This is the load-bearing fact behind the Step 5 adversarial anti-spoof
  matrix (AC-4 (c)): the audit log can prove Chat-vs-(Code∪Cowork) via
  PID, but **not** Code-vs-Cowork.

## 8. Change log

- **2026-05-28** — Initial Phase 1 v1 contract committed
  (PR for Step 1; codifies AC-1 + AC-8 partial, sets up AC-5 test
  surface). Schema discipline mirrors `tools/handoffs/_schema.py`
  (Lesson #5 §4) and `tools/loop/_schema.py` (PLAN-0010 §Step 3).
  OQ-T1 / OQ-T4 / OQ-V2 resolutions baked in from PR #69 ratifications.
- **2026-05-29** — Added §7 "Client invocation from Chat tab" (PLAN-0012
  Phase 1 Step 3a). Raw `mcp__vero-bridge__*` invocation + doc-rot guard
  ratified over a Python client wrapper; `message_type`-is-server-side
  clarified. Contract test: `tests/vero_bridge/test_chat_client.py`.
- **2026-05-29** — Added §7.5 "Cowork tab" (PLAN-0012 Phase 1 Step 3b).
  Cowork invocation is identical to Chat bar `claimed_tag="cowork"`;
  records the AC-7 parity definition, why the bridge is Cowork's one
  execution channel (Lesson #8), and the Code∪Cowork transport-
  indistinguishability behind the AC-4 (c) spoof matrix (Lesson #0017
  §3.1). Parity test: `tests/vero_bridge/test_cowork_client.py`.
- **2026-05-29** — **Step 4 live-evidence fixes (FINDING-1 + FINDING-2).**
  (1) §5.2/§4: `ts_ns` is **epoch wall-clock** ns, **not monotonic**; the
  OQ-T4 ordering key is the per-process `monotonic_counter` (resets per
  re-spawn). (2) §7.2: client-facing `ts_ns` + `last_call_ts_ns` are now
  **decimal strings** (`echo`/`bridge_whoami`/`bridge_status`) — int64 ns
  exceeds `2**53` and was being silently rounded by JSON-number-as-double
  clients (Cowork + Code harness) in the Step 4 matrix; Chat preserved it
  via the text-content channel. Audit log keeps the int. Server +
  unit-test changes land in the same PR; root cause: FastMCP dual-channel
  output (text vs `structuredContent`).
- **2026-05-29** — **Step 2b: first integration tool `read_repo_path`.**
  §7.1–§7.3 + §7.2 table add the `mcp__vero-bridge__read_repo_path`
  invocation surface (`version`, `claimed_tag`, `path`; `MessageType.SIGNAL`).
  §3.2 adds `ErrorCode.PATH_FORBIDDEN` (`"path-forbidden"`) — the one
  tool-policy code, raised by the read sandbox
  (`tools/vero_bridge/_repo_read.py`) and reusing the §3.1 error envelope.
  `TOOL_NOT_FOUND` reclassified as **reserved** (structural FastMCP
  enforcement per inventory §4 FINDING-3 — no server code emits it). Path
  sandbox = relative + no `..` + in-tree-after-symlink-resolve + not
  `.git/` + git-tracked allowlist + regular file + ≤2 MiB + UTF-8.
