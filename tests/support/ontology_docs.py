"""Every ontology doc the code generator can be pointed at, enumerated from disk.

One ``<ns>_v0.yaml`` per ``verticals/<ns>/ontology/`` directory, plus the shared
``ontology/core_v0.yaml``. Enumerated rather than listed, so a new vertical is covered
the day its ontology lands. Parked or template directories with no ``ontology/`` (today
``verticals/_template`` and ``verticals/vet_clinic``, README-only) are not docs and are
not expected here.

A glob that silently matches nothing would make every per-doc test pass over an empty
set, so ``test_sql_emitter.test_ontology_doc_enumeration_is_complete`` holds this
enumeration to the directory tree as a rule, not a roster or a numeric floor.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CORE_ONTOLOGY = REPO_ROOT / "ontology" / "core_v0.yaml"


def ontology_docs() -> list[Path]:
    """The vertical docs in sorted path order, then the shared ``core`` doc."""
    return [*sorted((REPO_ROOT / "verticals").glob("*/ontology/*_v0.yaml")), CORE_ONTOLOGY]
