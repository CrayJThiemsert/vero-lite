# `_template/` — Vertical scaffolding placeholder

**Status:** Empty placeholder (Phase 1, Session 10 Batch 2)
**Maturity target Phase 1:** L1 — Scaffolded (skeleton + how-to guide)
**Current contents:** None — see Rule of Three below.

## Purpose

When vero-lite supports 3+ verticals, this directory will hold the canonical
skeleton that new verticals copy from. Until then, it remains empty by design.

## Rule of Three (ADR-006)

Template content extracted from REAL patterns observed across at least
3 verticals — not designed upfront. First concrete vertical: `energy/`.
Premature abstraction here would lock in wrong assumptions.

## Expected structure (future, not Phase 1)

```
_template/
├── ontology/         ← YAML files
├── data_adapter/     ← Python module per data source
├── demo_data/        ← synthetic data generator
├── pitch_narrative.md
├── demo_queries.md
└── README.md
```

## Status timeline

- Phase 1 (now): Empty placeholder
- Phase 1 end: Skeleton + how-to guide (after `energy/` works)
- Phase 2: CLI generator (`vero-lite new-vertical <name>`) — see ADR-006
