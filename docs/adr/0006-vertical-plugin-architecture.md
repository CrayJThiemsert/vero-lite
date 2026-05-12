# ADR-006: Vertical Plugin Architecture

**Status:** Accepted
**Date:** 2026-05-11
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-005 (strategic pivot), CLAUDE.md §3

## Context

ADR-005 pivots Phase 1 to Operational Control Tower with at least 2 concrete
verticals planned (energy primary, industrial supply chain secondary) and
1 parked vertical (vet clinic, Phase 2). The architecture must support
adding verticals N+1 without rewriting core engine logic.

Three forces:
1. **Concrete-first principle** — don't design abstractions until 3+ concrete
   examples reveal real patterns (Rule of Three)
2. **No premature template** — first vertical (energy) should NOT shape itself
   to match a hypothetical template
3. **Adding vertical N must be cheap** — Phase 1 target is L1 Scaffolded
   (3-5 days to spin up a new vertical with skeleton + guide)

## Decision

### D1: Template directory structure

```
verticals/
├── _template/        ← skeleton (empty in Phase 1, populated in Phase 2)
├── energy/           ← first concrete vertical (Batch 3+)
├── supply_chain/     ← stub Phase 1; concrete in Batch 5+
└── vet_clinic/       ← parked stub (Phase 2 unparking)
```

### D2: Strategy doc public/private split

```
docs/strategy/
├── public/           ← abstract language, committed
└── private/          ← company-specific names, GITIGNORED
```

Rationale: company names + confidential business analysis stay out of public
repo while remaining accessible to Chat + Code tab via gitignored path.

### D3: Template maturity target Phase 1 = L1 Scaffolded

| Level | Description | Cost to spin up new vertical | Target phase |
|-------|-------------|------------------------------|--------------|
| L0 | Manual copy-modify | 2-4 weeks | Pre-template (now) |
| L1 | Skeleton + how-to guide | 3-5 days | **Phase 1 target** |
| L2 | CLI generator (`vero-lite new-vertical <name>`) | 1-2 days | Phase 2 |
| L3 | Web UI self-service | hours | Phase 3 (commercial) |

### D4: Rule of Three

`_template/` content is extracted from at least 3 working verticals (energy +
supply_chain + vet_clinic-unparked, OR energy + supply_chain + third TBD).
Until then, `_template/` is an empty placeholder. Premature template = wrong
template.

### 5 architectural patterns to lock in core

These are the patterns the engine itself owns (NOT in any single vertical):

1. **Ontology = single source of truth** — YAML files in `verticals/<name>/ontology/`
   drive code generation. No hardcoded entity types in core.
2. **Data Adapter = pluggable interface** — `class DataAdapter(Protocol)`
   defined in core; each vertical implements its own subclass.
3. **Action Framework = generic** — `RecommendedAction` is a generic envelope
   in core; vertical-specific action handlers register at runtime.
4. **Demo Data Generator = per-vertical** — each vertical owns its synthetic
   data generation; core defines the contract, not the content.
5. **Pitch Narrative = co-located** — `pitch_narrative.md` + `demo_queries.md`
   live INSIDE each vertical directory, not in a separate `docs/` tree.
   Co-location keeps sales materials adjacent to the technical reality.

## Consequences

### Positive

- **Adding vertical N is cheap** by Phase 1 end (L1 target)
- **Verticals can be parked/unparked** without engine changes (vet_clinic
  proves this in Batch 2)
- **Public vs private separation** prevents confidential leaks while
  preserving discoverability for non-public work
- **Co-located pitch materials** keep sales narrative honest — if the demo
  changes, the pitch must update next to it

### Negative

- **More directories upfront** than strictly needed for energy-only Phase 1.
  Acceptable cost for forward-flexibility.
- **Discipline required** to honor Rule of Three — temptation to "just sketch"
  `_template/` contents must be resisted until 3 verticals validate the pattern
- **Strategy doc split** introduces one more place developers must remember
  (mitigated by README in `docs/strategy/public/README.md`)

### Neutral

- Existing services structure (`services/api/`, etc.) is orthogonal — engine
  code stays in `services/`, vertical-specific instantiations stay in `verticals/`
- ADR-003 service port strategy continues to apply unchanged

## Alternatives Considered

### Alternative 1: Single `verticals/<name>/` with no `_template/`

- **Pros:** Simpler, fewer dirs
- **Cons:** Loses Rule of Three discipline; future template extraction has no
  obvious home; signals "we'll figure it out later" which usually means "never"
- **Why rejected:** The empty `_template/` is intentional signaling for future
  selves and contributors.

### Alternative 2: Verticals as separate repos / submodules

- **Pros:** Strong isolation; verticals can have independent release cadence
- **Cons:** Premature complexity for solo dev; cross-cutting changes (engine
  + vertical) become multi-repo PRs; harder to validate template extraction
- **Why rejected:** Monorepo while Phase 1; revisit at Phase 3+ if commercial
  customers want vertical-specific versioning.

### Alternative 3: Template-first (design `_template/` upfront, fit energy into it)

- **Pros:** Faster path to "look, it's a template platform"
- **Cons:** Violates Rule of Three; locks in wrong abstractions; energy vertical
  shaped by hypothetical template instead of real partner needs
- **Why rejected:** Rule of Three is non-negotiable. Concrete-first or nothing.

### Alternative 4: Mixed public/private in same docs/ subtree with frontmatter flag

- **Pros:** Single tree
- **Cons:** Easy to accidentally commit private content with wrong flag;
  gitignore-by-frontmatter requires custom tooling; reviewers can't tell
  public vs private from path
- **Why rejected:** Directory-level split is foolproof. Hard to commit
  `docs/strategy/private/foo.md` to a public-only tree.

## References

- ADR-005 (strategic pivot — drives vertical strategy)
- ADR-007 (OCT architecture — Batch 3, will define core engine contracts)
- ADR-008 (YAML ontology spec — Batch 3, will define D1 contents)
- Session 10 Chat handoff: `.claude/handoffs/session-10/2026-05-11-0325-chat-conversation-handoff.md` (D1-D4 acceptance)

## Implementation Notes

Batch 2 commits #2-#3 create the directory scaffolds. ADR-007/008 (Batch 3)
fill in the engine-facing details. PLAN-003 (Batch 4) translates this into
executable steps for ontology engine implementation.
