# PLAN-0012: vero-bridge — MCP transport operationalizing ADR-013 D1

**Status:** Ready for execution
**Owner:** Claude Code + Cowork (advisory drafter)
**Created:** 2026-05-28
**Related ADRs:** ADR-013 (D1 — MCP-transport-in-Code-Tier-2; OQ-1 — Cowork retained as advisory governance drafter)
**Related Plans:** PLAN-0009 (`vero-bridge` Phase-4 earmark re-anchor PLAN-0010 → PLAN-0012, PR #58; OQ-3 "no new ADR" precedent), PLAN-0011 (live-evidence dependency — Lesson #15 §7)
**Replaces:** ADR-0014 (WITHDRAWN — see `docs/adr/0014-WITHDRAWN.md` tombstone)

> **Status-vocabulary reconciliation (OQ-T2 RESOLVED at commit).**
> Cowork's authoring used `Status: Proposed` per the dispatch's literal
> instruction and surfaced the discrepancy with the PLAN template
> (`docs/plans/0000-template.md` line 3) + PLAN-0009 OQ-4 ratified
> 2026-05-25 ("PLANs use `Draft` → `Ready for execution`, **not** ADR
> vocabulary `Proposed`/`Accepted`"). Code reconciled at commit per
> Cowork's recommendation: flipped **`Proposed` → `Draft`** to honor
> PLAN-0009 OQ-4 + template convention. The dispatch's `Proposed` was
> a wording error (ADR-vocabulary leak from the withdrawn ADR-014's
> drafting context); the correct mint status is `Draft`. **Cray
> ratified 2026-05-28 PM late (session-22 routing turn that also
> resolved OQ-T1 + OQ-T4 + OQ-V2); Status flipped `Draft` → `Ready
> for execution` in this PR.** See §Open Questions OQ-T2 for historical
> record.

## Goal

`vero-bridge` is the MCP transport that operationalizes
[ADR-013 D1](../adr/0013-autonomy-axis-relocation.md) (lines 98–127): the
execution-automation axis lives in Code (Tier 2), so the machine-to-machine
channel that lets the executing harness exchange signals with the other
collaboration surfaces must also originate there. Today every inter-tier
handoff routes through Cray as a human relay (paste a path from one tab to
another); `vero-bridge` removes that relay for the cases where a surface
can connect as an MCP client to a Code-side server. This PLAN delivers a
**v1** transport spanning **Code (Tier 2, server) ↔ (Chat + Cowork)
(Tier 1 + Tier 0/1/1b, clients)** — both non-Code tabs are first-class
clients of a single shared Code-side stdio-MCP server in v1, **not** a
Code↔Chat-only transport.

**Why both clients in v1 (path-C decision, 2026-05-28 PM).** The earlier
single-client framing deferred the Cowork-client to v2 citing the
[cowork-network-locus runbook](../runbooks/cowork-network-locus.md) §3
(Cowork's outbound `web_fetch` does not exit Cray's machine, so a v1
loopback bus is unreachable from the Cowork sandbox). That deferral logic
assumed a **loopback-HTTP** transport. Under OQ-A's ratified **A1 =
stdio-MCP** (see §Open Questions OQ-A, ratified 2026-05-28 in this PR),
Cowork's MCP-client primitive connects to a Desktop-spawned local server
via Desktop's MCP infrastructure (not network egress), so the OQ-C
network-locus deferral logic does not apply to v1 transport. Cowork-client
viability is **empirically verified** by research note
[`2026-05-28-oq-b-chat-mcp-spawn-probe.md`](../research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md)
§3.7–§3.8 (T6 + T7 PASS — Cowork end-to-end invocation
`bridge_ping(name="cowork-t7")` returned pong at 2026-05-28T04:12:50+00:00)
and re-confirmed by the OQ-T3 follow-on probe §8 (T9 + T11 returned the
same server instance B PID=2092 across Code and Cowork). The OQ-C runbook
remains binding for **network-egress questions**; it is **moot for v1
transport** because v1 uses no network.

**Phase 2 is retained but narrowed.** Phase 2 is no longer "Cowork-client
basic transport" (that ships in Phase 1). Phase 2 is reserved for **future
Cowork-client features beyond basic transport** — authority-bearing
operations, long-lived sessions, scheduled-task carriers — that would
require an identity-enforcement mechanism beyond Option I's
capability-by-tool-design (see OQ-T3 RESOLVED). Phase 2 is not minted
until a concrete need arises.

The PLAN does **not** implement the transport — it is the plan for the
implementation; Code executes it in subsequent PRs (mirroring PLAN-0011's
split: PR #51 minted Draft, PR #52 ratified, PR #53 shipped the code).

## Structure (parent-PLAN, single file)

This is a single-file **parent-PLAN** with two phases: **Phase 1 = v1**
(Code-side stdio-MCP server + Chat-client + Cowork-client — the
deliverable) and **Phase 2 = v2** (future Cowork-client capabilities
beyond basic transport — authority-bearing operations, long-lived sessions,
scheduled-task carriers — placeholder; not minted until concrete need
arises). A separate sub-PLAN file is **not** spawned now because Phase 2 is
a placeholder for capabilities not yet specified. If Step 1 (wire format +
capability inventory) proves large during execution, Code may spawn
`docs/plans/0012-step1-wire-format.md` as a sub-PLAN and treat this file as
the parent — the same pattern PLAN-0009 used when Step 1b became
[`docs/plans/done/0009-step1b-contract-design.md`](done/0009-step1b-contract-design.md).

## Acceptance Criteria

> Eight criteria. AC-1…AC-6 cover the v1 (Phase 1) transport surface
> across **both clients** (Chat + Cowork); AC-7 binds cross-client
> wire-format + capability parity; AC-8 binds the
> capability-by-tool-design discipline that replaces transport-level
> identity enforcement under the Option I identity model (OQ-T3
> RESOLVED). Each AC names what evidence proves it (PLAN-0011
> §Acceptance Criteria per-AC style).

- [ ] **AC-1 — Transport contract is documented.** A written contract
  specifies the wire format (message framing), the message types
  carried, error codes, a version field, and the `claimed_tag` audit
  field carried in every message envelope (AC-4; audit-only — not used
  for authorization, per OQ-T3 RESOLVED Option I). Proven by a committed
  contract section (in this PLAN's Step 1 output or a spawned
  `0012-step1-wire-format.md`) that a reviewer can read and a parser can
  be written against, plus a schema-shaped definition (mirroring
  `tools/handoffs/_schema.py` discipline) the v1 code validates messages
  against. **OQ-A is RATIFIED A1 = stdio-MCP** (was a gate; resolved in
  this PR — see §Open Questions).

- [ ] **AC-2 — Code-side server runs in the harness session lifecycle.**
  The server starts and stops bound to the Code (Tier 2) harness session
  (not a detached daemon that outlives the session). Proven by an
  end-to-end test that starts the server, observes it accept a connection
  from **both** the Chat-side and Cowork-side client primitive,  and
  confirms it is torn down at session end; plus a documented lifecycle
  note. **Soft-violation of ADR-013 D1 acknowledged under A1** — under
  stdio-MCP, the server process is owned by Desktop (spawned via
  `mcpServers` config), not by Code (OQ-A §Open Questions). Mitigation:
  capability restriction (AC-8) + future ADR-013 amendment.

- [x] **AC-3 — Both clients connect and exchange a round-trip echo
  (cross-client live evidence).** v1 captures **two** live round-trip
  paths — **Chat→Code→Chat** and **Cowork→Code→Cowork** — each with a
  known payload, Code server echoes a per-session token, the client
  reports the matching token within a bounded latency. Proven by both
  evidence captures logged to a named file under
  `docs/research/private/`, both within bounded latency, both with
  matching tokens. **OQ-B = RESOLVED YES (FULL)** (Chat + Cowork
  MCP-client primitives both verified — research note §3.2–§3.8) — was a
  gate for Step 3; now unblocked. **DONE 2026-05-29 (Step 4):** Chat
  (record 7) + Cowork (record 9) round-trips captured live (Code record 8
  as a third path); evidence
  `docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md`
  + runbook `docs/runbooks/vero-bridge-cross-client-evidence.md`.

- [ ] **AC-4 — Safety boundary preserved (ADR-013 D2 not weakened) +
  audit log + adversarial anti-spoof matrix.** Three sub-criteria:
  - **(a) G5 bypass-immune matrix re-run stays green.** No transport
    path lets any connecting client induce a commit. The
    `pretooluse_git_deny.py` (G5) deterministic deny stays bypass-immune
    (ADR-013 D2 lines 142–164; PLAN-0009 AC-6) and is unaffected by the
    new server/client surface. Negative test: a transport message
    requesting a git operation is refused at the deny layer, not merely
    by prompt.
  - **(b) Server logs `claimed_tag` + observable transport facts as
    audit signals.** Server logs `claimed_tag` with every call alongside
    observable transport facts (PID, stdin_fd, ts_ns) as **audit-only
    signals** — not used for authorization (OQ-T3 RESOLVED Option I).
    Server **cannot** distinguish Code from Cowork via transport-level
    signals (empirical T9/T11/T12 in research note §8.4 — they share
    instance B PID=2092, ppid=2065, stdin_fd, stdout_fd); it **can**
    distinguish Chat from (Code∪Cowork) via PID (Chat = instance A
    PID=613). The audit log captures the discrepancy between claimed_tag
    and the observable signals where one exists.
  - **(c) Adversarial anti-spoof matrix smoke (cross-tab spoof).**
    Dispatch each tab to call a bridge tool with `claimed_tag` set to
    **each other tab's identity** — Chat claiming `cowork`, Cowork
    claiming `chat`, Code claiming `chat`, Cowork claiming `code`, Code
    claiming `cowork`. Server **accepts** the call (per Option I design
    — claimed_tag is audit-only; no rejection) but the audit log
    captures every spoof attempt with the discrepancy between claimed
    and observable signals. Evidence: the audit-log file at a named path
    under `docs/research/private/` with the spoof attempts captured plus
    analysis showing Chat-vs-(Code∪Cowork) is discriminable while
    Code-vs-Cowork is not. **Basis live-proven 2026-05-29 (Step 4, not
    full AC-4(c)):** Code+Cowork same-instance non-discriminability
    observed in two epochs (pre-fix pid 62929, post-fix pid 1189; shared
    pid/ppid/stdin_fd/stdout_fd, counter 1→2) — see Step 4 evidence §6 /
    runbook §2.2. The **full** cross-tab spoof matrix remains Step 5.

- [ ] **AC-5 — Test coverage for transport parse / dispatch / error
  paths (cross-client matrix + adversarial + AC-8 negative).** Unit +
  integration tests cover, **from both client paths** (Chat and Cowork):
  well-formed message parse; malformed / truncated message rejection;
  unknown message-type handling; version-mismatch handling; the
  transport-failure error contract (OQ-T1); **plus** the AC-4 (c)
  cross-tab anti-spoof matrix (each tab attempts to claim each other
  tab's identity); **plus** the AC-8 negative test (attempt to invoke a
  not-on-bridge operation via the transport returns a transport-layer
  "tool not found" error, not a tier-bypass). Proven by `pytest` green
  with a per-path test mapped to each case (happy × 2 clients, boundary
  × 2 clients, fail-closed × 2 clients, plus adversarial spoof matrix
  and AC-8 negative); `ruff` + `mypy` clean (mirror PLAN-0011 AC-6
  discipline); case-coverage matrix attached (happy / boundary /
  fail-closed / adversarial / concurrency) per the Cray
  verification-rigor directive (PLAN-0009 §Verification).

- [x] **AC-6 — Live evidence captured (both clients, live not mocked).**
  v1's round-trip is exercised in a real Code↔Chat session **and** a
  real Code↔Cowork session (not only mocked), and the verbatim evidence
  (payload, echoed token, latency, any error text) for **both** is
  written to a named file under `docs/research/private/` — the same
  live-vs-mock discipline Lesson #15 §5 mandates (a passing mock is "no
  evidence at all" that the real path works). The cross-client AC-3
  matrix + the AC-4 (c) adversarial spoof matrix both count toward this
  live-evidence requirement. Live evidence for the round-trip is **not
  gated** on the PLAN-0011 fresh-trigger re-run; that gate applies only
  to future Phase-2 auto-dispatch wiring (if/when minted). **DONE
  2026-05-29 (Step 4):** named live-evidence file
  `docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md`
  carries the verbatim pre-fix matrix (records 1–5) + post-fix re-smoke
  (records 7–9); all cells are real cross-tab invocations, not mocked.

- [x] **AC-7 — Cross-client wire-format + capability parity.** Both
  Chat-client and Cowork-client exercise the **same wire format**
  byte-by-byte for the same logical operation, and the **same tool
  surface** with the same Phase-1 capability scope (per OQ-V1 RESOLVED:
  Phase 1 = same safe-tool set for all tabs; capability differentiation
  deferred to Phase 2+). Proven by the cross-client smoke matrix
  (AC-3 + AC-4 (c)) showing identical wire-format bytes for the same
  logical operation invoked from both clients, and identical capability
  scope (capability inventory per AC-8 lists tools accessible from each
  client → Phase 1: same set). **DONE 2026-05-29 (Step 4):** all three
  clients invoke identical `echo` envelope (`version=1`, `claimed_tag`,
  `name`) and receive identical `{ok, echoed, ts_ns:string}` shape — see
  evidence §2.1 / runbook §2.1.

- [ ] **AC-8 — Capability-by-tool-design discipline (Option I identity
  model enforcement).** The bridge's tool surface is restricted to
  **tab-tier-safe operations** — operations that are safe for any tab
  (Chat, Cowork, Code) to invoke without violating the operating tier
  boundaries (ADR-009 D5; ADR-013 D1/D2). Dangerous operations —
  commit-to-main, authoritative dispatch with bind-on-Cray signature,
  configuration-changing writes outside the bridge's read-only /
  validate-only scope — are **not exposed as MCP tools**: they remain
  under Code's internal mechanisms (or under ADR-013 D2's deterministic
  deny hook for the commit boundary). Proven by an **explicit committed
  capability inventory document** listing every tool exposed on the
  bridge with its capability classification (safe-for-all / safe-for-some
  / not-on-bridge), **plus** the AC-5 negative test showing an attempt
  to invoke a not-on-bridge operation via the transport returns a
  transport-layer "tool not found" error (not a tier-bypass). The
  inventory is the canonical "what is exposed where" reference for Phase
  1 reviews + future Phase 2 differentiation decisions.

## Out of Scope

- ❌ **Tab-tier-bypass via the bridge.** The bridge does **not** enable
  Chat to write to repo (would violate Chat's repo-blind posture per
  ADR-009 D5 b), Cowork to commit (would violate ADR-009 D2 / ADR-013 D2
  deterministic deny hook), or any tab to escalate its tier authority.
  The bridge is **transport for tab-tier-safe signals only** — operations
  exposed on the bridge are restricted to those safe for any tab (Chat,
  Cowork, Code) to invoke (capability-by-tool-design per AC-8 + OQ-T3
  RESOLVED Option I). Dangerous operations (commit-to-main, authoritative
  dispatch, tier-escalating writes) remain under Code's internal
  mechanisms + ADR-013 D2's deterministic deny hook.

- ❌ **Any new ADR.** PLAN-0012 is minted under the already-Accepted
  ADR-013 D1, per the PLAN-0009 OQ-3 precedent
  ([done/0009-subagent-topology.md](done/0009-subagent-topology.md)
  §Resolved-decisions OQ-3: "no new ADR; mint an ADR only if a genuinely
  architecture-level choice surfaces"). The OQ-A soft-violation of
  ADR-013 D1 (Desktop spawns server, not Code) is acknowledged + tracked
  as a future ADR-013 amendment work item — **not** minted as a new ADR
  by this PLAN. If execution surfaces a genuinely architecture-level
  choice ADR-013 D1 did not anticipate, it is surfaced as a §Open
  Questions item for Cray, not minted by the drafter.

- ❌ **`.claude/settings.json` schema changes** beyond what ADR-013 D2
  already commits to (the deterministic `PreToolUse deny` hook + existing
  hook wiring). v1's server lifecycle (AC-2) under A1 = stdio-MCP runs
  via Desktop's `mcpServers` config (not Code-side `.claude/settings.json`
  hooks), so no `.claude/settings.json` changes are required by the
  transport itself.

- ❌ **PLAN-0011 AC-3/AC-7 fresh-trigger live re-run.** Cray-driven
  separately (STATUS session-19 ledger work #4; meta-awareness
  contamination per PR #53 §AC-3 requires a fresh trigger not in any
  tracked file). It is **independent** of v1 transport landing — v1
  basic transport carries no authority-bearing dispatch signal in Phase
  1 (capability-by-tool-design per AC-8), so the PLAN-0011 re-run is
  not a sequencing gate for any Phase 1 step.

- ❌ **v2 design.** Phase 2 is reserved for **future Cowork-client
  features beyond basic transport** — authority-bearing operations,
  long-lived sessions, scheduled-task carriers — which require an
  identity-enforcement mechanism beyond Option I's
  capability-by-tool-design (server cannot distinguish Code from Cowork
  via transport-level signals under A1 stdio-MCP — see OQ-T3 RESOLVED).
  v2 is not minted until a concrete need arises and is not pre-designed
  here. The mechanism choice (Option II multi-server with per-tab
  `mcpServers` entries vs Option III out-of-band shared secret vs other)
  is a Phase 2 design decision, not pre-committed.

  *(The OQ-C (ii-a)/(ii-b) public-endpoint re-test is no longer a v1
  gate — it was a gate for the loopback-HTTP transport assumption that
  A1 stdio-MCP supersedes; if a future v3 HTTP-loopback transport is
  ever explored, OQ-C re-test would gate that.)*

## Steps

> Each step is independently committable. Phase 1 = v1 multi-client
> deliverable (Code-side stdio-MCP server + Chat-client + Cowork-client);
> Phase 2 = future-capability placeholder. Steps gated on an Open
> Question name the gate explicitly.

### Phase 1 — v1: Code-side stdio-MCP server ↔ (Chat-client + Cowork-client)

#### Step 1 — Wire format / message schema + capability inventory

Design the transport contract: message framing, message types
(at minimum: `echo` for AC-3; room for `signal` carriers that future
ADR-013 D1 autonomy signals would use), error codes, a `version` field,
and a **`claimed_tag` audit field** carried in every message envelope
(audit-only — not authorization; OQ-T3 RESOLVED Option I). Mirror the
`tools/handoffs/_schema.py` discipline (stdlib-only, dataclass-typed,
fail-closed on unknown type / version mismatch). Inline here if small;
spawn `docs/plans/0012-step1-wire-format.md` as a sub-PLAN if large
(PLAN-0009 Step 1b precedent). Under A1 stdio-MCP (OQ-A RATIFIED), the
framing wraps MCP's native JSON-RPC; the `claimed_tag` rides on the
tool-call argument shape (the way `bridge_whoami(claimed_tag)` does in
the probe — research note §8.2).

**Also produces (Step 1 deliverable, AC-8 evidence):** the **capability
inventory document** — a committed file listing every tool exposed on
the bridge with its capability classification:
- **safe-for-all** — exposed; safe for any tab to invoke (read repo
  state, validate-without-commit, contract description, echo,
  dispatch-receive without authority)
- **safe-for-some** — exposed; safe for some tabs but with documented
  caveats (Phase 1: empty — capability differentiation is deferred per
  OQ-V1 RESOLVED; included for future Phase 2 use)
- **not-on-bridge** — NOT exposed; dangerous operations remaining under
  Code's internal mechanisms (commit-to-main, authoritative dispatch
  with bind-on-Cray signature, configuration-changing writes outside
  read-only/validate-only scope)

The inventory anchors AC-8 review and the AC-5 negative test.

Output: the AC-1 transport contract + schema + the AC-8 capability
inventory.

#### Step 2 — Code-side server (lifecycle + audit log)

Implement the server, ratified to **stdio-MCP under A1**. Under A1 the
server is **Desktop-spawned** via `mcpServers` config in
`claude_desktop_config.json` (UWP path per Lesson #0016) rather than
Code-harness-spawned — soft-violation of ADR-013 D1 acknowledged (OQ-A
§Open Questions); mitigation = capability restriction per AC-8 +
forthcoming ADR-013 amendment. Server starts at Desktop launch and is
long-lived for the Desktop session (per Lesson #0017 §3 — stateless
discipline mandatory; no per-tab state accumulation across the Desktop
session). Implement against the Step 1 contract. Preserve ADR-013 D2:
the server exposes no path to a git operation (AC-4 (a); AC-8 inventory
"not-on-bridge" classification).

**Audit log (AC-4 (b)).** Server logs `claimed_tag` + observable
transport facts (PID, ppid, stdin_fd, stdout_fd, ts_ns, monotonic
counter) on every call. Log destination for **Phase 1 evidence
capture**: append to a JSONL file under `docs/research/private/`
(gitignored); the path is named in the AC-6 evidence file. If/when
authority operations land on the bridge in Phase 2+, the audit channel
moves to a tracked-but-redacted location — a Phase 2 design decision,
not pre-committed here.

#### Step 3a — Chat-side client

Implement the Chat-tab client against the Step 1 wire format. **No
OQ-B gate** — OQ-B = RESOLVED YES (FULL) per research note §3.2–§3.5
(T1, T2, T3, T4 all PASS); Chat surfaces user-MCP tools via the same
`mcpServers` channel as Code/Cowork. Chat invokes
`mcp__vero-bridge__<tool>` from its deferred list (loaded via
ToolSearch).

#### Step 3b — Cowork-side client

Implement the Cowork-tab client against the **same Step 1 wire format
and same tool surface** as Step 3a (cross-client parity per AC-7). **No
OQ-B gate** — OQ-B = RESOLVED YES (FULL) per research note §3.7–§3.8
(T6 + T7 PASS; Cowork end-to-end `bridge_ping(name="cowork-t7")` returned
pong at 2026-05-28T04:12:50+00:00). Cowork invokes
`mcp__vero-bridge__<tool>` from its deferred list (loaded via
ToolSearch) — identical primitive shape to Step 3a.

#### Step 4 — Round-trip echo (cross-client matrix) + live evidence capture

Wire Step 2 + Steps 3a + 3b together: capture the **cross-client live
evidence matrix** to a named file under `docs/research/private/` (AC-3 +
AC-6). Cells:
- **Chat→Code→Chat (echo)** — Chat client sends payload, Code server
  echoes per-session token, Chat reports match within bounded latency.
- **Cowork→Code→Cowork (echo)** — same logical operation, same wire
  format byte-by-byte (AC-7 parity), from Cowork.
- *(Optional, if v1 includes any Code→client push capability)*
  **Chat→Code (dispatch-receive without echo)** + **Cowork→Code
  (dispatch-receive without echo)** — round out the matrix with
  one-way-with-ack paths.

Each cell captures: payload, claimed_tag, observable signals (PID,
stdin_fd, ts_ns) from the audit log, echoed token (where applicable),
latency, any error text. Establish the transport-failure error contract
here in practice (OQ-T1; pin before tests).

#### Step 5 — Tests + lint clean (cross-client + adversarial + AC-8 negative)

Unit + integration tests cover the **cross-client matrix from both
client paths** (AC-5):
- **Happy path × 2 clients** (parse + dispatch + echo round-trip)
- **Boundary × 2 clients** (max payload, edge encodings, version skew)
- **Fail-closed × 2 clients** (malformed/truncated rejection,
  unknown-type, version mismatch, transport-failure error contract)
- **Adversarial cross-tab anti-spoof matrix (AC-4 (c))** — each tab
  attempts to claim each other tab's identity; assert server accepts
  per Option I but audit log captures discrepancy where one exists
  (Chat-vs-(Code∪Cowork) is discriminable; Code-vs-Cowork is not)
- **AC-8 negative test** — attempt to invoke a not-on-bridge operation
  via the transport returns a transport-layer "tool not found" error,
  not a tier-bypass

Plus the **G5 bypass-immune matrix re-run + git-over-transport negative
test** (AC-4 (a)). `pytest` + `ruff` + `mypy` clean (PLAN-0011 AC-6
discipline). Attach the case-coverage matrix (happy / boundary /
fail-closed / adversarial / concurrency) with every row mapped to a
test and any uncovered case named as residual risk. The adversarial
dimension now explicitly includes the cross-tab spoof matrix.

### Phase 2 — Future Cowork-client capabilities beyond basic transport (PLACEHOLDER — not minted)

> **Phase 2 is a placeholder**, not a deferred design. Basic Cowork-client
> transport ships in Phase 1 (Step 3b). Phase 2 is reserved for
> capabilities not yet specified — minted only when a concrete need
> arises. No sequencing gates apply to Phase 1.

#### Step 6 — (Reserved) Authority-bearing operation on the bridge

If/when an authority-bearing operation (e.g., a tab triggering a
bind-on-Cray dispatch, or a write outside the Phase 1 read-only /
validate-only scope) is proposed for exposure on the bridge, Phase 2
addresses the identity mechanism needed to safely expose it. Options to
revisit: **Option II** multi-server per-tab `mcpServers` entries (each
tab gets its own server process — but all tabs see all entries' tools,
so capability scoping inside server code is still shared-routing-defeated
for the Code+Cowork pair — see research note §8.5); **Option III**
out-of-band shared secret (blocked under current Desktop behavior per
T8–T12: Desktop strips Claude-injected env when spawning the server, so
no per-tab credential channel via env — see research note §8.4); or
other mechanisms not yet enumerated (e.g., MCP-level session metadata if
Anthropic ships it).

#### Step 7 — (Reserved) Long-lived session / scheduled-task carrier

If/when the bridge carries long-lived state across Desktop sessions or
across Cowork scheduled-task carrier patterns, Phase 2 addresses the
state-management mechanism (the server is stateless in Phase 1; this
would be the first design pressure for adding per-call durable state).

#### Step 8 — (Reserved) Sequencing-gate footnote

If a future v3 HTTP-loopback transport is ever explored (it is not in
v1 or v2 scope; A1 stdio-MCP supersedes the loopback assumption per
OQ-A RATIFIED), the OQ-C (ii-a)/(ii-b) public-endpoint re-test from
[`cowork-network-locus runbook`](../runbooks/cowork-network-locus.md) §4
would gate that work — included here as a footnote for archeology only.

## Verification

Maps 1:1 to AC-1…AC-8 (per-AC inline, focused single-file style):

- **AC-1** — contract + schema committed and reviewable; a parser can be
  written against it; contract includes `claimed_tag` audit field
  (audit-only — not authorization, per OQ-T3 RESOLVED Option I). OQ-A is
  RATIFIED (was a gate; now resolved).
- **AC-2** — start→accept→teardown test green for **both** client paths
  (Chat + Cowork); lifecycle note documents the Desktop-spawned
  long-lived server model (Lesson #0017 §3) + the A1 soft-violation
  acknowledgment.
- **AC-3** — **two** live round-trip evidence captures (Chat path +
  Cowork path), each within bounded latency, each with matching token;
  both evidence paths recorded in the named file under
  `docs/research/private/`. OQ-B is RESOLVED YES (was a gate; now
  resolved).
- **AC-4** — three sub-criteria:
  - (a) G5 bypass-immune matrix re-run stays green; negative test
    proves a git-over-transport request is denied at the deny layer.
  - (b) audit-log file present (server logs `claimed_tag` + observable
    transport facts — PID, stdin_fd, ts_ns — on every call); audit log
    is the AC-6 (live, not mocked) evidence channel for the identity
    model.
  - (c) adversarial cross-tab anti-spoof matrix evidence: each tab
    attempting to claim each other tab's identity is captured in the
    audit log with the discrepancy between claimed and observable
    signals; Chat-vs-(Code∪Cowork) discriminability is demonstrated
    (Chat PID ≠ shared instance PID); Code-vs-Cowork
    non-discriminability is explicitly documented (same PID, ppid,
    stdin_fd, stdout_fd; reference research note §8.4 discriminator
    matrix).
- **AC-5** — `pytest` green with a test per parse/dispatch/error path
  **from both client paths** (Chat + Cowork): happy × 2, boundary × 2,
  fail-closed × 2; plus the AC-4 (c) adversarial cross-tab spoof matrix
  tests (server accepts per Option I; audit log captures discrepancy);
  plus the AC-8 negative test (not-on-bridge operation returns
  transport-layer "tool not found" error, not a tier-bypass). `ruff` +
  `mypy` clean; case-coverage matrix attached.
- **AC-6** — live (not mocked) round-trip evidence file present for
  **both** clients (Chat + Cowork), in line with Lesson #15 §5
  live-vs-mock discipline; live evidence for AC-4 (c) spoof matrix is
  part of this file (it requires real cross-tab invocation to capture
  the audit-log discrepancy).
- **AC-7** — cross-client wire-format equality: both clients exercise
  the same wire format byte-by-byte for the same logical operation
  (provable by diffing the captured request frames from AC-3) + same
  capability scope per OQ-V1 RESOLVED (provable by the AC-8 capability
  inventory listing identical tool sets per client in the Phase 1
  column).
- **AC-8** — committed capability inventory document present (lists
  every exposed tool with safe-for-all / safe-for-some / not-on-bridge
  classification + Phase 1 per-client column showing uniform Phase 1
  scope per OQ-V1); the AC-5 negative test demonstrates a not-on-bridge
  operation returns transport-layer "tool not found" (not a
  tier-bypass).

**Verification-rigor (Cray directive, PLAN-0009 §Verification).**
`vero-bridge` is autonomy-adjacent infrastructure; a green suite is not
sufficient evidence of correctness. Each v1 component ships a
case-coverage matrix (happy / boundary / fail-closed / adversarial /
concurrency), every row maps to a test, uncovered cases are named as
residual risk, and sign-off states confidence explicitly — not "tests
pass." The adversarial dimension now explicitly includes the
**cross-tab spoof matrix** (AC-4 (c), AC-5): server accepts each spoof
(Option I design); audit log captures the discrepancy where the signal
is observable (Chat-vs-(Code∪Cowork) discriminable) and explicitly
documents the non-discriminability case (Code-vs-Cowork — same shared
instance B, no transport-level signal exists to discriminate). Sign-off
states the residual identity-spoofing risk explicitly + the
capability-by-tool-design (AC-8) compensating control.

## Open Questions

> *PLAN-0012-local labels.* OQ-A/OQ-B/OQ-V1 below are local to this PLAN
> and are **distinct** from the project-historical "OQ-A" (the
> ADR-vs-PLAN governance question, resolved 2026-05-27) and from the
> runbook's "OQ-C" (the network-locus experiment). The third transport
> OQ is named **OQ-T1** (not "OQ-C") to avoid collision with the runbook,
> per the authoring dispatch. Each OQ is a decision the reader must
> make.

> **Resolution batch 2026-05-28 (PM, PR #67 — Code-Cowork joint).**
> OQ-A RATIFIED, OQ-B already RESOLVED YES (PR #64), OQ-T3 RESOLVED
> (Option I), OQ-V1 RESOLVED (new). Evidence:
> `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` §3–§5
> (OQ-B probe matrix T1–T7) and §8 (OQ-T3 follow-on appendix, T8–T12
> spoof matrix + Option I selection) +
> `docs/lessons/0016-claude-desktop-uwp-sandbox-config-path.md` (UWP
> config-path lesson) + `docs/lessons/0017-mcp-cross-tab-visibility-empirical-probe.md`
> §3 corrected (tab-group routing — Chat alone on instance A;
> Code+Cowork share instance B). Code authored the §Open Questions
> update in PR #64 from research; Cowork authored the multi-section
> redraft (PR #67) per ADR-013 OQ-1 (Cowork retained as advisory
> governance drafter) — author≠reviewer holds across the two PRs.

> **Ratification + resolution batch 2026-05-28 (PM late, this PR — Code).**
> **PLAN Status flipped `Draft` → `Ready for execution`** (Cray ratified
> 2026-05-28 in the STATUS-reconcile review of PR #68). **OQ-T1
> RESOLVED `fail-closed`**, **OQ-T4 RESOLVED `serial-per-instance`**,
> **OQ-V2 DEFERRED with `version: int` stub directive** (include
> `version` field in wire format; server accepts only `v1`; full
> negotiation policy decided when client-codepath divergence becomes
> load-bearing). All four decisions adjudicated by Cray in a single
> session-22 routing turn; Code committed the PLAN edits per ADR-009
> D2. Phase 1 Step 1 (wire format + capability inventory) is now
> green-lit — gating on OQ-T1 + OQ-T4 satisfied; Step 1 wire-format
> contract uses fail-closed error semantics + serial-per-instance
> concurrency model + `version: int` field with `v1`-only acceptance.

- **OQ-A — Code-side transport mechanism. RATIFIED 2026-05-28
  (Code-Cowork joint PR — this PR): A1 = stdio-MCP.** ADR-013 D1 places
  MCP transport in Code (Tier 2) but does **not** pin *how* (stdio-MCP
  vs HTTP-loopback vs other); the cowork-network-locus runbook addresses
  only Cowork's egress, not the Code↔(Chat+Cowork) mechanism. *Options
  considered:* (1) stdio-MCP — native MCP framing, simplest lifecycle
  binding to the Desktop process tree; (2) HTTP-loopback — easier
  multi-client fan-out but adds a bound port + identity surface +
  Cowork-egress gate (runbook §3); (3) other (named pipe, Unix socket).
  *Selection:* **A1 stdio-MCP for v1** — Cray pre-decided 2026-05-28
  AM (recorded session 20 / PR #63 header); jointly ratified 2026-05-28
  PM (this Code-Cowork PR) once OQ-B = RESOLVED YES proved Chat+Cowork
  client viability and OQ-T3 resolution selected the identity model
  compatible with stdio-MCP's shared-process reality. **Soft-violation
  of ADR-013 D1 acknowledged:** under A1, the server is owned by Desktop
  (spawned via `mcpServers` config in `claude_desktop_config.json` — UWP
  path per Lesson #0016), not by the Code-harness process. Mitigation =
  capability restriction per AC-8 (no shell, no git, no network, no
  state in the server; safe-tool surface only) + future ADR-013
  amendment to formalize the spawn-ownership exception + AC-4 (b)/(c)
  audit-log + anti-spoof matrix evidence. ADR-013 D2 (PreToolUse
  commit-deny) is unchanged and remains deterministic regardless of
  transport. The ADR-013 amendment is **out of scope for this PLAN**
  (per §Out of Scope bullet 2) — tracked as a follow-on work item.

- **OQ-B — Chat-side (and Cowork-side) MCP-client primitive availability.
  RESOLVED YES (FULL) 2026-05-28 (PR #64).** All three tabs (Chat, Code,
  Cowork) surface `mcpServers`-configured user-MCP tools in their
  deferred lists and successfully invoke them end-to-end. Evidence:
  probe matrix T1 (Chat list), T2 (Chat invoke), T4 (Chat liveness
  Δ +31s), T3 (Code invoke), T6 (Cowork list), T7 (Cowork invoke) — all
  PASS; raw responses captured verbatim in research note §3.2–§3.8. The
  earlier Lesson #8 §1 table (Chat sees only `mcp-registry` +
  `Claude in Chrome`) was a snapshot **before** any user-MCP was
  configured; when `mcpServers` is provisioned, all three tabs surface
  the user-MCP tools uniformly alongside their tab-specific platform MCP
  stacks. **Cross-finding note (now actioned).** PR #64's "Cross-finding
  note (Goal/v2 reframing candidate)" flagged that the original Goal's
  Cowork-client deferral logic became technically unnecessary under A1
  stdio-MCP. This PR (Cowork-authored multi-section redraft) actions
  that reframe — see §Goal, §Out of Scope, §Steps (3a + 3b cross-client
  matrix). **OQ-B is no longer a gate for any Phase 1 step** — Steps 3a
  and 3b are unblocked.

- **OQ-T1 — Transport-failure error contract. RESOLVED 2026-05-28 PM
  late (Cray-adjudicated, this PR): `fail-closed` for Phase 1.** On
  connection drop / timeout / malformed frame / version-mismatch, the
  server **drops the call + logs the failure + does NOT retry**. No
  silent degradation; no fallback path. *Options considered:*
  (a) **fail-closed** (selected) — safest under autonomy-adjacent
  infrastructure; aligns with ADR-013 D2 deterministic-deny posture;
  simplest AC-5 error-contract tests; (b) bounded-retry (N retries
  with backoff then drop) — Phase 2 option if transient failures
  observed in production; adds AC-5 surface; (c) surface-to-Cray
  (server emits "transport degraded" UI signal) — premature without
  a UI surface in Phase 1. *Implementation mapping:* AC-1 wire-format
  error codes (Step 1) MUST encode the 4 failure modes (drop, timeout,
  malformed, version-mismatch) as distinct codes; AC-5 error-contract
  tests assert fail-closed semantics on each. *Code recommendation
  carried (session-22 handoff §4 Action 2 Recommendation):* bounded-
  retry reconsidered for Phase 2 if evidence of transient-failure
  pressure emerges; surface-to-Cray reconsidered if/when a UI surface
  exists. ADR-013 D2 PreToolUse commit-deny remains deterministic
  regardless of transport state — a transport failure cannot weaken
  the safety boundary.

- **OQ-T2 — PLAN status vocabulary (`Proposed` vs `Draft`). RESOLVED at
  commit (PR #63).** The original authoring dispatch said
  `Status: Proposed`; the PLAN template + PLAN-0009 OQ-4 say PLANs mint
  as `Draft`. Cowork authored with `Proposed` (per explicit dispatch
  instruction) and surfaced this as an OQ; Code reconciled to `Draft` at
  commit per Cowork's recommendation. The dispatch's `Proposed` was a
  wording error (ADR-vocabulary leak from the withdrawn ADR-014 drafting
  context). The header flag reflects the reconciliation. **No further
  decision needed.** Preserved here for historical record of the
  reconciliation.

- **OQ-T3 — Per-client identity / authentication. RESOLVED 2026-05-28
  PM (Cray-ratified, PR #64 + this PR): Option I = single shared server
  + capability-by-tool-design; `claimed_tag` retained as audit-only;
  server CANNOT distinguish Code from Cowork via transport-level
  signals; safe-tools-only surface.**

  *Empirical resolution evidence* (research note §8.2 — verbatim probe
  T8–T12; §8.4 discriminator matrix; §8.5 Option I selection rationale;
  §8.6 OQ table mapping; §3.1 corrected tab-group routing in Lesson
  #0017): under A1 stdio-MCP, Desktop spawns 2 server instance pairs
  per `mcpServers` entry on fresh launch; **Chat → instance A
  (PID=613) alone; Code + Cowork → instance B (PID=2092, ppid=2065)
  share**. T10 (Chat claiming `cowork`) and T11 (Cowork claiming `chat`)
  both succeeded — server echoes `claimed_tag` verbatim; **spoofing is
  always possible**. The server can discriminate Chat-vs-(Code∪Cowork)
  via PID/stdin_fd; it **cannot** discriminate Code-vs-Cowork by any
  observable transport signal.

  *Option I details (verbatim from research note §8.5):*

  > Selected over Option II (multi-server per-tab `mcpServers` entries)
  > — doesn't close attack surface because all tabs see all entries'
  > tools, and capability scoping inside server code is
  > shared-routing-defeated for Code/Cowork — and over Option III
  > (out-of-band shared secret) — Desktop strips env (T8–T12 empirical
  > evidence), no viable per-tab credential channel under current
  > Desktop behavior.
  >
  > Option I details:
  > - 1 `mcpServers` entry (continues current vero-bridge-probe pattern,
  >   evolved into production vero-bridge)
  > - `claimed_tag` retained as **audit-only** (logged server-side with
  >   timestamp + observable signals; not used for authorization)
  > - **Tool surface restricted to tab-tier-safe operations** (read-only
  >   repo state, validate-without-commit, contract description,
  >   dispatch-receive). Dangerous operations (`commit_to_main`,
  >   authoritative dispatch) **not exposed as MCP tools** — Code uses
  >   its own internal mechanism + ADR-013 D2 deterministic deny hook
  >   for the deny boundary
  > - Threat model rationale: single-operator (Cray) — no multi-tenant
  >   adversary — so capability-by-tool-design is sufficient defense
  >   without spoof-resistant identity
  > - Phase 2+ deferred: if write/dispatch-with-authority operations
  >   needed later, revisit Option II/III with out-of-band credential
  >   channel (perhaps via Anthropic-provided sandbox secret injection
  >   if it ships)

  *Implementation mapping:* AC-4 (b) (audit log of `claimed_tag` +
  observable signals); AC-4 (c) (adversarial spoof matrix smoke); AC-8
  (capability-by-tool-design inventory); §Steps Step 1 (claimed_tag in
  wire format; capability inventory); §Steps Step 2 (audit log
  destination). Originally surfaced as the per-tab-identity concern in
  the ADR-0014 take-2 Cowork advisory pass
  (`.claude/handoffs/session-16/2026-05-27-1330-cowork-adr0014-take2-verification.md`
  Focus-2 OQ-C addition (b)); refined session 21 morning (OQ-B probe
  revealed shared-process); resolved session 21 afternoon (T8–T12 spoof
  matrix). Refines [[lesson-0017-mcp-cross-tab-visibility-empirical-probe]]
  §3 (tab-group routing — corrected from "all tabs share" to "Chat alone
  on instance A; Code+Cowork share instance B").

- **OQ-V1 — Per-client capability scoping convention. RESOLVED 2026-05-28
  PM (this PR): Phase 1 = same safe-tool set for all tabs (Chat,
  Cowork, Code); capability differentiation deferred to Phase 2+.** The
  bridge does **not** encode per-tab capability scopes in Phase 1; the
  safe-tool surface is uniform across all clients (AC-7 cross-client
  parity; AC-8 inventory Phase-1 column = same set for every client).
  Phase 2+ may introduce per-tab scoping if authority operations land on
  the bridge, but the mechanism (Option II multi-server, Option III
  out-of-band shared secret, or other — see OQ-T3 Option I details +
  Phase 2 §Steps Step 6) is a **Phase 2 design choice — not
  pre-committed here**. The Phase 1 uniform-scope choice is binding
  evidence that the bridge does not depend on (and cannot enforce)
  per-client capability boundaries at the transport layer — any future
  authority-bearing operation must come with its own out-of-band
  identity mechanism, not an attempt to discriminate at the bridge
  layer.

- **OQ-T4 — Cross-client concurrency / ordering. RESOLVED 2026-05-28
  PM late (Cray-adjudicated, this PR): `serial-per-instance` for
  Phase 1.** Surfaced by Cowork during PR #67's redraft (completion
  handoff §4) and lifted into the PLAN per Cray's 2026-05-28 PM
  decision; adjudicated by Cray in the same session-22 routing turn
  that ratified the PLAN. Under A1 stdio-MCP with the empirical
  tab-group routing (Lesson #0017 §3.1 corrected: Code + Cowork share
  instance B), if Code and Cowork both issue a `bridge_status()` or
  `echo(payload)` concurrently to the same server instance, the server
  **queues incoming calls and processes one-at-a-time per instance**.
  The MCP stdio protocol is JSON-RPC and protocol-permits concurrent
  in-flight requests (request `id` field disambiguates responses), but
  the server-side handler does NOT exploit that — it serializes.

  *Selection:* **(a) serial-per-instance.** Simplest contract for AC-5
  concurrency-dimension tests; deterministic audit-log ordering;
  acceptable latency profile for Phase 1's safe-tool surface (no
  long-running tools — `echo`, `bridge_status`, `bridge_whoami`,
  `read_repo_path`, `validate_handoff_frontmatter`, `lint_status`,
  `dispatch_receive` are all sub-second). *Options not selected:*
  (b) concurrent-per-call (better latency, harder audit-log
  reasoning) — Phase 2 optimization if/once contention-pressure
  evidence exists; (c) serial-per-tool / concurrent-across-tools
  (compromise) — most expressive, most complex, premature for Phase 1.

  *Implementation mapping:* AC-5 concurrency tests (Step 5 §6 §matrix)
  assert serial-per-instance ordering on near-simultaneous calls from
  Code + Cowork to instance B; audit-log assertion that two concurrent
  `dispatch_receive(envelope)` payloads land in a defined order (the
  one with earlier server-side receive timestamp wins). *Code
  recommendation carried (session-22 handoff §4 Action 3
  Recommendation):* concurrent-per-call reconsidered for Phase 2 once
  evidence of contention pressure emerges.

- **OQ-V2 — Wire-format version negotiation across clients. DEFERRED
  2026-05-28 PM late (Cray-adjudicated, this PR): include `version: int`
  field in the wire format; Phase 1 server accepts only `v1`; full
  negotiation policy (per-session / per-call / per-tab) decided when
  client-codepath divergence becomes load-bearing.** Surfaced by Cowork
  during PR #67's redraft (completion handoff §4) and lifted into the
  PLAN per Cray's 2026-05-28 PM decision; deferral confirmed by Cray
  in the same session-22 routing turn that ratified the PLAN.

  *Phase 1 wire-format directive (binding, applies to Step 1):*

  - Every wire frame carries a `version: int` field (mandatory; not
    optional; not defaultable).
  - Phase 1 server accepts **only `version: 1`**. Any frame with
    `version != 1` is rejected per OQ-T1 fail-closed semantics
    (transport-failure error contract → `version-mismatch` error
    code).
  - Clients (Chat + Cowork wrappers) emit `version: 1` byte-for-byte
    identically per AC-7 cross-client parity.

  *Policy decision deferred.* The choice between (a) **per-session**
  (server pins version on first call from a connecting client and
  rejects mismatched-version subsequent calls on the same session —
  strict, surfaces drift immediately), (b) **per-call** (server
  accepts any supported version on any call — permissive, allows
  incremental client upgrade), and (c) **per-tab** (server allows
  different versions on different instance routes — Chat-instance vN,
  Code+Cowork-instance vN+1) is deferred until client codepaths
  diverge. Rationale: in Phase 1 both clients are controlled by this
  project and share a single wrapper / wire format; no divergence
  pressure exists. The `version: int` field is the **forward-
  compatibility stub** that lets us defer the policy decision without
  baking in a wire-format breaking change later.

  *Pin trigger:* policy decision required before any Phase 2+ change
  that bumps the wire format to `v2` (e.g. adding new tool types,
  changing envelope schema, adding authority-bearing operations per
  OQ-V1 Phase 2 reconsideration).

  *Implementation mapping:* AC-1 (Step 1 wire format) — `version: int`
  field mandatory in message framing; AC-5 (Step 5 tests) — assert
  `version: 0` and `version: 2` both rejected with `version-mismatch`
  error per OQ-T1 fail-closed.

## Implementation Notes

Drafted by Cowork in Tier-1 (governance authoring) mode under the interim
ADR-009 D1 process, retained as the advisory governance drafter per
ADR-013 OQ-1 (lines 119–127). Cowork has no commit authority (ADR-009 D2;
ADR-013 D2 deterministic `pretooluse_git_deny.py`); Code reviews and
commits this file. AI-assisted per project convention (commit body, never
as `Co-Authored-By`, CLAUDE.md §7).

**Author≠reviewer disclosure (ADR-012 D4.3 / ADR-013 OQ-1).** This PLAN
has had two distinct authoring rounds:

1. **Original draft (PR #63, 2026-05-28 AM).** Cowork-authored from a
   Code-authored dispatch
   (`.claude/handoffs/session-19/2026-05-28-0930-code-cowork-plan0012-vero-bridge-dispatch.md`)
   — drafter (Cowork) distinct from outline originator (Code/Cray);
   independent-tier separation intact for the PLAN's structure, as in
   PLAN-0009. **Partial-overlap caveat (disclosed):** transport
   *substance* was previously deliberated in Cowork's own Tier-1b
   advisory passes on the withdrawn ADR-014
   (`2026-05-27-1145-...advisory-pass.md` and
   `2026-05-27-1330-...take2-verification.md`), where Cowork raised the
   Cowork-client locus question (→ OQ-C experiment), the ADR-vs-PLAN
   governance question, and the per-tab-identity concern (→ OQ-T3).
   Those Cowork contributions informed the original PLAN-0012 draft, so
   the independent-deliberation check on *those specific framings* is
   partially reduced.

2. **OQ resolutions update (PR #64, 2026-05-28 PM).** Code-authored
   from research evidence
   (`docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md`
   §3–§5 + §8) — author (Code) distinct from drafter of the original
   §Open Questions text (Cowork); separation intact because the
   resolutions lift research findings, not new governance.

3. **Multi-section redraft (this PR, 2026-05-28 PM).** Cowork-authored
   redraft of six sections (§Goal, §Acceptance Criteria, §Out of Scope,
   §Steps, §Open Questions, §Verification) from a Code-authored dispatch
   (`.claude/handoffs/session-21/2026-05-28-1325-code-cowork-plan0012-v1-expand-dispatch.md`,
   gitignored), to operationalize Cray's path-C decision
   (v1 = Code↔(Chat+Cowork), not Code↔Chat-only) and encode the OQ-T3
   RESOLVED Option I identity model under A1 stdio-MCP. Cowork is
   retained as the advisory governance drafter per ADR-013 OQ-1.
   **Partial-overlap caveat carries forward** — Cowork's original-draft
   framings (Cowork-client deferral logic now removed,
   per-tab-identity concern now resolved by Option I) are touched by
   this redraft, so the independent-deliberation check on those
   *specific* framings remains partially reduced. Code's review +
   Cray's ratification of this PR are the remaining independent checks.

   **OQ-T4 + OQ-V2 lift-from-handoff at commit (Code-edit, 2026-05-28
   PM).** Cowork surfaced two new OQs (OQ-T4 cross-client concurrency;
   OQ-V2 wire-format version negotiation) in §4 of the completion
   handoff. Per Cray's 2026-05-28 PM decision (Option A — "still open,
   Cray adjudicates separately"), Code lifted both OQs verbatim into
   the §Open Questions section at commit time so they stay visible
   after the gitignored handoff cycles. Author≠reviewer is preserved
   because Code lifts surfaced-but-unresolved content, not new
   governance. Cray adjudicates the OQ-T4/V2 decision options
   separately (likely a follow-up Code edit or a future Cowork
   dispatch when Phase 1 reaches the relevant step).

Code's review (ADR-009 D3 step 6) + Cray's ratification on this PR are
the live verification checks for the redraft.

**Schema / fact-pack self-check (K-1 validator gap flagged).** Per K-1
(Lesson #8 §1; `mcp__workspace__bash` refuses the WSL-UNC cwd — confirmed
across sessions), Cowork cannot run repo tooling. This PLAN is **not** a
`.claude/handoffs/` artifact, so `validate_handoff.py`'s frontmatter
schema does not apply to *this file*; the relevant canonical shape is the
PLAN template (`docs/plans/0000-template.md`), matched field-by-field
(Status / Owner / Created / Related ADRs / Goal / Acceptance Criteria /
Out of Scope / Steps / Verification — present, in order, plus the
dispatch-required Related Plans / Replaces header lines). The companion
completion handoff *is* a `.claude/handoffs/` artifact; its frontmatter is
mental-validated against `tools/handoffs/_schema.py` REQUIRED_FIELDS with
the K-1 gap explicitly flagged there. All repo citations in this draft
were verified against HEAD via Read/Glob this session:

- `0012` is the next free PLAN number (`docs/plans/` glob: `0004` +
  `0010` active, `done/{0003,0005,0006,0007,0008,0009*,0010-step1,0011}`,
  templates; no `0012*`).
- ADR-013 D1 (MCP-transport-in-Tier-2) + OQ-1 (Cowork advisory drafter) +
  D2 (commit boundary) — verified in `docs/adr/0013-autonomy-axis-relocation.md`.
- `docs/adr/0014-WITHDRAWN.md` (tombstone — PLAN-0012 replaces it) +
  `docs/runbooks/cowork-network-locus.md` (§2 finding, §3 v1 implication,
  §4 (ii-a)/(ii-b) open question) — both exist at HEAD.
- PLAN-0009 §Out-of-Scope `vero-bridge` re-anchor + OQ-3 no-new-ADR
  precedent — verified in `docs/plans/done/0009-subagent-topology.md`.
- Lesson #15 §7 (PLAN-0011 live-evidence dependency rolls into PLAN-0012
  sequencing) — verified in
  `docs/lessons/0015-classifier-payload-starvation-stop-events.md`.
- Both ADR-0014 Cowork advisory handoffs exist in
  `.claude/handoffs/session-16/`.

**Additional citations verified for the 2026-05-28 PM redraft (this PR):**

- `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` §3.2–§3.8
  (OQ-B probe matrix T1–T7) + §8.1–§8.7 (OQ-T3 follow-on appendix:
  T8–T12 raw responses, §8.4 discriminator matrix, §8.5 Option I
  selection, §8.6 OQ table mapping, §8.7 anti-pattern catch) — verified
  via Read this session.
- `docs/lessons/0016-claude-desktop-uwp-sandbox-config-path.md` (UWP
  config-path lesson; cited for Step 2 server lifecycle note) —
  verified via Read this session.
- `docs/lessons/0017-mcp-cross-tab-visibility-empirical-probe.md` §3
  (corrected tab-group routing: Chat alone on instance A; Code+Cowork
  share instance B) — verified via Read this session.
- `docs/runbooks/cowork-network-locus.md` (Goal-section reframe rationale
  — runbook addresses network egress, not MCP-client viability under
  stdio-MCP) — verified via Read this session.

**Non-commit reminder (ADR-009 D2 / ADR-013 D2 — load-bearing).** This is
a Cowork draft. Cowork does not commit; only Code commits, enforced
deterministically by `pretooluse_git_deny.py` (bypass-immune even to
`bypassPermissions`). Code applies the file write + commit on the
appropriate branch after review.
