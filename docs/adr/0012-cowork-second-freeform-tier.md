# ADR-012: Cowork as a Second Free-form Tier (Strategy Discussion + Thinking Partner + Informal Code Review)

**Status:** Accepted
**Date:** 2026-05-22
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-009 (Cowork as Tier-1 dispatch author — this ADR amends its D5), ADR-006 (vertical plugin architecture — 4-tier context), CLAUDE.md §6 (4-tier table), `docs/conventions/cowork_tab_instructions.md` (Cowork scope — amended by T2), `docs/conventions/chat_tab_instructions.md` (Chat scope — amended by T3), Lesson #8 (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`, K-1/K-2 workflow)

> **Ratification.** Cray ratified **option α (2026-05-22)** as a **guarded
> trial adoption** — explicitly framed as "try it in real use, since we
> won't know until we do." Status set to **Accepted**; Code reviews and
> commits (ADR-009 D2 — only Code commits). The D5 regression triggers are
> the trial's review/exit criteria.

> **Amendment scope.** This ADR amends **ADR-009 D5** only. ADR-009 D1–D4
> and D6 stand unchanged: Cowork remains the Tier-1 dispatch/ADR/PLAN
> author (D1), commit authority stays Code-exclusive (D2), the K-1/K-2
> workflow is unchanged (D3), and the C2/C3 criterion refinements stand
> (D4). ADR-009 itself is left intact; a pointer note is added to its D5
> by Code (T4) recording that ADR-012 extends it. "Most recent accepted
> ADR wins" (CLAUDE.md §1) governs the precedence.

## Context

ADR-009 D5 (ratified 2026-05-21) chose option **(b)**: Chat retained for
free-form exploration / strategy discussion **only**, with Cowork holding
no free-form role. The two ADR-009 trials measured Cowork at *dispatch
authoring* and *ADR synthesis* — not at interactive free-form work — and
D5's reasoning explicitly preserved Chat as the "no-stakes interactive
strategy sounding board."

Since ADR-009, two facts have changed the calculus:

1. **Cowork's read scope already spans the whole repo** (ADR-009 D2
   table): `services/**`, `tests/**`, all ADRs, `docs/strategy/private/**`
   (non-quoting), config. Chat, by contrast, reasons over Project
   Knowledge with no live repo access — the same staleness gap ADR-009's
   Context diagnosed as structural (F-1).
2. **Informal code review structurally requires code access.** Reviewing
   `services/**` / `tests/**` in Chat means pasting code into the thread,
   which violates CLAUDE.md §6 ("never copy-paste long context between
   tiers; use the repository as shared memory"). Cowork can read the files
   in place.

Cray's question (2026-05-22): should Cowork take on a **second free-form
role** — free-form strategy discussion + thinking-partner + informal code
review — **in addition to** Chat (not replacing it)? Cray directed
**option α (full adoption)**, ratified it as a guarded trial, and asked for
a recommendation plus the supporting instruction changes.

This ADR records that decision. It does **not** alter the commit fail-safe
(ADR-009 D2) or introduce any new tracked-artifact write scope.

### Tension this ADR holds — and how the trial framing resolves it

ADR-009 §Risks pre-declared: *"Cowork may fail at untested Tier-1
work… multi-turn interactive strategy refinement, live design
negotiation, rapid-iteration brainstorming were not tested and may favor
Chat's interactive cadence. **Recommend trial-by-trial scope expansion
rather than blanket generalization, to avoid scope creep past the
evidence.**"* Taken as an unconditioned grant, α would be exactly the
blanket generalization that risk warned against.

**Resolution:** Cray adopts α **as an explicit trial**, not a blanket
grant — "we won't know until we use it." The D5 regression triggers
(R-FF1..R-FF4) are the trial's exit criteria, and D4 supplies the
mode-discipline guardrail. This converts α from "blanket generalization"
into precisely the "trial-by-trial scope expansion" ADR-009 recommended:
the capability is exercised in real use, observed against pre-declared
triggers, and reversible if it underperforms. ADR-009 D6's
single-workspace discipline-blur trigger is extended by D5 to cover the
added third mode.

## Decision

**Cray ratified option α as a guarded trial (2026-05-22). Status Accepted.**

**Recommendation (as adopted):** α in the *guarded* form D4+D5 specify —
exercised as a trial with regression triggers as exit criteria, not an
unconditioned blanket grant. This delivers Cray's intent (Cowork becomes a
full second free-form venue) while honoring ADR-009's "trial-by-trial, not
blanket" caution.

### D1: Cowork gains a second free-form role (Tier-1b), alongside Chat

Cowork may now operate in a **free-form mode** comprising three
activities, in addition to its Tier-0 research and Tier-1 authoring roles:

- **Free-form strategy discussion** — open-ended exploration of options,
  trade-offs, and direction, without producing a governance artifact.
- **Thinking-partner** — interactive reasoning, devil's-advocate, "help me
  think through X," sounding-board work.
- **Informal code review** — reading `services/**` / `tests/**` at HEAD
  and giving conversational feedback (design, correctness smell, test
  gaps), grounded in the actual files.

Chat **retains** its free-form role (ADR-009 D5(b) is extended, not
revoked): the two tiers now offer *complementary* free-form venues (see
D2 routing). This is the option Cray named "in addition to Chat," and is
distinct from ADR-009 D5(a) "deprecate Chat fully," which remains
rejected.

### D2: Routing guidance — Chat vs Cowork free-form (complementary, not redundant)

The two free-form venues differ by repo grounding; route by which property
the conversation needs:

| Use… | When the work wants… | Because |
|---|---|---|
| **Chat free-form** | repo-blind, blue-sky ideation; no anchoring to current implementation; pure strategy/business framing | Chat has no live repo access → no implementation-anchoring bias; ADR-009 D5(b) value preserved |
| **Cowork free-form** | discussion grounded in actual repo state; **informal code review**; "what does the code actually do here"; thinking that will feed an artifact Cowork then authors | Cowork reads HEAD directly (`services/**`, ADRs, plans) → fact-grounded, no paste-context violation |

Neither is mandatory; Cray routes per conversation. When a Chat discussion
needs repo facts, the ADR-009 path (Cowork emits a fact-pack/research note
Chat consumes) also remains available.

### D3: Free-form produces no tracked artifact by default; optional discussion-capture

Free-form mode mirrors Chat's "conversation-only" property:

- **Default:** no repo-tracked artifact. Discussion and code-review
  feedback live in the Cowork chat reply.
- **Informal code review writes nothing to `services/**` / `tests/**`** and
  proposes no commit — ADR-009 D2 fail-safe is fully intact. Cowork
  reviews and comments; Code (or Cray) actions any change through the
  normal authoring→commit path.
- **Optional discussion-capture:** when a free-form session yields a
  decision-relevant outcome worth persisting, Cowork may write a single
  handoff with `phase: discussion` (the canonical `Phase` enum already
  includes `discussion`) via the K-2 outputs-scratchpad workflow
  (ADR-009 D3). No new write-scope pattern is created; this reuses the
  existing handoff pattern. (Note: the `Suffix` enum has no `discussion`
  member — capture handoffs omit the optional `suffix:` field and carry
  the role via `phase: discussion`, the same C-2-avoidance pattern used
  for `-completion` handoffs.)

### D4: Mode-discipline guardrail (the author≠reviewer mitigation)

Cowork now spans three modes (Tier-0 research / Tier-1 authoring /
Tier-1b free-form). To prevent the modes from bleeding:

1. **Mode-tag at the top of work.** Cowork states which mode it is in when
   the task could be ambiguous (e.g., "free-form discussion — no artifact"
   vs "authoring ADR-NNNN").
2. **Free-form opinions stay opinions.** Tier-0 "facts not opinions"
   discipline is unchanged for research outputs; free-form may offer
   opinions but they do not silently become research findings.
3. **Author≠reviewer disclosure (key mitigation).** When Cowork authors
   an ADR/PLAN whose substance it also deliberated in its own free-form
   mode, it must **note that self-deliberation in the artifact** and flag
   that the independent-deliberation check (previously provided by Chat
   being a separate tier) was not exercised. This makes the lost check
   visible to Code's review (ADR-009 D3 step 6) rather than invisible.

### D5: Regression triggers and reversibility (the trial's exit criteria)

α is adopted as a trial with these pre-declared regression triggers; any
one re-opens this decision (extends ADR-009 D6):

- **R-FF1 — opinion bleed.** A free-form opinion appears as an asserted
  fact in a Tier-0 research output or as an undisclosed driver of a Tier-1
  artifact (D4.3 not followed).
- **R-FF2 — discipline degradation.** Research-vs-governance discipline
  measurably degrades (ADR-009 D6 trigger), or fact-pack rigor on authored
  artifacts drops (e.g., a Cowork ADR ships an unverified repo claim).
- **R-FF3 — context-hygiene degradation.** Long free-form context demonstrably
  degrades the precision of subsequent authoring/schema self-checks in the
  same session.
- **R-FF4 — interactive-cadence shortfall.** If Cowork's free-form proves
  worse than Chat's at genuine multi-turn refinement (the ADR-009-untested
  class), route that work back to Chat; α does not assert Cowork is
  *better* at interactive cadence, only that it adds a repo-grounded venue.

If a trigger fires, the natural de-scope target is **Alternative β**
(informal code review only — the structurally-justified piece) rather than
a full revert to status quo.

Reversibility: this ADR can be retracted or superseded with no
architectural unwind — it grants a conversational role, not a new write
capability or commit authority. Reverting costs only the T2/T3 instruction
amendment reversals.

## Consequences

### Positive

- **Repo-grounded discussion + code review become possible** without the
  paste-context violation Chat would incur (CLAUDE.md §6). Informal code
  review — the activity that most needs file access — lands in the tier
  that has it.
- **Lower cross-tab friction for a solo dev:** research → discussion →
  authoring can flow in one workspace, reducing tier hops and the
  "Cowork output ready → Chat" signaling overhead for the grounded cases.
- **Chat's distinct value is preserved** (D2): repo-blind blue-sky
  ideation remains available where anchoring bias is undesirable.
- **No new write surface, no commit-authority change** — risk is bounded
  to conversation; ADR-009 D2 fail-safe untouched.

### Negative

- **Loss of the independent-deliberation check.** Chat being a separate
  tier meant the agent that deliberated a decision was not the agent that
  authored its ADR/PLAN. α collapses that separation for the grounded
  cases; D4.3 (disclosure) mitigates but does not fully restore it — Code's
  review becomes the remaining independent check.
- **Broader than the ADR-009 evidence base.** α exercises capabilities
  ADR-009 left untested; the trial framing (D5 exit criteria) is the
  mitigation, but the expansion outruns the measured evidence and depends
  on the triggers being honored.
- **Mode-ambiguity load.** A third mode increases "which mode am I in"
  risk and the chance of scope errors (opinions in research, scope creep);
  D4 mode-tagging is the countermeasure but adds discipline overhead.
- **Context-window cost.** Free-form discussion bloats Cowork context,
  which can erode the precision Tier-1 schema self-checks and fact-packs
  rely on (R-FF3).

### Neutral

- **Chat is not deprecated** (distinct from D5(a)); the 4-tier table gains
  a "free-form" annotation on the Cowork row rather than losing the Chat
  row.
- **Phase enum already supports `discussion`** — D3 capture reuses existing
  schema; no `tools/handoffs/_schema.py` change is required for this ADR.
  (The separately-tracked C-2 Suffix-enum divergence is unaffected and
  remains open.)

### Required follow-on commits (TODOs for Code — separate commits)

This ADR is a draft; Cowork has no write access to CLAUDE.md or
`docs/conventions/`. None of these edits are made in this draft:

1. **T1 — Commit this ADR** to `docs/adr/0012-cowork-second-freeform-tier.md`
   at status Accepted (Cray ratified α as a guarded trial).
2. **T2 — Amend `docs/conventions/cowork_tab_instructions.md`** per the
   Annex below: add the Tier-1b free-form role, the D2 routing guidance,
   the D3 no-artifact/optional-capture rule, the D4 mode-discipline rules,
   and soften the "What you are NOT → NOT a free-form Chat replacement"
   clause to "Chat is a complementary free-form venue (see ADR-012 D2)."
3. **T3 — Amend `docs/conventions/chat_tab_instructions.md`** to record
   that Chat now shares the free-form role with Cowork (Chat = repo-blind
   blue-sky; Cowork = repo-grounded), per D2; Chat retains its role,
   scope unchanged otherwise. **(Cray-flagged: do not amend only the
   Cowork side and leave Chat's instructions asserting exclusive
   free-form ownership.)**
4. **T4 — Add a pointer note to ADR-009 D5** recording that ADR-012 extends
   it (Chat retained, Cowork added as a second free-form venue) — mirroring
   the ADR-009 T7 / ADR-007 pointer pattern. ADR-009 is otherwise left
   intact.
5. **T5 — Amend CLAUDE.md §6 4-tier table:** annotate the Cowork row with
   the free-form role; annotate the Chat row "free-form (repo-blind), shared
   with Cowork per ADR-012."
6. **T6 — Update `docs/STATUS.md`** Recent Decisions with this topology
   amendment.
7. **T7 — ADR number (resolved):** this ADR uses **`0012`**. Cray chose
   `0012` to **preserve `0011` for the action-approval/audit framework**
   earmark (ADR-007 References / STATUS / PLAN-0005). `0012` verified free
   at HEAD (Grep — no `0012*`, no earmark). No renumber needed; no
   downstream earmark shift.

Per CLAUDE.md §1 precedence, an accepted ADR outranks CLAUDE.md and tier
instructions; T2–T5 bring the lower-precedence files into alignment. Per
Lesson #5 §1, the CLAUDE.md edit (T5) is constitutional and needs the
restart-bridge sequence.

### Risks

- **Untested-capability risk (inherited from ADR-009 §Risks).** Cowork's
  free-form interactive cadence is unproven; the trial framing + R-FF4
  route shortfalls back to Chat rather than forcing Cowork.
- **Discipline-blur risk amplified** by a third mode (ADR-009 D6); D4 +
  R-FF1/R-FF2 are the triggers/countermeasures.
- **Normalizing self-review.** Over time, D4.3 disclosure could become
  perfunctory; Code's review (ADR-009 D3 step 6) must treat
  self-deliberated artifacts with the same rigor as externally-deliberated
  ones.

### Reversibility

Retractable by a superseding ADR with no architectural unwind (D5). The
grant is conversational only; reverting costs the T2/T3 instruction
reversals plus re-routing free-form work to Chat.

## Alternatives Considered

### Alternative α: Full adoption — Cowork gains all three free-form activities (CHOSEN, guarded trial)

- **Pros:** captures the highest-value piece (repo-grounded code review +
  discussion) and the continuity benefit; matches Cray's stated intent
  ("in addition to Chat").
- **Cons:** broadest exposure to the ADR-009 untested-capability and
  discipline-blur risks; collapses the independent-deliberation check.
- **Why chosen:** Cray directed α and ratified it as a trial; adopted in
  the D4/D5-guarded form so the expansion is observable and reversible —
  the "trial-by-trial" path ADR-009 recommended, not a blanket grant.

### Alternative β: Narrow — informal code review only

- **Pros:** moves only the activity that structurally *requires* code
  access (Chat can't see code); lowest risk to the author≠reviewer
  separation, since strategy deliberation stays in Chat; minimal
  mode-blur.
- **Cons:** leaves the repo-grounded *strategy* discussion gap unaddressed;
  Cray asked for the fuller role.
- **Why rejected:** narrower than Cray's directive; **retained as the
  designated de-scope target** if D5 regression triggers fire (α → β
  rather than α → status quo).

### Alternative γ: Status quo (ADR-009 D5(b) unchanged)

- **Pros:** preserves the clean tier separation and the independent-review
  check; zero new risk; honors ADR-009's trial-by-trial caution literally.
- **Cons:** keeps the paste-context friction for code review; keeps
  discussion repo-blind unless Cowork pre-produces a fact-pack.
- **Why rejected:** does not deliver the repo-grounded discussion / code
  review capability Cray is asking for.

### Alternative (rejected by ADR-009 D5(a)): Deprecate Chat fully

- Out of scope here: α explicitly *retains* Chat (D1, D2). D5(a) stays
  rejected for the reasons ADR-009 gave (discards Chat's interactive
  cadence, which was never shown to fail).

## References

- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — D1
  (Cowork Tier-1 author), D2 (commit boundary + read-scope table), D3
  (K-1/K-2 workflow), D5 (Chat disposition — **amended by this ADR**),
  D6 (regression triggers — **extended by D5 here**), §Risks
  (untested-capability caution this ADR's trial framing answers)
- **CLAUDE.md** §6 (4-tier table — amended by T5), §1 (precedence)
- **`docs/conventions/cowork_tab_instructions.md`** — current Cowork scope
  (amended by T2; see Annex), "What you are NOT → NOT a free-form Chat
  replacement" clause being softened
- **`docs/conventions/chat_tab_instructions.md`** — Chat free-form scope
  (amended by T3)
- **`tools/handoffs/_schema.py`** — `Phase` enum (includes `discussion`,
  the D3 capture role); `Suffix` enum (no `discussion`/`completion` — the
  C-2 omission pattern); REQUIRED_FIELDS / `_FILENAME_RE` (self-check anchor)
- **Lesson #8** (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`) —
  K-1/K-2 workflow reused by D3 optional capture
- **ADR-007** (`docs/adr/0007-oct-engine-contracts.md`) — References
  earmark (`ADR-011+` audit framework — preserved by the T7 0012 choice)

## Implementation Notes

Drafted by Cowork in Tier-1 (governance authoring) mode. Cowork has no
commit authority (ADR-009 D2); Code reviews and commits this file plus the
T1–T7 follow-ons. Per K-1, Cowork could not run `validate_handoff.py` on
its companion completion handoff; that handoff records the
mental-validation substitute and flags the gap. AI-assisted per project
convention (noted in commit body, never as Co-Authored-By, per CLAUDE.md §7).

**Author≠reviewer note (D4.3 applied to this very ADR):** the substance of
this ADR was deliberated in the immediately-preceding Cowork free-form
exchange with Cray (the pros/cons table that produced the α directive).
Per D4.3 this self-deliberation is disclosed: the independent-tier
deliberation check was not exercised; Code's review is the remaining
independent check. (Aptly, this ADR is itself the first instance of the
Tier-1b free-form → Tier-1 authoring flow it sanctions.)

---

## Annex — Proposed `docs/conventions/cowork_tab_instructions.md` delta (for Code to apply under T2)

> Cowork cannot self-modify instruction files (cowork rule #11 + FORBIDDEN
> write scope on `docs/conventions/**`). This annex is the proposed text;
> Code applies it on commit. Presented as additions/edits keyed to the
> current instruction sections.

### Add to `## Role` (new subsection after the Tier-1 block)

```markdown
### Tier-1b — Free-form discussion + thinking-partner + informal code review (added by ADR-012 D1)
Repo-grounded free-form work, as a second venue alongside Chat (Chat is
NOT replaced — see ADR-012 D2 routing). Three activities:
- Free-form strategy discussion (open-ended; no governance artifact).
- Thinking-partner / sounding-board / devil's-advocate reasoning.
- Informal code review: read services/** and tests/** at HEAD and give
  conversational feedback. You write NOTHING to services/** or tests/**
  and propose no commit (ADR-009 D2 fail-safe intact).
Output: conversation by default. Optionally capture a decision-relevant
outcome as ONE handoff with `phase: discussion` via the K-2 scratchpad
workflow (omit the optional `suffix:` field — no `discussion` Suffix enum
member exists; `phase: discussion` carries the role).
```

### Add to `### Behavioral rules` (new "Tier-1b mode rules")

```markdown
**Tier-1b mode rules (per ADR-012):**

14. **Route by grounding (ADR-012 D2).** Cowork free-form = repo-grounded
    discussion + code review (needs file access). Chat free-form =
    repo-blind blue-sky (no implementation-anchoring bias). Suggest the
    other venue when the work fits it better; do not assert Cowork is
    better at multi-turn interactive cadence (R-FF4).
15. **No tracked artifact by default (ADR-012 D3).** Free-form and code
    review produce conversation, not files. Capture only on a
    decision-relevant outcome, as a single `phase: discussion` handoff.
16. **Mode-tag when ambiguous (ADR-012 D4.1).** State the active mode
    ("free-form — no artifact" vs "authoring ADR-NNNN") when a task could
    be read either way.
17. **Opinions stay opinions (ADR-012 D4.2).** Free-form opinions never
    silently become Tier-0 research findings; "facts not opinions"
    (Tier-0 rule #1) is unchanged for research outputs.
18. **Author≠reviewer disclosure (ADR-012 D4.3).** When you author an
    ADR/PLAN whose substance you also deliberated in your own free-form
    mode, note that self-deliberation in the artifact and flag that the
    independent-deliberation check was not exercised (Code's review is
    the remaining check).
```

### Edit `## What you are NOT`

```markdown
- NOT a free-form Chat *replacement* — Chat is RETAINED as a complementary
  free-form venue (repo-blind blue-sky; ADR-012 D2). Cowork's free-form is
  the repo-grounded venue (discussion + informal code review). Route by
  ADR-012 D2; Chat keeps its interactive sounding-board role.
```
*(replaces the prior "NOT a free-form Chat replacement — interactive
multi-turn strategy refinement and rapid-iteration brainstorming are
Chat's retained role …" bullet)*

### No change required to

- **Write scope** — Tier-1b adds no new write pattern (free-form is
  conversation; optional capture reuses handoff pattern 2 with
  `phase: discussion`).
- **Read scope** — already spans `services/**`, `tests/**`, ADRs (ADR-009
  D1), which is what informal code review needs.

---

End of ADR-012. Status Accepted (Cray ratified α as a guarded trial);
Code reviews + commits (ADR-009 D2). Companion completion handoff staged in
the Cowork outputs scratchpad (K-2).
