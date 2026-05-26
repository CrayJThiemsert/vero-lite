# Lesson #9: Anthropic Claude Code "Auto mode" is model-tier-gated (Sonnet+ required)

> **Status:** Codified 2026-05-25 (Phase 3.5 smoke test setup).
> **Source:** Direct UI observation 2026-05-25 ~16:30 +07 during
> `phase35-smoke-code-reader` Local routine setup; reproduced in screenshot
> evidence. Captured as F7 in
> `docs/research/private/phase3.5-smoke/findings.md` and promoted to a
> Lesson per the file's roll-up checklist (general Anthropic Claude Code
> primitive behavior, not vero-lite-specific).
> **Cross-references:** Lesson #3 (Code-tab worktree lifecycle traps —
> sibling Claude-Desktop-on-WSL operational lesson); Lesson #8 (Cowork
> K-1/K-2 — sibling Anthropic-primitive-constraint lesson); PLAN-0008
> AC-1 Run 2 evidence (Auto mode + classifier composition observed live
> 2026-05-25 — `docs/plans/done/0008-harness-autonomy-layer-phase-2.md`);
> ADR-013 (the autonomy axis relocation that motivates sustained
> scheduled autonomy + Phase 3.5 smoke setup).

## 1. The finding

The **Permission mode** dropdown in Claude Code (Desktop UI, both
interactive sessions and Local routines) shows up to **5 options**, but
the visibility of **"Auto mode"** depends on the **selected model**.

Observed options (2026-05-25):

| Mode | Description | Always available? |
|------|-------------|-------------------|
| Ask permissions | Claude pauses so you can approve each action | ✅ |
| Accept edits | Pre-approve Write/Edit; prompt for everything else | ✅ |
| Plan mode | Read-only research mode, no tool use; presents a plan | ✅ |
| Bypass permissions | Skip every prompt; classifier disabled | ✅ |
| **Auto mode** | Full per-tool auto-approval **gated by Anthropic safety classifier** | ❌ **Sonnet-tier or higher required** |

When **Haiku 4.5** is the selected model, "Auto mode" is rendered greyed
out with the explanatory label **"Not available for the selected model"**.
Switching to **Sonnet 4.6** (or higher tier) makes "Auto mode" selectable
immediately, without other config changes.

The behavior is **not documented in any Anthropic page surveyed** during
the PLAN-0009 Step 1a research spike (2026-05-25 — see
`docs/research/private/2026-05-25-subagent-primitive-survey.md` and the 4
docs cross-checked for the PLAN-0009 Step 1 split: Cowork Scheduled,
Live Artifacts, CC Routines, Desktop scheduled tasks).

## 2. Why it works this way (inferred)

Auto mode delegates per-tool approval decisions to **Anthropic's safety
classifier** — a separate model that judges each tool call for risk
before the harness lets it dispatch. AC-1 Run 2 (PLAN-0008 closeout
evidence, 2026-05-25 ~03:00 +07) confirmed this composition operates
correctly: Auto mode + classifier + vero-lite's Stop-continuation hook
all interleaved without per-tool prompts.

Classifier composition apparently requires a **base model with sufficient
reasoning capacity** to be itself classifier-gated. Haiku-tier models —
optimized for cost + throughput — do not satisfy the threshold. Sonnet
4.6 (and Opus) do.

(Anthropic has not published the threshold. The above is inference from
observed UI behavior; treat as "best current understanding" not
authoritative.)

## 3. Implication for sustained autonomous operation

Any Claude Code workflow that needs to run **without human approval
prompts** — and therefore needs the safety classifier to be in the loop
to keep mutation safe — must use a **Sonnet-tier (or higher) model**.

Concrete cases:

| Workflow | Mode needed | Model floor |
|---|---|---|
| Local routine (scheduled task) running unattended | Auto | Sonnet 4.6+ |
| Interactive session, multi-step refactor without per-tool clicks | Auto | Sonnet 4.6+ |
| Phase 3.5 (two-poller scheduled-task autonomy loop, if GO) | Auto | Sonnet 4.6+ |
| Subagent spawned with `permissionMode: auto` and `model: <X>` | Auto | Sonnet 4.6+ for `<X>` |
| Quick heartbeat / observation task (Cray approves once) | Accept edits | Haiku 4.5 OK |
| Code review / Q&A pause-on-every-step | Ask permissions | Any model |

**Cost trade-off (current Anthropic public pricing as of 2026-05-25):**

- Haiku 4.5: roughly $0.25 / $1.25 per M input / output tokens
- Sonnet 4.6: roughly $3 / $15 per M input / output tokens
- → Sonnet is ~10–12× cost of Haiku per token

For **heartbeat-class** scheduled workloads (~1k tokens/run × 24 runs/
day ≈ $0.10/day on Sonnet) the cost is negligible.

For **batch refactor or codebase-wide analysis** (~100k tokens/run) the
cost matters and Cray should explicitly choose the trade-off.

## 4. Mitigation patterns

### Pattern A — Pre-approve specific tools via "Always allow" (Haiku-compatible)

If Cray supervises the first run, the Desktop UI exposes "Always allow
this tool" buttons on each permission prompt. After approving each tool
once, subsequent runs of the same task with Haiku + Accept edits will not
prompt. The approval is tool-scoped (e.g., "always allow Bash") not
command-scoped, so this is **less safe than classifier-gated Auto** — a
prompt-injection or model misbehavior can use the pre-approved tool
freely.

Use for: low-stakes observation workloads where Cray has read the prompt
carefully + the worst tool outcome is bounded.

### Pattern B — Sonnet + Auto (recommended for any sustained autonomy)

Switch the model to Sonnet 4.6 (or higher) and Permission mode to Auto.
Classifier-gated. Standard recommended path for Phase 3.5-class
workloads.

### Pattern C — Bypass permissions (last resort — DO NOT USE for vero-lite)

Available on all models, but disables the classifier entirely. Equivalent
to running a model with unrestricted shell + git + file access on Cray's
machine. **Forbidden** in vero-lite-context per CLAUDE.md §8 (Public
Repository + Code Quality) — defeats every safety lever the autonomy
layer installs.

If you find yourself reaching for this, stop. Switch to Pattern B.

## 5. Phase 3.5 smoke test prescription (concrete)

For the Phase 3.5 smoke test set up 2026-05-25:

- **`phase35-smoke-cowork-heartbeat`** (Cowork Scheduled task) — Haiku
  4.5 is fine. Cowork's "Act without asking" mode is Cowork's own
  permission abstraction (separate from Code Permission mode) and Cowork
  agents on Haiku-tier are not gated by the Sonnet-classifier rule (this
  Lesson is specifically about Claude Code's Permission mode dropdown
  in interactive sessions and Local routines).

- **`phase35-smoke-code-reader`** (Code Desktop Local routine) — must
  use Sonnet 4.6 + Auto mode for sustained 24-48h observation. Cost
  budget ~$0.07–$0.10 per day for heartbeat-class observations.
  Acceptable.

## 6. Detection in the wild

If a future Claude Code session reports "I can't see Auto mode" or
"the Mode dropdown only shows 4 options":

1. Confirm the model selector in the Desktop UI (bottom-right of chat
   input, or in routine/scheduled-task config).
2. If Haiku-tier → switch to Sonnet 4.6 to confirm this Lesson's pattern.
3. If still missing after model switch → that's a different bug; file
   an Anthropic ticket.

## 7. Open questions

- **OQ-9.1 — Threshold definition.** Where exactly is the boundary?
  Sonnet 3.5 family vs Sonnet 4.x family? Haiku 4.5 vs Haiku 3.5? Not
  enough evidence as of 2026-05-25 — only Haiku 4.5 (off) and Sonnet 4.6
  (on) verified.
- **OQ-9.2 — Cowork parallel. ✅ RESOLVED 2026-05-26 — NO Sonnet floor
  on Cowork.** Live confirmation via Cowork scheduled-task editor:
  toggling **Model** between Haiku 4.5 ↔ Sonnet 4.6 leaves
  **"Act without asking"** mode available on both. Combined with the
  same-day end-to-end producer→consumer→archive proof on a
  `phase35-smoke-cowork-heartbeat` task running Haiku 4.5 + Act-without-
  asking + Hourly, this confirms Cowork's "Act without asking" is its
  own permission abstraction (tool-list-scoped — Connectors panel +
  per-conversation toggle), NOT a classifier-gated analog of Code Auto
  mode. PLAN-0010 §Step 2 Haiku 4.5 spec validated.
- **OQ-9.3 — Subagent inheritance.** A subagent spawned with
  `permissionMode: auto` inherits the parent's model unless `model:` is
  set in the agent file. If the parent is Sonnet and the subagent
  `model: Haiku`, does Auto silently downgrade to Accept edits, or does
  the agent fail to load? Worth verifying during Phase 3 Step 1b contract
  design.

---

*If this Lesson's gating reproduces in another Anthropic surface (Code
Routines cloud, Cowork mode, Mobile, etc.), expand §1 + §3 with the new
case rather than creating a sibling Lesson.*
