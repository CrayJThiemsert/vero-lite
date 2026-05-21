---
plan: PLAN-003
title: Ontology Engine — YAML schema, validator, codegen, first vertical
status: Proposed
last_updated: 2026-05-20
session: 10
batch: 4
related_adrs:
  - ADR-006 (vertical plugin architecture)
  - ADR-007 (OCT engine contracts)
  - ADR-008 (YAML ontology specification)
related_plans:
  - PLAN-001 (starter pack scaffold — done; ontology/README.md content superseded by this plan)
  - PLAN-004 (handoff frontmatter and dashboard — Phase A done, Phase B/C deferred)
supersedes_notes:
  - ontology/README.md (2026-05-05 PLAN-001 artifact; ontology now lives at verticals/<name>/ontology/<name>_v0.yaml per ADR-006 D1 / ADR-008 D5)
phase_scope: Phase 1 only (Phase 2 deferred to Batch 5+)
---

# PLAN-003 — Ontology Engine (Phase 1)

## 1. Status

**Proposed** — drafted 2026-05-20 by Chat tier (Session 10 Step 5),
consolidating scope from Batch 3 closeout (2026-05-13-1445) +
Batch 3.5 mid-handoff (2026-05-14-1505) + pre-draft consultation pair
(2026-05-20 0215 dispatch + 0245 reply).

Status moves to **Accepted** when:
- Cray ratifies this draft and Code lands the doc on `origin/main`.
- Phase 1 kickoff dispatch is then authored as a separate round.

## 2. Context

PLAN-003 implements what ADR-006 / ADR-007 / ADR-008 specified: a
**vertical-agnostic ontology engine** that takes a per-vertical YAML
file and emits Pydantic models, PostgreSQL DDL, JSON Schema, MCP tool
definitions, and TypeScript types.

This is the **first concrete moat-building work**. ADR-006 Pattern #1
("Ontology = single source of truth via YAML") becomes executable
here. ADR-008 §D5 fixes the codegen contract; this plan implements it
plus the validator (§D6) and the first concrete vertical instantiation
(energy v0).

### 2.1 Strategic frame (two-layer moat)

- **Layer 1 (this plan).** YAML + codegen. A domain expert authors
  `verticals/<name>/ontology/<name>_v0.yaml`; the engine emits 5
  artifacts per vertical. Proprietary engine + domain-readable config.
- **Layer 2 (Phase 2 — deferred to Batch 5+).** Operationalize the
  engine: DataAdapter Protocol implementations per vertical,
  RecommendedAction runtime, three-layer wiring. LLM-driven YAML
  authoring (ADR-009+) sits on top and compounds the moat.

Phase 2 is out of scope for PLAN-003. This plan ships **the engine
itself**, not its operational use.

## 3. Scope (Phase 1)

### 3.1 In scope

| Deliverable | Path | Source contract |
|---|---|---|
| Engine package | `services/engine/__init__.py` | ADR-008 §Implementation Notes |
| JSON Schema for ontology format | `services/engine/ontology_schema.json` | ADR-008 §D6 |
| L2 semantic validator | `services/engine/ontology_validator.py` | ADR-008 §D6 |
| Code generator + 5 emitters | `services/engine/code_generator.py` | ADR-008 §D5 |
| Error hierarchy | `services/engine/errors.py` | Q20 (consultation) |
| CLI module | `services/engine/cli.py` | Q3 → R-5 |
| First concrete vertical | `verticals/energy/ontology/energy_v0.yaml` | ADR-006 D1 |
| Tests | `tests/services/engine/test_*.py` | pytest 8 + pytest-cov |
| CLI wiring | `pyproject.toml [project.scripts] vero-lite = "services.engine.cli:app"` | R-5 |

### 3.2 Out of scope (defer to Batch 5+)

- `services/engine/data_adapter.py` (Protocol decl) and any
  `verticals/energy/data_adapter/` runtime — Phase 2.
- `RecommendedAction` Pydantic runtime + `services/api/main.py`
  three-layer wiring — Phase 2.
- LLM-driven YAML authoring surface — ADR-009+.
- pgvector embeddings on `OperationalEvent` — deferred until PLAN-002
  (custom Postgres image with pgvector + Apache AGE + pg_trgm) is
  drafted. v0 uses ADR-008 D3 `json` as stopgap if needed.
- TypeScript `tsc` compile-time check — deferred until the future
  Next.js frontend brings its own toolchain (Q7 → "light" path).
- Phase-enum amendment to add `consultation` value — STATUS deferred
  TODO (R-9).
- Cleanup of stale `ontology/README.md` — STATUS deferred TODO (R-9
  cohort).

### 3.3 Phase 2 deliverables explicitly listed (for forward reference)

For Batch 5+ author convenience — these are **not** part of PLAN-003:

- DataAdapter Protocol declaration + per-vertical implementation
- RecommendedAction Pydantic model + audit envelope
- Three-layer wiring placeholder (`services/api/main.py`)
- First end-to-end action loop (read → recommend → approve → execute)

## 4. Architectural anchors (read alongside this plan)

| Anchor | Path | Relevance |
|---|---|---|
| ADR-006 | `docs/adr/0006-vertical-plugin-architecture.md` | Pattern #1 = ontology as SSOT via YAML; directory canon |
| ADR-007 | `docs/adr/0007-oct-engine-contracts.md` | D2 RecommendedAction envelope (informs MCP emitter target shape; Phase 2 runtime) |
| ADR-008 | `docs/adr/0008-yaml-ontology-specification.md` | **Authoritative**: D1 (5 base entities), D3 (9 data types), D4 (3 cardinalities), D5 (codegen contract), D6 (validation layers) |
| Diagram convention | `docs/conventions/diagram-syntax.md` | Mermaid > ASCII |

If anything in this plan appears to contradict ADR-008, **ADR-008
wins** and the plan must be amended.

## 5. Toolchain pins

Verified in repo at HEAD `e64731f` by pre-draft consultation reply
(`2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md` §1).

| Layer | Choice | Source |
|---|---|---|
| Python | `>=3.12` (installed CPython 3.12.3) | `pyproject.toml:8`, `:45`, `:66` |
| Type checking | `mypy --strict` with `pydantic.mypy` plugin | `pyproject.toml:66-71` |
| Linting | `ruff target-version="py312"` | `pyproject.toml:45` |
| Validation models | Pydantic v2 (declared `>=2.9.0`, installed `2.13.3`) | `pyproject.toml:12` |
| Package manager | uv 0.11.9 + hatchling build backend; `packages=["services"]` | `pyproject.toml:36-41` |
| CLI framework | **Typer** (R-5) — entry `services.engine.cli:app` | new dep |
| YAML parser | **ruamel.yaml** (R-6) — source `line:col` for L2 diagnostics | new dep |
| JSON Schema | `jsonschema` (`Draft202012Validator.iter_errors`) | new dep |
| Pre-commit YAML lint | `check-jsonschema` against `verticals/*/ontology/*.yaml` | new dev dep, ADR-008 D6 |
| Logging | `structlog>=24.4.0` (already declared, currently unused) | `pyproject.toml:21` |
| Test runner | pytest 8 + pytest-asyncio + pytest-cov | `pyproject.toml:73-79` |
| Coverage | `[tool.coverage.run] source=["services"]`, `fail_under=70` aspirational (R-8) | `pyproject.toml:82+` |
| SQL dialect | **PostgreSQL** (postgres:16-alpine runtime) | `docker-compose.yml:3` + ADR-008 §D3 |

## 6. Emitter contracts (per ADR-008 D5)

All 5 emitters use **pure-Python structured builders** (not Jinja2 —
Q6). Output is written to `verticals/<name>/generated/` (gitignored
per ADR-008 D5).

### 6.1 Pydantic emitter → `models.py`
- One class per ontology object type; properties become typed fields.
- Generated code must pass `ruff` + `mypy --strict` (project-wide
  gate; pydantic plugin enabled).
- ADR-008 D3 → Python type mapping:
  `string`→`str`, `int`→`int`, `float`→`float`, `bool`→`bool`,
  `timestamp`→`datetime`, `date`→`date`, `enum`→`Literal[…]` or
  `StrEnum`, `json`→`dict[str, Any]`, `ref`→typed FK string.
- Acceptance: emitted file `import`s clean and `ast.parse` succeeds.

### 6.2 SQL emitter → `schema.sql`
- **PostgreSQL-specific**, per ADR-008 D3 verbatim:
  - `string`→`TEXT`, `int`→`BIGINT`, `float`→`DOUBLE PRECISION`,
    `bool`→`BOOLEAN`, `timestamp`→`TIMESTAMPTZ`, `date`→`DATE`,
    `enum`→`TEXT CHECK (col IN (...))`, `json`→**`JSONB`**,
    `ref`→`TEXT REFERENCES <tbl>(<pk>)`.
- Every `ref` column gets an explicit `CREATE INDEX` on the FK column
  (Postgres does not auto-index FKs).
- Acceptance: emitted file parses (run via in-process `psycopg`
  parser-only or stub; or behavioral assertion that `CREATE TABLE`
  statements exist for every object type).

### 6.3 JSON Schema emitter → `schema.json`
- Per-object-type JSON Schema (draft 2020-12), useful for runtime
  payload validation and for downstream LLM constrained decoding.
- Acceptance: `json.load` succeeds + each schema meta-validates
  against the JSON Schema 2020-12 meta-schema.

### 6.4 MCP emitter → `mcp_tools.json`
- **Tool-definition JSON document**, not a server stub. Phase 2 wires
  the server (R-2; deferred).
- Each tool def carries `name`, `description`, `inputSchema` (a JSON
  Schema for the tool's argument shape).
- Generated tools: at least one read-tool per object type (e.g.
  `list_assets`, `get_asset_by_id`); action-bearing tools deferred to
  Phase 2 (when RecommendedAction runtime exists).
- Acceptance: `json.load` succeeds; structural check that each entry
  has the required MCP tool fields.

### 6.5 TypeScript emitter → `types.ts`
- Type aliases / interfaces per object type (no runtime code).
- Acceptance = **light path** (Q7 → R "light"): Python-side
  structural check that the emitted text is well-formed TS — **no
  `tsc` compile** in Phase 1. Acceptance fallback baked here so the
  question does not re-surface midflight: TS emitter passes when
  emitted file is non-empty, contains one `export` per object type,
  and parses as valid TS via a lightweight Python regex/AST check.
- Real `tsc` typecheck deferred to the future frontend's toolchain.

## 7. Schema authoring conventions (PD-4 + Q19 + Q20)

These are documented in `services/engine/ontology_schema.json`
description fields and validator code headers — **not** as a separate
ADR-008 amendment (Batch 3.5 D-3 rationale: Rule of Three on
conventions).

- **Property-level constraints:** inline `pattern:` and `format:` per
  property; `required: true` inline per property (not a separate
  top-level `required: [...]` list).
- **Link naming:** `subject_verb_object` snake_case
  (e.g. `asset_hosted_at_site`).
- **Logging:** engine uses `structlog` for validator and codegen
  diagnostic events; CLI human-facing output is plain
  `print`/`sys.stderr.write`. The validator's stderr summary line is
  the machine contract (Lesson #7 §3.1) — exact format:
  `OK: N file(s) valid` on success, `<E> error(s) across <M> file(s)`
  on failure.
- **Error hierarchy (`services/engine/errors.py`):**
  - `OntologyError` (base)
  - `SchemaValidationError(OntologyError)` — L1 (JSON Schema)
  - `SemanticValidationError(OntologyError)` — L2 (custom Python)
  - `EmitError(OntologyError)` — codegen failures
  - Each carries structured location: `file`, `object_type`,
    `property`, `yaml_line`, `yaml_col`. Mirrors
    `tools/handoffs/_schema.py` `ValidationError` dataclass shape for
    cross-tool consistency.

## 8. Five base entities — representative properties

Per Q13 ratification: **examples-only**, marked "extend during
implementation". Plan doc carries the contract; `energy_v0.yaml`
content is authored against the real validator at implementation time
(per the pre-verification protocol). Full YAML below would freeze SSOT
and conflict with ADR-008 D1 (the YAML *is* the source).

### 8.1 Asset (physical operational unit)
- `primary_key: asset_id` (string)
- Representative properties — extend during implementation:
  - `name: string`, `asset_type: enum`, `capacity_kw: float`,
    `status: enum`, `install_date: date`
- Links: `hosted_at_site (many_to_one Site)`,
  `parent_of_asset (many_to_one Asset, self-reference)`

### 8.2 Site (physical location hosting Assets)
- `primary_key: site_id`
- Representative properties: `name: string`, `lat: float`,
  `lng: float`, `site_type: enum`
- Links: `hosts_asset (one_to_many Asset)` — inverse of §8.1

### 8.3 OperationalEvent (time-stamped operational signal)
- `primary_key: event_id`
- Representative properties: `event_type: enum`, `severity: enum`,
  `measured_value: float`, `unit: string`,
  `occurred_at: timestamp`, `description: string`
- Links: `emitted_by_asset (many_to_one Asset)`,
  `occurred_at_site (many_to_one Site)`
- **Vector embeddings deferred:** v0 omits `description_vector`;
  re-add when PLAN-002 (Postgres + pgvector) lands.

### 8.4 Alert (actionable notification)
- `primary_key: alert_id`
- Representative properties: `title: string`, `urgency: enum`,
  `status: enum`, `opened_at: timestamp`, `resolved_at: timestamp`,
  `reasoning: string`

### 8.5 RecommendedAction (AI-proposed action awaiting approval)
- `primary_key: action_id`
- Representative properties: `action_type: enum`,
  `confidence_score: float`, `status: enum`, `parameters: json`
- Mirrors ADR-007 D2 envelope at runtime (Phase 2).
- Links: `addresses_alert (many_to_one Alert)`,
  `target_asset (many_to_one Asset)`

### 8.6 Cardinality rule — Alert ↔ OperationalEvent (R-7)

ADR-008 D4 defers `many_to_many`. For the Alert↔OperationalEvent
domain reality (one Alert can be triggered by many Events; one Event
can trigger many Alerts), v0 models the relationship via an **explicit
join object type**:

```yaml
- name: AlertEventLink
  description: Join object linking Alerts to the OperationalEvents that triggered them.
  primary_key: link_id
  properties:
    - { name: link_id, type: string, required: true }
    - { name: created_at, type: timestamp, required: true }
  links:
    - { name: alert, type: many_to_one, target: Alert, required: true }
    - { name: event, type: many_to_one, target: OperationalEvent, required: true }
```

**Rule for emitters:** join object types emit a regular Pydantic model
+ SQL table + JSON Schema entry like any other object type; no special
casing. The "many-to-many" semantic is achieved by composition, not by
a new cardinality keyword.

**Rule for Phase 2 graph overlay (deferred):** the future Apache AGE
overlay can collapse `AlertEventLink` to a graph edge at projection
time. v0 stays SQL-pure.

## 9. Acceptance criteria

All criteria use **Lesson #7 §3 reliable verification methods** (R-8).
No `echo $?`, no "expect exit N" wording, anywhere.

### 9.1 Validator behavior

- **Happy path:** in-process `ontology_validator.main([energy_v0.yaml])`
  returns 0; captured stderr contains `OK: 1 file(s) valid`.
- **Failure path — L1:** ≥3 invalid-YAML cases per L1 violation class
  (missing required, wrong type, unknown property). Each test asserts
  the captured `stderr` contains both `<N> error(s)` and a line
  reference (`yaml_line:yaml_col`) per error.
- **Failure path — L2:** ≥3 invalid-semantic cases (dangling `ref`,
  link target missing, enum value not in allowed set). Same assertion
  shape as L1.

### 9.2 Codegen behavior

For each of the 5 emitters, given a valid `energy_v0.yaml`:

- **Pydantic:** `python -c "import ast; ast.parse(open('models.py').read())"`
  succeeds; behavioral assertion that one class per object type
  exists (`grep -c '^class ' models.py == N_object_types`).
- **SQL:** behavioral assertion — `grep -c '^CREATE TABLE ' schema.sql
  == N_object_types`; one `CREATE INDEX` per `ref` property.
- **JSON Schema:** `json.load` succeeds; each schema meta-validates
  against JSON Schema 2020-12 meta-schema.
- **MCP:** `json.load` succeeds; structural check on tool def shape;
  ≥1 tool per object type.
- **TS (light path):** file exists, non-empty, one `export` per object
  type, regex-validates as well-formed TS — **no `tsc`**.

### 9.3 CLI behavior

- `vero-lite validate energy` exits 0 on valid YAML and prints
  `OK: 1 file(s) valid` to stderr; behavioral assertion via
  `subprocess.run(..., capture_output=True)` + stderr `.decode()`
  inspection.
- `vero-lite generate energy` produces 5 output files in
  `verticals/energy/generated/`; behavioral assertion = each file
  exists + size > 0 + matches per-emitter acceptance from §9.2.

### 9.4 Project-wide invariants

- **PD-5 wording grep:** `grep -rilEw 'banpu|fastenal|next'` across
  new code + comments + tests = 0 hits.
- **Coverage (R-8, aspirational):** `pytest --cov=services` reports
  ≥70% line coverage on `services/engine/`. **Aspirational target**,
  not blocking — Phase 1 closes if coverage is below 70% provided all
  §9.1-§9.3 acceptance passes; surface the gap in closeout for Cray.
- **Lint + type:** `ruff check services/engine/` clean;
  `mypy --strict services/engine/` clean.

## 10. Worktree + Lesson #3 prevention (R-3)

Phase 1 uses **worktree mode ON** (multi-file Python module + tests +
CLI, buildable, CI fail-isolation). Lesson #3 prevention checklist
(per `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md`):

- **Pre-flight ownership sweep:** `find .git .claude -user root | wc -l`
  before first `git add` — sweep if non-zero (B1/B2 cascade).
- **Shell-context guard:** `uname -s` must equal `Linux` before any
  `uv` invocation (A3 destructive subtrap).
- **uv path:** WSL-native uv only; never the Windows uv from a wrong
  shell context.
- **First-commit FS leftover:** `verticals/energy/generated/` is
  gitignored; sandbox-root writes there are expected B3-class
  leftovers — accept, do not chase.
- **Pre-commit hook on each commit:** detect-secrets + ruff + mypy via
  `PATH="$PWD/.venv/bin:$PATH" git commit -F …` to bypass the
  hard-coded POSIX `INSTALL_PYTHON` trap (Lesson #3 §A3).

Phase 1 kickoff dispatch (next round) carries the full pre-flight
sequence as commands; this plan documents the **rationale**.

## 11. Risks and known unknowns

- **R1 — MCP tool-def shape ambiguity.** Plan pins "tool-definition
  JSON document" per §6.4. If a downstream MCP consumer expects a
  different shape, plan amendment, not midflight reshape.
- **R2 — TS emitter "light" path drift.** If a real `tsc` typecheck
  is later demanded, this is a Phase 2/frontend issue, not a PLAN-003
  amendment trigger.
- **R3 — Coverage below 70%.** Aspirational per R-8; closeout
  surfaces the gap; Cray decides next-batch follow-up.
- **R4 — `energy_v0.yaml` content drift from §8 examples.** Expected
  — §8 is examples-only per Q13. Closeout names the final property
  set so future readers can map plan↔implementation.
- **R5 — Phase 2 forward reference creep.** Anything that requires
  DataAdapter / RecommendedAction runtime / three-layer wiring is
  out of scope (§3.2). Surface, do not implement.

## 12. References

### Architectural anchors
- `docs/adr/0006-vertical-plugin-architecture.md`
- `docs/adr/0007-oct-engine-contracts.md` (commit `1cc6000`)
- `docs/adr/0008-yaml-ontology-specification.md` (commit `b23ca8a`)
- `docs/conventions/diagram-syntax.md`

### Lessons
- `docs/lessons/0001-*.md` — operational tooling traps (Trap 7/10/11
  cited by Lesson #3)
- `docs/lessons/0002-*.md` — entry-point traps
- `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md` — worktree
  lifecycle (renumbered from "#13" on 2026-05-16 `c85a595`)
- `docs/lessons/0007-harness-exit-code-artifact.md` — reliable
  verification methods (§3.1 stderr summary, §3.2 in-process `main()`,
  §3.3 behavioral side effect)

### Conventions and protocols
- `docs/conventions/chat_tab_instructions.md` — Tier 1 self-check +
  3 protocols (anchor verification, reliable verification,
  pre-verification) at commit `be38bce`
- `docs/conventions/handoff-frontmatter-schema.md` — handoff frontmatter
  schema (Phase enum: kickoff|dispatch|midflight|closeout|handoff|discussion)

### Predecessor handoffs (read priority)
- `.claude/handoffs/session-10/2026-05-13-1445-session10-batch3-closeout.md` — original Phase 1/Phase 2 outline
- `.claude/handoffs/session-10/2026-05-14-1505-chat-handoff-mid-session-batch-3.5-to-4.md` — D-1..D-6 locked decisions
- `.claude/handoffs/session-10/2026-05-20-0215-chat-plan003-pre-draft-consultation.md` — Chat → Code consultation dispatch
- `.claude/handoffs/session-10/2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md` — Code's fact-pack reply (this plan's source of truth for toolchain pins, emitter approach, worktree traps)

### Inspirational references (cite-allowed in code comments where useful)
- `docs/research/private/2026-05-13-palantir-ontology-reference.md` §5+§6 — Foundry 4-tier validation pattern (adopt/diverge rationale)

### Layer 2 informant (NOT cited in PLAN-003 itself; informs ADR-009+)
- (Cray's private strategy note on LLM-driven vertical creation; not committed)

---

*PLAN-003 (Phase 1) — drafted Session 10 Step 5. Status moves to
Accepted on Cray ratification + Code commit. Phase 1 kickoff dispatch
follows as a separate round.*

*AI-assisted per project convention.*
