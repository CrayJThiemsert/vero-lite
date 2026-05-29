# vero-bridge capability inventory (Phase 1)

> **Status:** Phase 1, frozen.
> **Plan:** [PLAN-0012 §AC-8](../plans/0012-vero-bridge.md) — "Capability-by-tool-design discipline (Option I identity model enforcement)"
> **Source draft:** PR #67 completion handoff §3 (Cowork-drafted; this PR materializes as a tracked file)
> **Identity model:** OQ-T3 RESOLVED Option I — `claimed_tag` is audit-only; the bridge surface is restricted to tab-tier-safe operations

This document is the **canonical "what is exposed where"** reference
for the vero-bridge MCP transport. Every tool exposed on the bridge is
listed here with its capability classification; every dangerous
operation explicitly kept off the bridge is listed too, with the
mechanism that handles it instead.

## 1. Classification taxonomy (AC-8)

Three classes per PLAN-0012 §Phase 1 Step 1:

| Class | Phase 1 binding | Definition |
|---|---|---|
| **safe-for-all** | Active. | Safe for any tab (Chat, Cowork, Code) to invoke without violating tier boundaries (ADR-009 D5; ADR-013 D1/D2). Read-only repo state, validate-without-commit, contract description, echo, dispatch-receive without authority. |
| **safe-for-some** | **Empty in Phase 1** (per [OQ-V1 RESOLVED](../plans/0012-vero-bridge.md#open-questions)). | Reserved for Phase 2+. Tools that are safe for some tabs with documented caveats. Phase 1 keeps the bridge surface uniform per OQ-V1; capability differentiation deferred. |
| **not-on-bridge** | Active (as exclusion list). | Dangerous operations remaining under Code's internal mechanisms or under ADR-013 D2's deterministic deny hook. **Not exposed as MCP tools at all** — attempting to invoke one returns a transport-layer `tool-not-found` error per AC-5 negative test. |

**Rationale (Option I capability-by-tool-design).** Under the
empirically-corrected tab-group routing (Lesson #0017 §3.1 — Code +
Cowork share instance B and are transport-indistinguishable), the
server cannot enforce per-tab capability boundaries at the transport
layer. So the discipline becomes: **don't expose dangerous tools in
the first place**. The not-on-bridge list is the load-bearing safety
boundary; the safe-for-all set is the trust boundary; safe-for-some
will exist only when an out-of-band identity mechanism lands.

## 2. Phase 1 tool surface (safe-for-all)

All seven tools below are exposed uniformly to every client (Chat,
Cowork, Code) per OQ-V1 RESOLVED. Each carries the wire-format
envelope per
[`docs/conventions/vero-bridge-wire-format.md`](vero-bridge-wire-format.md).

### 2.1 `echo`

**Purpose.** AC-3 round-trip live evidence carrier. Smallest possible
tool surface to prove the transport works end-to-end from both
clients.

| | |
|---|---|
| `message_type` | `echo` |
| Phase 1 args | `version: int`, `claimed_tag: str`, `name: str` (the payload) |
| Phase 1 returns | `{"ok": True, "echoed": <name>, "ts_ns": <decimal str>}` (ts_ns is epoch ns as a decimal string — wire-format §7.2 / FINDING-2) |
| Server side-effects | Audit-log entry per AC-4 (b). No state, no I/O outside log. |
| Classification rationale | Pure-function; no repo state read; no operation outside echo + timestamp + audit log. Cannot violate any tier boundary by design. |

### 2.2 `bridge_status`

**Purpose.** Reports the server's operational state to clients (version,
uptime, last-call timestamp, instance routing). Useful for client-side
liveness checks and the AC-3 cross-client smoke matrix.

| | |
|---|---|
| `message_type` | `signal` (subkind `status`) — or a dedicated message type to be confirmed in Step 2 |
| Phase 1 args | `version: int`, `claimed_tag: str` |
| Phase 1 returns | `{"ok": True, "protocol_version": 1, "uptime_s": <int>, "pid": <int>, "ppid": <int>, "last_call_ts_ns": <decimal str \| None>}` (last_call_ts_ns is a decimal string — FINDING-2) |
| Server side-effects | Audit-log entry per AC-4 (b). Reads server-process state (PID, ppid, uptime counter). No repo state read; no filesystem write. |
| Classification rationale | Reports observable server-process facts that are already public via `ps aux`. No repo state surfaced; no privileged information leaked. |

### 2.3 `bridge_whoami`

**Purpose.** OQ-T3 empirical-probe carry-over. Returns the audit-log
fingerprint for the current call — `claimed_tag` + observable transport
facts (PID, ppid, stdin_fd, stdout_fd, ts_ns, env_keys_seen). Lets
clients self-audit how the server saw them, and lets AC-4 (c)
cross-tab anti-spoof tests assert the per-call observable fingerprint
matches the expected instance routing.

| | |
|---|---|
| `message_type` | `signal` (subkind `whoami`) — or a dedicated message type to be confirmed in Step 2 |
| Phase 1 args | `version: int`, `claimed_tag: str` |
| Phase 1 returns | `{"ok": True, "claimed_tag": <verbatim>, "pid": <int>, "ppid": <int>, "stdin_fd": <str>, "stdout_fd": <str>, "ts_ns": <decimal str>, "env_keys_seen": [<str>, ...]}` (ts_ns is a decimal string — FINDING-2) |
| Server side-effects | Audit-log entry per AC-4 (b). Reads `/proc/self/fd/{0,1}` + `os.environ` for `CLAUDE_*` keys. No repo state read; no filesystem write. |
| Classification rationale | Returns server-process introspection. Per OQ-T3 empirical evidence (research note §8.2 T8–T12), this is the AC-4 (c) anti-spoof audit primitive — and it's safe-for-all because the values are already self-observable via `ps aux` + `os.environ` from any process that can read `/proc`. |

### 2.4 `read_repo_path`

**Purpose.** Read a path under the repo root and return its contents.
Phase-1-scope: read-only access to repo-tracked content (governance
files, plan/ADR docs, tests, source). Enables Chat + Cowork to read
the same repo state Code reads (closes the K-2 read-block per
[Lesson #8](../lessons/0008-cowork-tier1-k1-k2-workflow.md) §1) for
contract reasoning + governance review.

| | |
|---|---|
| `message_type` | `signal` (`MessageType.SIGNAL`; subkind `read_repo` is implicit in the tool name — the schema enum carries no subkind) |
| Phase 1 args | `version: int`, `claimed_tag: str`, `path: str` (relative to repo root) |
| Phase 1 returns | `{"ok": True, "path": <str>, "size": <int_bytes>, "content": <utf-8 str>}` on success; a `path-forbidden` error envelope (`{"ok": False, "error_code": "path-forbidden", "error_message": <str>}`, wire-format §3.1) on any sandbox violation |
| Server side-effects | Audit-log entry per AC-4 (b) (accepted **and** rejected). Reads one file from disk + one read-only `git ls-files` query (tracked-status check). **No write.** |
| Classification rationale | **Read-only.** Realized Phase-1 sandbox ([`tools/vero_bridge/_repo_read.py`](../../tools/vero_bridge/_repo_read.py)): the path must be (1) relative with no `..` component, (2) not under `.git/`, (3) inside the repo root after symlink resolution (a tracked symlink whose target escapes the tree is rejected), (4) **git-tracked** — the load-bearing allowlist rule, which by construction excludes every gitignored sensitive path (`.env`, `.claude/state/`, `docs/research/private/` audit logs, `docs/strategy/private/`) without a hand-curated denylist, (5) a regular file ≤ 2 MiB whose bytes decode as UTF-8. Every violation → `ErrorCode.PATH_FORBIDDEN`. AC-5 negatives ([`tests/vero_bridge/test_read_repo_path.py`](../../tests/vero_bridge/test_read_repo_path.py)) assert rejection of absolute / `..` / out-of-tree-symlink / `.git/` / gitignored / untracked / directory / oversize / binary paths. |
| Phase 2 question | Authoritative path-allowlist vs path-blocklist. **Phase 1 realized the conservative allowlist (git-tracked files only).** A future widening (e.g. read of a generated-but-untracked artifact) would revisit this with an explicit, reviewed allowlist extension. |

### 2.5 `validate_handoff_frontmatter`

**Purpose.** Closes the K-1 forcing fact for Cowork
([Lesson #8](../lessons/0008-cowork-tier1-k1-k2-workflow.md) §3 — UNC
abort on `mcp__workspace__bash`). Cowork has been unable to run
`tools/handoffs/validate_handoff.py` directly; exposing it via the
bridge lets Cowork validate handoffs without needing Code to broker
the run.

| | |
|---|---|
| `message_type` | `signal` (`MessageType.SIGNAL`; subkind `validate_handoff` is implicit in the tool name) |
| Phase 1 args | `version: int`, `claimed_tag: str`, `content: str` (the handoff file body, including frontmatter) |
| Phase 1 returns | `{"ok": True, "valid": <bool>, "errors": [{"field": <str>, "value": <str>, "message": <str>, "severity": "error" \| "warning"}, ...]}`. **`ok` is transport success; `valid` is content validity** — an invalid handoff is `ok=True, valid=False` (validation findings are a successful result, not a transport error). `valid` is `False` iff any finding is error-severity (`ValidationError.is_error()`). |
| Server side-effects | Audit-log entry per AC-4 (b) (accepted **and** rejected). Invokes `tools/handoffs/_schema.py::parse_frontmatter_text` (a content-based entry point added alongside this tool; same validation as the path-based `parse_frontmatter` the CLI uses) in-process via [`tools/vero_bridge/_handoff_validate.py`](../../tools/vero_bridge/_handoff_validate.py). **No filesystem write.** |
| Classification rationale | Pure validation against the committed schema. No state mutation; no privileged information. The validation logic is the same code already in repo + already runnable by Code; the bridge only changes *who* can invoke it. No new `ErrorCode` — only a non-str `content` is `MALFORMED_FRAME`. **Warning-surfacing nuance** (mirrors `parse_frontmatter`): a warning is returned only when the block *also* has a blocking error; a block whose only issue is advisory parses cleanly and reports `valid=True` with no findings. AC-5 cases ([`tests/vero_bridge/test_validate_handoff_frontmatter.py`](../../tests/vero_bridge/test_validate_handoff_frontmatter.py)): valid body, missing-required, invalid-enum, missing-fence, mixed error+warning, empty content. |

### 2.6 `lint_status`

**Purpose.** Returns the Q4 freshness check for `docs/STATUS.md` per
[Lesson #5 §4 + STATUS update workflow](../../docs/STATUS.md#update-workflow).
Useful for Cowork drafting context (Cowork can check if STATUS is
stale before authoring a session-reconcile).

| | |
|---|---|
| `message_type` | `signal` (subkind `lint_status`) — confirmed Step 2 |
| Phase 1 args | `version: int`, `claimed_tag: str` |
| Phase 1 returns | `{"ok": True, "fresh": <bool>, "status_head_commit": <short_sha>, "newest_substantive_sha": <short_sha>, "drift_commits": [<sha>, ...]}` |
| Server side-effects | Audit-log entry per AC-4 (b). Reads `docs/STATUS.md` frontmatter + invokes `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`. **No write.** |
| Classification rationale | Read-only repo introspection + read-only git query. The check is already documented + already runnable from CLI; bridge-exposure is ergonomics, not capability extension. |

### 2.7 `dispatch_receive`

**Purpose.** **Reserved placeholder** for Phase 1 dispatch handoff
receive-side. Code uses this to surface a dispatch envelope to a
client tab without committing authority (the client receives the
dispatch as informational; bind-on-Cray happens through Code's
internal mechanism, not via the bridge). Anchors AC-3 dispatch arm
when minted; in Phase 1 the surface exists but may stay no-op until
the dispatch flow is wired in a follow-up step.

| | |
|---|---|
| `message_type` | `dispatch_receive` |
| Phase 1 args | `version: int`, `claimed_tag: str`, `envelope: dict` (handoff envelope per [`docs/conventions/handoff-frontmatter-schema.md`](handoff-frontmatter-schema.md)) |
| Phase 1 returns | `{"ok": True, "received_id": <str>, "ts_ns": <int>}` |
| Server side-effects | Audit-log entry per AC-4 (b). May write to a gitignored receive-queue file under `docs/research/private/`. **No commit, no bind-on-Cray.** |
| Classification rationale | Receive-side only. Does not carry authority — the envelope is informational. Authority-bearing operations (commit, bind-on-Cray) remain not-on-bridge. |

## 3. Not-on-bridge (the exclusion list)

These operations are **explicitly NOT exposed as MCP tools**. Attempting
to invoke them via the transport returns a transport-layer
`tool-not-found` error per AC-5 negative test — they remain under
Code's internal mechanisms or under ADR-013 D2's deterministic deny
hook.

| Operation | Where it lives instead | Why kept off-bridge |
|---|---|---|
| `commit_to_main` / any git write (`git commit`, `git push`, `git reset --hard`, etc.) | ADR-013 D2 `pretooluse_git_deny.py` (deterministic deny hook); Code-only via `Bash` tool in main Code session | Authority operation; ADR-013 D2 binding "only Code commits" must not weaken under any transport. AC-4 (a) negative test asserts a transport-layer git request is refused at the deny layer, not just by prompt. |
| `dispatch_bind_on_cray` | Code's internal handoff mechanism + Cray's UI review | Authority-bearing: a "binding" handoff implies Cray has ratified. Bind cannot be delegated to a non-Cray actor; bridge transport gives no Cray-presence signal. |
| `write_file` (generic file write) | Code's `Write` / `Edit` tools (which trigger PreToolUse hooks: G1/G2/C4) | Bridge writes would bypass C4 (research path), G1/G2 (ADR/PLAN slot gates), and the broader PreToolUse classifier dispatch — would be a tier-bypass. |
| `run_shell` / `Bash` execution | Code's `Bash` tool (gated by classifier + dispatch hooks) | Shell execution is the broadest authority operation; bridge-exposing it would defeat every safety hook in `.claude/hooks/`. |
| Any `git_*` op (status, log, diff, branch, etc.) **as a write or state-changing query** | Code's `Bash` + `gh` workflow | Read-only `git log` is exposed indirectly via `lint_status` (constrained query); arbitrary `git_*` would create a tier-bypass for branch / config / state changes. |
| `set_status` / `STATUS.md` write or any authority-override op | Code's `Edit` + the [Section 6 PR workflow](../STATUS.md#update-workflow) | `STATUS.md` is the project ledger; writes carry authority (they bind the project's stated state). Bridge writes would bypass the documented update workflow + PR review. |
| `modify_settings` / `.claude/settings.json` writes | Code's `Edit`; gated by `update-config` skill + Cray approval | Settings drive hook execution + tool permissions. A bridge write to settings could disable safety hooks; explicit Cray approval required. |
| `kill_server` / `restart_server` / lifecycle commands | Claude Desktop UI (Cray-driven) | Server lifecycle is owned by Desktop under A1 stdio-MCP (per the [OQ-A soft-violation note](../plans/0012-vero-bridge.md#open-questions)); allowing a bridge tool to kill its own host violates the "no recursive control" principle and would let a misbehaving client take the server down. |

**Rule.** Adding a new tool requires either:

1. classifying it as **safe-for-all** (must be read-only or
   echo-shaped; must not carry authority; must not bypass any
   PreToolUse hook even indirectly), **and** adding it here with
   per-tool schema, classification rationale, and AC-5 unit tests; or
2. classifying it as **safe-for-some** (Phase 2+; requires an
   out-of-band identity mechanism — see PLAN-0012 OQ-T3 §Phase 2
   reconsideration); or
3. keeping it **not-on-bridge** and documenting where it lives
   instead.

There is no path #4 (silent expose without inventory entry).

## 4. AC-8 negative test (asserted by Step 5)

Step 5's AC-5 test suite contains an AC-8 negative case: a transport
call to a tool name that is **on the not-on-bridge list** (e.g.
`commit_to_main`, `write_file`, `run_shell`, `git_commit`) is **refused
at the FastMCP framework layer** with:

```text
mcp.server.fastmcp.exceptions.ToolError: Unknown tool: <tool name>
```

**FINDING-3 (Step 5, 2026-05-29) — contract corrected.** This section
originally specified a server-emitted JSON body
(`{"ok": False, "error_code": "tool-not-found", "error_message": "…"}`).
The actual Phase-1 architecture registers tools via FastMCP
`@mcp.tool()` decorators and has **no generic dispatcher** to receive an
arbitrary tool name and emit that body — an unregistered name is rejected
by the framework with a `ToolError` **before any server code runs**. That
is a strictly **stronger** boundary: the operation never reaches an
implementation, so there is no side channel and no tier-bypass surface
(it does NOT escalate to the PreToolUse deny hook because nothing is ever
dispatched). `ErrorCode.TOOL_NOT_FOUND` remains reserved in
`tools/vero_bridge/_schema.py` for a hypothetical future
generic-dispatcher surface (Phase 2+); Phase 1 enforces not-on-bridge
**structurally** (the dangerous op is simply never registered).

The AC-8 negative test
(`tests/vero_bridge/test_server_adversarial.py`) therefore asserts:
(1) `await mcp.list_tools()` returns **exactly** the safe-for-all set,
and (2) each not-on-bridge op raises `ToolError("Unknown tool: …")`.
Evidence:
`docs/research/private/2026-05-29-vero-bridge-step5-spoof-matrix.md` §5.

## 5. Phase 2 reconsideration trail

Each safe-for-all tool in §2 names a Phase 2 question. The Phase 2
mint condition (PLAN-0012 §Phase 2 PLACEHOLDER) is: when a concrete
need for a not-on-bridge or safe-for-some capability lands, this
inventory gets an amendment alongside the OQ-V1 reconsideration +
the out-of-band identity mechanism decision (OQ-T3 §Phase 2 entry).

The AC-7 cross-client parity binding (same wire format byte-by-byte,
same Phase-1 capability scope for all tabs) is the **load-bearing
constraint** that lets us defer per-tab capability differentiation
without leaking authority to an unintended tab.

## 6. Change log

- **2026-05-28** — Initial Phase 1 inventory materialized (this PR,
  Step 1). Source draft: PR #67 completion handoff §3 (Cowork-drafted).
  Seven safe-for-all + eight not-on-bridge entries. Classification
  rationale + Phase 2 reconsideration trail added per AC-8 / PLAN-0012
  Cowork-handoff guidance.
- **2026-05-29** — §4 AC-8 negative contract corrected (FINDING-3,
  Step 5). The not-on-bridge enforcement is a FastMCP framework
  `ToolError` ("Unknown tool: …"), not a server-emitted
  `tool-not-found` JSON body — the decorator architecture has no generic
  dispatcher. Structural (never-registered) enforcement; stronger than
  the original spec. `ErrorCode.TOOL_NOT_FOUND` reserved for Phase 2+.
- **2026-05-29** — **Step 2b: §2.4 `read_repo_path` realized + registered**
  (first integration tool). `message_type`, returns, side-effects, and
  classification rationale updated from spec to the as-built sandbox
  ([`tools/vero_bridge/_repo_read.py`](../../tools/vero_bridge/_repo_read.py)):
  git-tracked allowlist + `..`/absolute/symlink-escape/`.git`/non-regular/
  oversize/non-UTF-8 rejection, all surfaced as the new
  `ErrorCode.PATH_FORBIDDEN` (`"path-forbidden"`; wire-format §3.2). The
  safe-for-all registered surface grows from 3 → 4 tools; the AC-8
  tripwire (`tests/vero_bridge/test_server_adversarial.py`
  `SAFE_FOR_ALL_TOOLS`) updated accordingly.
- **2026-05-29** — **Step 2b: §2.5 `validate_handoff_frontmatter` realized +
  registered** (second integration tool). Runs the committed
  handoff-frontmatter schema in-process via a new content-based entry point
  `tools/handoffs/_schema.py::parse_frontmatter_text` (path-based
  `parse_frontmatter` refactored to call it — behavior-preserving) through
  the bridge adapter
  ([`tools/vero_bridge/_handoff_validate.py`](../../tools/vero_bridge/_handoff_validate.py)).
  No new `ErrorCode`. Safe-for-all registered surface grows 4 → 5; AC-8
  tripwire + wire-format §7 invocation surface updated. Closes the Lesson #8
  K-1 forcing fact (Cowork can now validate handoffs it authors).
