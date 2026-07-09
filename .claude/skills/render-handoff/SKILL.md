---
name: render-handoff
description: Generate a Code-session orientation handoff — the cross-session baton pass that lets the NEXT Code session resume with minimal context loss. Compacts the current session (what landed, verification state, decisions, failed attempts, open questions, next concrete steps) into a schema-conformant, validator-passing handoff under .claude/handoffs/session-NN/, following the real session-100..115 orientation shape. Use when closing or pausing a Code session, when Cray says "ทำ handoff / ปิด session / พัก session / close session / จบ session", or before a context reset (/clear, /compact) when work must continue in a fresh session. It is a SKILL, not a subagent, by design — it reads the live session transcript inline (a subagent's isolated context cannot see the session). Ends by announcing the handoff path for Cray to point the next session at.
model: fable
effort: xhigh
---

# render-handoff — Code-session orientation handoff generator

A task-triggered procedure (Tier 2.6). It turns "the session that just
happened" into a **compacted, resumable baton pass** for the next Code session —
not a transcript dump. The next session starts with a fresh context window and
**startup does NOT auto-read handoffs** (CLAUDE.md §9 reads CLAUDE.md → STATUS →
adr → plans only); Cray points the new session at this file, so it must stand
alone.

**Why a skill, not a subagent** (design fact — do not "fix" this): a subagent
runs in an isolated context window and cannot see this session's transcript,
which is the whole input. A skill runs inline and sees it. Never add
`context: fork` to this skill — fork makes it isolated like a subagent.

**Producer/consumer pair:** this skill is the *producer* (writes the handoff at
session close); `next-work-analyst` is the *consumer* (reads it at the next
session's start and re-verifies against code).

**Output contract:** one file under `.claude/handoffs/session-NN/`, schema-valid
(passes `tools/handoffs/validate_handoff.py`), following the orientation shape
below, ending with the path announced back to Cray. Handoffs are **gitignored
working notes** — never committed.

## Core rules (from 2025–26 handoff research + vero-lite conventions)

- **Compact, don't dump.** Ship the resumable core; prune redundant tool output.
  "Maximize recall first, then precision."
- **Reference, don't copy.** Point to ADR / PLAN / PR / commit / file:line — never
  duplicate what the repo already holds (repository = single source of truth).
- **Generate at end-of-session**, never mid-flight-and-forget (stale handoffs are
  the #1 failure mode). Stamp the real time.
- **Structured Markdown**, bullets/tables over prose.
- **Strip secrets** — no keys/tokens/PII in the file.
- **Only when worth it** — skip if the session was trivial (reconstruction < ~10 min).
- The "onboarding a new teammate" test: if a competent stranger couldn't resume
  from it, it's incomplete.

## Step 1 — Gather state (from the live session + fresh git evidence)

Pull, don't guess. Run git via `wsl bash -lc` + `source .venv/bin/activate`:

- **Fresh git facts:** `main` SHA (`git rev-parse --short main`), tree status
  (`git status --short`), open-PR count (`gh pr list --state open`).
- **What landed this session:** merged PRs + substantive SHAs → `references_commits`.
- **Verification / evidence state:** what was verified and how; live-run / host-state
  evidence paths (e.g. `docs/logs/…`); which checks are green.
- **Decisions made + the why** (so they aren't relitigated).
- **Failed attempts / dead ends + why they failed** (the highest-value, most-often-
  omitted section — saves the next session a repeat detour).
- **Open questions / blockers** (pending Cray decisions).
- **Next concrete steps** (the single unambiguous first action, then the rest).
- **Session number:** `session:` in `docs/STATUS.md` frontmatter.
- **Predecessor handoff:** newest file in the latest `.claude/handoffs/session-NN/`.

## Step 2 — Compose frontmatter (schema: `docs/conventions/handoff-frontmatter-schema.md`)

Required fields, all present, `actor: code` (→ filename must start `…-code-`):

```yaml
---
from: code-session-NN
to: code
actor: code
session: NN                 # int
batch: "Session-NN (YYYY-MM-DD) — <rich one-paragraph what-happened summary>"
phase: closeout
status: DONE                # DONE at CLOSE; PAUSED if work halts mid-flight to resume
created: YYYY-MM-DDTHH:MM:SS+07:00   # ISO8601 WITH timezone — validator rejects naive
title: "Code session-NN <CLOSE|PAUSE> — <what completed>. main=<SHA>, <N> open PRs. NEXT: <candidates>."
references_commits: [<shortSHA>, ...]
references_predecessor_handoffs:
  - session-<NN-1>/<predecessor-filename>.md
---
```

Get the timestamp from the shell: `wsl bash -lc "date '+%Y-%m-%dT%H:%M:%S+07:00'"`.

## Step 3 — Filename + path

`.claude/handoffs/session-NN/<YYYY-MM-DD>-<HHMM>-code-sessionNN-<CLOSE|PAUSE>-<planref>-<STATE>.md`

- `mkdir -p` the `session-NN/` dir if new. HHMM matches `created` (+07:00).
- The ALL-CAPS state slug (`CLOSE`/`PAUSE` + `<planref>` + `COMPLETE`/`READY`/…) is a
  de-facto convention (sessions 100–115); keep it — it telegraphs state at a glance.
- Prefix `code-` is enforced against `actor: code` by the validator.

## Step 4 — Body (orientation shape; model on the real session-115 handoff)

1. `> **Orientation.**` — ONE paragraph: what happened + **State** (`main` SHA, open-PR
   count, tree) + standing flags (e.g. `loop-dispatcher` state, MS-S1 warm/idle) +
   literal **`FIRST, sync: cd ~/work/vero-lite && git checkout main && git pull --ff-only origin main`**
   + "run git/tests via `wsl bash -lc` + `source .venv/bin/activate`".
2. `## 1. What landed` — PR table: `| PR | SHA | What |`.
3. `## 2. Verification / evidence state` — what was verified, evidence paths, green checks.
4. `## 3. Failed attempts / what to avoid` — dead ends + why (skip only if genuinely none).
5. `## 4. How to verify / resume` — health-check/test commands + the evidence-based
   definition-of-done (ties to §6 "Verification is hygiene" + the pre-committed pass/fail read).
6. `## 5. Open questions / blockers` — pending Cray decisions (omit if none).
7. `## 6. NEXT` — execute steps; first action unambiguous; reference the PLAN/ADR by path.
8. `## 7. Standing flags / mechanics for the next session` — branch-protection, scheduled
   tasks, §7 commit/PR mechanics, "handoffs are gitignored — never commit", live defaults.
9. Authorship footer: `*Authored by Code (session NN close, <ts>). State verified vs main <SHA>.
   AI-assisted (Claude Code); no Co-Authored-By per §7.*`

Keep every section compact and pointer-based. §3/§4 are the two research-backed
additions over older handoffs — include them.

## Step 5 — Dog-food the validator (MANDATORY — Lesson #8 anti-pattern: never skip)

```bash
wsl bash -lc "cd /home/crayj/work/vero-lite && source .venv/bin/activate && \
  uv run python tools/handoffs/validate_handoff.py .claude/handoffs/session-NN/<file>.md"
```

Exit 0 = valid. On error (missing/empty required field, bad enum, naive `created`,
filename↔`actor:` mismatch) fix and re-run until clean. Warnings (unknown field,
suffix-not-in-filename) don't block. Optionally refresh the dashboard:
`uv run python tools/handoffs/handoff_status.py NN --index`.

## Step 6 — Announce

Reply with the **exact handoff path** so Cray can point the next session at it
(startup won't find it automatically). Remind: it's a gitignored working note —
**do not commit**. If deep transcript detail is needed to reconstruct, note that
`tools/handoffs/render_transcript.py --latest --last N` can render the raw session,
but prefer the compacted synthesis you already hold in context.

---

*Sources: canonical schema `docs/conventions/handoff-frontmatter-schema.md`;
real template `.claude/handoffs/session-115/…-CLOSE-plan0060-COMPLETE.md`; K-1/K-2
+ dog-food discipline `docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`; handoff
anatomy research `docs/research/private/2026-07-09-handoff-skill-research.md`
(Anthropic context-engineering 2025-09-29 + practitioner consensus 2026).*
