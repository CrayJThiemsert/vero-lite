# PLAN-004 Phase A Batch 2 Step 2a — Migration Summary

**Date:** 2026-05-19
**Event type:** working-tree migration (gitignored handoffs frontmatter)
**Commit:** this `docs(logs):` commit (SHA assigned on commit; recorded in the gitignored closeout + STATUS housekeeping commit)
**Operator-grade detail:** `.claude/handoffs/session-10/2026-05-19-1205-code-plan004-batch2a-bulk-migration-v2-closeout.md` (gitignored)
**Supersedes:** Step 2a v0 dispatch (`2026-05-19-1100-chat-plan004-batch2a-bulk-migration.md`) paused per midflight `2026-05-19-1048` (gitignore evidence-model gap; resolved via Cray-ratified Option 1). Executed under v2 (`2026-05-19-1330`) + v2.1 patch (`2026-05-19-1500`, which closed 3 systematic ruleset gaps surfaced by the v2 dry-run midflight `2026-05-19-1143`).

## Summary

Migrated 20 working-tree gitignored handoff files in
`.claude/handoffs/session-10/` to PLAN-004 v2 schema conformance.
Token-bearing files only (filename contains a valid actor token
`chat-` / `code-` / `cowork-`); no file renames in this batch. The
`session10-*` rename cohort (12 files), the no-frontmatter file
(`2026-05-13-1030-chat-handoff-post-recovery.md`), and `README.md`
are deferred to Step 2b.

Migration was applied via a surgical line-level editor (not
parse-and-reemit): every unmodified frontmatter line — including YAML
block scalars (`note_on_path: |`, `purpose: |`), comments, and
deferred Cat G legacy fields — and the entire body were preserved
byte-exact. Only the specific §3 fields were inserted/edited.

Transformations applied (deterministic, per dispatch v2 §3 + v2.1 §2):
- `actor:` added from filename token — **12 files** (§3.1)
- `batch:` added from filename suffix-stem — **8 files** (§3.2)
- `status:` normalized to enum — **16 files** (§3.3 + v2.1 §2.1
  ratified extensions: `ready-to-*`→READY, `PAUSED_*`→PAUSED,
  `ACTIVE`→IN_PROGRESS, `COORDINATION_NOTICE`→READY)
- `phase:` normalized to enum — **14 files** (§3.4 + v2.1 §2.2
  ratified: `research-prompt-*`/`coordination`→dispatch,
  `mid-session`→handoff)
- Cat F `phase: <suffix>` → `phase: handoff` + `suffix:` — **3 files**
  (§3.5: 2× restart-bridge, 1× sync)
- `created:` TZ append — **0 files** (none in scope lacked TZ; the
  one Cat E file is a `session10-*` Step 2b file)
- `title:` added from first body `# heading` — **2 files** (v2.1 §2.3
  new §3.8)

Cat G legacy `references_*` field names **deferred to Phase B**
(v2.1 §3 ratified): left AS-IS; warning-level, non-blocking; ≈3
`warning: unknown field` lines persist by design (manifest §4.1).

(Exact per-file accounting in the operator closeout pointer above.)

## Key metrics

| Metric | Pre-migration | Post-migration |
|---|---|---|
| Validator stderr summary (Lesson #7 §3.1) | `127 error(s) across 66 file(s)` | `54 error(s) across 68 file(s)` |
| Schema-FAIL files | 34 | 14 |
| `scope_2a` files failing | 20 | **0** |
| Validator `main()` return (Lesson #7 §3.2) | 1 | 1 (Step 2b cohort still failing — expected, not a regression) |

The 20-file FAIL→PASS delta is exactly `scope_2a`. Remaining 14 FAIL =
Step 2b cohort (12 `session10-*` rename + 1 no-frontmatter + `README.md`).
File-count grew 66→68 (two schema-conformant handoffs created since the
pre-migration partition: the v2 midflight + v2.1 dispatch).

## What remains for Step 2b

- ~12 `session10-*` files needing actor-token injection via **rename**
  (manifest §4.4 + Decision 2)
- 1 no-frontmatter file: `2026-05-13-1030-chat-handoff-post-recovery.md`
  (manifest §4.5 / Decision 3)
- `.claude/handoffs/README.md` validator-scope exclusion (Phase B tool
  refinement, manifest §4.2 / §6.1)
- Cat G `references_*` opportunistic rename (Phase B autofix per
  manifest §6.3 / v2.1 §3)

## Reference

- PLAN-004 v2 D6 (two-artifact evidence model spec): `docs/plans/0004-handoff-frontmatter-and-dashboard.md`
- `docs/logs/README.md` (this directory's purpose)
- Manifest: `.claude/handoffs/session-10/2026-05-19-0842-code-plan004-batch2-manifest.md`
- v2 dispatch: `.claude/handoffs/session-10/2026-05-19-1330-chat-plan004-batch2a-bulk-migration-v2.md`
- v2.1 patch: `.claude/handoffs/session-10/2026-05-19-1500-chat-plan004-batch2a-v2_1-patch.md`
- v2 dry-run gap midflight: `.claude/handoffs/session-10/2026-05-19-1143-code-plan004-batch2a-v2-midflight.md`
- Foundation mini-batch commit: `1b02b05`; Lesson #7 commit: `1cd7ebc`

AI-assisted per project convention.
