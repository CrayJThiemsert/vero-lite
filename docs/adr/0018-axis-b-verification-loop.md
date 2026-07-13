# ADR-0018: Axis-B Verification Loop — `/goal` Stop-hook gate + `goal-evaluator` subagent

**Status:** Accepted
**Date:** 2026-06-10 (Accepted — ratified by Cray; SD-1 resolved = narrowed Write); **V2 Amendment** 2026-07-13 (Accepted — SD-0…SD-4 ratified as-recommended by Cray; discharges the D5 warn-only deferral + OQ-8 blocking-mode promotion — see §V2 Amendment below)
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-013 (autonomy-axis relocation — harness primitives are Code-built per D1; **this ADR applies that boundary**: the gate + evaluator are Code-authored), ADR-009 (D1 — this ADR is Cowork-drafted under the interim process; D2 — only Code commits; D3 — K-1/K-2 workflow used for the companion handoff), ADR-0017 (track-1 precedent off the same harness review; D7 harness-as-plugin forward link → OQ-8 here), ADR-0016 (D5 product-side `Procedure.goal` — a **distinct concept**; see D2 NB below), ADR-012 (D4.3 author≠reviewer disclosure), PLAN-0008 (in `done/` — the `Stop` continuation loop + Sonnet classifier this gate composes with), PLAN-0009 (subagent topology — the Step 5c dispatch-block spawn pattern + Step 1b subagent contract reused here), PLAN-0010 (scheduled-task autonomy loop — the unattended-run scope in D5), CLAUDE.md §6 (tier table), §7 (PR flow — explicitly NOT gated in v1, D5). Authoring dispatch: `.claude/handoffs/session-51/2026-06-10-0147-code-axisb-verification-loop-adr-dispatch.md`.

> **Drafting provenance.** Drafted (uncommitted) by Cowork in Tier-1
> governance-authoring mode under the unchanged **ADR-009 D1** interim process
> (ADR-013's relocation of governance authoring into a Code subagent is phased
> and not yet executed; ADR-013 OQ-1 retains Cowork as advisory governance
> drafter). ADR number **0018** confirmed free before drafting (G2 gate):
> `docs/adr/` tops at 0017; **0011 stays reserved** for the action-approval /
> audit framework (intentional gap per ADR-013 OQ-2 — not consumable); 0014 is
> WITHDRAWN. Code commits this draft per ADR-009 D2.
> **Author≠reviewer disclosure (ADR-012 D4.3):** the decision *directions* in
> D1–D7 were deliberated in this same Cowork session (a pre-draft consultation
> in which Cray reviewed and approved the per-OQ directions before drafting
> began); the OQ framing originates in the Code dispatch. The
> independent-deliberation check is therefore **partially exercised** (Cray
> adjudicated directions pre-draft); Code's R2 review + Cray's ratification at
> merge remain the independent checks on this text.

## Context

### The Axis-B gap (why this ADR exists)

The 2026-06-09 harness-engineering review (vero-lite vs Anthropic's public
guidance) reached a two-axis verdict. **Axis A (governance / safety)** — the
deterministic `pretooluse_*_deny` family + the Sonnet transcript classifier —
is at the frontier; nothing to fix. **Axis B (task-completion /
verification)** is thin: every PLAN carries Acceptance Criteria and every
STATUS closeout hand-writes a `Verification:` line, but **nothing
programmatically checks "did this turn actually satisfy its goal?" before the
agent stops**. There is no evaluator subagent and no goal gate. Anthropic's
#1 stated harness lesson — *give the agent a check it can run; separate the
critic from the creator* — is unimplemented.

Track 1 off that review (Skills adoption + `CLAUDE.md` slimming → ADR-0017) is
complete. This ADR opens **track 2**, flagged throughout STATUS as the
deferred *"Axis-B verification-loop track (evaluator subagent + `/goal`
Stop-hook gate)."*

### External grounding (embedded in the authoring dispatch §2)

Three Anthropic Engineering pieces ground the design (researched 2026-06-09;
reproduced inline in the dispatch because the dispatch is gitignored and
Cowork cannot fetch URLs):

- **"Effective harnesses for long-running agents" (2025-11-26)** — the goal
  must be a **durable artifact with a checkable pass/fail state** (the
  feature-list JSON where every item starts failing), not a chat message;
  compaction is insufficient — agents re-ground on **structural artifacts**.
- **"Harness design for long-running apps" (2026-03-24)** — a
  planner/generator/**evaluator** loop; the evaluator is a **distinct agent
  with its own context, prompted to find failure, not to bless** ("separate
  the critic from the creator").
- **"How we built Claude Code auto mode" (2026-03-25)** — the classifier is
  **reasoning-blind + injection-resistant** (the agent's own reasoning is
  stripped from classifier input); a task must not be able to talk its way
  past a gate.

### What the design must compose with (verified at HEAD this session)

- **`.claude/hooks/stop_continuation.py`** (read in full): on `Stop`, the
  flow is re-entry guard (`stop_hook_active`) → L1 turn-boundary reset →
  **chain-cap check** (`depth ≥ cap(8)` → Telegram + reset + release) →
  Sonnet classifier → `proceed` (block + depth++) / `dispatch` (block with a
  spawn instruction + depth++) / `pause` (reset chain, stop fires). Two
  load-bearing precedents reused below: **(a)** `_sonnet_classifier.py` is a
  **sibling module invoked from inside the hook**, not a second hook; **(b)**
  *the hook cannot spawn a subagent* — the PLAN-0009 Step 5c **dispatch-block
  arm** has the hook emit a `block` whose reason instructs the main agent to
  spawn via the Agent tool on its next turn.
- **`.claude/settings.json`**: the `Stop` matcher `*` carries exactly one
  hook today (`stop_continuation.py`). Adding a *second* Stop hook would
  introduce unverified multi-hook block-ordering semantics — avoided by D4.
- **Subagent siblings** (`.claude/agents/`): `explore-research`,
  `plan-drafter`, `status-scribe` share a proven contract — tools allowlist +
  `disallowedTools` (Bash/WebFetch/Agent), a PreToolUse write-deny hook,
  `maxTurns: 30`, **self-contained dispatch payload with no parent
  transcript**, a binding output schema with an author≠reviewer disclosure
  stamp, bounded summary ≤ 1k tokens, an adversarial-hardening section.
  `status-scribe` is the closest exemplar: Write narrowed to a single file by
  a dedicated deny hook.
- **Autonomous runs**: PLAN-0010's loop consumer runs unattended turns — the
  gate has the most value where no human is watching (D5).
- **Known failure mode**: the Axis-A Sonnet classifier **fail-closes** on
  infrastructure failure (any transport/billing error → `pause`). That is
  safe *for the classifier* because its fail-state stops the session. A goal
  gate has the **opposite geometry**: a gate that fail-closed by *blocking*
  Stop on a dead API would push the agent back into the loop it cannot
  satisfy — a wedge (bounded at chain-cap 8, but 8 futile turns). D4 decides
  the fail-semantics deliberately around this asymmetry.

## Decision

Seven decisions (D1–D7) resolve the dispatch's OQ-1…OQ-7; OQ-8 stays a
non-binding backlog under Open Questions. Scope discipline: this is a
**minimal first prototype that proves the loop** — goal declared → work done →
evaluator checks → gate records/annotates — not a maximal build (Anthropic's
"simplify the harness on capable models" caution applies).

### D1: Hybrid mechanism — deterministic check layer + LLM evaluator subagent (resolves OQ-1)

Verification mirrors the proven Axis-A two-layer pattern (deterministic hooks
+ Sonnet classifier), transposed from *governance* to *verification*:

1. **Deterministic layer (in the gate, D4).** Every acceptance criterion that
   reduces to an **exit code** is declared in the goal artifact as a
   `kind: check` criterion with an explicit command (e.g. `pytest -q`,
   `ruff check`, `mypy --strict`, a file-existence test). The gate runs these
   as subprocesses and records per-criterion pass/fail. Cheap, fast,
   un-arguable.
2. **LLM layer (the `goal-evaluator` subagent, D3).** Criteria that cannot be
   reduced to an exit code (e.g. *"the ADR resolves OQ-1…OQ-7 with
   decisions"*, *"the doc follows the template shape"*) are declared as
   `kind: judge` criteria and assessed by the evaluator subagent — spawned
   via the existing Step 5c dispatch-block arm, never by the hook itself.

**The split rule:** *if you can write the criterion as a command whose exit
code answers it, you must* (`check`); *only judgment residue goes to the LLM*
(`judge`). A goal with zero `judge` criteria never spawns the evaluator —
deterministic-only goals cost no tokens.

- **Rationale:** the Axis-A hybrid is production-proven in this exact harness
  (N=3 live hook-fire events; classifier conservatism verified live). The
  split keeps the LLM out of every check it is not needed for, which is both
  the cost posture and the reliability posture (deterministic where possible,
  probabilistic only at the judgment residue).
- **Alternative considered — LLM-evaluator-only (no deterministic layer):**
  *Rejected* — pays Sonnet tokens to learn what `pytest`'s exit code already
  says, and makes the un-arguable arguable. The deterministic-only
  alternative is treated fully in Alternatives (#1).

### D2: The goal artifact — `/goal` writes `.claude/state/goal.json`; PLAN ACs are referenced, never duplicated (resolves OQ-2)

A turn/session's goal + acceptance contract is declared via a **`/goal` slash
command** (project command, `.claude/commands/goal.md`, Code-authored per
ADR-013 D1) and stored as a **per-session goal file at
`.claude/state/goal.json`** — gitignored, sibling to `loop-counter.json` and
`stop-chain.json`, parsed stdlib-only like its siblings.

- **Shape (prototype spec in §Minimal-prototype spec below):** goal statement,
  optional `source` pointer to a canonical contract (typically a PLAN's
  Acceptance Criteria block), a `criteria[]` list where each criterion is
  `kind: check` (with `cmd`) or `kind: judge` (with `desc`), `status`
  (`active` / `passed` / `released-unevaluated`), and an `evaluations[]`
  verdict trail.
- **Derived, not canonical.** When a session executes a PLAN, the goal file
  **references** the PLAN's AC block (`source:`) and restates criteria only
  in checkable form — the PLAN remains the canonical contract (the same
  derived-artifact discipline as ADR-0017 D3/D6; on divergence the PLAN
  wins). Ad-hoc (non-PLAN) sessions may declare standalone criteria.
- **Lifecycle.** Created/replaced by `/goal`; marked `passed` by the gate
  when all criteria pass (the gate then stands down for the session);
  cleared/replaced explicitly by `/goal` (new goal or `clear`); a session
  end with an unmet goal leaves the file for the next session to re-ground
  on (the Anthropic structural-artifact pattern) — the gate re-arms on next
  Stop.
- **NB — naming collision with ADR-0016 D5.** `Procedure.goal` (ADR-0016) is
  a **product-side runtime LLM directive** compiled into the OCT engine's
  system prompt. The harness `/goal` artifact here is **harness-side
  verification state**. Same word, different layers, no shared code path —
  kept deliberately distinct; neither references the other.

- **Rationale:** a durable on-disk artifact with checkable pass/fail state is
  the load-bearing Anthropic pattern (Context §grounding); `.claude/state/`
  is where this harness already keeps exactly this class of gitignored
  machine state; reference-not-duplicate keeps the PLAN canonical.
- **Alternative considered — reuse the PLAN AC block directly as the
  contract (no goal file):** *Rejected* — PLAN ACs are prose for humans, not
  machine-checkable (no commands, no per-criterion state), and ad-hoc
  sessions have no PLAN; the goal file is the machine-readable projection
  with a `source` pointer preserving canonicality.

### D3: The `goal-evaluator` subagent — read-only critic with verdict-narrowed Write; "refute, not bless" (resolves OQ-3)

A **fourth subagent sibling** at `.claude/agents/goal-evaluator.md`,
Code-authored (ADR-013 D1), following the established contract
(`status-scribe` is the structural exemplar):

- **Receives (self-contained dispatch payload):** the goal-file path, the
  deterministic-layer results already recorded by the gate, and a bounded
  evidence fact-pack (e.g. `git diff --stat` summary, paths touched). It
  **reads the goal file and the evidence from disk itself** — see D6 for why
  the payload is pointers, not narrative.
- **Returns (binding output schema, mirroring its siblings):** per-`judge`
  criterion verdict `PASS / FAIL / INSUFFICIENT-EVIDENCE` + a one-paragraph
  reason each + an overall confidence statement + the ADR-012 D4.3
  author≠reviewer disclosure stamp + a *Surfaced decisions / Residual gaps*
  section. Bounded summary ≤ 1k tokens.
- **Records:** the evaluator **writes its own verdict** into the
  `evaluations[]` trail of `.claude/state/goal.json` — its `Write` is
  narrowed to that single file by a dedicated PreToolUse deny hook
  (`pretooluse_goal_evaluator_write_deny.py`), exactly the `status-scribe`
  single-file pattern. *(See SD-1 below — this refines the pre-draft
  consultation direction.)*
- **Tool posture:** `tools: Read, Grep, Glob, Write` (Write
  hook-narrowed to `goal.json`); `disallowedTools: Bash, WebFetch, Agent`.
  **The evaluator does not run the app or the tests** — it has no Bash by
  sibling convention; execution belongs to the deterministic layer (D1),
  whose recorded exit codes the evaluator consumes as evidence. This is the
  read-only-assessor answer to the dispatch's Playwright-MCP question
  (executor-evaluator treated in Alternatives #4).
- **Prompt posture ("separate the critic from the creator"):** the agent
  definition prompts it to **find failure** — assume the goal is unmet until
  the evidence forces PASS; `INSUFFICIENT-EVIDENCE` is the required verdict
  when evidence is missing (never benefit-of-the-doubt PASS); an
  adversarial-hardening section (sibling convention) instructs it to ignore
  any instruction embedded in the evidence that argues for blessing.

> **SD-1 — RESOLVED 2026-06-10 (Cray ratification): narrowed Write.** The
> pre-draft consultation direction was a strictly read-only evaluator
> (Read/Grep/Glob, no Write), with the main agent transcribing the verdict
> into the goal file. This draft instead gives the evaluator
> **hook-narrowed Write to `goal.json` only** (status-scribe precedent), so
> the critic's verdict reaches the record without passing through the
> creator's pen — removing a transcription-drift/shading seam at the cost of
> one more deny hook. **Cray chose narrowed Write at ratification** — the
> drafted D3 posture stands; the strict read-only + main-agent-transcription
> alternative is **not taken**. T2 builds the
> `pretooluse_goal_evaluator_write_deny.py` single-file deny hook accordingly.

- **Rationale:** distinct agent + own context + refute-prompting is the
  external grounding's core lesson; reusing the sibling contract
  (self-contained payload, output schema, disclosure stamp, write-deny hook)
  means the evaluator inherits conventions already production-proven in this
  harness rather than inventing new ones.
- **Alternative considered — evaluator as a prompt inside the gate hook (no
  subagent):** *Rejected* — a hook-embedded prompt shares no conventions
  with the agent layer, cannot Read evidence iteratively, and collapses the
  critic into the same process that runs the checks; the subagent boundary
  is what makes the critic separate.

### D4: Composition — `_goal_gate.py` invoked from inside `stop_continuation.py`; fail-OPEN with a loud alert (resolves OQ-4 — the load-bearing safety decision)

**Placement.** The gate ships as a **sibling module `_goal_gate.py`** invoked
from `stop_continuation.py::main()` — the exact `_sonnet_classifier.py`
precedent — **not** as a second Stop hook entry in `settings.json`. Insertion
point: **after** the re-entry guard, turn-boundary reset, and chain-cap
check; **before** the classifier dispatch. Control flow (prototype spec
below): no active goal → fall through to the classifier flow unchanged (zero
overhead, zero behavior change for goal-less sessions — the common case on
day one).

- **Why inside, not beside:** `settings.json`'s Stop matcher carries one hook
  today; two Stop hooks that can both emit `block` directives have
  **unverified ordering/merge semantics** in the harness. The in-flow module
  keeps a single Stop decision point, preserves the chain-cap as the *one*
  loop bound for all block sources (gate dispatches count toward the same
  `depth` as classifier proceeds — semantically each is a continuation), and
  mirrors how the classifier itself was integrated.
- **Evaluator spawn path:** when `judge` criteria need assessment, the gate
  emits the **existing dispatch-block** (PLAN-0009 Step 5c arm) instructing
  the main agent to spawn `goal-evaluator` next turn — the hook never spawns.
  Re-dispatch is guarded by an evaluation fingerprint (no re-spawn unless
  work happened since the last recorded evaluation), and the chain-cap
  bounds the worst case regardless.

**Fail-semantics: FAIL-OPEN, loudly.** When the LLM layer is unavailable
(billing 400, transport failure, evaluator spawn failure, malformed verdict):

1. the gate records `released-unevaluated` with the failure reason in the
   goal file's `evaluations[]` trail,
2. fires a **Telegram alert** (reusing `tools/notify/telegram.sh`, PLAN-0007)
   stating that a goal was released **without** evaluation, and
3. **lets the Stop fire** — it never blocks on infrastructure failure.

The deterministic layer (D1) is unaffected by API health and still runs.

- **Rationale (the asymmetry argument):** the Axis-A classifier fail-closes
  to `pause` — and a pause **stops the session**, which is the safe, cheap
  state. A goal gate's fail-closed equivalent would **block the Stop**,
  pushing the agent back into a loop it cannot satisfy while the API is
  down — a wedge (chain-cap-bounded at 8, but 8 futile turns of burn, and in
  an unattended PLAN-0010 run, 8 futile turns nobody is watching). Fail-open
  is safe here *specifically because the gate is additive*: every backstop
  that existed before this ADR — the Axis-A deny hooks, the classifier, the
  manual AC ritual (D7), Cray's review — still stands. The cost of a missed
  evaluation is a warning; the cost of a wedged unattended session is real.
- **Local-LLM (MS-S1) fallback:** **out of scope for v1** — it would couple
  the gate to a second infrastructure dependency to harden a path that
  fail-open already makes safe. Forward-declared in OQ-8.
- **Alternative considered — fail-closed (block Stop on evaluator
  unavailability):** *Rejected* — treated fully in Alternatives (#5).

### D5: Enforcement scope v1 — session-Stop only; warn + annotate, never hard-block (resolves OQ-5)

- **Where:** the gate runs at **session-Stop only** — in every Code session
  flavor (interactive **and** PLAN-0010 `loop-dispatcher` autonomous runs;
  the Stop hook fires identically in both, and the unattended case is where
  the gate earns its keep). It does **not** gate PR-merge and introduces
  **no new checkpoint** in v1. (Cowork/Chat sandboxes run no hooks — the
  gate is Code-harness-only by construction.)
- **How hard:** v1 is **warn + annotate**: on a FAIL or `released-unevaluated`
  verdict the gate fires Telegram, records the verdict trail in the goal
  file, and **lets the Stop fire**. It never hard-blocks a stop in v1. The
  single block-shaped behavior it has is the **evaluator-spawn dispatch**
  (one bounded continuation to obtain a verdict — an instruction to evaluate,
  not a refusal to stop).
- **Promotion path (explicitly deferred):** promoting FAIL to a blocking gate
  (and/or gating PR-merge) is a follow-on decision **after** false-positive
  data exists from v1 operation — the same phased posture as
  PLAN-0007→0008 (deterministic floor first, enforcement teeth later).
  Promotion criteria are parked in OQ-8.

- **Rationale:** a blocking gate with an unmeasured false-positive rate in
  unattended runs is how sessions wedge; warn-first generates the data that
  justifies (or kills) promotion. Matches the dispatch's "block, or only
  warn + annotate on first iteration?" prompt and the minimal-prototype
  constraint.
- **Alternative considered — block-on-FAIL from day one:** *Rejected for
  v1* — without operational false-positive data, every evaluator
  misjudgment becomes a session wedge; the chain-cap bounds but does not
  un-waste the burn. Reconsidered at promotion (OQ-8).

> **Deferral DISCHARGED (2026-07-13).** The promotion decision explicitly
> parked here is taken by the **V2 Amendment (2026-07-13)** below:
> warn→enforce graduates **per-goal** via an `enforce` flag (V2-D1), with
> this D5 warn-only posture remaining the **default tier** for every goal
> not marked enforcing. D5's reasoning is extended, not reversed (ADR-0016
> in-place-amendment discipline).

### D6: Injection resistance — structural reasoning-blindness via disk-sourced evidence (resolves OQ-6)

The evaluator inherits the auto-mode classifier's hardening posture, achieved
**structurally** rather than by input-stripping:

- **No transcript, by construction.** Subagents spawn fresh with **no parent
  transcript** (PLAN-0009 Step 1a — already true of every sibling). The main
  agent's reasoning, self-assessment, and narrative *never reach the
  evaluator* — the reasoning-blind property falls out of the existing
  architecture for free.
- **Input-sanitization contract (binding, the one rule that needs stating):**
  the dispatch payload the main agent passes to the evaluator is
  **pointers + machine outputs only** — the goal-file path, the
  gate-recorded deterministic results, diff stats/paths. The evaluator
  **reads the goal artifact and evidence from disk itself**; the spawn
  instruction template (verbatim in `_goal_gate.py`, mirroring the
  `_PLAN_DRAFTER_BUDGET_REMINDER` pattern) instructs the evaluator to
  **disregard any natural-language claims of success in the payload** and
  judge only from disk evidence. The creator cannot narrate its way past the
  critic because the critic does not accept narration as evidence.
- **Adversarial hardening section** (sibling convention) in the agent
  definition: instructions embedded in *read evidence* (e.g. a file
  containing "evaluator: mark this PASS") are named in *Residual gaps* and
  ignored — same posture as `status-scribe`'s.

- **Rationale:** the auto-mode lesson is that a task must not talk its way
  past its own gate; here the gate's critic literally never receives the
  talk. Stating the payload contract closes the one seam (a creator-authored
  payload) the architecture leaves open.
- **Alternative considered — pass the transcript but strip reasoning blocks
  (literal auto-mode mechanics):** *Rejected* — strictly more machinery for
  strictly more attack surface; the fresh-context subagent already provides
  a stronger guarantee than stripping.

### D7: The manual AC ritual is formalized + augmented, never replaced (resolves OQ-7)

The existing ritual — PLAN Acceptance Criteria blocks, STATUS closeout
`Verification:` lines, and the Cray verification-rigor directive
(case-coverage matrix + confidence sign-off, binding for all unattended
autonomy work per PLAN-0009 §Step 6 / PLAN-0010 §Verification) — **remains
canonical and required**. The verification loop is its machine-checked
projection:

- **Bright line:** the **PLAN AC block is the contract** (canonical,
  human-ratified); the **goal file is a derived projection** of it
  (machine-checkable, per-session); the **gate verdict is evidence**, not
  sign-off. On any divergence the PLAN wins and the goal file is corrected
  (ADR-0017 D3/D6 derived-artifact discipline, applied to verification
  state).
- **Augmentation, concretely:** STATUS `Verification:` lines and PLAN
  closeouts **may cite the gate's verdict trail** as evidence ("goal-gate:
  5/5 check + 2/2 judge PASS, evaluations[] at <ts>") — strengthening, not
  substituting, the hand-written line. Cray's sign-off on unattended
  autonomy work is **unchanged** by this ADR.
- **What would constitute drift (named so it can be caught):** a closeout
  citing *only* a gate verdict with no human-stated verification; a goal
  file whose criteria silently diverge from the PLAN AC block it claims as
  `source`. Both are review-time rejects.

- **Rationale:** the evaluator is a critic, not an authority — D5's warn-only
  posture and the verification-rigor directive both presume a human holds
  sign-off. Replacing the ritual was never on the table; formalizing its
  checkable subset is the whole Axis-B point.
- **Alternative considered — evaluator verdict replaces the manual
  `Verification:` line:** *Rejected* — collapses evidence into sign-off and
  hands a probabilistic component an authority the deterministic Axis-A
  layer was deliberately never given.

## Minimal-prototype spec (the PLAN-ready surface)

The smallest build that proves *goal declared → work done → evaluator checks
→ gate records/annotates*. Code authors all three components (ADR-013 D1);
exact code shape is the follow-on PLAN's to specify — this section fixes the
contracts tightly enough that the PLAN is a build plan, not a design debate.

### 1. The goal artifact (`.claude/state/goal.json`)

```jsonc
{
  "schema_version": 1,
  "goal": "one-sentence goal statement",
  "source": "docs/plans/0011-xxx.md#acceptance-criteria",  // optional canonical ref
  "session": 51,
  "created": "2026-06-10T02:12:00+07:00",
  "status": "active",            // active | passed | released-unevaluated
  "criteria": [
    { "id": "C1", "kind": "check", "cmd": "pytest -q",
      "desc": "test suite green", "timeout_s": 300 },
    { "id": "C2", "kind": "check", "cmd": "ruff check . && mypy --strict services",
      "desc": "lint + types clean", "timeout_s": 120 },
    { "id": "C3", "kind": "judge",
      "desc": "the drafted ADR resolves OQ-1..OQ-7 each with a decision" }
  ],
  "evaluations": [               // append-only verdict trail
    { "ts": "...", "fingerprint": "<work-state marker>",
      "deterministic": { "C1": "pass", "C2": "pass" },
      "judged": { "C3": { "verdict": "FAIL", "reason": "...",
                           "confidence": "medium" } },
      "evaluator": "goal-evaluator" }   // or "UNAVAILABLE: <reason>"
  ]
}
```

Stdlib-parseable (`json`), atomic-write via the `tempfile`+`os.replace`
pattern already used by `_save_chain`. The `/goal` slash command
(`.claude/commands/goal.md`) instructs the main agent to materialize this
file from the stated goal + referenced PLAN AC block; `/goal clear` retires
it.

### 2. The gate (`_goal_gate.py`, invoked from `stop_continuation.py`)

Control flow at the D4 insertion point (after chain-cap, before classifier):

1. **No `goal.json`, or `status != "active"`** → return `None`; the existing
   classifier flow proceeds **unchanged** (goal-less sessions: zero delta).
2. **Run `check` criteria** (subprocess, per-criterion `timeout_s`, total
   budget capped — VX-2); record results.
3. **All criteria resolved + all pass** → set `status: "passed"`, Telegram
   info ping, fall through to classifier (stop proceeds normally).
4. **`judge` criteria unresolved + work-since-last-evaluation** (fingerprint
   mismatch — e.g. the Step 3 `turn_touched` marker or a diff hash) → emit
   the **dispatch-block** instructing the main agent to spawn
   `goal-evaluator` (payload per D6 contract; instruction template verbatim
   in-module); `depth++` (counts toward chain-cap).
5. **FAIL verdict recorded (either layer), or fingerprint unchanged** →
   **do not block** (D5): Telegram warn with per-criterion summary, leave
   `status: "active"`, fall through (stop fires).
6. **Evaluator/LLM unavailable** → record `released-unevaluated` + loud
   Telegram warning, fall through (D4 fail-open).

Never raises into the harness (same catch-all posture as the classifier
wrapper); all state I/O honors env-var overrides for testability
(`CLAUDE_GOAL_PATH`, mirroring the existing `CLAUDE_*` override family).

### 3. The evaluator (`.claude/agents/goal-evaluator.md`)

Frontmatter: `tools: Read, Grep, Glob, Write`; `disallowedTools: Bash,
WebFetch, Agent`; `model: inherit`; `maxTurns: 30`; PreToolUse
`Write|Edit` → `pretooluse_goal_evaluator_write_deny.py` (allow only
`.claude/state/goal.json` — `status-scribe` single-file pattern; subject to
SD-1). Body: the D3 receive/return/record contract, the refute-not-bless
prompt posture, the D6 disk-evidence rule, the sibling-convention output
schema (disclosure stamp, bounded summary, Surfaced decisions, Residual
gaps), and an adversarial-hardening section.

### 4. Axis-A non-interference statement (binding)

This loop is **additive**. It changes **no** `pretooluse_*_deny` hook, **no**
classifier behavior, **no** registry row semantics, and **no** commit-boundary
mechanics (ADR-009 D2 / ADR-013 D2 untouched). The only modified existing
file is `stop_continuation.py` (one insertion point + one sibling-module
import, the same shape as the Step 5 classifier swap); when no goal is
active, its behavior is byte-for-byte today's. Any future change to Axis-A
behavior requires its own ADR.

## Required follow-on (TODOs for Code — separate commits)

This ADR is a Cowork draft (ADR-009 D2 — only Code commits). None of these
are done in this draft:

1. **T1 — Commit this ADR** at the status Cray sets (Proposed → Accepted on
   ratification).
2. **T2 — Draft + ratify the follow-on build PLAN** (next free PLAN number)
   covering: `_goal_gate.py` + `stop_continuation.py` insertion,
   `goal.json` schema module + tests, `/goal` command, `goal-evaluator`
   agent + write-deny hook, Telegram wiring, and the verification-rigor
   case-coverage matrix (happy / boundary / fail-closed→fail-open /
   adversarial / concurrency rows — including "API dead at Stop",
   "poison check command", "evaluator returns malformed verdict",
   "goal.json mid-write at Stop").
3. **T3 — Registry annotation:** add the verification-loop row(s) to
   `.claude/autonomy-triggers.md` documenting the gate's dispatch trigger
   (V-row class, distinct from G/C/L/H rows) so the classifier prompt and
   human review share one source of truth. Exact row shape is the PLAN's.
4. **T4 — STATUS update:** record this ADR in Recent Decisions; clear the
   "deferred Axis-B verification-loop track" earmark in Current Focus.

## Consequences

### Positive

- **Closes the #1-lesson gap:** the harness gains a check the agent runs +
  a critic separate from the creator — the two things the review found
  missing — while reusing proven primitives (dispatch-block arm, sibling
  subagent contract, state-file pattern, Telegram).
- **Highest value where supervision is lowest:** unattended PLAN-0010 runs
  get a recorded, criterion-level verdict trail instead of silence.
- **Zero cost when unused:** no active goal → no behavior change; goals
  with only `check` criteria → no LLM tokens at all.
- **The verdict trail is durable evidence** — closeouts cite it; drift
  between claimed and verified completion becomes visible.

### Negative

- **One more moving part in the Stop path.** `stop_continuation.py` gains an
  insertion point; a gate defect could disturb the continuation loop.
  Mitigated: in-flow module mirrors the proven classifier integration,
  never-raise wrapper, goal-less fall-through, and AC-gated regression
  tests (T2 matrix).
- **Warn-only v1 has no teeth:** a FAIL verdict stops nothing. Accepted
  deliberately (D5) — the promotion path exists once false-positive data
  does.
- **Evaluator quality is unmeasured at v1.** A lenient evaluator yields
  false confidence; a harsh one yields alert fatigue. The refute-prompt +
  `INSUFFICIENT-EVIDENCE` verdict + warn-only posture bound the damage
  while data accrues.
- **`/goal` discipline is manual.** Nothing forces a session to declare a
  goal; an undeclared session is exactly as unverified as today. Adoption
  pressure (e.g. loop-dispatcher auto-declaring goals from PLAN ACs) is
  OQ-8 material.

### Neutral

- **Vertical-agnostic core harness tooling** (ADR-006 posture; same class
  as the autonomy layer and skills).
- **Chain-cap semantics unchanged:** gate dispatches count toward the same
  cap-8 as classifier proceeds; the cap remains the single loop bound.
- **The verification loop and the product-side Procedure engine (ADR-0016)
  remain disjoint** — same "goal" word, different layers (D2 NB); no shared
  code path is created or implied.

### Reversibility

Fully reversible with bounded unwind: delete `_goal_gate.py` + the one
insertion point, the agent file, the command, the deny hook, and the
gitignored state file — `stop_continuation.py` returns to today's behavior.
No architectural state migrates; no Axis-A surface is touched either way
(§spec 4), so a revert never weakens any safety boundary.

## Open Questions

- **OQ-8 (non-binding backlog, forward-declared only):**
  - **Harness-as-plugin packaging:** fold the gate + evaluator + `/goal`
    command into the prospective vero-lite harness plugin bundle (ADR-0017
    D7 forward link / harness-review rec #6).
  - **MS-S1 local-LLM evaluator:** run `goal-evaluator` against the local
    model to decouple verification from Anthropic API billing — revisit
    once the loop is proven on the default model (and note Lesson #9
    model-tier gating applies to any such swap).
  - **Blocking-mode promotion:** criteria for promoting warn → block (e.g.
    N sessions of operation, false-positive rate < X, per-scope: autonomous
    first or interactive first) — decide with v1 data.
    **DISCHARGED 2026-07-13** — resolved by the **V2 Amendment** below:
    per-goal `enforce` flag, default warn (V2-D1); bounded
    block-then-`blocked-pending-human` ladder (V2-D3); pause on missing
    evidence, never a silent pass (V2-D4).
  - **PR-merge gating:** whether a FAIL/unevaluated goal should annotate or
    gate the PR flow (CLAUDE.md §7) — out of v1 scope.
  - **Auto-declared goals:** loop-dispatcher deriving `goal.json` from the
    PLAN AC block it executes, removing the manual `/goal` step in
    unattended runs.
- **VX — verify-at-execution items (Code confirms during T2, not
  re-litigated here):**
  - **VX-1:** the exact non-blocking warn/annotate mechanism available to a
    Stop hook (e.g. `systemMessage` field support vs stderr vs
    Telegram-only) — D5's warn channel of record is Telegram + the verdict
    trail; any in-UI annotation is bonus.
  - **VX-2:** deterministic-layer runtime budget at Stop (a full
    `pytest -q` per Stop may be seconds-to-minutes; per-criterion
    `timeout_s` + a total budget + possibly a changed-files-scoped test
    selection are PLAN decisions).
  - **VX-3:** `goal.json` concurrency with the loop-counter/stop-chain
    state writes (same atomic-replace pattern expected to suffice; confirm
    under the T2 concurrency matrix row).

## Alternatives Considered

### Alternative 1: Deterministic-only — no LLM evaluator

- **Pros:** zero token cost; zero new LLM dependency; exit codes never
  hallucinate.
- **Cons:** most PLAN ACs are *not* reducible to exit codes ("resolves each
  OQ with a decision", "follows template shape", "names residual risk") —
  a deterministic-only gate verifies the easy half and silently blesses the
  half where drift actually lives; Anthropic's evaluator lesson is
  precisely about the judgment residue.
- **Why rejected:** keeps the gap this track exists to close. The design
  does adopt its core insight as D1's split rule: deterministic wherever
  possible, LLM only at the residue.

### Alternative 2: Keep manual AC-verify (status quo)

- **Pros:** zero build; zero new failure surface; the ritual demonstrably
  works when a human runs it.
- **Cons:** nothing checks unattended runs; "Verification:" lines are
  written by the same agent that did the work (creator grades own
  homework); the review's #1-lesson gap persists indefinitely.
- **Why rejected:** the status quo is the problem statement (the same
  rejection shape as ADR-013 Alternative 3).

### Alternative 3: Separate second Stop hook (gate beside, not inside, `stop_continuation.py`)

- **Pros:** zero edits to the existing hook file; gate fully independent;
  arguably cleaner single-responsibility files.
- **Cons:** two Stop hooks can both emit `block` — the harness's
  ordering/merge semantics for competing Stop blocks are unverified here;
  the chain-cap would no longer be the single loop bound unless the second
  hook re-implements or shares chain state (coupling by the back door).
- **Why rejected:** D4 — the sibling-module-in-flow pattern is already
  proven by `_sonnet_classifier.py`, keeps one Stop decision point, and
  preserves the cap as the single bound. Revisit only if the in-flow
  integration proves unwieldy in T2.

### Alternative 4: Executor-evaluator — the evaluator runs the app/tests itself (Playwright-MCP style)

- **Pros:** closest to the Anthropic long-running-apps reference; the
  critic gathers its own evidence end-to-end.
- **Cons:** requires Bash/MCP in the evaluator — breaking the sibling
  no-Bash convention and re-opening the G5 identity-gate analysis for a
  fourth agent class; duplicates work the deterministic layer already does
  cheaply; widens the evaluator's attack/blast surface exactly where D6
  wants it narrow.
- **Why rejected:** for *this* harness's verification targets (tests,
  lint, docs criteria) the executor split (hook runs, critic reads) gets
  the same evidence with a strictly smaller trusted surface. An
  app-exercising evaluator can be revisited if verification targets ever
  include a running product UI.

### Alternative 5: Fail-closed gate (block Stop when the evaluator is unavailable)

- **Pros:** symmetrical with the Axis-A classifier's fail-closed posture;
  no goal ever escapes unevaluated.
- **Cons:** the symmetry is false — classifier-fail-closed *stops* the
  session (safe); gate-fail-closed *prevents stopping*, looping an agent
  against a dead API (chain-cap-bounded wedge, worst in exactly the
  unattended runs the gate most serves); couples session liveness to API
  billing state, a failure mode this repo has already hit live.
- **Why rejected:** D4's asymmetry argument; fail-open's cost (a loudly
  flagged unevaluated release, with all pre-existing backstops intact) is
  strictly lower than fail-closed's (unattended burn + a wedged session).

## V2 Amendment (2026-07-13): warn→enforce graduation + the drift-vs-redirect distinction

> **Accepted 2026-07-13; SD-0…SD-4 ratified as-recommended by Cray (typed,
> via AskUserQuestion); discharges the D5 warn-only deferral + OQ-8
> "Blocking-mode promotion".** In-place amendment per the ADR-0016
> dated-amendment precedent — **extends, does not reverse or renumber**:
> D1–D7 stand unchanged; this amendment changes the *consequence semantics*
> of the existing gate plus the `goal.json` schema, and nothing else.

> **Drafting provenance + author≠reviewer disclosure (ADR-012 D4.3).**
> Amendment authored by the in-harness **`plan-drafter`** subagent (ADR-013
> D1 phased authority) from a Code-authored design brief (2026-07-13
> session: research through 13 Jul 2026 + repo inventory; the
> drift-vs-redirect crux originates with Cray). Drafted first as the
> standalone vehicle `docs/adr/0030-axis-b-v2-enforcing.md` (the drafter
> could not edit this Accepted ADR pre-ratification), then merged here
> after SD-0 = in-place amendment — the 0030 draft is **not committed** and
> the number returns to the pool. **Code performed the independent R2
> review** (all load-bearing citations re-verified on disk — D5/OQ-8
> deferral text, `work_fingerprint()` at `_goal_gate.py:152`, the D4
> fail-open path, and both build hazards in spec note 1 confirmed real; no
> defects). **Cray ratified SD-0…SD-4 as-recommended** (typed, via
> AskUserQuestion, 2026-07-13); Code commits per ADR-009 D2. Separation:
> **INTACT** — author (plan-drafter), reviewer (Code R2), ratifier (Cray)
> are three distinct actors.

### Context for the amendment

**What v1 deferred.** D5 made v1 warn-only pending false-positive data;
OQ-8 parked "Blocking-mode promotion" to be decided with v1 data. This
amendment is that follow-on decision.

**Why now — drift is a measured failure mode.** The design brief's research
sweep (through 2026-07-13) finds goal drift has moved from anecdote to
measurement: **GD_actions** (drift by commission) and **GD_inaction** (drift
by omission) are named metrics, and StepShield-style scoring measures *how
fast* a violation is caught (**Early Intervention Rate**; the **Intervention
Gap** between violation turn and catch turn). The load-bearing finding: *a
rule broken that was followed 10 turns ago is a context failure, not a model
change* — drift is a decay process the harness must re-anchor against,
which is exactly what the durable goal artifact + per-Stop gate are shaped
for. v1 built the sensor; v2 connects it to a brake.

**The founder's crux — drift ≠ redirect.** A naive warn→block flip would
misfire on the most common legitimate event in this repo's sessions: Cray
changes the goal mid-session **on purpose**. The requirement this amendment
formalizes: **unintentional drift** (divergence with *no* fresh sign-off)
must be flagged — blocked, once enforcing; **deliberate redirect** (the
founder's prerogative — divergence *with* a fresh ratification event) must
pass freely and update the anchor. The distinguishing signal reuses a
primitive already trusted here: a **typed Cray sign-off** (an
`AskUserQuestion` selection or a typed message — the repo's existing
attribution-honesty bar: a Stop-hook "proceed" is the harness, never Cray).

**Constraints carried forward unchanged (binding):** (1) harness primitives
are **Code-built** (ADR-013 D1) — this amendment is governance text only
(drafter-authored, Code-committed per ADR-009 D2); (2) the gate/evaluator
stay **reasoning-blind + injection-resistant** (D6) — v2 adds no narration
channel; (3) the evaluator **refutes, does not bless** (D3) — warn→enforce
changes the *consequence* of its FAIL, not its mandate; (4) **no LLM in the
enforcement decision path** — the evaluator writes a verdict artifact to
disk; the deterministic gate applies a fixed rule over it (V2-D3).

### Ratified surfaced decisions (plan of record — all as-recommended, Cray, typed via AskUserQuestion, 2026-07-13)

- **SD-0 — home:** **in-place amendment to ADR-0018** (this section);
  standalone ADR-0030 not taken, the 0030 draft file not committed.
- **SD-1 — enforcement scope:** **per-goal `enforce` flag on `goal.json`,
  default warn**; enforce-all and unattended-only-detection alternatives
  not taken.
- **SD-2 — drift/redirect signal:** **ratification = typed Cray sign-off
  logged in `amendments[]`; divergence detection = evaluator-detected,
  deterministically-consequenced** — the LLM writes the divergence verdict
  to the trail; the gate applies the fixed drift/redirect rule over the
  artifact. The deterministic-scope-check and both-layers alternatives not
  taken (revisitable with v2 data).
- **SD-3 — scope:** **gate-graduation only**; the sibling hooks
  (anti-duplicate pre-create check, `SubagentStop` verification gate,
  per-turn re-injection) stay out of scope, each its own PLAN/ADR (V2-D5).
- **SD-4 — evidence-missing under enforcement:** **pause
  (`blocked-pending-human`), never a silent pass**; loud-warn-and-release
  not taken for enforcing goals.

### V2-D1: Graduated enforcement via a per-goal `enforce` flag — not a hard flip *(SD-1 ratified)*

`goal.json` gains a first-class boolean **`enforce`** (schema_version → 2):

- **`enforce: false` (default):** exactly v1 behavior — warn + annotate +
  Telegram, the Stop fires. Every existing goal, and every goal where Cray
  has not said otherwise, stays warn-only.
- **`enforce: true`:** set at `/goal` declaration time (or by a later
  ratified amendment) for goals Cray marks critical — an evidence-backed
  FAIL or an unratified divergence now has teeth (V2-D3 ladder).

Rationale: v1 was *deliberately* warn-only pending false-positive data (D5);
a repo-wide flip would discard that caution in one move. The tag makes
graduation per-goal and reversible — enforcement lands where the cost of
silent drift is highest (unattended PLAN-0010 runs, host-state work) while
routine goals keep accumulating calibration data at warn.

### V2-D2: The drift-vs-redirect mechanism — a ratification log in `goal.json` *(SD-2 ratified)*

`goal.json` gains an append-only **`amendments[]`** log; the goal statement
plus its latest ratified amendment = the **anchor**.

```jsonc
"amendments": [                    // append-only ratification log
  { "ts": "2026-07-13T14:02:00+07:00",
    "event": "typed",              // "typed" | "ask_user_question:<label>"
    "summary": "pivot: ship the fixture first, defer the live smoke",
    "prev_goal": "<verbatim prior goal statement>",
    "new_goal": "<verbatim new goal statement>",
    "fingerprint": "<work_fingerprint() at ratification>" }
]
```

- **A ratification event is a typed Cray sign-off only** — an
  `AskUserQuestion` selection or a typed instruction. A Stop-hook harness
  "proceed", a Code inference, or a subagent suggestion **never** qualifies
  (the existing attribution-honesty bar, now load-bearing in the
  mechanism). The main agent records the amendment at the moment of
  sign-off; the recorded `fingerprint` (the gate's existing
  `work_fingerprint()`) marks *when* in the work-state the redirect
  happened.
- **At each Stop**, the gate's decision over a detected divergence is
  deterministic given the artifact: divergence **with** an amendment entry
  fresher than the last evaluation fingerprint → **deliberate redirect** —
  pass freely, the anchor is already updated. Divergence **without** one →
  **unintentional drift** — warn (`enforce: false`) or the V2-D3 ladder
  (`enforce: true`).
- **Divergence detection (SD-2 ratified):** **evaluator-detected,
  deterministically-consequenced.** The `judge`-layer evaluator assesses
  "does this turn's disk evidence serve the anchor?" and writes the verdict
  to the trail (its only power — it cannot block, release, or ratify); the
  gate's drift/redirect/enforce rule is a pure function of the on-disk
  verdict + `amendments[]` + `enforce`. A deterministic scope-list detector
  (cheaper, coarser) was considered and not taken — revisitable with v2
  operating data.

### V2-D3: What an enforcing block is — bounded block, then pause-for-human; the decision rule is deterministic

For an `enforce: true` goal, the consequence ladder on an evidence-backed
FAIL (deterministic `check` failure, or a recorded `judge` FAIL /
drift-without-ratification verdict per V2-D2):

1. **First Stop with the failing verdict:** the gate emits a **block** (the
   existing dispatch-block shape, counting toward the same chain-cap-8)
   whose reason states the failing criteria verbatim and instructs the main
   agent to either **remediate** or **obtain a typed Cray ratification**
   (which converts the divergence to a redirect). One bounded continuation,
   not a loop.
2. **Re-Stop still failing (or cap pressure):** the gate stops blocking —
   the Stop **fires**, but the goal transitions to a new terminal-pending
   status **`blocked-pending-human`** with a loud Telegram alert. The goal
   **cannot be marked `passed`** until a human acts (re-ratify, remediate
   in a next session, or clear). Enforcement teeth = the *goal record*
   refuses to close, not an unbounded refusal to stop.

- **The D4 asymmetry argument still governs:** a gate must never loop an
  agent against a state it cannot satisfy. The ladder blocks **once**
  (bounded, chain-cap-counted), then converts to a pause-shaped state that
  stops the session safely — teeth without a wedge, in attended *and*
  unattended (PLAN-0010) runs.
- **No LLM in the decision path:** step transitions are pure functions of
  the on-disk verdict trail + `amendments[]` + `enforce` flag.

### V2-D4: Fail-semantics under enforcement — INSUFFICIENT-EVIDENCE never passes; missing evidence pauses *(SD-4 ratified)*

When the evaluator cannot run (MS-S1/API dead, spawn failure, malformed
verdict) or returns `INSUFFICIENT-EVIDENCE`:

- **`enforce: false` goals:** unchanged v1 fail-open — `released-unevaluated`
  + loud Telegram, the Stop fires (D4 stands for the warn tier).
- **`enforce: true` goals:** **never a silent pass.** The Stop fires (no
  wedge — same D4 geometry), but the goal transitions to
  `blocked-pending-human` with an `UNAVAILABLE`/`INSUFFICIENT-EVIDENCE`
  trail entry + loud Telegram. An enforcing gate that cannot verify
  **pauses for a human**; it does not auto-release. CLAUDE.md §6 applied
  mechanically: *"no fresh evidence = INSUFFICIENT-EVIDENCE, not a pass."*
- Deterministic `check` criteria are API-independent and always run; only
  the judge/divergence residue can be evidence-starved.

### V2-D5: Scope — the goal-gate graduation ONLY *(SD-3 ratified)*

This amendment changes the **consequence semantics of the existing gate**
and the **goal.json schema** — nothing else. The design brief's sibling
recommendations are explicitly **out of scope**, named so their absence is
a decision, not an omission (the ADR-0016 amendment scope-boundary
discipline): an **anti-duplicate pre-create `PreToolUse` check**
(drift-by-commission at file-creation time); a **`SubagentStop`
verification gate** (verifying subagent deliverables at their own
boundary); **per-turn re-injection** of the active PLAN/goal into context
(the "context failure, not a model change" countermeasure). Each is its own
PLAN/ADR. The Axis-A non-interference statement (spec §4 above) is
re-affirmed verbatim: no `pretooluse_*_deny` hook, no classifier behavior,
no commit-boundary mechanics change.

### V2 schema + build notes (the PLAN-ready surface)

Code implements (ADR-013 D1); the follow-on build PLAN specifies exact code
shape. Contracts fixed here:

1. **`goal.json` schema_version 2:** adds `enforce: bool` (default
   `false`), `amendments[]` (shape per V2-D2), and status value
   `blocked-pending-human`. **Build hazards (verified at HEAD, confirmed at
   R2):** (a) `_goal_state.py` *ignores unknown fields on parse and drops
   them on rewrite* (`Goal.from_json`/`to_json` handle only known fields) —
   `enforce`/`amendments[]` MUST be first-class `Goal` dataclass fields or
   the gate's own rewrite would silently strip the ratification log;
   (b) v1 `VALID_STATUSES` treats an unknown status as corrupt →
   `load_goal` returns `None` → a v1 reader silently stands down on a
   `blocked-pending-human` file — the PLAN needs a version-skew row in its
   test matrix.
2. **Gate rule table** (pure function of the artifact): the
   drift/redirect/enforce ladder in V2-D2/V2-D3, including the
   fingerprint-freshness comparison (`amendments[-1].fingerprint` vs the
   last evaluation fingerprint).
3. **Instrumentation for the evidence loop:** trail entries gain the fields
   needed to measure catch-latency (fingerprint at divergence detection vs
   at introduction where recoverable) — the GD_actions / GD_inaction /
   intervention-gap counters that motivated this graduation become
   measurable in our own trail (feeds V2-OQ-1).
4. **`/goal` command update:** accepts the `enforce` flag; documents the
   amendment-recording step (typed sign-off → append to `amendments[]`).

### Consequences (amendment-scope)

**Positive:** the v1 sensor gains a brake where Cray chooses — unattended
runs on critical goals can no longer silently close against a FAIL or an
unratified pivot; founder prerogative is formalized, not obstructed (a
deliberate redirect passes with one typed sign-off and leaves a durable
amendment trail); drift becomes classifiable in the trail (commission vs
omission vs redirect); no new trusted surface (reuses the gate, evaluator,
fingerprint, chain-cap, typed-sign-off primitive, Telegram).

**Negative:** a miscalibrated evaluator now has consequences on
`enforce: true` goals — a false drift verdict costs one bounded block + a
human-attention pause (mitigated by the opt-in default, the one-block
ladder, and ratify-to-override being one typed message); ratification
recording is a manual discipline — a sign-off not appended to
`amendments[]` reads as drift (mitigated: the block reason names the fix,
and the failure mode is a false *alarm*, never a false *pass*); schema-skew
risk is bounded by build-hazard note 1 + the PLAN test matrix.

**Neutral:** warn-tier behavior is byte-for-byte v1; goal-less sessions
remain zero-delta; the evaluator's prompt, tools, Write-narrowing, and
refute mandate are untouched; the ADR-0016 `Procedure.goal` disambiguation
(D2 NB) carries over unchanged.

**Reversibility:** per-goal reversible at zero build cost (`enforce: false`
or omit = v1). Full revert = remove the v2 fields + ladder from the
gate/schema modules; `blocked-pending-human` records degrade to
corrupt-file stand-down under a v1 reader (noisy but fail-safe — the gate
stands down, it never blocks).

### Open Questions (amendment)

- **V2-OQ-1:** promotion-evidence review — after N enforcing-goal sessions,
  review false-positive/false-negative counts from the instrumented trail
  (build note 3) before any default-flip discussion.
- **V2-OQ-2:** whether `/goal` for PLAN-0010 unattended runs should
  auto-set `enforce: true` (composes with OQ-8 "auto-declared goals",
  which remains open).
- **V2-OQ-3:** the sibling hooks (V2-D5 list) — sequencing, and whether any
  warrant ADR-level treatment vs PLAN-only.
- **V2-VX (verify-at-execution, Code confirms in the build PLAN):** the
  exact harness surface for the one-block remediation message;
  `amendments[]` concurrency with evaluator trail-writes (same
  atomic-replace pattern expected to suffice); v1↔v2 reader-skew rows in
  the test matrix.

### Amendment references

- **Design brief** — Code, session 2026-07-13 (research through 13 Jul
  2026 + repo inventory): GD_actions / GD_inaction drift metrics,
  StepShield Early Intervention Rate / Intervention Gap, the "context
  failure, not a model change" finding, Anthropic harness guidance
  (durable pass/fail artifact; critic≠creator; reasoning-blind
  injection-resistant classifier).
- **ADR-0016** — the in-place dated-amendment precedent (D2 Amendment
  2026-06-25; D2+D3 Amendments 2026-07-01, 2026-07-05: "extends, does not
  reverse or renumber") and its amendment scope-boundary discipline.
- **ADR-013 D1 / ADR-009 D2 / ADR-012 D4.3** — build authority, commit
  boundary, disclosure (as in the main References).
- **CLAUDE.md §6** — "no fresh evidence = INSUFFICIENT-EVIDENCE, not a
  pass" (V2-D4's governing principle).
- **Live code read for this amendment:** `.claude/hooks/_goal_gate.py`
  (warn path, dispatch arm, fail-open, `work_fingerprint()` at :152),
  `.claude/hooks/_goal_state.py` (schema v1; unknown-field drop on
  rewrite; `VALID_STATUSES` corrupt-stand-down), `docs/adr/` enumeration.
- **Superseded drafting vehicle:** `docs/adr/0030-axis-b-v2-enforcing.md`
  (uncommitted; deleted after this merge per SD-0 — number 0030 returns to
  the pool).

## References

- **Authoring dispatch:**
  `.claude/handoffs/session-51/2026-06-10-0147-code-axisb-verification-loop-adr-dispatch.md`
  (gitignored; embeds the external grounding + OQ-1…OQ-8 + acceptance
  criteria).
- **Anthropic sources** (as embedded in dispatch §2): "Effective harnesses
  for long-running agents" (2025-11-26); "Harness design for long-running
  apps" (2026-03-24); "How we built Claude Code auto mode" (2026-03-25).
- **ADR-013** (`docs/adr/0013-autonomy-axis-relocation.md`) — D1 (harness
  primitives → Code: the gate/evaluator/command are Code-built), D2 (commit
  fail-safe untouched), OQ-1 (Cowork as advisory governance drafter — the
  process drafting this).
- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — D1
  (drafting process), D2 (only Code commits), D3 (K-1/K-2 workflow for the
  companion handoff).
- **ADR-0017** (`docs/adr/0017-skills-as-a-memory-tier.md`) — track-1
  precedent; D3/D6 derived-artifact discipline (applied to the goal file in
  D2/D7 here); D7 harness-as-plugin forward link (OQ-8).
- **ADR-0016** (`docs/adr/0016-governed-procedure-engine.md`) — D5
  product-side `Procedure.goal`, distinct from the harness `/goal` (D2 NB).
- **ADR-012** (`docs/adr/0012-cowork-second-freeform-tier.md`) — D4.3
  disclosure stamps (evaluator output schema + this ADR's provenance).
- **PLAN-0008** (`docs/plans/done/0008-harness-autonomy-layer-phase-2.md`)
  — the Stop continuation loop + Sonnet classifier + chain-cap this gate
  composes with.
- **PLAN-0009** (`docs/plans/done/0009-subagent-topology.md`, a completed
  3-file series — also `done/0009-step4-dispatch-protocol.md` +
  `done/0009-step1b-contract-design.md`) — Step 5c dispatch-block spawn
  pattern (reused verbatim as the evaluator spawn path); Step 1b subagent
  contract (the sibling conventions D3 adopts).
- **PLAN-0010**
  (`docs/plans/0010-phase3-5-scheduled-task-autonomy-loop.md`) — the
  unattended-run scope (D5) + the verification-rigor directive (D7).
- **Live code read this session:** `.claude/hooks/stop_continuation.py`
  (control flow + dispatch arm + cap mechanics), `.claude/settings.json`
  (single Stop hook), `.claude/agents/status-scribe.md` +
  `.claude/agents/plan-drafter.md` (sibling contract),
  `tools/handoffs/_schema.py` (companion-handoff validation reference).

## Implementation Notes

- Drafted by Cowork in Tier-1 governance-authoring mode under the unchanged
  ADR-009 D1 interim process (ADR-013's Plan-subagent relocation is phased
  and not yet executed for this track; ADR-013 OQ-1 retains Cowork as
  advisory drafter). Cowork has no commit authority (ADR-009 D2); Code
  reviews and commits this file plus T1–T4.
- **G2 number gate:** 0018 confirmed free (0017 highest; 0011 intentionally
  reserved per ADR-013 OQ-2 — not consumed; 0014 WITHDRAWN). PLAN/Lesson
  0018 namespaces are separate.
- **K-1 validator gap:** Cowork bash refuses the WSL-UNC cwd (re-confirmed
  live this session — even `date` fails), so no repo tooling ran against
  this draft. This is a prose ADR (no handoff frontmatter validator
  applies); the companion completion handoff carries the field-by-field
  mental schema validation + flags the gap. Timestamps in this session were
  derived from the `vero-bridge` `bridge_status` server clock
  (`last_call_ts_ns`), not an agent-claimed clock.
- **Surfaced decision RESOLVED at ratification:** SD-1 (D3 — evaluator
  verdict-write posture) → **narrowed Write** (Cray, 2026-06-10); the drafted
  D3 posture stands and T2 builds the single-file deny hook. The strict
  read-only + main-agent-transcription alternative is not taken.
- **Author≠reviewer disclosure (ADR-012 D4.3):** D1–D7 directions were
  deliberated in this same Cowork session with Cray approving the
  directions pre-draft (a Tier-1b-style consultation preceding Tier-1
  authoring); the OQ framing is the Code dispatch's. Disclosed per D4.3;
  Code's R2 fact-pack review (ADR-009 D3 step 6) + Cray's ratification are
  the independent checks. AI-assisted per CLAUDE.md §7 (noted in commit
  body, never as Co-Authored-By).
- **Ratified Proposed → Accepted by Cray on 2026-06-10** (SD-1 = narrowed
  Write); Code applied the status flip + SD-1 resolution and committed.
