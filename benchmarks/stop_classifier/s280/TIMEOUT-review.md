# s280 — Stop-hook latency / timeout budget review

**Scope:** offline only. Zero live model calls; zero MS-S1 contact. Everything below is
read off disk or computed from figures already on disk. Two offline measurements were
run in this session (a prompt-size measurement and a positive control on the budget
test); both are marked **MEASURED** and print their values.

**Headline:** `OLLAMA_TIMEOUT_SEC = 75` should **not** be raised. The budget chain is
already over its own ceiling at 75, no test can see that, and the constant's stated
rationale is 3 months stale. The lever that actually buys classifier latency is the
**32,708-character system prompt**, which is already measured at 8.4 s median when slim
versus 38.2 s as shipped.

---

## 0. The chain as it actually stands (every value re-read on disk, s280)

| # | Constant | Value | File:line |
|---|---|---|---|
| 1 | Stop hook `timeout` | **180** | `.claude/settings.json` — Stop entry running `stop_continuation.py` (**MEASURED** via the test's own parser: `timeout = 180`) |
| 2 | `DEFAULT_CHECK_BUDGET_S` | **120** | `.claude/hooks/_goal_gate.py:116` |
| 3 | `REQUIRED_MARGIN_S` | **45** | `tests/handoffs/test_goal_gate_budget_fits_the_hook.py:41` |
| 4 | `OLLAMA_TIMEOUT_SEC` | **75** | `.claude/hooks/_sonnet_classifier.py:93` |
| 5 | `API_TIMEOUT_SEC` (sonnet rollback backend) | 20 | `.claude/hooks/_sonnet_classifier.py:87` |
| 6 | `TELEGRAM_TIMEOUT_SEC` (gate) | 5 | `.claude/hooks/_goal_gate.py:138` |
| 7 | `TELEGRAM_TIMEOUT_SEC` (stop hook) | 5 | `.claude/hooks/stop_continuation.py:82` |
| 8 | `work_fingerprint` git calls | 2 × 10 | `.claude/hooks/_goal_gate.py:317`, `:325` |
| 9 | `llm_request_timeout_s` (app + benchmarks) | 120.0 | `services/api/config.py:163-166` |
| 10 | `llm_status_timeout_s` (residency poll) | 3.0 | `services/api/config.py:181-189` |

**There is exactly one Stop hook.** Dumped from `.claude/settings.json`: `Stop` has a
single entry, `python .claude/hooks/stop_continuation.py`, `timeout: 180`. No other hook
event declares a timeout at all. So the 180 is the whole Stop-side wall-clock allowance,
not a share of it.

---

## 1. Control flow — can the gate budget and the classifier both be spent in one Stop event?

**Yes. Emphatically yes, and on the *common* path, not an exotic one.**

`stop_continuation.py::main()` runs three arms in sequence:

- `:512-513` — re-entry guard (`stop_hook_active`) → `return 0`, free.
- `:520-525` — chain-cap fail-safe. On cap-hit: one Telegram ping (5 s) + `return 0`.
  **This is the only arm that can skip both of the expensive ones.**
- `:531-537` — `gate_directive = _run_goal_gate(payload)`. **Only if this returns a
  non-`None` directive** does `main()` print it and `return 0` at `:536-537`.
- `:540` — `decision = _classify(payload)`. Reached on **every** `None` from the gate.

So the question reduces to: how many of `run_goal_gate`'s exits are `None` *after* it has
already spent the check budget? Enumerating `_goal_gate.py::run_goal_gate` (`:723-880`):

| # | Exit | Line | Returns | Checks already run? | Classifier runs? |
|---|---|---|---|---|---|
| 1 | no goal / not `active` | `:738-739` | `None` | no | **yes** (free gate) |
| 2 | battery lock fresh → defer | `:749-751` | `None` | no | **yes** (free gate) |
| 3 | *(stale lock ping — falls through, +5 s)* | `:756-762` | — | — | — |
| 4 | DB-contention stand-down | `:774-775` | `None` | **yes** | **yes** |
| 5 | goal PASSED | `:788-802` | `None` | **yes** | **yes** |
| 6a | checks not green, `enforce: true`, first time | `:806-809` → `:713` | directive | **yes** | no |
| 6b | checks not green, `enforce: true`, repeat | `:806-809` → `:710-712` | `None` | **yes** | **yes** |
| 6c | **checks not green, `enforce: false`** | `:806-809` → `:714-716` | `None` | **yes** | **yes** |
| 7 | work changed → dispatch evaluator | `:814-828` | directive | **yes** | no |
| 8 | dispatch unanswered, `enforce: true` → park | `:837-840` | `None` | **yes** | **yes** |
| 9 | dispatch unanswered, `enforce: false` → released | `:842-860` | `None` | **yes** | **yes** |
| 10 | divergence explained by amendment (redirect) | `:866-874` | `None` | **yes** | **yes** |
| 11 | judge residue not PASS / drift | `:875-880` → `_failing_consequence` | as 6a/6b/6c | **yes** | mostly **yes** |

**9 of the 11 exits fall through to the classifier.** Only two short-circuit it — the
enforce-block (`:713`) and the evaluator dispatch (`:828`) — and both require conditions
that do not hold on an ordinary turn.

🔴 **The default is the expensive path.** `enforce` defaults to `False`
(`.claude/hooks/_goal_state.py:330`, and the schema comment at `:21` — *"default false =
warn-only v1"*). So a goal whose checks are red takes exit **6c**: run every check under
the full budget, compute `work_fingerprint()` (2 git subprocesses), record a warn, ping
Telegram, return `None` — and then the classifier is called. That is the normal shape of
a session with an active goal that is not yet green, i.e. most of the life of a goal.

### Worst-case total against the 180 s hook timeout

| Component | Cite | Seconds |
|---|---|---|
| Battery-lock read | `_goal_gate.py:266-283` | ~0 |
| Stale-lock Telegram ping | `:756-762` w/ `:138` | 5 |
| `_run_checks` total budget | `:405` → `:116` `DEFAULT_CHECK_BUDGET_S` | **120** |
| `work_fingerprint()` — 2 × git | `:311-326`, `timeout=10` each | **20** |
| Warn Telegram ping | `:715` w/ `:138` | 5 |
| Classifier attempt 1 | `_sonnet_classifier.py:733` w/ `:93` | **75** |
| Classifier retry (parse-failure only, see below) | `:766-771` | **75** |
| Dispatch-suggestion Telegram ping | `stop_continuation.py:584` w/ `:82` | 5 |
| **Absolute ceiling** | | **305 s** |
| **Ceiling without the retry** | | **220 s** |

**Both exceed 180.** The current, post-s275 "fixed" configuration overruns its own hook
timeout by **40 s** in the no-retry case and by **125 s** with the retry.

**On the retry, precisely** (`_sonnet_classifier.py:750-776`): a transport **timeout** does
*not* retry — `:753-754` catches `URLError`/`TimeoutError` and returns `_pause` immediately.
The retry at `:766` fires only when attempt 1 returned a body that `_parse_response` rejected
(`:760-763`). So 2 × 75 requires a slow-but-malformed first response followed by a second slow
call. That is not hypothetical for this model: the 2026-08-02 research measured
**3/12 blank responses on the shipped baseline prompt** (`docs/research/private/2026-08-02-llm-placement-classifier-eval-and-palantir-aip-pattern.md`, condition-A row), and a blank body
raises `ValueError` at `:739-740` → retry.

### Is 220 s reachable in practice, or only in theory? — **Reachable.**

Three preconditions, all satisfiable today:

1. **An active goal with `check` criteria.** Ordinary; `/goal` is the documented Axis-B habit.
2. **Checks that consume the full 120 s.** A single criterion can do it alone: `_run_one_check`
   takes `timeout = min(criterion.timeout_s, remaining_budget_s)` (`:373`), and the authoring
   guidance still tells the author to size against a much larger number — see the defect in §6.
   A scoped `pytest` selection routinely exceeds 120 s.
3. **A slow or timing-out classifier call.** 🔴 **Already witnessed.** The 2026-08-02
   research records: *"the C5 case hit `OLLAMA_TIMEOUT_SEC=75` on 3/3 baseline runs while
   slim answered it correctly in 4–5 s"*, with a **38.2 s median** on the shipped prompt.

### 🔴 This arithmetic has been done here before — and it was NOT refuted

`docs/logs/2026-08-26-sd-premortem-replay-experiment.md:~270-276` records the identical
decomposition:

> the work sitting outside the check budget is Ollama 75 s (`_sonnet_classifier.py:93`) +
> git 2×10 s + Telegram 5 s ≈ 100 s, so a 179 s budget still totals ≈ 279 s against a
> 180 s Stop timeout.

Two replay runs derived **the same arithmetic** and returned opposite verdicts (DEAD vs
ALIVE). Read carefully: *"Nothing was measured differently; the two runs disagreed about
whether the claim was **load-bearing**."* And `docs/plans/0116-deterministic-claim-rollup-tool.md:~223`
(fixture F7a/F7b) states the record contains **no ruling on which labelling is correct**.

**So the arithmetic is corroborated by the record, not refuted.** What is unruled is
whether it *kills a design option*. I am reporting it as a measured consequence, which is
the reading run 4 took, and I am not asserting it kills anything.

Two differences from that prior pass, both in the direction of *more* overrun:

- It used a proposed budget of 179; today's is 120, so the sum is 220 not 279 — still over.
- It **omitted the classifier retry**, so its ~100 s of non-check work is a floor, not a ceiling.
  The true non-check ceiling is ~185 s.

---

## 2. What actually happens when each timeout blows

### 2a. `OLLAMA_TIMEOUT_SEC` (75 s) exceeded — **completely silent**

Trace:

1. `urlopen(req, timeout=OLLAMA_TIMEOUT_SEC)` at `_sonnet_classifier.py:733` raises
   `TimeoutError` (or a `URLError` wrapping it).
2. `_run_with_retry` catches it at `:753` → `return _pause(f"API unreachable: {exc}")`.
   **No retry** (§1).
3. `_pause` (`:216-222`) builds `{"decision": "pause", "matched_rows": [...], "reason": ...}`.
4. `stop_continuation.main()`: `verdict == "pause"` matches neither `:543` (`proceed`) nor
   `:563` (`dispatch`), so it falls to `:594-597` → `_reset_chain()` → `return 0`.

What is emitted, logged, or recorded: 🔴 **nothing.**

- **stdout:** nothing. No directive → the Stop fires normally.
- **stderr:** nothing. Contrast `:551-554`, which *does* print the contentless-proceed
  demotion. The pause arm prints no diagnostic at all, so the `reason` string carrying
  `"API unreachable: ..."` is **constructed and then discarded**.
- **Telegram:** nothing. Gate pings are gate-side; the classifier's pause arm pings nothing.
- **State:** `stop-chain.json` is *reset* (`:596`), which is the same thing a legitimate
  `pause` does. `goal.json` is untouched by the classifier.
- **The agent sees:** nothing. The turn ends exactly as it would on a real `pause`.
- **The user sees:** only the wall clock — up to 75 s of dead air at the end of a turn,
  with no explanation anywhere.

**Consequence for the decision:** a classifier timeout is byte-for-byte indistinguishable
from a legitimate `pause` on every observable surface. It cannot cause a wrong `proceed`
(fail-closed is genuinely fail-closed). So **raising `OLLAMA_TIMEOUT_SEC` buys no safety
whatsoever** — it only converts "silent pause" into "an actual classification". Since
`dispatch` was demoted to an advisory Telegram ping (PLAN-0092, `stop_continuation.py:563-592`),
the *only* behavioural gain from a longer timeout is **more auto-`proceed` continuations**.
That is a small benefit and arguably a negative one against the repo's stated
"spurious pauses over spurious proceeds" bias (`_sonnet_classifier.py:31-34`).

### 2b. The outer 180 s hook timeout exceeded — worse in kind, and partly unmeasured

- The harness terminates the hook. **Whether it kills the process tree or only the hook
  process is an explicitly OPEN question**: `docs/adr/0018-axis-b-verification-loop.md:1472-1474`
  (**D8-VX-4**, *"Measure once, before the timeout/budget fix is shaped"*) and
  `docs/plans/0120-goal-gate-test-db-isolation.md:147` (marked ❌). I am not asserting either way.
- **Established consequence:** no directive on stdout → the Stop fires. From the user's
  seat that is the *same* visible outcome as a pause. So the outer timeout is **not louder**
  than the inner one; it is equally quiet in the normal case.
- **The hazard that makes it worse:** a killed hook can leave the WSL-side `pytest` child of
  a `check` criterion orphaned, still holding the per-checkout test database with no owner
  to release it — `_goal_gate.py:118-130` and `tests/handoffs/test_goal_gate_budget_fits_the_hook.py:13-21`.
  🔴 That theory is **`asserted-not-verified`**, and `docs/plans/done/0115-…:680-691` records
  that the one fully-instrumented incident (s253) **points away from it** — the second pytest
  was the gate's own C1 *with its parent intact*, not an orphan. Anyone reopening this starts
  from "the evidence leans against", not "nobody has looked".
- **Net:** the outer timeout is *potentially* worse (a stranded shared resource; an
  interrupted append-only trail) and *no more visible*. It is not a graceful degrade.

**Therefore: raising `OLLAMA_TIMEOUT_SEC` is cheap in safety and expensive in overrun risk.**
The failure it prevents (a silent pause) is benign; the failure it invites (blowing the outer
180) is the one with a resource hazard attached.

---

## 3. The ceiling — how far can `OLLAMA_TIMEOUT_SEC` be raised?

### (a) Before a test fails: **no ceiling. Zero. MEASURED.**

🔴 **No test in the repo constrains `OLLAMA_TIMEOUT_SEC`.**

Complete reference enumeration (repo-wide grep, worktree copies and `__pycache__` excluded):

- `.claude/hooks/_sonnet_classifier.py:93` — the definition
- `.claude/hooks/_sonnet_classifier.py:733` — the use
- `tests/handoffs/test_sonnet_classifier.py:354` — `assert seen["timeout"] == sc.OLLAMA_TIMEOUT_SEC`

That single test **reads the constant**, so it tracks any value and can never redden on a change.
`test_goal_gate_budget_fits_the_hook.py` imports **only `_goal_gate`** (`:37`) — it never
imports the classifier, so it cannot see the number the margin is supposedly reserved for.

**Positive control, run offline this session** (no tree edit — the module attribute was
mutated in a throwaway interpreter):

```
PRE  OLLAMA_TIMEOUT_SEC = 75
baseline: all 3 budget tests PASS
POST OLLAMA_TIMEOUT_SEC = 3600
VERDICT: still ALL PASS at 3600 -> the budget module is BLIND to OLLAMA_TIMEOUT_SEC
measured: settings timeout = 180  budget = 120  margin = 45
```

`pre=75 post=3600`, three assertions green in both readings. **The one number in the chain
that the parent is asking about is the one number with no guard at all**, and the test that
*looks* like it guards the chain guards a different constant.

### (b) Before the outer hook timeout is threatened: **already breached — the true ceiling is 30, not 75**

The invariant that ought to hold, from §1's decomposition:

```
DEFAULT_CHECK_BUDGET_S  +  k × OLLAMA_TIMEOUT_SEC  +  20 (git)  +  10 (2 pings)  ≤  180
```

with `k = 1` single-attempt, `k = 2` retry-inclusive.

| Budget | k=1 ceiling on `OLLAMA_TIMEOUT_SEC` | k=2 ceiling |
|---|---|---|
| **120 (today)** | **30** | **15** |
| 75 | 75 | 37 |
| 60 (the test's floor, `:95`) | **90** | **45** |

So at today's budget the classifier's timeout would have to come **down to 30 s**, not up.
And with the budget at its own hard floor of 60 (`test_…:95` — below that every check times
out and the gate goes permanently unresolved), the **absolute ceiling is 90 s single-attempt,
45 s retry-inclusive**. Anything above 90 is unreachable without moving the 180 itself.

### (c) Before the per-turn human cost becomes unacceptable

This hook fires at **every** turn end, so its latency is paid by Cray every single turn.

| Per-turn hook latency | per 100 turns | per 300 turns | delta vs 6 s |
|---|---|---|---|
| **6 s** (today, warm) | 10 min | 30 min | — |
| **45 s** | 75 min | 3 h 45 m | +39 s/turn = **+65 min / 100 turns** |
| **68 s** | 1 h 53 m | 5 h 40 m | +62 s/turn = **+103 min / 100 turns** |

🔴 **Crucially, this column measures the wrong lever.** `OLLAMA_TIMEOUT_SEC` is a *ceiling*,
not a delay: the hook returns the instant the call completes. Raising 75 → 90 costs the human
**~0 at the median**; it costs only on the tail turns that would otherwise have been cut off.
What sets the per-turn tax is the **model + prompt**, not the timeout.

So the 45 s and 68 s rows are the cost of *adopting a 54–68 s model*, and on that the repo has
already ruled — `benchmarks/stop_classifier/RESULTS.md:20-22`:

> `gemma4:12b` / `qwen3.6:35b` were excluded **a priori** … **45–120 s/call is disqualifying
> for a hook that fires at every turn end**; no warm cycle spent re-measuring.

The Qwen 27B candidates at 54.4–67.9 s land squarely inside that already-disqualified band.

### **The binding constraint is (b), the outer hook timeout — and it is already violated.**

Not (a): nothing tests it. Not (c) *for the timeout itself*: raising a ceiling is near-free
for the human. (c) binds the **model choice**, and there the a-priori rule above already
settles it.

---

## 4. Ruling on the 45-vs-75 contradiction

**Read the test's own rationale first** (`tests/handoffs/test_goal_gate_budget_fits_the_hook.py:39-41`):

> `#: Seconds reserved for everything the Stop hook does AFTER the gate: the Sonnet
> classifier's API call, the Telegram notification, and the auto-handoff.`
> `REQUIRED_MARGIN_S = 45`

And the code-side comment (`_goal_gate.py:124-126`):

> *"That leaves 60 s of headroom (180 − 120) for the classifier's API call, Telegram and the
> auto-handoff; the pin requires at least 45 of it, so the two numbers are a floor and the
> actual slack, not a disagreement."*

### They describe the same thing, and **`REQUIRED_MARGIN_S = 45` is the wrong one.**

They are not different quantities. The margin's own docstring names the classifier call as
its **first listed** component. The classifier's own declared per-attempt ceiling is 75. A
margin of 45 reserved for "the classifier's call + Telegram + handoff" is **smaller than the
classifier's call alone**. That is a direct contradiction, and it is the *margin* that is wrong,
because 45 was never derived from anything — it is a round number, and the code (75) is what
actually runs.

Worse, the margin under-counts by more than the classifier: the real non-check work is
`75 (classifier) + 20 (2 × git in work_fingerprint, :317/:325) + 5–10 (Telegram) ≈ 100–105 s`
single-attempt, or **~185 s retry-inclusive**. So:

- `REQUIRED_MARGIN_S = 45` under-counts the *measured* non-check work by **~55 s minimum**.
- The code comment's "60 s of headroom" is likewise wrong — 60 does not cover 100 either.
- **The s275 fix (600 → 120) made the test pass without making the budget fit.** `120 + 45 ≤ 180`
  is green; `120 + 100 ≤ 180` is false. The pin measured the wrong sum.

**A curious near-miss worth recording:** 45 happens to be *exactly* the retry-inclusive
per-attempt ceiling at the budget floor — `(180 − 60 − 30) / 2 = 45`. So the number is
defensible as a per-attempt classifier cap; it is indefensible as a *lump* margin covering
everything after the gate. Whoever picked it may have had the right instinct and homed it in
the wrong place.

### Counterfactual: if a 54–68 s model were adopted

Sizing from the measured Qwen p95 of 67.9 s, plus a cold load that for a 27B-q8 is materially
larger than gpt-oss:20b's (**inference, not measured** — no cold-load figure for those tags
exists on disk):

| Constant | Today | Would have to become |
|---|---|---|
| `OLLAMA_TIMEOUT_SEC` | 75 | **≥ 90** (p95 67.9 + cold load + margin); realistically 120 |
| `DEFAULT_CHECK_BUDGET_S` | 120 | **60** (its own hard floor, `test_…:95`) |
| `REQUIRED_MARGIN_S` | 45 | **≥ 120** single-attempt, **≥ 210** retry-inclusive |
| `settings.json` Stop `timeout` | 180 | **≥ 180** single-attempt, **≥ 270** retry-inclusive |

**What would then break:** technically, nothing — and that is the danger. No test constrains
any of it (§3a); the gate would simply start losing its budget to a slower classifier and the
outer 180 would start firing. What genuinely breaks is the **human budget**: ~68 s of dead air
at every turn end, which is the band `benchmarks/stop_classifier/RESULTS.md:20-22` disqualified
a priori without spending a warm cycle on it.

---

## 5. Recommended values for the two consumers — **and yes, they must differ**

They must differ because the **loss functions are opposite**, and the repo already has the
precedent: `services/api/config.py:181-189` decouples `llm_status_timeout_s = 3.0` from
`llm_request_timeout_s = 120.0` for exactly this reason — *"so a slow/half-down MS-S1 degrades
the poll fast instead of hanging for a generation-length window per poll."*

- **A benchmark timeout is a data-loss boundary.** `config.py:174-179` states it outright: *"a
  client-side timeout ABORTS the call and discards every token already produced."* A timeout
  costs you the datapoint. Loss function: strictly minimise timeouts → be generous.
- **A hook timeout is a human-latency boundary against a fail-closed default.** A timeout costs
  you a silent pause, which is the conservative outcome anyway (§2a). Loss function: bound the
  tail → be stingy.

Setting one number for both would either lose benchmark calls or tax every turn.

### (a) Benchmark run that must not lose calls: **keep 120 s; do not couple it to the hook**

`llm_request_timeout_s = 120.0` (`config.py:163-166`) is already **1.77× the measured p95** of
the slowest candidate (67.9 s, `benchmarks/intake_extraction/RESULTS.md` per-arm table) and
1.71× the worst per-*case* figure (70.0 s, `bs-03`). No call in the s273b three-arm run was lost
to a transport timeout — RESULTS.md reports **0 transport errors** across 11 artifacts and
"unscored on transport = 0" on every axis.

- **Recommendation: leave at 120 s.** Raise only if a run actually loses a call, and raise from
  a measurement, not a guess.
- If `num_predict` is raised above 1024 (which PLAN-0119 contemplates), re-derive it from
  PLAN-0119 AC-4's own rule — `cap / decode_rate + load + prefill < timeout` — and note that
  doubling the cap roughly doubles the worst-case call, so 2048 tokens on a Qwen arm needs
  ~180–240 s, not 120.

### (b) Production hook: **do not raise 75. Fix the prompt, then the invariant.**

The tradeoff, stated plainly: raising `OLLAMA_TIMEOUT_SEC` costs the human ~nothing at the
median (it is a ceiling, not a delay) and buys ~nothing in safety (a timeout already degrades to
the conservative `pause`). What it *does* buy is more auto-`proceed` continuations, and what it
costs is pushing an already-over-budget chain further past the outer 180 with its stranded-resource
hazard. That is a bad trade.

**Ranked, cheapest-first:**

1. 🔴 **Cut the system prompt. This is the whole answer, and it is already measured.**
   The shipped system prompt is **32,708 characters** (**MEASURED** this session:
   `_build_system_prompt(registry)` over the live `.claude/autonomy-triggers.md`; registry alone
   = 27,758 chars). The 2026-08-02 research held the user message and `format` schema fixed and
   varied only the system prompt, 36 live calls:

   | condition | chars | blank | accuracy | self-consistent | median latency |
   |---|---|---|---|---|---|
   | A baseline (live prompt) | 28,832 | 3/12 | 4/6 | **0/4** | **38.2 s** |
   | **B slim** | **1,520** | **0/12** | **12/12** | **4/4** | **8.4 s** |
   | C micro | 558 | 0/12 | 9/12 | 4/4 | 4.5 s |

   Slim is **4.5× faster, strictly more accurate, and self-consistent where the baseline is 0/4**,
   and *"the C5 case hit `OLLAMA_TIMEOUT_SEC=75` on 3/3 baseline runs while slim answered it
   correctly in 4–5 s."* Cutting the prompt buys back ~30 s/turn, makes 75 comfortable, and makes
   the budget chain satisfiable — with **none** of the human cost of a raised timeout. The research
   names one prerequisite: *"the gold set had no negative ADR case … add that case before shipping
   the slim prompt."*

2. **Raise the OUTER `settings.json` timeout, not the inner one.** 180 → **240**. This is free in
   human terms — nobody waits 240 s unless something actually takes that long — and it is the only
   change that makes the invariant satisfiable without touching either latency budget.

3. **Then set the constants so the invariant actually holds.** With the outer at 240:
   `DEFAULT_CHECK_BUDGET_S = 120` (unchanged), `OLLAMA_TIMEOUT_SEC = 75` (unchanged),
   `k=2` retry-inclusive: `120 + 150 + 30 = 300` — still over. So either accept `k=1` and pin the
   retry as bounded (`120 + 75 + 30 = 225 ≤ 240` ✅), or drop the budget to 90
   (`90 + 150 + 30 = 270`, needs 270). **Recommended:** outer **240**, budget **120**,
   `OLLAMA_TIMEOUT_SEC` **75**, and *bound the retry* — a second attempt should get the
   *remaining* wall-clock, not a fresh 75.

4. **If nothing else is done, lower rather than raise.** Keeping the outer at 180 forces
   `OLLAMA_TIMEOUT_SEC ≤ 30` at budget 120, or ≤ 45 at budget 60. A defensible minimal edit is
   `OLLAMA_TIMEOUT_SEC = 45` + `DEFAULT_CHECK_BUDGET_S = 60` → `60 + 90 + 30 = 180`, retry-inclusive
   and exactly at the wire. Tight, but it is the first configuration in this chain's history that is
   actually satisfiable as written.

5. **Fix `REQUIRED_MARGIN_S` so the pin measures the real sum.** Whatever is chosen, the margin must
   be *derived*, not chosen: `margin = k × OLLAMA_TIMEOUT_SEC + 20 (git) + 10 (pings)`. And the test
   must **import `_sonnet_classifier` and read `OLLAMA_TIMEOUT_SEC`** — otherwise the pin stays blind
   to the largest term in its own sum (§3a, measured `pre=75 post=3600` all-green). PLAN-0119 AC-4
   already specifies the guard: *"cap and timeout cannot be changed independently — raising one
   without the other reddens."*

---

## 6. Adversarial findings — stated rationales that do not match what the code does

1. 🔴 **`_sonnet_classifier.py:93`'s rationale is stale by ~3 months and a measured 64% prompt
   growth.** The comment reads *"warm p95 ~22s; headroom for a ~25s cold load + generation."* The
   22 s comes from `benchmarks/stop_classifier/RESULTS.md:15` (`gpt-oss:20b` p95 21.57 s), measured
   **2026-06-12** against what that file calls the *"real registry, pre-C5"*.
   **MEASURED this session:** the registry was **17,083 bytes** at the commit that introduced the
   constant (`3375778`, 2026-06-12 14:25:55 +0700) and is **27,990 bytes** at HEAD — **+64%**.
   `git log -S"OLLAMA_TIMEOUT_SEC"` returns **exactly one commit**: the constant has never been
   revisited. Its successor measurement (2026-08-02) recorded a **38.2 s median** and **3/3 timeouts**
   on C5. The rationale describes a prompt that no longer exists.

2. 🔴 **`REQUIRED_MARGIN_S = 45` is smaller than the single component it names first.** §4.

3. 🔴 **The retry doubles the classifier's budget and no comment anywhere accounts for it.**
   `_run_with_retry:766-771` can spend a second full `OLLAMA_TIMEOUT_SEC`. Neither `_goal_gate.py:124-126`,
   nor `test_…:39-41`, nor the s275 fix commit, nor the 2026-08-26 replay log's ~100 s decomposition
   counts it. Every budget statement in the repo is a **single-attempt** statement.

4. 🔴 **`.claude/commands/goal.md:36-38` still tells the criterion author the budget is 600 s.**
   Verbatim: *"the total deterministic budget at Stop is 600 s (`CLAUDE_GOAL_CHECK_BUDGET_S`)"*.
   The code has said **120** since s275 (`_goal_gate.py:116`). The **authoring surface instructs the
   author to size criteria against 5× what the gate will allow**; a criterion written to that advice
   is silently `skipped`/`timeout`, which is *unresolved, never a pass* (VX-2), and the gate then reads
   "checks NOT green" forever with no explanation. The s275 fix corrected the code and the schema
   example (`_goal_state.py:25-33`) but missed the command file. This is a live, unreported drift and
   arguably the most actionable defect in this review.

5. **The classifier is the only Ollama consumer with no `num_predict`.** `_call_ollama:714-726` sends
   `"options": {"temperature": 0}` only — no generation cap, against the app's global 1024
   (`config.py:168`). Already flagged in `docs/plans/0119-local-model-serving-policy.md:~120` and in
   `benchmarks/intake_extraction/RESULTS.md`. **Relevant here:** an uncapped call has no *server-side*
   bound, so `OLLAMA_TIMEOUT_SEC` is the *only* thing bounding it. On a model that reasons long, the
   timeout is not a safety net — it is the sole limit. That argues for capping generation rather than
   extending the deadline.

6. **A caveat on the transfer of the intake latency figures — say it plainly.** The 54.4–67.9 s
   (`qwen3.8:27b-mtp-q4_K_M`, p50/p95) and 57.8–66.8 s (`qwen3.8:27b-mtp-q8_0`) are **verified** at
   `benchmarks/intake_extraction/RESULTS.md` §"Per-arm figures". They are **per-attempt**, not per-case
   (the per-case column sums attempts and runs 22.7–70.0 s). Four reasons they do **not** transfer
   cleanly to the Stop classifier:
   - **Different workload.** Intake-extraction demands a full package JSON (135–381 content tokens plus
     a large reasoning pass); the classifier emits a decision + row list + one-line reason.
   - **Different cap regime.** Every intake call ran under `num_predict = 1024`, and **45 of 66 attempts
     hit it** (`done_reason = "length"`, 45/45). Those latencies are substantially *"time to burn 1024
     tokens"*, not time-to-answer. The classifier sends no cap at all (finding 5).
   - **Different model.** 27B vs `gpt-oss:20b`'s 20B; and the classifier's cold-load cost scales with
     the tag's on-disk size, for which **no figure exists on disk** for those Qwen tags.
   - **Different prompt shape.** The classifier front-loads a ~32.7k-char system prompt (prefill-heavy,
     decode-light); intake is the reverse.

   What *does* transfer is the ratio: on the same workload the Qwen arms were **2.4–2.5× slower** than
   `gpt-oss:20b` (54.4/21.5 and 67.9/28.7). Applied to today's Stop-classifier measurement, that would
   put a Qwen-27B classifier at ~15 s warm / ~85 s cold — **already past the 75 s timeout on a cold call.**
   That is an inference from a ratio, not a measurement, and should be labelled as such wherever it is used.

7. ⚠️ **An unresolved disagreement between two instruments — flagging rather than picking a winner.**
   The parent reports today's dispatcher measurement on the Stop-classifier prompt at **~6 s warm /
   ~36 s cold** with `gpt-oss:20b`. The 2026-08-02 research measured the **same model on the same
   shipped prompt** at a **38.2 s median** with 3/3 timeouts on one case. The registry has not shrunk
   since (27,758 chars now vs the research's 28,832-char baseline is within noise). Those two readings
   are hard to reconcile, and the most likely explanation is that the dispatcher probe did **not** send
   the full 32,708-char system prompt. **Before any timeout decision is taken on the strength of the
   ~6 s figure, confirm what system prompt that probe sent.** If it was a slim prompt, it measured
   recommendation 5.b.1, not the status quo.

---

## 7. One-paragraph answer

**Do not raise `OLLAMA_TIMEOUT_SEC`.** The Stop event's worst case is already **220 s
single-attempt / 305 s with the classifier's retry** against a **180 s** hook timeout, because the
goal gate's 120 s check budget and the classifier's 75 s call are **additive on 9 of the gate's 11
exits — including the default `enforce: false` warn path** (`_goal_gate.py:714-716` → `stop_continuation.py:540`).
The true ceiling at today's budget is **30 s**, not 75; the absolute ceiling at the budget's own
floor of 60 is **90 s single-attempt, 45 s retry-inclusive**. `REQUIRED_MARGIN_S = 45` is the wrong
constant — it is smaller than the single component it names first — but no test would ever tell you:
**measured, `OLLAMA_TIMEOUT_SEC` can be set to 3600 with the entire suite green.** The constant's
own rationale ("warm p95 ~22s") cites a June measurement against a registry that has since grown
**64%**, and its successor measurement recorded a 38.2 s median with 3/3 timeouts. The lever that
actually buys classifier latency is the **32,708-character system prompt** — measured at **8.4 s
median and 12/12 accuracy when slim, versus 38.2 s and 4/6 as shipped** — not the timeout. Fix the
prompt, raise the *outer* 180 (free, it is a ceiling not a delay), derive `REQUIRED_MARGIN_S` from
`k × OLLAMA_TIMEOUT_SEC + 30`, make the pin actually import the classifier — and, separately and
urgently, fix `.claude/commands/goal.md:36-38`, which still tells every criterion author the budget
is **600 s**.
