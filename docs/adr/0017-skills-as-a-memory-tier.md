# ADR-0017: Skills as a Memory Tier — formalize `.claude/skills/` in the memory architecture

**Status:** Accepted (ratified 2026-06-09 via PR #236)
**Date:** 2026-06-09
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-009 (Cowork drafts / Code commits — **this ADR is authored under its D1 interim process**), ADR-013 (autonomy-axis relocation — skills are a harness primitive → Code authors, per D1; **this ADR applies that boundary**), ADR-006 (vertical-plugin architecture — Rule of Three + engine-vs-config; the forward-link for harness-as-plugin packaging, OQ-7 / D7), CLAUDE.md §1 (precedence — amended by T2), §4 (memory architecture — amended by T1), §10 (index — amended by T3), §11 (Tier 2 operational policy — already points at the two exemplar skills), `docs/runbooks/memory-architecture.md` (the full Tier model — amended by T4), `docs/for_llm/README.md` (Tier 2.5 derived-snippet rule, mirrored here). Predecessor: PR #234 (`471bcb5`, branch `docs/slim-claude-md-skills`, open — the slimming this ADR completes the governance half of). Authoring dispatch: `.claude/handoffs/session-49/2026-06-09-2140-code-skills-memory-tier-adr-dispatch.md`.

> **Drafting provenance.** Drafted (uncommitted) by Cowork in Tier-1 governance-authoring mode under the unchanged **ADR-009 D1** process (ADR-013's relocation of governance authoring into a Code subagent is phased and has **not** yet executed — Cowork retains interim drafting per ADR-013 D1 + OQ-1). ADR number **0017** confirmed free before drafting (G2 gate): `docs/adr/` tops at 0016, 0014 is WITHDRAWN, and `docs/STATUS.md` §50/§57 already earmarks ADR-017 = "Skills as a memory tier". PLAN-0017 and Lesson #0017 are separate numbering namespaces (no collision). Code commits this draft (ADR-009 D2). **Author≠reviewer disclosure (ADR-012 D4.3):** this ADR's substance was **not** deliberated in a prior Cowork free-form session — it renders the dispatch's eight open questions against the live repo; the independent check is Code's review + Cray's ratification at merge (Proposed → Accepted).

## Context

### What PR #234 shipped (the facts this ADR builds on)

A harness-engineering review (vero-lite vs Anthropic's public Claude Code / Agent-Skills guidance, 2026-06-09) produced a two-axis verdict. Axis A (governance / safety) found vero-lite at the frontier — nothing to fix. Axis B (task-completion / verification) is thin and deferred to a separate track. Cray took the low-risk first move from Axis A's adjacent recommendation: adopt Anthropic's **Agent Skills** pattern and slim the always-loaded constitution. Anthropic's stated rationale — a bloated `CLAUDE.md` causes ignored rules; procedure/domain knowledge belongs in **on-demand Skills**, loaded by relevance rather than every conversation.

That shipped as **PR #234** (commit `471bcb5`, open — constitutional change, Cray ratifies via merge):

- **New mechanism:** `.claude/skills/` — project-level, git-tracked skills, sibling to `.claude/agents/`. Two skills created:
  - `git-workflow` — git/commit/PR mechanics, the body-file backtick trap + recovery, commit+push hygiene (synthesizes Lessons #4/#10/#11).
  - `code-operational-policy` — worktree-mode decision table + transcript-handoff procedure (was the `CLAUDE.md` §11 body; Lesson #3).
- **`CLAUDE.md` slimmed:** §7 keeps the binding git rules + compact one-liners (detail → `git-workflow` skill); §11 → a one-line pointer to `code-operational-policy`; §10 index gains a `.claude/skills/` row. Always-on size 206→193 lines (2050→1908 words); ~644 words of how-to now load on demand only. **No binding rule was removed — only rationale/how-to moved.**
- **Deliberately NOT touched** (left for this ADR): the §4 memory-tier model, the §1 precedence ladder, and `docs/runbooks/memory-architecture.md`. PR #234 only added a navigational §10 row with the note: *"Formalizing Skills as a memory tier (§4 + runbook) is a pending governance follow-up."*

### What is unresolved (why this ADR exists)

`.claude/skills/` exists as a **mechanism** but has no place in the **memory architecture** (CLAUDE.md §4 / the runbook). Skills are a fourth home for knowledge alongside `CLAUDE.md` (always-on rules), `docs/conventions/` (canonical reference), and `docs/lessons/` (durable learnings) — and they have a genuinely different load model from all of them: **git-tracked yet on-demand, auto-invoked by description match** (unlike always-on Tier 1 or deliberately-pulled Tier 2). Without a formal placement, three risks accrue: (a) authors will not know whether a given piece of knowledge belongs in a skill vs a convention vs CLAUDE.md; (b) a skill could silently become a backdoor for un-reviewed binding rules or governance content; (c) the overlap with the (empty) Tier 2.5 `docs/for_llm/` staging area is undefined. This ADR places skills in the tier model and states the decision rule, the authority rule, the authoring owner, and the conventions.

### Repo reality (verified at HEAD this session)

- `docs/adr/` exists 0000–0013, 0014 (WITHDRAWN), 0015, 0016 → **0017 free** (G2 gate cleared above).
- `.claude/skills/git-workflow/SKILL.md` and `.claude/skills/code-operational-policy/SKILL.md` exist (on the PR #234 branch). Both carry `name` + `description` frontmatter and a `## References` section that points back to `CLAUDE.md` + Lessons (`git-workflow` explicitly states *"The binding rules live in `CLAUDE.md` §7"*).
- `docs/for_llm/` holds only `README.md` (Tier 2.5 staging area, **empty of content since 2026-05-07** — ~1 month). Its README already states the two rules this ADR mirrors for skills: *"Reference, don't duplicate — link to ADRs/plans rather than restate them"* and *"If a `for_llm/` file conflicts with CLAUDE.md or `docs/`, the canonical source wins."*

## Decision

Seven decisions (D1–D7) resolve the dispatch's OQ-1…OQ-7; the migration backlog (OQ-8) is a non-binding list under Open Questions. Each decision carries its rationale and the alternative rejected.

### D1: Skills are **Tier 2.6 — On-demand procedural skills** (resolves OQ-1)

`.claude/skills/<name>/SKILL.md` enters the §4 memory model as a new sub-tier **Tier 2.6**, placed adjacent to Tier 2.5 (`docs/for_llm/`) — both are **derived** (canonicals win on conflict; see D3). Read/load semantics, in one row + a sentence:

| Tier | Location | Scope / load model | Examples |
|------|----------|--------------------|----------|
| **2.6** | `.claude/skills/<name>/SKILL.md` | In repo, **git-tracked**, **auto-loaded by description match** when a task triggers the skill (not read every session like Tier 1; not deliberately pulled like Tier 2) | `git-workflow`, `code-operational-policy` |

A skill is the only memory home whose loading is **harness-driven by relevance** rather than always-on (Tier 1) or human/agent-initiated lookup (Tier 2/2.5). That distinct load model is why it earns its own row rather than folding into Tier 2 or Tier 2.5.

- **Rationale:** skills are repo-tracked (like Tier 1/2) yet auto-invoked on demand (like nothing else in the model), so neither "make it Tier 2" (deliberate-pull reference) nor "fold into Tier 2.5" (human-pasted snippet) captures the load semantics. A dedicated sub-tier adjacent to 2.5 keeps both the git-tracked-derived family together and the load model honest.
- **Alternative considered — sub-class of Tier 2 with an "auto-invoked" flag:** *Rejected* — Tier 2 is defined by *deliberate lookup*; auto-invocation is the load-bearing difference (it is what delivers the token saving), so it deserves a row, not a footnote.

### D2: Skills and `for_llm/` (Tier 2.5) **coexist**, split by consumer (resolves OQ-2)

Skills do **not** supersede or subsume Tier 2.5 `docs/for_llm/`. The bright line is the **consumer + trigger**:

- **`for_llm/` (Tier 2.5)** = a **human pastes** a whole-file primer into a **cold-start session** — crucially including **Chat**, which is repo-blind and **not a `vero-bridge` client**, so it *cannot* auto-load a skill. Passive, manual, whole-snippet.
- **Skill (Tier 2.6)** = the **harness auto-loads** a **task-triggered procedure** for the tiers that run skills — **Code** (and **Cowork** via the bridge / desktop client). Active, automatic, task-scoped.

Because Chat can only receive curated context by human paste, `for_llm/` retains a real niche that skills structurally cannot reach. They serve different tiers; they are not redundant.

- **Rationale:** the consumer split is structural, not stylistic — it follows from Chat being repo-blind and not a bridge client (ADR-009 Context K-1/K-2; OQ-T5 bridge-client posture). Declaring skills the successor would strand Chat's cold-start path.
- **Alternative considered — supersede / retire `for_llm/`:** *Rejected for now* — but noted in OQ-8: `for_llm/` has been empty ~1 month, so a future ADR may retire it if it stays unused. Retiring it is a separate decision, not bundled here.

### D3: Skills are **derived**; "synthesize procedure, cite the canonical, never own a binding rule" (resolves OQ-3)

Skills synthesize content owned elsewhere (lessons, conventions, CLAUDE.md). The discipline is **rule-vs-procedure**, not restate-vs-pointer:

1. **A skill MAY restate procedural how-to** in synthesized, actionable form — that is its value (e.g. `git-workflow` consolidating Lessons #4/#10/#11 into one place you read *while committing*). Forcing skills to be pointer-only would defeat the on-demand-usefulness that justifies them.
2. **A skill MUST NOT restate or redefine a binding rule.** Binding rules live in `CLAUDE.md`; the skill **points** to them. (`git-workflow` already does this correctly: *"The binding rules live in `CLAUDE.md` §7"*.)
3. **A skill MUST cite the canonical source** for each synthesized item (`git-workflow` cites each Lesson inline).
4. **On any conflict, the canonical wins** and the skill is corrected — the same authority rule Tier 2.5 `for_llm/` already carries.

**NB resolution (the shipped `git-workflow` skill):** its restatement of Lesson #4/#10/#11 is **acceptable synthesis** under this rule — it is procedural how-to (not binding rule), it cites every lesson, and it explicitly defers the binding rules to `CLAUDE.md` §7. No trimming required. The same check applies to `code-operational-policy` (it points to Lesson #3 + the runbook and restates only the decision table — acceptable).

- **Rationale:** a pointer-only skill is useless at the moment of need (you will not chase three lessons mid-commit); a restate-everything skill drifts from and shadow-governs the canonical. The rule-vs-procedure line keeps skills useful *and* subordinate.
- **Alternative considered — pointer-only skills (strict no-restate):** *Rejected* — it removes the on-demand-usefulness that is the entire point and pushes how-to back toward the always-on `CLAUDE.md` the slimming was meant to relieve.

### D4: **Code authors skills** (harness primitive, per ADR-013 D1); escalation rule for governance content (resolves OQ-4)

Skills are a harness primitive (loaded by the harness, like hooks and agents). Per **ADR-013 D1** the execution-automation axis lives in Code (Tier 2), the only tier that runs these primitives. Therefore:

- **All skills are Code-authored** — harness/procedure skills (`git-workflow`, `code-operational-policy`) and any future skill alike. No skill class requires **Cowork drafting**.
- **The author≠reviewer separation is preserved upstream, not inside the skill.** Governance/domain content a skill needs already lives in a **Cowork-drafted, Code-committed canonical** (ADR / convention); the skill only **references** it (D3). The governance content never originates in the skill.
- **Escalation rule (the guardrail):** if a skill would need to *originate* binding or governance/domain content (not merely point to an existing canonical), that triggers the **ADR-009 D1 path first** — Cowork drafts the canonical (ADR/convention), Code commits it, *then* Code packages the skill that references it. A skill must never be the first home of a governance rule (this is the D3 "never own a binding rule" rule, applied to authoring).

- **Rationale:** keeping skill *authoring* in Code matches ADR-013 D1 (harness primitives are Tier-2-only) while the escalation rule blocks the failure mode where a skill becomes a backdoor for un-reviewed governance. Together they keep skills firmly in the harness lane without weakening governance review.
- **Alternative considered — Cowork drafts "governance-content" skills:** *Rejected* — it would split skill authorship by content type, duplicating the canonical's governance content into a Cowork-authored skill (violating D3) and re-introducing the very author/reviewer entanglement ADR-013 OQ-1 resolves by keeping governance content in the ADR/convention layer.

### D5: The knowledge-placement decision rule (resolves OQ-5 — the load-bearing output)

Where does a given piece of knowledge go? Ask, in order:

| The knowledge is… | It goes in… | Load model |
|---|---|---|
| a **binding rule** the agent must always obey (a "must / never") | **`CLAUDE.md`** (keep it short) | always-on |
| a **durable learning** ("we hit X because Y; next time do Z") — advisory, timeless | **`docs/lessons/`** | reference (advisory) |
| **canonical reference / a standard** — definitions, schema, stable conventions you look up deliberately | **`docs/conventions/`** (or **`docs/runbooks/`** for operational how-to) | deliberate lookup |
| a **procedure / how-to needed only while doing a specific task**, best surfaced automatically at that moment | a **Skill** (`.claude/skills/`) | auto-load on description match |

Two bright lines disambiguate the close cases:

- **Skill vs `docs/conventions/` (both on-demand):** a **convention is the canonical statement** of a reference/standard, **pulled deliberately** by someone who knows to look (it is the source of truth). A **skill is a derived, task-triggered procedure** the harness **auto-surfaces** by description match; it **references** the convention and never replaces it. Mnemonic: *convention = the law on the shelf (you fetch it); skill = the checklist that pops up when you start the job (it fetches you).* Canonical vs derived; deliberate-pull vs auto-push.
- **Skill vs `CLAUDE.md`:** a **binding rule never moves into a skill** — a skill that fails to trigger would silently drop the rule. `CLAUDE.md` holds the rule (always loaded); the skill holds the how-to (loaded when relevant). This is exactly the PR #234 split: §7 kept the binding git rules; the how-to moved to `git-workflow`.

This rule is stated tightly enough to drop into `CLAUDE.md` §4 (or the runbook) verbatim — see T1/T4.

- **Rationale:** the slimming only pays off if authors route new knowledge correctly going forward; a one-table rule + two bright lines is the durable artifact that makes the routing reproducible.
- **Alternative considered — leave routing to author judgment:** *Rejected* — undocumented judgment is exactly what produced the bloated `CLAUDE.md` the review flagged; the rule is the anti-regression.

### D6: Skills carry **no independent precedence** (resolves OQ-6)

The §1 precedence ladder governs *rule conflicts*. Skills do not **originate** rules (D3), so they take **no rank** in the ladder. Make this explicit by adding one line covering both derived families:

> Derived artifacts — Tier 2.5 (`docs/for_llm/`) and Tier 2.6 (`.claude/skills/`) — carry **no independent precedence**. On any conflict with `CLAUDE.md`, an ADR, a convention, or a lesson, the **canonical wins** and the derived artifact is corrected.

- **Rationale:** slotting skills at a numeric rank would imply they can win some conflict, contradicting D3. "No independent precedence; fix the derived artifact" is both safer and simpler, and mirrors the rule Tier 2.5 already lives under.
- **Alternative considered — place skills at the bottom rung (below lessons, above STATUS):** *Rejected* — it implies a skill could outrank `docs/STATUS.md`-style state in a conflict, which is meaningless for a derived procedure; "no precedence" is the accurate statement.

### D7: Skill conventions live in the runbook; description discipline is the load-bearing rule (resolves OQ-7)

The skill conventions are codified as a new **section in `docs/runbooks/memory-architecture.md`** (not a new `docs/conventions/skills.md` file — Cray delegated this location choice to this ADR; the runbook keeps the Tier model and the skill conventions colocated and avoids spawning a file that must be separately maintained and cross-linked). The conventions:

- **Location / shape:** project skills at `.claude/skills/<kebab-name>/SKILL.md`, git-tracked, sibling to `.claude/agents/`. YAML frontmatter: `name`, `description`. Body = the procedure + a `## References` section pointing to the canonical(s) it derives from (per D3).
- **Description discipline (the single most important authoring rule):** the `description` is the **trigger contract** — it must name the trigger conditions precisely enough that the skill loads at the *right* task and stays silent otherwise. An over-broad description loads the skill always (defeating the token saving the whole pattern exists for); an under-broad one never loads it (dead weight). (Exemplar: `git-workflow`'s *"Use whenever committing, pushing, or creating/editing a PR, issue, or release."*)
- **Scope relationship (project vs global vs plugin skills):** project skills (`.claude/skills/`) are repo-canonical for project procedures. Global skills (`~/.claude/skills/`, e.g. the personal `eli-cray` skill) and plugin skills are personal / cross-project and **must not encode project-binding rules** (those belong in `CLAUDE.md` / ADRs per D3/D5). On a name collision, project-local context wins for project work. *(The exact harness resolution order for same-named project vs global vs plugin skills is **flagged for Code to confirm empirically** — see Open Questions OQ-B; this ADR asserts only the authority rule, not the loader's tie-break mechanics.)*
- **Forward link — harness-as-plugin packaging:** skills + hooks + agents could later be bundled as a portable **vero-lite harness plugin** for reuse across Claude-Desktop-on-WSL projects (harness-review recommendation #6; the same template-first, engine-vs-config reuse logic as ADR-006, and the "vero-lite as template for future projects" rationale behind ADR-009 T6 / Lesson #8). **Forward-declared only** — not decided here.

- **Rationale (location):** one new section beside the Tier model is lower-cost than a new convention file and keeps "what a skill is" next to "where skills sit in memory"; the runbook is already the §4 detail home.
- **Alternative considered — a dedicated `docs/conventions/skills.md`:** *Rejected for now* — viable if the conventions grow, but premature for two skills; promotable later (OQ-8).

### D7 Errata (2026-06-10 — OQ-B resolved, restart-confirmed)

OQ-B (the skill-loader tie-break this ADR delegated to Code) was probed
empirically (Session 50) and **restart-confirmed** (Session 51, ~99% confidence,
harness-reported base dirs as ground truth). Two D7 statements are corrected; the
D7 **authority rule stands**.

- **Tie-break mechanics (corrects the "project-local context wins" premise).**
  Empirically the loader does the **opposite**: on a same-bare-name collision the
  **global/user skill WINS over the project skill** — confirmed order
  `C:\Users\crayj\.claude\skills\` **>** `<repo>/.claude/skills/`. The **WSL**
  `~/.claude/skills/` root is **not scanned at all** (harness HOME = Windows side;
  a populated WSL skills dir never surfaced). **Plugin** skills are
  namespace-qualified (`plugin:skill`) and never bare-name-collide. The D7 *intent*
  ("project should govern project work") is a fair preference but **the loader does
  not enforce it** — authors must not rely on a project skill shadowing a
  same-named global one.
- **Factual premise corrections.** (1) `eli-cray`, cited in D7 as "the personal
  `eli-cray` skill" at `~/.claude/skills/`, is a **command** at
  `C:\Users\crayj\.claude\commands\eli-cray.md`, not a skill. (2) No global
  `~/.claude/skills/` directory existed on either root before the probe; the
  example implied a pre-existing populated global skills root that did not exist.
- **What still stands.** The D7 **authority rule** — global/plugin skills *must not
  encode project-binding rules* (those belong in `CLAUDE.md` / ADRs) — is
  **unchanged and reinforced**: since a personal global skill can silently outrank a
  project skill, a project could never safely lock a binding rule into a project
  skill anyway.
- **Durable home:** [`Lesson #22`](../lessons/0022-skill-loader-precedence.md)
  (full precedence ladder + probe method + authoring guard);
  `docs/runbooks/memory-architecture.md` §"Skill Conventions" carries the same
  resolution order. OQ-B below is marked resolved.

## Required follow-on edits (TODOs for Code — separate commits; the AC-2 diff plan)

This ADR is a Cowork draft; Code commits it and applies the edits below (ADR-009 D2 — Cowork has no write access to `CLAUDE.md`, `docs/conventions/`, or `docs/runbooks/`). **Dependency:** the §4 / §10 line context below assumes the **post-PR-#234 slimmed** `CLAUDE.md`; apply after #234 merges (this ADR may land before or after #234, but these edits reference post-#234 text — constraint per dispatch §5).

1. **T1 — Commit this ADR** to `docs/adr/0017-skills-as-a-memory-tier.md` at the status Cray sets (Proposed → Accepted on ratification).
2. **T2 — Amend `CLAUDE.md` §1 (Precedence):** append the D6 derived-artifacts line (Tier 2.5 + 2.6 carry no independent precedence; canonical wins; fix the derived artifact).
3. **T3 — Amend `CLAUDE.md` §4 (Memory Architecture):** add the **Tier 2.6** row (D1 table) to the tier table; add a one-line authority note (skills derived; canonicals win — D3); and add the **D5 decision-rule table** (or a one-line pointer to its runbook home if §4 length is a concern — Code's call at apply time).
4. **T4 — Amend `CLAUDE.md` §10 (Index):** revise the existing `.claude/skills/` row added by PR #234 — drop *"Formalizing Skills as a memory tier (§4 + runbook) is a pending governance follow-up"* (now resolved by this ADR) and cite **ADR-0017** + the §4 decision rule instead.
5. **T5 — Amend `docs/runbooks/memory-architecture.md`:**
   - add a **Tier 2.6** section mirroring the Tier 2.5 section (location, purpose, **derived** authority, lifecycle, load model);
   - add a Tier 2.6 node to the ASCII tier diagram (between Tier 2.5 and Tier 3, "auto-loaded by description match" arrow);
   - add a row to the Promotion Workflow examples table (e.g. *"git/PR mechanics how-to → Tier 2.6 `.claude/skills/git-workflow/`"*);
   - drop the **D5 decision rule** in as a subsection;
   - update **Cross-Tool Sharing** to note skills auto-load for **Code** and **Cowork (via bridge)** but **not Chat** (repo-blind, not a bridge client → use `for_llm/` paste — D2);
   - add the **D7 skill-conventions section** (location/shape, description discipline, project-vs-global/plugin scope, harness-as-plugin forward link).
6. **T6 — Update `docs/STATUS.md`:** record ADR-0017 in Recent Decisions; clear the §50/§57 "next: draft ADR-017" earmark; note the PR #234 follow-up is governance-complete.

Per CLAUDE.md §1, an accepted ADR outranks `CLAUDE.md` and the runbook; T2–T5 bring the lower-precedence files into alignment. Per Lesson #5 §1, the `CLAUDE.md` edits (T2–T4) are constitutional and need the restart-bridge sequence.

## Consequences

### Positive

- **Closes the PR #234 governance gap** — `.claude/skills/` moves from an undocumented mechanism to a named tier (2.6) with a load model, an authority rule, an owner, and conventions.
- **A reproducible routing rule** (D5) — future knowledge lands in the right home, which is the anti-regression against the `CLAUDE.md` bloat the review flagged.
- **Skills cannot shadow-govern** — D3 (no binding rule in a skill) + D4 escalation + D6 (no precedence) make a skill structurally unable to become an un-reviewed governance backdoor.
- **No tier is stranded** — D2 keeps `for_llm/` for Chat's repo-blind cold-start, which skills cannot serve.
- **Consistent with the topology** — D4 keeps skill authoring in Code (ADR-013 D1) while this ADR itself respects ADR-009 (Cowork drafts / Code commits).

### Negative

- **One more tier to teach** — Tier 2.6 adds a row and a decision rule authors must internalize. Mitigated by the single D5 table + two bright lines (kept deliberately small).
- **The reference-don't-restate line requires ongoing judgment** — D3's "procedure ok / binding rule not ok" boundary is a judgment call per skill; a future skill could over-restate. Mitigated: the escalation rule (D4) + Code review at skill-authoring time are the checks.
- **`for_llm/` ambiguity only deferred, not closed** — D2 keeps it alive while it has been empty a month; OQ-8 carries the retirement question forward rather than settling it.

### Neutral

- **Derived-family symmetry** — Tier 2.6 inherits Tier 2.5's exact authority posture (derived; canonicals win), so the model gains a row but no new authority concept.
- **Skills are vertical-agnostic harness tooling** — like the autonomy layer (ADR-013), they sit with the engine/harness, not inside any `verticals/<name>/`.
- **PR #234 sequencing** — this ADR can merge before or after #234; the T2–T5 edits assume #234's slimmed text and apply after it.

### Reversibility

Fully reversible. The tier is documentation (§4 row + runbook section) and the decision rule is advisory routing guidance — deleting them returns to "skills exist as a bare mechanism." No code or data migrates. D6 (no precedence) means removing the tier weakens no safety boundary; the commit fail-safe (ADR-009 D2 / ADR-013 D2) is untouched by this ADR.

## Open Questions

- **OQ-A — Migration backlog (resolves dispatch OQ-8; non-binding list).** Next extraction candidates from always-on context into skills / their right homes: the `CLAUDE.md` §6 autonomy-axis archaeology note (long prose → candidate skill or lesson pointer); the §4 tier-table prose; the transcript-handoff runbook detail already pointed at by `code-operational-policy`; and **whether `for_llm/` content folds into / is retired in favor of skills** (revisit if `for_llm/` stays empty — D2). None binding; each is its own future PR.
- **OQ-B — Skill loader tie-break (delegated to Code) — RESOLVED 2026-06-10** (Session 50 probe, Session 51 restart-confirm; see **D7 Errata** above + [`Lesson #22`](../lessons/0022-skill-loader-precedence.md)). Empirical resolution order: **global/user (`C:\Users\crayj\.claude\skills\`) > project (`<repo>/.claude/skills/`)**; WSL `~/.claude/skills/` not scanned; plugin skills namespaced. This **contradicts** the D7 "project-local context wins" premise (corrected in the errata) but leaves the D7 authority rule intact.
- **OQ-C — Skills as a formal memory tier in an ADR vs runbook-only (settled here, flagged for revisit).** This ADR formalizes the tier; if the harness-as-plugin packaging (D7 forward link) is pursued, the tier definition may need to move/duplicate into the plugin's own docs — revisit at that point.

## Alternatives Considered

### Alternative 1: Document skills only in the runbook, no ADR

- **Pros:** lighter; no constitutional edit; faster.
- **Cons:** skills touch the precedence ladder (D6) and the authoring-ownership boundary (D4, an ADR-013 interaction) — both are ADR-level concerns the runbook cannot bind; PR #234 explicitly flagged this as a *governance* follow-up.
- **Why rejected:** the placement, precedence, and ownership decisions are binding and cross-ADR; they need ADR authority, not a runbook note.

### Alternative 2: Fold skills into Tier 2.5 (`for_llm/`) — one "derived" tier

- **Pros:** no new tier; both are derived (canonicals win).
- **Cons:** conflates two different load models (human-pasted cold-start primer vs harness-auto-loaded task procedure) and two different consumers (Chat vs Code/Cowork); the auto-invocation that delivers the token saving disappears into a footnote.
- **Why rejected:** the load model is the whole point (D1); merging hides it. D2 instead draws the bright line and keeps both.

### Alternative 3: Skills supersede `for_llm/` outright

- **Pros:** one fewer tier; matches the "for_llm has been empty for a month" signal.
- **Cons:** strands Chat's only curated-context path — Chat is repo-blind and not a bridge client, so it cannot auto-load skills (D2).
- **Why rejected:** retiring `for_llm/` is a separate decision; bundling it here would remove a path still in use by a live tier. Carried to OQ-A instead.

## References

- **Predecessor / trigger:** PR #234 (`471bcb5`, branch `docs/slim-claude-md-skills`) — the `CLAUDE.md` slimming + the two exemplar skills; this ADR completes its governance half.
- **Authoring dispatch:** `.claude/handoffs/session-49/2026-06-09-2140-code-skills-memory-tier-adr-dispatch.md` (OQ-1…OQ-8, acceptance criteria, inputs list).
- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — D1 (the authoring process used here), D2 (only Code commits), D3 (K-1/K-2 workflow used for the companion closeout).
- **ADR-013** (`docs/adr/0013-autonomy-axis-relocation.md`) — D1 (harness primitives → Code; the basis for D4 here), OQ-1 (Cowork retained as advisory governance drafter).
- **ADR-006** (`docs/adr/0006-vertical-plugin-architecture.md`) — Rule of Three + engine-vs-config; the reuse logic behind the D7 harness-as-plugin forward link.
- **CLAUDE.md** §1 (precedence — amended by T2), §4 (memory architecture — amended by T3), §10 (index — amended by T4), §11 (already points at the two skills).
- **`docs/runbooks/memory-architecture.md`** — the full Tier 0–3 model (amended by T5); Tier 2.5 section + Cross-Tool Sharing table mirrored here.
- **`docs/for_llm/README.md`** — Tier 2.5 derived-snippet authority + "reference, don't duplicate" rule (mirrored for skills in D3).
- **Skill exemplars:** `.claude/skills/git-workflow/SKILL.md` (synthesizes Lessons #4/#10/#11; the D3 acceptable-synthesis reference), `.claude/skills/code-operational-policy/SKILL.md` (Lesson #3 + transcript-handoff runbook).
- **Anthropic sources** (researched 2026-06-09, per the dispatch): "Effective context engineering," "Equipping agents with Agent Skills," Claude Code best practices (bloated-`CLAUDE.md`-causes-ignored-rules rationale).
- **`docs/STATUS.md`** §50/§57 — the ADR-017 earmark cleared by T6.

## Implementation Notes

- Drafted by Cowork in Tier-1 governance-authoring mode under the unchanged ADR-009 D1 process (ADR-013's relocation to a Code Plan-subagent is phased and not yet executed). Cowork has no commit authority (ADR-009 D2); Code reviews and commits this file plus the T1–T6 follow-ons.
- **G2 number gate:** ADR-0017 confirmed free before drafting (0016 highest; 0014 WITHDRAWN; STATUS earmark matches; PLAN-0017 / Lesson #0017 are separate namespaces).
- **K-1 validator gap:** per K-1 (Cowork bash UNC refusal — re-confirmed live this session, blocks even `date`), Cowork could not run any validator; this is a prose ADR (not a handoff), so no frontmatter validator applies, but the companion completion handoff records the mental schema-validation substitute and flags the gap.
- **Author≠reviewer disclosure (ADR-012 D4.3):** the ADR's substance was not pre-deliberated in a Cowork free-form session; the independent check is Code's review (ADR-009 D3 step 6) + Cray's ratification at merge. AI-assisted per CLAUDE.md §7 (noted in commit body, never as Co-Authored-By).
- Status flips Proposed → Accepted on Cray ratification; Code applies the edit + commits.
