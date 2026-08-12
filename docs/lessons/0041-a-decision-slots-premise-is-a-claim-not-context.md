# Lesson #0041 — A decision slot's premise is a claim to measure, not context to inherit; and a true adjacent observation can launder a false one

**Date:** 2026-08-12 (session 224)
**Class:** advisory (governance-artifact hygiene / decision-slot design)
**Trigger:** Ruling PLAN-0103 **SD-8**
([#1135](https://github.com/CrayJThiemsert/vero-lite/pull/1135)). The slot had
stood unruled for four sessions as a three-way UI judgement. Running the surface
it described took about ten minutes and found its **factual premise was false —
and had been false when the slot was authored**.

## The lesson

A decision slot has two parts: a **premise** (what is true today) and **options**
(what to do about it). The options get scrutiny by construction — weighing them
*is* the decision. The premise gets none: it reads as context, and context reads
as settled.

**But every option inherits the premise's truth.** When SD-8's premise fell, two
of its three options fell with it — one described a state that did not exist, and
one quoted a cost that had already been paid. Four sessions of careful reasoning
about the options could not have found that, because the options were internally
coherent. Only measuring the premise could.

**Second half, and the sharper one: a true observation about an adjacent fact can
launder a false premise.** Session 222 added a "live input" note to this slot
recording that procurement was now live with `^/whoami$` refused at its edge —
**entirely true** — and characterised that as *"the shipped state — option (i) —
is now the live public surface."* The observation was real, freshly made, and
correctly cited. It carried the false premise forward under its own credibility.
A wrong claim adjacent to a verified one is the hardest kind to see.

## 1. What was actually wrong

SD-8 asked whether Tab G's "Act" card *"should render at all on a personaless
system"*, and stated as fact that it *"still renders a login form on a system
that will always refuse the login."*

Measured against a local reproduction of procurement's own committed
`published.env`: **the card renders on no published profile at all.** Zero
`input` elements of any type on either published tab; the string *"Act — the
human DOA gate"* absent from the DOM.

The mechanism is two facts in one file that compose:

* the Act card renders only in event mode (`view-hero.js:655`), and `mount()`
  defaults to manual (`:662`);
* the only control that reaches event mode is suppressed on every published
  profile (`:604-614`, `if (!published)`).

## 2. The falsifier was a different decision, made for an unrelated reason

The suppression was **PLAN-0100 Step 3**, and the code comment states why: event
mode fires `POST /demo/hero/event` — *the unauthenticated DB write D5(2)
excludes.*

That is a **data-write** decision. Its UI consequence — that the Act card, and
with it the login form, disappears from every published surface — was never
recorded anywhere, because it was not what that decision was about. The `if
(!published)` branch sits fifty lines from `renderActPanel` and mentions neither
the card nor personas.

So a security decision silently answered a UI question that a later slot would
spend four sessions asking. **The two artifacts have no link in either
direction.**

This is the same shape the `excision-scope` skill is about — walking a change's
call graph only *backwards* from the thing you touched, and never *forwards* into
what your change decides for someone else. Here it is not dead code, it is a dead
*question*.

## 3. Why the usual remedies do not reach this

* **Re-reading the slot does not re-check it.** The slot was carried forward
  three times — s221 added an input, s222 added the live-input note, s223 carried
  it into a handoff. Each pass transcribed the premise. **Transcription is not
  verification**, and a slot that has been "reviewed" three times feels more
  settled, not less.
* **Doc-vs-code drift checks target citations.** This project catches those well
  (four in this PLAN alone). But the premise had **no citation to check** — it
  was a claim about *rendered behaviour*, and nothing in the repo asserts what
  the published profile renders. A claim with no citation is invisible to a
  citation audit.
* **Reviewing the options finds nothing**, per the lesson above.
* **The freshest evidence made it worse.** See the s222 laundering above. The
  more recent and better-grounded the adjacent observation, the more authority it
  lends the premise riding beside it.

## 4. Operational form

1. **Mark the premise as a claim.** When a slot asserts something about
   observable behaviour, that sentence is a *finding*, not framing — it needs the
   same treatment as any claim: measured, cited, and dated.
2. **Measure before weighing.** If the premise is observable in under an hour,
   observe it. Ten minutes here retired two of three options and changed what the
   ruling meant. (This is
   [[0026-interpret-before-run-pre-commit-outcome-meaning]] pointed at a
   governance artifact rather than a benchmark.)
3. **Cost clauses inside options are claims too.** *"…at the cost of a new
   published-profile UI branch"* was false: the branch already existed, paid for
   by an unrelated decision. A price nobody re-checked distorts the comparison
   between options as much as a wrong premise does.
4. **When a decision changes behaviour for reason X, ask what else that change
   decides.** Not "what did I break" — "what question did I just answer for
   someone who does not know I answered it."
5. **Separate a true adjacent observation from the claim it sits beside.** When
   adding fresh evidence to an existing slot, state explicitly which part of the
   existing text it confirms and which part it does not touch. Silence reads as
   endorsement.

## 5. Scope

This does **not** mean doubting every settled decision — CLAUDE.md §6
("Verification is hygiene, not a verdict") still governs, including its tripwire:
citing that principle as a reason *not* to check is misapplying it. This lesson
lives on the other side of that line. It is about a check that was **never run**,
on a **claim** rather than a decision, so
[[0027-verify-not-indictment-refute-claim-not-decision]]'s claim-refutation
branch applies in full — adversarial, no deference.

It also does not mean every slot needs a measurement. It means the premise should
be **known** to be unmeasured rather than assumed true, and that a slot whose
premise is cheaply observable should not be ruled on before it is observed.

The correction here is classified `was an error`, not `superseded by new info`:
the suppression predates the slot's authoring, so the claim was wrong when
written rather than overtaken later. That distinction is worth preserving — it is
the difference between a record that evolved and a record that was never right.

Related: [[0026-interpret-before-run-pre-commit-outcome-meaning]] (know what an
outcome will mean before you run — same discipline, applied earlier);
[[0027-verify-not-indictment-refute-claim-not-decision]] (claim vs decision);
[[0035-negative-measurement-needs-a-positive-control]] (a measured absence needs a
control); [[0040-a-probe-proves-one-direction-only]] (an assertion is only as
strong as the mutation shown to break it — this is the same idea one layer out,
where the "assertion" is a sentence in a governance doc and there is no mutation
at all). The `excision-scope` skill covers the forwards-call-graph half of §2.
Worked record: PLAN-0103 §Surfaced decisions, SD-8 — read the slot, which carries
all four corrections inline.

*AI-assisted (Claude Code, session 224); no `Co-Authored-By` per CLAUDE.md §7.*
