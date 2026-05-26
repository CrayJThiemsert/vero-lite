# Lesson #10: Auto-mode classifier blocks direct push to `main` unconditionally

> **Status:** Codified 2026-05-26 (Session 11, PR #25 follow-up).
> **Source:** Direct classifier denial observed 2026-05-26 ~11:30 +07 in
> the post-PR-#24 STATUS update workflow. Three separate denial events:
> (1) `git push origin main` chained with `commit -F`; (2) the same push
> isolated to its own command after Cray's chat-level authorization;
> (3) even a downstream read-only `git status && git log` chained from
> the rejected push got swept up in the same denial decision.
> **Cross-references:** CLAUDE.md §7 (the rule this Lesson motivates);
> Lesson #9 (Auto-mode primitive behavior — sibling); ADR-009 D2
> (only-Code-commits boundary the Workflow rule reinforces); ADR-013 D2
> (`pretooluse_git_deny` is the *commit* gate; the classifier is the
> distinct *push* gate — they compose).

## 1. The finding

The Claude Code Auto-mode safety classifier **denies `git push origin main`
(and equivalents targeting the default branch) unconditionally**, even
when:

- `main` is the current branch and the local commit was clean
  (pre-commit hooks all passed)
- The user has just authorized the action in chat
- Recent project history (`docs(status):` direct-pushes `5768a62`,
  `04820be`) shows the same operation succeeded in prior sessions
- CLAUDE.md §7 lists `main` as "protected" without defining what counts
  as an exception

The classifier reads CLAUDE.md (it sees `main (protected)` as a literal
string in the constitution) and applies a default-deny rule for any
push to the default branch. **It does not see the chat conversation, the
git history pattern, or any in-process authorization.** Re-running the
denied command without a settings change produces the identical denial.

Observed denial messages:

> Permission for this action was denied by the Claude Code auto mode
> classifier. Reason: Direct push to main (default branch) bypasses PR
> review; user authorized updating STATUS but did not explicitly
> authorize pushing directly to main rather than via a feature branch
> + PR.

> Permission for this action was denied by the Claude Code auto mode
> classifier. Reason: Pushing directly to the protected default branch
> `main` bypasses PR review (CLAUDE.md §7 lists `main` as protected;
> ADR-009 D2 requires PR flow).

The second message confirms the classifier explicitly cites CLAUDE.md
§7 and (inferred) ADR-009 D2 as its decision authority.

## 2. Why it works this way (inferred)

The Auto-mode classifier is **session-isolated** — it sees the tool
call + its parameters + the project's CLAUDE.md, but not the live chat
history that authorized the action. This is by design: classifier-as-
guardrail must resist "but the user said it's OK in chat" prompt
injection. The trade-off is that chat-level authorization for
classifier-denied actions **does not propagate to the next attempt**.

For directly-protected operations (push to default branch, force push,
hooks-skip, secret-bearing files), the only durable paths are:

1. **Don't do the action** (use a PR flow instead) — the
   classifier-friendly default
2. **Add a permission rule** in `.claude/settings.local.json` that
   explicitly allowlists the command pattern (relaxes the guard)
3. **Run the action outside Claude Code** (manual terminal) — bypasses
   the classifier entirely; only the user's git creds matter

Of these, only (1) preserves the safety property.

## 3. Knock-on effect: chained commands rejected as a unit

When the denied push was chained as `commit -F … && push origin main`,
the **whole chain was rejected** — including the (independently safe)
`commit`. A separate Bash call to `git status && git log` immediately
after the denial was also denied (the classifier appeared to extend
its skepticism to nearby ops on the same branch).

**Operational consequence:** rework. The `commit -F` would have
succeeded on its own; running it inside a chain meant re-doing the
edit + re-running pre-commit. ~3 min of friction per occurrence in
this session.

## 4. Mitigations (codified in CLAUDE.md §7 amendment 2026-05-26)

**Primary mitigation — workflow rule (constitution-level, durable):**

> All commits to `main` land via feature / `chore/*` / `docs/*` branch
> + PR + merge — no exceptions. Even single-file `docs(status):`
> updates use a small `chore/*` PR.

This removes the entire "should I direct-push this one?" decision —
the answer is always no — and removes any case the classifier could
deny.

**Secondary mitigation — commit + push hygiene:**

> When the push target is a non-`main` branch, `git commit -F … && git
> push -u origin <branch>` chained is fine. When landing on `main` via
> PR, never chain commit with a push to `main` — always commit on a
> branch first, then PR-flow.

This protects against the chain-rejection footgun even when a
hypothetical settings exception is added in the future.

## 5. Rejected alternatives

- **Adding `Bash(git push origin main:*)` to `.claude/settings.local.json`.**
  Considered as "Option 2" in the Cray-Code discussion. Rejected: the
  permission rule is unscoped (no way to restrict to "only when the
  staged diff is `docs/STATUS.md`-only"), so it would relax the guard
  for *all* pushes to `main`, not just STATUS — a security trade-off
  for a small ergonomic win. Cray ratified rejection 2026-05-26.

- **Status quo + ask-per-occurrence.** Considered as "Option 3."
  Rejected: every `docs(status):` update would require an interactive
  authorization round-trip; ~2 min friction × N updates accumulates.
  Cray ratified rejection 2026-05-26.

## 6. Test of the prevention

The very PR that codifies this Lesson (CLAUDE.md §7 amendment + this
file) **must itself land via PR flow** — never direct-push. The act
of merging this Lesson is the first confirmation that the new rule
operates correctly.

## 7. Future cleanup hooks

If a future ADR or skill (e.g., `update-config`) chooses to add a
narrow classifier exception, this Lesson should be revisited and either
amended or marked superseded. The narrow exception would need to be
scoped (e.g., only allow direct-push when the staged diff matches a
glob like `docs/STATUS.md`-only) — which the current
`.claude/settings.json` permission grammar does not appear to support.
Treat any such future amendment as a constitution-level change (PR
required, this Lesson updated alongside).

---

*Codified by Code (Tier 2) under standard PR flow. AI assistance: drafted
by Claude Code (Opus 4.7) from in-session classifier denial events.
Never `Co-Authored-By` per CLAUDE.md §7.*
