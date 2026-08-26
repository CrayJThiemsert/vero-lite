# PLAN-0116: The rollup verdict moves out of the model — `tools/claim_rollup/` computes ALIVE / DEAD / NEEDS-EXECUTION from committed claims

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-26
**Related ADRs:** ADR-0038 (D2-C1 instrument-not-gate posture — this tool inherits the same line), ADR-0018 (the `goal-evaluator`'s refute-not-bless mandate — a *potential* future producer, not wired here), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (drafting route + disclosure)
**Related records:** `docs/logs/2026-08-26-sd-premortem-replay-experiment.md` (the four-run measurement this PLAN rests on — "the log" below), `docs/plans/done/0115-probe-battery-driver-and-verification-instrument-hardening.md` (donor pattern + the SD rulings that are this PLAN's ground truth), lesson #0047 (the claims/coverage vocabulary next door)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the
> in-harness `plan-drafter` subagent from a Code-authored dispatch carrying
> Cray's typed rulings (s256, 2026-08-26). The rulings are Cray's; the design,
> the ACs, and the surfaced decisions below are drafter positions for
> ratification. Fact-pack items were verified by Code at `main` = `13d11b7`
> this session; files cited below (`the log`, `done/0115`, the probe-battery
> README, `docs/plans/0000-template.md`) were opened with Read in this
> drafting session. Independent review: Code at PR; ratification: Cray.
> Author≠reviewer separation: **INTACT**. Uncommitted draft — Code commits
> per ADR-009 D2.

## Goal

Ship `tools/claim_rollup/` — a small deterministic tool that computes the
verdict **ALIVE / DEAD / NEEDS-EXECUTION / UNVERIFIABLE-FROM-TREE** for a
drafted decision option from a *committed* set of claims, where each claim
arrives with its `status` (VERIFIED / REFUTED / UNSETTLED), its
`load_bearing` flag, its citation, and (when unsettled) its probe spec. The
tool computes; it never infers, never reads the tree, never calls a model.
This implements the third row of the log's measured three-layer split —
*"rollup: ❌ 5 of 7 differed on an identical prompt → deterministic code,
never the model"* (log §Verdict) — and Cray's tool-first ruling: the tool
must be usable by **any** agent and must stand even if the `sd-premortem`
agent idea later dies. The tool's input vocabulary is CLAUDE.md §6's own:
an inherited premise is a claim, and a claim is VERIFIED, REFUTED, or
`asserted-not-verified` — this tool is the arithmetic that turns a ledger of
those into a verdict, reproducibly.

## Context — what four runs measured, and what this PLAN does about it

An LLM asked to judge drafted decision options against a byte-identical
replay tree produced **five different verdicts out of seven options when the
same prompt was run twice** (log §11). Claim-level citations were stable in
every run; the rollup was not. The sharpest case, SD-3(a): two runs derived
the *identical* arithmetic (≈ 279 s of Stop-path work against a 180 s Stop
timeout — component figures quoted from log §11) and one called it a
refutation (**DEAD**) while the other called it a *"measured consequence"*
(**ALIVE**). Nothing was measured differently; the runs disagreed about
whether the claim was **load-bearing**.

The rollup rule itself is four lines of arithmetic (restated in §Rollup
below). Four lines of arithmetic do not need a language model. What the model
was actually contributing — unreproducibly — was the *labelling*: which
claims are load-bearing, and whether a given refutation kills the option or
merely its wording. This PLAN moves the arithmetic into code and forces the
labelling to be a **committed, diffable input**.

### Trap 1 — the vacuous AC this PLAN refuses to write

The obvious acceptance test — "same input twice → same output" — is
**vacuous for deterministic code**: a pure function over a parsed file holds
that property by construction, so the test can never go RED for the reason it
claims and closes nothing (CLAUDE.md §8's load-bearing-green rule). It is
rejected. The AC that means something is a **replay of historical cases whose
ground truth is known**: the PLAN-0115 SD-1/SD-2/SD-3 options, whose real
rulings Cray typed at s254 (`done/0115` §"Cray's rulings (typed, s254)").
AC-1/AC-2 are built on that, and §Fixtures states exactly how the ground
truth is sourced and where its limits are.

### Trap 2 — moving the arithmetic does not move the variance

The measured instability lived in the model deciding **which claims are
load-bearing** (log §6, §11). If this tool *inferred* `load_bearing` — from
wording, from heuristics, from anything — the variance would simply relocate
into the tool's heuristics and nothing would be gained. Therefore
(design constraint DC-1): **`load_bearing` is a required per-claim input
field that the claim author commits to before any rollup can be computed.**
The tool computes; it never infers.

Stated honestly, and the PLAN must not overclaim: this removes variance from
the **arithmetic**, not from the **labelling**. What it buys instead is that
labelling instability becomes **visible and diffable at the claim level** —
the run-3/run-4 disagreement on SD-3(a) becomes a one-field diff between two
input files (AC-2 pins exactly this), reviewable by a human instead of buried
inside a verdict. Whether the labelling itself is stable across runs is
expressly **not measured by this PLAN** unless Cray rules it in — that is
SD-2 below, surfaced rather than decided.

## Design constraints (each traces to a measured defect or a typed ruling)

- **DC-1 — no inference path for `load_bearing` or `status`.** Both are
  required per-claim fields with **no default**; a claim missing either is
  INVALID-INPUT, never a guessed verdict. Trace: log §11 (identical
  arithmetic, opposite verdicts — the disagreement was load-bearing-ness);
  log §6 (the run-2 "wording defect" instruction flipped both regression
  controls, and the PLAN-0114 counterexample killed it as a rule).
- **DC-2 — the tool is a pure function of its input file.** No repository
  reads, no subprocess, no network, no model call, no clock-dependent
  behaviour in the verdict. This is the determinism boundary, and it is also
  what makes the tool usable by any agent (Cray's tool-first ruling): a
  caller supplies a file; the tool cannot be coupled to any producer.
- **DC-3 — fail-closed input contract** (Cray, typed, log §9 ruling 1: *"The
  agent's input contract is fail-closed"*). Malformed JSON, unknown `status`
  values, an empty claim list, **zero load-bearing claims** (see DC-3a), a
  VERIFIED/REFUTED claim without a citation, or a malformed probe spec →
  **INVALID-INPUT**: no verdict token is printed, exit code 2 (donor
  precedent: probe_battery's "bad battery definition").
  - **DC-3a — the vacuity guard.** "Every load-bearing claim VERIFIED" over
    a set with zero load-bearing claims is the empty-list trap CLAUDE.md §8
    names (*"'absent from the list' is satisfied by an empty list"*). A
    claim-set with no load-bearing claim gets no verdict — it gets refused.
- **DC-4 — `NEEDS-EXECUTION` is never free.** An UNSETTLED claim counts
  toward NEEDS-EXECUTION only with a **complete** probe spec: `action`,
  `pass_fail` (fixed before running), `cost` ∈ {cheap, medium, expensive} —
  the exact schema of the run-2 repair, which measurably cut the free-hedge
  rate 80% → 43% (log §5). A partial spec is not "supplied".
- **DC-5 — the ledger is total.** The report echoes **every** input claim —
  id, text, status, `load_bearing`, citation, probe spec, provenance —
  including non-load-bearing REFUTED ones (the "wording defect" findings run
  2 used to flip verdicts, log §6). They must stay visible for review; they
  never move the verdict. Recording is not retrieval: the report is the
  surface that makes a contested label findable.
- **DC-6 — the vocabulary is pinned and closed.** Exactly Cray's four
  verdicts; no fifth verdict, no scores, no confidence values, no ranking
  across options. Which option *wins* is Cray's decision, never an output of
  this tool.

## The rollup arithmetic (as ruled, plus the one case the ruling leaves open)

Computed **per option**, over that option's load-bearing claims only:

1. **DEAD** — at least one load-bearing claim REFUTED. Dominates everything:
   one refuted load-bearing claim kills the option regardless of what else
   remains unknown.
2. **ALIVE** — every load-bearing claim VERIFIED (and, per DC-3a, at least
   one exists).
3. **NEEDS-EXECUTION** — none refuted, at least one load-bearing claim
   UNSETTLED, and a runnable (DC-4-complete) probe spec supplied.
4. **UNVERIFIABLE-FROM-TREE** — none refuted, unsettled load-bearing claims
   exist, and **no** writable probe spec exists for any of them.

Non-load-bearing claims never change the verdict (they appear in the ledger
per DC-5). Consumer-side meaning, restated in the README from Cray's typed
ruling (log §9): **NEEDS-EXECUTION means BLOCKED** — the option does not
reach Cray until the measurement is performed.

**The mixed case is genuinely unspecified by the ruled text** — some
unsettled load-bearing claims carry runnable probe specs, others provably
cannot be probed from the tree. The four-line rule reads "*a* runnable probe
spec supplied" (∃) for NEEDS-EXECUTION and "*no* writable probe spec" for
UNVERIFIABLE-FROM-TREE, which literally makes NEEDS-EXECUTION dominate — but
whether that ∃-reading is the *intent* or an artifact of terse wording is not
this drafter's call. The tool will hard-code one reading forever. **SD-1
surfaces it**; the fixtures for the mixed case land only after Cray rules.

## Input / output contract (sketch — executor refines, constraints binding)

One input file describes one decision with one or more options
(JSON, mirroring `tools/probe_battery/`'s definitions-are-data posture):

```json
{
  "decision": "PLAN-0115 SD-2",
  "provenance": "reconstructed-from-record",
  "options": [
    {
      "id": "(b) trail annotation",
      "claims": [
        {
          "id": "C3",
          "text": "a battery trail entry is inert to the gate's control-flow reads",
          "load_bearing": true,
          "status": "REFUTED",
          "citation": ".claude/hooks/_goal_gate.py:405-407,583,600,411-419",
          "source": "docs/plans/done/0115-...md SD-2 measurement note",
          "probe": null
        }
      ]
    }
  ]
}
```

- `probe` (required when `status` = UNSETTLED and the claim is offered as
  probeable): `{ "action": ..., "pass_fail": ..., "cost": "cheap|medium|expensive" }`
  — the run-2 repair schema verbatim (DC-4).
- Optional per-claim `verified_at` (HEAD sha the citation was checked
  against): **echoed, never validated** (DC-2 — the tool reads no tree). The
  shelf-life problem (a premortem verdict expires when a premise changes —
  log §10, the PLAN-0114 SD-4 case) stays out of scope, carried as metadata
  a future consumer can act on.
- Optional per-claim `measurement` `{ "pattern": ..., "value": ... }` for
  count-based claims — echoed in the ledger so a count announces *which
  question it answered* (the log's middle layer: 64/53 vs 54/51 were both
  correct answers to silently different patterns, log §11). Advisory
  guidance in the README; the tool cannot enforce that a count is a count.
- Output: a human-readable report ending in a pinned verdict token per option
  (`CLAIM-ROLLUP: <VERDICT> — <decision> <option-id>`), plus `--json` for
  machine consumers. Exit-code mapping is **SD-3** (surfaced below).

## Fixtures — provenance, stated honestly

**The gap:** the full claim-sets from the four runs live only in a session
transcript. The merged log records verdicts and *selected* citations, not
complete claim-sets. Faithful reconstruction of what the runs emitted is
impossible, and pretending otherwise would present a backfill as a
measurement.

**Therefore the fixtures are hand-authored from the record** — the log plus
the archived `done/0115` SD sections — not reconstructions of any run's
output. Every fixture file carries `"provenance": "reconstructed-from-record"`
at top level (repo convention: a backfilled value is surfaced as such, never
presented as measured), and every claim carries a `source` pointer into the
log or `done/0115`. The ground truth an expected verdict is checked against
is **Cray's typed ruling or a recorded measurement**, never a run's output.

| # | Fixture (claim-set snapshot) | Expected | Ground-truth trace |
|---|---|---|---|
| F1 | SD-2(b), post-measurement: control-flow-inert claim load-bearing + REFUTED (`_goal_gate.py:405-407, :583, :600, :411-419` — record-quoted) | **DEAD** | typed: *"Both fail on measurement"* (`done/0115` s254 ruling 2) |
| F2 | SD-2(a), post-measurement: stderr-visibility claim load-bearing + REFUTED (exit-0 stderr contract; debug log 0 files — record-quoted) | **DEAD** | same typed ruling |
| F3 | SD-2(a), draft-time: same claim UNSETTLED + complete cheap probe spec | **NEEDS-EXECUTION** | *reconstructed* — consistent with run-1 P1's pre-committed read (log §3) |
| F4 | SD-1(b), draft-time: "~36 sites" effort claim load-bearing + UNSETTLED + probe = the pinned grep, cheap | **NEEDS-EXECUTION** | log §4 Defect A: *"`NEEDS-EXECUTION` was the correct answer"* |
| F5 | SD-1(b), post-grep: effort claim VERIFIED (54 sites / 51 files measured, `done/0115` Step 3) | **ALIVE** | typed: SD-1 → (b) (`done/0115` s254 ruling 1) |
| F6 | SD-3(b) record-and-defer: read-decidable claims VERIFIED | **ALIVE** | ruled: SD-3 → defer as recommended; run-2 repaired control P3′ (log §5) |
| F7a/F7b | SD-3(a) pair: the ≈ 279 s > 180 s arithmetic claim REFUTED in both files; `load_bearing: true` in F7a, `false` in F7b — otherwise byte-identical | **DEAD** / **ALIVE** | **deliberately none** — the record contains no ruling on which labelling is correct; the AC pins the *flip property*, not a winner (asserting one would be a backfill) |

F3 and F7's statuses are reconstructions of the *draft-time knowable state*
and are marked so in the fixture files. Line citations inside fixture claims
(e.g. `_sonnet_classifier.py:93`) are **record-quoted** from the log /
`done/0115`, not re-verified by this PLAN — correct provenance, since the
fixtures encode what the record says, and the tool never resolves citations
(DC-2).

## Acceptance Criteria

House rule (CLAUDE.md §8): every AC-closing green below is witnessed RED
through the shipped driver — `tools/probe_battery/`, never a `/tmp` script —
one probe per assertion, positive controls named for every absence/refusal
claim. Each AC names its witness.

- [ ] **AC-1 (replay of ruled history — the anti-vacuous determinism AC).**
  The scenario suite drives the real CLI over fixtures F1–F6 and gets exactly
  the ground-truth verdicts in the table above, each traced in-fixture to its
  typed ruling or recorded measurement. *A "same input twice, same output" AC
  was considered and rejected as vacuous — for a pure function it holds by
  construction and cannot go RED for the reason it claims (Trap 1).*
  **RED witness:** probe-battery mutations of `_rollup.py`, one per tracked
  assertion — e.g. deleting the DEAD-dominates clause must redden the F1
  assert; making REFUTED non-load-bearing claims count must redden the
  F7b-adjacent control; inverting the DC-4 conjunct must redden F4's
  NEEDS-EXECUTION assert. Under each mutation the sibling asserts stay green
  (the one-probe-one-assertion rule).
- [ ] **AC-2 (the §11 sharpest case becomes a one-field diff).** F7a → DEAD
  and F7b → ALIVE; and the test asserts the two fixture files differ in
  **exactly one field** (`load_bearing` on the arithmetic claim), pinning the
  property that the run-3/run-4 disagreement is now expressible — and
  reviewable — as one input line. **RED witness:** a mutation that makes the
  verdict insensitive to `load_bearing` on refuted claims reddens the
  F7a/F7b divergence assert; corrupting a second field in F7b reddens the
  exactly-one-field assert (its own probe).
- [ ] **AC-3 (no inference path — DC-1).** A fixture with `load_bearing`
  missing on one claim, and a fixture with an unknown `status`, each produce
  INVALID-INPUT: exit 2, **no verdict token** on stdout. Positive control
  (own probe): the well-formed sibling fixture still computes — so the
  refusal is not refuse-everything. **RED witness:** a mutation introducing a
  `load_bearing` default (`.get("load_bearing", True)`) reddens the refusal
  assert; the positive control stays green under it.
- [ ] **AC-4 (vacuity guard — DC-3a).** A claim-set whose claims are all
  `load_bearing: false` → INVALID-INPUT, never ALIVE. Positive control: a
  minimal one-verified-load-bearing-claim fixture → ALIVE. **RED witness:**
  a mutation deleting the zero-load-bearing guard reddens the refusal assert
  (the tool would return the vacuous ALIVE).
- [ ] **AC-5 (NEEDS-EXECUTION is not free — DC-4).** An UNSETTLED
  load-bearing claim whose probe spec is absent, or missing any of
  `action` / `pass_fail` / `cost`, or whose `cost` is outside the enum, does
  **not** count toward NEEDS-EXECUTION (disposition of the resulting option
  verdict per SD-1's ruling). Traces to log §4 Defect B: a costless
  NEEDS-EXECUTION appeared in 4 of 5 options; the spec requirement measurably
  cut it to 43%. **RED witness:** a mutation accepting a partial spec
  reddens the assert (the fixture would yield NEEDS-EXECUTION).
- [ ] **AC-6 (total ledger — DC-5).** The real rendered report (read from the
  scenario CLI run's stdout, not from an internal structure) contains every
  input claim's id, status, and `load_bearing` flag — including a
  non-load-bearing REFUTED claim, which must appear *and* not move the
  verdict. **RED witness:** a mutation that drops non-load-bearing claims
  from the renderer reddens the presence assert; its verdict assert stays
  green under that mutation (proving the two are independently witnessed).
- [ ] **AC-7 (scenario test per §8 — real producer into real consumer).**
  `tests/tools/test_claim_rollup_scenario.py` runs the real CLI
  (`python -m tools.claim_rollup`) as a subprocess over the real fixture
  files on disk and parses the real stdout — no stubbing of parser, rollup,
  or renderer on either side of the seam. Realistic data = the PLAN-0115
  replay fixtures (realistic by construction: they encode a real governance
  incident end-to-end). The test fails if the CLI emits no verdict token — a
  scenario that drives nothing does not satisfy §8. **RED witness:** AC-1's
  and AC-2's probes run through this path; additionally a mutation breaking
  `__main__.py`'s wiring (CLI parses but never calls the rollup) reddens the
  no-token assert.
- [ ] **AC-8 (README opens with the refusals table).** `tools/claim_rollup/README.md`
  opens with a **"What it refuses to do"** table (donor shape:
  `tools/probe_battery/README.md`), every refusal tracing to a measured
  defect or typed ruling — at minimum: refuses to infer `load_bearing`
  (log §11); refuses a verdict on zero load-bearing claims (§8 empty-list
  trap); refuses a free NEEDS-EXECUTION (log §4 Defect B / §5); refuses to
  read the tree or call a model (DC-2 / log §Verdict row 3); refuses to rank
  options or recommend (DC-6 — the decision table stays Cray's). Also:
  the NEEDS-EXECUTION-means-BLOCKED consumer note (log §9 ruling 1), and a
  disambiguation table for the two senses of "claim" now in `tools/`
  (`probe_coverage.Claim` = an assertion in a test; a claim here = an
  evidence assertion about a decision option). **Witness:** a docs AC — PR
  review against this list plus a non-empty grep for `refuses` and
  `NEEDS-EXECUTION` in the README (the `done/0115` AC-9 precedent: the
  witness is the review, not a pytest).

## Out of Scope (explicitly cut, with reasons)

- ❌ **No `sd-premortem` agent is built by this PLAN.** No `.claude/agents/`
  file, no dispatch template, no agent-side claim-emission contract. Cray's
  typed ruling: tool first, agent later; the tool must stand alone if the
  agent idea dies. (The log's own instruction, §10: no PLAN, no ADR, no
  agent file for `sd-premortem` as designed.)
- ❌ **No model invocation and no repository reads inside the tool** (DC-2).
  The tool never verifies a claim itself — statuses arrive as committed
  inputs. Verification of claims stays with the caller (and stays
  adversarial per ADR-0018's refute-not-bless mandate).
- ❌ **No labelling-stability measurement** — surfaced as SD-2, not decided
  here. If Cray rules it out, it is recorded in §Residual as expressly open.
- ❌ **No staleness / shelf-life validation.** A premortem verdict expires
  when a premise changes (log §10, the PLAN-0114 SD-4 case); this tool only
  echoes `verified_at` metadata. Modelling expiry is future work with its
  own design questions.
- ❌ **No CI, hook, gate, or dispatcher wiring.** The tool is an instrument a
  caller invokes, not a mechanical gate — the same ADR-0038 D2-C1 line the
  probe-battery driver holds. Wiring a verdict into any automated gate would
  need its own governance artifact.
- ❌ **No cross-option ranking, scoring, or recommendation output** (DC-6).

## Steps

### Step 1: core — schema + arithmetic (`_schema.py`, `_rollup.py`)

New package `tools/claim_rollup/{__init__.py, _schema.py, _rollup.py}`.
`_schema.py` parses fail-closed into typed objects (DC-1/DC-3/DC-3a/DC-4
enforced at parse; every refusal carries a reason string naming the claim
id). `_rollup.py` is the pure verdict function implementing §Rollup —
including the SD-1 ruling once made. Type hints, mypy-clean, ruff-clean
(§8). Unit suite `tests/tools/test_claim_rollup.py` covers the refusal
matrix and the arithmetic edges (all-verified, one-refuted-dominates,
unsettled±spec, non-load-bearing-refuted-inert).

### Step 2: CLI + report + README (`__main__.py`, `_report.py`)

CLI accepts one or more claim-set files; renders the DC-5 total ledger; ends
each option with the pinned verdict token; `--json` for machine output; exit
codes per SD-3's ruling (INVALID-INPUT = 2 either way, donor precedent).
README per AC-8, donor-shaped on `tools/probe_battery/README.md`.

### Step 3: replay fixtures + scenario suite + witness battery

Hand-author F1–F7 under `tests/tools/fixtures/claim_rollup/` per §Fixtures
(provenance-marked, per-claim `source` pointers; F-mixed lands only after
SD-1 is ruled). Ship `tests/tools/test_claim_rollup_scenario.py` (AC-7). At
execution, run the AC witness battery **through `tools/probe_battery/`** and
record the coverage report + probe evidence in the PR body per the
gate-evidence discipline.

**Build sequence: one PR.** The tool without its replay suite has no
evidence its arithmetic matches the ruled cases; the suite without the tool
drives nothing. Steps 1–3 are one deliverable.

## Surfaced decisions

- **SD-1 — the mixed case: some unsettled load-bearing claims carry runnable
  probe specs, others provably cannot be probed from the tree.** The ruled
  four-line arithmetic does not specify it (see §Rollup). Options:
  - **(a) [recommended]** ∃-reading — **NEEDS-EXECUTION dominates
    UNVERIFIABLE-FROM-TREE**: any runnable spec on an unsettled load-bearing
    claim → NEEDS-EXECUTION; the ledger flags every spec-less unsettled
    claim, so after the probes run, a re-roll lands on
    UNVERIFIABLE-FROM-TREE honestly if those remain. *Reason:* under
    "NEEDS-EXECUTION = BLOCKED", (a) keeps the option blocked while cheap
    measurements are outstanding — and a probe result can REFUTE, producing
    DEAD, which dominates everything; letting the option surface as
    UNVERIFIABLE while runnable probes sit unrun would recreate the free
    hedge the run-2 repair measurably closed. Matches the literal ruled text.
  - **(b)** ∀-reading — UNVERIFIABLE-FROM-TREE unless *every* unsettled
    load-bearing claim has a runnable spec. *Consequence:* strictest about
    what "verifiable" means, but surfaces the option to Cray with cheap
    probes unrun.
  - **(c)** a compound verdict naming both. *Consequence:* breaks DC-6's
    closed vocabulary; every consumer must then parse a fifth shape.
  - *Why Cray:* this hard-codes forever what Cray's typed four-line rule
    means in the one case its wording leaves open — an interpretation of a
    typed ruling is Cray's to fix, not the drafter's.
- **SD-2 — should this PLAN also measure whether the labelling itself is
  stable across runs?** (Mandated surfaced, not decided.) The tool removes
  variance from the arithmetic only; whether an LLM emits the same
  `load_bearing` flags on repeated identical dispatches is unmeasured.
  Options:
  - **(a)** include a bounded rider: N repeated claim-emission dispatches in
    the tool's input format against a fixed replay tree; diff the
    `load_bearing` flags file-to-file (the tool makes this a pure file
    diff). *Consequence:* answers now whether the residual variance lives in
    labelling, at the cost of N dispatches plus the log's full blinding
    discipline (replay tree, leak greps, pre-committed reads).
  - **(b) [recommended]** exclude: ship the tool; run the measurement as its
    own experiment afterwards, log-recorded like the four-run record.
    *Reason:* Cray ruled tool-first; the measurement is an experiment-class
    artifact with its own discipline, and the tool is precisely the
    instrument that makes it cheap later. *Consequence:* the question ships
    expressly open, recorded in §Residual.
  - *Why Cray:* it sets the scope boundary between a build PLAN and a
    measurement experiment — the same boundary Cray has ruled on twice this
    week (tool-first; record-then-escalate).
- **SD-3 — does the exit code encode the verdict?** Options:
  - **(a)** exit 0 for any successfully computed verdict; the verdict lives
    in the token / `--json` only. *Consequence:* clean logs (an honest DEAD
    is not a process "error"), but a lazy consumer checking only `rc` treats
    DEAD as success — fail-open by default.
  - **(b) [recommended]** donor-style distinct codes: 0 = ALIVE, distinct
    nonzero per non-ALIVE verdict, 2 = INVALID-INPUT. *Reason:* shell
    chaining (`&&`) becomes fail-closed by construction — only ALIVE
    proceeds — which is the posture of Cray's NEEDS-EXECUTION-means-BLOCKED
    ruling; and it follows the probe-battery precedent (exit 0 = PASS,
    1 = FAIL). *Consequence:* orchestration logs show nonzero exits for
    normal DEAD verdicts; consumers must read the code table.
  - *Why Cray:* this is the tool's contract with every future consumer,
    including whatever agent workflow eventually wraps it — the two options
    fail differently under a careless consumer, and which failure is
    acceptable is an operating-posture call.

## Verification

- The AC-named witness battery, run **through `tools/probe_battery/`** (§8
  as amended by PLAN-0115 — never a `/tmp` driver), one probe per tracked
  assertion, positive controls for every refusal/absence claim; coverage
  report + evidence in the PR body.
- Full offline gate at CI scope: full `pytest`, `mypy services/`, bare
  `ruff check .` — plus `mypy tools/claim_rollup` locally (§8 requires new
  code mypy-clean regardless of CI's scope; see §Residual).
- No live runs, no host state, no DB: the tool is pure (DC-2), so the
  offline oracle is the entire gate here.
- Closeout: PLAN stays **Draft** until Complete (G1 closeout precedent),
  then `git mv` to `done/`.

## Residual — asserted-not-verified register

- **The four runs' full claim-sets are unrecoverable** (transcript-only; the
  log records verdicts + selected citations). The fixtures therefore do not
  and cannot claim to mirror what any run emitted; their ground truth is the
  typed rulings and recorded measurements only (§Fixtures). Any future claim
  that a fixture "replays run N" would be false — the fixtures replay the
  *record*.
- **Labelling stability across runs: expressly unmeasured** unless SD-2(a)
  is ruled. If SD-2(b) is ruled, this line is the standing record that the
  question is open, so it cannot silently become an assumed property.
- **Whether CI's mypy scope covers `tools/`** — asserted-not-verified (the
  offline-gate convention names `mypy services/`); the executor checks the
  CI config at execution. §8's new-code cleanliness applies locally either
  way.
- **Record-quoted line citations inside fixtures** (e.g.
  `_sonnet_classifier.py:93`, `_goal_gate.py:405-407`) are quoted from the
  log / `done/0115` as fixture *content*, not re-verified against the live
  tree by this PLAN — correct provenance under DC-2 (the tool never resolves
  citations), and re-verification is meaningless for encoding what the
  record said at ruling time.
- **F3's and F7's draft-time statuses are reconstructions** of the knowable
  state at draft time, marked as such in the fixture files (repo convention:
  backfilled values are surfaced as reconstructed).
