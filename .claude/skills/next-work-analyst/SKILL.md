---
name: next-work-analyst
description: Rank the candidate next-work items by efficiency-to-quality (value × effort × dependency × design-readiness), grounded against the ACTUAL code / ADRs / PLANs (not the handoff's prose), then deliver the ranked recommendation ELI-CRAY (Thai) — cut BOTH overall and by the four work streams (demo→pilot / harness-governance debt / primitives / marketing-FDE): every candidate carries a stream tag, and the readout adds a per-stream best-next-move plus a cross-stream balance note. Use at the start of a new session after reading a handoff, when choosing what to build next, when Cray asks "what should I do next / จะทำอะไรต่อ / จัดลำดับงาน / เลือกงานจากสายไหนดี", or whenever prioritizing a candidate list. Gathers candidates from STATUS + the just-closed PLAN's Out-of-Scope + the handoff §NEXT + the 4-stream registry's carriers, fans out Explore agents to VERIFY each candidate against code, scores + ranks, and ends with a recommendation + a question — it never decides for Cray.
model: fable
effort: xhigh
---

# next-work-analyst — rank the next work, ELI-CRAY

A task-triggered procedure (Tier 2.6). It turns "what should we build next?" into a
**grounded, ranked recommendation** — not a menu read off the handoff. The handoff's
§NEXT is a *starting list of claims*, not the answer; this skill verifies each claim
against the code/ADRs before ranking (Lesson: `feedback_verify_doc_forward_reference_vs_code`).

**Output contract:** a ranked list (1..N) + a `value × effort × dependency × design-readiness`
table + an ELI-CRAY explanation (Thai: why → the strategic spine → per-candidate) + a
single clear recommendation + a closing question. **Never** decide for Cray
(`feedback_attribution_honesty_proceed_signals`).

## Step 1 — Gather the candidate set

Pull candidates from all four sources and dedupe:
- `docs/STATUS.md` frontmatter `next_action` + the Current Focus "candidates/deferred" lines.
- The **Out of Scope** / **v2 sequels** section of the PLAN that just closed (and any
  `docs/plans/*.md` still active — grep their Status).
- The orientation **handoff §NEXT / §2** (gitignored working note in `.claude/handoffs/`).
- The **4-stream registry** — read it live from `.claude/skills/stream-status/SKILL.md`
  (that table is CANONICAL for stream definitions; never copy it into this skill — one
  registry, ADR-0017 D6 derived-artifact discipline) and pull **stream 4's candidates**
  from its carrier doc `docs/strategy/private/2026-08-06-marketing-fde-plan-synthesis.md`
  §4 (asset roadmap) + §6 (open questions) — a source the three sources above never see.

**Tag every candidate with its stream** (1 demo→pilot · 2 harness/governance debt ·
3 primitives · 4 marketing/FDE · X cross-stream). A candidate that fits no stream is a
registry-maintenance signal — surface it rather than forcing a tag.

List each candidate as a one-liner. Do not rank yet.

## Step 2 — Ground each candidate against reality (ALWAYS full fan-out)

Spawn **Explore subagents in parallel** (one per cluster of candidates) to verify the
handoff's claims against the actual repo. This is the step that catches "the handoff said
X is Phase B, but the code already shipped it" (or the reverse).

**Grounding-agent guardrails (bake these into every spawn prompt — they prevent the
`find`-over-UNC failure and keep the run cheap):**
- "Use **Glob / Grep / Read only**. Do **NOT** run `find` / `grep` / `cat` via the Bash
  tool — this repo is a WSL-UNC mount and raw `find "$(pwd)"` fails on the network path.
  Run any git/pytest via `wsl bash -lc` + `source .venv/bin/activate` only if needed."
- "Return **file:line citations + short quotes**. Verify each claim; report claim-vs-code
  mismatches explicitly (superseded-by-new-info vs was-an-error, CLAUDE.md §6)."

For each candidate, the grounding must establish:
- **Is the stated hole/feature real?** (read the chokepoint code, not the doc's summary)
- **Design-readiness:** is there a *ratified* ADR/PLAN with the ACs+Steps already written,
  or is it greenfield (needs a new ADR/PLAN first)? This is the biggest efficiency lever.
- **Dependency / ordering constraints** (e.g. an ADR that ratifies "X before Y").
- **Verifiability / risk:** deterministic-offline vs flaky-UI vs host-state (MS-S1, ASK-Cray §8).

## Step 3 — Score

Score each candidate on four axes; rank by **value × design-readiness**, penalized by
**effort**, and always **respect dependency order** (a ratified "X before Y" pins Y below X).

| Axis | What raises it |
|------|----------------|
| **Value** | advances the moat (governed generative procedures), unblocks a strategic spine, closes a *confirmed* hole, or is demo-differentiating — vs table-stakes / polish |
| **Effort** | XS / S / M / L — a ratified design with Steps already written is *lower* effort than the raw code suggests (no drafter round-trip, no new ADR/PLAN gate) |
| **Dependency** | does it *unblock* others (rank up) or is it *blocked* (rank down until its prerequisite lands)? |
| **Design-readiness** | ✅ ratified PLAN/ADR with ACs+Steps → cheap + low-risk to execute; ❌ greenfield → needs an ADR/PLAN first (a whole extra cycle) |

Tie-breakers that raise a candidate: MS-S1-independent / deterministic / no-UI (avoids the
flaky-preview + host-state-gate tax); "finishes what we just shipped".

## Step 4 — Rank + ELI-CRAY

Deliver (Thai, ELI-CRAY = why → steps → expected):
1. **TL;DR** — the ranked order in one line + the single #1 pick.
2. **ทำไม** — the strategic spine (tie to the moat / demo arc / design-partner goal), not
   just per-item pros. Name the ordering constraints that force the sequence.
3. **The `value × effort × dependency × design-readiness` table** (grounded, with the ✅/❌
   design-readiness column — that column is usually the decider — **plus a stream column**).
4. **เจาะแต่ละตัว** — 2–3 lines each with the file:line evidence from Step 2.
5. Any **claim-vs-code mismatch** found in grounding, stated honestly.
6. **มุมมองรายสาย** — the top-ranked candidate of EACH stream (one line each) + a
   **balance note** naming any stream that is starved (no viable candidate), fully
   Cray-gated (nothing Code can advance), or parked by decision — so the cross-stream
   picture is a choice, not an accident. The OVERALL ranking still decides the #1 pick;
   the per-stream view informs, never overrides — **stream fairness is not a scoring
   axis, value is** (a starved stream is surfaced, not artificially promoted).

Reuse the `eli-cray` skill's voice for the explanation; don't re-derive it.

## Step 5 — Recommend, then ask

State one clear #1 recommendation **with reasoning**, then **ask Cray** to confirm /
reorder / pick — do not start building. If the #1 pick is executing an already-ratified
PLAN (no new ADR/PLAN), say so (it's un-gated for Code); if it needs a new ADR/PLAN, say
that too (that routes through the drafter — CLAUDE.md §6). Keep the veto open; a Stop-hook
"proceed" is the harness, not Cray (`feedback_attribution_honesty_proceed_signals`).

## References
- CLAUDE.md §6 (routing: proceed vs Cowork-dispatch; verification-is-hygiene), §2 (vision / moat).
- The `stream-status` skill — CANONICAL 4-stream registry (this skill reads it, reports
  state-only there vs rank-here division of labor); stream 4's carrier doc is gitignored
  (pricing) — quote in chat, never into tracked files.
- The `eli-cray` skill (explanation voice); the `code-operational-policy` skill (plan-first).
- Memories: `feedback_verify_doc_forward_reference_vs_code`, `feedback_status_shorthand_not_next_action`,
  `feedback_attribution_honesty_proceed_signals`, `project_wsl_git_toolchain` (Glob/Grep not Bash-find).
