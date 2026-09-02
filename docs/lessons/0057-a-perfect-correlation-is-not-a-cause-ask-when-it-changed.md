# Lesson #0057 — a perfect correlation is not a cause; ask when it changed

**Session:** 270 (2026-09-02); **resolved session 271** (same day) · **Subject:** three
subagents vanished from the harness registry (`goal-evaluator`, `plan-drafter`, `status-scribe`)
**Status:** advisory. The **do-not-act** instruction it carried was **discharged s271** once the
client change was confirmed — see "Resolution". It lives here because a gitignored handoff is
not a surface anyone greps.

---

## The situation

Since session 269, three of the four project subagents defined in `.claude/agents/` stop
being offered by the harness. `explore-research` — same directory, same last-touching
commit — keeps loading fine. The s269 handoff recorded it honestly as *"the cause is
unknown"* and told the next session to re-check rather than assume.

Session 270 re-checked, found **four** hypotheses that each fit the evidence **perfectly**,
and every one of them was wrong.

## The four dead hypotheses, and why each looked so good

The four files split 1-registered / 3-missing. With n=4, a great many properties split the
same way. Each of these was a clean 4/4:

| # | Hypothesis | Why it looked right | What killed it |
|---|---|---|---|
| 1 | **exec bit stripped** — the known WSL-UNC hazard in this repo | the session opened with `tools/notify/*.sh` showing pure `100755 → 100644` mode drift, so the hazard was demonstrably live; all three declared hook scripts are `100644` | `stop_continuation.py` is **also** `100644` and was firing the goal gate all session. A control on a known-working instance |
| 2 | **`hooks:` in the frontmatter** — present on exactly the 3 missing, absent from the 1 present | a genuinely clean 4/4 split, and the only frontmatter key that splits that way (`effort` covers just 1 of 3) | `git log -S` dates the blocks to **2026-05-26 / 06-03 / 06-10**. They worked for three months. _[**was an error**, s271: the *agents* worked for three months; the *hooks block* never did — the old client discarded it at load. Right property, wrong mechanism — see Resolution]_ |
| 3 | **`command:` lacks the `python` prefix** that `settings.json` uses on every hook | a real inconsistency, and a plausible load-time validation failure | same dates. It has always been written that way. _[s271: irrelevant — the flat form fails identically with `python` added; the schema rejects the shape, not the spelling]_ |
| 4 | **`Write`/`Edit` in `tools:`** — declared by all 3 missing, by neither the 1 present | fits 4/4, and a plausible policy tightening | `statusline-setup` (Tools: Read, **Edit**) and `general-purpose` (Tools: `*`) **are registered** in the same session |

A fifth, file size, also splits 4/4 (5,245 B present; 9,319 / 9,525 / 14,661 B missing) and
is equally irrelevant — see below.

## What actually settled it

Not a better correlation. **A question about time:**

> *When did this property last change?*

- `.claude/agents/` last changed at **`8114e5e`, 2026-09-01 14:42** (session 267).
- `.claude/settings.json` last changed **2026-08-29**.
- Commit **`9cffe2c`** (session 269, **2026-09-02**) says in its own body:
  *"Authored by the in-harness status-scribe subagent (ADR-013 D1)"*.

That last line is **tracked evidence in git**, not a handoff claim: `status-scribe` ran
successfully on 2026-09-02, *after* the last modification to its own definition file.

**Therefore the files are byte-identical to when they last worked.** No property of any
file — hooks block, tool list, command spelling, size — can explain a change, because
none of them changed. The variable that moved is in the **client/harness runtime**,
outside the repository.

## The generalisable lesson

**A hypothesis has to explain the CHANGE, not just fit the split.** A static property
cannot cause a transition. Before ranking correlations, ask the cheap question — *when did
each candidate last change?* — and discard everything that predates the last known-good
observation. Here that one question killed four hypotheses that no amount of further
correlation-hunting would have separated.

The corollary is about **n**: with four items, dozens of properties split 1/3. Correlation
strength is nearly worthless at that scale; **timeline evidence is not**, because it is a
different kind of evidence rather than more of the same. (Lesson
[#0053](0053-two-sessions-agreeing-through-one-instrument-is-one-measurement.md) is the
same shape from the other side — more agreement through one instrument is still one
measurement.)

## Resolution (session 271) — the client's tolerance moved, not the files

Session 271 ran the procedure below and closed every step:

1. **New conversation** (the registry is rebuilt only at session start): still absent. A
   deliberately failing spawn made the runtime say so — `Agent type 'goal-evaluator' not found.
   Available agents: …` — while `explore-research` spawned and answered in the same batch, the
   positive control without which two errors could have meant "the Agent tool is broken".
2. **The client updated.** Every transcript record carries the client version. Session 269's
   own log starts on **2.1.247**, spawns `status-scribe` at 18:00:35Z (→ `9cffe2c`), then flips
   to **2.1.255** at **2026-09-02T02:27:58Z** mid-session. Thirteen sessions on ≤ 2.1.247 spawned
   these agents; none on 2.1.255 did.
3. **What 2.1.255 rejects — in the client's own words.** The Desktop app keeps its bundled CLIs
   at `%APPDATA%\Claude\claude-code\<version>\claude.exe`, and `claude.exe -p noop --debug-file
   <f>` logs agent loading *before* it reaches auth, so this needed no API call:

   > `[ERROR] Agent 'goal-evaluator' not loaded: hooks.PreToolUse.0: Hook matcher "hooks" must
   > be an array of hook entries; received undefined — a PreToolUse/PermissionRequest hook that
   > cannot be loaded may be what guards the permissions declared beside it, so nothing it sits
   > in is applied until the entry is fixed or removed`

   The three files wrote the hooks block **flat** — `matcher:` and `command:` on the same list
   item. The documented shape (sub-agents docs, hooks docs, and this repo's own
   `settings.json`) is `matcher:` plus a nested `hooks:` array of `{type: command, command}`.
   The flat form was never documented anywhere. Same six-file probe set, both bundled binaries:

   | agent file | 2.1.247 | 2.1.255 |
   |---|---|---|
   | flat hooks (the repo's) | `Invalid hooks in agent … expected array, received undefined` logged at **DEBUG**; block **discarded, agent loaded** | same failure logged at **ERROR**; **agent refused** |
   | flat + `python` prefix | same | same — the prefix is irrelevant |
   | nested (documented) | loaded | loaded |
   | no hooks block | loaded | loaded |

   Hypothesis #2 had the right property and the wrong mechanism: the block did not *start*
   failing on 2026-09-02 — it had failed validation since the day it was written, and every
   earlier client swallowed the failure at DEBUG level. 2.1.255 turned that into fail-closed,
   for exactly the reason its message gives. The repo never changed; the client's tolerance did.
   (The changelog carries no section for 2.1.255 at all — the change was unannounced.)

**The fix** (the PR that carries this section): the three blocks rewritten to the documented
nested shape, with the `python` prefix `settings.json` already uses on every hook. Verified
offline against the real 2.1.255 binary with a flat-shape control **refused in the same run**;
the three converted files loaded. **Do not reintroduce the flat form.**

### The uncomfortable corollary — the three write-deny guards never ran in-harness

Under 2.1.247 the block was discarded at load, so `goal-evaluator`, `plan-drafter` and
`status-scribe` ran **without** the PreToolUse deny hooks that ADR-0018 SD-1, PLAN-0009 H2 and
PLAN-0034 prong 2 describe as enforcing their write scopes. Measured for 2.1.247 (in use from
2026-08-30); for the May–August clients it is an inference from the shape never having matched
the documented schema — strong, but not measured. The hook *scripts* have unit tests; the
*wiring* was never witnessed RED — the largest instance yet of `CLAUDE.md` §8's rule that a
load-bearing green is not evidence until its assertion has been seen to redden. 2.1.255 refusing
the whole agent is the client doing what this repo's constitution says to do: fail closed
rather than run unguarded. Recording that in ADR-0018 / PLAN-0034 is a **separate Cowork
dispatch** (Cray, s271: lesson + STATUS first).

**Measured the same session, after the harness hot-reloaded the edited files** (it watches
`.claude/agents/` — a file edit refreshes the registry mid-conversation; a client restart does
not): all three spawned (3/3), **but the guard did not fire.** `goal-evaluator`, told to Write
`.claude/state/s271-deny-probe.txt`, got `File created successfully`. The hook *script* is not
the reason: run directly on Windows from the same UNC cwd with the same PreToolUse payload it
returned exit 0 and `"permissionDecision": "deny"` with the SD-1 reason. So the harness never
invoked the frontmatter hook. Not yet separated: (i) a hot-reload attaches the agent but not its
hooks; (ii) the documented frontmatter-hook trust gate ("stricter than settings hooks — trusting
a parent folder isn't enough") — with a concrete lead: `~/.claude.json` holds **two** trust
entries for this folder, the backslash-UNC spelling `true` and the forward-slash spelling
`false`; (iii) the Desktop/SDK harness not applying subagent frontmatter hooks at all. The Desktop session writes no hook debug log, so this needs a **new conversation**
with the fix merged: spawn `goal-evaluator`, repeat the probe, pre-committed read = **denied**.
If it still succeeds, (i) is dead and the guards must move to `settings.json` — a project-level
`PreToolUse` on `Write|Edit` whose script dispatches on the payload's `agent_type` field, which
the docs say carries the agent's `name`. Until then the guards are **unwitnessed**, and every
claim that they enforce stays a claim. _[Executed s272 — part 2 below: still inert from a fresh
load, so the guards moved.]_

### Resolution, part 2 (session 272) — the nested shape made the files LOAD, not the hooks RUN

Two probes in a **new conversation** on the merged fix (`main` = `5db546f`, client 2.1.255, cwd =
the backslash-UNC spelling whose trust entry is `true`), neither needing a forbidden write:

1. **Frontmatter hook: inert.** `pretooluse_goal_evaluator_write_deny.py` was instrumented
   (uncommitted) to append one JSON line on every invocation — at entry and at each decision,
   with a fallback path — and controlled first by two direct runs (allow → empty stdout + trace;
   deny → the SD-1 JSON + trace; `4 → 8` lines). Then a *legitimate* dispatch (an active `/goal`
   with one `judge` criterion, the gate's own template and fingerprint) made `goal-evaluator`
   write `goal.json`: `evaluations[]` **0 → 1**, trace **8 → 8**, no fallback file. The harness
   never ran the script. Hypothesis (i) is dead — this registry was built fresh from the valid
   files; (ii) vs (iii) is not separated and no longer needs to be.
2. **Settings hook: live, with identity, and no edit was needed to see it.** The existing
   `pretooluse_git_deny.py` prints `agent_type` and `agent_id` inside its deny reason, so a
   `git commit --dry-run` from `general-purpose` and from `claude` (haiku) was the instrument:
   both DENIED, `agent_id` **equal to the agentId the Agent tool returned** for that spawn and
   `agent_type` equal to the `subagent_type`; the same command from the main agent ran. Settings
   hooks fire for subagent tool calls, and the payload says who is calling.

Two instrument lessons, each paid for with a run: the "ask the agent for a forbidden write" probe
is **model-confounded** — on Opus, `goal-evaluator` refused to attempt it (no Write call → no hook
trigger → nothing learned) while s271's parent had complied — so the discriminator is the agent's
*allowed* write through a real dispatch plus an instrument on the hook; and **control the
instrument's input too** — the first control runs both returned the fail-closed "malformed JSON"
deny because a heredoc'd payload had lost one backslash layer in a UNC `cwd` (`\\u…` became a
broken escape). Forward slashes in probe payloads, and the control reads before the real one.

**The fix (this PR).** `.claude/hooks/pretooluse_subagent_write_dispatch.py`, registered in
`settings.json` on `PreToolUse` `Write|Edit` beside the research-path and governance gates. It
reads the payload's `agent_type`; for `goal-evaluator` / `plan-drafter` / `status-scribe` it hands
the raw payload to that agent's guard script in a subprocess and forwards the verdict verbatim —
the three scripts are **unchanged** and still frontmatter-wired (harmless; double coverage if a
client ever applies them). Fail-closed where identity is known (a missing, crashing or timed-out
guard → deny); pass-through where it is not (main agent, other subagents, malformed stdin — the
harness serialises the payload, so no agent reaches a bypass there). The registration is pinned
both ways in `tests/handoffs/test_settings_hook_wiring.py` (dispatcher present; guards never
registered directly — the boundary inversion their docstrings warn about), and the scenario test
executes the command `settings.json` actually names, from the repo root, with the s272-recorded
payload shape. The three guard docstrings still say "subagent scoping comes from the frontmatter
wiring" — historically true, now superseded by the dispatcher; left as-is so the scripts stay
byte-identical.

**Witnessed live (session 273, 2026-09-02, `main` = `0077163`)** — the first conversation started
after the merge, so its settings snapshot carried the dispatcher. Both reads were pre-committed
before the run. **Step A, no false deny:** a fresh `/goal` with one `judge` criterion, the gate's
own template and a Windows-side fingerprint (`afdaea536749062c`, unchanged across the write);
`goal-evaluator` on Opus read the two files, judged J1 PASS and *edited* `goal.json` —
`evaluations[]` **0 → 1**, its tool result "updated successfully", the main agent's own first
Write of the session also un-denied. **Step B, the deny:** `goal-evaluator` on Fable (the model
that attempts the probe; Opus refuses) asked to Write `.claude/state/s271-deny-probe.txt` — one
tool call, denied with `pretooluse_goal_evaluator_write_deny.py`'s own SD-1 reason forwarded
verbatim, and the file **absent** afterwards. So the guards were **inert from their birth
(s269 → #1362) until 2026-09-02, and live from #1363**; and the custom agent's `agent_type` is
its frontmatter `name`, since that is the key the dispatcher routed on. Evidence:
`.claude/handoffs/session-273/evidence/step{A,B}-*.txt` (gitignored).

## How to check cheaply — three instruments, and one false green

- **Live, decisive, one call:** spawn a *known-absent* agent name; the error lists the registry
  verbatim. Spawn a known-present one in the same batch as the positive control.
- **Offline, no API, names the reason:** the `--debug-file` run above, in a directory holding
  copies of the agent files, then grep `\[ERROR\] Agent '…' not loaded`. The Desktop app keeps
  the previous version beside the current one, so a before/after is one more run. Use a
  **scratch copy, not the repo** — a headless session still fires the repo's SessionStart hooks.
- **`claude plugin validate .claude/agents` is a FALSE GREEN for this defect.** It passed the
  flat-shape files. It checks YAML, `name` and `description`, not the hooks schema. Do not cite
  it as evidence that an agent file loads.
- **A registered agent is not a guarded agent.** Registration and hook attachment are separate
  facts. The forbidden-write probe is model-confounded (s272: Opus refuses to attempt it); the
  robust probe is an instrument on the hook script plus the agent's *allowed* write through a real
  dispatch — zero invocations beside a successful write is the reading. Then run the script
  directly with the same payload — if it denies, the harness skipped it.

Two instrument failures from s271, for the next reader: a transcript scan whose *own command
text* contains the needle matches itself (exclude the running session's file); and the system
prompt — the agent registry included — is **not** recorded in `.jsonl` transcripts, so grepping
them for registry state measures prose, not state. A `subagent_type` inside a `tool_use` record
is the recorded signal.

## The test procedure, in cost order (as written s270; every step executed s271 — see Resolution)

1. **Restart the Claude Code session.** The agent registry is built at session start, so a
   restart is both the cheapest diagnostic and the most likely fix. If the three return, it
   was session-scoped and the case closes.
2. If they are still missing after a restart, the cause is a **client change**, not a
   glitch — check whether the client updated around 2026-09-01/02.
3. Only if a client change is *confirmed* to have dropped support for something these three
   declare does editing the files become correct — and that edit then needs its own
   evidence, recorded here.

## While they were missing (s269 → the fix) — what still worked

- **`plan-drafter` absent** → a *new* PLAN or ADR cannot be drafted in-harness. Editing an
  **existing Draft** PLAN is not G2-gated and needs no drafter.
- **`status-scribe` absent** → Code writes the STATUS reconcile directly. Do not recreate
  the agent file.
- **`goal-evaluator` absent** → a `/goal` with `judge` criteria can never close; the Stop
  gate re-dispatches every turn into a hole. Declare goals with **`check` criteria only**
  until the evaluator is back, or expect the dispatch loop. Never self-judge a `judge`
  criterion: ADR-0018 D6 exists precisely so the evaluator disregards the author's own
  prose success-claims, and writing your own verdict makes the mechanism decorative.

## References

- `.claude/settings.json` `PreToolUse` `Write|Edit` → `pretooluse_subagent_write_dispatch.py`
  (s272) — the live wiring of the three guards; `tests/handoffs/test_settings_hook_wiring.py`
  pins it both ways.
- `CLAUDE.md` §4 (a do-not-act instruction must live on a tracked, scanned surface),
  §6 (an inherited premise a decision rests on is a claim, not context).
- `docs/adr/0018-axis-b-verification-loop.md` D6 — why the evaluator's independence is the
  whole mechanism.
- Session-269 handoff §7 recorded the disappearance and the "check before assuming"
  instruction that made this diagnosis happen at all.
- Claude Code docs — sub-agents ("Hooks in subagent frontmatter", "Subagent files Claude Code
  skips") and hooks ("Hooks in skills and agents"): the nested shape is the only one documented,
  and the documented skip-reason list does not include a hooks-schema failure.
