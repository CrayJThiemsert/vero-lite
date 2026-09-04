# Lesson #0059 — a logic bug in a hook is contained; a syntax error is not

**Session:** 277 (2026-09-04) · **Measured on:** `.claude/hooks/stop_continuation.py`
before editing `_goal_gate.py` for PLAN-0120 Step 4 · **Status:** advisory (§1
precedence — promote to ADR if it must bind)

## The claim

The intuition is that a hook is dangerous to edit because it runs at every turn end, so
"keep the diff small". **The diff size is irrelevant.** What decides the blast radius is
which of two failure kinds you introduce, and they are contained by completely different
amounts:

| failure kind | what happens | contained? |
|---|---|---|
| **logic bug** — `KeyError`, wrong branch, `None` deref | the wrapper catches it, prints to stderr, returns `None` | ✅ the hook degrades to "does nothing" |
| **syntax error** | escapes the import guard, escapes `main()`, crashes the hook process | 🔴 **no** |

This is backwards from the usual worry. The elaborate change is safe; the typo is not.

## What was measured

`stop_continuation.py` wraps the goal gate in two layers:

```python
def _run_goal_gate(payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        from _goal_gate import run_goal_gate      # :257
    except ImportError:                            # :258  ← only ImportError
        return None
    try:
        return run_goal_gate(payload)
    except Exception as exc:                       # :262  ← any raise
        print(f"stop_continuation: goal gate raised unexpectedly: {exc}", file=sys.stderr)
        return None
```

Its docstring states the intent plainly: *"a missing `_goal_gate` module or any
unexpected raise inside it degrades to `None` … so the Stop hook can never break on the
verification layer."* The second layer delivers that. The first does not, and the gap
is one fact:

```
BROKEN ESCAPED `except ImportError` -> SyntaxError: invalid syntax
issubclass(SyntaxError, ImportError)        = False
issubclass(ModuleNotFoundError, ImportError) = True   ← control: issubclass discriminates
```

Measured in a scratch directory with no contact with the repo — a module with a real
syntax error, imported through the same `try/except ImportError` shape, with a
cleanly-importing module as the control. `SyntaxError` is not in `ImportError`'s tree,
so it propagates out of `_run_goal_gate`, out of `main()` — and `main()` has no
wrapper:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

**Three sites share the shape:** `.claude/hooks/stop_continuation.py:230`, `:258`,
and `.claude/hooks/pretooluse_classifier_dispatch.py:184`.

## Why the containment still matters

It is not an argument for carelessness — it is what makes hook work *tractable*. Session
277 rewrote `_run_one_check`'s return type, added a seventh check state, a new env
injection and a new stand-down branch in `_goal_gate.py`: **+130 insertions in the file
the Stop hook loads at every turn**, with the whole change landing live the moment it
hit disk (hooks are re-read per invocation; nothing is snapshotted). That was
acceptable because every one of those is a *logic* change, and the `except Exception`
layer bounds all of them to "the gate does nothing".

## The practice

1. **AST-parse and import the hook within seconds of every edit — before running
   anything else.** Not as part of the test run at the end; it is the one failure the
   wrapper cannot absorb, and it is instant to check:
   ```bash
   python -c "import ast,pathlib; ast.parse(pathlib.Path('.claude/hooks/_goal_gate.py').read_text()); print('AST OK')"
   python -c "import sys; sys.path.insert(0, '.claude/hooks'); import _goal_gate; print('import OK')"
   ```
   Do it again on `main` after the merge — that is the tree the hook actually runs from.
2. **Prefer an absent `goal.json` while editing the gate.** `run_goal_gate` returns at
   its first line when no goal is active, so the new code cannot run in the session that
   writes it. Session 277 kept it absent deliberately and verified it before and after.
3. **Do not let "the diff is big" stand in for a risk assessment.** Measure the wrapper
   first: `grep -n -B8 -A14 "<the entrypoint>" <the caller>`. In this codebase the
   answer is written in the caller's docstring.
4. ⚠️ **Widening `except ImportError` to `except Exception` at those three sites would
   close the gap** — it would make a syntax error degrade like everything else. Not done
   here: it changes fail-open behaviour the ADR-0018 D4 posture reasons about explicitly,
   so it is a decision, not a cleanup. Recorded as a candidate, not a recommendation.

## The adjacent finding, recorded so it is not re-derived

The same session's cost estimate for a design option — *"widening `_run_one_check`'s
return type touches every test that calls it"* — was **asserted, not measured**. The real
count is **one caller (`.claude/hooks/_goal_gate.py:409`) and zero test callers**. Cray
asked for an explanation before deciding, which is the only reason it was caught.

✎ **And that line number was itself wrong when this lesson was first written** — it read
`:344`, the call site's position *before* the same session's Step 4 edit moved it. A
link-and-citation checker caught it, with a control proving the checker could detect a
bad line at all. **A line number remembered from earlier in the same session is already
a claim**, and writing about a file you have just edited is exactly when it goes stale.

🔴 **A plausible-sounding cost is the hardest kind to catch, because nobody asks for
evidence.** "Bigger diff in a hook is riskier" sounds like engineering judgment and was
wrong twice over: wrong about what contains the risk, and wrong about the diff.

## Related

- [#0007](0007-harness-exit-code-artifact.md) — the other half of "what the harness
  silently swallows": an exit code that reports the truncator rather than the command.
- [#0057](0057-a-perfect-correlation-is-not-a-cause-ask-when-it-changed.md) — the same
  hook directory, and the same discipline of measuring the mechanism instead of
  accepting a hypothesis that fits.
- `docs/adr/0018-axis-b-verification-loop.md` §D4 — the fail-open posture the wrapper
  implements, and why the gate is allowed to degrade silently at all.
