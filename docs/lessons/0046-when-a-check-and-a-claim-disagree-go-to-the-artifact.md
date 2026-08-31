# Lesson #0046 — when a check and a claim disagree, go to the artifact

**Session:** 241 (2026-08-20→21) · **Measured on:** five incidents in one
session, six PRs, two new pre-commit guards · **Status:** advisory (§1
precedence — promote to ADR if it must bind)

## The claim

Every failure in this session had the same shape: **a check and a claim
disagreed, and the cheap move was to decide which one was wrong from the
armchair.** In five incidents the armchair answer was wrong three times in one
direction and twice in the other. Nothing but going to the artifact separated
them.

The dangerous corollary: **"the check is wrong" and "the artifact is wrong" are
both plausible every time**, so a habit that always reaches for one of them is
wrong roughly half the time while feeling consistent.

## What happened — five incidents, both directions

| # | The check said | The armchair answer | What measuring found |
|---|---|---|---|
| 1 | the new guard **blocked its own first commit** | "false positive, exempt the file" | 🔴 the **guard was right** — `_OWN_MACHINERY` was "cannot declare **but is still searched**", which is incoherent: a file that cannot declare cannot exempt its own examples either. Fixed with `Marker.local_only` |
| 2 | the guard flagged **`docs/STATUS.md`'s own narrative** for quoting a dead claim | "narrow the retired string until the quote stops matching" | 🔴 that is **editing the artifact to satisfy the instrument.** The marker went beside the quote instead — which bought the property actually wanted: on the surface an agent reads every session, a dead claim now carries a label saying so |
| 3 | a synthesis cited **five** grounding agents | "I dispatched five, so I have five" | 🔴 **four returned.** The fifth failed silently; two rows of a ranked recommendation were written with **no source** and retracted on measurement |
| 4 | three pre-write assertions **failed** (`ceiling: true` count, a case-sensitive needle, a needle straddling `**`) | "the artifact drifted" | ✅ the **artifact was right all three times** — the instrument was imprecise. All three failed **safe**, because the assertion ran before the write |
| 5 | a subagent reported it had **removed** two notes from STATUS | "the report describes the edit" | 🔴 **both notes were still there.** An archive note written from that report claimed they no longer appeared live — a false claim, into a tracked file, caught only by an absence check run *after* the append |

Three of the five (1, 3, 5) were **mine**, not inherited. Incident 4 is the only
one where the instinct to distrust the check would have been correct — and it
is also the only one that cost nothing, because the check ran before the write.

## The test

When a check and a claim disagree, **do not decide which to correct by which is
cheaper to change.** Read the artifact, then ask in this order:

1. **Is the check reporting a real property of the artifact?** Read the flagged
   line itself, not a summary of it. Incident 1's guard was reporting exactly
   what its own rules implied; the rules were the defect.
2. **If the check is right, does the fix change the artifact or the rule?**
   Narrowing a matcher until it stops matching is a fix to *the instrument's
   reach*, not to the thing it found. That is legitimate only when the reach was
   wrong on its own terms — never because the report was inconvenient.
3. **If the check is wrong, is it wrong about the artifact or about itself?**
   Incident 4's needles were wrong about themselves — case, punctuation,
   markdown emphasis inside a phrase. Fixing the needle is right; changing the
   file to match a bad needle is incident 2 in disguise.

### Two mechanical rules that made the difference

**Write the assertion before the action, not after.** Incidents 1, 2 and 4 were
all caught by a check that existed before the thing it was checking. Incident 5
was caught only *after* a bad write had already landed — by an absence check
that happened to be in the same script. Post-hoc verification finds the error
after it is in the file; a pre-committed assertion refuses to create it.

*Concretely, for a two-file move:* pin each slice by its expected **first AND
last** text, assert no neighbour-bleed, and check **presence-in-target and
absence-from-source separately** — never infer one from the other. That battery
aborted a rotation this session with both files untouched.

**Count the returns before you synthesise.** Before writing anything that
aggregates subagent results, list the agents dispatched and tick each one's
return. Four-of-five is not five, and a missing notification does not announce
itself. This rule already existed and did not fire, because it had no *moment of
application* — this sentence is the moment.

### The prevention half: choose a needle that formatting cannot break

*Added session 264, on three more incidents — all in one session, all the same
shape, all instrument-side.* The rule above says what to do **after** a check and
a claim disagree. This one keeps the disagreement from being manufactured.

Every one of the three was a verification `grep` reporting **zero hits on content
that was present**:

| needle used | what the artifact actually held |
|---|---|
| `Cray-ratified` | the document said `ratified` — the attribution lived in the code and commit, not the prose |
| `0-1` | an **en-dash**: `0–1` |
| `ontology move before it is a grader move` | markdown emphasis split it: `an **ontology** move before …` |

None was a defect in the artifact; all three were defects in the needle. A false
alarm costs the same as a false pass — both send you to re-check the wrong thing,
and the third one nearly had a merged PR reported as content-incomplete.

**So: pick needles that are ASCII-only, free of markdown emphasis, and short
enough not to straddle a wrap.** Prefer a stable identifier (`session: 264`,
`def role_vocabulary`) over a prose phrase. When a probe *must* quote prose, quote
the fragment least likely to carry markup, and treat a zero-hit result on content
you believe is present as a **needle** hypothesis first.

**The same class, one layer down: content built through a shell loses backticks
before it is ever compared.** Also session 264, four times — a PR body (recovered
via `gh api PATCH`), and three scripts written by heredoc. The worst was a probe
battery whose pinned first line arrived on disk as `( )`; the mutation matched
zero times and the driver correctly refused to credit it. A corrupted PR body is
cosmetic. A corrupted **needle** is a verification that silently proves nothing.
Build any content containing backticks with the Write tool — Lesson #11 states
this for PR bodies; it holds for scripts and battery files too.

## What this does NOT say

- It does not say check-failures are usually right. Incident 4 says the
  opposite, twice over.
- It does not license slowing every check down. The whole battery above is one
  script, written once, reused four times in this session.
- It says nothing about *whether a claim is true* — only about how to resolve a
  disagreement between two statements of it.

## Where this fires

`docs/lessons/` is advisory, and ADR-0038 measured that this repo obeys
mechanical rules almost perfectly and advisory ones poorly. So the two
operational halves are pushed into the surfaces that load at the moment of need,
and this file is the record rather than the delivery mechanism:

- **the count-the-returns rule** → `.claude/skills/fan-out-dispatch/` (loads
  when spawning parallel agents)
- **the instrument-vs-subject test and the pre-committed assertion battery** →
  `.claude/skills/code-operational-policy/` (loads when verifying, closing an AC,
  or planning multi-step work)

## References

- The two guards this session built, whose docstrings carry incidents 1 and 2 at
  source: `tools/check_retired_claims.py`, `tools/check_ac_consistency.py`.
- `docs/conventions/retired-claims.md` — where incident 2's resolution became a
  standing convention.
- Lesson #0026 (pre-committed pass/fail read), #0043 (a probe's RED must name
  what broke), #0042 (a remembered baseline is not evidence) — the same family,
  from the claim side rather than the check side.
- `CLAUDE.md` §6 "Verification is hygiene, not a verdict" — incident 4's
  `confirmed — prior intact` outcome is that rule, applied to the reviewer's own
  error rather than the author's.
