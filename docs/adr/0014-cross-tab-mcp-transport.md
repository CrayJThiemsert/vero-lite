# ADR-014: Cross-Tab MCP Transport — Replacing Paste-Relay Between Code, Cowork, and Chat

**Status:** Proposed
**Date:** 2026-05-27
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-013 (Autonomy Axis Relocation — **this ADR is the natural follow-on to D1's Phase-3 boundary + OQ-1 resolution**), ADR-012 (Cowork second free-form tier — **transport must preserve both free-form venues**), ADR-009 (Cowork-Tier-1 topology — **D2 "only Code commits" boundary must remain intact; D3 K-1/K-2 workflow constrains the Cowork side**), ADR-006 (vertical plugin architecture — cross-tab transport is vertical-agnostic core infrastructure). CLAUDE.md §1 (precedence), §4 (memory architecture — repo remains source of truth), §6 (4-tier table), §11 (Tier 2 operational policy). Lesson #8 (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md` — K-1/K-2 sandbox facts). Lesson #15 (`docs/lessons/0015-classifier-payload-starvation-stop-events.md` — classifier transcript-load fix; §7 explicitly states the bug does not invalidate ADR-013 D1). PLAN-0009 (`docs/plans/done/0009-subagent-topology.md` — subagent topology DONE; §Out-of-Scope names `vero-bridge` as Phase 4; OQ-3 "no new ADR" precedent). Source artifacts referenced from ADR-013: `docs/research/public/chat_harness_extension_points_analyzed.md` (Chat 5-point analysis), `.claude/handoffs/session-10/2026-05-23-0345-cowork-harness-extension-points-direction-b.md` (Cowork Direction-B forcing-fact capture). Cowork advisory pass on take 1: `.claude/handoffs/session-16/2026-05-27-1145-cowork-adr0014-advisory-pass.md`.

> **Ratification status.** Cray ratified the decision to author this ADR in
> free-form (2026-05-27). This take 2 draft is **Proposed**; Code flips to
> **Accepted** in the commit per ADR-009 D2 + ADR-013 D1 phasing, after
> Cray reviews the open questions in §Open Questions — most importantly
> the blocking OQs (OQ-A naming/governance, OQ-B sequencing,
> OQ-C feasibility). This ADR **codifies a direction Cray has already
> named**, not a re-litigation of whether cross-tab MCP transport is
> desirable.

> **Amendment scope.** This ADR **does not amend** ADR-009 D2, ADR-012,
> or ADR-013 D1–D5. It **operationalizes** ADR-013 D1's Phase-3
> boundary: where ADR-013 D1 named "MCP transport" as one of the
> autonomy primitives that lives in Code (Tier 2), this ADR specifies
> the cross-tab transport topology that lets Cowork's retained advisory
> drafts (ADR-013 OQ-1 resolved) and Code's execution-driven dispatches
> flow without Cray's manual paste-relay. ADR-009 D2 ("only Code
> commits") is **preserved unchanged** — MCP transport must not become
> a side-channel for non-Code identities to bypass the commit boundary.
> Per CLAUDE.md §1 precedence, "most recent accepted ADR wins" applies
> once this ADR is accepted. **OQ-A surfaces the genuine question** of
> whether the right artifact for this work is an ADR at all or a
> PLAN under already-Accepted ADR-013 D1 (per PLAN-0009 OQ-3 precedent).

## Context

### The bottleneck this ADR addresses

ADR-013 §Context named the structural problem in one sentence: *the
latency of the whole pipeline equals "Cray is at the keyboard."* The
4-tier model (CLAUDE.md §6) routes every inter-tier handoff through
Cray as a human relay — Code finishes → Cray reads → Cray pastes to
Chat/Cowork → next dispatch authored → Cray reads → Cray pastes to
Code → execute. ADR-013 addressed the **execution** side of this
bottleneck by relocating the autonomy axis into Code + subagents
(hooks, subagents, MCP servers, `defer` resume), letting Code proceed
on the clearly-best path without a Cray paste.

ADR-013 deliberately deferred the **cross-tab transport** side. D1
retains Cowork as the advisory drafter of governance artifacts even
after Phase 3 (OQ-1 resolved): the Plan subagent inside Code may draft
ADRs/PLANs, but Cowork keeps a draft/review role so an author≠reviewer
separation that a single-harness subagent cannot supply is preserved.
ADR-013 D3 retains the two free-form venues (Cowork Tier-1b and Chat).
Both retentions presuppose that Cowork's advisory drafts can reach
Code, and Code's execution-driven dispatches can reach Cowork for
review — *somehow*. ADR-013 did not say how. Until that "somehow" is
specified, every retained Cowork advisory pass and every Chat
free-form consultation re-incurs the paste-relay cost that ADR-013
diagnosed.

### The forcing fact (carried forward from ADR-013)

ADR-013 §Context recorded the forcing fact: **hooks, subagents, MCP
servers, and the headless / Agent-SDK `defer` resume execute only
inside Claude Code (Tier 2)**. Cowork and Chat are sandboxed desktop
surfaces. Lesson #8 documents the two consequences of that sandbox:

- **K-1 — bash UNC refusal.** Cowork's sandbox cannot execute shell
  commands inside a WSL-UNC-mounted repo. The sandbox is a **remote
  cloud Linux VM** that receives the UNC string as `cwd` and rejects
  it. Cowork's `Read` / `Glob` / `Write` work because they are proxied
  through the Windows desktop client; bash and network execute in the
  remote VM, not on Cray's machine.
- **K-2 — `.claude/` write block.** Cowork's `Write` tool refuses any
  path under `.claude/`; the documented exempt-subdir allowlist is not
  honored in the Cowork sandbox.

Both are Anthropic-side architectural facts with no shipped fix
(Lesson #8 §1, tracked tickets). **Any cross-tab MCP transport design
that asks Cowork to run an MCP *server* hits K-1 directly** —
listening on a socket, accepting connections, or maintaining a
long-lived server process all require the sandbox bash that K-1 denies.
This ADR must reckon with the asymmetry: Code can host MCP servers
(it has the harness, the local filesystem, and unrestricted bash);
Cowork and Chat cannot host them, only consume them. The Cowork
*client* side carries its own reachability question — see OQ-C —
because a loopback socket bound on Cray's machine is not on the
Cowork-VM's localhost.

### Repo reality (verified at HEAD this session)

Take 1 of this ADR carried a stale snapshot of repo state (pre-session-
14); take 2 corrects to HEAD per the Cowork advisory pass §1 C1 / §2
C3-C4.

- **PLAN-0007 (Phase 1, harness autonomy plumbing — hooks, classifier-
  dispatch, Telegram notification)** MERGED at commit `b2ea9b8` on
  2026-05-23 → archived to `docs/plans/done/0007-…`.
- **PLAN-0008 (Phase 2)** fully closed → `docs/plans/done/0008-…`.
- **PLAN-0009 (Phase 3 — subagent topology)** **DONE**; archived to
  `docs/plans/done/0009-subagent-topology.md`. The `plan-drafter` and
  `explore-research` subagents exist on disk. **This very draft is a
  `plan-drafter` artifact** — proof that Phase 3 has landed.
- **PLAN-0010 (Phase 3.5 — scheduled-task autonomy loop)** active.
- **PLAN-0011 (classifier-transcript-load fix, Lesson #15 §4)**
  archived to `docs/plans/done/0011-…`.
- **Next free PLAN slot:** **0012** (OQ-A asks whether the companion
  implementation work should mint as PLAN-0012 under ADR-013 D1 or as
  PLAN-0012 under this ADR).
- **ADR slots existing:** `0000–0010 + 0012 + 0013`. **`0011` is
  reserved** for the action-approval / audit framework (ADR-013
  §Context + OQ-2-resolved; PLAN-0009 OQ-3). `0014` exists on disk as
  this very draft. The Postgres-image ADR earmark from ADR-013
  §Consequences (Neutral) is now ≥ 0015; **`0011` stays reserved**.
- **Session-15/16 classifier-bridge commits** (`168baff` PR #49 Option-2
  WSL bridge; `885581a` PR #48 superseded) are **not** PLAN-0007
  shipment — take 1 mis-attributed them.
- Lesson #15 (classifier payload starvation — Stop events) is
  **codified** at `docs/lessons/0015-classifier-payload-starvation-
  stop-events.md`. Its §4 specifies the fix (transcript load for Stop
  events in `_build_user_message`); its §7 explicitly states the bug
  **does not invalidate ADR-013 D1** — the bug is in *how* Sonnet sees
  the dispatch trigger, not in *whether* Sonnet runs in Code (Tier 2).
  PLAN-0011 archived the fix as done, but live in-session auto-dispatch
  evidence beyond the gated smoke test is still pending — see OQ-B.

### The decision Cray made

Cray ratified the decision to author a governance artifact for this
work in free-form (2026-05-27). The ratification covers the
*direction* — adopt MCP as the cross-tab transport mechanism — but
leaves five sub-decisions open for Cray adjudication at review:
naming/governance (ADR vs PLAN), sequencing (Lesson #15 live evidence),
feasibility (Cowork client locus), topology (one bus vs N peer
servers), authentication, and Chat-side capability. The blocking
three (OQ-A, OQ-B, OQ-C) must resolve before Proposed → Accepted; the
remainder (OQ-1, OQ-4, OQ-5) can resolve at implementation time. See
§Open Questions.

## Decision

This ADR encodes four decisions (D1–D4). Each carries a rationale and
the alternative considered and rejected. D2 references OQ-C and OQ-1;
D4 is re-grounded against Lesson #15 sequencing per the Cowork advisory
pass §1 C1.

### D1: Adopt MCP as the cross-tab transport mechanism

The cross-tab handoff channel between Code, Cowork, and Chat is **MCP
(Model Context Protocol)** — the same protocol Anthropic uses for tool
integration — rather than shared filesystem, custom REST endpoints, or
a bespoke WebSocket layer. Concretely: Code (Tier 2) hosts one or more
MCP servers; Cowork (Tier 0 / 1 / 1b) connects as an MCP client and
calls tool endpoints to read advisory drafts staged for review, post
review comments, and pull execution dispatches for second-perspective
input; Chat (Tier 1, repo-blind) connects as a more restricted client
for free-form consultation that does not need repo grounding.

The **repository remains the durable source of truth** (CLAUDE.md §4).
MCP transport is **complementary and ephemeral** — it moves *pointers*
to artifacts (paths in `docs/adr/`, `docs/plans/`, `.claude/handoffs/`),
delivers *runtime* signals (e.g., "advisory pass requested", "review
complete"), and surfaces lightweight conversational state. It does
**not** replace the repo as the canonical store; artifacts still land
on disk and ride through git. MCP is the signaling layer; the repo is
the substrate.

PLAN-0009 §Out-of-Scope already named this work as **"Phase 4 — MCP
`vero-bridge` cross-surface transport. Build only after subagents
prove out. Carry to PLAN-0010."** OQ-A asks whether the working name
in this ADR (`mcp-handoff-bus`) should be reconciled with the existing
`vero-bridge` name.

- **Rationale:** MCP is the only transport whose protocol Anthropic
  has *already* embedded into all three Claude surfaces (Code, Cowork,
  Chat) as a first-class extension point. Picking it avoids inventing
  a parallel protocol stack and inherits Anthropic's evolving tooling.
  It also composes with ADR-013 D1's relocation: MCP servers are
  explicitly named as Tier-2-only primitives, so hosting them in Code
  matches the autonomy-axis topology rather than fighting it.
- **Alternatives rejected:** shared-filesystem-only (substrate, not
  signaling); custom REST/WebSocket (reinvents what MCP supplies). See
  §Alternatives Considered for full reject rationales.

### D2: Topology — Code hosts MCP servers; Cowork is client-only; Chat is restricted client

**What runs where (subject to OQ-1 adjudication on bus vs peer
topology; the Cowork-client side is subject to OQ-C feasibility
verification):**

| Tier | MCP role | Capability | Constraint |
|---|---|---|---|
| **Code (Tier 2)** | MCP **server(s)** host | Listens; serves tool endpoints for advisory-draft staging, review-comment intake, dispatch publication, execution-state signaling | Only Code can host servers (forcing fact — Tier-2-only primitive per ADR-013 §Context) |
| **Cowork (Tier 0 / 1 / 1b)** | MCP **client** | Connects to Code-hosted server; calls tool endpoints to read drafts, post review comments, fetch dispatches needing advisory input | K-1 / K-2 prevent Cowork from hosting a server. **Whether the Cowork *client* can reach a Code-hosted loopback socket depends on whether the client executes desktop-proxy-side or sandbox-VM-side — see OQ-C (blocking).** |
| **Chat (Tier 1, repo-blind)** | MCP **client (restricted)** | Connects for free-form consultation; receives non-repo-grounded prompts only | Chat has no repo read; transport must respect that — payloads to Chat must be self-contained per ADR-012 D2 repo-blind routing. Chat's MCP-client capability is unverified (OQ-5). |
| **Cray (Tier 3)** | Out-of-band | Telegram notification (existing per ADR-013 D5); not an MCP participant | Cray adjudication remains the human gate; MCP transport must surface notifications upstream rather than substitute for them |

**On topology — one bus vs N peer servers:** Cowork's Direction-B
analysis (referenced from ADR-013) sketched both options. A single
**bus server** in Code is simpler to operate but couples everything
into one process. **N peer servers** compose better but multiply the
operational surface. **Cray to adjudicate (OQ-1).** This ADR's D2
fixes only the *role assignment* (who is server, who is client); the
*server count* and *server name* (see OQ-A `vero-bridge` reconciliation)
are open.

- **Rationale (Code = server host):** the forcing fact carried from
  ADR-013 — MCP servers are Tier-2-only. Hosting in Code aligns
  capability with topology. Code already has the WSL filesystem, the
  hook layer (ADR-013 D2/D4), and the commit boundary (ADR-009 D2);
  putting the transport hub there means signaling can be
  hook-integrated and commit-aware.
- **Rationale (Cowork = client-only):** K-1 (bash UNC refusal) makes
  hosting a server in the Cowork sandbox structurally impossible
  without Anthropic shipping a fix. Client-only matches what Cowork
  *can* do (proxied Read/Write per Lesson #8). **Note:** even
  client-only is not free — see OQ-C for the loopback-reachability
  question.
- **Alternative rejected for v1 — Cowork hosts a server via a WSL-side
  bridge process:** introduces a fragile out-of-harness daemon
  contradicting the "no-state-outside-the-repo" principle (CLAUDE.md
  §4). Surfaced as OQ-2 in case Cray wants to revisit.

### D3: Authentication / authorization — preserve ADR-009 D2 "only Code commits" boundary

The MCP transport **must not become a side-channel** that lets a
non-Code identity perform actions ADR-009 D2 + ADR-013 D2 reserve to
Code (commits, pushes, branch / worktree operations, tracked-file
writes outside `docs/adr/`, `docs/plans/`). Concretely, the MCP server
endpoints exposed to Cowork and Chat clients are **read-mostly**:

- **Cowork client may:** read advisory-draft pointers; post review
  comments (stored to a `docs/research/private/` or comparable path
  Cowork already has write scope to); fetch execution-dispatch
  payloads queued for advisory review; signal "review complete" via a
  tool call that updates a Code-managed status file.
- **Chat client may:** receive consultation payloads (repo-blind);
  return free-form responses captured as `phase: discussion` handoffs
  per ADR-012 D3 if the conversation warrants persistence.
- **Neither Cowork nor Chat may:** call any MCP endpoint that triggers
  a `git commit`, `git push`, `git mv`, or write to a tracked path
  outside the existing ADR-009 D2 write-scope table. The MCP server in
  Code enforces this at the endpoint layer — there is no "commit on
  behalf of caller" endpoint. The deterministic `PreToolUse deny`
  hook from ADR-013 D2 remains the load-bearing safety boundary; D3
  here is a *belt-and-suspenders* refusal at the MCP endpoint layer so
  the boundary fails closed at two levels.

Authentication between Code and the client tabs is **localhost-only
in v1** — MCP servers bind to a loopback interface (or a
WSL-namespace-local socket) reachable only from the same machine. **The
v1 binding strategy is contingent on OQ-C** — if the Cowork MCP client
executes in the sandbox VM, "Cray's loopback" is unreachable and v1
must choose between (i) waiting for an Anthropic-side change, (ii)
relying on a desktop-side client locus that does not yet exist, or
(iii) accepting that v1 serves only Chat (if OQ-5 also resolves
positively) and the Code-internal subagent surface. No cross-machine
transport is in scope. The transport-layer security question
(TLS / token-based auth / per-tab identity) is deferred to OQ-4.

- **Rationale:** ADR-009 D2's commit fail-safe is the single rule
  ADR-013 D2 chose to make *deterministic* precisely because it must
  not be eroded as autonomy increases. Adding a transport without
  thinking through the commit boundary would risk re-introducing the
  exact erosion ADR-013 D2 closed. The endpoint-layer refusal is cheap
  belt-and-suspenders that costs nothing if the hook layer already
  catches.
- **Alternative considered — let Cowork commit via MCP for governance
  drafts (relax D2 inside the MCP channel):** would simplify the
  flow. *Rejected:* contradicts ADR-013 D2 hook-level enforcement and
  the recently-reinforced "only Code commits" boundary.

### D4: Phasing — defer transport build until Stop-event auto-dispatch is functional end-to-end

The cross-tab MCP transport implementation lands **after** the
Stop-event auto-dispatch arm (PreToolUse + SubagentStop classifier →
Sonnet judgment → dispatch / advisory signal) is functional
end-to-end *with live in-session evidence beyond the gated smoke
test*. That arm is the headline consumer of the proposed transport —
it carries dispatch and advisory signals into Cowork / Chat. The
**fix code is shipped** as of session 17: the `_build_user_message`
transcript-load fix from Lesson #15 §4 landed in **[PR #53][pr53]**
(commit `8d421fc`), executing PLAN-0011 (now in
`docs/plans/done/`); the gated live-API smoke
(`tests/handoffs/test_classifier_live_smoke.py`,
`RUN_LIVE_CLASSIFIER_TESTS=1`) PASSED against real Sonnet
(`decision: dispatch, matched_rows: ["D1"]`). What is **not yet**
done is the verbatim in-session re-run of the Smoke 2 / Smoke 3
triggers (AC-3 of PLAN-0011 was reframed → deferred-with-fresh-trigger
per documented meta-awareness contamination — the agent reads the
scenario file → recognizes the prompt as a test → behaves cautiously,
biasing the classifier's input). Until that fresh-trigger live
re-run shows D1/D2/C-row dispatch firing in a real session
boundary, the transport optimizes a flow whose payload is
empirically unproven in-the-wild.

[pr53]: https://github.com/CrayJThiemsert/vero-lite/pull/53

Until that evidence lands:

- The existing scratchpad + filesystem handoff workflow (Lesson #8 §2)
  remains the operating contract for Cowork advisory drafts.
- Cray's paste-relay continues for cross-tab signaling — accepted as
  the interim cost.
- This ADR's commit lands now (Proposed → Accepted) so the *direction*
  is recorded, but the implementation work (companion PLAN — see OQ-A
  on whether that is PLAN-0012 under this ADR or PLAN-0012 directly
  under ADR-013 D1) is drafted only once Stop-event auto-dispatch is
  observed working in a real session.

This re-grounded D4 replaces take 1's "defer until PLAN-0008+ Phase 3
lands" rationale, which was invalidated by the Cowork advisory pass §1
C1: Phase 3 (PLAN-0009) is DONE at HEAD; this very draft is the
evidence. The phasing dependency that genuinely remains is
**sequencing on live signal-source readiness** (OQ-B), not on a
milestone that has already shipped.

- **Rationale:** the value proposition of MCP transport is moving
  dispatch / advisory signals between tabs without paste-relay. If the
  upstream dispatch decision cannot ground itself (classifier-blind on
  Stop), the transport ships an empty channel. Lesson #15 §7
  explicitly states the bug **does not invalidate ADR-013 D1**, so
  this is a *sequencing* dependency, not an architectural retreat —
  ADR-013's Direction-B framing is intact; the transport just needs
  the signal source live before its blast radius is worth incurring.
- **Alternative considered — defer until the second subagent +
  scheduled-task AFK loop (PLAN-0010 Phase 4) prove out demand for
  the transport:** also defensible (more conservative). *Not adopted:*
  Lesson #15 readiness is the closer, more concrete gate, and PLAN-0010
  demand can express itself through the live-session evidence the
  Lesson #15 gate already requires.
- **Alternative considered — land MCP transport in parallel with the
  Lesson #15 transcript-load fix as one PR bundle:** *Rejected:*
  couples two changes into one PR surface, contradicting the small-PR
  discipline ADR-013 itself models. Sequence them so each is
  independently reviewable and revertable.

## Consequences

### Positive

- **Removes the cross-tab paste-relay bottleneck** for the retained
  advisory and free-form flows that ADR-013 D1 / D3 protected. Cowork
  advisory passes on Code-drafted ADRs/PLANs no longer require Cray to
  paste paths between tabs; the Plan subagent stages a draft, the MCP
  transport signals Cowork, Cowork reads and posts review, signals
  complete.
- **Preserves the author≠reviewer separation ADR-013 OQ-1 protected.**
  By making the advisory flow *cheap* (no Cray paste), the separation
  is something the harness can exercise routinely rather than
  something Cray has to consciously trigger. The structural check
  ADR-012 D4.3 and ADR-013 D1 set up becomes operationally durable.
- **Composes with the autonomy primitives ADR-013 already shipped.**
  The Telegram notification (ADR-013 D5), the classifier hooks
  (ADR-013 D4), the `PreToolUse deny` commit hook (ADR-013 D2) all
  operate in the same tier (Code) that hosts the MCP servers — they
  can share state, hook into the same events, and present a coherent
  surface.
- **Keeps the repo as the source of truth** (CLAUDE.md §4). MCP is
  *signaling*, not *storage*. Artifacts still land on disk; commits
  still ride through git; the audit trail is unchanged.

### Negative

- **Adds new infrastructure surface in Code.** MCP servers, endpoint
  schemas, client libraries on the Cowork/Chat side — all new code to
  maintain. A defect in the MCP layer has broader blast radius than a
  filesystem-only handoff did. Mitigated by D4 sequencing (land after
  Lesson #15 live evidence, so the signaling shapes the transport
  carries are observed rather than guessed) and by keeping the repo as
  the durable substrate (so a transient MCP outage degrades to "use
  the filesystem + paste-relay," not data loss).
- **Cowork-side capability remains asymmetric.** K-1 / K-2 still
  apply; Cowork is a client-only participant. **And per OQ-C, even
  client-only reachability is unproven** — if the Cowork client
  executes in the sandbox VM, the loopback v1 binding (D3) cannot
  reach it.
- **Authentication is under-specified in v1** (OQ-4). Localhost-only
  binding is the v1 floor but not a complete answer; cross-tab
  identity (which client is which tab) needs a story before this can
  scale beyond the single-developer-on-one-machine case vero-lite
  currently runs.
- **Chat's role is the weakest link.** Chat has no live repo read and
  its MCP-client capability is unverified (OQ-5). If Chat cannot be an
  MCP client, D2's "Chat as restricted client" row collapses to "Chat
  unchanged — still paste-relay for free-form consultation."

### Neutral

- **Vertical-agnostic infrastructure** (ADR-006). Cross-tab transport
  is core harness tooling, not vertical-specific; it sits with the
  engine, not inside any `verticals/<name>/`.
- **Lesson #8 (K-1/K-2 workflow) preserved.** This ADR does not alter
  the K-1/K-2 facts or the operating workflow they require; it
  *layers MCP on top of* the existing filesystem substrate.
- **ADR-slot inventory.** ADR slots existing at HEAD: `0000–0010 +
  0012 + 0013`. `0011` is **reserved** for the action-approval / audit
  framework (ADR-013 §Context + OQ-2-resolved; PLAN-0009 OQ-3) — it
  stays reserved after this ADR commits. `0014` is consumed by this
  draft. The Postgres-image earmark from ADR-013 §Consequences
  (Neutral) shifts to ≥ 0015. Recorded as follow-on T5 (STATUS bump).
- **Self-contained payloads as a design guideline (softened from take
  1).** The Smoke 2 incident motivated thinking about payload shape,
  but Lesson #15 §7 explicitly states that incident does not
  invalidate ADR-013 D1. Self-contained payloads are a useful design
  guideline for the MCP endpoints (reduces dependence on cross-tab
  transcript visibility) — *not* an architectural law derived from a
  single bug. The implementation PLAN can encode it as a schema
  convention rather than as a constraint elevated into this ADR.

### Required follow-on commits (TODOs for Code — separate commits)

This ADR is a plan-drafter subagent draft (ADR-009 D2 — only Code
commits; ADR-013 D1 — subagent-authored drafts still flow through
Code's commit). None of these edits are made in this draft:

1. **T1 — Commit this ADR** to
   `docs/adr/0014-cross-tab-mcp-transport.md` at the status Cray sets
   (Proposed → Accepted on ratification of the open questions —
   minimally OQ-A, OQ-B, OQ-C must resolve before flip).
2. **T2 — Mint companion PLAN-0012** for the implementation plan
   (slot verified free at HEAD per §Context "Repo reality"). **Defer
   drafting until Lesson #15 live in-session auto-dispatch evidence is
   observed** per D4. **OQ-A may redirect this T2 entirely** — if Cray
   chooses the PLAN-under-ADR-013 path, this ADR is withdrawn and T2
   becomes "mint PLAN-0012 under ADR-013 D1 directly." Steps once
   minted: MCP server scaffolding in Code, endpoint schema specification
   (with self-contained-payload guideline per the §Consequences
   Neutral note), Cowork client onboarding (gated on OQ-C resolution),
   Chat client investigation (gated on OQ-5), authentication v1
   (localhost-only) implementation, integration tests.
3. **T3 — Annotate ADR-013 D1** with a pointer note recording that
   ADR-014 operationalizes its Phase-3 boundary + OQ-1-resolved
   advisory-drafter retention. Skip if OQ-A withdraws this ADR.
4. **T4 — Annotate ADR-012 D2** (routing guidance) with a pointer
   note recording how the two free-form venues exchange signals with
   Code without paste-relay. Skip if OQ-A withdraws this ADR.
5. **T5 — Update `docs/STATUS.md`** Recent Decisions + Active TODOs
   (record the cross-tab MCP transport direction; bump any
   downstream ADR-slot earmarks to ≥ 0015; reaffirm 0011 reserved).
6. **T6 — Update CLAUDE.md §6 4-tier table** (deferred until the
   PLAN-0012 companion lands) with an annotation referencing ADR-014
   for the cross-tab transport.

Per CLAUDE.md §1 precedence, an accepted ADR outranks CLAUDE.md and
tier instructions; T6 brings the lower-precedence file into alignment
at the right phase.

### Risks

- **MCP-as-protocol may be insufficient for the signaling shapes the
  live auto-dispatch arm actually emits.** D4's sequencing mitigates
  this — observe the shapes before building. If the gap is structural,
  this ADR is superseded; reversibility is bounded.
- **OQ-C may resolve negatively** — i.e., the Cowork MCP client may
  execute in the sandbox VM and be unable to reach a loopback socket
  on Cray's machine. In that case D2's Cowork-client row degrades to
  "client-capable in principle, unreachable in v1," and v1 ships
  serving only the Code-internal subagent surface (and Chat if OQ-5
  resolves positively). The ADR is not invalidated, but its near-term
  utility narrows substantially.
- **Single-machine assumption may not survive multi-developer or
  multi-machine futures.** OQ-4 holds the cross-machine question.
- **K-1 / K-2 may be permanent Anthropic-side gaps** (carried from
  ADR-013 §Risks). Direction here does not depend on them being fixed.
- **Chat's MCP-client capability is assumed but not verified.** OQ-5
  holds the verification question.

### Reversibility

Retractable or supersedable with bounded unwind. MCP servers and
clients are additive code under Code's `services/` or `tools/` tree
that can be deleted to return to the pre-MCP filesystem-only handoff
flow; no architectural state is migrated and the repo remains the
durable store throughout. ADR-009 D2 / ADR-013 D2 commit boundary is
preserved at the hook layer regardless of whether MCP transport is
active, so a revert never weakens the safety boundary. The companion
PLAN is the unit of unwind for the implementation work — if Lesson #15
live evidence reveals MCP is wrong, the PLAN is scrapped before code
is written. **OQ-A's "withdraw this ADR in favor of PLAN-under-ADR-013"
path is the cleanest unwind** if Cray decides the artifact type is
wrong.

## Open Questions

Cray-adjudication needed. Listed in priority order. **OQ-A, OQ-B, and
OQ-C are blocking** — must resolve before Proposed → Accepted. The
remainder (OQ-1, OQ-2, OQ-4, OQ-5) can resolve at implementation time.

### OQ-A — Artifact type: ADR-014 vs PLAN-0012-under-ADR-013 (blocking; governance)

**Question:** (a) PLAN-0009 §Out-of-Scope already names this work as
**"Phase 4 — MCP `vero-bridge` cross-surface transport"**. Should this
ADR's working name `mcp-handoff-bus` be reconciled with the existing
`vero-bridge` name? (b) PLAN-0009 OQ-3 set the precedent: *"no new
ADR; Phase 3 executes already-Accepted ADR-013 D1; mint an ADR only
if a genuinely architecture-level choice surfaces."* This ADR's own
§Amendment-scope states it *"does not amend … operationalizes ADR-013
D1."* By the PLAN-0009 OQ-3 precedent, should this work be **ADR-014
at all**, or **PLAN-0012 under ADR-013 D1** (the way Phase 2 executed
D4 with no new ADR)?

**Recommendation:** Surface for Cray; lean toward **PLAN-0012 under
ADR-013** if no genuinely architecture-level choice has surfaced. The
candidate "architecture-level" hooks in this draft are (i) the MCP-vs-
alternatives selection (D1), (ii) the role-asymmetry topology (D2),
(iii) the commit-boundary preservation (D3). Of those, (i) is a
strong tool-choice, (ii) and (iii) are operational constraints
already implied by ADR-013 D2 + ADR-009 D2. A plausible read: D1 alone
is *not* architecture-level enough to warrant a new ADR; D1 + D2 + D3
+ D4 together might be. Cray to decide. If withdrawn, T2 becomes
"mint PLAN-0012 under ADR-013 D1" and T3 / T4 annotations drop.
Reconcile name to `vero-bridge` either way.

**What makes this a Cray decision:** the ADR-vs-PLAN governance call
is judgment about whether a transport choice rises to "architecture-
level" in Cray's mental model. PLAN-0009 OQ-3 set the precedent but
explicitly left "judgment call" room. Code cannot derive the answer.

**Resolve this OQ first.** A "PLAN-0012 under ADR-013" resolution
collapses much of the rest of this draft into the PLAN-side document,
which changes how OQ-B / OQ-C / OQ-1–5 are framed. Cray should pick
ADR-vs-PLAN before any subsequent edit pass folds in OQ-B / OQ-C
answers.

**Sub-dimensions** (flagged by Cowork take-2 verification §Focus-2):

- **(a-i) Slot-0014 disposition if withdrawn.** If Cray resolves
  OQ-A as PLAN-0012, the `0014` ADR slot should be **tombstoned**
  (`docs/adr/0014-WITHDRAWN.md` placeholder or similar), not reused
  for an unrelated future ADR. ADR-013 §Context explicitly reserves
  `0011`; a withdrawn-after-draft `0014` deserves the same archeological
  treatment so a future reader sees "0013, 0014-withdrawn, 0015" and
  not a confusing gap.
- **(a-ii) `vero-bridge` earmark orphan.** PLAN-0009 §Out-of-Scope
  named *"Phase 4 — MCP `vero-bridge` cross-surface transport. Build
  only after subagents prove out,"* and originally implied
  "carry to PLAN-0010." But PLAN-0010 ended up being the
  Phase-3.5 scheduled-task autonomy loop (a different surface
  entirely). The `vero-bridge` earmark therefore floats orphaned —
  neither PLAN-0010 nor any other minted PLAN owns it. Resolving OQ-A
  (whether as ADR-014 or PLAN-0012) is the moment to **re-anchor the
  `vero-bridge` earmark**. Naming reconciliation should be explicit
  either way: this work IS the realisation of PLAN-0009's `vero-bridge`
  earmark; pick `vero-bridge` or `mcp-handoff-bus` and update the
  earmark in PLAN-0009 §Out-of-Scope (annotation style, same pattern
  as PR #56's PLAN-0011 §Out-of-Scope annotation).
- **(a-iii) OQ-A-first resolution order** (already noted above; flagged
  separately by Cowork). The other blocking OQs (B, C) and the
  non-blocking OQs (1, 2, 4, 5) all carry implicit assumptions about
  the artifact type. Resolving OQ-A first prevents wasted edit cycles
  on the others.

### OQ-B — Lesson #15 live-evidence dependency (blocking; sequencing)

**Question:** D4 above is re-grounded to defer the transport
implementation until the Stop-event auto-dispatch arm produces *live
in-session* evidence beyond the AC-5 gated smoke test. Is that the
right gate, or should the gate be stricter (e.g., "N successful
auto-dispatches in real sessions over M days") or looser (e.g.,
"PLAN-0011 archived to `done/`, which has already happened")?

**Recommendation:** **Adopt the live-evidence gate as worded in D4** —
"functional end-to-end with live in-session evidence beyond the gated
smoke test." PLAN-0011 being archived is necessary but not sufficient
(archive ≠ live exercise). N=1 successful auto-dispatch in a real
session would clear it. Cite Lesson #15 §7 to confirm the gate is
sequencing, not architectural retreat: the bug does not invalidate
ADR-013 D1; it just makes the transport's payload empty until fixed
and observed.

**What makes this a Cray decision:** "what counts as live evidence"
is a verification-rigour judgment Cray makes, not a derivable
threshold.

**Sub-dimensions** (flagged by Cowork take-2 verification §Focus-2):

- **(b-i) Fix code is shipped — gate is now purely live-evidence.**
  Per D4 above, the `_build_user_message` transcript-load fix landed
  in PR #53 (commit `8d421fc`) executing PLAN-0011. So the OQ-B gate
  has only ONE stage remaining: fresh-trigger in-session live evidence
  (AC-3 reframing, PR #53 body). Cowork take-2 verification originally
  flagged this OQ as missing a "first stage = fix code yet implemented"
  prerequisite; that prerequisite is now obsolete (fix shipped).
  Wording above already reflects the post-PR-53 reality.

### OQ-C — Cowork MCP-client execution locus (blocking; feasibility)

**Question:** D3 commits to localhost-only binding in v1. D2 commits
Cowork to a client role. Per Lesson #8 §1, the Cowork sandbox is a
**remote cloud Linux VM**, not Cray's WSL machine. A loopback MCP
socket bound on Cray's machine is **not** on the Cowork-VM's
localhost. Resolving this requires answering: **where does the Cowork
MCP client execute — desktop-proxy side (can reach Cray's loopback
via the same proxy that carries Read/Write/Glob today) or sandbox-VM
side (cannot reach the loopback at all)?**

**Recommendation:** Verify experimentally before flipping this ADR to
Accepted. Until verified, treat D3's v1 binding as **contingent**.
Three outcomes and their consequences:
- (i) **Client runs desktop-proxy side** → loopback works; v1 ships
  for Cowork as designed.
- (ii) **Client runs sandbox-VM side** → loopback unreachable; v1
  cannot serve Cowork. Either narrow v1 to Chat (gated on OQ-5) + the
  Code-internal subagent surface, or wait for an Anthropic-side
  change, or accept a tunnel/bridge workaround whose fragility this
  ADR already rejected.
- (iii) **Capability does not exist today** → defer further; treat
  the Cowork-client row of D2 as aspirational.

**What makes this a Cray decision:** the verification is a small
empirical step (try connecting a trivial MCP client from a Cowork
session); the *decision about whether to proceed v1 without it* is
Cray's risk call.

**Sub-dimensions** (flagged by Cowork take-2 verification §Focus-2):

- **(c-i) App-level MCP locus, not just transport.** The "where the
  client runs" question generalizes to **where MCP-client logic
  executes in the Anthropic Desktop architecture as a whole** — the
  same locus question applies to Chat (OQ-5) and to any other
  surface that might host clients in the future. Whatever
  experiment resolves OQ-C should produce a generalizable answer
  about Desktop's MCP-client placement, not just a Cowork-specific
  yes/no. Capture the empirical finding in a runbook or research
  note so OQ-5 + future-surface OQs can cite it.
- **(c-ii) Identity-gate interaction with OQ-4.** D3's commit-boundary
  preservation (only Code commits) relies on the composed identity
  gate (ADR-013 D2). If a future cross-machine transport path (OQ-4)
  opens, the identity gate needs to extend — a remote Code session
  presenting `CLAUDE_TIER=code` is not automatically trustworthy if
  the identity check is local-only. OQ-C's resolution feeds OQ-4:
  even at localhost-only, the question "who is on the other end of
  the loopback socket" is non-trivial once cross-process boundaries
  are involved. Resolve OQ-C's "where does the client run" before
  re-opening OQ-4's "should we extend to cross-machine."
- **(c-iii) Run the OQ-C experiment before commit if possible.**
  The experiment is cheap (one trivial MCP client connection from
  a Cowork session). If Cray + Cowork can spend the ~10 min to
  run it before this ADR commits, OQ-C transitions from "blocking
  open question" to "resolved with empirical answer recorded" —
  much stronger artifact. If not feasible, OQ-C stays blocking
  and resolves at first attempt to wire Cowork to v1.

### OQ-1 — MCP topology: one bus server vs N peer servers

**Question:** Does Code host a single bus server (working name
`mcp-handoff-bus`; or `vero-bridge` per OQ-A) that exposes all
cross-tab endpoints, or N peer servers split by responsibility?

**Recommendation:** start with **one server** for v1; factor into
peers only if operational pain emerges. Solo-dev configuration does
not justify N-process overhead upfront. *Cray decision because:*
reversible but expensive once clients are coded against it.

### OQ-2 — Cowork-side server capability: client-only forever, or revisit if K-1 ships fix

**Question:** If Anthropic ships a K-1 fix, should Cowork optionally
host secondary MCP servers, or is client-only the durable end-state?

**Recommendation:** **client-only is the durable end-state.** Hosting
servers in Cowork sits poorly with the sandbox tab's ephemerality.
*Cray decision because:* preference about topology evolution.

### OQ-4 — Transport-layer security: localhost-only forever, or cross-machine path

**Question:** Does ADR-014 commit to localhost-only as the long-term
floor, or acknowledge a future cross-machine path and reserve the
question?

**Recommendation:** **acknowledge the future path but defer.**
Localhost-only is the v1 floor; cross-machine is a future ADR's
question once vero-lite has multiple developers or machines. *Cray
decision because:* interacts with vero-lite's deployment trajectory.

### OQ-5 — Chat's MCP-client capability: verify or treat as unknown

**Question:** Verify Chat's MCP-client capability before flipping, or
accept the unknown and gate the PLAN's Chat-client step on
verification?

**Recommendation:** **accept the unknown, condition the PLAN step.**
If verification fails, Chat stays paste-relay; the rest of D2 still
ships. Pair OQ-5 verification with OQ-C — both are small empirical
steps the PLAN can bundle. *Cray decision because:* Cray may have
direct knowledge of Claude Desktop's Chat-tab capabilities that this
draft does not.

## Alternatives Considered

Alternatives 2 and 3 are also discussed inline in D1's rationale; they
are restated here for completeness with their reject reasons.

- **Alt 1 — keep paste-relay (status quo).** *Rejected:* status quo is
  the problem statement; ADR-013 explicitly deferred this to a
  follow-on. Not addressing it leaves ADR-013's design half-implemented.
- **Alt 2 — shared-filesystem handoff with polling (extend Lesson #8
  §2).** *Rejected:* filesystem is good for *substrate*, not
  *signaling*. Polling is wasteful + high-latency and doesn't compose
  with the hook layer. D1 keeps the filesystem as substrate and adds
  MCP as the signaling layer; the two are complementary.
- **Alt 3 — custom REST or WebSocket endpoints.** *Rejected:* invents
  a parallel protocol stack that MCP already provides; no first-class
  harness integration; reimplements auth, schema versioning, client
  libraries.
- **Alt 4 — single-harness (collapse Cowork/Chat into Code
  subagents).** *Rejected:* discards the author≠reviewer separation
  ADR-013 OQ-1 explicitly protected; a same-harness subagent is a weak
  independent-perspective check. ADR-013 already rejected this in
  D3 + OQ-1.

## References

- **ADR-013** (`docs/adr/0013-autonomy-axis-relocation.md`) — **the
  parent ADR.** §Context (forcing fact: hooks/subagents/MCP/defer are
  Tier-2-only); D1 (autonomy relocation + Phase-3 boundary + OQ-1
  resolution Cowork-retained-as-advisory-drafter); D2 (`PreToolUse
  deny` commit hook — **preserved here, reinforced by ADR-014 D3
  endpoint-layer refusal**); D3 (free-form venues retained — **the
  retention this ADR's transport serves**); D4 (Sonnet pause/proceed
  classifier — composes with MCP signaling); D5 (Telegram notification
  — out-of-band channel that complements MCP); §Risks "MCP bus"
  (PLAN-0008+ must carry its own ratification); §Context (ADR-slot
  0011 reservation).
- **ADR-012** (`docs/adr/0012-cowork-second-freeform-tier.md`) — D2
  routing (Cowork repo-grounded vs Chat repo-blind — **the property
  ADR-014 D2 client roles must preserve**); D3 free-form produces no
  tracked artifact (the `phase: discussion` capture path); D4.3
  author≠reviewer disclosure (the discipline this ADR's transport
  operationalizes and that the bootstrap exception below discharges
  via the Cowork advisory pass).
- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — D1
  (Cowork as Tier-1 author — **the role MCP transport serves**); D2
  (only Code commits — **preserved unchanged here; ADR-014 D3 adds
  belt-and-suspenders refusal at the MCP endpoint layer**); D3
  (K-1/K-2 workflow — the constraint that forces Cowork client-only in
  D2); D4 (C2/C3 criteria — Cray-attention copy/paste reduction is
  ADR-014's positive consequence); D5(b) (free-form discussion mode).
- **ADR-006** (`docs/adr/0006-vertical-plugin-architecture.md`) — core
  vs vertical separation (cross-tab transport = vertical-agnostic core
  infrastructure).
- **CLAUDE.md** §1 (precedence — most-recent ADR wins); §4 (memory
  architecture — **repo remains source of truth; MCP is
  complementary**); §6 (4-tier table — amended by T6); §8 (secret
  hygiene — applies to any future cross-machine auth tokens, OQ-4);
  §11 (Tier 2 operational policy — MCP servers live here).
- **Lesson #8** (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`) —
  §1 K-1/K-2 facts (remote cloud VM — the forcing constraint on D2
  Cowork-client-only **and** the source of OQ-C); §2 workflow (the
  filesystem substrate MCP layers on top of); §5 anti-patterns.
- **Lesson #15** (`docs/lessons/0015-classifier-payload-starvation-
  stop-events.md`) — **codified**, not in flight. §4 (the
  `_build_user_message` Stop-event transcript-load fix); §7 (the bug
  does not invalidate ADR-013 D1 — the basis for D4's sequencing
  framing).
- **PLAN-0009** (`docs/plans/done/0009-subagent-topology.md`) — Phase
  3 DONE; §Out-of-Scope names **Phase 4 = MCP `vero-bridge` cross-
  surface transport** (the OQ-A naming reconciliation source); OQ-3
  (the no-new-ADR precedent for executing already-Accepted ADRs that
  OQ-A invokes).
- **Cowork advisory pass on take 1** (`.claude/handoffs/session-16/
  2026-05-27-1145-cowork-adr0014-advisory-pass.md`) — the independent-
  reviewer pass discharging the author≠reviewer separation for this
  take 2; §1 C1 (Phase-3 premise correction), §1 C2 (Cowork-client
  locus → OQ-C), §2 C3 (slot inventory), §2 C4 (commit attribution),
  §3 (title convention), §4 OQ-A/B/C, §5 smaller improvements.
- **Source artifacts referenced from ADR-013:**
  - `docs/research/public/chat_harness_extension_points_analyzed.md`
    (Chat 5-point analysis ranking MCP as one of the high-leverage
    primitives)
  - `.claude/handoffs/session-10/2026-05-23-0345-cowork-harness-
    extension-points-direction-b.md` (Cowork Direction-B capture;
    §3 forcing fact)
- **Anthropic blog / docs (per ADR-013 references):** "How Claude
  Code works in large codebases" (2026-05-14); Claude Code docs
  "Automate workflows with hooks" + MCP server documentation.

## Implementation Notes

Drafted by the in-harness **`plan-drafter` subagent** running inside
Code (Tier 2) per ADR-013 D1 phased authority (**take 2** — folds the
Cowork advisory pass on take 1). The subagent operates under the
contract specified in PLAN-0009 Step 1b (frontmatter, write-path
enforcement, result reduction) and ADR-012 D4.3 (author≠reviewer
disclosure). The harness `PreToolUse deny` hook restricts the
subagent's writes to `docs/adr/` and `docs/plans/`; no other path is
writable from this draft session, by construction. Per ADR-009 D2 +
ADR-013 D2, the subagent has no commit authority — the main Code
agent reviews and commits this file plus the T1–T6 follow-ons, on
Cray's flip Proposed → Accepted.

**Author ≠ reviewer disclosure (ADR-013 OQ-1 — primary; ADR-012 D4.3 —
mechanism).** This take 3 draft (Code-side edits on take 2) is the
result of two independent-reviewer rounds:

- **Round 1** (take 1 → take 2): authored by the in-harness
  `plan-drafter` subagent under ADR-013 D1 phased authority; reviewed
  by Cowork (Tier-1b advisory) on 2026-05-27 1145 +07, recorded at
  `.claude/handoffs/session-16/2026-05-27-1145-cowork-adr0014-advisory-pass.md`.
  Author (Code plan-drafter, Tier 2) ≠ reviewer (Cowork, Tier 1b).
  Folded into take 2 by re-spawning plan-drafter with the advisory
  feedback as scoped context.
- **Round 2** (take 2 → take 3): take-2 reviewed by Cowork again on
  2026-05-27 1330 +07, recorded at
  `.claude/handoffs/session-16/2026-05-27-1330-cowork-adr0014-take2-verification.md`.
  That pass confirmed Focus-1 (C1–C4 fixes) hold + flagged 2 new issues
  (N1: take-2's stale claim about Lesson #15 fix shipment; N2: PLAN-0011
  internal contradiction header-vs-body) and Focus-2 dimension
  refinements on OQ-A/B/C + Focus-4 attribution. N1/N2 were
  reconciled at the **documentation source** in PR [#56][pr56] (docs
  reconcile — PLAN-0011 §Out-of-Scope annotation, Lesson #15 §4 update,
  STATUS frontmatter) so that this take-3 ADR's claims point at
  consistent docs. Focus-2/4 are folded into this take-3 directly.

**The relevant separation framework is ADR-013 OQ-1** (the cross-tier
author/reviewer separation that ADR-013 contemplates as "the healthy
case"). ADR-012 D4.3 (the disclosure mechanism for author/reviewer
asymmetry) is the *vehicle* this disclosure uses, but the substantive
"separation is intact" claim rests on the fact that **author (Code
plan-drafter, Tier 2) and reviewer (Cowork, Tier 1b) are in different
tiers**, which is exactly the healthy case ADR-013 OQ-1 contrasts
with self-deliberation. (Earlier drafts mis-attributed the separation
framework solely to ADR-012 D4.3; Cowork take-2 verification §Focus-4
caught this and clarified.) The independent reviewer is Cray at PR
merge — the third layer of separation in the take 1 → 2 → 3 → ratify
sequence.

**Separation: DISCHARGED — across both Cowork rounds.** The bootstrap
chicken-and-egg exception take 1 raised is discharged: the advisory
passes happened via the existing paste-relay workflow, exactly as
ADR-013's interim retention of Cowork advisory authoring anticipated.
Both Cowork handoffs (1145 + 1330) are cited above so a future reader
can trace the full author/reviewer history. Future ADRs
operationalizing ADR-014 will not need the bootstrap exception; they
will have the transport this ADR specifies (subject to D4 sequencing).

AI-assisted per project convention (noted in commit body, never as
Co-Authored-By, per CLAUDE.md §7).

[pr56]: https://github.com/CrayJThiemsert/vero-lite/pull/56
