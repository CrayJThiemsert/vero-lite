# Runbook: vero-bridge cross-client live evidence (PLAN-0012 Step 4)

**Status:** Evidence captured + conclusions drawn 2026-05-29 (code-session-24,
post-PR #75 re-smoke). Ratification = Cray's merge of the Step 4 evidence PR.
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
| **FINDING-1** | `ts_ns` is epoch (wall-clock) ns, **not** monotonic | Ordering key is the per-process `monotonic_counter` (resets to 1 on every respawn). `server.py` docstring corrected in PR #75 (`b90442d`). |
| **FINDING-2** | `ts_ns` > 2⁵³ corrupted by JSON-double clients via structuredContent | Field string-typed (`server.py:149`); post-fix matrix (§2) proves byte-exact round-trip on all three clients. |

Both closed by [PR #75](https://github.com/CrayJThiemsert/vero-lite/pull/75).

## 4. What this closes in PLAN-0012

- **AC-3** — both clients round-trip echo (cross-client live evidence): **met**
  (Chat + Cowork captured; Code captured as a third path).
- **AC-6** — live evidence, not mocked, both clients: **met** (the gitignored
  evidence file is the named live-evidence artifact; every cell is a real
  cross-tab invocation).
- **AC-7** — cross-client wire-format + capability parity: **met** (§2.1).
- **AC-4(c)** — basis live-proven (§2.2); **full spoof matrix remains Step 5**.

Still ahead in Phase 1: **Step 5** (adversarial cross-tab spoof matrix + tests +
lint) and **Step 2b** (the four integration tools beyond `echo`).

## 5. Anti-patterns / boundary

- **Do not treat the audit `ts_ns` int as a monotonic clock.** It is wall-clock
  epoch ns (FINDING-1). For ordering within a server instance, use
  `monotonic_counter`; across instances/epochs the counter resets and is not
  comparable.
- **Do not re-introduce a JSON-number `ts_ns`** (or any > 2⁵³ integer) on the
  wire. The string-typing is load-bearing for cross-client correctness, not a
  cosmetic choice. If a future field needs a large integer, string-type it.
- **Do not cite §2.2 as the full anti-spoof proof.** It is the Code/Cowork
  non-discriminability *basis*. AC-4(c)'s full matrix (every tab claiming every
  other identity, audit-discrepancy capture) is Step 5.
- **`ps aux` before trusting a PID.** Server instances respawn across Desktop
  restarts (Lesson #0017 §5); the routing table in §2 is epoch-specific. Probe
  live PIDs at capture time rather than reusing a documented PID.

## 6. Provenance & supersession

- **Authored by:** code-session-24, 2026-05-29 (Asia/Bangkok).
- **Server fix under test:** PR #75 (`476e9c7` merge / `b90442d` substantive).
- **Source evidence (gitignored):**
  `docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md`
  + `docs/research/private/vero-bridge-audit.jsonl`.
- **Capture sessions:** pre-fix matrix session-22/23; post-fix re-smoke
  session-24 (2026-05-29 ~12:17–12:22 +07:00).
- **Cray ratification:** on merge of the Step 4 evidence PR.
- **Supersession trigger:** if the wire format changes the `ts_ns` type, or if a
  client later shows precision loss on the string value, supersede §2 in place
  and bump the Status date (do not silently edit the conclusion).
