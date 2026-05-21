---
plan: PLAN-0005
title: OCT Engine Runtime Layer (Phase 2) — DataAdapter, RecommendedAction runtime, three-layer wiring, first action loop
status: Ready for execution
last_updated: 2026-05-21
session: 10
batch: plan0005-phase2-authoring
related_adrs:
  - ADR-006 (vertical plugin architecture — D1 layout, §5 patterns 2/3/4)
  - ADR-007 (OCT engine contracts — D1 DataAdapter, D2 RecommendedAction envelope, D3 I/O boundary, D4 three-layer wiring)
  - ADR-008 (YAML ontology specification — D5 codegen contract that Phase 2 consumes)
related_plans:
  - PLAN-003 (ontology engine — Phase 1; MERGED 30619b8; Phase 2 forward-referenced in §3.3)
  - PLAN-002 (custom Postgres image w/ pgvector + Apache AGE + pg_trgm — NOT yet drafted; persistence dependency, see OQ-4)
  - PLAN-004 (handoff frontmatter + dashboard — Phase A done; Phase B/C deferred)
supersedes_notes:
  - PLAN-003 §3.3 "Phase 2 deliverables explicitly listed (for forward reference)" is realised here; PLAN-003 itself is unchanged and remains the Phase 1 record.
phase_scope: Phase 2 only (operationalises the Phase 1 engine; Layer 2 of the PLAN-003 §2.1 two-layer moat)
authored_by: cowork-session-10 (Tier 0 + Tier 1 merged workspace per ADR-009 D1; uncommitted draft — Code commits per ADR-009 D2)
---

# PLAN-0005 — OCT Engine Runtime Layer (Phase 2)

## 1. Status

**Ready for execution** — authored 2026-05-21 by Cowork (Tier 0 + Tier 1 merged
workspace, per ADR-009 D1); the six Open Questions in §8 were **adjudicated by
Cray on 2026-05-21** (all rulings matched the Cowork recommendation). This is
still an **uncommitted draft**; Code commits after review per ADR-009 D2 ("only
Code commits" fail-safe). K-2 does not block this path — `docs/plans/` is outside
`.claude/`.

Readiness gate:

- [x] Cray adjudicated the six Open Questions in §8 (per ADR-009 D1 Tier-1
      rule #8 — "surface, do not silently choose"). Done 2026-05-21.
- [x] Numbering/naming decision in §1.1 confirmed (new PLAN-0005).
- [ ] Code lands the doc on `origin/main`.
- [ ] A Phase 2 kickoff dispatch is then authored as a separate round (mirroring
      the PLAN-003 → kickoff-dispatch split).

### 1.1 Numbering / naming surface (Cray confirms)

The brief asked Cowork to judge whether this should be a **new PLAN-0005** or a
**PLAN-003 extension**, and to surface the question rather than silently choose.

**Cowork judgement: new PLAN-0005 (not a PLAN-003 extension).** Rationale:

1. PLAN-003 frontmatter pins `phase_scope: Phase 1 only (Phase 2 deferred to
   Batch 5+)`; PLAN-003 §3.3 states the Phase 2 deliverables "are **not** part
   of PLAN-003". Treating Phase 2 as a PLAN-003 edit would contradict the
   ratified scope boundary of an already-merged plan.
2. Repo convention is one document per plan number, numbered sequentially.
3. `docs/plans/` currently holds `0000-template`, `0003-ontology-engine`,
   `0004-handoff-frontmatter-and-dashboard`, and `done/PLAN-001-*`. The highest
   live number is 0004, so **0005 is the next free number**.

**Two surfaces flagged for Cray (not silently consumed):**

- **0002 is a reserved-but-undrafted slot.** STATUS "In-Flight Discussions"
  earmarks PLAN-002 for the custom Postgres image (pgvector + Apache AGE +
  pg_trgm). Cowork did **not** consume 0002; this plan takes 0005 to preserve
  that earmark. (Precedent: the round-2 trial surfaced the ADR-007 References
  earmark collision rather than silently consuming a future-earmarked slot.)
- **PLAN-003 was never moved to `done/`** despite Phase 1 merging at `30619b8`.
  CLAUDE.md §6 "Plan Flow" step 4 says `git mv docs/plans/NNNN-*.md
  docs/plans/done/` after completion. This is a Code-side housekeeping item
  (Cowork holds no `git mv` authority per ADR-009 D2). Flagged, not actioned.

## 2. Context

PLAN-003 (Phase 1, merged `30619b8`) shipped **the engine itself**: the YAML
ontology grammar (ADR-008 D2), the L1+L2 validator, the five codegen emitters
(Pydantic / Postgres DDL / JSON Schema / MCP tool-defs / TypeScript-light), the
`energy_v0.yaml` first vertical (6 object types + 7 link types), and the
`vero-lite` Typer CLI. Phase 1 stops at **compile-time** code generation; it
does not operationalise the engine.

Phase 2 (this plan) is **the runtime layer** — it makes the generated artifacts
do work at request time. It implements the three engine-owned contracts that
ADR-007 specified but PLAN-003 deferred: the **DataAdapter Protocol** (ingress),
the **RecommendedAction runtime envelope** (action layer), and the **three-layer
wiring** that connects ingress → semantic → action inside `services/api/`. It
then proves the wiring with a **first end-to-end action loop**
(read → recommend → approve → execute) on the energy vertical.

### 2.1 Strategic frame — Layer 2 of the two-layer moat

PLAN-003 §2.1 frames the moat in two layers:

- **Layer 1 (PLAN-003, shipped).** YAML + codegen. A domain expert authors the
  ontology; the engine emits five artifacts per vertical.
- **Layer 2 (this plan).** Operationalise the engine: DataAdapter implementations
  per vertical, the RecommendedAction runtime, three-layer wiring. LLM-driven
  YAML authoring (ADR-010+ / ADR-009 family) sits on top and compounds the moat —
  it is **not** in Phase 2.

This plan ships **the engine's operational use**, not new ontology expressiveness.

## 3. Scope (Phase 2)

### 3.1 Goal

Stand up the OCT engine **runtime layer** so that, for the energy vertical, the
system can ingest objects through a `DataAdapter`, materialise them as typed
entities, derive a `RecommendedAction` from an `Alert`, and carry that action
through a minimal **approve → execute** gate — all wired through `services/api/`
behind FastAPI endpoints, with the `RecommendedAction` shape conforming to the
ADR-007 D2 envelope. The deliverable is a working, tested, vertical-agnostic
runtime spine plus one concrete energy instantiation that exercises it
end-to-end.

### 3.2 In scope

| Deliverable | Path (proposed) | Source contract |
|---|---|---|
| DataAdapter Protocol declaration | `services/engine/data_adapter.py` | ADR-007 D1 (verbatim async signature) |
| Energy synthetic DataAdapter impl | `verticals/energy/data_adapter/__init__.py` (+ synthetic generator) | ADR-006 §5 pattern #4 + D1 layout; energy/README "synthetic generator first" |
| RecommendedAction runtime envelope | `services/engine/actions.py` | ADR-007 D2 (ReasoningStep, EntityRef, AuditMetadata, RecommendedAction) |
| Vertical registry (adapters + handlers) | `services/engine/registry.py` | ADR-006 §5 patterns #2/#3 ("register at runtime"); ADR-007 D1 "plugin discovery" — mechanism unpinned, see OQ-6 |
| Rule-based recommender (stub) | `services/engine/recommender.py` | ADR-007 D4 action layer; LLM hook deferred (OQ-3) |
| Persistence layer + first migration | `services/db/` + `alembic/` | declared deps (SQLAlchemy 2.0 async + Alembic + asyncpg); see OQ-4 |
| Three-layer wiring + action-loop endpoints | `services/api/main.py` (+ routers) | ADR-007 D3/D4 |
| First end-to-end action-loop test | `tests/services/engine/` + `tests/api/` | acceptance §7 |
| Dep / config additions if any | `pyproject.toml`, `.env.example` | Code-only edits |

### 3.3 Out of scope (defer to later batches)

- ❌ **LLM reasoning hook surface** — ADR-007 explicitly defers this to its own
  ADR (ADR-010+). Phase 2's "recommend" step is a deterministic rule (OQ-3); no
  model inference.
- ❌ **Full approval + audit framework** — ADR-007 D4 marks "Approval + audit"
  as a future-ADR placeholder (ADR-011+). Phase 2 ships only a **minimal**
  approval gate (OQ-2); correlation-id propagation, approval-chain enforcement,
  and immutable audit logging stay deferred.
- ❌ **Natural-language operational query** (OCT feature #2) and **anomaly
  detection** (OCT feature #3, beyond the rule-based stub) — later batches.
- ❌ **Mapping layer (dbt / SQLMesh)** — ADR-007 D4 names these for raw→canonical
  canonicalisation; neither is a repo dep. The synthetic adapter returns
  canonical-shaped dicts directly (OQ-5).
- ❌ **pgvector / Apache AGE / pg_trgm features** — depend on PLAN-002 (custom
  Postgres image), not yet drafted. Phase 2 targets base `postgres:16-alpine`.
- ❌ **TypeScript frontend consumption** of the generated `types.ts` — future
  frontend toolchain.
- ❌ **Second vertical (supply_chain) adapter** — Phase 2 instantiates energy
  only; Rule of Three (ADR-006 D4) is unaffected.

### 3.4 Forward reference (Phase 3+ — not part of this plan)

- LLM reasoning hook (ADR-010+) replacing the §3.2 rule-based recommender.
- Approval + audit framework (ADR-011+) replacing the §6.5 minimal gate.
- dbt/SQLMesh mapping layer once a real (non-synthetic) raw source exists.
- `vero-lite new-vertical <name>` generator (ADR-006 D3 L2 target).

## 4. Architectural anchors (read alongside this plan)

| Anchor | Path | Relevance |
|---|---|---|
| ADR-006 | `docs/adr/0006-vertical-plugin-architecture.md` | D1 directory layout; §5 patterns #2 (DataAdapter), #3 (Action Framework), #4 (Demo Data Generator) |
| ADR-007 | `docs/adr/0007-oct-engine-contracts.md` | **Authoritative**: D1 DataAdapter signature, D2 RecommendedAction envelope, D3 I/O boundary, D4 three-layer wiring + layer ownership table |
| ADR-008 | `docs/adr/0008-yaml-ontology-specification.md` | D5 codegen contract — Phase 2 **consumes** the emitted artifacts (Pydantic models, schema.sql, mcp_tools.json) |
| PLAN-003 | `docs/plans/0003-ontology-engine.md` | §2.1 two-layer frame; §3.3 Phase 2 forward-reference; §8.5 RecommendedAction representative properties; §10 worktree section (mirrored in §9 here) |
| CLAUDE.md §3 | `CLAUDE.md` | three-layer mental model (mapping → semantic → action) |
| Lesson #7 | `docs/lessons/0007-harness-exit-code-artifact.md` | §3 reliable verification methods — all §7 acceptance criteria use these |
| Lesson #3 | `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md` | worktree lifecycle prevention checklist (mirrored §9) |

If anything in this plan appears to contradict ADR-007, **ADR-007 wins** and the
plan must be amended.

## 5. Toolchain pins

Verified against the live repo (`pyproject.toml`, `docker-compose.yml`) at the
time of authoring. **No new runtime dependency is required** — the persistence
and async stack Phase 2 needs is already declared (and currently unused).

| Layer | Choice | Source (live repo) |
|---|---|---|
| Python | `>=3.12` | `pyproject.toml:8` |
| Web framework | FastAPI `>=0.115.0` (async-native) + uvicorn[standard] `>=0.30.0` | `pyproject.toml:10-11` |
| Validation models | Pydantic v2 `>=2.9.0`; `pydantic-settings>=2.5.0` | `pyproject.toml:12-13` |
| ORM / persistence | **SQLAlchemy `>=2.0.35` (async)** — already declared, currently unused | `pyproject.toml:14` |
| Migrations | **Alembic `>=1.13.0`** — already declared, currently unused | `pyproject.toml:15` |
| Postgres driver | **asyncpg `>=0.29.0`** | `pyproject.toml:16` |
| HTTP client | httpx `>=0.27.0` (for future Ollama/LLM ingress; not exercised in Phase 2) | `pyproject.toml:19` |
| Async tasks (optional) | redis `>=5.0.0` + celery `>=5.4.0` — declared, **not** wired in Phase 2 | `pyproject.toml:17-18` |
| Structured logging | structlog `>=24.4.0` | `pyproject.toml:21` |
| CLI framework | Typer `>=0.12.0` (extend existing `services/engine/cli.py`) | `pyproject.toml:22` |
| DB runtime | `postgres:16-alpine` (vero/vero/vero_lite); `redis:7-alpine` | `docker-compose.yml:2-3,19-20` |
| DB URL (async) | `postgresql+asyncpg://vero:vero@localhost:5432/vero_lite` | `services/api/config.py:18-21` | <!-- pragma: allowlist secret -->
| Test runner | pytest `>=8.3` + pytest-asyncio `>=0.24` (`asyncio_mode=auto`) + pytest-cov | `pyproject.toml:29-31,84` |
| Lint / type | ruff `target-version=py312` (E/F/W/I/B/UP/RUF/C90/N/S) + mypy `strict` w/ `pydantic.mypy` | `pyproject.toml:51-79` |
| Coverage | `[tool.coverage.run] source=["services"]`; `fail_under=70` | `pyproject.toml:89-95` |

**Pin note (carried from PLAN-003 J-1):** the SQL emitter maps `int → BIGINT`
(PLAN-003 §6.2 binding) though ADR-008 D3 narrative literally says `INTEGER`.
Any Phase 2 SQLAlchemy column types must match the **emitted** `schema.sql`
(BIGINT), not the ADR-008 narrative, if generated DDL and ORM models are to
co-exist (relevant to OQ-4 sub-question).

## 6. Component contracts

### 6.1 DataAdapter Protocol (`services/engine/data_adapter.py`)

Declare the Protocol **verbatim from ADR-007 D1**: `@runtime_checkable`,
`Protocol`, attribute `vertical_name: str`, and the four async methods
`fetch_objects(object_type, filter_expr=None, limit=1000) -> list[dict]`,
`fetch_links(link_type, from_pk=None, to_pk=None) -> list[dict]`,
`stream_events(event_type, since=None)` (async iterator), and
`health_check() -> dict`. The engine never instantiates a DataAdapter directly;
verticals register an implementation (§6.4).

Acceptance is structural (§7.1): a conforming class passes
`isinstance(impl, DataAdapter)` via `runtime_checkable`, and a deliberately
non-conforming class fails it.

### 6.2 Energy synthetic DataAdapter (`verticals/energy/data_adapter/`)

A synthetic implementation per ADR-006 §5 pattern #4 (Demo Data Generator =
per-vertical) and the energy README ("synthetic generator first; real adapter
once design partner agrees"). It deterministically produces `Asset`, `Site`,
and `OperationalEvent` shaped dicts matching `energy_v0.yaml`, plus
threshold-crossing events that the recommender (§6.5) can turn into Alerts. No
external network calls. Wording discipline: synthetic data uses abstract
identifiers only ("regional energy operator"); **no design-partner brand names
or internal codes** anywhere in the adapter or its fixtures.

### 6.3 RecommendedAction runtime envelope (`services/engine/actions.py`)

Implement the ADR-007 D2 Pydantic models exactly: `ReasoningStep`, `EntityRef`,
`AuditMetadata`, and `RecommendedAction` (fields: `id`, `title`, `description`,
`vertical`, `reasoning_trace`, `confidence` `[0.0, 1.0]`, `affected_entities`,
`suggested_handler`, `handler_payload`, `requires_approval=True`,
`approval_chain`, `audit_metadata`, `created_at`, `expires_at`).

⚠️ **This is the runtime envelope, distinct from the ontology entity
`RecommendedAction` in `energy_v0.yaml`** (which has `action_id`, `action_type`,
`confidence_score`, `status`, `parameters`, `alert_id`, `target_asset_id`).
PLAN-003 §8.5 says the ontology entity "mirrors" the envelope "at runtime" — but
the two field sets are not identical. **Resolved (OQ-1, §8, Cray 2026-05-21):**
the envelope is the in-flight runtime object; the ontology entity is the persisted
projection (map envelope → entity subset at the persistence boundary). Do **not**
unify the schemas.

### 6.4 Vertical registry (`services/engine/registry.py`)

A per-process registry keying `vertical_name → {adapter, handlers}`.
**Resolved (OQ-6, §8, Cray 2026-05-21):** explicit decorator/registration calls
(`register_adapter`, `register_handler`) — **not** entry-point packaging or
import-scan discovery. Revisit at vertical #2/#3 if dynamic discovery is warranted.

### 6.5 Rule-based recommender + minimal approval gate

`services/engine/recommender.py` turns an `Alert` (derived from a
threshold-crossing `OperationalEvent`) into a `RecommendedAction` via a
deterministic rule — **no LLM** (LLM hook deferred to ADR-010+, OQ-3). The
`reasoning_trace` carries `ReasoningStep`s of kind `rule_check`.

The **minimal approval gate** honours `requires_approval` and the ontology
entity's `status` lifecycle `proposed → approved → executed` (and `rejected`).
It does **not** implement the full audit framework (OQ-2). "Execute" invokes the
registered handler (a no-op/echo handler for energy in Phase 2).

### 6.6 Persistence (`services/db/` + Alembic)

**Resolved (OQ-4, §8, Cray 2026-05-21):** real persistence against
`postgres:16-alpine` using the already-declared SQLAlchemy 2.0 async + Alembic +
asyncpg stack; the first Alembic migration materialises the energy tables
consistent with the emitted `schema.sql` (BIGINT, per §5 pin note). ORM models
are **hand-authored** for Phase 2 (an "ORM emitter" is a later Rule-of-Three
candidate, §8.1). pgvector / Apache AGE / pg_trgm stay deferred to PLAN-002.

### 6.7 Three-layer wiring (`services/api/main.py`)

Wire ADR-007 D3/D4: ingress (`DataAdapter.fetch_*`) → semantic (typed
entities via generated Pydantic models) → action (`RecommendedAction` stream).
Add FastAPI routers exposing, at minimum: list/read object endpoints, list
recommendations, `POST .../approve`, `POST .../execute`. The existing `/health`
endpoint (`services/api/main.py`) is preserved.

## 7. Acceptance Criteria

All criteria use **Lesson #7 §3 reliable verification methods** — in-process
return probes, captured stderr/stdout summary lines, or behavioral side-effect
assertions. **No `echo $?`, no "expect exit N" wording anywhere** (Lesson #7 §4
forbidden patterns). API endpoints are exercised via `httpx.ASGITransport` /
FastAPI `TestClient` and asserted on **response JSON** (behavioral), never on a
shell exit code. pytest pass/fail is read from pytest's own
`N passed` / `N failed` summary line, not `$?`.

### 7.1 DataAdapter Protocol

- [ ] A conforming energy adapter satisfies `isinstance(adapter, DataAdapter)`
      (`runtime_checkable`) — asserted in-process in a pytest case.
- [ ] A class missing one async method fails the same `isinstance` check —
      asserted in-process (negative case).
- [ ] `await adapter.health_check()` returns a dict with a status key —
      behavioral assertion on the returned value.

### 7.2 Synthetic adapter behaviour

- [ ] `await adapter.fetch_objects("Asset")` returns a non-empty
      `list[dict]`; every dict validates against the generated energy `Asset`
      Pydantic model (behavioral: `Asset(**d)` constructs without raising).
- [ ] `stream_events("reading")` yields ≥1 threshold-crossing event suitable
      for Alert derivation — behavioral assertion on collected items.
- [ ] PD-5 wording grep across the new adapter + fixtures returns **0** hits for
      design-partner identifiers — assert the captured `grep -rilE` output line
      count is `0` (side-effect assertion, not exit code).

### 7.3 RecommendedAction envelope

- [ ] `RecommendedAction(**valid_payload)` constructs; `confidence` outside
      `[0.0, 1.0]` raises `ValidationError` — both asserted in-process.
- [ ] The envelope round-trips: `RecommendedAction.model_validate(
      action.model_dump())` equals the original — behavioral equality assertion.

### 7.4 Recommender + approval gate (the end-to-end loop)

- [ ] **read → recommend:** given a synthetic threshold-crossing event, the
      recommender returns a `RecommendedAction` with `requires_approval is True`,
      a non-empty `reasoning_trace`, and the ontology entity `status == "proposed"`
      — in-process assertion on the returned objects.
- [ ] **approve:** the approve transition moves `status` `proposed → approved`;
      approving an already-`executed`/`rejected` action raises a documented error
      — in-process assertion on the resulting `status`.
- [ ] **execute:** executing an `approved` action invokes the registered energy
      handler and moves `status` `approved → executed` — behavioral assertion on
      the handler side effect (e.g. a recorded call / returned receipt) and the
      final `status`.
- [ ] **full loop integration test:** one pytest case drives
      read → recommend → approve → execute and asserts the terminal `status` is
      `executed` and the persisted row (OQ-4) reflects it — behavioral.

### 7.5 API wiring

- [ ] `GET /health` still returns `{"status": "ok", ...}` (regression) — assert
      on response JSON via `TestClient`.
- [ ] The action-loop endpoints (list recommendations / approve / execute)
      return the expected status transitions — assert on response JSON and HTTP
      status codes, not on `$?`.
- [ ] OpenAPI schema (`GET /openapi.json`) lists the new routes — behavioral
      assertion that route paths are present in the parsed JSON.

### 7.6 Persistence (conditional on OQ-4 = "real persistence")

- [ ] `alembic upgrade head` against `postgres:16-alpine` creates the energy
      tables — behavioral: query `information_schema.tables` and assert the
      expected table names are present (not `$?`).
- [ ] An executed action's row is readable back with `status == "executed"` —
      behavioral round-trip assertion.

### 7.7 Project-wide invariants

- [ ] `ruff check services/` clean; `mypy --strict services/` clean — read the
      tools' own reported summary lines, not `$?`.
- [ ] `pytest` suite green — read pytest's `N passed` summary line.
- [ ] Coverage ≥70% on new `services/engine/` + `services/db/` code
      (`pytest --cov=services` report inspection) — **aspirational**, mirrors
      PLAN-003 R-8; surface the gap in closeout rather than block.

## 8. Open Questions — RESOLVED (Cray ruling 2026-05-21)

All six were adjudicated by Cray on 2026-05-21 per ADR-009 D1 Tier-1 rule #8;
each ruling **matched the Cowork recommendation**. They are now **binding** for
the Phase 2 kickoff dispatch.

- **OQ-1 — RESOLVED.** RecommendedAction is **two layers**: the ADR-007 D2
  envelope is the in-flight **runtime** object; the `energy_v0.yaml` entity is the
  **persisted projection** (map envelope → entity subset at the persistence
  boundary). Do **not** unify the schemas.
- **OQ-2 — RESOLVED.** **Minimal approval gate only** — honour `requires_approval`
  and the `proposed → approved → executed`/`rejected` transitions. The full audit
  framework (correlation-id propagation, `approval_chain` enforcement, immutable
  audit log) is **deferred to ADR-011+**.
- **OQ-3 — RESOLVED.** **Rule-based recommender** (e.g. threshold crossing →
  Alert → RecommendedAction) so the full loop runs end-to-end now. Real LLM
  reasoning lands with **ADR-010+**. Stated intent: prove the *whole pipe runs*
  first, then swap the "brain" — Phase 2 ships the rule stub, **not** a model call.
- **OQ-4 — RESOLVED.** **Real persistence** on base `postgres:16-alpine` using the
  declared SQLAlchemy 2.0 async + Alembic + asyncpg stack; **hand-author** the ORM
  models for Phase 2 (column types consistent with the emitted BIGINT DDL,
  §5 pin note). pgvector / Apache AGE / pg_trgm stay deferred to **PLAN-002**.
- **OQ-5 — RESOLVED.** **No mapping layer** in Phase 2 — the synthetic adapter
  returns canonical-shaped dicts directly. Introduce dbt/SQLMesh only when a real
  (non-synthetic) raw data source exists.
- **OQ-6 — RESOLVED.** **Explicit decorator/registration** (`register_adapter`,
  `register_handler`) — no entry-point packaging, no import-scan discovery.
  Revisit at vertical #2/#3 if dynamic discovery becomes warranted.

### 8.1 Deferred-but-foundational — revisit register (per Cray note 2026-05-21)

Cray flagged that every "do the simple thing first" choice above is a **genuine
production-foundational** capability, not throwaway scaffolding — each MUST be
picked back up at the right time, not silently forgotten. Tracked here as explicit
revisit triggers so the deferral is auditable rather than lost:

| Deferred (Phase 2 simplification) | Why it's foundational | Revisit trigger | Lands in |
|---|---|---|---|
| Rule-based recommender (OQ-3) | The reasoning "brain" is the actual product value; rules are a stand-in | LLM reasoning-hook ADR opened | ADR-010+ |
| Minimal approval gate (OQ-2) | Real ops need who-approved / audit trail / non-repudiation | First real design-partner data, or compliance review (PDPA — CLAUDE.md §8) | ADR-011+ |
| No mapping layer (OQ-5) | Real raw sources are messy; canonicalisation becomes mandatory | First non-synthetic data source connected | later batch (dbt/SQLMesh) |
| Hand-authored ORM (OQ-4) | DDL↔ORM drift is a real risk as the ontology grows | 3rd vertical, or DDL/ORM parity test (R6) starts failing repeatedly | "ORM emitter" Rule-of-Three candidate |
| Base Postgres only (OQ-4) | Vector search + graph overlay are core to the OCT vision | Semantic query / graph features prioritised | PLAN-002 |
| Explicit registry (OQ-6) | Many verticals need cheaper onboarding (ADR-006 D3 L2/L3) | vertical #2/#3, or `new-vertical` generator work | ADR-006 D3 L2 |

**Follow-on TODO for Code (Cowork cannot edit STATUS.md per ADR-009 D2):** add a
"PLAN-0005 deferred-foundational revisit register" entry to `docs/STATUS.md`
Active TODOs (or mint a short lessons/ note) so these six triggers survive beyond
this plan doc and surface at the right batch boundary.

## 9. Worktree + Lesson #3 prevention

Phase 2 is multi-file buildable Python (engine modules + per-vertical adapter +
API routers + tests + a migration) → **worktree mode ON** (CLAUDE.md §11 +
Lesson #3), as Phase 1 was. Apply the Lesson #3 prevention checklist, mirroring
PLAN-003 §10:

- **Pre-flight ownership sweep:** `find .git .claude -user root | wc -l` before
  the first `git add`; sweep if non-zero (B1/B2 cascade).
- **Shell-context guard:** `uname -s` must equal `Linux` before any `uv`
  invocation (A3 destructive subtrap); WSL-native `uv` only.
- **First-commit FS leftover:** `verticals/*/generated/` is gitignored;
  sandbox-root writes there are expected B3-class leftovers — accept, do not
  chase. (Phase 2 adds no new gitignored output dir unless OQ-4 introduces an
  Alembic versions cache.)
- **Pre-commit hook on each commit:** detect-secrets + ruff + mypy via
  `PATH="$PWD/.venv/bin:$PATH" git commit -F …` to bypass the hard-coded POSIX
  `INSTALL_PYTHON` trap (Lesson #3 §A3).

The Phase 2 kickoff dispatch (separate round) carries the full pre-flight
sequence as commands; this plan documents the rationale.

## 10. Risks and known unknowns

- **R1 — RecommendedAction shape drift (OQ-1).** If Cray picks (b) "unify", the
  ontology `energy_v0.yaml` entity changes and the engine must regenerate; that
  is a larger blast radius than (a). Resolve OQ-1 before kickoff.
- **R2 — Persistence scope creep (OQ-4).** Standing up SQLAlchemy + Alembic is
  the heaviest single piece. If it threatens the time budget, the in-memory
  fallback keeps the action loop demonstrable and defers DB work — surface
  early, do not silently expand.
- **R3 — Approval/audit boundary (OQ-2).** Temptation to build "just a bit" of
  the audit framework will leak ADR-011+ scope into Phase 2. The §3.3 cut line
  is binding once Cray rules on OQ-2; anything beyond is a stop-and-ask.
- **R4 — Async test ergonomics.** `asyncio_mode=auto` is set; async adapter +
  async SQLAlchemy sessions need careful fixture scoping. Mitigation: in-process
  `await` assertions per §7, no reliance on harness exit codes (Lesson #7).
- **R5 — Handler registry global state.** A per-process registry (OQ-6 rec) can
  leak between tests; mitigation: a registry-reset fixture.
- **R6 — Generated-DDL vs ORM divergence.** If ORM models are hand-authored
  (OQ-4 rec) they can drift from the emitted `schema.sql`. Mitigation: a test
  asserting table/column parity between the migration and the generated DDL.

## 11. Verification

"Done" for Phase 2 means: all §7 acceptance checkboxes pass via Lesson #7 §3
reliable methods; the full read → recommend → approve → execute loop is green in
an integration test; `ruff`/`mypy --strict`/`pytest` are clean (read from their
own summary lines); and the closeout names the final module/endpoint set so
future readers can map this plan to the implementation (mirroring PLAN-003 R4).
Per ADR-009 D2, **Code** runs the verification and commits; Cowork holds no
execution or commit authority.

## 12. References

### Architectural anchors
- `docs/adr/0006-vertical-plugin-architecture.md` (D1; §5 patterns #2/#3/#4)
- `docs/adr/0007-oct-engine-contracts.md` (D1/D2/D3/D4 — authoritative)
- `docs/adr/0008-yaml-ontology-specification.md` (D5 codegen contract consumed here)
- `CLAUDE.md` §3 (three-layer mental model)

### Plans
- `docs/plans/0003-ontology-engine.md` (Phase 1; §2.1, §3.3, §8.5, §10)
- `docs/plans/0000-template.md` (PLAN doc shape)
- PLAN-002 (custom Postgres image — undrafted; OQ-4 dependency)

### Lessons
- `docs/lessons/0007-harness-exit-code-artifact.md` (§3 reliable verification methods)
- `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md` (worktree prevention checklist)

### Live-repo fact-pack (verified at authoring)
- `pyproject.toml` (deps + tool config — toolchain pins §5)
- `docker-compose.yml` (postgres:16-alpine + redis:7-alpine)
- `services/api/main.py` (current `/health`-only app), `services/api/config.py`
  (async DB URL), `services/engine/{cli,code_generator,ontology_validator,errors}.py`
  (Phase 1 surfaces Phase 2 extends), `verticals/energy/ontology/energy_v0.yaml`
  (6 object types + 7 link types)

---

*PLAN-0005 (Phase 2) — Draft authored by Cowork (Tier 0 + Tier 1) 2026-05-21.
Status moves to Ready for execution on Cray adjudication of §8 OQ-1..OQ-6 + §1.1
numbering confirmation + Code commit. Phase 2 kickoff dispatch follows as a
separate round.*

*AI-assisted per project convention.*
