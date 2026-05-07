# Glossary

> vero-lite domain vocabulary. Reference for new contributors and AI agents.

---

| Term | Meaning |
|------|---------|
| **Ontology** | YAML files defining canonical objects, properties, relationships, and actions for a vertical |
| **Vertical** | A specific domain (vet clinic, pharmacy, dental clinic, etc.) |
| **Generator** | Code that reads ontology YAML and emits Pydantic models, SQL DDL, MCP tools, TS types |
| **MCP** | Model Context Protocol — standard for exposing tools/resources to LLM agents |
| **HITL** | Human-In-The-Loop — required before destructive AI actions |
| **Lineage** | Track-back from any data point to its sources, transformations, and decisions |
| **Object Explorer** | Foundry-style UI for browsing/querying canonical objects |
| **Time travel** | Query the state of objects at a past point in time (audit trail core feature) |
| **Mapping layer** | dbt/SQLMesh translates raw sources → canonical records (per `CLAUDE.md` §3) |
| **Semantic layer** | YAML ontology = single source of truth (the moat) |
| **Action layer** | FastAPI functions tied to objects with permissions + audit trail |
| **The moat** | YAML ontology + code generator — vero-lite's defensibility vs. generic CRUD platforms |
| **Design partner** | Early customer (vet clinic) co-developing features in exchange for discounted/free access |
| **PDPA** | Thailand Personal Data Protection Act — clinical data assumed PII |
| **AIP / Foundry / Apollo** | Palantir product names; vero-lite borrows architectural patterns |
| **Cray** | Cray-Legion5Pro dev machine (Win11 + WSL2 Ubuntu) |
| **MS-S1 MAX** | LLM server (AMD Ryzen AI Max+ 395, 128GB unified, 192.168.1.133) |
| **Cowork** | Anthropic's Desktop tool for non-developer file/task automation |
| **smb-flow** | Sibling project on Cray; coexists with vero-lite via env-overridable ports (ADR-003) |

---

## References

- `CLAUDE.md` §1 — Project Identity
- `CLAUDE.md` §3 — Architecture mental model
- `docs/conventions/tech-stack.md` — Implementation choices
