# Lesson #22: Skill-loader precedence — global/user **wins** over project (empirically), WSL root not scanned, mid-session rescan is live

> **Status:** Codified 2026-06-10 (Session 51, restart-confirm of the Session 50 ADR-0017 OQ-B probe). Resolves ADR-0017 **OQ-B** (skill loader tie-break, delegated to Code) and drives the **ADR-0017 D7 errata** of the same date. Probe ran with Cray's explicit approval.
> **Severity:** Medium (silent — the loader's tie-break is the *opposite* of the authority rule D7 asserts; an author who trusts "project shadows global" ships a skill that is silently overridden by a same-named global one). Sibling to [[lesson-0017-mcp-cross-tab-visibility-empirical-probe]] (empirical-probe discipline, same Desktop-on-WSL transport reality) and the memory note [[memory_feedback_empirical_probe_before_trivial_oq]] (probe before trivially resolving an observable OQ).
> **Cross-references:** ADR-0017 §D7 + §Open Questions OQ-B (the authority rule this lesson empirically qualifies); `docs/runbooks/memory-architecture.md` §"Skill Conventions" (the OQ-B placeholder this lesson's resolution order fills); `.claude/handoffs/session-50/2026-06-10-0057-code-oqb-loader-probe-restart-confirm.md` (gitignored probe bridge — verbatim in-session matrix + restart-confirm steps this lesson generalizes from).

## 1. The verified precedence ladder

The ADR-0017 OQ-B probe (Session 50, **restart-confirmed Session 51**) used 6 throwaway `SKILL.md` across 3 roots — distinct-named markers per root plus a deliberately **shared** `probe-collide` name to force a same-bare-name collision. Each invocation returns the harness-reported **base directory** (ground truth, not inference) plus a marker string the skill body prints verbatim.

| Root | Path (this environment) | Scanned by the harness? | Tie-break rank |
|---|---|---|---|
| **Global / user (Windows)** | `C:\Users\crayj\.claude\skills\` | **Yes** | **Wins** ⚠️ |
| **Project (repo)** | `<repo>/.claude/skills/` (WSL working tree) | **Yes** | Loses to global |
| **Global / user (WSL)** | `/home/crayj/.claude/skills/` | **No** — never surfaced even when populated on disk | — (not in scan path) |
| **Plugin** | namespace-qualified `plugin:skill` (e.g. `anthropic-skills:*`) | Yes, separate addressing space | Cannot bare-name-collide |

**Confirmed resolution order for a same-bare-name skill:**

> **global/user (Windows `C:\Users\crayj\.claude\skills\`) > project (`<repo>/.claude/skills/`)**; the **WSL** `~/.claude/skills/` root is **not scanned at all**; **plugin** skills are namespaced (`plugin:skill`) and so never collide on a bare name.

Evidence at clean restart (Session 51):
- `probe-collide` → base dir `C:\Users\crayj\.claude\skills\probe-collide`, marker `TIEBREAK_WINNER=WINDOWS_GLOBAL` — invoked across two sessions, **deterministic** (never flipped to the project copy).
- `probe-proj` → base dir = repo `.claude/skills/probe-proj`, marker `SCANNED_TIER=PROJECT_REPO` (project root *is* scanned — it just loses the tie).
- Startup available-skills list showed `probe-collide` **exactly twice** (project + Windows-global) and **never** showed `probe-wsl-global` — even though `/home/crayj/.claude/skills/probe-wsl-global` and `/home/crayj/.claude/skills/probe-collide` existed on disk. The WSL root being populated but never surfaced is the direct proof that it is outside the scan path (the harness HOME is the Windows side).

## 2. This **contradicts** the ADR-0017 D7 authority rule — and that gap is the point

ADR-0017 D7 asserts: *"On a name collision, project-local context wins for project work."* The loader does the **opposite** — a same-named **global** skill wins. The two are not reconciled by wishing:

- **Authority *intent*** may still be "the project's procedure should be the one that runs for project work" — that is a sensible governance preference.
- **The loader does not enforce that intent.** There is no mechanism by which a project `.claude/skills/foo/` shadows a global `~/.claude/skills/foo/`; the global copy wins silently.

**Therefore the operative rule for authors is the empirical one, not the aspirational one.** See §4 for the authoring guard. The ADR-0017 D7 errata (2026-06-10) records this correction in the ADR itself; this lesson is the durable advisory home.

## 3. Two premise corrections to D7 (both empirically wrong for this environment)

The probe also falsified two incidental factual premises in D7's prose:

1. **`eli-cray` is a *command*, not a global skill.** D7 calls it "the personal `eli-cray` skill" living at `~/.claude/skills/`. Verified location: `C:\Users\crayj\.claude\commands\eli-cray.md` (a command file — frontmatter `description` + `argument-hint`, body uses `$ARGUMENTS`). There is **no** WSL `~/.claude/commands/eli-cray.md`. The harness surfaces commands alongside skills in the invocable list, which is how D7's author mistook it for a skill — but the on-disk artifact is a command, in a different directory, with no `SKILL.md`.
2. **No global `~/.claude/skills/` directory existed on *either* root before this probe.** D7's "e.g. the personal `eli-cray` skill" implies a pre-existing populated global skills root; there was none. The Windows and WSL `~/.claude/skills/` dirs were both **created by the probe** and removed again at cleanup (restored to absent).

Neither correction changes D7's *authority* rule (global/plugin skills must not encode project-binding rules — still sound); they correct the **example** used to motivate it.

## 4. Authoring guard (the load-bearing takeaway)

- **Do NOT rely on a project skill shadowing a same-named global/user skill.** It won't — the global one wins. If you author a project skill whose bare name collides with one in `C:\Users\crayj\.claude\skills\`, the global copy runs and your project copy is dead weight. **Use a project-distinct name** (the repo's two real skills — `git-workflow`, `code-operational-policy` — are already collision-free and should stay that way).
- **Binding/governance content still never lives in any skill** (global or project) — that is the standing D3/D5 rule, and the tie-break finding *reinforces* it: since a personal global skill can silently outrank a project skill, a project could never safely "lock in" a rule via a project skill even if it wanted to. Binding rules stay in `CLAUDE.md` / ADRs.
- **WSL `~/.claude/skills/` is a dead drop.** Anything placed there is never loaded (harness HOME = Windows side). Author global skills only under `C:\Users\crayj\.claude\skills\`.

## 5. Mid-session rescan is live (no restart needed for pickup)

A secondary finding: creating a new `SKILL.md` mid-session makes it **invocable without a Desktop restart** — the harness rescans on file creation. Two caveats observed:
- **Refresh-cycle lag:** a newly created skill took one refresh cycle to surface (not instantaneous).
- **Transient duplicate listing:** `probe-collide` first appeared as **2 duplicate list entries** during the rescan before settling — so a doubled entry in the available-skills list mid-session is a rescan artifact, not necessarily two real roots. (At *clean restart*, the 2 `probe-collide` entries were genuine: project + Windows-global.)

**Practical consequence:** you can iterate on a skill in-session and test it immediately. But for a precedence/tie-break claim, **confirm under a clean restart** — the mid-session rescan ordering is not guaranteed to match the cold-start scan ordering, which is exactly why the Session 50 in-session finding was held at ~85% until the Session 51 restart raised it to ~99%.

## 6. How to re-probe if this changes

This resolution order is **empirical** as of 2026-06-10 and environment-specific (Claude Desktop on Windows, repo in WSL, harness HOME = Windows). Re-probe if any of these change:
- Claude Desktop major version bump, or a documented skill-precedence feature ships.
- Cray switches Desktop install format, or the harness HOME flips to the WSL side (would make WSL `~/.claude/skills/` the scanned global root).
- The repo moves out of WSL onto the Windows filesystem.

Re-probe recipe (throwaway, clean up after): drop a distinct-named `SKILL.md` under each candidate root plus one shared name across two roots; restart; invoke the shared name and read the harness-reported **base directory** (not the marker text alone — the base dir is ground truth). Remove all probe dirs and restore each global root to its prior absent/empty state. If the result contradicts §1, update **this** lesson (don't fork) and add an ADR-0017 errata addendum.

## 7. Related artifacts

- `docs/adr/0017-skills-as-a-memory-tier.md` — §D7 (authority rule + the two corrected premises) and §Open Questions OQ-B (now resolved by this lesson); carries the 2026-06-10 errata.
- `docs/runbooks/memory-architecture.md` — §"Skill Conventions (ADR-0017 D7)" project-vs-global-vs-plugin bullet; the OQ-B placeholder is replaced with this lesson's resolution order.
- [[lesson-0017-mcp-cross-tab-visibility-empirical-probe]] — sibling empirical-probe lesson; §5 empirical-probe-before-trivial-resolution discipline applies directly here.
- [[memory_feedback_empirical_probe_before_trivial_oq]] — the standing "probe an observable OQ, don't infer" memory note this probe honors.

---

*Codified by Code session 51 immediately after the OQ-B restart-confirm, at Cray's direction (routing pick: "Code drafts + PR, errata gated"). Probe ran with Cray's explicit approval. AI-assisted; no `Co-Authored-By` trailer per CLAUDE.md §7.*
