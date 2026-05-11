# `vet_clinic/` — Veterinary clinic vertical (PARKED — Phase 2)

**Status:** Parked (Phase 2 — Phase 1 pivoted to Operational Control Tower)
**Park decision:** Session 10, ADR-005
**Not deleted, just deferred:** Architectural decisions in ADRs 001-003
remain valid; ontology engine MUST support this vertical eventually.

## Why parked

Two enterprise opportunities surfaced mid-Session-10 with stronger pull:
existing executive relationships, larger contract size, cross-industry
template validation. See ADR-005 for full reasoning.

## When unparked

After Phase 1 OCT lands at least one paying design partner, AND template
maturity reaches L1 (`_template/` populated). Estimated: Phase 2 (month 7+).

## Architectural inheritance

All Phase 1 decisions apply — vet clinic vertical will instantiate the
same ontology engine + 3 OCT features, with `vet_clinic_v0.yaml` swapping
in for `energy_v0.yaml`.

## References

- ADR-001 (LLM model baseline — still valid)
- ADR-003 (service port strategy — still valid)
- ADR-005 (strategic pivot — rationale for parking)
