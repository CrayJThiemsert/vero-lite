# PLAN-0012: vero-bridge — MCP transport operationalizing ADR-013 D1

**Status:** Draft
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
> drafting context); the correct mint status is `Draft`. After Cray
> ratification, Status flips to `Ready for execution`. See §Open
> Questions OQ-T2 for historical record.

## Goal

`vero-bridge` is the MCP transport that operationalizes
[ADR-013 D1](../adr/0013-autonomy-axis-relocation.md) (lines 98–127): the
execution-automation axis lives in Code (Tier 2), so the machine-to-machine
channel that lets the executing harness exchange signals with the other
collaboration surfaces must also originate there. Today every inter-tier
handoff routes through Cray as a human relay (paste a path from one tab to
another); `vero-bridge` removes that relay for the cases where a surface
can connect as an MCP client to a Code-side server. This PLAN delivers a
**v1** transport spanning **Code (Tier 2, server) ↔ Chat (Tier 1,
client)** only. The **Cowork-client is explicitly dropped from v1** and
deferred to v2 per the ratified
[OQ-C experiment outcome](../runbooks/cowork-network-locus.md) §3 (Cowork's
outbound `web_fetch` does not exit Cray's machine, so a v1 loopback bus is
unreachable from the Cowork sandbox). The PLAN does **not** implement the
transport — it is the plan for the implementation; Code executes it in
subsequent PRs (mirroring PLAN-0011's split: PR #51 minted Draft, PR #52
ratified, PR #53 shipped the code).

## Structure (parent-PLAN, single file)

This is a single-file **parent-PLAN** with two phases: **Phase 1 = v1**
(Code server + Chat client — the deliverable) and **Phase 2 = v2**
(Cowork-client tunneled rendezvous — deferred placeholder with sequencing
dependencies, not a fleshed design). A separate sub-PLAN file is **not**
spawned now because Phase 2 is intentionally a placeholder until the OQ-C
(ii-a)/(ii-b) re-test runs (§Steps Phase 2). If Step 1 (wire format) proves
large during execution, Code may spawn `docs/plans/0012-step1-wire-format.md`
as a sub-PLAN and treat this file as the parent — the same pattern
PLAN-0009 used when Step 1b became
[`docs/plans/done/0009-step1b-contract-design.md`](done/0009-step1b-contract-design.md).

## Acceptance Criteria

> Seven criteria. AC-1…AC-6 cover the v1 (Phase 1) transport surface;
> AC-7 makes the Cowork-client v1 deferral + v2 sequencing gates an
> explicit checkable item (so the deferral is visible here and in
> §Out of Scope and §Steps, not hidden). Each AC names what evidence
> proves it (PLAN-0011 §Acceptance Criteria per-AC style).

- [ ] **AC-1 — Transport contract is documented.** A written contract
  specifies the wire format (message framing), the message types
  carried, error codes, and a version field. Proven by a committed
  contract section (in this PLAN's Step 1 output or a spawned
  `0012-step1-wire-format.md`) that a reviewer can read and a parser can
  be written against, plus a schema-shaped definition (mirroring
  `tools/handoffs/_schema.py` discipline) the v1 code validates messages
  against. **Blocked on OQ-A** (transport mechanism not pinned by
  ADR-013 D1 — see §Open Questions).

- [ ] **AC-2 — Code-side server runs in the harness session lifecycle.**
  The server starts and stops bound to the Code (Tier 2) harness session
  (not a detached daemon that outlives the session). Proven by an
  end-to-end test that starts the server, observes it accept a connection,
  and confirms it is torn down at session end; plus a documented
  lifecycle note (start hook, stop hook, or in-process supervisor —
  decided under OQ-A).

- [ ] **AC-3 — Chat-side client connects and exchanges a round-trip
  echo.** A Chat-tab MCP client connects to the Code-side server and
  completes one request→response echo. Proven by a captured live
  round-trip: the Chat client sends a known payload, the Code server
  echoes a per-session token, and the Chat side reports the matching
  token within a bounded latency, logged to a named evidence path under
  `docs/research/private/`. **Conditional on OQ-B** (Chat MCP-client
  primitive availability is unverified — see §Open Questions).

- [ ] **AC-4 — Safety boundary preserved (ADR-013 D2 not weakened).**
  No transport path lets any connecting client induce a commit. The
  `pretooluse_git_deny.py` (G5) deterministic deny stays bypass-immune
  (ADR-013 D2 lines 142–164; PLAN-0009 AC-6) and is unaffected by the
  new server/client surface. Proven by re-running the G5 bypass-immune
  matrix after the transport lands (it must stay green) plus a negative
  test that a transport message requesting a git operation is refused at
  the deny layer, not merely by prompt. The server must also identify
  *which* client connected (see OQ-T3) so a non-Code client can never be
  treated as the committing identity.

- [ ] **AC-5 — Test coverage for transport parse / dispatch / error
  paths.** Unit + integration tests cover: well-formed message parse;
  malformed / truncated message rejection; unknown message-type handling;
  version-mismatch handling; and the transport-failure error contract
  (OQ-T1). Proven by `pytest` green with a per-path test mapped to each
  case, `ruff` + `mypy` clean (mirror PLAN-0011 AC-6 discipline), and a
  case-coverage matrix (happy / boundary / fail-closed / adversarial /
  concurrency) per the Cray verification-rigor directive (PLAN-0009
  §Verification).

- [ ] **AC-6 — Live evidence captured.** v1's round-trip is exercised in
  a real Code↔Chat session (not only mocked), and the verbatim evidence
  (payload, echoed token, latency, any error text) is written to a named
  file under `docs/research/private/` — the same live-vs-mock discipline
  Lesson #15 §5 mandates (a passing mock is "no evidence at all" that the
  real path works). Live evidence for the round-trip is **not gated** on
  the PLAN-0011 fresh-trigger re-run; that gate applies only to the
  Phase-2 auto-dispatch wiring (see AC-7 + Step 8).

- [ ] **AC-7 — Cowork-client v1 deferral + v2 sequencing gates are
  documented.** The PLAN records, in both §Out of Scope and §Steps
  Phase 2 (mutually referential), that (a) the Cowork-client is dropped
  from v1 per the ratified OQ-C outcome
  ([cowork-network-locus runbook](../runbooks/cowork-network-locus.md)
  §3), and (b) v2 is gated on two live-evidence dependencies — the OQ-C
  (ii-a)/(ii-b) public-endpoint re-test (runbook §4) and the PLAN-0011
  AC-3/AC-7 fresh-trigger live re-run (Lesson #15 §7). Proven by the
  presence of those cross-references in the committed file.

## Out of Scope

- ❌ **Cowork-client in v1.** Ratified out per the OQ-C experiment
  ([cowork-network-locus runbook](../runbooks/cowork-network-locus.md)
  §2–§3): Cowork's `web_fetch` reaches the public internet but does **not**
  exit Cray's machine (server logged zero inbound hits; all four local
  URLs returned no body/token), so a v1 loopback bus on Cray's machine is
  unreachable from the Cowork sandbox. The Cowork-client is **deferred to
  v2** (Phase 2, Step 6–7), conditional on the (ii-a) public-endpoint
  re-test. *(Mutual reference: §Steps Phase 2.)*

- ❌ **Any new ADR.** PLAN-0012 is minted under the already-Accepted
  ADR-013 D1, per the PLAN-0009 OQ-3 precedent
  ([done/0009-subagent-topology.md](done/0009-subagent-topology.md)
  §Resolved-decisions OQ-3: "no new ADR; mint an ADR only if a genuinely
  architecture-level choice surfaces"). If drafting or execution surfaces
  a genuinely architecture-level choice ADR-013 D1 did not anticipate, it
  is surfaced as a §Open Questions item for Cray (OQ-A is the current
  candidate) — **not** minted as a new ADR by the drafter.

- ❌ **`.claude/settings.json` schema changes** beyond what ADR-013 D2
  already commits to (the deterministic `PreToolUse deny` hook + existing
  hook wiring). If v1's server lifecycle (AC-2) needs new settings wiring,
  that is a Code-side implementation detail under OQ-A, not a schema
  redesign.

- ❌ **Transport wire-format design that requires fresh architecture-level
  choice beyond ADR-013 D1's pointers.** Message framing at the
  application level **is** in scope (Step 1). But if a transport-mechanism
  choice not pinned by ADR-013 D1 surfaces (stdio-MCP vs HTTP-loopback vs
  other), it is surfaced as **OQ-A**, not silently selected.

- ❌ **PLAN-0011 AC-3/AC-7 fresh-trigger live re-run.** Cray-driven
  separately (STATUS session-19 ledger work #4; meta-awareness
  contamination per PR #53 §AC-3 requires a fresh trigger not in any
  tracked file). It is a **sequencing dependency** for Phase 2 (Step 8),
  not work this PLAN performs.

- ❌ **v2 design.** Phase 2 (Steps 6–8) is a placeholder with sequencing
  dependencies, **not** a fleshed-out design. The (ii-a)/(ii-b)
  discrimination has not happened (runbook §4); v2 design depends on its
  result.

## Steps

> Each step is independently committable. Phase 1 = v1 deliverable;
> Phase 2 = v2 deferred placeholder. Steps gated on an Open Question name
> the gate explicitly.

### Phase 1 — v1: Code-side server ↔ Chat-side client

#### Step 1 — Wire format / message schema design

Design the transport contract: message framing, message types
(at minimum: `echo` for AC-3; room for `dispatch`/`signal` carriers that
ADR-013 D1's autonomy signals will use), error codes, and a `version`
field. Mirror the `tools/handoffs/_schema.py` discipline (stdlib-only,
dataclass-typed, fail-closed on unknown type / version mismatch). Inline
here if small; spawn `docs/plans/0012-step1-wire-format.md` as a sub-PLAN
if large (PLAN-0009 Step 1b precedent). **Gated on OQ-A** — the framing
depends on whether the transport is stdio-MCP or HTTP-loopback. Output:
the AC-1 contract + schema.

#### Step 2 — Code-side server (lifecycle bound to harness session)

Implement the server in Code (Tier 2), started and stopped with the
harness session (AC-2). The stdio-MCP-vs-HTTP-loopback mechanism and the
exact lifecycle hook are **decided under OQ-A** — do not pick silently.
Once OQ-A resolves, implement against the Step 1 contract. Preserve
ADR-013 D2: the server exposes no path to a git operation (AC-4).

#### Step 3 — Chat-side client

Implement the Chat-tab client using the `mcp__Claude_*` connector
primitives. **Conditional on OQ-B** — verify Chat actually has an
MCP-client primitive that can *initiate* a connection before committing
this step (Lesson #8 documents only the Cowork-side primitives; Chat's
client capability is unverified). If OQ-B resolves that Chat lacks an
initiating primitive, surface to Cray before proceeding (do not force a
workaround).

#### Step 4 — Round-trip echo + live evidence capture

Wire Step 2 + Step 3 together: Chat client sends a payload, Code server
echoes a per-session token, Chat reports the match (AC-3). Capture the
live round-trip (payload, token, latency, any error text) to a named file
under `docs/research/private/` (AC-6). Establish the transport-failure
error contract here in practice (OQ-T1).

#### Step 5 — Tests + lint clean

Unit + integration tests for parse / dispatch / error paths (AC-5):
well-formed parse, malformed/truncated rejection, unknown-type, version
mismatch, transport-failure error contract. Add the G5 re-run +
git-over-transport negative test (AC-4). `pytest` + `ruff` + `mypy` clean
(PLAN-0011 AC-6 discipline). Attach the case-coverage matrix
(happy / boundary / fail-closed / adversarial / concurrency) with every
row mapped to a test and any uncovered case named as residual risk.

### Phase 2 — v2: Cowork-client tunneled rendezvous (DEFERRED — placeholder)

> **Deferred per the ratified OQ-C outcome** — v1 drops the Cowork-client
> ([cowork-network-locus runbook](../runbooks/cowork-network-locus.md)
> §3; *mutual reference: §Out of Scope*). Phase 2 is a placeholder with
> sequencing dependencies, not a design. v2 design depends on the
> (ii-a)/(ii-b) result that has not been measured yet (runbook §4).

#### Step 6 — OQ-C (ii-a)/(ii-b) discriminating re-test

Re-run the OQ-C protocol with URL D set to a genuinely public endpoint
(the prior run used the RFC-1918 WSL2 vNIC `172.22.59.116`, which cannot
discriminate (ii-a) public-IP-reachable from (ii-b) no-inbound-path —
runbook §4). Options + tradeoffs to be chosen at execution: ngrok or
cloudflared tunnel (~15 min, lower attack surface) vs Cray's WAN IP +
router port-forward (~5 min, higher attack surface). Output: a runbook §4
update resolving (ii-a) vs (ii-b).

#### Step 7 — Cowork-client implementation (conditional on Step 6)

If Step 6 resolves **(ii-a)** (public endpoint reachable), implement the
Cowork-client against a tunneled rendezvous; if **(ii-b)** (no inbound
path), fall back to "wait for Anthropic to ship a sandbox-side MCP
transport client" (runbook §4). Note the runbook §3 secondary fact:
`web_fetch` is lossy (body-only, no status/headers), so prefer a richer
outbound primitive for any Cowork transport built in v2.

#### Step 8 — PLAN-0011 fresh-trigger live re-run sequencing gate

> **Explicit dependency line (Lesson #15 §7).** PLAN-0011 AC-3/AC-7
> fresh-trigger live re-run (Cray-driven; STATUS session-19 work #4) is a
> **sequencing gate** for any Phase-2 step that wires the transport to
> carry live autonomy *dispatch* signals. The Stop-event auto-dispatch arm
> is the headline payload `vero-bridge` would carry; until that arm is
> proven live with a fresh trigger (not the contaminated `scenario3`/
> `scenario5` triggers), wiring v2 to carry it is premature. This is **not**
> a blocker for minting PLAN-0012 or for Phase 1 v1; it **is** a documented
> dependency before Phase 2 live-wiring.

## Verification

Maps 1:1 to AC-1…AC-7 (per-AC inline, focused single-file style):

- **AC-1** — contract + schema committed and reviewable; a parser can be
  written against it. (Gate: OQ-A resolved.)
- **AC-2** — start→accept→teardown test green; lifecycle note documented.
- **AC-3** — captured live round-trip with matching token within bounded
  latency, evidence path recorded. (Gate: OQ-B resolved.)
- **AC-4** — G5 bypass-immune matrix re-run stays green; negative test
  proves a git-over-transport request is denied at the deny layer; server
  identifies the connecting client (OQ-T3).
- **AC-5** — `pytest` green with a test per parse/dispatch/error path;
  `ruff` + `mypy` clean; case-coverage matrix attached.
- **AC-6** — live (not mocked) round-trip evidence file present
  (Lesson #15 §5 live-vs-mock discipline).
- **AC-7** — Cowork-client deferral + v2 gates cross-referenced in
  §Out of Scope and §Steps Phase 2.

**Verification-rigor (Cray directive, PLAN-0009 §Verification).**
`vero-bridge` is autonomy-adjacent infrastructure; a green suite is not
sufficient evidence of correctness. Each v1 component ships a
case-coverage matrix (happy / boundary / fail-closed / adversarial /
concurrency), every row maps to a test, uncovered cases are named as
residual risk, and sign-off states confidence explicitly — not "tests
pass."

## Open Questions

> *PLAN-0012-local labels.* OQ-A/OQ-B below are local to this PLAN and are
> **distinct** from the project-historical "OQ-A" (the ADR-vs-PLAN
> governance question, resolved 2026-05-27) and from the runbook's "OQ-C"
> (the network-locus experiment). The third transport OQ is named **OQ-T1**
> (not "OQ-C") to avoid collision with the runbook, per the authoring
> dispatch. Each OQ is a decision the reader must make.

- **OQ-A — Code-side transport mechanism.** ADR-013 D1 places MCP
  transport in Code (Tier 2) but does **not** pin *how* (stdio-MCP vs
  HTTP-loopback vs other); the cowork-network-locus runbook addresses only
  Cowork's egress, not the Code↔Chat mechanism. *Options:* (1) stdio-MCP —
  native MCP framing, simplest lifecycle binding to the harness process;
  (2) HTTP-loopback — easier multi-client fan-out (Code server, multiple
  tab clients) but adds a bound port + identity surface; (3) other (named
  pipe, Unix socket). *Recommendation (Cray/Code adjudicates):* stdio-MCP
  for v1 (Code↔Chat, two parties, simplest lifecycle), revisit for v2
  multi-client. **This determines Step 1 framing + Step 2; do not select
  silently.**

- **OQ-B — Chat-side MCP-client primitive availability.** Does the Chat
  tab actually have a `mcp__*` connector primitive that can *initiate* a
  client connection to a Code-side server? Lesson #8 documents only the
  Cowork-side primitives; Chat's initiating capability is **unverified**.
  *Decision needed:* verify (a trivial Chat-tab connection probe, like the
  OQ-C experiment did for Cowork) before committing Step 3. If Chat lacks
  an initiating primitive, v1's client side needs rethinking before any
  code lands.

- **OQ-T1 — Transport-failure error contract.** What is the defined
  behavior on connection drop, timeout, malformed frame, and
  version-mismatch? *Decision needed:* fail-closed (drop + log + no retry)
  vs bounded-retry vs surface-to-Cray; and whether a transport failure
  must never silently degrade a safety boundary (it must not — ADR-013 D2
  is deterministic regardless). Pin this before Step 4/Step 5 so the error
  tests (AC-5) assert against a defined contract, not ad-hoc behavior.

- **OQ-T2 — PLAN status vocabulary (`Proposed` vs `Draft`). RESOLVED at
  commit (Code, this PR).** The authoring dispatch said `Status: Proposed`;
  the PLAN template + PLAN-0009 OQ-4 say PLANs mint as `Draft`. Cowork
  authored with `Proposed` (per the explicit dispatch instruction) and
  surfaced this as an OQ; Code reconciled to `Draft` at commit per
  Cowork's recommendation. The dispatch's `Proposed` was a wording error
  (ADR-vocabulary leak from the withdrawn ADR-014 drafting context). The
  header flag has been rewritten to reflect the reconciliation. **No
  further decision needed.** Preserved here for historical record of the
  reconciliation.

- **OQ-T3 — Per-client identity / authentication.** When more than one
  tab can connect (v2, or even v1 if HTTP-loopback under OQ-A), how does
  the Code server distinguish which client is Cowork vs Chat vs a rogue
  connector, and how does that interact with the ADR-013 OQ-3
  `session != Code` commit-deny identity signal (delegated to Code,
  resolved in PLAN-0009 Step 1b)? *Decision needed:* the identity
  mechanism for transport clients, and confirmation it cannot be spoofed
  into the committing identity (AC-4). This was first surfaced as the
  per-tab-identity concern in the ADR-0014 take-2 Cowork advisory pass
  (`.claude/handoffs/session-16/2026-05-27-1330-cowork-adr0014-take2-verification.md`
  Focus-2 OQ-C addition (b)).

## Implementation Notes

Drafted by Cowork in Tier-1 (governance authoring) mode under the interim
ADR-009 D1 process, retained as the advisory governance drafter per
ADR-013 OQ-1 (lines 119–127). Cowork has no commit authority (ADR-009 D2;
ADR-013 D2 deterministic `pretooluse_git_deny.py`); Code reviews and
commits this file. AI-assisted per project convention (commit body, never
as `Co-Authored-By`, CLAUDE.md §7).

**Author≠reviewer disclosure (ADR-012 D4.3 / ADR-013 OQ-1).** This PLAN
was authored from a Code-authored dispatch
(`.claude/handoffs/session-19/2026-05-28-0930-code-cowork-plan0012-vero-bridge-dispatch.md`),
so the drafter (Cowork) is distinct from the outline's originator
(Code/Cray) — the independent-tier separation is **intact** for the
PLAN's structure, as in PLAN-0009. **One partial-overlap caveat,
disclosed:** the transport *substance* was previously deliberated in
Cowork's own Tier-1b advisory passes on the withdrawn ADR-014
(`2026-05-27-1145-...advisory-pass.md` and `2026-05-27-1330-...take2-verification.md`),
where Cowork raised the Cowork-client locus question (→ OQ-C experiment),
the ADR-vs-PLAN governance question, and the per-tab-identity concern
(→ OQ-T3). Those Cowork contributions now inform PLAN-0012, so the
independent-deliberation check on *those specific framings* is partially
reduced. Code's review (ADR-009 D3 step 6) + Cray's ratification are the
remaining independent checks.

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

**Non-commit reminder (ADR-009 D2 / ADR-013 D2 — load-bearing).** This is
a Cowork draft. Cowork does not commit; only Code commits, enforced
deterministically by `pretooluse_git_deny.py` (bypass-immune even to
`bypassPermissions`). Code applies the file write + commit on the
appropriate branch after review.
