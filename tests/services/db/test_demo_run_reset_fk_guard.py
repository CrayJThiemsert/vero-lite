"""PLAN-0110 AC-6 — a second child of ``pipeline_runs`` cannot arrive silently.

The same guard shape PLAN-0105 AC-5 built for the ``repair_case`` graph, applied to
the run graph this PLAN's reset deletes from — and it is needed for the same measured
reason. The reference graph around ``pipeline_runs`` is **two-shaped**, and the two
shapes fail in opposite directions:

* ``step_results.run_id`` holds a real ForeignKey with no ``ondelete``, so a bare
  parent delete raises **loudly**;
* ``audit_log.run_id`` and ``repair_case_run_link.run_id`` reference ``run_id`` with
  **no FK at all**, so deleting a run affects them **silently** — no error, no
  cascade, nothing reddens.

A review that walks backwards from the FK declarations finds the first shape and
misses the second entirely. This guard walks FORWARDS over the live ``Base.metadata``
and compares it against the reset module's **declared** classification, so a new
``run_id``-bearing table reddens CI until a human classifies it, whichever shape it
takes.

⚠️ Every expected set is read from the ARTIFACT (``services/db/demo_run_reset.py``),
never re-listed here. A guard holding its own copy of the thing it checks agrees with
itself forever, and that is the one failure mode a completeness guard cannot have.
"""

from __future__ import annotations

import sqlalchemy as sa

# Imported for its side effect: ``Base.metadata`` is populated by IMPORT, so a process
# that never imported an ORM module has no row for it. Mirrors ``alembic/env.py`` —
# without this the walk below would be quietly incomplete and every assertion would
# pass by inspecting an empty world.
import tests.db_support  # noqa: F401
from services.db.base import Base
from services.db.demo_run_reset import (
    FK_CHILD_DELETION_ORDER,
    FK_CHILD_TABLES,
    NO_FK_REFERENCERS,
    ROOT_TABLE,
)

_RUN_FK_TARGET = "pipeline_runs.run_id"


def _tables_with_a_run_id_column(metadata: sa.MetaData) -> set[str]:
    return {t.name for t in metadata.tables.values() if "run_id" in t.c}


def _tables_with_an_fk_to_pipeline_runs(metadata: sa.MetaData) -> set[str]:
    return {
        t.name
        for t in metadata.tables.values()
        for fk in t.foreign_keys
        if fk.target_fullname == _RUN_FK_TARGET
    }


def test_the_walk_is_not_vacuous() -> None:
    """A guard over an empty metadata passes over nothing and reports success.

    ``Base.metadata`` is populated by import side effect, so this is a live hazard
    rather than a hypothetical: a future refactor dropping the ``tests.db_support``
    import above would make every assertion below pass by walking an empty world.
    """
    assert len(Base.metadata.tables) > 1
    assert ROOT_TABLE in Base.metadata.tables, "the root table itself must be in the walk"
    assert _tables_with_an_fk_to_pipeline_runs(
        Base.metadata
    ), "the FK walk found nothing at all — it is not reading the live metadata"


def test_the_declared_fk_children_equal_the_fks_the_metadata_declares() -> None:
    """Set EQUALITY, in both directions, with each direction named in the message.

    A subset check would pass while the reset silently skipped a child (rows left
    behind, then a ForeignKeyViolation on the run delete); a superset check would pass
    while the reset deleted from a table that no longer references runs at all.
    """
    declared = set(FK_CHILD_TABLES)
    actual = _tables_with_an_fk_to_pipeline_runs(Base.metadata)
    assert actual == declared, (
        "the demo reset's declared FK children have drifted from the metadata. "
        f"Declares an FK to pipeline_runs but the reset never clears it: "
        f"{sorted(actual - declared)}. Declared by the reset but no longer an FK "
        f"child: {sorted(declared - actual)}."
    )


def test_the_deletion_order_lists_each_child_exactly_once() -> None:
    """The ORDER is the thing that executes; the SET is what the guard above checks.
    A duplicate or a missing entry would make the two disagree about the same table."""
    assert len(FK_CHILD_DELETION_ORDER) == len(set(FK_CHILD_DELETION_ORDER))
    assert set(FK_CHILD_DELETION_ORDER) == set(FK_CHILD_TABLES)


def test_every_run_id_bearing_table_is_classified() -> None:
    """The silent half — the one a backwards walk cannot see.

    Every table carrying a ``run_id`` column is either the root, a declared FK child,
    or explicitly listed in ``NO_FK_REFERENCERS`` with a policy. An unclassified one
    is a table the reset either orphans or ignores with nobody having decided which.
    """
    classified = {ROOT_TABLE} | set(FK_CHILD_TABLES) | set(NO_FK_REFERENCERS)
    unclassified = _tables_with_a_run_id_column(Base.metadata) - classified
    assert not unclassified, (
        "these tables carry run_id but the demo reset classifies neither their FK "
        f"shape nor a retention policy for them: {sorted(unclassified)}"
    )


def test_the_audit_log_is_classified_retain() -> None:
    """The one policy that is a rule rather than a judgement call.

    ``audit_log`` is never deleted by any reset — the chain must outlive every demo
    generation, and ``verify_chain`` walks it by ``audit_id`` without reading runs at
    all. Pinned as its own assertion so that flipping it to DELETE is a red test and
    not a diff nobody reads.
    """
    assert NO_FK_REFERENCERS["audit_log"].startswith("RETAIN")
    assert "audit_log" not in FK_CHILD_TABLES
