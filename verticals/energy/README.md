# `energy/` — Energy operator vertical (Phase 1, primary)

**Status:** Stub (Phase 1, Session 10 Batch 2 — directory created, no content yet)
**Design partner type:** Regional distributed energy operator (Energy-as-a-Service, batteries, grid)
**Next milestone:** Batch 3 — Energy ontology v0 draft (5 entities per ADR-006)

## Purpose

First concrete OCT vertical. Drives the canonical patterns the `_template/`
will eventually extract.

## Expected contents (Batch 3+)

- `ontology/` — Asset, Site, OperationalEvent, Alert, RecommendedAction
- `data_adapter/` — synthetic generator first; real adapter once design partner agrees
- `demo_data/` — NYISO/CAISO-style time-series simulation
- `pitch_narrative.md` — vertical-specific story
- `demo_queries.md` — 5-10 NL queries this vertical answers

## References

- ADR-005 (strategic pivot to OCT)
- ADR-006 (vertical plugin architecture)
- ADR-007 (OCT architecture detail) — Batch 3
- ADR-008 (YAML ontology spec) — Batch 3
