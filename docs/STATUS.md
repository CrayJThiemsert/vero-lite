---
last_updated: 2026-05-13
session: 10
batch: 3
state: stable
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Phase 1, Month 1, Session 10 Batch 3** — OCT engine contracts (ADR-007) + YAML ontology specification (ADR-008) landed. Phase 1 vertical = Operational Control Tower (OCT) per ADR-005; vet clinic vertical parked as Phase 2. Vertical plugin architecture codified per ADR-006. Directory scaffolds (`verticals/`, `docs/strategy/`) in place. Cowork Tier 0 first deliverable (Palantir Foundry ontology reference brief) cited from ADR-008 §Context.

Active priorities:
1. Engage 2 enterprise design partners — regional energy operator (primary) + industrial supply chain operator (secondary)
2. Build YAML ontology + code generator + 3 OCT features (the moat — vertical-agnostic engine per ADR-006)
3. Energy vertical instantiation first: `verticals/energy/ontology/energy_v0.yaml` (5 entities) + synthetic demo data (NYISO/CAISO-style time-series)

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-13 | ADR-007 (OCT engine contracts) + ADR-008 (YAML ontology specification) — both Accepted | `docs/adr/0007-oct-engine-contracts.md`, `docs/adr/0008-yaml-ontology-specification.md` |
| 2026-05-13 | Cowork Tier 0 first deliverable — Palantir Foundry ontology reference brief (validates ADR-008's 4-tier model; cited from ADR-008 §Context as influencing reference) | `docs/research/private/2026-05-13-palantir-ontology-reference.md` |
| 2026-05-11 | ADR-006 — Vertical Plugin Architecture (D1–D4 + 5 core patterns; template-first multi-vertical) | `docs/adr/0006-vertical-plugin-architecture.md` |
| 2026-05-11 | ADR-005 — Strategic Pivot from SMB vet clinic to Operational Control Tower (vet clinic parked as Phase 2) | `docs/adr/0005-strategic-pivot-to-oct.md` |
| 2026-05-10 | ADR-004 closed — GitHub noreply alias as canonical author email (provisional) | `docs/adr/0004-canonical-author-email.md` |
| 2026-05-10 | Worktree mode policy codified in CLAUDE.md §6 (per Lesson #13) | `CLAUDE.md` §6 |
| 2026-05-10 | Handoff rotation policy codified in runbook | `docs/runbooks/claude-code-chat-handoff.md` |

## In-Flight Discussions

- **Batch 3 (ADR-007 + ADR-008):** Both **Accepted 2026-05-13** — OCT engine contracts + YAML ontology specification (5 base types, JSON Schema validation). Cowork Tier 0 brief at `docs/research/private/2026-05-13-palantir-ontology-reference.md` cited from ADR-008 §Context; 5 open questions in the brief remain candidates for future ADR amendments.
- **Batch 4 (PLAN-003):** Ontology Engine implementation steps — first vertical `energy_v0.yaml` + code generator. Forthcoming.
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (see PLAN-001 line 9 forward-reference); ADR-005 has since been reused for the strategic pivot. The Postgres image ADR needs a fresh number (earliest available: ADR-009, post Batch 3's ADR-007/008).
- **Hook portability across environments:** Lesson #13 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **ADR-007** — OCT engine contracts (DataAdapter, RecommendedAction, three-layer wiring) *(Session 10 Batch 3)*
- [x] **ADR-008** — YAML ontology specification (5 base types, JSON Schema validation) *(Session 10 Batch 3)*
- [x] **`.gitignore` extension** — add `docs/research/private/` (Cowork closeout flag #1) *(Session 10 Batch 3-prep)*
- [ ] **PLAN-003** — Ontology Engine implementation: `verticals/energy/ontology/energy_v0.yaml` (5 entities) + code generator — *the moat* *(Batch 4)*
- [ ] **ADR-NN (TBD, ≥ ADR-009) + PLAN-002** — Custom Postgres image with extensions (renumbered after ADR-005 reused for strategic pivot)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [ ] Filesystem cleanup: `wsl -u root -- rm -rf .claude/worktrees/sad-northcutt-6a48ff/` (cosmetic, no rush)
- [x] **ADR-006** — Vertical Plugin Architecture *(Session 10 Batch 2)*
- [x] **ADR-005** — Strategic Pivot to OCT (vet clinic parked Phase 2) *(Session 10 Batch 2)*
- [x] **Directory scaffolds** — `verticals/{_template, energy, supply_chain, vet_clinic}/` + `docs/strategy/{public, private}/` *(Session 10 Batch 2)*
- [x] **Parked-note pass** — 6 vet-mentioning docs annotated *(Session 10 Batch 2)*
- [x] **ADR-004** — Canonical author email (GitHub noreply, provisional) *(Session 10)*
- [x] **Worktree mode policy** — codified in CLAUDE.md §6 *(Session 10)*
- [x] **Handoff rotation policy** — codified in runbook *(Session 10)*
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #12 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #13** — Code Tab worktree lifecycle traps *(Session 9)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*

## Next Steps

1. **Session 10 Batch 4** — Draft PLAN-003 (Ontology Engine implementation; `energy_v0.yaml` first vertical instantiation, code generator)
2. **Session 10 Batch 5+** — Energy vertical synthetic demo data generator + first design partner conversation prep
3. **Adjacent** — Mint new ADR number for the parked Postgres image decision (≥ ADR-009)
4. **Ongoing** — Continue exercising file-based handoff mechanism (Chat ↔ Code, Project Knowledge transport) across batches; capture any new traps as Lesson #13 amendments or new lessons.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A session closes (sync `last_updated` + `session` front-matter)

Manually edited at session boundaries. Not auto-generated.
