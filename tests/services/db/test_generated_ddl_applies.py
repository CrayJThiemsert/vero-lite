"""Every generated ``schema.sql`` applies to Postgres, top to bottom (PLAN-0127 PR-1, AC-5).

Measured s306 (M2): as emitted, the DDL of 6 of the 7 ontology docs failed at its FIRST
statement with ``UndefinedTableError``. ``emit_sql`` wrote tables in ``object_types``
insertion order with inline ``REFERENCES``, so a table declared before the table it
references could not be created. Only ``core`` applied, because it has no refs. No test
had ever applied the generated DDL — every SQL emitter test was a substring check — so
the defect was invisible.

This drives the real producer (``emit_sql`` over the real ontology docs, enumerated from
disk) into the real consumer (Postgres). Each doc applies in its own scratch schema inside
a transaction that is always rolled back, so docs that share a table name (``alert`` is in
several verticals) cannot collide and nothing outlives the test.

DB-backed: it SKIPS when Postgres is unreachable (``create_test_engine``), which is the
default on a dev box without ``.env`` loaded. CI runs it against a live Postgres. The
DB-free twin that reddens everywhere is ``test_sql_emitter``'s forward-reference check
(AC-12).

Known limit, stated rather than hidden: a doc that ``imports:`` a shared ontology emits
``REFERENCES`` to tables its own DDL does not create. No doc does today. When one does,
this test reddens naming the imported table, and that is the moment to apply the imported
doc's DDL first.
"""

from __future__ import annotations

import re
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from services.engine.code_generator import _load_imports, emit_sql, load_doc
from tests.db_support import create_test_engine
from tests.support.ontology_docs import ontology_docs

# The emitter ends every statement with ``;`` and a newline, and writes no ``;`` inside
# one. asyncpg prepares one statement at a time, so the file is applied statement by
# statement — which is also what lets a failure name the statement that broke.
_STATEMENT_END = re.compile(r";\s*\n")


def _statements(ddl: str) -> list[str]:
    """The DDL split into single statements, comment-only fragments dropped."""
    parts = (part.strip() for part in _STATEMENT_END.split(ddl))
    return [
        part
        for part in parts
        if any(line.strip() and not line.strip().startswith("--") for line in part.splitlines())
    ]


def _head(statement: str) -> str:
    """The statement's first non-comment line — enough to name it in a failure."""
    return next(
        line.strip()
        for line in statement.splitlines()
        if line.strip() and not line.strip().startswith("--")
    )


async def _apply_in_scratch_schema(
    engine: AsyncEngine, namespace: str, statements: list[str]
) -> str | None:
    """Apply ``statements`` in file order in a throwaway schema, always rolled back.

    Returns ``None`` when every statement applied, else a reason naming the statement's
    position, its first line, and the database's own error.
    """
    schema = f"generated_ddl_{namespace}"
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.execute(sa.text(f'SET LOCAL search_path TO "{schema}"'))
            for position, statement in enumerate(statements, start=1):
                try:
                    await conn.exec_driver_sql(statement)
                except DBAPIError as exc:
                    error = str(exc.orig).splitlines()[0]
                    return f"stmt {position}/{len(statements)} `{_head(statement)}`: {error}"
            return None
        finally:
            await trans.rollback()


async def test_every_generated_schema_applies_to_postgres(tmp_path: Path) -> None:
    """AC-5: each doc's generated DDL applies to Postgres exactly as emitted.

    Pre-fix (insertion order) this reads ``failed=6`` — every vertical at ``stmt 1`` —
    with ``core`` applying. Post-fix it reads ``failed=0``.
    """
    engine = await create_test_engine()
    docs = ontology_docs()
    failures: dict[str, str] = {}
    try:
        for yaml_path in docs:
            doc = load_doc(yaml_path)
            namespace = str(doc.get("namespace", ""))
            out = emit_sql(doc, tmp_path / namespace / "schema.sql", _load_imports(doc))
            ddl = out.read_text(encoding="utf-8")
            statements = _statements(ddl)
            # Splitter control: one statement per CREATE, no more and no fewer. A splitter
            # that merged two statements would hide the second from the failure report.
            declared = ddl.count("\nCREATE TABLE ") + ddl.count("\nCREATE INDEX ")
            if len(statements) != declared:
                failures[namespace] = (
                    f"splitter read {len(statements)} statements; the DDL declares {declared}"
                )
                continue
            reason = await _apply_in_scratch_schema(engine, namespace, statements)
            if reason is not None:
                failures[namespace] = reason
    finally:
        await engine.dispose()

    summary = f"docs={len(docs)} applied={len(docs) - len(failures)} failed={len(failures)}"
    print(summary)
    # One line per failing doc: pytest truncates a dict diff, and a RED that hides which
    # doc broke, at which statement, is one nobody can act on (Lesson #0043).
    assert failures == {}, "\n".join([summary, *(f"  {ns}: {why}" for ns, why in failures.items())])
