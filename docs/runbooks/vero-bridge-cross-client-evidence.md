# Runbook: vero-bridge cross-client live evidence (PLAN-0012 Steps 4 + 5)

**Status:** Evidence captured + conclusions drawn 2026-05-29 (code-session-24).
Covers Step 4 (post-PR #75 re-smoke) + Step 5 (adversarial spoof matrix). With
Step 5, all 8 PLAN-0012 Phase 1 ACs are DONE/PRESERVED. Ratification = Cray's
merge of the Step 4 (PR #76, merged) + Step 5 evidence PRs.
**Audience:** PLAN-0012 reviewers; future Phase-2 work that depends on the
identity model; anyone debugging `ts_ns` precision across MCP clients.
**Related:** [PLAN-0012 `vero-bridge`](../plans/0012-vero-bridge.md) (AC-3 / AC-6 /
AC-7 + AC-4(c) basis), [PR #75](https://github.com/CrayJThiemsert/vero-lite/pull/75)
(the `ts_ns` string fix — FINDING-1 + FINDING-2),
[Lesson #0017 — MCP cross-tab visibility](../lessons/0017-mcp-cross-tab-visibility-empirical-probe.md)
(§3 tab-group routing; §5 `ps aux` empirical-probe discipline),
[cowork-network-locus runbook](cowork-network-locus.md) (the gitignored-evidence
+ tracked-summary split this runbook reuses).
**Source evidence (gitignored audit trail):**
`docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md`
(verbatim per-cell records) + `docs/research/private/vero-bridge-audit.jsonl`
(the live audit log).

---

## 1. The question

Does the PLAN-0012 v1 bridge round-trip its server-side `ts_ns` stamp
**losslessly to every client** (Chat, Code, Cowork), and is the
cross-client wire format identical for the same logical operation? `ts_ns`
is an int64 ≈ 1.78×10¹⁸ nanosecond stamp — well above 2⁵³ — so it is a probe
for JSON-number precision loss across heterogeneous MCP client paths.

## 2. The finding (proven by live evidence)

**Before PR #75 (server returned `ts_ns` as a JSON number):** the value was
corrupted on the clients that parse FastMCP **structuredContent** into an
IEEE-754 double — **Code and Cowork rounded** it (e.g. `…852137` → `…852000`);
the **text-content** path (Chat) happened to survive exact. This is FINDING-2:
a JSON-number `ts_ns` above 2⁵³ cannot survive a double-parsing client. The
rounding lands at the 10²–10³ ns place — the precise fingerprint of a 19-digit
integer exceeding a double's ~15–16 significant decimal digits.

**After PR #75 (server returns `ts_ns` as a decimal string,
`server.py:149` → `str(record["ts_ns"])`):** every client round-trips the value
**byte-exact** against the audit-log int — Chat, Code, **and** Cowork. The fix
removes the dependence on which content channel (text vs structured) a client
reads.

Decisive evidence (post-fix re-smoke, 2026-05-29, three fresh-token cells):

| client | server pid (pts) | audit int `ts_ns` | client-observed | match |
|---|---|---|---|---|
| Chat | 586 (pts/5, instance A) | `1780031829240624177` | `"1780031829240624177"` | ✅ exact |
| Code | 1189 (pts/7, instance B) | `1780032001128448359` | `"1780032001128448359"` | ✅ exact |
| Cowork | 1189 (pts/7, instance B) | `1780032165530125591` | `"1780032165530125591"` | ✅ exact |

The audit log keeps the **int** as the source of truth (Python-read; never
JSON-double-parsed). The string on the wire is what the clients consume.

### 2.1 Cross-client wire-format + capability parity (AC-7)

All three clients invoke the **identical** `echo` tool with the **identical**
envelope — `version=1`, `claimed_tag`, `name` — and receive the **identical**
response shape — `{ok, echoed, ts_ns:string}`. Same wire format, same Phase-1
tool surface (per OQ-V1 RESOLVED: uniform safe-tool set for all tabs).

### 2.2 Code/Cowork same-instance routing (AC-4(c) basis)

Code and Cowork share **one** server instance with a **continuous** monotonic
counter — confirmed in two independent Desktop epochs:

- **Pre-fix:** code+cowork on `pid 62929`, counter 1→2.
- **Post-fix:** code+cowork on `pid 1189`, counter 1→2 (same pid/ppid/stdin_fd/
  stdout_fd across the two tabs).

Chat routes to a separate instance (instance A) in every epoch. So the server
can discriminate **Chat vs (Code∪Cowork)** by PID, but **cannot** discriminate
**Code vs Cowork** by any observable transport signal — the empirical basis for
AC-4(c) and the Option I identity model (OQ-T3 RESOLVED). The **full** adversarial
cross-tab spoof matrix (every tab claiming every other tab's identity) is
**Step 5**, not this Step 4.

## 3. FINDING resolution status

| Finding | Statement | Resolution |
|---|---|---|
| **FINDING-1** | `ts_ns` is epoch (wall-clock) ns, **not** monotonic | Ordering key is the per-process `monotonic_counter` (resets to 1 on every respawn). `server.py` docstring corrected in PR #75 (`b90442d`). Closed by PR #75. |
| **FINDING-2** | `ts_ns` > 2⁵³ corrupted by JSON-double clients via structuredContent | Field string-typed (`server.py:149`); post-fix matrix (§2) proves byte-exact round-trip on all three clients. Closed by PR #75. |
| **FINDING-3** | AC-8 not-on-bridge is enforced by FastMCP `ToolError`, **not** a server-emitted `tool-not-found` JSON body | The decorator architecture has no generic dispatcher; an unregistered op is rejected before any handler runs (stronger boundary). Capability-inventory §4 amended; `ErrorCode.TOOL_NOT_FOUND` reserved for Phase 2+. Closed by the Step 5 PR. |
| **FINDING-4** | A cooperative tab will not self-spoof its identity tag | Chat (conversation-only tier) refused to emit a spoofed `claimed_tag`; Cowork (tool-capable tier) complied. Agent-layer defense-in-depth on top of server Option-I. Surfaces governance OQ-T5 (Chat-as-bridge-client vs `chat_tab_instructions.md`). Documented in the Step 5 PR; OQ-T5 for Cray. |

## 4. What this closes in PLAN-0012

- **AC-3** — both clients round-trip echo (cross-client live evidence): **met**
  (Chat + Cowork captured; Code captured as a third path) — Step 4 / PR #76.
- **AC-6** — live evidence, not mocked, both clients: **met** (the gitignored
  evidence file is the named live-evidence artifact; every cell is a real
  cross-tab invocation) — Step 4 / PR #76.
- **AC-7** — cross-client wire-format + capability parity: **met** (§2.1) — Step 4 / PR #76.
- **AC-4(c)** — adversarial anti-spoof matrix: **met** (Step 5; see §Step 5 +
  spoof-matrix evidence). Server accepts spoofs (Option I); audit captures the
  discrepancy; Code-vs-Cowork non-discriminable; Chat discriminable. The
  *cooperative* "Chat claiming cowork" cell was substituted per **FINDING-4**.
- **AC-5** — test coverage (cross-client + adversarial + AC-8 negative): **met**
  (Step 5; 26 adversarial/negative/boundary tests + case-coverage matrix below).
- **AC-8** — capability-by-tool-design: **met** (Step 5; registered set asserted;
  not-on-bridge ops refused at framework layer per **FINDING-3**).

With Step 5, **all 8 ACs of PLAN-0012 Phase 1 are DONE/PRESERVED**. Still ahead:
**Step 2b** (the four integration tools beyond the three introspection tools) +
the **OQ-T5** governance reconciliation (Chat-as-bridge-client).

## 5. Step 5 — adversarial spoof matrix + capability boundary

### 5.1 What the spoof matrix shows (live)

`bridge_whoami` returns the caller's (spoofable, audit-only) `claimed_tag`
alongside the **non-spoofable** observable fingerprint (pid/ppid/stdin_fd/
stdout_fd). The live matrix (spoof-matrix evidence file §2–§4):

- **Code self-spoof (epoch A, pid 30773):** Code claimed `code`, then `chat`,
  then `cowork` — all accepted; **identical fingerprint** across all three.
  The tag does not change the observable identity.
- **Cowork spoof + Code witness (epoch B, pid 1138):** Cowork claimed `chat`
  then `code` (both accepted); Code then called honestly — **all three share
  pid 1138 / same fds**. Code and Cowork are **transport-indistinguishable**.
- **Chat:** routes to instance A (separate pid on pts/5) in every epoch →
  Chat-vs-(Code∪Cowork) **is** discriminable by pid. Chat **refused** to
  self-spoof (FINDING-4).

So: `claimed_tag` is audit-only (server never authorizes on it); the only
real discriminator is instance routing (Chat=A; Code+Cowork=B, indistinct).

### 5.2 Case-coverage matrix (AC-5)

| Dimension | Cases | Mapped tests / evidence | Status |
|---|---|---|---|
| Happy | echo / bridge_status / bridge_whoami well-formed → ok | `test_server.py` (happy per tool) | ✅ |
| Boundary / encoding | 10 k payload, unicode name+tag, empty name, `version=bool` | `test_server_adversarial.py` | ✅ |
| Fail-closed (OQ-T1) | version mismatch, empty / non-str / malformed `claimed_tag`, unknown message type | `test_server.py` + `test_schema.py` | ✅ |
| Adversarial — spoof (AC-4(c)) | server accepts any tag; signals independent of tag; audit captures discrepancy; live cross-tab | `test_server_adversarial.py` + spoof-matrix evidence §2–§4 | ✅ (Chat-spoof substituted — FINDING-4) |
| Adversarial — AC-8 / git negative | not-on-bridge + git ops → framework `ToolError`; registered set == safe-for-all | `test_server_adversarial.py` | ✅ (FINDING-3) |
| Concurrency (OQ-T4 serial-per-instance) | per-instance monotonic counter orders calls deterministically; sync handlers serialize | `test_server.py` (monotonic counter) + live counters 1→2→3 on pid 1138 | ✅ (see residual risk) |
| Safety (AC-4(a) G5) | git-over-transport refused; deny suite green | `test_pretooluse_git_deny.py` (full-suite re-run: 813 passed / 7 skipped) | ✅ |

**Residual risk (named, not hidden):**

1. **Cooperative Chat-spoof is unobtainable (FINDING-4).** A cooperative tab
   won't self-spoof, so the literal "Chat claiming cowork" cell is absent.
   Server-side spoof acceptance is proven via Code + Cowork + unit tests
   instead. A *non-cooperative* raw-MCP client (bypassing agent judgment) is
   out of scope for the Phase-1 single-operator threat model (OQ-T3).
2. **No true-concurrency race test.** OQ-T4 serial-per-instance is asserted by
   design (sync handlers) + monotonic-counter determinism, not a load/race
   test. Acceptable for Phase 1's sub-second safe tools; revisit if contention
   pressure emerges (OQ-T4 Phase 2 note).

### 5.3 FINDING-3 / FINDING-4 (see §3 table)

- **FINDING-3** — AC-8 enforcement is a framework `ToolError`, not a server
  JSON body; capability-inventory §4 amended. Stronger boundary (structural
  non-registration).
- **FINDING-4** — Chat refuses to self-spoof (correct, desirable). Surfaces
  **OQ-T5** (Chat-as-bridge-client vs `chat_tab_instructions.md` conversation-
  only posture) — **for Cray to adjudicate**, does not block Step 5.

## 6. Anti-patterns / boundary

- **Do not treat the audit `ts_ns` int as a monotonic clock.** It is wall-clock
  epoch ns (FINDING-1). For ordering within a server instance, use
  `monotonic_counter`; across instances/epochs the counter resets and is not
  comparable.
- **Do not re-introduce a JSON-number `ts_ns`** (or any > 2⁵³ integer) on the
  wire. The string-typing is load-bearing for cross-client correctness, not a
  cosmetic choice. If a future field needs a large integer, string-type it.
- **Do not claim the spoof matrix as a defense against a determined adversary.**
  The Phase-1 threat model is single-operator (OQ-T3). The matrix proves the
  server doesn't *rely* on `claimed_tag`; it does not (and need not) defend
  against a non-cooperative client under a multi-tenant adversary.
- **Do not read FINDING-4 as "Chat is broken."** A tab refusing to self-spoof
  is correct, desirable behaviour. The open item is governance (OQ-T5: is
  Chat a sanctioned bridge client?), not a code fix.
- **`ps aux` before trusting a PID.** Server instances respawn across Desktop
  restarts (Lesson #0017 §5); the routing table in §2 / §5.1 is epoch-specific.
  Probe live PIDs at capture time rather than reusing a documented PID — the
  Step 5 capture itself spanned two epochs (pid 30773 → 1138).

## 7. Provenance & supersession

- **Authored by:** code-session-24, 2026-05-29 (Asia/Bangkok).
- **Server under test:** Step 4 = PR #75 (`476e9c7` / `b90442d`); Step 5 = `main`
  `c4d10dd` (post-PR #77).
- **Source evidence (gitignored):**
  `docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md`
  (Step 4) +
  `docs/research/private/2026-05-29-vero-bridge-step5-spoof-matrix.md` (Step 5)
  + `docs/research/private/vero-bridge-audit.jsonl`.
- **Capture sessions:** pre-fix matrix session-22/23; post-fix re-smoke +
  Step 5 spoof matrix session-24 (2026-05-29).
- **Cray ratification:** Step 4 ratified on merge of PR #76; Step 5 on merge of
  the Step 5 PR.
- **Supersession trigger:** if the wire format changes the `ts_ns` type, if a
  client later shows precision loss on the string value, or if OQ-T5 resolves
  the Chat-client question, supersede the affected section in place and bump the
  Status date (do not silently edit a conclusion).
