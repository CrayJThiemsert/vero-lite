# Lesson #8: Cowork-Tier-1 K-1/K-2 operating workflow (template-reusable)

> **Status:** Codified 2026-05-21 (this batch, with ADR-009 ratification).
> **Source:** ADR-009 §Context, D3, T6; round-1 dispatch
> `.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md`
> §11 (Cowork's R3 self-check under K-1); round-2 dispatch
> `.claude/handoffs/session-10/2026-05-21-1100-cowork-adr0009-second-trial-dispatch.md`
> §2 (R3 mental validation against `_schema.py`); blocker investigation
> `.claude/handoffs/session-10/2026-05-20-1545-code-cowork-blocker-investigation.md`
> (§0 architectural facts, §2 four paths weighed, §3 `.claude/agents/handoffs/`
> negative test).
> **Cross-references:** ADR-009 (the topology-change ADR this Lesson
> documents the operational layer for); Lesson #3 (Code-tab worktree
> lifecycle traps — sibling Claude-Desktop-on-WSL operational lesson);
> Lesson #5 §3 schema-fidelity sub-rule (the durable layer the
> mental-validation substitute honors); Lesson #6 (surface→re-dispatch
> pattern — when Code's post-receive R2 check fails, the cycle this
> workflow's verification step substitutes for).

## 1. The constraints

Two documented Anthropic-side architectural gaps affect Cowork in
**Claude Desktop on Windows with WSL-mounted projects**. Both gaps
are tracked at `anthropics/claude-code` with no shipped fix as of
2026-05-21:

### K-1 — Cowork sandbox bash UNC refusal

Cowork's `mcp__workspace__bash` tool returns
`UNC paths are not supported: \\wsl.localhost\<distro>\<path>` on every
invocation when the project Context folder is a WSL UNC path. The Cowork
sandbox is a **remote cloud Linux VM**, not a local WSL container. The
sandbox receives the project's UNC path string as `cwd` and the Linux
shell rejects it — no command runs.

Other Cowork tools (`Read`, `Glob`, `Grep`, `Write`) work fine because
they are **proxied through the Windows desktop client** which resolves
UNC locally and ships file content to the sandbox.

**Consequence:** Cowork cannot execute shell commands inside the project
checkout — including the project's own `validate_handoff.py` for dog-food
self-validation of its own authored handoffs.

**Tickets:** [#45297](https://github.com/anthropics/claude-code/issues/45297) (open),
[#49933](https://github.com/anthropics/claude-code/issues/49933) (WSL Remote integration FR),
[#56145](https://github.com/anthropics/claude-code/issues/56145) (cloud sandbox provisioning),
[#54069](https://github.com/anthropics/claude-code/issues/54069) (closed duplicate, three-layer analysis).
No Anthropic ETA.

### K-2 — Cowork sandbox `.claude/` write block

Cowork's `Write` tool refuses any path under the project's `.claude/`
subtree with:

```
Write on <path> is blocked in this session — it resolves to a
protected location or a path outside the connected folder. Work on
a copy under the session outputs folder if you need to modify it.
```

The Claude Code CLI documents an exempt-subdir allowlist
(`.claude/commands`, `.claude/agents`, `.claude/skills`,
`.claude/worktrees` per [code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions)),
but the **Cowork sandbox does not honor this allowlist** — `.claude/agents/handoffs/`
was tested negative (blocker investigation §3). Claude Code CLI has
`--dangerously-skip-permissions` as a bypass; Cowork has none.

**Consequence:** Cowork cannot write directly to the canonical
`.claude/handoffs/session-NN/` path that this project (and many Claude
Code projects) use for inter-tier handoff files.

**Documentation:** [code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions),
v2.1.78+ release notes ("`.claude` is protected as a directory, except
for…"). [#57177](https://github.com/anthropics/claude-code/issues/57177) confirms Cowork
workspace paths are hardcoded in the app bundle. No user-side toggle.

## 2. The workflow (ADR-009 D3)

Per Cowork-Tier-1 trial (ADR-009 §Context, round 1 + round 2), the
following workflow substitutes Code's post-receive verification for
Cowork's blocked self-validation. This is the **steady-state operating
contract**, not a temporary scaffold.

```
1. Cray dispatches the task to Cowork via "+ New task" in Cowork tab
   (autonomous task prompt; meta-instruction includes reading list +
   permission boundary + scope override if needed).

2. Cowork reads the repo via Read/Glob/Grep (proxied; UNC-safe) and
   authors the artifact:

   • Handoff (kickoff dispatch, consultation, dispatch report, completion
     report, etc.): write to Cowork's outputs scratchpad with the
     canonical filename (e.g., 2026-05-21-1100-cowork-<topic>.md).
     K-2 blocks the canonical .claude/handoffs/ path; the outputs path
     is Cowork's workaround.

   • ADR / PLAN draft: write directly to docs/adr/NNNN-*.md or
     docs/plans/NNNN-*.md. K-2 does not apply outside .claude/.

3. Cowork performs MENTAL VALIDATION (K-1 blocks live validator):

   • Handoff frontmatter: cross-check field-by-field against the source
     of truth (this project: tools/handoffs/_schema.py REQUIRED_FIELDS,
     Phase enum, Actor enum, Status enum, _FILENAME_RE).
   • ADR / PLAN structure: cross-check vs docs/adr/0000-template.md or
     docs/plans/0000-template.md plus most-recent accepted examples.
   • EXPLICITLY FLAG the validator-gap in the completion report. Do
     not claim live-validator pass when only mental validation occurred.
     Trust-but-verify discipline.

4. Cowork reports artifact path(s) to Cray in chat reply
   (filename forward, not file content).

5. Cray pastes the path to Code in a separate Code session.

6. Code's receive workflow:

   a. For scratchpad artifacts: cp from Cowork outputs to canonical
      .claude/handoffs/session-NN/ path. chmod 644 to fix exec-bit
      artifact from /mnt/c filesystem copy.

   b. Run validate_handoff.py via in-process main() per Lesson #7
      §3.2 (NOT echo $?):
        PYTHONPATH=. .venv/bin/python -c \
          "from tools.handoffs.validate_handoff import main; \
           ret = main(['<path>']); print(f'RET={ret}')" \
          2> /tmp/v.stderr; cat /tmp/v.stderr
      Expected: stderr "OK: 1 file(s) valid"; stdout "RET=0".

   c. Apply R2 required-veto criteria (parent discussion
      2026-05-20-1235 §3.3):
        • Validator pass on dispatch frontmatter
        • Every Lesson #N citation resolves to docs/lessons/000N-*.md
        • Every file path cited resolves at HEAD
        • Every dep cited is in pyproject.toml OR installed in .venv
        • Every enum value (phase, suffix, status, actor) is canonical

   d. If all PASS: Code executes the dispatch / commits the draft.
   e. If any FAIL: Code surfaces midflight (Lesson #6 firing); Cowork
      re-dispatches with corrections.
```

## 3. When this lesson applies

**Applies if all of:**

- Project runs in **Claude Desktop on Windows** (not claude.ai web, not
  Linux desktop, not macOS desktop — those have different sandbox
  topology and may not exhibit K-1/K-2)
- Project repo lives on **WSL filesystem** accessed via UNC mount
  (`\\wsl.localhost\<distro>\...`) rather than a Windows-native NTFS path
- Project uses Cowork in a Tier-1 capacity (authors dispatches / ADRs /
  PLANs that need formal handoff to a Code tab or to commits)
- Project uses `.claude/handoffs/` (or any `.claude/`-rooted convention)
  for inter-tab handoff files

**Does NOT apply if:**

- Project runs entirely in Claude Code CLI (no Cowork tab) — CLI uses
  local sandboxing not subject to K-1
- Project Context folder is Windows-native (`C:\Users\…\…`) — K-1 may
  not trigger on Windows-drive paths (per blocker investigation §1.1
  hypothesis; ranked HIGH-likelihood-fix but untested in this project)
- Project does not use `.claude/`-rooted handoff paths — K-2 only blocks
  that subtree

The **vero-lite project** matches all four "applies" criteria, hence
this Lesson is binding here.

## 4. First validated uses

### 4.1 Round-1 trial — PLAN-003 Phase 1 kickoff dispatch (2026-05-20)

Cowork authored
`.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md`
under K-1 + K-2:

- Wrote to outputs scratchpad (K-2 workaround); Code copied to canonical
  on receive
- Performed mental validation against `_schema.py` in §11 of the
  dispatch; explicitly flagged K-1-blocked validator gap in §11.5
- Code's post-receive R2 check passed (pre-exec status
  `2026-05-20-1510-code-cowork-tier1-trial-preexec-status.md` §2): C1=0
- Phase 1 execution single-pass close (engine closeout
  `2026-05-20-1840-code-plan003-phase1-engine-closeout.md`): C4=0,
  7 commits, 58 tests, coverage 94.06%

**Trial scorecard under refined criteria (ADR-009 D4):** C1=0 / C2=0 /
C3=0 (K-1+K-2 = known constraints, not failures) / C4=0 → PASS.

### 4.2 Round-2 trial — ADR-009 itself (2026-05-21)

Cowork drafted `docs/adr/0009-cowork-tier1-tier-topology.md` (uncommitted
draft; Code commits per D2) + completion handoff
`2026-05-21-1100-cowork-adr0009-second-trial-dispatch.md`:

- ADR written directly to `docs/adr/` (K-2 does not apply outside
  `.claude/`)
- Completion handoff written to outputs scratchpad (K-2 workaround)
- Mental validation against `_schema.py` in §2 of the handoff; K-1
  flagged
- Code's post-receive R2 check passed (this batch): C1-analog = 0,
  C4-analog = 0 (no mid-review re-dispatch needed)

**Trial scorecard:** PASS — supports hypothesis across both
capability classes (concrete dispatch authoring + abstract ADR
synthesis).

## 5. Anti-patterns (do NOT do this)

- **Silent skip of dog-food.** Cowork ships a handoff/ADR without
  mental-validating the frontmatter against `_schema.py` AND without
  flagging the missing live-validator run. Result: Code's post-receive
  R2 check catches schema fails (Lesson #6 firing) that mental
  validation would have prevented pre-send. Trust-but-verify is the
  discipline; explicit gap-flagging is how it operates under K-1.
- **Fabricated validation report.** Cowork claims "validator passed" or
  "frontmatter OK per validate_handoff.py" when K-1 blocked the actual
  run. This is the same class as Lesson #5 §3 schema-fidelity failure
  #5 ("inferred-text-as-content") — fabricating verified state.
- **Writing to canonical `.claude/` path expecting it to work.** Cowork
  attempts `Write` to `.claude/handoffs/session-NN/cowork-*.md` and
  silently fails or retries; should immediately recognize K-2 + redirect
  to outputs scratchpad per §2 step 2.
- **Skipping the filename convention in outputs scratchpad.** Cowork
  uses an ad-hoc filename in scratchpad ("draft.md", "output.md") rather
  than the canonical pattern. Code's `cp` then has to rename; loses the
  natural-sort chronological view of `.claude/handoffs/session-NN/`.
- **Code skipping post-receive validator.** Code assumes Cowork's
  mental validation is sufficient and commits without running
  `validate_handoff.py` in-process. K-1 means Cowork's mental check is
  best-effort; Code's live-validator run is the authoritative gate.
  Cf. ADR-009 D3 step 6b.
- **Counting K-1/K-2 as Cowork-discipline failures in trial-criteria
  evaluation.** They are documented Anthropic-side gaps, not discipline
  issues. Per ADR-009 D4 amended C3, they don't count toward new
  failure modes. Counting them mis-routes the diagnostic.

## 6. Why this is a Lesson (Cray's rationale, 2026-05-21)

Cray ratified Lesson #8 promotion (vs leaving the workflow only in
ADR-009 §16 / `docs/conventions/cowork_tab_instructions.md`) on the
rationale that **vero-lite may become a template for future projects
using Claude Desktop + WSL + Cowork**. The K-1/K-2 constraints are
Anthropic-side architectural facts that affect ANY such project, not
unique to vero-lite. Codifying the workflow as a Lesson preserves it
durably so:

- Future projects forked from vero-lite inherit the operating contract
  without re-deriving it from incident pain
- Future ADRs / convention amendments in vero-lite itself can reference
  this Lesson by number rather than re-quoting the workflow
- The Lesson outlasts the trial protocol (a session-scoped handoff)
  and the ADR-009 §Context (which assumes prior reading)

## 7. Migration path if Anthropic ships fixes

When (if) Anthropic fixes K-1, K-2, or both:

- **K-1 fix shipped** (e.g., WSL Remote integration #49933 lands):
  Cowork can run `validate_handoff.py` directly. §2 step 3 mental
  validation becomes optional / belt-and-suspenders. Code's post-receive
  validator becomes a second-line check rather than the primary gate.
  Lesson stays accurate (the workflow is still valid, just less
  necessary).

- **K-2 fix shipped** (e.g., `.claude/` allowlist expansion or
  per-project bypass): Cowork can write directly to canonical
  `.claude/handoffs/session-NN/` path. §2 step 2 scratchpad workaround
  becomes unnecessary; §2 step 6a (Code `cp` from scratchpad) becomes
  unnecessary. C2 measurement becomes trivially 0 with no refinement
  needed. Update ADR-009 D4 retrospectively if applied.

- **Both fixes shipped:** Trigger ADR-009 D6 reversibility evaluation
  — the K-1/K-2 workarounds were a non-trivial cost of Cowork-as-Tier-1;
  with them removed, the Cowork-vs-Chat-for-Tier-1 cost-benefit may
  shift. May or may not result in topology revert; depends on what
  other evidence has accumulated.

**Until any fix ships**, the §2 workflow is canonical.

## 8. References

- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) §Context
  (K-1/K-2 facts), D1 (tier topology), D2 (commit boundary), D3
  (K-1/K-2 workflow — this Lesson's §2), D4 (C2/C3 criterion refinement),
  T6 (this Lesson's promotion mandate)
- **Trial protocol** (`.claude/handoffs/session-10/2026-05-20-1345-code-cowork-tier1-trial-protocol.md`)
  §16 (documented constraints), §16.3 (combined workflow — the source
  of §2 verbatim shape)
- **Parent discussion** (`.claude/handoffs/session-10/2026-05-20-1235-code-tier-collaboration-asymmetry-discussion.md`)
  §3.3 R2 required-veto criteria (the verification backbone of §2 step 6c)
- **Blocker investigation** (`.claude/handoffs/session-10/2026-05-20-1545-code-cowork-blocker-investigation.md`)
  §0 (Anthropic-side facts), §1 (architectural diagnosis), §2 (4 paths
  weighed; Path D ratified)
- **Round-1 dispatch** (`.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md`)
  §11 (Cowork's first R3 self-check under K-1; the pattern §3 codifies)
- **Round-1 closeout** (`.claude/handoffs/session-10/2026-05-20-1840-code-plan003-phase1-engine-closeout.md`)
  §7 trial scorecard
- **Round-2 dispatch** (`.claude/handoffs/session-10/2026-05-21-1100-cowork-adr0009-second-trial-dispatch.md`)
  §2 R3 mental validation field-by-field
- **Sibling lessons:**
  - Lesson #3 (`docs/lessons/0003-code-tab-worktree-lifecycle-traps.md`)
    — sibling Claude-Desktop-on-WSL operational lesson, Code-side
  - Lesson #5 §3 (`docs/lessons/0005-tier-system-audit-2026-05-15.md`)
    — schema-fidelity discipline (the durable layer mental-validation
    honors)
  - Lesson #6 (`docs/lessons/0006-code-surface-chat-redispatch-pattern.md`)
    — the surface→re-dispatch pattern that fires if §2 step 6e triggers
  - Lesson #7 (`docs/lessons/0007-harness-exit-code-artifact.md`) §3
    — the reliable-verification method catalog §2 step 6b uses
- **Anthropic tickets cited in §1:**
  - [#45297 Cowork UNC bug](https://github.com/anthropics/claude-code/issues/45297)
  - [#49933 WSL Remote integration FR](https://github.com/anthropics/claude-code/issues/49933)
  - [#54069 three-layer UNC analysis](https://github.com/anthropics/claude-code/issues/54069)
  - [#56145 cloud sandbox provisioning](https://github.com/anthropics/claude-code/issues/56145)
  - [#57177 Cowork workspace paths hardcoded](https://github.com/anthropics/claude-code/issues/57177)
- **Anthropic docs cited in §1:**
  [code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions)
  (`.claude/` exempt-subdir allowlist for Claude Code CLI; not honored
  in Cowork)
