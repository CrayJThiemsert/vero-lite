# s235 — the audit findings that ADR-0038 did NOT absorb

**Date:** 2026-08-17 · **Session:** 235 · **Base:** `main` at `29a95f6`
**Why this file exists:** the five-specialist audit of session 235 produced four
findings that landed in **no** ADR, **no** PLAN and **no** lesson. Until this file
they lived only in a **gitignored** session handoff — which session 235's own
retrieval measurement ranks as the *least* reliable home there is (§1 below), and
which `CLAUDE.md` §4 forbids as the home of anything that must survive.

This is a **`measure` artifact**: a dated `docs/logs/` record, not a PLAN and not a
rule. It carries no obligation on its own. Where a finding implies work, the work
is named and left unscheduled.

> **Provenance discipline.** Every figure below was **re-measured against `29a95f6`
> while writing this file**, not transcribed from the handoff. Where the fresh
> measurement disagrees with the handoff's, **both are shown and the handoff's is
> marked superseded** — the drift is small and directional, but a number copied
> forward without re-measurement is exactly the failure `CLAUDE.md` §8's
> inherited-premise rule now binds against.

---

## 1. The retrieval-reliability ranking — measured, and homed nowhere else

**Grep status:** zero hits anywhere in the repository before this file
(`retrieval.{0,30}reliab` across the tree, 2026-08-17).

Knowledge in this repo survives by **re-presentation, not location** — that is
ADR-0038's governing conclusion, and this ranking is the operational form of it.
Most reliable first:

| # | Surface | Why it ranks here |
|---|---------|-------------------|
| 1 | A hook / pre-commit guard | **Fires unasked.** No one has to remember it exists. |
| 2 | The enforcer's own input file (e.g. `.claude/autonomy-triggers.md`) | The consumer reads it by construction — `CLAUDE.md` §4's "name the rule's consumer" rule. |
| 3 | `CLAUDE.md` + the Tier-0 memory index | Always in context. |
| 4 | `docs/STATUS.md` Active TODOs | Scanned every session — **but it rotates.** |
| 5 | `docs/logs/` | Tracked, and **never rotated**. |
| 6 | `docs/plans/done/` + `docs/status-archive/` | Findable by **targeted grep**, never by scan. One tripwire there was invisible for **22 sessions**. |
| 7 | `.claude/handoffs/` and `.claude/evidence/` | **Three measured total losses. Not homes.** |

**How to use it:** it answers "where should this live?" — start at the top and take
the highest tier the fact can legitimately occupy. It does **not** license skipping
a canonical: a binding rule still belongs in `CLAUDE.md` regardless of tier 1's
reliability, because a hook that fails to fire silently drops it.

---

## 2. "Pruning" in this repo never reclaims storage — measured

**Freshly measured at `29a95f6`:**

| | bytes |
|---|---|
| `.git` | **28,939,149** |
| the whole `docs/` worktree | **18,061,092** |
| `docs/STATUS.md` revisions in the pack | **451** |

_[Handoff figures, superseded by the fresh run: `.git` 28,723,747 B, `docs/`
18,040,989 B, 450 revisions. The drift is this session's own commits; the
**relation** — `.git` larger than the entire `docs/` tree it stores — is unchanged
and is the load-bearing part.]_

**Deleting a file reclaims zero bytes — the blob is permanent.** Therefore **every
reclaim figure in this repo's governance is reader / agent context, not disk**:
R1's 64 KB ceiling, the deep-rotate numbers, the archive split trigger. R1 exists
because of the **Read tool's ~25k-token cap**, measured to bite at ~83 KB for this
repo's byte density.

🔴 **Consequence, and the reason this is written down: do not argue a rotation, a
prune or an archive split on disk grounds.** Any such argument is measurably
false. Argue it on whether a reader — human or agent — can still get through the
file.

---

## 3. `docker build` in CI — recommended, and owned by nothing

**Verified at source, 2026-08-17:** `.github/workflows/ci.yml` contains three
`docker` references and **none of them builds an image** — one comments on the
`postgres:16-alpine` service container, one is a throwaway-credential note, and
one explains that the final step reproduces *the image's dependency set* while
deliberately **not** building the image. `grep -i "docker build" docs/plans/` hits
only the archived `done/0095-docker-image-boot.md`; **PLAN-0107 has zero hits.**

**The CI audit rated it YES:** ~2–4 min cold, ~40–90 s with GHA layer cache, no new
dependencies.

🔴 **Its measured instance — why this is not hypothetical.** The prompt-log volume
shipped **root-owned**, so the published demo wrote **zero** prompt-log rows across
90+ `POST /query`, and **no offline test could see it.** This is a
three-condition-law failure of the ①-instrument kind: nothing in CI can read an
image's runtime filesystem ownership, because CI never builds the image.

⚠️ **One trap to disarm if this is ever added:**
`tests/docker/test_oracle_anti_tautology.py` bans a daemon **in the oracle** —
that is *not* a bar on a CI step. If the step is added, say so in its comment, or
the next reader will retire it on a misread.

**Status: unscheduled.** No PLAN owns it. This file does not create one.

---

## 4. The vacuity taxonomy has 11 classes; ADR-0038 promoted five

**Grep status:** the taxonomy itself has zero hits anywhere in the repository
before this file.

ADR-0038 made five classes binding. Of the remainder, two were found **LIVE** and
are **not** covered by those five:

1. **A bounded-key absence oracle** — a carrier evades every sentinel while using
   an already-allowed key. Live **by ruling**, and **already homed** at
   `tests/api/test_visitor_case_to_monitor_scenario.py`; recorded here only so the
   taxonomy is complete.
2. **An environmental-RED floor absorbing a real RED** — the floor is carried as a
   *count*, so the first genuinely new failure is absorbed into it. This is
   lesson #0043's sibling and is **already homed** at
   [`docs/lessons/0042-a-remembered-baseline-is-not-evidence.md`](../lessons/0042-a-remembered-baseline-is-not-evidence.md).

⚠️ **Correction to the handoff's framing, measured rather than relayed.** The
handoff carried both of these as unhomed alongside the taxonomy. They are not —
grep finds the environmental-RED floor in lesson #0042, lesson #0003 and the
`code-operational-policy` skill. **What is genuinely unhomed is the taxonomy as a
structure**, and that is what this section preserves.

**The one fact with no home at all: the promotion counter.** ADR-0038's three-strike
rule counts firings, and **no artifact records a count.** On the watch-list at
**two firings each**, one incident from promotion:

- **#0042** — an environmental-RED floor absorbing a real RED
- **#0043** — a probe's RED must name what broke
- **a cheap parameter change where the measured unit is wrong** (no lesson number)

🔴 **This is an ADR-0038 obligation with no owner** — the same shape as ADR-0037
D2.4, which sat ownerless for three sessions until someone walked D2's obligations
one at a time. Naming it here does not discharge it; PLAN-0108 is the natural
owner and does not currently claim it.

---

*Written session 235 (2026-08-17) as the tracked home for four findings that
otherwise existed only in a gitignored handoff. Every figure re-measured against
`29a95f6` at write time; two handoff claims were checked and corrected in place.
AI-assisted (Claude Code).*
