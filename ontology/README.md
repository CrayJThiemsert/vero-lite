# Ontology (the moat)

This directory will hold **YAML ontology files** — the canonical, single source of truth that drives code generation across the entire vero-lite stack.

## Status

**Empty placeholder for PLAN-001.** Real ontologies arrive in PLAN-002+.

## Concept

A vero-lite ontology is a YAML document describing, for one vertical (vet clinic, pharmacy, dental, ...):

- **Object types** — Patient, Visit, Diagnosis, Prescription, ...
- **Properties** — name, type, constraints, units, descriptions
- **Relationships** — Visit `belongs_to` Patient; Diagnosis `made_during` Visit
- **Actions** — typed FastAPI functions tied to objects (with permissions + audit trail)
- **Permissions** — role-based ACLs on properties and actions
- **Lineage hints** — where each object comes from (ETL source) and how it transforms

From a single ontology YAML, the **generator** (PLAN-004) emits:

- Pydantic v2 models (request/response, DB rows)
- SQL DDL (Postgres tables, indexes, constraints)
- JSON Schema (API docs, frontend forms)
- MCP tool definitions (for LLM agents to call typed actions)
- TypeScript types (for the future Next.js frontend)

## Planned layout

```
ontology/
├── _shared/                    # cross-vertical primitives
│   ├── identifiers.yaml        # ID types, NHS-style numbering, ...
│   └── timestamps.yaml         # created_at, updated_at, soft delete
└── vet/                        # vet-clinic vertical (first)
    ├── vet_clinic_v0.yaml      # Patient, Visit, Diagnosis (PLAN-002)
    ├── vet_clinic_v1.yaml      # + Prescription, Lab (later)
    └── README.md
```

Versions are explicit (`v0`, `v1`) so the generator can produce migrations between them.

## See

- [`../docs/plans/`](../docs/plans/) — PLAN-002 (first ontology), PLAN-004 (generator)
- [`../CLAUDE.md`](../CLAUDE.md) — three-layer architecture overview

---

_Last updated: 2026-05-05 (PLAN-001 scaffold)_
