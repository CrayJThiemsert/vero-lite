# ADR-008: YAML Ontology Specification

**Status:** Accepted
**Date:** 2026-05-13
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-006 (vertical plugin architecture, D1 + pattern 1), ADR-007 (OCT engine contracts, paired), CLAUDE.md §3. **Extended by ADR-0033 (2026-07-18)** — shared-ontology mechanism; see §"Pointer note (2026-07-18)" at the end of this file (appended, so this file's existing line anchors stay stable).

## Context

ADR-006 D1 establishes `verticals/<name>/ontology/*_v0.yaml` as the
single source of truth for each vertical's domain model. This ADR
specifies the **schema** that those YAML files must conform to.

Design influenced by Palantir Foundry's ontology model (object types,
properties, link types, action types — see research notes at
`docs/research/private/2026-05-13-palantir-ontology-reference.md` if
the Cowork dispatch completed) with deliberate simplifications for
solo-dev / open-source / local-LLM scope.

## Decision

### D1: 5 base entity types (object types in Palantir terminology)

Every vertical's `<name>_v0.yaml` MUST define these 5 base types
(may extend with vertical-specific types):

1. **Asset** — the operational unit being managed (battery, smart bin,
   vehicle, machine, animal patient, etc.)
2. **Site** — physical or logical location grouping multiple Assets
3. **OperationalEvent** — time-stamped occurrence concerning an Asset
   or Site (alarm, transition, reading)
4. **Alert** — a derived OperationalEvent meeting a threshold or rule;
   surfaced to operators
5. **RecommendedAction** — an Alert + LLM reasoning trace + suggested
   handler (matches ADR-007 RecommendedAction envelope at runtime)

### D2: YAML top-level structure

```yaml
version: 0
namespace: <vertical_name>  # matches verticals/<name>/

object_types:
  <ObjectTypeName>:
    primary_key: <property_name>
    title_key: <property_name>  # optional; defaults to primary_key
    description: <string>       # optional
    properties:
      <property_name>:
        type: <data_type>
        required: <bool>        # default false
        description: <string>   # optional
        constraints:            # optional
          <constraint_name>: <value>

link_types:
  <link_name>:
    from: <ObjectTypeName>
    to: <ObjectTypeName>
    cardinality: <one_to_one | one_to_many | many_to_one | many_to_many>
    foreign_key: <from.field → to.field>
    description: <string>       # optional
```

### D3: Supported data types (v0 — minimal set)

| Type | YAML literal | Generated Pydantic | Generated SQL |
|------|--------------|--------------------|----------------|
| `string` | text | `str` | `TEXT` |
| `int` | integer | `int` | `INTEGER` |
| `float` | floating-point | `float` | `DOUBLE PRECISION` |
| `bool` | boolean | `bool` | `BOOLEAN` |
| `timestamp` | ISO 8601 | `datetime` | `TIMESTAMPTZ` |
| `date` | ISO 8601 date | `date` | `DATE` |
| `enum` | requires `values:` list | `Literal[...]` | `TEXT CHECK (...)` |
| `json` | arbitrary JSON | `dict[str, Any]` | `JSONB` |
| `ref` | foreign key to another object | `str` (PK value) | `TEXT REFERENCES` |

**Deferred to v1 (Rule of Three trigger):** `media`, `geo`, `time_series`,
`shared property`. Add when 3+ verticals request them.

### D4: Cardinality grammar (v0 — restricted set)

Supported: `one_to_one`, `one_to_many`, `many_to_one`.

**Deferred:** `many_to_many` requires explicit join-table object type
(per ADR-006 D4 Rule of Three: defer until 3+ verticals need it).

### D5: Code generation contract

When `vero-lite generate <vertical>` runs on `<name>_v0.yaml`, it emits:

| Artifact | Path | Purpose |
|----------|------|---------|
| Pydantic models | `verticals/<name>/generated/models.py` | Runtime type safety |
| SQL DDL | `verticals/<name>/generated/schema.sql` | DB schema |
| JSON Schema | `verticals/<name>/generated/schema.json` | API validation |
| MCP tool defs | `verticals/<name>/generated/mcp_tools.json` | LLM tool exposure |
| TypeScript types | `verticals/<name>/generated/types.ts` | Frontend types |

`generated/` is gitignored; reproducible from `<name>_v0.yaml`.

### D6: Validation

Two levels:

**L1 (schema validation):** Conformance to ADR-008 grammar itself.
Implemented via JSON Schema in `services/engine/ontology_schema.json`.
CLI: `vero-lite validate <vertical>`. Pre-commit hook on
`verticals/*/ontology/*.yaml`.

**L2 (semantic validation):** Cross-reference integrity (foreign keys
resolve, enum values consistent, link cardinality enforceable).
Implemented in `services/engine/ontology_validator.py`. Runs as part of
`vero-lite generate`.

JSON Schema chosen over Pydantic schema for L1 because:
- Tooling ecosystem (IDE support, online validators, `jsonschema` lib)
- Industry standard for YAML/JSON validation
- Pydantic schema is downstream artifact (engine emits it from YAML);
  using Pydantic to validate the YAML that defines it = circular

(If Cowork research notes recommend differently, a follow-up ADR
amendment may revise this section.)

## Consequences

### Positive
- 5 base types give every vertical a common operational vocabulary
- Restricted v0 set (data types + cardinality) keeps PLAN-003 scope
  bounded
- Code generation contract makes engine output predictable; PLAN-003
  has clear deliverables
- JSON Schema validation = battle-tested tooling

### Negative
- 5 base types may not fit every vertical perfectly (vet clinic may
  want "Patient" not "Asset"); mitigated by allowing extension
- Restricted cardinality means some real-world many-to-many relationships
  must be modeled as join object types (acceptable; Palantir does the
  same with object-backed links)
- JSON Schema can be verbose for complex constraints; acceptable trade-off

### Neutral
- ADR-008 + ADR-007 paired form the complete engine contract surface
  through Phase 1

## Alternatives Considered

### Alternative 1: No base type set; each vertical defines its own

- **Pros:** Maximum flexibility
- **Cons:** No common vocabulary across verticals; OCT's 3 features
  can't generalize without baseline assumptions
- **Why rejected:** 5 base types ARE the OCT abstraction; without
  them, OCT is just "ontology per vertical" with no engine value-add

### Alternative 2: Pydantic schema for L1 validation

- **Pros:** Python-native; one less tool
- **Cons:** Circular (engine emits Pydantic from YAML; using Pydantic
  to validate that YAML = self-reference); less ecosystem tooling
- **Why rejected:** JSON Schema is the right industry choice; Pydantic
  remains the engine OUTPUT artifact

### Alternative 3: Include media / geo / time_series in v0

- **Pros:** Energy vertical wants time_series for asset readings
- **Cons:** Rule of Three (ADR-006 D4); media + geo aren't in
  immediate critical path
- **Why rejected:** Add in v1 when 3+ verticals validate the pattern.
  Energy vertical can use `json` type for time_series in v0 as a stopgap

### Alternative 4: Full Palantir Foundry parity (RIDs, shared properties, object-backed links, etc.)

- **Pros:** No ceiling on ontology expressiveness
- **Cons:** Solo-dev scope; YAGNI; "Palantir-lite" not "Palantir-full"
- **Why rejected:** vero-lite is intentionally lighter — see ADR-005
  framing ("OCT for distributed asset operations" not "full enterprise
  operating system")

## References

- ADR-006 (vertical plugin architecture, D1 + pattern 1)
- ADR-007 (OCT engine contracts, paired with this ADR)
- CLAUDE.md §3 (semantic layer = the moat)
- `docs/research/private/2026-05-13-palantir-ontology-reference.md`
  (Cowork-produced research notes; gitignored working reference;
  cited as design influence — a future batch may lift an edited
  version to `docs/strategy/public/palantir-ontology-reference.md`
  per Tier 2 responsibility)
- Palantir Foundry ontology docs (see research notes for URLs)
- Future: ADR for v1 ontology spec (media + geo + time_series + shared
  properties when Rule of Three triggers)

## Implementation Notes

Paired with ADR-007. PLAN-003 (Batch 4) will:
- Write `services/engine/ontology_schema.json` (the JSON Schema)
- Write `services/engine/ontology_validator.py` (L2)
- Write `services/engine/code_generator.py` (emit 5 artifacts)
- Write `verticals/energy/ontology/energy_v0.yaml` (first concrete
  instantiation — the actual moat-building task)

---

## Pointer note (2026-07-18) — extended by ADR-0033 (shared-ontology mechanism)

> **Extended, NOT amended in place** — D2/D3/D5 above stand as written for
> per-vertical docs. **ADR-0033** codifies the shared/core ontology
> construct: a repo-level shared home (`ontology/core_v0.yaml`) with the
> reserved `core` namespace token (a SEMANTIC reservation — the L1 namespace
> pattern already admits the token; enforcement is grammar prose +
> validator/CLI convention, ADR-0033 D1); the explicit `imports:` grammar
> key + shared-doc pre-pass resolution with qualified `core.<Type>` `ref`
> targets (ADR-0033 D2); and a constrained-collection type-system extension
> the D3 table cannot express — a `set` type with `items:` +
> `constraints: {min_length}` plus a `closed:` strict-object knob
> (ADR-0033 D3). The D3 deferral "`shared property` … Add when 3+ verticals
> request them" (`:79-80`) is consciously re-argued in ADR-0033 D6 **for
> `Person` only** (the ADR-0026 OQ-6 N≥2 re-trigger fired; the mechanism
> itself ships at N=1 consumer, consciously accepted — not genericized).
> Known drift, recorded there too (ADR-0033 D7): the D5 5-artifact table
> reflects the v0 baseline; the shipped generator emits 7 artifacts (ORM at
> a committed destination + context pack). This note is appended (not
> inserted) so existing `file:line` citations of this ADR remain valid.
