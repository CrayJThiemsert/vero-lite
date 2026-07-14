# Lesson #0030 — Verify the fact-pack before (and inside) the drafter; a newer ADR can resolve an older ADR's open question

**Date:** 2026-07-14 (session 130)
**Class:** advisory (dispatch hygiene / drafter rigor / ADR precedence)
**Trigger:** Building hero beat-1, Code dispatched `plan-drafter` to author ADR-0031
with **"OQ-8 (the typed AT-2 rule/criteria/DOA-tier sub-model) is unbuilt / a
precondition"** stated as a **given** in the fact-pack — inherited verbatim from
ADR-0024's Out-of-Scope line + the STATUS/handoff backlog. The drafter (bounded by
design — it trusts its dispatch fact-pack; research sweeps are upstream, see
`plan-drafter.md` point 2) built a coherent, high-quality ADR-0031 on that premise
and **rejected AT-2 generation** as "a second, far larger reversal with its
precondition (OQ-8) unbuilt." Fresh grounding — run *after* the draft came back, via
Code R2 — found the **opposite**: ADR-0025 already **decided AND built** OQ-8. The
typed `DoaLadder` / `ScoredRule` / `ComplianceGate` / `SoDConstraint` models
(`spec.py:615-752`) load and run today (the canned hero runs them). The whole
"mega-program" framing was false; AT-2 generation is an **S–M build on shipped
spec**. A load-bearing decision was very nearly made on a stale negative fact.

## The lesson — two intertwined threads

**1. The drafter is deliberately bounded — so an unverified fact-pack propagates
straight into the decision.** `plan-drafter` is `fable`, `maxTurns: 30`, and its
charter tells it *not* to grep extensively ("research sweeps are upstream —
`explore-research`'s job"). It trusts the dispatch. That is by design and it is
*fine* — **as long as the fact-pack was verified before the spawn.** The OQ-8 miss
was not the drafter being sloppy (it actually caught a *harder* thing — the AC-A8 /
AT-1-only impossibility — on its own). It was a **chain break**: Code fed an
unverified negative claim as a given and skipped the upstream `explore-research`
grounding the architecture intends. The primary fix is **upstream (Code dispatch
hygiene)**, with a drafter-side backstop.

**2. "Newest ADR wins" (CLAUDE.md §1 precedence) applies to FACTS, not just rules.**
An older ADR's stated open question / deferral / precondition may have been
**resolved by a later ADR**. ADR-0024 named OQ-8 a precondition and deferred AT-2
generation (D7); **ADR-0025 explicitly "decides its OQ-8"** (`0025:7`) and built the
typed home. Citing ADR-0024's OQ-8 as still-open — without checking the newer ADR —
is a precedence error dressed as a fact.

## Why

- **A negative claim ("X is unbuilt / absent / deferred / a precondition") is the
  most dangerous kind to inherit unverified.** It silently shapes the decision
  (here: "AT-2 generation is huge → recommend the composition compromise"), and it
  fails *safe-looking* — the artifact was well-formed and internally consistent,
  just built on a false premise. Same failure mode as a green result against the
  wrong target ([[0026-interpret-before-run-pre-commit-outcome-meaning]],
  [[0029-verify-full-suite-not-subset]]): a correct-looking output over a false
  fact is worse than an obvious error.
- **draft≠review≠verify caught it — but that makes R2 the *only* backstop.** If R2
  is ever rushed, the stale fact ships and drift accumulates "little by little" (the
  exact concern Cray raised). Verification is cheapest **before** the drafter, not
  after. Moving the grounding upstream removes the single point of failure.

## How to apply

- **Before dispatching `plan-drafter`, verify the fact-pack** — run
  `explore-research` / `Explore` to ground it, *especially every load-bearing
  NEGATIVE / precondition claim*. **Never pass "X is unbuilt / deferred / a
  precondition" as a given without an on-disk citation** ([[feedback_verify_doc_forward_reference_vs_code]]:
  a doc claim about shipped code is a claim to grep, not a fact).
- **When a claim rests on an older ADR's open question / deferral, grep the LATER
  ADRs first** (newest accepted ADR wins, CLAUDE.md §1) — e.g. ADR-0024 OQ-8 was
  resolved by ADR-0025. An OQ cited from an old ADR is "open until proven closed by
  a newer one," not "open."
- **Drafter-side backstop** (encoded in `plan-drafter.md` operating discipline): a
  load-bearing negative claim must be cited on-disk or flagged in *Residual gaps* as
  "asserted-not-verified — recommend an `explore-research` check"; do a **targeted,
  bounded** supersession grep, not an open-ended research sweep (that stays
  upstream).

Related: [[feedback_verify_doc_forward_reference_vs_code]],
[[feedback_draft_review_verify_separation_quality]]; CLAUDE.md §1 (newest ADR wins) +
§6 (verification is hygiene); [[0026-interpret-before-run-pre-commit-outcome-meaning]],
[[0027-verify-not-indictment-refute-claim-not-decision]],
[[0029-verify-full-suite-not-subset]]. Private Tier-0 companion:
`project_oq8_typed_at2_submodel_built_by_adr0025`.

*AI-assisted (Claude Code, session 130); no `Co-Authored-By` per CLAUDE.md §7.*
