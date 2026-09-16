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
| 1 | **demo→pilot** | `docs/plans/done/0126-*.md` (the `/story/` explainer; deploy record `docs/logs/2026-09-16-plan0126-fleet-story-deploy.md`) · `docs/plans/done/0100-*.md` (the published demo surface) · `docs/plans/done/0096-*.md` §Verification (residual risks) · ADR-0032 D1 (the wedge motion) · tie to stream 4: `docs/strategy/public/intro-video-production-rulings.md` §5 |
| 2 | **harness/governance debt** | `docs/plans/done/0102-*.md` (retire L1) · `docs/logs/2026-08-17-s235-unscheduled-measured-items.md` §2 (assembly-cost axis), §3 (seam-scoped mutation-testing CI) · STATUS row "CLAUDE.md follow-up extraction pass" |
| 3 | **primitives** | `docs/plans/0076-*.md` §(A) F-FACTORY · `docs/plans/done/0078-*.md` §L-3 + Out of Scope (the O-2 residue) · STATUS row "Custom Postgres image with extensions" |
| 4 | **marketing/FDE** | `docs/strategy/private/2026-08-06-marketing-fde-plan-synthesis.md` §4 asset roadmap, §6 open questions (gitignored — reference by path only, it carries pricing; absent from any worktree or fresh clone) · `docs/logs/2026-08-17-s235-unscheduled-measured-items.md` §1 (public one-pager v2) · `docs/strategy/public/intro-video-production-rulings.md` §5 (tie to stream 1) |

**This table is advisory** (ruled by Cray, typed s306; closes the "does a skill's registry
table bind?" question STATUS carried from s210). It is an index of *where* each stream's
state lives, never *what* that state is.

- **Pointers only.** A cell holds a path, a section, or a `STATUS row "<title>"` — never a
  status word (`COMPLETE`, `parked`, `neither drafted`, `as they appear`). Status words are
  what rotted here: after the s306 refresh every PLAN number was present and five claims
  across all four rows were still stale, which no number check can see.
- **No update obligation.** Nobody must edit this table when a PLAN closes. Step 2 is how a
  reader learns it is behind; fixing a pointer you notice is a courtesy `docs/*` PR.
- **One mechanical backstop, already live:** `tools/check_plan_archive_refs.py` (R8,
  `always_run`) reddens the commit that archives a PLAN this table names by glob — witnessed
  s306 by staging an archive of PLAN-0076 (exit 0 → 1, finding at this file's row 3; restored
  → 0). It cannot see a carrier that was never named; that is step 2 (a).
- **Provenance.** The four-stream split comes from §7 of the gitignored synthesis in row 4,
  whose frontmatter marks everything except its four frame decisions as not ratified. No ADR
  defines it.

### Naming a shipped demo surface (ruled by Cray, typed s306)

Name a shipped surface by **its PLAN number + the git identity of what shipped** — never an
invented release name or tag (the repo has none). A PLAN number survives the archive move
into `done/`; a path does not.

- **"story v1"** = the PLAN-0126 story page as deployed 2026-09-16: `services/api/static/story/`
  at the merged sha `ea6944fa` that `docs/logs/2026-09-16-plan0126-fleet-story-deploy.md`
  records as shipped — git tree `40a408f4`. The tree id is the identity: the same files give
  the same id at any commit, and any change to any file gives a new one, so
  `git rev-parse <sha>:services/api/static/story` answers "is this still story v1?" in one
  command. The next deployed tree is "story v2".
- **`?v=cNN` is a cache-bust counter, not a version.** It is per file, and
  `story/index.html` carries counters for the files it loads but none for itself — its own
  copy can change while every counter stays put. Never name a release by it.

## Procedure

1. **Ground the clock.** Read `docs/STATUS.md` frontmatter (`session`, `head_commit`,
   `blocked_on`, `next_action`) — then verify freshness: `git log --oneline -10` via
   WSL. STATUS routinely lags one session; if `head_commit` ≠ actual HEAD, say so and
   trust git + the artifacts, not the STATUS prose.
2. **Check this registry before trusting it, and say what you found.** The table is
   advisory (above) and can lag. Run both checks from one script file via `wsl bash -lc`
   (user CLAUDE.md B1), after `git fetch origin main`, writing output to a session-unique
   file (`/tmp` is shared across live sessions). Both were witnessed against known-answer
   controls at s306.

   ```
   set -o pipefail
   S=.claude/skills/stream-status/SKILL.md
   # (a) PLANs archived after this table last changed: the carriers it may be missing
   LAST=$(git log -1 --format=%H origin/main -- "$S")
   git log --no-renames --diff-filter=A --name-only --format= "$LAST"..origin/main -- docs/plans/done/
   # (b) every path and STATUS row title the table points at still resolves
   sed -n '/^| [1-4] |/p' "$S" | grep -o 'docs/[A-Za-z0-9_./*-]*\.md' | sort -u |
     while read -r p; do if ls -d $p >/dev/null 2>&1; then echo "OK      $p"; else echo "MISSING $p"; fi; done
   sed -n '/^| [1-4] |/p' "$S" | grep -o 'STATUS row "[^"]*"' | sed 's/^STATUS row "//; s/"$//' |
     while read -r t; do echo "hits=$(grep -c -F "$t" docs/STATUS.md)  $t"; done
   ```

   Reading it: **(a)** lists only PLANs archived *after* the table's last edit, so it is
   usually short and grows only until the table is next touched — say for each line whether
   it is a real carrier (then offer a `docs/*` PR) or not. **(b)** must print `OK` for every
   tracked path and `hits=` ≥ 1 for every STATUS row title; a `MISSING` or `hits=0` is a dead
   pointer. The one expected `MISSING` is the gitignored stream-4 synthesis in a worktree or
   fresh clone — then say stream 4 is rendered without it. **Name every finding before the
   stream blocks.** If you skipped this step, the readout says so.
3. **Per stream, read the registry sources** (scoped reads — never a wide Glob/Grep on
   the UNC root). For PLANs: the `Status:` line, AC checkbox tally (count `[x]` vs
   `[ ]` yourself — prose claims about counts have been wrong before), and any
   BLOCKED-ON / gated markers. For STATUS TODO rows: the newest bracketed session
   annotation wins.
4. **Recent motion:** from `git log` since the previous session's head, attribute
   merged PRs to streams by their scope/paths.
5. **Blockers:** distinguish *gated on Cray* (an SD/OQ ruling owed) vs *gated on work*
   vs *parked by decision* — never present a parked item as stalled (STATUS shorthand
   is not the next action).
6. **Render ELI-CRAY (Thai)**, one block per stream: **สถานะ** (one line) → **เดินล่าสุด**
   (PRs/commits since last look) → **ติดอะไร** (with the gated-on-whom distinction) →
   **ก้าวถัดไปที่เป็นรูปธรรม**. Close with a one-line cross-stream picture — but NO
   ranking and NO recommendation unless Cray asks (then hand off to
   `next-work-analyst`).

## Caveats

- Stream 4's canonical doc is **gitignored**; quote its content in chat freely but
  never copy pricing into a tracked file (public-repo boundary, CLAUDE.md §8).
- A `confirmed — prior intact` readout is hygiene, not a verdict (CLAUDE.md §6) — a
  stream with no motion since last check is reported as unchanged, not as a problem.
