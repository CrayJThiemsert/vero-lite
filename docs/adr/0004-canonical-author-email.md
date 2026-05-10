# ADR-004: Canonical Author Email for Git Commits

**Status:** Accepted
**Date:** 2026-05-10
**Deciders:** Jirachai Thiemsert (founder)
**Related:** CLAUDE.md §7 (Git Conventions)

## Context

vero-lite is a public Apache 2.0 repository. Every commit's author email
is permanently visible in `git log`, GitHub UI, and any clone/fork/archive.
The choice of canonical author email affects:

1. **Privacy** — personal email exposed in public artifacts is irreversible
   (clones and archives preserve it even after history rewrite).
2. **Professionalism** — design partner outreach (vet clinics, month 3)
   may surface commit log inspection.
3. **Portability** — coupling identity to a specific platform (GitHub)
   limits future migration optionality.
4. **Reversibility** — decisions affecting permanent public artifacts
   should be deferred when uncertainty is high.

This decision was deferred across Sessions 6, 7, 8, and 9. Session 10
closes it with explicit hard deadline.

The current `pyproject.toml` and CLAUDE.md §7 already specify
`16893502+CrayJThiemsert@users.noreply.github.com` (GitHub noreply alias).
This ADR ratifies that choice with explicit rationale.

## Decision

Canonical author email for all vero-lite commits is the **GitHub noreply
alias**: `16893502+CrayJThiemsert@users.noreply.github.com`.

This applies to:
- Local `git config user.email` on all developer machines
- `pyproject.toml` author metadata
- Commits authored via Claude Code (in Desktop or CLI)
- Any future contributor onboarding documentation

### Rule for future contributors

When vero-lite accepts external contributors, each contributor uses
**their own GitHub noreply alias** (`<id>+<username>@users.noreply.github.com`)
rather than personal emails, unless a future ADR supersedes this policy.

## Consequences

### Positive

- **Privacy by default** — no personal email exposed in public commit log;
  no spam/scraping/phishing harvesting surface.
- **Reversible** — future migration to a project-scoped alias (e.g.,
  `@vero-lite.dev`) only affects new commits; historical noreply commits
  remain valid GitHub identities.
- **Industry-standard** — matches OSS norms (many maintainers use noreply).
- **Zero infrastructure** — no DNS, MX, or domain renewal overhead.
- **PII hygiene story** — aligns with PDPA-conscious posture for the Thai
  healthcare market positioning.
- **Bot-resistant pre-commit enforcement possible** — pattern
  `*+*@users.noreply.github.com` is enforceable via hook if needed.

### Negative

- **GitHub-coupled identity** — if vero-lite migrates to GitLab/Forgejo,
  the noreply email becomes a broken link (mitigation: alias forwarding
  via a future project domain if/when adopted).
- **Less direct contact channel** — email replies to commit notifications
  bounce; design partners must reach out via other channels (LinkedIn,
  website contact form, etc.).
- **Slightly less personal vibe** — for B2B outreach, a personal email or
  branded alias may signal "real human" more strongly.

### Neutral

- Decision is explicitly **provisional**: vero-lite has high uncertainty
  on rebrand, team scaling, and platform commitment. Re-evaluation is
  triggered when any of these resolve (see "Re-evaluation Triggers"
  below).

## Alternatives Considered

### Alternative 1: Personal Gmail (`cray.j.thiemsert@gmail.com`)

- **Pros:** Direct contact channel; portable across platforms;
  human-readable identity signal.
- **Cons:** Permanent PII exposure in public repo (irreversible — clones
  and archives preserve email after history rewrite); spam harvesting
  risk; mixing personal and work inbox; lock-in to personal email for
  email rotation.
- **Why rejected:** Permanent PII cost not justified by benefits when
  Option C (project-scoped alias) provides direct contact + portability
  without the privacy cost. Reserved as fallback if noreply causes
  operational friction.

### Alternative 2: Project-scoped alias (`jirachai@vero-lite.dev`)

- **Pros:** Clean work/personal separation; brandable; portable across
  platforms; revocable; PDPA-strong narrative; scalable to team.
- **Cons:** Requires domain registration and email forwarding setup
  (~$15/yr + 1hr); premature commitment to the `vero-lite` codename
  which may rebrand; bus factor on domain renewal.
- **Why rejected (for now):** vero-lite has multiple uncertainties still
  in flight — codename may change, product direction may pivot, team
  composition unknown. Committing to a project-scoped domain before
  these resolve adds rebrand cost without proportionate near-term
  benefit. Strong candidate for re-evaluation once design partner
  traction exists.

## Re-evaluation Triggers

This ADR is reviewed and potentially superseded if any of the following
occur:

1. **First design partner signs** — direct contact channel becomes
   higher value; brand identity matters more.
2. **Codename `vero-lite` becomes final product name** — premature-commitment
   risk for Option C disappears.
3. **Team scales beyond solo founder** — multi-contributor email policy
   needs explicit pattern.
4. **Platform migration considered** — GitHub-coupled noreply becomes
   migration friction.
5. **Spam/abuse on noreply** — operational pain point forces change.

## References

- ADR deferral history: `docs/STATUS.md` In-Flight Discussions (Sessions 6–9)
- GitHub noreply email documentation:
  https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address
- CLAUDE.md §7 — Git Conventions (already references this email)

## Implementation Notes

No code changes required. Current state already conforms:

- `pyproject.toml`: ✅ uses noreply alias
- CLAUDE.md §7: ✅ documents noreply alias
- Past commits: ✅ all use noreply alias

This ADR ratifies existing practice with explicit reasoning and
re-evaluation triggers.
