# Lesson #7 — Harness `$?` artifact (claude.ai `wsl → bash -lc` environment)

**Surfaced:** 2026-05-19, PLAN-004 Batch 2 Step 1 manifest §4.0
(`2026-05-19-0842-code-plan004-batch2-manifest.md`).

**Discovered by:** Code tab while dog-fooding the validator on the Batch 2
exploration manifest. Validator's `main()` correctly returns 1 on bad
input; `echo $?` after the same invocation reads 0.

## 1. The artifact

The execution harness used by Code in the claude.ai environment —
`wsl -d ubuntu-24.04 -- bash -lc '<command>'` — does **not propagate
child-process exit codes** through `$?`. All `$?` reads return 0
regardless of the real exit code.

Proven via direct probe:

```bash
false; echo $?                                            # → 0  (false exits 1)
(exit 7); echo $?                                         # → 0
python -c "import sys; sys.exit(5)"; echo $?              # → 0
python -c "raise SystemExit(1)"; echo $?                  # → 0
.venv/bin/python tools/handoffs/validate_handoff.py --all; echo $?  # → 0 (even when 127 errors found)
```

The validator/reader tooling **logic is correct**:

- pytest 19/19 (Batch 1 quality gate) asserts `main()` return values
  in-process — green.
- Direct probe: `validate_handoff.main(["<bad file>"])` returns `1`;
  on a schema-conformant file returns `0`; `--all` on the real
  `.claude/handoffs/` tree returns `1` with stderr summary
  `127 error(s) across 56 file(s)`.

The bug is in the **harness layer** between Python's process exit and
the shell variable `$?` that subsequent commands read. It is not a
project tooling regression.

## 2. Why this matters

Acceptance criteria phrased as "expect exit 0" or "validator returns
clean" verified via `echo $?` are **structurally unreliable** in this
environment. They will report PASS on actual failure. Two historical
closeouts (`2026-05-19-0213-code-plan004-batch1-closeout.md`,
`2026-05-19-0242-code-status-housekeeping-post-batch1-closeout.md`)
both reported "dog-food exit 0" via `echo $?`. The underlying claims
HOLD (the files ARE schema-conformant — re-verified via reliable method
in manifest §4.0/§7), but the wording was unreliable. Not amended
retroactively (CLAUDE.md §7 "no amend"; Lesson #6 "no silent papering");
this lesson is the going-forward correction.

## 3. Reliable verification methods (use these instead)

Three acceptable replacements for `echo $?`. Use ≥1 per assertion.

### 3.1 stderr summary line capture

The Batch 1 validator emits a one-line summary to stderr at end of run:

- PASS: `OK: N file(s) valid`
- FAIL: `<E> error(s) across <M> file(s)`

Capture and grep:

```bash
.venv/bin/python tools/handoffs/validate_handoff.py --all 2>&1 \
  | tee /tmp/validator-output.txt
grep -E '^(OK:|[0-9]+ error)' /tmp/validator-output.txt
```

Test the captured summary against the expected pattern in dispatch
acceptance criteria.

### 3.2 In-process `main()` return probe

For Python tools that expose a `main()` function returning an int:

```bash
.venv/bin/python -c "
import sys
sys.path.insert(0, 'tools/handoffs')
from validate_handoff import main
ret = main(['--all'])
print(f'RET={ret}')
" > /tmp/validator-ret.txt
grep -q '^RET=0$' /tmp/validator-ret.txt && echo PASS || echo FAIL
```

This bypasses the harness entirely; the assertion lives inside the
Python process.

### 3.3 Behavioral assertion on side effects

When the tool produces observable side effects (file written, schema
table populated, count change), assert on the side effect directly,
not on the runner's exit code:

```bash
# example: post-migration validator should report N valid files
.venv/bin/python tools/handoffs/validate_handoff.py --all 2>&1 \
  | grep -E "^OK: ${EXPECTED_N} file\(s\) valid"
```

If the grep matches: PASS. If not: FAIL (the validator's own stderr
self-report is the contract, not the harness exit code).

## 4. Forbidden patterns in dispatches and closeouts

The following wording is **banned** in any dispatch acceptance criteria,
closeout PASS/FAIL determination, or stop-and-ask trigger:

- `echo $?` followed by an expected value (`echo $?  # expect 0`)
- "Expect exit N" / "Exit code N" / "Returns 0" without specifying
  HOW the return is observed (reliable method per §3 above)
- "Dog-food: exit 0" as standalone evidence — always pair with §3.1 or
  §3.2 verification
- "If exit 0 then PASS" — replace with "If stderr matches `OK: …` then
  PASS"

The negative wording rules out the failure mode; the positive guidance
in §3 keeps dispatch authors from re-inventing methods every time.

## 5. Scope

**Applies to:** any tool invocation in any Code-tab dispatch in this
environment, where exit-code semantics determine PASS/FAIL.

**Does not apply to:**
- Tool runs whose output is rendered or parsed directly (no exit-code
  reliance) — e.g. `git log --oneline` for human inspection
- Pre-commit hooks (hooks run by `pre-commit run --all-files` print
  their own per-hook pass/fail; the hook framework's overall exit is
  rendered to terminal but rarely depended on by dispatches — if
  depended on, use §3.1 by parsing the framework's summary lines)
- pytest in CI / local pytest runs that print `passed`/`failed` lines —
  parse those lines, not `$?`

## 6. Detection cue

If you find yourself writing "expect exit 0" or `echo $?` in a dispatch
acceptance criterion: **STOP.** Rewrite per §3 before sending.

If you find yourself reading `$?` in a Code-tab closeout to determine
PASS/FAIL: **STOP.** Re-run the command capturing stderr and apply §3.1
or §3.2 instead. Report the reliable signal in the closeout.

## 7. Related

- Lesson #5 §3 (schema-fidelity discipline for Chat dispatches) — sister
  pattern: avoid inferred content; this lesson is the runtime-verification
  counterpart
- Lesson #6 (Code surface → Chat re-dispatch → Code execute) — Code's
  obligation to surface harness anomalies rather than paper over
- PLAN-004 Batch 1 closeout (`2026-05-19-0213-code-plan004-batch1-closeout.md`)
  + STATUS housekeeping closeout (`2026-05-19-0242-code-status-housekeeping-post-batch1-closeout.md`)
  — retroactive note: both reported "exit 0" via `echo $?`; substance
  is sound (re-verified), wording is unreliable, not amended
- PLAN-004 Batch 2 Step 1 manifest (`2026-05-19-0842-code-plan004-batch2-manifest.md`)
  §4.0 — origin discovery + reliable-method probe results

AI-assisted per project convention.
