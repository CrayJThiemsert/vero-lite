# ADR-005: Strategic Pivot — From SMB Vet Clinic to Operational Control Tower

**Status:** Accepted
**Date:** 2026-05-11
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-006 (vertical plugin architecture), CLAUDE.md §1

## Context

Sessions 1-9 of vero-lite targeted Thai SMB veterinary clinics as the
Phase 1 vertical. Architecture (ontology engine + code generator + local-LLM
inference) was designed vertical-agnostic but assumed vet clinic as first
concrete instantiation.

During Session 10, two enterprise opportunities surfaced with materially
different characteristics than the original vet clinic bet:

1. **Regional distributed energy operator** — Energy-as-a-Service, battery
   storage, grid management. Existing executive relationship at decision-maker
   level. Operational complexity that current AI/analytics tools don't address.

2. **Industrial distributed inventory operator** — Smart bins, vending,
   maintenance-repair-operations supply chain. Cross-geography asset
   operations at scale. Existing executive contact.

Both opportunities share:
- Distributed-asset operations as the core problem (not records-keeping)
- Existing data infrastructure to integrate WITH (not greenfield)
- Need for "Operational Intelligence" — ontology + LLM reasoning + workflow execution
- Higher contract value than SMB market
- Cross-industry pattern overlap (validates template strategy)

## Decision

**Phase 1 vertical pivots from SMB veterinary clinics to Operational Control
Tower (OCT) for distributed asset operations.**

**Veterinary clinic vertical = parked as Phase 2** (not deleted). All
architectural decisions (ADRs 001-004) remain valid; only the first
vertical instantiation changes.

### OCT defined

Three vertical-agnostic features:

1. **Ontology-driven operational map** — visual graph of entities,
   relationships, real-time status.
2. **Natural language operational query** — executives ask in plain
   language, LLM routes through ontology to data, returns answer with
   provenance.
3. **Anomaly detection + suggested action** — LLM-generated recommendation
   with reasoning trace, awaiting human approval before execution.

### Design partner sequence

| Order | Partner type | Why |
|-------|--------------|-----|
| 1 (primary) | Regional energy operator | Strongest existing relationship; energy data abundance for synthetic demo |
| 2 (secondary) | Industrial supply chain operator | Cross-industry validation; reference customer for template strategy |

Specific company names are intentionally omitted from this ADR until
formal agreements exist (see `docs/strategy/private/` for non-public detail).

### Vertical instantiation pattern

```
              Operational Control Tower (core)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Energy    Supply Chain   Vet (parked)
                          │
            (each = ontology + data adapter swap,
             same core engine + 3 features)
```

## Consequences

### Positive

- **Larger contract value** — enterprise vs SMB economics
- **Cross-industry validation** — template strategy proven, not theoretical
- **Existing relationships** — reduces design partner acquisition cost to ~0
- **Data sovereignty framing** — PDPA-specific narrative generalizes to
  "on-prem option for sensitive operational data" (works in US + Thai markets)
- **Architecture decisions preserved** — no rework of ADRs 001-004; ontology
  engine was already vertical-agnostic

### Negative

- **Vet clinic deferred** — investment in vet-specific thinking (handwriting
  OCR, Thai medical text) becomes Phase 2 work
- **Enterprise sales cycle longer** — quarter-scale, not week-scale
- **Compliance scope wider** — energy/industrial operators have their own
  regulatory regimes (NERC CIP for US energy, sector-specific in Thailand)
- **Synthetic demo data harder** — energy/grid telemetry simulation requires
  more domain modeling than vet clinic transactions

### Neutral

- Local LLM strategy unchanged (ADR-001 — MS-S1 MAX inference)
- Network topology unchanged (ADR-002 — Cray ↔ MS-S1 MAX LAN)
- Service port strategy unchanged (ADR-003 — `${VAR:-default}` pattern)
- Author email unchanged (ADR-004)

## Alternatives Considered

### Alternative 1: Continue vet clinic, defer enterprise opportunities

- **Pros:** No pivot cost; SMB market still attractive long-term
- **Cons:** Burns existing executive relationships (cooling off if not engaged
  in Phase 1 timeframe); higher design partner acquisition cost; smaller
  contracts; harder template validation (single-vertical bet)
- **Why rejected:** Existing relationships are time-bound assets. Acting on
  them in Phase 1 doesn't preclude vet clinic in Phase 2; the reverse may.

### Alternative 2: Pursue both verticals in parallel

- **Pros:** Hedge bets; broader market exposure
- **Cons:** Solo developer; context-switching cost; cannot do justice to either;
  "Small but strong" framing demands focus
- **Why rejected:** Phase 1 is about depth (3 features done well), not breadth.
  Parallel verticals = neither converges.

### Alternative 3: Pivot to ONE enterprise vertical only, drop vet clinic permanently

- **Pros:** Maximum focus
- **Cons:** Vet clinic ontology design partially informed the engine; the
  Phase 2 expansion option has marketing/positioning value; "platform that
  works across industries" is stronger than "platform that works for
  energy companies"
- **Why rejected:** Park ≠ delete. Optional future value at zero current cost.

### Alternative 4: Greenfield rewrite for OCT

- **Pros:** No legacy baggage from vet-specific thinking
- **Cons:** ADRs 001-004 + Phase 1 scaffolding are vertical-agnostic by design;
  rewrite cost is real, value is illusory
- **Why rejected:** The architecture WAS designed for this. Pivot needs
  ontology + data adapter swap, not engine rewrite.

## References

- Session 10 Chat conversation handoff: `.claude/handoffs/session-10/2026-05-11-0325-chat-conversation-handoff.md` (decision history)
- ADR-006: Vertical Plugin Architecture (template strategy)
- ADR-007: OCT Architecture (Batch 3, forthcoming)
- ADR-008: YAML Ontology Specification (Batch 3, forthcoming)
- `docs/strategy/private/` (gitignored — specific opportunity analysis)

## Implementation Notes

This ADR is paired with Batch 2 commits #5-#8 which:
- Add "parked" notes to vet-mentioning artifacts (commit #5) — freezes
  historical context BEFORE this pivot ADR lands
- Land this ADR (commit #6) — abstract framing of the pivot
- Land ADR-006 (commit #7) — architectural codification
- Update CLAUDE.md + STATUS.md (commit #8) — visible state shift
