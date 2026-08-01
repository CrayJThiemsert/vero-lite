# Lesson #0034 — A deliberate gate recorded outside the scanned surface is indistinguishable from an oversight

**Date:** 2026-08-01 (session 199; the item had been in this state since s177)
**Class:** advisory (knowledge placement / backlog hygiene)
**Trigger:** Cray asked why the MS-S1 hosting ADR "ไม่แสดงอยู่ใน backlogs เลย"
after a `next-work-analyst` run. It was not missing — it was correctly withheld,
by a gate whose existence was recorded only on surfaces a backlog scan does not
read. Proving that took a grounding sweep; the answer changed no code and fixed
no defect. Closed by [#1009](https://github.com/CrayJThiemsert/vero-lite/pull/1009).

## The lesson

**When you decide *not* to act, and the decision outlives the session, record the
gate in the surface where the item would otherwise be looked for.** Rationale can
live anywhere. The *existence of the gate* cannot: an item absent from the list a
reader scans is read as forgotten, and the only way to learn otherwise is to go
and prove a negative.

A correct omission and a lapse produce the same observable — nothing. The
difference is legible only if the gate is written where the absence is noticed.

## The incident, measured

The MS-S1 hosting ADR was tracked. `docs/STATUS.md` carried it as a bullet under
`## In-Flight Discussions`. Enumerating every `- [ ]` row under `## Active TODOs`
returned **18 rows, none of them this one**.

The clean measurement came from a set the s183 handoff had already defined. It
named **five** items as trigger-gated with their triggers unfired — F-FACTORY,
the `candidate_quotes` O-2 residue, OQ-4, the custom Postgres image, and the
hosting ADR. **Four of the five were Active TODOs. This was the only one that was
not.** A shared status with an unshared location is the tell, and it converts a
vague "should this be here?" into a finding in one grep.

Three compounding factors, each individually reasonable:

1. **The gate's definition lived in an archived PLAN.** `PLAN-0095` §OQ-1 states
   the tripwire precisely — it fires when someone writes deployment configuration
   for a *specific* hosting model (exposure beyond the LAN, tenancy, TLS/authn
   posture, or pointing a deployed image at an off-LAN LLM endpoint). Correct
   content, in `docs/plans/done/`.
2. **The "do not pick this up" instruction lived in a gitignored handoff.**
   s183's handoff says it plainly. `.claude/handoffs/` is not in the repo, so it
   is not a surface any scan — or any future session that did not read that exact
   file — can reach.
3. **The surface that *did* carry the item described it in words that contradicted
   the gate.** The bullet opened "a **LIVE candidate** needing its own ADR
   (surfaced s176, **still not drafted**)". Read alone, that is a call to action.
   Nothing adjacent to it said the trigger had not fired.

So the reader had a to-do-shaped sentence in a discussion-shaped section, with the
reconciling fact in two places they could not see.

## Why this is not Lesson #0024

[[0024-rules-must-live-where-the-enforcer-looks]] is the sibling, and the
distinction matters when applying either.

| | #0024 | this lesson |
|---|---|---|
| What is misplaced | a rule that must be **enforced** | a decision **not to act** |
| Who cannot see it | the **enforcer** (classifier, hook) | the **reader / ranker** (a human, a backlog scan) |
| Failure mode | the rule is silently not enforced — a wrong **action** | the decision is silently re-opened — wasted **doubt** |
| Cost | an action that should have been blocked | human time spent proving a non-bug |

#0024 says: put an enforced rule in the enforcer's input. This one says: put a
withheld decision in the reader's input. Both reduce to *place knowledge where the
consumer actually looks*, which is ADR-0017 D5's routing rule — but D5 routes by
**who reads it and when**, and neither of these questions is answered by that
alone. #0024 added "what enforces it?"; this adds **"where would someone look for
it if they thought it was missing?"**

## The rule

1. **A deliberate non-action gets the same recording discipline as an action.**
   "We decided not to do X yet" is a decision with a home, not an absence.
2. **The gate goes in the list, not in the narrative.** For backlog items in this
   repo that means `## Active TODOs`, with the trigger stated inline and marked
   unfired. The house precedent is the OQ-4 row: an Active TODO carrying its own
   dated criterion and closing with *"Not due yet — premature re-measure burns the
   pre-commitment on an under-powered sample."* Copy that shape.
3. **Never let an item's wording and its gate disagree.** If the row says "LIVE
   candidate, still not drafted" while the record says "do not pick up", the row
   is wrong regardless of which one reflects intent.
4. **Gitignored handoffs and archived PLANs are legitimate homes for the
   *rationale*, never for the *gate's existence*.** This is #0024's "prose homes
   keep the how-to and rationale" applied to decisions instead of rules.
5. **When a PLAN archives with an open OQ, the OQ's home is an Active TODO row
   that names its trigger** — not an In-Flight bullet, and not a pointer into
   `done/` alone.

## Detection

Cheap and mechanical, worth running when a set of items shares a status:

- **Do they share a location?** Group by status, group by section, compare. A
  4-of-5 split is a finding; it took one grep here.
- **Does any item's own wording contradict its status?** Grep the list for
  action-shaped phrasing ("still not drafted", "needs", "LIVE") and check each
  against whether it is actually available to pick up.
- **Is the reconciling fact reachable?** If the sentence that makes an omission
  correct lives only in `.claude/handoffs/` or `docs/plans/done/`, it is not
  reachable from the list, and the list is where the question gets asked.

## A smaller adjacent hazard, recorded not fixed

`## In-Flight Discussions` has **no stated rotation rule**. Grepping
`docs/runbooks/` and `docs/conventions/` for "In-Flight" returns nothing but the
STATUS heading itself; R2's rolling window
([`memory-architecture.md`](../runbooks/memory-architecture.md) §R2) specifies
Current Focus and Recent Decisions and is silent on this section. So the section
that was holding a live commitment has an undefined lifecycle. Not fixed here —
the item was moved out of it rather than the section being given a rule — but a
future STATUS-hygiene pass should either give it one or state that it is
permanent.

## Cross-references

- [[0024-rules-must-live-where-the-enforcer-looks]] — the enforcement-side sibling
  (see the comparison table above; do not conflate them).
- [[0023-status-md-rotation]] — the rotation policy this section sits outside of.
- [[0027-verify-not-indictment-refute-claim-not-decision]] — the check that
  proved the omission correct is logged `confirmed — prior intact`; the cost
  recorded here is the *need* for the check, not its outcome.
- `docs/plans/done/0095-docker-image-boot.md` §OQ-1 — the gate's definition.
- `docs/STATUS.md` §"Active TODOs" — where the row now lives, and the OQ-4 row
  that models the shape.

*AI-assisted (Claude Code, session 199); no `Co-Authored-By` per CLAUDE.md §7.*
