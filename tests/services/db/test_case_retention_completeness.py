"""PLAN-0105 Step 4 / AC-5 — the eighth table cannot arrive silently.

The reference graph around ``repair_case`` is **two-shaped**, and the shapes fail
in opposite directions: six children hold a real ForeignKey and none declares
``ondelete``, so a bare parent delete raises **loudly**; ``repair_case_run_link``
references ``case_id`` with **no FK at all**, so deleting a case orphans its rows
**silently**. A review that walks backwards from the FK declarations finds the
six and misses the seventh — which is exactly how the seventh was nearly missed.

This guard walks FORWARDS instead: over the live ``Base.metadata``, comparing it
against the sweep module's **declared** classification sets. A new
``case_id``-bearing table reddens CI until a human classifies it, whichever shape
it takes — and that is needed under both SD-1 options, because a no-FK eighth
table orphans under ``CASCADE`` just as happily.

⚠️ The declared sets are read from the ARTIFACT (`services/db/repair_case_retention.py`),
never re-listed here. A guard holding its own copy of the thing it checks agrees
with itself forever.

⚠️ Placed under ``tests/services/db/`` rather than the ``tests/db/`` the PLAN's
Step 4 names, matching where the repair-case DB tests already live
(`tests/services/db/test_repair_case_migration.py`, and Step 1's own module).
"""

from __future__ import annotations

import sqlalchemy as sa

# Imported for its side effect: ``Base.metadata`` is populated by IMPORT, so a
# process that never imported an ORM module has no row for it. This helper's
# import block mirrors ``alembic/env.py`` — without it the walk below would be
# quietly incomplete and the guard would pass over tables that exist.
import tests.db_support  # noqa: F401
from services.db.base import Base
from services.db.repair_case_retention import (
    FK_CHILD_TABLES,
    NO_FK_REFERENCERS,
    ROOT_TABLE,
)

_CASE_FK_TARGET = "repair_case.case_id"


def _tables_with_a_case_id_column(metadata: sa.MetaData) -> set[str]:
    return {t.name for t in metadata.tables.values() if "case_id" in t.c}


def _tables_with_an_fk_to_repair_case(metadata: sa.MetaData) -> set[str]:
    return {
        t.name
        for t in metadata.tables.values()
        for fk in t.foreign_keys
        if fk.target_fullname == _CASE_FK_TARGET
    }


def test_the_walk_is_not_vacuous() -> None:
    """A guard over an empty metadata passes over nothing and reports success.

    ``Base.metadata`` is populated by import side effect, so this is a live
    hazard rather than a hypothetical: a future refactor that drops the
    ``tests.db_support`` import above would make every assertion below pass by
    walking an empty world.
    """
    assert len(Base.metadata.tables) > 1
    assert ROOT_TABLE in Base.metadata.tables, "the root table itself must be in the walk"


def test_ac5i_the_declared_fk_children_equal_the_fks_the_metadata_declares() -> None:
    """Set EQUALITY, in both directions.

    A subset check would pass while the sweep silently skipped a table (rows
    left behind, then a ForeignKeyViolation on the parent delete); a superset
    check would pass while the sweep deleted from a table that no longer
    references cases at all.

    ⚠️ The two directions are spelled out in the message rather than left to a
    bare ``==``: a set comparison of eight near-identical ``repair_case_*`` names
    is truncated by pytest to `{'repair_case...e_task_event'}` on both sides,
    which is a RED nobody can read. Measured, not guessed — that is exactly what
    this assertion printed under its own non-vacuity probe.
    """
    declared = set(FK_CHILD_TABLES)
    actual = _tables_with_an_fk_to_repair_case(Base.metadata)
    assert actual == declared, (
        "the sweep's declared FK children have drifted from the metadata. "
        f"Declares an FK to repair_case but the sweep never clears it: "
        f"{sorted(actual - declared)}. Declared by the sweep but no longer an FK "
        f"child: {sorted(declared - actual)}."
    )


def test_ac5ii_every_case_id_bearing_table_is_classified_exactly_once() -> None:
    """The forwards half — the one that catches the shape a FK walk cannot see.

    ``repair_case_run_link`` is the standing proof this clause is not theoretical:
    it carries ``case_id`` and no FK, so it appears in this walk and in no FK
    walk anywhere.
    """
    declared_once = [set(FK_CHILD_TABLES), set(NO_FK_REFERENCERS), {ROOT_TABLE}]
    for left_index, left in enumerate(declared_once):
        for right in declared_once[left_index + 1 :]:
            assert not (left & right), (
                f"{sorted(left & right)} is classified twice — the sweep would then "
                "treat it under one policy and retain it under another"
            )

    classified: set[str] = set().union(*declared_once)
    unclassified = _tables_with_a_case_id_column(Base.metadata) - classified
    assert not unclassified, (
        f"{sorted(unclassified)} carries a `case_id` and is in none of the sweep's "
        "declared sets. Classify it in `services/db/repair_case_retention.py`: an FK "
        "child (deleted with its case), a no-FK referencer (with an explicit policy — "
        "see `repair_case_run_link`), or the root. Do NOT silence this by deleting the "
        "assertion: an unclassified table is exactly the silent orphan AC-5 exists for."
    )


def test_every_no_fk_referencer_carries_an_explicit_policy() -> None:
    """A table listed with an empty or missing policy is worse than an unlisted one:
    it reads as considered while telling the sweep nothing."""
    assert NO_FK_REFERENCERS, "the run link is a standing member; an empty map is a defect"
    for table, policy in NO_FK_REFERENCERS.items():
        assert policy.strip(), f"{table} is listed with no policy"
        assert table in Base.metadata.tables, f"{table} is declared but no longer mapped"


def _synthetic(*, with_fk: bool) -> sa.MetaData:
    """A metadata carrying the root plus one newly-arrived ``case_id`` table.

    Built on its own ``MetaData`` rather than by defining a mapped class here:
    a scratch class on ``Base`` would join the global metadata for the whole test
    process, and ``create_all`` in every other DB test would then try to build it.
    """
    md = sa.MetaData()
    sa.Table(ROOT_TABLE, md, sa.Column("case_id", sa.Text, primary_key=True))
    column = (
        sa.Column("case_id", sa.Text, sa.ForeignKey(_CASE_FK_TARGET))
        if with_fk
        else sa.Column("case_id", sa.Text)
    )
    sa.Table("scratch_case_note", md, sa.Column("note_id", sa.Text, primary_key=True), column)
    return md


def test_the_guard_would_catch_an_eighth_table_of_either_shape() -> None:
    """The guard's own bite, demonstrated on both shapes at once.

    Not a substitute for the external non-vacuity probe (which mutates the real
    declared set and watches the real assertion redden) — this is the cheaper,
    permanent half: it keeps the DETECTOR honest after a refactor, where the probe
    only ever ran once, by hand, on one day.
    """
    fk_shaped = _synthetic(with_fk=True)
    assert "scratch_case_note" in _tables_with_an_fk_to_repair_case(
        fk_shaped
    ), "an FK-shaped newcomer must surface in the FK walk, so AC-5(i)'s equality breaks"
    assert set(FK_CHILD_TABLES) != _tables_with_an_fk_to_repair_case(fk_shaped)

    silent_shaped = _synthetic(with_fk=False)
    assert "scratch_case_note" not in _tables_with_an_fk_to_repair_case(
        silent_shaped
    ), "the dangerous shape is invisible to an FK walk — that is the whole point"
    classified = set(FK_CHILD_TABLES) | set(NO_FK_REFERENCERS) | {ROOT_TABLE}
    assert _tables_with_a_case_id_column(silent_shaped) - classified == {
        "scratch_case_note"
    }, "the forwards walk is what catches it"
