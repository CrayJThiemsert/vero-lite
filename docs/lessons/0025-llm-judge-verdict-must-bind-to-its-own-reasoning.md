# Lesson #25: An LLM judge's verdict must be contractually bound to its own reasoning — or it will contradict itself

> **Status:** Codified 2026-06-12 (Session 56, Cray-approved). Code-authored.
> **Severity:** Medium (cost = wasted continuation turns + classifier calls on
> finished work; the drift direction was anti-conservative but not dangerous —
> no gate was bypassed).
> **Cross-references:** PR
> [#278](https://github.com/CrayJThiemsert/vero-lite/pull/278) (the prompt fix
> + contract test in `tests/handoffs/test_sonnet_classifier.py`);
> `.claude/hooks/_sonnet_classifier.py::_build_system_prompt` (the binding
> rules live here); `benchmarks/stop_classifier/gold.yaml` case
> `pause-complete-merged` (the failure class, now a permanent probe);
> ADR-0018 D3 (the `goal-evaluator` judge — the named generalization target);
> [[0024-rules-must-live-where-the-enforcer-looks]] (sibling lesson from the
> same calibration arc).

## 1. The incident (observed live, N=4 in one session)

The Stop-hook classifier (then serving on API Sonnet) returned **`proceed`**
with reasons that *described the opposite verdict*, e.g.:

> "Session is cleanly complete — all PRs merged, tree clean … this is a
> **natural stop** with no next action that matches any trigger row."

`stop_continuation.py` correctly maps `proceed` → block-the-stop → the agent
is sent back into the loop — so finished work got "pushed" into extra turns,
each costing a classifier call and a summary re-statement. Four occurrences
in session 56, all the same shape: **reason says pause, verdict says
proceed.** This also ran *against* the design's conservative bias ("spurious
pauses preferred over spurious proceeds").

## 2. Root cause — under-specified verdict semantics + no cross-field contract

Two gaps in the judge's prompt, neither a model defect:

1. **`PROCEED` was defined as "keep iterating without Cray's input"** — a
   competent model can read that as *"nothing here needs Cray"*, i.e. SAFE-to-
   continue, which is true of completed work. The intended meaning was
   HAS-WORK-to-continue. A verdict defined without a required observable
   invites semantic drift.
2. **Nothing required the structured output's fields to agree.** `decision`
   and `reason` were generated as independent fields; the model could (and
   did) produce a perfectly coherent pause-rationale attached to a proceed
   verdict, and no validation caught it — schema validity checks shape, not
   coherence.

## 3. The rule — three bindings for any `{verdict, reason}` judge

1. **Define each verdict by a required observable, not a vibe.** Here:
   `PROCEED` ⇒ *there exists concrete remaining work to do right now, and the
   reason MUST name that next action*. Completed work / waiting-on-a-human ⇒
   `PAUSE`, stated explicitly as the mapping for that world-state.
2. **State the cross-field contract and forbid the observed mismatch class by
   name:** "Decision and reason must AGREE: never return PROCEED with a reason
   that describes completion, a natural stop, or the absence of a next
   action."
3. **Pin both with tests:** a contract test asserting the rules are present in
   the built prompt (so they cannot silently regress out), and a gold case
   reproducing the exact observed failure against the real prompt surface.
   Post-fix, both the local `gpt-oss:20b` and prod Sonnet answer the gold
   case correctly.

## 4. Generalization (the reason this is a lesson, not a bugfix note)

This applies to **every LLM judge in the system**, not just the stop
classifier. Named candidate: the **`goal-evaluator`** (ADR-0018 D3) — it
already has the REFUTE-don't-bless framing; the addition this lesson suggests
is the same cross-field binding (a PASS verdict must cite the evidence that
satisfies the criterion; a verdict whose own narrative describes unmet
criteria is forbidden by name). More broadly: when a judge's output schema
has a decision field and a justification field, treat their **coherence** as
part of the output contract — schema validation alone will never catch a
self-contradicting judgment.

*AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.*
