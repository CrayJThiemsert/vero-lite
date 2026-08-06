---
name: stream-status
description: On-demand progress dashboard of the four vero-lite work streams — (1) demo→pilot, (2) harness/governance maintenance debt, (3) primitives, (4) marketing/FDE — computed live from STATUS.md + active PLAN statuses + recent git log (no state file of its own). Use when Cray asks "งาน 4 สายไปถึงไหน / ความคืบหน้าแต่ละสาย / stream status / track the work streams", at session start when choosing which stream to advance, or before a cross-stream planning discussion. Renders ELI-CRAY (Thai): per-stream สถานะ → เดินล่าสุด → ติดอะไร → ก้าวถัดไป. For RANKING what to do next use next-work-analyst instead — this skill reports state, it does not prioritize.
---

# stream-status — the 4-stream progress readout

A task-triggered procedure (Tier 2.6). Answers "where does each work stream stand?"
**computed on demand** — this skill owns NO state file; the repo is the single source
of truth (CLAUDE.md §4). It reports; it never ranks or decides (that is
`next-work-analyst`'s job, and decisions are Cray's).

## The stream registry

| # | Stream | Where its state lives |
|---|--------|----------------------|
| 1 | **demo→pilot** | `docs/plans/0100-*.md` (published demo surface — read its AC checkboxes + Steps section, not prose claims); PLAN-0096 residual risks (`docs/plans/done/0096-*.md` §Verification preamble); the STATUS Active-TODO row for PLAN-0100; ADR-0032 D1 (the wedge motion itself) |
| 2 | **harness/governance debt** | `docs/plans/0102-*.md` (retire L1); STATUS Active-TODO rows: CLAUDE.md extraction pass (parked), assembly-cost tripwire, seam-scoped mutation-testing CI |
| 3 | **primitives** | `docs/plans/0076-*.md` §A (T1 F-FACTORY — the procedure-aware ExecutorFactory half); the O-2 residue (`docs/plans/done/0078-*.md` §L-3 + Out-of-Scope); custom Postgres image (needs fresh ADR + PLAN, neither drafted — STATUS TODO) |
| 4 | **marketing/FDE** | `docs/strategy/private/2026-08-06-marketing-fde-plan-synthesis.md` (gitignored — reference BY PATH ONLY in any tracked output; it carries pricing) + its §4 asset roadmap and §6 open questions; tracked-side artifacts (landing-layer PLAN, one-pager assets) as they appear |

Registry maintenance: when a PLAN closes or a new artifact becomes a stream's live
carrier, update THIS table in the same PR that archives/creates the artifact — the
registry is the only part of this skill that rots.

## Procedure

1. **Ground the clock.** Read `docs/STATUS.md` frontmatter (`session`, `head_commit`,
   `blocked_on`, `next_action`) — then verify freshness: `git log --oneline -10` via
   WSL. STATUS routinely lags one session; if `head_commit` ≠ actual HEAD, say so and
   trust git + the artifacts, not the STATUS prose.
2. **Per stream, read the registry sources** (scoped reads — never a wide Glob/Grep on
   the UNC root). For PLANs: the `Status:` line, AC checkbox tally (count `[x]` vs
   `[ ]` yourself — prose claims about counts have been wrong before), and any
   BLOCKED-ON / gated markers. For STATUS TODO rows: the newest bracketed session
   annotation wins.
3. **Recent motion:** from `git log` since the previous session's head, attribute
   merged PRs to streams by their scope/paths.
4. **Blockers:** distinguish *gated on Cray* (an SD/OQ ruling owed) vs *gated on work*
   vs *parked by decision* — never present a parked item as stalled (STATUS shorthand
   is not the next action).
5. **Render ELI-CRAY (Thai)**, one block per stream: **สถานะ** (one line) → **เดินล่าสุด**
   (PRs/commits since last look) → **ติดอะไร** (with the gated-on-whom distinction) →
   **ก้าวถัดไปที่เป็นรูปธรรม**. Close with a one-line cross-stream picture — but NO
   ranking and NO recommendation unless Cray asks (then hand off to
   `next-work-analyst`).

## Caveats

- Stream 4's canonical doc is **gitignored**; quote its content in chat freely but
  never copy pricing into a tracked file (public-repo boundary, CLAUDE.md §8).
- A `confirmed — prior intact` readout is hygiene, not a verdict (CLAUDE.md §6) — a
  stream with no motion since last check is reported as unchanged, not as a problem.
