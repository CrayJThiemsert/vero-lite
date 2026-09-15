# PLAN-0125 fact-pack measures — the first `measure` blocks

**Date:** 2026-09-15
**Event type:** measurement
**Commit:** every block below is sealed against `main` at `e83422c` (its `against_sha`), the tree Step 1 emitted them from; they land in the PLAN-0125 Step 1 PR
**Operator-grade detail:** `.claude/handoffs/session-302/` (gitignored)

## Summary

The first population of ADR-0038 D3's `measure` bucket, emitted by `tools/measure.py`
(PLAN-0125 Step 1, §3.3). Every block was written by the tool, not typed. Its `hash`
is the seal the staleness guard (Step 2) recomputes, and every block is `rerun: true`,
so the guard can re-derive each value offline.

Five blocks re-measure PLAN-0125's own grounding rows at the historical tree `f65f7ea`,
where s291 took them. They are cited from the PLAN as `measure:<hash>:historical`. The
sixth is §3.3's file-content control, over a path that is live today.

## What each block re-measures

Each predicate was fixed before the tool ran. Its expected value is Code's s299 reading
(G15, G17) or the drafter's s291 Grep (G16).

| Metric | PLAN-0125 row | Predicate | Control |
|---|---|---|---|
| `status_head_range_commits` | G15: every commit in the range | `value == 9` | the empty range `793b9d9..793b9d9` |
| `status_head_drift` | G15 / SD-1's premise: substantive commits only | `value == 3` | the same empty range |
| `status_pr_needles_absent` | G16: `#1453`–`#1456` absent from STATUS | `value == 0` | `#1445` in the same blob |
| `status_pr_needles_present` | G16: `#1449`–`#1452` present (occurrences) | `value == 18` | `#1445` in the same blob |
| `status_bytes` | G17: STATUS's size at `f65f7ea` | `value == 58401` | the PLAN template's size at `f65f7ea` |
| `template_measure_tokens` | §3.3: file-content control | `value == 0` | `Goal` in the same file |

## Blocks

<!-- measure:v1 -->
```json
{
  "schema": "measure/v1",
  "metric": "status_head_range_commits",
  "value": "9",
  "units": "commits",
  "procedure": {
    "argv": [
      "git",
      "log",
      "--format=%h",
      "793b9d96a3a1a2e5f186d560859b59e07d0c47d4..f65f7eaddfcf96fd3c3f92235f41f615864de6af"
    ],
    "reduce": "lines"
  },
  "against_sha": "e83422c25e8e61a8819f41e8b14a79bb2b6da9e3",
  "declared_paths": [],
  "history": true,
  "who": "code-s302",
  "when": "2026-09-15T10:15:37Z",
  "predicate": "value == 9",
  "pass": true,
  "control": {
    "argv": [
      "git",
      "log",
      "--format=%h",
      "793b9d96a3a1a2e5f186d560859b59e07d0c47d4..793b9d96a3a1a2e5f186d560859b59e07d0c47d4"
    ],
    "reduce": "lines",
    "value": "0"
  },
  "rerun": true,
  "hash": "sha256:25057a9df1039e40"
}
```

<!-- measure:v1 -->
```json
{
  "schema": "measure/v1",
  "metric": "status_head_drift",
  "value": "3",
  "units": "commits",
  "procedure": {
    "argv": [
      "git",
      "log",
      "--no-merges",
      "--invert-grep",
      "--grep=^docs(status):",
      "--format=%h",
      "793b9d96a3a1a2e5f186d560859b59e07d0c47d4..f65f7eaddfcf96fd3c3f92235f41f615864de6af"
    ],
    "reduce": "lines"
  },
  "against_sha": "e83422c25e8e61a8819f41e8b14a79bb2b6da9e3",
  "declared_paths": [],
  "history": true,
  "who": "code-s302",
  "when": "2026-09-15T10:15:37Z",
  "predicate": "value == 3",
  "pass": true,
  "control": {
    "argv": [
      "git",
      "log",
      "--no-merges",
      "--invert-grep",
      "--grep=^docs(status):",
      "--format=%h",
      "793b9d96a3a1a2e5f186d560859b59e07d0c47d4..793b9d96a3a1a2e5f186d560859b59e07d0c47d4"
    ],
    "reduce": "lines",
    "value": "0"
  },
  "rerun": true,
  "hash": "sha256:18f4bda80869355a"
}
```

<!-- measure:v1 -->
```json
{
  "schema": "measure/v1",
  "metric": "status_pr_needles_absent",
  "value": "0",
  "units": "occurrences",
  "procedure": {
    "argv": [
      "git",
      "show",
      "f65f7eaddfcf96fd3c3f92235f41f615864de6af:docs/STATUS.md"
    ],
    "reduce": "count:#145[3-6]"
  },
  "against_sha": "e83422c25e8e61a8819f41e8b14a79bb2b6da9e3",
  "declared_paths": [],
  "history": true,
  "who": "code-s302",
  "when": "2026-09-15T10:15:37Z",
  "predicate": "value == 0",
  "pass": true,
  "control": {
    "argv": [
      "git",
      "show",
      "f65f7eaddfcf96fd3c3f92235f41f615864de6af:docs/STATUS.md"
    ],
    "reduce": "count:#1445",
    "value": "5"
  },
  "rerun": true,
  "hash": "sha256:2948eb7b4ebeac6e"
}
```

<!-- measure:v1 -->
```json
{
  "schema": "measure/v1",
  "metric": "status_pr_needles_present",
  "value": "18",
  "units": "occurrences",
  "procedure": {
    "argv": [
      "git",
      "show",
      "f65f7eaddfcf96fd3c3f92235f41f615864de6af:docs/STATUS.md"
    ],
    "reduce": "count:#(1449|1450|1451|1452)"
  },
  "against_sha": "e83422c25e8e61a8819f41e8b14a79bb2b6da9e3",
  "declared_paths": [],
  "history": true,
  "who": "code-s302",
  "when": "2026-09-15T10:15:37Z",
  "predicate": "value == 18",
  "pass": true,
  "control": {
    "argv": [
      "git",
      "show",
      "f65f7eaddfcf96fd3c3f92235f41f615864de6af:docs/STATUS.md"
    ],
    "reduce": "count:#1445",
    "value": "5"
  },
  "rerun": true,
  "hash": "sha256:b1ab25a694da57d7"
}
```

<!-- measure:v1 -->
```json
{
  "schema": "measure/v1",
  "metric": "status_bytes",
  "value": "58401",
  "units": "bytes",
  "procedure": {
    "argv": [
      "git",
      "show",
      "f65f7eaddfcf96fd3c3f92235f41f615864de6af:docs/STATUS.md"
    ],
    "reduce": "bytes"
  },
  "against_sha": "e83422c25e8e61a8819f41e8b14a79bb2b6da9e3",
  "declared_paths": [],
  "history": true,
  "who": "code-s302",
  "when": "2026-09-15T10:15:37Z",
  "predicate": "value == 58401",
  "pass": true,
  "control": {
    "argv": [
      "git",
      "show",
      "f65f7eaddfcf96fd3c3f92235f41f615864de6af:docs/plans/0000-template.md"
    ],
    "reduce": "bytes",
    "value": "390"
  },
  "rerun": true,
  "hash": "sha256:5ccd9e336579d9b2"
}
```

<!-- measure:v1 -->
```json
{
  "schema": "measure/v1",
  "metric": "template_measure_tokens",
  "value": "0",
  "units": "occurrences",
  "procedure": {
    "file": "docs/plans/0000-template.md",
    "reduce": "count:measure"
  },
  "against_sha": "e83422c25e8e61a8819f41e8b14a79bb2b6da9e3",
  "declared_paths": [
    "docs/plans/0000-template.md"
  ],
  "history": false,
  "who": "code-s302",
  "when": "2026-09-15T10:15:37Z",
  "predicate": "value == 0",
  "pass": true,
  "control": {
    "file": "docs/plans/0000-template.md",
    "reduce": "count:Goal",
    "value": "1"
  },
  "rerun": true,
  "hash": "sha256:1ad2e01bd2ec20db"
}
```
