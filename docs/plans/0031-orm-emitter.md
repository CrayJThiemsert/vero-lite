# PLAN-0031: ORM emitter — the 6th generator artifact (Group B / B1)

**Status:** Draft
**Owner:** both (Cowork/Tier-1 authors this PLAN; Code commits + executes per ADR-009 D1/D2)
**Created:** 2026-06-18
**Related ADRs:** ADR-006 (D4 Rule of Three — the trigger now met on 3 verticals; D3 plugin maturity); ADR-008 (D3 YAML→type mappings + D5 "the engine emits N artifacts per vertical"); ADR-007 (D2 runtime envelopes — **unaffected**)
**Related Plans:** PLAN-0003 (the ontology engine + the existing 5 emitters); PLAN-0005 (§6.4 / OQ-4 "Phase 2 hand-authors the ORM"; **§8.1 register: "hand-authored ORM → 'ORM emitter' Rule-of-Three candidate"**; C-1 "ORM tracks the *emitted* DDL"; R6 DDL↔ORM drift risk); PLAN-0019 (SD-A2 — the engine-infra ORM tables excluded from the parity guard)

> **Disclosure (ADR-012 D4.3).** Originated by **Code's** session-67 dispatch
> (`.claude/handoffs/session-67/2026-06-18-1453-code-dispatch-groupb-foundation.md`)
> on Cray's Group-B trigger decision (Rule-of-Three met). Drafted (uncommitted) by
> **Cowork** (Tier-1, ADR-009 D1). The trigger, the gap evidence, and the build
> scope were **originated in Code's dispatch + PLAN-0005 §8.1**, not in a Cowork
> free-form self-deliberation — **not** an ADR-012 D4.3 self-deliberation case.
> Reviewers: **Cray** (PLAN ratification) + **Code** (PR review). Cowork re-verified
> every cited code line / file / symbol against the live repo this session
> (fact-pack-first, ADR-009 D1 Tier-1 rule #4).

> **No ADR gate.** B1 is an **additive generator artifact** — it adds a 6th
> `emit_*` to an existing, ADR-008-sanctioned codegen surface. It carries **no**
> ADR-006-area governance touch (that is B2 / ADR-0023). PLAN-0031 can ratify +
> ship **independently of and before** ADR-0023 (see SD-B in the completion
> handoff).

---

## Goal

Add a **6th emitter** (`emit_orm`) to `services/engine/code_generator.py` that
generates the **SQLAlchemy ORM** from the ontology YAML, so the ontology is the
**single source of truth** for the ORM as it already is for the other five
artifacts. Today the SQLAlchemy ORM (`services/db/models.py`) is **hand-authored**
and tracks the emitted DDL only by discipline; a property change must be applied in
several places (regenerate DDL + hand-edit `models.py` + a migration), and the
drift is caught **after-the-fact** by `tests/services/db/test_schema_parity.py`
(e.g. session-61 `measured_kind` touched ontology→DDL + `models.py` + Alembic
`0003`). Generating the ORM makes parity hold **by construction** — no drift, no
double-maintenance — and is the **PLAN-0005 §8.1 "ORM emitter" Rule-of-Three
candidate**, whose trigger ("3rd vertical / DDL↔ORM parity-test drift") has now
fired.

## The gap + the anchors (live code, re-verified session 67)

- `services/engine/code_generator.py` emits **5** artifacts —
  `emit_pydantic` (`:111`), `emit_sql` DDL (`:184`), `emit_jsonschema` (`:241`),
  `emit_mcp` (`:296`), `emit_typescript` (`:334`) — wired in `generate_all`
  (`:360-369`), each a pure-Python structured builder (no Jinja2; the project is
  dep-conservative), deterministic + ordered by `object_types` insertion order.
  `generate_all` writes `models.py` (**Pydantic**), `schema.sql`, `schema.json`,
  `mcp_tools.json`, `types.ts` into `output_dir`.
- **The SQLAlchemy ORM is hand-authored** at `services/db/models.py` — 6 classes
  for the energy ontology (`Site`, `Asset`, `OperationalEvent`, `Alert`,
  `RecommendedAction`, `AlertEventLink`). Its own docstring (`:1-17`) states:
  *"Phase 2 hand-authors the ORM (an 'ORM emitter' is a later Rule-of-Three
  candidate, PLAN-0005 §8.1). Column types track the emitted DDL … not the ADR-008
  D3 narrative — see PLAN-0005 C-1."* CHECK constraints are intentionally omitted
  (enum validity at the Pydantic layer).
- `tests/services/db/test_schema_parity.py` — the **drift guard**: 4 tests assert
  the ORM (via `Base.metadata`, **scoped to the `services/db/models` module**) ==
  the emitted DDL (`emit_sql(load_doc(energy_v0.yaml))`) on **table names**
  (`:99`), **column names** (`:104`), **column types** (`:112`, C-1), and
  **indexes** (`:154`). It deliberately **excludes** the cross-vertical engine-infra
  tables (`pipeline_runs` / `step_results`) — PLAN-0019 SD-A2.

> The parity test already passing proves `emit_sql` produces exactly the 6 energy
> tables the hand-authored ORM declares — so an ORM emitter consuming the **same**
> `load_doc(energy_v0.yaml)` can reproduce the ORM, and parity then holds by
> construction.

## Type mapping (the ORM emitter must match the DDL emitter + the current ORM)

| YAML type | DDL (`emit_sql`) | SQLAlchemy ORM (`emit_orm` target — matches `services/db/models.py`) |
|---|---|---|
| `string` | `TEXT` | `Mapped[str]` / `Text` |
| `int` | `BIGINT` | `Mapped[int]` / `BigInteger` |
| `float` | `DOUBLE PRECISION` | `Mapped[float]` / `Double` |
| `bool` | `BOOLEAN` | `Mapped[bool]` / `Boolean` |
| `timestamp` | `TIMESTAMPTZ` | `Mapped[datetime]` / `DateTime(timezone=True)` |
| `date` | `DATE` | `Mapped[date]` / `Date` |
| `enum` | `TEXT CHECK (...)` | `Mapped[str]` / `Text` *(CHECK omitted — enum validity at the Pydantic layer; parity covers types, not constraints — `models.py:14-17`)* |
| `json` | `JSONB` | `Mapped[dict[str, Any]]` / `JSONB` (postgresql dialect) |
| `ref` | `TEXT REFERENCES <t>(<pk>)` | `Mapped[str]` / `Text, ForeignKey("<t>.<pk>")` |

Plus: `primary_key` → `mapped_column(..., primary_key=True)`; `required` →
`nullable=False` (and `Mapped[T]`); optional → `Mapped[T | None]`
(`mapped_column` nullable by default); each **`ref`** column → an
`Index("idx_<table>_<col>", "<col>")` in `__table_args__` (mirrors `emit_sql`'s
`CREATE INDEX idx_<table>_<col>` and the existing ORM `__table_args__`).

## Decided / surfaced design points

- **B1-DP-1 — generated-ORM output location (SURFACED; Cowork recommends a
  per-vertical `generated/` file re-exported by `services/db/models.py`).** The
  other 5 emitters write under `verticals/<ns>/generated/`; the SQLAlchemy ORM
  currently lives **centrally** at `services/db/models.py` (imported by
  `services/db/` + the parity test). Options: **(a)** emit to
  `verticals/<ns>/generated/orm.py` and make `services/db/models.py` a thin
  **re-export** of the energy generated ORM (consistent with the other emitters;
  generalises per-vertical — Rule of Three); **(b)** emit directly to
  `services/db/models.py` (central; least import churn but a non-`generated/`
  output path breaks the emitter-output convention). *Cowork recommends (a).*
  Either way the `Base` is the shared `services/db/base.Base` (the ORM must bind to
  one metadata). **Code/Cray confirm at review** — it touches the parity-test
  import path.
- **B1-DP-2 / SD-D — ORM emitter ↔ Alembic (SURFACED; Cowork recommends: emitter
  generates the ORM model only).** The emitter's job is the **ORM model**, not the
  migration. A live-DB schema change still needs an Alembic migration — kept
  **hand-written or `alembic revision --autogenerate`** *from* the now-generated
  ORM. Generating migrations is **out of scope** (migrations encode deltas + data
  moves, not just the current shape). B1 removes the `models.py` hand-edit, **not**
  the migration step. *Cray/Code confirm.*

## Acceptance Criteria

- [ ] **AC-1 — A 6th emitter.** `emit_orm(doc: dict[str, Any], output_path: Path)
      -> Path` generates SQLAlchemy 2.0 declarative models (`Mapped` /
      `mapped_column`, bound to `services/db/base.Base`) for **every**
      `object_type` in the ontology, as a pure-Python structured builder (no
      Jinja2), **deterministic** and ordered by `object_types` insertion order —
      mirroring the existing five emitters.
- [ ] **AC-2 — Type/constraint mapping matches the DDL + current ORM.** Column
      types, `primary_key`, `nullable`, `ForeignKey` (for `ref`), and the
      `Index("idx_<table>_<col>", ...)` for each `ref` column reproduce the
      mapping table above — i.e. the generated energy ORM is **schema-equivalent**
      to the current hand-authored `services/db/models.py`.
- [ ] **AC-3 — Wired into `generate_all` + reachable via the engine CLI.**
      `generate_all` gains `outputs["orm"] = emit_orm(doc, output_dir / <name>)`.
      Regeneration is driven through the engine CLI (**`uv run vero-lite`**, **not**
      `python -m` — the latter is a silent no-op); verify via the CLI's `OK:`
      output **and** the regenerated artifact's mtime (dispatch §1).
- [ ] **AC-4 — Parity holds by construction.** `test_schema_parity` (tables /
      columns / types / indexes) passes against the **generated** ORM. The test is
      **retained** (now guarding generated-ORM ↔ generated-DDL emitter divergence,
      still a real guard) and **not** weakened. No regression vs the current
      hand-authored ORM schema.
- [ ] **AC-5 — `services/db/models.py` reconciliation (B1-DP-1).** Per the chosen
      option, `services/db/` imports + the parity-test import keep working. The
      **engine-infra** ORM tables (`pipeline_runs` / `step_results`) stay
      hand-authored and **excluded** from the parity guard (PLAN-0019 SD-A2) — the
      emitter is **per-vertical-ontology**, not engine-infra.
- [ ] **AC-6 — Quality bar (CLAUDE.md §8), offline, deterministic.** Type hints +
      tests + **ruff clean + `mypy --strict` clean**; fully **offline** (no
      host-state — pure codegen + metadata/text compares); same input → **byte-
      identical** output (like the other emitters).
- [ ] **AC-7 — No regression.** The 5 existing emitters and `generate_all`'s
      existing outputs are unchanged; the full `uv run pytest -q` suite stays green
      (baseline stated at execution — STATUS records 1608 passed / 22 skipped).

## Out of Scope

- ❌ **Generating Alembic migrations** (B1-DP-2 / SD-D) — emit the ORM model only;
  migrations stay hand-written / `--autogenerate`.
- ❌ **Engine-infra ORM** (`pipeline_runs` / `step_results`) — cross-vertical,
  hand-authored, excluded from the parity guard (PLAN-0019 SD-A2).
- ❌ **B2 registry auto-discovery** — separate PLAN-0032 (gated on ADR-0023).
- ❌ **CHECK constraints in the ORM** — intentionally omitted (`models.py:14-17`);
  enum validity at the Pydantic layer; parity covers types, not constraints.
- ❌ **New vertical (#4), UI, NL-query, partner data** — engine-internal only.

## Steps

### Step 1 — `emit_orm` in `code_generator.py`

Add `emit_orm(doc, output_path)` beside the other emitters (mirror
`emit_pydantic`'s structured-builder shape). Build, per `object_type`: the class
header (`class <Obj>(Base):`, `__tablename__ = _snake(<Obj>)`), each
`mapped_column` from the type map (AC-2), `primary_key=True` on the PK, `nullable`
from `required`, `ForeignKey` for `ref`, and `__table_args__` with an
`Index("idx_<table>_<col>", "<col>")` per `ref`. Reuse the existing `_snake` +
the `ref`-target/`primary_key` resolution `emit_sql` already uses (`:161-166`).
Emit the "do not edit by hand" header + the needed imports (`Mapped`,
`mapped_column`, the SQLAlchemy types used, `JSONB` when any `json`,
`ForeignKey`/`Index` when any `ref`, and `Base`). (AC-1, AC-2, AC-6)

### Step 2 — Wire into `generate_all` + confirm the CLI

Add `outputs["orm"] = emit_orm(doc, output_dir / <orm-filename per B1-DP-1>)`.
Confirm the engine CLI (`uv run vero-lite`) regenerates it; verify `OK:` + mtime
(AC-3).

### Step 3 — Reconcile `services/db/models.py` (B1-DP-1)

Apply the ratified B1-DP-1 option (recommended: emit
`verticals/energy/generated/orm.py`; make `services/db/models.py` re-export it).
Keep `services/db/` imports + the parity-test import working; the engine-infra
tables stay where they are (AC-5).

### Step 4 — Tests

(i) Retain + re-point `test_schema_parity` to the generated ORM (AC-4). (ii) Add a
`emit_orm` **unit test** (a small fixture ontology → assert the generated classes,
column types, PK/nullable, FK, and indexes) alongside the other emitter tests in
`tests/services/engine/`. Offline; deterministic-output assertion (AC-6).

### Step 5 — Gate

`ruff` + `mypy --strict` clean; `uv run pytest -q` green vs the stated baseline
(AC-6, AC-7).

### Step 6 — Handback → Code commits + executes

Hand the uncommitted draft path back to Code. Code reviews, commits this PLAN via
a `docs(plans):` chore PR (ADR-009 D2; CLAUDE.md §7), executes on a `feat/*`
branch + PR (offline-only), reconciles `docs/STATUS.md`, then on completion
`git mv docs/plans/0031-*.md docs/plans/done/`.

## Verification

- **Parity (AC-4):** `test_schema_parity` green against the generated ORM —
  tables, columns, types (C-1), and indexes all match `emit_sql` by construction;
  the guard is retained, not relaxed.
- **No-regression (AC-7):** the 5 existing emitter outputs are byte-unchanged; the
  full suite is green vs baseline.
- **Determinism (AC-6):** regenerating twice yields byte-identical output.
- **No host-state at any point** — pure codegen + offline tests (CLAUDE.md §8).

## Surfaced decisions (SD-N) — for Cray/Code to adjudicate

- **B1-DP-1 — generated-ORM output location.** (a) per-vertical
  `verticals/<ns>/generated/orm.py` re-exported by `services/db/models.py`
  *(Cowork recommends)* vs (b) emit directly to the central `services/db/models.py`.
  Touches the parity-test import path → Code/Cray confirm at review.
- **SD-D / B1-DP-2 — ORM emitter ↔ Alembic.** Emitter generates the **ORM model
  only** *(Cowork recommends)*; migrations stay hand-written / `--autogenerate`.
  Confirm migrations remain out of scope.

## References

- **Code anchors (live, re-verified this session):**
  `services/engine/code_generator.py` (`emit_pydantic` `:111`, `emit_sql` `:184`,
  `emit_jsonschema` `:241`, `emit_mcp` `:296`, `emit_typescript` `:334`,
  `generate_all` `:360-369`; `_snake` `:65`, the `ref`/PK resolution `:161-166`);
  `services/db/models.py` (the hand-authored ORM + its `:1-17` docstring naming the
  ORM-emitter candidate); `services/db/base.py` (`Base`);
  `tests/services/db/test_schema_parity.py` (`:99`/`:104`/`:112`/`:154` the four
  parity tests; the engine-infra exclusion `:23-37`).
- **Governance / triggers:** ADR-006 D4 (Rule of Three) + D3 (plugin maturity);
  ADR-008 D3 (type mappings) + D5 (emitters); PLAN-0005 §6.4 / OQ-4, **§8.1
  register** (the ORM-emitter trigger), C-1 (ORM tracks emitted DDL), R6 (drift
  risk); PLAN-0019 SD-A2 (engine-infra exclusion); CLAUDE.md §1 (semantic layer =
  the moat), §6 (Plan Flow), §8 (code quality; no host-state); ADR-009 D1/D2;
  ADR-012 D4.3.
- **Dispatch + roadmap:**
  `.claude/handoffs/session-67/2026-06-18-1453-code-dispatch-groupb-foundation.md` §1;
  `.claude/handoffs/session-67/2026-06-18-0938-code-session67-roadmap-sequencing-handoff.md`
  §"Phase B / B1".

---

*PLAN-0031, the ORM emitter (Group B / B1 — the 6th generator artifact). Drafted
by Cowork (Tier-1, ADR-009 D1); Code reviews, commits (ADR-009 D2), and executes;
Cray ratifies. Engine-internal; offline-only build (no host-state); the 5 existing
emitters + `test_schema_parity` not regressed (parity held by construction).
AI-assisted (Claude, Cowork session); no `Co-Authored-By` per CLAUDE.md §7.*
