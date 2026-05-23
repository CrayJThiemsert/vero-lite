# ADR-013: Autonomy Axis Relocation — Direction B Ratification

**Status:** Accepted
**Date:** 2026-05-23
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-009 (Cowork as Tier-1 dispatch author — **this ADR amends its D1**), ADR-012 (Cowork second free-form tier — **this ADR extends it**), ADR-006 (vertical plugin architecture — 4-tier context; autonomy work is vertical-agnostic core infrastructure), CLAUDE.md §6 (4-tier table — amended by T-follow-ons), §8 (secret hygiene), §11 (Tier 2 operational policy), Lesson #8 (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`, K-1/K-2 workflow). Source artifacts: `docs/research/public/chat_harness_extension_points_analyzed.md` (Chat 5-point analysis), `.claude/handoffs/session-10/2026-05-23-0345-cowork-harness-extension-points-direction-b.md` (Cowork Direction-B capture), `.claude/handoffs/session-10/2026-05-23-1245-chat-harness-autonomy-dispatch.md` (this ADR's authoring dispatch).

> **Ratification status.** Cray ratified **Direction B** in free-form
> (captured in the Cowork direction-b handoff §2, 2026-05-23) and
> adjudicated the five open questions E.1–E.5 (dispatch §2). This ADR
> **codifies decisions already taken** — it is not a re-litigation of
> whether to pursue Direction B. Status flipped Proposed → **Accepted**
> by Code per Cray's chat-tier dispatch adjudication (Chat dispatch §2
> item 1, 2026-05-23) and committed in the T1 commit of the
> `feat/plan0007-harness-autonomy-phase1` branch (CLAUDE.md §6 Decision
> Flow; ADR-009 D2 — Cowork drafted Proposed, Code applies the
> ratification edit + commits).

> **Amendment scope.** This ADR **amends ADR-009 D1** (relocates the
> autonomy/execution axis from the merged-Cowork authoring tier into Code
> + subagents; Cowork/Chat shift toward advisory). It **preserves
> ADR-009 D2** (only Code commits) and **reinforces it** with a
> deterministic hook (D2 below). It leaves **ADR-009 D3** (K-1/K-2
> workflow) and **D4** (C2/C3 criteria) unchanged. It **extends ADR-012**
> (free-form venues are retained, not revoked — D3 below). On conflict,
> "most recent accepted ADR wins" (CLAUDE.md §1) applies once this ADR is
> accepted.

## Context

### The bottleneck this ADR addresses

The vero-lite 4-tier model (CLAUDE.md §6) routes every inter-tier handoff
through Cray as a **human relay**: Code finishes → Cray reads → Cray
pastes to Chat/Cowork → next dispatch authored → Cray reads → Cray pastes
to Code → execute. The latency of the whole pipeline equals "Cray is at
the keyboard." When Cray is away, everything stops. The goal Cray set in
the free-form session that produced the Direction-B capture (direction-b
§1) is **semi-autonomous operation**: agents hand work to each other and
proceed when one path is clearly best, **pausing for Cray only at genuine
judgment gates**.

### Why the autonomy axis cannot be distributed across the three UI tabs

Two prior artifacts analyzed Anthropic's five harness extension points
(CLAUDE.md / hooks / skills / plugins / MCP, plus subagents) against this
goal:

- The Chat analysis (`chat_harness_extension_points_analyzed.md`) ranked
  hooks + subagents highest-leverage and produced an 8-row ROI table.
- The Cowork Direction-B capture added the **forcing fact** (direction-b
  §3): all four autonomy primitives — **hooks, subagents, MCP servers,
  and the headless / Agent-SDK `defer` resume** — execute **only inside
  Claude Code (Tier 2)**. Cowork and Chat are sandboxed desktop surfaces
  that cannot run hooks or bash (K-1 UNC-bash refusal + K-2 `.claude/`
  write block, both re-confirmed live this session). A semi-autonomous
  engine therefore cannot be spread across the three UI tabs; it must
  live where the harness runs.

### Repo reality (verified at HEAD 68053fe this session)

- `.claude/settings.json` and `.claude/hooks/` **do not exist** — the
  hook / plugin / MCP layers are at zero. The autonomy work is
  greenfield, not a retrofit (direction-b §3).
- Several tier-scope rules are currently enforced only by **prose the
  model must remember** (e.g. ADR-009 D2 "only Code commits"; Cowork
  must-not-write `services/**`). A `PreToolUse deny` hook makes them
  deterministic and **bypass-immune even to `bypassPermissions`**
  (direction-b §4.1).
- ADR slots: 0000–0010 + 0012 exist; **0011 is reserved** for the
  action-approval / audit framework (STATUS Active TODOs); **0013 is
  free** (this ADR). PLAN slots: 0004 active, 0003/0005/0006 in `done/`;
  **0007 is free** (companion PLAN). `.claude/autonomy-triggers.md` does
  not exist (greenfield).

### The decision Cray made

Cowork presented **Direction A** (augment the existing 4-tier topology in
place) versus **Direction B** (relocate the autonomy axis into Code +
subagents; Cowork/Chat become advisory) as a surface item per Tier-1 rule
#8. **Cray chose Direction B** (direction-b §2) — an explicit Cray
decision, not a Cowork recommendation. Cray then adjudicated five open
questions (dispatch §2):

| # | Decision | Source |
|---|----------|--------|
| E.1 | Harness-autonomy work slots **before** partner-trial-readiness | Chat synthesis |
| E.2 | Telegram token rotated → new bot `@vero_tg_bot` (bot ID `8492382723`); chat_id `5247477693`; curl smoke test PASS (`{"ok":true}`) 2026-05-23T12:39+07:00 | Cray confirmed |
| E.3 | Phase 1 scope = items #1–#5 (notification + D2 enforcement + handoff-validator hook) — not notification alone | Cray E.3 |
| E.4 | **New trigger:** pause + Telegram alert when an agent loops > 6 rounds on the same problem | Cray E.4 |
| E.5 | Pause/proceed classifier model = **Sonnet** (accuracy over cost) | Cray E.5 |

## Decision

This ADR encodes five decisions (D1–D5). Each carries a rationale and the
alternative considered and rejected.

### D1: The autonomy / execution axis relocates to Code (Tier 2) + subagents

The semi-autonomous "engine" — hooks, subagents, MCP transport, and the
`defer` headless resume primitive — lives **in Claude Code (Tier 2)**,
the only tier that can run it. Cowork (Tier 0 / 1 / 1b) and Chat (Tier 1)
**shift toward an advisory / second-perspective role**: consulted when
Cray wants a viewpoint from outside the executing harness, rather than
serving as the primary authoring tier for execution-driving artifacts.

This **amends ADR-009 D1**, which made the merged-Cowork workspace the
primary Tier-1 dispatch/ADR/PLAN author. Under D1 here, the
*execution-automation* responsibility moves to Code + subagents
(direction-b §6 item 3: a read-only Explore subagent for research, a Plan
subagent for ADR/PLAN drafting, the main agent edits/commits).

**The relocation is phased, not instantaneous.** Until the subagent
topology lands (PLAN-0008+, Phase 3), Cowork **retains interim governance
authoring** — this very ADR and its companion PLAN-0007 are Cowork-authored
under the unchanged ADR-009 D1 process precisely because the relocation
has not yet executed.

**End-state (OQ-1, Cray-adjudicated 2026-05-23): Cowork is retained as the
advisory drafter of governance artifacts even after Phase 3.** The Plan
subagent inside Code may draft ADRs/PLANs, but Cowork keeps a
drafting/review role on governance so that an author≠reviewer separation
(which a single-harness subagent cannot supply for its own output) is
preserved. Cowork/Chat shift to advisory for *execution-automation*
authoring (the autonomy engine itself), **not** to zero governance
involvement. This makes the follow-on instruction edits an *annotation*,
not a deprecation (T4). See Open Questions → OQ-1.

- **Rationale:** the forcing fact (Context) makes this not a preference
  but a constraint — autonomy primitives are Tier-2-only. Locating the
  engine where it can run, and demoting the sandboxed tabs to advisory,
  is the only topology that delivers Cray's semi-autonomy goal without
  fighting the K-1/K-2 architecture. Direction B "accepts this rather
  than fighting it" (direction-b §3).
- **Alternative considered — Direction A (augment the 4-tier topology in
  place):** keep Cowork/Chat as primary authors and bolt automation onto
  the relay. *Rejected by Cray:* the relay's automation hooks still can't
  run in the sandboxed tabs, so Direction A leaves the human-relay
  bottleneck structurally intact — it automates around Cray without
  removing Cray from the critical path.

### D2: Preserve the "only Code commits" fail-safe — and enforce it deterministically

ADR-009 D2 ("only Code commits") is **retained unchanged as the standing
fail-safe** and is **reinforced**: it moves from prose-only enforcement to
a deterministic **`PreToolUse deny` hook** that blocks `git
commit`/`push`/`merge` from any non-Code session identity. Hook-layer
`deny` is **bypass-immune even to `bypassPermissions`** (direction-b
§4.1), so the boundary survives autonomous "proceed" execution.

- **Rationale:** Direction B increases autonomy, which raises the cost of
  any silent boundary breach. Encoding the most safety-critical rule
  (commit authority) as a deterministic hook rather than remembered prose
  is the belt-and-suspenders the increased autonomy warrants (direction-b
  §4). It also closes the standing risk that a future model "forgets" a
  prose rule (the article's "instructions written for your current model
  can work against a future one" warning).
- **Alternative considered — keep D2 as prose-only + classifier-gated:**
  rely on the Sonnet pause/proceed classifier (D4) alone to refuse
  commits from non-Code sessions. *Rejected:* a prompt-based classifier is
  probabilistic and can be talked around; the commit fail-safe is exactly
  the rule that must be deterministic. The classifier registry keeps
  commit/push as a belt-and-suspenders trigger (D4 registry), but the
  hook `deny` is the load-bearing guarantee.

### D3: Free-form venues (ADR-012) are retained — Direction B changes *who authors*, not *where ideas are explored*

ADR-012's two free-form venues stand: **Cowork Tier-1b** (repo-grounded
discussion / thinking-partner / informal code review) and **Chat**
(repo-blind blue-sky). Direction B does **not** revoke ADR-012. The
advisory shift in D1 is consistent with — indeed amplifies — the free-form
role: as Cowork/Chat vacate primary execution-authoring, their
second-perspective / sounding-board value (which the autonomy engine in
Code cannot self-supply) becomes their *primary* contribution.

- **Rationale:** the two ADR-012 trials never tested free-form against
  failure; D1 relocates the *authoring* axis (where Cowork was shown to
  add value over Chat) and *preserves* the exploration axis. Collapsing
  both would discard the independent-perspective check that an autonomous
  single-harness engine most needs. This **extends ADR-012** rather than
  superseding it.
- **Alternative considered — fold free-form into Code subagents too
  (full single-harness):** let a Code "devil's-advocate" subagent supply
  the second perspective and retire the Cowork/Chat free-form venues.
  *Rejected:* a subagent inside the same harness shares the harness's
  framing and context, so it is a weak substitute for a genuinely
  separate tier's perspective; ADR-012 D5 R-FF4 already anticipates
  routing interactive work to a separate venue. Retain the external
  venues.

### D4: Pause/proceed classifier = Sonnet, on `Stop` + `PreToolUse` hooks; criteria registry at `.claude/autonomy-triggers.md`

The hard problem — classifying *clearly-best (proceed)* vs *needs-Cray
(pause)* — is solved by a **prompt-based hook running Sonnet** (per Cray
E.5) on the `Stop` (continuation loop) and `PreToolUse` (proceed/pause
gate) events. The decision criteria live in a **canonical,
machine-readable registry at `.claude/autonomy-triggers.md`**, so the
prompt reads one source of truth rather than embedding criteria in
settings or scattering them across CLAUDE.md.

- **Rationale (model = Sonnet):** Cray adjudicated accuracy over cost
  (E.5). The classifier gates real autonomous execution including the
  approach to the commit boundary; a misclassification that proceeds past
  a judgment gate is more expensive than the marginal token cost of
  Sonnet over Haiku. (The Chat analysis had sketched Haiku as the default;
  Cray overrode to Sonnet — recorded as the rationale for the deviation.)
- **Rationale (registry location):** a single machine-readable file lets
  the hook prompt, future skills, and human review share one list; it
  sits under `.claude/` with the rest of the harness config. Exact file
  shape is PLAN-0007's to specify; Cowork proposes the location and Code
  validates fit (PLAN-0007 §Trigger registry).
- **Alternative considered — embed criteria inline in
  `.claude/settings.json` hook prompts:** *Rejected:* duplicates the list
  across the `Stop` and `PreToolUse` prompts and drifts; a single
  referenced registry is DRY and reviewable. (`settings.json` still
  *references* the registry; it does not inline it.)

### D5: Notification channel = Telegram bot `@vero_tg_bot` via env-var token

The out-of-band alert that reaches Cray when AFK is a **Telegram bot
(`@vero_tg_bot`)**, invoked from a hook via an **environment-variable
token** (`$TELEGRAM_BOT_TOKEN`, `$TELEGRAM_CHAT_ID`) — never a committed
secret (CLAUDE.md §8). Per Cray E.2 the token was rotated to the new bot
(ID `8492382723`; chat_id `5247477693`) and smoke-tested PASS
(`{"ok":true}`, 2026-05-23T12:39+07:00). The `Notification` hook fires on
`permission_prompt` / `idle_prompt` matchers.

- **Rationale:** Telegram is reachable on Cray's phone away from the desk,
  has a trivial `curl` bot API, and needs no extra infrastructure. The
  env-var indirection keeps the token out of the public repo (CLAUDE.md §8
  "NEVER commit tokens"), satisfying the secret-hygiene constraint while
  the rotated token + PASS smoke test confirm the channel is live.
- **Alternative considered — Windows desktop toast notification:**
  *Rejected as the primary channel:* a desktop toast does not reach Cray
  when away from the machine, which is the exact scenario the
  notification exists for. (A desktop toast may be added later as a
  secondary local channel; it is out of Phase 1 scope.)

## Consequences

### Positive

- **Removes the human-relay bottleneck by construction** for the
  clearly-best path: the `Stop` continuation loop + auto-handoff let Code
  proceed without a Cray paste, and the `Notification` hook reaches Cray
  only at genuine gates.
- **The most safety-critical boundary becomes deterministic** (D2 hook):
  "only Code commits" no longer depends on a model remembering prose, and
  is immune to `bypassPermissions`.
- **Retires the K-1 mental-validation workaround** for any handoff Code
  touches: moving `validate_handoff.py` into a Code-side hook (PLAN-0007
  item #5) validates frontmatter deterministically in the one tier that
  can run it.
- **Preserves the independent-perspective check** (D3): the external
  free-form venues survive, which an autonomous single-harness engine
  cannot self-supply.

### Negative

- **Concentrates capability and risk in Code.** As autonomy centralizes
  in Tier 2, a defect in the hook layer has broader blast radius than a
  prose mistake did. Mitigated by phasing (PLAN-0007 Phase 1 deliberately
  excludes the `Stop` continuation loop and the classifier — items
  deferred to PLAN-0008+) and by D2's deterministic commit fail-safe.
- **Cowork/Chat advisory demotion is under-specified at the end-state.**
  D1 is explicitly phased; *when* Cowork stops authoring governance (once
  the Plan subagent exists) is unresolved (OQ-1). Until resolved, the
  current ADR-009 D1 authoring process continues, which is mildly
  incoherent with the stated direction.
- **New external dependency (Telegram) + an env-var contract.** A dev
  session without the env vars set must degrade gracefully (PLAN-0007
  item #2 no-op requirement); a misconfigured token silently drops
  alerts.

### Neutral

- **Vertical-agnostic infrastructure.** The autonomy layer is core
  harness tooling, not vertical-specific (ADR-006 patterns: it sits with
  the engine, not inside any `verticals/<name>/`). It applies uniformly
  across energy / supply_chain / future verticals.
- **Lesson #8 (K-1/K-2 workflow) retained.** ADR-013 does not alter the
  Cowork operating workflow; it routes *around* K-1/K-2 by relocating
  hook-dependent work to Code, where K-1/K-2 do not apply. The Cowork
  workflow stands for as long as Cowork authors anything.
- **ADR-number earmark interaction (Cray-confirmed 2026-05-23).** STATUS
  Active TODOs loosely earmarked "≥ ADR-013" as the floor for the
  custom-Postgres-image ADR (PLAN-002). Consuming 0013 here shifts that
  floor to **≥ 0014**; Cray confirmed the shift. Recorded as follow-on T6
  (STATUS bump).

### Required follow-on commits (TODOs for Code — separate commits)

This ADR is a Cowork draft (ADR-009 D2 — only Code commits). None of these
edits are made in this draft:

1. **T1 — Commit this ADR** to `docs/adr/0013-autonomy-axis-relocation.md`
   at the status Cray sets (Proposed → Accepted on ratification).
2. **T2 — Commit companion PLAN-0007**
   (`docs/plans/0007-harness-autonomy-layer-phase-1.md`) after ADR-013 is
   accepted (sequencing gate, dispatch §6).
3. **T3 — Amend CLAUDE.md §6 4-tier table:** annotate the autonomy-axis
   relocation (Code + subagents own execution automation; Cowork/Chat
   advisory-shifted), referencing ADR-013.
4. **T4 — Amend `docs/conventions/cowork_tab_instructions.md` and
   `chat_tab_instructions.md`** to **annotate** the advisory shift (OQ-1
   resolved 2026-05-23: Cowork retained as advisory governance drafter, not
   deprecated). Defer until the Phase-3 boundary so instructions are not
   churned mid-transition.
5. **T5 — Add pointer notes** to ADR-009 D1 (amended by ADR-013) and
   ADR-012 (extended by ADR-013), mirroring the ADR-009 T7 / ADR-012 T4
   pointer pattern.
6. **T6 — Update `docs/STATUS.md`** Recent Decisions + Active TODOs (record
   the topology amendment; bump the Postgres-image ADR earmark to ≥ 0014).

Per CLAUDE.md §1 precedence, an accepted ADR outranks CLAUDE.md and tier
instructions; T3–T4 bring the lower-precedence files into alignment. Per
Lesson #5 §1, the CLAUDE.md edit (T3) is constitutional and needs the
restart-bridge sequence.

### Risks

- **K-1 / K-2 may be permanent Anthropic-side gaps.** Direction B does not
  depend on them being fixed — it relocates hook work to Code where they
  do not apply — so this risk is *reduced* relative to ADR-009, not
  increased.
- **Classifier misjudgment.** A Sonnet pause/proceed hook can still
  proceed past a gate it should have paused on. Mitigated by: the D2
  deterministic commit hook (the worst case — an unwanted commit — is
  hard-blocked regardless of the classifier), the always-pause registry
  (D4), and Phase 1 deliberately *not* shipping the continuation loop yet.
- **Agent-based hooks are experimental** (Anthropic flag, direction-b
  §7): prefer command/prompt hooks for anything load-bearing in Phase 1.
- **Scope creep past the ratified direction.** This ADR codifies E.1–E.5
  only; it does not pre-authorize Phase 2–4. PLAN-0008+ must carry its own
  ratification for the continuation loop, stateful loop-detection,
  subagent topology, and MCP bus.

### Reversibility

Retractable or supersedable with bounded unwind. The conversational/advisory
shift (D1) and the free-form retention (D3) cost only instruction-file
reversals. The hooks (D2, D4, D5) are additive `.claude/` config that can
be deleted to return to the pre-autonomy relay; no architectural state is
migrated. The commit fail-safe (D2) is *strengthened* either way, so a
revert never weakens the safety boundary.

## Open Questions (resolved — Cray-adjudicated 2026-05-23)

- **OQ-1 — End-state of Cowork/Chat authoring. RESOLVED:** Cowork is
  **retained as the advisory drafter** of governance artifacts after Phase
  3 (not removed from governance). The Plan subagent inside Code may draft,
  but Cowork keeps a draft/review role to preserve the author≠reviewer
  separation a single-harness subagent cannot supply. Consequence: follow-on
  T4 **annotates** (does not deprecate) the Cowork/Chat instruction files,
  and is still deferred to the Phase-3 boundary to avoid mid-transition
  churn. Folded into D1 above.
- **OQ-2 — ADR-011 vs 0013 ordering. RESOLVED:** Cray confirmed the
  intentional non-sequential mint is acceptable — it is a labeling concern
  only, with no impact on the work itself (precedent: ADR-012 minted before
  the reserved 0011). 0011 stays reserved for the audit framework; 0013 is
  this ADR.
- **OQ-3 (PLAN-0007 Step 4) — `PreToolUse deny` session-identity signal.
  DELEGATED TO CODE:** Cray asked Code to analyze and decide the mechanism
  by which the commit-boundary hook determines "session != Code" (env
  marker vs settings-scope vs other). Tracked in PLAN-0007 Step 4 + Notes.

## Alternatives Considered

### Alternative 1: Direction A — augment the existing 4-tier topology in place

- **Pros:** no topology change; keeps the proven ADR-009 authoring split;
  smaller governance surface.
- **Cons:** the automation hooks cannot run in the sandboxed Cowork/Chat
  tabs (K-1/K-2), so the human-relay bottleneck stays structurally intact;
  Direction A automates *around* Cray without removing Cray from the
  critical path.
- **Why rejected:** Cray selected Direction B (direction-b §2). Direction
  A does not deliver the semi-autonomy goal given the forcing fact.

### Alternative 2: Single-harness — fold free-form into Code subagents too

- **Pros:** maximal consolidation; one place to reason about; no cross-tab
  signaling at all.
- **Cons:** a subagent inside the executing harness shares its framing and
  context, making it a weak independent-perspective check; discards the
  external-venue value ADR-012 established.
- **Why rejected:** D3 retains the external free-form venues precisely
  because an autonomous engine most needs a perspective it cannot
  self-supply.

### Alternative 3: Status quo — no autonomy layer (keep the pure human relay)

- **Pros:** zero new config; zero new failure surface; Cray fully in the
  loop on every step.
- **Cons:** the bottleneck Cray named (everything stops when AFK) persists
  indefinitely; the lesson-capture, handoff-validation, and commit-boundary
  rules stay prose-only.
- **Why rejected:** Cray's explicit goal is semi-autonomy; the status quo
  is the problem statement, not a candidate solution.

## References

- **Source artifacts:**
  - `docs/research/public/chat_harness_extension_points_analyzed.md`
    (Chat 5-point analysis + 8-row ROI table)
  - `.claude/handoffs/session-10/2026-05-23-0345-cowork-harness-extension-points-direction-b.md`
    (Cowork Direction-B capture — forcing fact §3, 4 technical specifics
    §4, pause/proceed sketch §5, Code asks §6)
  - `.claude/handoffs/session-10/2026-05-23-1245-chat-harness-autonomy-dispatch.md`
    (this ADR's authoring dispatch — E.1–E.5 §2, ADR scope §3)
- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — D1
  (**amended here**), D2 (**preserved + reinforced here**), D3 (unchanged),
  D4 (unchanged)
- **ADR-012** (`docs/adr/0012-cowork-second-freeform-tier.md`) — free-form
  venues (**extended here**, D3)
- **ADR-006** (`docs/adr/0006-vertical-plugin-architecture.md`) — core vs
  vertical separation (autonomy = core infrastructure)
- **CLAUDE.md** §6 (4-tier table — amended by T3), §8 (secret hygiene —
  Telegram env-var token), §11 (Tier 2 operational policy), §1 (precedence)
- **Lesson #8** (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`) —
  K-1/K-2 workflow (routed around, not altered)
- **Anthropic blog:** "How Claude Code works in large codebases"
  (2026-05-14); Claude Code docs "Automate workflows with hooks"
- `tools/handoffs/_schema.py` — handoff schema (the validator PLAN-0007
  item #5 migrates into a hook)

## Implementation Notes

Drafted by Cowork in Tier-1 (governance authoring) mode under the
unchanged ADR-009 D1 process (the relocation D1 mandates has not yet
executed). Cowork has no commit authority (ADR-009 D2); Code reviews and
commits this file plus the T1–T6 follow-ons. Per K-1, Cowork could not run
`validate_handoff.py`; the companion closeout records the
mental-validation substitute and flags the gap. AI-assisted per project
convention (noted in commit body, never as Co-Authored-By, per CLAUDE.md §7).

**Author≠reviewer disclosure (ADR-012 D4.3).** The substance of this ADR
was deliberated in Cowork's own Tier-1b free-form session — the
Direction-B capture (`2026-05-23-0345-cowork-...`) authored by Cowork, plus
Cray's free-form adjudication. The same tier (Cowork) that deliberated
Direction B is authoring its ratifying ADR, so the
independent-tier-deliberation check is **not** exercised here. Per ADR-012
D4.3 this is disclosed explicitly; Code's review (ADR-009 D3 step 6) is the
remaining independent check. (Chat authored the intervening synthesis
dispatch, which supplies one layer of cross-tier review of the framing,
but not of this ADR's text.)
