# Lesson #0029 — A named-subset "green" is not a full-suite green (verify the whole suite; make CI required)

**Date:** 2026-07-07 (session 106; the regression is from sessions 104–105)
**Class:** advisory (verification / CI hygiene)
**Trigger:** In session 105 (PR
[#600](https://github.com/CrayJThiemsert/vero-lite/pull/600)) `main` was found
**CI-red since #595**, merged red through #596–#598. The two failures lived in
`tests/api/test_runs_endpoints.py`. The session-104 closeout had reported *"52 db +
489 procedures green"* — a hand-picked subset that **excluded `tests/api/`**,
exactly where the regression was. It was compounded by CI being `pull_request`-only
and **not required** by branch protection, so a red PR could merge. (Fixed in
session 106: `main` branch protection now requires the `gate` check + enforce-admins
— it was previously *completely* unprotected.)

## The lesson — two intertwined threads

**1. A subset pass masks a regression in the tests it excludes.** Reporting "N
passed" from a chosen subset (`pytest tests/db tests/procedures`) *reads* as "the
suite is green" but only proves the subset is green. The RF-1 guard regression
(#595) broke `tests/api/` — outside the reported subset — so it looked green and
merged. **When you claim a suite pass, run the whole suite** (`pytest` at the root,
including `tests/api/`), or name the exact excluded scope so the gap is visible
instead of implied.

**2. CI that isn't required doesn't stop a red merge.** The workflow was
`pull_request`-only (no run on push to `main`) *and* not required by branch
protection → a PR could merge with a red or absent check, and there was no
main-push CI to catch it afterward. #595's regression stayed red across four
merges. **Prove "main is green" via a fresh PR's CI** — there is no main-push run to
read. The systemic fix (session 106): branch protection now requires `gate` green +
`enforce_admins` before merge. (`main` had *no* classic protection, *no* rulesets —
contradicting CLAUDE.md §7's "protected, no direct push" claim, which until now was
enforced only by convention + a soft hook.)

**The concrete bug that exposed it (RF-1 mechanism).** The RF-1 gate-resolve library
guard (`resolve_gated_step`, #595) checks the resolved **`Person` OBJECT**, not
`person_id`. A vertical that authors **no principals** (energy, so `person=None`)
409s an *authenticated* gate-resolve — the two happy-path tests in `tests/api/` hit
it. The fix provisioned a real authored `Person` test-side (monkeypatch
`auth._principal_index`) rather than adding a principals block to energy's
`procedures.yaml` (which would arm vertical-wide membership enforcement — the OQ-6
N≥2 boundary). *(This code-specific gotcha is also a private Tier-0 memory; the
durable, transferable lesson is the verification/CI discipline above.)*

## Why

- **"Verification is hygiene" needs the right blast radius.** CLAUDE.md §6 requires
  fresh evidence against a pass/fail read fixed before the run — and the evidence
  must cover the *actual* affected surface, not a convenient slice. A green result
  against a partial scope is the same failure mode as a green result against the
  wrong target ([[0026-interpret-before-run-pre-commit-outcome-meaning]]: "a green
  result against the wrong thing is worse than a red one").
- **Branch protection turns a convention into an invariant.** "All via PR, no red
  merges" as convention + a soft hook is bypassable — #595 proved it (four red
  merges). `enforce_admins` + a required check is not bypassable, and it makes the
  §7 "protected" claim *true at the platform*, not just aspirational.

## How to apply

- Report the **full** suite, or state the exact excluded scope. Never let a subset
  stand in for "the suite is green."
- To assert "main is green," open (or read) a **fresh PR's CI** — don't infer it
  from a main run that doesn't exist.
- Keep the `gate` check **required** in branch protection (done session 106). If
  main ever merges red again, first re-check protection is still on:
  `gh api repos/CrayJThiemsert/vero-lite/branches/main/protection`.
- For a personless-vertical gate-resolve 409: provision a real authored `Person`
  test-side (monkeypatch `_principal_index`); do **not** add a principals block to a
  production vertical that authors none by design (OQ-6).

Related: CLAUDE.md §6 (verification is hygiene) + §7 (all commits via PR);
[[0026-interpret-before-run-pre-commit-outcome-meaning]] (green-against-the-wrong-thing);
[[0028-omit-when-none-evolving-hash-chained-log]] (sibling from the same ADR-016 S2
arc). Private Tier-0 companions: `project_ci_pr_only_not_required_red_merges_to_main`,
`project_rf1_gate_resolve_requires_person_object`.

*AI-assisted (Claude Code, session 106); no `Co-Authored-By` per CLAUDE.md §7.*
