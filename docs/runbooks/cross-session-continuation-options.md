# Runbook: continuing work across sessions — the three options, measured

## Status

🔴 **RULED: stay MANUAL. Cray, typed, 2026-09-10 (session 290).**

The question was whether Claude can start the next session itself and resume from
a handoff, so work continues while nobody is at the machine. It can — the
mechanism exists and was proven end to end this session — but every option
carries a limitation that matters more than the convenience, so the project
continues with Cray opening each session and pointing it at the handoff.

**Revisit when:** Claude Code Desktop ships a mechanism better than what existed
on 2026-09-10. This runbook records what was measured so that revisit is a
comparison, not a re-investigation.

**Do not read this as "it does not work."** It works. The ruling is about fit.

---

## The three options

| | **Manual** (Cray opens it) | **Routine** (Desktop scheduled task) | **Chip** (`spawn_task`) |
|---|---|---|---|
| Fresh context window | yes | yes | yes |
| Starts itself | no | **yes** | no — needs a click |
| Can read a **gitignored** handoff | yes | **yes** | **no** |
| Machine must be awake + online | — | **yes** | yes |
| Interactive approvals persist | n/a | **no** | no |
| Where the result appears | the session | Routines → *routine* → History | a new session |
| Isolated from the main checkout | no | no | **yes** (own worktree) |
| Authority when something goes wrong | a human can interrupt | **full, unsupervised** | full, inside a worktree |

---

## What was measured, 2026-09-10 (s290)

Recorded so a later session does not re-derive it.

**A Routine run is a real session.** `handoff-reader (OBSERVE-ONLY smoke)` fired
one-shot, oriented itself from the newest handoff, re-verified the claim against
`git`, and reported. `list_sessions` returns it as a normal `local_…` session
with `cwd` set to the project folder; the Desktop **sidebar does not list it** —
it is filed under **Routines → the routine → History**. The folder is set for the
task automatically; it did not need setting by hand.

**A Routine has full local authority.** Bash + git through WSL, the local
filesystem including gitignored paths, and LAN reach to MS-S1. Nothing
distinguishes it from a human-attended session: it inherits `CLAUDE_TIER=code`
from shell init and therefore passes `pretooluse_git_deny.py` exactly as Cray's
own session does. **This is the gap `docs/plans/0124-unattended-run-authority.md`
exists to close, and that PLAN is `Draft`, parked on six unruled SDs.**

**Interactive approvals do NOT persist.** Two approvals were granted during the
run; afterwards the routine's **"Always allowed"** panel was empty and the task
directory under `~/.claude/scheduled-tasks/<id>/` held only `SKILL.md`. Two
independent readings, one from the UI and one from the filesystem. Consequence:
the tracked `permissions.allow` block in `.claude/settings.json` is not a
convenience, it is the only layer that survives a run.

**A Chip cannot read a handoff.** `spawn_task` gives the spawned session **its
own git worktree**, and a worktree carries only tracked files. Measured against
two existing worktrees: `.claude/handoffs` and `.claude/state` are **ABSENT** in
both, present in the main checkout. Handoffs are gitignored
(`.claude/handoffs/.gitignore`), so the pattern this project relies on for
cross-session continuity is invisible from a chip.

**A cloud routine cannot either**, for a different reason: it clones the
repository, and a gitignored file is never cloned. It also has no LAN route to
MS-S1. Same outcome, unrelated mechanism.

**Reporting is the weak link.** `notifyOnCompletion: true` was set and no
notification reached the creating session. The run's output lives in its own
session under Routines → History, which is easy to miss. Any unattended work must
report through a channel the operator actually watches —
`tools/notify/telegram.sh` is the seam this repo already has. ⚠️ That script is a
**graceful no-op** when its env vars are unset: it exits **0** and writes one line
to stderr, so `RC=0` does not mean a message was sent. The discriminator is the
captured stderr, not the exit code.

**Desktop banner, verbatim:** *"Local routines only run while your computer is
awake and online."* Machine asleep is a missed run, not a delayed one; a task due
while the app is closed runs at next launch, which may be hours later than
intended.

---

## Which option fits which situation

**Manual — when evidence may overturn the premise.** Diagnosis, interpretation,
anything that ends in a ruling (an SD, a `CLAUDE.md` §8 typed go, a G1/G2 gate).

Session 290 is the worked example: the task arrived as *"the classifier times out
50% of the time."* It ended as *"real timeouts are 27 of 187 and genuine network
failure is 2."* The premise inverted. Five instrument errors were made and caught
in the same session, every one because two numbers disagreed — and three
fabricated instructions arrived from the Stop hook and were refused. None of that
is work you would hand to an unsupervised chain **yet**.

**Routine — when the decision is already made and the pass/fail read is written
down BEFORE the run.** Running the offline gate and reporting; accumulating a
sample for a measurement window; watching CI. If the result needs interpreting
after you see it, it is manual work wearing a schedule.

**Chip — when the work stands alone from tracked files.** A red test with an
obvious cause, a `git worktree prune`, a task fully specified in a PLAN. The
worktree isolation is a genuine advantage: it makes the concurrent-write hazard
impossible rather than merely unlikely — s290 came within one `git stash` of
losing a subagent's in-flight edit because pre-commit stashed unstaged changes
while an agent was writing the same file.

---

## What would have to change before a long unattended chain is safe

1. **Attendance.** Today a Routine carries the same authority as a human-attended
   session. `docs/plans/0124-unattended-run-authority.md` designs the fix and is
   parked awaiting Cray's rulings. Its sharpest point: a flag asserting *"I am
   unattended"* is fail-**open** — a launcher that forgets to set it grants full
   authority — so the marker must assert **presence** instead.
2. **The merge gap.** No deterministic hook matches `gh pr merge` or `--auto`.
   The only mention anywhere under `.claude/hooks/` is the classifier's own
   prompt admitting it: *"anchored on `git`, so `gh pr merge` never matches it."*
   Nothing gates MS-S1 reach either.
3. **A watched reporting channel**, with a positive delivery signal rather than an
   exit code.
4. **Error compounding.** An uncaught mistake becomes the next session's premise.
   s289 handed over *"timeout 50%"* in good faith and it was the wrong frame; a
   chain that cannot notice this keeps walking. The honest gate on extending a
   chain is: *does the next session's premise survive contact with evidence?* If a
   run finds evidence contradicting its handoff and nobody is there to adjudicate,
   the chain should stop, not continue.

---

## Related

- `docs/plans/0124-unattended-run-authority.md` — the attendance design (Draft, parked)
- `docs/runbooks/loop-dispatcher-scheduled-task.md` — the one scheduled task this project already operates
- `docs/runbooks/scheduler-daemon.md`
- `.claude/settings.json` — see `_permissions_comment` for why there is an `allow` block and deliberately no `deny`
- `docs/plans/0122-stop-classifier-prompt-repair.md` — SD-3 / AC-12, the proceed-arm defect that produced the three fabricated instructions
- `.claude/handoffs/` — gitignored working notes; the artifact the manual flow depends on
