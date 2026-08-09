---
name: excision-scope
description: Enumerate the true blast radius before deleting anything — retiring a guard or hook, removing a feature, excising a subsystem, dropping a config surface, or executing a PLAN whose Steps say "remove X". Encodes the failure that cost PLAN-0102 three separate scope misses: a review that walks the call graph only BACKWARDS from the marker symbol finds every site that touches it and misses every callee those sites exclusively own. Also records why a linter cannot close the gap (ruff flags a dead import, never a dead private function or module constant, so an AC reading "ruff + mypy clean" passes over it) and points at tools/excision_scope.py, which computes the forwards half. Use when about to delete a named set of symbols, when writing or executing the Steps of an excision PLAN, when an AC claims "no dead code left", or when reviewing a diff that removes more than one function.
---

# excision-scope — what actually dies when you delete something

## The rule

**Scope an excision in BOTH directions, and the forwards half is the one that
gets skipped.**

- **Backwards** — from the marker symbol to every site that references it. This
  is the pass people do, and it works. It is how PLAN-0102's R2 found three
  sites (`awaiting_ack`, `clear_turn_scoped`, `_apply_commit_reset`) whose names
  contain no `L1` token at all and which a name-keyed grep therefore cannot see.
- **Forwards** — from each function you are deleting to the things **only** that
  function calls. Skipping this is what left PLAN-0102's Steps naming
  `_apply_commit_reset` but not the four symbols it exclusively owned, and
  asserting that two imports must be KEPT when their only callers were the very
  functions the same Step deletes.

## ⚠️ Do not delegate the forwards half to the linter

`ruff` reports an **unused import**. It does **not** report an unused private
function or an unused module constant. So an acceptance criterion phrased
"the removed identifiers have zero remaining call sites, and ruff + mypy are
clean" is satisfied by a tree still carrying dead functions. That is measured,
not theoretical — it is what PLAN-0102's AC-9 did.

`mypy` does not close it either: dead code type-checks fine.

## The tool

```bash
python tools/excision_scope.py --root .claude/hooks --delete _apply_commit_reset _handle_write_or_edit
```

It computes to a fixpoint every symbol whose *only* referencers are inside the
deletion set, and reports four things:

| Section | What to do with it |
|---|---|
| **Transitively orphaned** | The forwards half. Each is a candidate — verify, then delete. |
| **⚠️ Named for deletion but still used** | You would break something. Resolve before proceeding. |
| **Already unreferenced** | Pre-existing, not yours. Entry points legitimately live here. |
| **⚠️ Name not found** | A typo silently shrinks the answer to nothing and looks exactly like "all clear". |

**Its output is a list to verify, never a verdict.** It is static AST analysis:
`getattr`, string-keyed registries, `settings.json` command strings, pytest
fixture names and anything outside `--root` are all invisible to it. The tool
prints its own blind spots on every run — read them, and do not trim them
(`tests/tools/test_excision_scope.py` fails if you do).

That self-declaration is not decoration. In its historical validation the tool
listed `normalize_file_path` as orphaned; the real caller lives in
`pretooluse_classifier_dispatch.py`, outside the four files that run analysed.
The caveat earned its place on the first real run.

### Reproducing the historical validation

Recorded here because the original harness lived in `/tmp` and `/tmp` does not
survive a reboot — the same way session 216 lost its edge-timeout harness. Two
commands rebuild it:

```bash
mkdir -p /tmp/pre && for f in _loop_counter pretooluse_loop_detect posttooluse_progress_observer stop_continuation; do git show "02d77c5^:.claude/hooks/$f.py" > "/tmp/pre/$f.py"; done
```

```bash
python tools/excision_scope.py --root /tmp/pre --delete LoopType.FILE_EDIT L1_GRACE_BUDGET l1_threshold_for l1_deny_threshold_for reset_untouched_l1 reset_l1_for_targets record_turn_touched record_subagent_touched take_subagent_touched clear_turn_touched clear_turn_scoped record_awaiting_ack take_awaiting_ack note_attempted_edit note_content_hash mark_warned _handle_write_or_edit _handle_subagent_stop _maybe_warn_l1 _warn_advisory _apply_commit_reset _apply_turn_boundary_reset _apply_ack_clear _ack_clear_guarded _resolve_target
```

That deletion set is what PLAN-0102's Steps actually named. The run must surface
`stop_continuation::_state_path`, its three orphaned `_loop_counter` imports and
`DEFAULT_COUNTER_PATH`, the five-symbol commit-reset subsystem, and the three
constants Step 5 omitted. If a future change to the tool stops surfacing them, it
has regressed on the incident it exists for.

## Judgment the tool cannot make for you

An orphan is a *candidate*, and sometimes the right answer is to keep it:

- **A public primitive on a shared spine.** PLAN-0102 left `observe()` in place
  though it lost its last caller: deleting it would have turned `_record`'s
  `bump` parameter into a constant and pulled a refactor into the one function
  every surviving L2/L3/L4 increment flows through. Cosmetic win, real
  regression risk, against the PLAN's own rule that everything the survivors
  call stays unmodified.
- **A symbol with a consumer outside `--root`.** Widen the roots and re-run
  before concluding.

Record the decision either way. An orphan you deliberately keep, left
unexplained, reads to the next session as an oversight.

## Ordering, when the excision spans a shared layer

Deleting shared symbols is **not** separable into safe checkpoints. If Step N
stops calling a symbol and Step N+1 deletes it, then every intermediate tree
between them fails to import. Land them in **one commit**. The specific shape
that bites: an orphaned `from … import X` raises `ImportError` at module load —
before any code runs, caught by no `try`/`except` — so it takes down every arm
of that module at once, silently, with no other symptom.

## Verify behaviourally, not by string absence

The string being gone proves nothing about the behaviour being gone, and prose
about a retired feature legitimately keeps mentioning its name. Two consequences:

1. Assert the **behaviour** is extinct, with a **live positive control in the
   same run** — otherwise "no output" is indistinguishable from "the whole layer
   died". This matters most when the thing you removed had stopped firing on its
   own: a test that merely observes silence passes identically before and after.
2. A structural guard must read the **AST**, not `grep` the source. PLAN-0102's
   own guard went RED against a correct file because the module docstring
   explains the retirement and therefore names the retired identifiers — a guard
   that cannot tell a call from a comment punishes a file for documenting itself.

## References

- `tools/excision_scope.py` — the tool, and its module docstring for the
  incident it was built from.
- `docs/plans/done/0102-retire-l1-loop-detect.md` §"Corrections found by
  executing this PLAN" — the three misses, with their one root cause.
- [`docs/lessons/0039-a-self-authored-guard-inherits-the-authors-blind-spot.md`](../../../docs/lessons/0039-a-self-authored-guard-inherits-the-authors-blind-spot.md)
  — why a self-supplied predicate goes green on the cases that bite.
- CLAUDE.md §8 — the scenario-test rule the excision's replacement tests owe.
