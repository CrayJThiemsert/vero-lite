# PLAN-004 Phase A Batch 2 Step 2b.1 — Migration Summary

**Date:** 2026-05-19
**Event type:** working-tree migration (gitignored handoff renames + ref-graph fixup)
**Commit:** this `docs:` commit pair (Commit A renames evidence + Commit B ref-graph; SHAs in the gitignored closeout)
**Operator-grade detail:** gitignored closeout `.claude/handoffs/session-10/2026-05-19-<HHMM>-code-plan004-batch2b1-rename-and-refgraph-closeout.md` — resolve by date (`2026-05-19`) + topic (`plan004-batch2b1-rename-and-refgraph-closeout`); HHMM = closeout write-time (deliberately HHMM-agnostic to not repeat the 2a `1205` placeholder-imprecision — see J6 in the closeout)
**Renames evidence:** `.claude/handoffs/session-10/_rename-map.md` (gitignored, two-artifact evidence model PLAN-004 v2 D6)
**Sub-batch of:** Batch 2 per Step 3 handoff Q1=B (2b.1 = renames + ref-graph; 2b.2 = no-frontmatter file + STATUS housekeeping, queued separately)

## Summary

Renamed **12** `session10-*` legacy handoff files in
`.claude/handoffs/session-10/` to inject the required `-<actor>-` token
(`<DATE>-<HHMM>-session10-<TOPIC>.md` → `<DATE>-<HHMM>-<actor>-session10-<TOPIC>.md`),
per Decision 2 (`2026-05-19-0915-chat-session-handoff-to-new-thread-step2.md` §2).
`<actor>` derived from each file's `from:` field (claude-chat → chat;
claude-code → code); all 12 matched cleanly, zero ambiguity. Filesystem
rename (NOT `git mv`) — target dir gitignored, no history to preserve
(J1). Frontmatter migrated per Step 2a v2/v2.1 rules during the 1453
apply.

§3.6.bis (ratified mini-ratification #1, `2026-05-19-1535-…`) resolved
the one blocker: `2026-05-11-0420-chat-session10-batch2-kickoff.md`
`created: 2026-05-11T<HHMM>:00+07:00` literal placeholder → `04:20:00`
from the filename HHMM token.

Reference-graph fixup (W2) updated **18** inbound references across
**7** files via surgical full-string replace (filename string only;
everything else byte-exact). Classification by §3.4.bis (ratified
mini-ratification #2, `2026-05-19-1635-…`): a file-level pointer-vs-datum
rule with a closed enumerated PRESERVE set; **43** in-repo references
across 6 frozen governance records were PRESERVED (rewriting them would
falsify a `status: DONE` deliverable / the executing dispatch / Decision
2's scope / Code's own classification surfaces). The §3.4-scope denylist
+ sanity-check circuit breaker (ratified 1635) and its dynamic update
(mini-ratification #3, `2026-05-19-1700-…`, added PRESERVE #5 + the
Code-surface auto-qualify class clause) gated the mutation.

`_rename-map.md` is the gitignored two-artifact companion; it is a
non-handoff companion file (same class as `README.md` per manifest
§4.2/§6.1) and is not schema-validatable by filename (Decision A,
mini-ratification #5 `2026-05-19-1800-…`). Its `suffix:` field was
omitted per mini-ratification #4 (`2026-05-19-1730-…`, J4 — the 1500
dispatch's "extensible-suffix policy" claim was factually wrong; the
schema `suffix:` enum is closed).

Cat G legacy `references_*` field names **deferred to Phase B** (no
change this batch).

## Key metrics

| Metric | Pre-2b.1 (post Step 2a v2.1) | Post-2b.1 |
|---|---|---|
| Validator stderr summary (Lesson #7 §3.1) | `54 error(s) across 68 file(s)` | `2 error(s) across <M> file(s)` (file count benign per J2 durable rule — anchor on error + cohort, not count) |
| Schema-FAIL files | 14 | 3 (1 handoff-class + 2 companion-class) |
| **Handoff-class** FAIL (the durable invariant, Decision A) | 13 (12 `session10-*` + post-recovery) | **1** (`post-recovery` only — Step 2b.2 scope) |
| Companion-class non-conformances (expected; Phase B exclusion) | (`README.md`) | `README.md` + `_rename-map.md` |
| Validator `main()` return (Lesson #7 §3.2) | 1 | 1 (Step 2b.2 cohort still failing — expected, not a regression) |

The 12 `session10-*` FAIL→PASS delta is exactly the rename cohort.
Remaining handoff-class FAIL = `{2026-05-13-1030-chat-handoff-post-recovery.md}`
(Step 2b.2). PRESERVE-set integrity verified: all 6 frozen governance
records retain their old-filename references intact (13/14/1/12/2/1).

## What remains for Step 2b.2

- 1 no-frontmatter file: `2026-05-13-1030-chat-handoff-post-recovery.md`
  (manifest §4.5 / Decision 3) — full frontmatter authoring + its own
  ref pass (reuses §3.4.bis)
- STATUS.md content refresh (Current Focus / Recent Decisions / Active
  TODOs) + optional STATUS housekeeping commit (Q3-pattern)
- `README.md` + `_rename-map.md` validator-scope exclusion (Phase B tool
  refinement, manifest §4.2/§6.1 — Decision A classification ratified,
  implementation deferred)
- Cat G `references_*` opportunistic rename (Phase B autofix)

## Process note (5-surface ledger → post-Phase-A retro)

Step 2b.1 surfaced 5 ruleset/tooling gaps (§3.6.bis, §3.4.bis,
PRESERVE-self-reference, J4 suffix, J5 filename), all the same root
(dispatch assumption about validator/schema/tooling unverified against
the actual tool). Mini-ratification #5 (`2026-05-19-1800-…`) applied the
retro finding **in-batch** via a bounded comprehensive pre-flight
(Decision B) to break the per-gap loop. Lesson #8 mint stays deferred to
post-Phase-A retro (Q3=A reaffirmed). Full ledger + retro candidate in
the gitignored closeout.

## Reference

- PLAN-004 v2 D6 (two-artifact evidence model): `docs/plans/0004-handoff-frontmatter-and-dashboard.md`
- `docs/logs/README.md` (this directory's purpose)
- Predecessor summary (Step 2a): `docs/logs/2026-05-19-plan004-batch2a-migration.md`
- Manifest: `.claude/handoffs/session-10/2026-05-19-0842-code-plan004-batch2-manifest.md`
- Original 2b.1 dispatch: `.claude/handoffs/session-10/2026-05-19-1500-chat-plan004-batch2b1-rename-and-refgraph.md`
- Mini-ratifications #1–#5: `2026-05-19-{1535,1635,1700,1730,1800}-chat-plan004-batch2b1-*.md`
- Rename map (full, gitignored): `.claude/handoffs/session-10/_rename-map.md`

AI-assisted per project convention.
