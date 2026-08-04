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

## 1.1 Mechanism CORRECTED, and the ban relaxed (re-measured 2026-07-26, s175)

§1's *prohibition* has held for over two months and is retained. Its
*explanation* was wrong, and the wrong explanation cost us a usable tool.

The harness does **not** "fail to propagate exit codes". What happens is that
`wsl bash -lc '<STR>'` reassembles the argv and passes `<STR>` through **one
extra shell expansion** before the inner bash ever parses it. A bare `$?` is
therefore consumed *a layer early* — it never reaches the command whose status
you wanted. Escape it and it works:

```bash
wsl bash -lc 'false; echo "rc=$?"'      # → rc=0    ← FABRICATED SUCCESS
wsl bash -lc 'false; echo "rc=\$?"'     # → rc=1    ← correct
wsl bash -lc 'cd /etc; echo "$(pwd)"'   # → /home/crayj/work/vero-lite  ← ran BEFORE the cd
wsl bash -lc 'cd /etc; echo "\$(pwd)"'  # → /etc
```

**Outer quote style is load-bearing.** With a double-quoted outer argument the
`\` is eaten before WSL sees it, so `"... \$? ..."` is *still* broken. Use a
**single-quoted outer argument and write `\$` for every `$`**.

Classified per CLAUDE.md §6 as **`was an error`**, not `superseded by new
info`: the environment did not change, the diagnosis was wrong from the start.
It was a *protective* error — banning bare `echo $?` was correct and remains
correct — but it over-generalized to "exit codes are unreadable here", which
pushed every dispatch toward stderr-parsing when a two-character fix existed.

## 1.2 The hazard nobody had recorded: stderr **erases** stdout

Measured the same day, and worse than the exit-code artifact because it
destroys evidence rather than merely misreporting it. The two streams are
handed file descriptors that **share one file offset**, so they overwrite each
other byte-for-byte instead of interleaving:

```bash
wsl bash -lc 'printf "STDOUT_LINE_%02d\n" 1 2 3 4 5 6 7 8; echo SHORT_ERR >&2'
# → SHORT_ERR          ... and NOTHING else. All 8 stdout lines gone. 3/3 runs.

wsl bash -lc 'exec 2>&1; printf "STDOUT_LINE_%02d\n" 1 2 3 4 5 6 7 8; echo SHORT_ERR >&2'
# → all 9 lines present.
```

A **single** stderr line — a git advice message, a deprecation warning — can
erase an entire stdout, with no error and no marker. Session 175 shipped three
PRs while silently reading corrupted output; the tell, once you know to look
for it, is a truncated fragment such as `msert/vero-lite.git` (the tail of
`CrayJThiemsert/vero-lite.git`) or two messages fused into one line.

**`2>&1` is therefore a correctness requirement in this environment, not a
style preference.**

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

### 3.4 The default idiom — capture to a file, echo the real code, read a slice

Added 2026-07-26. This is the pattern to reach for by default; §3.1–§3.3 remain
valid for assertions that key on a tool's own stderr self-report.

```bash
wsl bash -lc 'set -uo pipefail; cd /abs/path || exit 9; ( <CMD> ) >/tmp/run.log 2>&1; rc=\$?; echo "EXIT=\$rc"; tail -30 /tmp/run.log; exit \$rc'
```

Why each part earns its place:

- **`( ... )` not `{ ...; }`** — a brace group is not a subshell, so an `exit`
  inside it terminates the whole invocation and silently skips the reporting
  tail.
- **`>/tmp/run.log 2>&1`** — one merged stream into one file. Defeats §1.2
  entirely, and keeps the *full* output available to read later with `sed -n`
  rather than losing it to truncation.
- **`rc=\$?` escaped** — per §1.1. Unescaped, this prints `EXIT=` (empty) and
  the whole idiom is decorative. That happened on this idiom's first real use.
- **`echo` the code BEFORE the slice** — the failure signal must not itself be
  truncatable.
- **`tail`, never `head`** — see §4.

For anything non-trivial, write a `.py`/`.sh` file with the Write tool and
execute that instead. Zero escaping, and it is re-runnable.

## 4. Forbidden patterns in dispatches and closeouts

The following wording is **banned** in any dispatch acceptance criteria,
closeout PASS/FAIL determination, or stop-and-ask trigger:

- **Piping a command whose success matters into `head`/`tail`** (added
  2026-07-26). The pipeline reports the *truncator's* status — ~always 0 — so a
  failure reads as success, and the truncation cuts the traceback that would
  have revealed it. This is not theoretical: in s175 a Python script aborted on
  an assertion, `| tail -6` cut the traceback, the exit code was swallowed, the
  run was reported as successful, and the wrong diagnosis was relayed to Cray.
  If you must pipe, add `set -o pipefail`.
- **`| head` *under* `pipefail`** — the inverse trap. `head` closes the pipe
  early, the producer dies of SIGPIPE, and the pipeline reports **141**: a
  *successful* command turned into a spurious failure. `tail` drains its input
  and is safe. (This contradicts community advice recommending `head -c` as an
  output cap; measured here 2026-07-26.)
- **Newline-separated commands inside `wsl bash -lc "..."`** — newlines do not
  short-circuit. A failing step in the middle runs on, and the harness sees only
  the last command's status. Chain with `&&`, or open with `set -euo pipefail`.
  Measured: `echo A; false; echo B` → `EXIT=0`.
- **An unescaped `$` inside a `bash -c` string** — see §1.1.
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

## 6.1 Enforcement (added 2026-07-26)

Prose placement is advisory placement (Lesson #0024). Two of the four hazards
are syntactically detectable, so they are now **enforced** rather than merely
written down: `posttooluse_progress_observer.py::_shell_hygiene_warning` emits
an agent-visible advisory after any Bash call that pipes into `head`/`tail`
without `pipefail`, uses `head` under `pipefail`, or carries an unescaped `$`
inside a `bash -c` string. Pinned by `tests/handoffs/test_shell_hygiene_advisory.py`.

**A fourth shape added 2026-08-04 (session 204): any `$` — escaped or not — inside a
DOUBLE-quoted `bash -c` argument.** §1.1 above already stated that the outer quote
style is load-bearing, but the enforcement built for it only fired on an *unescaped*
`$`, so the escaped-under-double-quotes form was invisible to the very check meant to
police it. That gap ran a whole session: the agent followed the advisory's own wording
("write `\$` for every `$`"), kept the outer quotes double, read `EXIT=0` over a run
with two RED tests, and went on to conclude that CLAUDE.md §8 prescribed an
ineffective fix — a wrong diagnosis that came within one step of an unnecessary
constitutional amendment. The substance of §1.1 was correct throughout; only its
enforcement was half-built.

The generalisable point, and the reason this is recorded rather than quietly patched:
**when a remedy has two required halves, stating one of them is worse than stating
neither.** A half-remedy is followed confidently and fails silently, whereas no
remedy at least leaves the reader looking. Both the advisory text and the predicate
now name both halves — a SINGLE-quoted outer argument AND `\$` for every `$`.

It is a PostToolUse advisory, not a PreToolUse deny, on purpose: the harm is
not *running* the command, it is *believing* its output — which is knowable
only once it has run. It also protects the observer's own signal, since a
masked failure means L3/L4 see exit 0 and a body with the traceback cut off,
so the masking silently disarms the loop detection.

**§1.2 is deliberately NOT enforced.** Whether a command will emit stderr is
not knowable from its text, so a check would either miss most cases or warn on
every call. `2>&1` stays a discipline, carried by the CLAUDE.md §8 rule.

## 7. Related

- **CLAUDE.md §8** — the binding one-line rule this lesson is the mechanics for
- **Lesson #0001 Trap 9** (`${PIPESTATUS[0]}` / `tee` breaks `$?`) — the same
  mechanism as §4's first bullet, found earlier in a pre-commit context and
  exemplified with `tee`; this lesson is the general statement
- **Lesson #0024** (rules must live where the enforcer looks) — the argument
  for §6.1
- **Lesson #0004** (WSL `bash -c` variable-expansion trap) — the quoting-layer
  sibling; §1.1 here is the exit-code instance of that same double-expansion
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
