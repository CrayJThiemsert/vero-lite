# Runbook — Alembic migrations from the generated ORM (autogenerate workflow)

> PLAN-0049 Step 5 (SD-5, ratified 2026-07-04). This is the **documented
> workflow + hand-verify** disposition: ship the `alembic revision
> --autogenerate` workflow, hand-verify it against a known migration, and add a
> CI drift guard. A `vero-lite migrate` CLI wrapper is deferred (SD-5) — promote
> only if friction warrants.

## When this applies

Only when an ontology **content change alters the DB schema** of a vertical that
has a **committed ORM** — i.e. **energy** today (`services/db/models.py`, the
only entry in `_ORM_COMMITTED_DEST`). Changes that do **not** touch the DB
schema need no migration:

- **Enum value additions** (e.g. `asset_type += feeder`) — enums store as `Text`;
  the value space lives in the generated Pydantic layer + `schema.sql` CHECK, not
  the DB column type. No migration.
- **`quantity_bindings` / `measured_kind` metadata** — ontology metadata, not DB
  columns. No migration.
- **supply_chain and other verticals with no committed ORM** (SD-3) — their
  generated ORM lands in the gitignored `verticals/<v>/generated/orm.py`; there
  are no DB tables/migrations for them. `alembic` is energy-only.

A **new/removed/retyped column or table** (e.g. the Step-1 `Asset.rated_current_a`
add) **does** need a migration.

## The workflow

From the repo root, with the dev venv active and the dev DB reachable:

1. **Edit the ontology YAML** (`verticals/<vertical>/ontology/<vertical>_v0.yaml`).
2. **Regenerate** the committed ORM (+ the gitignored reference artifacts):

   ```
   uv run vero-lite generate energy
   ```

   This rewrites `services/db/models.py` from the ontology (do not hand-edit it —
   it is generated).
3. **Draft the migration** from the ORM↔DB diff:

   ```
   uv run alembic revision --autogenerate -m "asset rated_current_a"
   ```

   `alembic/env.py` sets `target_metadata = Base.metadata` and `compare_type=True`,
   so autogenerate detects added/removed columns **and** type changes.
4. **Hand-review the draft.** Autogenerate emits *"please adjust"* — it is a
   draft, not gospel. Check the column type / nullability / naming, delete any
   spurious diff, and renumber the file into the `NNNN_slug.py` house style
   (`down_revision` = the prior head). Enum CHECK constraints are intentionally
   omitted (parity guards types, not constraints — see `emit_orm`).
5. **Apply + confirm no residual drift:**

   ```
   uv run alembic upgrade head
   uv run alembic check      # -> "No new upgrade operations detected."
   ```
6. **Commit** the migration + the regenerated `services/db/models.py` together
   with the ontology edit (see `tests/services/db/test_schema_parity.py` — it
   re-checks ORM↔DDL parity by construction).

## CI drift guard

`.github/workflows/ci.yml` runs `alembic check` immediately after `alembic
upgrade head` on every PR. If a PR changes the generated ORM (via an ontology
edit) without the matching migration, `alembic check` autogenerates a non-empty
diff and **fails the gate** — the "migration was forgotten" tripwire.

## Hand-verify record — migration `0009` (PLAN-0049 Step 1)

Verified 2026-07-04 that `alembic revision --autogenerate` reproduces the
hand-authored `0009_asset_rated_current_a.py`. Procedure: with the ORM carrying
`Asset.rated_current_a`, temporarily removed `0009` from `alembic/versions/`,
set the DB to `0008`, and ran autogenerate. The generated body was:

```python
def upgrade() -> None:
    op.add_column('asset', sa.Column('rated_current_a', sa.Double(), nullable=True))

def downgrade() -> None:
    op.drop_column('asset', 'rated_current_a')
```

This matches the hand-authored `0009` exactly (the hand-authored form omits the
explicit `nullable=True`, which is the SQLAlchemy default — semantically
identical). The throwaway revision was deleted and `0009` restored. Conclusion:
the autogenerate workflow is faithful for the column-add case; hand-review
remains required for naming/renumbering and to strip any spurious diff.
