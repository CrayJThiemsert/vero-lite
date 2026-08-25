# PLAN-0115: The probe-battery driver ships — and the verification instrument stops being rebuilt wrong in `/tmp` every session

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-25
**Related ADRs:** ADR-0038 (C1 witnessed-RED promotion; D1 three-strike rule; D2-C1's refusal of a mechanical gate — reconciled below), ADR-0018 (goal gate — the Step 2 seam), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (drafting route + disclosure)
**Related lessons/PLANs:** #0047 (probe coverage — the shipped library half), #0026 (pre-committed read), #0007 (command output is evidence), PLAN-0099 (the method Step 4 promotes), PLAN-0114 Step 1 / session 253 (the incident record this PLAN answers)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored dispatch carrying Cray's three
> typed rulings (s253, 2026-08-25). The rulings are Cray's; the implementation
> designs, the surfaced decisions, and the fact-pack corrections below are
> drafter positions for ratification. Every `file:line` cited was opened with
> Read/Grep in this drafting session on 2026-08-25, except items explicitly
> marked *session-attributed* in §Residual. Independent review: Code at PR;
> ratification: Cray. Author≠reviewer separation: **INTACT**. Uncommitted
> draft — Code commits per ADR-009 D2.

## Goal

Ship the probe-battery **driver** as a tracked tool (`tools/probe_battery/`) so
the witnessed-RED discipline (CLAUDE.md §8, promoted by ADR-0038 C1) stops
being re-implemented from scratch in `/tmp` each session — s253 measured that a
fresh driver re-makes, by default, four defect classes a prior session had
already fixed. Close the two safety holes the s253 run exposed (the Stop-hook
goal gate evaluating a deliberately-mutated tree; the unbounded `drop_all`
teardown that hung 67 minutes), amend §8 so the binding rule *names the tool*
(Cray ruling 2), and promote PLAN-0099's flake-attribution method to a lesson
(Cray ruling 3).

## Cray's rulings (typed, s253 — LOCKED; restated for the record, not re-opened)

1. **Scope: "เอาตามที่แนะนำ"** — the recommended tiers (MUST / SHOULD / ALSO as
   carried into §Steps below).
2. **"แก้ §8 ให้ชี้เครื่องมือ"** — amend CLAUDE.md §8 so the witnessed-RED rule
   names the tool (Step 4a drafts the exact text).
3. **"เอา lesson 0099 ด้วย"** — include the lesson promoting PLAN-0099's method
   (Step 4b drafts it in full).

## Context — what s253 measured, verified against the tree this session

**No tracked driver exists** (grounded negative, re-verified 2026-08-25):
`tools/` enumerated — the probe machinery is exactly two things: the shipped
*library* half `tools/probe_coverage.py` (AST claim enumeration +
`render_report`; verdict fails on GAPS and STALE ids, `:201-205, :254-256`)
and `tools/probes/vero_bridge_probe.py`, which is an unrelated liveness probe
(the new package's README must disambiguate the two names). No `scripts/`
directory. `PROBE-VERDICT` appears only in prose (see correction F-2 below) —
no code implements a battery driver anywhere tracked.

**The four measured driver defects** (s253's `/tmp` driver; session-attributed
as incidents, but each maps onto a tree-verifiable seam):

1. **Crash credited as RED.** The driver keyed on `returncode == 0` and
   discarded captured output, so an `AttributeError` from a disabled `None`
   guard and a `KeyError` raised one line *before* the tracked assertion both
   counted as witnessed. The repo already knows this failure class —
   ADR-0038 D4's W-1 watch-list entry ("a probe's RED must name what broke",
   lesson #0043) — and W-1 now has its s253 recurrence; see SD-4.
2. **Over-crediting.** One reddened test marked ALL its claims witnessed,
   though a run stops at the first failing assertion (the exact
   one-mutation-one-assertion rule §8 already states in prose).
3. **Hand-rolled addressing.** The driver rebuilt `owner::source` keys while
   `Claim.stable_key` — which adds `occurrence` precisely to break the
   two-identical-asserts collision (`tools/probe_coverage.py:74-84`) — sat
   unused on the object it imported.
   `tests/tools/test_probe_coverage.py:183` ships the collision test.
4. **A tautological self-check.** An `EXEMPTION_OVERLAPS` check intersected
   the exemption set with a credit set that had already been filtered of
   exempted keys — empty by construction, printed as live evidence.

**Safety hole 1 — the goal gate vs a mutated tree** (verified):
`.claude/hooks/_goal_gate.py` runs `check` criteria via
`subprocess.run(argv, cwd=REPO_ROOT)` with no lock and no notion of a busy
tree (`:237-244`), and `work_fingerprint()` = sha256(HEAD + porcelain status)
(`:185-214`) — so a live mutation both (a) lets a Stop event record false
`fail` entries into `goal.json`'s append-only trail (observed s253,
unremovable by hand) and (b) reads as "new work", eligible to dispatch the
`goal-evaluator` against a deliberately-broken tree. Useful seams already
exist: `CHECK_SKIPPED = "skipped"` (`:131`, returned at `:226`), and
`_goal_state.py` does atomic tmpfile+`os.replace` I/O with a `CLAUDE_*`
env-override family for testability (its module contract, `:1-53`; mirrored in
`_goal_gate.py:69-70`).

**Safety hole 2 — the unbounded teardown** (verified):
`tests/db_support.py` defines `_LOCK_TIMEOUT = "10s"` with the comment "Fail
loudly rather than hang forever if a prior test leaked one" (`:83-85`) but
applies it ONLY to setup (`_reset_public_schema_once`, `:194`). The per-module
`db_engine` fixtures call `Base.metadata.drop_all` with no bound —
`tests/services/db/test_gate_state_machine.py:174-183` is the canonical
unbounded shape, and a `drop_all`-grep over `tests/` shows ~36 more fixture
sites like it. s253 measured a 67-minute hang: one `idle in transaction`
session, a three-deep lock chain, a second pytest queued behind it. The test
DB is scoped **per checkout, not per process**
(`worktree_scoped_test_url`, `tests/db_support.py:91-102`), so that second
pytest shares the first one's DB by design. **Donor pattern already in-tree:**
s253 bounded exactly one module —
`tests/services/db/test_continue_no_decision_run.py:174-183` sets
`SET lock_timeout = '20s'` before `drop_all`, with the incident written into
the comment. Step 3 generalizes it (mechanism = SD-1).

**The promotion gap** (verified with a live positive control): grepping
`forced reproduction|reproduce deterministically|frozen clock|deterministic
reproduction` across `CLAUDE.md`, `docs/lessons/`, `docs/adr/`,
`docs/conventions/`, `docs/runbooks/`, `.claude/skills/` returns **zero
matches**, while the same pattern over
`docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`
matches (`:38`, `:58`) — the zero is real, the search is live. PLAN-0099 is
cited on durable surfaces (lessons #0036/#0037, ADR-0038 C3) only for its
coverage ledger and store-at-write rule — never for its attribution *method*:
measure the mechanism at scale (528M clock samples, `0099:40-42`), compute the
predicted rate and match it to the observed one (P(flake) ≈ 0.9%/execution vs
the 1-in-3 suite failure, `:43-47`), rule out alternatives *by construction*
(`:48-55`), and force deterministic reproduction — three ways (`:56-60`) —
concluding the with/without comparison from one run per side plus reasoning
(`:61-68`), not repetition.

### Fact-pack corrections (dispatch asked; three found)

- **F-1.** "Every DB test module writes its own unbounded teardown" — every
  module **except one**: `test_continue_no_decision_run.py:174-183` is already
  bounded (s253's own fix). That file is the donor pattern, not a target.
- **F-2.** `PROBE-VERDICT` appears in **two** tracked files, not three —
  `docs/lessons/0047-…md:6` and `docs/lessons/0011-…md:80,84` — both prose.
  The grounded negative (no code emits it) is unchanged.
- **F-3.** The positive-control grep over PLAN-0099 matches **two lines**
  (`:38`, `:58`), not three hits. The control still proves the search live.

## Frame reconciliations (arguments this PLAN owes, not silent contradictions)

**R-A — `probe_coverage.py`'s "library-first" docstring (`:32-34`).** The
docstring anticipates *"a session's battery imports `enumerate_claims` and
`render_report`"* — a per-session battery script, not a shipped driver. That
framing drew the shipped/per-session boundary at the wrong seam, and s253 is
the measurement: all four defects lived in the un-shipped half (mutate,
restore, classify, credit), and none of them is visible to the shipped half by
construction — `render_report` sees claim keys and credit maps, never *how*
credit was earned. The correct seam: the **machinery** (atomic mutate,
SIGTERM-safe restore, outcome classification, one-claim crediting, mandatory
report) ships; the **probe definitions** (which mutation, which declared
claim, which expected direction) stay per-session *data* fed to the driver.
Step 1 updates the docstring to state the new seam; #0047's substance is
untouched.

**R-B — ADR-0038 D2-C1 refused form (c), "a mechanical gate"
(`0038:242-247`).** A vacuity *gate* — an automatic judge blessing greens —
was refused because a self-authored guard inherits its author's blind spot.
The driver is not that: it is an **instrument the author invokes**, whose
output (the coverage report + per-probe classifications) still goes through
review; it automates the mechanics, never the verdict's authority. The
out-of-scope cut "no CI / pre-commit auto-run" is the line that keeps it on
the right side of the refusal — crossing that line later would need an
ADR-0038 amendment, not just a workflow tweak.

**R-C — the gate lives on a tracked surface.** Per CLAUDE.md §4, a gate's
definition and do-not-act instruction must live tracked-and-scanned: Step 2's
logic goes in `.claude/hooks/_goal_gate.py` (tracked); the lock file under
gitignored `.claude/state/` is the ephemeral *state* the tracked gate reads,
never the gate itself.

**R-D — the process boundary.** The driver runs WSL-side (where pytest runs);
the Stop hook runs Windows-side (`settings.json` invokes `python
.claude/hooks/…`). A `fcntl` lock is invisible across that boundary, so the
lock is a JSON lockfile protocol on the shared filesystem, freshness-bounded
by writer-side heartbeat (WSL2's non-monotonic wall clock means mtime
comparisons must be generous and same-writer — design detail in Step 2).

## Acceptance Criteria

House rule applies to every AC below (§8): each load-bearing green is
witnessed RED by a named probe, one probe per assertion, positive controls
named for every absence/zero claim.

- [ ] **AC-1 (restore survives SIGTERM).** Scenario test spawns the driver as
  a child process against a tmp fixture project, waits until a mutation is
  measurably on disk (positive control: the subject's bytes differ from the
  snapshot — proving the mutation reached disk, not a no-op), SIGTERMs it, and
  asserts the subject is restored **byte-identical** (hash compare).
  Second assertion, own probe: after a simulated SIGKILL (child killed with
  no handler chance), the persisted snapshot manifest lets a follow-up
  `restore` invocation recover byte-identical, and the driver **refuses to
  start a new battery** while an unrestored manifest exists.
- [ ] **AC-2 (a crash is a refusal, not a credit).** Feed a probe whose
  mutation raises `AttributeError` before any tracked assertion; assert the
  outcome is classified `CRASHED` and **no claim is credited**. Positive
  control (its own probe): the same harness with a genuine
  predicted-assertion RED classifies `WITNESSED` and credits — otherwise a
  driver that refuses everything would pass this AC vacuously.
- [ ] **AC-3 (one claim per probe).** A probe reddening a test that carries
  two tracked claims credits **at most the claim whose assertion failed**; the
  report names the sibling claim as a GAP. Positive control: a second probe
  targeting the sibling credits it.
- [ ] **AC-4 (declared-claim match).** A probe that reddens a *different*
  assertion than the one it pre-declared is classified `MISFIRE` and credits
  nothing (pre-committed read discipline: crediting the accidentally-hit claim
  would let the result rewrite the prediction).
- [ ] **AC-5 (`stable_key` addressing is mandatory).** The driver addresses
  claims only via `Claim.stable_key`; on a fixture module with two identical
  asserts in one owner, crediting one leaves the other visibly uncovered
  (driver-level restatement of `tests/tools/test_probe_coverage.py:183`).
- [ ] **AC-6 (report is mandatory; self-checks are non-tautological).** Every
  battery run terminates in a `render_report` call and prints its verdict
  token; and the s253 tautology is replayed as a closed-incident oracle: an
  exemption overlapping a *declared* credit — computed from the pre-filter
  set — must be reported as an overlap. Witnessed RED by reconstructing the
  pre-fix shape (post-filter intersection) and showing the check go silent.
- [ ] **AC-7 (gate stands down under the lock — SHOULD tier).** With the lock
  held and an isolated `CLAUDE_GOAL_PATH` (hook-test hygiene), a Stop-event
  gate invocation returns `None`, runs **no** check subprocess, and the
  evaluations trail's length is unchanged (**delta** assert, not presence).
  Positive control, own probe: the identical fixture without the lock writes a
  trail entry — proving the gate was live, so the absence is not vacuous.
- [ ] **AC-8 (teardown reddens instead of hanging — SHOULD tier).** With a
  second session left `idle in transaction` holding a conflicting lock, the
  bounded teardown fails within the bound with a lock-timeout error naming the
  operation (the test itself carries an outer timeout so a regression hangs
  the test, not the suite — per the "DB race tests HANG instead of reddening"
  precedent). Plus a guard: no `drop_all` teardown in `tests/` without a bound
  (mechanism per SD-1), written rule-not-roster so a **new** module is caught
  (the guard walks the tree on disk, not the git index — the
  committed-file-guard blindness does not apply).
- [ ] **AC-9 (§8 names the tool).** CLAUDE.md §8's witnessed-RED bullet
  carries the Step 4a pointer sentence verbatim; a grep for
  `tools/probe_battery` in CLAUDE.md §8 is non-empty. (A docs AC — its
  "witness" is the review of the constitutional PR, not a pytest.)
- [ ] **AC-10 (the lesson exists and is honest about its status).**
  `docs/lessons/0048-…md` exists with the Step 4b text: advisory, states the
  rate-vs-cause distinction, records PLAN-0099's four moves with citations,
  and carries the below-threshold tally note instead of minting any rule.

## Out of Scope (explicitly cut, with reasons — Cray-ruled)

- ❌ **Porting the s253 battery onto the shared tool, and a `probe-battery`
  skill** — fast-follow PR; the driver must exist and settle first.
- ❌ **Any rule of the form "n≥2 observations on both sides"** — it would
  encode repetition-as-evidence, contradicting the repo's own best method:
  PLAN-0099 concluded its with/without comparison from one run per side plus
  mechanism reasoning (`0099:61-68`). Repeat-sampling establishes a *rate*;
  it does not establish a *cause* (Step 4b is this argument in lesson form).
- ❌ **Auto-running batteries in CI or pre-commit** — batteries mutate real
  source files; they stay agent/human-invoked. Also the R-B line: auto-run
  would turn the instrument into the mechanical gate ADR-0038 D2-C1 refused.
- ❌ **Teaching `tests/db_support.py` about the probe-battery lock** — the
  teardown bound (in scope) and the battery lock (Step 2) are different
  mechanisms for different actors; coupling them would make every DB test
  depend on battery state.
- ❌ **Fixing the Stop-timeout/check-budget mismatch beyond recording it** —
  unless Cray rules it in via SD-3; it was not in the ruled tiers and its
  incident-causality is unverified (§Residual).

## Steps

### Step 1: `tools/probe_battery/` — the driver (MUST)

New package: `tools/probe_battery/{__init__.py, _battery.py, README.md}` plus
`tests/tools/test_probe_battery.py` (unit) and
`tests/tools/test_probe_battery_scenario.py` (scenario — real driver → real
pytest subprocess → real report, on a self-contained tmp fixture project with
genuine modules and asserts; never against the live tree; §8's scenario rule).

Contract (each item traces to a measured defect or to the dispatch's MUST
list):

1. **Probe definitions are data.** A battery is a list of probes; each probe
   pre-declares: subject file, mutation (as an old→new edit applied by the
   tool), the target test node-id, and exactly one `Claim.stable_key` it
   predicts will redden (pre-committed read; AC-4).
2. **Atomic mutate.** Snapshot first (out-of-tree, under
   `.claude/state/probe_battery/<run>/`, with a JSON manifest: subject path,
   sha256, HEAD sha, pid, heartbeat); then write via tmpfile + `os.replace`
   (the `_goal_state.py` I/O posture) so a mid-write kill never leaves a
   truncated subject.
3. **Restore that survives SIGTERM.** `signal.signal(SIGTERM, …)` +
   `try/finally` restore (repo precedent for the handler shape:
   `services/engine/procedures/scheduler_daemon.py:197-204`); and because
   SIGKILL runs no Python, the *guarantee* is the persisted manifest: a
   `restore` subcommand recovers byte-identical, and a start with an
   unrestored manifest refuses to run (AC-1). POSIX-only signal scenario is
   acceptable — the driver runs WSL-side and CI is Linux; the platform marker
   states this.
4. **Outcome classification** distinguishes: `WITNESSED` (the declared
   assertion failed), `MISFIRE` (a different assertion failed), `CRASHED`
   (non-assertion exception, or a raise before the tracked line), `GREEN`
   (mutation applied — verified reached disk — but nothing reddened),
   `SETUP/COLLECT-ERROR`, `SKIPPED`, `NO-TESTS`. Implementation reads pytest's
   machine-readable failure record (`--junitxml` message/type + failing
   location), never bare `returncode` (defect 1; AC-2). Only `WITNESSED`
   credits, and it credits exactly one claim (defect 2; AC-3).
5. **`Claim.stable_key` addressing, mandatory** (defect 3; AC-5). No
   alternate keying path exists in the API.
6. **`render_report` is called on every run** — the driver owns the exit path
   so a battery cannot end without the #0047 §6 fourth-clause report; any
   printed self-check computes from pre-filter inputs (defect 4; AC-6).

Also in this step: update `tools/probe_coverage.py:32-34`'s docstring to the
R-A seam ("driver-first; per-session content is the probe definitions"), and a
README section disambiguating `tools/probe_battery/` (mutation battery driver)
from `tools/probes/` (live liveness probes).

### Step 2: cross-process lock + `_goal_gate.py` early-return (SHOULD)

- Driver acquires `.claude/state/probe_battery.lock` (JSON: pid, run id,
  HEAD sha, heartbeat counter + timestamp refreshed per probe) before the
  first mutation; releases after verified restore.
- `.claude/hooks/_goal_gate.py`: in `run_goal_gate`, **before** `_run_checks`
  and before any fingerprint read, a fresh lock → return `None` with a stderr
  note — no subprocess, no trail write, no Telegram (semantics = SD-2; the
  design intent is that a deliberately-mutated tree leaves **zero residue** in
  `goal.json`). Lock path honors a `CLAUDE_PROBE_BATTERY_LOCK` env override
  (the existing `CLAUDE_*` testability family, `_goal_gate.py:69-70`).
- Staleness (R-D): freshness is judged from the lock's own heartbeat fields
  with a generous bound (order of tens of minutes — WSL2 clock hazard); a
  stale lock is treated as **absent for gating** but produces a loud stderr
  warning naming the unrestored-manifest recovery path. A dead driver must
  not silence the gate indefinitely.
- Tests: AC-7's pair, with `CLAUDE_GOAL_PATH` isolated per the hook-test
  hygiene precedent; plus a stale-lock case asserting the gate proceeds and
  warns.

### Step 3: bound the `drop_all` teardown (SHOULD)

Mechanism contingent on SD-1; recommended form:

- `tests/db_support.py` gains a shared bounded-teardown helper (e.g.
  `async def drop_all_bounded(conn, timeout: str = "20s")` — `SET
  lock_timeout` then `drop_all`, the donor pattern from
  `test_continue_no_decision_run.py:174-183`, with the s253 incident comment
  moved to the helper as its rationale).
- Migrate the ~36 fixture sites (enumerate at execution via the `drop_all`
  grep; the count here is an estimate, the enumeration is the AC).
- Guard per AC-8: an AST/grep walk over `tests/` on disk failing any
  `drop_all` teardown not routed through the helper (rule, not roster).

### Step 4: the docs PR — §8 amendment + lesson 0048 (ALSO — rulings 2 + 3)

**4a — CLAUDE.md §8 amendment (ruling 2).** A pointer inside the existing
witnessed-RED bullet — not a new rule, so ADR-0038 D1 is not tripped and §4's
keep-it-short instruction is honored (the §8 pointer pattern already exists
twice: the ms-s1 skills pointer and the Lesson #0007 pointer). Constitutional
text is drafter-authored by convention; **Code commits this exact sentence
verbatim**, appended to the end of the witnessed-RED bullet:

> Probe batteries run through the shipped driver — **`tools/probe_battery/`**
> — never a from-scratch `/tmp` script: crash-vs-assertion crediting,
> one-claim-per-probe, `Claim.stable_key` addressing, SIGTERM-surviving
> restore, and the mandatory coverage report live in the tool, and a
> hand-rolled driver was measured (s253) re-making all four of its retired
> defect classes at once. Mechanics: the module README (PLAN-0115).

**4b — `docs/lessons/0048-repeat-sampling-establishes-a-rate-not-a-cause.md`
(ruling 3).** Advisory (a lesson does not trip ADR-0038 D1; only promotion
does). Full draft text for Code to write verbatim:

> # Lesson 0048: Repeat-sampling establishes a rate; measuring the mechanism establishes a cause
>
> **Status:** Advisory (ADR-0038 D1 — this lesson promotes nothing; it names
> a method so the method stops being unciteable)
> **Source:** PLAN-0099 (`docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`),
> promoted to a durable surface by PLAN-0115 (Cray ruling 3, s253)
>
> ## The gap this closes
>
> PLAN-0099 root-caused this repo's hardest intermittent, and its *method* was
> cited nowhere durable: a grep for `forced reproduction|reproduce
> deterministically|frozen clock|deterministic reproduction` across CLAUDE.md,
> lessons, ADRs, conventions, runbooks and skills returned zero matches
> (positive control: the same pattern matches inside PLAN-0099 itself, `:38`,
> `:58` — measured 2026-08-25). The repo cites 0099 for its coverage ledger
> and its store-at-write rule (lessons #0036/#0037, ADR-0038 C3) — never for
> how it *attributed* the flake.
>
> ## The method — four moves, in 0099's own record
>
> 1. **Measure the mechanism directly, at scale.** Not the flaky test — the
>    clock under it: 300 s tight loop, 528M samples, 20 backward steps, all
>    ≥ 400 ms (`0099:40-42`).
> 2. **Compute the predicted rate and match it to the observed one.**
>    P(flake) ≈ step-rate × exposure-window ≈ 0.9%/execution — matching the
>    observed 1-in-3 full-suite failure (`0099:43-47`). A mechanism whose
>    arithmetic reproduces the observed rate is attribution; a hunch that
>    survives N reruns is not.
> 3. **Rule out alternatives by construction, not by sampling.** Postgres
>    `now()` excluded by showing no `server_default` exists on any timestamp
>    column — a structural fact, worth infinite reruns (`0099:48-55`).
> 4. **Force deterministic reproduction.** Three ways — exact tie, −5 ms
>    inversion, frozen clock through the real HTTP path (`0099:56-60`). A
>    defect you can summon on demand needs no statistics at all.
>
> Where 0099 compared with/without a change, it ran **once per side** and
> concluded by reasoning over the mechanism (`0099:61-68` — the `<`
> experiment). That is the point: repetition was never what carried the
> conclusion.
>
> ## The distinction, stated once
>
> **Repeat-sampling establishes a RATE** — how often, with what variance;
> indispensable when the rate itself is the claim. **Measuring the mechanism
> and forcing deterministic reproduction establishes a CAUSE.** A rule of the
> form "n ≥ 2 observations on both sides" (considered and cut in PLAN-0115)
> would tax every comparison with repetition while buying no attribution —
> the repo's best-attributed defect used n=1 per side.
>
> ## Adjacent tally — recorded, not promoted (ADR-0038 D1.5 discipline)
>
> The cost-estimation class ("a pre-run estimate missed by ≥ 4×, root cause
> knowable in advance") stands at **two** distinct firings:
> `docs/logs/2026-07-05-plan0051-live-ab-results.md:40` (~4×, ~2 h vs ~30 min,
> root-caused to per-call latency) and s253's ~10× miss on the probe-battery
> session (session-attributed). Two < three: no rule is minted; this tally
> exists so the third firing can promote without archaeology.

Both files ride one small `docs/*` PR (§7 allows it; the constitutional edit
needs no gate — it is convention-routed through a drafter, which this PLAN
satisfies).

## Build sequence — and what ships if only one PR is affordable

1. **PR-A (Step 1, MUST)** — the driver + tests + docstring seam. The
   PLAN's reason to exist.
2. **PR-B (Step 4, ALSO)** — §8 amendment + lesson 0048. Two files, minutes
   of work, carries two typed Cray rulings: **never the cut**. Sequenced
   after PR-A only because §8 must not name a tool that does not exist yet.
3. **PR-C (Steps 2+3, SHOULD)** — lock + gate early-return + teardown bound.

**If only one PR is affordable: PR-A ships.** PR-B is deferred-not-dropped
(typed rulings; recorded as owed in STATUS). PR-C is the cut line — carried
as a named follow-up, not silently dropped, because each of its two holes has
a measured incident behind it.

## Surfaced decisions (for Cray — implementation-level; the three rulings above are not re-opened)

- **SD-1 — teardown-bound mechanism.** (a) edit ~36 fixtures in place with
  the donor pattern; (b) **[recommended]** shared `drop_all_bounded` helper in
  `tests/db_support.py` + migrate + rule-not-roster guard; (c) server-side
  (per-role `lock_timeout` on the test DB). Why Cray: (b) touches a shared
  test seam every DB module depends on; (c) is host-adjacent state. Reason
  for (b): one incident comment in one place, new modules inherit the bound
  by using the helper, and the guard catches the module that does not.
- **SD-2 — gate behavior under a fresh lock.** (a) **[recommended]** silent
  `None` + stderr note — zero residue in `goal.json`, which is the entire
  point of the guard; (b) a trail annotation ("skipped: battery lock") — more
  auditable but writes to the exact artifact being protected and interacts
  with PLAN-0097's warn-dedup reads. Why Cray: it changes what the Axis-B
  trail means during batteries.
- **SD-3 — the Stop-timeout/check-budget mismatch.** `settings.json:71` gives
  the Stop hook 180 s while `_goal_gate.py:104` budgets checks 600 s (no
  local override — verified). Fix in this PLAN (one-line alignment, e.g. Stop
  timeout ≥ budget + margin, or budget ≤ 150 s), or record-and-defer.
  **Recommend defer** (out-of-scope cut 5): the mismatch is a verified
  configuration fact but an *unverified* incident cause, and it was not in
  the ruled tiers. Why Cray: it is a harness-posture change either way.
- **SD-4 — ADR-0038 D4 watch-list W-1.** s253's crash-credited-as-RED is a
  recurrence of W-1 ("a probe's RED must name what broke", #0043 — already at
  2 firings + this one). Amending an Accepted ADR is G1-gated and D1.6
  prescribes an amendment pass at promotion. (a) **[recommended]** record the
  tally claim here and in lesson 0048's PR body; open the ADR-0038 amendment
  as its own follow-up dispatch (promotion is an obligation once counted —
  but the counting-and-amendment is a governance artifact of its own, not a
  rider on a tooling PLAN); (b) fold the amendment into PR-B. Why Cray:
  either way commits Cray to the D1.6 obligation (enforcement work becomes
  owed for the promoted class).

## Verification

- Steps 1–3: the AC-named probe pairs, run through the driver's own scenario
  suite (`tests/tools/test_probe_battery*.py`), full `pytest` + `mypy
  services/` + bare `ruff check .` per the offline-gate scope rule. Every
  zero/absence AC names its positive control inline (AC-1, AC-2, AC-7).
- Step 2 additionally: a manual end-to-end on the dev box — start a battery,
  trigger a Stop, read `goal.json` before/after (delta), release, trigger a
  Stop, observe the normal path. Evidence recorded in the PR body per the
  gate-evidence discipline.
- Step 4: PR review against the verbatim texts above; AC-9's grep.
- Closeout: PLAN stays **Draft** until Complete (G1 closeout precedent), then
  `git mv` to `done/`.

## Residual — asserted-not-verified register

- **The Stop-timeout orphan-pytest theory** (a 180 s-killed hook leaving a
  pytest child holding the test DB): configuration facts verified
  (`settings.json:71`, `_goal_gate.py:104`, no local override); causal link to
  any specific incident **not** verified. Carried in SD-3, not asserted.
- **s253's ~10× estimate miss** and the four `/tmp`-driver defect
  measurements: session-attributed (the `/tmp` artifacts are gone by design);
  their tree-visible seams are cited instead where they exist.
- **The exact unbounded-fixture count** (~36): estimated from a bounded grep;
  Step 3's execution enumerates and the AC-8 guard makes the number
  self-maintaining.
