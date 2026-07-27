# PLAN-0094: L1 loop-detect — count non-progress, warn before denying, restore the reset paths

**Status:** Draft — **Steps 1+2 BUILT and MERGED** (s174, PR #917: `e33f7e0`, `c88d3e8`, merge `2cda070`); **Step 3 BUILT and MERGED** (s175, PR #922 — AC-3/4/5 closed); **Step 5 BUILT** (s177 — AC-9 closed). **Steps 4 and 6 remain unbuilt.** **Step 4 was RE-SCOPED at s179** after its probe-before-build gate returned a refutation: `PostToolUseFailure` does not fire, so design element **D4(a) is withdrawn** and **AC-1(ii), AC-6, and AC-8(ii) are withdrawn with it** (see the boxed record under §D4). Step 4 consequently **no longer carries a `settings.json` diff and is no longer gated on a Cray per-diff approval** — the removal of (a) removed the only gated surface. What remains of Step 4 — (b), (c), `observe()`, `clear_turn_scoped()`, closing **AC-7 + AC-8(i)/(iii)** — is deterministic-offline and ungated.
**Owner:** Claude Code
**Created:** 2026-07-25

> **⚠️ Line citations below drift — re-verify at use (added s175).** This PLAN was
> written *before* Step 1, which added ~12 lines to `.claude/hooks/_loop_counter.py`.
> Every citation into that file written pre-Step-1 is now low by roughly that amount,
> and a handful of others no longer point at what they describe. **Symbols are the
> stable reference; line numbers are not.** Spot-checked against `main` on 2026-07-26;
> **four rows re-verified and corrected s179 (2026-07-27) — including one row this
> table had itself marked "✅ exact", which has since drifted. The table is not
> self-maintaining; re-check at use.**
>
> | Cited | Actual | Note |
> |---|---|---|
> | `_loop_counter.py:551-558` (`has_triggered`) | **`:563`** | drifted |
> | `_loop_counter.py:573-579` (`l1_threshold_for`) | **`:585`** | drifted — **Step 3 changes this bar to `T+G`** |
> | `_loop_counter.py:582-596` (`reset_l1_for_targets`) | **`:594`** | drifted |
> | `_loop_counter.py:194` (`turn_touched`) | **`:195`** | drifted — **Step 3 adds `warned_at` as a sibling here** |
> | `_loop_counter.py:362-364` ("failed") | — | now `agent_id` prose; **wrong target** |
> | `_loop_counter.py:350-353` ("payloads") | — | now session-id resolution; **wrong target** |
> | `posttooluse_progress_observer.py:483-484` (dead `Task`/`Agent` branch) | — | branch **deleted** in Step 1; line is now `_handle_bash` |
> | `_loop_counter.py:84,96` (thresholds `6` / `15`) | **`:88,100`** | drifted **since this table was written** — the *values* stay byte-identical (`6` / `15`); re-verified s179 |
> | `_loop_counter.py:508-524` (`increment` couples count+ring) | **`:558-574`** | drifted |
> | `_loop_counter.py:634-638` (`clear_turn_touched`) | **`:777-781`** | drifted |
> | `stop_continuation.py:539` ("the existing reset call") | **`:576`** (call) / **`:224-239`** (`_apply_turn_boundary_reset`) | **wrong target** — `:539` is now a comment in the dispatch-verdict branch |
> | `posttooluse_progress_observer.py:298-303` (`increment`) | `:300` | ✅ range still covers it |
> | `pretooluse_loop_detect.py:140-144,149,211` | as cited | ✅ **exact** — the Step 3 targets |
>
> Also note the **§Context section describes the deleted `("Task","Agent")` branch in
> the present tense** (`:98-99`, `:483-484`). That is historically accurate as a record
> of what Step 1 fixed, but it is not current state.
**Related ADRs:** ADR-013 (row E.4 — the originating trigger, consequence "pause + Telegram alert", `docs/adr/0013-autonomy-axis-relocation.md:90`; D2 deterministic-deny precedent — cited, not amended), ADR-0018 (warn-only-v1 precedent, cited; its Stop-flow context line at `docs/adr/0018-axis-b-verification-loop.md:66` is descriptive and untouched)

## Goal

Change what the L1 file-edit guard **measures**, **when it walls**, and **how a
wall opens** — without touching any threshold value. Today L1 counts *touches*
(every successful Write/Edit of one path, `posttooluse_progress_observer.py:298-303`)
and hard-denies at the bar (`pretooluse_loop_detect.py:149,211`), so six
distinct edits implementing one ratified plan step are indistinguishable from
six retries of the same failing edit — while the actual thrash shape (retrying
a broken `old_string`) cannot increment the counter at all, because the
observer fires only on success. This PLAN (P1) re-keys the L1 count to
**non-progress** — ~~failed/rejected edits,~~ repeated `old_string` attempts and
content-hash oscillation — so distinct forward edits score zero **(the
failed-edit half is WITHDRAWN s179: the harness emits no event for a failed
`Edit`, so it cannot be observed — §D4 box; the thrash shape named two
sentences up stays uncountable, and P1 now delivers only the
stop-miscounting-forward-progress half)**; (P2) demotes
the **first** trip to a Telegram ping + agent-visible warning with the edit
allowed, keeping the deny as a **second**-trip wall; (P3) adds an
`awaiting_ack` marker cleared by a genuinely-fired `Stop`, so a denied target
gets a deterministic, human-in-the-loop exit the agent cannot fake; and (F3c)
wires + fixes the subagent-completion reset that has been **dead code since it
shipped** (2026-06-08), correcting the three documents that describe it as
live. This is Lesson #0021 §6's explicitly deferred "B later" option coming
due (Cray: "A now, B later", 2026-06-08 — `docs/lessons/0021-…md:110-114`),
not a new idea.

## Context — the verified fact base

All file:line references below re-verified on disk this draft (2026-07-25);
facts from the caller's session-173 fact-pack that cannot be grounded in a
repo file are marked *(caller-verified s173)*.

### P1 — the wrong unit of measurement

- `has_triggered` is `count >= threshold` (`_loop_counter.py:551-558`);
  `_handle_write_or_edit` increments on **every** successful Write/Edit
  (`posttooluse_progress_observer.py:277-307`, increment at `:298-303`) with
  no distinctness check, no oscillation check, no reference to the outcome.
- **`ActionRecord.result` has never been populated on the L1 path.** The
  `_now_action(tool, target)` call at `:302` omits `result`, which defaults to
  `""` (`_loop_counter.py:134`). L2/L3/L4 populate it (`"failed"` `:364`,
  `"error"` `:441`, `"failure"` `:344`) — and no decision reads it anywhere.
- **PostToolUse fires only on success, so L1 is blind to failed edits.**
  Probed live *(caller-verified s173)*: a successful Write took the counter to
  1; an Edit whose `old_string` did not match left it at 1 with no new action
  record. Consequence: the retry-the-same-broken-`old_string` thrash — the
  exact shape the guard was designed for — **cannot increment L1 at all**.
  L1 today measures forward progress exclusively.
- ~~**The harness provides the missing event.**~~ **REFUTED s179 — see the
  boxed record under §D4.** The claim was: `PostToolUseFailure` exists in
  Claude Code 2.1.132 *(caller-verified s173, extracted from the harness
  bundle's own schema)* with payload `{hook_event_name, tool_name, tool_input,
  tool_use_id, error, is_interrupt?, duration_ms?}` — note **no
  `tool_response`**; `error: string` is the recordable value (the natural
  filler for the always-empty `ActionRecord.result`). **A live probe registered
  under that exact event name never fired.** The harness does **not** provide
  the missing event, and `ActionRecord.result` therefore stays `""` on the L1
  path — the one design element that would have populated it is withdrawn.
  Classification per CLAUDE.md §6: the s173 *claim* was **`was an error`**
  (a bundle-extracted schema was reported as if it established runtime
  behavior); the *decision* to design D4(a) on it was **`superseded by new
  info`** — it was the correct call on the evidence then available, which is
  precisely why the PLAN made Step 4 probe-first.

### P2 — the deny is the last hard wall

`pretooluse_loop_detect.py:131-152` emits `permissionDecision: "deny"`
(`:149`, printed at `:211`), bypass-immune by design (`:20-27`). The
originating specification never asked for that: **ADR-0013 row E.4**
(`docs/adr/0013-autonomy-axis-relocation.md:90`) defines the trigger's
consequence verbatim as "**pause + Telegram alert** when an agent loops > 6
rounds on the same problem" — the hard deny was a PLAN-0008 Step 2
implementation choice layered on top of the Accepted ADR's wording. Two
in-project precedents additionally demoted sibling guards on identical
reasoning:

- **ADR-0018 D5** — the goal gate is warn-only v1: a FAIL verdict never
  blocks a stop (`.claude/autonomy-triggers.md:216-219`).
- **PLAN-0092** — the Stop-side dispatch order was demoted to a suggestion
  after 14 recorded misfires / 0 recorded valid fires across ~2 months:
  "A misfired suggestion costs one ping; a misfired order cost a turn"
  (`.claude/autonomy-triggers.md:133-134`).

L1 is the last loop row still enforced as a first-strike hard deny — a
posture stricter than its own Accepted-ADR mandate.

### P3 / F3 / F4 — no ack-shaped exit

Lesson #0021 §4 states the general form: a verbal/chat ack does NOT unblock a
deterministic PreToolUse gate; the legitimate unblock is a **state
transition**, not a conversational one — and hand-editing
`loop-counter.json` to dismiss a trip is the forbidden circumvention
(`docs/lessons/0021-…md:79-87`). But no sanctioned state transition
representing "Cray saw this and the turn ended" exists: the turn-boundary
reset is **sticky** (a file touched in turn N survives N's Stop; recovery
costs two turns — Lesson #0021 `:36-39`), and the commit reset requires a
committable tree — which the gated file can itself block (s169: ruff `F821`
on the gated file; `--no-verify` forbidden by CLAUDE.md §8).

### F3c — the reset path that never worked

- `_handle_agent_completion` runs only when `tool_name in ("Task","Agent")`
  (`posttooluse_progress_observer.py:483-484`), but `.claude/settings.json`
  registers PostToolUse for **`Write|Edit` and `Bash` only** (`:38-61`). No
  Task/Agent matcher exists in project settings, and the user-level
  `C:\Users\crayj\.claude\settings.json` has **no `hooks` key at all**
  (re-verified by the drafter this draft). The hook process is never started
  for a Task call: **reset path (c) is dead code and has never been live in
  production.**
- Even if wired, it would not do what its docstring claims: it resets by
  `counter.turn_touched` (`:324`) — whatever the **main agent** touched this
  turn — not by the subagent's edits. A subagent making zero edits would
  still clear the whole turn's budget.
- Its unit tests pass because they feed a synthetic `{"tool_name": "Task"}`
  payload straight into `main()`
  (`tests/handoffs/test_posttooluse_progress_observer.py:595-649`). **Nothing
  asserts the settings.json wiring.** This is the third live instance of
  Lesson #0012 §7's meta-lesson ("don't trust a claimed mitigation — verify
  the mechanism", `docs/lessons/0012-…md:105-108`).
- Three surfaces document the dead path as live: `.claude/autonomy-triggers.md`
  row L1 (`:96`) + the reset-paths paragraph (`:107-111`); Lesson #0021 §3
  item 2 (`:68-72`) + §5 (`:97-99`); and the deny message itself —
  `pretooluse_loop_detect.py:140-144` tells the blocked agent the counter
  resets "for a subagent's edits — when the Agent tool returns", which is
  false.
- Correct events available: `SubagentStop` (already a registered event type —
  `settings.json:85-95`, matcher `plan-drafter` → `subagentstop_notify.py`)
  or `TaskCompleted` *(event list caller-verified s173)*.

### The incident series — four L1 code-path fires in five sessions

From `docs/STATUS.md` *(caller-verified s173)*:

| Session | Target | Outcome |
|---|---|---|
| s168 | `cli.py` at 6 edits | reset via commit; clean |
| s169 | `run_analytics.py` | **genuine deadlock** — all three exits shut (subagent inherits the exhausted counter; turn boundary sticky; commit blocked by ruff `F821` on the gated file); Cray adjudicated twice by typed AskUserQuestion; landed via a **shell escape** |
| s170 | `tests/support/run_corpus_factory.py` | same shape; commit blocked by ruff `C901`; Cray **authorised a shell escape** via a guarded patch script |
| s172 | PLAN-0093 Step 1 (`nl_query.py` work) | false fire — prompted this PLAN |

Stated honestly: **two of four ended in a Cray-authorised shell escape**. The
guard is being routinely bypassed to get legitimate work done — the strongest
available evidence that its failure mode costs more than what it prevents.
No recorded incident shows the L1 deny catching a genuine runaway loop; this
PLAN nevertheless keeps a hard wall (one trip later, P2) rather than going
warn-only, because L1's tail risk — unbounded AFK token burn + file churn —
is destructive in a way the PLAN-0092 dispatch arm's was not. Cray may
overrule toward warn-only at ratification; the warn/deny split makes that a
one-line change later.

### Substrate already shipped — build on it, do not re-plan it

PR #912 (`2d09002`) landed the state-lifetime fix: age-out on load
(`prune_stale_entries`, `COUNTER_MAX_AGE_HOURS = 6.0`, env override —
`_loop_counter.py:111,419-439`), the session boundary
(`load_counter(path, session_id=…)` re-mints on mismatch, `:477-478`), and
`main_session_id(payload)` returning `None` under a subagent's `agent_id` so
a subagent can never wipe the parent's budget (`:346-368`). Everything below
extends this substrate; nothing re-opens it.

### Why no ADR amendment

The originating Accepted-ADR specification of this trigger is **ADR-0013 row
E.4** (`docs/adr/0013-autonomy-axis-relocation.md:90`), verbatim: "**New
trigger:** pause + Telegram alert when an agent loops > 6 rounds on the same
problem". Note what E.4 specifies as the consequence: **pause + Telegram
alert** — not deny. The hard `deny` was a PLAN-0008 Step 2 implementation
choice; nothing in the ADR mandates it. This PLAN therefore needs no
amendment — it moves L1 *toward* the Accepted ADR's own wording, not away
from it: P2's warn (ping first, wall later) is closer to "pause + Telegram
alert" than a first-strike deny is, and P1 changes only the *proxy* for
E.4's "loops on the same problem" (E.4 names the loop; the touch-count proxy
was implementation). The remaining ADR references are descriptive (ADR-0018's
Stop-flow context line, `0018-…md:66`) or unrelated ("L1 schema-validation"
in ADR-0008/0021/0023/0033). The deny semantics being changed have no ADR
mandate to amend, and the E.4 consequence wording is honored *better* after
this PLAN than before it — same posture as PLAN-0092 §Why-no-ADR: **this
PLAN is the governance record.** *(Correction at R2: the first draft claimed
ADR-0018:66 was the only loop-detect ADR reference — the drafter's grep
pattern missed E.4's "loops > 6 rounds" phrasing. Caught by Code R2.)*

## Hard constraint — the anti-pattern (binding on this PLAN and its review)

**No threshold changes, in either direction.** Raising the doc bar 6→15
(2026-06-08) treated the symptom — bar too low *for that path class* — and
the same false-fire class recurred on code paths at 6 (s168–s172). A
threshold raise leaves the cause (**wrong unit of measurement** — touches,
not non-progress) in place, so the false fire returns on whichever path class
still carries the old bar, while the true positive is weakened in the same
motion. `LOOP_TRIGGER_THRESHOLD = 6` (`_loop_counter.py:84`) and
`L1_DOC_THRESHOLD = 15` (`:96`) are byte-unchanged by this PLAN; only the
unit counted under them changes. The base value 6 is also the Accepted ADR's
own number — E.4 reads "loops **> 6 rounds** on the same problem"
(`docs/adr/0013-autonomy-axis-relocation.md:90`) — so keeping the number and
fixing only the proxy for "rounds on the same problem" is fidelity to E.4,
not drift from it. (A companion lesson on this exact anti-pattern is being
written; this PLAN must not contradict it.)

## Design

### D1 — F3c: wire the subagent-completion reset on `SubagentStop`, scoped to the subagent's own edits

**Event: `SubagentStop`, matcher `*`, invoking the existing observer.** Add a
`SubagentStop` entry to `settings.json` whose hooks include
`posttooluse_progress_observer.py`; the observer's `main()` branches on
`hook_event_name == "SubagentStop"` **before** the `tool_name` dispatch.
Why `SubagentStop` over the alternatives: it is the subagent-lifecycle
boundary Lesson #0021 §3 intended, it is already a registered event type in
this project (`settings.json:85-95` — precedent for payload shape), and it
fires regardless of how the subagent was invoked. *Rejected:* a
`PostToolUse` `Task|Agent` matcher (fires only on success; payload shape for
Task unverified here; perpetuates the tool-name coupling that shipped dead);
`TaskCompleted` (task-tracker semantics, unexercised in this repo).
**`settings.json` diff → Cray per-diff approval.**

**Scoping fix: reset the subagent's edits, not the turn's — keyed per
agent.** `_handle_write_or_edit` gains one branch: when the payload carries a
non-empty `agent_id` (the same signal `main_session_id` keys on,
`_loop_counter.py:362-364`), record the target into a new additive state
dict `subagent_touched` (`{agent_id: [targets]}`, deduplicated per key,
sibling to `turn_touched` at `_loop_counter.py:194`; `from_json` tolerant —
missing → `{}`, so old/new readers interoperate). The `SubagentStop` handler
resets L1 for exactly the **completing agent's own** recorded targets (keyed
by the payload's `agent_id`, reusing `reset_l1_for_targets`,
`_loop_counter.py:582-596`), then pops that key. Evidence the event carries
the key: the shipped `SubagentStop` consumer already reads
`payload.get("agent_id")` and formats it into its alert
(`subagentstop_notify.py:62,70`), and it is the same field the
PreToolUse-side subagent signal keys on ("populated live on subagent
payloads", `_loop_counter.py:350-353`); the Step 1 tests pin the keyed
behavior either way. Fail-safe for the unpopulated case: a `SubagentStop`
payload with a missing/empty `agent_id` clears **all** recorded
`subagent_touched` entries — failing toward bounded over-clearing (only ever
subagent-edited targets), never toward leaving a completed drafter's budget
wedged. Consequences: a zero-edit subagent clears **nothing**; the main
agent **cannot launder its own budget through a trivial spawn** (the
self-unlock hazard the current `turn_touched` semantics would have created
had they ever been wired); and with two subagents in parallel, agent A's
completion no longer clears entries recorded by a still-running agent B —
the per-agent keying closes the same cross-contamination class D1 exists to
fix, one level down (R2-3). `turn_touched` and the Stop-hook reset are
unchanged.

> **RATIFIED by Cray 2026-07-25 (session 173) — this is a decision, not a diff
> approval.** The scoping fix above **changes what Lesson #0021 §3 recorded as
> the 2026-06-08 fix**: that lesson describes reset path (c) as resetting "the
> L1 counters for the files touched this turn", i.e. turn-scoped. Cray ratified
> the divergence to subagent-scoped-and-per-agent-keyed. Rationale of record:
> the turn-scoped semantics were never live (no matching event registration), so
> nothing is being taken away — but wiring them **as written** would have
> created a self-unlock path (any zero-edit spawn clears the main agent's
> budget), which is a new hazard, not a restoration. Step 2 must therefore
> record this in Lesson #0021 as **`was an error`** in the CLAUDE.md §6 sense —
> the documented mechanism was never real — rather than as `superseded by new
> info`.

The dead `tool_name in ("Task","Agent")` branch (`:483-484`) is **deleted**,
and its synthetic-payload tests (`test_posttooluse_progress_observer.py:595-649`)
are **rewritten** to the new contract (they currently pin the wrong
semantics).

### D2 — documentation corrections (the F3c fallout)

- `.claude/autonomy-triggers.md`: annotate row L1 (`:96`) and the reset-paths
  paragraph (`:104-112`) — reset path (c) was **dead from wiring** between
  2026-06-08 and PLAN-0094 (handler existed, no matching event registration);
  now live on `SubagentStop`, scoped to the subagent's own edits. Preserve
  machine-readability (`:266-269`); annotation of an existing row, not a new
  row — the PLAN-0092 AC-5 shape (plan-drafter drafts, Code commits, ADR-009
  D1/D2).
- `docs/lessons/0021-…md`: add an amendment section — the §3 item-2 fix
  landed unwired; tests passed on synthetic payloads with nothing pinning the
  wiring; third live instance of Lesson #0012 §7's verify-the-mechanism
  meta-lesson. Classify per CLAUDE.md §6: the lesson's claim was
  **`was an error`** (the fix never worked), not superseded.
- `pretooluse_loop_detect.py:140-144` deny-message dead-path claim: corrected
  in Step 3 (the P2 rewrite replaces the whole message) — noted here so it is
  not edited twice.

### D3 — P2: warn on the first trip, deny on the second

Split responsibilities along the line the codebase already draws (observer
pings L2/L3 inline, `posttooluse_progress_observer.py:210-220`; gate walls
L1/L4):

- **Warn (observer-side).** When an L1 increment crosses the path-class
  threshold `T` (`l1_threshold_for`, `_loop_counter.py:573-579`), the
  observer fires the Telegram ping (existing `{loop_type, target,
  last_6_actions}` contract + a `stage: warn` line) and emits the
  **agent-visible** advisory: the PostToolUse `{"decision": "block",
  "reason": …}` output shape, which feeds the reason into the model's context
  without undoing the already-completed write — the write is allowed, the
  agent is told "L1 warn on `<target>`: N non-progress edits; reassess;
  `+G` more deny". Fired **once** per (target, warn stage): a `warned_at`
  stamp on the entry dedupes; grace-zone edits do not re-ping. The observer's
  "never blocks" docstring (`:5-6`) is reworded to "never denies a pending
  tool call; may attach advisory feedback". *Rejected:* warning via
  PreToolUse `permissionDecision: "ask"` — an AFK Cray turns "ask" into a
  block, which is the pause we are demoting, not a warn.
- **Deny (gate-side).** `pretooluse_loop_detect.py` denies L1 only at
  `count >= T + G` (`G` = grace budget, **OQ-1**, recommended 3). The deny
  message is rewritten: reports the warn→deny semantics and the *real* exits
  (turn boundary with the sticky caveat; commit; subagent-scoped reset; the
  P3 stop-ack) — the dead-path claim (`:140-144`) dies here. L4 deny
  behavior is untouched (its unit is already failure-based; no recorded
  false-fire series).

The mandate argument outranks the precedents: E.4's stated consequence was
"pause + Telegram alert" all along (§Why no ADR amendment) — warn-first
*restores* the Accepted ADR's own consequence, and the second-trip deny is
hardening retained beyond the mandate, not required by it.

### D4 — P1: count non-progress, not touches

> **⚠️ D4(a) WITHDRAWN — the probe refuted its premise (s179, 2026-07-27).**
>
> Step 4's own probe-before-build instruction fired and returned a negative.
> **A failed `Edit` invokes no hook in this harness build — not
> `PostToolUseFailure`, and not `PostToolUse` either.** Two independent
> measurements, one session apart:
>
> 1. **s173** — the observer, live on `PostToolUse`: "a successful Write took
>    the counter to 1; an Edit whose `old_string` did not match left it at 1
>    with no new action record" (§Context P1, third bullet). Already in this
>    PLAN — it is what motivated (a).
> 2. **s179** — a payload-dump probe registered on **both** events at once,
>    so one run covered both. A successful `Write` dumped
>    `hook_event_name: "PostToolUse"`, keys `[cwd, duration_ms, effort,
>    hook_event_name, permission_mode, prompt_id, session_id, tool_input,
>    tool_name, tool_response, tool_use_id, transcript_path]`, `tool_response`
>    carrying `[content, filePath, originalFile, structuredPatch, type,
>    userModified]` and **no `error` key**. An `Edit` whose `old_string` was
>    absent then failed as designed and dumped **nothing at all**.
>
> **The control is what makes this readable.** Without a known-good event in
> the same run, "no dump" is indistinguishable from "the config never
> reloaded" — and hook registrations are snapshotted at session start, so a
> mid-session `settings.json` edit has no effect (measured s178; the probe
> had to be staged, then armed by a restart). The pass/fail read was fixed
> **before** the run and the "neither fired" cell was pre-labelled
> INSUFFICIENT-EVIDENCE, not a pass.
>
> **Consequences.** (a) is withdrawn, and with it **AC-1(ii), AC-6, and
> AC-8(ii)** — every criterion whose subject is a `PostToolUseFailure`
> payload. The `settings.json` registration is not written, so **Step 4 loses
> its Cray per-diff gate** (Lesson #0021 §4 applies to guard
> self-modification; there is now no self-modification to approve). **(b) and
> (c) survive whole** on the success path, as does the `observe()` /
> `increment()` split and `clear_turn_scoped()`.
>
> **What is permanently lost, stated plainly:** the s169-class thrash —
> retrying one broken `old_string` — remains **uncountable**, because the
> harness emits no observation of it. This PLAN's §Goal calls that "the exact
> shape the guard was designed for". Step 4 now delivers the *other* half:
> distinct forward edits stop being miscounted as thrash (AC-7). **Re-open
> trigger:** any future Claude Code build that emits a hook event on a failed
> tool call — re-probe with the same control-plus-subject shape before
> believing a schema, whatever its source.

The L1 `count` becomes a count of **non-progress observations**:

- ~~**(a) Failed / rejected edit**~~ — **WITHDRAWN s179, see the box above.**
  The design was: a new `PostToolUseFailure` registration, matcher
  `Write|Edit`, invoking the observer; the handler branching on
  `hook_event_name == "PostToolUseFailure"` **before** the tool-name dispatch
  (the payload also carries `tool_name: "Write"|"Edit"` and must not fall into
  the success path); incrementing L1 with `result = error[:200]`; and
  registering `sha1(old_string)` in the per-target attempt set so (b) sees
  failed repeats. The stated dependency — "**(b) cannot see *failed* repeat
  attempts unless (a) is wired**" — still holds and is now the shape of the
  loss, not of a build order: (b) sees **successful** repeats only.
  *Worth keeping for whoever re-opens this:* the "branch before the tool-name
  dispatch" instruction was load-bearing and remains correct. `main()`
  dispatches on `tool_name` after its `SubagentStop` check
  (`posttooluse_progress_observer.py:665`), so a failure payload would have
  been routed into `_handle_write_or_edit` and counted as a **success** —
  the opposite of the intent. AC-6's own "payload falls through `main()`"
  wording understated this; it would not have fallen through, it would have
  been mis-handled.
- **(b) Repeated `old_string`** — per-target, per-turn set of
  `sha1(old_string)` (additive entry field `attempted_edits`). A successful
  Edit whose `old_string` hash is already present increments (the same
  operation re-applied is churn, not progress). Edge accepted, not fixed:
  sequentially applying one `old_string` to multiple genuine occurrences
  counts as non-progress — mitigations are `replace_all`, distinct context
  strings, and P2 itself (the first mis-count now costs a ping, not a block).
- **(c) Oscillation** — after each successful Write/Edit, `sha1` of the
  on-disk file content; a hash already seen this turn on this target (the
  file returned to a prior state) increments; otherwise it is appended
  (additive entry field `content_hashes`, capped at 32/target/turn).
- **Distinct successful forward edits score zero.** The action is still
  appended to the `last_6_actions` ring for evidence, and `turn_touched` is
  still recorded (Stop semantics need it regardless) — a new record-only
  `observe()` op lands beside `increment()` in `_loop_counter.py`, since
  `increment` couples count+ring (~~`:508-524`~~ → **`:558-574`**, re-verified
  s179).
- **Per-turn scoping:** the Stop hook clears `attempted_edits` /
  `content_hashes` on entries that survive the turn (a
  `clear_turn_scoped()` sibling to `clear_turn_touched`, ~~`:634-638`~~ →
  **`_loop_counter.py:777-781`**, re-verified s179);
  `count` keeps today's lifetime (reset paths unchanged). All state fields
  are additive; `from_json` tolerance + the 6 h age-out (#912) mean stale
  schemas self-clear — no migration.
- **Scope guard:** ~~the `PostToolUseFailure` registration is matcher
  `Write|Edit`~~ — moot with (a) withdrawn; **no new registration ships**.
  The guarantee it existed to give still holds, and now trivially: Step 4
  touches `_handle_write_or_edit` only, so it feeds **only L1**, and
  L2/L3/L4 semantics are byte-unchanged (they already count failures — the
  right unit, via `PostToolUse` on `Bash`, which *does* fire on a non-zero
  exit and is read by `_bash_outcome`, `posttooluse_progress_observer.py:263-293`).
  **This asymmetry is the finding in one line: the harness reports a failed
  `Bash`, but not a failed `Edit`.**

### D5 — P3: `awaiting_ack` — the deterministic exit the agent cannot fake

- **Write:** on emitting a deny, the gate appends the normalized target to a
  new top-level state list `awaiting_ack` (additive; atomic save via the
  existing `os.replace` path). This makes Step 2's gate a state **writer** for
  the first time (docstring `:17-19` updated); the write happens only on the
  deny branch, and a racing lost write self-heals — the deny re-fires on the
  next attempt and re-writes.
- **Clear:** `stop_continuation.py` clears the marker and resets the L1
  entries for the marked targets **only on the paths where the stop actually
  fires** — pause (`:618-621`), cap-hit (`:546-549`), dispatch-suggestion
  (`:587-616`), contentless-proceed demotion (`:574-580`). It does **not**
  clear on the classifier-`proceed` block (`:581-585`) or the goal-gate
  directive (`:555-561`) — those return the agent to its loop without Cray;
  clearing there would let the machinery unlock itself. The re-entry
  early-return (`:533-534`) also does not clear (conservative).
- **Why unforgeable:** a fired stop by construction ends the turn and returns
  the prompt to Cray — the agent cannot mint one. The deny's Telegram ping
  told Cray *why* the turn is ending; Cray's next typed message is the go.
  Marker written only by the deny gate, cleared only by the Stop hook — **no
  agent-side action touches it**, so P3 is not a sanctioned version of the
  forbidden `loop-counter.json` hand-edit (Lesson #0021 §4); that
  prohibition stands verbatim.
- **Honest limit, recorded:** the guarantee is "the turn ended and Cray
  regained the prompt", not "Cray typed an explicit ack token". The stronger
  form (parse an ack out of `UserPromptSubmit`) was considered and declined
  v1: it parses conversation content (injectable) and the weaker form already
  beats every recorded incident — in s169/s170 Cray was present and typing;
  what was missing was *any* working state transition.
- **Sticky-turn override:** the ack-clear runs at the same Stop the sticky
  rule would skip (target touched this turn) — for exactly the denied
  targets, two-turn recovery becomes one. Fresh-budget size is **OQ-2**
  (recommended: full reset — entry deletion, same as every other reset path).

## Acceptance Criteria

Each AC names the test that proves it and the mutation that reddens it. All
are deterministic-offline; `tests/handoffs/` runs happen in the **main tree**
(5 hook tests are known false-RED in a git worktree).

- [x] **AC-1 (CLOSED — (i)+(iii) at s174 #917; (ii) WITHDRAWN s179) — the settings wiring is pinned by a test (the F3c class-killer).**
  New `tests/handoffs/test_settings_hook_wiring.py` parses
  `.claude/settings.json` as data and asserts: (i) a `SubagentStop` entry
  whose hooks include `posttooluse_progress_observer.py`; ~~(ii) a
  `PostToolUseFailure` entry, matcher `Write|Edit`, including the same
  observer;~~ (iii) the existing `PostToolUse` `Write|Edit` + `Bash`
  registrations are retained. **RED today** (neither registration exists) —
  and RED forever after against the exact gap that let reset path (c) ship
  dead with green tests.
  **(ii) WITHDRAWN s179 with D4(a).** The registration is not written, so
  there is nothing to pin. The module's own scope note (`:17-24`) records
  that (ii) was *deliberately left unasserted rather than asserted-and-skipped*
  — "a check that passes because it was skipped is exactly the vacuous form
  this module was written to kill." **Step 4 must update that docstring** to
  say withdrawn-on-evidence rather than pending-at-Step-4; leaving it as-is
  would leave the module claiming a debt that no longer exists. No test is
  added and none is skipped — the correct closure for a criterion whose
  subject does not exist.
- [x] **AC-2 (CLOSED s174 #917) — SubagentStop resets exactly the completing subagent's
  edits.** Rewritten tests in
  `tests/handoffs/test_posttooluse_progress_observer.py` (replacing
  `:595-649`): a `SubagentStop` payload resets L1 for the completing agent's
  recorded targets; a zero-edit subagent's completion resets **nothing**; a
  target edited only by the main agent **survives** (the anti-self-unlock
  assertion); with two agents recorded, agent A's completion resets only A's
  targets while **B's survive** (the R2-3 parallel case); a payload with a
  missing `agent_id` clears all recorded subagent entries (the bounded
  fail-safe). **RED** against today's code (no `hook_event_name` branch; the
  old semantics reset by `turn_touched`).
- [x] **AC-3 (CLOSED — 2 of 3 at s174 #917 [registry row L1 + Lesson #0021 §3], the deny message at s175 Step 3) — the three lying surfaces are corrected.** Grep oracle:
  `PLAN-0094` is non-empty in `.claude/autonomy-triggers.md` **and**
  `docs/lessons/0021-l1-loop-detect-subagent-and-doc-threshold.md`
  (impossible today), and `pretooluse_loop_detect.py` no longer contains the
  anchor `for a subagent's edits` — chosen because it exists as one
  contiguous run on a single source line today (`:142`), whereas the prose
  phrase "when the Agent tool returns" is split across the f-string boundary
  `:142-143` and does **not** exist as a contiguous source string: an oracle
  keyed on it would pass vacuously today and forever (R2 catch — the exact
  vacuous-oracle failure class AC-1 exists to kill). Constraint on Step 3:
  the rewritten deny message describes the restored reset in `SubagentStop`
  wording and must not re-use the anchor phrase, so the oracle stays
  non-vacuous after the fix.
- [x] **AC-4 (CLOSED s175 Step 3) — warn stage allows; deny moves to the second trip.** Gate
  tests: seeded `count` in `[T, T+G)` → `main()` emits **no** deny JSON
  (edit allowed); seeded `count >= T+G` → deny emitted, with the rewritten
  message naming the real exits. **RED today** — the gate denies at `T`
  (`pretooluse_loop_detect.py:198-211`).
- [x] **AC-5 (CLOSED s175 Step 3) — the warning is agent-visible and fires once.** Observer tests:
  an L1 increment crossing `T` emits the advisory `decision: block` reason on
  stdout exactly once and one Telegram warn ping (capture stub, existing
  `CLAUDE_TELEGRAM_SCRIPT` pattern); further grace-zone edits emit neither.
  **RED today** (the observer never prints and never pings for L1 —
  `:305-306`).
- [~] **AC-6 — ~~failed edits finally count~~ — WITHDRAWN s179, premise
  refuted.** The criterion was: an observer test in which a
  `PostToolUseFailure` payload (per the s173 schema — `error` string, **no**
  `tool_response`) increments L1 and records `result == error[:200]`
  (non-empty — the field that has been `""` on every L1 record). **The event
  does not fire** (§D4 box), so the only way to make this test green would be
  to feed a synthetic payload straight into `main()` — a test that passes
  while the live path stays dead, which is the precise failure class **AC-1
  was written to kill**. It is therefore withdrawn rather than weakened.
  **Consequence carried forward: `ActionRecord.result` stays `""` on every L1
  record.** It is the only field on the L1 path with no writer, and D4(a) was
  its only planned one — see the open question at §Open Questions (OQ-3).
- [ ] **AC-7 — distinct forward progress scores zero (the s168/s172
  regression test).** Observer test: six successful Write/Edits of one
  target with distinct `old_string`s and advancing content hashes leave
  `count == 0` while `turn_touched` contains the target and the ring buffer
  holds the actions. **RED today** (count would read 6 — today's unit is the
  mutation).
- [ ] **AC-8 (RE-SCOPED s179 — (i)+(iii) stand, (ii) WITHDRAWN) — repeats and oscillation count.** Observer tests: (i) the same
  `old_string` sha1 twice (success path) → `count == 1` after the second;
  ~~(ii) two `PostToolUseFailure`s carrying the same `old_string` →
  `count == 2` (the (a)+(b) dependency, otherwise invisible);~~ (iii) a
  content hash returning to a previously-seen state → increment. ~~**RED**
  against a build that ships (a) without (b)/(c) or vice versa.~~
  **(ii) WITHDRAWN with D4(a)** — its subject is a `PostToolUseFailure`
  payload. (i) and (iii) are success-path only and are unaffected; both are
  **RED today** against touch-counting, which increments on every edit and so
  cannot produce `count == 1` after two identical `old_string`s. The
  non-vacuity mutation for the re-scoped AC-8 is therefore **not** "ships (a)
  without (b)/(c)" — that mutation no longer exists. Replace it with: drop
  the `attempted_edits` membership check → (i) reddens; drop the
  `content_hashes` membership check → (iii) reddens; each mutation must
  redden exactly its own row.
- [x] **AC-9 (CLOSED s177 Step 5) — `awaiting_ack` lifecycle.** Tests across gate + Stop hook: a
  deny writes the marker; a Stop that **fires** (patched classifier →
  `pause`) clears it and resets the target's entry *even though the target
  was touched this turn* (sticky override); a classifier-`proceed` block
  (substantive reason) does **not** clear; a goal-gate directive does **not**
  clear. **RED today** (no marker exists; the sticky rule keeps the counter).
  *[Built s177: 11 rows — 4 gate-side, 7 Stop-side. **8 were RED-first**; the
  three negative rows ("must NOT arm", "must NOT clear") pass trivially against
  featureless code, so each was proven by a named mutation instead — dropping
  the L1 scope guard, clearing inside the re-entry guard, and clearing on a
  substantive proceed each reddened exactly its own row. One finding the
  RED-first run surfaced that the design had not anticipated: the marker is
  **dropped on every Stop regardless of path** unless `awaiting_ack` round-trips
  through `LoopCounter.to_json`, because the always-on turn-boundary reset
  rewrites the whole document — so the negative rows would have "passed" for
  the wrong reason. Additive-and-tolerant was necessary but not sufficient;
  additive-and-**serialized** is the actual requirement.]*
- [ ] **AC-10 — offline gate green; siblings byte-unchanged.** Full
  `pytest tests/` + `mypy` at CI scope + `ruff check` in the main tree; the
  existing L2/L3/L4, commit-reset, and Stop turn-boundary test blocks stay
  green **unmodified**; threshold constants byte-unchanged
  (~~`_loop_counter.py:84,96`~~ → **`:88,100`**, re-verified s179 — the
  **values `6` and `15` are byte-identical**; only the line numbers moved,
  and the s175 drift table's "✅ exact" row for this entry is now itself
  drifted). Non-vacuity sweep: for each of AC-1…AC-9 **that is still live**
  apply the named mutation in the working tree, watch the named test go RED,
  restore from a `/tmp` copy (never `git checkout` — it wipes the uncommitted
  work under test), re-run GREEN. CI is PR-only → re-run the full suite on
  each merge commit.

## Out of Scope

- ❌ **Any threshold change** — `LOOP_TRIGGER_THRESHOLD = 6` /
  `L1_DOC_THRESHOLD = 15` stay byte-identical (see §Hard constraint). This
  includes "harmonizing" the doc/code split that P1 may eventually make
  redundant — a follow-up note, not a step.
- ❌ L2/L3 auto-reset — stays deferred per PLAN-0008 §Step 8.
- ❌ Anything shipped in PR #912 (age-out, session boundary,
  `main_session_id`) — substrate, referenced not re-planned.
- ❌ L2/L3/L4 unit-of-measurement or deny changes; `PostToolUseFailure`
  feeding anything but L1.
- ❌ The Stop-hook classifier / dispatch / goal-gate arms (PLAN-0092 /
  ADR-0018 territory) — the P3 clear is an addition to the Stop flow, not a
  change to any arm's verdict handling.
- ❌ Any sanctioned manual counter-clearing tool/CLI — the Lesson #0021 §4
  prohibition on hand-editing `loop-counter.json` stands verbatim.
- ❌ `UserPromptSubmit` ack-token parsing (the stronger F4 form — declined
  v1, D5).

## Steps

Ordered by risk, cheapest and most-reversible first. The unwired-reset fix
leads: it restores a documented exit that never worked, would plausibly have
unblocked s169/s170/s172, and touches neither deny semantics nor the counting
unit. P2 (warn-first) lands **before** P1 (unit change) deliberately: once
the warn stage exists, any imprecision during P1's shakeout costs a ping, not
a wall. Recommended landing: four PRs (Step 1+2 / Step 3 / Step 4 / Step 5),
each soaking on Cray's live loop before the next; Step 6 closes out. Every
`settings.json` diff is presented to Cray **per-diff** before commit
(Lesson #0021 §4 — routing pick ≠ per-diff approval).

### Step 1: F3c — wire + fix the subagent-completion reset (D1; AC-1, AC-2)

`settings.json`: add the `SubagentStop` matcher-`*` entry invoking the
observer **[Cray per-diff]**. `posttooluse_progress_observer.py`: branch
`main()` on `hook_event_name` first; new `SubagentStop` handler resets by the
completing agent's `subagent_touched` key (missing-id → clear-all fail-safe,
D1); `_handle_write_or_edit` records `agent_id`-carrying edits under
`subagent_touched[agent_id]`; delete the dead `("Task","Agent")` branch.
`_loop_counter.py`: additive `subagent_touched` dict + JSON round-trip.
Tests: AC-1 wiring pin (new module) + AC-2 rewrites, RED-first against the
unmodified code.
*Rollback:* revert the PR — the state field is additive and ignored by old
readers; behavior returns exactly to today's (dead path, documented in Step 2
as historical).

### Step 2: documentation corrections (D2; AC-3)

Annotate `.claude/autonomy-triggers.md` row L1 + reset-paths paragraph
(dead-from-wiring window 2026-06-08 → PLAN-0094; now `SubagentStop`-scoped);
amend Lesson #0021 (`was an error` classification; the wiring-pin moral).
Rides the Step 1 PR (the corrections are true only once Step 1 lands).
*Rollback:* docs revert; no behavior.

### Step 3: P2 — warn-first, deny-second (D3; AC-4, AC-5; completes AC-3's deny-message string)

`posttooluse_progress_observer.py`: warn emission (advisory
`decision: block` reason + Telegram `stage: warn` ping) on crossing `T`, with
`warned_at` dedupe; docstring contract reword. `pretooluse_loop_detect.py`:
deny bar moves to `T + G` for L1 (L4 untouched); deny message rewritten (real
exits; dead-path string removed). `_loop_counter.py`: additive `warned_at`.
Tests per AC-4/AC-5, RED-first.
*Rollback:* revert the PR → first-trip deny returns (today's behavior);
additive state ignored. This step is deliberately independent of Step 4 — if
P1 is delayed, warn-first alone already converts the s172 shape from a wall
into a ping.

### Step 4 (RE-SCOPED s179): P1 — non-progress counting (D4 minus (a); AC-7, AC-8(i)/(iii))

**The probe ran and returned a refutation — see the §D4 box.** No
`settings.json` diff ships, (a) is not built, and **this step is no longer
Cray-gated**. What remains is deterministic-offline:

- `attempted_edits` (b) + `content_hashes` (c) as **additive** entry fields
  (`from_json` tolerance + the 6 h age-out mean stale schemas self-clear).
- `observe()` — a record-only op beside `increment()` in `_loop_counter.py`
  (`:558-574`), since `increment` couples count+ring.
- `_handle_write_or_edit` **increments only on (b)/(c), observes otherwise**
  — this is the whole of AC-7.
- `clear_turn_scoped()` wired into the Stop hook's existing reset call:
  `_apply_turn_boundary_reset` (`stop_continuation.py:224-239`, called at
  `:576`), beside the `clear_turn_touched(counter)` at `:237`.
  *(The PLAN's original `stop_continuation.py:539` citation is stale — `:539`
  is now a comment inside the dispatch-verdict branch. Re-verified s179.)*
- Update the `test_settings_hook_wiring.py` scope note (`:17-24`) per AC-1(ii).

Tests per **AC-7 and AC-8(i)/(iii)**, RED-first — AC-7 is the regression test
for the incident series and is the reason this step is still worth building.

*Rollback:* revert the PR → touch-counting returns. State self-clears via
age-out; no migration either direction. **No registration to remove** — the
"removing the registration returns L1 to success-only blindness" clause is
withdrawn with (a); L1 **remains** blind to failed edits either way, which is
now a harness limit rather than a rollback consequence.

### Step 5: P3 — `awaiting_ack` (D5; AC-9)

`pretooluse_loop_detect.py`: write the marker on deny (docstring: gate is now
a narrow writer). `stop_continuation.py`: clear + reset marked targets on the
fired-stop paths only (pause / cap / dispatch-suggestion / contentless
demotion — not proceed, not goal-gate directive, not re-entry).
`_loop_counter.py`: additive top-level `awaiting_ack`. Tests per AC-9,
RED-first, including the two negative cases (proceed, goal-gate).
*Rollback:* revert the PR → no ack exit (today's behavior); a stale marker in
state is inert to reverted code and age-outs with the file.

### Step 6: closeout (AC-10)

Full offline gate in the main tree; sibling-invariance check; non-vacuity
mutation sweep with `/tmp`-copy restores; per-PR merge-commit re-runs (CI is
PR-only). Update `docs/STATUS.md`; `git mv` this PLAN to `done/` only after
Cray confirms the live-loop soak raised no regression (the guards run on
Cray's own working loop — the soak *is* part of verification).

## Open Questions — OQ-1/OQ-2 RESOLVED by Cray 2026-07-25 (s173); **OQ-3 OPEN (raised s179)**

OQ-1 and OQ-2 were priced as recommended; the values below are **locked** and
Steps 3 and 5 build to them. Recorded here rather than left open so the
committed PLAN does not read as awaiting a decision that has been made.
**OQ-3 is new** — it exists only because D4(a) was withdrawn, and Step 4
cannot be built without answering it.

- **OQ-1 → RESOLVED: `G = 3`** (deny at `T+3`). Cray took the recommendation.
- **OQ-2 → RESOLVED: full fresh budget** after an acknowledged pause (entry
  deletion, identical to every other reset path). Cray took the recommendation
  — so no third threshold class is minted, which keeps D5 consistent with this
  PLAN's own anti-pattern argument.

The original framing of each, retained for the reasoning lineage:

- **OQ-1 — the grace budget `G` (P2).** Recommended **3** (deny at `T+3`):
  large enough to finish a step's tail after a warn (s168 needed 0 more
  productive edits post-6; s172's step would have finished), small enough
  that a genuinely thrashing agent burns ≤ 3 more non-progress attempts
  AFK. Alternative: 6 (a full second budget — more forgiving, doubles the
  worst-case AFK burn). Cray's call because `G` prices exactly how much
  unattended token burn Cray tolerates between the ping and the wall — a
  cost/comfort tradeoff, not a correctness one.
- **OQ-2 — the post-ack budget (P3).** Recommended **full fresh budget**
  (entry deletion — identical to every other reset path; simplest; and under
  P1 the refilled budget measures non-progress, so a refill is cheap).
  Alternative: a reduced budget (e.g. `ceil(T/2)`) for a target that has
  already walled once this session — more conservative, but it mints a third
  threshold class, which rubs against this PLAN's own anti-pattern argument.
  Cray's call because it sets how much rope a twice-suspect target gets while
  Cray may still be AFK after the ack-turn.

### OQ-3 (OPEN, raised s179) — what writes `ActionRecord.result` on the L1 path now?

**Why this is suddenly a question.** `ActionRecord.result` has never been
populated on the L1 path (§Context P1, second bullet: `_now_action(tool,
target)` omits it, defaulting to `""` — `_loop_counter.py:134`). D4(a) was its
**only** planned writer. With (a) withdrawn, Step 4 ships a counter that
increments on repeats and oscillation while every record in the `last_6_actions`
evidence ring still says `result: ""`. **Cray reads that ring** — it is what the
deny message and the Telegram ping point at when the guard walls a target.

**The three options, with the trade-off named:**

- **(a) Leave it `""`.** Zero code. Honest — nothing observed the outcome, so
  nothing is claimed. Cost: the ring shows six identical-looking `Edit` rows and
  cannot answer "*why* did this trip?" without re-reading the diff.
- **(b) Populate with the non-progress reason** that caused the increment —
  e.g. `"repeat:<sha1[:8]>"` for a (b) hit, `"oscillation:<sha1[:8]>"` for a
  (c) hit, `""` for an observed-not-counted edit. The ring becomes
  self-describing: a wall says *which* rule fired, per action. Cost: `result`
  now means "why this counted", not "how the tool call ended" — a quiet
  semantic change from L2/L3/L4, which use it for outcomes (`"failed"`,
  `"error"`, `"failure"`). Note **no decision reads the field anywhere today**
  (§Context P1), so the change is observably safe; it is a naming/consistency
  cost, not a behavioral one.
- **(c) Drop `result` from the L1 path.** Smallest surface, but deletes a field
  the sibling levels populate, and forecloses (b) later for no gain.

**Recommendation: (b).** The whole PLAN is about making the guard's *unit* mean
something; leaving the evidence ring mute keeps the diagnosis manual at exactly
the moment Cray is interrupted. The semantic drift from L2/L3/L4 is real but
contained — no reader exists to break, and L1 is genuinely measuring a different
thing (non-progress) than the levels that record outcomes.

**Cray's call because** it decides what Cray sees in the ring at the moment the
guard walls, which is a working-experience judgment, not a correctness one — the
same class as OQ-1's cost/comfort tradeoff. **Step 4's build is blocked on this
answer**: `_handle_write_or_edit` must pass *something* (or nothing) to
`_now_action` on the increment paths, and retrofitting the string later means
re-touching every AC-8 assertion.

## Verification

- **The offline oracle is the gate** (CLAUDE.md §8): every AC is
  deterministic hook logic exercisable via in-process tests + capture stubs;
  no MS-S1 involvement anywhere in this PLAN. `tests/handoffs/` verdicts are
  read in the **main tree** (known worktree false-REDs).
- **Two cheap live checks, both in-worktree and non-host-state, evidence not
  gate:** (i) the Step 4 `PostToolUseFailure` probe (schema confirmation
  before building on it); (ii) after Step 3, one deliberate warn-crossing on
  a scratch file to confirm the advisory reason actually surfaces in the
  agent's context — the channel contract is harness-documented but this
  project has never used it.
- **Non-vacuity is per-AC and mutation-named** (AC-10): the exact gap this
  PLAN exists to close — green tests over dead wiring — is re-tested against
  itself by AC-1, which fails on registration removal alone, no hook-code
  mutation required.
- **The reversal seam is clean per step:** every state-schema change is
  additive + `from_json`-tolerant + age-out-bounded (6 h), every behavior
  change is a single-PR `git revert`, and no step depends on a later one
  (F3c, P2, P1, P3 each stand alone; only (b)-sees-failed-repeats depends on
  (a), and both live inside Step 4).

---

*Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased
authority; ADR-012 D4.3 author≠reviewer disclosure). Outline originator: Code
(session-173 dispatch, 2026-07-25, from Cray's approved P1/P2/P3 direction +
the Cray-routed F3c fold-in). Independent reviewer: Cray at PR merge; Code
performs R2 + commits per ADR-009 D2. Separation: INTACT.*
