# `docs/strategy/` — Strategy documents (public)

**Status:** Active (Phase 1, Session 10 Batch 2+)
**Companion:** `docs/strategy/private/` (gitignored — see below)

## Purpose

Strategic narrative — market framing, design partner sequencing, competitive
positioning, phase planning — at the abstraction level appropriate for a
public repository.

This directory captures the **what** and **why** of vero-lite's strategy
without revealing **who** (specific companies, contacts) or **how much**
(deal structure, contract terms).

## Public vs private split (ADR-006 D2)

| Location | What lives here | Tracked? |
|----------|-----------------|----------|
| `docs/strategy/public/` (this dir) | Abstract framing, anonymized partner archetypes, phase planning, competitive analysis at industry level | ✅ Yes |
| `docs/strategy/private/` | Company-specific opportunity analysis, design partner names, executive contacts, deal structure, confidential benchmarks | ❌ Gitignored |

The directory-level split is intentional (per ADR-006 D2 Alternative 4):
foolproof — hard to commit `docs/strategy/private/foo.md` to a public
repository when the entire `private/` subtree is gitignored.

## Wording discipline (Session 10 Batch 2 standard)

Files committed under `public/` MUST use abstract language:

| Concrete (private only) | Abstract (public only) |
|-------------------------|------------------------|
| Specific company name | "regional energy operator" / "industrial supply chain operator" |
| Specific executive | "design partner contact" / "executive sponsor" |
| Deal size / terms | "enterprise-scale" / "Phase 1 design partner economics" |

If a sentence requires a concrete name to make sense → it belongs in
`private/`, not here.

## Self-check before committing files under public/

```bash
# Run against staged diff before each commit. The pattern is the union of
# concrete brand/company names you must keep out of public files; see
# private/ for the canonical list.
git diff --cached -- docs/strategy/public/ | grep -iE '<concrete-brand-1>|<concrete-brand-2>'
# Expected: zero hits
```

Use word-boundary `-iEw` if a brand name overlaps a common English word
(e.g. a brand whose name is also a generic word); review hits manually
since the word-boundary flag will still trigger on the generic English use.

## References

- ADR-005 — Strategic Pivot to Operational Control Tower
- ADR-006 — Vertical Plugin Architecture (D2 codifies this split)
- Session 10 Batch 2 kickoff handoff (gitignored handoff archive)
